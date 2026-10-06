"""Part 2 on ONE static slide, in the same architecture style as the Part 1 slide.
Run from deck/journey with NODE_PATH pointing at a folder that has @resvg/resvg-js:   python gen_part2_onepage.py
Output: Part2_Architecture.pptx
"""
import os, re, shutil, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen_part1_onepage as P1
G = P1.G

# the helpers from the Part 1 slide (icons, regions, labels, connectors), plus a few more glyphs
HELPERS = P1.JS.split('frame("PART 1')[0]
HELPERS = HELPERS.replace("const GLY = {", r'''const GLY = {
  find: `<circle cx="44" cy="44" r="20" fill="none" stroke="STROKE" stroke-width="4.5"/><path d="M59 59 L78 78" stroke="STROKE" stroke-width="5" stroke-linecap="round"/><path d="M34 40 H54 M34 49 H48" stroke="STROKE" stroke-width="3.5" stroke-linecap="round"/>`,
  agree: `<circle cx="38" cy="50" r="18" fill="none" stroke="STROKE" stroke-width="4.5"/><circle cx="62" cy="50" r="18" fill="none" stroke="STROKE" stroke-width="4.5"/><path d="M42 50 L48 57 L58 43" fill="none" stroke="STROKE" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round"/>`,
  key: `<circle cx="34" cy="50" r="14" fill="none" stroke="STROKE" stroke-width="4.5"/><path d="M48 50 H80 M70 50 V63 M60 50 V58" fill="none" stroke="STROKE" stroke-width="4.5" stroke-linecap="round"/>`,
  rules: `<path d="M24 31 L30 37 L40 25 M24 51 L30 57 L40 45 M24 71 L30 77 L40 65" fill="none" stroke="STROKE" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/><path d="M50 31 H76 M50 51 H76 M50 71 H76" stroke="STROKE" stroke-width="4" stroke-linecap="round"/>`,
  chart: `<rect x="26" y="52" width="13" height="24" rx="2" fill="STROKE"/><rect x="44" y="38" width="13" height="38" rx="2" fill="STROKE"/><rect x="62" y="24" width="13" height="52" rx="2" fill="STROKE"/>`,''', 1)
HELPERS += r'''
const wp = (name, key, cx, cy, s = 0.8) => { ART[name] = PEOPLE[key]; add({ name, kind: "image", static: true, x: cx - s / 2, y: cy - s / 2, w: s, h: s }); };
'''

BODY = r'''
frame("PART 2  ·  ARCHITECTURE", "Part 2 decides every packet.", "Every request. The AI helps. A person decides.",
  "All patient data is made up. The AI reads, finds the evidence and recommends. A person decides. The system never denies on its own.");

ring("R1", 1.9, 1.4, 11.0, 1.7, C.green);   rl("R1L", 12.8, "1   INTAKE AND READ", 1.44);
ring("R2", 1.9, 3.2, 11.0, 1.75, C.purple);  rl("R2L", 12.8, "2   THE AI READS, THEN CHECKS ITS OWN WORK", 3.24);
ring("R3", 1.9, 5.05, 11.0, 1.95, C.amber);  rl("R3L", 12.8, "3   DECIDE", 5.09);

/* outside the regions */
icon("iPrv", 1.05, 2.0, "doc", "ext");
cap("cPrv", 1.05, 2.45, "Provider", ["fax or portal"], 1.4);

/* region 1: intake and read */
wp("iInt", "intake", 2.95, 2.0);
cap("cInt", 2.95, 2.45, "Intake coordinator", ["uploads, assigns a nurse"], 1.6);
icon("iApp", 4.8, 2.0, "server", "code");
cap("cApp", 4.8, 2.45, "App server", ["upload, assign, progress"], 1.6);
icon("iUns", 6.65, 2.0, "parts", "etl");
cap("cUns", 6.65, 2.45, "Unstructured API", ["pages to elements, with page numbers"], 1.6);
icon("iKey", 8.5, 2.0, "key", "code");
cap("cKey", 8.15, 2.45, "Billing code to service", ["pattern match, then library lookup"], 1.45);
db("iLib", 11.5, 1.95);
cap("cLib", 11.5, 2.4, "Policy library", ["from Part 1"], 1.7);
seg("a1", 1.5, 2.0, 2.5, 2.0, true);    tag("a1t", 1.45, 1.74, 1.1, "packet PDF");
seg("a2", 3.4, 2.0, 4.35, 2.0, true);   tag("a2t", 3.35, 1.74, 1.05, "upload");
seg("a3", 5.25, 2.0, 6.2, 2.0, true);   tag("a3t", 5.2, 1.74, 1.05, "pages");
seg("a4", 7.1, 2.0, 8.05, 2.0, true);   tag("a4t", 7.05, 1.74, 1.05, "elements, JSON");
seg("a5", 11.0, 1.95, 8.95, 1.95, true); tag("a5t", 9.0, 1.69, 2.0, "service, key facts, rules");
txt("n1", 9.5, 2.82, 3.3, 0.3, ["No service for the code: it says no policy yet. It never guesses."], { size: 9, italic: true });

/* region 2: the AI reads. It runs right to left, under the lookup. */
seg("l1", 8.8, 2.42, 8.8, 3.45, true);   tag("l1t", 8.9, 2.5, 2.4, "elements and key facts", "left");
icon("iSon", 8.8, 3.9, "spark", "ai");
cap("cSon", 8.8, 4.35, "Claude Sonnet", ["reads it 3 times and fills one entry per key fact"], 1.75);
icon("iAgr", 6.8, 3.9, "agree", "code");
cap("cAgr", 6.8, 4.35, "Three reads must agree", ["if not, the key fact is marked unsure"], 1.75);
icon("iEvi", 4.8, 3.9, "find", "code");
cap("cEvi", 4.8, 4.35, "Evidence matcher", ["finds the exact quote: exact, then fuzzy. Gives the page."], 1.75);
icon("iHai", 2.8, 3.9, "spark", "ai");
cap("cHai", 2.9, 4.35, "Claude Haiku", ["checks the quote really supports the fact"], 1.55);
seg("m1", 8.35, 3.9, 7.25, 3.9, true);  tag("m1t", 7.25, 3.64, 1.1, "3 reads");
seg("m2", 6.35, 3.9, 5.25, 3.9, true);  tag("m2t", 5.25, 3.64, 1.1, "agreed facts");
seg("m3", 4.35, 3.9, 3.25, 3.9, true);  tag("m3t", 3.25, 3.64, 1.1, "quotes found");
txt("n2", 10.0, 3.55, 2.8, 0.7, ["Each key fact comes out with its status, value, page and exact quote."], { size: 9, italic: true });
seg("m4", 2.35, 3.9, 1.98, 3.9, false);  seg("m4b", 1.98, 3.9, 1.98, 5.85, false);  seg("m4c", 1.98, 5.85, 2.55, 5.85, true);

/* region 3: decide */
icon("iEng", 3.0, 5.85, "rules", "code");
cap("cEng", 3.0, 6.3, "Rules engine", ["Missing: pend. Unsure: verify. Not met: escalate. All met: approve."], 1.75);
wp("iNur", "nurse", 5.2, 5.85);
cap("cNur", 5.2, 6.3, "UM nurse", ["reviews the evidence. Approves, pends, or escalates."], 1.75);
wp("iDir", "md", 7.4, 5.85);
cap("cDir", 7.4, 6.3, "Medical director", ["decides escalations. The only one who can deny."], 1.75);
db("iCas", 9.6, 5.8);
cap("cCas", 9.6, 6.3, "Case database", ["cases, evidence, comments, audit trail"], 1.75);
icon("iDsh", 11.8, 5.85, "chart", "code");
cap("cDsh", 11.8, 6.3, "Live dashboard", ["for intake and directors"], 1.6);
seg("d1", 3.45, 5.85, 4.75, 5.85, true);   tag("d1t", 3.45, 5.58, 1.3, "recommendation");
seg("d2", 5.65, 5.85, 6.95, 5.85, true);   tag("d2t", 5.65, 5.58, 1.3, "escalate");
seg("d3", 7.85, 5.85, 9.1, 5.85, true);    tag("d3t", 7.85, 5.58, 1.25, "decision, reason");
seg("d4", 10.1, 5.85, 11.35, 5.85, true);  tag("d4t", 10.1, 5.58, 1.25, "live numbers");
txt("n3", 2.75, 5.1, 6.0, 0.4, ["Pend sends the provider one precise question. The reply is read again and comes back to the nurse."], { size: 9, italic: true });
'''

NOTES = [open(os.path.join(HERE, "..", "..", "docs", "PART2_ARCHITECTURE_SCRIPT.md"), encoding="utf-8").read().split("## What Part 2 is", 1)[1].split("## Endpoints")[0].replace("## ", "").strip()]

if __name__ == "__main__":
    G.build("Part 2 on one slide", "Part2_Architecture", HELPERS + BODY, ['{ hold: 0, fx: [] }'], NOTES)
    out = os.path.join(HERE, "Part2_Architecture.pptx")
    tmp = out + ".tmp"
    with zipfile.ZipFile(out) as zi, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zo:
        for it in zi.infolist():
            data = zi.read(it.filename)
            if it.filename == "ppt/slides/slide1.xml":
                x = data.decode("utf-8")
                x = re.sub(r"<p:timing>.*?</p:timing>", "", x, flags=re.S)
                x = re.sub(r"<p:transition.*?</p:transition>|<p:transition[^>]*/>", "", x, flags=re.S)
                data = x.encode("utf-8")
            zo.writestr(it, data)
    shutil.move(tmp, out)
    print("static slide: no timing, no transition")
