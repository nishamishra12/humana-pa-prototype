// Builds ONE animated slide: the business value, as back-of-the-napkin math.
// Each click does the math for one lever on a "napkin", then the napkin folds into that lever's card.
// Run:  node build_value_math.js   -> Business_Value_Click_Through.pptx + preview_value_math.html (?step=N shows the state after N clicks)
// The animation is written straight into the slide XML, the same way as build_future.js (pptxgenjs cannot do animations).
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");
const JSZip = require("jszip");
const { Resvg } = require("@resvg/resvg-js");

const OUT = path.join(__dirname, "Business_Value_Click_Through.pptx");
const C = {
  ink: "16211E", muted: "5C6B66", line: "CBD5D1", white: "FFFFFF", paper: "FAF8F3",
  green: "1F6F5C", greenSoft: "E3F0EB", purple: "5F3AA8", purpleSoft: "EBE2F8", amber: "8A5A00", amberSoft: "FCEFD0",
  pub: "2F5DA8", pubSoft: "E4ECF8", asm: "C0590E", asmSoft: "FCE9D8", // blue = a public number, orange = an assumption
};
const H = "Cambria", B = "Calibri";

/* ---------- illustrations (flat SVG rendered to PNG) ---------- */
function person(o) {
  const hair = `<path d="M33 42 C31 22 69 22 67 42 C63 33 55 30 50 30 C45 30 37 33 33 42Z" fill="#${o.hair}"/>`;
  const acc = o.nurse ? `<path d="M34 31 C34 17 66 17 66 31 L62 34 L38 34Z" fill="#FFFFFF" stroke="#C9D2CF" stroke-width="1"/><path d="M48 21h4v3h3v4h-3v3h-4v-3h-3v-4h3z" fill="#1F6F5C"/><path d="M36 67 C34 85 66 85 64 67" fill="none" stroke="#3B4A52" stroke-width="2.6"/><circle cx="50" cy="84" r="3" fill="#3B4A52"/>` : "";
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><clipPath id="c"><circle cx="50" cy="50" r="48"/></clipPath></defs><circle cx="50" cy="50" r="48" fill="#${o.bg}"/><g clip-path="url(#c)"><path d="M14 100 C14 74 30 64 50 64 C70 64 86 74 86 100Z" fill="#${o.top}"/><rect x="43" y="52" width="14" height="16" rx="5" fill="#${o.skin}"/><circle cx="50" cy="42" r="16" fill="#${o.skin}"/>${hair}<circle cx="44" cy="43" r="1.8" fill="#2B2B2B"/><circle cx="56" cy="43" r="1.8" fill="#2B2B2B"/><path d="M44.5 49.5 Q50 54 55.5 49.5" stroke="#8A4B3A" stroke-width="1.8" fill="none" stroke-linecap="round"/>${acc}</g></svg>`;
}
const memberDoor = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><clipPath id="c"><circle cx="50" cy="50" r="48"/></clipPath></defs><circle cx="50" cy="50" r="48" fill="#EBE2F8"/><g clip-path="url(#c)"><rect x="56" y="22" width="28" height="62" rx="2" fill="#FFFFFF" stroke="#5F3AA8" stroke-width="2.5"/><circle cx="62" cy="54" r="2.4" fill="#5F3AA8"/><path d="M8 100 C8 78 20 70 36 70 C52 70 62 78 62 100Z" fill="#8A9A5B"/><rect x="30" y="58" width="12" height="14" rx="4" fill="#F6D9BE"/><circle cx="36" cy="49" r="13" fill="#F6D9BE"/><path d="M23 48 C21 31 51 31 49 48 C46 40 40 38 36 38 C32 38 26 40 23 48Z" fill="#D5D8DC"/><circle cx="31.5" cy="49" r="1.6" fill="#2B2B2B"/><circle cx="40.5" cy="49" r="1.6" fill="#2B2B2B"/><path d="M32 55 Q36 58 40 55" stroke="#8A4B3A" stroke-width="1.6" fill="none" stroke-linecap="round"/></g></svg>`;
const star = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="48" fill="#FCEFD0"/><path d="M50 16 L59.5 38.5 L84 40.5 L65.5 56.5 L71 80.5 L50 68 L29 80.5 L34.5 56.5 L16 40.5 L40.5 38.5Z" fill="#D9A400" stroke="#8A5A00" stroke-width="2.5" stroke-linejoin="round"/></svg>`;
const ART = {
  Ic1: person({ bg: "E3F0EB", skin: "8D5A3C", hair: "2B2B2B", top: "2F8F83", nurse: true }),
  Ic2: memberDoor,
  Ic3: star,
};

/* ---------- layout spec (inches). Everything lives here so the preview and the slide match ---------- */
const items = [];
const add = (o) => items.push(o);
const COLS = [0.5, 4.69, 8.88], CW = 3.95; // three columns, one per lever
const ACC = [C.green, C.purple, C.amber];
const ACCS = [C.greenSoft, C.purpleSoft, C.amberSoft];
const t = (text, o = {}) => ({ text, options: { fontFace: B, fontSize: 12, color: C.ink, ...o } });

// static frame
add({ name: "eyebrow", kind: "text", static: true, x: 0.5, y: 0.3, w: 7, h: 0.28, runs: [t("BUSINESS VALUE  ·  BACK-OF-THE-NAPKIN MATH", { bold: true, fontSize: 11, color: C.green, charSpacing: 3 })] });
add({ name: "title", kind: "text", static: true, x: 0.5, y: 0.55, w: 8.6, h: 0.75, valign: "middle", runs: [t("What right-first-time is worth to Humana, per year.", { fontFace: H, fontSize: 26 })] });
add({ name: "legPub", kind: "node", static: true, x: 9.2, y: 0.72, w: 1.9, h: 0.36, fill: C.pubSoft, line: C.pub, lineW: 1, radius: 0.06, align: "center", margin: [0, 0.04, 0, 0.04], runs: [t("Public or measured", { bold: true, fontSize: 11, color: C.pub })] });
add({ name: "legAsm", kind: "node", static: true, x: 11.23, y: 0.72, w: 1.6, h: 0.36, fill: C.asmSoft, line: C.asm, lineW: 1, radius: 0.06, align: "center", margin: [0, 0.04, 0, 0.04], runs: [t("Assumption", { bold: true, fontSize: 11, color: C.asm })] });
add({ name: "footer", kind: "text", static: true, x: 0.5, y: 6.62, w: 12.33, h: 0.6, runs: [t("Public numbers: Humana 2025 10-K and full-year results, KFF, Health Affairs (2026), CMS Star Ratings, analyst estimates. Assumptions are what a pilot would measure. The total uses the low end of every range.", { fontSize: 9, color: C.muted })] });

// click 1: the three ways prior authorization touches Humana's money
const HEADS = [
  ["Nurses review every request", "A cost: nurse time"],
  ["Members stay or leave", "Revenue: about $17,000 each a year"],
  ["Medicare pays a 4-star bonus", "Revenue: about 5% more per member"],
];
HEADS.forEach(([a, b], i) => {
  add({ name: `Ic${i + 1}`, kind: "image", x: COLS[i], y: 1.48, w: 0.85, h: 0.85 });
  add({ name: `Lb${i + 1}`, kind: "text", x: COLS[i] + 0.98, y: 1.5, w: CW - 1.0, h: 0.8, valign: "middle", runs: [t(a, { bold: true, fontSize: 13, breakLine: true }), t(b, { fontSize: 10.5, color: C.muted })] });
  add({ name: `Ring${i + 1}`, kind: "ring", x: COLS[i] - 0.04, y: 1.42, w: CW + 0.08, h: 0.97, line: ACC[i], lineW: 3 });
});

// the cards each napkin folds into
const CARDS = [
  ["FASTER REVIEW", "$100M to $200M", "saved a year", "9.5M requests × 15 to 30 min × $60 an hour × 75% less reading"],
  ["MEMBERS WHO STAY", "$180M", "revenue kept a year", "104,000 leave over prior authorization × 1 in 10 kept × $17,000. About $17M of it is margin."],
  ["STAR BONUS", "$100M", "expected a year", "$2B on one contract × 5 points better odds of winning the fourth star back"],
];
CARDS.forEach(([eb, big, sub, how], i) => add({
  name: `Card${i + 1}`, kind: "node", x: COLS[i], y: 2.62, w: CW, h: 2.05, fill: ACCS[i], line: ACC[i], lineW: 1.25, radius: 0.1, valign: "top", margin: [0.18, 0.2, 0.12, 0.22],
  runs: [t(eb, { bold: true, fontSize: 11, color: ACC[i], charSpacing: 2, breakLine: true }), t(big, { fontFace: H, fontSize: 28, color: ACC[i], breakLine: true }), t(sub, { fontSize: 13, bold: true, breakLine: true }), t(" ", { fontSize: 6, breakLine: true }), t(how, { fontSize: 10.5, color: C.muted })],
}));

// the napkins: drawn after the cards so each one sits on top while its math is worked
const KIND = { pub: C.pub, asm: C.asm };
const NAPKINS = [
  {
    head: "NAPKIN 1 OF 3  ·  FASTER REVIEW",
    lines: [[["9.5M", "pub"], " standard requests a year (Humana, 2025)"], [["× 15 to 30 min", "asm"], " of nurse review each"], [["× $60", "asm"], " an hour, loaded nurse cost"],
      [["= $140M to $290M", "calc"], " a year spent reading packets"], [["× 75%", "asm"], " less reading time, because the AI reads first"], [["= $100M to $200M", "calc"], " saved a year"]],
    big: "$100M to $200M", sub: "saved a year",
    note: "Not fewer nurses. The same nurses absorb about 25% more members in 2026.",
  },
  {
    head: "NAPKIN 2 OF 3  ·  MEMBERS WHO STAY",
    lines: [[["5.2M", "pub"], " Medicare Advantage members"], [["× 2%", "asm"], " leave because of prior authorization friction"], [["= 104,000", "calc"], " members leave a year"],
      [["× 1 in 10", "asm"], " kept by getting it right the first time"], [["= 10,400", "calc"], " members stay"], [["× $17,000", "pub"], " revenue each a year"], [["= $180M", "calc"], " revenue kept a year"]],
    big: "$180M", sub: "revenue kept a year",
    note: "Evidence: plans that use prior authorization most lose 4.7 points more members than plans that use it least (Health Affairs, 2026).",
  },
  {
    head: "NAPKIN 3 OF 3  ·  STAR BONUS",
    lines: [[["2.3M", "pub"], " members in one contract, H5216 (45%)"], [["× $850", "pub"], " bonus each at 4 stars (5% of $17,000)"], [["= $2B", "calc"], " a year, lost when it fell to 3.5 stars"],
      [["3 measures", "pub"], " sit on prior authorization: getting care, complaints, leaving"], [["× 5 points", "asm"], " better odds of winning the star back"], [["= $100M", "calc"], " expected a year"]],
    big: "$100M", sub: "expected a year",
    note: "Humana says it missed 4 stars by a small number of measures. Size of the prize: about $2B on one contract.",
  },
];
NAPKINS.forEach((n, i) => {
  const k = i + 1;
  add({ name: `Nap${k}`, kind: "node", x: 0.5, y: 2.62, w: 12.33, h: 3.75, fill: C.paper, line: ACC[i], lineW: 1.5, radius: 0.12, runs: [t(" ", { fontSize: 8 })] });
  add({ name: `NapH${k}`, kind: "text", x: 0.85, y: 2.78, w: 7, h: 0.3, runs: [t(n.head, { bold: true, fontSize: 11, color: ACC[i], charSpacing: 2 })] });
  n.lines.forEach((parts, j) => {
    const [[num, kind], rest] = parts;
    add({ name: `M${k}_${j + 1}`, kind: "text", x: 0.85, y: 3.2 + j * 0.42, w: 7.1, h: 0.38, valign: "middle",
      runs: [t(num, { bold: true, fontSize: 15, color: kind === "calc" ? C.ink : KIND[kind] }), t(rest, { fontSize: 14, color: kind === "calc" ? C.ink : C.muted })] });
  });
  add({ name: `Res${k}`, kind: "node", x: 8.3, y: 3.2, w: 4.2, h: 1.35, fill: ACCS[i], line: ACC[i], lineW: 1.25, radius: 0.1, align: "center", margin: [0.06, 0.1, 0.06, 0.1],
    runs: [t(n.big, { fontFace: H, fontSize: 28, color: ACC[i], breakLine: true }), t(n.sub, { fontSize: 13, bold: true })] });
  add({ name: `Note${k}`, kind: "text", x: 8.3, y: 4.75, w: 4.2, h: 1.4, runs: [t(n.note, { fontSize: 11.5, color: C.muted, italic: true })] });
});

// clicks 8 and 9: value, minus what it takes to build and run, equals a rough profit
const box = (name, x, line, fill, eb, big, bigColor, small) => add({ name, kind: "node", x, y: 4.95, w: 3.85, h: 1.3, fill, line, lineW: 1.25, radius: 0.1, valign: "middle", margin: [0.08, 0.16, 0.08, 0.2],
  runs: [t(eb, { bold: true, fontSize: 10.5, color: C.muted, charSpacing: 2, breakLine: true }), t(big, { fontFace: H, fontSize: 22, color: bigColor, breakLine: true }), ...small] });
const sm = (text, o = {}) => t(text, { fontSize: 10, color: C.muted, ...o });
box("Total", 0.5, C.ink, C.white, "VALUE THAT REACHES PROFIT", "About $217M a year", C.ink, [sm("$100M saved + $100M star bonus + $17M margin on members kept. Total value about $400M.")]);
add({ name: "Minus", kind: "text", x: 4.35, y: 4.95, w: 0.4, h: 1.3, align: "center", valign: "middle", runs: [t("−", { fontFace: H, fontSize: 26, color: C.muted })] });
box("Cost", 4.75, C.asm, C.white, "COST TO BUILD AND RUN", "About $10M a year", C.ink,
  [sm("AI ", {}), sm("$1.2M", { bold: true, color: C.pub }), sm(" · parsing ", {}), sm("$2M", { bold: true, color: C.pub }), sm(" · team ", {}), sm("$3.75M", { bold: true, color: C.asm }), sm(" · platform ", {}), sm("$2M", { bold: true, color: C.asm })]);
add({ name: "Equals", kind: "text", x: 8.6, y: 4.95, w: 0.4, h: 1.3, align: "center", valign: "middle", runs: [t("=", { fontFace: H, fontSize: 26, color: C.muted })] });
box("Profit", 9.0, C.green, C.greenSoft, "ROUGH PROFIT", "About $207M a year", C.green, [sm("13% of Humana's 2025 profit. About 20 to 1.")]);

/* ---------- timeline: one click per slot ---------- */
const FI = (name, delay = 0, dur = 450) => ({ t: "fadeIn", name, delay, dur });
const FO = (name, delay = 0, dur = 350) => ({ t: "fadeOut", name, delay, dur });
const napIn = (k) => {
  const n = NAPKINS[k - 1].lines.length;
  return [FI(`Ring${k}`), FI(`Nap${k}`), FI(`NapH${k}`, 150), ...Array.from({ length: n }, (_, j) => FI(`M${k}_${j + 1}`, 450 + j * 450)), FI(`Res${k}`, 450 + n * 450 + 150), FI(`Note${k}`, 450 + n * 450 + 500)];
};
const napOut = (k) => {
  const n = NAPKINS[k - 1].lines.length;
  return [FO(`Nap${k}`), FO(`NapH${k}`), ...Array.from({ length: n }, (_, j) => FO(`M${k}_${j + 1}`)), FO(`Res${k}`), FO(`Note${k}`), FO(`Ring${k}`), FI(`Card${k}`, 300, 600)];
};
const slots = [
  { fx: [FI("Ic1"), FI("Lb1"), FI("Ic2", 350), FI("Lb2", 350), FI("Ic3", 700), FI("Lb3", 700)] },
  { fx: napIn(1) }, { fx: napOut(1) },
  { fx: napIn(2) }, { fx: napOut(2) },
  { fx: napIn(3) }, { fx: napOut(3) },
  { fx: [FI("Total")] },
  { fx: [FI("Minus"), FI("Cost", 200), FI("Equals", 1200), FI("Profit", 1500, 600)] },
];
const STEP_NOTES = [
  "Prior authorization touches Humana's money in three places. Nurses review every request, which is a cost. Members decide whether to stay, which is revenue. And Medicare pays a bonus to plans with four stars.",
  "Start with the nurses. Humana gets about 9.5 million standard requests a year. Say each takes 15 to 30 minutes, at about 60 dollars an hour. That is 140 to 290 million dollars a year spent reading packets. If the AI reads first and cuts reading time by three quarters, Humana saves 100 to 200 million.",
  "And that is not fewer nurses. The same nurses absorb the growth: about 25 percent more members in 2026.",
  "Next, members. Humana has 5.2 million. A 2026 study found members leave more often from plans that use prior authorization most. Say it pushes 2 percent of Humana's members out: about 104,000 a year. Keep one in ten by getting it right the first time, and 10,400 members stay. At 17,000 dollars each, that is 180 million of revenue kept.",
  "About 17 million of that is margin. And a member who stays this year usually stays next year too.",
  "Last, stars. One Humana contract, 2.3 million members, fell from four and a half stars to three and a half. That bonus is about 850 dollars a member, about 2 billion a year. Three of the measures sit on prior authorization: getting care, complaints and leaving. Raise the odds of winning the star back by 5 points, and that is worth 100 million a year.",
  "I cannot claim how much of the star we win back. That is why it is an expected value, and why the pilot measures the survey and complaint scores directly.",
  "Add up the low end: about 400 million dollars of value a year. Not all of it is profit. For the members we keep, only the margin counts. So the part that reaches profit is about 217 million.",
  "It costs about 10 million a year to build and run. The AI itself is about 1 million: 13 cents a case, measured. Turning the faxed pages into text is about 2 million. The team and the platform are the rest. And 10 million is the high end. These people would not work on this full time. They would share their time with other work. And I used Unstructured's public API, which is a full pipeline. With an enterprise contract, or a simpler parser, that cost drops by about a third. So, after cost, about 200 million a year in profit. Humana made 1.6 billion in profit last year, so that is more than 10 percent on top. For every dollar Humana spends, it gets about 20 back. And the pilot tells us which of these numbers are real.",
];

/* ---------- build ---------- */
function draw(pres, s, PNG) {
  const m2 = (m) => m.map((v) => v * 72);
  items.forEach((o) => {
    if (o.kind === "image") s.addImage({ data: "image/png;base64," + PNG[o.name], x: o.x, y: o.y, w: o.w, h: o.h, objectName: o.name });
    else if (o.kind === "ring") s.addShape(pres.ShapeType.roundRect, { x: o.x, y: o.y, w: o.w, h: o.h, rectRadius: 0.1, fill: { type: "none" }, line: { color: o.line, width: o.lineW }, objectName: o.name });
    else if (o.kind === "node") {
      const m = o.margin || [0.06, 0.12, 0.06, 0.12]; // top, right, bottom, left
      s.addText(o.runs, { shape: pres.ShapeType.roundRect, rectRadius: o.radius ?? 0.08, x: o.x, y: o.y, w: o.w, h: o.h, fill: { color: o.fill }, line: { color: o.line, width: o.lineW }, align: o.align || "left", valign: o.valign || "middle", margin: m2([m[3], m[1], m[2], m[0]]), objectName: o.name, isTextBox: false });
    } else s.addText(o.runs, { x: o.x, y: o.y, w: o.w, h: o.h, align: o.align || "left", valign: o.valign || "top", margin: 0, objectName: o.name, isTextBox: true, fit: "none" });
  });
}

async function main() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE";
  pres.title = "Business value";
  pres.author = "Nisha Mishra";
  const PNG = {};
  for (const [k, svg] of Object.entries(ART)) PNG[k] = Buffer.from(new Resvg(svg, { fitTo: { mode: "width", value: 360 } }).render().asPng()).toString("base64");
  const s = pres.addSlide();
  s.background = { color: C.white };
  draw(pres, s, PNG);
  s.addNotes(["One slide. Click once per step. Finish the talking point, then click."].concat(STEP_NOTES.map((x, i) => "Click " + (i + 1) + ": " + x)).join(String.fromCharCode(10, 10)));
  await pres.writeFile({ fileName: OUT });

  const zip = await JSZip.loadAsync(fs.readFileSync(OUT));
  const f = "ppt/slides/slide1.xml";
  let xml = await zip.file(f).async("string");
  const ids = {};
  for (const m of xml.matchAll(/<p:cNvPr id="(\d+)" name="([^"]*)"/g)) ids[m[2]] = m[1];
  const missing = [...new Set(slots.flatMap((sl) => sl.fx.map((e) => e.name)))].filter((n) => !ids[n]);
  if (missing.length) throw new Error("No shape for: " + missing.join(", "));
  const byName = Object.fromEntries(items.map((o) => [o.name, o]));
  xml = xml.replace("</p:sld>", buildTiming(ids, byName) + "</p:sld>");
  zip.file(f, xml);
  fs.writeFileSync(OUT, await zip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" }));
  fs.writeFileSync(path.join(__dirname, "preview_value_math.html"), preview());
  console.log("wrote", OUT, "|", slots.length, "clicks");
}

function buildTiming(ids, byName) {
  let n = 3;
  const id = () => n++;
  const setVis = (spid, val, delay) => `<p:set><p:cBhvr><p:cTn id="${id()}" dur="1" fill="hold"><p:stCondLst><p:cond delay="${delay}"/></p:stCondLst></p:cTn><p:tgtEl><p:spTgt spid="${spid}"/></p:tgtEl><p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst></p:cBhvr><p:to><p:strVal val="${val}"/></p:to></p:set>`;
  const filt = (spid, trans, dur) => `<p:animEffect transition="${trans}" filter="fade"><p:cBhvr><p:cTn id="${id()}" dur="${dur}"/><p:tgtEl><p:spTgt spid="${spid}"/></p:tgtEl></p:cBhvr></p:animEffect>`;
  const effect = (e, nodeType) => {
    const spid = ids[e.name], o = byName[e.name];
    const grp = o.kind === "image" ? "" : ' grpId="0"';
    const body = e.t === "fadeIn" ? setVis(spid, "visible", 0) + filt(spid, "in", e.dur) : filt(spid, "out", e.dur) + setVis(spid, "hidden", Math.max(e.dur - 1, 0));
    return `<p:par><p:cTn id="${id()}" presetID="10" presetClass="${e.t === "fadeIn" ? "entr" : "exit"}" presetSubtype="0" fill="hold"${grp} nodeType="${nodeType}"><p:stCondLst><p:cond delay="${e.delay}"/></p:stCondLst><p:childTnLst>${body}</p:childTnLst></p:cTn></p:par>`;
  };
  let clicksXml = "";
  slots.forEach((sl) => {
    const outerId = id(), slotId = id();
    const inner = sl.fx.map((e, k) => effect(e, k === 0 ? "clickEffect" : "withEffect")).join("");
    clicksXml += `<p:par><p:cTn id="${outerId}" fill="hold"><p:stCondLst><p:cond delay="indefinite"/></p:stCondLst><p:childTnLst><p:par><p:cTn id="${slotId}" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>${inner}</p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn></p:par>`;
  });
  const bld = [...new Set(slots.flatMap((sl) => sl.fx.map((e) => e.name)))].filter((nm) => byName[nm].kind !== "image")
    .map((nm) => { const o = byName[nm]; const bg = o.kind === "ring" || (o.kind === "node" && o.fill); return `<p:bldP spid="${ids[nm]}" grpId="0"${bg ? ' animBg="1"' : ""}/>`; }).join("");
  return `<p:timing><p:tnLst><p:par><p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot"><p:childTnLst><p:seq concurrent="1" nextAc="seek"><p:cTn id="2" dur="indefinite" nodeType="mainSeq"><p:childTnLst>${clicksXml}</p:childTnLst></p:cTn><p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst><p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst></p:seq></p:childTnLst></p:cTn></p:par></p:tnLst><p:bldLst>${bld}</p:bldLst></p:timing>`;
}

/* ---------- static preview. ?step=N shows what is on screen after N clicks ---------- */
function preview() {
  const px = 96, pt = (v) => v * 1.3333;
  const esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;");
  const html = items.map((o) => {
    const base = `left:${o.x * px}px;top:${o.y * px}px;width:${o.w * px}px;height:${o.h * px}px;`;
    if (o.kind === "image") return `<img data-n="${o.name}" src="data:image/svg+xml;base64,${Buffer.from(ART[o.name]).toString("base64")}" style="position:absolute;${base}">`;
    if (o.kind === "ring") return `<div data-n="${o.name}" style="position:absolute;${base}border:${o.lineW}px solid #${o.line};border-radius:10px;box-sizing:border-box"></div>`;
    const inner = o.runs.map((r) => `<span style="font-family:${r.options.fontFace || B};font-size:${pt(r.options.fontSize || 12)}px;font-weight:${r.options.bold ? 700 : 400};font-style:${r.options.italic ? "italic" : "normal"};letter-spacing:${(r.options.charSpacing || 0) * 0.5}px;color:#${r.options.color || C.ink}">${esc(r.text)}</span>${r.options.breakLine ? "<br>" : ""}`).join("");
    const m = o.margin ? o.margin.map((v) => v * px) : [0, 0, 0, 0];
    const box = o.kind === "node" ? `background:#${o.fill};border:${o.lineW}px solid #${o.line};border-radius:${(o.radius ?? 0.08) * px}px;` : "";
    const jc = (o.valign || (o.kind === "node" ? "middle" : "top")) === "top" ? "flex-start" : "center";
    return `<div data-n="${o.name}" style="position:absolute;${base}${box}box-sizing:border-box;overflow:hidden;display:flex;flex-direction:column;justify-content:${jc};text-align:${o.align || "left"};padding:${m[0]}px ${m[1]}px ${m[2]}px ${m[3]}px;line-height:1.18"><div>${inner}</div></div>`;
  }).join("\n");
  const data = JSON.stringify(slots.map((sl) => sl.fx.map((e) => [e.name, e.t])));
  const script = `<script>const S=${data};const q=new URLSearchParams(location.search).get("step");const k=q===null?S.length:+q;const vis={};const all=new Set(S.flat().map(e=>e[0]));S.slice(0,k).forEach(sl=>sl.forEach(([n,t])=>{vis[n]=t!=="fadeOut"}));document.querySelectorAll("[data-n]").forEach(el=>{const n=el.dataset.n;if(all.has(n)&&!vis[n])el.style.display="none"})</script>`;
  return `<!doctype html><meta charset="utf-8"><body style="margin:0;background:#fff"><div style="position:relative;width:${13.333 * px}px;height:${7.5 * px}px;background:#fff">${html}</div>${script}`;
}

main().catch((e) => { console.error(e); process.exit(1); });
