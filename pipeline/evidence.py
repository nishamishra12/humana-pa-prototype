"""Evidence matching, one step beyond Ctrl+F.

An exact-text search proves a sentence exists. It does not prove the sentence means what the AI says,
that it is the right sentence among several, or that a scan was read correctly. This module does three
more things:

  1. locate_quote   finds the quote even when a scan or a line break changed a few characters (fuzzy
                    match), but refuses to match if any NUMBER differs. "LVEF 28%" never matches "LVEF 38%".
                    It returns the real text from the packet, so the screen highlights what is on the page.
  2. verify_meaning a second, independent AI call reads each quote in its surrounding page and says
                    whether it really states the fact. It catches "no evidence of instability" being
                    quoted as instability, and quotes about something else.
  3. reconcile      when the packet states a fact more than once, keep every statement, say which one
                    wins, and show the others to the nurse.

The model does the reading. Plain code does the matching and the number checks.
"""
import os, re, unicodedata
from rapidfuzz import fuzz
from . import telemetry as tel

FUZZY_MIN = 88          # similarity needed (out of 100) when the exact text is not found
MIN_QUOTE = 8           # shorter quotes are too weak to trust
VERIFY_MODEL = os.getenv("PA_VERIFY_MODEL", "claude-haiku-4-5-20251001")

_PUNCT = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"', "–": "-", "—": "-", "−": "-", " ": " "})


def norm_map(s):
    """Lowercase, straighten quotes and dashes, rejoin words split by a line break, collapse spaces.
    Returns the normalized text and, for each character, its index in the original (to find the real span)."""
    out, idx, prev_space = [], [], False
    i, n = 0, len(s)
    while i < n:
        ch = s[i]
        if ch == "­":
            i += 1
            continue
        if ch == "-" and i + 1 < n and s[i + 1] in "\r\n" and out and out[-1].isalpha():
            i += 2
            while i < n and s[i] in " \t\r\n":
                i += 1
            continue
        for c in unicodedata.normalize("NFKC", ch).lower().translate(_PUNCT):
            if c.isspace():
                if out and not prev_space:
                    out.append(" ")
                    idx.append(i)
                    prev_space = True
            else:
                out.append(c)
                idx.append(i)
                prev_space = False
        i += 1
    while out and out[-1] == " ":
        out.pop()
        idx.pop()
    return "".join(out), idx


def page_texts(elements):
    pages = {}
    for e in elements:
        pages.setdefault(e.page, []).append(e.text)
    return {p: "\n".join(t) for p, t in pages.items()}


_NUM = re.compile(r"\d+(?:\.\d+)?")


def _numbers(s):
    return sorted(_NUM.findall(s))


def locate_quote(quote, pages, prefer_page=None):
    """Find `quote` in the packet. Returns dict(page, text, start, end, score, method) or None.
    method is "exact" or "fuzzy". Fuzzy matches must carry the same numbers as the quote."""
    nq, _ = norm_map(quote or "")
    if len(nq) < MIN_QUOTE:
        return None
    best = None
    for pg, raw in pages.items():
        nt, idx = norm_map(raw)
        pos = nt.find(nq)
        if pos >= 0:
            s, e = idx[pos], idx[pos + len(nq) - 1] + 1
            hit = dict(page=pg, text=raw[s:e], start=s, end=e, score=100.0, method="exact")
            if best is None or best["method"] != "exact" or pg == prefer_page:
                best = hit
            if pg == prefer_page:
                break
            continue
        if best and best["method"] == "exact":
            continue
        if len(nq) < 14:
            continue
        al = fuzz.partial_ratio_alignment(nq, nt)
        if al is None or al.score < FUZZY_MIN:
            continue
        span = nt[al.dest_start:al.dest_end]
        if _numbers(span) != _numbers(nq):
            continue  # a different number means a different fact
        s, e = idx[al.dest_start], idx[max(al.dest_end - 1, al.dest_start)] + 1
        hit = dict(page=pg, text=raw[s:e], start=s, end=e, score=round(al.score, 1), method="fuzzy")
        if best is None or hit["score"] > best["score"]:
            best = hit
    return best


def context_for(pages, hit, radius=350):
    raw = pages[hit["page"]]
    return raw[max(0, hit["start"] - radius): min(len(raw), hit["end"] + radius)]


VERDICT_TOOL = {
    "name": "record_verdicts",
    "description": "Record, for each item, whether the passage really states the claim.",
    "input_schema": {"type": "object", "properties": {"verdicts": {"type": "array", "items": {"type": "object", "properties": {
        "id": {"type": "string"},
        "verdict": {"type": "string", "enum": ["supports", "contradicts", "unrelated", "insufficient"]},
        "reason": {"type": "string", "description": "One short plain sentence."}},
        "required": ["id", "verdict", "reason"]}}}, "required": ["verdicts"]},
}
VERIFY_SYSTEM = (
    "You are a strict checker of clinical documentation. For each item you get a claim about a patient and a passage "
    "from the chart with its surrounding text. Decide from the passage alone: does it state the claim?\n"
    "supports = the passage states it. contradicts = the passage says the opposite or gives a different value "
    "(for example 'no evidence of instability' when the claim is that instability was found). "
    "unrelated = the passage is about something else. insufficient = it hints at the claim but does not state it. "
    "A claim with several parts is supported if the passage correctly states any part and nothing in it contradicts the claim: the passage does not have to cover everything. "
    "Be literal. Do not use outside knowledge. Give a one-sentence plain reason."
)


def verify_meaning(items, client):
    """items: list of dict(id, claim, quote, context). Returns {id: (verdict, reason)}.
    One batched call. If the call fails, returns {} and the caller keeps the exact-text result only."""
    if not items:
        return {}
    listing = "\n\n".join(f"ITEM {it['id']}\nClaim: {it['claim']}\nPassage: \"{it['quote']}\"\nSurrounding text: {it['context']}" for it in items)
    for attempt in (1, 2):  # one retry: a transient error should not silently skip the check
        try:
            resp = client.messages.create(model=VERIFY_MODEL, max_tokens=3000, system=VERIFY_SYSTEM, tools=[VERDICT_TOOL],
                                         tool_choice={"type": "tool", "name": "record_verdicts"},
                                         messages=[{"role": "user", "content": listing}])
            tel.llm_usage(resp)
            out = next(b for b in resp.content if b.type == "tool_use").input.get("verdicts", [])
            return {v["id"]: (v["verdict"], v["reason"]) for v in out}
        except Exception as e:
            print(f"[verify] meaning check failed, attempt {attempt} ({type(e).__name__}: {str(e)[:100]})")
    return {}  # never block a case because the checker was unavailable
