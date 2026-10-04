"""Step 2 of the policy build: turn the policy source into structured elements with Unstructured.

Same service the packets use (the Transform API). Each element keeps its id, type, text and page. A policy is written in
sections (A. General, B. Nationally Covered Indications, B.1, B.2 ...), and the draft step cites the section each rule
came from, so the titles matter.

Transform reads PDFs, Word files and images, not plain text or HTML. A policy that arrives as text from an API is rendered
to a simple PDF first, which is also what a policy PDF from a health plan looks like. A PDF that already exists is sent as is.

If the Unstructured key is missing or the call fails, a local fallback splits the text into paragraphs so the build still runs,
and the result says so.
"""
import json, os, re

from .sources import WORK

REPLACE = {"’": "'", "‘": "'", "“": '"', "”": '"', "–": "-", "—": "-", "≤": "<=", "≥": ">=", "§": "Sec."}


def _ascii(t):
    for a, b in REPLACE.items():
        t = t.replace(a, b)
    return t.encode("latin-1", "replace").decode("latin-1")


def _is_heading(line):
    return bool(re.match(r"^([A-Z]\.\s|NCD |LCD |Sec\. )", line)) and len(line) < 100


def to_pdf(text, path):
    from fpdf import FPDF
    pdf = FPDF()
    pdf.set_auto_page_break(True, 15)
    pdf.add_page()
    for ln in [x for x in text.split("\n") if x.strip()]:
        ln = _ascii(ln.strip())
        head = _is_heading(ln)
        pdf.set_font("Helvetica", "B" if head else "", 11 if head else 10)
        pdf.multi_cell(0, 7 if head else 5.5, ln, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)
    pdf.output(path)


def parse_unstructured(path):
    from unstructured_transform_client import TransformClient
    client = TransformClient(api_key=os.environ["UNSTRUCTURED_API_KEY"], server_url="https://transform.unstructured.io")
    with open(path, "rb") as f:
        res = client.parse.run(input=f, output="elements")
    els = [dict(type=e.type, text=e.text, page=(getattr(e.metadata, "page_number", None) or 1)) for e in res.elements if e.text and e.text.strip()]
    return els, dict(profile=str(getattr(res, "profile", "")), pages=getattr(res.metadata, "page_count", None))


def parse_local(path):
    text = open(path, encoding="utf-8").read()
    out = [dict(type="Title" if _is_heading(p) else "NarrativeText", text=p, page=1) for p in [x.strip() for x in text.split("\n")] if p]
    return out, dict(profile="local fallback", pages=1)


def parse(policy_id, version):
    """Reads the source in the work folder, writes elements.json beside it. Returns (elements, info)."""
    folder = os.path.join(WORK, policy_id, version)
    src = os.path.join(folder, "source.txt")
    pdf_path = os.path.join(folder, "source.pdf")
    try:
        if not os.path.exists(pdf_path):
            to_pdf(open(src, encoding="utf-8").read(), pdf_path)
        els, info = parse_unstructured(pdf_path)
        info["engine"] = "unstructured"
    except Exception as e:
        els, info = parse_local(src)
        info["engine"] = "local"
        info["note"] = f"Unstructured not used: {type(e).__name__}: {str(e)[:100]}"
    for i, e in enumerate(els, 1):
        e["id"] = f"e{i}"
    json.dump(dict(info=info, elements=els), open(os.path.join(folder, "elements.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    return els, info
