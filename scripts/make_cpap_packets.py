"""Three made-up packets for the new-service demo: continuous positive airway pressure (CPAP) for obstructive sleep apnea.
The procedure code is an equipment (HCPCS) code, E0601, so the packet has no CPT code and no policy in the library until the
policy owner adds one. PDFs go to packets/demo_new_service/.

  cpap_complete.pdf      everything the policy asks for is documented            -> the tool recommends approve
  cpap_missing_test.pdf  no sleep study report in the packet                      -> the tool asks the provider for it (pend)
  cpap_low_ahi.pdf       sleep study shows mild apnea (AHI 9), no other pathway   -> the tool sends it to a medical director

All patient data is MADE UP. Run from the repo root:  python scripts/make_cpap_packets.py
"""
import os
from datetime import date

from fpdf import FPDF

OUT = "packets/demo_new_service"
os.makedirs(OUT, exist_ok=True)
TODAY = date(2026, 10, 4)
FOOTER = "Made-up data for a software prototype. Not a real patient."


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


def one_line(pdf, text, size=10.5):
    while size > 6:
        pdf.set_font("Helvetica", "", size)
        if pdf.get_string_width(text) <= pdf.w - pdf.l_margin - pdf.r_margin - 1:
            break
        size -= 0.25
    pdf.cell(0, 6, text, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10.5)


def write(path, fax_line, pages):
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
            else:
                pdf.multi_cell(0, 5.4, ln, new_x="LMARGIN", new_y="NEXT")
    pdf.output(path)


def request_page(m, npages):
    return ("Prior Authorization Request - Durable Medical Equipment", [
        "## Health Plan",
        "Humana Medicare Advantage. Plan ID: H5216-014-000. Request type: standard pre-service review.",
        f"Date of request: {TODAY.isoformat()}",
        "",
        "## Member Information",
        f"!! Member: {m['name']}   DOB: {m['dob']} (age {m['age']})   Member ID: {m['mid']}",
        f"Address: {m['addr']}   Phone: {m['phone']}",
        "",
        "## Requesting Provider",
        f"{m['doc']} -- Sleep Medicine. NPI: {m['npi']}",
        f"Practice: {m['practice']}",
        f"Phone: {m['ph2']}   Fax: {m['fax']}",
        "",
        "## Requested Service",
        "!! Requested service: Home CPAP device (continuous positive airway pressure), initial rental",
        "!! HCPCS E0601   ICD-10: G47.33 (obstructive sleep apnea)",
        "Level of care requested: OUTPATIENT. Place of service: Home.",
        "",
        "## Submission Contact",
        f"Submitted through the provider portal by {m['coord']}, Authorization Coordinator.",
        f"Supporting clinical documentation attached ({npages} pages including this request).",
    ])


def consult_page(m, finding):
    return ("Sleep Medicine Consultation", [
        f"Patient: {m['name']}, a {m['age']}-year-old adult seen in clinic on {m['seen']}.",
        "",
        "## Reason for visit",
        "Loud snoring, witnessed pauses in breathing, and unrefreshing sleep for about two years. A family member reports the patient falls asleep while watching television.",
        "",
        "## Assessment",
        f"A face-to-face clinical evaluation for obstructive sleep apnea was completed today, including history, Epworth sleepiness score of 14, neck circumference and airway exam. {finding}",
        "",
        "## Plan",
        "Order a sleep study. If it confirms obstructive sleep apnea, start CPAP therapy.",
    ])


def sleep_study_page(m, ahi, kind):
    return ("Sleep Study Report", [
        f"Patient: {m['name']}   Study date: {m['study']}",
        "",
        "## Test",
        f"{kind}. The study was ordered by the patient's treating physician, {m['doc']}, and performed under the supervision of a board-certified sleep physician.",
        "",
        "## Results",
        f"Apnea-hypopnea index (AHI): {ahi} events per hour. Study length was adequate for the number of events scored.",
        f"Lowest oxygen saturation 84 percent.",
        "",
        "## Interpretation",
        f"{'Moderate to severe' if ahi >= 15 else 'Mild'} obstructive sleep apnea. Interpreted by {m['doc']}.",
    ])


def education_page(m, done=True):
    return ("CPAP Education Visit", [
        f"Patient: {m['name']}   Date: {m['edu']}",
        "",
        "The patient attended a face-to-face education session with the equipment supplier's respiratory therapist before the equipment was ordered. "
        "The therapist reviewed how CPAP works, mask fitting, cleaning, and the importance of nightly use." if done else
        "Education visit not yet scheduled.",
    ])


MEMBERS = {
    "complete": dict(name="Raymond Okafor", dob="1962-05-09", age=64, mid="MBR-7710", addr="48 Birchwood Lane, Dayton, OH", phone="555-0148", doc="Dr. Elena Marsh",
                     npi="1234567890", practice="Great Lakes Sleep Medicine", ph2="555-0192", fax="555-0193", coord="Dina Pruitt", seen="2026-09-02", study="2026-09-16", edu="2026-09-28"),
    "missing": dict(name="Patricia Linden", dob="1958-11-21", age=67, mid="MBR-7722", addr="9 Harbor Street, Toledo, OH", phone="555-0161", doc="Dr. Samuel Ortiz",
                    npi="2234567891", practice="Maumee Valley Sleep Clinic", ph2="555-0177", fax="555-0178", coord="Joel Reeves", seen="2026-09-04", study="", edu="2026-09-29"),
    "low": dict(name="Gerald Whitaker", dob="1971-02-17", age=55, mid="MBR-7735", addr="302 Elm Court, Columbus, OH", phone="555-0105", doc="Dr. Anita Rao",
                npi="3234567892", practice="Capital Sleep Center", ph2="555-0120", fax="555-0121", coord="Nora Vance", seen="2026-09-08", study="2026-09-20", edu="2026-09-30"),
}

for key, m in MEMBERS.items():
    fax = f"FAX  {m['practice']}  {TODAY.isoformat()}  to Humana UM"
    if key == "complete":
        pages = [consult_page(m, "He has no history of a prior CPAP trial."), sleep_study_page(m, 28, "Attended in-lab polysomnography (PSG)"), education_page(m)]
        name = "cpap_complete.pdf"
    elif key == "missing":
        pages = [consult_page(m, "Findings are consistent with obstructive sleep apnea and the sleep study report is to follow."), education_page(m)]
        name = "cpap_missing_test.pdf"
    else:
        pages = [consult_page(m, "He has no other medical conditions."), sleep_study_page(m, 9, "Attended in-lab polysomnography (PSG)"), education_page(m)]
        name = "cpap_low_ahi.pdf"
    pages = [request_page(m, len(pages) + 1)] + pages
    write(os.path.join(OUT, name), fax, pages)
    print("wrote", os.path.join(OUT, name), len(pages), "pages")
