"""M6 held-out eval set: adversarial packets written WITHOUT looking at extract.py's regex
patterns, each targeting one specific real-world failure mode. Ground truth is annotated by
hand per fact (present / absent / negated), separately from whatever the extractor outputs,
so results/evals.py can score recall and hallucination rate independently, per D-007.

Not part of evals/manifest.json (the original plumbing-proof set) on purpose.
"""
import os, random
from fpdf import FPDF
from PIL import Image, ImageDraw, ImageFont, ImageFilter

OUT = "packets/holdout"
os.makedirs(OUT, exist_ok=True)


def header(name, mid, dob, age, facility, cpt, proc, admit):
    return ("Prior Authorization Request - Inpatient Admission", [
        f"Member: {name}   DOB: {dob} (age {age})   Member ID: {mid}",
        f"Requesting facility: {facility}, Utilization Review Dept.",
        f"Requested service: Elective inpatient admission, {proc}",
        f"CPT {cpt}. Planned admit date: {admit}.",
        "Level of care requested: INPATIENT."])


def write_pdf(fname, pages):
    pdf = FPDF()
    pdf.set_auto_page_break(True, 15)
    for title, lines in pages:
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 15)
        pdf.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 11)
        for l in lines:
            pdf.multi_cell(0, 7, l, new_x="LMARGIN", new_y="NEXT")
    pdf.output(os.path.join(OUT, fname))


# H1 -- Patricia Reyes: clinically real facts, phrased the way an actual dictation reads,
# none of it matching extract.py's exact keyword patterns.
write_pdf("h1_ambiguous_phrasing.pdf", [
    header("Patricia Reyes", "MBR-0811", "1959-04-02", 67, "Oakhill Community Hospital", "22612",
           "lumbar fusion L4-L5", "2026-11-02"),
    ("Surgeon Operative Plan", [
        "Diagnosis: chronic low back pain with radiating leg pain, L4-L5 level.",
        "Surgeon expects patient to remain hospitalized for 3 nights given her cardiac history.",
        "Shared decision making completed with patient and son."]),
    ("Imaging", [
        "Imaging obtained; formal read pending at time of submission."]),
    ("History and Conservative Management", [
        "Patient has a significant cardiac history and is followed by cardiology.",
        "Patient underwent an extensive trial of nonsurgical management over several months,",
        "including physiotherapy and anti-inflammatory medication, without lasting relief."]),
    ("Post-Operative Plan", [
        "Will require telemetry monitoring post-operatively given her cardiac history."]),
])

# H2 -- Marcus Webb: two different length-of-stay statements. The later, more specific one
# (3 midnights, written after his comorbidities are reviewed) is the clinically correct one.
write_pdf("h2_conflicting_values.pdf", [
    header("Marcus Webb", "MBR-0822", "1962-09-18", 64, "Pinecrest Surgical Center", "22612",
           "lumbar fusion L5-S1", "2026-11-05"),
    ("Surgeon Operative Plan", [
        "Diagnosis: L5-S1 instability with radiculopathy.",
        "Expected length of stay: 1 midnight.",
        "Shared decision making documented."]),
    ("Imaging and Conservative Care", [
        "Flexion-extension radiographs show dynamic instability at L5-S1.",
        "Failed 8 months of conservative care: physical therapy, NSAIDs, epidural injection."]),
    ("Pre-Admission Addendum (reviewed after cardiology clearance)", [
        "Past medical history: coronary artery disease.",
        "Given comorbidities, anticipate a 3-midnight stay for monitoring and mobilization.",
        "Post-operative plan: telemetry monitoring."]),
])

# H3 -- Angela Petrov: one negation extract.py already handles (comorbidities "none"), and one
# it doesn't (indication_evidence) -- same packet, direct contrast.
write_pdf("h3_negation.pdf", [
    header("Angela Petrov", "MBR-0833", "1965-01-27", 61, "Lakeshore Medical Center", "22612",
           "lumbar fusion L4-L5", "2026-11-08"),
    ("Surgeon Operative Plan", [
        "Diagnosis: lumbar spondylolisthesis L4-L5.",
        "Expected length of stay: 2 midnights.",
        "Shared decision making documented with the patient."]),
    ("Imaging and Conservative Care", [
        "No evidence of segmental instability on flexion-extension radiographs.",
        "Failed 7 months of conservative care: physical therapy, NSAIDs, epidural injection."]),
    ("History and Physical", [
        "No significant comorbidities. Patient is otherwise healthy.",
        "Post-operative plan: routine recovery, discharge planning."]),
])


# H4 -- Walter Kim: clean, complete, unambiguous content (like p01) -- the only variable under
# test is whether a degraded scan survives real OCR. Rendered as noisy rotated images, not text,
# so pdftotext gets nothing and the live Unstructured API must actually OCR it.
def render_scan_page(lines, out_path, title=None):
    img = Image.new("L", (1700, 2200), color=255)
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 30)
        bold = ImageFont.truetype("arialbd.ttf", 34)
    except Exception:
        font = bold = ImageFont.load_default()
    y = 120
    if title:
        d.text((100, y), title, font=bold, fill=0)
        y += 70
    for line in lines:
        d.text((100, y), line, font=font, fill=0)
        y += 55
    img = img.rotate(random.uniform(-1.6, 1.6), fillcolor=255, expand=False)
    img = img.filter(ImageFilter.GaussianBlur(radius=0.6))
    noise = Image.effect_noise(img.size, 22).point(lambda p: p)
    img = Image.blend(img.convert("L"), noise, 0.08)
    img = img.point(lambda p: min(255, int(p * 0.93 + 12)))
    img.convert("RGB").save(out_path, "JPEG", quality=72)


scan_pages = [
    ("Prior Authorization Request - Inpatient Admission", [
        "Member: Walter Kim   DOB: 1957-06-30 (age 69)   Member ID: MBR-0844",
        "Requesting facility: Fairview General Hospital, Utilization Review Dept.",
        "Requested service: Elective inpatient admission, lumbar fusion L4-L5",
        "CPT 22612. Planned admit date: 2026-11-10.",
        "Level of care requested: INPATIENT."]),
    ("Surgeon Operative Plan", [
        "Diagnosis: L4-L5 instability with neurogenic claudication.",
        "Expected length of stay: 3 midnights.",
        "Shared decision making documented with the patient."]),
    ("Imaging and Conservative Care", [
        "Flexion-extension radiographs show dynamic instability at L4-L5.",
        "Failed 9 months of conservative care: physical therapy, NSAIDs, epidural injection."]),
    ("History and Physical", [
        "Past medical history: heart failure, type 2 diabetes.",
        "Post-operative plan: telemetry monitoring and cardiology co-management."]),
]

tmp_imgs = []
for i, (title, lines) in enumerate(scan_pages):
    p = os.path.join(OUT, f"_scan_page{i}.jpg")
    render_scan_page(lines, p, title)
    tmp_imgs.append(p)

pdf = FPDF()
for p in tmp_imgs:
    pdf.add_page()
    pdf.image(p, x=0, y=0, w=210, h=272)
pdf.output(os.path.join(OUT, "h4_degraded_scan.pdf"))
for p in tmp_imgs:
    os.remove(p)

print("wrote 4 holdout packets to", OUT)
