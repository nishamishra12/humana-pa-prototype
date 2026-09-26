from fpdf import FPDF

PAGES = [
 ("Prior Authorization Request - Inpatient Admission", [
  "Member: John Doe   DOB: 1955-03-14 (age 71)   Member ID: MBR-0042",
  "Requesting facility: Riverside General Hospital, Utilization Review Dept.",
  "Requested service: Elective inpatient admission, open lumbar spinal fusion, L4-L5",
  "CPT 22612 (posterolateral arthrodesis, single level). Planned admit date: 2026-10-06.",
  "Level of care requested: INPATIENT."]),
 ("Surgeon Operative Plan", [
  "Diagnosis: lumbar spondylolisthesis L4-L5 with neurogenic claudication.",
  "Failed 6 months conservative care: physical therapy, NSAIDs, two epidural steroid injections.",
  "Plan: open L4-L5 decompression and posterolateral fusion with instrumentation.",
  "Surgeon expects a multi-day stay for pain control and mobilization.",
  "Exact length of stay not documented."]),
 ("History and Physical", [
  "71-year-old male. Past medical history: heart failure, EF 40 percent; type 2 diabetes,",
  "HbA1c 8.1 percent. Hypertension. Former smoker.",
  "Medications: metformin, lisinopril, carvedilol, furosemide, gabapentin.",
  "Exam: positive straight-leg raise on the left, diminished left EHL strength 4/5."]),
 ("Cardiology Clearance", [
  "Patient evaluated pre-operatively. EF 40 percent, NYHA class II, stable on therapy.",
  "Cleared for surgery with elevated peri-operative cardiac risk.",
  "Recommend telemetry monitoring and cardiology co-management post-operatively."]),
]

pdf = FPDF()
pdf.set_auto_page_break(True, 15)
for title, lines in PAGES:
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 15); pdf.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    for l in lines:
        pdf.multi_cell(0, 7, l, new_x="LMARGIN", new_y="NEXT")
pdf.output("packets/john_doe_lumbar_fusion_incomplete.pdf")
print("ok")
