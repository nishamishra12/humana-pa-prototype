// Builds ONE animated slide: the product metrics.
// Same method and look as build_friction.js and build_journey.js: one slide, one click per step, nothing plays by itself.
// Run:  NODE_PATH=<folder with @resvg/resvg-js> node build_metrics_slide.js   -> Product_Metrics.pptx + preview_metrics.html
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");
const JSZip = require("jszip");
const { Resvg } = require("@resvg/resvg-js"); // draws the SVG art to PNG (npm i @resvg/resvg-js)

const OUT = path.join(__dirname, "Product_Metrics.pptx"); // default: ONE slide, one click per step
const OUT_STEPS = path.join(__dirname, "Product_Metrics_Steps.pptx"); // only with --slides: one slide per step
const C = {
  ink: "16211E", muted: "5C6B66", green: "1F6F5C", greenSoft: "E3F0EB", line: "CBD5D1",
  coral: "B8452F", coralSoft: "FBE9E4", amber: "8A5A00", amberSoft: "FCEFD0",
  purple: "5F3AA8", purpleSoft: "EBE2F8", ok: "18764A", okSoft: "DDF3E7", white: "FFFFFF",
  provPanel: "F5F3EE", payPanel: "EEF5F2",
};
const H = "Cambria", B = "Calibri";

/* ---------- illustrations (flat SVG, rendered to PNG so they work in Google Slides) ---------- */

const ART = {};
const items = [];
const add = (o) => items.push(o);
const line = (name, x, y, w, h, o = {}) => add({ name, kind: "line", x, y, w, h, line: C.muted, lineW: 1.75, arrow: true, ...o });
const caption = (name, text) => add({ name, kind: "text", x: 0.5, y: 6.5, w: 12.33, h: 0.65, valign: "middle", runs: [{ text, options: { fontSize: 16, color: C.ink, fontFace: B } }] });
const card = (name, x, y, w, h, fill, lineC, tag, tagColor, parts, o = {}) => {
  const r = [{ text: tag, options: { bold: true, fontSize: 9, color: tagColor, fontFace: B, charSpacing: 1.5, breakLine: true, paraSpaceAfter: 5 } }];
  parts.forEach((p, i) => r.push({ text: p[0], options: { bold: !!p[2], fontSize: p[1] || 11, color: p[3] || C.ink, fontFace: p[4] || B, breakLine: i < parts.length - 1, paraSpaceAfter: p[5] ?? 4 } }));
  add({ name, kind: "node", x, y, w, h, fill, line: lineC, lineW: 1.25, radius: 0.1, runs: r, valign: "top", margin: [0.16, 0.2, 0.08, 0.2] });
};

// static frame
add({ name: "eyebrow", kind: "text", static: true, x: 0.5, y: 0.3, w: 5, h: 0.28, runs: [{ text: "HOW WE MEASURE IT", options: { bold: true, fontSize: 11, color: C.green, fontFace: B, charSpacing: 3 } }] });
add({ name: "title", kind: "text", static: true, x: 0.5, y: 0.55, w: 9.4, h: 0.75, valign: "middle", runs: [{ text: "One number to win. Guardrails so we do not cheat.", options: { fontSize: 26, color: C.ink, fontFace: H } }] });
add({ name: "sub", kind: "text", static: true, x: 9.5, y: 0.55, w: 3.33, h: 0.75, align: "right", valign: "middle", runs: [{ text: "Right first time", options: { fontSize: 14, color: C.muted, fontFace: B } }] });
add({ name: "footer", kind: "text", static: true, x: 0.5, y: 7.1, w: 12.33, h: 0.25, runs: [{ text: "Leading numbers are live on the operations dashboard. The lagging ones need Humana's own data. Humana's public figure for context: 64.7% of appealed Medicare Advantage denials were overturned in 2025.", options: { fontSize: 9, color: C.muted, fontFace: B } }] });

card("K1", 0.5, 1.45, 3.9, 3.0, C.greenSoft, C.green, "NORTH STAR", C.green, [
  ["Right-first-time rate", 26, false, C.ink, H, 10],
  ["Of every 100 requests, how many get the right answer the first time, with no back and forth.", 15, true, C.ink, B, 12],
  ["A case has rework when the nurse asks for something already sent, a director sends it back, or a denial is overturned because the packet already had the answer.", 12, false, C.muted],
]);
card("K2", 4.7, 1.45, 3.9, 3.0, C.white, C.line, "LEADING  ·  SEEN IN DAYS TO WEEKS", C.muted, [
  ["First-review rate", 14, true, C.ink, B, 1], ["Decided with no pend. Higher is better.", 12, false, C.muted, B, 14],
  ["Avoidable pends", 14, true, C.ink, B, 1], ["The provider says it was already sent. Lower is better.", 12, false, C.muted, B, 14],
  ["Avoidable escalations", 14, true, C.ink, B, 1], ["A director sends it back to the nurse. Lower is better.", 12, false, C.muted, B, 14],
  ["Nurse agrees with the AI", 14, true, C.ink, B, 1], ["The nurse's first action matched. Higher is better.", 12, false, C.muted, B, 0],
]);
card("K3", 8.93, 1.45, 3.9, 3.0, "F3F5F4", C.line, "LAGGING  ·  MONTHS, WITH HUMANA'S DATA", C.muted, [
  ["Overturned because the info was in the packet", 14, true, C.ink, B, 1], ["An appeal wins and the packet already had the answer. Lower is better.", 12, false, C.muted, B, 14],
  ["Cost per decision", 14, true, C.ink, B, 1], ["Total spend on a case divided by decided cases. Lower is better.", 12, false, C.muted, B, 14],
  ["Month over month", 14, true, C.ink, B, 1], ["The same numbers as a trend.", 12, false, C.muted, B, 0],
]);
line("Becomes", 8.62, 2.95, 0.29, 0);
card("G", 0.5, 4.7, 6.9, 1.5, C.coralSoft, C.coral, "GUARDRAILS", C.coral, [
  ["Time limit: never slower than the CMS clock.   Approvals: the share must not jump.   No AI denials: only a director denies.", 13.5, false, C.ink],
]);
card("D", 7.6, 4.7, 5.23, 1.5, C.okSoft, C.ok, "WHAT AN EXECUTIVE DECIDES WITH IT", C.ok, [
  ["Add nurse capacity. Choose the next service to onboard. Review the owner's queue. Make a pilot live, or pause it.", 13.5, false, C.ink],
]);

const CAPS = {
  c1: "One number to win: the right-first-time rate. Of every hundred requests, how many get the right answer the first time, with no back and forth.",
  c2: "Leading indicators show it in days. First-review rate, avoidable pends, avoidable escalations, and how often the nurse agrees with the AI.",
  c3: "Lagging indicators take months and need Humana's data. They turn the early read into the full north star.",
  c4: "Guardrails so we do not cheat. Never slower than the CMS clock. Approvals must not jump. The AI never denies.",
  c5: "And each number leads to a decision: nurse capacity, which service to onboard, the owner's queue, and whether a pilot goes live.",
};
Object.entries(CAPS).forEach(([k, v]) => caption(k, v));

const FI = (name, delay = 0, dur = 500) => ({ t: "fadeIn", name, delay, dur });
const FO = (name, delay = 0, dur = 300) => ({ t: "fadeOut", name, delay, dur });
const WI = (name, dir, delay = 0, dur = 600) => ({ t: "wipeIn", name, dir, delay, dur });
const slots = [
  { hold: 0, fx: [FI("K1"), FI("c1", 200)] },
  { hold: 0, fx: [FO("c1"), FI("K2", 300), FI("c2", 300)] },
  { hold: 0, fx: [FO("c2"), WI("Becomes", "left", 200, 300), FI("K3", 500), FI("c3", 300)] },
  { hold: 0, fx: [FO("c3"), FI("G", 300), FI("c4", 300)] },
  { hold: 0, fx: [FO("c4"), FI("D", 300), FI("c5", 300)] },
];
const STEP_NOTES = [
  "One number to win: the right-first-time rate. Out of every hundred requests, how many get the right answer the first time, with no back and forth. That helps the member, who gets care sooner. It helps the provider, who does not send things twice. It helps the nurse, who does less rework. And it helps the plan, which pays for fewer appeals. A case has rework when the nurse asks for something the provider already sent, when a director sends it back to the nurse, or when a denial is overturned because the packet already had the answer.",
  "We cannot see the full north star live, because the appeals part arrives months later. So we watch leading indicators, which move in days. The first-review rate: cases decided with no pend. Avoidable pends: the provider replies that it was already sent. The nurse types that when the reply is added. Avoidable escalations: a director sends the case back to the nurse. And how often the nurse's first action matches the AI. These are on the operations dashboard, live.",
  "The lagging indicators take months and need Humana's own data. Overturned because the information was in the packet. Cost per decision. And the trend month over month. When that data arrives, the early read becomes the full north star. We would ask Humana for these.",
  "Guardrails, so we do not cheat. Humana already meets the CMS time limit, and we must not slow it down. If the share of approvals jumps, we may be approving too much just to look good. And the AI never denies. A medical director denies and writes the reason.",
  "And each number leads to a decision for an executive. Is there enough nurse capacity before a deadline passes. Which service to onboard next, from the requests that arrived with no policy. Whether the policy owner has time for the drafts waiting. And whether a pilot service goes live or pauses. The dashboard is built around those four decisions.",
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
  pres.title = "How we measure it";
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
    fs.writeFileSync(path.join(__dirname, "preview_metrics.html"), preview());
    if (process.argv.includes("--steps")) [4, 6, 10, 11, 13].forEach((k) => fs.writeFileSync(path.join(__dirname, `Product_Metrics_s${k}.html`), preview().replace('new URLSearchParams(location.search).get("step")', `"${k}"`)));
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
  fs.writeFileSync(path.join(__dirname, "preview_metrics.html"), preview());
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
