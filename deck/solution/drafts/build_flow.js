// Slide: the product flow, today against with PA Desk. Run: node build_flow.js
const { Slide, C, B } = require("./kit");

const s = new Slide({ file: "Product_Flow", title: "The flow, today and with PA Desk", eyebrow: "IN THE PRODUCT", heading: "With all of that underneath, the flow is simple.", sub: "What each person now does", footer: "The nurse still confirms every recommendation. Only a medical director can deny." });

const W = 2.3, GAP = 0.2, X = (i) => 0.5 + i * (W + GAP);
s.text("TodayLbl", 0.5, 1.45, 4, 0.3, [{ text: "TODAY", options: { bold: true, fontSize: 11, color: C.muted, fontFace: B, charSpacing: 3 } }]);
const TODAY = [["Fax or portal", "The provider sends the packet"], ["Intake checks it in", "Routes it to a nurse"], ["The nurse reads 14 pages", "Hunts across policy, benefits and provider systems"], ["Missing a detail?", "Pend. Back to the provider. The case starts again"], ["Decision", "Approve, or escalate to a medical director"]];
TODAY.forEach(([t, d], i) => {
  s.node("T" + i, X(i), 1.8, W, 1.25, [{ text: t, options: { bold: true, fontSize: 13, color: C.ink, fontFace: B, breakLine: true, paraSpaceAfter: 3 } }, { text: d, options: { fontSize: 10.5, color: C.muted, fontFace: B } }], { fill: C.grey, line: C.line, lineW: 1, radius: 0.1, valign: "top", margin: [0.14, 0.14, 0.06, 0.14] });
  if (i) s.hline("TA" + i, X(i) - GAP + 0.01, 2.42, GAP - 0.02, { color: "9AA5A1" });
});

s.text("NewLbl", 0.5, 3.55, 4, 0.3, [{ text: "WITH PA DESK", options: { bold: true, fontSize: 11, color: C.green, fontFace: B, charSpacing: 3 } }]);
const NEW = [
  ["person", "Intake uploads the PDF", "That is all intake does"],
  ["ai", "The system reads it", "Finds the details, cites each one, checks the policy"],
  ["person", "The nurse sees a checklist", "Evidence beside each item, and a recommendation"],
  ["person", "Approve, ask, or escalate", "A missing detail becomes one precise question"],
  ["person", "A medical director decides", "Only the hard cases. Only they can deny"],
];
NEW.forEach(([k, t, d], i) => {
  s.step("N" + i, X(i), 3.95, W, 1.45, k, t, d, { ts: 13.5, ss: 10.5, margin: [0.26, 0.14, 0.06, 0.14] });
  s.badge("NB" + i, i + 1, X(i) + 0.2, 3.95, C.green);
  if (i) s.hline("NA" + i, X(i) - GAP + 0.01, 4.67, GAP - 0.02);
});
s.node("Bar", 0.5, 5.75, 12.33, 1.15, [
  { text: "What changes", options: { bold: true, fontSize: 11, color: C.green, fontFace: B, charSpacing: 1.5, breakLine: true, paraSpaceAfter: 3 } },
  { text: "The nurse starts from a cited checklist, not a stack of pages. A missing detail is found at once, not after a loop. Hard cases reach a physician early, with the evidence attached.", options: { fontSize: 13, color: C.ink, fontFace: B } },
], { fill: C.okSoft, line: C.ok, lineW: 1, radius: 0.1, valign: "top", margin: [0.12, 0.22, 0.06, 0.22] });

s.click("The top row is how it works today. A packet arrives by fax or portal. Intake checks it in. The nurse reads fourteen pages and hunts across systems. A missing detail goes back to the provider and the case starts again. With the product underneath, intake uploads the PDF. That is all intake does.", "NewLbl", "N0", "NB0");
s.click("The system reads the packet, finds the details the policy cares about, cites each one, and checks them against the library.", "NA1", "N1", "NB1");
s.click("The nurse opens a checklist with the evidence beside every item and a recommendation. The nurse is reviewing, not hunting.", "NA2", "N2", "NB2");
s.click("The nurse approves, asks the provider one precise question, or escalates. A missing detail is found at the start, not after a loop.", "NA3", "N3", "NB3");
s.click("A medical director decides the hard cases, with the evidence already attached. Only a medical director can deny.", "NA4", "N4", "NB4");
s.click("What changes: the nurse starts from a cited checklist, not a stack of pages. A missing detail is found at once. Hard cases reach a physician early.", "Bar");

// the "today" row is visible from the start
s.build();
