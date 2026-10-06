"""The roadmap on ONE static slide: three phases, with two milestones inside phase 1. No animation, no transition.
Run from deck/journey with NODE_PATH pointing at a folder that has @resvg/resvg-js:   python gen_roadmap.py
Output: Roadmap.pptx
"""
import json, os, re, shutil, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from gen_part2_onepage import HELPERS, G


def phase(n, x, w, color, soft, head, title, sub, body, who, gate):
    js = [f'ring("Ph{n}", {x}, 1.45, {w}, 4.2, {color});',
          f'txt("H{n}", {x + 0.25}, 1.62, {w - 0.5}, 0.25, [{json.dumps(head)}], {{ size: 10.5, color: {color}, bold: true }});',
          f'txt("T{n}", {x + 0.25}, 1.92, {w - 0.5}, 0.45, [{json.dumps(title)}], {{ size: 20, color: C.ink }});']
    if sub:
        js.append(f'txt("S{n}", {x + 0.25}, 2.36, {w - 0.5}, 0.28, [{json.dumps(sub)}], {{ size: 11.5, color: C.muted, bold: true }});')
    if body:
        js.append(f'txt("B{n}", {x + 0.25}, 2.75, {w - 0.5}, 1.5, [{json.dumps(body)}], {{ size: 13, color: C.ink }});')
    js.append(f'txt("W{n}", {x + 0.25}, 4.45, {w - 0.5}, 0.3, [{json.dumps("FOR   " + who)}], {{ size: 11, color: C.ink, bold: true }});')
    js.append(f'add({{ name: "G{n}", kind: "node", static: true, x: {x + 0.2}, y: 4.85, w: {w - 0.4}, h: 0.65, fill: {soft}, line: {color}, lineW: 1, radius: 0.06, valign: "middle", margin: [0.03, 0.12, 0.03, 0.12], runs: [{{ text: "GATE   ", options: {{ bold: true, fontSize: 9.5, color: {color}, fontFace: B, charSpacing: 1.5 }} }}, {{ text: {json.dumps(gate)}, options: {{ fontSize: 11, color: C.ink, fontFace: B }} }}] }});')
    return "\n".join(js)


def milestone(n, x, title, value):
    return (f'add({{ name: "M{n}", kind: "node", static: true, x: {x}, y: 2.75, w: 2.6, h: 1.55, fill: C.white, line: C.green, lineW: 1.25, radius: 0.08, valign: "top", margin: [0.1, 0.12, 0.05, 0.12], '
            f'runs: [{{ text: "MILESTONE {n}", options: {{ bold: true, fontSize: 9, color: C.green, fontFace: B, charSpacing: 1.5, breakLine: true }} }}, '
            f'{{ text: {json.dumps(title)}, options: {{ bold: true, fontSize: 14, color: C.ink, fontFace: B, breakLine: true }} }}, '
            f'{{ text: {json.dumps(value)}, options: {{ fontSize: 11.5, color: C.muted, fontFace: B }} }}] }});')


BODY = 'frame("THE ROADMAP", "Three phases over a year.", "Each phase earns the next one", "The months are illustrative. The order is the point.");\n'
BODY += phase(1, 0.5, 5.95, "C.green", "C.greenSoft", "PHASE 1   ·   MONTHS 1 TO 4", "Right first time. A person decides.", "North star: right-first-time rate. Two milestones ladder up to it.", None,
              "Nurse, provider, member, plan", "A tested library. Evals on real cases. Zero wrong approvals.") + "\n"
BODY += milestone(1, 0.75, "Build the library", "One central place for every policy and what it checks. Every rule traces to the policy's own words.") + "\n"
BODY += milestone(2, 3.55, "Decide every packet", "Fewer pends. The right answer the first time. A sooner decision for the member.") + "\n"
BODY += 'seg("mA", 3.35, 3.5, 3.55, 3.5, true);\n'
BODY += phase(2, 6.75, 3.05, "C.purple", "C.purpleSoft", "PHASE 2   ·   MONTHS 5 TO 9", "Scale.", None,
              "More services, one at a time, ranked by Humana's own request history.", "The plan", "Evals on real cases for each new service.") + "\n"
BODY += phase(3, 10.1, 2.73, "C.amber", "C.amberSoft", "PHASE 3   ·   MONTHS 10 TO 12", "Member status.", None,
              "The member sees where a request stands. It reads the trusted record.", "The member", "A compliance review.") + "\n"
BODY += 'seg("pA", 6.47, 3.5, 6.73, 3.5, true);  seg("pB", 9.82, 3.5, 10.08, 3.5, true);\n'
BODY += r'''
add({ name: "Band", kind: "node", static: true, x: 0.5, y: 5.88, w: 12.33, h: 0.5, fill: C.green, line: C.green, lineW: 1, radius: 0.08, align: "center", valign: "middle", margin: [0.02, 0.15, 0.02, 0.15],
  runs: [{ text: "A person decides in every phase. The AI never denies.", options: { bold: true, fontSize: 14, color: C.white, fontFace: B } }] });
'''

txt = open(os.path.join(HERE, "..", "..", "docs", "ROADMAP_SCRIPT.md"), encoding="utf-8").read()
NOTES = [txt.split("## Script", 1)[1].strip()]

if __name__ == "__main__":
    G.build("The roadmap", "Roadmap", HELPERS + BODY, ['{ hold: 0, fx: [] }'], NOTES)
    out = os.path.join(HERE, "Roadmap.pptx")
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
    print("static slide: no timing, no transition;", len(NOTES[0].split()), "words in the notes")
