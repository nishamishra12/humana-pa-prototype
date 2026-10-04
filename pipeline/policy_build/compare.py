"""The policy build's own eval: compare an AI draft with the approved (hand-written) criteria for the same policy.

Criteria are matched by the fact they test, then the test is compared (same operator and value, or the same mode). For each
approved criterion the result is:
  same     the draft has a criterion on the same fact with the same test
  differs  the draft tests the same fact but with a different test (a person must look)
  missed   the draft has nothing for that fact
Draft criteria on a fact that no approved criterion tests are listed as extra (they may be real gaps in the approved set, or invented).
"""
import json, os

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")


def _norm_test(test):
    """Library style: ('gte', 35) / ('in', frozenset) / ('absent',) / ('present',) / ('info',)."""
    t = (test or {}).get("type")
    v = (test or {}).get("value")
    if t in ("gte", "lte"):
        return (t, float(v)) if isinstance(v, (int, float)) else (t, None)
    if t == "in":
        return ("in", frozenset(str(x).lower() for x in (v or [])))
    return (t,)


def _approved_test(c):
    chk = c.get("check")
    if chk:
        op = chk["op"]
        return (op, float(chk["value"])) if op in ("gte", "lte") else ("in", frozenset(str(x).lower() for x in chk["value"]))
    if c.get("mode") == "absent":
        return ("absent",)
    if c.get("test") == "informational" or not c.get("required_fact"):
        return ("informational",)
    return ("present",)


def load_approved(policy_id):
    lib = json.load(open(os.path.join(ROOT, "policies", "policy_library.json"), encoding="utf-8"))
    pols = lib["policies"] if isinstance(lib["policies"], list) else list(lib["policies"].values())
    p = next((x for x in pols if x["id"] == policy_id), None)
    return p["criteria"] if p else None


def compare(draft, policy_id):
    approved = load_approved(policy_id)
    if approved is None:
        return None
    ai_by_fact = {}
    for c in draft["criteria"]:
        if c.get("required_fact") and (c.get("test") or {}).get("type") != "informational":
            ai_by_fact.setdefault(c["required_fact"], []).append(c)
    rows, used = [], set()
    for h in approved:
        fact = h.get("required_fact")
        want = _approved_test(h)
        if want == ("informational",) and not fact:
            rows.append(dict(id=h["id"], fact=None, result="info", note="informational note, not tested"))
            continue
        cands = ai_by_fact.get(fact, [])
        if not cands:
            rows.append(dict(id=h["id"], fact=fact, result="missed", approved=_show(want), draft=None))
            continue
        same = next((c for c in cands if _norm_test(c.get("test")) == want or (want == ("present",) and _norm_test(c.get("test")) in (("present",), ("in", frozenset())))), None)
        used.update(id(c) for c in cands)
        if same is not None:
            rows.append(dict(id=h["id"], fact=fact, result="same", approved=_show(want), draft=_show(_norm_test(same.get("test"))), draft_id=same["id"]))
        else:
            c = cands[0]
            rows.append(dict(id=h["id"], fact=fact, result="differs", approved=_show(want), draft=_show(_norm_test(c.get("test"))), draft_id=c["id"]))
    extra = [dict(id=c["id"], fact=c["required_fact"], test=_show(_norm_test(c.get("test"))), text=c["text"]) for c in draft["criteria"]
             if c.get("required_fact") and (c.get("test") or {}).get("type") != "informational" and id(c) not in used]
    n = {k: sum(1 for r in rows if r["result"] == k) for k in ("same", "differs", "missed")}
    return dict(policy_id=policy_id, rows=rows, extra=extra, counts=n, approved_count=sum(1 for r in rows if r["result"] != "info"))


def _show(t):
    if t[0] in ("gte", "lte"):
        return f"{t[0]} {t[1]:g}" if t[1] is not None else t[0]
    if t[0] == "in":
        return "in " + ", ".join(sorted(t[1]))
    return t[0]
