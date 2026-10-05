"""Three made-up packets for allergen immunotherapy with subcutaneous immunotherapy (SCIT), policy LCD L40046 (Palmetto GBA).
The request code is CPT 95165 (antigen preparation and provision for allergen immunotherapy), which CMS lists in Billing and Coding
article A59971. PDFs go to packets/demo_new_service/.

  scit_complete.pdf      everything the policy asks for is documented            -> the tool recommends approve
  scit_missing_history.pdf   no record of medicines tried or allergen avoidance       -> the tool asks the provider for it (pend)
  scit_pregnant.pdf      complete, but the patient is pregnant                    -> a limitation in the policy: escalate to a medical director

All patient data is MADE UP. Run from the repo root:  python scripts/make_scit_packets.py
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
    return ("Prior Authorization Request - Allergen Immunotherapy", [
        "## Health Plan",
        "Humana Medicare Advantage. Plan ID: H5216-014-000. Request type: standard pre-service review.",
        f"Date of request: {TODAY.isoformat()}",
        "",
        "## Member Information",
        f"!! Member: {m['name']}   DOB: {m['dob']} (age {m['age']})   Member ID: {m['mid']}",
        f"Address: {m['addr']}   Phone: {m['phone']}",
        "",
        "## Requesting Provider",
        f"{m['doc']} -- Allergy and Immunology. NPI: {m['npi']}",
        f"Practice: {m['practice']}",
        f"Phone: {m['ph2']}   Fax: {m['fax']}",
        "",
        "## Requested Service",
        "!! Requested service: Subcutaneous allergen immunotherapy (SCIT), antigen preparation and provision for a course of injections",
        "!! CPT 95165   ICD-10: J30.2 (other seasonal allergic rhinitis); J30.81 (allergic rhinitis due to animal dander)",
        "Level of care requested: OUTPATIENT. Place of service: Physician office.",
        "",
        "## Submission Contact",
        f"Submitted through the provider portal by {m['coord']}, Authorization Coordinator.",
        f"Supporting clinical documentation attached ({npages} pages including this request).",
    ])


def consult_page(m, extra, treatment=True):
    return ("Allergy and Immunology Consultation", [
        f"Patient: {m['name']}, {m['age']}-year-old, seen in clinic on {m['seen']}.",
        "",
        "## History",
        "Nasal congestion, sneezing, itchy watery eyes and postnasal drip every spring and fall, and a milder pattern all year. Symptoms are worst in the weeks of tree pollen and ragweed season and when cleaning the house or being around cats. Allergic conjunctivitis accompanies the rhinitis. Mild asthma is well controlled.",
        "",
        *(["## Treatment so far",
           "Environmental control measures are in place: mattress and pillow covers, a HEPA filter in the bedroom, windows closed in pollen season. She has used intranasal fluticasone daily and cetirizine daily for 10 weeks, which is more than 28 consecutive days, with only partial relief. Symptoms still interfere with sleep and work.",
           ""] if treatment else []),
        "## Assessment",
        (f"Allergic rhinitis with conjunctivitis, poorly controlled despite allergen avoidance and medicines. {extra}" if treatment else f"Allergic rhinitis with conjunctivitis. {extra}"),
        "No beta blocker use. No history of anaphylaxis to immunotherapy. A shared decision making discussion about immunotherapy, including risks and the 3 to 5 year course, took place today and the patient wishes to proceed.",
    ])


def testing_page(m, positive=True):
    if positive:
        return ("Allergy Skin Testing Report", [
            f"Patient: {m['name']}   Date of test: {m['test']}",
            "",
            "## Method",
            "Percutaneous skin prick testing with a standard aeroallergen panel. Positive control (histamine) wheal 6 mm. Negative control 0 mm.",
            "",
            "## Results (wheal diameter)",
            "Dust mite, Dermatophagoides pteronyssinus: 9 mm (positive).",
            "Dust mite, Dermatophagoides farinae: 8 mm (positive).",
            "Oak pollen: 7 mm (positive). Ragweed pollen: 6 mm (positive). Cat dander: 5 mm (positive).",
            "",
            "## Interpretation",
            "Clinically relevant specific IgE to dust mite, tree pollen, ragweed and cat dander, which matches the history. Serum specific IgE to Dermatophagoides pteronyssinus was 12.4 kU/L (class 4).",
        ])
    return ("Allergy Testing Note", [
        f"Patient: {m['name']}",
        "",
        "Allergy skin testing and serum allergen-specific IgE testing have been discussed. Testing has not been done yet. The patient prefers to start immunotherapy first and test later.",
    ])


def plan_page(m, pregnant=False):
    return ("Immunotherapy Treatment Plan", [
        f"Patient: {m['name']}   Plan date: {m['plan']}",
        "",
        f"The antigen extracts will be prepared by {m['doc']}, a physician (MD) who has examined the patient and set the plan of treatment and dosage regimen.",
        "",
        ("Pregnancy status: the patient is 14 weeks pregnant. Immunotherapy would start during this pregnancy." if pregnant else "Pregnancy status: the patient is not pregnant. A urine pregnancy test was negative at the last visit."),
        "",
        "## Schedule",
        "Build-up: one injection a week for about 6 months, then a maintenance dose once a month. An initial course of 3 to 5 years is planned, with a review every 6 to 12 months.",
        "",
        "## Safety",
        "Injections are given only in the physician's office, which is equipped to treat anaphylaxis. The patient waits 30 minutes after each injection. Epinephrine is on site and staff are trained in emergency treatment.",
    ])


MEMBERS = {
    "complete": dict(name="Marisol Quinn", dob="1985-04-12", age=41, mid="MBR-8810", addr="77 Orchard Way, Dayton, OH", phone="555-0201", doc="Dr. Priya Raman",
                     npi="4234567893", practice="Miami Valley Allergy and Asthma", ph2="555-0211", fax="555-0212", coord="Tessa Hartwell", seen="2026-09-10", test="2026-09-17", plan="2026-09-24"),
    "missing": dict(name="Helen Brandt", dob="1979-08-30", age=47, mid="MBR-8822", addr="14 Cedar Lane, Toledo, OH", phone="555-0233", doc="Dr. Omar Haddad",
                    npi="5234567894", practice="Lakeside Allergy Associates", ph2="555-0244", fax="555-0245", coord="Rob Teller", seen="2026-09-12", test="", plan="2026-09-26"),
    "pregnant": dict(name="Dana Okoye", dob="1992-01-19", age=34, mid="MBR-8835", addr="209 Willow Court, Columbus, OH", phone="555-0256", doc="Dr. Linda Cho",
                     npi="6234567895", practice="Capital Allergy and Immunology", ph2="555-0267", fax="555-0268", coord="Mia Sorensen", seen="2026-09-15", test="2026-09-22", plan="2026-09-29"),
}

for key, m in MEMBERS.items():
    fax = f"FAX  {m['practice']}  {TODAY.isoformat()}  to Humana UM"
    if key == "complete":
        pages = [consult_page(m, "She is not pregnant (urine hCG negative today)."), testing_page(m), plan_page(m)]
        name = "scit_complete.pdf"
    elif key == "missing":
        pages = [consult_page(m, "She is not pregnant (urine hCG negative today).", treatment=False), testing_page(m), plan_page(m)]  # no record of medicines or avoidance
        name = "scit_missing_history.pdf"
    else:
        pages = [consult_page(m, "She is currently 14 weeks pregnant."), testing_page(m), plan_page(m, pregnant=True)]
        name = "scit_pregnant.pdf"
    pages = [request_page(m, len(pages) + 1)] + pages
    write(os.path.join(OUT, name), fax, pages)
    print("wrote", os.path.join(OUT, name), len(pages), "pages")
