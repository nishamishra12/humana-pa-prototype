"""Deterministic decision engine.

Takes extracted facts + the policy library and produces a criteria checklist, the
completeness gate (what is missing, phrased as one specific question), and a
recommendation. The engine can recommend approve, pend (ask for missing info) or
escalate. It has no deny value: only a medical director can deny.

Works for every procedure in the registry (policies/policy_library.json `procedures`). The CPT code picks
the procedure; the procedure lists its facts and the policies that apply, in order of authority.
Criteria can test a number (gte, lte), a choice (in), presence (default), or absence (mode "absent").
This is plain code, not AI, so the same facts always give the same recommendation.
"""
import json, os
from .procedures import library, procedure_for_cpt, defs_by_key, ui_schema

LIBRARY = library()
POLICIES = {p["id"]: p for p in LIBRARY["policies"]}
ORDER = {lvl: i for i, lvl in enumerate(LIBRARY["hierarchy"])}


def refresh():
    """Pick up a newly published library without restarting the app."""
    global LIBRARY, POLICIES, ORDER
    from .procedures import reload
    LIBRARY = reload()
    POLICIES = {p["id"]: p for p in LIBRARY["policies"]}
    ORDER = {lvl: i for i, lvl in enumerate(LIBRARY["hierarchy"])}

LEVEL_LABEL = {"REGULATION": "Regulation", "NCD": "NCD", "LCD": "LCD",
               "HUMANA_INTERNAL": "Humana policy (illustrative)", "MCG": "MCG"}


def _check(chk, value):
    op, want = chk["op"], chk["value"]
    if value is None:
        return False
    try:
        if op == "gte":
            return float(value) >= want
        if op == "lte":
            return float(value) <= want
        if op == "in":
            allowed = [str(w).lower() for w in want]
            if isinstance(value, (list, tuple)):
                return any(str(v).lower() in allowed for v in value)
            return str(value).lower() in allowed
    except (TypeError, ValueError):
        return False
    return False


def _applies(crit, facts):
    cond = crit.get("applies_if")
    if not cond:
        return True
    f = facts.get(cond["fact"], {})
    return f.get("status") == "found" and str(f.get("value")).lower() == str(cond["equals"]).lower()


def _judge(crit, facts):
    """Return (status, fact_key) with status in met | not_met | missing | unsure | info."""
    key = crit.get("required_fact")
    if crit.get("test") == "informational" or not key:
        return "info", key
    f = facts.get(key, {"status": "missing"})
    st = f["status"]
    if st == "unsure":
        return "unsure", key
    if crit.get("mode") == "absent":  # satisfied when the packet says there is none
        return ("met" if st == "none" else "not_met" if st == "found" else "missing"), key
    if st == "found":
        chk = crit.get("check")
        if chk:
            return ("met" if _check(chk, f.get("value")) else "not_met"), key
        return "met", key
    if st == "none":
        return "not_met", key
    return "missing", key


def _evidence_list(f):
    if not f:
        return []
    ev = [dict(page=e["page"], quote=e["quote"], match=e.get("match"), score=e.get("score"), date=e.get("date"), supports=e.get("supports", True))
          for e in f.get("evidence", []) if e.get("page")]
    if not ev and f.get("page"):
        ev = [dict(page=f["page"], quote=f.get("quote"), match="exact", score=100.0, date=None, supports=True)]
    return ev


def analyze(facts: dict) -> dict:
    cpt = facts.get("_cpt")
    pkey, proc = procedure_for_cpt(cpt)
    covered = LIBRARY.get("covered_cpt_codes", [])
    if not proc:
        names = ", ".join(p["short"].lower() for p in LIBRARY["procedures"].values() if p.get("status") != "planned")
        today = f"Today PA Desk checks {names}. " if names else "No service is switched on yet. "
        return dict(
            checklist=[], gate=dict(complete=False, questions=[]), action="no_policy",
            rationale=(f"We do not have a policy for procedure code {cpt or 'unknown'} ({facts.get('_procedure') or 'procedure not identified'}). "
                      f"{today}We will not judge this case against the wrong policy."),
            policies=[], cannot_deny=True, cpt_covered=False, covered_cpt_codes=covered, procedure=None, fact_schema=[])
    defs = defs_by_key(proc)
    checklist, questions, unsure = [], {}, {}
    policies = sorted((POLICIES[pid] for pid in proc["policies"]), key=lambda p: ORDER[p["level"]])
    for pol in policies:
        for c in pol["criteria"]:
            if not _applies(c, facts):
                continue
            status, key = _judge(c, facts)
            f = facts.get(key) if key else None
            soft = c.get("severity") == "soft"
            evl = _evidence_list(f)
            item = dict(
                policy_id=pol["id"], layer=LEVEL_LABEL[pol["level"]], policy_title=pol["title"],
                verified=pol["verified"], cite=c["cite"], criterion_id=c["id"], text=c["text"], short=c.get("short"),
                status=("advisory" if (soft and status == "missing") else status),
                fact_key=key,
                evidence=dict(page=evl[0]["page"], quote=evl[0]["quote"]) if evl else None,
                evidence_all=evl,
                note=(f or {}).get("note"),
            )
            checklist.append(item)
            if status == "unsure":
                unsure.setdefault(key, dict(fact=key, note=(f or {}).get("note")))
            if status == "missing" and not soft:
                q = questions.setdefault(key, dict(fact=key, question=_provider_facing(c["if_missing"]), affects=[], note=(f or {}).get("note")))
                q["affects"].append(c["id"])

    def label(key):
        return (defs.get(key) or {}).get("phrase") or key

    gate = dict(complete=not questions and not unsure, questions=list(questions.values()), unsure=list(unsure.values()))
    not_met = [c for c in checklist if c["status"] == "not_met"]
    if unsure:
        action = "verify"
        rationale = ("We could not confirm " + ", ".join(label(k) for k in unsure) +
                     ". Check the packet and confirm it before you decide. Do not ask the provider yet.")
    elif questions:
        action = "pend"
        rationale = ("The packet is missing " + ", ".join(label(q["fact"]) for q in questions.values()) +
                     ". Ask the provider for exactly that before judging the case.")
    elif not_met:
        action = "escalate"
        rationale = ("The packet is complete, but " + "; ".join((c.get("short") or c["text"][:60]) for c in not_met) +
                     ". This needs a physician's clinical judgment, so it goes to a medical director.")
    else:
        action = "approve"
        rationale = "The packet is complete and every criterion is supported."
    return dict(checklist=checklist, gate=gate, action=action, rationale=rationale, library_version=LIBRARY.get("version"),
                policies=[dict(id=p["id"], level=LEVEL_LABEL[p["level"]], title=p["title"], source=p["source"],
                               url=p["url"], verified=p["verified"]) for p in policies if p["criteria"]],
                cannot_deny=True, cpt_covered=True, covered_cpt_codes=covered,
                procedure=dict(key=pkey, name=proc["name"], short=proc["short"], cpts=proc["cpts"], status=proc.get("status", "live")),
                fact_schema=ui_schema(proc))


def _provider_facing(text):
    t = text[5:] if text.startswith("Ask: ") else text
    return t[:1].upper() + t[1:]
