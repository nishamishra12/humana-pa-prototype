"""LLM fact extraction, behind the same interface as extract.py's extract_facts().

Two safeguards the rule-based extractor doesn't have, both aimed directly at M6's findings:
  1. The prompt explicitly instructs negation handling (status "none", not "found") and
     conflicting-value handling (prefer the later/more authoritative statement, note the
     conflict) -- the two mechanisms that produced the critical hallucination and the wrong-
     value bug in the held-out set.
  2. Every quote the model returns is verified against the real packet text before being
     trusted. A quote that doesn't appear verbatim in the source is downgraded to "missing"
     with a note -- the model's claimed page number is never trusted on its own; the real
     page comes from where the verified quote actually is.
"""
import os, re, json
from .ingest import Element
from .extract import extract_header, _months, _fact

FACT_FIELDS = ["expected_los_days", "comorbidities", "post_op_needs",
               "indication_evidence", "conservative_treatment", "shared_decision_making"]

TOOL = {
    "name": "record_facts",
    "description": "Record the six clinical facts extracted from a prior authorization packet.",
    "input_schema": {
        "type": "object",
        "properties": {
            "expected_los_days": {"type": "object", "properties": {
                "status": {"type": "string", "enum": ["found", "implied", "missing"]},
                "value": {"type": ["integer", "null"], "description": "Number of midnights, only if status is found."},
                "quote": {"type": ["string", "null"], "description": "Exact sentence copied verbatim from the packet."},
                "note": {"type": ["string", "null"]}}, "required": ["status", "value", "quote", "note"]},
            "comorbidities": {"type": "object", "properties": {
                "status": {"type": "string", "enum": ["found", "none", "missing"]},
                "value": {"type": ["array", "null"], "items": {"type": "string"}, "description": "Short labels, e.g. 'heart failure'."},
                "quote": {"type": ["string", "null"]}, "note": {"type": ["string", "null"]}}, "required": ["status", "value", "quote", "note"]},
            "post_op_needs": {"type": "object", "properties": {
                "status": {"type": "string", "enum": ["found", "none", "missing"]},
                "value": {"type": ["string", "null"]}, "quote": {"type": ["string", "null"]}, "note": {"type": ["string", "null"]}},
                "required": ["status", "value", "quote", "note"]},
            "indication_evidence": {"type": "object", "properties": {
                "status": {"type": "string", "enum": ["found", "none", "implied", "missing"],
                          "description": "'none' means imaging/exam explicitly RULES OUT a finding (e.g. 'no evidence of instability') -- this is not the same as 'missing'."},
                "value": {"type": ["string", "null"], "enum": ["instability", "deformity", "pseudarthrosis", "neural compression", None]},
                "quote": {"type": ["string", "null"]}, "note": {"type": ["string", "null"]}}, "required": ["status", "value", "quote", "note"]},
            "conservative_treatment": {"type": "object", "properties": {
                "status": {"type": "string", "enum": ["found", "missing"]},
                "value": {"type": ["string", "null"]}, "quote": {"type": ["string", "null"]}, "note": {"type": ["string", "null"]}},
                "required": ["status", "value", "quote", "note"]},
            "shared_decision_making": {"type": "object", "properties": {
                "status": {"type": "string", "enum": ["found", "missing"]},
                "value": {"type": ["string", "null"]}, "quote": {"type": ["string", "null"]}, "note": {"type": ["string", "null"]}},
                "required": ["status", "value", "quote", "note"]},
        },
        "required": FACT_FIELDS,
    },
}

SYSTEM = """You extract six specific clinical facts from a prior authorization packet for a lumbar \
spinal fusion. Be literal and conservative. Two rules matter more than anything else:

1. NEGATION. If the text explicitly rules something out ("no evidence of instability", "no \
significant comorbidities", "imaging does not show..."), that is status "none", never "found". \
Reread the sentence before answering: does it say the finding IS present, or does it say the \
finding is ABSENT? A sentence containing the right keyword is not evidence by itself -- check \
what the sentence actually asserts.

2. CONFLICTS. If two different statements give different values for the same fact (e.g. two \
different lengths of stay), they are not equally valid. Prefer the one that is more specific, \
written later, or follows a review of additional information (like a cardiology clearance or an \
addendum) -- that is the corrected, authoritative figure, not the earlier draft estimate. Name \
the conflict in "note".

For every fact you report as found/none/implied, "quote" must be copied verbatim, character for \
character, from the packet text below. If you cannot find an exact sentence that supports your \
answer, set status to "missing" and quote to null -- do not paraphrase and do not invent a quote.

Never guess a value that is not stated. "implied" means the text gestures at the fact without \
giving a usable value (e.g. "a multi-day stay" with no number of midnights)."""


def _normalize(s):
    return re.sub(r"\s+", " ", s or "").strip().lower()


def _locate_quote(quote, elements):
    """Finds the real page a quote appears on. Returns None if it can't be verified verbatim
    (allowing for whitespace differences only) -- this is what stops a hallucinated citation
    from reaching the UI."""
    if not quote:
        return None
    nq = _normalize(quote)
    if len(nq) < 8:
        return None
    for e in elements:
        if nq in _normalize(e.text):
            return e.page
    return None


def _to_fact(raw, elements):
    if not raw or raw.get("status") == "missing" or not raw.get("quote"):
        return _fact(raw.get("status", "missing") if raw else "missing", raw.get("note") if raw else None)
    page = _locate_quote(raw["quote"], elements)
    if page is None:
        return _fact("unsure", note=f"The AI quoted text it could not show in the packet: \"{raw['quote'][:80]}\". Check the packet.")
    f = _fact(raw["status"], raw.get("value"), page, raw["quote"], raw.get("note"))
    return f


def _extract_facts_once(elements: list[Element], client) -> dict:
    full = "\n".join(e.text for e in elements)
    packet_text = "\n\n".join(f"[page {e.page}] {e.text}" for e in elements)

    resp = client.messages.create(
        model="claude-sonnet-5", max_tokens=1500, system=SYSTEM,
        tools=[TOOL], tool_choice={"type": "tool", "name": "record_facts"},
        messages=[{"role": "user", "content": f"Packet:\n\n{packet_text}"}],
    )
    tool_use = next(b for b in resp.content if b.type == "tool_use")
    raw = tool_use.input

    facts = extract_header(full)
    facts["_extractor"] = "llm"
    for key in FACT_FIELDS:
        facts[key] = _to_fact(raw.get(key), elements)
    if facts["conservative_treatment"]["status"] == "found" and facts["conservative_treatment"]["quote"]:
        facts["conservative_treatment"]["duration_months"] = _months(facts["conservative_treatment"]["quote"])
    return facts


def extract_facts(elements: list[Element], n_votes: int = 3) -> dict:
    """Self-consistency wrapper: this client exposes no temperature control (verified: the
    installed SDK's messages.create() has no such parameter), and the model has real run-to-run
    variance on borderline calls -- confirmed directly: on one sanity-set packet, 1 of 8 runs
    treated a bare diagnosis as sufficient imaging evidence when it should not have. Running
    n_votes times and only trusting a fact when every run agrees on its status turns that
    variance into an honest "needs a human" rather than a silent coin flip. This is the
    reproducibility NFR from ARCHITECTURE.md applied to the one place the model actually
    disagrees with itself. n_votes=1 skips voting, for fast interactive use."""
    import anthropic
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    from concurrent.futures import ThreadPoolExecutor
    n = max(1, n_votes)
    with ThreadPoolExecutor(max_workers=n) as pool:
        runs = list(pool.map(lambda _: _extract_facts_once(elements, client), range(n)))
    if len(runs) == 1:
        return runs[0]

    facts = dict(runs[0])
    for key in FACT_FIELDS:
        statuses = {r[key]["status"] for r in runs}
        if len(statuses) == 1:
            continue  # every run agreed; keep runs[0]'s version as-is
        votes = ", ".join(sorted(f"{r[key]['status']}" for r in runs))
        facts[key] = _fact("unsure", note=f"The AI read this {len(runs)} times and gave different answers ({votes}). Check the packet.")
    return facts
