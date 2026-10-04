// Slide: what the prototype shows, and how it stays observable. Run: node build_walkthrough.js
const { Slide, C, B } = require("./kit");

const s = new Slide({ file: "Prototype_Walkthrough", title: "Walking through the prototype", eyebrow: "THE PROTOTYPE", heading: "Five things you are about to see.", sub: "Each persona, and how we watch it run", footer: "Prototype data is made up. The shared dashboard link is a snapshot. The live operations page refreshes every few seconds." });

const tile = (name, x, y, w, h, kind, tag, title, lines) => {
  const k = { person: [C.amberSoft, C.amber, C.amber], data: [C.greenSoft, C.green, C.green], ai: [C.purpleSoft, C.purple, C.purple] }[kind];
  const r = [{ text: tag, options: { bold: true, fontSize: 9, color: k[2], fontFace: B, charSpacing: 1.5, breakLine: true, paraSpaceAfter: 3 } }, { text: title, options: { bold: true, fontSize: 16, color: C.ink, fontFace: B, breakLine: true, paraSpaceAfter: 6 } }];
  lines.forEach((l, i) => r.push({ text: "•  " + l, options: { fontSize: 11, color: C.muted, fontFace: B, breakLine: i < lines.length - 1, paraSpaceAfter: 3 } }));
  s.node(name, x, y, w, h, r, { fill: k[0], line: k[1], lineW: 1.25, radius: 0.1, valign: "top", margin: [0.18, 0.2, 0.08, 0.2] });
  s.badge(name + "n", name.slice(-1), x + 0.22, y, C.green);
};
const W = 3.97, G = 0.21;
tile("T1", 0.5, 1.5, W, 2.5, "person", "INTAKE AND NURSE", "Upload, read, decide", ["Intake uploads a packet", "The nurse sees every detail with its page and sentence", "Approve, ask the provider one question, or escalate"]);
tile("T2", 0.5 + W + G, 1.5, W, 2.5, "person", "POLICY OWNER", "Keep the library right", ["Requests without a policy shows what to onboard", "Add a service, draft and review a policy, publish", "Planned, pilot, live. Every step in an audit trail"]);
tile("T3", 0.5 + 2 * (W + G), 1.5, W, 2.5, "person", "MEDICAL DIRECTOR", "Only the hard cases", ["Escalated cases arrive with the evidence attached", "The only role that can deny", "A denial needs a written reason"]);
tile("T4", 0.5, 4.25, 6.06, 2.6, "data", "HONEYCOMB", "Every packet is a trace", ["Each step is timed: reading, details, evidence, rules", "One board shows the numbers that matter", "Traces arrive as cases move, so a slow or failing step shows at once"]);
tile("T5", 0.5 + 6.06 + G, 4.25, 6.06, 2.6, "data", "OPERATIONS DASHBOARD", "How it stays live", ["The live page refreshes every few seconds as cases move", "It reads the same events, so Honeycomb and the dashboard agree", "The shared link is a snapshot for reading afterwards"]);

s.click("This is what I will show. First, the intake coordinator and the nurse. Intake uploads a packet. The nurse sees every detail with its page and the exact sentence it came from, and a recommendation the nurse can confirm, pend with one question, or escalate.", "T1", "T1n");
s.click("Second, the policy owner. This is the part that keeps the whole product honest. Requests without a policy shows what to onboard next. The owner adds a service, drafts and reviews a policy, and publishes. A service starts as planned, then pilot, then live. Every step is in an audit trail.", "T2", "T2n");
s.click("Third, the medical director. Only the hard cases reach them, with the evidence already attached. They are the only role that can deny, and a denial needs a written reason.", "T3", "T3n");
s.click("Now how we watch it. Every packet is a trace in Honeycomb. Each step is timed: reading the pages, the details, the evidence, the rules. If a step slows down or fails, it shows at once. One board holds the numbers that matter.", "T4", "T4n");
s.click("And the operations dashboard. The live page refreshes every few seconds as cases move through the product. It reads the same events as Honeycomb, so the two agree. The link I shared is a snapshot for reading afterwards. I will move a case in the prototype and you can watch the numbers change.", "T5", "T5n");

s.build();
