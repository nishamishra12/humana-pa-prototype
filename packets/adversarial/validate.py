"""Check adversarial packets: schema, page refs, coverage, and that expected_action follows from truth."""
import json, glob, collections, os

ICD_KEYS = ["expected_los_days","comorbidities","lvef_percent","lvef_method","nyha_class","cardiomyopathy_type",
            "recent_mi_revasc","optimal_medical_therapy_months","shared_decision_making","limiting_conditions"]
BAR_KEYS = ["expected_los_days","comorbidities","bmi","prior_medical_treatment"]
OBESITY_RELATED = ["diabetes","sleep apnea","hypertension","nafld","osteoarthritis","dyslipidemia","hyperlipidemia","gerd"]

def derive(p):
    t = p["truth"]; svc = p["service"]
    keys = ICD_KEYS if svc == "icd" else BAR_KEYS
    needed = list(keys)
    if svc == "icd":
        ctype = t["cardiomyopathy_type"]
        if ctype["truth"] == "present" and ctype.get("value") in ("ischemic", "other"):
            needed.remove("optimal_medical_therapy_months")
    if any(t[k]["truth"] == "absent" for k in needed):
        return "pend"
    if any(t[k].get("ambiguous") for k in keys):
        return "verify"
    v = {k: t[k].get("value") for k in keys}
    fails = []
    if svc == "icd":
        if v["cardiomyopathy_type"] == "other": fails.append(1)
        if v["lvef_percent"] > 35: fails.append(2)
        if v["lvef_method"] not in ("echocardiography","nuclear imaging","cardiac MRI","angiography"): fails.append(3)
        if v["nyha_class"] not in ("II","III"): fails.append(4)
        if t["recent_mi_revasc"]["truth"] == "present": fails.append(5)
        if v["cardiomyopathy_type"] == "non-ischemic" and v["optimal_medical_therapy_months"] < 3: fails.append(6)
        if t["shared_decision_making"]["truth"] != "present": fails.append(7)
        if t["limiting_conditions"]["truth"] == "present": fails.append(8)
        if v["expected_los_days"] < 2 or t["comorbidities"]["truth"] != "present": fails.append(9)
    else:
        if v["bmi"] < 35: fails.append(1)
        com = t["comorbidities"]
        if com["truth"] != "present" or not any(w in c.lower() for c in com["value"] for w in OBESITY_RELATED): fails.append(2)
        if t["prior_medical_treatment"]["truth"] != "present": fails.append(3)
        if v["expected_los_days"] < 2: fails.append(4)
    return ("escalate" if fails else "approve"), fails

packets = []
for f in sorted(glob.glob("batch_*.json")):
    packets += json.load(open(f, encoding="utf-8"))

errors = []
ids = [p["id"] for p in packets]
if ids != [f"adv_{i:03d}" for i in range(1, 41)]: errors.append(f"ids out of order: {ids}")
for p in packets:
    keys = ICD_KEYS if p["service"] == "icd" else BAR_KEYS
    if set(p["truth"]) != set(keys): errors.append(f"{p['id']}: truth keys {set(p['truth']) ^ set(keys)}")
    n = len(p["pages"])
    if not 6 <= n + 0 <= 9 and not 5 <= n <= 8: errors.append(f"{p['id']}: {n} clinical pages")
    for k, e in p["truth"].items():
        if e["truth"] not in ("present","absent","negated"): errors.append(f"{p['id']}.{k}: bad truth")
        pg = e.get("page")
        if e["truth"] == "absent":
            if pg is not None: errors.append(f"{p['id']}.{k}: absent but page set")
        elif not (isinstance(pg, int) and 2 <= pg <= n + 1):
            errors.append(f"{p['id']}.{k}: page {pg} out of range 2..{n+1}")
    d = derive(p)
    action = d if isinstance(d, str) else d[0]
    if action != p["expected_action"]:
        errors.append(f"{p['id']}: derived {d} but expected {p['expected_action']}")
    if p["planned_admit_date"] <= "2026-10-04": errors.append(f"{p['id']}: admit date not in future")

print("packets:", len(packets))
print("pages per packet (clinical):", sorted(collections.Counter(len(p['pages']) for p in packets).items()))
print("service:", dict(collections.Counter(p['service'] for p in packets)))
print("actions:", dict(collections.Counter(p['expected_action'] for p in packets)))
for s in ("icd","bariatric"):
    print(f"  {s}:", dict(collections.Counter(p['expected_action'] for p in packets if p['service']==s)))
print("categories:", dict(sorted(collections.Counter(p['category'] for p in packets).items())))
print("ERRORS:" if errors else "no errors")
for e in errors: print("  ", e)

if not errors:
    json.dump(packets, open("adv_all.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    os.makedirs("packets", exist_ok=True)
    for p in packets:
        json.dump(p, open(f"packets/{p['id']}.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print("wrote adv_all.json and packets/adv_XXX.json")
