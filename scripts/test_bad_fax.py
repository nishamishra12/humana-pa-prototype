"""Send the bad fax through the same Unstructured call the prototype makes, and check
which key facts come back as text.

Run: python scripts/test_bad_fax.py interview/01_bariatric_surgery/D_bad_fax_walker_gastric_bypass.pdf
"""
import json, os, sys, time
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
os.environ["HONEYCOMB_API_KEY"] = ""  # this test sends nothing to Honeycomb
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pipeline.ingest import _ingest_unstructured

# what a nurse would need, and where it lives: (label, page, handwritten?, text to find)
CHECKS = [
    ("Member name", 1, True, "Denise Walker"),
    ("Date of birth", 1, True, "2/23/1978"),
    ("Member ID", 1, True, "MBR-41003"),
    ("Billing code", 1, True, "43644"),
    ("BMI", 1, True, "45.9"),
    ("Diet program", 1, True, "supervised diet program"),
    ("Callback number", 1, True, "937-555-0120"),
    ("Billing code", 2, False, "43644"),
    ("Level of care", 2, False, "INPATIENT"),
    ("BMI", 3, False, "BMI 45.9"),
    ("Program dates", 3, False, "2026-01-13 to 2026-08-18"),
    ("Non-smoker", 3, False, "Non-smoker"),
    ("Margin note", 3, True, "276 confirmed"),
    ("Visit table row", 4, False, "2026-08-18"),
    ("Visits attended", 4, False, "8 of 8"),
    ("PHQ-9 score", 5, False, "PHQ-9 score 3"),
    ("Psych clearance note", 5, True, "cleared"),
    ("A1c", 6, False, "8.6%"),
    ("Sleep apnea AHI", 6, False, "AHI 34"),
    ("Follow-up visits", 7, False, "2 weeks, 3 months, 6 months and 12"),
    ("Surgeon signature", 7, True, "Reyes"),
]


def norm(s):
    return " ".join(s.lower().replace(",", ", ").split())


path = sys.argv[1]
t0 = time.time()
els = _ingest_unstructured(path)
secs = time.time() - t0
by_page = {}
for e in els:
    by_page.setdefault(e.page, []).append(e.text)

print(f"{len(els)} elements from {len(by_page)} pages in {secs:.0f} s\n")
hits = 0
for label, page, hw, needle in CHECKS:
    text = norm(" ".join(by_page.get(page, [])))
    ok = norm(needle) in text
    hits += ok
    print(f"{'FOUND ' if ok else 'MISSED'}  p{page}  {'handwritten' if hw else 'typed      '}  {label}: {needle}")
print(f"\n{hits} of {len(CHECKS)} found")

out = os.path.splitext(path)[0] + "_unstructured.json"
json.dump([e.__dict__ for e in els], open(out, "w", encoding="utf-8"), indent=1)
print("elements saved to", out)
print("\nPAGE 1 (handwritten cover sheet) as Unstructured read it:")
for t in by_page.get(1, []):
    print("  |", t)
