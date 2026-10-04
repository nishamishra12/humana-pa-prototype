// Builds ONE animated slide: Part 2 of the product, how a packet moves through PA Desk.
// Same method and look as build_friction.js and build_journey.js: one slide, one click per step, nothing plays by itself.
// Run:  NODE_PATH=<folder with @resvg/resvg-js> node build_packet.js   -> Packet_Journey.pptx + preview_packet.html
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");
const JSZip = require("jszip");
const { Resvg } = require("@resvg/resvg-js"); // draws the SVG art to PNG (npm i @resvg/resvg-js)

const OUT = path.join(__dirname, "Packet_Journey.pptx"); // default: ONE slide, one click per step
const OUT_STEPS = path.join(__dirname, "Packet_Journey_Steps.pptx"); // only with --slides: one slide per step
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
  doc: `<rect x="32" y="22" width="36" height="50" rx="3" fill="#FFFFFF" stroke="#B8452F" stroke-width="3"/><path d="M39 35h22M39 45h22M39 55h14" stroke="#B8452F" stroke-width="3"/>`,
  search: `<circle cx="44" cy="44" r="17" fill="#FFFFFF" stroke="#1F6F5C" stroke-width="5"/><path d="M57 57 L76 76" stroke="#1F6F5C" stroke-width="6.5" stroke-linecap="round"/>`,
  spark: `<path d="M50 20 L57 43 L80 50 L57 57 L50 80 L43 57 L20 50 L43 43Z" fill="#5F3AA8"/><circle cx="74" cy="26" r="5" fill="#5F3AA8"/>`,
  check: `<path d="M50 20 L75 30 V52 C75 67 63 75 50 81 C37 75 25 67 25 52 V30Z" fill="#FFFFFF" stroke="#1F6F5C" stroke-width="3.5"/><path d="M37 50 L47 60 L64 40" fill="none" stroke="#1F6F5C" stroke-width="5.5" stroke-linecap="round" stroke-linejoin="round"/>`,
  rules: `<rect x="26" y="24" width="48" height="52" rx="4" fill="#FFFFFF" stroke="#1F6F5C" stroke-width="3.5"/><path d="M34 40 l5 5 l9 -10 M34 58 l5 5 l9 -10" fill="none" stroke="#1F6F5C" stroke-width="4" stroke-linecap="round"/><path d="M55 41h13M55 59h13" stroke="#1F6F5C" stroke-width="4"/>`,
};
const ART = {
  AvProv: building,
  AvIntake: person({ bg: "D8EAE3", skin: SKIN.a, hair: "6B4226", style: "bun", top: "3C6E8F", acc: "clip" }),
  IcRead: disc("FBE9E4", G.doc),
  IcFind: disc("E3F0EB", G.search),
  IcDetail: disc("EBE2F8", G.spark),
  IcEvid: disc("E3F0EB", G.check),
  IcRules: disc("E3F0EB", G.rules),
  AvNurse: person({ bg: "CDE8E0", skin: SKIN.c, hair: "2B2B2B", style: "short", top: "2F8F83", acc: "nurse" }),
  AvMD: person({ bg: "E3D9F5", skin: SKIN.d, hair: "4A3B32", style: "short", top: "5F3AA8", coat: true, acc: "doctor" }),
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
const pkt = (name, x, y) => add({ name, kind: "node", x, y, w: 0.95, h: 0.36, fill: C.white, line: C.coral, lineW: 1.5, radius: 0.06, align: "center", margin: [0, 0, 0, 0], runs: [{ text: "14 pages", options: { bold: true, fontSize: 10, color: C.coral, fontFace: B } }] });
const caption = (name, text) => add({ name, kind: "text", x: 0.5, y: 6.5, w: 12.33, h: 0.65, valign: "middle", runs: [{ text, options: { fontSize: 16, color: C.ink, fontFace: B } }] });

// static frame
add({ name: "eyebrow", kind: "text", static: true, x: 0.5, y: 0.3, w: 5, h: 0.28, runs: [{ text: "THE PRODUCT, PART 2 OF 2", options: { bold: true, fontSize: 11, color: C.green, fontFace: B, charSpacing: 3 } }] });
add({ name: "title", kind: "text", static: true, x: 0.5, y: 0.55, w: 8.4, h: 0.75, valign: "middle", runs: [{ text: "Then every packet is read with that library.", options: { fontSize: 26, color: C.ink, fontFace: H } }] });
add({ name: "sub", kind: "text", static: true, x: 8.6, y: 0.55, w: 4.23, h: 0.75, align: "right", valign: "middle", runs: [{ text: "The AI reads and cites. Code decides.", options: { fontSize: 14, color: C.muted, fontFace: B } }] });
add({ name: "panelSrc", kind: "node", static: true, x: 0.5, y: 1.45, w: 3.3, h: 4.85, fill: C.provPanel, line: C.line, lineW: 1, radius: 0.1, runs: [{ text: " ", options: { fontSize: 8 } }] });
add({ name: "panelApp", kind: "node", static: true, x: 4.15, y: 1.45, w: 8.68, h: 4.85, fill: C.payPanel, line: C.line, lineW: 1, radius: 0.1, runs: [{ text: " ", options: { fontSize: 8 } }] });
add({ name: "hdrSrc", kind: "text", static: true, x: 0.7, y: 1.52, w: 2.9, h: 0.55, runs: [{ text: "PROVIDER AND INTAKE", options: { bold: true, fontSize: 11, color: C.ink, fontFace: B, charSpacing: 3, breakLine: true } }, { text: "Nothing changes here", options: { fontSize: 10, color: C.muted, fontFace: B } }] });
add({ name: "hdrApp", kind: "text", static: true, x: 4.4, y: 1.52, w: 8.2, h: 0.55, runs: [{ text: "PA DESK", options: { bold: true, fontSize: 11, color: C.ink, fontFace: B, charSpacing: 3, breakLine: true } }, { text: "Every packet is read with the approved library", options: { fontSize: 10, color: C.muted, fontFace: B } }] });
add({ name: "footer", kind: "text", static: true, x: 0.5, y: 7.1, w: 12.33, h: 0.25, runs: [{ text: "All packets are made up. The reader and the evidence check use an AI model. The rules engine is plain code and cannot deny.", options: { fontSize: 9, color: C.muted, fontFace: B } }] });
add({ name: "leftNote", kind: "text", static: true, x: 0.7, y: 5.1, w: 2.9, h: 1.0, runs: [{ text: "Nothing changes for the provider or for intake. What changes is what happens next.", options: { italic: true, fontSize: 11.5, color: C.muted, fontFace: B } }] });

// provider and intake
node("L1", 0.7, 2.2, 2.9, 1.05, "Provider's office", "Sends the request packet by fax or portal");
avatar("AvProv", 0.82, 2.42, 0.6);
node("L2", 0.7, 3.6, 2.9, 1.05, "Intake coordinator", "Uploads one PDF, up to 15 MB");
avatar("AvIntake", 0.82, 3.82, 0.6);
pkt("P1", 2.5, 4.47);
line("AL", 2.15, 3.25, 0, 0.35);
line("Stub", 3.6, 4.125, 0.35, 0, { arrow: false });
line("Up", 3.95, 2.625, 0, 1.5, { arrow: false });
line("ArrIn", 3.95, 2.625, 0.45, 0);

// inside PA Desk
const CX = [4.4, 7.25, 10.1], CW = 2.5, R1 = 2.15, R2 = 3.9, RH = 0.95;
const ndesc = (n, x, y, title, desc, art, o = {}) => { node(n, x, y, CW, RH, title, desc, { margin: [0.04, 0.08, 0.04, 0.85], ...o }); avatar(art, x + 0.12, y + 0.17, 0.6); };
ndesc("N1", CX[0], R1, "Read the pages", "ETL + AI picks how to read each page and splits it into pieces", "IcRead");
ndesc("N2", CX[1], R1, "Find the service", "The procedure code on the request picks it", "IcFind");
ndesc("N3", CX[2], R1, "Read the details", "AI fills one form. Three reads must agree", "IcDetail");
line("A12", CX[0] + CW + 0.02, R1 + RH / 2, 0.31, 0);
line("A23", CX[1] + CW + 0.02, R1 + RH / 2, 0.31, 0);
chip("C1", CX[0] + 0.05, R1 + RH + 0.08, 1.15, "Typed pieces");
chip("C2", CX[0] + 1.3, R1 + RH + 0.08, 1.15, "Page and box");
add({ name: "T3", kind: "text", x: CX[1], y: R1 + RH + 0.05, w: CW, h: 0.42, runs: [{ text: "No service for the code? Flagged 'No policy yet'. Nothing is guessed.", options: { bold: true, fontSize: 9.5, color: C.coral, fontFace: B } }] });
chip("C4", CX[2] + 0.05, R1 + RH + 0.08, 1.15, "Never guesses");
line("E1", CX[2] + CW / 2 + 0.3, R1 + RH, 0, 0.58, { arrow: false });
line("E2", CX[0] + CW / 2, R1 + RH + 0.58, CX[2] + CW / 2 + 0.3 - (CX[0] + CW / 2), 0, { arrow: false });
line("E3", CX[0] + CW / 2, R1 + RH + 0.58, 0, R2 - (R1 + RH + 0.58));
ndesc("N4", CX[0], R2, "Check the evidence", "Code finds each quote on its page. A second AI checks it", "IcEvid");
ndesc("N5", CX[1], R2, "Apply the rules", "Plain code compares the details with the approved rules", "IcRules");
ndesc("N6", CX[2], R2, "The nurse confirms", "Sees a cited checklist and a recommendation", "AvNurse");
line("A45", CX[0] + CW + 0.02, R2 + RH / 2, 0.31, 0);
line("A56", CX[1] + CW + 0.02, R2 + RH / 2, 0.31, 0);

// the three ways out, then the medical director
const FY = 5.12, OY = 5.42, OH = 0.78;
const OX = [4.4, 6.4, 8.45], OW = 1.9;
line("Fork1", CX[2] + 0.2 + 1.15, R2 + RH, 0, FY - (R2 + RH), { arrow: false });
line("Fork2", OX[0] + OW / 2, FY, CX[2] + 1.35 - (OX[0] + OW / 2), 0, { arrow: false });
OX.forEach((x, i) => line("Drop" + i, x + OW / 2, FY, 0, OY - FY));
add({ name: "OutApprove", kind: "node", x: OX[0], y: OY, w: OW, h: OH, fill: C.okSoft, line: C.ok, lineW: 1, runs: runs("Approve", "Every rule is met", C.ok, 13, 10, C.ok), margin: [0.04, 0.12, 0.04, 0.14] });
add({ name: "OutPend", kind: "node", x: OX[1], y: OY, w: OW, h: OH, fill: C.amberSoft, line: C.amber, lineW: 1, runs: runs("Pend", "One question to the provider", C.amber, 13, 10, C.amber), margin: [0.04, 0.12, 0.04, 0.14] });
add({ name: "OutEsc", kind: "node", x: OX[2], y: OY, w: OW, h: OH, fill: C.purpleSoft, line: C.purple, lineW: 1, runs: runs("Escalate", "Needs a physician", C.purple, 13, 10, C.purple), margin: [0.04, 0.12, 0.04, 0.14] });
line("ArrMD", OX[2] + OW + 0.02, OY + OH / 2, 0.23, 0, { color: C.purple });
node("MD", 10.6, OY, 2.0, OH, "Medical director", "Only role that can deny", { fill: C.purpleSoft, line: C.purple, tc: C.purple, ts: 12.5, ds: 10, margin: [0.03, 0.08, 0.03, 0.7] });
avatar("AvMD", 10.68, OY + 0.14, 0.5);

const CAPS = {
  c1: "A provider sends the request packet by fax or portal. The intake coordinator uploads it as one PDF. Nothing changes here.",
  c2: "An ETL step with AI inside chooses how to read each page, typed text or scan, and splits it into typed pieces with their place on the page.",
  c3: "The procedure code on the request picks the service. If no service uses it, the case is flagged 'No policy yet'. Nothing is guessed.",
  c4: "An AI fills one form, the details this service needs. It reads three times and the answers must agree. If it cannot tell, it says so.",
  c5: "Plain code finds each quoted sentence on its page. A second AI call checks that the sentence supports the claim.",
  c6: "The rules engine is plain code. Missing: pend. Unsure: verify. A rule not met: escalate. All met: approve. There is no deny.",
  c7: "The nurse sees a checklist with the evidence beside each item. There are three ways out.",
  c8: "Hard cases go to a medical director. Only a medical director can deny, and writes the reason.",
  c9: "The AI reads and cites. Code decides. A nurse confirms. Only a medical director can deny.",
};
Object.entries(CAPS).forEach(([k, v]) => caption(k, v));

/* ---------- timeline: one click per slot. Nothing plays by itself. ---------- */
const FI = (name, delay = 0, dur = 500) => ({ t: "fadeIn", name, delay, dur });
const FO = (name, delay = 0, dur = 300) => ({ t: "fadeOut", name, delay, dur });
const WI = (name, dir, delay = 0, dur = 600) => ({ t: "wipeIn", name, dir, delay, dur });
const slots = [
  { hold: 0, fx: [FI("L1"), FI("AvProv"), WI("AL", "down", 300, 300), FI("L2", 500), FI("AvIntake", 500), FI("P1", 900), WI("Stub", "left", 1100, 250), WI("Up", "up", 1300, 400), WI("ArrIn", "left", 1700, 300), FI("c1", 100)] },
  { hold: 0, fx: [FO("c1"), FO("P1", 200), FI("N1", 400), FI("IcRead", 400), FI("C1", 1000), FI("C2", 1200), FI("c2", 300)] },
  { hold: 0, fx: [FO("c2"), WI("A12", "left", 200, 300), FI("N2", 500), FI("IcFind", 500), FI("T3", 1000), FI("c3", 300)] },
  { hold: 0, fx: [FO("c3"), WI("A23", "left", 200, 300), FI("N3", 500), FI("IcDetail", 500), FI("C4", 1000), FI("c4", 300)] },
  { hold: 0, fx: [FO("c4"), WI("E1", "down", 200, 300), WI("E2", "right", 500, 600), WI("E3", "down", 1100, 300), FI("N4", 1400), FI("IcEvid", 1400), FI("c5", 300)] },
  { hold: 0, fx: [FO("c5"), WI("A45", "left", 200, 300), FI("N5", 500), FI("IcRules", 500), FI("c6", 300)] },
  { hold: 0, fx: [FO("c6"), WI("A56", "left", 200, 300), FI("N6", 500), FI("AvNurse", 500), WI("Fork1", "down", 1000, 250), WI("Fork2", "right", 1250, 500), WI("Drop0", "down", 1750, 250), WI("Drop1", "down", 1750, 250), WI("Drop2", "down", 1750, 250), FI("OutApprove", 2000), FI("OutPend", 2000), FI("OutEsc", 2000), FI("c7", 300)] },
  { hold: 0, fx: [FO("c7"), WI("ArrMD", "left", 200, 250), FI("MD", 500), FI("AvMD", 500), FI("c8", 300)] },
  { hold: 0, fx: [FO("c8"), FI("c9", 300)] },
];

const STEP_NOTES = [
  "A provider sends the request packet by fax or portal. The intake coordinator uploads it as one PDF, up to fifteen megabytes. Nothing about the provider's side or intake changes. What changes is what happens next.",
  "The PDF goes through an ETL step that has AI inside, the Unstructured partitioner. It looks at the document and decides how to read each page: as typed text, or as a scan that needs optical character recognition. It partitions the page into pieces, works out where each piece sits, the bounding box, and labels each one: title, paragraph, table. The output is a list of typed pieces, each with its page and position. Everything after this works from that list.",
  "Next, the service. The procedure code on the request is matched to a service in the approved library. If no service uses that code, the packet is flagged 'No policy yet'. Nothing is guessed. The nurse decides, and the policy owner sees the demand on the requests-without-a-policy page.",
  "An AI reads the packet and fills one form, the details this service needs, for example the ejection fraction. It reads three times and the answers must agree. Where it counts dates, our code does the counting. If it cannot tell, it says so. It never guesses.",
  "Then we check the evidence. For every detail, plain code finds the quoted sentence on its page. A second AI call checks that the sentence really supports the claim. If not, the detail loses its tick and the nurse sees that.",
  "The rules engine is plain code. It compares the details with the approved rules. A missing detail means pend. An unclear one means verify. A rule that is not met means escalate. Everything met means approve. The same details always give the same answer. There is no deny in its vocabulary.",
  "The nurse sees a checklist with the evidence beside each item and a recommendation. There are three ways out. Approve, when everything is met. Pend, with one precise question to the provider. Or escalate, when a physician's judgment is needed.",
  "Hard cases go to a medical director, with the evidence already attached. Only a medical director can deny, and writes the reason.",
  "The point to land: the AI reads and cites. Code decides. A nurse confirms. A medical director alone can deny.",
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
  pres.title = "Part 2: how a packet moves through PA Desk";
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
    fs.writeFileSync(path.join(__dirname, "preview_packet.html"), preview());
    if (process.argv.includes("--steps")) [4, 6, 10, 11, 13].forEach((k) => fs.writeFileSync(path.join(__dirname, `preview_pkt_s${k}.html`), preview().replace('new URLSearchParams(location.search).get("step")', `"${k}"`)));
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
  fs.writeFileSync(path.join(__dirname, "preview_packet.html"), preview());
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
