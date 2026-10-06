"""The numbers behind the executive and utilization management dashboards, computed live from the case data.
No patient names: only case ids and staff names. Used by the /api/dashboard route and by scripts/export_dashboard_data.py."""
import json
from datetime import datetime, timezone


def compute(c):
    now = datetime.now(timezone.utc)
    users = {r["id"]: dict(name=r["name"], role=r["role"]) for r in c.execute("SELECT id,name,role FROM users")}
    t = lambda s: datetime.fromisoformat(s) if s else None
    hrs = lambda a, b: round((b - a).total_seconds() / 3600, 1)

    cases, audit_by_case = [], {}
    for r in c.execute("SELECT * FROM audit ORDER BY id"):
        audit_by_case.setdefault(r["case_id"], []).append(dict(action=r["action"], user_id=r["user_id"], detail=r["detail"] or "", at=r["created_at"]))
    for r in c.execute("SELECT id,status,priority,received_at,due_at,decided_at,assignee_id,md_id,analysis,cpt,procedure_name FROM cases"):
        a = json.loads(r["analysis"])["action"]
        aud = audit_by_case.get(r["id"], [])
        cases.append(dict(id=r["id"], cpt=r["cpt"], what=r["procedure_name"], status=r["status"], priority=r["priority"], received=t(r["received_at"]), due=t(r["due_at"]), decided=t(r["decided_at"]),
                          assignee=r["assignee_id"], md=r["md_id"], ai=a, at_risk=a != "approve", audit=aud,
                          pended=any(x["action"] == "pended" for x in aud), returned=[x for x in aud if x["action"] == "returned"]))
    n = len(cases)
    decided = [x for x in cases if x["status"] in ("approved", "denied")]
    open_ = [x for x in cases if x["status"] not in ("approved", "denied")]
    overdue = [x for x in open_ if x["due"] and x["due"] < now]
    due_soon = [x for x in open_ if x["due"] and 0 <= (x["due"] - now).total_seconds() < 24 * 3600]
    within = [x for x in decided if x["due"] and x["decided"] and x["decided"] <= x["due"]]
    tt = [hrs(x["received"], x["decided"]) for x in decided if x["decided"]]
    pct = lambda a, b: round(100 * a / b) if b else None

    # human actions on the AI's recommendation: agree = both approve, or both send to a person
    # one result per case: the nurse's first action. A case sent back and escalated twice counts once.
    nurse_ids = {uid for uid, u in users.items() if u["role"] == "nurse"}
    acts = []
    for x in cases:
        if x["ai"] == "no_policy":
            continue
        first = next((e for e in x["audit"] if e["action"] in ("approved", "approved_override", "pended", "escalated") and e["user_id"] in nurse_ids), None)
        if first:
            human_flag = first["action"] in ("pended", "escalated")
            acts.append(dict(case=x["id"], user=first["user_id"], cpt=x["cpt"], override=first["action"] == "approved_override", agree=human_flag == x["at_risk"], ai_flag=x["at_risk"], human_flag=human_flag,
                             missed=human_flag and not x["at_risk"], extra=x["at_risk"] and not human_flag))
    returned = [e for x in cases for e in x["returned"]]
    avoidable_return = [e for e in returned if e["detail"].startswith("The packet already has what we need")]
    escalations = sum(1 for x in cases for e in x["audit"] if e["action"] == "escalated")
    replies = [e for x in cases for e in x["audit"] if e["action"] == "provider_reply"]
    typed = [e for e in replies if "already sent" in e["detail"] or "new information" in e["detail"]]
    avoidable_pends = [e for e in typed if "already sent" in e["detail"]]

    status_order = [("new", "Not started"), ("in_review", "In review with a nurse"), ("pended", "Waiting on the provider"), ("escalated", "With a medical director"),
                    ("approved", "Approved"), ("denied", "Denied")]
    exec_ = dict(
        total=n, at_risk=sum(x["at_risk"] for x in cases), clean=sum(not x["at_risk"] for x in cases),
        by_status=[dict(label=lab, n=sum(1 for x in cases if x["status"] == k)) for k, lab in status_order],
        risk_split=[dict(label=lab, n=sum(1 for x in cases if x["ai"] == k)) for k, lab in
                    [("approve", "AI says approve (not at risk)"), ("pend", "AI says pend: something is missing"), ("escalate", "AI says escalate: a rule is not met"),
                     ("verify", "AI says verify: unclear, a person decides"), ("no_policy", "No policy for this service")]],
        pended=sum(1 for x in cases if x["status"] == "pended"), with_md=sum(1 for x in cases if x["status"] == "escalated"),
        approved=sum(1 for x in cases if x["status"] == "approved"), denied=sum(1 for x in cases if x["status"] == "denied"),
        avg_hours=round(sum(tt) / len(tt), 1) if tt else None, decided=len(decided),
        within_deadline=pct(len(within), len(decided)), overdue=len(overdue), due_soon=len(due_soon),
        first_review_rate=pct(sum(1 for x in decided if not x["pended"]), len(decided)),
        agree_rate=pct(sum(a["agree"] for a in acts), len(acts)), n_actions=len(acts), overrides=sum(a["override"] for a in acts),
        avoidable_escalations=len(avoidable_return), returns=len(returned), escalations=escalations,
        replies=len(typed), avoidable_pends=len(avoidable_pends),
    )

    def aging(items):
        b = [("Under 1 day", 0, 1), ("1 to 3 days", 1, 3), ("3 to 5 days", 3, 5), ("5 days or more", 5, 999)]
        return [dict(label=l, n=sum(1 for x in items if lo <= (now - x["received"]).total_seconds() / 86400 < hi)) for l, lo, hi in b]

    unassigned = [x for x in cases if x["assignee"] is None and x["status"] not in ("approved", "denied")]
    nurses = []
    for uid, u in users.items():
        if u["role"] != "nurse":
            continue
        mine = [x for x in cases if x["assignee"] == uid]
        mo = [x for x in mine if x["status"] not in ("approved", "denied")]
        md_ = [x for x in mine if x["status"] in ("approved", "denied")]
        mt = [hrs(x["received"], x["decided"]) for x in md_ if x["decided"]]
        ov = sum(1 for a in acts if a["user"] == uid and a["override"])
        nurses.append(dict(name=u["name"], assigned=len(mine), open=len(mo), at_risk_open=sum(x["at_risk"] for x in mo), overdue=sum(1 for x in mo if x["due"] and x["due"] < now),
                           pended=sum(1 for x in mo if x["status"] == "pended"), escalated=sum(1 for x in mo if x["status"] == "escalated"),
                           decided=len(md_), avg_hours=round(sum(mt) / len(mt), 1) if mt else None, overrides=ov))
    directors = []
    for uid, u in users.items():
        if u["role"] != "medical_director":
            continue
        waiting = [x for x in cases if x["md"] == uid and x["status"] == "escalated"]
        dec = sum(1 for x in cases for e in x["audit"] if e["user_id"] == uid and e["action"] in ("approved", "approved_override", "denied"))
        ret = sum(1 for e in returned if e["user_id"] == uid)
        directors.append(dict(name=u["name"], waiting=len(waiting), oldest_days=round(max((now - x["received"]).total_seconds() / 86400 for x in waiting), 1) if waiting else None,
                              decided=dec, returned=ret))
    um = dict(unassigned=len(unassigned), oldest_unassigned_days=round(max(((now - x["received"]).total_seconds() / 86400 for x in unassigned), default=0), 1),
              aging=aging(open_), nurses=nurses, directors=directors, open=len(open_), overdue=len(overdue), due_soon=len(due_soon),
              at_risk_open=sum(x["at_risk"] for x in open_))
    # ---- what an executive can act on: capacity, which service next, owner review, pilot services
    from pipeline import procedures
    lib = procedures.library()
    services = []
    for key, p in lib["procedures"].items():
        codes = set(p["cpts"])
        mine = [x for x in cases if x["cpt"] in codes and x["ai"] != "no_policy"]
        a = [t for t in acts if t["cpt"] in codes]
        services.append(dict(key=key, name=p["short"], status=p.get("status", "live"), cases=len(mine), decided=sum(1 for x in mine if x["status"] in ("approved", "denied")),
                             flagged=pct(sum(1 for x in mine if x["at_risk"]), len(mine)), reviews=len(a), agree=pct(sum(t["agree"] for t in a), len(a)),
                             missed=sum(t["missed"] for t in a), extra=sum(t["extra"] for t in a)))
    groups = {}
    for x in open_:
        if x["ai"] == "no_policy":
            g = groups.setdefault(x["cpt"] or "unknown", dict(code=x["cpt"] or "unknown", what=x["what"], n=0, oldest=x["received"]))
            g["n"] += 1
            g["oldest"] = min(g["oldest"], x["received"])
    demand = sorted(groups.values(), key=lambda g: (-g["n"], g["oldest"]))
    for g in demand:
        g["oldest_days"] = round((now - g["oldest"]).total_seconds() / 86400, 1)
        del g["oldest"]
    try:
        drafts = c.execute("SELECT COUNT(*) FROM policy_builds WHERE status='draft' AND kind != 'earlier run'").fetchone()[0]
    except Exception:
        drafts = 0
    exec_["services"] = services
    exec_["decisions"] = dict(
        capacity=dict(overdue=len(overdue), due_soon=len(due_soon), open=len(open_), unassigned=um["unassigned"], oldest_unassigned_days=um["oldest_unassigned_days"]),
        demand=dict(total=sum(g["n"] for g in demand), codes=demand[:4]),
        owner=dict(drafts=drafts, version=lib.get("version")),
        pilots=[s for s in services if s["status"] == "pilot"])
    # ---- model efficiency: how the AI's work holds up against the two people who check it
    p1 = lambda a, b: round(100 * a / b, 1) if b else None
    tp = sum(1 for a in acts if a["human_flag"] and a["ai_flag"])
    fn = sum(1 for a in acts if a["human_flag"] and not a["ai_flag"])   # the AI approved, the nurse sent it on
    fp = sum(1 for a in acts if a["ai_flag"] and not a["human_flag"])   # the AI flagged, the nurse approved
    tn = sum(1 for a in acts if not a["ai_flag"] and not a["human_flag"])
    nurse_eff = dict(reviews=len(acts), ai_approved=fn + tn, wrong_approvals=fn, wrong_approvals_pct=p1(fn, fn + tn), ai_flagged=tp + fp, false_alarms=fp, false_alarms_pct=p1(fp, tp + fp),
                     recall=p1(tp, tp + fn), precision=p1(tp, tp + fp))
    try:
        approved = rejected = edited = 0
        for r in c.execute("SELECT d.decision, d.edited FROM policy_decisions d JOIN policy_builds b ON b.id=d.build_id WHERE b.status='published'"):
            if r["decision"] == "approved":
                approved += 1
                edited += 1 if r["edited"] else 0
            elif r["decision"] == "rejected":
                rejected += 1
        policies = c.execute("SELECT COUNT(*) FROM policy_builds WHERE status='published'").fetchone()[0]
    except Exception:
        approved = rejected = edited = policies = 0
    owner_eff = dict(policies=policies, drafted=approved + rejected, approved=approved, rejected=rejected, edited=edited,
                     precision=p1(approved, approved + rejected), edit_rate=p1(edited, approved))
    return dict(generated=now.strftime("%Y-%m-%d %H:%M UTC"), n=n, exec=exec_, um=um, eff=dict(owner=owner_eff, nurse=nurse_eff))

