"""One-time migration: adds a procedure registry and two new curated policies (NCD 20.4 ICD, NCD 100.1
bariatric surgery) to policies/policy_library.json, so the product covers three illnesses instead of one.

Each procedure lists the facts the AI must find, and the policies that apply, in order of authority.
Criteria use a small, explicit `check` so the engine can test numbers and choices, not only presence.
The criteria text comes from the official NCD text in policies/corpus/ncds.json (retrieved from the CMS
Coverage database); a copy of each source text is saved under policies/raw/ for audit.
"""
import json, os

ROOT = os.path.join(os.path.dirname(__file__), "..")
LIB = os.path.join(ROOT, "policies", "policy_library.json")
lib = json.load(open(LIB, encoding="utf-8"))

# ---- save source text of the two new NCDs for audit ----
ncds = json.load(open(os.path.join(ROOT, "policies", "corpus", "ncds.json"), encoding="utf-8"))
src = {d["id"]: d for d in ncds if d.get("id") in ("20.4", "100.1")}
os.makedirs(os.path.join(ROOT, "policies", "raw"), exist_ok=True)
for nid, d in src.items():
    with open(os.path.join(ROOT, "policies", "raw", f"NCD_{nid.replace('.', '_')}.txt"), "w", encoding="utf-8") as f:
        f.write(f"NCD {nid}: {d['title']}\nVersion {d.get('version')}, effective {d.get('effective')}\n{d.get('url')}\n\n{d.get('indications')}\n")

# ---- shared short phrases for criteria that already exist ----
SHORT = {"LOC-1": "the expected stay does not cross 2 midnights", "LOC-2": "no risk factors are documented",
         "HUM-1": "no risk-raising comorbidities are documented", "HUM-2": "no post-operative needs beyond routine recovery are documented",
         "LCD-IND": "no qualifying indication is documented", "LCD-CONS": "conservative treatment is not documented"}
for p in lib["policies"]:
    for c in p["criteria"]:
        if c["id"] in SHORT:
            c["short"] = SHORT[c["id"]]
        if c["id"] == "LOC-1":
            c["check"] = {"op": "gte", "value": 2}

# ---- new policies ----
def crit(id, text, cite, fact, if_missing, short, check=None, mode=None, applies_if=None):
    c = {"id": id, "text": text, "cite": cite, "required_fact": fact, "if_missing": if_missing, "short": short}
    if check: c["check"] = check
    if mode: c["mode"] = mode
    if applies_if: c["applies_if"] = applies_if
    return c

ncd204 = {
    "id": "NCD-20.4", "level": "NCD", "answers": "Q2_MEDICAL_NECESSITY",
    "title": "Implantable Cardioverter Defibrillators (ICDs)",
    "source": "CMS Medicare Coverage Database, NCD 20.4 v5, effective 07/31/2023 (last reviewed February 2018)",
    "url": "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?ncdid=110",
    "verified": True, "verified_from": "CMS Coverage database download (policies/corpus/ncds.json), source text saved in policies/raw/NCD_20_4.txt",
    "applies_to": "Primary prevention for ischemic or non-ischemic dilated cardiomyopathy (NCD 20.4, B3 and B4). Other covered pathways (B1, B2, B5) are not modeled and go to a physician.",
    "criteria": [
        crit("ICD-PATH", "The request rests on ischemic or non-ischemic dilated cardiomyopathy with heart failure. The other covered pathways (prior sustained ventricular tachycardia or cardiac arrest, prior heart attack with LVEF 30% or less, inherited rhythm disorders) are outside this prototype and go to a physician.",
             "NCD 20.4, B3 and B4", "cardiomyopathy_type", "Ask: what is the cause of the cardiomyopathy: ischemic (coronary disease or prior heart attack) or non-ischemic?",
             "the indication is a pathway this prototype does not model", {"op": "in", "value": ["ischemic", "non-ischemic"]}),
        crit("ICD-LVEF", "Left ventricular ejection fraction (LVEF) is 35% or less.", "NCD 20.4, B3 and B4", "lvef_percent",
             "Ask: what is the most recent ejection fraction, how was it measured, and on what date?", "the ejection fraction is above 35%", {"op": "lte", "value": 35}),
        crit("ICD-METHOD", "LVEF was measured by echocardiography, nuclear imaging, cardiac MRI, or catheter angiography.", "NCD 20.4, B (additional criteria)", "lvef_method",
             "Ask: how was the ejection fraction measured?", "the ejection fraction was not measured by an accepted method",
             {"op": "in", "value": ["echocardiography", "nuclear imaging", "cardiac MRI", "angiography"]}),
        crit("ICD-NYHA", "Heart failure is NYHA class II or III.", "NCD 20.4, B3 and B4", "nyha_class",
             "Ask: what is the patient's NYHA heart failure class?", "the NYHA class is not II or III", {"op": "in", "value": ["II", "III"]}),
        crit("ICD-WAIT", "No heart attack in the past 40 days, and no bypass surgery or stent procedure in the past 3 months.", "NCD 20.4, B3 and B4", "recent_mi_revasc",
             "Ask: has the patient had a heart attack in the past 40 days, or bypass surgery or a stent in the past 3 months?", "there was a recent heart attack, bypass, or stent", mode="absent"),
        crit("ICD-OMT", "For non-ischemic cardiomyopathy: the patient has been on optimal medical therapy for at least 3 months.", "NCD 20.4, B4", "optimal_medical_therapy_months",
             "Ask: how long has the patient been on optimal heart failure medicines?", "the patient has had under 3 months of optimal medical therapy",
             {"op": "gte", "value": 3}, applies_if={"fact": "cardiomyopathy_type", "equals": "non-ischemic"}),
        crit("ICD-SDM", "A formal shared decision making visit, using an evidence-based decision tool, took place before the implant.", "NCD 20.4, B3 and B4", "shared_decision_making",
             "Ask: is a shared decision making visit with a decision tool documented before the implant?", "no shared decision making visit is documented"),
        crit("ICD-EXCL", "The patient is clinically stable and has no condition that rules out an ICD (severe brain damage, another illness with survival under 1 year, poorly controlled atrial fibrillation).",
             "NCD 20.4, B (additional criteria)", "limiting_conditions",
             "Ask: is the patient clinically stable, and are there any conditions that limit survival or rule out an ICD?", "a condition that rules out an ICD is documented", mode="absent"),
    ],
}
ncd1001 = {
    "id": "NCD-100.1", "level": "NCD", "answers": "Q2_MEDICAL_NECESSITY",
    "title": "Bariatric Surgery for Treatment of Co-Morbid Conditions Related to Morbid Obesity",
    "source": "CMS Medicare Coverage Database, NCD 100.1 v5, effective 09/24/2013",
    "url": "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?ncdid=57",
    "verified": True, "verified_from": "CMS Coverage database download (policies/corpus/ncds.json), source text saved in policies/raw/NCD_100_1.txt",
    "applies_to": "Open and laparoscopic Roux-en-Y gastric bypass (CPT 43644), nationally covered. Stand-alone sleeve gastrectomy is decided by each Medicare contractor and is not modeled.",
    "criteria": [
        crit("BAR-BMI", "Body-mass index (BMI) is 35 or higher.", "NCD 100.1, B", "bmi", "Ask: what is the patient's BMI, and when was it measured?", "the BMI is under 35", {"op": "gte", "value": 35}),
        crit("BAR-CM", "At least one comorbidity related to obesity is documented (type 2 diabetes counts).", "NCD 100.1, B", "comorbidities",
             "Ask: which obesity-related conditions does the patient have, such as type 2 diabetes?", "no obesity-related comorbidity is documented"),
        crit("BAR-TX", "The patient was previously unsuccessful with medical treatment for obesity.", "NCD 100.1, B", "prior_medical_treatment",
             "Ask: what medical treatment for obesity was tried, for how long, and what was the result?", "no unsuccessful medical treatment is documented"),
    ],
}
lib["policies"] = [p for p in lib["policies"] if p["id"] not in ("NCD-20.4", "NCD-100.1")] + [ncd204, ncd1001]

# ---- fact definitions ----
def fact(key, label, kind, phrase, ask, statuses, hint="", unit=None, values=None, none_text=None):
    d = {"key": key, "label": label, "kind": kind, "phrase": phrase, "ask": ask, "statuses": statuses, "hint": hint}
    if unit: d["unit"] = unit
    if values: d["values"] = values
    if none_text: d["none_text"] = none_text
    return d

F_LOS = fact("expected_los_days", "Expected stay", "number", "the expected length of stay",
             "Number of midnights of hospital care the physician expects. If the text only says something like 'a multi-day stay' with no number, use status implied.",
             ["found", "implied", "missing"], "Number of midnights, like 3", unit="midnight")
F_COM = fact("comorbidities", "Comorbidities", "list", "comorbidity documentation",
             "Short labels for the patient's conditions that raise risk, for example 'heart failure'. Use status none only when the packet says there are none.",
             ["found", "none", "missing"], "For example: heart failure, diabetes", none_text="None documented as present")
F_SDM_L = fact("shared_decision_making", "Shared decision making", "text", "shared decision making",
               "A documented shared decision making discussion with the patient, including risks and benefits.", ["found", "missing"], "Optional note")
F_SDM_I = fact("shared_decision_making", "Shared decision making", "text", "the shared decision making visit",
               "A documented formal shared decision making visit between the patient and a physician or qualified practitioner, using an evidence-based decision tool on ICDs, before the implant.",
               ["found", "missing"], "What was documented, and when")

lumbar_facts = [
    F_LOS, F_COM,
    fact("post_op_needs", "Post-op care needs", "text", "post-operative care needs",
         "Post-operative monitoring or care needs. Use status none only if the packet says recovery is routine.", ["found", "none", "missing"], "What care is needed after surgery", none_text="Routine recovery only"),
    fact("indication_evidence", "Surgical indication", "enum", "imaging or exam evidence for the surgical indication",
         "The qualifying finding on imaging or exam. Use status none when the imaging or exam explicitly RULES OUT a finding (for example 'no evidence of instability'). That is not the same as missing.",
         ["found", "none", "implied", "missing"], "", values=["instability", "deformity", "pseudarthrosis", "neural compression"]),
    fact("conservative_treatment", "Conservative care", "text", "the conservative treatment history",
         "Which non-surgical treatments were tried and for how long (therapy, medicines, injections).", ["found", "missing"], "What was tried and for how long"),
    F_SDM_L,
]
icd_facts = [
    F_LOS, F_COM,
    fact("lvef_percent", "Ejection fraction", "number", "the most recent ejection fraction",
         "The most recent measured left ventricular ejection fraction, as a percent number. If two measurements conflict, use the later one and say so in the note.", ["found", "missing"], "Percent, like 30", unit="%"),
    fact("lvef_method", "How it was measured", "enum", "how the ejection fraction was measured",
         "How the most recent ejection fraction was measured.", ["found", "missing"], "", values=["echocardiography", "nuclear imaging", "cardiac MRI", "angiography", "other"]),
    fact("nyha_class", "NYHA class", "enum", "the NYHA heart failure class",
         "The New York Heart Association functional class of heart failure, I to IV.", ["found", "missing"], "", values=["I", "II", "III", "IV"]),
    fact("cardiomyopathy_type", "Cause of heart failure", "enum", "the cause of the cardiomyopathy",
         "ischemic if caused by coronary artery disease or a prior heart attack. non-ischemic if dilated cardiomyopathy without a coronary cause. other if the request rests on something else, such as prior sustained ventricular tachycardia, cardiac arrest, or an inherited rhythm disorder.",
         ["found", "missing"], "", values=["ischemic", "non-ischemic", "other"]),
    fact("recent_mi_revasc", "Recent heart attack, bypass, or stent", "event", "whether there was a heart attack in the past 40 days or a bypass or stent in the past 3 months",
         "Use status found if a heart attack within 40 days, or bypass surgery or a stent within 3 months, is documented. Use status none only if the packet states there was none, or gives dates that are outside those windows.",
         ["found", "none", "missing"], "What happened and when", none_text="None in the waiting window"),
    fact("optimal_medical_therapy_months", "Months on heart failure medicines", "number", "how long the patient has been on optimal heart failure medicines",
         "Number of months on guideline-directed heart failure medical therapy.", ["found", "missing"], "Number of months, like 4", unit="month"),
    F_SDM_I,
    fact("limiting_conditions", "Conditions that rule out an ICD", "list", "whether any condition rules out an ICD",
         "Conditions that rule out an ICD: severe irreversible brain damage, a non-cardiac illness with expected survival under 1 year, atrial fibrillation with a poorly controlled rate, or a patient who is not clinically stable. Use status none only if the packet says there are none.",
         ["found", "none", "missing"], "For example: none, or the condition", none_text="None documented"),
]
bariatric_facts = [
    F_LOS, F_COM,
    fact("bmi", "BMI", "number", "the patient's BMI", "The most recent body-mass index in kg/m2.", ["found", "missing"], "Number, like 41", unit="kg/m2"),
    fact("prior_medical_treatment", "Prior medical treatment", "text", "the history of medical treatment for obesity",
         "Supervised medical treatment for obesity that was tried and did not work (diet, exercise, medicines), with how long and the result.", ["found", "missing"], "What was tried, for how long, and the result"),
]
lib["procedures"] = {
    "lumbar_fusion": {"name": "Lumbar spinal fusion", "short": "Lumbar fusion", "cpts": ["22612"], "policies": ["CFR-42-412.3", "LCD-L37848", "HUM-IP-ILLUSTRATIVE", "MCG-STUB"], "facts": lumbar_facts},
    "icd": {"name": "Implantable cardioverter defibrillator (ICD)", "short": "ICD, heart failure", "cpts": ["33249"], "policies": ["CFR-42-412.3", "NCD-20.4", "MCG-STUB"], "facts": icd_facts},
    "bariatric": {"name": "Bariatric surgery (Roux-en-Y gastric bypass)", "short": "Bariatric surgery", "cpts": ["43644"], "policies": ["CFR-42-412.3", "NCD-100.1", "MCG-STUB"], "facts": bariatric_facts},
}
lib["covered_cpt_codes"] = sorted({c for p in lib["procedures"].values() for c in p["cpts"]})
lib["covered_cpt_note"] = ("The curated criteria apply ONLY to the procedures listed under `procedures`. Any other CPT has no entry here: the engine refuses to score it "
                           "against another service's criteria and routes it to the retrieval fallback (pipeline/policy_retrieval.py), whose output a person must confirm.")
lib["version"] = "0.2.0"
lib["open_items"] = lib.get("open_items", []) + [
    "ICD: only the primary-prevention cardiomyopathy pathways (NCD 20.4 B3 and B4) are modeled. Secondary prevention, prior MI with LVEF 30% or less, and inherited disorders route to a physician.",
    "Bariatric: Roux-en-Y bypass is nationally covered. Stand-alone sleeve gastrectomy is decided by each Medicare contractor, so it is not modeled.",
    "The new criteria were written from the NCD text and have not been signed off by a clinical policy owner.",
]
json.dump(lib, open(LIB, "w", encoding="utf-8", newline="\n"), indent=2, ensure_ascii=False)
print("procedures:", list(lib["procedures"]), "| policies:", [p["id"] for p in lib["policies"]])
