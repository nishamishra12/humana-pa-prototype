"""Interview packets: 6 services, 2 packets each (A = straightforward, B = complex), into interview/<service>/.

Services: bariatric sleeve (43775), total knee (27447), spinal cord stimulator (63685), hypoglossal nerve
stimulation (64582), vertebral augmentation (22514), TMS for depression (90867).

Each packet is a typed fax-style PDF in the same layout the pipeline already reads (PA request page with the
fixed header, then clinical notes, reports and records). The facts follow the CMS policy for the service, so a
policy built from it has something real to check. All patient data is MADE UP. Run from the repo root:

    python scripts/make_interview_packets.py
"""
import os
from datetime import date

from fpdf import FPDF

OUT = "interview"
TODAY = date(2026, 10, 6)
FOOTER = "Made-up data for a software prototype. Not a real patient."


def age_of(dob):
    y, m, d = map(int, dob.split("-"))
    return TODAY.year - y - ((TODAY.month, TODAY.day) < (m, d))


def bmi(lb, inch):
    return round(lb * 703 / (inch * inch), 1)


class FaxPDF(FPDF):
    fax_line = ""

    def header(self):
        self.set_font("Helvetica", "", 7.5)
        self.set_text_color(110, 110, 110)
        self.cell(0, 4, f"{self.fax_line}   |   Page {self.page_no()} of {{nb}}", new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(0, 0, 0)
        self.ln(2)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(110, 110, 110)
        self.cell(0, 5, FOOTER, align="C")
        self.set_text_color(0, 0, 0)


def one_line(pdf, text, size=10.5, style=""):
    while size > 6:
        pdf.set_font("Helvetica", style, size)
        if pdf.get_string_width(text) <= pdf.w - pdf.l_margin - pdf.r_margin - 1:
            break
        size -= 0.25
    pdf.cell(0, 6, text, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10.5)


def write_pdf(path, fax_line, pages):
    """pages = [(title, [lines])]. Markup: '' blank, '## ' heading, '!! ' single line, '~ ' monospaced row, else a paragraph."""
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


def member(name, dob, mid, sex, addr, phone, doc, specialty, npi, practice, ph2, fax, coord, admit, npages):
    return dict(name=name, dob=dob, mid=mid, sex=sex, addr=addr, phone=phone, surgeon=doc, specialty=specialty, npi=npi,
                practice=practice, ph2=ph2, fax=fax, coord=coord, admit=admit, npages=npages)


def pa_page(m, service, cpt, icd10, level, place, setting_title, extra=None):
    """Page 1, in the fixed header format the pipeline reads."""
    return (f"Prior Authorization Request - {setting_title}", [
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
        f"!! Requested service: {service}",
        f"!! CPT {cpt}   ICD-10: {icd10}",
        f"Planned admit date: {m['admit']}",
        f"Level of care requested: {level}",
        f"Place of service: {place}",
        "",
        "## Submission Contact",
        f"Submitted through the provider portal by {m['coord']}, Authorization Coordinator.",
        f"Callback: {m['ph2']}. Supporting clinical documentation attached ({m['npages']} pages including this request).",
    ] + ([""] + extra if extra else []))


# ======================================================================================
# 01  BARIATRIC SURGERY: laparoscopic sleeve gastrectomy, CPT 43775   (NCD 100.1, LCD L35022)
# ======================================================================================
BARI = "Riverbend Bariatric Surgery Center"
M_B1 = member("Linda Carter", "1980-04-12", "MBR-41001", "F", "214 Maple Court, Dayton, OH 45420", "(937) 555-0101", "Dr. Alan Reyes, MD",
              "Bariatric Surgery", "1457382096", BARI, "(937) 555-0120", "(937) 555-0121", "Sheila Brandt", "2026-11-12", 6)
M_B2 = member("Robert Hayes", "1971-09-30", "MBR-41002", "M", "88 Cedar Lane, Springfield, OH 45504", "(937) 555-0133", "Dr. Paul Whitman, MD",
              "General and Bariatric Surgery", "1639420785", "Springfield Weight Loss Surgery Group", "(937) 555-0150", "(937) 555-0151", "Carlos Menendez",
              "2026-11-19", 5)
M_B3 = member("Denise Walker", "1978-02-23", "MBR-41003", "F", "5 Fairview Terrace, Dayton, OH 45431", "(937) 555-0166", "Dr. Alan Reyes, MD",
              "Bariatric Surgery", "1457382096", BARI, "(937) 555-0120", "(937) 555-0121", "Sheila Brandt", "2026-11-17", 6)
SLEEVE = "Elective inpatient admission, laparoscopic sleeve gastrectomy (stand-alone)"
BYPASS = "Elective inpatient admission, laparoscopic Roux-en-Y gastric bypass"


def bari_a(m):
    return [
        pa_page(m, SLEEVE, "43775", "E66.01 (Morbid obesity due to excess calories); Z68.41 (BMI 40.0-44.9); E11.9; I10; G47.33",
                "INPATIENT", "Hospital, inpatient (acute care).", "Inpatient Admission",
                ["Expected length of stay: 1 midnight.", "Procedure is planned as a stand-alone laparoscopic sleeve gastrectomy."]),
        ("Surgical Consultation - Bariatric Surgery", [
            f"Date of consultation: 2026-09-15.   Patient: {m['name']}, age {age_of(m['dob'])}, female.",
            "## History",
            "Ms. Carter is referred by her primary care physician for surgical treatment of severe obesity. Weight has been above 230 lb for 12 years. "
            "She has type 2 diabetes mellitus (diagnosed 2021, on metformin 1000 mg twice daily), hypertension on lisinopril 20 mg daily, and obstructive "
            "sleep apnea treated with CPAP. She also reports knee pain with walking.",
            "## Measurements",
            f"Height 64 in. Weight 245 lb. BMI {bmi(245, 64)} kg/m2 (measured in clinic 2026-09-15). Highest recorded BMI 44.0.",
            "## Prior medical treatment for obesity",
            "Completed a 6-month physician-supervised weight management program (Riverbend Medical Weight Management) from 2026-02-10 to 2026-08-12 with "
            "monthly visits, registered dietitian counseling and a documented calorie-controlled diet. Net weight change over the program: 252 lb to 247 lb. "
            "Patient was unable to maintain a healthy weight despite adequate participation. Earlier attempts include a commercial program in 2019 with regain.",
            "## Assessment",
            "Severe obesity with obesity-related comorbidities (type 2 diabetes, hypertension, OSA). No history of prior bariatric surgery. Non-smoker. "
            "No history of eating disorder. No known cardiac disease. No hepatic disease. No autoimmune disease.",
            "## Plan",
            "Laparoscopic sleeve gastrectomy as a stand-alone procedure. No staged operation is planned. Patient has received education on the operation, "
            "risks, the required lifestyle changes and lifelong follow-up, and has demonstrated understanding and willingness to carry out these changes. "
            "I certify that the patient has made a diligent effort to achieve a healthy body weight, as described in this note and in the attached program records.",
            "Dr. Alan Reyes, MD, Bariatric Surgery. Board certified, American Board of Surgery. Fellowship trained in minimally invasive and bariatric surgery. "
            "Completed an accredited surgical residency; maintains continuing medical education.",
        ]),
        ("Medical Weight Management Program - Visit Summary", [
            "Riverbend Medical Weight Management. Physician: Dr. Nina Patel, MD. Registered dietitian: Rachel Owens, RD.",
            "~ Date        Weight   Visit",
            "~ 2026-02-10  252 lb   Intake, 1500 kcal plan, RD counseling",
            "~ 2026-03-10  250 lb   RD follow-up, food log reviewed",
            "~ 2026-04-14  249 lb   MD visit, activity plan added",
            "~ 2026-05-12  251 lb   RD follow-up",
            "~ 2026-06-16  248 lb   MD visit",
            "~ 2026-07-14  249 lb   RD follow-up",
            "~ 2026-08-12  247 lb   Final visit, program completed",
            "",
            "Summary: Patient attended 7 of 7 scheduled visits and kept a food log. Weight loss was not sustained beyond 5 lb. "
            "Structured dietary program overseen by a physician and a registered dietitian. Patient failed to maintain a healthy weight despite adequate participation.",
        ]),
        ("Psychological Evaluation - Pre-bariatric", [
            "Date: 2026-08-28.   Evaluator: Dr. Susan Lindgren, PhD, Clinical Psychologist.",
            "Patient has no history of psychiatric disorder and is not taking psychotropic medication. Screening for depression (PHQ-9 score 4) and "
            "anxiety was negative. No evidence of binge eating disorder or bulimia. No alcohol or substance use disorder. No current tobacco use.",
            "Patient understands the operation, the dietary changes and the need for lifelong follow-up, and is judged capable and willing to carry out "
            "these changes. Cleared from a psychological standpoint to proceed with bariatric surgery.",
        ]),
        ("Primary Care Note - Comorbidity Documentation", [
            "Date: 2026-09-02.   Physician: Dr. Marcus Hill, MD.",
            "Type 2 diabetes mellitus: hemoglobin A1c 8.2% on metformin 1000 mg twice daily. Hypertension: blood pressure 142/88 on lisinopril 20 mg. "
            "Obstructive sleep apnea: AHI 28 on 2025 sleep study, uses CPAP nightly. These conditions are not easily controlled with non-invasive means "
            "and pose considerable risk to function and survival if untreated.",
            "Cardiac risk assessment: EKG normal sinus rhythm, no cardiac history. Pulmonary: no COPD. Cleared for general anesthesia, ASA class 3.",
        ]),
        ("Postoperative Care Plan", [
            "Postoperative care will be provided by the operating surgeon immediately after surgery and throughout the global period.",
            "Follow-up visits with the bariatric surgery team are scheduled at 2 weeks, 3 months, 6 months and 12 months, which is at least three visits in "
            "the first year. Lifetime follow-up for dietary issues, vitamin and mineral supplementation, exercise and lifestyle changes will be supported by "
            "counseling and a monthly support group supervised by Dr. Reyes.",
        ]),
    ]


def bari_b(m):
    return [
        pa_page(m, SLEEVE.replace(" (stand-alone)", ""), "43775", "E66.01; R73.03; I10; F33.1",
                "INPATIENT", "Hospital, inpatient (acute care).", "Inpatient Admission",
                ["Expected length of stay: not stated."]),
        ("Surgical Consultation Note", [
            "Date: 2026-09-08.   Patient: Robert Hayes, age 54, male.",
            "## History",
            "Mr. Hayes requests weight loss surgery. He has gained about 60 lb over 10 years. He has tried many diets over the years, including a commercial "
            "program for a few weeks and a ketogenic diet for about two months, with regain each time. No dietitian or physician supervised these attempts and "
            "the patient has no records of them.",
            "Comorbidities: prediabetes (A1c 6.0% last spring), hypertension that is currently well controlled on one medication, and 'borderline' sleep apnea "
            "by symptoms, no sleep study on file. Mild knee pain.",
            "Medications: amlodipine 5 mg daily, sertraline 100 mg daily.",
            "## Measurements",
            f"Height 69 in. Weight 249 lb. BMI {bmi(249, 69)} kg/m2 (clinic scale).",
            "## Plan",
            "Laparoscopic sleeve gastrectomy. If weight regain occurs, the sleeve may be converted later to a gastric bypass or a duodenal switch. The sleeve "
            "is the first stage of that plan.",
            "Dr. Paul Whitman, MD, General and Bariatric Surgery.",
        ]),
        ("Primary Care Visit Note", [
            "Date: 2026-09-29.   Physician: Dr. Janet Morris, MD.",
            f"Visit for blood pressure follow-up. Weight today 233 lb, height 69 in, BMI {bmi(233, 69)} kg/m2. Patient reports he has been 'cutting back' since "
            "seeing the surgeon.",
            "Blood pressure 128/80 on amlodipine 5 mg. Hemoglobin A1c 6.0%. Fasting glucose 108. No diagnosis of diabetes.",
            "Mental health: history of major depressive disorder, currently stable on sertraline 100 mg. He was seen by a psychiatrist 4 years ago. "
            "No recent mental health evaluation. Referral for a pre-surgical psychological evaluation was placed on 2026-09-29, appointment not yet scheduled.",
            "Tobacco: stopped smoking 5 months ago after 20 years. Alcohol: 2 to 3 drinks per week.",
        ]),
        ("Patient Questionnaire - Weight History", [
            "Completed by the patient on 2026-09-08.",
            "Have you ever been in a medically supervised weight loss program? No.",
            "Have you ever had weight loss surgery? No.",
            "Do you have any psychiatric history or take medication for mood? Yes, depression, sertraline.",
            "Do you have diabetes? No, my doctor says I am pre-diabetic.",
            "Do you have trouble breathing or sleeping? I snore and wake up tired.",
        ]),
        ("Insurance Fax Cover Sheet", [
            "Please review and respond by fax. Surgery tentatively scheduled for 2026-11-19. Thank you.",
            "Attached: surgical consultation note, primary care visit note, patient questionnaire. Surgeon credentials and a postoperative care plan are "
            "available on request.",
        ]),
    ]


def bari_c(m):
    """A nationally covered procedure (laparoscopic Roux-en-Y gastric bypass) with every requirement documented."""
    return [
        pa_page(m, BYPASS, "43644", "E66.01 (Morbid obesity due to excess calories); Z68.42 (BMI 45.0-49.9); E11.65; I10; G47.33",
                "INPATIENT", "Hospital, inpatient (acute care).", "Inpatient Admission",
                ["Expected length of stay: 2 midnights."]),
        ("Surgical Consultation - Bariatric Surgery", [
            f"Date of consultation: 2026-09-21.   Patient: {m['name']}, age {age_of(m['dob'])}, female.",
            "## History",
            "Ms. Walker is referred by her primary care physician for surgical treatment of severe obesity. Weight has been above 250 lb for 14 years. "
            "She has type 2 diabetes mellitus (diagnosed 2019, on metformin 1000 mg twice daily and semaglutide), hypertension on losartan 100 mg daily, and "
            "obstructive sleep apnea treated with CPAP. She also has gastroesophageal reflux and knee pain.",
            "## Measurements",
            f"Height 65 in. Weight 276 lb. BMI {bmi(276, 65)} kg/m2 (measured in clinic 2026-09-21).",
            "## Prior medical treatment for obesity",
            "Completed a 7-month physician-supervised weight management program (Riverbend Medical Weight Management) from 2026-01-13 to 2026-08-18 with "
            "monthly visits, registered dietitian counseling and a documented calorie-controlled diet. Net weight change over the program: 281 lb to 276 lb. "
            "Patient was unable to maintain a healthy weight despite adequate participation. Earlier attempts include a commercial program in 2018 and a "
            "medication trial with regain.",
            "## Assessment",
            "Severe obesity with obesity-related comorbidities (type 2 diabetes, hypertension, OSA, reflux). No history of prior bariatric surgery. Non-smoker. "
            "No history of eating disorder. No known cardiac disease. No hepatic disease. No autoimmune disease.",
            "## Plan",
            "Laparoscopic Roux-en-Y gastric bypass. Gastric bypass is chosen over a sleeve because of her reflux and diabetes. Patient has received education "
            "on the operation, risks, the required lifestyle changes and lifelong follow-up, and has demonstrated understanding and willingness to carry out "
            "these changes. I certify that the patient has made a diligent effort to achieve a healthy body weight, as described in this note and in the "
            "attached program records.",
            "Dr. Alan Reyes, MD, Bariatric Surgery. Board certified, American Board of Surgery. Fellowship trained in minimally invasive and bariatric surgery. "
            "Completed an accredited surgical residency; maintains continuing medical education.",
        ]),
        ("Medical Weight Management Program - Visit Summary", [
            "Riverbend Medical Weight Management. Physician: Dr. Nina Patel, MD. Registered dietitian: Rachel Owens, RD.",
            "~ Date        Weight   Visit",
            "~ 2026-01-13  281 lb   Intake, 1500 kcal plan, RD counseling",
            "~ 2026-02-17  279 lb   RD follow-up, food log reviewed",
            "~ 2026-03-17  278 lb   MD visit, activity plan added",
            "~ 2026-04-21  280 lb   RD follow-up",
            "~ 2026-05-19  277 lb   MD visit",
            "~ 2026-06-23  278 lb   RD follow-up",
            "~ 2026-07-21  277 lb   RD follow-up",
            "~ 2026-08-18  276 lb   Final visit, program completed",
            "",
            "Summary: Patient attended 8 of 8 scheduled visits and kept a food log. Weight loss was not sustained beyond 5 lb. "
            "Structured dietary program overseen by a physician and a registered dietitian. Patient failed to maintain a healthy weight despite adequate participation.",
        ]),
        ("Psychological Evaluation - Pre-bariatric", [
            "Date: 2026-09-02.   Evaluator: Dr. Susan Lindgren, PhD, Clinical Psychologist.",
            "Patient has no history of psychiatric disorder and is not taking psychotropic medication. Screening for depression (PHQ-9 score 3) and "
            "anxiety was negative. No evidence of binge eating disorder or bulimia. No alcohol or substance use disorder. No current tobacco use.",
            "Patient understands the operation, the dietary changes and the need for lifelong follow-up, and is judged capable and willing to carry out "
            "these changes. Cleared from a psychological standpoint to proceed with bariatric surgery.",
        ]),
        ("Primary Care Note - Comorbidity Documentation", [
            "Date: 2026-09-09.   Physician: Dr. Marcus Hill, MD.",
            "Type 2 diabetes mellitus: hemoglobin A1c 8.6% on metformin and semaglutide. Hypertension: blood pressure 146/90 on losartan 100 mg. "
            "Obstructive sleep apnea: AHI 34 on 2025 sleep study, uses CPAP nightly. These conditions are not easily controlled with non-invasive means "
            "and pose considerable risk to function and survival if untreated.",
            "Cardiac risk assessment: EKG normal sinus rhythm, no cardiac history. Pulmonary: no COPD. Cleared for general anesthesia, ASA class 3.",
        ]),
        ("Postoperative Care Plan", [
            "Postoperative care will be provided by the operating surgeon immediately after surgery and throughout the global period.",
            "Follow-up visits with the bariatric surgery team are scheduled at 2 weeks, 3 months, 6 months and 12 months, which is at least three visits in "
            "the first year. Lifetime follow-up for dietary issues, vitamin and mineral supplementation, exercise and lifestyle changes will be supported by "
            "counseling and a monthly support group supervised by Dr. Reyes.",
        ]),
    ]


# ======================================================================================
# 02  TOTAL KNEE REPLACEMENT, CPT 27447   (LCD L36575)
# ======================================================================================
ORTHO = "Ridgeline Orthopedics and Sports Medicine"
M_K1 = member("Dorothy Evans", "1956-01-20", "MBR-42001", "F", "1620 Willow Creek Dr, Columbus, OH 43215", "(614) 555-0102", "Dr. James Whitaker, MD",
              "Orthopedic Surgery", "1562048317", ORTHO, "(614) 555-0130", "(614) 555-0131", "Imani Whitfield", "2026-11-16", 5)
M_K2 = member("Harold Jennings", "1953-07-08", "MBR-42002", "M", "47 Pine Hollow Rd, Toledo, OH 43614", "(419) 555-0144", "Dr. Michael Banks, MD",
              "Orthopedic Surgery", "1730294851", "Maumee Joint and Spine Clinic", "(419) 555-0170", "(419) 555-0171", "Reyna Castellanos", "2026-11-23", 5)


def knee_a(m):
    return [
        pa_page(m, "Elective inpatient admission, total knee arthroplasty, right knee", "27447", "M17.11 (Unilateral primary osteoarthritis, right knee)",
                "INPATIENT", "Hospital, inpatient (acute care).", "Inpatient Admission",
                ["Expected length of stay: 2 midnights."]),
        ("Orthopedic Consultation", [
            "Date: 2026-09-22.   Patient: Dorothy Evans, age 70, female.",
            "## History",
            "Progressive right knee pain for over 3 years, now severe. Pain 8/10 with walking and on stairs, 5/10 at rest, and it wakes her at night. She "
            "can walk about one block with a cane and cannot climb stairs without a rail. She has difficulty getting up from a chair, putting on shoes and "
            "getting in and out of a car. These are major limits to her activities of daily living.",
            "## Examination",
            f"Height 63 in, weight 173 lb, BMI {bmi(173, 63)} kg/m2. Right knee: small effusion, medial joint line tenderness, crepitus, flexion 105 degrees, "
            "flexion contracture 8 degrees, varus alignment. Stable ligaments. Neurovascularly intact. No signs of infection.",
            "## Assessment and plan",
            "Advanced primary osteoarthritis of the right knee with pain and functional disability despite conservative therapy. Recommend right total "
            "knee arthroplasty. Risks, benefits and alternatives discussed. Patient wishes to proceed.",
        ]),
        ("Radiology Report - Right Knee, Weight-Bearing", [
            "Date: 2026-09-18.   Study: Right knee, weight-bearing AP, lateral and sunrise views. Radiologist: Dr. Hannah Lee, MD.",
            "Findings: Severe medial compartment joint space narrowing with bone-on-bone contact. Marginal osteophytes in all three compartments. Subchondral "
            "sclerosis and subchondral cysts of the medial tibial plateau. Varus deformity of 9 degrees. No fracture, no lytic lesion, no loosening hardware.",
            "Impression: Advanced tricompartmental osteoarthritis of the right knee, Kellgren-Lawrence grade 4.",
        ]),
        ("Conservative Treatment Record", [
            "## Medications",
            "Naproxen 500 mg twice daily from 2026-02-01 to 2026-07-30 (6 months) with partial relief that faded. Acetaminophen 1 g three times daily. "
            "Topical diclofenac gel. Pain remains 8/10 with activity.",
            "## Injections",
            "Corticosteroid injection, right knee, 2026-03-05: relief about 3 weeks. Second injection 2026-05-14: relief under 2 weeks.",
            "## Physical therapy",
            "Supervised physical therapy at Columbus Rehab, 12 visits from 2026-04-01 to 2026-05-28: flexibility and strengthening exercises, gait training. "
            "Activities of daily living remain diminished despite completing the plan of care. Discharged to a home exercise program.",
            "## Assistive device",
            "Uses a cane in the left hand since 2026-03.",
        ]),
        ("Pre-operative Medical Evaluation", [
            "Date: 2026-09-25.   Physician: Dr. Frank Delaney, MD, Internal Medicine.",
            "Medical history: hypertension, well controlled. Hemoglobin A1c 6.2%, no diabetes diagnosis. Non-smoker. No history of knee infection. EKG normal.",
            "Labs: hemoglobin 13.4, creatinine 0.9, CRP 3 mg/L. Medically optimized and cleared for surgery, ASA class 2.",
        ]),
    ]


def knee_b(m):
    return [
        pa_page(m, "Elective inpatient admission, total knee arthroplasty, left knee", "27447", "M17.12 (Unilateral primary osteoarthritis, left knee); E11.65",
                "INPATIENT", "Hospital, inpatient (acute care).", "Inpatient Admission",
                ["Expected length of stay: 3 midnights."]),
        ("Orthopedic Office Note", [
            "Date: 2026-09-30.   Patient: Harold Jennings, age 73, male.",
            "## History",
            "Knee pain for about 2 years, now worse. Pain 5 to 6 out of 10 with activity. The right knee gives out occasionally and he has had one near-fall. "
            "He still walks around the house and shops with a cart. He would like a knee replacement 'so I can play golf again.'",
            "Medications: metformin, lisinopril, warfarin for atrial fibrillation. Ibuprofen was tried for about 3 weeks last year and stopped because of "
            "stomach upset. Physical therapy was recommended, patient declined because of cost.",
            "## Examination",
            f"Height 68 in, weight 273 lb, BMI {bmi(273, 68)} kg/m2. Right knee: mild effusion, medial joint line tenderness, flexion 100 degrees.",
            "## Imaging",
            "Weight-bearing films were ordered. Report to follow. An outside MRI report is attached.",
            "## Plan",
            "Schedule total knee replacement. Corticosteroid injection given today, response to be assessed in 2 weeks.",
        ]),
        ("Outside MRI Report - Knee", [
            "Date: 2026-07-12.   Facility: Northwest Imaging.   Study: MRI of the knee without contrast. Laterality in the report header: not stated.",
            "Findings: Tricompartmental chondromalacia with grade 2 to 3 changes in the medial compartment. Small joint effusion. Degenerative tear of the "
            "posterior horn of the medial meniscus. Mild marginal osteophytes. No avascular necrosis.",
            "Impression: Degenerative changes of the knee with chondromalacia and meniscal tear. Clinical correlation recommended.",
        ]),
        ("Primary Care Summary", [
            "Date: 2026-09-10.   Physician: Dr. Lisa Park, MD.",
            "Type 2 diabetes, hemoglobin A1c 9.3% (uncontrolled), on metformin. Atrial fibrillation on warfarin, INR 2.6. Hypertension.",
            "Knee pain managed with acetaminophen as needed. Patient was advised to lose weight and to attend physical therapy.",
        ]),
        ("Prior Authorization Fax Cover", [
            "Please authorize total knee arthroplasty. Surgery date tentatively 2026-11-23. Weight-bearing X-ray report will be sent when received. "
            "Physical therapy records not available.",
        ]),
    ]


# ======================================================================================
# 03  SPINAL CORD STIMULATOR, permanent implant CPT 63685   (LCD L36204)
# ======================================================================================
PAIN = "Great Lakes Pain and Neuromodulation Institute"
M_S1 = member("Karen Mitchell", "1969-11-02", "MBR-43001", "F", "309 Linden Ave, Cleveland, OH 44106", "(216) 555-0103", "Dr. Priya Raman, MD",
              "Pain Medicine", "1285047396", PAIN, "(216) 555-0140", "(216) 555-0141", "Tomas Ibarra", "2026-11-10", 6)
M_S2 = member("Steven Lopez", "1962-03-25", "MBR-43002", "M", "75 Harbor St, Lorain, OH 44052", "(440) 555-0177", "Dr. Greg Hanson, DO",
              "Anesthesiology, Interventional Pain", "1720385946", "Erie Shores Interventional Pain", "(440) 555-0190", "(440) 555-0191", "Wanda Oyelaran",
              "2026-11-12", 5)
SCS = "Permanent spinal cord stimulator pulse generator implantation (after successful trial)"


def scs_a(m):
    return [
        pa_page(m, SCS, "63685", "M96.1 (Postlaminectomy syndrome, not elsewhere classified); G89.4 (Chronic pain syndrome)",
                "OUTPATIENT", "Ambulatory surgery center.", "Outpatient Procedure"),
        ("Pain Medicine Evaluation", [
            "Date: 2026-07-14.   Patient: Karen Mitchell, age 56, female.",
            "## History",
            "Chronic low back and left leg pain for 3 years since an L4-L5 laminectomy and fusion in 2023 (failed back surgery syndrome). Pain is neuropathic "
            "in character, burning and shooting into the left leg. Average pain 8/10 on a numeric rating scale. Imaging shows solid fusion, no recurrent "
            "stenosis and no surgical target. Spine surgeon agrees there is no further surgical option.",
            "## Conservative treatment tried",
            "Gabapentin 600 mg three times daily, duloxetine 60 mg daily and tramadol 50 mg twice daily with inadequate relief. Physical therapy for 12 "
            "weeks (2025-10 to 2026-01). Three lumbar epidural steroid injections (2025-06, 2025-09, 2026-02) with relief under 3 weeks each. "
            "Cognitive behavioral pain program completed 2026-03.",
            "## Plan",
            "Screening for spinal cord stimulation. Psychological evaluation ordered. Patient education visit scheduled.",
        ]),
        ("Psychological Evaluation - Spinal Cord Stimulator Screening", [
            "Date: 2026-07-28.   Evaluator: Dr. Evelyn Shaw, PsyD.",
            "PHQ-9 score 8 (mild). GAD-7 score 6. No active substance abuse: urine drug screen consistent with prescribed medications only, no history of "
            "substance use disorder. No active psychosis. Realistic expectations about the treatment. Patient is a good candidate from a psychological "
            "standpoint. Cleared to proceed.",
        ]),
        ("Patient Education and Consent Record", [
            "Date: 2026-08-04.   Seen by: Dr. Priya Raman and nurse educator Mary Hobbs, RN.",
            "An extensive discussion of risks and benefits was held, including infection, lead migration, no relief and need for revision. Written "
            "disclosure was provided. Patient signed the consent for a trial and, if the trial is successful, for permanent implantation. The same "
            "physician will perform the trial and the permanent implant.",
        ]),
        ("Spinal Cord Stimulator Trial Report", [
            "Procedure: Percutaneous trial lead placement (CPT 63650), 2026-09-08. Duration of trial: 10 days, lead removed 2026-09-18.",
            "~ Measure                   Before trial   End of trial",
            "~ Pain, left leg (NRS)           8/10          3/10",
            "~ Pain, low back (NRS)           7/10          3/10",
            "~ Walking tolerance             10 min         45 min",
            "~ Tramadol use                  100 mg/day     50 mg/day",
            "",
            "Result: 63% reduction in target pain, 50% reduction in analgesic medication, and clear functional improvement (walking, sleeping through the "
            "night). Patient wishes to proceed to permanent implantation. Lead position confirmed by fluoroscopy on the trial day: two leads, "
            "T8-T9, adequate coverage of the painful area.",
        ]),
        ("Operative Plan", [
            "Permanent implant of two percutaneous leads and a pulse generator at the ambulatory surgery center, 2026-11-10. Surgeon: Dr. Priya Raman, MD. "
            "Board certified in Pain Medicine, American Board of Anesthesiology. Hospital privileges at Lakeshore Medical Center.",
        ]),
    ]


def scs_b(m):
    return [
        pa_page(m, SCS, "63685", "M54.16 (Radiculopathy, lumbar region); G89.29 (Other chronic pain)",
                "OUTPATIENT", "Ambulatory surgery center.", "Outpatient Procedure"),
        ("Pain Clinic Progress Note", [
            "Date: 2026-09-30.   Patient: Steven Lopez, age 64, male.",
            "## History",
            "Chronic low back pain with right leg radiation for 6 years, no prior spine surgery. MRI shows multilevel degenerative disease and a right L5-S1 "
            "foraminal narrowing. Two epidural injections in 2024 with temporary help.",
            "Medications: oxycodone 15 mg three times daily, gabapentin 300 mg twice daily. Physical therapy: home exercise program only. No formal PT.",
            "Urine drug screen 2026-08-19: positive for oxycodone and also positive for a benzodiazepine that is not prescribed. Patient says a friend gave "
            "him one tablet. Counseled. A repeat screen has not been done.",
            "## Spinal cord stimulator trial",
            "A 7-day percutaneous trial was done 2026-09-16. Patient reports he is 'a little better.' Pain went from 7/10 to about 4.5/10 on the diary. "
            "Oxycodone dose unchanged. He says he can do more around the house.",
            "## Plan",
            "Proceed with permanent SCS implant. Psychological evaluation was ordered 2026-09-16, not yet completed.",
        ]),
        ("Trial Diary Summary", [
            "Patient-reported pain scores during the 7-day trial (0 to 10):",
            "~ Day 1: 6   Day 2: 5   Day 3: 5   Day 4: 4   Day 5: 5   Day 6: 4   Day 7: 4",
            "Baseline average before the trial: 7. Average during the trial: 4.7. Percent reduction: about 33%.",
            "Medication log: oxycodone unchanged at 45 mg per day. No reduction in pain medication.",
            "Function: no objective measure recorded.",
        ]),
        ("Consent Form", [
            "Patient signed consent for a spinal cord stimulator trial and permanent implant on 2026-09-02. Risks and benefits listed on the standard form.",
            "No separate educational visit recorded.",
        ]),
        ("Fax Cover", [
            "Please authorize permanent SCS implant. Procedure to be done at our ASC on 2026-11-12. Psychological evaluation results will follow.",
        ]),
    ]


# ======================================================================================
# 04  HYPOGLOSSAL NERVE STIMULATION, CPT 64582   (LCD L38528)
# ======================================================================================
ENT = "Lakeshore Ear, Nose and Throat and Sleep Surgery"
M_H1 = member("James Anderson", "1974-06-15", "MBR-44001", "M", "56 Beacon Hill Rd, Akron, OH 44304", "(330) 555-0104", "Dr. Elena Park, MD",
              "Otolaryngology, Sleep Surgery", "1396057248", ENT, "(330) 555-0150", "(330) 555-0151", "Pamela Duarte", "2026-11-10", 6)
M_H2 = member("Patricia Nguyen", "1966-02-14", "MBR-44002", "F", "902 Orchard Way, Canton, OH 44718", "(330) 555-0188", "Dr. Brian Fox, MD",
              "Otolaryngology", "1480256937", "Stark County ENT Associates", "(330) 555-0210", "(330) 555-0211", "Dana Kessler", "2026-11-17", 5)
HGNS = "Hypoglossal nerve stimulator implantation for obstructive sleep apnea"


def hgns_a(m):
    return [
        pa_page(m, HGNS, "64582", "G47.33 (Obstructive sleep apnea)", "OUTPATIENT", "Hospital outpatient department.", "Outpatient Procedure"),
        ("ENT Sleep Surgery Consultation", [
            "Date: 2026-08-26.   Patient: James Anderson, age 52, male.",
            "## History",
            "Moderate to severe obstructive sleep apnea diagnosed in 2026. Loud snoring, witnessed apneas and daytime sleepiness (Epworth score 14). "
            "Could not tolerate CPAP, see sleep medicine note.",
            "## Examination",
            f"Height 70 in, weight 201 lb, BMI {bmi(201, 70)} kg/m2. Tonsils grade 1. Friedman tongue position 3. No neuromuscular disease. No "
            "implanted electronic device (no pacemaker, no defibrillator). No history of heart failure, myocardial infarction or arrhythmia. Blood "
            "pressure controlled. No pulmonary disease.",
            "## Plan",
            "Candidate for hypoglossal nerve stimulation. Drug-induced sleep endoscopy done, see report.",
        ]),
        ("Polysomnography Report", [
            "Date of study: 2026-03-10 (attended in-lab polysomnogram). Interpreting physician: Dr. Aaron Cole, MD, Sleep Medicine.",
            "~ Apnea-hypopnea index (AHI): 41 events/hour",
            "~ Obstructive apneas: 92% of events   Central apneas: 3%   Mixed apneas: 5%",
            "~ Lowest oxygen saturation: 78%   Time below 90%: 14%",
            "Impression: Severe obstructive sleep apnea. Central and mixed events are 8% of the total AHI.",
        ]),
        ("Sleep Medicine Note - CPAP Failure and Shared Decision Making", [
            "Date: 2026-06-18.   Physician: Dr. Aaron Cole, MD, Sleep Medicine.",
            "CPAP trial from 2026-03-25 to 2026-06-10 with three mask types and pressure adjustments. Download data: average use 2.1 hours per night on 3 "
            "nights per week. Residual AHI on CPAP 21 events/hour. Patient is intolerant of CPAP, with less than 4 hours per night on fewer than 5 nights "
            "per week despite consultation with a sleep expert, mask refitting and desensitization.",
            "Shared decision making was held on 2026-06-18 and documented: alternatives (oral appliance, surgery, hypoglossal nerve stimulation) discussed. "
            "Patient chooses hypoglossal nerve stimulation.",
        ]),
        ("Drug-Induced Sleep Endoscopy Report", [
            "Date: 2026-08-12.   Surgeon: Dr. Elena Park, MD.",
            "Findings: Retropalatal collapse is anterior-posterior, partial. No complete concentric collapse at the soft palate level. Tongue base collapse "
            "moderate. Lateral wall collapse mild. No other anatomical findings that would compromise device performance.",
            "Impression: Suitable airway pattern for hypoglossal nerve stimulation.",
        ]),
        ("Pre-operative Medical Summary", [
            "Date: 2026-09-20.   Physician: Dr. Laura Simmons, MD, Internal Medicine.",
            "No pulmonary arterial hypertension (echo 2026-09-02: normal pulmonary pressures, ejection fraction 60%). No valvular disease. No severe "
            "psychiatric illness. No MRI-incompatible devices. No contraindication to general anesthesia.",
            "Device: FDA-approved hypoglossal nerve stimulation system.",
        ]),
    ]


def hgns_b(m):
    return [
        pa_page(m, HGNS, "64582", "G47.33 (Obstructive sleep apnea); I10", "OUTPATIENT", "Hospital outpatient department.", "Outpatient Procedure"),
        ("ENT Office Note", [
            "Date: 2026-09-24.   Patient: Patricia Nguyen, age 60, female.",
            "Severe snoring and sleep apnea. She has tried CPAP at home and 'does not like the mask', stopped after a few weeks, no download data. No "
            "sleep medicine consultation. She would prefer an implant.",
            f"Height 63 in, weight 195 lb, BMI {bmi(195, 63)} kg/m2. Tonsils grade 3. Hypertension on two medications, blood pressure 138/86 today.",
            "Plan: drug-induced sleep endoscopy to be scheduled. Request authorization for the hypoglossal nerve stimulator so the surgery can be booked.",
        ]),
        ("Polysomnography Report", [
            "Date of study: 2024-04-02 (attended in-lab polysomnogram).",
            "~ Apnea-hypopnea index (AHI): 52 events/hour",
            "~ Obstructive events: 79%   Central events: 14%   Mixed events: 7%",
            "~ Lowest oxygen saturation: 81%",
            "Impression: Severe obstructive sleep apnea with a component of central events.",
        ]),
        ("Cardiology Note", [
            "Date: 2026-06-15.   Physician: Dr. Omar Haddad, MD.",
            "Hypertension, on lisinopril and amlodipine. Echocardiogram: ejection fraction 50%, mild pulmonary hypertension, mild mitral regurgitation. "
            "No heart failure symptoms. No arrhythmia. Continue current treatment.",
        ]),
        ("Fax Cover", [
            "Please authorize the hypoglossal nerve stimulator, surgery planned for 2026-11-17. Sleep endoscopy report will be sent after the procedure.",
        ]),
    ]


# ======================================================================================
# 05  VERTEBRAL AUGMENTATION, CPT 22514   (LCD L38213)
# ======================================================================================
IR = "Westfield Spine Intervention Center"
M_V1 = member("Margaret Collins", "1947-05-19", "MBR-45001", "F", "118 Birch Street, Dayton, OH 45409", "(937) 555-0105", "Dr. Kevin Shah, MD",
              "Interventional Radiology", "1175038264", IR, "(937) 555-0140", "(937) 555-0141", "Sheila Brandt", "2026-10-22", 5)
M_V2 = member("Walter Stevens", "1949-12-03", "MBR-45002", "M", "27 Quarry Road, Youngstown, OH 44505", "(330) 555-0166", "Dr. Alan Rivera, MD",
              "Pain Medicine", "1840295736", "Mahoning Spine and Pain Clinic", "(330) 555-0205", "(330) 555-0206", "Lucia Santangelo", "2026-10-28", 5)
PVA = "Percutaneous vertebral augmentation (kyphoplasty), lumbar, one level"


def pva_a(m):
    return [
        pa_page(m, PVA, "22514", "M80.08XA (Age-related osteoporosis with current pathological fracture, vertebra, initial encounter)",
                "OUTPATIENT", "Hospital outpatient department.", "Outpatient Procedure"),
        ("Interventional Radiology Consultation", [
            "Date: 2026-09-28.   Patient: Margaret Collins, age 79, female.",
            "## History",
            "Sudden onset of severe low back pain on 2026-08-30 while lifting a laundry basket, 4 weeks and 5 days ago. Pain is worse with standing and "
            "turning in bed, 7/10 at rest on most days and 9/10 with movement. She is not hospitalized. The pain has been getting worse over the last 2 weeks "
            "despite treatment.",
            "## Non-surgical management so far (4 weeks)",
            "Acetaminophen and tramadol 50 mg every 6 hours, a thoracolumbar brace worn since 2026-09-02, and 8 physical therapy visits for gentle mobility. "
            "Pain scale (NRS) is still 7 at rest and 9 with activity. Function: bed-to-chair transfers need help; Roland-Morris score 19 of 24.",
            "## Examination",
            "Point tenderness over L1. Neurologic exam normal: strength 5/5, reflexes normal, no sensory loss, no bowel or bladder symptoms.",
            "## Plan",
            "Percutaneous kyphoplasty at L1.",
        ]),
        ("MRI Report - Lumbar and Thoracolumbar Spine", [
            "Date: 2026-09-22.   Study: MRI of the thoracolumbar spine without contrast. Radiologist: Dr. Peter Wong, MD.",
            "Findings: Acute compression fracture of L1 with marked bone marrow edema on STIR sequences. Vertebral body height loss about 38% anteriorly, "
            "with mild focal kyphosis of 14 degrees. No retropulsion, no canal compromise, no neural impingement. No epidural abscess. Multilevel osteopenia. "
            "No suspicious lesion; the appearance is osteoporotic.",
            "Impression: Acute osteoporotic compression fracture of L1.",
        ]),
        ("Bone Density and Labs", [
            "DEXA 2026-09-10: lumbar spine T-score -3.1. Diagnosis: osteoporosis.",
            "Labs 2026-09-26: INR 1.0, platelets 245, WBC 6.8, ESR 14, CRP 4 mg/L. Calcium 9.4. No evidence of infection. Not on anticoagulants. "
            "No allergy to bone cement or contrast. Not pregnant (age 79).",
        ]),
        ("Pre-procedure Clearance", [
            "Date: 2026-10-02.   Physician: Dr. Rita Alvarez, MD.",
            "Cleared for the procedure with conscious sedation, ASA class 3. No spinal instability on flexion-extension films. No myelopathy. "
            "Not hospitalized, living at home with her daughter.",
        ]),
    ]


def pva_b(m):
    return [
        pa_page(m, PVA, "22514", "M80.08XA; C61 (Malignant neoplasm of prostate)", "OUTPATIENT", "Hospital outpatient department.", "Outpatient Procedure"),
        ("Pain Clinic Note", [
            "Date: 2026-10-01.   Patient: Walter Stevens, age 76, male.",
            "## History",
            "Back pain for about 4 months after a minor fall in the spring. Pain 6/10 on average, worse with standing. Initially treated by his primary care "
            "physician with acetaminophen, then oxycodone for about 3 weeks. No brace. No formal physical therapy.",
            "Past history: prostate cancer treated with androgen deprivation therapy, PSA recently rising. Bone scan in 2025 showed uptake at L2 and T10. "
            "Followed by oncology. Atrial fibrillation on warfarin.",
            "## Examination",
            "Tenderness over L2. Strength 5/5. Sensation intact. No neurologic deficit.",
            "## Plan",
            "Kyphoplasty at L2 to relieve pain. Warfarin to be held 5 days before the procedure.",
        ]),
        ("Plain Film Report - Lumbar Spine", [
            "Date: 2026-07-15.   Study: AP and lateral radiographs of the lumbar spine.",
            "Findings: Compression deformity of L2 with about 30% height loss. Osteopenia. Degenerative changes at multiple levels. No MRI or bone scan was "
            "performed during this episode. Age of the fracture cannot be determined from this study.",
        ]),
        ("Lab Results", [
            "Date: 2026-09-28.   INR 2.6 (on warfarin). Platelets 190. PSA 14.2 ng/mL, up from 6.0 six months ago.",
            "Hemoglobin 11.9. Calcium 9.8. Alkaline phosphatase 168 (mildly elevated).",
        ]),
        ("Fax Cover", [
            "Please authorize L2 kyphoplasty, scheduled 2026-10-28. MRI will be done if required. Oncology notes available on request.",
        ]),
    ]


# ======================================================================================
# 06  TMS FOR DEPRESSION, CPT 90867   (LCD L34641)
# ======================================================================================
PSY = "Northcoast Psychiatry and TMS Center"
M_T1 = member("Emily Foster", "1988-08-09", "MBR-46001", "F", "40 Meadow Park Dr, Columbus, OH 43220", "(614) 555-0106", "Dr. Daniel Kim, MD",
              "Psychiatry", "1932047658", PSY, "(614) 555-0160", "(614) 555-0161", "Imani Whitfield", "2026-10-20", 5)
M_T2 = member("Kevin Brennan", "1982-01-17", "MBR-46002", "M", "711 Station Rd, Toledo, OH 43615", "(419) 555-0155", "Karen Doyle, APRN-CNP",
              "Psychiatric Nurse Practitioner", "1295048637", "Maumee Behavioral Health", "(419) 555-0180", "(419) 555-0181", "Reyna Castellanos", "2026-10-27", 5)
TMS = "Therapeutic repetitive transcranial magnetic stimulation (TMS), initial treatment course"


def tms_a(m):
    return [
        pa_page(m, TMS, "90867", "F33.2 (Major depressive disorder, recurrent, severe without psychotic features)", "OUTPATIENT",
                "Office / outpatient TMS suite.", "Outpatient Treatment"),
        ("Psychiatric Evaluation", [
            "Date: 2026-09-18.   Patient: Emily Foster, age 38, female. Evaluated by Dr. Daniel Kim, MD, Psychiatry.",
            "## History",
            "Recurrent major depressive disorder, current episode 14 months, severe. PHQ-9 score 22 (severe). Hamilton Depression Rating Scale 27. "
            "Hopelessness and fatigue. No suicidal intent, no psychosis. No mania. No alcohol or substance use.",
            "## Medication trials in the current episode (two different classes)",
            "Sertraline (SSRI) titrated to 200 mg daily for 10 weeks, 2025-09 to 2025-11: no clinically significant response. Bupropion XL (NDRI) 300 mg for "
            "8 weeks, 2025-12 to 2026-02: no response. Aripiprazole 5 mg augmentation for 6 weeks: no benefit, stopped for restlessness. Each trial was at an "
            "adequate dose and duration.",
            "## Assessment and order",
            "Treatment-resistant major depression. I have examined the patient and reviewed the records. I order a course of left prefrontal rTMS. "
            "I am experienced in TMS and will supervise treatments on site.",
        ]),
        ("Psychotherapy Records", [
            "Provider: Dr. Hannah Brooks, PsyD. Evidence-based psychotherapy: cognitive behavioral therapy, weekly, 16 sessions from 2026-01-12 to 2026-05-08.",
            "~ PHQ-9 at start: 20    at session 8: 21    at end: 21",
            "No significant improvement in depressive symptoms as measured by the PHQ-9 across the course of CBT.",
        ]),
        ("Rating Scales", [
            "~ Date          PHQ-9   HAM-D",
            "~ 2025-09-15     22      28   (baseline of current treatment)",
            "~ 2025-12-01     21      27   (after sertraline)",
            "~ 2026-03-02     20      26   (after bupropion)",
            "~ 2026-09-18     22      27   (evaluation)",
        ]),
        ("TMS Safety Screening", [
            "Date: 2026-09-25.   Completed by Dr. Daniel Kim, MD.",
            "No history of seizure or epilepsy. No head trauma. No neurologic disorder. No cochlear implants, aneurysm clips, deep brain stimulators or "
            "other metal implants in the head or neck. No psychotic disorder. Not pregnant. Not currently on ECT.",
            "Patient has read and signed the TMS consent.",
        ]),
    ]


def tms_b(m):
    return [
        pa_page(m, TMS, "90867", "F33.1 (Major depressive disorder, recurrent, moderate)", "OUTPATIENT", "Office / outpatient TMS suite.", "Outpatient Treatment"),
        ("Psychiatric Progress Note", [
            "Date: 2026-09-29.   Patient: Kevin Brennan, age 44, male. Seen by Karen Doyle, APRN-CNP.",
            "## History",
            "Recurrent depression. Low mood, poor sleep and low energy for 5 months. PHQ-9 score 15 (moderately severe). Reports 'I do not want to take more "
            "pills.' No suicidal thoughts.",
            "Medication history: citalopram 20 mg for 4 weeks, changed to escitalopram 10 mg for 3 weeks, both SSRIs, stopped for sexual side effects. "
            "No other antidepressant has been tried.",
            "Psychotherapy: referred to a therapist, first appointment scheduled for 2026-10-14. No therapy so far.",
            "Past history: one generalized seizure at age 19 during alcohol withdrawal, none since, no anticonvulsant. Alcohol use now about 6 drinks per "
            "week.",
            "## Plan",
            "Start TMS. I recommend a course of left prefrontal rTMS. Order written by the nurse practitioner; supervising psychiatrist Dr. Aaron Levine has "
            "not examined the patient.",
        ]),
        ("Rating Scale", [
            "PHQ-9 on 2026-09-29: 15. PHQ-9 on 2026-06-10: 12. No other scales on file.",
        ]),
        ("Pharmacy Fill History", [
            "Citalopram 20 mg: filled 2026-07-01 (30 tablets). Escitalopram 10 mg: filled 2026-08-04 (21 tablets). No further antidepressant fills.",
        ]),
        ("Fax Cover", [
            "Please authorize TMS, 36 sessions to begin the week of 2026-10-27. Safety screening form to follow.",
        ]),
    ]


# ======================================================================================
# What goes where, and what each packet is for
# ======================================================================================
SERVICES = [
    dict(folder="01_bariatric_surgery", name="Bariatric surgery", cpt="43775", policy="NCD 100.1, plus LCD L35022 (Novitas)",
         scope="Weight-loss surgery for morbid obesity: sleeve, bypass and band.",
         packets=[
             dict(file="A_straightforward_carter_sleeve.pdf", who=M_B1, pages=bari_a, level="Straightforward",
                  tests="BMI 42 with diabetes, hypertension and sleep apnea. A 6-month supervised diet program with a dietitian, a psychological clearance, no contraindications, a surgeon certification and a postoperative plan are all in the packet. A stand-alone sleeve.",
                  expect="Approve. Every requirement is met and has a quote."),
             dict(file="B_complex_hayes_sleeve.pdf", who=M_B2, pages=bari_b, level="Complex",
                  tests="BMI 36.8 in the consult but 34.4 three weeks later at the primary care visit. Prediabetes and a controlled blood pressure instead of a clear comorbidity. Only self-directed diets, no supervised program. A depression history with the psychological evaluation still pending. The sleeve is described as the first stage of a longer plan, not stand-alone. No surgeon credentials or postoperative plan.",
                  expect="Pend or escalate. Conflicting BMI and several missing items, each with a question for the provider."),
             dict(file="C_approve_walker_gastric_bypass.pdf", who=M_B3, pages=bari_c, level="Straightforward, nationally covered procedure",
                  tests="A laparoscopic Roux-en-Y gastric bypass (43644), which the national policy covers. BMI 45.9 with diabetes, hypertension and sleep apnea, a 7-month supervised diet program, psychological clearance, no contraindications, a surgeon certification and a postoperative plan.",
                  expect="Approve, once the rule NONCOVERED-PROCEDURE-ABSENT is rejected in the NCD review. That rule's check ('procedure type must be none') fails every packet that names a procedure, so with it approved even this packet escalates."),
         ]),
    dict(folder="02_total_knee_replacement", name="Total knee replacement", cpt="27447", policy="LCD L36575 (Noridian)",
         scope="Total knee replacement for arthritis of the knee, first-time and revision.",
         packets=[
             dict(file="A_straightforward_evans_right_knee.pdf", who=M_K1, pages=knee_a, level="Straightforward",
                  tests="Weight-bearing X-ray with grade 4 osteoarthritis, severe pain and limited walking, six months of NSAIDs, two injections, 12 physical therapy visits and a cane.",
                  expect="Approve. Imaging, functional limits and failed conservative treatment are all documented."),
             dict(file="B_complex_jennings_laterality_mismatch.pdf", who=M_K2, pages=knee_b, level="Complex",
                  tests="The request says left knee, the exam and plan are about the right knee, and the outside MRI does not say which side. No weight-bearing X-ray report. Conservative treatment is 3 weeks of ibuprofen and a refused physical therapy course. Uncontrolled diabetes (A1c 9.3%) and warfarin.",
                  expect="Pend. Ask which knee, ask for the X-ray report, and ask what conservative treatment was tried."),
         ]),
    dict(folder="03_spinal_cord_stimulator", name="Spinal cord stimulator", cpt="63685 (also 63650)", policy="LCD L36204 (Noridian)",
         scope="Implanting spinal cord stimulator leads and the pulse generator for chronic pain.",
         packets=[
             dict(file="A_straightforward_mitchell_permanent_implant.pdf", who=M_S1, pages=scs_a, level="Straightforward",
                  tests="Failed back surgery syndrome. Medications, physical therapy and injections tried. A psychological screen, a patient education record and a 10-day trial with 63% pain reduction, 50% less medication and better walking.",
                  expect="Approve. The trial result clears the 50% bar and the screening is documented."),
             dict(file="B_complex_lopez_weak_trial.pdf", who=M_S2, pages=scs_b, level="Complex",
                  tests="The trial gave about 33% pain reduction with no drop in opioids and no measured function. A urine screen positive for a drug that was not prescribed. The psychological evaluation is not done. Only home exercise, no formal physical therapy.",
                  expect="Escalate or pend. The trial misses the 50% threshold and the screening items are missing."),
         ]),
    dict(folder="04_hypoglossal_nerve_stimulation", name="Hypoglossal nerve stimulation", cpt="64582", policy="LCD L38528 (WPS)",
         scope="Implanting a nerve stimulator for moderate to severe obstructive sleep apnea.",
         packets=[
             dict(file="A_straightforward_anderson.pdf", who=M_H1, pages=hgns_a, level="Straightforward",
                  tests="Age 52, BMI 28.8, AHI 41 on a sleep study from 7 months ago, 8% central and mixed events, CPAP intolerance with shared decision making, a sleep endoscopy without complete concentric collapse, small tonsils and no excluding conditions.",
                  expect="Approve. Every number is inside the policy limits."),
             dict(file="B_complex_nguyen.pdf", who=M_H2, pages=hgns_b, level="Complex",
                  tests="BMI 34.5 is close to the 35 limit. The sleep study is 30 months old, over the 24-month limit. Central and mixed events are 21%, under the 25% limit. CPAP 'dislike' with no sleep expert or shared decision making. No sleep endoscopy yet. Tonsils grade 3. Mild pulmonary hypertension.",
                  expect="Pend. Several numbers are near a limit and several items are missing or stale."),
         ]),
    dict(folder="05_vertebral_augmentation", name="Vertebral augmentation", cpt="22514 (also 22513)", policy="LCD L38213 (WPS)",
         scope="Cement into a painful vertebral compression fracture: vertebroplasty and kyphoplasty.",
         packets=[
             dict(file="A_straightforward_collins_acute_fracture.pdf", who=M_V1, pages=pva_a, level="Straightforward",
                  tests="An acute L1 osteoporotic fracture, 5 weeks old, with an MRI from 14 days ago showing bone marrow edema. Pain of 7 to 9, worsening despite 4 weeks of non-surgical care, 38% height loss, no neurologic deficit, no infection and normal coagulation.",
                  expect="Approve. Timing, imaging, pain and conservative care all meet the criteria."),
             dict(file="B_complex_stevens_old_fracture_cancer_history.pdf", who=M_V2, pages=pva_b, level="Complex",
                  tests="A fracture about 4 months old, past the acute and subacute window. Only an X-ray from 3 months ago, no MRI. Pain of 6, 3 weeks of opioids and no brace or physical therapy. A prostate cancer history with a rising PSA and bone scan uptake, so the fracture may not be osteoporotic. Warfarin with an INR of 2.6.",
                  expect="Escalate. The fracture may be metastatic or too old, and imaging is missing."),
         ]),
    dict(folder="06_tms_depression", name="TMS for depression", cpt="90867 (also 90868, 90869)", policy="LCD L34641 (WPS)",
         scope="Magnetic stimulation treatment for depression that has not responded to other treatment.",
         packets=[
             dict(file="A_straightforward_foster.pdf", who=M_T1, pages=tms_a, level="Straightforward",
                  tests="Severe recurrent depression, PHQ-9 22. Two adequate medication trials from different classes plus a third, 16 sessions of CBT with no improvement on PHQ-9, ordered by a psychiatrist who examined the patient, and a clean safety screen.",
                  expect="Approve. Severity, failed treatments, therapy and prescriber all meet the policy."),
             dict(file="B_complex_brennan.pdf", who=M_T2, pages=tms_b, level="Complex",
                  tests="Moderate depression, PHQ-9 15. Only one medication class tried, for a few weeks each. Psychotherapy not started. A seizure at age 19 during alcohol withdrawal. Ordered by a nurse practitioner, not a psychiatrist who examined the patient.",
                  expect="Pend or escalate. Several policy requirements are missing and a seizure history is a safety limit."),
         ]),
]


def readme(svc):
    lines = [f"# {svc['name']}", "",
             f"- **Service to create:** {svc['name']}",
             f"- **Describe it as:** {svc['scope']}",
             f"- **Billing code to start with:** {svc['cpt']}",
             f"- **Policy to build:** {svc['policy']}", "",
             "## The two packets", ""]
    for p in svc["packets"]:
        lines += [f"### {p['file']}  ({p['level']})", "", f"**What it contains:** {p['tests']}", "", f"**What to expect:** {p['expect']}", ""]
    lines += ["The expected result is a guide. It depends on which rules you approved when you reviewed the policy.", "",
              "All patient data is made up."]
    return "\n".join(lines) + "\n"


def main():
    os.makedirs(OUT, exist_ok=True)
    index = ["# Interview packets", "",
             "Six services, two packets each (bariatric also has a third, C, a covered gastric bypass). A is straightforward, B is complex. Build the service first (describe it, add the billing code, build the policy, review it, submit), then upload the packets.", "",
             "| Service | Billing code | Policy | Packet A | Packet B |", "|---|---|---|---|---|"]
    for svc in SERVICES:
        d = os.path.join(OUT, svc["folder"])
        os.makedirs(d, exist_ok=True)
        for p in svc["packets"]:
            m = p["who"]
            pages = p["pages"](m)
            assert len(pages) == m["npages"], (p["file"], len(pages), m["npages"])
            write_pdf(os.path.join(d, p["file"]), f"{m['practice']}   Fax {m['fax']}   {TODAY.isoformat()}", pages)
        open(os.path.join(d, "README.md"), "w", encoding="utf-8").write(readme(svc))
        a, b = svc["packets"][:2]
        extra = "".join(f"; {p['file']}" for p in svc["packets"][2:])
        index.append(f"| {svc['name']} | {svc['cpt']} | {svc['policy']} | {a['file']} | {b['file']}{extra} |")
        print(svc["folder"], "->", [p["file"] for p in svc["packets"]])
    index += ["", "All patient data is made up. Regenerate with `python scripts/make_interview_packets.py`."]
    open(os.path.join(OUT, "README.md"), "w", encoding="utf-8").write("\n".join(index) + "\n")


if __name__ == "__main__":
    main()
