// Builds ONE animated slide: how a prior authorization moves today.
// Run:  node build_journey.js        -> Journey_Animation.pptx + preview.html (static layout check)
// The animation is written straight into the slide XML (pptxgenjs cannot do animations).
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");
const JSZip = require("jszip");
const { Resvg } = require("@resvg/resvg-js"); // draws the SVG art to PNG (npm i @resvg/resvg-js)

const OUT = path.join(__dirname, "Journey_Animation.pptx"); // only with --animated
const OUT_STEPS = path.join(__dirname, "Journey_Steps.pptx"); // default: one slide per step
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

/* ---------- layout spec (inches). Everything lives here so the preview and the slide match ---------- */
const items = []; // {name, kind, x,y,w,h, ...}
const add = (o) => items.push(o);
const runs = (title, desc, tc = C.ink, ts = 13, ds = 10.5, dc = C.muted) => [
  { text: title, options: { bold: true, fontSize: ts, color: tc, fontFace: B, breakLine: !!desc } },
  ...(desc ? [{ text: desc, options: { fontSize: ds, color: dc, fontFace: B } }] : []),
];
const AVM = [0.06, 0.12, 0.06, 1.0]; // text margin that leaves room for an avatar on the left
const node = (name, x, y, w, h, title, desc, o = {}) => add({ name, kind: "node", x, y, w, h, fill: C.white, line: C.line, lineW: 1, runs: runs(title, desc, o.tc, o.ts, o.ds), margin: AVM, ...o });
const avatar = (name, x, y, size) => add({ name, kind: "image", x, y, w: size, h: size });
const tag = (name, x, y, w, h, text, o = {}) => add({ name, kind: "node", x, y, w, h, fill: C.coralSoft, line: C.coral, lineW: 1, runs: [{ text, options: { fontSize: 11, bold: true, color: C.coral, fontFace: B } }], margin: [0.05, 0.12, 0.05, 0.12], ...o });
// a packet badge that straddles the bottom or top edge of a node, so it never crowds the text
const pkt = (name, x, y) => add({ name, kind: "node", x, y, w: 0.95, h: 0.36, fill: C.white, line: C.coral, lineW: 1.5, radius: 0.06, align: "center", margin: [0, 0, 0, 0], runs: [{ text: "14 pages", options: { bold: true, fontSize: 10, color: C.coral, fontFace: B } }] });
const ring = (name, x, y, w, h, color) => add({ name, kind: "ring", x: x - 0.06, y: y - 0.06, w: w + 0.12, h: h + 0.12, line: color, lineW: 3 });
const caption = (name, text) => add({ name, kind: "text", x: 0.5, y: 6.5, w: 12.33, h: 0.65, valign: "middle", runs: [{ text, options: { fontSize: 16, color: C.ink, fontFace: B } }] });
const label = (name, text, color) => add({ name, kind: "text", x: 7.3, y: 0.5, w: 5.53, h: 0.6, align: "right", valign: "middle", runs: [{ text, options: { bold: true, fontSize: 14, color, fontFace: B, charSpacing: 1 } }] });
const line = (name, x, y, w, h, o = {}) => add({ name, kind: "line", x, y, w, h, line: C.muted, lineW: 2, arrow: true, ...o });

// static frame
add({ name: "eyebrow", kind: "text", static: true, x: 0.5, y: 0.3, w: 4, h: 0.28, runs: [{ text: "CURRENT STATE", options: { bold: true, fontSize: 11, color: C.green, fontFace: B, charSpacing: 3 } }] });
add({ name: "title", kind: "text", static: true, x: 0.5, y: 0.55, w: 7.2, h: 0.75, valign: "middle", runs: [{ text: "How a prior authorization moves today.", options: { fontSize: 26, color: C.ink, fontFace: H } }] });
add({ name: "panelProv", kind: "node", static: true, x: 0.5, y: 1.45, w: 4.45, h: 4.85, fill: C.provPanel, line: C.line, lineW: 1, radius: 0.1, runs: [{ text: " ", options: { fontSize: 8 } }] });
add({ name: "panelPay", kind: "node", static: true, x: 5.55, y: 1.45, w: 7.28, h: 4.85, fill: C.payPanel, line: C.line, lineW: 1, radius: 0.1, runs: [{ text: " ", options: { fontSize: 8 } }] });
add({ name: "hdrProv", kind: "text", static: true, x: 0.85, y: 1.52, w: 3.9, h: 0.55, runs: [{ text: "PROVIDER", options: { bold: true, fontSize: 11, color: C.ink, fontFace: B, charSpacing: 3, breakLine: true } }, { text: "Hospital or physician office", options: { fontSize: 10, color: C.muted, fontFace: B } }] });
add({ name: "hdrPay", kind: "text", static: true, x: 5.8, y: 1.52, w: 6.5, h: 0.55, runs: [{ text: "PAYER", options: { bold: true, fontSize: 11, color: C.ink, fontFace: B, charSpacing: 3, breakLine: true } }, { text: "The health plan: Utilization Management (UM)", options: { fontSize: 10, color: C.muted, fontFace: B } }] });
add({ name: "footer", kind: "text", static: true, x: 0.5, y: 7.1, w: 12.33, h: 0.25, runs: [{ text: "An elective inpatient lumbar spinal fusion request, as it works today.", options: { fontSize: 9, color: C.muted, fontFace: B } }] });

// provider side (nodes start at x 0.85 so the resend loop has room on the left)
node("L1", 0.85, 2.2, 3.85, 0.95, "Surgeon's office", "Staff assemble the packet.");
avatar("AvL1", 0.97, 2.32, 0.71);
pkt("P1", 3.55, 2.97); pkt("P1b", 3.55, 2.97);
node("Member", 0.85, 3.45, 3.85, 0.95, "The member: John Doe, 71", "Waiting on the surgery. Sees none of this.");
avatar("AvM", 0.97, 3.57, 0.71);
node("L3", 0.85, 4.75, 3.85, 0.7, "Provider decodes the pend", "Works out what is missing.", { ts: 12, ds: 10, margin: [0.04, 0.12, 0.04, 0.85] });
avatar("AvL3", 0.95, 4.83, 0.54);
pkt("PL3", 3.55, 5.27);
tag("T3", 0.85, 5.68, 3.85, 0.55, "A pend does not stop the clock.");

// payer side
node("Intake", 5.8, 2.2, 3.5, 0.95, "Intake", "Checks member, form, and codes. Not a clinical check.");
avatar("AvIntake", 5.92, 2.32, 0.71);
pkt("P2", 8.3, 2.97); pkt("P2b", 8.3, 2.97);
tag("T1", 9.5, 2.2, 3.1, 0.95, "Nobody has read the clinical pages yet.");
tag("T5", 9.5, 2.2, 3.1, 0.95, "Back to the start of the line. Maybe a different nurse.");
node("Nurse", 5.8, 3.45, 3.5, 0.95, "UM nurse", "Reads all 14 pages and checks them against policy.");
avatar("AvNurse", 5.92, 3.57, 0.71);
pkt("P3", 8.3, 3.27);
add({ name: "T2", kind: "text", x: 9.5, y: 3.4, w: 3.1, h: 0.28, runs: [{ text: "4 facts hidden in 14 pages", options: { bold: true, fontSize: 11, color: C.coral, fontFace: B } }] });
const chip = (n, x, y, t) => add({ name: n, kind: "node", x, y, w: 1.5, h: 0.3, fill: C.white, line: C.green, lineW: 1, radius: 0.06, align: "center", margin: [0, 0.04, 0, 0.04], runs: [{ text: t, options: { fontSize: 10, color: C.ink, fontFace: B } }] });
chip("Chip1", 9.5, 3.72, "Expected stay"); chip("Chip2", 11.1, 3.72, "Risk factors");
chip("Chip3", 9.5, 4.06, "Imaging"); chip("Chip4", 11.1, 4.06, "Conservative care");

// outcomes
add({ name: "OutPend", kind: "node", x: 5.8, y: 4.75, w: 2.1, h: 0.7, fill: C.amberSoft, line: C.amber, lineW: 1, runs: runs("Pend", "Asks the provider", C.amber, 13, 10, C.amber), margin: [0.04, 0.12, 0.04, 0.14] });
add({ name: "OutApprove", kind: "node", x: 8.0, y: 4.75, w: 2.1, h: 0.7, fill: C.okSoft, line: C.ok, lineW: 1, runs: runs("Approve", "Packet is complete", C.ok, 13, 10, C.ok), margin: [0.04, 0.12, 0.04, 0.14] });
add({ name: "OutEsc", kind: "node", x: 10.25, y: 4.75, w: 2.3, h: 0.7, fill: C.purpleSoft, line: C.purple, lineW: 1, runs: runs("Escalate", "Needs a physician", C.purple, 13, 10, C.purple), margin: [0.04, 0.12, 0.04, 0.14] });
ring("RingPend", 5.8, 4.75, 2.1, 0.7, C.amber);
ring("RingApprove", 8.0, 4.75, 2.1, 0.7, C.ok);
ring("RingEsc", 10.25, 4.75, 2.3, 0.7, C.purple);
node("MD", 9.1, 5.62, 3.6, 0.62, "Medical director", "Decides. Only role that can deny.", { fill: C.purpleSoft, line: C.purple, ts: 12, ds: 10, tc: C.purple, margin: [0.03, 0.1, 0.03, 0.8] });
avatar("AvMD", 9.18, 5.67, 0.52);
tag("T4", 5.8, 5.62, 3.1, 0.62, "A denial can be appealed, and many are overturned.");

// arrows
line("ArrFax", 4.7, 2.675, 1.1, 0, { color: C.coral, dash: "dash" });
avatar("IcFax", 4.98, 2.08, 0.54);
add({ name: "LblFax", kind: "text", x: 4.72, y: 2.72, w: 1.06, h: 0.25, align: "center", runs: [{ text: "FAX", options: { bold: true, fontSize: 11, color: C.coral, fontFace: B, charSpacing: 3 } }] });
line("ArrIn", 7.55, 3.15, 0, 0.3);
line("ForkStub", 7.55, 4.4, 0, 0.15, { arrow: false });
line("ForkBar", 6.85, 4.55, 4.55, 0, { arrow: false });
line("DropPend", 6.85, 4.55, 0, 0.2);
line("DropApprove", 9.05, 4.55, 0, 0.2);
line("DropEsc", 11.4, 4.55, 0, 0.2);
line("ArrPend", 4.7, 5.1, 1.1, 0, { flipH: true, color: C.amber });
line("ArrMD", 11.4, 5.45, 0, 0.17, { color: C.purple });
// the resend loop: out of the provider's pend box, up the left edge, back into the surgeon's office
line("ResA", 0.66, 5.1, 0.19, 0, { color: C.coral, arrow: false });
line("ResB", 0.66, 2.675, 0, 2.425, { color: C.coral, arrow: false });
line("ResC", 0.66, 2.675, 0.19, 0, { color: C.coral });

// labels + captions
label("LabelA", "PATH 1  ·  A COMPLETE PACKET", C.ok);
label("LabelB", "PATH 2  ·  SOMETHING IS MISSING", C.amber);
label("LabelC", "PATH 3  ·  NEEDS A PHYSICIAN", C.purple);
const CAPS = {
  c1: "A surgeon decides a patient needs a lumbar fusion. The office assembles a packet of clinical documents.",
  c2: "The packet is faxed to the plan. Fourteen pages.",
  c3: "Intake checks the member, the form, and the codes. That is a paperwork check, not a clinical one.",
  c4: "A UM nurse picks it up and reads all fourteen pages.",
  c5: "She hunts for four facts and checks each one against policy.",
  c6: "Then there are three ways out.",
  c7: "Path 1. Every fact is there and every criterion is met. She approves.",
  c8: "Path 2. A fact is missing. She pends the case and sends it back to the provider.",
  c9: "The provider has to work out what is missing.",
  c9b: "They find it and resend the packet. It goes through the fax all over again.",
  c9c: "Back at intake, the case starts from zero. The clock never stopped.",
  c10: "Path 3. The facts are there but the case is borderline. It goes to a medical director.",
  c11: "Only the medical director can deny. A denial can be appealed, and many are overturned.",
  c12: "Every step is somebody doing their job correctly. The delay is built into the process.",
};
Object.entries(CAPS).forEach(([k, v]) => caption(k, v));

/* ---------- timeline: slots play one after another. hold = pause (seconds) before the slot starts ---------- */
const FI = (name, delay = 0, dur = 500) => ({ t: "fadeIn", name, delay, dur });
const FO = (name, delay = 0, dur = 300) => ({ t: "fadeOut", name, delay, dur });
const WI = (name, dir, delay = 0, dur = 600) => ({ t: "wipeIn", name, dir, delay, dur });
const slots = [
  { hold: 0, fx: [FI("L1"), FI("AvL1", 0), FI("Member", 200), FI("AvM", 200), FI("P1", 600), FI("c1", 300)] },
  { hold: 3.5, fx: [FO("c1"), FI("IcFax", 300), WI("ArrFax", "left", 300), FI("LblFax", 300), FO("P1", 900), FI("c2", 500)] },
  { hold: 2.2, fx: [FO("c2"), FI("Intake", 300), FI("AvIntake", 300), FI("P2", 700), FI("c3", 300), FI("T1", 1500)] },
  { hold: 4, fx: [FO("c3"), WI("ArrIn", "down", 300), FO("P2", 300), FI("Nurse", 700), FI("AvNurse", 700), FI("P3", 1000), FI("c4", 300)] },
  { hold: 2.8, fx: [FO("c4"), FI("T2", 300), FI("Chip1", 600), FI("Chip2", 900), FI("Chip3", 1200), FI("Chip4", 1500), FI("c5", 300)] },
  { hold: 3.5, fx: [FO("c5"), WI("ForkStub", "down", 300, 250), WI("ForkBar", "left", 550, 500), WI("DropPend", "down", 1050, 250), WI("DropApprove", "down", 1050, 250), WI("DropEsc", "down", 1050, 250), FI("OutPend", 1300), FI("OutApprove", 1300), FI("OutEsc", 1300), FI("c6", 300)] },
  { hold: 2.2, fx: [FO("c6"), FI("LabelA", 300), FI("RingApprove", 300), FI("c7", 300)] },
  { hold: 3.8, fx: [FO("c7"), FO("LabelA"), FO("RingApprove"), FI("LabelB", 400), FI("RingPend", 400), FO("P3", 400), FI("c8", 400)] },
  { hold: 3.0, fx: [FO("c8"), WI("ArrPend", "right", 300), FI("L3", 800), FI("AvL3", 800), FI("PL3", 1000), FI("T3", 1500), FI("c9", 300)] },
  // the loop: pend box -> up the left edge -> back into the surgeon's office, then through the fax again
  { hold: 2.5, fx: [FO("c9"), WI("ResA", "right", 300, 250), WI("ResB", "up", 550, 700), WI("ResC", "left", 1250, 250), FI("P1b", 1500), FO("PL3", 1500), FI("c9b", 300)] },
  { hold: 3.2, fx: [FO("c9b"), FO("P1b"), FO("T1"), FI("P2b", 500), FI("T5", 700), FI("c9c", 400)] },
  { hold: 4.0, fx: [FO("c9c"), FO("LabelB"), FO("RingPend"), FO("ArrPend"), FO("L3"), FO("AvL3"), FO("T3"), FO("ResA"), FO("ResB"), FO("ResC"), FO("P2b"), FO("T5"), FI("LabelC", 500), FI("RingEsc", 500), FI("c10", 500)] },
  { hold: 3.2, fx: [FO("c10"), WI("ArrMD", "down", 300, 400), FI("MD", 700), FI("AvMD", 700), FI("T4", 1500), FI("c11", 300)] },
  { hold: 4.5, fx: [FO("c11"), FO("LabelC"), FO("RingEsc"), FI("c12", 400)] },
];

/* ---------- build the slide ---------- */
const ANIMATED = process.argv.includes("--animated");
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
  pres.title = "How a prior authorization moves today";
  pres.author = "Nisha Mishra";
  const PNG = {};
  for (const [k, svg] of Object.entries(ART)) PNG[k] = Buffer.from(new Resvg(svg, { fitTo: { mode: "width", value: 360 } }).render().asPng()).toString("base64");

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
  s.addNotes(NOTES);
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
  console.log("wrote", OUT, "| animation length about", Math.round(total), "seconds");
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
  const outerId = id();
  let t = 0, slotsXml = "";
  slots.forEach((sl, i) => {
    const fx = sl.fx.map((e) => ({ ...e, delay: e.delay + (i > 0 ? Math.round(sl.hold * 1000) : 0) }));
    const slotId = id();
    const inner = fx.map((e, k) => effect(e, i === 0 && k === 0 ? "clickEffect" : k === 0 ? "afterEffect" : "withEffect")).join("");
    slotsXml += `<p:par><p:cTn id="${slotId}" fill="hold"><p:stCondLst><p:cond delay="${t}"/></p:stCondLst><p:childTnLst>${inner}</p:childTnLst></p:cTn></p:par>`;
    t += Math.max(...fx.map((e) => e.delay + e.dur));
  });
  const bld = [...new Set(slots.flatMap((sl) => sl.fx.map((e) => e.name)))].filter((nm) => !["line", "image"].includes(byName[nm].kind))
    .map((nm) => { const o = byName[nm]; const bg = o.kind === "ring" || (o.kind === "node" && o.fill); return `<p:bldP spid="${ids[nm]}" grpId="0"${bg ? ' animBg="1"' : ""}/>`; }).join("");
  const rootId = 1, seqId = 2;
  return `<p:timing><p:tnLst><p:par><p:cTn id="${rootId}" dur="indefinite" restart="never" nodeType="tmRoot"><p:childTnLst><p:seq concurrent="1" nextAc="seek"><p:cTn id="${seqId}" dur="indefinite" nodeType="mainSeq"><p:childTnLst><p:par><p:cTn id="${outerId}" fill="hold"><p:stCondLst><p:cond delay="indefinite"/></p:stCondLst><p:childTnLst>${slotsXml}</p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn><p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst><p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst></p:seq></p:childTnLst></p:cTn></p:par></p:tnLst><p:bldLst>${bld}</p:bldLst></p:timing>`;
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


const STEP_NOTES = [
  "A surgeon decides the patient needs a lumbar spinal fusion. The office assembles a packet of clinical documents: notes, imaging, history. Meet John Doe, 71. He is waiting and sees none of this.",
  "They fax the packet to the plan. Fourteen pages. Fax is still how most of this moves.",
  "On the plan side, intake checks the member, the form, and the codes. That is a paperwork check. Nobody has read the clinical pages yet.",
  "Intake assigns the packet to a UM nurse. She picks it up.",
  "She reads all fourteen pages. She is hunting for four facts: the expected stay, the risk factors, the imaging evidence, and the conservative treatment. Then she checks each one against policy.",
  "When she finishes, there are three ways out: approve, pend, or escalate.",
  "Path one. Every fact is there and every criterion is met. She approves. This is the good case.",
  "Path two. A fact is missing. She pends the case and it goes back to the provider.",
  "The provider has to work out what is missing. Nobody tells them in plain terms. A pend does not stop the CMS clock.",
  "They find it and resend. The packet goes through the fax all over again.",
  "Back at intake, the case starts from zero. Maybe a different nurse reads it. The clock never stopped.",
  "Path three. The facts are there, but the case is borderline. It goes to a medical director.",
  "Only the medical director can deny. A denial can be appealed, and many are overturned. That is the cost of getting it wrong the first time.",
  "Close on this: every step is somebody doing their job correctly. The delay is built into the process.",
];

const NOTES = `Walk this left to right and let it play. One click starts it.

Start with the provider. A surgeon decides the patient needs a lumbar fusion, and the office assembles a packet. Fourteen pages of clinical documents. They fax it to the plan.

On the plan side, intake checks the member, the form, and the codes. That is a paperwork check. Nobody has read the clinical pages yet.

A UM nurse picks it up. She reads all fourteen pages, hunting for four facts, and checks each one against policy.

Then there are three ways out.

Path one: everything is there, and she approves.

Path two: a fact is missing. She pends the case and it goes back to the provider. They have to work out what is missing, find it, and resend. The packet goes through the fax all over again, and the case starts again from zero. A pend does not stop the clock.

Path three: the facts are there but the case is borderline. It goes to a medical director, the only role that can deny. A denial can be appealed, and many are overturned.

Close on this: every step is somebody doing their job correctly. The delay is built into the process.`;

main().catch((e) => { console.error(e); process.exit(1); });
