"""Builds docs/dashboard.html: an executive view and a utilization management view, from the app's own case data (app/pa.db).

Everything on the page is computed here from the cases and the audit trail. No patient names go on the page, only case ids.
Re-run after you decide cases in the app, then publish docs/dashboard.html again:
    python scripts/export_dashboard_data.py
In production the same two views are SQL over the warehouse (see docs/dashboard_views.sql).
"""
import json, os, sqlite3
from datetime import datetime, timezone

ROOT = os.path.join(os.path.dirname(__file__), "..")
c = sqlite3.connect(os.path.join(ROOT, "app", "pa.db"))
c.row_factory = sqlite3.Row
now = datetime.now(timezone.utc)
users = {r["id"]: dict(name=r["name"], role=r["role"]) for r in c.execute("SELECT id,name,role FROM users")}
t = lambda s: datetime.fromisoformat(s) if s else None
hrs = lambda a, b: round((b - a).total_seconds() / 3600, 1)

cases, audit_by_case = [], {}
for r in c.execute("SELECT * FROM audit ORDER BY id"):
    audit_by_case.setdefault(r["case_id"], []).append(dict(action=r["action"], user_id=r["user_id"], detail=r["detail"] or "", at=r["created_at"]))
for r in c.execute("SELECT id,status,priority,received_at,due_at,decided_at,assignee_id,md_id,analysis FROM cases"):
    a = json.loads(r["analysis"])["action"]
    aud = audit_by_case.get(r["id"], [])
    cases.append(dict(id=r["id"], status=r["status"], priority=r["priority"], received=t(r["received_at"]), due=t(r["due_at"]), decided=t(r["decided_at"]),
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
acts = []
for x in cases:
    for e in x["audit"]:
        if e["action"] in ("approved", "approved_override", "pended", "escalated"):
            human_flag = e["action"] != "approved" and e["action"] != "approved_override"
            acts.append(dict(case=x["id"], user=e["user_id"], override=e["action"] == "approved_override", agree=human_flag == x["at_risk"]))
returned = [e for x in cases for e in x["returned"]]
avoidable_return = [e for e in returned if e["detail"].startswith("The packet already has what we need")]
escalations = sum(1 for x in cases for e in x["audit"] if e["action"] == "escalated")

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
data = dict(generated=now.strftime("%Y-%m-%d %H:%M UTC"), n=n, exec=exec_, um=um)

TEMPLATE = open(os.path.join(os.path.dirname(__file__), "dashboard_template.html"), encoding="utf-8").read()
html = TEMPLATE.replace("__DATA__", json.dumps(data).replace("</", "<\\/"))
out = os.path.join(ROOT, "docs", "dashboard.html")
with open(out, "w", encoding="utf-8", newline="\n") as f:
    f.write(html)
print("wrote", out, "|", n, "cases |", len(decided), "decided |", len(acts), "human actions")
