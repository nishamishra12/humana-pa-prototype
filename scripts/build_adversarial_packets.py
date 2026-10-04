"""Turns the hard packets written by a separate AI session (docs/ADVERSARIAL_PACKET_PROMPT.md) into PDFs and a scoring manifest.

Put the JSON files it returned in evals/adversarial/ (one packet object per file, or a list per file), then run:
    python scripts/build_adversarial_packets.py
It writes packets/adversarial/*.pdf and evals/adversarial_manifest.json (same shape as evals/multi_manifest.json),
then score with:  python scripts/run_evals.py --adversarial
The author's truth is used as written. Nothing here looks at how our reader works.
"""
import glob, json, os, sys
from fpdf import FPDF

ROOT = os.path.join(os.path.dirname(__file__), "..")
IN = os.path.join(ROOT, "evals", "adversarial")
OUT = os.path.join(ROOT, "packets", "adversarial")
MANIFEST = os.path.join(ROOT, "evals", "adversarial_manifest.json")
os.makedirs(IN, exist_ok=True)
os.makedirs(OUT, exist_ok=True)

SERVICE = {
    "icd": ("33249", "implantation of a transvenous implantable cardioverter defibrillator (ICD)"),
    "bariatric": ("43644", "laparoscopic Roux-en-Y gastric bypass"),
}
FOOTER = "Made-up data for a software prototype. Not a real patient."


def ascii_safe(s):
    return (s or "").replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"').replace("–", "-").replace("—", "-").replace("²", "2").replace("≥", ">=").replace("≤", "<=").replace("°", " deg").replace(" ", " ").encode("latin-1", "replace").decode("latin-1")


def header_page(p):
    cpt, text = SERVICE[p["service"]]
    m = p["member"]
    return ("Prior Authorization Request", [
        "## Health Plan",
        "Humana Medicare Advantage -- Gold Choice PPO.",
        "",
        "## Member Information",
        f"Member: {m['name']}   DOB: {m['dob']} (age {m['age']})   Member ID: {m['member_id']}",
        f"Sex: {m.get('sex', '')}",
        "",
        "## Requesting Provider",
        f"Practice: {p['practice']}",
        "",
        "## Requested Service",
        f"Requested service: Elective inpatient admission, {text}",
        f"CPT {cpt}",
        f"Planned admit date: {p['planned_admit_date']}",
        "Level of care requested: INPATIENT",
    ])


def write_pdf(path, pages):
    pdf = FPDF()
    pdf.set_auto_page_break(True, 15)
    for title, lines in pages:
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 9, ascii_safe(title), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
        pdf.set_font("Helvetica", "", 10.5)
        for line in lines:
            line = ascii_safe(line)
            if line == "":
                pdf.ln(3)
            elif line.startswith("## "):
                pdf.set_font("Helvetica", "B", 11.5)
                pdf.cell(0, 7, line[3:], new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("Helvetica", "", 10.5)
            else:
                pdf.multi_cell(0, 6, line, new_x="LMARGIN", new_y="NEXT")
        pdf.set_y(-18)
        pdf.set_font("Helvetica", "I", 8)
        pdf.cell(0, 6, FOOTER)
    pdf.output(path)


def main():
    packets = []
    for f in sorted(glob.glob(os.path.join(IN, "*.json"))):
        d = json.load(open(f, encoding="utf-8"))
        packets += d if isinstance(d, list) else [d]
    if not packets:
        print("No packets found in", IN)
        return
    manifest = []
    for p in packets:
        pages = [header_page(p)] + [(pg["title"], pg["lines"]) for pg in p["pages"]]
        name = f"{p['id']}.pdf"
        write_pdf(os.path.join(OUT, name), pages)
        facts = {k: dict(truth=v["truth"], value=v.get("value"), why=v.get("why", ""), critical=None) for k, v in p["truth"].items()}
        manifest.append(dict(file=f"adversarial/{name}", procedure={"icd": "icd", "bariatric": "bariatric"}[p["service"]],
                             label=f"[{p.get('category', '?')}] {p.get('why_hard', '')}"[:160], member=p["member"]["name"], needs_ocr=False,
                             note=p.get("action_reasoning", ""), expected_action=p["expected_action"], expected_missing=[], facts=facts,
                             category=p.get("category"), difficulty=p.get("difficulty")))
    json.dump(manifest, open(MANIFEST, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(f"built {len(manifest)} packets -> {OUT}\nmanifest -> {MANIFEST}")


if __name__ == "__main__":
    main()
