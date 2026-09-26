import sqlite3, json, os, hashlib, secrets, glob
from datetime import datetime, timedelta, timezone

ROOT = os.path.join(os.path.dirname(__file__), "..")
DB_PATH = os.path.join(os.path.dirname(__file__), "pa.db")

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


def init():
    c = conn()
    c.executescript(SCHEMA)
    if c.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        seed(c)
    c.commit()
    c.close()


def audit(c, case_id, user_id, action, detail="", at=None):
    c.execute("INSERT INTO audit(case_id,user_id,action,detail,created_at) VALUES(?,?,?,?,?)",
              (case_id, user_id, action, detail, at or now()))


def notify(c, user_id, case_id, body):
    c.execute("INSERT INTO notifications(user_id,case_id,body,created_at) VALUES(?,?,?,?)", (user_id, case_id, body, now()))


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
    audit(c, case_id, None, "received", f"Packet received ({len(elements)} elements, {engine} ingestion)", received)
    audit(c, case_id, None, "analyzed", f"Recommendation: {analysis['action']}", received)
    return case_id


def seed(c):
    from pipeline.run import process
    users = [
        ("maria.santos@humana-demo.test", "maria", "Maria Santos", "nurse", "UM Nurse"),
        ("james.okafor@humana-demo.test", "james", "James Okafor", "nurse", "UM Nurse"),
        ("priya.patel@humana-demo.test", "patel", "Dr. Priya Patel", "medical_director", "Medical Director"),
        ("alan.brooks@humana-demo.test", "brooks", "Dr. Alan Brooks", "medical_director", "Medical Director"),
    ]
    for email, handle, name, role, title in users:
        salt = secrets.token_hex(8)
        c.execute("INSERT INTO users(email,handle,name,role,title,salt,pw) VALUES(?,?,?,?,?,?,?)",
                  (email, handle, name, role, title, salt, hash_pw("demo1234", salt)))
    uid = {h: c.execute("SELECT id FROM users WHERE handle=?", (h,)).fetchone()[0] for h in ("maria", "james", "patel", "brooks")}

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
