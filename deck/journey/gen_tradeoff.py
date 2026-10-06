"""The key tradeoff on ONE static slide: two tradeoffs side by side, a person at both ends. No animation, no transition.
Run from deck/journey with NODE_PATH pointing at a folder that has @resvg/resvg-js:   python gen_tradeoff.py
Output: Tradeoff.pptx
"""
import json, os, re, shutil, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from gen_part2_onepage import HELPERS, G

CARDS = [
    dict(n=1, x=0.5, panel="C.provPanel", tag="MILESTONE 1  ·  THE LIBRARY", title="Who approves the key facts?",
         rows=[("THE CHOICE", "The owner approves every key fact the AI writes. The AI does not approve its own."),
               ("WHY NOT AUTO", "Too many key facts floods the nurse with flags. Too few lets requirements through."),
               ("THE COST", "Time, and a new persona doing new work. But it is one time for each policy."),
               ("HOW WE RELAX IT", "Test on 100 policies. Tune. Let it approve only when precision and recall are high.")]),
    dict(n=2, x=6.78, panel="C.payPanel", tag="MILESTONE 2  ·  THE PACKETS", title="How cautious is the AI?",
         rows=[("THE CHOICE", "Recall over precision. When unsure, send it to a person."),
               ("WHY", "A missed problem is a wrong approval. A false alarm costs a few minutes."),
               ("THE COST", "Some false alarms, so the nurse sees more flagged cases."),
               ("HOW WE RELAX IT", "Watch the nurses. Many approvals on flagged cases: raise precision. A miss: fix that first.")]),
]


def card(c):
    n, x = c["n"], c["x"]
    js = [f'panel("Card{n}", {x}, 1.45, 6.05, 4.5, {c["panel"]});',
          f'txt("Tg{n}", {x + 0.3}, 1.65, 5.4, 0.25, [{json.dumps(c["tag"])}], {{ size: 10.5, color: C.green, bold: true }});',
          f'txt("Ti{n}", {x + 0.3}, 1.95, 5.4, 0.5, [{json.dumps(c["title"])}], {{ size: 22, color: C.ink }});']
    for i, (lab, val) in enumerate(c["rows"]):
        y = 2.7 + i * 0.8
        js.append(f'txt("L{n}{i}", {x + 0.3}, {y + 0.02:.2f}, 1.55, 0.4, [{json.dumps(lab)}], {{ size: 9.5, bold: true }});')
        js.append(f'txt("V{n}{i}", {x + 1.95}, {y:.2f}, 3.85, 0.75, [{json.dumps(val)}], {{ size: 12.5, color: C.ink }});')
    return "\n".join(js)


BODY = 'frame("THE KEY TRADEOFF", "Two tradeoffs. A person at both ends.", "Trust before speed", "The AI does the heavy lifting in between. A person decides in every phase.");\n'
BODY += "\n".join(card(c) for c in CARDS) + "\n"
BODY += r'''
add({ name: "Band", kind: "node", static: true, x: 0.5, y: 6.1, w: 12.33, h: 0.55, fill: C.green, line: C.green, lineW: 1, radius: 0.08, align: "center", valign: "middle", margin: [0.02, 0.15, 0.02, 0.15],
  runs: [{ text: "A person approves the rules going in, and confirms the decision coming out.", options: { bold: true, fontSize: 14, color: C.white, fontFace: B } }] });
'''

txt = open(os.path.join(HERE, "..", "..", "docs", "TRADEOFF_SCRIPT.md"), encoding="utf-8").read()
NOTES = [txt.split("## Script", 1)[1].strip()]

if __name__ == "__main__":
    G.build("The key tradeoff", "Tradeoff", HELPERS + BODY, ['{ hold: 0, fx: [] }'], NOTES)
    out = os.path.join(HERE, "Tradeoff.pptx")
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
