"""A stored copy of the CMS billing articles and the codes each one lists.

Why: the screens used to call the CMS website while a person waited (about 10 seconds the first time, and calls sometimes dropped).
A scheduled job (scripts/refresh_cms_index.py) now copies the articles and their codes into the database. The screens read only the database.
If the copy has not been made yet, every function here falls back to the live CMS call, so nothing breaks.

Tables (app/db.py): cms_articles (one row per article version) and cms_article_codes (one row per code on an article).
"""
import time
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
