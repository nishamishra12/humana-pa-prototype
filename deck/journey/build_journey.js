// Builds ONE animated slide: how a prior authorization moves today.
// Run:  node build_journey.js        -> Journey_Animation.pptx + preview.html (static layout check)
// The animation is written straight into the slide XML (pptxgenjs cannot do animations).
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");
const JSZip = require("jszip");

const OUT = path.join(__dirname, "Journey_Animation.pptx");
const C = {
  ink: "16211E", muted: "5C6B66", green: "1F6F5C", greenSoft: "E3F0EB", line: "CBD5D1",
  coral: "B8452F", coralSoft: "FBE9E4", amber: "8A5A00", amberSoft: "FCEFD0",
  purple: "5F3AA8", purpleSoft: "EBE2F8", ok: "18764A", okSoft: "DDF3E7", white: "FFFFFF",
  provPanel: "F5F3EE", payPanel: "EEF5F2",
};
const H = "Cambria", B = "Calibri";

/* ---------- layout spec (inches). Everything lives here so the preview and the slide match ---------- */
const items = []; // {name, kind, x,y,w,h, ...}
const add = (o) => items.push(o);
const runs = (title, desc, tc = C.ink, ts = 14, ds = 11.5, dc = C.muted) => [
  { text: title, options: { bold: true, fontSize: ts, color: tc, fontFace: B, breakLine: !!desc } },
  ...(desc ? [{ text: desc, options: { fontSize: ds, color: dc, fontFace: B } }] : []),
];
const node = (name, x, y, w, h, title, desc, o = {}) => add({ name, kind: "node", x, y, w, h, fill: C.white, line: C.line, lineW: 1, runs: runs(title, desc, o.tc, o.ts, o.ds), margin: [0.06, 0.12, 0.06, 0.14], ...o });
const tag = (name, x, y, w, h, text, o = {}) => add({ name, kind: "node", x, y, w, h, fill: C.coralSoft, line: C.coral, lineW: 1, runs: [{ text, options: { fontSize: 12, bold: true, color: C.coral, fontFace: B } }], margin: [0.05, 0.12, 0.05, 0.12], ...o });
const pkt = (name, x, y) => add({ name, kind: "node", x, y, w: 0.95, h: 0.4, fill: C.white, line: C.coral, lineW: 1.5, radius: 0.06, align: "center", margin: [0, 0, 0, 0], runs: [{ text: "14 pages", options: { bold: true, fontSize: 11, color: C.coral, fontFace: B } }] });
const ring = (name, x, y, w, h, color) => add({ name, kind: "ring", x: x - 0.06, y: y - 0.06, w: w + 0.12, h: h + 0.12, line: color, lineW: 3 });
const caption = (name, text) => add({ name, kind: "text", x: 0.5, y: 6.5, w: 12.33, h: 0.65, valign: "middle", runs: [{ text, options: { fontSize: 18, color: C.ink, fontFace: B } }] });
const label = (name, text, color) => add({ name, kind: "text", x: 7.3, y: 0.5, w: 5.53, h: 0.6, align: "right", valign: "middle", runs: [{ text, options: { bold: true, fontSize: 16, color, fontFace: B, charSpacing: 1 } }] });
const line = (name, x, y, w, h, o = {}) => add({ name, kind: "line", x, y, w, h, line: C.muted, lineW: 2, arrow: true, ...o });

// static frame
add({ name: "eyebrow", kind: "text", static: true, x: 0.5, y: 0.3, w: 4, h: 0.28, runs: [{ text: "CURRENT STATE", options: { bold: true, fontSize: 11, color: C.green, fontFace: B, charSpacing: 3 } }] });
add({ name: "title", kind: "text", static: true, x: 0.5, y: 0.55, w: 7.2, h: 0.75, valign: "middle", runs: [{ text: "How a prior authorization moves today.", options: { fontSize: 28, color: C.ink, fontFace: H } }] });
add({ name: "panelProv", kind: "node", static: true, x: 0.5, y: 1.45, w: 4.45, h: 4.85, fill: C.provPanel, line: C.line, lineW: 1, radius: 0.1, runs: [{ text: " ", options: { fontSize: 8 } }] });
add({ name: "panelPay", kind: "node", static: true, x: 5.55, y: 1.45, w: 7.28, h: 4.85, fill: C.payPanel, line: C.line, lineW: 1, radius: 0.1, runs: [{ text: " ", options: { fontSize: 8 } }] });
add({ name: "hdrProv", kind: "text", static: true, x: 0.7, y: 1.52, w: 4.0, h: 0.55, runs: [{ text: "PROVIDER", options: { bold: true, fontSize: 12, color: C.ink, fontFace: B, charSpacing: 3, breakLine: true } }, { text: "Hospital or physician office", options: { fontSize: 11, color: C.muted, fontFace: B } }] });
add({ name: "hdrPay", kind: "text", static: true, x: 5.75, y: 1.52, w: 6.5, h: 0.55, runs: [{ text: "PAYER", options: { bold: true, fontSize: 12, color: C.ink, fontFace: B, charSpacing: 3, breakLine: true } }, { text: "The health plan: Utilization Management (UM)", options: { fontSize: 11, color: C.muted, fontFace: B } }] });
add({ name: "footer", kind: "text", static: true, x: 0.5, y: 7.1, w: 12.33, h: 0.25, runs: [{ text: "An elective inpatient lumbar spinal fusion request, as it works today.", options: { fontSize: 9, color: C.muted, fontFace: B } }] });

// provider side
const PM = [0.06, 1.3, 0.06, 0.14]; // text margin that leaves room for a packet icon on the right
node("L1", 0.75, 2.2, 3.95, 0.95, "Surgeon's office", "Orders the fusion. Staff assemble the packet.", { margin: PM });
pkt("P1", 3.62, 2.48);
node("Member", 0.75, 3.45, 3.95, 0.95, "The member: John Doe, 71", "Waiting on the surgery. Sees none of this.");
node("L3", 0.75, 4.75, 3.95, 0.7, "Provider decodes the pend", "Works out what is missing, then resends.", { margin: PM, ts: 13, ds: 10.5 });
pkt("PL3", 3.62, 4.9);
tag("T3", 0.75, 5.58, 3.95, 0.6, "A pend does not stop the clock. The case starts again from zero.");

// payer side
node("Intake", 5.8, 2.2, 3.5, 0.95, "Intake", "Checks member, form, and codes. Not a clinical check.", { margin: PM });
pkt("P2", 8.22, 2.48);
tag("T1", 9.5, 2.2, 3.1, 0.95, "Nobody has read the clinical pages yet.");
node("Nurse", 5.8, 3.45, 3.5, 0.95, "UM nurse", "Reads all 14 pages and checks them against policy.", { margin: PM });
pkt("P3", 8.22, 3.73);
add({ name: "T2", kind: "text", x: 9.5, y: 3.4, w: 3.1, h: 0.28, runs: [{ text: "4 facts hidden in 14 pages", options: { bold: true, fontSize: 12, color: C.coral, fontFace: B } }] });
const chip = (n, x, y, t) => add({ name: n, kind: "node", x, y, w: 1.5, h: 0.3, fill: C.white, line: C.green, lineW: 1, radius: 0.06, align: "center", margin: [0, 0.04, 0, 0.04], runs: [{ text: t, options: { fontSize: 11, color: C.ink, fontFace: B } }] });
chip("Chip1", 9.5, 3.72, "Expected stay"); chip("Chip2", 11.1, 3.72, "Risk factors");
chip("Chip3", 9.5, 4.06, "Imaging"); chip("Chip4", 11.1, 4.06, "Conservative care");

// outcomes
add({ name: "OutPend", kind: "node", x: 5.8, y: 4.75, w: 2.1, h: 0.7, fill: C.amberSoft, line: C.amber, lineW: 1, runs: runs("Pend", "Asks the provider", C.amber, 14, 11, C.amber), margin: [0.04, 0.12, 0.04, 0.14] });
add({ name: "OutApprove", kind: "node", x: 8.0, y: 4.75, w: 2.1, h: 0.7, fill: C.okSoft, line: C.ok, lineW: 1, runs: runs("Approve", "Packet is complete", C.ok, 14, 11, C.ok), margin: [0.04, 0.12, 0.04, 0.14] });
add({ name: "OutEsc", kind: "node", x: 10.25, y: 4.75, w: 2.3, h: 0.7, fill: C.purpleSoft, line: C.purple, lineW: 1, runs: runs("Escalate", "Needs a physician", C.purple, 14, 11, C.purple), margin: [0.04, 0.12, 0.04, 0.14] });
ring("RingPend", 5.8, 4.75, 2.1, 0.7, C.amber);
ring("RingApprove", 8.0, 4.75, 2.1, 0.7, C.ok);
ring("RingEsc", 10.25, 4.75, 2.3, 0.7, C.purple);
node("MD", 9.4, 5.65, 3.2, 0.6, "Medical director", "Decides. The only role that can deny.", { fill: C.purpleSoft, line: C.purple, ts: 13, ds: 10.5, tc: C.purple, margin: [0.03, 0.12, 0.03, 0.14] });
tag("T4", 5.8, 5.65, 3.4, 0.6, "A denial can be appealed, and many are overturned.");

// arrows
line("ArrFax", 4.7, 2.675, 1.1, 0, { color: C.coral, dash: "dash" });
add({ name: "LblFax", kind: "text", x: 4.72, y: 2.33, w: 1.06, h: 0.28, align: "center", runs: [{ text: "FAX", options: { bold: true, fontSize: 11, color: C.coral, fontFace: B, charSpacing: 3 } }] });
line("ArrIn", 7.55, 3.15, 0, 0.3);
line("ForkStub", 7.55, 4.4, 0, 0.15, { arrow: false });
line("ForkBar", 6.85, 4.55, 4.55, 0, { arrow: false });
line("DropPend", 6.85, 4.55, 0, 0.2);
line("DropApprove", 9.05, 4.55, 0, 0.2);
line("DropEsc", 11.4, 4.55, 0, 0.2);
line("ArrPend", 4.7, 5.1, 1.1, 0, { flipH: true, color: C.amber });
line("ArrMD", 11.4, 5.45, 0, 0.2, { color: C.purple });

// labels + captions
label("LabelA", "PATH 1  ·  A COMPLETE PACKET", C.ok);
label("LabelB", "PATH 2  ·  SOMETHING IS MISSING", C.amber);
label("LabelC", "PATH 3  ·  NEEDS A PHYSICIAN", C.purple);
const CAPS = {
  c1: "A surgeon decides a patient needs a lumbar fusion. The office assembles a packet of clinical documents.",
  c2: "The packet is faxed to the plan. Fourteen pages.",
  c3: "Intake checks the member, the form, and the codes. That is a paperwork check, not a clinical one.",
  c4: "A UM nurse picks it up and reads all fourteen pages.",
  c5: "She hunts for four facts and checks each one against policy.",
  c6: "Then there are three ways out.",
  c7: "Path 1. Every fact is there and every criterion is met. She approves.",
  c8: "Path 2. A fact is missing. She pends the case and it goes back to the provider.",
  c9: "The provider has to work out what is missing, then resend. The case starts again from zero, and the clock keeps running.",
  c10: "Path 3. The facts are there but the case is borderline. It goes to a medical director.",
  c11: "Only the medical director can deny. A denial can be appealed, and many are overturned.",
  c12: "Every step is somebody doing their job correctly. The delay is built into the process.",
};
Object.entries(CAPS).forEach(([k, v]) => caption(k, v));

/* ---------- timeline: slots play one after another. hold = pause (seconds) before the slot starts ---------- */
const FI = (name, delay = 0, dur = 500) => ({ t: "fadeIn", name, delay, dur });
const FO = (name, delay = 0, dur = 300) => ({ t: "fadeOut", name, delay, dur });
const WI = (name, dir, delay = 0, dur = 600) => ({ t: "wipeIn", name, dir, delay, dur });
const slots = [
  { hold: 0, fx: [FI("L1"), FI("Member", 200), FI("P1", 400), FI("c1", 300)] },
  { hold: 3.5, fx: [FO("c1"), WI("ArrFax", "left", 300), FI("LblFax", 300), FO("P1", 900), FI("c2", 500)] },
  { hold: 2.2, fx: [FO("c2"), FI("Intake", 300), FI("P2", 500), FI("c3", 300), FI("T1", 1500)] },
  { hold: 4, fx: [FO("c3"), WI("ArrIn", "down", 300), FO("P2", 300), FI("Nurse", 700), FI("P3", 900), FI("c4", 300)] },
  { hold: 2.8, fx: [FO("c4"), FI("T2", 300), FI("Chip1", 600), FI("Chip2", 900), FI("Chip3", 1200), FI("Chip4", 1500), FI("c5", 300)] },
  { hold: 3.5, fx: [FO("c5"), WI("ForkStub", "down", 300, 250), WI("ForkBar", "left", 550, 500), WI("DropPend", "down", 1050, 250), WI("DropApprove", "down", 1050, 250), WI("DropEsc", "down", 1050, 250), FI("OutPend", 1300), FI("OutApprove", 1300), FI("OutEsc", 1300), FI("c6", 300)] },
  { hold: 2.2, fx: [FO("c6"), FI("LabelA", 300), FI("RingApprove", 300), FI("c7", 300)] },
  { hold: 3.8, fx: [FO("c7"), FO("LabelA"), FO("RingApprove"), FI("LabelB", 400), FI("RingPend", 400), FO("P3", 400), FI("c8", 400)] },
  { hold: 3.0, fx: [FO("c8"), WI("ArrPend", "right", 300), FI("L3", 800), FI("PL3", 1000), FI("T3", 1500), FI("c9", 300)] },
  { hold: 5.0, fx: [FO("c9"), FO("LabelB"), FO("RingPend"), FO("ArrPend"), FO("L3"), FO("PL3"), FO("T3"), FI("LabelC", 500), FI("RingEsc", 500), FI("c10", 500)] },
  { hold: 3.2, fx: [FO("c10"), WI("ArrMD", "down", 300, 400), FI("MD", 700), FI("T4", 1500), FI("c11", 300)] },
  { hold: 4.5, fx: [FO("c11"), FO("LabelC"), FO("RingEsc"), FI("c12", 400)] },
];

/* ---------- build the slide ---------- */
async function main() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5 in
  pres.title = "How a prior authorization moves today (animated)";
  pres.author = "Nisha Mishra";
  const s = pres.addSlide();
  s.background = { color: C.white };
  const m2 = (m) => (m ? m.map((v) => v * 72) : undefined); // inches -> points, [top,right,bottom,left]
  items.forEach((o) => {
    if (o.kind === "line") {
      s.addShape(pres.ShapeType.line, { x: o.x, y: o.y, w: o.w, h: o.h, flipH: !!o.flipH, objectName: o.name, line: { color: o.color || o.line, width: o.lineW, dashType: o.dash || "solid", ...(o.arrow ? { endArrowType: "triangle" } : {}) } });
    } else if (o.kind === "ring") {
      s.addShape(pres.ShapeType.roundRect, { x: o.x, y: o.y, w: o.w, h: o.h, rectRadius: 0.1, fill: { type: "none" }, line: { color: o.line, width: o.lineW }, objectName: o.name });
    } else if (o.kind === "node") {
      const m = o.margin || [0.06, 0.12, 0.06, 0.12];
      s.addText(o.runs, { shape: pres.ShapeType.roundRect, rectRadius: o.radius ?? 0.08, x: o.x, y: o.y, w: o.w, h: o.h, fill: { color: o.fill }, line: { color: o.line, width: o.lineW }, align: o.align || "left", valign: "middle", margin: m2([m[0], m[1], m[2], m[3]]), objectName: o.name, isTextBox: false });
    } else {
      s.addText(o.runs, { x: o.x, y: o.y, w: o.w, h: o.h, align: o.align || "left", valign: o.valign || "top", margin: 0, objectName: o.name, isTextBox: true, fit: "none" });
    }
  });
  s.addNotes(NOTES);
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
  const pv = preview();
  fs.writeFileSync(path.join(__dirname, "preview.html"), pv);
  if (process.argv.includes("--steps")) [3, 6, 7, 9, 11].forEach((k) => fs.writeFileSync(path.join(__dirname, `preview_s${k}.html`), pv.replace('new URLSearchParams(location.search).get("step")', `"${k}"`)));
  let total = 0; slots.forEach((sl) => (total += sl.hold + Math.max(...sl.fx.map((e) => (e.delay + e.dur) / 1000))));
  console.log("wrote", OUT, "| animation length about", Math.round(total), "seconds");
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
    const grp = o.kind === "line" ? "" : ' grpId="0"';
    let preset, cls, sub, body;
    if (e.t === "fadeIn") { preset = 10; cls = "entr"; sub = 0; body = setVis(spid, "visible", 0) + filt(spid, "fade", "in", e.dur); }
    else if (e.t === "fadeOut") { preset = 10; cls = "exit"; sub = 0; body = filt(spid, "fade", "out", e.dur) + setVis(spid, "hidden", Math.max(e.dur - 1, 0)); }
    else { const d = e.dir === "down" ? fromTop.down : dirs[e.dir]; preset = 22; cls = "entr"; sub = d[0]; body = setVis(spid, "visible", 0) + filt(spid, d[1], "in", e.dur); }
    return `<p:par><p:cTn id="${id()}" presetID="${preset}" presetClass="${cls}" presetSubtype="${sub}" fill="hold"${grp} nodeType="${nodeType}"><p:stCondLst><p:cond delay="${e.delay}"/></p:stCondLst><p:childTnLst>${body}</p:childTnLst></p:cTn></p:par>`;
  };
  const outerId = id();
  let t = 0, slotsXml = "";
  slots.forEach((sl, i) => {
    const fx = sl.fx.map((e) => ({ ...e, delay: e.delay + (i > 0 ? Math.round(sl.hold * 1000) : 0) }));
    const slotId = id();
    const inner = fx.map((e, k) => effect(e, i === 0 && k === 0 ? "clickEffect" : k === 0 ? "afterEffect" : "withEffect")).join("");
    slotsXml += `<p:par><p:cTn id="${slotId}" fill="hold"><p:stCondLst><p:cond delay="${t}"/></p:stCondLst><p:childTnLst>${inner}</p:childTnLst></p:cTn></p:par>`;
    t += Math.max(...fx.map((e) => e.delay + e.dur));
  });
  const bld = [...new Set(slots.flatMap((sl) => sl.fx.map((e) => e.name)))].filter((nm) => byName[nm].kind !== "line")
    .map((nm) => { const o = byName[nm]; const bg = o.kind === "ring" || (o.kind === "node" && o.fill); return `<p:bldP spid="${ids[nm]}" grpId="0"${bg ? ' animBg="1"' : ""}/>`; }).join("");
  const rootId = 1, seqId = 2;
  return `<p:timing><p:tnLst><p:par><p:cTn id="${rootId}" dur="indefinite" restart="never" nodeType="tmRoot"><p:childTnLst><p:seq concurrent="1" nextAc="seek"><p:cTn id="${seqId}" dur="indefinite" nodeType="mainSeq"><p:childTnLst><p:par><p:cTn id="${outerId}" fill="hold"><p:stCondLst><p:cond delay="indefinite"/></p:stCondLst><p:childTnLst>${slotsXml}</p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn><p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst><p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst></p:seq></p:childTnLst></p:cTn></p:par></p:tnLst><p:bldLst>${bld}</p:bldLst></p:timing>`;
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
    if (o.kind === "ring") return `<div data-n="${o.name}" style="position:absolute;${base}border:${o.lineW}px solid #${o.line};border-radius:10px;box-sizing:border-box"></div>`;
    const m = o.margin ? o.margin.map((v) => v * px) : [0, 0, 0, 0];
    const box = o.kind === "node" ? `background:#${o.fill};border:${o.lineW}px solid #${o.line};border-radius:${(o.radius ?? 0.08) * px}px;` : "";
    return `<div data-n="${o.name}" style="position:absolute;${base}${box}box-sizing:border-box;overflow:hidden;display:flex;flex-direction:column;justify-content:${o.valign === "top" ? "flex-start" : "center"};text-align:${o.align || "left"};padding:${m[0]}px ${m[1]}px ${m[2]}px ${m[3]}px;line-height:1.15"><div>${inner}</div></div>`;
  }).join("\n");
  const data = JSON.stringify(slots.map((sl) => sl.fx.map((e) => [e.name, e.t])));
  const script = `<script>const S=${data};const q=new URLSearchParams(location.search).get("step");if(q!==null){const k=+q;const vis={};const all=new Set(S.flat().map(e=>e[0]));S.slice(0,k).forEach(sl=>sl.forEach(([n,t])=>{vis[n]=t!=="fadeOut"}));document.querySelectorAll("[data-n]").forEach(el=>{const n=el.dataset.n;if(all.has(n)&&!vis[n])el.style.display="none"})}</script>`;
  return `<!doctype html><meta charset="utf-8"><body style="margin:0;background:#fff"><div style="position:relative;width:${13.333 * px}px;height:${7.5 * px}px;background:#fff">${html}</div>${script}`;
}

const NOTES = `Walk this left to right and let it play. One click starts it.

Start with the provider. A surgeon decides the patient needs a lumbar fusion, and the office assembles a packet. Fourteen pages of clinical documents. They fax it to the plan.

On the plan side, intake checks the member, the form, and the codes. That is a paperwork check. Nobody has read the clinical pages yet.

A UM nurse picks it up. She reads all fourteen pages, hunting for four facts, and checks each one against policy.

Then there are three ways out.

Path one: everything is there, and she approves.

Path two: a fact is missing. She pends the case. The provider has to work out what is missing and resend, and the case starts again from zero. A pend does not stop the clock.

Path three: the facts are there but the case is borderline. It goes to a medical director, the only role that can deny. A denial can be appealed, and many are overturned.

Close on this: every step is somebody doing their job correctly. The delay is built into the process.`;

main().catch((e) => { console.error(e); process.exit(1); });
