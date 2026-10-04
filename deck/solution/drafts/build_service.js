// Slide: what a service is, and how it links codes, policies and details. Run: node build_service.js
const { Slide, C, B } = require("./kit");

const s = new Slide({ file: "Service_Link", title: "A service links codes, policies and details", eyebrow: "THE PRODUCT, PART 1 OF 2", heading: "A service is what ties it together.", sub: "Any product or business name we choose", footer: "Example: the implantable defibrillator (ICD) service. Codes come from CMS billing articles, each with its source." });

// the hub
s.node("Hub", 4.55, 3.1, 4.23, 1.45, [
  { text: "SERVICE", options: { bold: true, fontSize: 9, color: C.green, fontFace: B, charSpacing: 2, breakLine: true, paraSpaceAfter: 3 } },
  { text: "ICD for heart failure", options: { bold: true, fontSize: 22, color: C.ink, fontFace: B, breakLine: true, paraSpaceAfter: 4 } },
  { text: "Any name the business uses for a kind of request", options: { fontSize: 11, color: C.muted, fontFace: B } },
], { fill: C.greenSoft, line: C.green, lineW: 2, radius: 0.12, align: "center", margin: [0.1, 0.15, 0.1, 0.15] });

// codes (left)
s.step("Codes", 0.5, 2.75, 3.4, 2.15, "data", "Procedure codes in", "The short code on every request that names the procedure. CPT is five digits, like 33249. HCPCS is a letter and four digits, used for equipment, like E0601. This is how a packet finds its service.", { ts: 15, ss: 11, margin: [0.2, 0.18, 0.08, 0.18] });
s.hline("ACodes", 3.93, 3.83, 0.58);
// policies (right)
s.step("Pols", 9.43, 2.75, 3.4, 2.15, "data", "Policies it checks against", "In order of authority: federal regulation, national policy (NCD), local policy (LCD), the plan's own policy, then commercial criteria. Each brings its rules.", { ts: 15, ss: 11, margin: [0.2, 0.18, 0.08, 0.18] });
s.hline("APols", 8.82, 3.83, 0.58, { left: true });
// details (below)
s.step("Dets", 4.05, 5.2, 5.2, 1.2, "ai", "Details the reader looks for in the packet", "For this service: ejection fraction, how it was measured, recent heart attack, months on medicines. Each is one question the AI answers from the packet.", { ts: 14, ss: 11, margin: [0.2, 0.18, 0.06, 0.18] });
s.vline("ADets", 6.67, 4.58, 0.58);

// lifecycle strip
const LC = [["Planned", "On the rollout list. No packet is sent to it", C.grey, C.line, C.muted], ["Pilot", "Switched on. Nurses check every recommendation", C.amberSoft, C.amber, C.amber], ["Live", "Switched on and tested", C.okSoft, C.ok, C.ok]];
s.text("LCLbl", 0.5, 6.5, 2.0, 0.5, [{ text: "A service moves through", options: { bold: true, fontSize: 11, color: C.ink, fontFace: B } }], { valign: "middle" });
LC.forEach(([t, d, f, l, c], i) => {
  const x = 2.55 + i * 3.45;
  s.node("LC" + i, x, 6.45, 3.15, 0.58, [{ text: t + "  ", options: { bold: true, fontSize: 12, color: c, fontFace: B } }, { text: d, options: { fontSize: 10, color: C.muted, fontFace: B } }], { fill: f, line: l, lineW: 1, radius: 0.08, margin: [0.03, 0.12, 0.03, 0.12] });
  if (i) s.hline("LA" + i, x - 0.3, 6.74, 0.27);
});

// production: how we choose the services
s.node("Gtm", 3.55, 1.48, 6.23, 1.2, [
  { text: "WHICH SERVICES FIRST?", options: { bold: true, fontSize: 9, color: C.coral, fontFace: B, charSpacing: 2, breakLine: true, paraSpaceAfter: 3 } },
  { text: "In production, Humana's own history of prior authorization requests sets the rollout plan: volume, pends and reversals by procedure code. In the prototype, the owner sees the same signal as 'Requests without a policy'.", options: { fontSize: 11, color: C.ink, fontFace: B } },
], { fill: C.coralSoft, line: C.coral, lineW: 1.25, radius: 0.1, valign: "top", margin: [0.1, 0.18, 0.06, 0.18] });
s.vline("AGtm", 6.67, 2.7, 0.36);

s.click("A service is the thing that ties it together. A service is any product or business name we choose for a kind of request. 'ICD for heart failure', 'lumbar fusion', 'CPAP therapy'. It is not a medical standard. It is how the business groups the work.", "Hub");
s.click("First, the procedure codes. Every request carries a code that names the procedure. A CPT code is five digits. A HCPCS code is a letter and four digits, used for equipment and supplies. The code on the request is how a packet finds its service. Each code we store has a source, a CMS billing article.", "Codes", "ACodes");
s.click("Second, the policies. The service lists the policies it is checked against, in order of authority. Federal regulation first, then national and local policies, then the plan's own. Each policy brings its approved rules.", "Pols", "APols");
s.click("Third, the details. The service lists what the packet reader must look for. Each detail is one question. The rules compare the answers with the policy.", "Dets", "ADets");
s.click("In production, which services we onboard first comes from Humana's own history of prior authorization requests. Volume, pend rate and reversals by procedure code give a rollout plan. In the prototype the owner sees the same signal live, as requests without a policy.", "Gtm", "AGtm");
s.click("A service is not switched on at once. It starts as planned, a name and a code on the rollout list. It becomes a pilot when it has a policy, a code and its details, and nurses check every recommendation. It goes live only after a written note on what was tested.", "LCLbl", "LC0", "LC1", "LA1", "LC2", "LA2");

s.build();
