"""Turns the 10 fresh packets from the separate AI session (docs/LIVE_PACKET_PROMPT.md) into PDFs you upload in the app,
plus the answer key the app uses to score the AI and the nurse.

Put the JSON it returned in evals/live/ (one packet object per file, or a list per file), then run:
    python scripts/build_live_packets.py
It writes packets/live/live_001.pdf ... and evals/live_truth.json ({"live_001.pdf": "pend", ...}),
and prints the table you check in the UI: file, expected action, why.
These packets are a clean test: the reader was never tuned on them. Do not tune on them before the first score.
"""
import glob, json, os, sys

sys.path.insert(0, os.path.dirname(__file__))
from build_adversarial_packets import header_page, write_pdf  # same form page and PDF layout as the 40 hard packets

ROOT = os.path.join(os.path.dirname(__file__), "..")
IN = os.path.join(ROOT, "evals", "live")
OUT = os.path.join(ROOT, "packets", "live")
TRUTH = os.path.join(ROOT, "evals", "live_truth.json")
MANIFEST = os.path.join(ROOT, "evals", "live_manifest.json")
os.makedirs(IN, exist_ok=True)
os.makedirs(OUT, exist_ok=True)

packets = []
for f in sorted(glob.glob(os.path.join(IN, "*.json"))):
    d = json.load(open(f, encoding="utf-8"))
    packets += d if isinstance(d, list) else [d]
if not packets:
    sys.exit(f"No packets found in {IN}")
truth, manifest = {}, []
print(f"{'file':14s} {'expected':9s} {'category':30s} why")
for p in packets:
    name = f"{p['id']}.pdf"
    pages = [header_page(p)] + [(pg["title"], pg["lines"]) for pg in p["pages"]]
    write_pdf(os.path.join(OUT, name), pages)
    truth[name] = p["expected_action"]
    facts = {k: dict(truth=v["truth"], value=v.get("value"), why=v.get("why", ""), critical=None) for k, v in p["truth"].items()}
    manifest.append(dict(file=f"live/{name}", procedure=p["service"], label=f"[{p.get('category', '?')}] {p.get('why_hard', '')}"[:160], member=p["member"]["name"],
                         needs_ocr=False, note=p.get("action_reasoning", ""), expected_action=p["expected_action"], expected_missing=[], facts=facts,
                         category=p.get("category"), difficulty=p.get("difficulty")))
    print(f"{name:14s} {p['expected_action']:9s} {str(p.get('category')):30s} {p.get('why_hard', '')[:90]}")
json.dump(truth, open(TRUTH, "w", encoding="utf-8"), indent=1)
json.dump(manifest, open(MANIFEST, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(f"\nbuilt {len(packets)} PDFs -> {OUT}\nanswer key -> {TRUTH}")
