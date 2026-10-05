"""Step 1b of the policy build: find the procedure codes (CPT and HCPCS) that go with a policy, and say where each one came from.

A policy's own text rarely lists billing codes. CMS publishes them in separate "Billing and Coding" articles that sit beside the policy.
  LCD  The Coverage API links each LCD to its articles (related-documents). Each article has a list of codes (hcpc-code).
  NCD  The API does not link an NCD to its articles. We find the Billing and Coding articles whose title matches the NCD title,
       and mark the ones whose text names the NCD number. A person confirms before anything is used.
  CFR, uploaded file  No code source. The owner adds codes by hand and says where each came from.

Nothing here decides anything. It lists codes with their sources. The owner picks which ones to use.
"""
import html, re, time
from datetime import datetime, timezone

from rapidfuzz import fuzz

from . import sources as S

ARTICLE_URL = "https://www.cms.gov/medicare-coverage-database/view/article.aspx?articleid={id}&ver={ver}"
MIN_TITLE_SCORE = 70
MAX_ARTICLES = 6
_cache = {}


def _articles(tok):
    """All CMS articles (Billing and Coding, Policy Articles and others). About 2,200 rows, kept for an hour."""
    hit = _cache.get("articles")
    if hit and time.time() - hit[0] < 3600:
        return hit[1]
    rows = S._cms("/reports/local-coverage-articles/", tok)["data"]
    _cache["articles"] = (time.time(), rows)
    return rows


def _plain(t):
    t = re.sub(r"^billing and coding:\s*", "", t or "", flags=re.I)
    return re.sub(r"\s*-\s*policy article$", "", t, flags=re.I).strip()


def _mac(a):
    return re.sub(r"\s+", " ", (a.get("contractor_name_type") or "")).strip()


def _article_codes(tok, aid, ver):
    """The code list CMS attaches to the article. Equipment (DME) policy articles have no list: their codes appear in the text, so for those
    we read the HCPCS equipment and supply codes (a letter and four digits) from the text and say so."""
    rows = S._cms(f"/data/article/hcpc-code/?articleid={aid}&ver={ver}", tok)["data"]
    if rows:
        return [dict(code=r["hcpc_code_id"], description=html.unescape((r.get("long_description") or r.get("short_description") or "").strip()), short=html.unescape((r.get("short_description") or "").strip()), group=int(r["hcpc_code_group"]) if str(r.get("hcpc_code_group") or "").isdigit() else None) for r in rows]
    try:
        r = S._cms(f"/data/article/?articleid={aid}&ver={ver}", tok)["data"][0]
    except Exception:
        return []
    text = S.clean(" ".join(str(r.get(k) or "") for k in ("cms_cov_policy", "description", "other_comments")))
    out = []
    for c in sorted(set(re.findall(r"\b[A-EG-V]\d{4}\b", text))):
        m = re.search(r"(?:HCPCS codes?|such as)\s+" + re.escape(c) + r"\s*\(([A-Za-z][^)]{8,140})\)", text)
        if m:
            desc = m.group(1).strip()
        else:
            k = text.index(c)
            desc = "Only mentioned in the article text: " + " ".join(text[max(0, k - 60):k + 70].split()) + "..."
        out.append(dict(code=c, description=desc))
    return out


def _article_cites(tok, aid, ver, number):
    """True if the article text names the NCD number, for example 'NCD 20.4'."""
    try:
        r = S._cms(f"/data/article/?articleid={aid}&ver={ver}", tok)["data"][0]
    except Exception:
        return False
    text = S.clean(" ".join(str(r.get(k) or "") for k in ("cms_cov_policy", "description", "other_comments")))
    return bool(re.search(r"(?<![\d.])" + re.escape(number) + r"(?![\d])", text))


def _ref(a, ver, score=None, cites=None, n=0):
    ident = a.get("document_display_id") or f"A{a['document_id']}"
    return dict(id=ident, version=ver, title=_plain(a["title"]), mac=_mac(a), url=ARTICLE_URL.format(id=a["document_id"], ver=ver), match_score=score, cites_ncd=cites, n_codes=n)


def _collect(found):
    """found: list of (article ref, codes). Returns one row per code with the articles that list it, most agreed first."""
    by = {}
    for ref, codes in found:
        for c in codes:
            row = by.setdefault(c["code"], dict(code=c["code"], description=c["description"], short=c.get("short", ""), group=c.get("group"), listed_by=[]))
            if c.get("group") and (not row["group"] or c["group"] < row["group"]):
                row["group"] = c["group"]  # the lowest group any article gives it
            if ref["id"] not in row["listed_by"]:
                row["listed_by"].append(ref["id"])
    out = list(by.values())  # articles come best match first, so codes from the best-matching article come first
    for r in out:
        r["n_articles"] = len(r["listed_by"])
    return out


def find(kind, ident, title=None):
    """kind: ncd, lcd, cfr or file. ident: '20.4', 'L37848', ... Returns the codes with sources. Never raises: a failure is reported in 'note'."""
    base = dict(method="none", retrieved_at=datetime.now(timezone.utc).isoformat(timespec="seconds"), articles=[], codes=[], note="")
    if kind not in ("ncd", "lcd"):
        base["note"] = "This kind of policy has no code source. Add the codes yourself and say where each one came from."
        return base
    try:
        tok = S._cms_token()
        found = []
        if kind == "lcd":
            idx = S._cms("/reports/local-coverage-final-lcds/", tok)["data"]
            r = next(x for x in idx if x["document_display_id"] == ident)
            rel = S._cms(f"/data/lcd/related-documents/?lcdid={r['document_id']}&ver={r['document_version']}", tok)["data"]
            arts = {a["document_id"]: a for a in _articles(tok)}
            for x in rel:
                a = arts.get(x.get("r_article_id"))
                if not a:
                    continue
                codes = _article_codes(tok, a["document_id"], x["r_article_version"])
                if codes:
                    found.append((_ref(a, x["r_article_version"], n=len(codes)), codes))
            base["method"] = "lcd_related_articles"
            base["note"] = "CMS links these articles to the LCD. The codes are the ones each article lists."
        else:
            pool = [a for a in _articles(tok) if (a.get("title") or "").lower().startswith("billing and coding") or "policy article" in (a.get("title") or "").lower()]
            scored = sorted(((fuzz.token_set_ratio((title or "").lower(), _plain(a["title"]).lower()), a) for a in pool), key=lambda x: -x[0])
            for score, a in scored[:12]:
                if score < MIN_TITLE_SCORE or len(found) >= MAX_ARTICLES:
                    break
                ver = a["document_version"]
                cites = _article_cites(tok, a["document_id"], ver, ident)
                codes = _article_codes(tok, a["document_id"], ver)
                if codes:
                    found.append((_ref(a, ver, score=round(score), cites=cites, n=len(codes)), codes))
            found.sort(key=lambda f: (not f[0]["cites_ncd"], -(f[0]["match_score"] or 0)))
            base["method"] = "ncd_title_match"
            base["note"] = ("CMS does not link an NCD to its billing articles. These are the Billing and Coding articles whose title matches this policy. "
                            "Check that they are about the same service before you use a code.") if found else \
                           "No Billing and Coding article matches this policy. Add the codes yourself and say where each one came from."
        base["articles"] = [f[0] for f in found]
        base["codes"] = _collect(found)
    except Exception as e:
        base["note"] = f"Could not look up codes ({type(e).__name__}). Add them yourself, or build again later."
    return base


_STOP = {"with", "from", "that", "this", "inpatient", "outpatient", "surgery", "procedure", "procedures", "service", "services", "treatment", "therapy", "for", "and", "the", "of", "acute", "chronic",
         "adults", "adult", "requests", "request", "not", "does", "cover", "covers", "only", "new"}


def stems(text):
    """The words of a service name, cut to five letters, so allergen, allergy and allergic all match 'allerg'."""
    out = []
    for w in re.findall(r"[a-z0-9]+", (text or "").lower()):
        if len(w) > 2 and w not in _STOP:
            st = w[:5] if len(w) > 5 else w
            if st not in out:
                out.append(st)
    return out


def rank(title, name_stems, scope_stems=()):
    """How well a title fits a service. The service name decides. The description only breaks ties. Returns 0 when the name does not fit."""
    t = (title or "").lower()
    if not name_stems:
        return 0
    frac = sum(1 for w in name_stems if w in t) / len(name_stems)
    if frac < 0.5:
        return 0
    extra = [w for w in scope_stems if w not in name_stems]
    return frac + (0.3 * sum(1 for w in extra if w in t) / len(extra) if extra else 0)


def search_articles(query, scope="", limit=14):
    """Billing and Coding and Policy articles whose title fits the service name. No codes yet: the owner opens an article to see them.
    Returns (articles, note). Never raises."""
    ns, ss = stems(query), stems(scope)
    if not ns:
        return [], "Type a word or two from the service name."
    try:
        tok = S._cms_token()
        scored = []
        for a in _articles(tok):
            t = (a.get("title") or "")
            if not (t.lower().startswith("billing and coding") or "policy article" in t.lower()):  # equipment (DME) policies list their codes in a Policy Article
                continue
            r = rank(_plain(t), ns, ss)
            if r:
                scored.append((r, a))
        scored.sort(key=lambda x: (-x[0], x[1].get("title") or ""))
        out, seen = [], set()
        for r, a in scored:
            key = (_plain(a["title"]).lower(), _mac(a))
            if key in seen:
                continue
            seen.add(key)
            ref = _ref(a, a["document_version"], score=round(r * 100))
            ref["aid"] = a["document_id"]
            out.append(ref)
            if len(out) >= limit:
                break
        return out, "" if out else "No Billing and Coding article matches these words. Try other words, or add the code yourself."
    except Exception as e:
        return [], f"Could not reach CMS ({type(e).__name__}). Add codes yourself, or try again later."


def codes_of_article(aid, ver):
    """The codes CMS lists on one article, with the article as their source. Never raises."""
    try:
        tok = S._cms_token()
        a = next((x for x in _articles(tok) if str(x["document_id"]) == str(aid)), None)
        if not a:
            return None, [], "CMS has no such article."
        ref = _ref(a, ver)
        ref["aid"] = a["document_id"]
        return ref, _article_codes(tok, a["document_id"], ver), ""
    except Exception as e:
        return None, [], f"Could not reach CMS ({type(e).__name__})."


def consensus(articles, top=8):
    """Reads the codes of the best-matching articles and counts how many articles list each code. Regional contractors write their own articles,
    so a code listed by most of them is likely core to the service. Returns (rows, n_read). Never raises."""
    from concurrent.futures import ThreadPoolExecutor
    try:
        tok = S._cms_token()
    except Exception:
        return [], 0
    pick = articles[:top]

    def one(a):
        try:
            return a, _article_codes(tok, a["aid"], a["version"])
        except Exception:
            return a, []
    with ThreadPoolExecutor(max_workers=6) as ex:
        got = [g for g in ex.map(one, pick) if g[1]]
    rows = _collect([(a, cs) for a, cs in got])
    srcs = {a["id"]: a for a, _ in got}
    for r in rows:
        r["sources"] = [srcs[i] for i in r["listed_by"] if i in srcs][:3]
    rows.sort(key=lambda r: ((r["group"] or 1) > 1, -r["n_articles"], r["code"]))  # the main group first, then the codes listed by more articles
    return rows, len(got)
