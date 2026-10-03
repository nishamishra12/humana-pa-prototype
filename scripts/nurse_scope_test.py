import os, tempfile
from app import db
db.DB_PATH = os.path.join(tempfile.mkdtemp(), "t.db")
from fastapi.testclient import TestClient
from app.main import app

def client(email):
    t = TestClient(app); r = t.post("/api/login", json={"email": email, "password": "demo1234"}); assert r.status_code == 200; return t

maria, james = client("maria.santos@humana-demo.test"), client("james.okafor@humana-demo.test")
admin, md = client("carla.mendez@humana-demo.test"), client("priya.patel@humana-demo.test")

def ids(t, view="all"): return sorted(c["id"] for c in t.get(f"/api/cases?view={view}").json()["cases"])
allc = ids(admin)
mine_m, mine_j = ids(maria), ids(james)
print("admin sees:", len(allc), "| maria:", mine_m, "| james:", mine_j)
assert set(mine_m).isdisjoint(mine_j) and len(mine_m) + len(mine_j) < len(allc) + 1
assert all(c in allc for c in mine_m + mine_j)
# a nurse's own 'all' view is already scoped
assert ids(maria, "all") == mine_m and ids(maria, "pended") == [c for c in ids(maria, "pended") if c in mine_m]
# counts are scoped too
cnt = maria.get("/api/cases?view=all").json()["counts"]; print("maria counts:", cnt); assert cnt["all"] == len(mine_m)
# deep links to James's case: every endpoint 404s for Maria
theirs = mine_j[0]
for method, path, body in [("get", f"/api/cases/{theirs}", None), ("get", f"/api/cases/{theirs}/export", None),
                           ("post", f"/api/cases/{theirs}/comments", {"body": "x"}), ("post", f"/api/cases/{theirs}/assign", {"user_id": 2}),
                           ("post", f"/api/cases/{theirs}/action", {"action": "approve", "note": "x"}),
                           ("post", f"/api/cases/{theirs}/addendum", {"text": "x"})]:
    r = getattr(maria, method)(path, **({"json": body} if body else {}))
    print(f"  maria {method.upper()} {path.split('/api')[1]} ->", r.status_code); assert r.status_code == 404
# her own case still works end to end
own = mine_m[0]; assert maria.get(f"/api/cases/{own}").status_code == 200 and maria.get(f"/api/cases/{own}/export").status_code == 200
# search cannot reach other nurses' cases
name = admin.get(f"/api/cases").json()["cases"]
jn = next(c["member_name"] for c in name if c["id"] == theirs)
assert maria.get(f"/api/cases?view=all&q={jn.split()[0]}").json()["cases"] == []
# admin and MD unaffected
assert ids(md) == allc and admin.get(f"/api/cases/{theirs}").status_code == 200 and md.get(f"/api/cases/{theirs}").status_code == 200
print("ALL SCOPE CHECKS PASSED")
