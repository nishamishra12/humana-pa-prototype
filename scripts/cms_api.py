import json, sys, urllib.request

BASE = "https://api.coverage.cms.gov/v1"

def token():
    with urllib.request.urlopen(f"{BASE}/metadata/license-agreement", timeout=30) as r:
        return json.load(r)["data"][0]["Token"]

def get(path, tok):
    req = urllib.request.Request(BASE + path, headers={"Authorization": f"Bearer {tok}"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)

if __name__ == "__main__":
    tok = token()
    lcds = get("/reports/local-coverage-final-lcds/", tok)["data"]
    ncds = get("/reports/national-coverage-ncd/", tok)["data"]
    print("LCDs:", len(lcds), "| NCDs:", len(ncds))
    kw = ("spinal fusion", "lumbar", "spine", "spinal", "inpatient", "two-midnight", "artificial disc")
    for label, rows, key in (("LCD", lcds, "title"), ("NCD", ncds, "title")):
        for r in rows:
            t = (r.get(key) or "").lower()
            if any(k in t for k in kw):
                print(label, r.get("document_display_id") or r.get("document_id"), "|", r.get(key), "|", (r.get("contractor_name_type") or "")[:40].replace("\r\n"," "))
