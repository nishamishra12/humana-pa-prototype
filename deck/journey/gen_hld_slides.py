"""Two high-level-design slides for Part 1, one per flow, in the same click-by-click style as the person slides.
Run from deck/journey with NODE_PATH pointing at a folder that has @resvg/resvg-js:   python gen_hld_slides.py
Output: Part1_Flow1_HLD.pptx (CMS data to a service) and Part1_Flow2_HLD.pptx (a policy to approved rules and key facts).
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from gen_person_slides import build

CYL = r'''
const cylSvg = (f, s) => `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 220 150"><path d="M4 22 V124 A106 22 0 0 0 216 124 V22" fill="#${f}" stroke="#${s}" stroke-width="3"/><ellipse cx="110" cy="22" rx="106" ry="20" fill="#${f}" stroke="#${s}" stroke-width="3"/></svg>`;
'''


class Slide:
    def __init__(self, eyebrow, title, sub, footer):
        self.js = [CYL, f"frame({json.dumps(eyebrow)}, {json.dumps(title)}, {json.dumps(sub)}, {json.dumps(footer)});"]
        self.slots, self.notes, self.prev = [], [], None

    def panel(self, name, y, h, fill, label):
        self.js.append(f'panel("{name}", 0.5, {y}, 12.33, {h}, {fill});')
        self.js.append(f'label("{name}L", 0.7, {y + 0.03}, 6, {json.dumps(label)});')

    def box(self, name, x, y, w, h, kind, title, sub):
        self.js.append(f'step("{name}", {x}, {y}, {w}, {h}, {json.dumps(kind)}, {json.dumps(title)}, {json.dumps(sub)});')

    def text(self, name, x, y, w, h, lines, size=9.5, color="C.muted", align="left", valign="top", bold_first=False, italic=False):
        runs = []
        for i, t in enumerate(lines):
            bold = bold_first and i == 0
            runs.append(f'{{ text: {json.dumps(t)}, options: {{ fontSize: {size}, color: {color}, fontFace: B, bold: {str(bold).lower()}, italic: {str(italic).lower()}, breakLine: {str(i < len(lines) - 1).lower()} }} }}')
        self.js.append(f'add({{ name: "{name}", kind: "text", x: {x}, y: {y}, w: {w}, h: {h}, align: "{align}", valign: "{valign}", runs: [{", ".join(runs)}] }});')

    def cyl(self, name, x, y, w, h):
        self.js.append(f'ART["{name}"] = cylSvg(C.greenSoft, C.green); add({{ name: "{name}", kind: "image", x: {x}, y: {y}, w: {w}, h: {h} }});')

    def line(self, name, x, y, w, h, arrow=True, flipH=False, flipV=False, dash=False):
        o = [f"arrow: {str(arrow).lower()}"] + (["flipH: true"] if flipH else []) + (["flipV: true"] if flipV else []) + (['dash: "dash"'] if dash else [])
        self.js.append(f'line("{name}", {x}, {y}, {w}, {h}, {{ {", ".join(o)} }});')

    def click(self, caption, note, fx):
        n = len(self.slots) + 1
        self.js.append(f'caption("c{n}", {json.dumps(caption)});')
        pre = [f'FO("c{n - 1}")'] if n > 1 else []
        self.slots.append("{ hold: 0, fx: [" + ", ".join(pre + fx + [f'FI("c{n}", 300)']) + "] }")
        self.notes.append(note)

    def make(self, title, out):
        build(title, out, "\n".join(self.js), self.slots, self.notes)


FI = lambda n, d=0: f'FI("{n}", {d})'
WI = lambda n, dr="left", d=0, du=300: f'WI("{n}", "{dr}", {d}, {du})'

# ------------------------------------------------------------------ flow 1
s = Slide("PART 1  ·  FLOW 1", "From CMS data to a service.", "How the owner finds codes and policies",
          "All data shown is public CMS data. Every billing code keeps the CMS article it came from as its source.")
s.panel("P1", 1.45, 1.4, "C.provPanel", "WEEKLY REFRESH")
s.panel("P2", 2.95, 1.35, "C.payPanel", "THE OWNER CREATES A SERVICE")
s.panel("P3", 4.4, 1.8, "C.provPanel", "THE OWNER PICKS")

s.box("S_cms", 0.8, 1.82, 2.6, 0.88, "ext", "CMS Coverage API", "Public CMS data")
s.line("A1", 3.4, 2.26, 0.8, 0)
s.box("S_job", 4.2, 1.82, 2.4, 0.88, "code", "Refresh job", "Weekly. Changes only.")
s.line("A2", 6.6, 2.26, 0.8, 0)
s.cyl("Db", 7.4, 1.55, 2.2, 1.3)
s.text("DbT", 7.4, 1.85, 2.2, 0.95, ["Database", "cms_articles", "cms_article_codes", "cms_policies"], size=10, color="C.ink", align="center", valign="middle", bold_first=True)
s.text("E1", 9.9, 1.55, 2.8, 1.25, ["CMS API CALLS", "/reports/local-coverage-articles/", "/data/article/hcpc-code/", "/reports/national-coverage-ncd/", "/reports/local-coverage-final-lcds/", "/data/ncd/   /data/lcd/"], size=9, bold_first=True)

s.box("S_owner", 0.8, 3.32, 2.4, 0.88, "person", "Policy owner", "Creates a service")
s.line("A3", 3.2, 3.76, 1.0, 0)
s.box("S_app", 4.2, 3.32, 2.4, 0.88, "code", "App server", "Reads the database")
s.line("A4h", 6.6, 3.76, 1.9, 0, arrow=False)
s.line("A4v", 8.5, 2.86, 0, 0.9, flipV=True)
s.text("E2", 9.3, 3.28, 3.4, 1.0, ["APP ENDPOINTS", "POST /api/policies/services", "GET .../code-suggestions   .../code-consensus", "GET .../suggestions   (policies)", "POST .../codes/from-cms   .../policies"], size=9, bold_first=True)

s.line("F1", 5.4, 4.2, 0, 0.52, arrow=False)
s.line("F2", 2.3, 4.72, 3.4, 0, arrow=False)
s.line("F3", 2.3, 4.72, 0, 0.23)
s.line("F4", 5.7, 4.72, 0, 0.23)
s.box("S_codes", 0.8, 4.95, 3.0, 0.85, "code", "Billing codes", "Most articles it is found in")
s.box("S_pol", 4.2, 4.95, 3.0, 0.85, "code", "Policies", "Library first, then CMS")
s.line("M1", 2.3, 5.8, 0, 0.18, arrow=False)
s.line("M2", 2.3, 5.98, 6.4, 0, arrow=False)
s.line("M3", 5.7, 5.8, 0, 0.18, arrow=False)
s.line("M4", 8.7, 5.8, 0, 0.18, flipV=True)
s.box("S_sel", 7.6, 4.95, 2.2, 0.85, "person", "Owner selects", "Codes and a policy")
s.line("A5", 9.8, 5.375, 0.5, 0)
s.box("S_saved", 10.3, 4.95, 2.4, 0.85, "data", "Service saved", "A new library version")
s.text("N_new", 10.3, 5.86, 2.4, 0.3, ["A new policy goes to flow 2."], size=9.5, color="C.green", italic=True)

s.click("A weekly job calls the CMS Coverage API.",
        "It starts with CMS. A weekly job calls the CMS Coverage API for three things: the billing articles, the billing codes listed on each article, and the national and local coverage policies. These are the calls it makes. The API is public. The job gets a short-lived token first.",
        [FI("S_cms"), FI("E1", 200)])
s.click("It only fetches what is new or changed.",
        "The job compares version numbers with what we already stored, and fetches only what is new or changed. The first run takes a few minutes. After that, a weekly run is small. If a call fails, that item is tried again next run.",
        [WI("A1", "left", 100, 250), FI("S_job", 300)])
s.click("And saves it in our database. The owner never waits on CMS.",
        "It saves everything in our database: one table for articles, one for the billing codes on each article, one for the policies with their coverage text. This is why the owner never waits on the CMS website, and why it still works if CMS is down. It also lets us ask which articles list a given code.",
        [WI("A2", "left", 100, 250), FI("Db", 300), FI("DbT", 300)])
s.click("The owner creates a service. The app server reads the database.",
        "Now the owner creates a service, for example allergen immunotherapy. They give it a name and one sentence on what it covers. The app server reads the database. It never calls CMS while the owner waits. These are the endpoints the screens call.",
        [FI("S_owner"), WI("A3", "left", 150, 250), FI("S_app", 400), WI("A4h", "left", 700, 350), WI("A4v", "up", 1000, 300), FI("E2", 700)])
s.click("It shows billing codes, and policies that match.",
        "The app matches the service name to article titles and reads the codes from the database. We rank each code by how many articles it is found in. A code found in nine of nine articles is more likely to be right than one found in one. The app also suggests policies, from our library first and then from CMS. If a policy is already approved, the owner adds it in one click and nothing is read or reviewed again.",
        [WI("F1", "down", 100, 200), WI("F2", "left", 300, 300), WI("F3", "down", 600, 200), WI("F4", "down", 600, 200), FI("S_codes", 800), FI("S_pol", 800)])
s.click("The owner picks. The service is saved.",
        "The owner ticks the billing codes to use. Each code keeps the CMS article it came from as its source. They pick a policy. The service is saved as a new version of the library. If the policy is new, it goes to the build flow, which is the next slide.",
        [WI("M1", "down", 0, 150), WI("M3", "down", 0, 150), WI("M2", "right", 150, 450), WI("M4", "up", 600, 200), FI("S_sel", 700), WI("A5", "left", 900, 250), FI("S_saved", 1100), FI("N_new", 1200)])
s.make("From CMS data to a service", "Part1_Flow1_HLD")

# ------------------------------------------------------------------ flow 2
t = Slide("PART 1  ·  FLOW 2", "From a policy to approved rules.", "Parse, draft, validate, approve",
          "Policies shown are public Medicare policies. The AI drafts. It never publishes. A person approves every rule.")
t.panel("Q1", 1.45, 2.0, "C.provPanel", "READ AND DRAFT")
t.panel("Q2", 3.55, 2.0, "C.payPanel", "CHECK, APPROVE, SAVE")

t.box("T_src", 0.8, 1.85, 2.5, 0.9, "ext", "Policy source", "CMS, eCFR or a PDF")
t.line("B1", 3.3, 2.3, 0.7, 0)
t.box("T_unst", 4.0, 1.85, 2.7, 0.9, "etl", "Unstructured API", "Partitions the document")
t.text("D_unst", 4.0, 2.8, 2.7, 0.62, ["Uses a partitioner to parse the document and extract elements: title, text, page number. Output is JSON."], size=9.5)
t.line("B2", 6.7, 2.3, 0.7, 0)
t.box("T_llm", 7.4, 1.85, 2.7, 0.9, "ai", "Claude Sonnet", "Drafts the rules")
t.text("D_llm", 7.4, 2.8, 2.7, 0.62, ["Prompt: 10 rules. Fixed output form. Each rule has its exact quote, key fact and question."], size=9.5)
t.text("E3", 10.45, 1.8, 2.3, 1.55, ["API CALLS", "Unstructured:", "client.parse.run, elements", "Anthropic:", "messages.create, forced tool record_policy"], size=9, bold_first=True)

t.line("P1", 10.1, 2.3, 0.18, 0, arrow=False)
t.line("P2", 10.28, 2.3, 0, 1.2, arrow=False)
t.line("P3", 3.0, 3.5, 7.28, 0, arrow=False)
t.line("P4", 3.0, 3.5, 0, 0.45)
t.box("T_val", 0.8, 3.95, 2.5, 0.9, "code", "Validator", "Text matching, rule checks")
t.text("D_val", 0.8, 4.9, 2.5, 0.62, ["Finds the quote in the policy: exact, then fuzzy (88+) with the same numbers. Every number in a test is in its quote."], size=9.5)
t.line("B3", 3.3, 4.4, 0.7, 0)
t.box("T_own", 4.0, 3.95, 2.7, 0.9, "person", "Policy owner", "Approve, edit, reject")
t.text("D_own", 4.0, 4.9, 2.7, 0.62, ["Each rule beside its exact quote. Only approved rules are checked."], size=9.5)
t.line("B4", 6.7, 4.4, 0.7, 0)
t.cyl("Lib", 7.4, 3.75, 2.5, 1.35)
t.text("LibT", 7.4, 4.1, 2.5, 0.95, ["Policy library", "Rules and key facts", "Versions, audit trail"], size=10, color="C.ink", align="center", valign="middle", bold_first=True)
t.text("E4", 10.45, 3.9, 2.3, 1.5, ["APP ENDPOINTS", "POST /builds", "GET /builds/{id}", "POST /builds/{id}/criteria/{cid}", "POST /builds/{id}/publish"], size=9, bold_first=True)

t.js.append('add({ name: "KF", kind: "node", x: 0.5, y: 5.68, w: 12.33, h: 0.68, fill: C.greenSoft, line: C.green, lineW: 1.25, radius: 0.08, valign: "middle", margin: [0.05, 0.18, 0.05, 0.18], runs: [{ text: "KEY FACT   ", options: { bold: true, fontSize: 11, color: C.green, fontFace: B, charSpacing: 2 } }, { text: "One thing a nurse must find in a packet to apply a rule: a name and type, the exact policy sentence, and the question to ask the provider if it is missing.", options: { fontSize: 12.5, color: C.ink, fontFace: B } }] });')

t.click("The owner picks a policy: from CMS, eCFR, or a PDF.",
        "A policy needs to be built only if it is new. The source can be a CMS national or local policy, a federal regulation from eCFR, or the plan's own PDF. For CMS and eCFR the system fetches the full text. For a PDF the owner uploads it.",
        [FI("T_src")])
t.click("Unstructured parses it into elements, as JSON.",
        "Step one is the ETL. Unstructured uses a partitioner to parse the document and extract elements: the title, the text, the page number. It gives the output as JSON. We keep that structure because a rule hangs on a section, and flat text would lose it. A real element looks like this: type Title, text NCD 30.3.3 Acupuncture for Chronic Lower Back Pain, page 1.",
        [WI("B1", "left", 100, 250), FI("T_unst", 300), FI("D_unst", 700)])
t.click("Claude Sonnet drafts the rules, exact quotes, key facts and questions.",
        "The elements go to the language model, Claude Sonnet. It has a system prompt with 10 rules. For example: one condition per rule, copy the exact sentence the rule comes from, use a key fact we already know or propose a new one, and write the question to ask the provider if the fact is missing. It must answer through a fixed form, so the output is always structured. For each rule we get the rule in plain words, the exact quote, the key fact, the test, the question, and how confident the model is.",
        [WI("B2", "left", 100, 250), FI("T_llm", 300), FI("D_llm", 700), FI("E3", 700)])
t.click("Code checks every quote and number against the policy.",
        "The validator is code, with real algorithms. It never trusts the model's quote. It re-finds it. First it normalises both texts: lowercase, straight quotes, words split across lines rejoined. Then it searches for the quote on every page. If the exact text is not there, it tries a fuzzy match and needs at least 88 out of 100. A fuzzy match must carry the same numbers, or it is rejected, because a different number is a different rule. Then it checks that every number in the test appears in the quote, that the key fact exists, and it scans for requirement-sounding sentences that no rule covers. A rule that fails is shown to the owner. It is never dropped.",
        [WI("P1", "left", 0, 150), WI("P2", "down", 100, 300), WI("P3", "right", 350, 600), WI("P4", "down", 950, 250), FI("T_val", 1100), FI("D_val", 1300)])
t.click("The owner approves, edits or rejects each rule.",
        "Then the owner reviews. Each rule is shown beside the exact quote it came from, with its key fact and the question. They approve, edit or reject each one. Only approved rules are checked. If they reject the only rule that uses a key fact, that key fact is not checked and not asked for. The AI drafts. A person signs.",
        [WI("B3", "left", 100, 250), FI("T_own", 300), FI("D_own", 700)])
t.click("Approved rules and key facts are saved as a new version.",
        "The approved rules and key facts are saved on the policy, as a new version of the library. Every version is kept and can be rolled back, and every action is in the audit trail. A service shows the combined key facts of its policies. A policy approved once can be reused by any service that needs it.",
        [WI("B4", "left", 100, 250), FI("Lib", 300), FI("LibT", 300), FI("E4", 600)])
t.click("A key fact is what a nurse must find in a packet.",
        "A key fact is one thing a nurse must find in a packet to apply a rule. For a heart device it could be the ejection fraction, how long the patient has been on medicine, or whether a shared decision visit happened. It has a name and a type, the exact policy sentence behind it, and the question to ask the provider if the packet does not have it. It matters for four reasons. It turns a long policy into a short list the nurse can check. It tells the AI reader exactly what to look for in every packet, and nothing more. It gives the nurse one precise question to send when something is missing. And it ties every check to the policy's own words, which is the audit trail.",
        [FI("KF")])
t.make("From a policy to approved rules", "Part1_Flow2_HLD")
