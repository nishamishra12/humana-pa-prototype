import json, os, re, secrets, shutil
from datetime import datetime, timezone
from fastapi import FastAPI, Form, HTTPException, Request, Response, UploadFile, File
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import db
from pipeline.ingest import Element
from pipeline.extract import _months
from pipeline.engine import analyze
from pipeline.run import process, extract as run_extract
from pipeline.procedures import procedure_for_cpt, defs_by_key, display_for
from pipeline import telemetry as tel
from . import dashboard as dash_mod
from . import policy_admin

ROOT = os.path.join(os.path.dirname(__file__), "..")
UPLOADS = os.path.join(db.DATA_DIR if os.getenv("PA_DATA_DIR") else ROOT, "uploads")
os.makedirs(UPLOADS, exist_ok=True)
db.init()


def _reanalyze_all():
    c = db.conn()
    for r in c.execute("SELECT id, facts, analysis FROM cases").fetchall():
        if json.loads(r["analysis"]).get("action") == "no_policy":
            continue  # the packet was never read for a service. A nurse checks it again (the packet is read then), so do not guess here
        res = json.dumps(analyze(json.loads(r["facts"])))
        if res != r["analysis"]:
            c.execute("UPDATE cases SET analysis=? WHERE id=?", (res, r["id"]))
    c.commit()
    c.close()


_reanalyze_all()

app = FastAPI(title="PA Decision Support")
SESSION_DAYS = 14
MAX_UPLOAD_MB = 15
MAX_UPLOADS_PER_DAY = int(os.getenv("PA_MAX_UPLOADS_PER_DAY", "40"))  # a cap on AI spend if the link is shared widely


@app.middleware("http")
async def no_cache_static(request: Request, call_next):
    """This is a prototype under active edit: never let the browser cache web/* so a
    reload always shows the latest app.js/style.css instead of a stale cached copy."""
    response = await call_next(request)
    if not request.url.path.startswith("/api"):
        response.headers["Cache-Control"] = "no-store"
    return response


def me(request: Request, c):
    sid = request.cookies.get("sid") or ""
    row = c.execute("SELECT user_id, created_at FROM sessions WHERE sid=?", (sid,)).fetchone()
    if not row or (datetime.now(timezone.utc) - datetime.fromisoformat(row["created_at"])).days >= SESSION_DAYS:
        raise HTTPException(401, "Sign in required")
    return c.execute("SELECT * FROM users WHERE id=?", (row["user_id"],)).fetchone()


def check_case_access(c, u, cid):
    """A nurse works only her own cases. Another nurse's case answers the same 404 as a case
    that does not exist, so the API never confirms it is there. Admin and medical directors
    keep their wider view."""
    if u["role"] == "policy_owner":
        raise HTTPException(404, "Case not found")  # the policy owner works on policies, not cases
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
    c.execute("INSERT INTO sessions(sid,user_id,created_at) VALUES(?,?,?)", (sid, u["id"], db.now()))
    c.commit()
    response.set_cookie("sid", sid, httponly=True, samesite="lax", secure=os.getenv("PA_COOKIE_SECURE") == "1", max_age=SESSION_DAYS * 86400)
    return user_dict(u)


@app.post("/api/logout")
def logout(request: Request, response: Response):
    c = db.conn()
    c.execute("DELETE FROM sessions WHERE sid=?", (request.cookies.get("sid", ""),))
    c.commit()
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
        ai_action=a["action"], ai_missing=len(a["gate"]["questions"]), ai_unsure=len(a["gate"].get("unsure", [])), sla=db.sla_status(r["due_at"], r["decided_at"], r["priority"]))


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
    if u["role"] == "policy_owner":
        rows = []
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
    _, proc = procedure_for_cpt(d["facts"].get("_cpt"))
    for df in (proc["facts"] if proc else []):
        f = d["facts"].get(df["key"])
        if isinstance(f, dict):
            f["display"] = display_for(df, f)
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


@app.get("/api/cases/{cid}/pdf")
def original_pdf(cid: str, request: Request):
    """The packet exactly as it arrived, for a nurse who wants to read it on her own."""
    c = db.conn()
    check_case_access(c, me(request, c), cid)
    r = c.execute("SELECT packet_file FROM cases WHERE id=?", (cid,)).fetchone()
    if not r or not r["packet_file"]:
        raise HTTPException(404, "No original file for this case")
    name = os.path.basename(r["packet_file"])
    for folder in (UPLOADS, os.path.join(ROOT, "packets"), os.path.join(ROOT, "packets", "demo"), os.path.join(ROOT, "packets", "holdout"), os.path.join(ROOT, "packets", "multi")):
        p = os.path.join(folder, name)
        if os.path.isfile(p):
            with open(p, "rb") as f:
                return Response(content=f.read(), media_type="application/pdf",
                                headers={"Content-Disposition": f'inline; filename="{cid}_packet.pdf"'})
    raise HTTPException(404, "The original file is no longer on this server")


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


RETURN_REASONS = {
    "reconsider": "Please look at this again",
    "info_enough": "The packet already has what we need",
    "ask_provider": "Ask the provider for more first",
    "wrong_policy": "A different policy applies",
    "other": "Other",
}


def _truth_for(packet_file):
    """Test packets with a known right answer (evals/live_truth.json: {"adv_041.pdf": "pend"}). Real packets have none."""
    try:
        t = json.load(open(os.path.join(ROOT, "evals", "live_truth.json"), encoding="utf-8"))
    except Exception:
        return None
    return t.get(re.sub(r"^[0-9a-f]{8}_", "", os.path.basename(packet_file or "")))


def _cls(needs_person, flagged):
    return ("TP" if flagged else "FN") if needs_person else ("FP" if flagged else "TN")


def _test_file(packet_file):
    return re.sub(r"^[0-9a-f]{8}_", "", os.path.basename(packet_file or "")) if _truth_for(packet_file) else None


def _tel_recommendation(cid, res, packet_file):
    """One event when the AI recommends. If the packet has a known right answer, also the AI's own TP/FN/FP/TN."""
    exp = _truth_for(packet_file)
    a = dict(**{"case.id": cid, "case.test_file": _test_file(packet_file), "ai.recommendation": res["action"], "ai.flagged": res["action"] != "approve"})
    if exp:
        a.update({"truth.expected_action": exp, "truth.needs_person": exp != "approve", "truth.class": _cls(exp != "approve", res["action"] != "approve")})
    tel.event("case.ai_recommendation", **a)


def _tel_decision(cid, packet_file, role, action, ai, reason=""):
    """One event per human decision. No names, no free text. 'human.class' treats the human's decision as the judge of the AI:
    the human flagged a case the AI approved -> FN (the AI missed it); the human approved a case the AI flagged -> FP (an over-flag)."""
    if action not in ("approve", "pend", "escalate", "deny", "return"):
        return
    human_flagged = action != "approve"
    ai_flagged = ai != "approve"
    a = {"case.id": cid, "case.test_file": _test_file(packet_file), "human.role": role, "human.action": action, "ai.recommendation": ai, "human.agrees_with_ai": human_flagged == ai_flagged,
         "human.class": _cls(human_flagged, ai_flagged) if action != "return" else None, "human.return_reason": reason or None}
    exp = _truth_for(packet_file)
    if exp:
        a.update({"truth.expected_action": exp, "truth.human_was_right": (action == "approve") == (exp == "approve")})
    tel.event("case.human_decision", **a)


class Act(BaseModel):
    action: str
    reason: str = ""
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
            raise HTTPException(400, "PA Desk did not recommend approval. Add your reason to approve anyway.")
        c.execute("UPDATE cases SET status='approved', decided_at=? WHERE id=?", (db.now(), cid))
        db.audit(c, cid, u["id"], "approved" if ai == "approve" else "approved_override",
                 "Approved. Matched the recommendation." if ai == "approve" else f"Approved against the recommendation ({ai}). Reason: {note}")
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
        if body.reason and body.reason not in RETURN_REASONS:
            raise HTTPException(400, "Choose one of the listed reasons")
        label = RETURN_REASONS.get(body.reason, "")
        if not (label or note):
            raise HTTPException(400, "Say why you are returning this case")
        c.execute("UPDATE cases SET status='in_review' WHERE id=?", (cid,))
        text = (label + (": " if label and note else "") + note)
        post_comment(c, cid, u, text, "comment")
        db.audit(c, cid, u["id"], "returned", text)
        if r["assignee_id"]:
            db.notify(c, r["assignee_id"], cid, f"{u['name']} returned {cid} to you")
    else:
        raise HTTPException(400, "Unknown action")
    c.commit()
    _tel_decision(cid, r["packet_file"], u["role"], a, ai, body.reason if a == "return" else "")
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
    facts = run_extract(els, fast=True)
    res = analyze(facts)
    c.execute("UPDATE cases SET facts=?, analysis=?, status='in_review' WHERE id=?", (json.dumps(facts), json.dumps(res), cid))
    c.execute("INSERT INTO comments(case_id,user_id,kind,body,created_at) VALUES(?,?,?,?,?)",
              (cid, None, "provider_reply", body.text.strip(), db.now()))
    db.audit(c, cid, u["id"], "provider_reply", f"Provider response added as page {page}. Case checked again. Recommendation: {res['action']}")
    if r["assignee_id"]:
        db.notify(c, r["assignee_id"], cid, f"The provider replied on {cid}. It is back in your queue")
    c.commit()
    return case_detail(c, cid)


@app.post("/api/cases/{cid}/recheck")
def recheck(cid: str, request: Request):
    """Reads the packet again and checks it against the policy library as it is now. Used when a case arrived before its policy existed."""
    c = db.conn()
    u = me(request, c)
    check_case_access(c, u, cid)
    if u["role"] not in ("nurse", "medical_director", "admin"):
        raise HTTPException(403, "Not allowed")
    r = c.execute("SELECT * FROM cases WHERE id=?", (cid,)).fetchone()
    if not r:
        raise HTTPException(404, "Case not found")
    if r["status"] in ("approved", "denied"):
        raise HTTPException(400, "This case already has a decision")
    els = [Element(page=e["page"], type=e["type"], text=e["text"]) for e in c.execute("SELECT * FROM elements WHERE case_id=? ORDER BY page,id", (cid,))]
    before = json.loads(r["analysis"]).get("action")
    facts = run_extract(els)
    res = analyze(facts)
    c.execute("UPDATE cases SET facts=?, analysis=? WHERE id=?", (json.dumps(facts), json.dumps(res), cid))
    db.audit(c, cid, u["id"], "rechecked", f"Case checked again against policy library {res.get('library_version')}. Recommendation: {before} to {res['action']}")
    c.commit()
    return case_detail(c, cid)


class FixFact(BaseModel):
    kind: str  # found | none | missing
    value: str = ""
    page: int | None = None


@app.post("/api/cases/{cid}/facts/{key}")
def fix_fact(cid: str, key: str, body: FixFact, request: Request):
    """The nurse's feedback on what the AI read. Saves her answer, logs it, and re-checks the case.
    Every correction is a signal about how well the AI reads (see docs/METRICS_FRAMEWORK.md).
    The facts and their allowed answers come from the procedure's definition, so this works for every illness."""
    c = db.conn()
    u = me(request, c)
    check_case_access(c, u, cid)
    if u["role"] not in ("nurse", "medical_director"):
        raise HTTPException(403, "Only a nurse or medical director can correct what we read.")
    r = c.execute("SELECT * FROM cases WHERE id=?", (cid,)).fetchone()
    if not r:
        raise HTTPException(404, "Case not found")
    facts = json.loads(r["facts"])
    _, proc = procedure_for_cpt(facts.get("_cpt"))
    defs = defs_by_key(proc) if proc else {}
    if key not in defs:
        raise HTTPException(404, "Unknown fact")
    d = defs[key]
    if r["status"] in ("approved", "denied"):
        raise HTTPException(400, "This case already has a decision")
    old = facts.get(key, {}).get("status", "missing")
    kind, v = body.kind, body.value.strip()
    if kind == "found":
        if key == "shared_decision_making":
            v = v or "Documented"
        if not v:
            raise HTTPException(400, "Write what the packet says")
        k = d["kind"]
        if k == "number":
            try:
                num = float(v)
            except ValueError:
                raise HTTPException(400, "Enter a number" + (f", like {d['hint'].split('like')[-1].strip()}" if "like" in d.get("hint", "") else ""))
            value = int(num) if num == int(num) else num
        elif k == "list":
            value = [x.strip() for x in re.split(r"[,;]", v) if x.strip()]
        elif k == "enum":
            match = next((o for o in d["values"] if o.lower() == v.lower()), None)
            if not match:
                raise HTTPException(400, "Choose one: " + ", ".join(d["values"]))
            value = match
        else:
            value = v
        fact = dict(status="found", value=value, page=body.page, quote=f"Confirmed by {u['name']}: {v}", note=None, confirmed_by=u["name"])
        if key == "conservative_treatment":
            fact["duration_months"] = _months(v)
    elif kind == "none":
        if "none" not in d["statuses"]:
            raise HTTPException(400, "This fact cannot be marked as none")
        fact = dict(status="none", value=[] if d["kind"] == "list" else None, page=body.page, quote=f"Confirmed by {u['name']}: the packet says there is none", note=None, confirmed_by=u["name"])
    elif kind == "missing":
        fact = dict(status="missing", value=None, page=None, quote=None, note=f"Confirmed missing by {u['name']}", confirmed_by=u["name"])
    else:
        raise HTTPException(400, "kind must be found, none or missing")
    facts[key] = fact
    facts.setdefault("_corrections", []).append(dict(fact=key, was=old, now=fact["status"], by=u["name"], at=db.now()))
    res = analyze(facts)
    c.execute("UPDATE cases SET facts=?, analysis=? WHERE id=?", (json.dumps(facts), json.dumps(res), cid))
    db.audit(c, cid, u["id"], "fact_corrected", f"{d['label']}: changed from \"{old}\" to \"{fact['status']}\". Recommendation is now: {res['action']}")
    c.commit()
    return case_detail(c, cid)


JOBS: dict[str, dict] = {}


@app.get("/api/jobs/{job}")
def job_status(job: str, request: Request):
    c = db.conn()
    me(request, c)
    return JOBS.get(job, dict(stage="waiting"))


@app.post("/api/cases")
def upload(request: Request, file: UploadFile = File(...), assignee_id: int | None = Form(None), job: str | None = Form(None)):
    c = db.conn()
    u = me(request, c)
    if u["role"] in ("medical_director", "policy_owner"):
        raise HTTPException(403, "Intake uploads packets. Medical directors decide escalated cases.")
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(400, "Upload a PDF packet")
    today = c.execute("SELECT COUNT(*) FROM audit WHERE action='received' AND created_at >= ?", (db.now(-1),)).fetchone()[0]
    if today >= MAX_UPLOADS_PER_DAY:
        raise HTTPException(429, f"The demo accepts {MAX_UPLOADS_PER_DAY} new packets a day. Try again tomorrow.")
    file.file.seek(0, 2)
    if file.file.tell() > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(413, f"Packets over {MAX_UPLOAD_MB} MB are not accepted in the demo")
    file.file.seek(0)
    dest = os.path.join(UPLOADS, f"{secrets.token_hex(4)}_{os.path.basename(file.filename)}")
    with open(dest, "wb") as out:
        shutil.copyfileobj(file.file, out)
    def progress(stage, **info):
        if job:
            JOBS[job] = dict(stage=stage, **info)
    els, engine, facts, res = process(dest, progress=progress)
    cid = db.create_case(c, els, engine, facts, res, os.path.basename(dest))
    _tel_recommendation(cid, res, os.path.basename(dest))
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
    if job:
        JOBS[job] = dict(stage="done", case_id=cid)
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
                            never_denied=res["action"] in ("approve", "pend", "escalate", "verify")))
    return dict(results=results, passed=sum(r["passed"] for r in results), total=len(results),
                zero_denials=all(r["never_denied"] for r in results),
                caveat="We wrote these packets alongside the checker, so a pass shows the flow works. It does not prove accuracy. Real accuracy needs messier packets.")


@app.get("/api/evals/holdout")
def evals_holdout(request: Request):
    """M6: a held-out adversarial set, written without reference to extract.py's patterns.
    Uses the live Unstructured API when UNSTRUCTURED_API_KEY is set (required for the OCR
    packet, which has no text layer at all), local pdftotext fallback otherwise."""
    c = db.conn()
    me(request, c)
    from pipeline.holdout_eval import run_holdout
    out = run_holdout(local_only=not os.getenv("UNSTRUCTURED_API_KEY"))
    out["caveat"] = ("We wrote these packets to be hard, not typical. A miss here points to one specific weakness. "
                      "It does not say how often that weakness shows up on real packets.")
    return out


@app.get("/healthz")
def healthz():
    return {"ok": True}


class ResetDemo(BaseModel):
    confirm: str = ""


@app.post("/api/admin/reset-demo")
def reset_demo(body: ResetDemo, request: Request):
    """Wipes every case and re-seeds the demo data. Intake only, and only with confirm='RESET'. For the day before a demo."""
    c = db.conn()
    u = me(request, c)
    if u["role"] != "admin" or body.confirm != "RESET":
        raise HTTPException(403, "Intake only, with confirm set to RESET")
    for t in ("notifications", "audit", "comments", "elements", "cases", "sessions"):
        c.execute(f"DELETE FROM {t}")
    c.execute("DELETE FROM users")
    c.commit()
    c.close()
    db.init()
    return {"ok": True, "note": "Demo data reset. Everyone is signed out."}


@app.get("/api/dashboard")
def dashboard_data(request: Request):
    """Live numbers for the executive and utilization management views (web/ops.html). Intake and medical directors only."""
    c = db.conn()
    u = me(request, c)
    if u["role"] not in ("admin", "medical_director"):
        raise HTTPException(403, "This view is for intake and medical directors")
    return dash_mod.compute(c)


policy_admin.setup(app, me)
app.mount("/", StaticFiles(directory=os.path.join(ROOT, "web"), html=True), name="web")
