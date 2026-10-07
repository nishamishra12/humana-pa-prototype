const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");
const JSZip = require("jszip");
const { Resvg } = require("@resvg/resvg-js");
const OUT = path.join(__dirname, "Roadmap.pptx");
const OUT_STEPS = path.join(__dirname, "Roadmap_Steps.pptx");
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


const tile = (glyph, fill, stroke) => `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect x="3" y="3" width="94" height="94" rx="16" fill="#${fill}" stroke="#${stroke}" stroke-width="3"/>${glyph.replace(/STROKE/g, "#" + stroke)}</svg>`;
const GLY = {
  find: `<circle cx="44" cy="44" r="20" fill="none" stroke="STROKE" stroke-width="4.5"/><path d="M59 59 L78 78" stroke="STROKE" stroke-width="5" stroke-linecap="round"/><path d="M34 40 H54 M34 49 H48" stroke="STROKE" stroke-width="3.5" stroke-linecap="round"/>`,
  agree: `<circle cx="38" cy="50" r="18" fill="none" stroke="STROKE" stroke-width="4.5"/><circle cx="62" cy="50" r="18" fill="none" stroke="STROKE" stroke-width="4.5"/><path d="M42 50 L48 57 L58 43" fill="none" stroke="STROKE" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round"/>`,
  key: `<circle cx="34" cy="50" r="14" fill="none" stroke="STROKE" stroke-width="4.5"/><path d="M48 50 H80 M70 50 V63 M60 50 V58" fill="none" stroke="STROKE" stroke-width="4.5" stroke-linecap="round"/>`,
  rules: `<path d="M24 31 L30 37 L40 25 M24 51 L30 57 L40 45 M24 71 L30 77 L40 65" fill="none" stroke="STROKE" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/><path d="M50 31 H76 M50 51 H76 M50 71 H76" stroke="STROKE" stroke-width="4" stroke-linecap="round"/>`,
  chart: `<rect x="26" y="52" width="13" height="24" rx="2" fill="STROKE"/><rect x="44" y="38" width="13" height="38" rx="2" fill="STROKE"/><rect x="62" y="24" width="13" height="52" rx="2" fill="STROKE"/>`,
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


const wp = (name, key, cx, cy, s = 0.8) => { ART[name] = PEOPLE[key]; add({ name, kind: "image", static: true, x: cx - s / 2, y: cy - s / 2, w: s, h: s }); };
frame("THE ROADMAP", "Three phases over a year.", "Each phase earns the next one", "The months are illustrative. The order is the point.");
ring("Ph1", 0.5, 1.45, 5.95, 4.2, C.green);
txt("H1", 0.75, 1.62, 5.45, 0.25, ["PHASE 1   \u00b7   MONTHS 1 TO 4"], { size: 10.5, color: C.green, bold: true });
txt("T1", 0.75, 1.92, 5.45, 0.45, ["Right first time. A person decides."], { size: 20, color: C.ink });
txt("S1", 0.75, 2.36, 5.45, 0.28, ["North star: right-first-time rate. Two milestones ladder up to it."], { size: 11.5, color: C.muted, bold: true });
txt("W1", 0.75, 4.45, 5.45, 0.3, ["FOR   Nurse, provider, member, plan"], { size: 11, color: C.ink, bold: true });
add({ name: "G1", kind: "node", static: true, x: 0.7, y: 4.85, w: 5.55, h: 0.65, fill: C.greenSoft, line: C.green, lineW: 1, radius: 0.06, valign: "middle", margin: [0.03, 0.12, 0.03, 0.12], runs: [{ text: "GATE   ", options: { bold: true, fontSize: 9.5, color: C.green, fontFace: B, charSpacing: 1.5 } }, { text: "A tested rulebook. Evals on real cases. Zero wrong approvals.", options: { fontSize: 11, color: C.ink, fontFace: B } }] });
add({ name: "M1", kind: "node", static: true, x: 0.75, y: 2.75, w: 2.6, h: 1.55, fill: C.white, line: C.green, lineW: 1.25, radius: 0.08, valign: "top", margin: [0.1, 0.12, 0.05, 0.12], runs: [{ text: "MILESTONE 1", options: { bold: true, fontSize: 9, color: C.green, fontFace: B, charSpacing: 1.5, breakLine: true } }, { text: "Build the rulebook", options: { bold: true, fontSize: 14, color: C.ink, fontFace: B, breakLine: true } }, { text: "Onboard a service. Attach its policies. Turn each policy into a checklist of what it wants to see.", options: { fontSize: 11.5, color: C.muted, fontFace: B } }] });
add({ name: "M2", kind: "node", static: true, x: 3.55, y: 2.75, w: 2.6, h: 1.55, fill: C.white, line: C.green, lineW: 1.25, radius: 0.08, valign: "top", margin: [0.1, 0.12, 0.05, 0.12], runs: [{ text: "MILESTONE 2", options: { bold: true, fontSize: 9, color: C.green, fontFace: B, charSpacing: 1.5, breakLine: true } }, { text: "Recommend on every request", options: { bold: true, fontSize: 14, color: C.ink, fontFace: B, breakLine: true } }, { text: "The AI checks each request against the rulebook, with evidence. The nurse confirms.", options: { fontSize: 11.5, color: C.muted, fontFace: B } }] });
seg("mA", 3.35, 3.5, 3.55, 3.5, true);
ring("Ph2", 6.75, 1.45, 3.05, 4.2, C.purple);
txt("H2", 7.0, 1.62, 2.55, 0.25, ["PHASE 2   \u00b7   MONTHS 5 TO 9"], { size: 10.5, color: C.purple, bold: true });
txt("T2", 7.0, 1.92, 2.55, 0.45, ["Scale. Edge cases."], { size: 20, color: C.ink });
txt("B2", 7.0, 2.72, 2.55, 1.6, ["More services, ranked by Humana's request history.", " ", "Edge case: every rule met, but the procedure is not covered.", " ", "Edge case: checking the provider and the facility."], { size: 12, color: C.ink });
txt("W2", 7.0, 4.45, 2.55, 0.3, ["FOR   The plan, the director"], { size: 11, color: C.ink, bold: true });
add({ name: "G2", kind: "node", static: true, x: 6.95, y: 4.85, w: 2.65, h: 0.65, fill: C.purpleSoft, line: C.purple, lineW: 1, radius: 0.06, valign: "middle", margin: [0.03, 0.12, 0.03, 0.12], runs: [{ text: "GATE   ", options: { bold: true, fontSize: 9.5, color: C.purple, fontFace: B, charSpacing: 1.5 } }, { text: "Evals on real cases for each new service.", options: { fontSize: 11, color: C.ink, fontFace: B } }] });
ring("Ph3", 10.1, 1.45, 2.73, 4.2, C.amber);
txt("H3", 10.35, 1.62, 2.23, 0.25, ["PHASE 3   \u00b7   MONTHS 10 TO 12"], { size: 10.5, color: C.amber, bold: true });
txt("T3", 10.35, 1.92, 2.23, 0.45, ["Member status."], { size: 20, color: C.ink });
txt("B3", 10.35, 2.75, 2.23, 1.5, ["The member sees where a request stands. It reads the trusted record."], { size: 13, color: C.ink });
txt("W3", 10.35, 4.45, 2.23, 0.3, ["FOR   The member"], { size: 11, color: C.ink, bold: true });
add({ name: "G3", kind: "node", static: true, x: 10.299999999999999, y: 4.85, w: 2.33, h: 0.65, fill: C.amberSoft, line: C.amber, lineW: 1, radius: 0.06, valign: "middle", margin: [0.03, 0.12, 0.03, 0.12], runs: [{ text: "GATE   ", options: { bold: true, fontSize: 9.5, color: C.amber, fontFace: B, charSpacing: 1.5 } }, { text: "A compliance review.", options: { fontSize: 11, color: C.ink, fontFace: B } }] });
seg("pA", 6.47, 3.5, 6.73, 3.5, true);  seg("pB", 9.82, 3.5, 10.08, 3.5, true);

add({ name: "Band", kind: "node", static: true, x: 0.5, y: 5.88, w: 12.33, h: 0.5, fill: C.green, line: C.green, lineW: 1, radius: 0.08, align: "center", valign: "middle", margin: [0.02, 0.15, 0.02, 0.15],
  runs: [{ text: "A person decides in every phase. The AI never denies.", options: { bold: true, fontSize: 14, color: C.white, fontFace: B } }] });

const slots = [
  { hold: 0, fx: [] },
];
const STEP_NOTES = [
 "This is the roadmap. Three phases, about a year. The months are illustrative. The order is what matters. Each phase earns the next one.\n\nWe start with Phase 1. It has one goal: get each request right the first time, with a person still deciding. My north star here is the right-first-time rate. Out of every 100 requests, how many are right the first time, with no back and forth?\n\nPhase 1 has two milestones.\n\nMilestone 1 is building the rulebook. Here we onboard a new service. We attach every policy that applies to it. Then we turn each policy into a checklist. The checklist says what the policy wants to see in a request. This is the foundation that the AI in milestone 2 uses.\n\nMilestone 2 is the recommendation. The AI checks every request against the rulebook we created in milestone 1. It recommends what to do, with the evidence from the packet, and gives it to the nurse. The nurse stops hunting. The provider stops re-sending. And the request gets decided faster.\n\nPhase 2 is scale, plus a few more features. We onboard more services, ranked by Humana's own request history. And we handle a few edge cases. One is where every clinical rule is met, but the procedure isn't covered. The system will suggest the usual next step, like a covered alternative. The other is checking the provider and the facility, for the things a fax can't tell us.\n\nPhase 3 is member status. The member sees where a request stands. It comes last because a status is only as good as the record behind it.\n\nSo: prove it's right, then widen it, then show it to the member. And a person decides in every phase.\n\nNow let me walk you through our personas in Phase 1."
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
      s.addShape(pres.ShapeType.roundRect, { x: o.x, y: o.y, w: o.w, h: o.h, rectRadius: 0.1, fill: { type: "none" }, line: { color: o.line, width: o.lineW, dashType: o.dash || "solid" }, objectName: o.name });
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
  pres.title = "The roadmap";
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
    fs.writeFileSync(path.join(__dirname, "preview_Roadmap.html"), preview());
    if (process.argv.includes("--steps")) [4, 6, 10, 11, 13].forEach((k) => fs.writeFileSync(path.join(__dirname, `Roadmap_s${k}.html`), preview().replace('new URLSearchParams(location.search).get("step")', `"${k}"`)));
    console.log("wrote", OUT_STEPS, "|", slots.length, "slides, press Next to walk through");
    return;
  }

  const s = pres.addSlide();
  s.background = { color: C.white };
  draw(pres, s, PNG, null);
  s.addNotes(STEP_NOTES.join(String.fromCharCode(10, 10)));
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
  fs.writeFileSync(path.join(__dirname, "preview_Roadmap.html"), preview());
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
    if (o.kind === "ring") return `<div data-n="${o.name}" style="position:absolute;${base}border:${o.lineW}px ${o.dash ? "dashed" : "solid"} #${o.line};border-radius:10px;box-sizing:border-box"></div>`;
    const m = o.margin ? o.margin.map((v) => v * px) : [0, 0, 0, 0];
    const box = o.kind === "node" ? `background:#${o.fill};border:${o.lineW}px solid #${o.line};border-radius:${(o.radius ?? 0.08) * px}px;` : "";
    return `<div data-n="${o.name}" style="position:absolute;${base}${box}box-sizing:border-box;overflow:hidden;display:flex;flex-direction:column;justify-content:${o.valign === "top" ? "flex-start" : "center"};text-align:${o.align || "left"};padding:${m[0]}px ${m[1]}px ${m[2]}px ${m[3]}px;line-height:1.15"><div>${inner}</div></div>`;
  }).join("\n");
  const data = JSON.stringify(slots.map((sl) => sl.fx.map((e) => [e.name, e.t])));
  const script = `<script>const S=${data};const q=new URLSearchParams(location.search).get("step");if(q!==null){const k=+q;const vis={};const all=new Set(S.flat().map(e=>e[0]));S.slice(0,k).forEach(sl=>sl.forEach(([n,t])=>{vis[n]=t!=="fadeOut"}));document.querySelectorAll("[data-n]").forEach(el=>{const n=el.dataset.n;if(all.has(n)&&!vis[n])el.style.display="none"})}</script>`;
  return `<!doctype html><meta charset="utf-8"><body style="margin:0;background:#fff"><div style="position:relative;width:${13.333 * px}px;height:${7.5 * px}px;background:#fff">${html}</div>${script}`;
}


main().catch((e) => { console.error(e); process.exit(1); });
