"""Part 1 on ONE static slide, drawn as an architecture diagram in the style of a cloud reference architecture:
people and outside systems on the left, dashed regions for each stage, an icon with a label for every component,
labelled connectors, and the two databases drawn as database icons. No animation and no transition.
Run from deck/journey with NODE_PATH pointing at a folder that has @resvg/resvg-js:   python gen_part1_onepage.py
Output: Part1_One_Page.pptx
"""
import json, os, re, sys, zipfile, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen_person_slides as G

# the shared engine, with two small additions: a dashed ring, and notes taken as written
G.ENGINE = G.ENGINE.replace('fill: { type: "none" }, line: { color: o.line, width: o.lineW }, objectName: o.name });',
                            'fill: { type: "none" }, line: { color: o.line, width: o.lineW, dashType: o.dash || "solid" }, objectName: o.name });')
G.ENGINE = G.ENGINE.replace('border:${o.lineW}px solid #${o.line};border-radius:10px;box-sizing:border-box', 'border:${o.lineW}px ${o.dash ? "dashed" : "solid"} #${o.line};border-radius:10px;box-sizing:border-box')
G.ENGINE = G.ENGINE.replace('["One slide. Click once per friction point. Finish your talking point, then click."].concat(STEP_NOTES.map((t, i) => "Click " + (i + 1) + ": " + t)).join(String.fromCharCode(10, 10))', 'STEP_NOTES.join(String.fromCharCode(10, 10))')

JS = r'''
const tile = (glyph, fill, stroke) => `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect x="3" y="3" width="94" height="94" rx="16" fill="#${fill}" stroke="#${stroke}" stroke-width="3"/>${glyph.replace(/STROKE/g, "#" + stroke)}</svg>`;
const GLY = {
  cloud: `<path d="M30 68 C14 68 12 46 30 44 C30 26 56 22 64 38 C82 36 90 56 72 68 Z" fill="none" stroke="STROKE" stroke-width="4.5" stroke-linejoin="round"/>`,
  clock: `<circle cx="50" cy="55" r="25" fill="none" stroke="STROKE" stroke-width="4.5"/><path d="M50 38 V55 L62 62" fill="none" stroke="STROKE" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M30 24 L40 31 M70 24 L60 31" stroke="STROKE" stroke-width="4.5" stroke-linecap="round"/>`,
  screen: `<rect x="20" y="26" width="60" height="40" rx="4" fill="none" stroke="STROKE" stroke-width="4.5"/><path d="M38 78 H62 M50 66 V78" stroke="STROKE" stroke-width="4.5" stroke-linecap="round"/><path d="M30 40 H54 M30 50 H46" stroke="STROKE" stroke-width="3.5" stroke-linecap="round"/>`,
  server: `<rect x="22" y="24" width="56" height="22" rx="4" fill="none" stroke="STROKE" stroke-width="4.5"/><rect x="22" y="54" width="56" height="22" rx="4" fill="none" stroke="STROKE" stroke-width="4.5"/><circle cx="34" cy="35" r="3.5" fill="STROKE"/><circle cx="34" cy="65" r="3.5" fill="STROKE"/><path d="M48 35 H66 M48 65 H66" stroke="STROKE" stroke-width="3.5" stroke-linecap="round"/>`,
  doc: `<path d="M32 20 H58 L72 34 V80 H32 Z" fill="none" stroke="STROKE" stroke-width="4.5" stroke-linejoin="round"/><path d="M58 20 V34 H72" fill="none" stroke="STROKE" stroke-width="4.5" stroke-linejoin="round"/><path d="M40 50 H64 M40 60 H64 M40 70 H54" stroke="STROKE" stroke-width="3.5" stroke-linecap="round"/>`,
  parts: `<rect x="24" y="22" width="52" height="14" rx="3" fill="STROKE"/><rect x="24" y="42" width="24" height="16" rx="3" fill="none" stroke="STROKE" stroke-width="4"/><rect x="52" y="42" width="24" height="16" rx="3" fill="none" stroke="STROKE" stroke-width="4"/><rect x="24" y="64" width="52" height="14" rx="3" fill="none" stroke="STROKE" stroke-width="4"/>`,
  spark: `<path d="M50 18 L58 42 L82 50 L58 58 L50 82 L42 58 L18 50 L42 42Z" fill="STROKE"/><circle cx="76" cy="24" r="5.5" fill="STROKE"/>`,
  shield: `<path d="M50 20 L76 30 V52 C76 68 64 78 50 84 C36 78 24 68 24 52 V30 Z" fill="none" stroke="STROKE" stroke-width="4.5" stroke-linejoin="round"/><path d="M37 52 L47 62 L64 42" fill="none" stroke="STROKE" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>`,
};
const cylSvg = (f, s) => `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 220 170"><path d="M6 28 V138 A104 26 0 0 0 214 138 V28" fill="#${f}" stroke="#${s}" stroke-width="4"/><ellipse cx="110" cy="28" rx="104" ry="24" fill="#${f}" stroke="#${s}" stroke-width="4"/><path d="M6 66 A104 26 0 0 0 214 66 M6 102 A104 26 0 0 0 214 102" fill="none" stroke="#${s}" stroke-width="3"/></svg>`;
const SOFT = { ext: [C.white, "5C6B66"], code: [C.greenSoft, C.green], etl: [C.coralSoft, C.coral], ai: [C.purpleSoft, C.purple], person: [C.amberSoft, C.amber] };
const icon = (name, cx, cy, glyph, kind, s = 0.8) => { const [f, st] = SOFT[kind]; ART[name] = tile(GLY[glyph], f, st); add({ name, kind: "image", static: true, x: cx - s / 2, y: cy - s / 2, w: s, h: s }); };
const db = (name, cx, cy, w = 1.0, h = 0.78) => { ART[name] = cylSvg(C.greenSoft, C.green); add({ name, kind: "image", static: true, x: cx - w / 2, y: cy - h / 2, w, h }); };
const who = (name, cx, cy, s = 0.8) => { ART[name] = PEOPLE.owner; add({ name, kind: "image", static: true, x: cx - s / 2, y: cy - s / 2, w: s, h: s }); };
const ring = (name, x, y, w, h, color) => add({ name, kind: "ring", static: true, x, y, w, h, line: color, lineW: 1.25, dash: "dash" });
const txt = (name, x, y, w, h, lines, o = {}) => add({ name, kind: "text", static: true, x, y, w, h, align: o.align || "left", valign: o.valign || "top",
  runs: lines.map((t, i) => ({ text: t, options: { fontSize: (i === 0 && o.title) ? o.title : (o.size || 9), color: (i === 0 && o.title) ? C.ink : (o.color || C.muted), fontFace: B, bold: (i === 0 && !!o.title) || !!o.bold, italic: !!o.italic, breakLine: i < lines.length - 1 } })) });
const cap = (name, cx, y, title, lines, w = 1.8) => txt(name, cx - w / 2, y, w, 0.9, [title, ...lines], { align: "center", title: 10.5, size: 8.5 });
const seg = (name, x1, y1, x2, y2, arrow, color, dash) => add({ name, kind: "line", static: true, x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.abs(x2 - x1), h: Math.abs(y2 - y1), flipH: x2 < x1, flipV: y2 < y1, line: color || C.ink, lineW: 1.5, arrow: !!arrow, dash: dash ? "dash" : undefined });
const rl = (name, xr, t, y) => txt(name, xr - 7, y, 7, 0.25, [t], { size: 11, color: C.ink, bold: true, align: "right" });
const tag = (name, x, y, w, t, align) => txt(name, x, y, w, 0.2, [t], { size: 9, color: C.green, bold: true, align: align || "center" });

frame("PART 1  ·  ARCHITECTURE", "Part 1 builds the policy library.", "Before go-live. The biggest piece of work.",
  "Billing codes and policies come from public CMS data. The AI drafts. A person approves every rule. Every billing code keeps its CMS article as its source.");

ring("R1", 1.9, 1.4, 11.0, 1.55, C.green);  rl("R1L", 12.8, "1   WEEKLY REFRESH", 1.44);
ring("R2", 1.9, 3.05, 11.0, 1.55, C.amber);  rl("R2L", 12.8, "2   THE OWNER CREATES A SERVICE", 3.09);
ring("R3", 1.9, 4.7, 11.0, 2.3, C.purple);  rl("R3L", 11.9, "3   BUILD AND APPROVE A POLICY  (ONLY WHEN THE POLICY IS NEW)", 4.74);

/* outside the regions */
icon("iCms", 1.05, 2.05, "cloud", "ext");
cap("cCms", 1.05, 2.5, "CMS Coverage API", ["public CMS data"], 1.4);
who("iOwn", 1.05, 3.75);
cap("cOwn", 1.05, 4.2, "Policy owner", [], 1.4);

/* region 1 */
icon("iJob", 3.6, 2.0, "clock", "code");
cap("cJob", 3.6, 2.45, "Refresh job", ["weekly, changes only"]);
db("iDb1", 6.6, 2.0);
txt("cDb1", 7.25, 1.72, 2.4, 0.9, ["CMS database", "cms_articles", "cms_article_codes", "cms_policies"], { title: 10.5, size: 8.5 });
txt("n1", 9.9, 1.75, 2.9, 0.9, ["Compares versions and fetches only what is new or changed. The owner never waits on the CMS website."], { size: 9, italic: true });
seg("a1", 1.5, 2.0, 3.15, 2.0, true);        tag("a1t", 1.45, 1.74, 1.75, "articles, codes, policies");
seg("a2", 4.05, 2.0, 6.05, 2.0, true);       tag("a2t", 4.05, 1.74, 2.0, "saves what changed");

/* region 2 */
icon("iScr", 3.6, 3.7, "screen", "code");
cap("cScr", 3.6, 4.15, "Owner screens", ["services, codes, policies"]);
icon("iApp", 6.6, 3.7, "server", "code");
cap("cApp", 6.6, 4.15, "App server", ["suggests codes and policies"]);
seg("b1", 1.5, 3.75, 3.15, 3.75, true);      tag("b1t", 1.45, 3.5, 1.75, "creates a service");
seg("b2", 4.05, 3.58, 6.15, 3.58, true);     tag("b2t", 4.05, 3.34, 2.1, "service and choices");
seg("b3", 6.15, 3.9, 4.05, 3.9, true);       tag("b3t", 4.05, 3.94, 2.1, "suggestions");
seg("b4", 6.6, 3.28, 6.6, 2.42, true);       tag("b4t", 6.7, 2.82, 0.9, "reads", "left");
seg("b5", 7.05, 3.7, 12.3, 3.7, false);      seg("b5b", 12.3, 3.7, 12.3, 5.1, true);  tag("b5t", 7.6, 3.46, 4.5, "saves the service, its codes and policy");
txt("n2", 8.3, 4.1, 3.4, 0.4, ["A code sends a packet to one service. A service can use many policies."], { size: 9, italic: true });

/* region 3 */
const X = [2.75, 4.75, 6.75, 8.75, 10.6];
icon("iSrc", X[0], 5.55, "doc", "ext");
cap("cSrc", X[0], 6.0, "Policy source", ["CMS, eCFR or a PDF"], 1.7);
icon("iUns", X[1], 5.55, "parts", "etl");
cap("cUns", X[1], 6.0, "Unstructured API", ["A partitioner parses it into elements: title, text, page number. JSON out."], 1.8);
icon("iLlm", X[2], 5.55, "spark", "ai");
cap("cLlm", X[2], 6.0, "Claude Sonnet", ["10-rule prompt, fixed output form. Rule, exact quote, key fact, question."], 1.8);
icon("iVal", X[3], 5.55, "shield", "code");
cap("cVal", X[3], 6.0, "Validator", ["Text matching: exact, then fuzzy. Numbers and key facts checked."], 1.8);
who("iRev", X[4], 5.55);
cap("cRev", X[4], 6.0, "Owner review", ["Approve, edit or reject each rule beside its quote."], 1.7);
db("iDb2", 12.3, 5.55, 0.95, 0.8);
cap("cDb2", 12.3, 6.0, "Policy library", ["services, codes, policies, key facts, versions"], 1.5);
seg("c1", X[0] + 0.45, 5.55, X[1] - 0.45, 5.55, true);   tag("c1t", X[0] + 0.45, 5.3, X[1] - X[0] - 0.9, "full text");
seg("c2", X[1] + 0.45, 5.55, X[2] - 0.45, 5.55, true);   tag("c2t", X[1] + 0.45, 5.3, X[2] - X[1] - 0.9, "elements (JSON)");
seg("c3", X[2] + 0.45, 5.55, X[3] - 0.45, 5.55, true);   tag("c3t", X[2] + 0.45, 5.3, X[3] - X[2] - 0.9, "draft rules");
seg("c4", X[3] + 0.45, 5.55, X[4] - 0.45, 5.55, true);   tag("c4t", X[3] + 0.45, 5.3, X[4] - X[3] - 0.9, "checked draft");
seg("c5", X[4] + 0.45, 5.55, 11.78, 5.55, true);         tag("c5t", X[4] + 0.4, 5.3, 0.8, "approved");
'''

NOTES = [open(os.path.join(HERE, "..", "..", "docs", "PART1_ARCHITECTURE_SCRIPT.md"), encoding="utf-8").read().split("## What Part 1 is", 1)[1].split("## Check before you say it")[0].replace("## ", "").strip()]

if __name__ == "__main__":
    G.build("Part 1 on one slide", "Part1_One_Page", JS, ['{ hold: 0, fx: [] }'], NOTES)
    # no animation and no transition: take out the timing the engine writes
    out = os.path.join(HERE, "Part1_One_Page.pptx")
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
