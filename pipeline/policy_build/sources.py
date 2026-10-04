"""Step 1 of the policy build: fetch the official text of one policy and record where it came from.

Sources:
  NCD  CMS Medicare Coverage Database API (api.coverage.cms.gov), by NCD number such as "20.4"
  LCD  the same API, by LCD id such as "L37848"
  CFR  the eCFR API, by title, part and section such as (42, 412, 412.3)
  FILE a local file (a PDF or a text file), for a policy that has no API

Each fetch is saved under policies/work/<policy_id>/<version>/source.txt with a meta.json that holds the URL, the
version or effective date, when it was retrieved, and a hash of the text. The hash is how a scheduled check can tell
that a policy has changed since the last approved version.
"""
import gzip, hashlib, html, json, os, re, urllib.request
from datetime import datetime, timezone

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
WORK = os.path.join(ROOT, "policies", "work")
CMS = "https://api.coverage.cms.gov/v1"
ECFR = "https://www.ecfr.gov/api/versioner/v1"


def clean(s):
    """The CMS fields hold HTML. Turn it into plain text, one paragraph per line."""
    if not s:
        return ""
    s = html.unescape(str(s))
    s = re.sub(r"<br\s*/?>|</p>|</li>|</tr>|</div>|</h\d>", "\n", s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s).replace("\xa0", " ")
    s = re.sub(r"[ \t]+", " ", s)
    return re.sub(r"\n\s*\n+", "\n", s).strip()


def _get(url, headers=None):
    req = urllib.request.Request(url, headers={"Accept-Encoding": "gzip", "User-Agent": "PADeskPolicyBuild/1.0", **(headers or {})})  # eCFR requires compression
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
        return gzip.decompress(data) if r.headers.get("Content-Encoding") == "gzip" else data


def _cms(path, tok):
    return json.loads(_get(CMS + path, {"Authorization": f"Bearer {tok}"}))


def _cms_token():
    return json.loads(_get(CMS + "/metadata/license-agreement"))["data"][0]["Token"]


def fetch_ncd(number):
    tok = _cms_token()
    idx = _cms("/reports/national-coverage-ncd/", tok)["data"]
    r = next(x for x in idx if x["document_display_id"] == number)
    d = _cms(f"/data/ncd/?ncdid={r['document_id']}&ncdver={r['document_version']}", tok)["data"][0]
    text = f"NCD {number}: {r['title']}\nVersion {r['document_version']}, effective {d.get('effective_date')}\n\n" \
           + clean(d.get("item_service_description")) + "\n\n" + clean(d.get("indications_limitations"))
    raw = f"<h1>NCD {number}: {r['title']}</h1><p>Version {r['document_version']}, effective {d.get('effective_date')}</p>" + (d.get("item_service_description") or "") + (d.get("indications_limitations") or "")
    return dict(policy_id=f"NCD-{number}", level="NCD", title=r["title"], version=f"v{r['document_version']}", effective=d.get("effective_date"),
                url=f"https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?ncdid={r['document_id']}", text=text, html=raw, source="CMS Coverage API")


def fetch_lcd(display_id):
    tok = _cms_token()
    idx = _cms("/reports/local-coverage-final-lcds/", tok)["data"]
    r = next(x for x in idx if x["document_display_id"] == display_id)
    d = _cms(f"/data/lcd/?lcdid={r['document_id']}&ver={r['document_version']}", tok)["data"][0]
    text = f"LCD {display_id}: {r['title']}\nVersion {r['document_version']}\n\n" + clean(d.get("indication")) + "\n\n" + clean(d.get("cms_cov_policy"))
    raw = f"<h1>LCD {display_id}: {r['title']}</h1>" + (d.get("indication") or "") + (d.get("cms_cov_policy") or "")
    return dict(policy_id=f"LCD-{display_id}", level="LCD", title=r["title"], version=f"v{r['document_version']}", effective=d.get("rev_eff_date"),
                url=f"https://www.cms.gov/medicare-coverage-database/view/lcd.aspx?lcdid={r['document_id']}", text=text, html=raw, source="CMS Coverage API")


def fetch_cfr(title, part, section):
    titles = json.loads(_get(f"{ECFR}/titles.json"))["titles"]
    today = next(t["up_to_date_as_of"] for t in titles if t["number"] == title)  # the newest date the eCFR has
    url = f"{ECFR}/full/{today}/title-{title}.xml?part={part}&section={section}"
    xml = _get(url).decode("utf-8", "replace")
    text = clean(xml)
    raw = re.sub(r"<HEAD>", "<h2>", xml).replace("</HEAD>", "</h2>").replace("<P>", "<p>").replace("</P>", "</p>")
    raw = re.sub(r"</?DIV\d*[^>]*>", "", raw)
    return dict(policy_id=f"CFR-{title}-{section}", level="REGULATION", title=f"{title} CFR {section}", version=today, effective=today,
                url=f"https://www.ecfr.gov/current/title-{title}/section-{section}", text=text, html=f"<html><body>{raw}</body></html>", source="eCFR API")


def from_file(path, policy_id, level, title):
    """A policy with no API, for example a PDF from a health plan. The text is read later by the parse step."""
    return dict(policy_id=policy_id, level=level, title=title, version=datetime.now(timezone.utc).strftime("%Y-%m-%d"), effective=None,
                url=os.path.abspath(path), text=None, source="file", file=os.path.abspath(path))


def save(src):
    """Write source.txt and meta.json. Returns the folder."""
    folder = os.path.join(WORK, src["policy_id"], src["version"])
    os.makedirs(folder, exist_ok=True)
    meta = {k: v for k, v in src.items() if k not in ("text", "html")}
    if src.get("html"):
        open(os.path.join(folder, "source.html"), "w", encoding="utf-8").write(src["html"] if "<html" in src["html"] else f"<html><body>{src['html']}</body></html>")
    if src.get("text") is not None:
        open(os.path.join(folder, "source.txt"), "w", encoding="utf-8").write(src["text"])
        meta["sha256"] = hashlib.sha256(src["text"].encode("utf-8")).hexdigest()
        meta["chars"] = len(src["text"])
    meta["retrieved_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    json.dump(meta, open(os.path.join(folder, "meta.json"), "w", encoding="utf-8"), indent=1)
    return folder


def changed(policy_id, new_sha):
    """True if the newest saved source for this policy has a different hash. A scheduled job calls this for every policy."""
    base = os.path.join(WORK, policy_id)
    if not os.path.isdir(base):
        return True
    versions = sorted(os.listdir(base))
    try:
        return json.load(open(os.path.join(base, versions[-1], "meta.json"), encoding="utf-8")).get("sha256") != new_sha
    except Exception:
        return True
