"""Generate the made-up test packets and the manifest with expected outcomes.
All data is fictional. Run: python scripts/make_packets.py
"""
import json, os
from fpdf import FPDF

OUT = "packets"
os.makedirs(OUT, exist_ok=True)


def header(name, mid, dob, age, facility, cpt, proc, admit, level="INPATIENT"):
    return ("Prior Authorization Request - Inpatient Admission", [
        f"Member: {name}   DOB: {dob} (age {age})   Member ID: {mid}",
        f"Requesting facility: {facility}, Utilization Review Dept.",
        f"Requested service: Elective inpatient admission, {proc}",
        f"CPT {cpt}. Planned admit date: {admit}.",
        f"Level of care requested: {level}."])


PACKETS = [
    dict(
        file="p01_complete_degenerative.pdf", label="Complete packet, criteria clearly met",
        expected=dict(action="approve", gate_complete=True, missing=[]),
        pages=[
            header("Linda Ramirez", "MBR-0101", "1953-07-02", 73, "Lakeside Regional Hospital", "22612",
                   "open lumbar spinal fusion, L4-L5", "2026-10-13"),
            ("Surgeon Operative Plan", [
                "Diagnosis: degenerative spondylolisthesis L4-L5 with neurogenic claudication.",
                "Plan: open L4-L5 decompression and posterolateral fusion with instrumentation.",
                "Expected length of stay: 3 midnights for pain control, mobilization and monitoring.",
                "Shared decision making completed with patient and daughter; risks and benefits reviewed."]),
            ("Imaging and Conservative Care", [
                "Flexion-extension radiographs show 5 mm anterolisthesis at L4-L5 with dynamic instability.",
                "MRI shows severe central canal stenosis at L4-L5.",
                "Failed 9 months of conservative care: physical therapy, NSAIDs, and two epidural steroid injections."]),
            ("History and Physical", [
                "Past medical history: heart failure (EF 35 percent), COPD on home oxygen, type 2 diabetes.",
                "Post-operative plan: telemetry monitoring, respiratory therapy and cardiology co-management."]),
        ]),
    dict(
        file="p02_john_doe_missing_los.pdf", label="Hero case: length of stay not documented",
        expected=dict(action="pend", gate_complete=False, missing=["expected_los_days"]),
        pages=[
            header("John Doe", "MBR-0042", "1955-03-14", 71, "Riverside General Hospital", "22612",
                   "open lumbar spinal fusion, L4-L5", "2026-10-06"),
            ("Surgeon Operative Plan", [
                "Diagnosis: lumbar spondylolisthesis L4-L5 with neurogenic claudication.",
                "Plan: open L4-L5 decompression and posterolateral fusion with instrumentation.",
                "Surgeon expects a multi-day stay for pain control and mobilization.",
                "Exact length of stay not documented.",
                "Shared decision making documented with the patient."]),
            ("Imaging and Conservative Care", [
                "Flexion-extension radiographs show dynamic instability at L4-L5.",
                "Failed 6 months of conservative care: physical therapy, NSAIDs, two epidural steroid injections."]),
            ("History and Physical", [
                "71-year-old male. Past medical history: heart failure, EF 40 percent; type 2 diabetes,",
                "HbA1c 8.1 percent. Hypertension. Former smoker."]),
            ("Cardiology Clearance", [
                "EF 40 percent, NYHA class II, stable on therapy. Cleared for surgery with elevated",
                "peri-operative cardiac risk. Recommend telemetry monitoring and cardiology co-management",
                "post-operatively."]),
        ]),
    dict(
        file="p03_missing_imaging.pdf", label="Length of stay clear, instability not evidenced",
        expected=dict(action="pend", gate_complete=False, missing=["indication_evidence"]),
        pages=[
            header("Robert Chen", "MBR-0207", "1958-01-21", 68, "St. Anne Medical Center", "22612",
                   "open lumbar spinal fusion, L3-L4", "2026-10-20"),
            ("Surgeon Operative Plan", [
                "Diagnosis: lumbar spondylolisthesis L3-L4 with back and leg pain.",
                "Expected length of stay: 3 midnights.",
                "Failed 8 months conservative care: physical therapy, NSAIDs and epidural injection.",
                "Shared decision making documented."]),
            ("History and Physical", [
                "Past medical history: coronary artery disease, obesity BMI 41, type 2 diabetes.",
                "Post-operative plan: telemetry and pulmonary monitoring."]),
        ]),
    dict(
        file="p04_short_stay_low_risk.pdf", label="Complete but short stay, low risk: needs a physician",
        expected=dict(action="escalate", gate_complete=True, missing=[]),
        pages=[
            header("Susan Whitfield", "MBR-0315", "1961-11-09", 64, "Maple Grove Surgical Hospital", "22612",
                   "open lumbar spinal fusion, L5-S1", "2026-10-15"),
            ("Surgeon Operative Plan", [
                "Diagnosis: degenerative disc disease L5-S1 with instability.",
                "Expected length of stay: 1 midnight.",
                "Shared decision making completed."]),
            ("Imaging and Conservative Care", [
                "Flexion-extension radiographs show instability at L5-S1.",
                "Failed 12 months of conservative care: physical therapy, NSAIDs and injections."]),
            ("History and Physical", [
                "Healthy 64-year-old, no significant comorbidities.",
                "Post-operative plan: routine recovery, discharge planning."]),
        ]),
    dict(
        file="p05_missing_two_items.pdf", label="Two items missing: stay and conservative care",
        expected=dict(action="pend", gate_complete=False, missing=["expected_los_days", "conservative_treatment"]),
        pages=[
            header("Marcus Bell", "MBR-0422", "1957-05-30", 69, "Harbor View Hospital", "22612",
                   "open lumbar spinal fusion, L4-L5", "2026-10-22"),
            ("Surgeon Operative Plan", [
                "Diagnosis: L4-L5 instability with neurogenic claudication.",
                "Flexion-extension radiographs show dynamic instability at L4-L5.",
                "Shared decision making documented."]),
            ("History and Physical", [
                "Past medical history: heart failure, chronic kidney disease stage 3.",
                "Post-operative plan: telemetry monitoring."]),
        ]),
    dict(
        file="p06_deformity_meets.pdf", label="Deformity indication, complete",
        expected=dict(action="approve", gate_complete=True, missing=[]),
        pages=[
            header("Grace Okonkwo", "MBR-0518", "1954-09-17", 72, "Northgate University Hospital", "22612",
                   "lumbar fusion L2-L5 with instrumentation", "2026-10-27"),
            ("Surgeon Operative Plan", [
                "Diagnosis: symptomatic degenerative lumbar scoliosis with functional limitation in daily activities.",
                "Expected length of stay: 4 midnights, multi-level fusion with anticipated ICU step-down.",
                "Shared decision making completed with patient and spouse."]),
            ("Imaging and Conservative Care", [
                "Standing full-spine radiographs show sagittal imbalance of 6 cm and scoliotic curvature of 38 degrees.",
                "Failed 14 months of non-operative treatment: physical therapy, NSAIDs, bracing and injections."]),
            ("History and Physical", [
                "Past medical history: COPD, osteoporosis, hypertension.",
                "Post-operative plan: step-down unit monitoring and respiratory therapy."]),
        ]),
]

manifest = []
for p in PACKETS:
    pdf = FPDF()
    pdf.set_auto_page_break(True, 15)
    for title, lines in p["pages"]:
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 15)
        pdf.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 11)
        for l in lines:
            pdf.multi_cell(0, 7, l, new_x="LMARGIN", new_y="NEXT")
    pdf.output(os.path.join(OUT, p["file"]))
    manifest.append(dict(file=p["file"], label=p["label"], expected=p["expected"]))

json.dump(manifest, open(os.path.join("evals", "manifest.json"), "w"), indent=1)
print("wrote", len(manifest), "packets")
