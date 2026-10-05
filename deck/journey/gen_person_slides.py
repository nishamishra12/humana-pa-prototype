"""Generates the overview slide and the four person slides (click by click, with captions), in the same style as the other flow slides.
Run from deck/journey with NODE_PATH pointing at a folder that has @resvg/resvg-js:   python gen_person_slides.py
Writes build_ps_*.js and runs each one. Output: Two_Parts_Overview.pptx, Person_Policy_Owner.pptx, Person_Intake.pptx, Person_Nurse.pptx, Person_Director.pptx
"""
import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
fr = open(os.path.join(HERE, "build_friction.js"), encoding="utf-8").read().split("\n")
ART_PRE = "\n".join(fr[20:40])  # SKIN, person(), building, faxIcon
ENGINE = "\n".join(fr[[k for k, l in enumerate(fr) if l.startswith("const ANIMATED")][0]:])

HEAD = r'''const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");
const JSZip = require("jszip");
const { Resvg } = require("@resvg/resvg-js");
const OUT = path.join(__dirname, "__OUT__.pptx");
const OUT_STEPS = path.join(__dirname, "__OUT___Steps.pptx");
const C = { ink: "16211E", muted: "5C6B66", green: "1F6F5C", greenSoft: "E3F0EB", line: "CBD5D1", coral: "B8452F", coralSoft: "FBE9E4", amber: "8A5A00", amberSoft: "FCEFD0", purple: "5F3AA8", purpleSoft: "EBE2F8", ok: "18764A", okSoft: "DDF3E7", white: "FFFFFF", provPanel: "F5F3EE", payPanel: "EEF5F2" };
const H = "Cambria", B = "Calibri";
'''

COMMON = r'''
const disc = (bg, glyph) => `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="48" fill="#${bg}"/>${glyph}</svg>`;
const SPARK = `<path d="M50 20 L57 43 L80 50 L57 57 L50 80 L43 57 L20 50 L43 43Z" fill="#5F3AA8"/><circle cx="74" cy="26" r="5" fill="#5F3AA8"/>`;
const PEOPLE = {
  owner: person({ bg: "E3D9F5", skin: SKIN.b, hair: "2B2B2B", style: "bun", top: "6B4C9A", acc: "clip" }),
  intake: person({ bg: "D8EAE3", skin: SKIN.a, hair: "6B4226", style: "bun", top: "3C6E8F", acc: "clip" }),
  nurse: person({ bg: "CDE8E0", skin: SKIN.c, hair: "2B2B2B", style: "short", top: "2F8F83", acc: "nurse" }),
  md: person({ bg: "E3D9F5", skin: SKIN.d, hair: "4A3B32", style: "short", top: "5F3AA8", coat: true, acc: "doctor" }),
  ai: disc("EBE2F8", SPARK),
};
const items = [];
const add = (o) => items.push(o);
const KIND = {
  person: { fill: C.amberSoft, line: C.amber, tag: "PERSON", tc: C.amber },
  etl: { fill: C.coralSoft, line: C.coral, tag: "ETL + AI", tc: C.coral },
  ai: { fill: C.purpleSoft, line: C.purple, tag: "AI", tc: C.purple },
  code: { fill: C.greenSoft, line: C.green, tag: "CODE", tc: C.green },
  data: { fill: C.greenSoft, line: C.green, tag: "CODE + DATA", tc: C.green },
  ext: { fill: C.white, line: C.line, tag: "INPUT", tc: C.muted },
};
const frame = (eyebrow, title, sub, footer) => {
  add({ name: "eyebrow", kind: "text", static: true, x: 0.5, y: 0.3, w: 7, h: 0.28, runs: [{ text: eyebrow, options: { bold: true, fontSize: 11, color: C.green, fontFace: B, charSpacing: 3 } }] });
  add({ name: "title", kind: "text", static: true, x: 0.5, y: 0.55, w: 8.8, h: 0.75, valign: "middle", runs: [{ text: title, options: { fontSize: 26, color: C.ink, fontFace: H } }] });
  add({ name: "sub", kind: "text", static: true, x: 9.2, y: 0.55, w: 3.63, h: 0.75, align: "right", valign: "middle", runs: [{ text: sub, options: { fontSize: 14, color: C.muted, fontFace: B } }] });
  add({ name: "footer", kind: "text", static: true, x: 0.5, y: 7.1, w: 12.33, h: 0.25, runs: [{ text: footer, options: { fontSize: 9, color: C.muted, fontFace: B } }] });
};
const panel = (name, x, y, w, h, fill) => add({ name, kind: "node", static: true, x, y, w, h, fill, line: C.line, lineW: 1, radius: 0.1, runs: [{ text: " ", options: { fontSize: 8 } }] });
const label = (name, x, y, w, t, sub) => add({ name, kind: "text", static: true, x, y, w, h: 0.5, runs: [{ text: t, options: { bold: true, fontSize: 11, color: C.ink, fontFace: B, charSpacing: 2, breakLine: !!sub } }, ...(sub ? [{ text: sub, options: { fontSize: 10, color: C.muted, fontFace: B } }] : [])] });
const avatar = (name, x, y, size) => add({ name, kind: "image", x, y, w: size, h: size });
const step = (name, x, y, w, h, kind, title, sub) => {
  const k = KIND[kind];
  add({ name, kind: "node", x, y, w, h, fill: k.fill, line: k.line, lineW: 1.25, radius: 0.1, valign: "top", margin: [0.22, 0.1, 0.05, 0.1],
    runs: [{ text: k.tag, options: { bold: true, fontSize: 8.5, color: k.tc, fontFace: B, charSpacing: 1.5, breakLine: true } }, { text: title, options: { bold: true, fontSize: 12.5, color: C.ink, fontFace: B, breakLine: !!sub } }, ...(sub ? [{ text: sub, options: { fontSize: 10, color: C.muted, fontFace: B } }] : [])] });
};
const badge = (name, n, cx, cy) => add({ name, kind: "node", x: cx - 0.16, y: cy - 0.16, w: 0.32, h: 0.32, fill: C.green, line: C.green, lineW: 1, radius: 0.16, align: "center", margin: [0, 0, 0, 0], runs: [{ text: String(n), options: { bold: true, fontSize: 11, color: C.white, fontFace: B } }] });
const line = (name, x, y, w, h, o = {}) => add({ name, kind: "line", x, y, w, h, line: C.muted, lineW: 1.75, arrow: true, ...o });
const caption = (name, text) => add({ name, kind: "text", x: 0.5, y: 6.5, w: 12.33, h: 0.65, valign: "middle", runs: [{ text, options: { fontSize: 16, color: C.ink, fontFace: B } }] });
const FI = (name, delay = 0, dur = 500) => ({ t: "fadeIn", name, delay, dur });
const FO = (name, delay = 0, dur = 300) => ({ t: "fadeOut", name, delay, dur });
const WI = (name, dir, delay = 0, dur = 600) => ({ t: "wipeIn", name, dir, delay, dur });
const ART = Object.fromEntries(Object.entries(PEOPLE).map(([k, v]) => ["Av_" + k, v]));
'''

# ---------------------------------------------------------------- the person slides
def person_slide(spec):
    lanes = spec["lanes"]  # [(key, label, sub)] top lane then bottom lane
    steps = spec["steps"]
    n = len(steps)
    g = 0.27
    w = min(2.0, (12.0 - (n - 1) * g) / n)
    x0 = 0.66 + (12.0 - (n * w + (n - 1) * g)) / 2
    LY = [1.5, 3.75]
    BY = [LY[0] + 0.7, LY[1] + 0.7]
    BH = 1.35
    js = [f'frame({json.dumps(spec["eyebrow"])}, {json.dumps(spec["title"])}, {json.dumps(spec["sub"])}, {json.dumps(spec["footer"])});']
    for i, (key, lab, sub) in enumerate(lanes):
        js.append(f'panel("Lane{i}", 0.5, {LY[i]}, 12.33, 2.15, {"C.provPanel" if i == 0 else "C.payPanel"});')
        js.append(f'avatar("Av_{key}", 0.62, {LY[i] + 0.1}, 0.45); label("LaneLb{i}", 1.17, {LY[i] + 0.12}, 5, {json.dumps(lab)}, {json.dumps(sub)});')
        # the lane avatars are static, so they are not part of the animation
    slots, caps, notes = [], [], []
    for i, st in enumerate(steps):
        x = x0 + i * (w + g)
        lane = st["lane"]
        cy = BY[lane] + BH / 2
        js.append(f'step("S{i}", {x:.3f}, {BY[lane]}, {w:.3f}, {BH}, {json.dumps(st["kind"])}, {json.dumps(st["title"])}, {json.dumps(st["sub"])}); badge("B{i}", {i + 1}, {x + 0.17:.3f}, {BY[lane]});')
        fx = []
        if i:
            pl = steps[i - 1]["lane"]
            px = x0 + (i - 1) * (w + g) + w
            pcy = BY[pl] + BH / 2
            if pl == lane:
                js.append(f'line("A{i}a", {px + 0.02:.3f}, {cy}, {g - 0.04:.3f}, 0);')
                fx.append('WI("A%da", "left", 200, 300)' % i)
            else:
                xm = px + g / 2
                top, bot = min(pcy, cy), max(pcy, cy)
                js.append(f'line("A{i}a", {px + 0.02:.3f}, {pcy}, {g / 2 - 0.02:.3f}, 0, {{ arrow: false }}); line("A{i}b", {xm:.3f}, {top}, 0, {bot - top}, {{ arrow: false }}); line("A{i}c", {xm:.3f}, {cy}, {g / 2 - 0.02:.3f}, 0);')
                fx += ['WI("A%da", "left", 150, 200)' % i, 'WI("A%db", "%s", 350, 450)' % (i, "down" if cy > pcy else "up"), 'WI("A%dc", "left", 800, 200)' % i]
        js.append(f'caption("c{i + 1}", {json.dumps(st["caption"])});')
        pre = [f'FO("c{i}")'] if i else []
        slots.append("{ hold: 0, fx: [" + ", ".join(pre + fx + [f'FI("S{i}", 600)', f'FI("B{i}", 600)', f'FI("c{i + 1}", 300)']) + "] }")
        notes.append(st["note"])
    if spec.get("result"):
        js.append(f'caption("c{n + 1}", {json.dumps(spec["result"])});')
        slots.append("{ hold: 0, fx: [" + f'FO("c{n}"), FI("c{n + 1}", 300)' + "] }")
        notes.append(spec["result_note"])
    return "\n".join(js), slots, notes


def lanes_slide(spec):
    """Overview: two rows, each left to right. One click per row."""
    js = [f'frame({json.dumps(spec["eyebrow"])}, {json.dumps(spec["title"])}, {json.dumps(spec["sub"])}, {json.dumps(spec["footer"])});']
    slots, notes = [], []
    LY = [1.5, 4.1]
    for r, lane in enumerate(spec["rows"]):
        n = len(lane["steps"])
        g = 0.22
        x0, w = 3.35, (12.6 - 3.35 - (n - 1) * g) / n
        y = LY[r]
        names = []
        js.append(f'panel("P{r}", 0.5, {y}, 12.33, 2.0, {"C.provPanel" if r == 0 else "C.payPanel"});')
        js.append(f'label("PL{r}", 0.75, {y + 0.25}, 2.5, {json.dumps(lane["label"])}, {json.dumps(lane["sub"])});')
        js.append(f'add({{ name: "PT{r}", kind: "text", static: true, x: 0.75, y: {y + 0.95}, w: 2.4, h: 0.9, runs: [{{ text: {json.dumps(lane["human"])}, options: {{ italic: true, fontSize: 11, color: C.muted, fontFace: B }} }}] }});')
        for i, st in enumerate(lane["steps"]):
            x = x0 + i * (w + g)
            js.append(f'step("R{r}S{i}", {x:.3f}, {y + 0.3}, {w:.3f}, 1.4, {json.dumps(st["kind"])}, {json.dumps(st["title"])}, {json.dumps(st["sub"])});')
            names.append(f'FI("R{r}S{i}", {i * 150})')
            if i:
                js.append(f'line("R{r}A{i}", {x - g + 0.02:.3f}, {y + 1.0}, {g - 0.04:.3f}, 0);')
                names.append(f'WI("R{r}A{i}", "left", {i * 150 + 100}, 250)')
        names.append(f'FI("RC{r}", 300)')
        js.append(f'caption("RC{r}", {json.dumps(lane["caption"])});')
        pre = ([f'FO("RC{r - 1}")'] if r else [])
        slots.append("{ hold: 0, fx: [" + ", ".join(pre + names) + "] }")
        notes.append(lane["note"])
        if r == 0:
            js.append(f'line("Link", 6.67, 3.5, 0, 0.58); add({{ name: "LinkLb", kind: "text", x: 6.95, y: 3.58, w: 5.5, h: 0.4, valign: "middle", runs: [{{ text: {json.dumps(spec["link"])}, options: {{ bold: true, fontSize: 12, color: C.green, fontFace: B }} }}] }});')
            slots.append('{ hold: 0, fx: [FO("RC0"), WI("Link", "down", 200, 300), FI("LinkLb", 400), FI("RCL", 300)] }')
            js.append(f'caption("RCL", {json.dumps(spec["link_caption"])});')
            notes.append(spec["link_note"])
            # the second row follows the link click
            slots[-1] = slots[-1]
    # fix the order of fades: row 2 fades the link caption
    slots[2] = slots[2].replace('FO("RC0")', 'FO("RCL")')
    return "\n".join(js), slots, notes


def build(name, out, js_items, slots, notes, ai_icon=True):
    body = COMMON + "\n" + js_items + "\n"
    body += "const slots = [\n  " + ",\n  ".join(slots) + ",\n];\n"
    body += "const STEP_NOTES = " + json.dumps(notes, indent=1) + ";\nconst NOTES = \"\";\nconst OUT_STEPS_UNUSED = true;\n"
    # people art is rendered as PNG by the engine; the lane avatars are images
    body = body.replace("const items = [];", "const items = [];")
    src = HEAD.replace("__OUT___Steps", out + "_Steps").replace("__OUT__", out) + ART_PRE + "\n" + body + ENGINE
    src = src.replace('pres.title = "The friction points";', f'pres.title = {json.dumps(name)};')
    src = src.replace("One slide. Click once per friction point. Finish your talking point, then click.", "One slide. One click per step. Finish your talking point, then click.")
    src = src.replace('path.join(__dirname, "preview.html")', f'path.join(__dirname, "preview_{out}.html")')
    src = src.replace("path.join(__dirname, `preview_s${k}.html`)", f'path.join(__dirname, `{out}_s${{k}}.html`)')
    path = os.path.join(HERE, "build_ps_" + out + ".js")
    open(path, "w", encoding="utf-8", newline="\n").write(src)
    r = subprocess.run(["node", path], capture_output=True, text=True, cwd=HERE)
    print(r.stdout.strip() or r.stderr.strip()[:400])


FOOT = "All patient data is made up. The AI reads, drafts and cites. A person decides."

OWNER = dict(
    eyebrow="THE POLICY OWNER  ·  PART 1", title="The policy owner builds the library.", sub="Before go-live. The biggest piece of work.", footer="Policies shown are public Medicare policies. The AI drafts. It never publishes. Every code is stored with its source.",
    lanes=[("owner", "POLICY OWNER", "A person"), ("ai", "PA DESK", "ETL + AI, and plain code")],
    steps=[
        dict(lane=0, kind="person", title="Picks the policy", sub="A CMS policy, or the plan's own PDF", caption="The owner starts by choosing a policy for a procedure we want to cover.", note="The policy owner starts by choosing a policy for a procedure we want to cover. It can be a CMS national or local policy, picked from a list, or the plan's own PDF."),
        dict(lane=0, kind="person", title="Adds the billing codes", sub="Each code, with its source", caption="Along with the billing codes that tell us when this policy applies. Each code keeps its source.", note="Along with the policy, the owner adds the billing codes that identify the procedure. A code is the short code on every request that names the procedure. Each code is stored with its source, a CMS billing article. This is how a packet will find this policy later."),
        dict(lane=1, kind="etl", title="Reads the policy", sub="Titles, paragraphs, tables and pages", caption="The ETL step with AI inside reads the policy and keeps its structure.", note="The ETL step with AI inside reads the policy. It keeps the structure: titles, paragraphs, tables and the page each came from. Flat text would lose the sections the rules hang on."),
        dict(lane=1, kind="ai", title="Drafts the key facts", sub="A rule for each, with its source sentence", caption="The AI turns each requirement into a rule, and names the fact a nurse must check.", note="The AI turns each requirement into a rule. For each rule it names the key fact a nurse must check, for example the ejection fraction, and copies the exact sentence the rule came from. That list of key facts is what we later look for in every packet for this procedure."),
        dict(lane=1, kind="code", title="Checks the draft", sub="Every quote, number and fact", caption="Plain code checks the draft. Anything that fails goes to the owner. It is never dropped.", note="Plain code checks the draft. Is the quote really in the policy? Is every number in the quote? Does the fact exist? Anything that fails is shown to the owner, never dropped. No AI in this step."),
        dict(lane=0, kind="person", title="Reviews every rule", sub="Approve, edit or reject", caption="The owner reads each rule beside the official text. The AI drafts. A person signs.", note="The owner reads each rule with the official text beside it. They approve, edit or reject every one. The AI drafts. It never publishes. A person signs."),
        dict(lane=0, kind="person", title="Links and publishes", sub="Codes to a service. A versioned library", caption="They link the codes to a service and publish. Every version is kept and can be rolled back.", note="Then the owner links the codes and the policy to a service, which is any name the business uses for a kind of request, like ICD for heart failure. They publish a version. Every version is kept, so it can be rolled back, and every action is in an audit trail."),
    ],
    result="The result: for every procedure we cover, the key facts to check when a packet arrives.",
    result_note="The result of part one: for every procedure we cover, a library of key facts to check when a packet arrives. This is the biggest piece of real work, and it happens before go-live. It is what the AI uses in part two.",
)

INTAKE = dict(
    eyebrow="THE INTAKE COORDINATOR  ·  PART 2", title="The intake coordinator checks and assigns.", sub="The first person to touch a packet", footer=FOOT,
    lanes=[("intake", "INTAKE COORDINATOR", "A person"), ("ai", "PA DESK", "ETL + AI, and plain code")],
    steps=[
        dict(lane=0, kind="person", title="Uploads the packet", sub="One PDF per request", caption="A provider sends the packet. The intake coordinator uploads it as one PDF.", note="A provider sends the request packet by fax or portal. The intake coordinator uploads it as one PDF. Nothing about this step changes from today."),
        dict(lane=1, kind="etl", title="Reads it", sub="And finds the procedure code", caption="The ETL step reads every page, and the procedure code on the request is found.", note="The ETL step with AI inside reads every page and keeps typed pieces with their positions. Then plain pattern matching finds the procedure code on the request form."),
        dict(lane=1, kind="code", title="Shows what it found", sub="Member, code, planned date. Or 'No policy yet'", caption="It shows what it found. If no policy covers that code, it says 'No policy yet'.", note="The screen shows what it found: the member, the procedure code, the planned date and the number of pages. If no service uses that code, the case is flagged No policy yet. Nothing is guessed."),
        dict(lane=0, kind="person", title="Checks the packet", sub="Right member? Readable? Covered?", caption="The intake coordinator checks the packet. This is a paperwork check, not a clinical one.", note="The intake coordinator checks the packet. Is it the right member, is it readable, is it a procedure we cover. This is a paperwork check, not a clinical one."),
        dict(lane=0, kind="person", title="Opens the team view", sub="Each nurse's cases and deadlines", caption="They see each nurse's schedule: open cases, which are at risk, and which are close to the deadline.", note="Then they open the team view. They see each nurse's workload: how many open cases, how many are at risk, and which are close to their CMS deadline. That is how they decide who should take the next packet."),
        dict(lane=0, kind="person", title="Assigns a nurse", sub="The nurse is told. The clock runs.", caption="They assign the packet to a nurse. The nurse is notified, and the CMS clock is tracked.", note="They assign the packet to a nurse. The nurse is notified. The CMS clock is tracked from the day the packet arrived."),
    ],
    result="Intake owns who reviews it. They never judge the clinical content.",
    result_note="Intake owns who reviews the packet. They do not judge the clinical content. That is the nurse's job, with the AI's help.",
)

NURSE = dict(
    eyebrow="THE UM NURSE  ·  PART 2", title="The nurse has less to read.", sub="The star player, with the AI beside them", footer=FOOT,
    lanes=[("nurse", "UM NURSE", "A person"), ("ai", "PA DESK", "AI, and plain code")],
    steps=[
        dict(lane=1, kind="ai", title="Compares the packet", sub="With the key facts for this procedure", caption="When a packet arrives, the AI compares it with the key facts for the policies linked to this procedure.", note="When the packet arrives, the AI compares it with the key facts from the library, for the policies that mention this procedure. It reads the packet three times and the answers must agree. If it cannot tell, it says so."),
        dict(lane=1, kind="code", title="Finds the evidence", sub="The page and exact sentence for each fact", caption="For every fact it shows the page and the exact sentence it relied on.", note="For every fact, plain code finds the quoted sentence on its page, and a second AI checks that the sentence supports the claim. The nurse sees the real text from the page, not the AI's version."),
        dict(lane=1, kind="code", title="Recommends", sub="Approve, pend with an exact question, or escalate", caption="Then it recommends: approve, pend with the exact question to ask, or escalate to the director.", note="Then it recommends. Approve, when every fact is there and every rule is met. Pend, with the exact question to ask the provider, when something is missing. Or escalate to the director when a rule is not met. There is no deny."),
        dict(lane=0, kind="person", title="Reviews the checklist", sub="Evidence beside every item", caption="The nurse reviews a checklist with the evidence beside each item.", note="The nurse reviews a checklist with the evidence beside every item. They are reviewing, not hunting through fourteen pages."),
        dict(lane=0, kind="person", title="Decides", sub="Approve. Send the question. Or escalate.", caption="They decide. They can follow the recommendation or override it.", note="The nurse decides. They can follow the recommendation, or override it. If they approve against the recommendation, that is recorded."),
        dict(lane=1, kind="code", title="If pended", sub="The reply is checked again", caption="If pended, the provider replies and the packet is checked again, and it returns to the nurse.", note="If the nurse pends, the provider gets one precise question. When the provider replies, the packet is read again and returns to the nurse."),
        dict(lane=1, kind="code", title="If escalated", sub="To the director, with the evidence", caption="If escalated, it goes to the medical director with the evidence attached.", note="If the nurse escalates, the case goes to the medical director with the evidence attached and the nurse's note."),
    ],
    result="The nurse owns the recommendation. The AI never decides.",
    result_note="The nurse owns the recommendation. The AI reads, compares and cites. It never decides.",
)

DIRECTOR = dict(
    eyebrow="THE MEDICAL DIRECTOR  ·  PART 2", title="The director decides the hard cases.", sub="The only person who can deny", footer=FOOT,
    lanes=[("md", "MEDICAL DIRECTOR", "A person"), ("ai", "PA DESK", "Plain code")],
    steps=[
        dict(lane=1, kind="code", title="The case arrives", sub="With the evidence and the nurse's note", caption="The case arrives in the director's queue, sorted by the clock, with the evidence and the nurse's note.", note="The case arrives in the director's queue, sorted by the clock, with the evidence and the nurse's note already attached."),
        dict(lane=0, kind="person", title="Reads the evidence", sub="Which rules are not met, and the page behind each", caption="The director reads which rules were not met, and the page behind each one.", note="The director reads which rules were not met, and the page and sentence behind each one."),
        dict(lane=0, kind="person", title="Decides", sub="Approve. Deny with a reason. Or send back.", caption="They decide. Approve. Deny, with a written reason. Or send it back to the nurse, with a reason.", note="They decide. They can approve. They can deny, and a denial needs a written reason. Or they can send the case back to the nurse, with a reason. Only a medical director can deny."),
        dict(lane=1, kind="code", title="Records it", sub="The decision, the reason, who decided", caption="The decision, the reason and who decided are recorded in the audit trail.", note="The decision, the reason and who made it are recorded in the audit trail."),
        dict(lane=1, kind="code", title="Closes or returns", sub="Back to the nurse if sent back", caption="The case closes, or returns to the nurse if it was sent back.", note="The case closes. If it was sent back, it returns to the nurse's queue with the director's reason."),
    ],
    result="The director owns any denial. Only they can deny.",
    result_note="The director owns any denial. Only a medical director can deny, and they write the reason.",
)

OVERVIEW = dict(
    eyebrow="THE SOLUTION", title="The solution has two parts.", sub="A person is in the loop in both", footer="The AI drafts, reads and cites. A person approves, confirms and decides. The AI never denies.",
    rows=[
        dict(label="PART 1", sub="Before go-live. The biggest piece of work.", human="A person in the loop: the policy owner approves every rule.", caption="Part one builds the library: the policies and billing codes we cover, and the key facts to check for each. The policy owner approves every rule.", note="The solution has two parts. Part one is the library, and it is the biggest piece of real work. It happens before go-live. We pass in the policies for the procedures we want to cover, along with their billing codes. The ETL step with AI inside reads them, and the AI drafts the key facts to check for each procedure. A policy owner approves every rule. The human in the loop in part one is the policy owner.",
             steps=[dict(kind="ext", title="Policies and billing codes", sub="The procedures we cover"), dict(kind="etl", title="ETL + AI reads them", sub="Keeps the structure"), dict(kind="ai", title="AI drafts the key facts", sub="And a rule for each"), dict(kind="person", title="Policy owner approves", sub="Every rule. A person signs."), dict(kind="data", title="The library", sub="Versioned. Linked to a service.")]),
        dict(label="PART 2", sub="Every packet.", human="People in the loop: intake assigns, the nurse confirms, the director decides.", caption="Part two reads every packet with that library. Intake assigns, the AI compares and recommends, the nurse confirms, and the director decides the hard cases.", note="Part two is the daily work. When a packet arrives, the intake coordinator checks it and assigns it to a nurse. The ETL step reads it, and the AI compares it with the key facts from the library for this procedure. It suggests approve, pend with an exact question, or escalate. The nurse confirms, and the director decides the hard cases. The humans in the loop in part two are the intake coordinator, the nurse and the director.",
             steps=[dict(kind="person", title="Intake coordinator", sub="Checks the packet. Assigns a nurse."), dict(kind="etl", title="ETL + AI reads it", sub="Typed pieces with positions"), dict(kind="ai", title="AI compares it", sub="With the key facts, and recommends"), dict(kind="person", title="UM nurse confirms", sub="Approve, pend with one question, or escalate"), dict(kind="person", title="Medical director", sub="Decides the hard cases. Only they can deny.")]),
    ],
    link="Part 2 only uses what Part 1 approved", link_caption="The link between them is simple. Part two only uses what part one approved.", link_note="The link between the two is simple. Part two only ever uses what part one approved. The rules the nurse sees are never made up when a case arrives.",
)

if __name__ == "__main__":
    js, slots, notes = lanes_slide(OVERVIEW)
    # the last click: the closing line
    js += '\ncaption("RCZ", "A person is in the loop in both parts. The AI never decides.");'
    slots.append('{ hold: 0, fx: [FO("RC1"), FI("RCZ", 300)] }')
    notes.append("The point to land: a person is in the loop in both parts. In part one, the policy owner approves every rule. In part two, a nurse confirms every recommendation and a director decides the hard cases. The AI never decides.")
    build("The solution has two parts", "Two_Parts_Overview", js, slots, notes)
    for spec, out, nm in ((OWNER, "Person_Policy_Owner", "The policy owner"), (INTAKE, "Person_Intake", "The intake coordinator"), (NURSE, "Person_Nurse", "The UM nurse"), (DIRECTOR, "Person_Director", "The medical director")):
        js, slots, notes = person_slide(spec)
        build(nm, out, js, slots, notes)
