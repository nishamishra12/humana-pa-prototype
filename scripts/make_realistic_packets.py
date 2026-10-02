"""Longer, demo-quality PA packets for manual end-to-end testing (Admin -> Nurse -> Medical
Director). Not part of any eval set -- these are for clicking through the real app, not for
scoring. Each is 6-7 pages with full demographics, insurance, referring provider, and detailed
clinical narrative, unlike the terse eval fixtures. All data is made up.
"""
import os
from fpdf import FPDF

OUT = "packets/demo"
os.makedirs(OUT, exist_ok=True)


def pdf_with_pages(fname, pages):
    pdf = FPDF()
    pdf.set_auto_page_break(True, 15)
    for title, lines in pages:
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 9, title, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
        pdf.set_font("Helvetica", "", 10.5)
        for line in lines:
            if line == "":
                pdf.ln(3)
            elif line.startswith("## "):
                pdf.set_font("Helvetica", "B", 11.5)
                pdf.cell(0, 7, line[3:], new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("Helvetica", "", 10.5)
            else:
                pdf.multi_cell(0, 6, line, new_x="LMARGIN", new_y="NEXT")
    pdf.output(os.path.join(OUT, fname))


def demographics_page(member):
    return ("Prior Authorization Request", [
        "## Health Plan",
        "Humana Medicare Advantage -- Gold Choice PPO. Plan ID: H5216-014-000.",
        "",
        "## Member Information",
        f"Member: {member['name']}   DOB: {member['dob']} (age {member['age']})   Member ID: {member['mid']}",
        f"Address: {member['address']}",
        f"Phone: {member['phone']}   Sex: {member['sex']}",
        "Primary Insurance: Humana Medicare Advantage (primary). Secondary: none on file.",
        "",
        "## Referring / Requesting Provider",
        f"{member['surgeon']}, MD -- Orthopedic Spine Surgery",
        f"NPI: {member['npi']}   Practice: {member['facility']}",
        f"Phone: {member['phone2']}   Fax: {member['fax']}",
        "",
        "## Requested Service",
        f"Elective inpatient admission, {member['proc']}",
        f"CPT {member['cpt']}   ICD-10: {member['icd10']}",
        f"Planned admission date: {member['admit']}",
        "Level of care requested: INPATIENT.",
        "",
        "## Prior Authorization Contact",
        "Submitted via provider portal by: Jennifer Ruiz, Surgical Scheduling Coordinator.",
        "Callback number: (614) 555-0199.",
    ])


M1 = dict(name="Dorothy Alvarez", dob="1957-11-03", age=68, mid="MBR-11042", sex="F",
          address="4420 Larkspur Lane, Columbus, OH 43215", phone="(614) 555-0133",
          surgeon="Dr. Nathan Pierce", npi="1932847561", facility="Columbus Spine & Orthopedic Associates",
          phone2="(614) 555-0180", fax="(614) 555-0181", proc="open lumbar spinal fusion, L4-L5",
          cpt="22612", icd10="M43.16 (Spondylolisthesis, lumbar region)", admit="2026-11-14")

M2 = dict(name="Richard Okonkwo-Baptiste", dob="1961-04-19", age=65, mid="MBR-11058", sex="M",
          address="118 Chesterfield Court, Dublin, OH 43017", phone="(614) 555-0147",
          surgeon="Dr. Elaine Whitfield", npi="1740296385", facility="Midwest Orthopedic & Spine Institute",
          phone2="(614) 555-0190", fax="(614) 555-0191", proc="open lumbar spinal fusion, L5-S1",
          cpt="22612", icd10="M43.17 (Spondylolisthesis, lumbosacral region)", admit="2026-11-18")

M3 = dict(name="Patricia Yun-Harmon", dob="1963-08-27", age=63, mid="MBR-11077", sex="F",
          address="29 Windermere Ave, Westerville, OH 43081", phone="(614) 555-0162",
          surgeon="Dr. Marcus Delacroix", npi="1685904723", facility="Capital City Spine Surgery",
          phone2="(614) 555-0200", fax="(614) 555-0201", proc="open lumbar spinal fusion, L3-L4",
          cpt="22612", icd10="M43.16 (Spondylolisthesis, lumbar region)", admit="2026-11-21")


COMMON_PAGES_APPROVE = [
    ("History and Physical", [
        "## Chief Complaint",
        "Progressive low back pain radiating into the left lower extremity, worsening over the past",
        "14 months, now with intermittent numbness in the left foot.",
        "",
        "## History of Present Illness",
        "The patient is a well-known established patient of this practice, followed since early last",
        "year for mechanical low back pain. Over the past 14 months, symptoms have progressed from",
        "intermittent discomfort to a constant aching pain with episodic sharp radicular pain down the",
        "left leg to the foot, accompanied by subjective numbness along the L5 dermatome. Pain is",
        "worse with standing and walking more than two blocks, and improves somewhat with sitting.",
        "The patient reports the pain is now significantly limiting activities of daily living,",
        "including the ability to care for grandchildren and participate in church activities.",
        "",
        "## Past Medical History",
        "Hypertension, well controlled on lisinopril. Type 2 diabetes mellitus, diet and metformin",
        "controlled, most recent HbA1c 6.8. Hyperlipidemia on atorvastatin. No history of prior spine",
        "surgery.",
        "",
        "## Past Surgical History",
        "Cholecystectomy (2011). Total knee arthroplasty, right (2019), uncomplicated recovery.",
        "",
        "## Medications",
        "Lisinopril 10mg daily, metformin 500mg twice daily, atorvastatin 20mg daily, gabapentin",
        "300mg three times daily, acetaminophen as needed.",
        "",
        "## Allergies",
        "No known drug allergies.",
        "",
        "## Physical Examination",
        "Vital signs stable. Lumbar spine with decreased range of motion in flexion and extension,",
        "paraspinal muscle tenderness L4 through S1. Positive straight leg raise on the left at 40",
        "degrees, reproducing radicular symptoms. Motor strength 4/5 left extensor hallucis longus,",
        "otherwise 5/5 throughout. Sensation diminished to light touch along the left L5 dermatome.",
        "Deep tendon reflexes symmetric. Gait is antalgic, favoring the left side.",
    ]),
]

COMMON_PAGES_TAIL = [
    ("Consent and Prior Authorization Summary", [
        "## Shared Decision Making",
        "Risks, benefits, and alternatives (continued conservative management, injection therapy,",
        "surgery) were discussed at length with the patient and her daughter, who was present as",
        "support. The patient expressed understanding of the surgical risks including infection,",
        "bleeding, nerve injury, hardware failure, and the possibility of incomplete symptom relief.",
        "The patient elected to proceed with surgical intervention after conservative measures",
        "failed to provide durable relief.",
        "",
        "## Payer Notice",
        "This request is submitted under the member's Humana Medicare Advantage plan. Provider",
        "attests that the information contained in this packet is accurate and complete to the best",
        "of their knowledge as of the date of submission.",
    ]),
]


def build_approve(fname, m):
    pages = [demographics_page(m)] + COMMON_PAGES_APPROVE + [
        ("Surgeon Operative Plan", [
            "## Diagnosis",
            f"Degenerative spondylolisthesis, {m['proc'].split(', ')[1]}, with associated neurogenic",
            "claudication and radiculopathy, refractory to non-operative management.",
            "",
            "## Planned Procedure",
            f"Open posterior lumbar decompression and instrumented fusion, {m['proc'].split(', ')[1]},",
            "with pedicle screw fixation and posterolateral arthrodesis.",
            "",
            "## Expected Hospital Course",
            "Expected length of stay: 3 midnights. The patient will require inpatient monitoring for",
            "pain control, early mobilization with physical therapy, and wound checks. Given the",
            "patient's cardiovascular risk factors, telemetry monitoring is planned for the first",
            "24 hours post-operatively.",
            "",
            "## Post-Operative Plan",
            "Telemetry monitoring overnight, physical therapy evaluation on post-operative day one,",
            "staged mobilization, discharge planning to begin day two pending functional status.",
        ]),
        ("Imaging and Diagnostic Studies", [
            "## Lumbar Spine Radiographs, Flexion-Extension Views",
            "TECHNIQUE: Standing lateral radiographs of the lumbar spine were obtained in flexion and",
            "extension positions.",
            "",
            "FINDINGS: There is grade 1 anterolisthesis of L4 on L5 measuring approximately 6mm on",
            "neutral views, increasing to 9mm on flexion views with near-complete reduction on",
            "extension, consistent with dynamic segmental instability. Disc space height is moderately",
            "decreased at this level. No acute fracture.",
            "",
            "IMPRESSION: Grade 1 degenerative spondylolisthesis at L4-L5 with radiographic evidence of",
            "dynamic instability on flexion-extension imaging.",
            "",
            "## MRI Lumbar Spine Without Contrast",
            "FINDINGS: Moderate to severe central canal stenosis at L4-L5 secondary to anterolisthesis,",
            "ligamentum flavum hypertrophy, and facet arthropathy. Moderate bilateral neural foraminal",
            "narrowing, left greater than right, correlating with the patient's left-sided radicular",
            "symptoms.",
        ]),
        ("Conservative Treatment History", [
            "## Timeline of Non-Operative Management",
            "Physical therapy: 16 sessions over 10 weeks, focused on core stabilization and lumbar",
            "extension exercises, with only transient symptom improvement.",
            "",
            "Medications: NSAIDs (naproxen) trialed for 8 weeks with partial relief; discontinued due",
            "to GI upset. Gabapentin titrated to current dose for neuropathic component, with partial",
            "benefit.",
            "",
            "Interventional: Two fluoroscopically guided left L4-L5 transforaminal epidural steroid",
            "injections, approximately 3 months apart. First injection provided roughly 6 weeks of",
            "meaningful relief; second injection provided minimal benefit, suggesting progression of",
            "the underlying instability.",
            "",
            "Total duration of conservative care: approximately 11 months, exceeding typical payer",
            "thresholds for surgical consideration in degenerative spondylolisthesis.",
        ]),
    ] + COMMON_PAGES_TAIL
    pdf_with_pages(fname, pages)


def build_pend(fname, m):
    pages = [demographics_page(m)] + COMMON_PAGES_APPROVE + [
        ("Surgeon Operative Plan", [
            "## Diagnosis",
            f"Degenerative spondylolisthesis, {m['proc'].split(', ')[1]}, with associated neurogenic",
            "claudication and radiculopathy, refractory to non-operative management.",
            "",
            "## Planned Procedure",
            f"Open posterior lumbar decompression and instrumented fusion, {m['proc'].split(', ')[1]},",
            "with pedicle screw fixation and posterolateral arthrodesis.",
            "",
            "## Expected Hospital Course",
            "Given the patient's comorbidities and the extent of the planned decompression, the",
            "surgical team anticipates the patient will need more than a brief overnight stay for",
            "adequate pain control and mobilization before a safe discharge can be considered. Exact",
            "anticipated duration to be determined based on intra-operative findings.",
            "",
            "## Post-Operative Plan",
            "Telemetry monitoring overnight, physical therapy evaluation on post-operative day one,",
            "staged mobilization, discharge planning to begin once functional milestones are met.",
        ]),
        ("Imaging and Diagnostic Studies", [
            "## Lumbar Spine Radiographs, Flexion-Extension Views",
            "TECHNIQUE: Standing lateral radiographs of the lumbar spine were obtained in flexion and",
            "extension positions.",
            "",
            "FINDINGS: There is grade 1 anterolisthesis of L4 on L5 measuring approximately 6mm on",
            "neutral views, increasing to 9mm on flexion views with near-complete reduction on",
            "extension, consistent with dynamic segmental instability. Disc space height is moderately",
            "decreased at this level. No acute fracture.",
            "",
            "IMPRESSION: Grade 1 degenerative spondylolisthesis at L4-L5 with radiographic evidence of",
            "dynamic instability on flexion-extension imaging.",
        ]),
        ("Conservative Treatment History", [
            "## Timeline of Non-Operative Management",
            "Physical therapy: 16 sessions over 10 weeks, focused on core stabilization and lumbar",
            "extension exercises, with only transient symptom improvement.",
            "",
            "Medications: NSAIDs (naproxen) trialed for 8 weeks with partial relief; discontinued due",
            "to GI upset. Gabapentin titrated to current dose for neuropathic component, with partial",
            "benefit.",
            "",
            "Interventional: Two fluoroscopically guided left L4-L5 transforaminal epidural steroid",
            "injections, approximately 3 months apart. First injection provided roughly 6 weeks of",
            "meaningful relief; second injection provided minimal benefit.",
            "",
            "Total duration of conservative care: approximately 11 months.",
        ]),
    ] + COMMON_PAGES_TAIL
    pdf_with_pages(fname, pages)


def build_escalate(fname, m):
    pages = [demographics_page(m)] + [
        ("History and Physical", [
            "## Chief Complaint",
            "Low back pain with mild left leg discomfort, present for approximately 6 months.",
            "",
            "## History of Present Illness",
            "The patient reports a 6-month history of low back pain with occasional mild radiation",
            "into the left buttock and posterior thigh, without clear dermatomal numbness. Symptoms",
            "are intermittent and tend to flare with prolonged standing. The patient has continued to",
            "work full duty throughout this period with occasional modified activity on flare days.",
            "",
            "## Past Medical History",
            "No significant past medical history. Patient reports no chronic conditions and takes no",
            "regular medications.",
            "",
            "## Past Surgical History",
            "None.",
            "",
            "## Medications",
            "None on a regular basis; ibuprofen as needed for flares.",
            "",
            "## Allergies",
            "No known drug allergies.",
            "",
            "## Physical Examination",
            "Vital signs stable, well-appearing. Lumbar spine with mild decreased range of motion.",
            "Straight leg raise negative bilaterally. Motor strength 5/5 throughout. Sensation intact.",
            "Reflexes symmetric. Gait normal.",
        ]),
        ("Surgeon Operative Plan", [
            "## Diagnosis",
            f"Degenerative disc disease with instability, {m['proc'].split(', ')[1]}.",
            "",
            "## Planned Procedure",
            f"Open posterior lumbar decompression and instrumented fusion, {m['proc'].split(', ')[1]}.",
            "",
            "## Expected Hospital Course",
            "Expected length of stay: 1 midnight. Patient is young, healthy, and anticipated to",
            "mobilize quickly.",
            "",
            "## Post-Operative Plan",
            "Routine recovery with standard post-operative monitoring; discharge planning to begin",
            "the morning after surgery pending adequate pain control and mobility.",
        ]),
        ("Imaging and Diagnostic Studies", [
            "## Lumbar Spine Radiographs, Flexion-Extension Views",
            "FINDINGS: Mild dynamic translation at the level in question on flexion-extension views,",
            "consistent with early segmental instability. No fracture or high-grade listhesis.",
            "",
            "IMPRESSION: Mild instability, as above.",
        ]),
        ("Conservative Treatment History", [
            "## Timeline of Non-Operative Management",
            "Physical therapy: 12 sessions over 8 weeks. One lumbar epidural steroid injection with",
            "partial, short-lived relief. NSAIDs used intermittently.",
            "",
            "Total duration of conservative care: approximately 5 months.",
        ]),
    ] + COMMON_PAGES_TAIL
    pdf_with_pages(fname, pages)


build_approve("demo_alvarez_approve.pdf", M1)
build_pend("demo_okonkwo_pend.pdf", M2)
build_escalate("demo_yun_escalate.pdf", M3)
print("wrote 3 realistic demo packets to", OUT)
