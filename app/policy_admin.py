"""The policy owner's screens: build a draft from an official policy, review each rule beside its source, publish a versioned library.

What this does and does not do:
- A build runs the policy pipeline (fetch, parse with Unstructured, AI draft, code checks). The AI drafts. It never publishes.
- The owner approves, edits or rejects every rule. A rule that failed the code checks, or that needs a fact the packet reader does not find yet, cannot be approved.
- Publishing writes a new versioned library (the live file on the data disk) and reloads the engine. Each version is kept, so a change can be reverted.
- Cases that already exist keep the recommendation they were given. New cases, and any case re-analyzed, use the new version.
"""
import copy, json, os, re, secrets, shutil, threading
from datetime import datetime, timezone

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel

from . import db
from pipeline import engine, procedures, telemetry as tel
from pipeline.policy_build import sources as S
from pipeline.policy_build.build import run as run_build
from pipeline.policy_build.compare import compare as compare_live
from pipeline.policy_build import codes as cms_codes

router = APIRouter(prefix="/api/policies")
MAX_BUILDS_PER_DAY = int(os.getenv("PA_MAX_BUILDS_PER_DAY", "12"))  # each build is one AI call plus an Unstructured parse
VERSIONS_DIR = os.path.join(db.DATA_DIR, "library_versions")
ROOT = os.path.join(os.path.dirname(__file__), "..")
_me = None  # set by setup(): the app's own sign-in check


def setup(app, me):
    """Called once by the app. Registers the routes, and gives a fresh data disk the policy runs we already have."""
    global _me
    _me = me
    app.include_router(router)
    try:
        if os.getenv("PA_DATA_DIR") and not os.path.isdir(S.WORK):
            shutil.copytree(os.path.join(ROOT, "policies", "work"), S.WORK)
        _seed_builds()
    except Exception as e:  # never stop the app over the seed
        print(f"[policy_admin] seed skipped: {type(e).__name__}: {str(e)[:100]}")


def _seed_builds():
    c = db.conn()
    owner = c.execute("SELECT id FROM users WHERE role='policy_owner'").fetchone()
    if not (owner and os.path.isdir(S.WORK)):
        return
    for pid in sorted(os.listdir(S.WORK)):
        for ver in sorted(os.listdir(os.path.join(S.WORK, pid))):
            folder = os.path.join(S.WORK, pid, ver)
            if not all(os.path.exists(os.path.join(folder, f)) for f in ("draft.json", "report.json", "meta.json", "elements.json")):
                continue
            if c.execute("SELECT 1 FROM policy_builds WHERE folder=? OR (policy_id=? AND version=?)", (folder, pid, ver)).fetchone():
                continue
            rep = json.load(open(os.path.join(folder, "report.json"), encoding="utf-8"))
            c.execute("INSERT INTO policy_builds(id,policy_id,kind,ident,service,status,stage,folder,version,created_by,created_at,summary) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                      ("b-" + secrets.token_hex(4), pid, "earlier run", pid, "", "draft", "Ready to review", folder, ver, owner["id"], db.now(), json.dumps(rep["counts"])))
    c.commit()


def _owner(request):
    c = db.conn()
    u = _me(request, c)
    if u["role"] != "policy_owner":
        raise HTTPException(403, "This screen is for the policy owner")
    return c, u


def _log(c, u, action, policy_id=None, build_id=None, detail=""):
    """One line in the owner's audit trail. Every build, decision, publish and revert is written here and never changed."""
    c.execute("INSERT INTO policy_audit(at,user_id,action,policy_id,build_id,detail) VALUES(?,?,?,?,?,?)", (db.now(), u["id"], action, policy_id, build_id, (detail or "")[:400]))


_corpus_cache = {}


def _corpus(kind):
    """The CMS policies kept by the back end (policies/corpus). The owner picks from this list. A scheduled job refreshes it, the screen does not."""
    if kind not in _corpus_cache:
        path = os.path.join(ROOT, "policies", "corpus", "ncds.json" if kind == "ncd" else "lcds.json")
        rows = [dict(id=x["id"], title=x.get("title", ""), effective=x.get("effective")) for x in json.load(open(path, encoding="utf-8")) if "error" not in x]
        _corpus_cache[kind] = (rows, datetime.fromtimestamp(os.path.getmtime(path), timezone.utc).strftime("%Y-%m-%d"))
    return _corpus_cache[kind]


@router.get("/corpus")
def corpus(kind: str, request: Request, q: str = ""):
    c, u = _owner(request)
    if kind not in ("ncd", "lcd"):
        raise HTTPException(400, "Choose NCD or LCD")
    rows, as_of = _corpus(kind)
    toks = [t for t in re.split(r"\s+", q.lower().strip()) if t]
    hits = [r for r in rows if all(t in (r["id"] + " " + r["title"]).lower() for t in toks)] if toks else sorted(rows, key=lambda r: r["title"])
    lib = {p["id"] for p in procedures.library()["policies"]}
    prefix = "NCD-" if kind == "ncd" else "LCD-"
    return dict(as_of=as_of, total=len(rows), matches=len(hits), results=[dict(r, in_library=(prefix + r["id"]) in lib) for r in hits[:12]])


def _fetchable(policy_id):
    """The way to re-fetch a policy in the live library. Returns (kind, ident) or None for a policy with no API."""
    if policy_id.startswith("NCD-"):
        return "ncd", policy_id[4:]
    if policy_id.startswith("LCD-"):
        return "lcd", policy_id[4:]
    m = re.match(r"^CFR-(\d+)-(.+)$", policy_id)
    if m:
        part = m.group(2).split(".")[0]
        return "cfr", (int(m.group(1)), int(part), m.group(2))
    return None


def _services(lib, pid):
    return [p["short"] for p in lib["procedures"].values() if pid in p.get("policies", [])]


def _latest_hash(policy_id):
    base = os.path.join(S.WORK, policy_id)
    if not os.path.isdir(base):
        return None, None
    ver = sorted(os.listdir(base))[-1]
    try:
        m = json.load(open(os.path.join(base, ver, "meta.json"), encoding="utf-8"))
        return m.get("sha256"), m.get("retrieved_at")
    except Exception:
        return None, None


# ---------- the library list ----------
@router.get("")
def policies(request: Request):
    c, u = _owner(request)
    lib = procedures.library()
    rows = []
    for p in lib["policies"]:
        sha, at = _latest_hash(p["id"])
        rows.append(dict(id=p["id"], title=p["title"], level=p["level"], source=p["source"], url=p.get("url"), verified=bool(p.get("verified")),
                         criteria=len(p.get("criteria", [])), waiting=len(p.get("waiting_rules", [])), n_facts=len(p.get("facts", [])), services=_services(lib, p["id"]), fetchable=bool(_fetchable(p["id"])),
                         last_saved=at, has_saved=bool(sha), note=p.get("verified_from") or p.get("applies_to")))
    builds = [dict(r) for r in c.execute("SELECT b.*, u.name AS who FROM policy_builds b LEFT JOIN users u ON u.id=b.created_by ORDER BY b.created_at DESC, b.rowid DESC LIMIT 25")]
    done = {r[0]: r[1] for r in c.execute("SELECT build_id, SUM(decision != 'pending') FROM policy_decisions GROUP BY build_id")}
    for b in builds:
        b["summary"] = json.loads(b["summary"]) if b.get("summary") else None
        b["total"] = sum(b["summary"].values()) if b["summary"] else None
        b["decided"] = done.get(b["id"], 0) or 0
    seen = {r[0]: r[1] for r in c.execute("SELECT cpt, COUNT(*) FROM cases GROUP BY cpt")}
    pols = {x["id"]: x for x in lib["policies"]}
    drafts = {r[0]: r[1] for r in c.execute("SELECT service, COUNT(*) FROM policy_builds WHERE status IN ('draft','running') GROUP BY service")}
    svc = [dict(key=k, name=p["short"], full=p["name"], scope=p.get("scope") or "", n_drafts=drafts.get(k, 0), cpts=p["cpts"], policies=p.get("policies", []), checked=p.get("cpt_checked"), status=p.get("status", "live"),
                sources=p.get("cpt_sources", []), other_codes=p.get("cms_other_codes", []), n_details=len(p["facts"]), note=p.get("status_note"),
                n_rules=sum(len(pols[i].get("criteria", [])) for i in p.get("policies", []) if i in pols), n_cases=sum(seen.get(x, 0) for x in p["cpts"]))
           for k, p in lib["procedures"].items()]
    waiting = [json.loads(r["analysis"]).get("action") == "no_policy" for r in c.execute("SELECT analysis FROM cases WHERE status NOT IN ('approved','denied')")]
    return dict(version=lib.get("version"), policies=rows, builds=builds, services=[dict(key=k, name=p["short"]) for k, p in lib["procedures"].items()], services_detail=svc, demand_count=sum(waiting),
                n_drafts=sum(1 for b in builds if b["status"] == "draft"), versions=_versions(c))


# ---------- start a build ----------
class BuildReq(BaseModel):
    kind: str
    ident: str
    service: str = ""


def _start(c, u, kind, ident, service, file=None, meta_in=None):
    n = c.execute("SELECT COUNT(*) FROM policy_builds WHERE created_at >= ? AND kind != 'earlier run'", (db.now(-1),)).fetchone()[0]
    if n >= MAX_BUILDS_PER_DAY:
        raise HTTPException(429, f"The demo allows {MAX_BUILDS_PER_DAY} new drafts a day. Try again tomorrow.")
    bid = "b-" + secrets.token_hex(4)
    c.execute("INSERT INTO policy_builds(id,kind,ident,service,status,stage,created_by,created_at) VALUES(?,?,?,?,?,?,?,?)",
              (bid, kind, ident, service, "running", "Starting", u["id"], db.now()))
    if kind != "earlier run":
        _log(c, u, "draft_started", None, bid, f"{kind.upper()} {ident}")
    c.commit()
    threading.Thread(target=_run, args=(bid, kind, ident, service, file, meta_in), daemon=True).start()
    return bid


def _run(bid, kind, ident, service, file, meta_in):
    c = db.conn()
    stages = {"1": "Getting the policy", "2": "Reading the policy", "3": "Drafting the rules", "4": "Checking every rule", "5": "Comparing with the live rules"}

    def log(msg):
        s = stages.get(msg[:1])
        if s:
            c.execute("UPDATE policy_builds SET stage=? WHERE id=?", (s, bid))
            c.commit()
    try:
        lib = procedures.library()
        vocab = None
        if service == "new":
            vocab = []
        elif service in lib["procedures"]:
            vocab = lib["procedures"][service]["facts"]
        out = run_build({"cfr": "cfr"}.get(kind, kind), _ident(kind, ident), vocab=vocab, log=log, file=file, meta_in=meta_in)
        meta = out["meta"]
        c.execute("UPDATE policy_builds SET policy_id=?, folder=?, version=?, status='draft', stage='Ready to review', summary=? WHERE id=?",
                  (meta["policy_id"], out["folder"], meta["version"], json.dumps(out["report"]["counts"]), bid))
        tel.event("policy.build", **{"policy.id": meta["policy_id"], "policy.criteria_drafted": len(out["draft"]["criteria"]), "policy.checks_fail": out["report"]["counts"]["fail"]})
    except Exception as e:
        c.execute("UPDATE policy_builds SET status='error', stage='Failed', error=? WHERE id=?", (f"{type(e).__name__}: {str(e)[:300]}", bid))
    c.commit()


def _ident(kind, ident):
    if kind == "cfr":
        m = re.match(r"^\s*(\d+)\s+CFR\s+(?:Sec\.?\s*)?(\d+)\.(\d+)\s*$", ident, re.I) or re.match(r"^\s*(\d+)[ .,/-]+(\d+)[ .,/-]+([\d.]+)\s*$", ident)
        if not m:
            raise ValueError("Write a regulation like 42 CFR 412.3")
        if len(m.groups()) == 3 and "." not in m.group(3):
            return int(m.group(1)), int(m.group(2)), f"{m.group(2)}.{m.group(3)}"
        return int(m.group(1)), int(m.group(2)), m.group(3) if "." in m.group(3) else f"{m.group(2)}.{m.group(3)}"
    return ident.strip()


@router.post("/builds")
def new_build(body: BuildReq, request: Request):
    c, u = _owner(request)
    if body.kind not in ("ncd", "lcd", "cfr"):
        raise HTTPException(400, "Choose a source")
    if not body.ident.strip():
        raise HTTPException(400, "Enter the policy number")
    try:
        _ident(body.kind, body.ident)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return dict(id=_start(c, u, body.kind, body.ident, body.service))


@router.post("/builds/upload")
def upload_build(request: Request, file: UploadFile = File(...), policy_id: str = Form(...), title: str = Form(...), level: str = Form("HUMANA_INTERNAL"), service: str = Form("")):
    c, u = _owner(request)
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(400, "Upload a PDF")
    pid = re.sub(r"[^A-Za-z0-9._-]+", "-", policy_id.strip()) or "UPLOAD"
    os.makedirs(os.path.join(S.WORK, "_uploads"), exist_ok=True)
    dest = os.path.join(S.WORK, "_uploads", f"{secrets.token_hex(4)}.pdf")
    with open(dest, "wb") as out:
        shutil.copyfileobj(file.file, out)
    return dict(id=_start(c, u, "file", pid, service, file=dest, meta_in=dict(policy_id=pid, level=level, title=title.strip())))


# ---------- one build ----------
def _decisions(c, bid):
    return {r["criterion_id"]: dict(decision=r["decision"], edited=json.loads(r["edited"]) if r["edited"] else None) for r in c.execute("SELECT * FROM policy_decisions WHERE build_id=?", (bid,))}


def _effective(crit, dec):
    """The criterion with the owner's edits applied."""
    out = copy.deepcopy(crit)
    e = (dec or {}).get("edited") or {}
    for k in ("text", "if_missing", "short"):
        if e.get(k) is not None:
            out[k] = e[k]
    if "value" in e and e["value"] is not None:
        out["test"] = dict(out["test"], value=e["value"])
    return out


def _all_fact_keys(lib, service=None, policy_id=None):
    """The details the packet reader can find. For one service, only that service's details. For a policy, the services whose stack lists it.
    With neither, every service's details (a policy no service uses yet)."""
    procs = lib["procedures"]
    if service in procs:
        chosen = [procs[service]]
    elif policy_id and any(policy_id in p.get("policies", []) for p in procs.values()):
        chosen = [p for p in procs.values() if policy_id in p.get("policies", [])]
    else:
        chosen = list(procs.values())
    return {d["key"] for p in chosen for d in p["facts"]}


def _blocked(crit, rep, lib):
    """A rule the owner cannot approve: the code checks failed."""
    if rep["level"] == "fail":
        return "The automatic checks failed: " + "; ".join(rep["issues"])
    return None


def _waiting(crit, lib, keys=None):
    """A rule the owner can approve, but that cannot be used yet: it needs a detail the packet reader does not look for."""
    keys = keys if keys is not None else _all_fact_keys(lib)
    f = crit.get("required_fact")
    ai = crit.get("applies_if")
    new = []
    if crit["test"]["type"] != "informational" and f and f not in keys:
        new.append(f)
    if ai and ai.get("fact") and ai["fact"] not in keys:
        new.append(ai["fact"])
    if new:
        return "Needs a key fact the AI reader does not look for yet (" + ", ".join(x.replace("_", " ") for x in new) + "). You can approve the rule now. It is saved with the policy and changes nothing until a service has this key fact."
    return None


@router.get("/builds/{bid}")
def get_build(bid: str, request: Request):
    c, u = _owner(request)
    b = c.execute("SELECT * FROM policy_builds WHERE id=?", (bid,)).fetchone()
    if not b:
        raise HTTPException(404, "Draft not found")
    out = dict(id=b["id"], status=b["status"], stage=b["stage"], error=b["error"], policy_id=b["policy_id"], kind=b["kind"], ident=b["ident"], version=b["version"])
    if b["status"] not in ("draft", "published"):
        return out
    f = b["folder"]
    meta = json.load(open(os.path.join(f, "meta.json"), encoding="utf-8"))
    els = json.load(open(os.path.join(f, "elements.json"), encoding="utf-8"))
    draft = json.load(open(os.path.join(f, "draft.json"), encoding="utf-8"))
    rep = json.load(open(os.path.join(f, "report.json"), encoding="utf-8"))
    lib = procedures.library()
    dec = _decisions(c, bid)
    repb = {r["id"]: r for r in rep["criteria"]}
    ctx = b["service"] if b["service"] in lib["procedures"] else ""
    ctx_open = bool(ctx) and lib["procedures"][ctx].get("status", "live") != "live"
    keys_ok = _all_fact_keys(lib, ctx or None, meta["policy_id"]) | ({f["key"] for f in draft.get("new_facts", [])} if ctx_open else set())
    crits = []
    for cr in draft["criteria"]:
        d = dec.get(cr["id"], {})
        eff = _effective(cr, d)
        issues = [i for i in repb[cr["id"]]["issues"] if "new packet detail" not in i and "NEW fact" not in i]
        crits.append(dict(eff, original_test=cr["test"], check=("pass" if repb[cr["id"]]["level"] == "review" and not issues else repb[cr["id"]]["level"]), issues=issues, decision=d.get("decision") or "pending",
                          edited=bool(d.get("edited")), blocked=_blocked(cr, repb[cr["id"]], lib), waiting=_waiting(cr, lib, keys_ok)))
    live = next((p for p in lib["policies"] if p["id"] == meta["policy_id"]), None)
    cpath = os.path.join(f, "codes.json")
    codes = json.load(open(cpath, encoding="utf-8")) if os.path.exists(cpath) else dict(method="none", articles=[], codes=[], note="This draft was built before codes were fetched. Build it again to fetch them.")
    mine = [k for k, p in lib["procedures"].items() if meta["policy_id"] in p.get("policies", [])]
    out.update(used_by=[p["short"] for p in lib["procedures"].values() if meta["policy_id"] in p.get("policies", [])])
    out.update(codes=codes, service_now=ctx or (mine[0] if mine else ""), service_ctx=ctx, service_ctx_name=lib["procedures"][ctx]["short"] if ctx else "",
               service_ctx_status=lib["procedures"][ctx].get("status", "live") if ctx else "", services=[dict(key=k, name=p["short"], cpts=p["cpts"], status=p.get("status", "live"), fact_keys=[d["key"] for d in p["facts"]]) for k, p in lib["procedures"].items()])
    out.update(meta=dict(meta), elements=els["elements"], engine=els["info"].get("engine"), criteria=crits, new_facts=draft.get("new_facts", []),
               not_modeled=draft.get("not_modeled", []), uncovered=rep["uncovered"], counts=rep["counts"],
               change_report=compare_live(draft, meta["policy_id"]) if live else None, in_library=bool(live), live_criteria=len(live["criteria"]) if live else 0,
               tally={k: sum(1 for x in crits if x["decision"] == k) for k in ("approved", "rejected", "pending")}, library_version=lib.get("version"),
               waiting_approved=sum(1 for x in crits if x["decision"] == "approved" and x["waiting"]))
    return out


class DecisionReq(BaseModel):
    decision: str
    text: str | None = None
    if_missing: str | None = None
    short: str | None = None
    value: float | list[str] | None = None


@router.post("/builds/{bid}/criteria/{cid}")
def decide(bid: str, cid: str, body: DecisionReq, request: Request):
    c, u = _owner(request)
    b = c.execute("SELECT * FROM policy_builds WHERE id=?", (bid,)).fetchone()
    if not b or b["status"] != "draft":
        raise HTTPException(400, "This draft is not open for review")
    draft = json.load(open(os.path.join(b["folder"], "draft.json"), encoding="utf-8"))
    rep = json.load(open(os.path.join(b["folder"], "report.json"), encoding="utf-8"))
    crit = next((x for x in draft["criteria"] if x["id"] == cid), None)
    if not crit:
        raise HTTPException(404, "Rule not found")
    if body.decision not in ("approved", "rejected", "pending"):
        raise HTTPException(400, "Choose approve, reject or undo")
    block = _blocked(crit, next(r for r in rep["criteria"] if r["id"] == cid), procedures.library())
    if body.decision == "approved" and block:
        raise HTTPException(400, block)
    edited = {k: v for k, v in dict(text=body.text, if_missing=body.if_missing, short=body.short, value=body.value).items() if v is not None}
    t = crit["test"]["type"]
    if "value" in edited:
        if t in ("gte", "lte") and not isinstance(edited["value"], (int, float)):
            raise HTTPException(400, "A threshold needs a number")
        if t == "in" and not isinstance(edited["value"], list):
            raise HTTPException(400, "Give a list of values")
        if t not in ("gte", "lte", "in"):
            raise HTTPException(400, "This rule has no value to edit")
    prev = _decisions(c, bid).get(cid, {})
    c.execute("INSERT OR REPLACE INTO policy_decisions(build_id,criterion_id,decision,edited,decided_by,decided_at) VALUES(?,?,?,?,?,?)",
              (bid, cid, body.decision, json.dumps(edited) if edited else (json.dumps(prev["edited"]) if prev.get("edited") and not edited else None), u["id"], db.now()))
    label = {"approved": "approved", "rejected": "rejected", "pending": "undid the decision on"}[body.decision]
    _log(c, u, "rule_" + body.decision, b["policy_id"], bid, f"{label} {cid}" + (" (edited)" if edited else ""))
    c.commit()
    return dict(ok=True)


# ---------- publish ----------
def _test_text(c):
    t, v, f = c["test"]["type"], c["test"].get("value"), c["required_fact"]
    return {"gte": f"{f} >= {v}", "lte": f"{f} <= {v}", "present": "non_empty", "informational": "informational"}.get(t)


def _to_library(c, yesno=()):
    """A reviewed draft criterion in the shape the rules engine reads. A yes or no detail tested with present means 'is yes'."""
    t = c["test"]["type"]
    if c.get("required_fact") in yesno and t in ("present", "absent"):
        c = dict(c, test=dict(type="in", value=["yes"] if t == "present" else ["no"]))
        t = "in"
    out = dict(id=c["id"], text=c["text"], cite=c["cite"], required_fact=None if t == "informational" else c["required_fact"], if_missing=c.get("if_missing"), short=c.get("short"))
    test = _test_text(c)
    if test:
        out["test"] = test
    if t in ("gte", "lte"):
        out["check"] = dict(op=t, value=c["test"]["value"])
    elif t == "in":
        out["check"] = dict(op="in", value=c["test"]["value"])
    elif t == "absent":
        out["mode"] = "absent"
    if c.get("applies_if"):
        out["applies_if"] = dict(fact=c["applies_if"]["fact"], equals=c["applies_if"]["equals"])
    return out


def _bump(v):
    parts = (v or "0.0.0").split(".")
    try:
        parts[-1] = str(int(parts[-1]) + 1)
    except ValueError:
        parts.append("1")
    return ".".join(parts)


def _key(c):
    """What a rule means to the engine: the fact it tests and the test. Two rules with the same key are the same rule, whatever they are called."""
    return json.dumps([c.get("required_fact"), c.get("check"), c.get("mode"), c.get("applies_if")], sort_keys=True, default=str)


def _diff(old, new):
    ok, nk = {_key(x): x for x in old}, {_key(x): x for x in new}
    return dict(added=[nk[k]["id"] for k in nk if k not in ok], removed=[ok[k]["id"] for k in ok if k not in nk], changed=[],
                unchanged=len([k for k in nk if k in ok]))


def _write_live(lib):
    os.makedirs(VERSIONS_DIR, exist_ok=True)
    tmp = procedures.LIVE_PATH + ".tmp"
    json.dump(lib, open(tmp, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    os.replace(tmp, procedures.LIVE_PATH)
    procedures.reload()
    engine.refresh()


def _snapshot(lib):
    os.makedirs(VERSIONS_DIR, exist_ok=True)
    path = os.path.join(VERSIONS_DIR, f"{lib.get('version')}.json")
    if not os.path.exists(path):
        json.dump(lib, open(path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)


def _check_attach(att, lib, draft, folder, policy_id):
    """The owner may tie the policy to a service and say which procedure codes send a packet to it. Every code needs a source:
    either one the CMS lookup found for this policy, or a note the owner wrote. A code can belong to one service only."""
    if not att or not att.service:
        return None
    if att.service == "__new__":
        if not att.new_service or not att.new_service.name.strip() or not att.new_service.short.strip():
            raise HTTPException(400, "Give the new service a name and a short name")
        if not att.codes:
            raise HTTPException(400, "A new service needs at least one procedure code, or no packet can reach it")
    elif att.service not in lib["procedures"]:
        raise HTTPException(400, "That service does not exist")
    cpath = os.path.join(folder, "codes.json")
    found = {c["code"]: c for c in (json.load(open(cpath, encoding="utf-8")).get("codes", []) if os.path.exists(cpath) else [])}
    arts = {a["id"]: a for a in (json.load(open(cpath, encoding="utf-8")).get("articles", []) if os.path.exists(cpath) else [])}
    owner_of = {c: k for k, p in lib["procedures"].items() for c in p["cpts"]}
    out = []
    for c in att.codes:
        code = c.code.strip().upper()
        if not re.match(r"^([0-9]{5}|[A-Z][0-9]{4})$", code):
            raise HTTPException(400, f"{c.code} is not a billing code. A code is 5 digits, or a letter and 4 digits.")
        if owner_of.get(code) and owner_of[code] != att.service:
            raise HTTPException(400, f"Code {code} already belongs to {lib['procedures'][owner_of[code]]['short']}. A code can send a packet to one service only.")
        if len([x for x in att.codes if x.code.strip().upper() == code]) > 1:
            raise HTTPException(400, f"Code {code} is listed twice")
        if code in found:
            f = found[code]
            out.append(dict(code=code, description=f["description"], sources=[dict(article=i, version=arts[i]["version"], title=arts[i]["title"], mac=arts[i]["mac"], url=arts[i]["url"]) for i in f["listed_by"] if i in arts], note=None))
        elif c.source.strip():
            out.append(dict(code=code, description=c.description.strip() or None, sources=[], note="Added by the policy owner. Source: " + c.source.strip()[:300]))
        else:
            raise HTTPException(400, f"Say where code {code} came from. CMS did not list it for this policy.")
    return dict(service=att.service, codes=out, new_service=att.new_service, details=att.details)


def _covered(lib):
    return sorted({c for p in lib["procedures"].values() if p.get("status") != "planned" for c in p["cpts"]})


def _slug(s):
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")[:40] or "service"


def _fact_def(nf, ask=None):
    """A detail the AI proposed, in the shape the packet reader and the rules engine use. Yes or no details become an enum of yes and no."""
    kind, vals, sts = nf["kind"], list(nf.get("values") or []), [s.lower() for s in (nf.get("statuses") or [])]
    if kind == "enum" and not vals and sts:
        vals = [s for s in sts if s not in ("unknown", "missing", "found", "none")]
    if kind == "enum" and not vals:
        vals = ["yes", "no"]
    d = dict(key=nf["key"], label=nf["label"], kind=kind, phrase=nf["label"][:1].lower() + nf["label"][1:], ask=(ask or nf["ask"]).strip(), hint="")
    d["statuses"] = ["found", "implied", "missing"] if kind == "number" else ["found", "none", "missing"] if kind in ("list", "text", "event") else ["found", "missing"]
    if kind == "list" and vals:
        d["values"] = [v for v in vals if v != "none"]
    if kind == "enum":
        d["values"] = vals
    return d


def _is_yesno(d):
    return d["kind"] == "enum" and {str(v).lower() for v in d.get("values", [])} <= {"yes", "no", "not_applicable"} and "yes" in [str(v).lower() for v in d.get("values", [])]


def _make_service(att, lib, approved, draft, policy_id):
    """Creates the service in the library from the approved rules and the details they need. Returns its key."""
    new = {f["key"]: f for f in draft.get("new_facts", [])}
    asks = {d.key: d.ask for d in att["details"] if d.ask.strip()}
    used = []
    for x in approved:
        for k in (x.get("required_fact"), (x.get("applies_if") or {}).get("fact")):
            if k and k in new and k not in used:
                used.append(k)
    key = _slug(att["new_service"].short)
    if key in lib["procedures"]:
        raise HTTPException(400, "A service with that short name already exists")
    lib["procedures"][key] = dict(name=att["new_service"].name.strip(), short=att["new_service"].short.strip(), cpts=[], policies=[policy_id],
                                  facts=[_fact_def(new[k], asks.get(k)) for k in used], status="pilot")
    return key


def _apply_attach(att, lib, policy_id, who):
    """Adds the policy to the service's stack and the codes to its list, with their sources. Returns the codes added."""
    if not att:
        return []
    proc = lib["procedures"][att["service"]]  # for a new service, publish() has already created it and set att["service"] to its key
    if policy_id not in proc.setdefault("policies", []):
        proc["policies"].append(policy_id)
    added = []
    for c in att["codes"]:
        if c["code"] not in proc["cpts"]:
            proc["cpts"].append(c["code"])
            proc.setdefault("cpt_sources", []).append(dict(c, added_by=who, added_at=datetime.now(timezone.utc).strftime("%Y-%m-%d"), for_policy=policy_id))
            added.append(c["code"])
    lib["covered_cpt_codes"] = _covered(lib)
    return added


class CodeReq(BaseModel):
    code: str
    description: str = ""
    source: str = ""  # for a code the owner adds by hand: where it came from


class NewServiceReq(BaseModel):
    name: str = ""
    short: str = ""


class DetailReq(BaseModel):
    key: str
    ask: str = ""


class AttachReq(BaseModel):
    service: str = ""  # a service key, or "__new__" to create one
    codes: list[CodeReq] = []
    new_service: NewServiceReq | None = None
    details: list[DetailReq] = []


class PublishReq(BaseModel):
    confirm: bool = False
    note: str = ""
    attach: AttachReq | None = None


@router.post("/builds/{bid}/publish")
def publish(bid: str, body: PublishReq, request: Request):
    c, u = _owner(request)
    if not body.confirm:
        raise HTTPException(400, "Confirm that you want to change the live library")
    b = c.execute("SELECT * FROM policy_builds WHERE id=?", (bid,)).fetchone()
    if not b or b["status"] != "draft":
        raise HTTPException(400, "This draft is not open for publishing")
    draft = json.load(open(os.path.join(b["folder"], "draft.json"), encoding="utf-8"))
    meta = json.load(open(os.path.join(b["folder"], "meta.json"), encoding="utf-8"))
    dec = _decisions(c, bid)
    open_ = [x["id"] for x in draft["criteria"] if (dec.get(x["id"], {}).get("decision") or "pending") == "pending"]
    if open_:
        raise HTTPException(400, f"{len(open_)} rules still need a decision (approve or reject each one)")
    approved = [_effective(x, dec.get(x["id"])) for x in draft["criteria"] if dec[x["id"]]["decision"] == "approved"]
    if not approved:
        raise HTTPException(400, "Approve at least one rule to publish")
    lib = copy.deepcopy(procedures.raw())
    att = _check_attach(body.attach, lib, draft, b["folder"], meta["policy_id"])
    _snapshot(procedures.raw())
    pol = next((p for p in lib["policies"] if p["id"] == meta["policy_id"]), None)
    now_lib = procedures.library()
    new_key = None
    pol_facts = []  # key facts this policy adds. They are saved on the policy, and every service that uses the policy shows them.
    if att and att["service"] == "__new__":
        new_key = _make_service(att, lib, approved, draft, meta["policy_id"])
        att["service"] = new_key
        keys = {d["key"] for d in lib["procedures"][new_key]["facts"]}
    elif att:
        keys = {d["key"] for d in now_lib["procedures"][att["service"]]["facts"]}
        newmap = {f["key"]: f for f in draft.get("new_facts", [])}
        asks = {d.key: d.ask for d in att["details"] if d.ask.strip()}
        for x in approved:
            for k in (x.get("required_fact"), (x.get("applies_if") or {}).get("fact")):
                if k and k in newmap and k not in keys and k not in {d["key"] for d in pol_facts}:
                    pol_facts.append(_fact_def(newmap[k], asks.get(k)))
        if pol_facts and lib["procedures"][att["service"]].get("status", "live") == "live":
            raise HTTPException(400, "This service is live, and these rules need new key facts. Move the service back to pilot first.")
        keys |= {d["key"] for d in pol_facts}
    else:
        keys = _all_fact_keys(now_lib, None, meta["policy_id"])
    yesno = {d["key"] for p in list(lib["procedures"].values()) + list(now_lib["procedures"].values()) for d in p["facts"] if _is_yesno(d)} | {d["key"] for d in pol_facts if _is_yesno(d)}
    active = [x for x in approved if not _waiting(x, now_lib, keys)]
    held = [x for x in approved if _waiting(x, now_lib, keys)]
    conv = [_to_library(x, yesno) for x in active]
    held_rules = [dict(_to_library(x, yesno), needs_detail=[k for k in {x.get("required_fact"), (x.get("applies_if") or {}).get("fact")} if k and k not in keys]) for x in held]
    who = u["name"]
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if pol:
        change = _diff(pol.get("criteria", []), conv) if conv else dict(added=[], removed=[], changed=[], unchanged=len(pol.get("criteria", [])))
        if conv:  # a draft whose approved rules all wait for the packet reader never wipes the rules that are live
            pol["criteria"] = conv
        pol["waiting_rules"] = held_rules
        for d in pol_facts:
            if d["key"] not in {x["key"] for x in pol.setdefault("facts", [])}:
                pol["facts"].append(d)
        pol["verified"] = True
        pol["verified_from"] = f"Draft built {stamp} from {meta['source']} {meta['version']}, reviewed and approved by {who}"
    else:
        change = dict(added=[x["id"] for x in conv], removed=[], changed=[], unchanged=0)
        lib["policies"].append(dict(id=meta["policy_id"], level=meta["level"], answers="Q2_MEDICAL_NECESSITY", title=meta["title"], source=meta["source"], url=meta.get("url"),
                                    verified=True, verified_from=f"Draft built {stamp} from {meta['source']} {meta['version']}, reviewed and approved by {who}",
                                    applies_to="Not attached to a service yet. It does not affect any case until a service lists it.", criteria=conv, waiting_rules=held_rules, facts=pol_facts))
    attached_codes = _apply_attach(att, lib, meta["policy_id"], u["name"])
    lib["version"] = _bump(lib.get("version"))
    _snapshot(lib)
    _write_live(lib)
    c.execute("UPDATE policy_builds SET status='published' WHERE id=?", (bid,))
    c.execute("INSERT INTO policy_versions(library_version,kind,policy_id,build_id,published_by,published_at,changelog,note) VALUES(?,?,?,?,?,?,?,?)",
              (lib["version"], "publish", meta["policy_id"], bid, u["id"], db.now(), json.dumps(dict(change, approved=len(approved), rejected=len(draft["criteria"]) - len(approved), waiting=len(held), codes=attached_codes, service=att["service"] if att else None)), body.note.strip()[:300]))
    _log(c, u, "published", meta["policy_id"], bid, f"Library {lib['version']}: {len(active)} rules live, {len(held)} waiting, {len(draft['criteria']) - len(approved)} rejected" + (f"; attached to {att['service']} with codes {', '.join(attached_codes)}" if att and attached_codes else "") + (f". Note: {body.note.strip()}" if body.note.strip() else ""))
    c.commit()
    tel.event("policy.publish", **{"policy.id": meta["policy_id"], "policy.library_version": lib["version"], "policy.rules_approved": len(approved)})
    return dict(ok=True, version=lib["version"], change=change, waiting=len(held), codes=attached_codes, attached=bool(pol and _services(lib, pol["id"])) or bool(att))


# ---------- services ----------
class ServiceReq(BaseModel):
    name: str
    short: str
    scope: str = ""  # one sentence: which requests belong to this service
    codes: list[CodeReq] = []


def _bump_and_write(lib):
    lib["version"] = _bump(lib.get("version"))
    lib["covered_cpt_codes"] = _covered(lib)
    _snapshot(lib)
    _write_live(lib)


@router.post("/services")
def create_service(body: ServiceReq, request: Request):
    """A service on the rollout list: a name and its procedure codes with their sources. It is planned, so no packet is routed to it yet."""
    c, u = _owner(request)
    if not body.name.strip() or not body.short.strip():
        raise HTTPException(400, "Give the service a name and a short name")
    lib = copy.deepcopy(procedures.raw())
    key = _slug(body.short)
    if key in lib["procedures"]:
        raise HTTPException(400, "A service with that short name already exists")
    owner_of = {x: k for k, p in lib["procedures"].items() for x in p["cpts"]}
    src = []
    for cr in body.codes:
        code = cr.code.strip().upper()
        if not re.match(r"^([0-9]{5}|[A-Z][0-9]{4})$", code):
            raise HTTPException(400, f"{cr.code} is not a billing code. A code is 5 digits, or a letter and 4 digits.")
        if code in owner_of:
            raise HTTPException(400, f"Code {code} already belongs to {lib['procedures'][owner_of[code]]['short']}.")
        if not cr.source.strip():
            raise HTTPException(400, f"Say where code {code} came from")
        src.append(dict(code=code, description=cr.description.strip() or None, sources=[], note="Added by the policy owner. Source: " + cr.source.strip()[:300],
                        added_by=u["name"], added_at=datetime.now(timezone.utc).strftime("%Y-%m-%d")))
    lib["procedures"][key] = dict(name=body.name.strip(), short=body.short.strip(), scope=body.scope.strip()[:300], cpts=[s["code"] for s in src], policies=[], facts=[], status="planned", cpt_sources=src)
    _snapshot(procedures.raw())
    _bump_and_write(lib)
    c.execute("INSERT INTO policy_versions(library_version,kind,policy_id,build_id,published_by,published_at,changelog,note) VALUES(?,?,?,?,?,?,?,?)",
              (lib["version"], "service", None, None, u["id"], db.now(), None, f"Added {body.short.strip()} to the rollout list"))
    _log(c, u, "service_created", None, None, f"{body.short.strip()}: planned, codes {', '.join(s['code'] for s in src) or 'none yet'}")
    c.commit()
    return dict(ok=True, key=key, version=lib["version"])


# ---------- one service ----------
def _svc(lib, key):
    p = lib["procedures"].get(key)
    if not p:
        raise HTTPException(404, "Service not found")
    return p


def _publish_service_change(c, u, lib, key, what, audit_action):
    """One saved version for a change to a service: snapshot, bump, write, record."""
    _snapshot(procedures.raw())
    _bump_and_write(lib)
    c.execute("INSERT INTO policy_versions(library_version,kind,policy_id,build_id,published_by,published_at,changelog,note) VALUES(?,?,?,?,?,?,?,?)",
              (lib["version"], "service", None, None, u["id"], db.now(), None, what))
    _log(c, u, audit_action, None, None, what)
    c.commit()
    return lib["version"]


def _rules_build(c, policy_id):
    """The draft that holds a policy's rules beside their exact quotes: the one that was approved, else the latest open draft. None for a policy written by hand."""
    r = c.execute("SELECT id, status FROM policy_builds WHERE policy_id=? AND status IN ('published','draft') ORDER BY (status='published') DESC, created_at DESC LIMIT 1", (policy_id,)).fetchone()
    return dict(id=r["id"], status=r["status"]) if r else None


@router.get("/services/{key}")
def service_detail(key: str, request: Request):
    """Everything about one service on one page: its codes, its policies, the key facts they add up to, and what happened to it."""
    c, u = _owner(request)
    lib = procedures.library()
    p = _svc(lib, key)
    r = procedures.raw()["procedures"][key]
    pols = {x["id"]: x for x in lib["policies"]}
    used = {}  # key fact -> the policies whose rules test it
    for pid in p.get("policies", []):
        for cr in pols.get(pid, {}).get("criteria", []) + pols.get(pid, {}).get("waiting_rules", []):
            for k in (cr.get("required_fact"), (cr.get("applies_if") or {}).get("fact")):
                if k and pid not in used.setdefault(k, []):
                    used[k].append(pid)
    attached = []
    for pid in p.get("policies", []):
        x = pols.get(pid)
        if x:
            attached.append(dict(id=pid, title=x["title"], level=x["level"], source=x["source"], url=x.get("url"), rules=len(x.get("criteria", [])), waiting=len(x.get("waiting_rules", [])),
                                 verified=bool(x.get("verified")), n_facts=len(x.get("facts", [])), note=x.get("verified_from") or x.get("applies_to"), build=_rules_build(c, pid)))
    drafts = [dict(r2) for r2 in c.execute("SELECT id, kind, ident, policy_id, status, stage, created_at FROM policy_builds WHERE service=? AND status IN ('running','draft','error') ORDER BY created_at DESC", (key,))]
    seen = {x[0]: x[1] for x in c.execute("SELECT cpt, COUNT(*) FROM cases GROUP BY cpt")}
    short = p["short"]
    acts = [dict(at=a["at"], who=a["who"], action=a["action"], detail=a["detail"]) for a in c.execute("SELECT a.*, u.name AS who FROM policy_audit a LEFT JOIN users u ON u.id=a.user_id WHERE a.detail LIKE ? ORDER BY a.id DESC LIMIT 12", (f"%{short}%",))]
    return dict(key=key, name=p["name"], short=short, scope=p.get("scope") or "", status=p.get("status", "live"), note=p.get("status_note"), version=lib.get("version"),
                codes=[dict(code=x, source=next((y for y in r.get("cpt_sources", []) if y["code"] == x), None)) for x in p["cpts"]],
                other_codes=len(p.get("cms_other_codes", [])), checked=p.get("cpt_checked"),
                policies=attached, drafts=drafts,
                facts=[dict(key=d["key"], label=d["label"], ask=d.get("ask") or "", kind=d["kind"], used_by=used.get(d["key"], []), from_policy=d.get("from_policy")) for d in p["facts"]],
                n_cases=sum(seen.get(x, 0) for x in p["cpts"]), activity=acts)


_STOP = {"with", "from", "that", "this", "inpatient", "outpatient", "surgery", "procedure", "service", "treatment", "therapy", "for", "and", "the", "of"}


@router.get("/services/{key}/suggestions")
def suggestions(key: str, request: Request, q: str = ""):
    """Policies that may apply to this service. Today they come from the service name and what the owner types, matched against the CMS lists the
    back end keeps, plus every policy already in the library. Matching from the service's codes needs a code index of the CMS articles, a back-end job
    that is not built yet."""
    c, u = _owner(request)
    lib = procedures.library()
    p = _svc(lib, key)
    mine = set(p.get("policies", []))
    ns, ss = cms_codes.stems(q or p["name"]), cms_codes.stems("" if q else p.get("scope") or "")
    out = []
    for x in lib["policies"]:
        if x["id"] in mine:
            continue
        sc = cms_codes.rank(x["id"] + " " + x["title"], ns, ss)
        out.append(dict(policy_id=x["id"], title=x["title"], level=x["level"], in_library=True, rules=len(x.get("criteria", [])), verified=bool(x.get("verified")), kind=None, ident=None, effective=None, match=sc > 0, _s=sc))
    out.sort(key=lambda o: -o["_s"])
    cms = []
    if ns:
        in_lib = {x["id"] for x in lib["policies"]}
        for kind in ("ncd", "lcd"):
            rows, as_of = _corpus(kind)
            pre = "NCD-" if kind == "ncd" else "LCD-"
            for r2 in rows:
                if pre + r2["id"] in in_lib:
                    continue
                sc = cms_codes.rank(r2["id"] + " " + r2["title"], ns, ss)
                if sc:
                    cms.append((sc, dict(policy_id=pre + r2["id"], title=r2["title"], level=kind.upper(), in_library=False, rules=0, verified=False, kind=kind, ident=r2["id"], effective=r2.get("effective"))))
        cms.sort(key=lambda t: (-t[0], t[1]["title"]))
        seen, uniq = set(), []
        for sc, row in cms:  # one row per title: the same policy is published by several regional contractors
            k = (row["kind"], row["title"].lower())
            if k not in seen:
                seen.add(k); uniq.append((sc, row))
        cms = uniq
    if q:
        toks = [t for t in q.lower().split() if t]
        out = [o for o in out if all(t in (o["policy_id"] + " " + o["title"]).lower() for t in toks)]
    for o in out:
        o.pop("_s", None)
    return dict(library=out[:8], cms=[x[1] for x in cms[:8]], asked=bool(q))


class AttachPolicyReq(BaseModel):
    policy_id: str


@router.post("/services/{key}/policies")
def attach_policy(key: str, body: AttachPolicyReq, request: Request):
    """Adds a policy that is already in the library to this service. A live service cannot change its policies: move it back to pilot first."""
    c, u = _owner(request)
    lib = copy.deepcopy(procedures.raw())
    p = _svc(lib, key)
    pol = next((x for x in lib["policies"] if x["id"] == body.policy_id), None)
    if not pol:
        raise HTTPException(404, "That policy is not in the library. Build it first.")
    if body.policy_id in p.get("policies", []):
        raise HTTPException(400, "This policy is already on the service")
    if p.get("status", "live") == "live":
        raise HTTPException(400, "This service is live. Move it back to pilot before you change its policies.")
    have = {d["key"] for d in procedures.library()["procedures"][key]["facts"]} | {d["key"] for d in pol.get("facts", [])}
    need = sorted({k for cr in pol.get("criteria", []) for k in (cr.get("required_fact"), (cr.get("applies_if") or {}).get("fact")) if k and k not in have})
    if need:
        raise HTTPException(400, "This policy's rules need key facts this service does not have yet: " + ", ".join(x.replace("_", " ") for x in need) + ". Build the policy again for this service so the system can add them.")
    brings = [d["label"] for d in pol.get("facts", []) if d["key"] not in {x["key"] for x in procedures.library()["procedures"][key]["facts"]}]
    p.setdefault("policies", []).append(body.policy_id)
    ver = _publish_service_change(c, u, lib, key, f"{p['short']}: added policy {body.policy_id}", "service_policy_added")
    return dict(ok=True, version=ver, brings=brings, rules=len(pol.get("criteria", [])))


@router.post("/services/{key}/policies/{policy_id}/remove")
def detach_policy(key: str, policy_id: str, request: Request):
    c, u = _owner(request)
    lib = copy.deepcopy(procedures.raw())
    p = _svc(lib, key)
    if policy_id not in p.get("policies", []):
        raise HTTPException(404, "This policy is not on the service")
    if p.get("status", "live") == "live":
        raise HTTPException(400, "This service is live. Move it back to pilot before you change its policies.")
    p["policies"].remove(policy_id)
    ver = _publish_service_change(c, u, lib, key, f"{p['short']}: removed policy {policy_id}", "service_policy_removed")
    return dict(ok=True, version=ver)


@router.post("/services/{key}/codes")
def add_service_code(key: str, body: CodeReq, request: Request):
    c, u = _owner(request)
    lib = copy.deepcopy(procedures.raw())
    p = _svc(lib, key)
    if p.get("status", "live") == "live":
        raise HTTPException(400, "This service is live. Move it back to pilot before you change its codes.")
    code = body.code.strip().upper()
    if not re.match(r"^([0-9]{5}|[A-Z][0-9]{4})$", code):
        raise HTTPException(400, f"{body.code} is not a billing code. A code is 5 digits, or a letter and 4 digits.")
    owner_of = {x: k for k, q in lib["procedures"].items() for x in q["cpts"]}
    if code in owner_of:
        raise HTTPException(400, f"Code {code} already sends packets to {lib['procedures'][owner_of[code]]['short']}. A code can belong to one service only.")
    if not body.source.strip():
        raise HTTPException(400, f"Say where code {code} came from")
    p["cpts"].append(code)
    p.setdefault("cpt_sources", []).append(dict(code=code, description=body.description.strip() or None, sources=[], note="Added by the policy owner. Source: " + body.source.strip()[:300],
                                                 added_by=u["name"], added_at=datetime.now(timezone.utc).strftime("%Y-%m-%d")))
    ver = _publish_service_change(c, u, lib, key, f"{p['short']}: added code {code}", "service_code_added")
    return dict(ok=True, version=ver)


# ---------- billing codes suggested from CMS ----------
def _code_rows(lib, key, rows):
    """Codes with whether this service already has them, or another service does."""
    owner_of = {x: k for k, q in lib["procedures"].items() for x in q["cpts"]}
    out = []
    for r in rows:
        o = owner_of.get(r["code"])
        out.append(dict(r, taken=None if not o else ("this" if o == key else lib["procedures"][o]["short"])))
    return out


@router.get("/services/{key}/code-suggestions")
def code_suggestions(key: str, request: Request, q: str = ""):
    """Where the owner can get billing codes from, with the source already attached:
    1. the policies already on the service (the codes CMS listed when each policy was built), and
    2. CMS Billing and Coding articles whose title matches the service name, or what the owner types."""
    c, u = _owner(request)
    lib = procedures.library()
    p = _svc(lib, key)
    from_pol = []
    for pid in p.get("policies", []):
        base = os.path.join(S.WORK, pid)
        if not os.path.isdir(base):
            continue
        path = os.path.join(base, sorted(os.listdir(base))[-1], "codes.json")
        if not os.path.exists(path):
            continue
        cd = json.load(open(path, encoding="utf-8"))
        if cd.get("codes"):
            x = next((y for y in lib["policies"] if y["id"] == pid), {})
            arts = {a["id"]: a for a in cd.get("articles", [])}
            rows = [dict(code=r["code"], description=r["description"], short=r.get("short", ""), group=r.get("group"), sources=[arts[i] for i in r["listed_by"] if i in arts][:3]) for r in cd["codes"]]
            from_pol.append(dict(policy_id=pid, title=x.get("title", pid), note=cd.get("note", ""), codes=_code_rows(lib, key, rows)))
    arts, note = cms_codes.search_articles(q or p["name"], "" if q else p.get("scope") or "")
    return dict(from_policies=from_pol, articles=arts, note=note, asked=bool(q))


@router.get("/services/{key}/code-consensus")
def code_consensus(key: str, request: Request, q: str = ""):
    """The codes that most of the matching CMS articles list, most agreed first."""
    c, u = _owner(request)
    lib = procedures.library()
    p = _svc(lib, key)
    arts, note = cms_codes.search_articles(q or p["name"], "" if q else p.get("scope") or "")
    best = max((a["match_score"] for a in arts), default=0)
    rows, n = cms_codes.consensus([a for a in arts if a["match_score"] >= best], top=20)  # every article that fits the name as well as the best one, and none that fit worse
    return dict(read=n, codes=_code_rows(lib, key, [dict(r, n_articles=r["n_articles"]) for r in rows[:40]]))


@router.get("/services/{key}/code-article")
def code_article(key: str, aid: str, ver: int, request: Request):
    c, u = _owner(request)
    lib = procedures.library()
    _svc(lib, key)
    ref, rows, note = cms_codes.codes_of_article(aid, ver)
    if not ref:
        raise HTTPException(502, note or "Could not read the article")
    return dict(article=ref, note=note, codes=_code_rows(lib, key, [dict(r, sources=[ref]) for r in rows]))


class CmsCode(BaseModel):
    code: str
    description: str = ""
    sources: list[dict] = []


class CmsCodesReq(BaseModel):
    codes: list[CmsCode]


@router.post("/services/{key}/codes/from-cms")
def add_codes_from_cms(key: str, body: CmsCodesReq, request: Request):
    """Adds the codes the owner ticked. Each keeps the CMS article it came from."""
    c, u = _owner(request)
    lib = copy.deepcopy(procedures.raw())
    p = _svc(lib, key)
    if p.get("status", "live") == "live":
        raise HTTPException(400, "This service is live. Move it back to pilot before you change its codes.")
    owner_of = {x: k for k, q in lib["procedures"].items() for x in q["cpts"]}
    added = []
    for cc in body.codes:
        code = cc.code.strip().upper()
        if not re.match(r"^([0-9]{5}|[A-Z][0-9]{4})$", code):
            raise HTTPException(400, f"{cc.code} is not a billing code")
        if code in p["cpts"]:
            continue
        if code in owner_of:
            raise HTTPException(400, f"Code {code} already sends packets to {lib['procedures'][owner_of[code]]['short']}. A code can belong to one service only.")
        srcs = [dict(article=str(a.get("id", ""))[:20], version=a.get("version"), title=str(a.get("title", ""))[:200], mac=str(a.get("mac", ""))[:120], url=a.get("url"))
                for a in cc.sources[:3] if str(a.get("url", "")).startswith("https://www.cms.gov/")]
        if not srcs:
            raise HTTPException(400, f"Code {code} has no CMS article as its source")
        p["cpts"].append(code)
        p.setdefault("cpt_sources", []).append(dict(code=code, description=cc.description.strip() or None, sources=srcs, note=None, added_by=u["name"], added_at=datetime.now(timezone.utc).strftime("%Y-%m-%d")))
        added.append(code)
    if not added:
        raise HTTPException(400, "Nothing new to add")
    ver = _publish_service_change(c, u, lib, key, f"{p['short']}: added codes {', '.join(added)} from CMS", "service_code_added")
    return dict(ok=True, version=ver, added=added)


@router.post("/services/{key}/codes/{code}/remove")
def remove_service_code(key: str, code: str, request: Request):
    c, u = _owner(request)
    lib = copy.deepcopy(procedures.raw())
    p = _svc(lib, key)
    if p.get("status", "live") == "live":
        raise HTTPException(400, "This service is live. Move it back to pilot before you change its codes.")
    if code not in p["cpts"]:
        raise HTTPException(404, "That code is not on the service")
    p["cpts"].remove(code)
    p["cpt_sources"] = [x for x in p.get("cpt_sources", []) if x["code"] != code]
    ver = _publish_service_change(c, u, lib, key, f"{p['short']}: removed code {code}", "service_code_removed")
    return dict(ok=True, version=ver)


class StatusReq(BaseModel):
    status: str
    note: str = ""
    confirm: bool = False


@router.post("/services/{key}/status")
def set_service_status(key: str, body: StatusReq, request: Request):
    """planned -> pilot -> live, and back. A service needs a policy with rules, its details and a code before it can be a pilot.
    Going live needs a written note on what was tested."""
    c, u = _owner(request)
    lib = copy.deepcopy(procedures.raw())
    p = lib["procedures"].get(key)
    if not p:
        raise HTTPException(404, "Service not found")
    now = p.get("status", "live")
    if body.status not in ("planned", "pilot", "live") or body.status == now:
        raise HTTPException(400, "Choose a different status")
    if not body.confirm:
        raise HTTPException(400, "Confirm the change")
    pols = {x["id"]: x for x in lib["policies"]}
    if body.status in ("pilot", "live"):
        problems = []
        if not p["cpts"]:
            problems.append("it has no billing codes")
        if not any(pols.get(i, {}).get("criteria") for i in p.get("policies", [])):
            problems.append("it has no policy with approved rules")
        if not procedures.library()["procedures"][key]["facts"]:
            problems.append("it has no key facts for the packet reader to find")
        if problems:
            raise HTTPException(400, "This service cannot start yet: " + "; ".join(problems) + ".")
    if body.status == "live" and len(body.note.strip()) < 10:
        raise HTTPException(400, "Write what was tested before this service goes live (at least a sentence)")
    p["status"] = body.status
    p["status_note"] = body.note.strip()[:300] or None
    _snapshot(procedures.raw())
    _bump_and_write(lib)
    c.execute("INSERT INTO policy_versions(library_version,kind,policy_id,build_id,published_by,published_at,changelog,note) VALUES(?,?,?,?,?,?,?,?)",
              (lib["version"], "service", None, None, u["id"], db.now(), None, f"{p['short']}: {now} to {body.status}" + (f". {body.note.strip()}" if body.note.strip() else "")))
    _log(c, u, "service_status", None, None, f"{p['short']}: {now} to {body.status}" + (f". {body.note.strip()}" if body.note.strip() else ""))
    c.commit()
    return dict(ok=True, version=lib["version"])


# ---------- requests that had no policy ----------
@router.get("/demand")
def demand(request: Request):
    """Open cases that arrived with a procedure we do not cover, grouped by procedure code. This is the owner's list of what to onboard next."""
    c, u = _owner(request)
    lib = procedures.library()
    svc_of = {x: p for p in lib["procedures"].values() for x in p["cpts"]}
    groups = {}
    for r in c.execute("SELECT id, cpt, procedure_name, received_at, analysis FROM cases WHERE status NOT IN ('approved','denied') ORDER BY received_at"):
        if json.loads(r["analysis"]).get("action") != "no_policy":
            continue
        g = groups.setdefault(r["cpt"] or "unknown", dict(code=r["cpt"] or "unknown", what=r["procedure_name"], n=0, oldest=r["received_at"], cases=[]))
        g["n"] += 1
        g["cases"].append(r["id"])
    out = sorted(groups.values(), key=lambda g: (-g["n"], g["oldest"]))
    for g in out:
        g["cases"] = g["cases"][:6]
        p = svc_of.get(g["code"])
        g["service"] = p["short"] if p else None
        g["service_status"] = p.get("status", "live") if p else None
    return dict(rows=out)


# ---------- versions ----------
def _versions(c):
    return [dict(n=r["n"], version=r["library_version"], kind=r["kind"], policy_id=r["policy_id"], build_id=r["build_id"], at=r["published_at"], who=r["who"], note=r["note"],
                 changelog=json.loads(r["changelog"]) if r["changelog"] else None)
            for r in c.execute("SELECT v.*, u.name AS who FROM policy_versions v LEFT JOIN users u ON u.id=v.published_by ORDER BY v.n DESC LIMIT 50")]


@router.get("/audit")
def audit(request: Request):
    c, u = _owner(request)
    rows = [dict(at=r["at"], who=r["who"], action=r["action"], policy_id=r["policy_id"], build_id=r["build_id"], detail=r["detail"])
            for r in c.execute("SELECT a.*, u.name AS who FROM policy_audit a LEFT JOIN users u ON u.id=a.user_id ORDER BY a.id DESC LIMIT 300")]
    return dict(rows=rows, versions=_versions(c), version=procedures.library().get("version"))


class RevertReq(BaseModel):
    version: str
    confirm: bool = False


@router.post("/revert")
def revert(body: RevertReq, request: Request):
    c, u = _owner(request)
    if not body.confirm:
        raise HTTPException(400, "Confirm that you want to go back")
    path = os.path.join(VERSIONS_DIR, f"{body.version}.json")
    if not re.match(r"^[0-9.]+$", body.version) or not os.path.exists(path):
        raise HTTPException(404, "That version was not saved")
    lib = json.load(open(path, encoding="utf-8"))
    _write_live(lib)
    c.execute("INSERT INTO policy_versions(library_version,kind,policy_id,build_id,published_by,published_at,changelog,note) VALUES(?,?,?,?,?,?,?,?)",
              (lib["version"], "revert", None, None, u["id"], db.now(), None, f"Went back to version {lib['version']}"))
    _log(c, u, "reverted", None, None, f"Went back to library version {lib['version']}")
    c.commit()
    return dict(ok=True, version=lib["version"])


# ---------- is the source still the same? ----------
@router.post("/{policy_id}/check-update")
def check_update(policy_id: str, request: Request):
    c, u = _owner(request)
    f = _fetchable(policy_id)
    if not f:
        raise HTTPException(400, "This policy has no online source to check. Upload a new PDF instead.")
    kind, ident = f
    try:
        src = {"ncd": S.fetch_ncd, "lcd": S.fetch_lcd}[kind](ident) if kind in ("ncd", "lcd") else S.fetch_cfr(*ident)
    except Exception as e:
        raise HTTPException(502, f"Could not reach the source: {type(e).__name__}")
    import hashlib
    new = hashlib.sha256(src["text"].encode("utf-8")).hexdigest()
    old, at = _latest_hash(policy_id)
    _log(c, u, "checked_for_update", policy_id, None, "Source changed since the last saved copy" if old and old != new else ("Source is the same" if old else "No earlier copy to compare"))
    c.commit()
    return dict(checked_at=db.now(), source=src["source"], version=src["version"], effective=src.get("effective"),
                changed=None if not old else old != new, last_saved=at,
                note=("No earlier copy to compare with. Build a draft to save one." if not old else ("The source text has changed since the last saved copy." if old != new else "The source text is the same as the last saved copy.")))
