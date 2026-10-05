// Builds ONE animated slide: Part 1 of the product, building the policy library and onboarding a service.
// Same method and look as build_friction.js and build_journey.js: one slide, one click per step, nothing plays by itself.
// Run:  NODE_PATH=<folder with @resvg/resvg-js> node build_onboarding.js   -> Policy_Service_Onboarding.pptx + preview_onboarding.html
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");
const JSZip = require("jszip");
const { Resvg } = require("@resvg/resvg-js"); // draws the SVG art to PNG (npm i @resvg/resvg-js)

const C = { ink: "16211E", muted: "5C6B66", green: "1F6F5C", greenSoft: "E3F0EB", line: "CBD5D1", purple: "5F3AA8", purpleSoft: "EBE2F8", white: "FFFFFF" };
const H = "Cambria", B = "Calibri";
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

// ONE plain slide: the four people you will meet. No animation, no transitions.
// Run:  NODE_PATH=<folder with @resvg/resvg-js> node build_personas.js   -> Personas.pptx
const ART = {
  owner: person({ bg: "E3D9F5", skin: SKIN.b, hair: "2B2B2B", style: "bun", top: "6B4C9A", acc: "clip" }),
  intake: person({ bg: "D8EAE3", skin: SKIN.a, hair: "6B4226", style: "bun", top: "3C6E8F", acc: "clip" }),
  nurse: person({ bg: "CDE8E0", skin: SKIN.c, hair: "2B2B2B", style: "short", top: "2F8F83", acc: "nurse" }),
  md: person({ bg: "E3D9F5", skin: SKIN.d, hair: "4A3B32", style: "short", top: "5F3AA8", coat: true, acc: "doctor" }),
};
const m2 = (m) => m.map((v) => v * 72); // top, right, bottom, left (inches) -> points

const CARDS = [
  { key: "owner", color: C.purple, tag: "PART 1  ·  BEFORE GO-LIVE", title: "Policy owner", what: "Builds the library the AI checks against. Chooses the policies and procedures we cover, and approves every rule.", owns: "What we check against" },
  { key: "intake", color: C.green, tag: "PART 2  ·  EVERY PACKET", title: "Intake coordinator", what: "Receives the packet, checks it in, and assigns it to a nurse. Sees every nurse's workload.", owns: "Who reviews it" },
  { key: "nurse", color: C.green, tag: "PART 2  ·  EVERY PACKET", title: "UM nurse", what: "Reviews the packet with the AI's help. Confirms approve, asks the provider one precise question, or escalates.", owns: "The recommendation" },
  { key: "md", color: C.green, tag: "PART 2  ·  EVERY PACKET", title: "Medical director", what: "Decides the hard cases, with the evidence attached. Writes the reason for every decision.", owns: "Any denial. Only they can deny." },
];

async function main() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5 in
  pres.title = "Four people, two parts";
  pres.author = "Nisha Mishra";
  const s = pres.addSlide();
  s.background = { color: C.white };

  s.addText("THE PEOPLE", { x: 0.5, y: 0.3, w: 4, h: 0.28, margin: 0, isTextBox: true, fontFace: B, fontSize: 11, bold: true, color: C.green, charSpacing: 3, objectName: "eyebrow" });
  s.addText("Four people, two parts.", { x: 0.5, y: 0.55, w: 7.5, h: 0.75, margin: 0, isTextBox: true, valign: "middle", fontFace: H, fontSize: 28, color: C.ink, objectName: "title" });
  s.addText("The people you will meet in the prototype", { x: 7.6, y: 0.55, w: 5.23, h: 0.75, margin: 0, isTextBox: true, align: "right", valign: "middle", fontFace: B, fontSize: 14, color: C.muted, objectName: "sub" });

  const W = 2.8, Y = 1.55, CH = 4.25;
  const X = [0.5, 3.85, 6.85, 9.85];
  const PNG = {};
  for (const [k, svg] of Object.entries(ART)) PNG[k] = Buffer.from(new Resvg(svg, { fitTo: { mode: "width", value: 360 } }).render().asPng()).toString("base64");

  CARDS.forEach((c, i) => {
    s.addText(
      [
        { text: c.tag, options: { bold: true, fontSize: 9.5, color: c.color, fontFace: B, charSpacing: 1.5, breakLine: true, paraSpaceAfter: 85 } },
        { text: c.title, options: { bold: true, fontSize: 19, color: C.ink, fontFace: B, breakLine: true, paraSpaceAfter: 8 } },
        { text: c.what, options: { fontSize: 14, color: C.muted, fontFace: B } },
      ],
      { shape: pres.ShapeType.roundRect, rectRadius: 0.1, x: X[i], y: Y, w: W, h: CH, fill: { color: C.white }, line: { color: c.color, width: 2 }, align: "left", valign: "top", margin: m2([0.2, 0.2, 0.15, 0.2]), objectName: "Card" + (i + 1), isTextBox: false }
    );
    s.addImage({ data: "image/png;base64," + PNG[c.key], x: X[i] + 0.2, y: Y + 0.5, w: 0.95, h: 0.95, objectName: "Avatar" + (i + 1) });
    s.addText(
      [{ text: "OWNS  ", options: { bold: true, fontSize: 9.5, color: c.color, fontFace: B, charSpacing: 1.5 } }, { text: c.owns, options: { bold: true, fontSize: 12.5, color: C.ink, fontFace: B } }],
      { shape: pres.ShapeType.roundRect, rectRadius: 0.06, x: X[i] + 0.15, y: Y + CH - 0.75, w: W - 0.3, h: 0.55, fill: { color: i === 0 ? C.purpleSoft : C.greenSoft }, line: { color: c.color, width: 0.75 }, align: "left", valign: "middle", margin: m2([0.04, 0.12, 0.04, 0.12]), objectName: "Owns" + (i + 1), isTextBox: false }
    );
  });
  // a thin divider between part 1 and part 2
  s.addShape(pres.ShapeType.line, { x: 3.58, y: Y, w: 0, h: CH, line: { color: C.line, width: 1.5, dashType: "dash" }, objectName: "Divider" });

  s.addText(
    [{ text: "One more teammate: the AI.  ", options: { bold: true, fontSize: 15, color: C.green, fontFace: B } }, { text: "It reads, drafts and cites. It never decides.", options: { fontSize: 15, color: C.ink, fontFace: B } }],
    { shape: pres.ShapeType.roundRect, rectRadius: 0.08, x: 0.5, y: 6.1, w: 12.33, h: 0.65, fill: { color: C.white }, line: { color: C.green, width: 1.25 }, align: "center", valign: "middle", margin: m2([0.05, 0.2, 0.05, 0.2]), objectName: "AIBar", isTextBox: false }
  );

  s.addNotes([
    "These are the four people you will meet in the prototype. Each owns one decision.",
    "The policy owner is part one. They work before go-live, and it is the biggest piece of real work. They choose the policies and procedures we cover, and they approve every rule the AI drafts. They own what we check against.",
    "Then part two, every packet. The intake coordinator receives the packet, checks it in and assigns it to a nurse. They can see every nurse's workload. They own who reviews it.",
    "The UM nurse is the star player. They review the packet with the AI's help and confirm approve, ask the provider one precise question, or escalate. They own the recommendation.",
    "The medical director decides the hard cases, with the evidence attached, and writes the reason. They own any denial. Only they can deny.",
    "And one more teammate: the AI. It reads, drafts and cites. It never decides.",
  ].join(String.fromCharCode(10, 10)));

  await pres.writeFile({ fileName: path.join(__dirname, "Personas.pptx") });
  console.log("wrote Personas.pptx");
}
main().catch((e) => { console.error(e); process.exit(1); });
