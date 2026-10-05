// Builds ONE animated slide: phase 2.
// Same method and look as build_friction.js and build_journey.js: one slide, one click per step, nothing plays by itself.
// Run:  NODE_PATH=<folder with @resvg/resvg-js> node build_phase2.js   -> Phase_2.pptx + preview_phase2.html
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");
const JSZip = require("jszip");
const { Resvg } = require("@resvg/resvg-js"); // draws the SVG art to PNG (npm i @resvg/resvg-js)

const OUT = path.join(__dirname, "Phase_2.pptx"); // default: ONE slide, one click per step
const OUT_STEPS = path.join(__dirname, "Phase_2_Steps.pptx"); // only with --slides: one slide per step
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

const disc = (bg, glyph) => `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="48" fill="#${bg}"/>${glyph}</svg>`;
const G = {
  check: `<path d="M50 20 L75 30 V52 C75 67 63 75 50 81 C37 75 25 67 25 52 V30Z" fill="#FFFFFF" stroke="#1F6F5C" stroke-width="3.5"/><path d="M37 50 L47 60 L64 40" fill="none" stroke="#1F6F5C" stroke-width="5.5" stroke-linecap="round" stroke-linejoin="round"/>`,
  doc: `<rect x="32" y="22" width="36" height="50" rx="3" fill="#FFFFFF" stroke="#B8452F" stroke-width="3"/><path d="M39 35h22M39 45h22M39 55h14" stroke="#B8452F" stroke-width="3"/>`,
  link: `<rect x="20" y="40" width="36" height="20" rx="10" fill="none" stroke="#1F6F5C" stroke-width="5.5"/><rect x="44" y="40" width="36" height="20" rx="10" fill="none" stroke="#1F6F5C" stroke-width="5.5"/>`,
  lock: `<rect x="31" y="46" width="38" height="30" rx="5" fill="#B8452F"/><path d="M38 46 V38 a12 12 0 0 1 24 0 V46" fill="none" stroke="#B8452F" stroke-width="6"/><circle cx="50" cy="61" r="4" fill="#FFFFFF"/>`,
  loop: `<path d="M71 40 A22 22 0 1 0 72 60" fill="none" stroke="#5F3AA8" stroke-width="6.5" stroke-linecap="round"/><path d="M60 30 L72 40 L58 47" fill="none" stroke="#5F3AA8" stroke-width="6.5" stroke-linecap="round" stroke-linejoin="round"/>`,
};
const ART = {
  IcA1: disc("E3F0EB", G.check), IcA2: disc("FBE9E4", G.doc), IcA3: disc("E3F0EB", G.link),
  IcGate: disc("FBE9E4", G.lock), IcB1: disc("E3F0EB", G.link),
  AvM: person({ bg: "E8E4DC", skin: SKIN.d, hair: "D5D8DC", style: "short", top: "8A9A5B" }),
  IcB3: disc("EBE2F8", G.loop),
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
const node = (name, x, y, w, h, title, desc, o = {}) => add({ name, kind: "node", x, y, w, h, fill: o.fill || C.white, line: o.line || C.line, lineW: o.lineW || 1.25, radius: 0.08, runs: runs(title, desc, o.tc || C.ink, o.ts || 14, o.ds || 11, o.dc || C.muted), margin: o.margin || [0.04, 0.1, 0.04, 0.85], align: o.align });
const caption = (name, text) => add({ name, kind: "text", x: 0.5, y: 6.5, w: 12.33, h: 0.65, valign: "middle", runs: [{ text, options: { fontSize: 16, color: C.ink, fontFace: B } }] });

// static frame
add({ name: "eyebrow", kind: "text", static: true, x: 0.5, y: 0.3, w: 5, h: 0.28, runs: [{ text: "PHASE 2", options: { bold: true, fontSize: 11, color: C.green, fontFace: B, charSpacing: 3 } }] });
add({ name: "title", kind: "text", static: true, x: 0.5, y: 0.55, w: 9.6, h: 0.75, valign: "middle", runs: [{ text: "Phase 1 builds the record. Phase 2 puts it to work.", options: { fontSize: 26, color: C.ink, fontFace: H } }] });
add({ name: "sub", kind: "text", static: true, x: 10.0, y: 0.55, w: 2.83, h: 0.75, align: "right", valign: "middle", runs: [{ text: "Every phase has a reason", options: { fontSize: 14, color: C.muted, fontFace: B } }] });
add({ name: "panelP1", kind: "node", static: true, x: 0.5, y: 1.45, w: 3.7, h: 4.3, fill: C.provPanel, line: C.line, lineW: 1, radius: 0.1, runs: [{ text: " ", options: { fontSize: 8 } }] });
add({ name: "panelP2", kind: "node", static: true, x: 6.55, y: 1.45, w: 6.28, h: 4.3, fill: C.payPanel, line: C.line, lineW: 1, radius: 0.1, runs: [{ text: " ", options: { fontSize: 8 } }] });
add({ name: "hdrP1", kind: "text", static: true, x: 0.7, y: 1.52, w: 3.4, h: 0.55, runs: [{ text: "PHASE 1  ·  THIS PROTOTYPE", options: { bold: true, fontSize: 11, color: C.ink, fontFace: B, charSpacing: 2, breakLine: true } }, { text: "Recommend only", options: { fontSize: 10, color: C.muted, fontFace: B } }] });
add({ name: "hdrP2", kind: "text", static: true, x: 6.75, y: 1.52, w: 5.9, h: 0.55, runs: [{ text: "PHASE 2  ·  AFTER THE GATE", options: { bold: true, fontSize: 11, color: C.ink, fontFace: B, charSpacing: 2, breakLine: true } }, { text: "Earned, one step at a time", options: { fontSize: 10, color: C.muted, fontFace: B } }] });
add({ name: "footer", kind: "text", static: true, x: 0.5, y: 7.1, w: 12.33, h: 0.25, runs: [{ text: "Phase 2 is a plan, not built. Each step waits for its gate.", options: { fontSize: 9, color: C.muted, fontFace: B } }] });

// phase 1
const PY = [2.15, 3.35, 4.55];
const ndesc = (n, x, y, w, h, title, desc, art, o = {}) => { node(n, x, y, w, h, title, desc, o); avatar(art, x + 0.12, y + 0.22, 0.6); };
ndesc("A1", 0.7, PY[0], 3.3, 1.05, "Recommend only", "The AI recommends with citations. The nurse confirms.", "IcA1", { ts: 13.5, ds: 10.5 });
ndesc("A2", 0.7, PY[1], 3.3, 1.05, "No more pend loops", "A missing detail is found at once, as one question.", "IcA2", { ts: 13.5, ds: 10.5 });
ndesc("A3", 0.7, PY[2], 3.3, 1.05, "One service at a time", "Planned, then pilot, then live.", "IcA3", { ts: 13.5, ds: 10.5 });

// the gate
add({ name: "Gate", kind: "node", x: 4.45, y: 2.15, w: 1.9, h: 3.45, fill: C.coralSoft, line: C.coral, lineW: 1.5, radius: 0.1, valign: "top", align: "center", margin: [1.0, 0.1, 0.05, 0.1], runs: [
  { text: "THE GATE", options: { bold: true, fontSize: 11, color: C.coral, fontFace: B, charSpacing: 2, breakLine: true } },
  { text: " ", options: { fontSize: 6, breakLine: true } },
  { text: "Evals on real, labeled cases", options: { fontSize: 10.5, color: C.ink, fontFace: B, breakLine: true } },
  { text: " ", options: { fontSize: 6, breakLine: true } },
  { text: "A compliance review for anything the member sees", options: { fontSize: 10.5, color: C.ink, fontFace: B } }] });
avatar("IcGate", 5.1, 2.3, 0.6);
line("ArrIn", 4.2, 3.875, 0.25, 0);
line("ArrOut", 6.35, 3.875, 0.2, 0);

// phase 2
const QY = [2.15, 3.35, 4.55];
ndesc("B1", 6.75, QY[0], 5.9, 1.05, "The member sees where the request stands", "Fed by the decision record from phase 1. Patient Access API, January 2027.", "AvM");
ndesc("B2", 6.75, QY[1], 5.9, 1.05, "Learn from outcomes", "Denial and appeal results feed back into the rules and the evals.", "IcB3");
ndesc("B3", 6.75, QY[2], 5.9, 1.05, "More services", "Onboard the next ones, ranked by Humana's request history.", "IcB1");

add({ name: "Never", kind: "node", x: 0.5, y: 5.88, w: 12.33, h: 0.5, fill: C.green, line: C.green, lineW: 1, radius: 0.08, align: "center", margin: [0.03, 0.2, 0.03, 0.2], runs: [{ text: "In every phase, a person decides.  ", options: { bold: true, fontSize: 14, color: C.white, fontFace: B } }, { text: "The AI never denies and never approves on its own.", options: { fontSize: 12, color: "D5EBE3", fontFace: B } }] });

const CAPS = {
  c1: "Phase 1 is what you have seen. The AI recommends with citations and the nurse confirms. It removes the pend and builds the decision record.",
  c2: "Phase 2 has a gate: evals on real labeled cases, and a compliance review for anything the member sees.",
  c3: "First: the member sees where the request stands. The decision record from phase 1 feeds it.",
  c4: "Second: learn from outcomes. Denial and appeal results feed back into the rules and the evals.",
  c5: "Third: more services, ranked by Humana's own request history.",
  c6: "In every phase, a person decides. The AI never denies and never approves on its own.",
};
Object.entries(CAPS).forEach(([k, v]) => caption(k, v));

const FI = (name, delay = 0, dur = 500) => ({ t: "fadeIn", name, delay, dur });
const FO = (name, delay = 0, dur = 300) => ({ t: "fadeOut", name, delay, dur });
const WI = (name, dir, delay = 0, dur = 600) => ({ t: "wipeIn", name, dir, delay, dur });
const slots = [
  { hold: 0, fx: [FI("A1"), FI("IcA1"), FI("A2", 200), FI("IcA2", 200), FI("A3", 400), FI("IcA3", 400), FI("c1", 100)] },
  { hold: 0, fx: [FO("c1"), WI("ArrIn", "left", 200, 300), FI("Gate", 500), FI("IcGate", 500), WI("ArrOut", "left", 1000, 300), FI("c2", 300)] },
  { hold: 0, fx: [FO("c2"), FI("B1", 300), FI("AvM", 300), FI("c3", 300)] },
  { hold: 0, fx: [FO("c3"), FI("B2", 300), FI("IcB3", 300), FI("c4", 300)] },
  { hold: 0, fx: [FO("c4"), FI("B3", 300), FI("IcB1", 300), FI("c5", 300)] },
  { hold: 0, fx: [FO("c5"), FI("Never", 300), FI("c6", 300)] },
];
const STEP_NOTES = [
  "Phase one is what you have just seen. The AI recommends, with citations, and the nurse confirms. It removes the pend. A missing detail is found at the start, as one precise question, not after a loop. I add services one at a time, planned, then pilot, then live. And it builds something that matters for what comes next: a trusted record of every decision, with its evidence.",
  "Phase two has a gate. I do not build the next layer on a record I have not tested. First, evals on real, labeled cases, not made-up ones. Second, a compliance review for anything the member sees. Until the gate opens, nothing in phase two goes live.",
  "First, the member. In friction six, the member waits with no view. I did not build it first, because a status is only as good as the record behind it. The decision record that phase one creates is exactly what the member view reads. And from January 2027, plans must offer a Patient Access API with prior authorization information, so this is on the way regardless.",
  "Second, learn from outcomes. When a denial is appealed and overturned, I want to know whether the packet already had the answer. That result feeds back into the rules and the evals. That is the full version of right-first-time.",
  "Third, more services. I onboard them one at a time, ranked by Humana's own history of prior authorization requests: volume, pends and reversals by procedure code. The process is the one you saw: policy, codes, service, pilot, live.",
  "And in every phase a person decides. The AI never denies, and it never approves on its own. A nurse confirms every recommendation. Only a medical director denies, and writes the reason.",
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
  pres.title = "Phase 2";
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
    fs.writeFileSync(path.join(__dirname, "preview_phase2.html"), preview());
    if (process.argv.includes("--steps")) [4, 6, 10, 11, 13].forEach((k) => fs.writeFileSync(path.join(__dirname, `Phase_2_s${k}.html`), preview().replace('new URLSearchParams(location.search).get("step")', `"${k}"`)));
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
  fs.writeFileSync(path.join(__dirname, "preview_phase2.html"), preview());
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
