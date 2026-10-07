"""The closing slide: thank you, three things to remember, and an open floor. No animation, no transition.
Run from deck/journey with NODE_PATH pointing at a folder that has @resvg/resvg-js:   python gen_close.py
Output: Close.pptx
"""
import json, os, re, shutil, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from gen_part2_onepage import HELPERS, G

POINTS = [
    ("1", "Right first time.", "Fewer pends, faster answers, less back and forth."),
    ("2", "A person decides.", "The AI recommends with evidence. It never denies."),
    ("3", "Prove it, then widen it.", "Evals first. Then more services. Then the member."),
]

BODY = r'''
add({ name: "Left", kind: "node", static: true, x: 0, y: 0, w: 6.2, h: 7.5, fill: C.green, line: C.green, lineW: 1, radius: 0, runs: [{ text: " ", options: { fontSize: 8 } }] });
add({ name: "Eyebrow", kind: "text", static: true, x: 0.7, y: 2.3, w: 5, h: 0.3, runs: [{ text: "PRIOR AUTHORIZATION DECISION SUPPORT", options: { bold: true, fontSize: 11, color: C.greenSoft, fontFace: B, charSpacing: 3 } }] });
add({ name: "Thanks", kind: "text", static: true, x: 0.7, y: 2.7, w: 5.2, h: 1.3, valign: "middle", runs: [{ text: "Thank you.", options: { fontSize: 54, color: C.white, fontFace: H } }] });
add({ name: "Q", kind: "text", static: true, x: 0.7, y: 4.0, w: 5.2, h: 0.5, runs: [{ text: "Happy to take your questions.", options: { fontSize: 18, color: C.greenSoft, fontFace: B } }] });
add({ name: "Name", kind: "text", static: true, x: 0.7, y: 6.6, w: 5.2, h: 0.35, runs: [{ text: "Nisha Mishra", options: { bold: true, fontSize: 12, color: C.white, fontFace: B } }] });
add({ name: "Head", kind: "text", static: true, x: 6.9, y: 1.55, w: 5.9, h: 0.3, runs: [{ text: "THREE THINGS TO REMEMBER", options: { bold: true, fontSize: 11, color: C.green, fontFace: B, charSpacing: 3 } }] });
'''
for i, (n, head, line) in enumerate(POINTS):
    y = 2.1 + i * 1.35
    BODY += (f'add({{ name: "N{i}", kind: "node", static: true, x: 6.9, y: {y}, w: 0.6, h: 0.6, fill: C.greenSoft, line: C.green, lineW: 1, radius: 0.3, align: "center", valign: "middle", margin: 0, '
             f'runs: [{{ text: {json.dumps(n)}, options: {{ bold: true, fontSize: 16, color: C.green, fontFace: B }} }}] }});\n')
    BODY += (f'add({{ name: "P{i}", kind: "text", static: true, x: 7.75, y: {y - 0.05}, w: 5.1, h: 0.9, runs: ['
             f'{{ text: {json.dumps(head)}, options: {{ fontSize: 20, color: C.ink, fontFace: H, breakLine: true }} }}, '
             f'{{ text: {json.dumps(line)}, options: {{ fontSize: 13, color: C.muted, fontFace: B }} }}] }});\n')

NOTES = ["Thank you. If I leave you with three things: get it right the first time, keep a person deciding, and prove it before we widen it. I'm happy to take your questions."]

if __name__ == "__main__":
    G.build("Close", "Close", HELPERS + BODY, ['{ hold: 0, fx: [] }'], NOTES)
    out = os.path.join(HERE, "Close.pptx")
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
