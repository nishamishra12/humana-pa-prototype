// Builds ONE animated slide: Part 1 of the product, building the policy library and onboarding a service.
// Same method and look as build_friction.js and build_journey.js: one slide, one click per step, nothing plays by itself.
// Run:  NODE_PATH=<folder with @resvg/resvg-js> node build_onboarding.js   -> Policy_Service_Onboarding.pptx + preview_onboarding.html
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");
const JSZip = require("jszip");
const { Resvg } = require("@resvg/resvg-js"); // draws the SVG art to PNG (npm i @resvg/resvg-js)

const OUT = path.join(__dirname, "Policy_Service_Onboarding.pptx"); // default: ONE slide, one click per step
const OUT_STEPS = path.join(__dirname, "Policy_Service_Onboarding_Steps.pptx"); // only with --slides: one slide per step
const C = {
  ink: "16211E", muted: "5C6B66", green: "1F6F5C", greenSoft: "E3F0EB", line: "CBD5D1",
  coral: "B8452F", coralSoft: "FBE9E4", amber: "8A5A00", amberSoft: "FCEFD0",
  purple: "5F3AA8", purpleSoft: "EBE2F8", ok: "18764A", okSoft: "DDF3E7", white: "FFFFFF",
  provPanel: "F5F3EE", payPanel: "EEF5F2",
};
const H = "Cambria", B = "Calibri";

/* ---------- illustrations (flat SVG, rendered to PNG so they work in Google Slides) ---------- */
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

// round icons in the same flat style as the people
const disc = (bg, glyph) => `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="48" fill="#${bg}"/>${glyph}</svg>`;
const G = {
  gov: `<path d="M24 42 L50 24 L76 42Z" fill="#1F6F5C"/><g fill="#9FB0AA"><rect x="29" y="46" width="9" height="24"/><rect x="45.5" y="46" width="9" height="24"/><rect x="62" y="46" width="9" height="24"/></g><rect x="22" y="72" width="56" height="7" fill="#1F6F5C"/>`,
  doc: `<rect x="32" y="22" width="36" height="50" rx="3" fill="#FFFFFF" stroke="#B8452F" stroke-width="3"/><path d="M39 35h22M39 45h22M39 55h14" stroke="#B8452F" stroke-width="3"/>`,
  pdf: `<rect x="32" y="22" width="36" height="50" rx="3" fill="#FFFFFF" stroke="#8A5A00" stroke-width="3"/><path d="M39 36h22M39 46h22" stroke="#8A5A00" stroke-width="3"/><rect x="38" y="55" width="24" height="9" rx="2" fill="#8A5A00"/>`,
  spark: `<path d="M50 20 L57 43 L80 50 L57 57 L50 80 L43 57 L20 50 L43 43Z" fill="#5F3AA8"/><circle cx="74" cy="26" r="5" fill="#5F3AA8"/>`,
  check: `<path d="M50 20 L75 30 V52 C75 67 63 75 50 81 C37 75 25 67 25 52 V30Z" fill="#FFFFFF" stroke="#1F6F5C" stroke-width="3.5"/><path d="M37 50 L47 60 L64 40" fill="none" stroke="#1F6F5C" stroke-width="5.5" stroke-linecap="round" stroke-linejoin="round"/>`,
  link: `<rect x="20" y="40" width="36" height="20" rx="10" fill="none" stroke="#1F6F5C" stroke-width="5.5"/><rect x="44" y="40" width="36" height="20" rx="10" fill="none" stroke="#1F6F5C" stroke-width="5.5"/>`,
  book: `<path d="M22 28 H47 V74 H22Z M53 28 H78 V74 H53Z" fill="#FFFFFF" stroke="#1F6F5C" stroke-width="3.5"/><path d="M29 40h12M29 49h12M60 40h12M60 49h12" stroke="#1F6F5C" stroke-width="3"/>`,
};
const ART = {
  IcCms: disc("E3F0EB", G.gov),
  IcFed: disc("FBE9E4", G.doc),
  IcHum: disc("FCEFD0", G.pdf),
  IcRead: disc("FBE9E4", G.doc),
  IcDraft: disc("EBE2F8", G.spark),
  IcCheck: disc("E3F0EB", G.check),
  AvOwner: person({ bg: "E3D9F5", skin: SKIN.b, hair: "2B2B2B", style: "bun", top: "6B4C9A", acc: "clip" }),
  IcLink: disc("E3F0EB", G.link),
  IcBook: disc("E3F0EB", G.book),
};

/* ---------- layout spec (inches) ---------- */
const items = [];
const add = (o) => items.push(o);
const runs = (title, desc, tc = C.ink, ts = 13, ds = 10.5, dc = C.muted) => [
  { text: title, options: { bold: true, fontSize: ts, color: tc, fontFace: B, breakLine: !!desc } },
  ...(desc ? [{ text: desc, options: { fontSize: ds, color: dc, fontFace: B } }] : []),
];
const line = (name, x, y, w, h, o = {}) => add({ name, kind: "line", x, y, w, h, line: C.muted, lineW: 1.75, arrow: true, ...o });
const avatar = (name, x, y, size) => add({ name, kind: "image", x, y, w: size, h: size });
const node = (name, x, y, w, h, title, desc, o = {}) => add({ name, kind: "node", x, y, w, h, fill: o.fill || C.white, line: o.line || C.line, lineW: o.lineW || 1.25, radius: 0.08, runs: runs(title, desc, o.tc || C.ink, o.ts || 13.5, o.ds || 10.5, o.dc || C.muted), margin: o.margin || [0.04, 0.1, 0.04, 0.85], align: o.align });
const chip = (n, x, y, w, t, color = C.green) => add({ name: n, kind: "node", x, y, w, h: 0.3, fill: C.white, line: color, lineW: 1, radius: 0.06, align: "center", margin: [0, 0.04, 0, 0.04], runs: [{ text: t, options: { fontSize: 10, color: C.ink, fontFace: B } }] });
const caption = (name, text) => add({ name, kind: "text", x: 0.5, y: 6.5, w: 12.33, h: 0.65, valign: "middle", runs: [{ text, options: { fontSize: 16, color: C.ink, fontFace: B } }] });

// static frame
add({ name: "eyebrow", kind: "text", static: true, x: 0.5, y: 0.3, w: 5, h: 0.28, runs: [{ text: "THE PRODUCT, PART 1 OF 2", options: { bold: true, fontSize: 11, color: C.green, fontFace: B, charSpacing: 3 } }] });
add({ name: "title", kind: "text", static: true, x: 0.5, y: 0.55, w: 8.4, h: 0.75, valign: "middle", runs: [{ text: "Building the library, then onboarding a service.", options: { fontSize: 26, color: C.ink, fontFace: H } }] });
add({ name: "sub", kind: "text", static: true, x: 8.6, y: 0.55, w: 4.23, h: 0.75, align: "right", valign: "middle", runs: [{ text: "Once per service, and when a policy changes", options: { fontSize: 14, color: C.muted, fontFace: B } }] });
add({ name: "panelSrc", kind: "node", static: true, x: 0.5, y: 1.45, w: 3.3, h: 4.85, fill: C.provPanel, line: C.line, lineW: 1, radius: 0.1, runs: [{ text: " ", options: { fontSize: 8 } }] });
add({ name: "panelApp", kind: "node", static: true, x: 4.15, y: 1.45, w: 8.68, h: 4.85, fill: C.payPanel, line: C.line, lineW: 1, radius: 0.1, runs: [{ text: " ", options: { fontSize: 8 } }] });
add({ name: "hdrSrc", kind: "text", static: true, x: 0.7, y: 1.52, w: 2.9, h: 0.55, runs: [{ text: "OFFICIAL SOURCES", options: { bold: true, fontSize: 11, color: C.ink, fontFace: B, charSpacing: 3, breakLine: true } }, { text: "What a nurse checks by hand today", options: { fontSize: 10, color: C.muted, fontFace: B } }] });
add({ name: "hdrApp", kind: "text", static: true, x: 4.4, y: 1.52, w: 8.2, h: 0.55, runs: [{ text: "PA DESK", options: { bold: true, fontSize: 11, color: C.ink, fontFace: B, charSpacing: 3, breakLine: true } }, { text: "A policy owner turns a policy into a service the system can use", options: { fontSize: 10, color: C.muted, fontFace: B } }] });
add({ name: "footer", kind: "text", static: true, x: 0.5, y: 7.1, w: 12.33, h: 0.25, runs: [{ text: "Policies shown are public Medicare policies. The Humana policy and MCG slots are placeholders. The AI drafts. It never publishes.", options: { fontSize: 9, color: C.muted, fontFace: B } }] });

// sources
const SY = [2.2, 3.4, 4.6];
node("S1", 0.7, SY[0], 2.9, 0.95, "CMS coverage database", "National and local policies, plus their billing articles");
avatar("IcCms", 0.82, SY[0] + 0.17, 0.6);
node("S2", 0.7, SY[1], 2.9, 0.95, "Federal rules", "Regulations, from the eCFR");
avatar("IcFed", 0.82, SY[1] + 0.17, 0.6);
node("S3", 0.7, SY[2], 2.9, 0.95, "Humana policy", "The plan's own PDF. Commercial criteria are licensed");
avatar("IcHum", 0.82, SY[2] + 0.17, 0.6);
SY.forEach((y, i) => line("Stub" + (i + 1), 3.6, y + 0.475, 0.35, 0, { arrow: false }));
line("Bracket", 3.95, SY[0] + 0.475, 0, SY[2] - SY[0], { arrow: false });
line("ArrIn", 3.95, 2.675, 0.45, 0);

// the flow inside PA Desk
const CX = [4.4, 7.25, 10.1], CW = 2.5, R1 = 2.2, R2 = 3.98, RH = 1.0;
const ndesc = (n, x, y, title, desc, art, o = {}) => { node(n, x, y, CW, RH, title, desc, { margin: [0.04, 0.08, 0.04, 0.85], ...o }); avatar(art, x + 0.12, y + 0.2, 0.6); };
ndesc("R1", CX[0], R1, "Read the policy", "ETL + AI keeps titles, paragraphs, tables and pages", "IcRead");
ndesc("R2", CX[1], R1, "Draft the rules", "AI writes each rule with its source sentence", "IcDraft");
ndesc("R3", CX[2], R1, "Check the draft", "Code checks every quote, number and detail", "IcCheck");
line("A12", CX[0] + CW + 0.02, R1 + RH / 2, 0.31, 0);
line("A23", CX[1] + CW + 0.02, R1 + RH / 2, 0.31, 0);
chip("D1", CX[1] + 0.05, R1 + RH + 0.1, 1.15, "Ejection fraction");
chip("D2", CX[1] + 1.3, R1 + RH + 0.1, 1.15, "Heart attack");
add({ name: "T4", kind: "text", x: CX[2], y: R1 + RH + 0.1, w: CW, h: 0.3, runs: [{ text: "No AI here.", options: { bold: true, fontSize: 11, color: C.coral, fontFace: B } }] });
// the turn: out of the check, back to the left, down into the owner
line("E1", CX[2] + CW / 2, R1 + RH, 0, 0.55, { arrow: false });
line("E2", CX[0] + CW / 2, R1 + RH + 0.55, CX[2] - CX[0], 0, { arrow: false });
line("E3", CX[0] + CW / 2, R1 + RH + 0.55, 0, R2 - (R1 + RH + 0.55), { });
ndesc("O1", CX[0], R2, "Policy owner approves", "Approves, edits or rejects each rule", "AvOwner", { fill: C.purpleSoft, line: C.purple, tc: C.purple, ts: 13 });
ndesc("O2", CX[1], R2, "Link to codes and a service", "A policy gets procedure codes and joins a service", "IcLink");
ndesc("O3", CX[2], R2, "Publish a version", "One versioned library. Any version can roll back", "IcBook");
line("A56", CX[0] + CW + 0.02, R2 + RH / 2, 0.31, 0);
line("A67", CX[1] + CW + 0.02, R2 + RH / 2, 0.31, 0);
chip("K1", CX[1] + 0.05, R2 + RH + 0.1, 1.15, "CPT code 33249");
chip("K2", CX[1] + 1.3, R2 + RH + 0.1, 1.15, "ICD service");

// the bottom zone: first the rollout plan, then what we get
const BY = 5.5;
add({ name: "Gtm", kind: "node", x: CX[0], y: BY, w: 8.2, h: 0.72, fill: C.coralSoft, line: C.coral, lineW: 1.25, radius: 0.1, margin: [0.05, 0.2, 0.05, 0.2], runs: [{ text: "Which services first?  ", options: { bold: true, fontSize: 11.5, color: C.coral, fontFace: B } }, { text: "In production, Humana's own history of prior authorization requests sets the rollout plan: volume, pends and reversals by procedure code.", options: { fontSize: 11.5, color: C.ink, fontFace: B } }] });
add({ name: "Get", kind: "node", x: CX[0], y: BY - 0.02, w: 8.2, h: 0.78, fill: C.okSoft, line: C.ok, lineW: 1.25, radius: 0.1, margin: [0.04, 0.2, 0.04, 0.2], runs: [{ text: " ", options: { fontSize: 8 } }] });
const GET = ["A versioned library of services, with codes, policies and details", "Every rule tied to its official sentence and a named approver", "Every code with its source, and every change in an audit trail", "Planned, pilot, then live. Any version can be rolled back"];
GET.forEach((t, i) => add({ name: "G" + i, kind: "text", x: CX[0] + 0.2 + (i % 2) * 4.0, y: BY + 0.05 + Math.floor(i / 2) * 0.36, w: 3.85, h: 0.34, valign: "middle", runs: [{ text: "✓  ", options: { bold: true, fontSize: 10.5, color: C.ok, fontFace: B } }, { text: t, options: { fontSize: 10, color: C.ink, fontFace: B } }] }));

const CAPS = {
  c1: "Today a nurse checks every case against CMS, national and local policies, federal rules and Humana's own documents. We start from the same sources.",
  c2: "An ETL step with AI inside reads each policy and keeps its structure: titles, paragraphs, tables and the page each came from.",
  c3: "An AI turns each requirement into a rule, names the detail a nurse must check, and quotes the exact official sentence.",
  c4: "Plain code checks every quote, number and detail. Anything that fails goes to the owner. It is never dropped.",
  c5: "A policy owner approves, edits or rejects every rule. The AI drafts. It never publishes.",
  c6: "The policy gets procedure codes and joins a service: any product or business name we choose. The service holds its codes, policies and details.",
  c7: "In production, Humana's history of prior authorization requests decides which services we onboard first.",
  c8: "We publish one versioned library. Part two reads every packet with it.",
  c9: "What we get.",
};
Object.entries(CAPS).forEach(([k, v]) => caption(k, v));

/* ---------- timeline: one click per slot. Nothing plays by itself. ---------- */
const FI = (name, delay = 0, dur = 500) => ({ t: "fadeIn", name, delay, dur });
const FO = (name, delay = 0, dur = 300) => ({ t: "fadeOut", name, delay, dur });
const WI = (name, dir, delay = 0, dur = 600) => ({ t: "wipeIn", name, dir, delay, dur });
const slots = [
  { hold: 0, fx: [FI("S1"), FI("IcCms"), FI("S2", 150), FI("IcFed", 150), FI("S3", 300), FI("IcHum", 300), WI("Stub1", "left", 500, 250), WI("Stub2", "left", 500, 250), WI("Stub3", "left", 500, 250), WI("Bracket", "down", 750, 400), FI("c1", 100)] },
  { hold: 0, fx: [FO("c1"), WI("ArrIn", "left", 200, 300), FI("R1", 500), FI("IcRead", 500), FI("c2", 300)] },
  { hold: 0, fx: [FO("c2"), WI("A12", "left", 200, 300), FI("R2", 500), FI("IcDraft", 500), FI("D1", 1000), FI("D2", 1200), FI("c3", 300)] },
  { hold: 0, fx: [FO("c3"), WI("A23", "left", 200, 300), FI("R3", 500), FI("IcCheck", 500), FI("T4", 1000), FI("c4", 300)] },
  { hold: 0, fx: [FO("c4"), WI("E1", "down", 200, 300), WI("E2", "right", 500, 600), WI("E3", "down", 1100, 300), FI("O1", 1400), FI("AvOwner", 1400), FI("c5", 300)] },
  { hold: 0, fx: [FO("c5"), WI("A56", "left", 200, 300), FI("O2", 500), FI("IcLink", 500), FI("K1", 1000), FI("K2", 1200), FI("c6", 300)] },
  { hold: 0, fx: [FO("c6"), FI("Gtm", 300), FI("c7", 300)] },
  { hold: 0, fx: [FO("c7"), FO("Gtm"), WI("A67", "left", 200, 300), FI("O3", 500), FI("IcBook", 500), FI("c8", 300)] },
  { hold: 0, fx: [FO("c8"), FI("Get", 300), FI("G0", 400), FI("G1", 600), FI("G2", 800), FI("G3", 1000), FI("c9", 300)] },
];

const STEP_NOTES = [
  "Today a nurse checks every case against official policy, by hand. CMS publishes national and local coverage determinations, with billing articles beside them. Federal rules sit above those. Humana has its own documents. Each one says what must be true for a service to be covered. We start from the same sources.",
  "We read each policy with an ETL step that has AI inside. It keeps the structure: titles, paragraphs, tables and the page each came from. A flat block of text would lose the sections the rules hang on.",
  "An AI drafts the rules. Each requirement becomes one rule. For each rule it names the detail a nurse needs to check, for example the ejection fraction, and copies the exact sentence the rule came from. Those details are what we later look for in the packet.",
  "Plain code checks the draft. Is the quote really in the policy? Is every number in the quote? Does the detail exist? Anything that fails is shown to the owner, never dropped. There is no AI in this step.",
  "A policy owner approves, edits or rejects every rule, with the official text beside it. The AI drafts. It never publishes. A rule that needs a detail we cannot read yet waits.",
  "Then we link it. A procedure code is the short code on every request that names the procedure. A CPT code is five digits, for example 33249 for an implantable defibrillator. A HCPCS code is a letter and four digits, used for equipment. The policy gets its codes, with their source, and joins a service. A service is any product or business name we choose for a kind of request: ICD for heart failure, lumbar fusion, CPAP. The service holds its codes, its policies and the details to look for.",
  "In production we would not onboard services at random. Humana's own history of prior authorization requests, by procedure code, gives volume, pends and reversals, so we start where it matters most. In the prototype the owner sees the same signal live, as requests without a policy.",
  "We publish one versioned library. Every version is kept, so a change can be rolled back, and every action is in an audit trail. Part two reads every packet with this library.",
  "What we get: a versioned library of services, each with its codes, policies and the details to look for. Every rule is tied to the official sentence and approved by a named owner. Every code has its source and every change is recorded. A new service goes from planned to pilot to live, and any version can be rolled back.",
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
  pres.title = "Part 1: building the library and onboarding a service";
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
    fs.writeFileSync(path.join(__dirname, "preview_onboarding.html"), preview());
    if (process.argv.includes("--steps")) [4, 6, 10, 11, 13].forEach((k) => fs.writeFileSync(path.join(__dirname, `preview_onb_s${k}.html`), preview().replace('new URLSearchParams(location.search).get("step")', `"${k}"`)));
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
  fs.writeFileSync(path.join(__dirname, "preview_onboarding.html"), preview());
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
