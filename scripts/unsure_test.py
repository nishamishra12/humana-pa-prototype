"""Checks the 'AI is not sure' state and the nurse correction buttons on a throwaway database."""
import os, json, tempfile
from app import db
db.DB_PATH = os.path.join(tempfile.mkdtemp(), "t.db")
from fastapi.testclient import TestClient
from app.main import app
from pipeline.engine import analyze


def cl(email):
    t = TestClient(app)
    assert t.post("/api/login", json={"email": email, "password": "demo1234"}).status_code == 200
    return t


maria, james, admin = cl("maria.santos@humana-demo.test"), cl("james.okafor@humana-demo.test"), cl("carla.mendez@humana-demo.test")

# 1. Unsure never turns into a provider question
c = db.conn()
row = c.execute("SELECT * FROM cases WHERE id='PA-1005'").fetchone()
facts = json.loads(row["facts"])
facts["indication_evidence"] = dict(status="unsure", value=None, page=None, quote=None,
                                    note="The AI read this 3 times and gave different answers (found, found, implied). Check the packet.")
res = analyze(facts)
print("1a. action is 'verify':", res["action"] == "verify")
print("1b. no provider question drafted:", res["gate"]["questions"] == [], "| unsure:", [u["fact"] for u in res["gate"]["unsure"]])
print("1c. rationale:", res["rationale"])
c.execute("UPDATE cases SET facts=?, analysis=? WHERE id='PA-1005'", (json.dumps(facts), json.dumps(res)))
c.commit()
row = next(r for r in maria.get("/api/cases?view=attention").json()["cases"] if r["id"] == "PA-1005")
print("1d. list shows it:", row["ai_action"], "unsure count:", row["ai_unsure"])

# 2. Nurse resolves it: found
r = maria.post("/api/cases/PA-1005/facts/indication_evidence", json={"kind": "found", "value": "instability", "page": 3})
d = r.json()
print("2a. nurse says 'in the packet' ->", r.status_code, "| action now:", d["analysis"]["action"], "| fact:", d["facts"]["indication_evidence"]["status"])
print("2b. correction is logged:", any(a["action"] == "fact_corrected" for a in d["audit"]), "| saved on the case:", d["facts"]["_corrections"][-1])

# 3. Nurse says it is really missing -> normal pend with a question
r = maria.post("/api/cases/PA-1005/facts/indication_evidence", json={"kind": "missing"})
d = r.json()
print("3. nurse confirms missing -> action:", d["analysis"]["action"], "| question drafted:", bool(d["analysis"]["gate"]["questions"]))

# 4. AI said missing, nurse finds it (a false 'missing' the metrics need)
r = maria.post("/api/cases/PA-1004/facts/expected_los_days", json={"kind": "found", "value": "3"})
d = r.json()
print("4. John Doe: nurse enters 3 midnights -> action:", d["analysis"]["action"], "| correction:", d["facts"]["_corrections"][-1]["was"], "->", d["facts"]["_corrections"][-1]["now"])

# 5. Guards
print("5a. admin blocked:", admin.post("/api/cases/PA-1004/facts/expected_los_days", json={"kind": "found", "value": "3"}).status_code == 403)
print("5b. another nurse sees nothing:", james.post("/api/cases/PA-1004/facts/expected_los_days", json={"kind": "found", "value": "3"}).status_code == 404)
print("5c. bad number rejected:", maria.post("/api/cases/PA-1004/facts/expected_los_days", json={"kind": "found", "value": "three"}).status_code == 400)
print("5d. bad indication rejected:", maria.post("/api/cases/PA-1005/facts/indication_evidence", json={"kind": "found", "value": "tired"}).status_code == 400)
print("5e. unknown fact rejected:", maria.post("/api/cases/PA-1004/facts/shoe_size", json={"kind": "found", "value": "9"}).status_code == 404)
print("5f. 'none' only where it makes sense:", maria.post("/api/cases/PA-1004/facts/expected_los_days", json={"kind": "none"}).status_code == 400)
print("ALL UNSURE CHECKS RAN")
