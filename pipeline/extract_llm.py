"""AI fact extraction for any procedure in the registry (policies/policy_library.json `procedures`).

What the AI does, step by step:
  1. Reads the whole packet and fills the fact form for this procedure. For every fact it returns the value
     AND every sentence in the packet that states it (including conflicting ones, with dates when stated).
  2. It does this 3 times in parallel. If the 3 reads disagree on a fact's status or value, that fact
     becomes "unsure" and goes to the nurse. It is never guessed.
  3. Each quote is located in the packet with pipeline/evidence.locate_quote (fuzzy, but never across a
     different number). A quote that is not in the packet is dropped.
  4. A second, independent AI call checks that each located sentence really states the fact
     (pipeline/evidence.verify_meaning). A sentence that says something else turns the fact into "unsure".
Nothing here decides a case. The rules engine does that, and a person confirms it.
"""
import os, re, json
from concurrent.futures import ThreadPoolExecutor
from .ingest import Element
from .extract import extract_header, _months, _fact
from . import evidence as ev

EXTRACT_MODEL = os.getenv("PA_EXTRACT_MODEL", "claude-sonnet-5")

SYSTEM = """You read a prior authorization packet and fill in a fact form for one procedure. Be literal and conservative.

1. NEGATION. If the text rules something out ("no evidence of instability", "no significant comorbidities", "denies diabetes"), that is status "none", never "found". Reread the sentence: does it say the finding IS present, or that it is ABSENT?

2. CONFLICTS. If the packet states a fact more than once with different values, the later, dated or more specific statement is the current one (for example a repeat echocardiogram after treatment replaces an older one, even if the older report appears on a later page of the packet). Choose the current value, and list BOTH statements as evidence: the one that backs your value with supports_value true, the other with supports_value false. Put the dates in "date". Name the conflict in "note".

3. QUOTES. For every fact you report as found, none or implied, "evidence" must contain the exact sentence or phrase, copied verbatim, character for character, from the packet text below. Include up to 3 statements. If you cannot find an exact sentence that supports your answer, use status "missing" and an empty evidence list. Do not paraphrase. Do not invent a quote.

4. NEVER GUESS a value that is not stated. "implied" means the text gestures at the fact without a usable value.

Only use the statuses allowed for each fact."""


def _value_schema(d):
    k = d["kind"]
    if k == "number":
        return {"type": ["number", "null"]}
    if k == "enum":
        return {"type": ["string", "null"], "enum": list(d["values"]) + [None]}
    if k == "list":
        return {"type": ["array", "null"], "items": {"type": "string"}}
    return {"type": ["string", "null"]}


def build_tool(proc):
    props = {}
    for d in proc["facts"]:
        props[d["key"]] = {"type": "object", "description": d["ask"], "properties": {
            "status": {"type": "string", "enum": d["statuses"]},
            "value": _value_schema(d),
            "evidence": {"type": "array", "items": {"type": "object", "properties": {
                "quote": {"type": "string", "description": "Exact text copied verbatim from the packet."},
                "date": {"type": ["string", "null"], "description": "Date of the document or measurement, if stated."},
                "supports_value": {"type": "boolean", "description": "True if this statement backs the chosen value."}},
                "required": ["quote", "date", "supports_value"]}},
            "note": {"type": ["string", "null"], "description": "Name any conflict between statements."}},
            "required": ["status", "value", "evidence", "note"]}
    return {"name": "record_facts", "description": f"Record the facts for: {proc['name']}.",
            "input_schema": {"type": "object", "properties": props, "required": [d["key"] for d in proc["facts"]]}}


def _coerce(raw, proc):
    """The model occasionally returns a nested field as a JSON string, or an evidence item as a bare string.
    Repair what we can, so one odd reply does not lose a whole case. Raises if it cannot be repaired."""
    if isinstance(raw, str):
        raw = json.loads(raw)
    out = {}
    for d in proc["facts"]:
        v = raw.get(d["key"])
        if isinstance(v, str):
            v = json.loads(v)
        if not isinstance(v, dict) or "status" not in v:
            raise ValueError(f"unreadable answer for {d['key']}")
        ev_items = v.get("evidence") or []
        if isinstance(ev_items, str):
            ev_items = json.loads(ev_items)
        fixed = []
        for e in ev_items:
            if isinstance(e, str):
                e = {"quote": e, "date": None, "supports_value": True}
            fixed.append({"quote": e.get("quote", ""), "date": e.get("date"), "supports_value": bool(e.get("supports_value", True))})
        out[d["key"]] = {"status": v["status"], "value": v.get("value"), "evidence": [e for e in fixed if e["quote"]], "note": v.get("note")}
    return out


def _run_once(packet_text, proc, client):
    last = None
    for attempt in (1, 2):  # one retry on an unreadable reply
        resp = client.messages.create(
            model=EXTRACT_MODEL, max_tokens=4000, system=SYSTEM, tools=[build_tool(proc)],
            tool_choice={"type": "tool", "name": "record_facts"},
            messages=[{"role": "user", "content": f"Procedure: {proc['name']}\n\nPacket:\n\n{packet_text}"}])
        raw = next(b for b in resp.content if b.type == "tool_use").input
        try:
            return _coerce(raw, proc)
        except Exception as e:
            last = e
            print(f"[extract] unreadable AI reply, attempt {attempt} ({type(e).__name__}: {str(e)[:80]})")
    raise last


def _same(a, b, kind):
    if kind == "number":
        return a == b or (a is not None and b is not None and abs(float(a) - float(b)) < 1e-9)
    if kind == "enum":
        return (a or "").lower() == (b or "").lower()
    return True  # text and list values are free wording; the status must agree, and the evidence is checked below


def _combine(runs, d):
    """Merge the reads of one fact. Returns (agreed, raw, why). raw is the first read with the evidence of
    all reads added (duplicates removed)."""
    reads = [r.get(d["key"]) or {"status": "missing", "value": None, "evidence": [], "note": None} for r in runs]
    statuses = {r["status"] for r in reads}
    if len(statuses) > 1:
        return False, reads[0], "We read this more than once and got different answers. Check the packet."
    if not all(_same(reads[0]["value"], r["value"], d["kind"]) for r in reads[1:]):
        vals = ", ".join(sorted({str(r["value"]) for r in reads}))
        return False, reads[0], f"We read this more than once and got different values ({vals}). Check the packet."
    merged = list(reads[0]["evidence"])
    seen = {re.sub(r"\s+", " ", e["quote"]).strip().lower() for e in merged}
    for r in reads[1:]:
        for e in r["evidence"]:
            key = re.sub(r"\s+", " ", e["quote"]).strip().lower()
            if key not in seen:
                seen.add(key)
                merged.append(e)
    out = dict(reads[0])
    out["evidence"] = merged
    return True, out, None


def _claim_text(d, raw):
    st, v = raw["status"], raw["value"]
    label = d.get("phrase") or d["label"]
    if st == "none":
        return f"The packet states that there is none: {label}."
    if v is None or d["kind"] in ("text", "event"):
        return f"The packet documents {label}."  # free text: do not make one sentence carry the whole summary
    if isinstance(v, list):
        return f"The passage mentions at least one of these (it does not need to mention all): {', '.join(v)}. Topic: {label}."
    return f"The value for {label} is {v}."


def _assemble(d, agreed, raw, why, pages, verdicts):
    """Turn one fact's raw answer into the stored fact: located evidence, checked meaning, final status."""
    st = raw["status"]
    if not agreed:
        return _fact("unsure", note=why)
    if st == "missing":
        return _fact("missing", note=raw.get("note"))
    located = []
    for e in raw["evidence"]:
        hit = ev.locate_quote(e["quote"], pages)
        if hit:
            located.append(dict(page=hit["page"], quote=hit["text"], model_quote=e["quote"], match=hit["method"], score=hit["score"],
                                date=e.get("date"), supports=bool(e.get("supports_value", True))))
    backing = [x for x in located if x["supports"]]
    if not backing:
        return _fact("unsure", note="We could not find the exact wording in the packet. Check it yourself.")
    for i, x in enumerate(backing):
        v = verdicts.get(f"{d['key']}#{i}")
        x["verdict"], x["reason"] = v if v else (None, None)
    for x in backing:  # the checker sometimes answers in its own words
        if x.get("verdict") in ("sufficient", "supported", "support", "yes"):
            x["verdict"] = "supports"
    verdict_list = [x["verdict"] for x in backing if x.get("verdict")]
    checked = False
    if verdict_list:
        if "supports" in verdict_list:
            checked = True
        elif all(v in ("contradicts", "unrelated") for v in verdict_list):
            # every sentence we found says something else: do not trust the fact. 'insufficient' alone keeps it, without the tick.
            reason = next((x["reason"] for x in backing if x.get("reason")), "")
            f = _fact("unsure", note=f"The sentence we found does not clearly state this. {reason} Check the packet.".replace("  ", " "))
            f["evidence"] = located
            return f
    f = _fact(st, raw["value"], backing[0]["page"], backing[0]["quote"], raw.get("note"))
    f["evidence"] = located
    if checked:
        f["checked"] = True
    others = [x for x in located if not x["supports"]]
    if others and not f.get("note"):
        f["note"] = "The packet also states: " + "; ".join(
            f"“{x['quote'][:90]}” (p.{x['page']}" + (f", {x['date']}" if x.get("date") else "") + ")" for x in others[:2])
    return f


def extract_facts(elements: list[Element], proc_key: str, n_votes: int = 3) -> dict:
    import anthropic
    from .procedures import library
    proc = library()["procedures"][proc_key]
    defs = proc["facts"]
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    full = "\n".join(e.text for e in elements)
    packet_text = "\n\n".join(f"[page {e.page}] {e.text}" for e in elements)
    n = max(1, n_votes)
    with ThreadPoolExecutor(max_workers=n) as pool:
        runs = list(pool.map(lambda _: _run_once(packet_text, proc, client), range(n)))

    pages = ev.page_texts(elements)
    combined = {d["key"]: _combine(runs, d) for d in defs}
    items = []  # one batched meaning check over every fact that has a located supporting sentence
    for d in defs:
        agreed, raw, _ = combined[d["key"]]
        if not agreed or raw["status"] == "missing":
            continue
        i = 0
        for e in raw["evidence"]:
            if not e.get("supports_value", True):
                continue
            hit = ev.locate_quote(e["quote"], pages)
            if hit:
                items.append(dict(id=f"{d['key']}#{i}", claim=_claim_text(d, raw), quote=hit["text"], context=ev.context_for(pages, hit)))
                i += 1
    verdicts = ev.verify_meaning(items, client)

    facts = extract_header(full)
    facts["_extractor"] = "llm"
    facts["_procedure_key"] = proc_key
    for d in defs:
        agreed, raw, why = combined[d["key"]]
        facts[d["key"]] = _assemble(d, agreed, raw, why, pages, verdicts)
    cons = facts.get("conservative_treatment")
    if cons and cons["status"] == "found" and cons.get("quote"):
        cons["duration_months"] = _months(cons["quote"])
    return facts
