// Builds ONE plain slide: how we know it works (the evals).
// Run:  NODE_PATH="<scratchpad>/tools/node_modules" node build_evals.js   -> Evals.pptx
// Numbers come from docs/eval_scorecard.html (5 stability runs, policy search report, human citation audit).
const path = require("path");
const pptxgen = require("pptxgenjs");

const OUT = path.join(__dirname, "Evals.pptx");
const C = {
  ink: "16211E", muted: "5C6B66", green: "1F6F5C", greenSoft: "E3F0EB", line: "CBD5D1",
  amber: "8A5A00", amberSoft: "FCEFD0", purple: "5F3AA8", white: "FFFFFF",
};
const H = "Cambria", B = "Calibri";

const NOTES = [
  "The last question I would get is: how do you know it works? So I tested it three ways, and I rerun all three every time I change anything.",
  "One, does it read the packet right? I made nine packets with known answers: approve, pend, escalate, a conflicting value, a ruled-out condition, a recent heart attack, and a noisy scan. I ran them five times in a row. Every run found all fifty-three facts that were really there. It never claimed a fact that was missing or ruled out, thirteen checks per run. The right recommendation came back every time. A case takes about twenty seconds. I also asked a separate AI session, which never saw my code, to write forty harder packets from the policy text alone. That is the fairer test, and I will show you those results [fill in when the run finishes].",
  "Two, does it find the right policy for a new service? I tested forty-four services, each described two ways. The old keyword search had the right policy in the top eight about eighty percent of the time. Embeddings from Unstructured Pipelines got it to about ninety-eight percent. I use that to decide how to build the policy library.",
  "Three, can a person trust the citation? I judged twenty-four cited sentences myself, with the answer key hidden. Three out of four were a clear yes, and almost nine out of ten were yes or partly. I also planted five wrong pairs, a claim with a sentence about something else. The product's second check caught all five, and so did I. The weak spots were claims with several parts that cite only one sentence. The fix is to show the whole passage, and I would build that next.",
  "Now the honest part. These packets are made up, and I wrote most of them. This proves the plumbing works. It does not prove accuracy on real faxes. A zero out of sixty-five is good, but it only tells me the true rate is probably under five percent. To claim under one percent I need about three hundred missing-fact checks. The real test is real, de-identified cases, labeled by senior nurses before the tool sees them. And the tool never denies. A missing fact goes to the nurse as not sure, never as a guess.",
].join(String.fromCharCode(10, 10));

async function main() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5 in
  pres.title = "How we know it works";
  pres.author = "Nisha Mishra";
  const s = pres.addSlide();
  s.background = { color: C.white };
  const m2 = (m) => m.map((v) => v * 72); // inches -> points; my order is top, right, bottom, left

  const text = (name, x, y, w, h, runs, o = {}) =>
    s.addText(runs, { x, y, w, h, align: o.align || "left", valign: o.valign || "top", margin: 0, objectName: name, isTextBox: true, fit: "none" });
  const node = (name, x, y, w, h, fill, line, runs, o = {}) => {
    const m = o.margin || [0.06, 0.12, 0.06, 0.12];
    s.addText(runs, { shape: pres.ShapeType.roundRect, rectRadius: o.radius ?? 0.08, x, y, w, h, fill: { color: fill }, line: { color: line, width: o.lineW || 1 }, align: o.align || "left", valign: o.valign || "middle", margin: m2([m[3], m[1], m[2], m[0]]), objectName: name, isTextBox: false });
  };

  text("eyebrow", 0.5, 0.3, 4, 0.28, [{ text: "HOW WE KNOW IT WORKS", options: { bold: true, fontSize: 11, color: C.green, fontFace: B, charSpacing: 3 } }]);
  text("title", 0.5, 0.55, 8.6, 0.75, [{ text: "Three checks. Rerun on every change.", options: { fontSize: 26, color: C.ink, fontFace: H } }], { valign: "middle" });
  text("sub", 8.3, 0.55, 4.53, 0.75, [{ text: "All packets are made up", options: { fontSize: 13, color: C.muted, fontFace: B } }], { align: "right", valign: "middle" });

  const W = 3.97, GAP = 0.21, X = [0.5, 0.5 + W + GAP, 0.5 + 2 * (W + GAP)];
  const card = (i, num, question, big, line, notes, status) => {
    node("Card" + num, X[i], 1.45, W, 3.85, C.white, C.line, [
      { text: num + "  " + question, options: { bold: true, fontSize: 12, color: C.green, fontFace: B, breakLine: true, paraSpaceAfter: 8 } },
      { text: big, options: { fontSize: 34, color: C.ink, fontFace: H, breakLine: true } },
      { text: line, options: { bold: true, fontSize: 12.5, color: C.ink, fontFace: B, breakLine: true, paraSpaceAfter: 6 } },
      ...notes.map((n, k) => ({ text: n, options: { fontSize: 11, color: C.muted, fontFace: B, breakLine: k < notes.length - 1, paraSpaceAfter: 3 } })),
    ], { valign: "top", margin: [0.15, 0.2, 0.1, 0.2], radius: 0.1 });
    if (status) node("Status" + num, X[i] + 0.2, 4.72, W - 0.4, 0.45, C.amberSoft, C.amber, [{ text: status, options: { fontSize: 10.5, color: C.amber, fontFace: B, bold: true } }], { margin: [0.03, 0.12, 0.03, 0.12], radius: 0.06, lineW: 0.75 });
  };
  card(0, "1", "Does it read the packet right?", "53 of 53", "facts found when they were there. Same result in 5 runs.", [
    "0 of 13 absent or ruled-out facts claimed.",
    "Right recommendation in 9 of 9 packets, every run.",
    "About 20 seconds a case.",
  ], "Next: 40 harder packets from a separate AI session");
  card(1, "2", "Does it find the right policy?", "97.7%", "right policy in the top 8 for a new service.", [
    "44 services, each described 2 ways.",
    "Old keyword search: 79.5%.",
    "Embeddings from Unstructured Pipelines.",
  ]);
  card(2, "3", "Can a person trust the citation?", "75% yes", "of 24 cited sentences judged by a person. 88% yes or partly.", [
    "5 of 5 planted wrong pairs caught.",
    "Weak spot: a claim with several parts cites one sentence.",
    "Fix: show the whole passage.",
  ]);

  node("Limits", 0.5, 5.42, 12.33, 0.88, C.amberSoft, C.amber, [
    { text: "What this does not show yet", options: { bold: true, fontSize: 12, color: C.amber, fontFace: B, breakLine: true, paraSpaceAfter: 2 } },
    { text: "Real faxes. These packets are made up and mostly written by us. The real test is real, de-identified cases labeled by senior nurses before the tool sees them. 0 of 65 only says the true error rate is probably under 5%.", options: { fontSize: 11.5, color: C.ink, fontFace: B } },
  ], { margin: [0.06, 0.2, 0.06, 0.2], lineW: 0.75 });

  node("Point", 0.5, 6.4, 12.33, 0.78, C.green, C.green, [
    { text: "Never a guess. Never a denial.", options: { fontSize: 16, bold: true, color: C.white, fontFace: B, breakLine: true, paraSpaceAfter: 2 } },
    { text: "A missing fact goes to the nurse as 'not sure'. Only a medical director can deny.", options: { fontSize: 11.5, color: "D5EBE3", fontFace: B } },
  ], { align: "center", margin: [0.05, 0.25, 0.05, 0.25] });

  text("footer", 0.5, 7.22, 12.33, 0.22, [{ text: "Source: PA Desk eval scorecard (5 stability runs, 44-service policy search, 24-item human citation audit). Synthetic data.", options: { fontSize: 9, color: C.muted, fontFace: B } }]);
  s.addNotes(NOTES);
  await pres.writeFile({ fileName: OUT });
  console.log("wrote", OUT);
}
main().catch((e) => { console.error(e); process.exit(1); });
