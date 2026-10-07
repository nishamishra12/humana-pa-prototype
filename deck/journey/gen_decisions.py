"""Decisions and trade-offs on ONE static slide: one business decision (do not train on past decisions) and the two
trade-offs, a person at both ends. No animation, no transition.
Run from deck/journey with NODE_PATH pointing at a folder that has @resvg/resvg-js:   python gen_decisions.py
Output: Decisions_Tradeoffs.pptx
"""
import json, os, re, shutil, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from gen_part2_onepage import HELPERS, G

W, GAP, X0 = 3.99, 0.18, 0.5
CARDS = [
    dict(panel="C.greenSoft", tag="BUSINESS DECISION  ·  THE READER", title="Learn from past decisions, or read the policy?",
         rows=[("THE CHOICE", "Read this patient's packet against the policy. Do not train on Humana's past decisions."),
               ("WHY", "Past decisions carry old mistakes and old bias. CMS: decide on the patient's own record."),
               ("THE COST", "No shortcut from years of history. Every rule is built and approved."),
               ("HOW HISTORY HELPS", "Test data for the evals. A ranking of which services to onboard next.")]),
    dict(panel="C.provPanel", tag="TRADE-OFF  ·  THE RULEBOOK", title="Who approves the key facts?",
         rows=[("THE CHOICE", "The owner approves every key fact the AI drafts. The AI does not approve its own."),
               ("WHY NOT AUTO", "Too many floods the nurse with pends. Too few lets a requirement through."),
               ("THE COST", "Owner time. But it is one time for each policy."),
               ("HOW WE RELAX IT", "Her decisions become a test set. High precision and recall on new policies: auto.")]),
    dict(panel="C.payPanel", tag="TRADE-OFF  ·  THE PACKETS", title="How cautious is the AI?",
         rows=[("THE CHOICE", "Recall over precision. When unsure, send it to a person."),
               ("WHY", "A miss is a wrong approval. A false alarm costs a few minutes."),
               ("THE COST", "Some false alarms, so nurses see more flagged cases."),
               ("HOW WE RELAX IT", "Watch the nurses. Many approvals on flags: raise precision. A miss: fix it first.")]),
]


def card(i, c):
    x = X0 + i * (W + GAP)
    js = [f'panel("Card{i}", {x:.2f}, 1.45, {W}, 4.5, {c["panel"]});',
          f'txt("Tg{i}", {x + 0.25:.2f}, 1.62, {W - 0.5:.2f}, 0.25, [{json.dumps(c["tag"])}], {{ size: 10, color: C.green, bold: true }});',
          f'txt("Ti{i}", {x + 0.25:.2f}, 1.9, {W - 0.5:.2f}, 0.62, [{json.dumps(c["title"])}], {{ size: 17, color: C.ink }});']
    for j, (lab, val) in enumerate(c["rows"]):
        y = 2.62 + j * 0.82
        js.append(f'txt("L{i}{j}", {x + 0.25:.2f}, {y:.2f}, {W - 0.5:.2f}, 0.22, [{json.dumps(lab)}], {{ size: 9, bold: true }});')
        js.append(f'txt("V{i}{j}", {x + 0.25:.2f}, {y + 0.22:.2f}, {W - 0.5:.2f}, 0.56, [{json.dumps(val)}], {{ size: 11.5, color: C.ink }});')
    return "\n".join(js)


BODY = 'frame("DECISIONS AND TRADE-OFFS", "Three decisions. A person at both ends.", "Trust before speed", "CMS, February 2024: a coverage decision must rest on the patient\'s own record, not on a prediction from large data sets.");\n'
BODY += "\n".join(card(i, c) for i, c in enumerate(CARDS)) + "\n"
BODY += r'''
add({ name: "Band", kind: "node", static: true, x: 0.5, y: 6.12, w: 12.33, h: 0.55, fill: C.green, line: C.green, lineW: 1, radius: 0.08, align: "center", valign: "middle", margin: [0.02, 0.15, 0.02, 0.15],
  runs: [{ text: "Start cautious. Watch what people do. Relax the AI only as fast as the evidence allows.", options: { bold: true, fontSize: 14, color: C.white, fontFace: B } }] });
'''

txt = open(os.path.join(HERE, "..", "..", "docs", "DECISIONS_SCRIPT.md"), encoding="utf-8").read()
NOTES = [txt.split("## Script", 1)[1].strip()]

if __name__ == "__main__":
    G.build("Decisions and trade-offs", "Decisions_Tradeoffs", HELPERS + BODY, ['{ hold: 0, fx: [] }'], NOTES)
    out = os.path.join(HERE, "Decisions_Tradeoffs.pptx")
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
