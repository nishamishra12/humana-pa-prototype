const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");
const JSZip = require("jszip");
const { Resvg } = require("@resvg/resvg-js");
const OUT = path.join(__dirname, "Part1_Flow2_HLD.pptx");
const OUT_STEPS = path.join(__dirname, "Part1_Flow2_HLD_Steps.pptx");
const C = { ink: "16211E", muted: "5C6B66", green: "1F6F5C", greenSoft: "E3F0EB", line: "CBD5D1", coral: "B8452F", coralSoft: "FBE9E4", amber: "8A5A00", amberSoft: "FCEFD0", purple: "5F3AA8", purpleSoft: "EBE2F8", ok: "18764A", okSoft: "DDF3E7", white: "FFFFFF", provPanel: "F5F3EE", payPanel: "EEF5F2" };
const H = "Cambria", B = "Calibri";
const SKIN = { a: "F2C9A0", b: "C98F63", c: "8D5A3C", d: "F6D9BE" };
function person(o) {
  const hair = { short: `<path d="M33 42 C31 22 69 22 67 42 C63 33 55 30 50 30 C45 30 37 33 33 42Z" fill="#${o.hair}"/>`,
    long: `<path d="M33 42 C31 22 69 22 67 42 C63 33 55 30 50 30 C45 30 37 33 33 42Z" fill="#${o.hair}"/><path d="M33 40 C29 58 33 68 39 69 L41 46Z M67 40 C71 58 67 68 61 69 L59 46Z" fill="#${o.hair}"/>`,
    bun: `<path d="M33 42 C31 22 69 22 67 42 C63 33 55 30 50 30 C45 30 37 33 33 42Z" fill="#${o.hair}"/><circle cx="50" cy="22" r="7" fill="#${o.hair}"/>`,
    none: "" }[o.style || "short"];
  const body = o.coat
    ? `<path d="M14 100 C14 74 30 64 50 64 C70 64 86 74 86 100Z" fill="#FFFFFF" stroke="#C9D2CF" stroke-width="1.5"/><path d="M42 64 L50 82 L58 64Z" fill="#${o.top}"/>`
    : `<path d="M14 100 C14 74 30 64 50 64 C70 64 86 74 86 100Z" fill="#${o.top}"/>`;
  const acc = {
    nurse: `<path d="M34 31 C34 17 66 17 66 31 L62 34 L38 34Z" fill="#FFFFFF" stroke="#C9D2CF" stroke-width="1"/><path d="M48 21h4v3h3v4h-3v3h-4v-3h-3v-4h3z" fill="#1F6F5C"/><path d="M36 67 C34 85 66 85 64 67" fill="none" stroke="#3B4A52" stroke-width="2.6"/><circle cx="50" cy="84" r="3" fill="#3B4A52"/>`,
    doctor: `<path d="M37 66 C35 85 65 85 63 66" fill="none" stroke="#3B4A52" stroke-width="2.6"/><circle cx="50" cy="84" r="3" fill="#3B4A52"/>`,
    headset: `<path d="M32 43 C30 22 70 22 68 43" fill="none" stroke="#2F3B45" stroke-width="3"/><rect x="29" y="40" width="6" height="10" rx="3" fill="#2F3B45"/><path d="M32 50 Q36 58 44 56" stroke="#2F3B45" stroke-width="2" fill="none"/>`,
    clip: `<rect x="56" y="68" width="28" height="32" rx="3" fill="#B98B5B"/><rect x="59" y="72" width="22" height="26" fill="#FFFFFF"/><path d="M62 79h16M62 85h16M62 91h10" stroke="#9AA5A1" stroke-width="2"/>`,
    none: "",
  }[o.acc || "none"];
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><clipPath id="c"><circle cx="50" cy="50" r="48"/></clipPath></defs><circle cx="50" cy="50" r="48" fill="#${o.bg}"/><g clip-path="url(#c)">${body}<rect x="43" y="52" width="14" height="16" rx="5" fill="#${o.skin}"/><circle cx="50" cy="42" r="16" fill="#${o.skin}"/>${hair}<circle cx="44" cy="43" r="1.8" fill="#2B2B2B"/><circle cx="56" cy="43" r="1.8" fill="#2B2B2B"/><path d="M44.5 49.5 Q50 54 55.5 49.5" stroke="#8A4B3A" stroke-width="1.8" fill="none" stroke-linecap="round"/>${acc}</g></svg>`;
}
const building = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><clipPath id="c"><circle cx="50" cy="50" r="48"/></clipPath></defs><circle cx="50" cy="50" r="48" fill="#F2E6D8"/><g clip-path="url(#c)"><rect x="20" y="34" width="60" height="60" fill="#FFFFFF" stroke="#9FB0AA" stroke-width="2"/><rect x="43" y="14" width="14" height="22" fill="#1F6F5C"/><rect x="39" y="18" width="22" height="14" fill="#1F6F5C"/><path d="M50 17v16M42 25h16" stroke="#fff" stroke-width="4"/><g fill="#BCD3CB"><rect x="27" y="44" width="10" height="10"/><rect x="45" y="44" width="10" height="10"/><rect x="63" y="44" width="10" height="10"/><rect x="27" y="62" width="10" height="10"/><rect x="63" y="62" width="10" height="10"/></g><rect x="42" y="68" width="16" height="26" fill="#8FA9A0"/></g></svg>`;
const faxIcon = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="48" fill="#FBE9E4"/><rect x="33" y="14" width="34" height="26" fill="#FFFFFF" stroke="#B8452F" stroke-width="2.5"/><path d="M39 22h22M39 28h22M39 34h14" stroke="#B8452F" stroke-width="2.5"/><rect x="16" y="38" width="68" height="34" rx="7" fill="#4A5A64"/><rect x="24" y="46" width="22" height="10" rx="2" fill="#DDE5E2"/><g fill="#DDE5E2"><circle cx="58" cy="49" r="2.4"/><circle cx="66" cy="49" r="2.4"/><circle cx="74" cy="49" r="2.4"/><circle cx="58" cy="58" r="2.4"/><circle cx="66" cy="58" r="2.4"/><circle cx="74" cy="58" r="2.4"/></g><rect x="30" y="70" width="40" height="16" fill="#FFFFFF" stroke="#4A5A64" stroke-width="2.5"/></svg>`;

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


const cylSvg = (f, s) => `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 220 150"><path d="M4 22 V124 A106 22 0 0 0 216 124 V22" fill="#${f}" stroke="#${s}" stroke-width="3"/><ellipse cx="110" cy="22" rx="106" ry="20" fill="#${f}" stroke="#${s}" stroke-width="3"/></svg>`;

frame("PART 1  \u00b7  FLOW 2", "From a policy to approved rules.", "Parse, draft, validate, approve", "Policies shown are public Medicare policies. The AI drafts. It never publishes. A person approves every rule.");
panel("Q1", 0.5, 1.45, 12.33, 2.0, C.provPanel);
label("Q1L", 0.7, 1.48, 6, "READ AND DRAFT");
panel("Q2", 0.5, 3.55, 12.33, 2.0, C.payPanel);
label("Q2L", 0.7, 3.5799999999999996, 6, "CHECK, APPROVE, SAVE");
step("T_src", 0.8, 1.85, 2.5, 0.9, "ext", "Policy source", "CMS, eCFR or a PDF");
line("B1", 3.3, 2.3, 0.7, 0, { arrow: true });
step("T_unst", 4.0, 1.85, 2.7, 0.9, "etl", "Unstructured API", "Partitions the document");
add({ name: "D_unst", kind: "text", x: 4.0, y: 2.8, w: 2.7, h: 0.62, align: "left", valign: "top", runs: [{ text: "Uses a partitioner to parse the document and extract elements: title, text, page number. Output is JSON.", options: { fontSize: 9.5, color: C.muted, fontFace: B, bold: false, italic: false, breakLine: false } }] });
line("B2", 6.7, 2.3, 0.7, 0, { arrow: true });
step("T_llm", 7.4, 1.85, 2.7, 0.9, "ai", "Claude Sonnet", "Drafts the rules");
add({ name: "D_llm", kind: "text", x: 7.4, y: 2.8, w: 2.7, h: 0.62, align: "left", valign: "top", runs: [{ text: "Prompt: 10 rules. Fixed output form. Each rule has its exact quote, key fact and question.", options: { fontSize: 9.5, color: C.muted, fontFace: B, bold: false, italic: false, breakLine: false } }] });
add({ name: "E3", kind: "text", x: 10.45, y: 1.8, w: 2.3, h: 1.55, align: "left", valign: "top", runs: [{ text: "API CALLS", options: { fontSize: 9, color: C.muted, fontFace: B, bold: true, italic: false, breakLine: true } }, { text: "Unstructured:", options: { fontSize: 9, color: C.muted, fontFace: B, bold: false, italic: false, breakLine: true } }, { text: "client.parse.run, elements", options: { fontSize: 9, color: C.muted, fontFace: B, bold: false, italic: false, breakLine: true } }, { text: "Anthropic:", options: { fontSize: 9, color: C.muted, fontFace: B, bold: false, italic: false, breakLine: true } }, { text: "messages.create, forced tool record_policy", options: { fontSize: 9, color: C.muted, fontFace: B, bold: false, italic: false, breakLine: false } }] });
line("P1", 10.1, 2.3, 0.18, 0, { arrow: false });
line("P2", 10.28, 2.3, 0, 1.2, { arrow: false });
line("P3", 3.0, 3.5, 7.28, 0, { arrow: false });
line("P4", 3.0, 3.5, 0, 0.45, { arrow: true });
step("T_val", 0.8, 3.95, 2.5, 0.9, "code", "Validator", "Text matching, rule checks");
add({ name: "D_val", kind: "text", x: 0.8, y: 4.9, w: 2.5, h: 0.62, align: "left", valign: "top", runs: [{ text: "Finds the quote in the policy: exact, then fuzzy (88+) with the same numbers. Every number in a test is in its quote.", options: { fontSize: 9.5, color: C.muted, fontFace: B, bold: false, italic: false, breakLine: false } }] });
line("B3", 3.3, 4.4, 0.7, 0, { arrow: true });
step("T_own", 4.0, 3.95, 2.7, 0.9, "person", "Policy owner", "Approve, edit, reject");
add({ name: "D_own", kind: "text", x: 4.0, y: 4.9, w: 2.7, h: 0.62, align: "left", valign: "top", runs: [{ text: "Each rule beside its exact quote. Only approved rules are checked.", options: { fontSize: 9.5, color: C.muted, fontFace: B, bold: false, italic: false, breakLine: false } }] });
line("B4", 6.7, 4.4, 0.7, 0, { arrow: true });
ART["Lib"] = cylSvg(C.greenSoft, C.green); add({ name: "Lib", kind: "image", x: 7.4, y: 3.75, w: 2.5, h: 1.35 });
add({ name: "LibT", kind: "text", x: 7.4, y: 4.1, w: 2.5, h: 0.95, align: "center", valign: "middle", runs: [{ text: "Policy library", options: { fontSize: 10, color: C.ink, fontFace: B, bold: true, italic: false, breakLine: true } }, { text: "Rules and key facts", options: { fontSize: 10, color: C.ink, fontFace: B, bold: false, italic: false, breakLine: true } }, { text: "Versions, audit trail", options: { fontSize: 10, color: C.ink, fontFace: B, bold: false, italic: false, breakLine: false } }] });
add({ name: "E4", kind: "text", x: 10.45, y: 3.9, w: 2.3, h: 1.5, align: "left", valign: "top", runs: [{ text: "APP ENDPOINTS", options: { fontSize: 9, color: C.muted, fontFace: B, bold: true, italic: false, breakLine: true } }, { text: "POST /builds", options: { fontSize: 9, color: C.muted, fontFace: B, bold: false, italic: false, breakLine: true } }, { text: "GET /builds/{id}", options: { fontSize: 9, color: C.muted, fontFace: B, bold: false, italic: false, breakLine: true } }, { text: "POST /builds/{id}/criteria/{cid}", options: { fontSize: 9, color: C.muted, fontFace: B, bold: false, italic: false, breakLine: true } }, { text: "POST /builds/{id}/publish", options: { fontSize: 9, color: C.muted, fontFace: B, bold: false, italic: false, breakLine: false } }] });
add({ name: "KF", kind: "node", x: 0.5, y: 5.68, w: 12.33, h: 0.68, fill: C.greenSoft, line: C.green, lineW: 1.25, radius: 0.08, valign: "middle", margin: [0.05, 0.18, 0.05, 0.18], runs: [{ text: "KEY FACT   ", options: { bold: true, fontSize: 11, color: C.green, fontFace: B, charSpacing: 2 } }, { text: "One thing a nurse must find in a packet to apply a rule: a name and type, the exact policy sentence, and the question to ask the provider if it is missing.", options: { fontSize: 12.5, color: C.ink, fontFace: B } }] });
caption("c1", "The owner picks a policy: from CMS, eCFR, or a PDF.");
caption("c2", "Unstructured parses it into elements, as JSON.");
caption("c3", "Claude Sonnet drafts the rules, exact quotes, key facts and questions.");
caption("c4", "Code checks every quote and number against the policy.");
caption("c5", "The owner approves, edits or rejects each rule.");
caption("c6", "Approved rules and key facts are saved as a new version.");
caption("c7", "A key fact is what a nurse must find in a packet.");
const slots = [
  { hold: 0, fx: [FI("T_src", 0), FI("c1", 300)] },
  { hold: 0, fx: [FO("c1"), WI("B1", "left", 100, 250), FI("T_unst", 300), FI("D_unst", 700), FI("c2", 300)] },
  { hold: 0, fx: [FO("c2"), WI("B2", "left", 100, 250), FI("T_llm", 300), FI("D_llm", 700), FI("E3", 700), FI("c3", 300)] },
  { hold: 0, fx: [FO("c3"), WI("P1", "left", 0, 150), WI("P2", "down", 100, 300), WI("P3", "right", 350, 600), WI("P4", "down", 950, 250), FI("T_val", 1100), FI("D_val", 1300), FI("c4", 300)] },
  { hold: 0, fx: [FO("c4"), WI("B3", "left", 100, 250), FI("T_own", 300), FI("D_own", 700), FI("c5", 300)] },
  { hold: 0, fx: [FO("c5"), WI("B4", "left", 100, 250), FI("Lib", 300), FI("LibT", 300), FI("E4", 600), FI("c6", 300)] },
  { hold: 0, fx: [FO("c6"), FI("KF", 0), FI("c7", 300)] },
];
const STEP_NOTES = [
 "A policy needs to be built only if it is new. The source can be a CMS national or local policy, a federal regulation from eCFR, or the plan's own PDF. For CMS and eCFR the system fetches the full text. For a PDF the owner uploads it.",
 "Step one is the ETL. Unstructured uses a partitioner to parse the document and extract elements: the title, the text, the page number. It gives the output as JSON. We keep that structure because a rule hangs on a section, and flat text would lose it. A real element looks like this: type Title, text NCD 30.3.3 Acupuncture for Chronic Lower Back Pain, page 1.",
 "The elements go to the language model, Claude Sonnet. It has a system prompt with 10 rules. For example: one condition per rule, copy the exact sentence the rule comes from, use a key fact we already know or propose a new one, and write the question to ask the provider if the fact is missing. It must answer through a fixed form, so the output is always structured. For each rule we get the rule in plain words, the exact quote, the key fact, the test, the question, and how confident the model is.",
 "The validator is code, with real algorithms. It never trusts the model's quote. It re-finds it. First it normalises both texts: lowercase, straight quotes, words split across lines rejoined. Then it searches for the quote on every page. If the exact text is not there, it tries a fuzzy match and needs at least 88 out of 100. A fuzzy match must carry the same numbers, or it is rejected, because a different number is a different rule. Then it checks that every number in the test appears in the quote, that the key fact exists, and it scans for requirement-sounding sentences that no rule covers. A rule that fails is shown to the owner. It is never dropped.",
 "Then the owner reviews. Each rule is shown beside the exact quote it came from, with its key fact and the question. They approve, edit or reject each one. Only approved rules are checked. If they reject the only rule that uses a key fact, that key fact is not checked and not asked for. The AI drafts. A person signs.",
 "The approved rules and key facts are saved on the policy, as a new version of the library. Every version is kept and can be rolled back, and every action is in the audit trail. A service shows the combined key facts of its policies. A policy approved once can be reused by any service that needs it.",
 "A key fact is one thing a nurse must find in a packet to apply a rule. For a heart device it could be the ejection fraction, how long the patient has been on medicine, or whether a shared decision visit happened. It has a name and a type, the exact policy sentence behind it, and the question to ask the provider if the packet does not have it. It matters for four reasons. It turns a long policy into a short list the nurse can check. It tells the AI reader exactly what to look for in every packet, and nothing more. It gives the nurse one precise question to send when something is missing. And it ties every check to the policy's own words, which is the audit trail."
];
const NOTES = "";
const OUT_STEPS_UNUSED = true;
const ANIMATED = !process.argv.includes("--slides");
const animatedNames = new Set(slots.flatMap((sl) => sl.fx.map((e) => e.name)));

// what is on screen after the first k slots have played
function visibleAfter(k) {
  const vis = new Set();
  slots.slice(0, k).forEach((sl) => sl.fx.forEach((e) => (e.t === "fadeOut" ? vis.delete(e.name) : vis.add(e.name))));
  return vis;
}

function draw(pres, s, PNG, vis) {
  const m2 = (m) => m.map((v) => v * 72); // inches -> points
  items.forEach((o) => {
    if (vis && animatedNames.has(o.name) && !vis.has(o.name)) return;
    if (o.kind === "image") {
      s.addImage({ data: "image/png;base64," + PNG[o.name], x: o.x, y: o.y, w: o.w, h: o.h, objectName: o.name });
    } else if (o.kind === "line") {
      s.addShape(pres.ShapeType.line, { x: o.x, y: o.y, w: o.w, h: o.h, flipH: !!o.flipH, flipV: !!o.flipV, objectName: o.name, line: { color: o.color || o.line, width: o.lineW, dashType: o.dash || "solid", ...(o.arrow ? { endArrowType: "triangle" } : {}) } });
    } else if (o.kind === "ring") {
      s.addShape(pres.ShapeType.roundRect, { x: o.x, y: o.y, w: o.w, h: o.h, rectRadius: 0.1, fill: { type: "none" }, line: { color: o.line, width: o.lineW }, objectName: o.name });
    } else if (o.kind === "node") {
      const m = o.margin || [0.06, 0.12, 0.06, 0.12]; // my spec order is top, right, bottom, left
      // pptxgenjs wants [left, right, bottom, top]
      s.addText(o.runs, { shape: pres.ShapeType.roundRect, rectRadius: o.radius ?? 0.08, x: o.x, y: o.y, w: o.w, h: o.h, fill: { color: o.fill }, line: { color: o.line, width: o.lineW }, align: o.align || "left", valign: o.valign || "middle", margin: m2([m[3], m[1], m[2], m[0]]), objectName: o.name, isTextBox: false });
    } else {
      s.addText(o.runs, { x: o.x, y: o.y, w: o.w, h: o.h, align: o.align || "left", valign: o.valign || "top", margin: 0, objectName: o.name, isTextBox: true, fit: "none" });
    }
  });
}

async function main() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5 in
  pres.title = "From a policy to approved rules";
  pres.author = "Nisha Mishra";
  const PNG = {};
  for (const [k, svg] of Object.entries(ART)) PNG[k] = Buffer.from(new Resvg(svg, { fitTo: { mode: "width", value: 360 } }).render().asPng()).toString("base64");

  if (!ANIMATED) {
    // one slide per step: press Next to walk the flow
    slots.forEach((_, i) => {
      const s = pres.addSlide();
      s.background = { color: C.white };
      draw(pres, s, PNG, visibleAfter(i + 1));
      s.addNotes(STEP_NOTES[i]);
    });
    await pres.writeFile({ fileName: OUT_STEPS });
    fs.writeFileSync(path.join(__dirname, "preview_Part1_Flow2_HLD.html"), preview());
    if (process.argv.includes("--steps")) [4, 6, 10, 11, 13].forEach((k) => fs.writeFileSync(path.join(__dirname, `Part1_Flow2_HLD_s${k}.html`), preview().replace('new URLSearchParams(location.search).get("step")', `"${k}"`)));
    console.log("wrote", OUT_STEPS, "|", slots.length, "slides, press Next to walk through");
    return;
  }

  const s = pres.addSlide();
  s.background = { color: C.white };
  draw(pres, s, PNG, null);
  s.addNotes(["One slide. One click per step. Finish your talking point, then click."].concat(STEP_NOTES.map((t, i) => "Click " + (i + 1) + ": " + t)).join(String.fromCharCode(10, 10)));
  await pres.writeFile({ fileName: OUT });

  // inject the animation
  const zip = await JSZip.loadAsync(fs.readFileSync(OUT));
  const f = "ppt/slides/slide1.xml";
  let xml = await zip.file(f).async("string");
  const ids = {};
  for (const m of xml.matchAll(/<p:cNvPr id="(\d+)" name="([^"]*)"/g)) ids[m[2]] = m[1];
  const missing = new Set();
  slots.forEach((sl) => sl.fx.forEach((e) => { if (!ids[e.name]) missing.add(e.name); }));
  if (missing.size) throw new Error("No shape for: " + [...missing].join(", "));
  const byName = Object.fromEntries(items.map((o) => [o.name, o]));
  const timing = buildTiming(ids, byName);
  xml = xml.replace("</p:sld>", timing + "</p:sld>");
  zip.file(f, xml);
  fs.writeFileSync(OUT, await zip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" }));
  fs.writeFileSync(path.join(__dirname, "preview_Part1_Flow2_HLD.html"), preview());
  let total = 0; slots.forEach((sl) => (total += sl.hold + Math.max(...sl.fx.map((e) => (e.delay + e.dur) / 1000))));
  console.log("wrote", OUT, "| ", slots.length, "clicks");
}

function buildTiming(ids, byName) {
  let n = 3;
  const id = () => n++;
  const dirs = { left: [8, "wipe(left)"], right: [2, "wipe(right)"], down: [1, "wipe(up)"], up: [4, "wipe(down)"] };
  // PowerPoint names wipe direction by where it starts: "from top" = subtype 1 / wipe(up)
  const fromTop = { down: [1, "wipe(up)"] };
  const setVis = (spid, val, delay) => `<p:set><p:cBhvr><p:cTn id="${id()}" dur="1" fill="hold"><p:stCondLst><p:cond delay="${delay}"/></p:stCondLst></p:cTn><p:tgtEl><p:spTgt spid="${spid}"/></p:tgtEl><p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst></p:cBhvr><p:to><p:strVal val="${val}"/></p:to></p:set>`;
  const filt = (spid, filter, trans, dur) => `<p:animEffect transition="${trans}" filter="${filter}"><p:cBhvr><p:cTn id="${id()}" dur="${dur}"/><p:tgtEl><p:spTgt spid="${spid}"/></p:tgtEl></p:cBhvr></p:animEffect>`;
  const effect = (e, nodeType) => {
    const spid = ids[e.name], o = byName[e.name];
    const grp = o.kind === "line" || o.kind === "image" ? "" : ' grpId="0"';
    let preset, cls, sub, body;
    if (e.t === "fadeIn") { preset = 10; cls = "entr"; sub = 0; body = setVis(spid, "visible", 0) + filt(spid, "fade", "in", e.dur); }
    else if (e.t === "fadeOut") { preset = 10; cls = "exit"; sub = 0; body = filt(spid, "fade", "out", e.dur) + setVis(spid, "hidden", Math.max(e.dur - 1, 0)); }
    else { const d = e.dir === "down" ? fromTop.down : dirs[e.dir]; preset = 22; cls = "entr"; sub = d[0]; body = setVis(spid, "visible", 0) + filt(spid, d[1], "in", e.dur); }
    return `<p:par><p:cTn id="${id()}" presetID="${preset}" presetClass="${cls}" presetSubtype="${sub}" fill="hold"${grp} nodeType="${nodeType}"><p:stCondLst><p:cond delay="${e.delay}"/></p:stCondLst><p:childTnLst>${body}</p:childTnLst></p:cTn></p:par>`;
  };
  // one click per step: the presenter finishes the talking point, then clicks. Nothing plays by itself.
  let clicksXml = "";
  slots.forEach((sl) => {
    const outerId = id(), slotId = id();
    const inner = sl.fx.map((e, k) => effect(e, k === 0 ? "clickEffect" : "withEffect")).join("");
    clicksXml += `<p:par><p:cTn id="${outerId}" fill="hold"><p:stCondLst><p:cond delay="indefinite"/></p:stCondLst><p:childTnLst><p:par><p:cTn id="${slotId}" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>${inner}</p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn></p:par>`;
  });
  const bld = [...new Set(slots.flatMap((sl) => sl.fx.map((e) => e.name)))].filter((nm) => !["line", "image"].includes(byName[nm].kind))
    .map((nm) => { const o = byName[nm]; const bg = o.kind === "ring" || (o.kind === "node" && o.fill); return `<p:bldP spid="${ids[nm]}" grpId="0"${bg ? ' animBg="1"' : ""}/>`; }).join("");
  const rootId = 1, seqId = 2;
  return `<p:timing><p:tnLst><p:par><p:cTn id="${rootId}" dur="indefinite" restart="never" nodeType="tmRoot"><p:childTnLst><p:seq concurrent="1" nextAc="seek"><p:cTn id="${seqId}" dur="indefinite" nodeType="mainSeq"><p:childTnLst>${clicksXml}</p:childTnLst></p:cTn><p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst><p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst></p:seq></p:childTnLst></p:cTn></p:par></p:tnLst><p:bldLst>${bld}</p:bldLst></p:timing>`;
}

/* ---------- static preview: every object visible at once, to check the layout ---------- */
function preview() {
  const px = 96, pt = (v) => v * 1.3333;
  const esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;");
  const html = items.map((o) => {
    const base = `left:${o.x * px}px;top:${o.y * px}px;width:${o.w * px}px;height:${o.h * px}px;`;
    if (o.kind === "line") {
      const horiz = o.h === 0, col = "#" + (o.color || o.line);
      return `<div data-n="${o.name}" style="position:absolute;${base}${horiz ? `border-top:${o.lineW}px ${o.dash ? "dashed" : "solid"} ${col}` : `border-left:${o.lineW}px solid ${col}`}"></div>`;
    }
    const inner = o.runs ? o.runs.map((r) => `<span style="font-family:${r.options.fontFace || B};font-size:${pt(r.options.fontSize || 12)}px;font-weight:${r.options.bold ? 700 : 400};color:#${r.options.color || C.ink}">${esc(r.text)}</span>${r.options.breakLine ? "<br>" : ""}`).join("") : "";
    if (o.kind === "image") return `<img data-n="${o.name}" src="data:image/svg+xml;base64,${Buffer.from(ART[o.name]).toString("base64")}" style="position:absolute;${base}">`;
    if (o.kind === "ring") return `<div data-n="${o.name}" style="position:absolute;${base}border:${o.lineW}px solid #${o.line};border-radius:10px;box-sizing:border-box"></div>`;
    const m = o.margin ? o.margin.map((v) => v * px) : [0, 0, 0, 0];
    const box = o.kind === "node" ? `background:#${o.fill};border:${o.lineW}px solid #${o.line};border-radius:${(o.radius ?? 0.08) * px}px;` : "";
    return `<div data-n="${o.name}" style="position:absolute;${base}${box}box-sizing:border-box;overflow:hidden;display:flex;flex-direction:column;justify-content:${o.valign === "top" ? "flex-start" : "center"};text-align:${o.align || "left"};padding:${m[0]}px ${m[1]}px ${m[2]}px ${m[3]}px;line-height:1.15"><div>${inner}</div></div>`;
  }).join("\n");
  const data = JSON.stringify(slots.map((sl) => sl.fx.map((e) => [e.name, e.t])));
  const script = `<script>const S=${data};const q=new URLSearchParams(location.search).get("step");if(q!==null){const k=+q;const vis={};const all=new Set(S.flat().map(e=>e[0]));S.slice(0,k).forEach(sl=>sl.forEach(([n,t])=>{vis[n]=t!=="fadeOut"}));document.querySelectorAll("[data-n]").forEach(el=>{const n=el.dataset.n;if(all.has(n)&&!vis[n])el.style.display="none"})}</script>`;
  return `<!doctype html><meta charset="utf-8"><body style="margin:0;background:#fff"><div style="position:relative;width:${13.333 * px}px;height:${7.5 * px}px;background:#fff">${html}</div>${script}`;
}


main().catch((e) => { console.error(e); process.exit(1); });
