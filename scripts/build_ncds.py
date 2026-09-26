"""Download every NCD (full text) from the CMS Coverage API into policies/corpus/ncds.json."""
import json, re, html, sys, os, time
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(__file__))
from cms_api import token, get

def clean(s):
    if not s: return ""
    s = html.unescape(str(s))
    s = re.sub(r'<br\s*/?>|</p>|</li>|</tr>|</div>', '\n', s)
    s = re.sub(r'<[^>]+>', ' ', s)
    s = html.unescape(s).replace('\xa0', ' ')
    s = re.sub(r'[ \t]+', ' ', s)
    return re.sub(r'\n\s*\n+', '\n', s).strip()

tok = token()
idx = get("/reports/national-coverage-ncd/", tok)["data"]

def fetch(r):
    for _ in range(3):
        try:
            d = get(f"/data/ncd/?ncdid={r['document_id']}&ncdver={r['document_version']}", tok)["data"][0]
            return {"kind": "NCD", "id": r["document_display_id"], "version": r["document_version"],
                    "title": r["title"], "effective": d.get("effective_date"),
                    "description": clean(d.get("item_service_description")),
                    "indications": clean(d.get("indications_limitations")),
                    "url": f"https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?ncdid={r['document_id']}"}
        except Exception as e:
            err = str(e)[:80]; time.sleep(1.5)
    return {"kind": "NCD", "id": r["document_display_id"], "error": err}

with ThreadPoolExecutor(8) as ex:
    out = list(ex.map(fetch, idx))
json.dump(out, open("policies/corpus/ncds.json", "w", encoding="utf-8"))
print("NCDs:", sum(1 for x in out if "error" not in x), "ok,", sum(1 for x in out if "error" in x), "failed")
