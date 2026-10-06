"""A stored copy of the CMS billing articles and the codes each one lists.

Why: the screens used to call the CMS website while a person waited (about 10 seconds the first time, and calls sometimes dropped).
A scheduled job (scripts/refresh_cms_index.py) now copies the articles and their codes into the database. The screens read only the database.
If the copy has not been made yet, every function here falls back to the live CMS call, so nothing breaks.

Tables (app/db.py): cms_articles (one row per article version) and cms_article_codes (one row per code on an article).
Also the national (NCD) and local (LCD) coverage policies with their coverage text: table cms_policies (one row per policy).
"""
import json, os, re, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

from . import codes as C, sources as S


def _kept(a):
    t = (a.get("title") or "").lower()
    return t.startswith("billing and coding") or "policy article" in t  # equipment (DME) policies list their codes in a Policy Article


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sync(c, limit=None, workers=6, log=print):
    """Copies the article list, then the codes of every article that is new or has a new version. Safe to run again and again."""
    tok = S._cms_token()
    rows = [a for a in C._articles(tok) if _kept(a)]
    log(f"CMS lists {len(rows)} billing articles")
    for a in rows:
        did, ver = int(a["document_id"]), int(a["document_version"])
        c.execute("""INSERT INTO cms_articles(document_id,version,display_id,title,mac,updated_on) VALUES(?,?,?,?,?,?)
                     ON CONFLICT(document_id,version) DO UPDATE SET display_id=excluded.display_id, title=excluded.title, mac=excluded.mac, updated_on=excluded.updated_on""",
                  (did, ver, a.get("document_display_id") or f"A{did}", a["title"], C._mac(a), a.get("updated_on")))
        c.execute("DELETE FROM cms_article_codes WHERE document_id=? AND version<>?", (did, ver))  # an older version of the same article is dropped
        c.execute("DELETE FROM cms_articles WHERE document_id=? AND version<>?", (did, ver))
    c.commit()
    todo = [r for r in c.execute("SELECT document_id, version FROM cms_articles WHERE codes_at IS NULL")]
    if limit:
        todo = todo[:limit]
    log(f"{len(todo)} articles need their codes")

    def one(r):
        try:
            return r, C._article_codes(tok, r["document_id"], r["version"]), None
        except Exception as e:
            return r, None, f"{type(e).__name__}"
    done = failed = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for fut in as_completed([ex.submit(one, r) for r in todo]):
            r, cs, err = fut.result()
            if err:
                failed += 1  # left without a date, so the next run tries again
                continue
            for x in cs:
                c.execute("INSERT OR REPLACE INTO cms_article_codes(document_id,version,code,description,short,grp) VALUES(?,?,?,?,?,?)",
                          (r["document_id"], r["version"], x["code"], x["description"], x.get("short", ""), x.get("group")))
            c.execute("UPDATE cms_articles SET codes_at=? WHERE document_id=? AND version=?", (_now(), r["document_id"], r["version"]))
            done += 1
            if done % 50 == 0:
                c.commit()
                log(f"  {done} of {len(todo)}")
    c.commit()
    c.execute("INSERT OR REPLACE INTO cms_meta(key,value) VALUES('synced_at',?)", (_now(),))
    c.commit()
    n = c.execute("SELECT COUNT(*) FROM cms_article_codes").fetchone()[0]
    log(f"Done. {done} articles read, {failed} failed (they are tried again next run). {n} codes stored.")
    return dict(articles=len(rows), read=done, failed=failed, codes=n)


def ready(c):
    """True when the copy exists and holds codes."""
    try:
        return bool(c.execute("SELECT 1 FROM cms_meta WHERE key='synced_at'").fetchone()) and c.execute("SELECT COUNT(*) FROM cms_articles WHERE codes_at IS NOT NULL").fetchone()[0] > 0
    except Exception:
        return False


def as_of(c):
    try:
        r = c.execute("SELECT value FROM cms_meta WHERE key='synced_at'").fetchone()
        return r[0][:10] if r else None
    except Exception:
        return None


def _ref(r, score=None):
    return dict(id=r["display_id"], version=r["version"], title=C._plain(r["title"]), mac=r["mac"], url=C.ARTICLE_URL.format(id=r["document_id"], ver=r["version"]),
                match_score=score, cites_ncd=None, n_codes=0, aid=r["document_id"])


def search_articles(c, query, scope="", limit=14):
    if not ready(c):
        return C.search_articles(query, scope, limit)
    ns, ss = C.stems(query), C.stems(scope)
    if not ns:
        return [], "Type a word or two from the service name."
    scored = []
    for r in c.execute("SELECT * FROM cms_articles WHERE codes_at IS NOT NULL"):
        sc = C.rank(C._plain(r["title"]), ns, ss)
        if sc:
            scored.append((sc, r))
    scored.sort(key=lambda x: (-x[0], x[1]["title"]))
    out, seen = [], set()
    for sc, r in scored:
        k = (C._plain(r["title"]).lower(), r["mac"])
        if k in seen:
            continue
        seen.add(k)
        out.append(_ref(r, round(sc * 100)))
        if len(out) >= limit:
            break
    return out, "" if out else "No Billing and Coding article matches these words. Try other words, or add the code yourself."


def codes_of_article(c, aid, ver):
    if not ready(c):
        return C.codes_of_article(aid, ver)
    r = c.execute("SELECT * FROM cms_articles WHERE document_id=? AND version=?", (aid, ver)).fetchone()
    if not r:
        return C.codes_of_article(aid, ver)
    rows = [dict(code=x["code"], description=x["description"], short=x["short"], group=x["grp"]) for x in c.execute("SELECT * FROM cms_article_codes WHERE document_id=? AND version=? ORDER BY code", (aid, ver))]
    return _ref(r), rows, ""


def consensus(c, articles, top=8):
    if not ready(c):
        return C.consensus(articles, top)
    got = []
    for a in articles[:top]:
        rows = [dict(code=x["code"], description=x["description"], short=x["short"], group=x["grp"]) for x in c.execute("SELECT * FROM cms_article_codes WHERE document_id=? AND version=?", (a["aid"], a["version"]))]
        if rows:
            got.append((a, rows))
    out = C._collect(got)
    srcs = {a["id"]: a for a, _ in got}
    for r in out:
        r["sources"] = [srcs[i] for i in r["listed_by"] if i in srcs][:3]
    out.sort(key=lambda r: ((r["group"] or 1) > 1, -r["n_articles"], r["code"]))
    return out, len(got)


def articles_listing(c, codes):
    """Which stored articles list at least one of these codes, and how many of them. Used to suggest the policy that goes with a set of codes."""
    codes = [x for x in codes if x]
    if not codes or not ready(c):
        return []
    q = ",".join("?" * len(codes))
    return [dict(r) for r in c.execute(f"""SELECT a.document_id, a.version, a.display_id, a.title, a.mac, COUNT(DISTINCT k.code) AS n
                                          FROM cms_article_codes k JOIN cms_articles a ON a.document_id=k.document_id AND a.version=k.version
                                          WHERE k.code IN ({q}) GROUP BY a.document_id, a.version ORDER BY n DESC, a.title LIMIT 20""", codes)]


# ---------- national and local coverage policies ----------
ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
_KIND = {"NCD": "/reports/national-coverage-ncd/", "LCD": "/reports/local-coverage-final-lcds/"}
_COLS = "kind,id,version,document_id,title,mac,effective,description,indications,summary,url,fetched_at"


def import_corpus_json(c, root=ROOT):
    """One-time start: loads the policies already downloaded to policies/corpus/*.json, with no call to CMS. Returns the number of rows."""
    n = 0
    for kind, f in (("NCD", "ncds.json"), ("LCD", "lcds.json")):
        path = os.path.join(root, "policies", "corpus", f)
        if not os.path.exists(path):
            continue
        for x in json.load(open(path, encoding="utf-8")):
            if "error" in x:
                continue
            m = re.search(r"(?:lcdid|ncdid)=(\d+)", x.get("url") or "")
            c.execute(f"INSERT OR IGNORE INTO cms_policies({_COLS}) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                      (kind, x["id"], str(x.get("version")), int(m[1]) if m else None, x.get("title"), x.get("mac"), x.get("effective"), x.get("description"), x.get("indications"),
                       x.get("summary"), x.get("url"), "2026-10-04T00:00:00+00:00"))
            n += 1
    c.commit()
    return n


def _fetch_policy(tok, kind, r):
    for attempt in range(3):
        try:
            if kind == "LCD":
                d = S._cms(f"/data/lcd/?lcdid={r['document_id']}&ver={r['document_version']}", tok)["data"][0]
                return dict(kind=kind, id=r["document_display_id"], version=str(r["document_version"]), document_id=int(r["document_id"]), title=r["title"], mac=S.clean(r.get("contractor_name_type")),
                            effective=d.get("rev_eff_date") or r.get("effective_date"), description=None, indications=S.clean(d.get("indication")), summary=S.clean(d.get("cms_cov_policy")),
                            url=f"https://www.cms.gov/medicare-coverage-database/view/lcd.aspx?lcdid={r['document_id']}")
            d = S._cms(f"/data/ncd/?ncdid={r['document_id']}&ncdver={r['document_version']}", tok)["data"][0]
            return dict(kind=kind, id=r["document_display_id"], version=str(r["document_version"]), document_id=int(r["document_id"]), title=r["title"], mac=None, effective=d.get("effective_date"),
                        description=S.clean(d.get("item_service_description")), indications=S.clean(d.get("indications_limitations")), summary=None,
                        url=f"https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?ncdid={r['document_id']}")
        except Exception:
            time.sleep(1.5)
    return None


def sync_policies(c, workers=8, limit=None, log=print):
    """Reads the CMS lists of NCDs and LCDs and fetches only the policies that are new or have a new version. Policies CMS no longer lists are removed."""
    tok = S._cms_token()
    fetched = removed = failed = 0
    for kind, path in _KIND.items():
        idx = S._cms(path, tok)["data"]
        have = {r["id"]: r["version"] for r in c.execute("SELECT id, version FROM cms_policies WHERE kind=?", (kind,))}
        todo = [r for r in idx if have.get(r["document_display_id"]) != str(r["document_version"])]
        if limit:
            todo = todo[:limit]
        log(f"{kind}: CMS lists {len(idx)}, {len(todo)} are new or changed")
        with ThreadPoolExecutor(max_workers=workers) as ex:
            for row in ex.map(lambda r: _fetch_policy(tok, kind, r), todo):
                if not row:
                    failed += 1
                    continue
                c.execute(f"INSERT OR REPLACE INTO cms_policies({_COLS}) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                          (row["kind"], row["id"], row["version"], row["document_id"], row["title"], row["mac"], row["effective"], row["description"], row["indications"],
                           row["summary"], row["url"], _now()))
                fetched += 1
        if not limit:
            live = {r["document_display_id"] for r in idx}
            gone = [i for i in have if i not in live]
            for i in gone:
                c.execute("DELETE FROM cms_policies WHERE kind=? AND id=?", (kind, i))
            removed += len(gone)
        c.commit()
    c.execute("INSERT OR REPLACE INTO cms_meta(key,value) VALUES('policies_synced_at',?)", (_now(),))
    c.commit()
    log(f"Policies done. {fetched} fetched, {removed} removed, {failed} failed (tried again next run).")
    return dict(fetched=fetched, removed=removed, failed=failed)


def policy_titles(c, kind):
    """(rows, as_of) for the policy picker: id, title and effective date of every NCD or LCD. Falls back to the downloaded files when the table is empty."""
    kind = kind.upper()
    rows = [dict(id=r["id"], title=r["title"] or "", effective=r["effective"]) for r in c.execute("SELECT id, title, effective FROM cms_policies WHERE kind=?", (kind,))]
    if rows:
        r = c.execute("SELECT value FROM cms_meta WHERE key='policies_synced_at'").fetchone() or c.execute("SELECT MAX(fetched_at) FROM cms_policies").fetchone()
        return rows, (r[0] or "")[:10]
    path = os.path.join(ROOT, "policies", "corpus", "ncds.json" if kind == "NCD" else "lcds.json")
    rows = [dict(id=x["id"], title=x.get("title", ""), effective=x.get("effective")) for x in json.load(open(path, encoding="utf-8")) if "error" not in x]
    return rows, "file"
