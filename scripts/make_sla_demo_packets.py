"""Two extra made-up packets used only to demo SLA alerting (not part of the eval set)."""
import os
from fpdf import FPDF

OUT = "packets"
os.makedirs(OUT, exist_ok=True)

PACKETS = [
    ("s01_breached_demo.pdf", "Theresa Nakamura", "MBR-0601", "1960-02-11", 66, "Crestview Medical Center",
     "lumbar fusion L4-L5", "2026-10-18", [
        ("Surgeon Operative Plan", [
            "Diagnosis: L4-L5 instability with neurogenic claudication.",
            "Expected length of stay: 3 midnights.",
            "Shared decision making documented."]),
        ("Imaging and Conservative Care", [
            "Flexion-extension radiographs show dynamic instability at L4-L5.",
            "Failed 7 months of conservative care: physical therapy, NSAIDs, epidural injection."]),
        ("History and Physical", [
            "Past medical history: heart failure, type 2 diabetes.",
            "Post-operative plan: telemetry monitoring."]),
    ]),
    ("s02_soon_demo.pdf", "Daniel Osei", "MBR-0702", "1966-08-23", 60, "Crestview Medical Center",
     "lumbar fusion L5-S1", "2026-10-19", [
        ("Surgeon Operative Plan", [
            "Diagnosis: L5-S1 instability with radiculopathy.",
            "Expected length of stay: 2 midnights.",
            "Shared decision making documented."]),
        ("Imaging and Conservative Care", [
            "Flexion-extension radiographs show dynamic instability at L5-S1.",
            "Failed 9 months of conservative care: physical therapy, NSAIDs, epidural injection."]),
        ("History and Physical", [
            "Past medical history: COPD, coronary artery disease.",
            "Post-operative plan: telemetry and respiratory therapy."]),
    ]),
]

for fname, name, mid, dob, age, facility, proc, admit, pages in PACKETS:
    pdf = FPDF()
    pdf.set_auto_page_break(True, 15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(0, 10, "Prior Authorization Request - Inpatient Admission", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    for l in [f"Member: {name}   DOB: {dob} (age {age})   Member ID: {mid}",
              f"Requesting facility: {facility}, Utilization Review Dept.",
              f"Requested service: Elective inpatient admission, {proc}",
              "CPT 22612. Planned admit date: " + admit + ".",
              "Level of care requested: INPATIENT."]:
        pdf.multi_cell(0, 7, l, new_x="LMARGIN", new_y="NEXT")
    for title, lines in pages:
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 15)
        pdf.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 11)
        for l in lines:
            pdf.multi_cell(0, 7, l, new_x="LMARGIN", new_y="NEXT")
    pdf.output(os.path.join(OUT, fname))

print("wrote", len(PACKETS), "SLA demo packets")
