"""Download every active LCD and NCD from the CMS Coverage API into policies/corpus/."""
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

tok = token(); t0 = time.time()
lcds = get("/reports/local-coverage-final-lcds/", tok)["data"]
ncds = get("/reports/national-coverage-ncd/", tok)["data"]
print("index:", len(lcds), "LCDs,", len(ncds), "NCDs")
print("NCD index keys:", list(ncds[0].keys()))

def fetch_lcd(r):
    for attempt in range(3):
        try:
            d = get(f"/data/lcd/?lcdid={r['document_id']}&ver={r['document_version']}", tok)["data"][0]
            return {"kind": "LCD", "id": r["document_display_id"], "version": r["document_version"],
                    "title": r["title"], "mac": clean(r.get("contractor_name_type")),
                    "effective": d.get("rev_eff_date") or r.get("effective_date"),
                    "indications": clean(d.get("indication")),
                    "summary": clean(d.get("cms_cov_policy")),
                    "url": f"https://www.cms.gov/medicare-coverage-database/view/lcd.aspx?lcdid={r['document_id']}"}
        except Exception as e:
            err = str(e)[:80]; time.sleep(1.5)
    return {"kind": "LCD", "id": r["document_display_id"], "error": err}

with ThreadPoolExecutor(8) as ex:
    out = list(ex.map(fetch_lcd, lcds))
json.dump(out, open("policies/corpus/lcds.json", "w", encoding="utf-8"))
print("LCDs done:", sum(1 for x in out if "error" not in x), "ok,", sum(1 for x in out if "error" in x), "failed", f"({time.time()-t0:.0f}s)")
json.dump(ncds, open("policies/corpus/ncd_index.json", "w", encoding="utf-8"))
