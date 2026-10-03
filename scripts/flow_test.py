"""Checks the flow fixes from docs/UX_CRITIQUE.md on a throwaway database."""
import os, tempfile
from app import db
db.DB_PATH = os.path.join(tempfile.mkdtemp(), "t.db")
from fastapi.testclient import TestClient
from app.main import app


def cl(email):
    t = TestClient(app)
    assert t.post("/api/login", json={"email": email, "password": "demo1234"}).status_code == 200
    return t


admin, maria, james = cl("carla.mendez@humana-demo.test"), cl("maria.santos@humana-demo.test"), cl("james.okafor@humana-demo.test")
patel = cl("priya.patel@humana-demo.test")
uid = {u["handle"]: u["id"] for u in admin.get("/api/users").json()}


def notes(t):
    return [n["body"] for n in t.get("/api/notifications").json()]


# 1. handoff notifications
before = len(notes(maria))
with open("packets/p01_complete_degenerative.pdf", "rb") as f:
    cid = admin.post("/api/cases", files={"file": ("a.pdf", f, "application/pdf")}).json()["id"]
admin.post(f"/api/cases/{cid}/assign", json={"user_id": uid["maria"]})
n = notes(maria)
print("1a. assign notifies the nurse:", len(n) == before + 1 and "assigned" in n[0], "|", n[0])
admin.post(f"/api/cases/{cid}/assign", json={"user_id": uid["maria"]})
print("1b. assigning to the same nurse again does not notify twice:", len(notes(maria)) == before + 1)

before = len(notes(maria))
maria.post("/api/cases/PA-1002/addendum", json={"text": "Flexion-extension radiographs show dynamic instability at L3-L4."})
n = notes(maria)
print("1c. provider reply notifies the nurse:", len(n) == before + 1, "|", n[0])
row = next(c for c in maria.get("/api/cases?view=attention").json()["cases"] if c["id"] == "PA-1002")
print("1d. list says 'provider_reply':", row["last_event"] == "provider_reply")

before = len(notes(maria))
patel.post("/api/cases/PA-1003/action", json={"action": "approve", "note": "Reviewed, approve."})
n = notes(maria)
print("1e. director decision notifies the nurse:", len(n) == before + 1, "|", n[0])

# 2. urgency order: breached first, then least time left
rows = maria.get("/api/cases?view=attention").json()["cases"]
due = [r["due_at"] for r in rows]
print("2. attention queue sorted by least time left:", due == sorted(due), "| first:", rows[0]["member_name"], rows[0]["sla"])

# 3. director home
rows = patel.get("/api/cases?view=decide").json()
print("3. director 'decide' view is only escalated cases for her:", all(r["status"] == "escalated" for r in rows["cases"]), "| count:", rows["counts"]["decide"])
patel2 = patel.get("/api/cases?view=decide").json()["counts"]["decide"]

# 4. directors cannot upload
with open("packets/p01_complete_degenerative.pdf", "rb") as f:
    r = patel.post("/api/cases", files={"file": ("a.pdf", f, "application/pdf")})
print("4. director upload blocked:", r.status_code == 403, "|", r.json().get("detail"))
print("ALL FLOW CHECKS RAN")
