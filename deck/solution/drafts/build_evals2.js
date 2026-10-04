// Slide: the evals, current numbers from docs/eval_scorecard.html. Run: node build_evals2.js
const { Slide, C, B, H } = require("./kit");

const s = new Slide({ file: "Evals_Current", title: "How we know it works", eyebrow: "HOW WE KNOW IT WORKS", heading: "Three checks. Rerun on every change.", sub: "All packets are made up", footer: "Source: PA Desk eval scorecard. 9 packets x 5 runs, a 24-item human citation audit, and 40 packets from a separate author. Synthetic data." });

const card = (name, x, w, num, q, big, line, notes, status) => {
  const r = [
    { text: num + "  " + q, options: { bold: true, fontSize: 12, color: C.green, fontFace: B, breakLine: true, paraSpaceAfter: 8 } },
    { text: big, options: { fontSize: 32, color: C.ink, fontFace: H, breakLine: true } },
    { text: line, options: { bold: true, fontSize: 12.5, color: C.ink, fontFace: B, breakLine: true, paraSpaceAfter: 6 } },
    ...notes.map((n, k) => ({ text: n, options: { fontSize: 11, color: C.muted, fontFace: B, breakLine: k < notes.length - 1, paraSpaceAfter: 3 } })),
  ];
  s.node(name, x, 1.45, w, 3.85, r, { fill: C.white, line: C.line, lineW: 1.25, radius: 0.1, valign: "top", margin: [0.16, 0.2, 0.1, 0.2] });
};
const W = 3.97, G = 0.21, X = (i) => 0.5 + i * (W + G);
card("E1", X(0), W, "1", "Does it read the packet right?", "45 of 45", "recommendations right. 9 packets, 5 runs.", ["53 of 53 details found when they were there.", "0 of 65 absent details claimed as present.", "About 17 seconds a packet."]);
card("E2", X(1), W, "2", "Can a person trust the citation?", "75% yes", "of 24 citations judged by a person. 87.5% yes or partly.", ["5 of 5 planted wrong citations caught.", "Weak spot: a claim with several parts cites one sentence.", "Fix: show the whole supporting passage."]);
card("E3", X(2), W, "3", "Hard packets from another author", "57% to 86%", "of cases needing a person caught, first run to run 4.", ["40 packets, 28 needing a person, 12 hard categories.", "Wrong approvals fell from 12 to 4.", "We tuned on this same set, so a fresh set is the final test."]);

s.node("Limits", 0.5, 5.45, 12.33, 0.78, [{ text: "What this does not show yet  ", options: { bold: true, fontSize: 12, color: C.amber, fontFace: B } }, { text: "Real faxes. These packets are made up and most were written by us. The real test is real, de-identified cases labeled by senior nurses before the tool sees them.", options: { fontSize: 11.5, color: C.ink, fontFace: B } }], { fill: C.amberSoft, line: C.amber, lineW: 0.75, radius: 0.08, margin: [0.06, 0.2, 0.06, 0.2] });
s.node("Point", 0.5, 6.32, 12.33, 0.7, [{ text: "Never a guess. Never a denial.  ", options: { fontSize: 15, bold: true, color: C.white, fontFace: B } }, { text: "A detail it cannot find goes to the nurse as 'not sure'. Only a medical director can deny.", options: { fontSize: 11.5, color: "D5EBE3", fontFace: B } }], { fill: C.green, line: C.green, align: "center", margin: [0.05, 0.25, 0.05, 0.25] });

s.click("How do I know it works? Three checks, and I rerun all three on every change. First, does it read the packet right. Nine packets with known answers: approve, pend, escalate, a conflicting value, a ruled-out condition, a recent heart attack, and a noisy scan. Five runs in a row. Forty-five of forty-five right. Fifty-three of fifty-three details found. None invented.", "E1");
s.click("Second, can a person trust the citation. I judged twenty-four cited sentences myself with the answer key hidden. Three in four were a clear yes, and nearly nine in ten were yes or partly. I also planted wrong pairs and the product caught all five. The weak spot is a claim with several parts that cites only one sentence. The fix is to show the whole passage.", "E2");
s.click("Third, hard packets from a separate author who never saw our code. Forty packets, twenty-eight needing a person. I look at recall first, because a miss is a wrong approval. The first run caught fifty-seven percent. After fixes it caught eighty-six percent, and wrong approvals fell from twelve to four. I tuned on this same set, so these later numbers show what I improved, not a clean accuracy. A fresh set is the final test.", "E3");
s.click("The honest part. These packets are made up and I wrote most of them. This proves the plumbing works. It does not prove accuracy on real faxes. The real test is real, de-identified cases labeled by senior nurses before the tool sees them. And the design means a mistake is a flag, never a denial.", "Limits", "Point");

s.build();
