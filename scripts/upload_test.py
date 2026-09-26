import os, tempfile
from app import db
db.DB_PATH = os.path.join(tempfile.mkdtemp(), "t.db")
from fastapi.testclient import TestClient
from app.main import app
t = TestClient(app)
t.post("/api/login", json={"email": "maria.santos@humana-demo.test", "password": "demo1234"})
with open("packets/p03_missing_imaging.pdf", "rb") as f:
    r = t.post("/api/cases", files={"file": ("new_packet.pdf", f, "application/pdf")})
d = r.json()
print(r.status_code, d.get("id"), "| engine:", d.get("engine"), "| member:", d.get("member_name"), "| action:", d["analysis"]["action"], "| missing:", [q["fact"] for q in d["analysis"]["gate"]["questions"]])
r = t.post("/api/cases", files={"file": ("notes.txt", b"hello", "text/plain")}); print("non-pdf ->", r.status_code, r.json()["detail"])
