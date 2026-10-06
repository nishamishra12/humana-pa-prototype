"""The simple two-part overview slide: two cards and one link line. Static, no animation, no transition.
Run from deck/journey with NODE_PATH pointing at a folder that has @resvg/resvg-js:   python gen_overview_simple.py
Output: Two_Parts_Overview_Simple.pptx
"""
import json, os, re, shutil, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from gen_part2_onepage import HELPERS, G

P1 = [("WHEN", "Once for each service"), ("WHO", "Policy owner"), ("GOES IN", "A service, its billing codes and its policies"),
      ("COMES OUT", "A list of key facts, each with its rule"), ("A PERSON IN THE LOOP", "The owner approves every rule")]
P2 = [("WHEN", "Every time a request comes in"), ("WHO", "Intake coordinator, UM nurse, medical director"), ("GOES IN", "A packet from a provider"),
      ("COMES OUT", "A recommendation, with the evidence for every key fact"), ("A PERSON IN THE LOOP", "The nurse confirms. Only the director can deny.")]


def card(n, x, panel, eyebrow, title, sub, rows, people):
    js = [f'panel("Card{n}", {x}, 1.45, 6.05, 4.3, {panel});',
          f'txt("Eb{n}", {x + 0.3}, 1.65, 3, 0.25, [{json.dumps(eyebrow)}], {{ size: 10.5, color: C.green, bold: true }});',
          f'txt("Ti{n}", {x + 0.3}, 1.95, 4.2, 0.5, [{json.dumps(title)}], {{ size: 22, color: C.ink }});',
          f'txt("Su{n}", {x + 0.3}, 2.5, 4.4, 0.3, [{json.dumps(sub)}], {{ size: 12 }});']
    for i, (k, who) in enumerate(people):
        js.append(f'wp("Av{n}{i}", "{who}", {x + 5.75 - 0.3 - 0.62 * (len(people) - 1 - i) - 0.28:.2f}, 2.05, 0.56);')
    for i, (lab, val) in enumerate(rows):
        y = 3.0 + i * 0.56
        js.append(f'txt("L{n}{i}", {x + 0.3}, {y + 0.01:.2f}, 1.7, 0.4, [{json.dumps(lab)}], {{ size: 9.5, bold: true }});')
        js.append(f'txt("V{n}{i}", {x + 2.05}, {y:.2f}, 3.8, 0.5, [{json.dumps(val)}], {{ size: 13, color: C.ink }});')
    return "\n".join(js)


BODY = 'frame("THE SOLUTION", "The solution has two parts.", "A person is in the loop in both", "The AI drafts, reads and cites. A person approves, confirms and decides. The AI never denies.");\n'
BODY += card(1, 0.5, "C.provPanel", "PART 1", "Build the library", "Onboard a service. Before go-live. The biggest piece of work.", P1, [("owner", "owner")]) + "\n"
BODY += card(2, 6.78, "C.payPanel", "PART 2", "Decide every packet", "The daily work. Every request.", P2, [("i", "intake"), ("n", "nurse"), ("d", "md")]) + "\n"
BODY += r'''
add({ name: "Link", kind: "node", static: true, x: 0.5, y: 5.88, w: 12.33, h: 0.45, fill: C.green, line: C.green, lineW: 1, radius: 0.08, align: "center", valign: "middle", margin: [0.02, 0.15, 0.02, 0.15],
  runs: [{ text: "Part 2 only uses what Part 1 approved.", options: { bold: true, fontSize: 14, color: C.white, fontFace: B } }] });
add({ name: "KF", kind: "node", static: true, x: 0.5, y: 6.45, w: 12.33, h: 0.55, fill: C.greenSoft, line: C.green, lineW: 1.25, radius: 0.08, valign: "middle", margin: [0.04, 0.18, 0.04, 0.18],
  runs: [{ text: "KEY FACT   ", options: { bold: true, fontSize: 11, color: C.green, fontFace: B, charSpacing: 2 } }, { text: "Something the policy says must be in the packet, like length of stay, and the rule it has to pass.", options: { fontSize: 13, color: C.ink, fontFace: B } }] });
'''

txt = open(os.path.join(HERE, "..", "..", "docs", "OVERVIEW_SCRIPT.md"), encoding="utf-8").read()
NOTES = [txt.split("## Script", 1)[1].strip()]

if __name__ == "__main__":
    G.build("The solution has two parts", "Two_Parts_Overview_Simple", HELPERS + BODY, ['{ hold: 0, fx: [] }'], NOTES)
    out = os.path.join(HERE, "Two_Parts_Overview_Simple.pptx")
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
