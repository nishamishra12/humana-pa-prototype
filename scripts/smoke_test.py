from fastapi.testclient import TestClient
from app.main import app
t = TestClient(app)
t.post("/api/login", json={"email": "maria.santos@humana-demo.test", "password": "demo1234"})
cs = t.get("/api/cases").json()["cases"]
print([(x["id"], x["member_name"], x["status"], x["ai_action"]) for x in cs])
hero = next(x for x in cs if x["member_name"] == "John Doe")["id"]
print("hero", hero)
r = t.post(f"/api/cases/{hero}/action", json={"action": "deny", "note": "x"}); print("nurse deny ->", r.status_code, r.json()["detail"])
r = t.post(f"/api/cases/{hero}/action", json={"action": "approve"}); print("approve w/o reason ->", r.status_code, r.json()["detail"])
d = t.post(f"/api/cases/{hero}/addendum", json={"text": "Surgeon addendum: Expected length of stay: 3 midnights."}).json()
print("after addendum:", d["status"], d["analysis"]["action"], "missing:", [q["fact"] for q in d["analysis"]["gate"]["questions"]])
r = t.post(f"/api/cases/{hero}/action", json={"action": "approve"}); print("approve ->", r.status_code, r.json()["status"])
t2 = TestClient(app); t2.post("/api/login", json={"email": "priya.patel@humana-demo.test", "password": "demo1234"})
print("MD inbox:", [(x["id"], x["status"]) for x in t2.get("/api/cases?view=mine").json()["cases"]], "| notifications:", [n["body"] for n in t2.get("/api/notifications").json()])
esc = t2.get("/api/cases?view=escalated").json()["cases"][0]["id"]
print("MD deny w/o rationale ->", t2.post(f"/api/cases/{esc}/action", json={"action": "deny"}).status_code)
print("MD deny with rationale ->", t2.post(f"/api/cases/{esc}/action", json={"action": "deny", "note": "1-midnight stay, no risk factors, outpatient appropriate"}).json()["status"])
r = t2.get("/api/evals").json(); print("evals", r["passed"], "/", r["total"], "zero denials:", r["zero_denials"])
