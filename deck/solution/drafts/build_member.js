// Slide: what we chose not to build, the member's view. Run: node build_member.js
const { Slide, C, B, H } = require("./kit");

const s = new Slide({ file: "Not_Built_Member_Status", title: "What we did not build", eyebrow: "A CHOICE WE MADE", heading: "We did not build the member's view. Here is why.", sub: "Phase 2, with reasons", footer: "Sources: CMS-0057-F fact sheet (cms.gov), Patient Access API requirement from January 1, 2027. The brief's sixth friction point is the member waiting in the dark." });

s.node("Left", 0.5, 1.5, 4.2, 4.1, [
  { text: "THE SIXTH FRICTION", options: { bold: true, fontSize: 9, color: C.purple, fontFace: B, charSpacing: 1.5, breakLine: true, paraSpaceAfter: 6 } },
  { text: "The member waits with no view of where the request stands.", options: { fontSize: 22, color: C.ink, fontFace: H, breakLine: true, paraSpaceAfter: 10 } },
  { text: "A real problem. We chose not to build it first.", options: { bold: true, fontSize: 13, color: C.purple, fontFace: B } },
], { fill: C.purpleSoft, line: C.purple, lineW: 1.5, radius: 0.12, valign: "top", margin: [0.25, 0.28, 0.1, 0.28] });

const R = [
  ["1", "A status is only as good as the record behind it", "If we show a member a status, it must be right. So we build the trusted decision record first."],
  ["2", "It touches a regulated interface", "Member messages and a status screen need their own compliance and security review. That is its own project."],
  ["3", "Waiting costs nothing", "The record built now is exactly what the member view will read. Phase 1 is the foundation, not a detour."],
];
R.forEach(([n, t, d], i) => {
  const y = 1.5 + i * 1.4;
  s.node("R" + n, 5.0, y, 7.83, 1.25, [{ text: t, options: { bold: true, fontSize: 15, color: C.ink, fontFace: B, breakLine: true, paraSpaceAfter: 4 } }, { text: d, options: { fontSize: 11.5, color: C.muted, fontFace: B } }], { fill: C.white, line: C.line, lineW: 1.25, radius: 0.1, valign: "top", margin: [0.16, 0.2, 0.06, 0.7] });
  s.badge("Rn" + n, n, 5.33, y + 0.35, C.purple);
});

s.node("Jan", 0.5, 5.85, 12.33, 1.05, [
  { text: "What makes the timing right  ", options: { bold: true, fontSize: 12, color: C.green, fontFace: B } },
  { text: "From January 1, 2027, plans must offer a Patient Access API that includes prior authorization information. That is about three months away. The decision record we build now is what feeds it.", options: { fontSize: 12, color: C.ink, fontFace: B } },
], { fill: C.okSoft, line: C.ok, lineW: 1, radius: 0.1, margin: [0.08, 0.22, 0.08, 0.22] });

s.click("One thing we deliberately did not build is the member's view. The brief's sixth friction is the member waiting in the dark. It is real. We chose not to build it first, and every phase should have a reason I can say out loud.", "Left");
s.click("Reason one. A status is only as good as the record behind it. If we show a member a status it must be right, so we build the trusted decision record first.", "R1", "Rn1");
s.click("Reason two. It touches a regulated interface. Member messages and a status screen need their own compliance and security review. That is its own project.", "R2", "Rn2");
s.click("Reason three. Waiting costs nothing. The record built in phase one is exactly what the member view will read. Phase one is the foundation, not a detour.", "R3", "Rn3");
s.click("And the timing works. From January 2027 plans must offer a Patient Access API that includes prior authorization information, about three months away. The decision record we build now is what feeds it.", "Jan");

s.build();
