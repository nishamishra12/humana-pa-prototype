"""Multi-illness demo/eval packets: ICD for heart failure (CPT 33249, NCD 20.4) and
laparoscopic Roux-en-Y gastric bypass (CPT 43644, NCD 100.1). Nine PDFs into packets/multi/.

Each page is ONE faxed document (PA request, consult note, echo report, ...), dense and a little
noisy, with facts phrased the way clinicians write them (not one keyword form). icd4 is the
same clinical content as icd1 for a different patient, rendered image-only with a degraded scan
look (rotation, noise, blur, low contrast) and NO text layer, to exercise OCR.

All patient data is MADE UP. Run from the repo root:  python scripts/make_multi_illness_packets.py
Truth for each packet lives in evals/multi_manifest.json (written by hand, checked by eye).
"""
import os
import random
import shutil
import subprocess
import tempfile
from datetime import date

import numpy as np
from fpdf import FPDF
from PIL import Image, ImageFilter

OUT = "packets/multi"
os.makedirs(OUT, exist_ok=True)

TODAY = date(2026, 10, 4)
FOOTER = "Made-up data for a software prototype. Not a real patient."


def age_of(dob):
    y, m, d = map(int, dob.split("-"))
    return TODAY.year - y - ((TODAY.month, TODAY.day) < (m, d))


class FaxPDF(FPDF):
    fax_line = ""

    def header(self):
        self.set_font("Helvetica", "", 7.5)
        self.set_text_color(110, 110, 110)
        self.cell(0, 4, f"{self.fax_line}   |   Page {self.page_no()} of {{nb}}",
                  new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(0, 0, 0)
        self.ln(2)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(110, 110, 110)
        self.cell(0, 5, FOOTER, align="C")
        self.set_text_color(0, 0, 0)


def one_line(pdf, text, size=10.5, style=""):
    """Print text on a single line, shrinking the font if needed (keeps header lines unwrapped)."""
    while size > 6:
        pdf.set_font("Helvetica", style, size)
        if pdf.get_string_width(text) <= pdf.w - pdf.l_margin - pdf.r_margin - 1:
            break
        size -= 0.25
    pdf.cell(0, 6, text, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10.5)


def write_text_pdf(path, fax_line, pages):
    """pages = [(title, [lines])]. Line markup: '' blank, '## ' heading, '!! ' single line,
    '~ ' monospaced table row, anything else = wrapped paragraph."""
    pdf = FaxPDF()
    pdf.fax_line = fax_line
    pdf.alias_nb_pages("{nb}")
    pdf.set_auto_page_break(True, 16)
    pdf.set_margins(16, 12, 16)
    for title, lines in pages:
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 9, title, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)
        pdf.set_font("Helvetica", "", 10.5)
        for ln in lines:
            if ln == "":
                pdf.ln(2.5)
            elif ln.startswith("## "):
                pdf.ln(1)
                pdf.set_font("Helvetica", "B", 11)
                pdf.cell(0, 6.5, ln[3:], new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("Helvetica", "", 10.5)
            elif ln.startswith("!! "):
                one_line(pdf, ln[3:])
            elif ln.startswith("~ "):
                pdf.set_font("Courier", "", 9)
                pdf.cell(0, 5, ln[2:], new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("Helvetica", "", 10.5)
            else:
                pdf.multi_cell(0, 5.4, ln, new_x="LMARGIN", new_y="NEXT")
    pdf.output(path)


def pa_page(m, service, cpt, icd10, plan_note=None):
    """Page 1, in the required header format."""
    return ("Prior Authorization Request - Inpatient Admission", [
        "## Health Plan",
        "Humana Medicare Advantage. Plan ID: H5216-014-000. Request type: standard pre-service review.",
        f"Date of request: {TODAY.isoformat()}",
        "",
        "## Member Information",
        f"!! Member: {m['name']}   DOB: {m['dob']} (age {age_of(m['dob'])})   Member ID: {m['mid']}",
        f"Address: {m['addr']}",
        f"Phone: {m['phone']}   Sex: {m['sex']}",
        "Primary insurance: Humana Medicare Advantage (primary). Secondary: none on file.",
        "",
        "## Requesting Provider",
        f"{m['surgeon']} -- {m['specialty']}",
        f"NPI: {m['npi']}",
        f"Practice: {m['practice']}",
        f"Phone: {m['ph2']}   Fax: {m['fax']}",
        "",
        "## Requested Service",
        f"!! Requested service: Elective inpatient admission, {service}",
        f"!! CPT {cpt}   ICD-10: {icd10}",
        f"Planned admit date: {m['admit']}",
        "Level of care requested: INPATIENT",
        "Place of service: Hospital, inpatient (acute care).",
        "",
        "## Submission Contact",
        f"Submitted through the provider portal by {m['coord']}, Authorization Coordinator.",
        f"Callback: {m['ph2']}. Supporting clinical documentation attached ({m['npages']} pages including this request).",
    ] + ([""] + plan_note if plan_note else []))


# --------------------------------------------------------------------------------------
# Members (all made up)
# --------------------------------------------------------------------------------------
HEART = "Heartland Cardiac Electrophysiology Associates"
BAR = "Lakeview Bariatric & Metabolic Surgery Center"


def member(name, dob, mid, sex, addr, phone, surgeon, specialty, npi, practice, ph2, fax, coord, admit, npages):
    return dict(name=name, dob=dob, mid=mid, sex=sex, addr=addr, phone=phone, surgeon=surgeon,
                specialty=specialty, npi=npi, practice=practice, ph2=ph2, fax=fax, coord=coord,
                admit=admit, npages=npages)


M_ICD1 = member("Gerald Fitzpatrick", "1959-03-12", "MBR-30417", "M", "812 Orchard Ridge Rd, Akron, OH 44313",
                "(330) 555-0142", "Dr. Anita Rao, MD", "Cardiac Electrophysiology", "1578043926", HEART,
                "(330) 555-0170", "(330) 555-0171", "Pamela Duarte", "2026-11-10", 8)
M_ICD2 = member("Loretta Vasquez-Moyer", "1956-07-22", "MBR-30458", "F", "47 Sycamore Court, Canton, OH 44718",
                "(330) 555-0188", "Dr. Samuel Whitcomb, MD", "Cardiac Electrophysiology", "1649205738",
                "Stark County Heart & Rhythm Clinic", "(330) 555-0210", "(330) 555-0211", "Dana Kessler", "2026-11-12", 7)
M_ICD3 = member("Raymond Okafor", "1954-01-30", "MBR-30502", "M", "2290 Lakeshore Blvd, Cleveland, OH 44108",
                "(216) 555-0119", "Dr. Priya Venkataraman, MD", "Cardiac Electrophysiology", "1830417562",
                "Lakeshore Cardiovascular Specialists", "(216) 555-0140", "(216) 555-0141", "Tomas Ibarra", "2026-11-17", 7)
M_ICD4 = member("Beverly Tanaka-Holt", "1960-09-05", "MBR-30573", "F", "15 Birchwood Terrace, Toledo, OH 43614",
                "(419) 555-0126", "Dr. Marcus Lindqvist, MD", "Cardiac Electrophysiology", "1295736084",
                "Maumee Valley Electrophysiology Group", "(419) 555-0150", "(419) 555-0151", "Reyna Castellanos", "2026-11-19", 8)
M_ICD5 = member("Dennis Kowalczyk", "1955-12-14", "MBR-30619", "M", "630 Harbor View Dr, Lorain, OH 44052",
                "(440) 555-0174", "Dr. Helen Abernathy, MD", "Cardiac Electrophysiology", "1417258093",
                "Erie Shores Heart Institute", "(440) 555-0190", "(440) 555-0191", "Wanda Oyelaran", "2026-10-14", 8)
M_BAR1 = member("Marcia Delgado-Finch", "1960-02-17", "MBR-30644", "F", "903 Cobblestone Way, Dayton, OH 45419",
                "(937) 555-0133", "Dr. Joel Hartmann, MD", "Bariatric Surgery", "1086392745", BAR,
                "(937) 555-0160", "(937) 555-0161", "Sheila Brandt", "2026-11-09", 7)
M_BAR2 = member("Thomas Eberhardt", "1959-10-21", "MBR-30688", "M", "58 Millstone Lane, Springfield, OH 45503",
                "(937) 555-0149", "Dr. Naomi Feldstein, MD", "Bariatric Surgery", "1563820917",
                "Buckeye Metabolic & Weight Surgery", "(937) 555-0185", "(937) 555-0186", "Carlos Menendez", "2026-11-16", 7)
M_BAR3 = member("Yolanda Prescott", "1961-06-03", "MBR-30701", "F", "2114 Foxglove Ave, Columbus, OH 43211",
                "(614) 555-0127", "Dr. Raymond Teague, MD", "Bariatric Surgery", "1720458391",
                "Capital Bariatric Surgery Associates", "(614) 555-0195", "(614) 555-0196", "Imani Whitfield", "2026-11-18", 7)
M_BAR4 = member("Franklin Adeyemi", "1958-11-28", "MBR-30736", "M", "7 Ashland Park Dr, Youngstown, OH 44512",
                "(330) 555-0163", "Dr. Katherine Ostrowski, MD", "Bariatric Surgery", "1352967480",
                "Mahoning Valley Surgical Weight Program", "(330) 555-0205", "(330) 555-0206", "Lucia Santangelo", "2026-11-23", 7)

ICD_SERVICE = "implantation of a transvenous implantable cardioverter defibrillator (ICD)"
BAR_SERVICE = "laparoscopic Roux-en-Y gastric bypass"


def bmi(lb, inch):
    return round(703 * lb / inch ** 2, 1)


# sanity-check the BMI arithmetic used in the notes
assert bmi(254, 65) == 42.3 and bmi(259, 68) == 39.4
assert bmi(204, 63) == 36.1 and bmi(191, 63) == 33.8 and bmi(266, 70) == 38.2


# --------------------------------------------------------------------------------------
# ICD packets
# --------------------------------------------------------------------------------------
def icd1_pages(m):
    """Complete, non-ischemic, LVEF 28%, NYHA III, GDMT 8 months, SDM documented."""
    first = m["name"].split()[0]
    pron = "He" if m["sex"] == "M" else "She"
    pos = "his" if m["sex"] == "M" else "her"
    age = age_of(m["dob"])
    return [
        pa_page(m, ICD_SERVICE, "33249", "I42.0 (Dilated cardiomyopathy); I50.22 (Chronic systolic HF)"),
        ("Cardiology Consultation - Heart Failure Clinic", [
            f"Date of visit: 2026-09-16.   Patient: {m['name']}   Age/Sex: {age} {m['sex']}",
            "Referred by: Dr. L. Mbeki (PCP) for evaluation of primary-prevention ICD candidacy.",
            "",
            "## Reason for visit",
            "Follow-up of dilated cardiomyopathy with chronic heart failure with reduced ejection fraction (HFrEF).",
            "",
            "## History of present illness",
            f"{age}-year-old {'man' if m['sex']=='M' else 'woman'} with a non-ischemic dilated cardiomyopathy, first recognized "
            f"after an admission for decompensated heart failure earlier this year. {pron} reports dyspnea after walking about "
            f"one block on level ground or climbing one flight of stairs, two-pillow orthopnea, and ankle swelling by the end of "
            f"the day. {pron} is comfortable at rest. No syncope or presyncope. No palpitations, no ICD shocks (no device in place). "
            f"Weight is stable on diuretic. {pron} has not needed an ED visit or admission for HF since the spring.",
            "Symptom burden has been stable over the last 3 months: marked limitation of ordinary activity, comfortable at rest, "
            "consistent with NYHA functional class III.",
            "",
            "## Cardiac history",
            "Ischemic evaluation: left heart catheterization 2026-07-21 without obstructive coronary disease (report on file). "
            "No myocardial infarction, CABG or PCI in the past 12 months, and none before that either. No stent. "
            "No history of sustained VT, VF or cardiac arrest.",
            "",
            "## Past medical history",
            "Heart failure as above. Hypertension, long-standing. Chronic kidney disease stage 3a (baseline eGFR in the high 40s). "
            "Remote appendectomy. Cataract extraction OU 2021. Seasonal allergies. Former smoker, quit 2008, 10 pack-years. "
            "Alcohol: 1-2 beers on weekends; counseled. No illicit drug use.",
            "",
            "## Exam",
            "BP 118/72, HR 70 regular, SpO2 97% RA, BMI 29. JVP about 8 cm. Lungs clear. S3 present, soft apical MR murmur. "
            "Trace bilateral ankle edema. Warm extremities.",
            "",
            "## Assessment and plan",
            "Dilated cardiomyopathy, non-ischemic, symptomatic HFrEF, NYHA III, on guideline-directed therapy (see medication list). "
            "LVEF remains severely reduced on the latest echocardiogram (page 3). Candidate for primary-prevention ICD. "
            "Referred to EP for implantation. Continue current regimen, daily weights, 2 g sodium diet. Return in 6 weeks.",
        ]),
        ("Transthoracic Echocardiogram Report", [
            "Study date: 2026-08-12.   Indication: cardiomyopathy, reassessment of LV function on therapy.",
            f"Patient: {m['name']}   DOB: {m['dob']}   Sonographer: K. Yamada, RDCS.   Interpreting physician: R. Castellano, MD, FASE.",
            "",
            "## Findings",
            "Left ventricle: moderately to severely dilated (LVIDd 6.3 cm, LVIDs 5.6 cm). Wall thickness normal. "
            "Global hypokinesis with no discrete regional wall motion abnormality. No LV thrombus on contrast-enhanced views.",
            "Left ventricular ejection fraction 28% by TTE (biplane method of discs, apical 4- and 2-chamber).",
            "Diastolic function: restrictive filling pattern, E/e' 17.",
            "Left atrium: moderately enlarged, LA volume index 44 mL/m2.",
            "Right ventricle: normal size, mildly reduced longitudinal function, TAPSE 15 mm.",
            "Valves: mild-to-moderate functional mitral regurgitation. Mild tricuspid regurgitation. Aortic valve trileaflet, no stenosis.",
            "Estimated RVSP 38 mmHg. IVC 2.0 cm with less than 50% collapse. No pericardial effusion.",
            "",
            "## Impression",
            "1. Dilated left ventricle with severely reduced systolic function, LVEF 28%.",
            "2. Mild-to-moderate functional MR. 3. Elevated filling pressures. 4. No thrombus.",
            "",
            "Electronically signed 2026-08-12 16:41.",
        ]),
        ("Cardiac Catheterization Report", [
            "Procedure date: 2026-07-21.   Operator: T. Brannigan, MD.   Access: right radial.",
            "Indication: new cardiomyopathy with reduced EF; define coronary anatomy before device decisions.",
            "",
            "## Hemodynamics",
            "RA mean 9 mmHg. PA 42/22, mean 30 mmHg. PCWP 21 mmHg. Aortic pressure 124/70. LVEDP 22 mmHg. "
            "Fick cardiac index 2.1 L/min/m2.",
            "",
            "## Coronary angiography",
            "Left main: normal. LAD: smooth, mild luminal irregularity, maximum 20% proximal stenosis. "
            "LCx: normal. RCA: dominant, normal. No obstructive coronary artery disease in any vessel. TIMI 3 flow throughout.",
            "",
            "## Intervention",
            "None performed. No stent placed. Radial hemostasis band removed without incident.",
            "",
            "## Impression",
            "Angiographically normal-to-minimal coronary arteries. Findings support a non-ischemic etiology for the "
            "patient's dilated cardiomyopathy. Elevated biventricular filling pressures. Continue medical therapy.",
        ]),
        ("Medication Reconciliation - Heart Failure Clinic", [
            "Reconciled 2026-09-16 with patient and pharmacy fill history.",
            "Allergies: sulfa (rash).",
            "",
            "## Guideline-directed medical therapy for HFrEF",
            "~ Drug                         Dose              Start date    Status",
            "~ sacubitril/valsartan          97/103 mg BID     2026-02-02    active (titrated up 04-2026)",
            "~ carvedilol                    25 mg BID         2026-02-02    active (titrated up 05-2026)",
            "~ spironolactone                25 mg daily       2026-03-02    active",
            "~ dapagliflozin                 10 mg daily       2026-03-16    active",
            "~ furosemide                    40 mg daily       2026-01-20    active, dose adjusted PRN",
            "",
            "## Other medications",
            "~ amlodipine                    5 mg daily        2019          active",
            "~ atorvastatin                  20 mg nightly     2022          active",
            "~ omeprazole                    20 mg daily       2023          active",
            "",
            "## Comment",
            "Patient has remained on optimal tolerated doses of ARNI, beta blocker, MRA and SGLT2 inhibitor continuously since "
            "early February 2026, a total of 8 months of guideline-directed medical therapy at today's date. Adherence good "
            "per pharmacy refills; no missed fills. No drug intolerance. Potassium and creatinine monitored at each titration.",
        ]),
        ("ECG Report and Laboratory Results", [
            "## 12-lead ECG, 2026-09-16",
            "Sinus rhythm, rate 71. PR 206 ms (first-degree AV block). QRS 104 ms, no bundle branch block. QTc 452 ms. "
            "Nonspecific T-wave flattening laterally. No atrial fibrillation or flutter. No pathologic Q waves. "
            "Read by: S. Okonjo, MD.",
            "",
            "## Laboratory results, collected 2026-09-16",
            "~ Test               Result     Reference",
            "~ Sodium             139        135-145 mmol/L",
            "~ Potassium          4.5        3.5-5.0 mmol/L",
            "~ BUN                29 (H)     8-23 mg/dL",
            "~ Creatinine         1.5 (H)    0.6-1.2 mg/dL",
            "~ eGFR               48 (L)     >60 mL/min/1.73m2",
            "~ NT-proBNP          2,140 (H)  <450 pg/mL",
            "~ Hemoglobin         13.1       13.5-17.5 g/dL",
            "~ TSH                1.9        0.4-4.5 mIU/L",
            "~ HbA1c              5.6%",
            "",
            "Comment: CKD stage 3a, stable over three measurements since April 2026. TSH normal. Iron studies adequate.",
        ]),
        ("Shared Decision Making Visit Note - ICD", [
            "Date: 2026-09-24.   Duration: 38 minutes.   Clinician: Dr. M. Aldaine, cardiology (not the implanting physician).",
            f"Patient: {m['name']}.   Accompanied by: spouse.",
            "",
            "## Purpose",
            "Formal shared decision making encounter before any decision on primary-prevention ICD implantation.",
            "",
            "## Decision tool",
            "Reviewed the patient decision aid 'Should I get an ICD? A guide for people with heart failure' "
            "(evidence-based, patient-facing decision aid, booklet and short video). Patient and spouse viewed the video in clinic "
            "and walked through the booklet with the clinician.",
            "",
            "## Discussion",
            "Discussed the absolute reduction in risk of sudden cardiac death with an ICD versus medical therapy alone, "
            "the chance of appropriate and inappropriate shocks, device infection, lead problems, bleeding, "
            "pneumothorax, battery replacement, and the option of declining the device. Discussed driving and activity guidance. "
            "Teach-back performed; patient restated risks and benefits correctly.",
            "",
            "## Outcome",
            f"{first} values the chance of avoiding sudden death and prefers to proceed with ICD implantation. Questions answered. "
            "Decision made jointly. This visit took place before the planned implant.",
        ]),
        ("Electrophysiology Surgeon Operative Plan", [
            f"Date: 2026-09-30.   Surgeon: {m['surgeon']}, cardiac electrophysiology.",
            f"Patient: {m['name']}.",
            "",
            "## Planned procedure",
            "Insertion of a transvenous single-chamber ICD (CPT 33249), left subclavian approach under conscious sedation, "
            "with defibrillation testing per protocol. Pre-op: hold nothing; INR not applicable (no anticoagulant).",
            "",
            "## Indication",
            "Primary prevention of sudden cardiac death in non-ischemic dilated cardiomyopathy with chronic systolic heart failure.",
            "",
            "## Expected hospital course",
            "Anticipated inpatient stay: 2 midnights, for post-implant rhythm monitoring on telemetry, "
            "pocket and lead-position surveillance with a repeat chest film, device interrogation, and renal function and "
            "volume status monitoring given CKD and diuretic dosing. Discharge on post-op day 2 if device checks are normal.",
            "",
            "## Comorbidities relevant to peri-procedural risk",
            "Chronic heart failure, hypertension, and CKD stage 3 (eGFR 48).",
            "",
            "## Pre-procedure assessment",
            "Patient is clinically stable: euvolemic, NYHA III unchanged over 3 months, no admission since spring. "
            "No condition limiting life expectancy to under one year, no severe neurologic impairment, no atrial fibrillation "
            "(sinus rhythm on ECG), no active infection. No conditions that would rule out an ICD were identified.",
        ]),
    ]


def icd2_pages(m):
    """Missing: therapy duration/start dates, and shared decision making. LVEF 30%, NYHA II, non-ischemic."""
    age = age_of(m["dob"])
    return [
        pa_page(m, ICD_SERVICE, "33249", "I42.0 (Dilated cardiomyopathy); I50.22"),
        ("History and Physical - Electrophysiology Clinic", [
            f"Date: 2026-09-23.   Patient: {m['name']}   Age: {age}   Sex: {m['sex']}",
            "Referring: Dr. D. Ferreira, cardiology.",
            "",
            "## Chief complaint",
            "Dilated cardiomyopathy with reduced EF, referred for evaluation of an implantable defibrillator.",
            "",
            "## HPI",
            "Ms. Vasquez-Moyer is a 70-year-old woman with a dilated cardiomyopathy and chronic systolic heart failure. "
            "She gets mildly short of breath climbing two flights of stairs or walking uphill, but is able to do her "
            "housework and shop for groceries without stopping. No orthopnea, no PND. Occasional ankle puffiness in summer heat. "
            "No syncope, no near-syncope, no palpitations. Functional status corresponds to NYHA class II.",
            "",
            "## Cardiac history",
            "Coronary CT angiography performed this summer showed no coronary stenosis, supporting a non-ischemic cause of "
            "the cardiomyopathy (see page 4). She has not had a heart attack. No stents, no bypass surgery. "
            "No recent MI, PCI or CABG. No history of ventricular arrhythmia.",
            "",
            "## Other history",
            "Hypertension. Type 2 diabetes, diet-controlled. Hypothyroidism. Osteoarthritis of both knees. "
            "Cholecystectomy 1998. Never smoker. Lives with husband, independent in ADLs. Retired schoolteacher.",
            "",
            "## Exam",
            "BP 126/74, HR 68, SpO2 98%, BMI 27. Neck veins not distended. Lungs clear. Regular rhythm, S3 absent, soft systolic "
            "murmur at apex. No peripheral edema. Neuro non-focal.",
            "",
            "## Assessment",
            "Symptomatic non-ischemic dilated cardiomyopathy, NYHA II, LVEF about 30%. Clinically stable at last visit. "
            "Plan: ICD implantation for primary prevention. Will request authorization for elective inpatient admission.",
        ]),
        ("Echocardiography Report", [
            "Date of study: 2026-08-26.   Location: Stark County Heart & Rhythm Clinic, Echo Lab.",
            f"Patient: {m['name']}   DOB: {m['dob']}   Reading cardiologist: V. Raman, MD.",
            "",
            "## Summary of findings",
            "Technically adequate study. The left ventricle is dilated (LVEDD 6.0 cm). Left ventricular systolic function is "
            "moderately to severely reduced, with an estimated LVEF of 30% (biplane Simpson). Diffuse hypokinesis.",
            "No LV thrombus. LA mildly dilated. RV size normal, systolic function low-normal. Mild functional MR, "
            "trace TR, RVSP 32 mmHg. No pericardial effusion. Aortic root normal.",
            "",
            "## Conclusion",
            "Dilated cardiomyopathy; LVEF approximately 30% by transthoracic echocardiography.",
        ]),
        ("Coronary CT Angiography Report", [
            "Date: 2026-07-14.   Indication: new cardiomyopathy, exclude obstructive coronary artery disease.",
            "Technique: prospectively gated, 128-slice scanner, 1 sublingual nitroglycerin, 75 mL contrast. HR 58.",
            "",
            "## Findings",
            "Coronary calcium score 0 (Agatston). No coronary plaque. All three major coronary arteries and branches "
            "are patent without stenosis. Left main, LAD, LCx and RCA are normal. Right dominant circulation.",
            "Cardiac chambers: dilated left ventricle. No intracardiac thrombus. Pulmonary veins normal. "
            "Incidental 4 mm noncalcified RUL nodule, low-risk, no follow-up required in a never-smoker.",
            "",
            "## Impression",
            "No coronary artery disease. Non-ischemic dilated cardiomyopathy.",
        ]),
        ("Current Medication List", [
            f"Patient: {m['name']}   Printed from EHR 2026-09-23.   Allergies: penicillin (hives).",
            "",
            "## Active outpatient medications",
            "~ sacubitril/valsartan 97/103 mg tablet, one tablet twice daily",
            "~ metoprolol succinate 100 mg tablet, once daily",
            "~ spironolactone 25 mg tablet, once daily",
            "~ empagliflozin 10 mg tablet, once daily",
            "~ furosemide 20 mg tablet, once daily as needed for swelling",
            "~ levothyroxine 75 mcg tablet, once daily before breakfast",
            "~ acetaminophen 500 mg tablet, as needed for knee pain",
            "~ calcium with vitamin D, once daily",
            "",
            "Pharmacy: Giant Eagle Pharmacy, Canton. Med list reviewed with patient at visit, no changes today.",
            "Immunizations: influenza 2025, COVID-19 2025, pneumococcal PCV20 2024.",
        ]),
        ("ECG Report and Laboratory Results", [
            "## 12-lead ECG, 2026-09-23",
            "Normal sinus rhythm at 66 bpm. PR 168 ms. QRS 98 ms, narrow. QTc 438 ms. No ST-T changes. "
            "No evidence of prior myocardial infarction. No arrhythmia on the tracing. Interpreted by: B. Lindgren, MD.",
            "",
            "## Laboratory results, 2026-09-23",
            "~ Test               Result     Reference",
            "~ Sodium             140        135-145 mmol/L",
            "~ Potassium          4.3        3.5-5.0 mmol/L",
            "~ Creatinine         0.9        0.6-1.2 mg/dL",
            "~ eGFR               68         >60 mL/min/1.73m2",
            "~ NT-proBNP          780 (H)    <450 pg/mL",
            "~ Hemoglobin         12.8       12.0-15.5 g/dL",
            "~ HbA1c              6.2%",
            "~ TSH                2.4        0.4-4.5 mIU/L",
        ]),
        ("Electrophysiology Surgeon Operative Plan", [
            f"Date: 2026-09-25.   Surgeon: {m['surgeon']}, cardiac electrophysiology.   Patient: {m['name']}.",
            "",
            "## Procedure",
            "Transvenous ICD implantation (single chamber), left pectoral pocket, CPT 33249.",
            "",
            "## Indication",
            "Primary prevention in non-ischemic dilated cardiomyopathy, LVEF 30%, NYHA class II.",
            "",
            "## Expected stay",
            "Two midnights of inpatient care are expected: overnight telemetry, post-implant chest radiograph, "
            "device interrogation the next morning, and observation of the pocket. Discharge on the second morning, assuming "
            "no complications.",
            "",
            "## Comorbidities and risk factors",
            "Heart failure with reduced EF, hypertension, type 2 diabetes (diet-controlled), hypothyroidism.",
            "",
            "## Clinical status",
            "Clinically stable and euvolemic. No limiting conditions: no severe neurologic injury, no non-cardiac illness with "
            "a prognosis under 1 year, rhythm is sinus (no atrial fibrillation). Consent will be obtained on the day of admission.",
        ]),
    ]


def icd3_pages(m):
    """Newer echo (Aug 2026, LVEF 42%) on page 3; older echo (Nov 2025, LVEF 30%) on page 7. 42% governs."""
    age = age_of(m["dob"])
    return [
        pa_page(m, ICD_SERVICE, "33249", "I42.0 (Dilated cardiomyopathy); I50.22"),
        ("Cardiology Consultation Note", [
            f"Date of service: 2026-09-09.   Patient: {m['name']}   Age: {age}   Sex: {m['sex']}",
            "",
            "## HPI",
            f"{age}-year-old man with a non-ischemic dilated cardiomyopathy diagnosed last year. He was started on "
            "heart failure medications after the diagnosis. He walks his dog daily and can climb a flight of stairs; "
            "he notes slight breathlessness with brisk walking uphill but not with ordinary activity. "
            "No orthopnea. No syncope. No ICD discharges (no device). Symptoms put him in NYHA class II.",
            "",
            "## Ischemic work-up and events",
            "Cardiac catheterization (see page 4) showed no obstructive coronary disease. He has not had a myocardial infarction, "
            "bypass surgery or stent at any time, certainly not within the last year.",
            "",
            "## PMH",
            "Hypertension. Hyperlipidemia. Gout. Chronic kidney disease stage 2. Left rotator cuff repair 2017. "
            "Non-smoker. Occasional wine.",
            "",
            "## Exam",
            "BP 122/76, HR 64, SpO2 98%, BMI 31. No JVD. Clear lungs. Regular rhythm, no gallop. No edema.",
            "",
            "## Assessment and plan",
            "Non-ischemic dilated cardiomyopathy with HFrEF, NYHA II. His EF has improved on therapy. "
            "Continue GDMT. Discussed ICD candidacy with EP; formal shared decision making visit on 2026-09-18 (page 5). "
            "Surgical plan on page 6.",
        ]),
        ("Echocardiogram Report - Most Recent", [
            "Study date: 2026-08-20.   Type: complete transthoracic echocardiogram with contrast (Definity).",
            f"Patient: {m['name']}   DOB: {m['dob']}   Interpreting: A. Nwosu, MD, FACC.",
            "Comparison: no prior study available for comparison at the time of this interpretation.",
            "",
            "## Findings",
            "Left ventricle mildly dilated, LVIDd 5.6 cm. Mild global hypokinesis, worse in the inferolateral wall. "
            "Overall left ventricular systolic function is mildly reduced, LVEF 42% (biplane Simpson, contrast-enhanced).",
            "Normal LV wall thickness. Grade I diastolic dysfunction. Left atrium mildly dilated. "
            "RV normal size and function. Trivial MR and TR. No pericardial effusion. No thrombus.",
            "",
            "## Impression",
            "Mild LV dilatation with mildly reduced systolic function, LVEF 42%.",
        ]),
        ("Cardiac Catheterization and Hemodynamic Report", [
            "Date: 2025-11-18.   Operator: J. Petrakis, MD.   Access: right radial.",
            f"Patient: {m['name']}.",
            "",
            "## Coronary angiography",
            "Left main normal. LAD with minimal luminal irregularities, no flow-limiting stenosis. LCx normal. RCA dominant, normal. "
            "No obstructive coronary artery disease.",
            "",
            "## Hemodynamics",
            "LVEDP 20 mmHg. PCWP 18 mmHg. No gradient across the aortic valve. Right heart pressures mildly elevated.",
            "",
            "## Impression",
            "Non-ischemic cardiomyopathy. No intervention performed.",
            "",
            "## Heart failure medications on file (clinic list, updated 2026-09-09)",
            "~ Drug                         Dose              Start date",
            "~ sacubitril/valsartan          97/103 mg BID     2025-12-08",
            "~ carvedilol                    25 mg BID         2025-12-08",
            "~ spironolactone                25 mg daily       2026-01-12",
            "~ empagliflozin                 10 mg daily       2026-01-12",
            "~ amlodipine                    5 mg daily        2018",
            "~ atorvastatin                  40 mg daily       2020",
            "~ allopurinol                   100 mg daily      2019",
            "Total time on guideline-directed medical therapy: 9 months, adherence confirmed.",
        ]),
        ("Shared Decision Making Visit - ICD", [
            f"Date: 2026-09-18.   Clinician: Dr. P. Venkataraman.   Patient: {m['name']}; wife present.",
            "",
            "Patient-facing evidence-based ICD decision aid (video and printed worksheet from the national heart failure "
            "decision-support program) was reviewed together at this visit. Benefits (lower risk of sudden cardiac death), "
            "risks (infection, shocks, lead failure, bleeding), alternatives (medical therapy alone, wearable defibrillator), "
            "and personal values were discussed for 30 minutes. The patient asked good questions and understood the content.",
            "",
            "The patient wishes to proceed. Decision made jointly with the clinician, before scheduling the implant.",
        ]),
        ("Electrophysiology Surgeon Operative Plan", [
            f"Date: 2026-09-29.   Surgeon: {m['surgeon']}, electrophysiology.   Patient: {m['name']}.",
            "",
            "## Planned procedure",
            "Transvenous ICD implant, CPT 33249, left subclavian access.",
            "",
            "## Indication as submitted",
            "Primary-prevention ICD for non-ischemic dilated cardiomyopathy, on a background of HFrEF, NYHA II. "
            "See imaging in this packet for the most current ventricular function.",
            "",
            "## Hospital course",
            "Expected length of stay: 2 midnights for post-implant telemetry and device check.",
            "",
            "## Comorbidities",
            "Heart failure, hypertension, hyperlipidemia, chronic kidney disease stage 2, gout.",
            "",
            "## Condition",
            "Clinically stable, euvolemic, no conditions limiting survival, no severe neurologic impairment, "
            "no atrial fibrillation. No exclusion identified.",
        ]),
        ("Outside Records - Echocardiogram (prior)", [
            "Records received from: Fairview Regional Medical Center, Cardiology Lab. Released 2026-09-02.",
            "",
            "Study date: 2025-11-04.   Patient: " + m["name"] + "   DOB: " + m["dob"],
            "Indication: new dyspnea and elevated BNP, evaluate LV function.",
            "",
            "## Findings",
            "Left ventricle moderately dilated (LVIDd 6.1 cm). Global hypokinesis. LVEF 30% by biplane Simpson. "
            "Moderate functional mitral regurgitation. LA moderately enlarged. RVSP 41 mmHg. No effusion.",
            "",
            "## Impression",
            "Dilated cardiomyopathy with moderately to severely reduced LVEF (30%). Recommend ischemic evaluation "
            "and initiation of guideline-directed medical therapy.",
            "",
            "Signed: Dr. E. Ramaswamy, 2025-11-04.",
            "",
            "## ECG, 2026-09-09 (this practice)",
            "Sinus rhythm 62 bpm, PR 174 ms, QRS 96 ms, no pathologic Q waves, QTc 430 ms.",
        ]),
    ]


def icd5_pages(m):
    """Ischemic cardiomyopathy, LVEF 31%, NYHA II, SDM present, NSTEMI 2026-09-09 (25 days before request)."""
    age = age_of(m["dob"])
    return [
        pa_page(m, ICD_SERVICE, "33249", "I25.5 (Ischemic cardiomyopathy); I50.22"),
        ("Cardiology Consultation - ICD Evaluation", [
            f"Date: 2026-09-29.   Patient: {m['name']}   Age: {age}   Sex: {m['sex']}",
            "",
            "## Reason for referral",
            "Primary-prevention ICD evaluation, ischemic cardiomyopathy with reduced ejection fraction.",
            "",
            "## History of present illness",
            f"{age}-year-old man with long-standing multivessel coronary artery disease managed medically, and ischemic "
            "cardiomyopathy with chronic systolic heart failure. He reports dyspnea on walking up a slope or more than "
            "two blocks, with no symptoms during routine household tasks and none at rest (NYHA II). No syncope. "
            "No sustained ventricular arrhythmia documented.",
            "He was hospitalized earlier this month; see the interval history below and the discharge summary on page 6.",
            "",
            "## Interval history",
            "Admitted 2026-09-09 to Erie Shores Medical Center with chest pressure and a troponin rise, diagnosed with an "
            "NSTEMI. Coronary angiography the next day showed known multivessel disease without a target for PCI; "
            "managed medically. Discharged 2026-09-12 free of angina.",
            "",
            "## PMH",
            "Coronary artery disease, ischemic cardiomyopathy, hypertension, hyperlipidemia, type 2 diabetes (metformin). "
            "No CABG. No prior stent. Former smoker, quit 2015. Left inguinal hernia repair 2012.",
            "",
            "## Exam",
            "BP 124/70, HR 66, SpO2 96%. Lungs with minimal bibasilar crackles. No edema. Regular rhythm.",
            "",
            "## Assessment and plan",
            "Ischemic cardiomyopathy, LVEF 31%, NYHA II, status post recent NSTEMI. Planned ICD per EP. "
            "SDM visit completed (page 7). Continue GDMT and antiplatelet therapy.",
        ]),
        ("Echocardiogram Report", [
            "Study date: 2026-09-11 (inpatient, post-NSTEMI day 2).   Type: limited TTE.",
            f"Patient: {m['name']}.   Reader: C. Hoffmeyer, MD.",
            "",
            "## Findings",
            "Left ventricle dilated, LVEDD 6.1 cm. Akinesis of the basal-to-mid inferior and inferolateral segments with "
            "hypokinesis of the anterior wall. Quantitative LVEF 31% (biplane Simpson).",
            "Mild-to-moderate ischemic mitral regurgitation. RV function preserved. LA mildly dilated. No LV thrombus. "
            "No pericardial effusion.",
            "",
            "## Impression",
            "Ischemic cardiomyopathy with LVEF 31% by echocardiography. Regional wall-motion abnormalities in the RCA/LCx territory.",
        ]),
        ("Cardiac Catheterization Report", [
            "Date: 2026-09-10.   Indication: NSTEMI, troponin I peak 14.2 ng/mL.   Operator: R. Ingram, MD.",
            "",
            "## Angiographic findings",
            "Left main: 30% distal stenosis. LAD: diffuse 60-70% mid disease, small caliber distal vessel. "
            "LCx: 80% proximal OM1 stenosis, diffusely diseased distal vessel. RCA: chronic total occlusion proximal, "
            "collateralized from the left system. Presumed culprit: subtotal OM1 lesion with small territory.",
            "",
            "## Decision",
            "Heart team review: no suitable target for PCI given diffuse small-vessel disease; CABG not recommended "
            "at this time (poor distal targets, patient preference). Medical management intensified. No stent deployed.",
            "",
            "## Hemodynamics",
            "LVEDP 24 mmHg. Aortic 128/74.",
        ]),
        ("Heart Failure Medication List with Start Dates", [
            f"Patient: {m['name']}.   Reconciled 2026-09-29.",
            "",
            "~ Drug                          Dose              Start date",
            "~ sacubitril/valsartan          49/51 mg BID      2025-08-04",
            "~ metoprolol succinate          100 mg daily      2025-08-04",
            "~ eplerenone                    25 mg daily       2025-09-15",
            "~ dapagliflozin                 10 mg daily       2025-10-20",
            "~ furosemide                    40 mg daily       2025-08-04",
            "~ aspirin                       81 mg daily       2012",
            "~ clopidogrel                   75 mg daily       2026-09-10 (post NSTEMI)",
            "~ rosuvastatin                  40 mg daily       2026-09-10 (increased)",
            "~ metformin                     1000 mg BID       2016",
            "",
            "Patient has been on guideline-directed HF therapy for more than a year (14 months since 2025-08).",
        ]),
        ("Hospital Discharge Summary (Erie Shores Medical Center)", [
            f"Patient: {m['name']}.   Admitted: 2026-09-09.   Discharged: 2026-09-12.",
            "",
            "## Principal diagnosis",
            "Non-ST elevation myocardial infarction (NSTEMI), onset 2026-09-09.",
            "",
            "## Hospital course",
            "Presented with 2 hours of substernal chest pressure. ECG with lateral ST depression, troponin I peak 14.2 ng/mL. "
            "Started on heparin, dual antiplatelet therapy and high-intensity statin. Cath 2026-09-10: multivessel disease, "
            "no PCI or CABG possible (see page 4). Limited echo 2026-09-11 with LVEF 31%. Remained hemodynamically stable, "
            "no recurrent chest pain, no arrhythmia on telemetry.",
            "",
            "## Disposition",
            "Discharged home 2026-09-12 in stable condition, NYHA II. Follow up in cardiology within 2 weeks. "
            "ICD evaluation as an outpatient.",
        ]),
        ("Shared Decision Making Visit Note - ICD", [
            "Date: 2026-09-30.   Clinician: Dr. H. Abernathy (EP).   Duration 35 minutes.   Patient and daughter present.",
            "",
            "We used the ICD patient decision aid (illustrated pamphlet and interactive web tool, evidence-based) to "
            "review the survival benefit of a primary-prevention ICD, procedural risk, shocks, and the alternative of medical "
            "therapy alone. The patient described his own priorities and chose to move ahead with the device.",
            "Informed of the recent heart attack and the usual waiting period; patient states understanding.",
            "",
            "## Outcome",
            "Shared decision making visit completed and documented before implant scheduling.",
        ]),
        ("Electrophysiology Surgeon Operative Plan", [
            f"Date: 2026-09-30.   Surgeon: {m['surgeon']}, cardiac electrophysiology.   Patient: {m['name']}.",
            "",
            "## Procedure",
            "Transvenous ICD (single chamber), CPT 33249.",
            "",
            "## Indication",
            "Primary prevention, ischemic cardiomyopathy with LVEF 31%, NYHA class II.",
            "",
            "## Expected stay",
            "2 midnights, telemetry and device interrogation, pocket check.",
            "",
            "## Comorbidities",
            "Coronary artery disease, heart failure, type 2 diabetes, hypertension, hyperlipidemia.",
            "",
            "## Status",
            "Clinically stable since discharge on 09-12. No other conditions limiting survival; no atrial fibrillation; "
            "no severe neurologic impairment.",
        ]),
    ]


# --------------------------------------------------------------------------------------
# Bariatric packets
# --------------------------------------------------------------------------------------
def bar1_pages(m):
    """BMI 42.3, T2DM + HTN + OSA, 12-month supervised program with RD plus anti-obesity drug, psych cleared."""
    age = age_of(m["dob"])
    return [
        pa_page(m, BAR_SERVICE, "43644", "E66.01 (Morbid obesity); E11.9; G47.33"),
        ("Bariatric Surgery Consultation / History and Physical", [
            f"Date: 2026-09-15.   Patient: {m['name']}   Age: {age}   Sex: {m['sex']}",
            "",
            "## Chief complaint",
            "Severe obesity with obesity-related disease; evaluation for surgical weight loss.",
            "",
            "## HPI",
            "Ms. Delgado-Finch is a 66-year-old woman with class III obesity of more than twenty years' duration. She has type 2 "
            "diabetes, hypertension and obstructive sleep apnea, each of which is worsening. Knee and back pain now limit walking. "
            "She completed a 12-month physician-supervised weight management program (details on pages 3 and 4) and, despite "
            "full participation, has regained the weight she lost.",
            "",
            "## Anthropometrics",
            "Height 65 in. Weight 254 lb. BMI 42.3 kg/m2 (measured in clinic 2026-09-15).",
            "",
            "## Past medical history",
            "Type 2 diabetes mellitus (on metformin, HbA1c 8.1%). Hypertension. Obstructive sleep apnea on CPAP. "
            "Osteoarthritis of the knees. Hysterectomy 2004. Cholecystectomy 2012.",
            "",
            "## Medications",
            "Metformin 1000 mg BID, lisinopril 20 mg daily, amlodipine 5 mg daily, liraglutide 3 mg daily (weight management), "
            "atorvastatin 20 mg nightly, acetaminophen PRN. NKDA.",
            "",
            "## Social",
            "Never smoker, no alcohol. Lives with husband. Retired bookkeeper.",
            "",
            "## Exam",
            "BP 134/82, HR 78, SpO2 96%. Neck circumference 17 in. Abdomen obese, soft, no hernia. Mild bilateral knee crepitus. "
            "No edema.",
            "",
            "## Assessment and plan",
            "Class III obesity with T2DM, hypertension and OSA, previously unsuccessful with medical treatment. "
            "Candidate for laparoscopic Roux-en-Y gastric bypass. Pre-op workup completed.",
        ]),
        ("Registered Dietitian Notes - Supervised Weight Management Program", [
            "Program: Physician-supervised medical weight management program, enrolled 2025-08-12, completed 2026-08-12.",
            f"Patient: {m['name']}.   Dietitian: Ruth Calloway, RD, LDN.   Supervising physician: Dr. A. Mehra.",
            "",
            "## Structure",
            "Monthly visits with the registered dietitian, 12 consecutive monthly visits, all attended (12 of 12). "
            "1,200-1,400 kcal meal plan, food and activity logs reviewed at each visit, structured walking program, "
            "behavioral counseling, and physician review quarterly.",
            "",
            "## Weight trajectory",
            "~ Visit        Weight (lb)   BMI",
            "~ 2025-08-12   268           44.6   (program intake)",
            "~ 2025-11-11   259           43.1",
            "~ 2026-02-10   252           41.9   (nadir)",
            "~ 2026-05-12   258           42.9",
            "~ 2026-08-12   266           44.3   (program exit)",
            "",
            "## Outcome",
            "Initial loss of 16 lb over six months, followed by regain of 14 lb despite adherence; the patient plateaued "
            "after month 6. Program judged unsuccessful for sustained weight loss. No further benefit expected from "
            "continuing non-surgical care. Recommend surgical consultation.",
        ]),
        ("Primary Care Notes and Anti-Obesity Medication", [
            f"Patient: {m['name']}.   PCP: Dr. L. Osei.   Visits 2025-09 through 2026-07 summarized.",
            "",
            "## Anti-obesity pharmacotherapy",
            "Liraglutide 3 mg daily (Saxenda) started 2025-09-15 as an adjunct to the dietitian program; titrated over 5 weeks. "
            "Continued 11 months. Early loss of about 9 lb then plateau; nausea mild. Weight regained while still on full dose. "
            "Considered unsuccessful.",
            "",
            "## Comorbidity management",
            "Type 2 diabetes: metformin, HbA1c 8.3% (2025-08), 8.1% (2026-07). Hypertension: lisinopril and amlodipine, "
            "BP 130s/80s. Sleep apnea: diagnosed on polysomnography (AHI 34/hr), on CPAP with good adherence.",
            "",
            "## Other",
            "Influenza vaccine given 2025-10. Colonoscopy 2024 normal. Mammogram 2026-03 normal. Statin continued.",
        ]),
        ("Psychological Evaluation - Pre-Bariatric", [
            "Date: 2026-08-26.   Evaluator: Dr. S. Landry, PhD, clinical psychologist.   Patient: " + m["name"],
            "",
            "## Method",
            "90-minute clinical interview, MMPI-3, BDI-II, structured eating disorder screen.",
            "",
            "## Findings",
            "Mood euthymic. BDI-II score 7 (minimal). No binge-eating disorder, no bulimia, no active substance use. "
            "Understands the procedure, lifelong vitamin supplementation, and dietary changes. Realistic expectations. "
            "Supportive spouse. No history of psychiatric hospitalization.",
            "",
            "## Opinion",
            "Psychologically cleared for bariatric surgery. No contraindication identified. Recommend post-operative "
            "support group.",
        ]),
        ("Laboratory, Sleep Study and Pre-operative Testing", [
            "## Labs 2026-09-02",
            "~ HbA1c             8.1%",
            "~ Fasting glucose   158 mg/dL",
            "~ Creatinine        0.8 mg/dL",
            "~ ALT / AST         38 / 31 U/L",
            "~ Vitamin D 25-OH   19 ng/mL (L)",
            "~ B12               412 pg/mL",
            "~ Hemoglobin        13.4 g/dL",
            "",
            "## Polysomnography (2024-11): AHI 34 events/hour, moderate-to-severe OSA. CPAP prescribed.",
            "## Upper endoscopy 2026-08-20: mild gastritis, H. pylori negative, no hiatal hernia.",
            "## ECG 2026-08-28: normal sinus rhythm. Chest X-ray: clear.",
            "",
            "Comment: pre-operative clearance from cardiology not required; low risk by RCRI.",
        ]),
        ("Bariatric Surgeon Operative Plan", [
            f"Date: 2026-09-22.   Surgeon: {m['surgeon']}, bariatric surgery.   Patient: {m['name']}.",
            "",
            "## Procedure",
            "Laparoscopic Roux-en-Y gastric bypass (CPT 43644). Five ports, 30 mL gastric pouch, 100 cm Roux limb, "
            "stapled gastrojejunostomy, leak test with methylene blue.",
            "",
            "## Expected hospital course",
            "Expected length of stay: 2 midnights. Day 0 monitoring with CPAP, DVT prophylaxis, glucose management. "
            "Upper GI series post-op day 1 as needed. Discharge on post-operative day 2 if tolerating liquids.",
            "",
            "## Comorbidities driving peri-operative risk",
            "Type 2 diabetes, hypertension, obstructive sleep apnea requiring CPAP.",
            "",
            "## Readiness",
            "Dietitian-supervised program completed, psychological clearance obtained, patient educated, "
            "and consent discussion scheduled for admission day.",
        ]),
    ]


def bar2_pages(m):
    """BMI 39.4, T2DM, LOS 2. NOTHING about any prior supervised/medical weight-loss treatment."""
    age = age_of(m["dob"])
    return [
        pa_page(m, BAR_SERVICE, "43644", "E66.01 (Morbid obesity); E11.65"),
        ("Bariatric Surgery Evaluation - History and Physical", [
            f"Date: 2026-09-18.   Patient: {m['name']}   Age: {age}   Sex: {m['sex']}",
            "Referral source: Dr. G. Pruitt (primary care).",
            "",
            "## Reason for visit",
            "Consultation regarding surgical treatment of severe obesity.",
            "",
            "## HPI",
            "Mr. Eberhardt is a 66-year-old man with severe obesity and type 2 diabetes. He reports gradual weight gain over "
            "adulthood and is now bothered by exertional fatigue, knee pain on stairs, and a rising HbA1c. "
            "He is motivated and has read about gastric bypass. No history of GI bleeding, ulcer disease or reflux requiring surgery.",
            "",
            "## Measurements",
            "Height 68 in. Weight 259 lb. BMI 39.4 kg/m2 today.",
            "",
            "## Past medical history",
            "Type 2 diabetes mellitus. Benign prostatic hyperplasia. Right inguinal hernia repair 2009. "
            "Left knee arthroscopy 2015.",
            "",
            "## Medications",
            "Metformin 1000 mg BID, glipizide 5 mg daily, tamsulosin 0.4 mg nightly. NKDA.",
            "",
            "## Social history",
            "Married, retired electrician. Quit smoking 2002. Two to three beers a week. Drives, independent.",
            "",
            "## Exam",
            "BP 128/78, HR 76, SpO2 97%. Obese abdomen, no scars other than hernia repair site, no hernia currently. "
            "No edema. Gait normal.",
            "",
            "## Impression",
            "Class II obesity (BMI 39.4) with type 2 diabetes. Surgical evaluation under way. Orders: labs, EGD, "
            "psychological evaluation, anesthesia screen.",
        ]),
        ("Primary Care Progress Note", [
            f"Date: 2026-08-27.   Patient: {m['name']}.   PCP: Dr. G. Pruitt.",
            "",
            "## Diabetes",
            "HbA1c 7.9% (previously 7.4%). Home fasting glucose 130-160. No hypoglycemia. Foot exam normal, "
            "monofilament intact. Retinal exam 2026-02 without retinopathy. Urine albumin/creatinine 18 mg/g (normal).",
            "",
            "## Other",
            "BP 126/76 off antihypertensives. Lipids: LDL 98 on no statin; discussed starting atorvastatin, patient will think about it. "
            "Prostate: IPSS 8, stable on tamsulosin. Hearing screen normal. Immunizations current.",
            "",
            "## Plan",
            "Refer to bariatric surgery for evaluation as requested by the patient. Recheck HbA1c in 3 months. "
            "Continue metformin and glipizide.",
        ]),
        ("Laboratory and Pre-operative Testing", [
            "## Labs 2026-09-10",
            "~ HbA1c             7.9%",
            "~ Fasting glucose   149 mg/dL",
            "~ Creatinine        1.0 mg/dL",
            "~ ALT / AST         44 / 36 U/L",
            "~ Total cholesterol 182 mg/dL",
            "~ TSH               1.7 mIU/L",
            "~ Vitamin D 25-OH   26 ng/mL",
            "~ Hemoglobin        14.6 g/dL",
            "",
            "## Upper endoscopy 2026-09-12",
            "Normal esophagus, small (<2 cm) sliding hiatal hernia, mild antral gastritis, biopsies negative for H. pylori.",
            "## ECG 2026-09-12: sinus rhythm, no acute changes. Chest X-ray: no infiltrate.",
            "## Liver ultrasound: mild hepatic steatosis.",
        ]),
        ("Psychological Evaluation", [
            f"Date: 2026-09-14.   Evaluator: Dr. W. Haddad, PsyD.   Patient: {m['name']}",
            "",
            "Clinical interview and standardized inventories (BDI-II 5, GAD-7 3). No active mood or anxiety disorder, "
            "no eating disorder, no substance misuse. Good understanding of risks, benefits and lifelong follow-up. "
            "Support from spouse. Cleared from a psychological standpoint to proceed with bariatric surgery.",
        ]),
        ("Anesthesia Pre-operative Screening", [
            f"Date: 2026-09-21.   Patient: {m['name']}.   ASA class: III (obesity, diabetes).",
            "",
            "Mallampati II, neck circumference 16.5 in, STOP-BANG 2 (low risk for sleep apnea). Good functional capacity, "
            "more than 4 METs. No cardiac symptoms. Airway: no difficult-airway predictors. NPO instructions given. "
            "Hold glipizide the morning of surgery. Continue metformin until the day before.",
        ]),
        ("Bariatric Surgeon Operative Plan", [
            f"Date: 2026-09-28.   Surgeon: {m['surgeon']}, bariatric surgery.   Patient: {m['name']}.",
            "",
            "## Procedure",
            "Laparoscopic Roux-en-Y gastric bypass, CPT 43644.",
            "",
            "## Hospital course",
            "Inpatient stay of 2 midnights anticipated: glucose management with insulin sliding scale, early ambulation, "
            "VTE prophylaxis, advancement from clear liquids to full liquids, hydration. Discharge on post-operative day 2.",
            "",
            "## Comorbidity",
            "Type 2 diabetes mellitus on oral agents.",
            "",
            "## Plan",
            "Pre-op labs and testing complete; psychological clearance obtained; anesthesia screened. Will request inpatient authorization.",
        ]),
    ]


def bar3_pages(m):
    """Most recent BMI 33.8 (2026-09-14) on page 2; intake BMI 36.1 (2026-03-09) on page 5. Latest governs."""
    age = age_of(m["dob"])
    return [
        pa_page(m, BAR_SERVICE, "43644", "E66.01; E11.9"),
        ("Bariatric Surgeon Pre-operative Visit", [
            f"Date: 2026-09-14.   Patient: {m['name']}   Age: {age}   Sex: {m['sex']}",
            "",
            "## Interval history",
            "Ms. Prescott is a 65-year-old woman with obesity and type 2 diabetes, seen after six months in our "
            "supervised weight management program. She has lost some weight but remains symptomatic: diabetes not at goal "
            "(HbA1c 7.8%), joint pain, fatigue.",
            "",
            "## Measurements today",
            "Height 63 in, weight 191 lb, BMI 33.8 kg/m2.",
            "",
            "## PMH",
            "Type 2 diabetes mellitus. Hypothyroidism. Cesarean section 1992. Cataract surgery 2024. Never smoker.",
            "",
            "## Medications",
            "Metformin 1000 mg BID, empagliflozin 10 mg daily, levothyroxine 88 mcg daily, phentermine discontinued 2026-06.",
            "",
            "## Exam",
            "BP 122/74, HR 80, SpO2 98%. Abdomen soft, no hernia. No edema.",
            "",
            "## Plan",
            "Proceed with the surgical pathway as planned; request authorization for laparoscopic Roux-en-Y gastric bypass. "
            "Operative plan on page 7.",
        ]),
        ("Primary Care Note", [
            f"Date: 2026-08-19.   Patient: {m['name']}.   PCP: Dr. T. Wong.",
            "",
            "Type 2 diabetes: HbA1c 7.8%, on metformin and empagliflozin, no hypoglycemia. Retinopathy screen negative 2026-04. "
            "Kidney function normal (eGFR 84). Hypothyroidism: TSH 2.0. Blood pressure 120s/70s without treatment. "
            "Lipids: LDL 104. Discussed bariatric surgery goals and glycemic outcomes.",
            "",
            "Health maintenance: mammogram 2026-05 normal, DEXA 2025 osteopenia, shingles vaccine complete.",
        ]),
        ("Psychological Evaluation", [
            f"Date: 2026-07-30.   Evaluator: Dr. E. Navarro, PhD.   Patient: {m['name']}",
            "",
            "Interview and screening instruments reviewed. PHQ-9 4, GAD-7 2, no disordered eating (EDE-Q below cut-off), no "
            "substance use disorder. Good insight into the lifelong commitments of bariatric surgery. Psychologically "
            "cleared to proceed.",
        ]),
        ("Weight Management Program - Dietitian Intake and Progress Notes", [
            "Program: supervised weight management program, Capital Bariatric Surgery Associates.   Dietitian: M. Okoye, RD.",
            f"Patient: {m['name']}.",
            "",
            "## Program intake, 2026-03-09",
            "Height 63 in, weight 204 lb, BMI 36.1 kg/m2 at intake. Comorbid type 2 diabetes. Baseline 24-hour recall shows "
            "frequent sweetened beverages and late-evening eating. Goals: 1,300-kcal plan, protein target 70 g/day, "
            "30 min walking 5 days/week.",
            "",
            "## Follow-up",
            "Monthly visits 2026-04 through 2026-09 attended. Intermediate weights: 2026-05 200 lb, 2026-07 195 lb. "
            "Physician-supervised, with phentermine 37.5 mg daily added 2026-04 and stopped 2026-06 for palpitations.",
            "",
            "## Assessment",
            "Six months of supervised dietary and medication-assisted treatment with partial, non-durable weight loss; "
            "glycemic control not adequate. Medical treatment judged unsuccessful.",
        ]),
        ("Laboratory and Pre-operative Testing", [
            "## Labs 2026-09-08",
            "~ HbA1c             7.8%",
            "~ Fasting glucose   141 mg/dL",
            "~ Creatinine        0.8 mg/dL",
            "~ ALT / AST         30 / 27 U/L",
            "~ TSH               2.0 mIU/L",
            "~ Ferritin          58 ng/mL",
            "~ Vitamin B12       498 pg/mL",
            "",
            "## Upper endoscopy 2026-08-28: normal, no hiatal hernia, H. pylori negative.",
            "## ECG 2026-09-02: normal sinus rhythm. Echocardiogram not indicated.",
        ]),
        ("Bariatric Surgeon Operative Plan", [
            f"Date: 2026-09-21.   Surgeon: {m['surgeon']}, bariatric surgery.   Patient: {m['name']}.",
            "",
            "## Procedure",
            "Laparoscopic Roux-en-Y gastric bypass, CPT 43644.",
            "",
            "## Expected length of stay",
            "The patient will need to stay in hospital for 2 midnights: glucose monitoring and insulin coverage, "
            "pain control, VTE prophylaxis, ambulation, diet advancement.",
            "",
            "## Comorbidity",
            "Type 2 diabetes mellitus.",
            "",
            "## Readiness",
            "Work-up complete, psychological clearance obtained, patient educated.",
        ]),
    ]


def bar4_pages(m):
    """BMI 38.2; prior supervised program documented; H&P states NO diabetes, HTN, sleep apnea, or other conditions."""
    age = age_of(m["dob"])
    return [
        pa_page(m, BAR_SERVICE, "43644", "E66.01 (Morbid obesity)"),
        ("Bariatric Surgery Consultation - History and Physical", [
            f"Date: 2026-09-17.   Patient: {m['name']}   Age: {age}   Sex: {m['sex']}",
            "",
            "## Reason for visit",
            "Evaluation for gastric bypass; severe obesity.",
            "",
            "## HPI",
            "Mr. Adeyemi is a 67-year-old man with obesity since his thirties. He is otherwise in good health. He enrolled in a "
            "supervised nutrition program last year and wants a more durable solution.",
            "",
            "## Anthropometrics",
            "Height 70 in. Weight 266 lb. BMI 38.2 kg/m2.",
            "",
            "## Past medical history",
            "The patient has no diabetes (HbA1c 5.4%), no hypertension (BP 118/74 today, on no antihypertensives), and no sleep "
            "apnea (STOP-BANG 1, no snoring). He has no other obesity-related medical conditions: no dyslipidemia, no reflux, "
            "no fatty liver, no significant joint disease. Remote appendectomy 1990. Seasonal allergic rhinitis.",
            "",
            "## Medications",
            "Cetirizine 10 mg as needed. No chronic daily medications. NKDA.",
            "",
            "## Social",
            "Never smoker. Rare alcohol. Works as a high-school principal. Married.",
            "",
            "## Exam",
            "Well-appearing. Heart and lungs normal. Abdomen obese, soft, nontender. No edema.",
            "",
            "## Impression",
            "Class II obesity, BMI 38.2, no obesity-related comorbidities. Proceeding with the surgical evaluation.",
        ]),
        ("Dietitian Program Notes - Supervised Weight Management", [
            "Program: Mahoning Valley supervised nutrition and weight management program, 2025-09-08 to 2026-06-08 (9 months).",
            f"Patient: {m['name']}.   Dietitian: Priscilla Nwankwo, RD, CDCES.",
            "",
            "## Summary",
            "Nine consecutive monthly dietitian visits plus 4 physician visits; structured low-calorie meal plan, activity "
            "program and food logging. Documented weights: 272 lb at intake (2025-09-08), nadir 261 lb (2026-01-12), "
            "back to 268 lb at exit (2026-06-08).",
            "",
            "## Assessment",
            "Participation excellent, weight loss not sustained. Prior supervised medical treatment was unsuccessful. "
            "Recommend surgical evaluation.",
        ]),
        ("Primary Care Note", [
            f"Date: 2026-08-11.   Patient: {m['name']}.   PCP: Dr. B. Rosales.",
            "",
            "Annual wellness visit. Blood pressure 116/72, heart rate 68. Fasting glucose 92, HbA1c 5.4%. Lipid panel normal "
            "(LDL 96, HDL 48). Liver enzymes normal. Colonoscopy 2023 normal. PSA 1.1. Immunizations current. "
            "Discussed referral to bariatric surgery at the patient's request.",
        ]),
        ("Psychological Evaluation", [
            f"Date: 2026-09-02.   Evaluator: Dr. R. Kapoor, PhD.   Patient: {m['name']}",
            "",
            "Clinical interview and screening: PHQ-9 2, GAD-7 1; no binge eating; no substance misuse; expectations realistic; "
            "family support present. Cleared psychologically for surgery.",
        ]),
        ("Laboratory and Pre-operative Testing", [
            "## Labs 2026-09-05",
            "~ HbA1c             5.4%",
            "~ Fasting glucose   92 mg/dL",
            "~ Creatinine        0.9 mg/dL",
            "~ ALT / AST         26 / 24 U/L",
            "~ TSH               1.5 mIU/L",
            "~ Vitamin D 25-OH   31 ng/mL",
            "",
            "## Upper endoscopy 2026-09-10: normal.",
            "## ECG 2026-09-10: normal sinus rhythm.",
        ]),
        ("Bariatric Surgeon Operative Plan", [
            f"Date: 2026-09-24.   Surgeon: {m['surgeon']}, bariatric surgery.   Patient: {m['name']}.",
            "",
            "## Procedure",
            "Laparoscopic Roux-en-Y gastric bypass, CPT 43644.",
            "",
            "## Expected hospital stay",
            "Two midnights anticipated for post-operative monitoring, pain control, ambulation, VTE prophylaxis, and diet advancement.",
            "",
            "## Pre-operative status",
            "Work-up complete. Psychological clearance documented. Medical history as per H&P.",
        ]),
    ]


# --------------------------------------------------------------------------------------
# Image-only scan (icd4)
# --------------------------------------------------------------------------------------
def find_pdftoppm():
    p = shutil.which("pdftoppm")
    if p:
        return p
    cand = r"C:\Users\prans\AppData\Local\Programs\MiKTeX\miktex\bin\x64\pdftoppm.exe"
    if os.path.exists(cand):
        return cand
    raise SystemExit("pdftoppm not found")


def degrade_to_scan(text_pdf, out_pdf, seed):
    """Render each page to an image, rotate 1-3 degrees, add noise, lower contrast, blur, save an image-only PDF."""
    rng = random.Random(seed)
    nrng = np.random.default_rng(seed)
    tmp = tempfile.mkdtemp()
    subprocess.run([find_pdftoppm(), "-r", "150", "-gray", "-png", text_pdf, os.path.join(tmp, "pg")], check=True)
    files = sorted(f for f in os.listdir(tmp) if f.endswith(".png"))
    pages = []
    for f in files:
        img = Image.open(os.path.join(tmp, f)).convert("L")
        angle = rng.uniform(1.0, 3.0) * rng.choice([-1, 1])
        img = img.rotate(angle, resample=Image.BICUBIC, expand=False, fillcolor=255)
        img = img.filter(ImageFilter.GaussianBlur(radius=0.9))
        arr = np.asarray(img, dtype=np.float32)
        arr = arr * 0.82 + 38                      # lower contrast: black ~38, white ~247
        arr = arr + nrng.normal(0, 14, arr.shape)  # gaussian noise
        img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
        jpg = os.path.join(tmp, f.replace(".png", ".jpg"))
        img.save(jpg, "JPEG", quality=68)
        pages.append(Image.open(jpg).convert("L"))
    pages[0].save(out_pdf, "PDF", save_all=True, append_images=pages[1:], resolution=150.0)
    shutil.rmtree(tmp, ignore_errors=True)


# --------------------------------------------------------------------------------------
def main():
    jobs = [
        ("icd1_complete_nonischemic.pdf", M_ICD1, icd1_pages, HEART),
        ("icd2_missing_therapy_and_sdm.pdf", M_ICD2, icd2_pages, M_ICD2["practice"]),
        ("icd3_conflicting_lvef.pdf", M_ICD3, icd3_pages, M_ICD3["practice"]),
        ("icd5_recent_mi.pdf", M_ICD5, icd5_pages, M_ICD5["practice"]),
        ("bar1_complete.pdf", M_BAR1, bar1_pages, BAR),
        ("bar2_missing_prior_treatment.pdf", M_BAR2, bar2_pages, M_BAR2["practice"]),
        ("bar3_bmi_changed.pdf", M_BAR3, bar3_pages, M_BAR3["practice"]),
        ("bar4_negated_comorbidity.pdf", M_BAR4, bar4_pages, M_BAR4["practice"]),
    ]
    for fname, m, builder, practice in jobs:
        pages = builder(m)
        assert len(pages) == m["npages"], (fname, len(pages), m["npages"])
        write_text_pdf(os.path.join(OUT, fname), f"FAX  {practice}  |  Fax {m['fax']}  |  Received 2026-10-04", pages)
        print("wrote", fname, len(pages), "pages")

    # icd4: same clinical content as icd1, different patient, image-only scan
    pages = icd1_pages(M_ICD4)
    assert len(pages) == M_ICD4["npages"]
    tmp_pdf = os.path.join(tempfile.mkdtemp(), "icd4_text.pdf")
    write_text_pdf(tmp_pdf, f"FAX  {M_ICD4['practice']}  |  Fax {M_ICD4['fax']}  |  Received 2026-10-04", pages)
    degrade_to_scan(tmp_pdf, os.path.join(OUT, "icd4_scanned_noisy.pdf"), seed=4404)
    print("wrote icd4_scanned_noisy.pdf (image-only,", len(pages), "pages)")


if __name__ == "__main__":
    main()
