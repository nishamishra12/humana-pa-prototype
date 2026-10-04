"""Reads the multi-illness demo packets once, with the real upload path (Unstructured OCR + AI reader
+ meaning check), and saves what was read to packets/fixtures/. The app loads these when it seeds demo
cases, so starting the app never needs the network and the demo always shows the same cases.
Run again after changing the reader:  python scripts/build_fixtures.py
"""
import os, sys, json
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
load_dotenv(".env")
from pipeline.run import process

ROOT = os.path.join(os.path.dirname(__file__), "..")
PACKETS = ["icd1_complete_nonischemic", "icd3_conflicting_lvef", "icd5_recent_mi", "bar1_complete", "bar3_bmi_changed"]
OUT = os.path.join(ROOT, "packets", "fixtures")
os.makedirs(OUT, exist_ok=True)


def one(name):
    els, engine, facts, res = process(os.path.join(ROOT, "packets", "multi", name + ".pdf"))
    with open(os.path.join(OUT, name + ".json"), "w", encoding="utf-8") as f:
        json.dump(dict(file=name + ".pdf", engine=engine, elements=[dict(page=e.page, type=e.type, text=e.text) for e in els], facts=facts), f, ensure_ascii=False, indent=1)
    return name, res["action"]


with ThreadPoolExecutor(max_workers=5) as pool:
    for name, action in pool.map(one, [a for a in (sys.argv[1:] or PACKETS)]):
        print(name, "->", action)
