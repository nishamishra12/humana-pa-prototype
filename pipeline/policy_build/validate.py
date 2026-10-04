"""Step 4 of the policy build: plain code checks the AI's draft. No AI here.

For every drafted criterion:
  - the source quote must be found in the policy text (exact, or fuzzy with the same numbers),
  - every number in the test must appear in that quote (a threshold the policy did not state is rejected),
  - the fact must exist in the vocabulary or be declared as a new fact,
  - "in" tests may only use values the fact can take,
  - the id must be unique.
For the whole draft:
  - rule-like sentences in the source that no criterion and no not-modeled note covers are listed as possible misses.

A criterion is "pass", "review" (a person should look closely) or "fail". Nothing is dropped silently: failures are shown to the owner.
"""
import re

from pipeline import evidence as ev

RULE_WORDS = re.compile(r"\b(must|only|require[sd]?|covered|non-?covered|not covered|at least|no more than|within|following|if |when |unless|except)\b|\d+\s*%|\d+\s*(days?|weeks?|months?|years?)\b", re.I)


def _sentences(text):
    parts = re.split(r"(?<=[.;:])\s+|\n+", text)
    return [p.strip() for p in parts if len(p.strip()) > 25]


def _num_strings(s):
    return set(re.findall(r"\d+(?:\.\d+)?", s or ""))


def _locate(quote, pages):
    """Find a quote. A quote shortened with '...' is accepted when every piece is found in the text. Returns a hit dict or None."""
    if not quote:
        return None
    pieces = [p.strip() for p in re.split(r"\.\.\.|…", quote) if len(p.strip()) >= ev.MIN_QUOTE]
    if len(pieces) <= 1:
        return ev.locate_quote(quote, pages)
    hits = [ev.locate_quote(p, pages) for p in pieces]
    if all(hits):
        return dict(method="exact" if all(h["method"] == "exact" for h in hits) else "fuzzy", score=min(h["score"] for h in hits), pieces=len(pieces))
    return None


def validate(draft, elements, vocab):
    keys = {d["key"]: d for d in vocab}
    new_keys = {f["key"]: f for f in draft.get("new_facts", [])}
    pages = {}
    for e in elements:
        pages[e.get("page", 1)] = pages.get(e.get("page", 1), "") + e["text"] + "\n"
    full = "\n".join(e["text"] for e in elements)
    seen, rows = set(), []
    quotes = []
    for c in draft["criteria"]:
        issues, level = [], "pass"

        def bad(msg, sev="fail"):
            nonlocal level
            issues.append(msg)
            if sev == "fail" or level == "pass":
                level = "fail" if sev == "fail" else "review"

        if c["id"] in seen:
            bad("duplicate id")
        seen.add(c["id"])
        q = c.get("source_quote") or ""
        hit = _locate(q, pages)
        if not hit:
            bad("the quote is not in the policy text")
        elif hit["method"] == "fuzzy":
            bad(f"quote matched only approximately ({hit['score']})", "review")
        quotes.append(q)
        t = c.get("test") or {}
        tt, val = t.get("type"), t.get("value")
        fact = c.get("required_fact")
        if tt in ("gte", "lte"):
            if not isinstance(val, (int, float)) or isinstance(val, bool):
                bad("a threshold test needs a number")
            else:
                words = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "twelve": 12}
                nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", q)] + [float(v) for w, v in words.items() if re.search(rf"\b{w}\b", q, re.I)]
                if any(abs(n - val) < 1e-9 for n in nums):
                    pass
                elif any(abs(n * 100 - val) < 1e-6 for n in nums):
                    bad("the policy writes this as a fraction; the draft converted it to a percent. Check the conversion.", "review")
                else:
                    bad(f"the number {val:g} does not appear in the quote")
        elif tt == "in":
            if not isinstance(val, list) or not val:
                bad("an 'in' test needs a list of values")
            elif fact in keys and keys[fact].get("values"):
                extra = [v for v in val if str(v).lower() not in [str(x).lower() for x in keys[fact]["values"]]]
                if extra:
                    bad(f"values the fact cannot take: {', '.join(map(str, extra))}")
        elif tt in ("absent", "present", "informational"):
            pass
        else:
            bad(f"unknown test type {tt}")
        if tt != "informational":
            if not fact:
                bad("a testable criterion needs a fact")
            elif fact not in keys and fact not in new_keys:
                bad(f"the packet detail {fact} is not one the reader knows and was not declared as new")
            elif fact in new_keys:
                bad(f"needs a new packet detail ({fact}): the packet reader does not look for it yet", "review")
        ai = c.get("applies_if")
        if ai and ai.get("fact") not in keys and ai.get("fact") not in new_keys:
            bad(f"applies_if names an unknown packet detail {ai.get('fact')}")
        elif ai and ai.get("fact") in keys:
            af = keys[ai["fact"]]
            allowed = [str(v).lower() for v in (af.get("values") or [])]
            if af.get("kind") != "enum" or (allowed and str(ai.get("equals")).lower() not in allowed):
                bad(f"applies_if says 'only when {ai['fact']} is {ai.get('equals')}', which that detail can never be. The engine would skip this rule.", "review")
        if c.get("confidence") == "low":
            bad("the AI marked its own confidence low", "review")
        rows.append(dict(id=c["id"], level=level, issues=issues, quote_found=bool(hit), match=hit["method"] if hit else None))

    # coverage: rule-like sentences that nothing in the draft accounts for
    covered_text = " ".join(quotes + [n.get("quote", "") for n in draft.get("not_modeled", [])])
    norm = lambda s: re.sub(r"\W+", " ", s.lower()).strip()
    cov = norm(covered_text)
    uncovered = []
    for s in _sentences(full):
        if RULE_WORDS.search(s) and norm(s) not in cov and not any(norm(w) in cov for w in re.split(r"(?<=[.;])\s+", s) if len(w) > 30):
            # a shorter quote can cover part of a long sentence: count the sentence as covered if most of its words appear in the covered text
            words = set(norm(s).split())
            if len(words & set(cov.split())) / max(1, len(words)) < 0.6:
                uncovered.append(s)
    n = {k: sum(1 for r in rows if r["level"] == k) for k in ("pass", "review", "fail")}
    return dict(criteria=rows, counts=n, total=len(rows), uncovered=uncovered, new_facts=[f["key"] for f in draft.get("new_facts", [])],
                not_modeled=len(draft.get("not_modeled", [])))
