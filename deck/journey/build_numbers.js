// Builds ONE animated slide: how a prior authorization moves today.
// Run:  node build_journey.js        -> Journey_Animation.pptx + preview.html (static layout check)
// The animation is written straight into the slide XML (pptxgenjs cannot do animations).
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");
const JSZip = require("jszip");
const { Resvg } = require("@resvg/resvg-js"); // draws the SVG art to PNG (npm i @resvg/resvg-js)

const OUT = path.join(__dirname, "Numbers.pptx"); // ONE plain slide, no animation
const OUT_STEPS = path.join(__dirname, "Numbers_Steps.pptx"); // only with --slides: one slide per step
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
const ART = {
  AvL1: building,
  AvM: person({ bg: "E8E4DC", skin: SKIN.d, hair: "D5D8DC", style: "short", top: "8A9A5B" }),
  AvL3: person({ bg: "F2E6D8", skin: SKIN.b, hair: "2B2B2B", style: "long", top: "C0733F", acc: "headset" }),
  AvIntake: person({ bg: "D8EAE3", skin: SKIN.a, hair: "6B4226", style: "bun", top: "3C6E8F", acc: "clip" }),
  AvNurse: person({ bg: "CDE8E0", skin: SKIN.c, hair: "2B2B2B", style: "short", top: "2F8F83", acc: "nurse" }),
  AvMD: person({ bg: "E3D9F5", skin: SKIN.d, hair: "4A3B32", style: "short", top: "5F3AA8", coat: true, acc: "doctor" }),
  IcFax: faxIcon,
};

/* ---------- layout spec (inches) for the numbers slide ---------- */
const items = [];
const add = (o) => items.push(o);

add({ name: "eyebrow", kind: "text", x: 0.5, y: 0.3, w: 4, h: 0.28, runs: [{ text: "THE NUMBERS", options: { bold: true, fontSize: 11, color: C.green, fontFace: B, charSpacing: 3 } }] });
add({ name: "title", kind: "text", x: 0.5, y: 0.55, w: 8.6, h: 0.75, valign: "middle", runs: [{ text: "Fast is not the same as right.", options: { fontSize: 26, color: C.ink, fontFace: H } }] });
add({ name: "sub", kind: "text", x: 8.3, y: 0.55, w: 4.53, h: 0.75, align: "right", valign: "middle", runs: [{ text: "Medicare Advantage prior authorization", options: { fontSize: 13, color: C.muted, fontFace: B } }] });
add({ name: "footer", kind: "text", x: 0.5, y: 7.1, w: 12.33, h: 0.25, runs: [{ text: "Sources: Humana CY2025 public prior authorization reports (CMS-0057-F). KFF, 2024 data. HHS OIG data brief OEI-09-24-00331. AMA 2025 Prior Authorization Physician Survey.", options: { fontSize: 9, color: C.muted, fontFace: B } }] });

const CW = 4.0, GX = 0.165, CX = [0.5, 0.5 + CW + GX, 0.5 + 2 * (CW + GX)];
const sect = (name, y, text, color) => add({ name, kind: "text", x: 0.5, y, w: 12.33, h: 0.26, runs: [{ text, options: { bold: true, fontSize: 11, color, fontFace: B, charSpacing: 2 } }] });
const stat = (name, i, y, h, color, soft, big, label, src, tagline) => add({
  name, kind: "node", x: CX[i], y, w: CW, h, fill: soft, line: color, lineW: 1.5, radius: 0.08, valign: "top", margin: [0.1, 0.2, 0.08, 0.2],
  runs: [
    ...(tagline ? [{ text: tagline, options: { bold: true, fontSize: 9.5, color, fontFace: B, charSpacing: 2, breakLine: true } }] : []),
    { text: big, options: { fontSize: 36, color, fontFace: H, breakLine: true } },
    { text: label, options: { bold: true, fontSize: 12.5, color: C.ink, fontFace: B, breakLine: true, paraSpaceAfter: 4 } },
    { text: src, options: { fontSize: 10, color: C.muted, fontFace: B } },
  ],
});

// row 1: Humana is fast, at scale
sect("S1", 1.45, "HUMANA IS FAST, AT SCALE", C.ok);
stat("A1", 0, 1.72, 1.3, C.ok, C.okSoft, "1 day", "standard decisions take, on average", "Humana Medicare Advantage, 2025. Federal limit: 7 days.");
stat("A2", 1, 1.72, 1.3, C.ok, C.okSoft, "4 to 11 hours", "expedited decisions take, on average", "Depends on the contract, 2025. Federal limit: 72 hours.");
stat("A3", 2, 1.72, 1.3, C.green, C.greenSoft, "9.5 million", "standard requests decided in one year", "Humana, 2025. And about 2.3 million more are coming: 1.03M new members × 2.2 requests each (KFF).");

// row 2: but a denial that is appealed is often reversed. Humana first, then the wider picture
sect("S2", 3.14, "BUT WHEN A DENIAL IS APPEALED, IT IS OFTEN REVERSED", C.coral);
stat("B1", 0, 3.42, 1.55, C.coral, C.coralSoft, "64.7%", "of appealed Humana denials were overturned", "Humana's own federal reports, 2025. Only 2.7% of denials are appealed, so we do not claim 65% of denials are wrong.", "HUMANA");
stat("B2", 1, 3.42, 1.55, C.coral, C.coralSoft, "80.7%", "of appealed denials were overturned across Medicare Advantage", "KFF, 2024. 53 million requests, 4.1 million denied.", "THE WIDER PICTURE");
stat("B3", 2, 3.42, 1.55, C.coral, C.coralSoft, "95%", "of appealed skilled nursing denials were overturned", "HHS OIG, 19 plans, data from June 2024.", "THE EXTREME");

// row 3: the human side, and the point
sect("S3", 5.1, "THE HUMAN SIDE: WHAT PHYSICIANS REPORT", C.amber);
stat("C1", 0, 5.38, 1.35, C.amber, C.amberSoft, "93%", "of physicians say it can delay care at least some of the time", "AMA survey of 1,000 physicians, December 2025.");
stat("C2", 1, 5.38, 1.35, C.amber, C.amberSoft, "26%", "report a serious adverse event for a patient", "Same survey. Physician-reported.");
add({ name: "Point", kind: "node", x: CX[2], y: 5.38, w: CW, h: 1.35, fill: C.green, line: C.green, lineW: 1, radius: 0.08, margin: [0.1, 0.22, 0.1, 0.22], runs: [{ text: "An overturned denial is care that was delayed.", options: { fontSize: 15, bold: true, color: C.white, fontFace: B, breakLine: true, paraSpaceAfter: 4 } }, { text: "Our goal is not faster. It is right the first time.", options: { fontSize: 15, bold: true, color: "D5EBE3", fontFace: B } }] });
add({ name: "Gap", kind: "text", x: 0.5, y: 6.8, w: 12.33, h: 0.28, valign: "middle", runs: [{ text: "Not published by Humana or CMS: how many hours plan reviewers spend on prior authorization. That is a number we would measure in a pilot.", options: { fontSize: 11, italic: true, color: C.muted, fontFace: B } }] });

const slots = [];
const STEP_NOTES = [
  "I read Humana's own public reports, and Humana is fast. A standard decision takes one day on average. The federal limit is seven. An expedited decision takes four to eleven hours, and the federal limit is seventy-two. And that is across nine and a half million requests. That is real operational strength. And the pile is growing. Humana added about a million members in a month, and a Humana member makes about 2.2 requests a year, so about 2.3 million more requests are coming, each one read by a nurse.",
  "But fast is not the same as right. Sixty-five percent of appealed Humana denials were overturned. That comes from Humana's own federal report for 2025. I do not claim sixty-five percent of denials are wrong. Only about three percent of denials are appealed. But the ones that are appealed get reversed most of the time, and an overturn often comes from new information. That is my point. The first look was missing something.",
  "Zoom out and the problem is bigger. Across all of Medicare Advantage, eighty-one percent of appealed denials were overturned in 2024. And the Inspector General found ninety-five percent of appealed skilled nursing denials were overturned.",
  "There is another side of the coin. We may not solve this one directly, but it adds color to the problem. Physicians feel it, and they are the people closest to the patient. Ninety-three percent say prior authorization can delay care. Twenty-six percent report a serious adverse event for a patient.",
  "One more thing. I could not find a report from Humana or from the federal government on how many hours reviewers spend on prior authorization. A physician reports thirteen hours a week. I will not say a utilization nurse spends the same. But with nine and a half million requests, and fourteen pages to read and check against policy on each one, I would expect a big part of their shift goes to this. A pilot is how we would measure it.",
  "So we want to be right, and stay inside the federal limits. But the biggest goal is to be correct. An overturned denial is care that was delayed. Our goal is not to be faster. Our goal is to be right the first time. And speed becomes a line we do not cross.",
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
      s.addShape(pres.ShapeType.line, { x: o.x, y: o.y, w: o.w, h: o.h, flipH: !!o.flipH, objectName: o.name, line: { color: o.color || o.line, width: o.lineW, dashType: o.dash || "solid", ...(o.arrow ? { endArrowType: "triangle" } : {}) } });
    } else if (o.kind === "ring") {
      s.addShape(pres.ShapeType.roundRect, { x: o.x, y: o.y, w: o.w, h: o.h, rectRadius: 0.1, fill: { type: "none" }, line: { color: o.line, width: o.lineW }, objectName: o.name });
    } else if (o.kind === "node") {
      const m = o.margin || [0.06, 0.12, 0.06, 0.12]; // my spec order is top, right, bottom, left
      // pptxgenjs wants [left, right, bottom, top]
      s.addText(o.runs, { shape: pres.ShapeType.roundRect, rectRadius: o.radius ?? 0.08, x: o.x, y: o.y, w: o.w, h: o.h, fill: { color: o.fill }, line: { color: o.line, width: o.lineW }, align: o.align || "left", valign: "middle", margin: m2([m[3], m[1], m[2], m[0]]), objectName: o.name, isTextBox: false });
    } else {
      s.addText(o.runs, { x: o.x, y: o.y, w: o.w, h: o.h, align: o.align || "left", valign: o.valign || "top", margin: 0, objectName: o.name, isTextBox: true, fit: "none" });
    }
  });
}

async function main() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5 in
  pres.title = "The numbers";
  pres.author = "Nisha Mishra";
  const PNG = {};
  for (const [k, svg] of Object.entries(ART)) PNG[k] = Buffer.from(new Resvg(svg, { fitTo: { mode: "width", value: 360 } }).render().asPng()).toString("base64");

  // this slide is a plain slide: everything is on screen from the start, no clicks
  {
    const s = pres.addSlide();
    s.background = { color: C.white };
    draw(pres, s, PNG, null);
    s.addNotes(STEP_NOTES.join(String.fromCharCode(10, 10)));
    await pres.writeFile({ fileName: OUT });
    fs.writeFileSync(path.join(__dirname, "preview.html"), preview());
    console.log("wrote", OUT, "| one plain slide, no animation");
    return;
  }

  if (!ANIMATED) {
    // one slide per step: press Next to walk the flow
    slots.forEach((_, i) => {
      const s = pres.addSlide();
      s.background = { color: C.white };
      draw(pres, s, PNG, visibleAfter(i + 1));
      s.addNotes(STEP_NOTES[i]);
    });
    await pres.writeFile({ fileName: OUT_STEPS });
    fs.writeFileSync(path.join(__dirname, "preview.html"), preview());
    if (process.argv.includes("--steps")) [4, 6, 10, 11, 13].forEach((k) => fs.writeFileSync(path.join(__dirname, `preview_s${k}.html`), preview().replace('new URLSearchParams(location.search).get("step")', `"${k}"`)));
    console.log("wrote", OUT_STEPS, "|", slots.length, "slides, press Next to walk through");
    return;
  }

  const s = pres.addSlide();
  s.background = { color: C.white };
  draw(pres, s, PNG, null);
  s.addNotes(["One slide. Click once per point. Finish your talking point, then click."].concat(STEP_NOTES.map((t, i) => "Click " + (i + 1) + ": " + t)).join(String.fromCharCode(10, 10)));
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
  fs.writeFileSync(path.join(__dirname, "preview.html"), preview());
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
