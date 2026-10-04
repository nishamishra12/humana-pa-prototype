"""Checks the backend pieces behind the redesign: original PDF, upload progress, return reasons."""
import os, tempfile
from app import db
db.DB_PATH = os.path.join(tempfile.mkdtemp(), "t.db")
from fastapi.testclient import TestClient
from app.main import app


def cl(email):
    t = TestClient(app)
    assert t.post("/api/login", json={"email": email, "password": "demo1234"}).status_code == 200
    return t


admin, maria, james, patel = (cl(f"{n}@humana-demo.test") for n in ("carla.mendez", "maria.santos", "james.okafor", "priya.patel"))

r = maria.get("/api/cases/PA-1005/pdf")
print("1a. nurse reads her own original PDF:", r.status_code == 200 and r.content[:4] == b"%PDF")
print("1b. another nurse gets 404:", james.get("/api/cases/PA-1005/pdf").status_code == 404)
print("1c. admin can open it:", admin.get("/api/cases/PA-1005/pdf").status_code == 200)

with open("packets/p01_complete_degenerative.pdf", "rb") as f:
    d = admin.post("/api/cases", files={"file": ("a.pdf", f, "application/pdf")}, data={"job": "abc123"}).json()
j = admin.get("/api/jobs/abc123").json()
print("2a. upload job reports done:", j.get("stage") == "done" and j.get("case_id") == d["id"])
print("2b. unknown job says waiting:", admin.get("/api/jobs/nope").json()["stage"] == "waiting")
print("2c. uploaded file is served:", admin.get(f"/api/cases/{d['id']}/pdf").status_code == 200)
print("2d. audit says pages, not elements:", "pages" in d["audit"][0]["detail"] and "element" not in d["audit"][0]["detail"])

c = db.conn(); mid = c.execute("SELECT id FROM users WHERE handle='patel'").fetchone()[0]
r = maria.post("/api/cases/PA-1004/action", json={"action": "escalate", "md_id": mid, "note": "Please decide."})
print("3a. escalate:", r.status_code)
r = patel.post("/api/cases/PA-1004/action", json={"action": "return", "reason": "bogus"})
print("3b. bad reason rejected:", r.status_code == 400)
r = patel.post("/api/cases/PA-1004/action", json={"action": "return"})
print("3c. return with no reason or note rejected:", r.status_code == 400)
r = patel.post("/api/cases/PA-1004/action", json={"action": "return", "reason": "info_enough", "note": "See page 2."})
d = r.json()
print("3d. return with a reason:", r.status_code == 200 and d["status"] == "in_review", "|", [a["detail"] for a in d["audit"] if a["action"] == "returned"][0])
print("ALL REDESIGN CHECKS RAN")
