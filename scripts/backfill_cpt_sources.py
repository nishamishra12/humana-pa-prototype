"""Records, for each service in the policy library, where its CPT codes come from.

The three demo services were set up with one code each, typed in by hand. This looks each code up in the CMS Billing and Coding
articles that go with the service's policy and stores the article next to the code. Codes CMS lists that we have not enabled are
kept for reference. Run: PYTHONPATH=. python scripts/backfill_cpt_sources.py
"""
import json, os, sys

from pipeline.policy_build import codes as C

ROOT = os.path.join(os.path.dirname(__file__), "..")
PATHS = [os.path.join(ROOT, "policies", "policy_library.json"), os.path.join(ROOT, "app", "policy_library.live.json")]
# the policy whose billing articles list this service's codes
LOOKUP = {"lumbar_fusion": ("lcd", "L37848", None), "icd": ("ncd", "20.4", "Implantable Automatic Defibrillators"),
          "bariatric": ("ncd", "100.1", "Bariatric Surgery for Treatment of Co-Morbid Conditions Related to Morbid Obesity")}

found = {k: C.find(*v) for k, v in LOOKUP.items()}
for k, r in found.items():
    print(k, r["method"], len(r["articles"]), "articles", len(r["codes"]), "codes")
for path in PATHS:
    if not os.path.exists(path):
        continue
    lib = json.load(open(path, encoding="utf-8"))
    for key, proc in lib["procedures"].items():
        r = found.get(key)
        if not r:
            continue
        arts = {a["id"]: a for a in r["articles"]}
        by = {c["code"]: c for c in r["codes"]}
        src = []
        for code in proc["cpts"]:
            c = by.get(code)
            if not c:
                src.append(dict(code=code, description=None, sources=[], note="Not found in the CMS Billing and Coding articles. Verify before use."))
                continue
            src.append(dict(code=code, description=c["description"], sources=[dict(article=i, version=arts[i]["version"], title=arts[i]["title"], mac=arts[i]["mac"], url=arts[i]["url"]) for i in c["listed_by"]]))
        proc["cpt_sources"] = src
        proc["cpt_checked"] = r["retrieved_at"][:10]
        proc["cms_other_codes"] = [dict(code=c["code"], description=c["description"], listed_by=c["n_articles"]) for c in r["codes"] if c["code"] not in proc["cpts"]]
    json.dump(lib, open(path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("updated", os.path.relpath(path, ROOT))
