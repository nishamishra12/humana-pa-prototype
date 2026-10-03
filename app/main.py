import json, os, re, secrets, shutil
from fastapi import FastAPI, Form, HTTPException, Request, Response, UploadFile, File
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import db
from pipeline.ingest import Element
from pipeline.extract import extract_facts
from pipeline.engine import analyze
from pipeline.run import process

ROOT = os.path.join(os.path.dirname(__file__), "..")
UPLOADS = os.path.join(ROOT, "uploads")
os.makedirs(UPLOADS, exist_ok=True)
db.init()

app = FastAPI(title="PA Decision Support")
SESSIONS: dict[str, int] = {}


@app.middleware("http")
async def no_cache_static(request: Request, call_next):
    """This is a prototype under active edit: never let the browser cache web/* so a
    reload always shows the latest app.js/style.css instead of a stale cached copy."""
    response = await call_next(request)
    if not request.url.path.startswith("/api"):
        response.headers["Cache-Control"] = "no-store"
    return response


def me(request: Request, c):
    sid = request.cookies.get("sid")
    uid = SESSIONS.get(sid or "")
    if not uid:
        raise HTTPException(401, "Sign in required")
    return c.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()


def check_case_access(c, u, cid):
    """A nurse works only her own cases. Another nurse's case answers the same 404 as a case
    that does not exist, so the API never confirms it is there. Admin and medical directors
    keep their wider view."""
    if u["role"] != "nurse":
        return
    r = c.execute("SELECT assignee_id FROM cases WHERE id=?", (cid,)).fetchone()
    if not r or r["assignee_id"] != u["id"]:
        raise HTTPException(404, "Case not found")


def user_dict(u):
    return dict(id=u["id"], handle=u["handle"], name=u["name"], role=u["role"], title=u["title"]) if u else None


class Login(BaseModel):
    email: str
    password: str


@app.post("/api/login")
def login(body: Login, response: Response):
    c = db.conn()
    u = c.execute("SELECT * FROM users WHERE email=?", (body.email.strip().lower(),)).fetchone()
    if not u or db.hash_pw(body.password, u["salt"]) != u["pw"]:
        raise HTTPException(401, "Wrong email or password")
    sid = secrets.token_hex(16)
    SESSIONS[sid] = u["id"]
    response.set_cookie("sid", sid, httponly=True, samesite="lax")
    return user_dict(u)


@app.post("/api/logout")
def logout(request: Request, response: Response):
    SESSIONS.pop(request.cookies.get("sid", ""), None)
    response.delete_cookie("sid")
    return {"ok": True}


@app.get("/api/me")
def get_me(request: Request):
    c = db.conn()
    u = me(request, c)
    unread = c.execute("SELECT COUNT(*) FROM notifications WHERE user_id=? AND read=0", (u["id"],)).fetchone()[0]
    return dict(user_dict(u), unread=unread)


@app.get("/api/demo-accounts")
def demo_accounts():
    c = db.conn()
    return [dict(email=r["email"], name=r["name"], title=r["title"], role=r["role"]) for r in c.execute("SELECT * FROM users ORDER BY id")]


@app.get("/api/users")
def users(request: Request):
    c = db.conn()
    me(request, c)
    return [user_dict(u) for u in c.execute("SELECT * FROM users ORDER BY id")]


def last_events(c):
    """Most recent handoff-type event per case, so lists can say 'Provider replied' etc."""
    out = {}
    for e in c.execute("SELECT case_id, action FROM audit WHERE action IN ('provider_reply','returned','assigned','pended','escalated','approved','approved_override','denied') ORDER BY id"):
        out[e["case_id"]] = e["action"]
    return out


def row_case(r, names, last=None):
    a = json.loads(r["analysis"])
    f = json.loads(r["facts"])
    return dict(
        id=r["id"], member_name=r["member_name"], member_id=r["member_id"], dob=r["dob"], age=r["age"], facility=r["facility"],
        procedure=r["procedure_name"], cpt=r["cpt"], setting=r["setting"], status=r["status"], priority=r["priority"],
        assignee=names.get(r["assignee_id"]), assignee_id=r["assignee_id"], md=names.get(r["md_id"]), md_id=r["md_id"],
        received_at=r["received_at"], due_at=r["due_at"], decided_at=r["decided_at"], engine=r["engine"],
        extractor=f.get("_extractor", "rule_based"), last_event=(last or {}).get(r["id"]),
        ai_action=a["action"], ai_missing=len(a["gate"]["questions"]), sla=db.sla_status(r["due_at"], r["decided_at"], r["priority"]))


def names_map(c):
    return {u["id"]: dict(id=u["id"], name=u["name"], handle=u["handle"], role=u["role"]) for u in c.execute("SELECT * FROM users")}


@app.get("/api/cases")
def list_cases(request: Request, view: str = "all", q: str = ""):
    c = db.conn()
    u = me(request, c)
    db.raise_sla_alerts(c)
    c.commit()
    names = names_map(c)
    last = last_events(c)
    mine_only = u["role"] == "nurse"
    rows = [row_case(r, names, last) for r in c.execute("SELECT * FROM cases ORDER BY received_at DESC")]
    if mine_only:
        rows = [r for r in rows if r["assignee_id"] == u["id"]]
    open_ = ("new", "in_review", "pended", "escalated")
    at_risk = ("soon", "breached")
    def keep(r):
        if view == "mine":
            return r["status"] in open_ and (r["assignee_id"] == u["id"] or r["md_id"] == u["id"])
        if view == "attention":
            return r["status"] in ("new", "in_review") and (r["assignee_id"] == u["id"])
        if view == "at_risk":
            return r["status"] in open_ and r["sla"] in at_risk
        if view == "unassigned":
            return r["status"] in open_ and not r["assignee_id"]
        if view == "decide":
            return r["status"] == "escalated" and r["md_id"] == u["id"]
        if view in ("pended", "escalated"):
            return r["status"] == view
        if view == "done":
            return r["status"] in ("approved", "denied")
        return True
    rows = [r for r in rows if keep(r)]
    if view in ("attention", "mine", "at_risk", "pended", "escalated", "decide"):
        rows.sort(key=lambda r: r["due_at"])  # least time left first; breached cases come first
    if view == "unassigned":
        rows.sort(key=lambda r: r["received_at"])
    if q:
        ql = q.lower()
        rows = [r for r in rows if ql in (r["member_name"] + r["id"] + r["procedure"] + r["member_id"]).lower()]
    counts = {}
    allrows = [row_case(r, names, last) for r in c.execute("SELECT * FROM cases")]
    if mine_only:
        allrows = [r for r in allrows if r["assignee_id"] == u["id"]]
    counts["all"] = len(allrows)
    counts["mine"] = sum(1 for r in allrows if r["status"] in open_ and (r["assignee_id"] == u["id"] or r["md_id"] == u["id"]))
    counts["attention"] = sum(1 for r in allrows if r["status"] in ("new", "in_review") and r["assignee_id"] == u["id"])
    counts["at_risk"] = sum(1 for r in allrows if r["status"] in open_ and r["sla"] in at_risk)
    counts["decide"] = sum(1 for r in allrows if r["status"] == "escalated" and r["md_id"] == u["id"])
    counts["unassigned"] = sum(1 for r in allrows if r["status"] in open_ and not r["assignee_id"])
    counts["pended"] = sum(1 for r in allrows if r["status"] == "pended")
    counts["escalated"] = sum(1 for r in allrows if r["status"] == "escalated")
    counts["done"] = sum(1 for r in allrows if r["status"] in ("approved", "denied"))
    return dict(cases=rows, counts=counts)


def case_detail(c, cid):
    r = c.execute("SELECT * FROM cases WHERE id=?", (cid,)).fetchone()
    if not r:
        raise HTTPException(404, "Case not found")
    names = names_map(c)
    d = row_case(r, names, last_events(c))
    d["facts"] = json.loads(r["facts"])
    d["analysis"] = json.loads(r["analysis"])
    d["elements"] = [dict(page=e["page"], type=e["type"], text=e["text"]) for e in
                     c.execute("SELECT * FROM elements WHERE case_id=? ORDER BY page,id", (cid,))]
    d["comments"] = [dict(id=x["id"], kind=x["kind"], body=x["body"], created_at=x["created_at"], user=names.get(x["user_id"]))
                     for x in c.execute("SELECT * FROM comments WHERE case_id=? ORDER BY created_at,id", (cid,))]
    d["audit"] = [dict(action=x["action"], detail=x["detail"], created_at=x["created_at"], user=names.get(x["user_id"]))
                  for x in c.execute("SELECT * FROM audit WHERE case_id=? ORDER BY created_at,id", (cid,))]
    return d


@app.get("/api/cases/{cid}")
def get_case(cid: str, request: Request):
    c = db.conn()
    check_case_access(c, me(request, c), cid)
    return case_detail(c, cid)


@app.get("/api/cases/{cid}/export")
def export_case(cid: str, request: Request):
    """The full case record: facts, criteria checklist, decision, and the complete append-only
    audit trail. This is the system-of-record artifact described in ARCHITECTURE.md section 7."""
    c = db.conn()
    check_case_access(c, me(request, c), cid)
    d = case_detail(c, cid)
    d["exported_at"] = db.now()
    d["note"] = "Made-up prototype data. Not a real member record."
    payload = json.dumps(d, indent=2, default=str)
    return Response(content=payload, media_type="application/json",
                     headers={"Content-Disposition": f'attachment; filename="{cid}_record.json"'})


class Assign(BaseModel):
    user_id: int


@app.post("/api/cases/{cid}/assign")
def assign(cid: str, body: Assign, request: Request):
    c = db.conn()
    u = me(request, c)
    check_case_access(c, u, cid)
    old = c.execute("SELECT assignee_id FROM cases WHERE id=?", (cid,)).fetchone()
    c.execute("UPDATE cases SET assignee_id=? WHERE id=?", (body.user_id, cid))
    db.audit(c, cid, u["id"], "assigned", f"Assigned to user {body.user_id}")
    if body.user_id and body.user_id != u["id"] and (not old or old["assignee_id"] != body.user_id):
        db.notify(c, body.user_id, cid, f"{u['name']} assigned {cid} to you")
    c.commit()
    return case_detail(c, cid)


class Comment(BaseModel):
    body: str


def post_comment(c, cid, u, body, kind="comment"):
    c.execute("INSERT INTO comments(case_id,user_id,kind,body,created_at) VALUES(?,?,?,?,?)", (cid, u["id"], kind, body, db.now()))
    for h in set(re.findall(r"@(\w+)", body)):
        t = c.execute("SELECT * FROM users WHERE handle=?", (h,)).fetchone()
        if t and t["id"] != u["id"]:
            db.notify(c, t["id"], cid, f"{u['name']} mentioned you on {cid}")


@app.post("/api/cases/{cid}/comments")
def add_comment(cid: str, body: Comment, request: Request):
    c = db.conn()
    u = me(request, c)
    check_case_access(c, u, cid)
    if not body.body.strip():
        raise HTTPException(400, "Write something first")
    post_comment(c, cid, u, body.body.strip())
    db.audit(c, cid, u["id"], "commented", body.body.strip()[:120])
    c.commit()
    return case_detail(c, cid)


class Act(BaseModel):
    action: str
    note: str = ""
    md_id: int | None = None
    question: str = ""


@app.post("/api/cases/{cid}/action")
def act(cid: str, body: Act, request: Request):
    c = db.conn()
    u = me(request, c)
    check_case_access(c, u, cid)
    r = c.execute("SELECT * FROM cases WHERE id=?", (cid,)).fetchone()
    if not r:
        raise HTTPException(404, "Case not found")
    ai = json.loads(r["analysis"])["action"]
    a, note = body.action, body.note.strip()
    if r["status"] in ("approved", "denied"):
        raise HTTPException(400, "This case already has a decision")
    if a in ("approve", "pend", "escalate", "deny", "return") and u["role"] not in ("nurse", "medical_director"):
        raise HTTPException(403, "Intake does not make clinical decisions. Assign this case to a nurse instead.")
    if a == "deny":
        if u["role"] != "medical_director":
            raise HTTPException(403, "Only a medical director can deny. Escalate this case instead.")
        if not note:
            raise HTTPException(400, "A denial needs the clinical rationale in the note")
        c.execute("UPDATE cases SET status='denied', decided_at=?, md_id=? WHERE id=?", (db.now(), u["id"], cid))
        db.audit(c, cid, u["id"], "denied", note)
        if r["assignee_id"] and r["assignee_id"] != u["id"]:
            db.notify(c, r["assignee_id"], cid, f"{u['name']} denied {cid}")
    elif a == "approve":
        if ai != "approve" and not note:
            raise HTTPException(400, "The system did not recommend approval. Add your reason to override.")
        c.execute("UPDATE cases SET status='approved', decided_at=? WHERE id=?", (db.now(), cid))
        db.audit(c, cid, u["id"], "approved" if ai == "approve" else "approved_override",
                 "Approved. Matched the recommendation." if ai == "approve" else f"Override of recommendation '{ai}': {note}")
        if u["role"] == "medical_director" and r["assignee_id"] and r["assignee_id"] != u["id"]:
            db.notify(c, r["assignee_id"], cid, f"{u['name']} approved {cid}")
    elif a == "pend":
        q = body.question.strip()
        if not q:
            raise HTTPException(400, "Write the question for the provider")
        c.execute("UPDATE cases SET status='pended' WHERE id=?", (cid,))
        post_comment(c, cid, u, q, "provider_request")
        db.audit(c, cid, u["id"], "pended", "Question sent to provider: " + q)
    elif a == "escalate":
        if not body.md_id:
            raise HTTPException(400, "Choose a medical director to tag")
        md = c.execute("SELECT * FROM users WHERE id=? AND role='medical_director'", (body.md_id,)).fetchone()
        if not md:
            raise HTTPException(400, "That user is not a medical director")
        if not note:
            raise HTTPException(400, "Tell the medical director what you need decided")
        c.execute("UPDATE cases SET status='escalated', md_id=? WHERE id=?", (md["id"], cid))
        post_comment(c, cid, u, f"@{md['handle']} {note}", "escalation")
        db.notify(c, md["id"], cid, f"{u['name']} escalated {cid} to you")
        db.audit(c, cid, u["id"], "escalated", f"Escalated to {md['name']}: {note}")
    elif a == "return":
        if u["role"] != "medical_director":
            raise HTTPException(403, "Only a medical director returns escalated cases")
        c.execute("UPDATE cases SET status='in_review' WHERE id=?", (cid,))
        if note:
            post_comment(c, cid, u, note, "comment")
        db.audit(c, cid, u["id"], "returned", note or "Returned to nurse")
        if r["assignee_id"]:
            db.notify(c, r["assignee_id"], cid, f"{u['name']} returned {cid} to you")
    else:
        raise HTTPException(400, "Unknown action")
    c.commit()
    return case_detail(c, cid)


class Addendum(BaseModel):
    text: str


@app.post("/api/cases/{cid}/addendum")
def addendum(cid: str, body: Addendum, request: Request):
    """Simulates the provider replying with the missing documentation, then re-runs the analysis."""
    c = db.conn()
    u = me(request, c)
    check_case_access(c, u, cid)
    r = c.execute("SELECT * FROM cases WHERE id=?", (cid,)).fetchone()
    if not r:
        raise HTTPException(404, "Case not found")
    page = c.execute("SELECT MAX(page) FROM elements WHERE case_id=?", (cid,)).fetchone()[0] + 1
    c.execute("INSERT INTO elements(case_id,page,type,text) VALUES(?,?,?,?)", (cid, page, "NarrativeText", body.text.strip()))
    els = [Element(page=e["page"], type=e["type"], text=e["text"]) for e in
           c.execute("SELECT * FROM elements WHERE case_id=? ORDER BY page,id", (cid,))]
    facts = extract_facts(els)
    res = analyze(facts)
    c.execute("UPDATE cases SET facts=?, analysis=?, status='in_review' WHERE id=?", (json.dumps(facts), json.dumps(res), cid))
    c.execute("INSERT INTO comments(case_id,user_id,kind,body,created_at) VALUES(?,?,?,?,?)",
              (cid, None, "provider_reply", body.text.strip(), db.now()))
    db.audit(c, cid, u["id"], "provider_reply", f"Provider response added as page {page}; re-analyzed. Recommendation: {res['action']}")
    if r["assignee_id"]:
        db.notify(c, r["assignee_id"], cid, f"The provider replied on {cid}. It is back in your queue")
    c.commit()
    return case_detail(c, cid)


@app.post("/api/cases")
def upload(request: Request, file: UploadFile = File(...), assignee_id: int | None = Form(None)):
    c = db.conn()
    u = me(request, c)
    if u["role"] == "medical_director":
        raise HTTPException(403, "Intake uploads packets. Medical directors decide escalated cases.")
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(400, "Upload a PDF packet")
    dest = os.path.join(UPLOADS, f"{secrets.token_hex(4)}_{os.path.basename(file.filename)}")
    with open(dest, "wb") as out:
        shutil.copyfileobj(file.file, out)
    els, engine, facts, res = process(dest)
    cid = db.create_case(c, els, engine, facts, res, os.path.basename(dest))
    if u["role"] == "admin":
        if assignee_id:
            nurse = c.execute("SELECT * FROM users WHERE id=? AND role='nurse'", (assignee_id,)).fetchone()
            if not nurse:
                raise HTTPException(400, "That user is not a nurse")
            c.execute("UPDATE cases SET assignee_id=? WHERE id=?", (assignee_id, cid))
            db.audit(c, cid, u["id"], "assigned", f"Received by intake, assigned to {nurse['name']}")
        else:
            db.audit(c, cid, u["id"], "assigned", "Received by intake, not yet assigned to a nurse")
    else:
        c.execute("UPDATE cases SET assignee_id=? WHERE id=?", (u["id"], cid))
        db.audit(c, cid, u["id"], "assigned", "Assigned to uploader")
    c.commit()
    return case_detail(c, cid)


@app.get("/api/notifications")
def notifications(request: Request):
    c = db.conn()
    u = me(request, c)
    rows = c.execute("SELECT * FROM notifications WHERE user_id=? ORDER BY created_at DESC, id DESC LIMIT 30", (u["id"],)).fetchall()
    return [dict(id=r["id"], case_id=r["case_id"], body=r["body"], read=bool(r["read"]), created_at=r["created_at"]) for r in rows]


@app.post("/api/notifications/read")
def read_notifications(request: Request):
    c = db.conn()
    u = me(request, c)
    c.execute("UPDATE notifications SET read=1 WHERE user_id=?", (u["id"],))
    c.commit()
    return {"ok": True}


@app.get("/api/evals")
def evals(request: Request):
    c = db.conn()
    me(request, c)
    man = json.load(open(os.path.join(ROOT, "evals", "manifest.json")))
    results = []
    for m in man:
        els, eng, facts, res = process(os.path.join(ROOT, "packets", m["file"]), local=True)
        missing = sorted(q["fact"] for q in res["gate"]["questions"])
        exp = m["expected"]
        results.append(dict(file=m["file"], label=m["label"], expected_action=exp["action"], actual_action=res["action"],
                            expected_missing=sorted(exp["missing"]), actual_missing=missing,
                            passed=res["action"] == exp["action"] and missing == sorted(exp["missing"]),
                            never_denied=res["action"] in ("approve", "pend", "escalate")))
    return dict(results=results, passed=sum(r["passed"] for r in results), total=len(results),
                zero_denials=all(r["never_denied"] for r in results),
                caveat="These packets and the rule-based extractor were written together, so a pass shows the pipeline works, not that it is accurate. Accuracy needs messier packets and the model extractor.")


@app.get("/api/evals/holdout")
def evals_holdout(request: Request):
    """M6: a held-out adversarial set, written without reference to extract.py's patterns.
    Uses the live Unstructured API when UNSTRUCTURED_API_KEY is set (required for the OCR
    packet, which has no text layer at all), local pdftotext fallback otherwise."""
    c = db.conn()
    me(request, c)
    from pipeline.holdout_eval import run_holdout
    out = run_holdout(local_only=not os.getenv("UNSTRUCTURED_API_KEY"))
    out["caveat"] = ("This set was written to be hard, not representative. A failure here names a specific gap in "
                      "extract.py; it is not a claim about how often that gap fires on real packets.")
    return out


app.mount("/", StaticFiles(directory=os.path.join(ROOT, "web"), html=True), name="web")
