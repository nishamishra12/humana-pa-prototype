"""Deterministic decision engine.

Takes extracted facts + the policy library and produces a criteria checklist, the
completeness gate (what is missing, phrased as one specific question), and a
recommendation. The engine can recommend approve, pend (ask for missing info) or
escalate. It has no deny value: only a medical director can deny.
"""
import json, os

LIB_PATH = os.path.join(os.path.dirname(__file__), "..", "policies", "policy_library.json")
LIBRARY = json.load(open(LIB_PATH, encoding="utf-8"))
POLICIES = {p["id"]: p for p in LIBRARY["policies"]}
ORDER = {lvl: i for i, lvl in enumerate(LIBRARY["hierarchy"])}

LEVEL_LABEL = {"REGULATION": "Regulation", "NCD": "NCD", "LCD": "LCD",
               "HUMANA_INTERNAL": "Humana policy (illustrative)", "MCG": "MCG"}


def _judge(crit, facts):
    """Return (status, fact_key) with status in met | not_met | missing | info."""
    key = crit.get("required_fact")
    test = crit.get("test")
    if test == "informational" or not key:
        return "info", key
    f = facts.get(key, {"status": "missing"})
    st = f["status"]
    if key == "expected_los_days":
        if st == "found":
            return ("met" if f["value"] >= 2 else "not_met"), key
        return "missing", key
    if st == "found":
        return "met", key
    if st == "none":
        return "not_met", key
    return "missing", key


def analyze(facts: dict) -> dict:
    checklist, questions = [], {}
    policies = sorted(POLICIES.values(), key=lambda p: ORDER[p["level"]])
    for pol in policies:
        for c in pol["criteria"]:
            status, key = _judge(c, facts)
            f = facts.get(key) if key else None
            soft = c.get("severity") == "soft"
            item = dict(
                policy_id=pol["id"], layer=LEVEL_LABEL[pol["level"]], policy_title=pol["title"],
                verified=pol["verified"], cite=c["cite"], criterion_id=c["id"], text=c["text"],
                status=("advisory" if (soft and status == "missing") else status),
                fact_key=key,
                evidence=dict(page=f["page"], quote=f["quote"]) if f and f.get("page") else None,
                note=(f or {}).get("note"),
            )
            checklist.append(item)
            if status == "missing" and not soft:
                q = questions.setdefault(key, dict(fact=key, question=c["if_missing"], affects=[], note=(f or {}).get("note")))
                q["affects"].append(c["id"])

    # LCD indication 2 (deformity): non-operative treatment for at least 12 months
    ind, cons = facts.get("indication_evidence", {}), facts.get("conservative_treatment", {})
    if ind.get("status") == "found" and ind.get("value") == "deformity" and cons.get("status") == "found":
        months = cons.get("duration_months")
        if months is not None:
            ok = months >= 12
            checklist.append(dict(
                policy_id="LCD-L37848", layer="LCD", policy_title=POLICIES["LCD-L37848"]["title"], verified=True,
                cite="LCD L37848, Indication 2b", criterion_id="LCD-DEF-12M",
                text="For deformity without instability or neural compression: nonresponse to at least 1 year of non-operative treatment.",
                status="met" if ok else "not_met", fact_key="conservative_treatment",
                evidence=dict(page=cons["page"], quote=cons["quote"]), note=f"{months:g} months documented."))

    gate = dict(complete=not questions, questions=list(questions.values()))
    not_met = [c for c in checklist if c["status"] == "not_met"]
    if questions:
        action = "pend"
        rationale = ("The packet is missing " + ", ".join(_label(q["fact"]) for q in questions.values()) +
                     ". Ask the provider for exactly that before judging the case.")
    elif not_met:
        action = "escalate"
        rationale = ("The packet is complete, but " + "; ".join(_short(c) for c in not_met) +
                     ". This needs a physician's clinical judgment, so it goes to a medical director.")
    else:
        action = "approve"
        rationale = "The packet is complete and every criterion is supported by the record."
    return dict(checklist=checklist, gate=gate, action=action, rationale=rationale,
                policies=[dict(id=p["id"], level=LEVEL_LABEL[p["level"]], title=p["title"], source=p["source"],
                               url=p["url"], verified=p["verified"]) for p in policies if p["criteria"]],
                cannot_deny=True)


def _label(key):
    return {"expected_los_days": "the expected length of stay", "comorbidities": "comorbidity documentation",
            "post_op_needs": "post-operative care needs", "indication_evidence": "imaging or exam evidence for the surgical indication",
            "conservative_treatment": "the conservative treatment history", "shared_decision_making": "shared decision making"}.get(key, key)


def _short(c):
    return {"LOC-1": "the expected stay does not cross 2 midnights", "LOC-2": "no risk factors are documented",
            "HUM-1": "no risk-raising comorbidities are documented", "HUM-2": "no post-operative needs beyond routine recovery are documented",
            "LCD-DEF-12M": "non-operative treatment was under 12 months",
            "LCD-IND": "no qualifying indication is documented", "LCD-CONS": "conservative treatment is not documented"}.get(c["criterion_id"], c["text"][:60])
