// Builds two static slides in the business value style:
//   Metrics.pptx          metrics and leading indicators, one column per value lever (nurses, members, stars)
//   Evals_Framework.pptx  how we know the AI is right, before go-live (test sets) and after (every human decision)
// Run:  node build_metrics_evals.js   (NODE_PATH must point at pptxgenjs and @resvg/resvg-js)
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");
const { Resvg } = require("@resvg/resvg-js");

const C = {
  ink: "16211E", muted: "5C6B66", line: "CBD5D1", white: "FFFFFF", paper: "FAF8F3",
  green: "1F6F5C", greenSoft: "E3F0EB", purple: "5F3AA8", purpleSoft: "EBE2F8", amber: "8A5A00", amberSoft: "FCEFD0",
  coral: "B8452F", coralSoft: "FBE9E4", pub: "2F5DA8", pubSoft: "E4ECF8",
};
const H = "Cambria", B = "Calibri";
const t = (text, o = {}) => ({ text, options: { fontFace: B, fontSize: 12, color: C.ink, ...o } });

/* ---------- the same three icons as the value slide ---------- */
const nurse = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><clipPath id="c"><circle cx="50" cy="50" r="48"/></clipPath></defs><circle cx="50" cy="50" r="48" fill="#E3F0EB"/><g clip-path="url(#c)"><path d="M14 100 C14 74 30 64 50 64 C70 64 86 74 86 100Z" fill="#2F8F83"/><rect x="43" y="52" width="14" height="16" rx="5" fill="#8D5A3C"/><circle cx="50" cy="42" r="16" fill="#8D5A3C"/><path d="M33 42 C31 22 69 22 67 42 C63 33 55 30 50 30 C45 30 37 33 33 42Z" fill="#2B2B2B"/><circle cx="44" cy="43" r="1.8" fill="#2B2B2B"/><circle cx="56" cy="43" r="1.8" fill="#2B2B2B"/><path d="M44.5 49.5 Q50 54 55.5 49.5" stroke="#8A4B3A" stroke-width="1.8" fill="none" stroke-linecap="round"/><path d="M34 31 C34 17 66 17 66 31 L62 34 L38 34Z" fill="#FFFFFF" stroke="#C9D2CF" stroke-width="1"/><path d="M48 21h4v3h3v4h-3v3h-4v-3h-3v-4h3z" fill="#1F6F5C"/><path d="M36 67 C34 85 66 85 64 67" fill="none" stroke="#3B4A52" stroke-width="2.6"/><circle cx="50" cy="84" r="3" fill="#3B4A52"/></g></svg>`;
const member = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><clipPath id="c"><circle cx="50" cy="50" r="48"/></clipPath></defs><circle cx="50" cy="50" r="48" fill="#EBE2F8"/><g clip-path="url(#c)"><rect x="56" y="22" width="28" height="62" rx="2" fill="#FFFFFF" stroke="#5F3AA8" stroke-width="2.5"/><circle cx="62" cy="54" r="2.4" fill="#5F3AA8"/><path d="M8 100 C8 78 20 70 36 70 C52 70 62 78 62 100Z" fill="#8A9A5B"/><rect x="30" y="58" width="12" height="14" rx="4" fill="#F6D9BE"/><circle cx="36" cy="49" r="13" fill="#F6D9BE"/><path d="M23 48 C21 31 51 31 49 48 C46 40 40 38 36 38 C32 38 26 40 23 48Z" fill="#D5D8DC"/><circle cx="31.5" cy="49" r="1.6" fill="#2B2B2B"/><circle cx="40.5" cy="49" r="1.6" fill="#2B2B2B"/><path d="M32 55 Q36 58 40 55" stroke="#8A4B3A" stroke-width="1.6" fill="none" stroke-linecap="round"/></g></svg>`;
const star = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="48" fill="#FCEFD0"/><path d="M50 16 L59.5 38.5 L84 40.5 L65.5 56.5 L71 80.5 L50 68 L29 80.5 L34.5 56.5 L16 40.5 L40.5 38.5Z" fill="#D9A400" stroke="#8A5A00" stroke-width="2.5" stroke-linejoin="round"/></svg>`;

/* ======================= slide 1: metrics and leading indicators ======================= */
function metricsSlide() {
  const items = [], add = (o) => items.push(o);
  const office = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><clipPath id="c"><circle cx="50" cy="50" r="48"/></clipPath></defs><circle cx="50" cy="50" r="48" fill="#E2EEF4"/><g clip-path="url(#c)"><rect x="20" y="34" width="60" height="60" fill="#FFFFFF" stroke="#2E6B8A" stroke-width="2"/><rect x="43" y="14" width="14" height="22" fill="#2E6B8A"/><rect x="39" y="18" width="22" height="14" fill="#2E6B8A"/><path d="M50 17v16M42 25h16" stroke="#fff" stroke-width="4"/><g fill="#BCD3E0"><rect x="27" y="44" width="10" height="10"/><rect x="45" y="44" width="10" height="10"/><rect x="63" y="44" width="10" height="10"/><rect x="27" y="62" width="10" height="10"/><rect x="63" y="62" width="10" height="10"/></g><rect x="42" y="68" width="16" height="26" fill="#8FA9B8"/></g></svg>`;
  const shield = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="48" fill="#FCEFD0"/><path d="M50 16 L78 26 L78 50 C78 68 66 80 50 86 C34 80 22 68 22 50 L22 26Z" fill="#FFFFFF" stroke="#8A5A00" stroke-width="3" stroke-linejoin="round"/><path d="M37 51 L46 60 L64 41" fill="none" stroke="#8A5A00" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
  const slate = "2E6B8A", slateSoft = "E2EEF4";
  add({ name: "eyebrow", kind: "text", x: 0.5, y: 0.3, w: 8, h: 0.28, runs: [t("METRICS AND LEADING INDICATORS", { bold: true, fontSize: 11, color: C.green, charSpacing: 3 })] });
  add({ name: "title", kind: "text", x: 0.5, y: 0.55, w: 12.3, h: 0.75, valign: "middle", runs: [t("How we know it is working, for everyone it touches.", { fontFace: H, fontSize: 26 })] });
  // north star
  add({ name: "nsBox", kind: "node", x: 0.5, y: 1.42, w: 12.33, h: 0.95, fill: C.white, line: C.green, lineW: 1.5, radius: 0.1, runs: [t(" ", { fontSize: 8 })] });
  add({ name: "nsLeft", kind: "text", x: 0.8, y: 1.47, w: 3.9, h: 0.85, valign: "middle", runs: [t("NORTH STAR", { bold: true, fontSize: 10.5, color: C.green, charSpacing: 2, breakLine: true }), t("Right-first-time rate", { fontFace: H, fontSize: 22, color: C.green })] });
  add({ name: "nsRight", kind: "text", x: 4.85, y: 1.47, w: 7.75, h: 0.85, valign: "middle", runs: [t("Of every 100 requests, how many get the right answer the first time, with no back and forth.", { fontSize: 13, bold: true, breakLine: true }), t("Rework: asking for something already sent, a director sending it back, or a denial overturned when the packet had the answer.", { fontSize: 10.5, color: C.muted })] });
  // one column per stakeholder the brief names
  const CW = 2.93, gap = 0.2, top = 2.55, ch = 3.3;
  const WHO = [
    { icon: member, acc: C.purple, soft: C.purpleSoft, name: "Member", value: "Care on time. Not stuck while faxes go back and forth.",
      lead: ["Days to a decision", "Fax in to answer out. Lower is better."], lag: ["Members leaving the plan", "Members with a request, against those without."] },
    { icon: office, acc: slate, soft: slateSoft, name: "Provider", value: "One clear question. Not “send everything again.”",
      lead: ["Avoidable pends", "We asked for something already sent. Lower is better."], lag: ["Appeals and complaints", "About prior authorization. Lower is better."] },
    { icon: nurse, acc: C.green, soft: C.greenSoft, name: "Nurse and director", value: "Review the evidence. No hunting.",
      lead: ["Minutes per case", "Nurse: open to decision. Lower is better."], lead2: ["Avoidable escalations", "Director: sent up for missing info only."], lag: ["Cost per decision", "Review spend per decided case."] },
    { icon: shield, acc: C.amber, soft: C.amberSoft, name: "Humana", value: "Lower cost, members who stay, Stars protected.",
      lead: ["Member complaints to Medicare", "Filed any time, so we see them in weeks. Also a Star measure."], lag: ["Star rating", "Including the “getting needed care” survey."] },
  ];
  WHO.forEach((W, i) => {
    const x = 0.5 + i * (CW + gap);
    add({ name: `col${i}`, kind: "node", x, y: top, w: CW, h: ch, fill: W.soft, line: W.acc, lineW: 1.25, radius: 0.1, runs: [t(" ", { fontSize: 8 })] });
    add({ name: `ic${i}`, kind: "image", art: W.icon, x: x + 0.18, y: top + 0.16, w: 0.56, h: 0.56 });
    add({ name: `hd${i}`, kind: "text", x: x + 0.86, y: top + 0.16, w: CW - 0.98, h: 0.56, valign: "middle", runs: [t(W.name, { bold: true, fontSize: 14, color: W.acc })] });
    const row = (label, [a, b]) => [t(label, { bold: true, fontSize: 9, color: W.acc, charSpacing: 2, breakLine: true }), t(a, { bold: true, fontSize: 12.5, breakLine: true }), t(b, { fontSize: 10.5, color: C.muted, breakLine: true })];
    add({ name: `bd${i}`, kind: "text", x: x + 0.2, y: top + 0.85, w: CW - 0.4, h: ch - 0.95,
      runs: [t(W.value, { fontSize: 11.5, italic: true, color: C.ink, breakLine: true }), t(" ", { fontSize: 7, breakLine: true }), ...row("LEADING  ·  WEEKS", W.lead),
        ...(W.lead2 ? [t(W.lead2[0], { bold: true, fontSize: 12.5, breakLine: true }), t(W.lead2[1], { fontSize: 10.5, color: C.muted, breakLine: true })] : []),
        t(" ", { fontSize: 7, breakLine: true }), ...row("LAGGING  ·  QUARTERS", W.lag)] });
  });
  add({ name: "guard", kind: "node", x: 0.5, y: 6.0, w: 12.33, h: 0.5, fill: C.coralSoft, line: C.coral, lineW: 1, radius: 0.08, margin: [0.04, 0.2, 0.04, 0.22],
    runs: [t("GUARDRAILS   ", { bold: true, fontSize: 10.5, color: C.coral, charSpacing: 2 }), t("Never slower than the CMS clock  ·  Zero wrong approvals  ·  The AI never denies", { fontSize: 12, color: C.ink })] });
  add({ name: "footer", kind: "text", x: 0.5, y: 6.65, w: 12.33, h: 0.5, runs: [t("Days to a decision, avoidable pends, minutes per case and escalations are live today, in the app's dashboard and in Honeycomb. Complaints and the lagging numbers need Humana's own data.", { fontSize: 9, color: C.muted })] });
  const notes = [
    "So how do we know this is working? One number to win: the right-first-time rate. Out of every 100 requests, how many get the right answer the first time, with no back and forth.",
    "Then one leading number and one lagging number for each person this touches. Leading numbers move in weeks. Lagging numbers take quarters.",
    "For the member, the leading number is days to a decision. How fast can we get them an answer? Over time, it is fewer members leaving the plan. That is member satisfaction, showing up in who stays.",
    "For the provider, it is fewer avoidable pends. And when we do pend, we ask the right question, once. Over time, getting it right the first time means fewer appeals and fewer complaints. That builds trust, and a better relationship with the provider.",
    "For the nurse and the medical director, this is human hours, so they will feel it first. For the nurse, it is minutes per case. For the director, it is avoidable escalations: cases that only needed a missing fact, so they never should have reached a physician. Over time, it is a lower cost per decision across the whole utilization management team.",
    "For Humana, the leading number is member complaints to Medicare. Members can file those any time, so we see them within weeks. And complaints are one of the Star measures. Over time, it is the Star rating itself, and that is the bonus we talked about.",
    "And the guardrails, so we do not cheat. Never slower than the CMS clock. Zero wrong approvals. And the AI never denies.",
  ].join("\n\n");
  return { file: "Metrics.pptx", title: "Metrics and leading indicators", items, notes };
}

/* ======================= slide 2: evals framework ======================= */
function evalsSlide() {
  const items = [], add = (o) => items.push(o);
  add({ name: "eyebrow", kind: "text", x: 0.5, y: 0.3, w: 8, h: 0.28, runs: [t("EVALS FRAMEWORK", { bold: true, fontSize: 11, color: C.purple, charSpacing: 3 })] });
  add({ name: "title", kind: "text", x: 0.5, y: 0.55, w: 12.3, h: 0.75, valign: "middle", runs: [t("Tuned for recall. Measured on every run.", { fontFace: H, fontSize: 26 })] });
  // left: the five runs
  add({ name: "runsBox", kind: "node", x: 0.5, y: 1.42, w: 6.85, h: 4.45, fill: C.paper, line: C.line, lineW: 1, radius: 0.1, runs: [t(" ", { fontSize: 8 })] });
  add({ name: "runsH", kind: "text", x: 0.8, y: 1.55, w: 6.4, h: 0.62, runs: [t("FIVE RUNS ON 40 HARD PACKETS", { bold: true, fontSize: 11, color: C.purple, charSpacing: 2, breakLine: true }), t("28 should go to a person. Same model each run. Each run changed the prompt and the guardrails.", { fontSize: 10.5, color: C.muted })] });
  add({ name: "runsChart", kind: "chart", x: 0.7, y: 2.2, w: 6.45, h: 2.85,
    labels: ["1 First test", "2 First fixes", "3 Dates by code", "4 Policy tests", "5 Month tolerance"],
    series: [{ name: "Recall: risky cases caught", values: [57, 89, 79, 86, 86], color: C.purple }, { name: "Precision: flags that were right", values: [94, 78, 96, 92, 92], color: "9C8BC6" }] });
  add({ name: "runsWrong", kind: "text", x: 0.8, y: 5.12, w: 6.4, h: 0.6, valign: "middle", runs: [t("Wrong approvals per run:  ", { bold: true, fontSize: 11 }), t("12  →  3  →  6  →  4  →  4", { fontSize: 12, bold: true, color: C.coral }), t(".  Each one left is a test case we fix next.", { fontSize: 11, color: C.muted })] });
  // right: the four numbers to watch, plus the rest
  add({ name: "watch", kind: "node", x: 7.55, y: 1.42, w: 5.28, h: 4.45, fill: C.white, line: C.purple, lineW: 1.25, radius: 0.1, runs: [t(" ", { fontSize: 8 })] });
  add({ name: "watchH", kind: "text", x: 7.85, y: 1.55, w: 4.8, h: 0.35, runs: [t("FOUR NUMBERS WE WATCH", { bold: true, fontSize: 11, color: C.purple, charSpacing: 2 })] });
  const STEP = [
    ["When a policy is built", "The AI drafts the key facts. It must not miss one.", [["Recall", "100%", "key facts found"], ["Precision", "73%", "approved by the owner"]]],
    ["When a packet is decided", "Risky cases must reach a person. Goal: 100%.", [["Recall", "86%", "risky cases caught"], ["Precision", "92%", "flags that were right"]]],
  ];
  STEP.forEach(([head, sub, pair], i) => {
    const y = 1.98 + i * 1.62;
    add({ name: `sh${i}`, kind: "text", x: 7.85, y, w: 4.8, h: 0.55, runs: [t(head, { bold: true, fontSize: 13, breakLine: true }), t(sub, { fontSize: 10.5, color: C.muted })] });
    pair.forEach(([lbl, num, what], j) => add({ name: `sp${i}${j}`, kind: "text", x: 7.85 + j * 2.45, y: y + 0.6, w: 2.35, h: 0.85,
      runs: [t(num, { fontFace: H, fontSize: 24, color: C.purple, breakLine: true }), t(lbl + ": ", { bold: true, fontSize: 10.5 }), t(what, { fontSize: 10.5, color: C.muted })] }));
  });
  add({ name: "more", kind: "text", x: 7.85, y: 5.22, w: 4.8, h: 0.55, valign: "middle", runs: [t("ALSO TRACKED  ", { bold: true, fontSize: 9.5, color: C.purple, charSpacing: 2 }), t("Errors 0% (0.6% retried)  ·  Speed 18 s typical, 35 s slow  ·  Cost 13 cents a case", { fontSize: 10.5 })] });
  add({ name: "rule", kind: "node", x: 0.5, y: 6.0, w: 12.33, h: 0.5, fill: C.purpleSoft, line: C.purple, lineW: 1, radius: 0.08, margin: [0.04, 0.2, 0.04, 0.22],
    runs: [t("ALL LIVE IN HONEYCOMB   ", { bold: true, fontSize: 10.5, color: C.purple, charSpacing: 2 }), t("Every run and every human decision is tracked continuously. A human check is relaxed only when recall stays at 100%.", { fontSize: 11.5 })] });
  add({ name: "footer", kind: "text", x: 0.5, y: 6.65, w: 12.33, h: 0.5, runs: [t("Packets are made up. Policy-build numbers are from the owner's live reviews; the nurse numbers are still too few to show. Next: de-identified real cases, labelled by senior nurses first.", { fontSize: 9, color: C.muted })] });
  const notes = [
    "This is how I know the AI is right. I am tuning it for recall over precision, the trade-off I talked about. A miss is a wrong approval, so recall comes first.",
    "I built about 40 hard packets, and I designed 28 of them so they should go to a person. I ran them five times, with the same model each time. Each run, I changed the prompt and the guardrails, and watched both numbers.",
    "In run one, recall was only 57 percent. Twelve risky cases were approved.",
    "In run two, recall jumped to 89 percent, but precision dropped. It was flagging too much.",
    "In run three, I moved date counting into code. Before, the AI was working out things like six months of therapy from the dates, and it got some of them wrong. Now plain code does that math. Precision went back up, but recall dipped. It let a few more risky cases through.",
    "By run four, it settled: 86 percent recall and 92 percent precision. Every miss that is left becomes a test case I fix next.",
    "In run five, the numbers held. That is when I knew it was stable enough.",
    "There are four numbers I keep watching: recall and precision, at two steps. First, when a policy is built. The AI drafts the key facts, and it should not miss any, so recall matters most there. Second, when a packet is decided. Risky cases have to reach a person, so recall has to get to 100 percent.",
    "Then there is error rate, latency and cost. Zero failed calls. About 18 seconds a case. About 13 cents a case.",
    "All of this is tracked continuously in Honeycomb, and I will show you that in the demo.",
  ].join("\n\n");
  return { file: "Evals_Framework.pptx", title: "Evals framework", items, notes };
}

/* ---------- shared drawing + preview ---------- */
function draw(pres, s, items) {
  const m2 = (m) => m.map((v) => v * 72);
  items.forEach((o) => {
    if (o.kind === "chart") {
      s.addChart(pres.charts.LINE, o.series.map((x) => ({ name: x.name, labels: o.labels, values: x.values })), {
        x: o.x, y: o.y, w: o.w, h: o.h, objectName: o.name, chartColors: o.series.map((x) => x.color), lineSize: 3, lineDataSymbol: "circle", lineDataSymbolSize: 8,
        showValue: true, dataLabelPosition: "t", dataLabelFormatCode: '0"%"', dataLabelFontSize: 10, dataLabelFontFace: "Calibri", dataLabelColor: C.ink,
        valAxisMinVal: 40, valAxisMaxVal: 100, valAxisMajorUnit: 20, valAxisLabelFormatCode: '0"%"', valAxisLabelFontSize: 9, valAxisLabelColor: C.muted, valAxisLabelFontFace: "Calibri",
        catAxisLabelFontSize: 10, catAxisLabelColor: C.muted, catAxisLabelFontFace: "Calibri", valGridLine: { color: "E3E7E5", size: 0.5 }, catGridLine: { style: "none" },
        showLegend: true, legendPos: "b", legendFontSize: 10, legendFontFace: "Calibri", legendColor: C.ink,
      });
    } else if (o.kind === "image") s.addImage({ data: "image/png;base64," + Buffer.from(new Resvg(o.art, { fitTo: { mode: "width", value: 300 } }).render().asPng()).toString("base64"), x: o.x, y: o.y, w: o.w, h: o.h, objectName: o.name });
    else if (o.kind === "node") {
      const m = o.margin || [0.06, 0.12, 0.06, 0.12];
      s.addText(o.runs, { shape: pres.ShapeType.roundRect, rectRadius: o.radius ?? 0.08, x: o.x, y: o.y, w: o.w, h: o.h, fill: { color: o.fill }, line: { color: o.line, width: o.lineW }, align: o.align || "left", valign: o.valign || "middle", margin: m2([m[3], m[1], m[2], m[0]]), objectName: o.name, isTextBox: false });
    } else s.addText(o.runs, { x: o.x, y: o.y, w: o.w, h: o.h, align: o.align || "left", valign: o.valign || "top", margin: 0, objectName: o.name, isTextBox: true, fit: "none" });
  });
}
function preview(items) {
  const px = 96, pt = (v) => v * 1.3333, esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;");
  const html = items.map((o) => {
    const base = `left:${o.x * px}px;top:${o.y * px}px;width:${o.w * px}px;height:${o.h * px}px;`;
    if (o.kind === "chart") {
      const W = o.w * px, Hh = o.h * px, padL = 40, padB = 60, padT = 18, n = o.labels.length;
      const X = (i) => padL + (i + 0.5) * ((W - padL - 10) / n), Y = (v) => padT + (100 - v) / 60 * (Hh - padT - padB);
      const lines = o.series.map((sr) => `<polyline fill="none" stroke="#${sr.color}" stroke-width="3" points="${sr.values.map((v, i) => X(i) + "," + Y(v)).join(" ")}"/>` +
        sr.values.map((v, i) => `<circle cx="${X(i)}" cy="${Y(v)}" r="4" fill="#${sr.color}"/><text x="${X(i)}" y="${Y(v) - 8}" font-size="12" text-anchor="middle" font-family="Calibri">${v}%</text>`).join("")).join("");
      const grid = [40, 60, 80, 100].map((v) => `<line x1="${padL}" x2="${W - 10}" y1="${Y(v)}" y2="${Y(v)}" stroke="#E3E7E5"/><text x="${padL - 6}" y="${Y(v) + 4}" font-size="11" text-anchor="end" fill="#5C6B66" font-family="Calibri">${v}%</text>`).join("");
      const cats = o.labels.map((l, i) => `<text x="${X(i)}" y="${Hh - padB + 18}" font-size="12" text-anchor="middle" fill="#5C6B66" font-family="Calibri">${l}</text>`).join("");
      const leg = o.series.map((sr, k) => `<rect x="${padL + k * 230}" y="${Hh - 22}" width="12" height="12" fill="#${sr.color}"/><text x="${padL + k * 230 + 18}" y="${Hh - 12}" font-size="12" font-family="Calibri">${sr.name}</text>`).join("");
      return `<svg style="position:absolute;${base}" width="${W}" height="${Hh}">${grid}${lines}${cats}${leg}</svg>`;
    }
    if (o.kind === "image") return `<img src="data:image/svg+xml;base64,${Buffer.from(o.art).toString("base64")}" style="position:absolute;${base}">`;
    const inner = o.runs.map((r) => `<span style="font-family:${r.options.fontFace || B};font-size:${pt(r.options.fontSize || 12)}px;font-weight:${r.options.bold ? 700 : 400};letter-spacing:${(r.options.charSpacing || 0) * 0.5}px;color:#${r.options.color || C.ink}">${esc(r.text)}</span>${r.options.breakLine ? "<br>" : ""}`).join("");
    const m = o.margin ? o.margin.map((v) => v * px) : [0, 0, 0, 0];
    const box = o.kind === "node" ? `background:#${o.fill};border:${o.lineW}px solid #${o.line};border-radius:${(o.radius ?? 0.08) * px}px;` : "";
    const jc = (o.valign || (o.kind === "node" ? "middle" : "top")) === "top" ? "flex-start" : "center";
    return `<div style="position:absolute;${base}${box}box-sizing:border-box;overflow:hidden;display:flex;flex-direction:column;justify-content:${jc};text-align:${o.align || "left"};padding:${m[0]}px ${m[1]}px ${m[2]}px ${m[3]}px;line-height:1.18"><div>${inner}</div></div>`;
  }).join("\n");
  return `<!doctype html><meta charset="utf-8"><body style="margin:0;background:#fff"><div style="position:relative;width:${13.333 * px}px;height:${7.5 * px}px;background:#fff">${html}</div>`;
}

async function main() {
  for (const sl of [metricsSlide(), evalsSlide()]) {
    const pres = new pptxgen();
    pres.layout = "LAYOUT_WIDE";
    pres.title = sl.title;
    pres.author = "Nisha Mishra";
    const s = pres.addSlide();
    s.background = { color: C.white };
    draw(pres, s, sl.items);
    s.addNotes(sl.notes);
    await pres.writeFile({ fileName: path.join(__dirname, sl.file) });
    fs.writeFileSync(path.join(__dirname, "preview_" + sl.file.replace(".pptx", ".html")), preview(sl.items));
    console.log("wrote", sl.file);
  }
}
main().catch((e) => { console.error(e); process.exit(1); });
