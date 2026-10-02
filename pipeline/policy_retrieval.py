"""M7, part 2: the bounded retrieval fallback described in ARCHITECTURE.md section 5.

Used only when a packet's procedure has no entry in the curated policy_library.json. Searches
the full downloaded CMS corpus (969 LCDs + 345 NCDs, policies/corpus/) for the real policy that
actually applies, then has Claude turn its real indications text into a plain-language checklist.

This never feeds into the automated decision engine. Its output is always marked unverified and
routed to a human to confirm -- exactly the "it never silently substitutes for the curated table"
rule the architecture doc states. engine.py enforces that separately by escalating any case whose
CPT isn't in the curated table, before this module is ever reached for a real decision.
"""
import os, re, json
from functools import lru_cache

ROOT = os.path.join(os.path.dirname(__file__), "..")
STOPWORDS = {"the", "a", "an", "of", "for", "with", "and", "or", "to", "in", "on", "at", "by"}


def _tokens(s):
    return [w for w in re.findall(r"[a-z0-9]+", (s or "").lower()) if w not in STOPWORDS and len(w) > 2]


@lru_cache(maxsize=1)
def _corpus():
    lcds = json.load(open(os.path.join(ROOT, "policies", "corpus", "lcds.json"), encoding="utf-8"))
    ncds = json.load(open(os.path.join(ROOT, "policies", "corpus", "ncds.json"), encoding="utf-8"))
    return [d for d in lcds + ncds if "error" not in d]


def _score(query_tokens, doc):
    title_tokens = set(_tokens(doc["title"]))
    body_tokens = set(_tokens(doc.get("indications") or doc.get("description") or ""))
    qset = set(query_tokens)
    title_hits = len(qset & title_tokens)
    body_hits = len(qset & body_tokens)
    return title_hits * 3 + body_hits


def keyword_candidates(query_text, top_k=8):
    qtok = _tokens(query_text)
    scored = [(_score(qtok, d), d) for d in _corpus()]
    scored = [x for x in scored if x[0] > 0]
    scored.sort(key=lambda x: -x[0])
    return [d for _, d in scored[:top_k]]


def find_policy(procedure_text, top_k=8):
    """Keyword search narrows ~1,300 documents to a handful; Claude picks (or rejects) among
    just those, which keeps the LLM's job bounded and auditable instead of an open-ended search."""
    import anthropic
    candidates = keyword_candidates(procedure_text, top_k=top_k)
    if not candidates:
        return dict(matched=False, reason="No keyword overlap with any policy in the corpus.", candidates=[])

    listing = "\n".join(f"{i+1}. [{c['kind']} {c['id']}] {c['title']}" for i, c in enumerate(candidates))
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    resp = client.messages.create(
        model="claude-sonnet-5", max_tokens=600,
        system=("You are matching a requested procedure to a Medicare coverage policy from a short, "
                "pre-filtered list. Only pick one if it genuinely governs this exact procedure. If none "
                "of them do, say so -- a wrong match routed to a human reviewer is worse than admitting "
                "no match was found."),
        tools=[{"name": "pick_policy", "input_schema": {"type": "object", "properties": {
            "matched": {"type": "boolean"},
            "number": {"type": ["integer", "null"], "description": "1-based list position of the match, or null if none."},
            "reasoning": {"type": "string"}}, "required": ["matched", "number", "reasoning"]}}],
        tool_choice={"type": "tool", "name": "pick_policy"},
        messages=[{"role": "user", "content": f"Requested procedure: {procedure_text}\n\nCandidates:\n{listing}"}],
    )
    out = next(b for b in resp.content if b.type == "tool_use").input
    if not out.get("matched") or not out.get("number"):
        return dict(matched=False, reason=out.get("reasoning") or "No candidate was a genuine match (model did not finish its reasoning).", candidates=[c["title"] for c in candidates])
    chosen = candidates[out["number"] - 1]
    return dict(matched=True, reasoning=out["reasoning"], policy=chosen,
               other_candidates=[c["title"] for c in candidates if c is not chosen])


def draft_criteria(policy_doc):
    """Turns a real policy's indications text into a plain checklist. Marked verified=False --
    this is a draft for a human to approve, never something the engine acts on automatically."""
    import anthropic
    text = (policy_doc.get("indications") or policy_doc.get("description") or "")[:6000]
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    resp = client.messages.create(
        model="claude-sonnet-5", max_tokens=1200,
        system=("Turn this Medicare coverage policy's indications text into a short checklist of what "
                "must be documented for coverage. Each item should be one concrete, checkable thing a "
                "reviewer looks for in a chart. Quote or closely paraphrase the policy; do not invent "
                "requirements the text doesn't state. 3 to 8 items."),
        tools=[{"name": "record_checklist", "input_schema": {"type": "object", "properties": {
            "items": {"type": "array", "items": {"type": "object", "properties": {
                "text": {"type": "string"}, "basis": {"type": "string", "description": "The exact phrase from the policy this item is drawn from."}},
                "required": ["text", "basis"]}}}, "required": ["items"]}}],
        tool_choice={"type": "tool", "name": "record_checklist"},
        messages=[{"role": "user", "content": f"Policy: {policy_doc['title']} ({policy_doc['kind']} {policy_doc['id']})\n\n{text}"}],
    )
    items = next(b for b in resp.content if b.type == "tool_use").input["items"]
    return dict(
        id=f"{policy_doc['kind']}-{policy_doc['id']}", level=policy_doc["kind"], title=policy_doc["title"],
        source=f"CMS Medicare Coverage Database, {policy_doc['kind']} {policy_doc['id']}" + (f", {policy_doc.get('mac')}" if policy_doc.get("mac") else ""),
        url=policy_doc.get("url"), verified=False,
        verified_note="Drafted automatically from the real policy text by the retrieval fallback. Not reviewed by the Utilization Management Committee. Must not be used to auto-decide a case.",
        criteria=[dict(text=i["text"], cite=f"{policy_doc['kind']} {policy_doc['id']}", basis=i["basis"]) for i in items],
    )


def lookup_and_draft(procedure_text):
    match = find_policy(procedure_text)
    if not match["matched"]:
        return dict(matched=False, procedure=procedure_text, reasoning=match["reason"])
    drafted = draft_criteria(match["policy"])
    return dict(matched=True, procedure=procedure_text, reasoning=match["reasoning"], policy=drafted)
