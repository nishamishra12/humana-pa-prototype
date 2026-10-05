import sqlite3, json, os, hashlib, secrets, glob
from datetime import datetime, timedelta, timezone

ROOT = os.path.join(os.path.dirname(__file__), "..")
DATA_DIR = os.getenv("PA_DATA_DIR") or os.path.dirname(__file__)  # on a host, point this at the persistent disk
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, "pa.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, email TEXT UNIQUE, handle TEXT UNIQUE, name TEXT, role TEXT, title TEXT, salt TEXT, pw TEXT);
CREATE TABLE IF NOT EXISTS cases(
  id TEXT PRIMARY KEY, member_name TEXT, member_id TEXT, dob TEXT, age INTEGER, facility TEXT, procedure_name TEXT, cpt TEXT,
  setting TEXT, status TEXT, assignee_id INTEGER, md_id INTEGER, priority TEXT, received_at TEXT, due_at TEXT, decided_at TEXT,
  packet_file TEXT, engine TEXT, facts TEXT, analysis TEXT);
CREATE TABLE IF NOT EXISTS elements(id INTEGER PRIMARY KEY, case_id TEXT, page INTEGER, type TEXT, text TEXT);
CREATE TABLE IF NOT EXISTS comments(id INTEGER PRIMARY KEY, case_id TEXT, user_id INTEGER, kind TEXT, body TEXT, created_at TEXT);
CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY, case_id TEXT, user_id INTEGER, action TEXT, detail TEXT, created_at TEXT);
CREATE TABLE IF NOT EXISTS notifications(id INTEGER PRIMARY KEY, user_id INTEGER, case_id TEXT, body TEXT, read INTEGER DEFAULT 0, created_at TEXT);
"""


def now(offset_days=0.0):
    return (datetime.now(timezone.utc) + timedelta(days=offset_days)).isoformat(timespec="seconds")


def conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def hash_pw(pw, salt):
    return hashlib.pbkdf2_hmac("sha256", pw.encode(), salt.encode(), 60_000).hex()


POLICY_SCHEMA = """
CREATE TABLE IF NOT EXISTS policy_builds(id TEXT PRIMARY KEY, policy_id TEXT, kind TEXT, ident TEXT, service TEXT, status TEXT, stage TEXT, error TEXT,
  folder TEXT, version TEXT, created_by INTEGER, created_at TEXT, summary TEXT);
CREATE TABLE IF NOT EXISTS policy_decisions(build_id TEXT, criterion_id TEXT, decision TEXT, edited TEXT, decided_by INTEGER, decided_at TEXT, PRIMARY KEY(build_id, criterion_id));
CREATE TABLE IF NOT EXISTS policy_versions(n INTEGER PRIMARY KEY AUTOINCREMENT, library_version TEXT, kind TEXT, policy_id TEXT, build_id TEXT,
  published_by INTEGER, published_at TEXT, changelog TEXT, note TEXT);
CREATE TABLE IF NOT EXISTS cms_articles(document_id INTEGER, version INTEGER, display_id TEXT, title TEXT, mac TEXT, updated_on TEXT, codes_at TEXT, PRIMARY KEY(document_id, version));
CREATE TABLE IF NOT EXISTS cms_article_codes(document_id INTEGER, version INTEGER, code TEXT, description TEXT, short TEXT, grp INTEGER, PRIMARY KEY(document_id, version, code));
CREATE INDEX IF NOT EXISTS cms_article_codes_code ON cms_article_codes(code);
CREATE TABLE IF NOT EXISTS cms_meta(key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS policy_audit(id INTEGER PRIMARY KEY AUTOINCREMENT, at TEXT, user_id INTEGER, action TEXT, policy_id TEXT, build_id TEXT, detail TEXT);
"""


def ensure_policy_owner(c):
    """The policy owner is added to databases created before this role existed."""
    if c.execute("SELECT COUNT(*) FROM users WHERE role='policy_owner'").fetchone()[0] == 0:
        salt = secrets.token_hex(8)
        c.execute("INSERT INTO users(email,handle,name,role,title,salt,pw) VALUES(?,?,?,?,?,?,?)",
                  ("dana.whitfield@humana-demo.test", "dana", "Dana Whitfield", "policy_owner", "Policy Owner", salt, hash_pw("demo1234", salt)))


def init():
    c = conn()
    c.executescript(SCHEMA)
    c.execute("CREATE TABLE IF NOT EXISTS sessions(sid TEXT PRIMARY KEY, user_id INTEGER, created_at TEXT)")  # sign-ins survive a restart
    c.executescript(POLICY_SCHEMA)
    if c.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        seed(c)
    seed_multi(c)
    ensure_policy_owner(c)  # after seeding: an empty users table is what triggers the seed
    c.commit()
    c.close()


def audit(c, case_id, user_id, action, detail="", at=None):
    c.execute("INSERT INTO audit(case_id,user_id,action,detail,created_at) VALUES(?,?,?,?,?)",
              (case_id, user_id, action, detail, at or now()))
    try:  # one event per human action, so Honeycomb can show overrides and the time from recommendation to decision. No detail text: it can hold names.
        from pipeline import telemetry
        telemetry.event("case.human_action", **{"case.id": case_id, "case.action": action, "case.override": action == "approved_override"})
    except Exception:
        pass


def notify(c, user_id, case_id, body):
    c.execute("INSERT INTO notifications(user_id,case_id,body,created_at) VALUES(?,?,?,?)", (user_id, case_id, body, now()))


def sla_status(due_at, decided_at, priority):
    """ok | soon | breached while open; met | late_decided once decided."""
    if decided_at:
        return "met" if decided_at <= due_at else "late_decided"
    remaining_hours = (datetime.fromisoformat(due_at) - datetime.now(timezone.utc)).total_seconds() / 3600
    threshold = 24 if priority == "expedited" else 48
    if remaining_hours < 0:
        return "breached"
    if remaining_hours < threshold:
        return "soon"
    return "ok"


def raise_sla_alerts(c):
    """Checked whenever the inbox is listed (no background scheduler in this prototype):
    the first time a case is found soon-due or breached, log it once and notify the assignee."""
    open_ = ("new", "in_review", "pended", "escalated")
    for r in c.execute(f"SELECT * FROM cases WHERE status IN ({','.join('?' * len(open_))})", open_):
        st = sla_status(r["due_at"], None, r["priority"])
        if st not in ("soon", "breached"):
            continue
        marker = f"sla_{st}"
        if c.execute("SELECT 1 FROM audit WHERE case_id=? AND action=?", (r["id"], marker)).fetchone():
            continue
        clock = "72-hour expedited" if r["priority"] == "expedited" else "7-day standard"
        label = f"has passed its {clock} CMS decision clock" if st == "breached" else f"is within {24 if r['priority']=='expedited' else 48} hours of its {clock} CMS decision clock"
        audit(c, r["id"], None, marker, f"SLA alert: case {label}.")
        target = r["assignee_id"] or r["md_id"]
        if target:
            notify(c, target, r["id"], f"{r['id']} {'has breached' if st == 'breached' else 'is close to breaching'} the CMS decision clock")


def create_case(c, elements, engine, facts, analysis, packet_file, priority="standard", received_offset=0.0, case_id=None):
    n = c.execute("SELECT COUNT(*) FROM cases").fetchone()[0]
    case_id = case_id or f"PA-{1001 + n}"
    m = facts.get("_member", {})
    received = now(received_offset)
    due = (datetime.fromisoformat(received) + timedelta(hours=72 if priority == "expedited" else 24 * 7)).isoformat(timespec="seconds")
    c.execute("INSERT INTO cases VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
        case_id, m.get("name", "Unknown member"), m.get("member_id", "-"), m.get("dob"), m.get("age"), facts.get("_facility") or "-",
        facts.get("_procedure") or "-", facts.get("_cpt"), facts.get("_setting") or "inpatient",
        "new", None, None, priority, received, due, None, packet_file, engine, json.dumps(facts), json.dumps(analysis)))
    for e in elements:
        c.execute("INSERT INTO elements(case_id,page,type,text) VALUES(?,?,?,?)", (case_id, e.page, e.type, e.text))
    audit(c, case_id, None, "received", f"Packet received ({len({e.page for e in elements})} pages)", received)
    audit(c, case_id, None, "analyzed", f"Recommendation: {analysis['action']}", received)
    return case_id


def seed(c):
    from pipeline.run import process
    users = [
        ("carla.mendez@humana-demo.test", "carla", "Carla Mendez", "admin", "Intake Coordinator"),
        ("maria.santos@humana-demo.test", "maria", "Maria Santos", "nurse", "UM Nurse"),
        ("james.okafor@humana-demo.test", "james", "James Okafor", "nurse", "UM Nurse"),
        ("priya.patel@humana-demo.test", "patel", "Dr. Priya Patel", "medical_director", "Medical Director"),
        ("alan.brooks@humana-demo.test", "brooks", "Dr. Alan Brooks", "medical_director", "Medical Director"),
    ]
    for email, handle, name, role, title in users:
        salt = secrets.token_hex(8)
        c.execute("INSERT INTO users(email,handle,name,role,title,salt,pw) VALUES(?,?,?,?,?,?,?)",
                  (email, handle, name, role, title, salt, hash_pw("demo1234", salt)))
    uid = {h: c.execute("SELECT id FROM users WHERE handle=?", (h,)).fetchone()[0] for h in ("carla", "maria", "james", "patel", "brooks")}

    plan = [  # file, offset days, priority, status, assignee
        ("p06_deformity_meets.pdf", -5.0, "standard", "approved", "james"),
        ("p03_missing_imaging.pdf", -3.0, "standard", "pended", "maria"),
        ("p04_short_stay_low_risk.pdf", -2.0, "standard", "escalated", "maria"),
        ("p02_john_doe_missing_los.pdf", -1.0, "standard", "new", "maria"),
        ("p01_complete_degenerative.pdf", -0.5, "standard", "new", "maria"),
        ("p05_missing_two_items.pdf", -0.3, "expedited", "new", "james"),
    ]
    for f, off, pr, status, who in plan:
        els, eng, facts, res = process(os.path.join(ROOT, "packets", f), local=True)
        cid = create_case(c, els, eng, facts, res, f, pr, off)
        c.execute("UPDATE cases SET assignee_id=? WHERE id=?", (uid[who], cid))
        audit(c, cid, None, "assigned", f"Assigned to {who}", now(off))
        if status == "approved":
            c.execute("UPDATE cases SET status='approved', decided_at=? WHERE id=?", (now(off + 0.2), cid))
            audit(c, cid, uid[who], "approved", "Approved. Matched the recommendation.", now(off + 0.2))
        elif status == "pended":
            q = res["gate"]["questions"][0]["question"]
            c.execute("UPDATE cases SET status='pended' WHERE id=?", (cid,))
            c.execute("INSERT INTO comments(case_id,user_id,kind,body,created_at) VALUES(?,?,?,?,?)",
                      (cid, uid[who], "provider_request", q, now(off + 0.1)))
            audit(c, cid, uid[who], "pended", "Sent one specific question to the provider", now(off + 0.1))
        elif status == "escalated":
            c.execute("UPDATE cases SET status='escalated', md_id=? WHERE id=?", (uid["patel"], cid))
            c.execute("INSERT INTO comments(case_id,user_id,kind,body,created_at) VALUES(?,?,?,?,?)",
                      (cid, uid[who], "escalation", "@patel packet is complete but the stay is 1 midnight and there are no documented risk factors. Can you make the level-of-care call?", now(off + 0.2)))
            notify(c, uid["patel"], cid, "Maria Santos escalated this case and tagged you")
            audit(c, cid, uid[who], "escalated", "Escalated to Dr. Priya Patel", now(off + 0.2))

    # SLA alerting demo: left unactioned on purpose, so these show up at-risk / breached.
    # -7.5d standard (due at 7d) => already past the clock. -2.6d expedited (due at 72h) => due soon.
    for f, off, pr in (("s01_breached_demo.pdf", -7.5, "standard"), ("s02_soon_demo.pdf", -2.6, "expedited")):
        els, eng, facts, res = process(os.path.join(ROOT, "packets", f), local=True)
        cid = create_case(c, els, eng, facts, res, f, pr, off)
        c.execute("UPDATE cases SET assignee_id=? WHERE id=?", (uid["maria"], cid))
        audit(c, cid, None, "assigned", "Assigned to maria", now(off))

MULTI_PLAN = [  # fixture, offset days, priority, assignee. New cases for the other illnesses, left for the nurse to work.
    ("icd1_complete_nonischemic", -0.9, "standard", "maria"),
    ("icd3_conflicting_lvef", -0.6, "standard", "james"),
    ("icd5_recent_mi", -0.4, "standard", "maria"),
    ("bar1_complete", -0.7, "standard", "james"),
    ("bar3_bmi_changed", -0.2, "expedited", "maria"),
]


def seed_multi(c):
    """Adds the ICD and bariatric demo cases from packets/fixtures/ (built by scripts/build_fixtures.py).
    Safe to run on every start: a case is added only once. Skipped quietly if the fixtures are not built."""
    from pipeline.ingest import Element
    from pipeline.engine import analyze
    fx = os.path.join(ROOT, "packets", "fixtures")
    uid = {r["handle"]: r["id"] for r in c.execute("SELECT id, handle FROM users")}
    if not uid:
        return
    for name, off, pr, who in MULTI_PLAN:
        path = os.path.join(fx, name + ".json")
        if not os.path.exists(path) or c.execute("SELECT 1 FROM cases WHERE packet_file=?", (name + ".pdf",)).fetchone():
            continue
        d = json.load(open(path, encoding="utf-8"))
        els = [Element(page=e["page"], type=e["type"], text=e["text"]) for e in d["elements"]]
        cid = create_case(c, els, d["engine"], d["facts"], analyze(d["facts"]), d["file"], pr, off)
        c.execute("UPDATE cases SET assignee_id=? WHERE id=?", (uid[who], cid))
        audit(c, cid, None, "assigned", f"Assigned to {who}", now(off))
