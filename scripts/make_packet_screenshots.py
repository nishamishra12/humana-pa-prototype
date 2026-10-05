"""Cuts the input and output panes for steps 3 to 6 out of architecture/inner_workings.html and saves each one as a PNG,
ready to paste into the packet slides. Uses Microsoft Edge in headless mode. Run from the repo root:  python scripts/make_packet_screenshots.py
"""
import os, re, subprocess, tempfile, time
from bs4 import BeautifulSoup
from PIL import Image, ImageChops

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "architecture", "inner_workings.html")
OUT = os.path.join(ROOT, "deck", "journey", "screenshots")
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
os.makedirs(OUT, exist_ok=True)

html = open(SRC, encoding="utf-8").read()
styles = "".join(re.findall(r"<style>.*?</style>", html, re.S))
soup = BeautifulSoup(html, "html.parser")

# (file name, section id, heading text that starts the pane)
PANES = [
    ("step3_input", "s3", "Input: page 1 from Unstructured"),
    ("step3_output_what_the_code_read_and_the_lookup", "s3", "Output 1"),
    ("step3_output_3_policy_stack", "s3", "Output 3"),
    ("step4_input", "s4", "Input: one request"),
    ("step4_output_three_reads", "s4", "Output: three independent reads"),
    ("step5_output_evidence_table", "s5", "Every quote the reader gave"),
    ("step5_output_what_the_nurse_sees", "s5", "What the nurse sees"),
    ("step6_input", "s6", "Input: the facts"),
    ("step6_output_checklist", "s6", "Output: the checklist"),
]


def pane_for(section, start):
    for h in section.find_all(["h4", "h3"]):
        if h.get_text(strip=True).startswith(start):
            node = h
            while node and not (node.name == "div" and "pane" in (node.get("class") or [])):
                node = node.parent
            if node:
                return node
    raise SystemExit(f"pane not found: {start}")


def trim(path, pad=18):
    im = Image.open(path).convert("RGB")
    bg = Image.new("RGB", im.size, (255, 255, 255))
    box = ImageChops.difference(im, bg).getbbox()
    if box:
        l, t, r, b = box
        im = im.crop((max(0, l - pad), max(0, t - pad), min(im.width, r + pad), min(im.height, b + pad)))
    im.save(path)
    return im.size


for name, sid, start in PANES:
    sec = soup.find("section", id=sid)
    pane = pane_for(sec, start)
    page = f'<!doctype html><html data-theme="light"><meta charset="utf-8">{styles}<style>body{{background:#fff!important;margin:0;padding:24px;width:1040px}}.pane{{margin:0!important}}.tw{{overflow:visible!important}}</style><body>{pane}</body></html>'
    tmp = os.path.join(tempfile.gettempdir(), name + ".html")
    open(tmp, "w", encoding="utf-8").write(page)
    png = os.path.join(OUT, name + ".png")
    for attempt in range(4):
        if os.path.exists(png):
            os.remove(png)
        subprocess.run([EDGE, "--headless" if attempt % 2 else "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run", f"--user-data-dir={tempfile.mkdtemp()}", "--force-device-scale-factor=2",
                        "--virtual-time-budget=4000", f"--screenshot={png}", "--window-size=1100,3200", "file:///" + tmp.replace("\\", "/")],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
        for _ in range(20):
            if os.path.exists(png) and os.path.getsize(png) > 1000:
                break
            time.sleep(0.5)
        if os.path.exists(png):
            break
    else:
        raise SystemExit("Edge did not write " + png)
    print(name, trim(png))
