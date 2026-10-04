// Slide: the metrics. Run: node build_metrics.js
const { Slide, C, B, H } = require("./kit");

const s = new Slide({ file: "Metrics", title: "How we measure it", eyebrow: "METRICS", heading: "One number to win, and guardrails so we do not cheat.", sub: "Right first time", footer: "Source: docs/METRICS_FRAMEWORK.md. Humana's public figure for context: 64.7% of appealed Medicare Advantage denials were overturned in 2025." });

const card = (name, x, y, w, h, fill, line, tag, tc, title, rows, o = {}) => {
  const r = [{ text: tag, options: { bold: true, fontSize: 9, color: tc, fontFace: B, charSpacing: 1.5, breakLine: true, paraSpaceAfter: 3 } }];
  if (title) r.push({ text: title, options: { bold: true, fontSize: o.ts || 17, color: C.ink, fontFace: o.tf || B, breakLine: true, paraSpaceAfter: 6 } });
  rows.forEach(([a, b], i) => { r.push({ text: a, options: { bold: true, fontSize: 11.5, color: C.ink, fontFace: B, breakLine: true } }); if (b) r.push({ text: b, options: { fontSize: 10.5, color: C.muted, fontFace: B, breakLine: i < rows.length - 1, paraSpaceAfter: 5 } }); });
  s.node(name, x, y, w, h, r, { fill, line, lineW: 1.25, radius: 0.1, valign: "top", margin: [0.16, 0.2, 0.06, 0.2] });
};
const W = 3.97, G = 0.21, X = (i) => 0.5 + i * (W + G);
card("M1", X(0), 1.5, W, 3.1, C.greenSoft, C.green, "NORTH STAR", C.green, "Right-first-time rate", [["Of every 100 requests, how many get the right answer the first time, with no back and forth.", ""], ["We only know it fully months later, so in the demo we show the early signals.", ""]], { ts: 20, tf: H });
card("M2", X(1), 1.5, W, 3.1, C.white, C.line, "EARLY SIGNALS, SEEN IN DAYS", C.muted, "", [["First-review rate", "Decided on the first review with no pend. Higher is better."], ["Avoidable pend rate", "Pends where the provider says 'I already sent that'. Lower is better."], ["Avoidable escalation rate", "Escalations the director sends back. Lower is better."]]);
card("M3", X(2), 1.5, W, 3.1, C.coralSoft, C.coral, "GUARDRAILS", C.coral, "", [["Time limit", "We must not slow Humana down. It already meets the CMS clock."], ["Approvals", "If the share of approvals jumps, we may be approving too much."], ["No AI denials", "The AI never denies. A director denies and writes the reason."]]);

s.node("MAi", 0.5, 4.85, 12.33, 2.05, [{ text: "IS THE AI DOING ITS JOB", options: { bold: true, fontSize: 9, color: C.purple, fontFace: B, charSpacing: 1.5 } }], { fill: C.purpleSoft, line: C.purple, lineW: 1.25, radius: 0.1, valign: "top", margin: [0.14, 0.2, 0.06, 0.2] });
const AI = [
  ["Catches what needs a person", "Of the cases that needed a person, how many we flagged. We look at this first."],
  ["Flags that were right", "Of the cases we flagged, how many really needed a person. A miss costs nurse time."],
  ["Wrong approvals", "A case that needed a person but was approved. The dangerous failure."],
  ["Finds details that are there", "Of the details in the packet, how many the AI found."],
  ["Makes up details", "How often the AI claims a detail that is not there."],
  ["Seconds per packet", "How long one packet takes to read."],
];
AI.forEach(([t, d], i) => {
  const x = 0.72 + (i % 3) * 4.1, y = 5.3 + Math.floor(i / 3) * 0.78;
  s.text("AI" + i, x, y, 3.9, 0.72, [{ text: t, options: { bold: true, fontSize: 12, color: C.ink, fontFace: B, breakLine: true } }, { text: d, options: { fontSize: 10.5, color: C.muted, fontFace: B } }]);
});

s.click("One number to win: the right-first-time rate. Out of every hundred requests, how many get the right answer the first time, with no back and forth. That helps the member, the provider, the nurse, and the plan's appeals bill. We only know it fully months later, so in the demo I show early signals.", "M1");
s.click("The early signals we can see in days. The first-review rate: cases decided on the first review with no pend. The avoidable pend rate: pends where the provider says they already sent it. The avoidable escalation rate: escalations a director sends back to the nurse.", "M2");
s.click("Guardrails so we do not cheat. We must not slow Humana down against the CMS clock. If the share of approvals jumps, we may be approving too much to look good. And the AI never denies.", "M3");
s.click("And for the AI itself. I look at recall first: of the cases that needed a person, how many did we catch. A miss is a wrong approval, the dangerous failure. Then precision: of the cases we flagged, how many really needed a person. An extra flag costs a few minutes of nurse time. Then whether it finds the details that are there, and whether it makes any up.", "MAi", "AI0", "AI1", "AI2", "AI3", "AI4", "AI5");

s.build();
