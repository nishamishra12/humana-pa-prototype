// ONE plain slide: what Humana is already doing, as a three-column table. No animation, no transitions.
// Run:  node build_humana_table.js   -> Humana_Moves.pptx
const path = require("path");
const pptxgen = require("pptxgenjs");

const C = { ink: "16211E", muted: "5C6B66", green: "1F6F5C", greenSoft: "DDF3E7", line: "CBD5D1", head: "F3F5F4", white: "FFFFFF" };
const H = "Cambria", B = "Calibri";

async function main() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5 in
  pres.title = "What Humana is already doing";
  pres.author = "Nisha Mishra";
  const s = pres.addSlide();
  s.background = { color: C.white };

  s.addText("WHAT HUMANA IS ALREADY DOING", { x: 0.5, y: 0.3, w: 6, h: 0.28, margin: 0, isTextBox: true, fontFace: B, fontSize: 11, bold: true, color: C.green, charSpacing: 3 });
  s.addText("Humana is already acting. Here is the gap.", { x: 0.5, y: 0.55, w: 9.2, h: 0.75, margin: 0, isTextBox: true, valign: "middle", fontFace: H, fontSize: 26, color: C.ink });
  s.addText("And where my project fits", { x: 9.4, y: 0.55, w: 3.43, h: 0.75, margin: 0, isTextBox: true, align: "right", valign: "middle", fontFace: B, fontSize: 14, color: C.muted });

  const border = { type: "solid", color: C.line, pt: 1 };
  const cell = (text, o = {}) => ({ text, options: { fontFace: B, fontSize: o.fs || 15, bold: !!o.bold, color: o.color || C.ink, fill: { color: o.fill || C.white }, valign: "middle", align: o.align || "left", border: [border, border, border, border], margin: [0.08, 0.16, 0.08, 0.16] } });
  const head = (text) => cell(text, { fs: 11, bold: true, color: C.muted, fill: C.head });

  const rows = [
    [head("HUMANA'S MOVE"), head("LEVER"), head("WHAT IT LEAVES UNTOUCHED")],
    [cell("Cuts about a third of outpatient requirements", { bold: true }), cell("Volume", { bold: true, color: C.green }), cell("Complex and inpatient requests still need a full review", { color: C.muted })],
    [cell("Gold card for proven physicians", { bold: true }), cell("Exemption", { bold: true, color: C.green }), cell("Everyone else is still reviewed", { color: C.muted })],
    [cell("Decides 95% of complete electronic requests in one business day", { bold: true }), cell("Speed target", { bold: true, color: C.green }), cell("Incomplete requests, and faxed or scanned ones", { color: C.muted })],
    [cell("Publishes approvals, denials, appeals, overturns and times", { bold: true }), cell("Transparency", { bold: true, color: C.green }), cell("It reports a wrong decision. It does not prevent one.", { color: C.muted })],
    [cell("My prototype", { bold: true, fs: 16, fill: C.greenSoft }), cell("Faster, right first time", { bold: true, color: C.green, fill: C.greenSoft }), cell("Shortens the review itself, and gets each remaining request right the first time", { bold: true, fill: C.greenSoft })],
  ];
  s.addTable(rows, { x: 0.5, y: 1.6, w: 12.33, colW: [4.9, 2.3, 5.13], rowH: [0.4, 0.82, 0.82, 0.82, 0.82, 0.95], objectName: "HumanaTable" });

  s.addText("Faster means care starts sooner. Right first time means fewer pend loops and fewer overturned denials.", { x: 0.5, y: 6.45, w: 12.33, h: 0.5, margin: 0, isTextBox: true, valign: "middle", fontFace: B, fontSize: 16, color: C.ink });
  s.addText("Source: Humana, 'Humana accelerates efforts to eliminate prior authorization requirements' (policy.humana.com, 2025). 'Complete electronic requests' is Humana's wording. Reading the gap as incomplete and faxed requests is mine.", { x: 0.5, y: 7.1, w: 12.33, h: 0.25, margin: 0, isTextBox: true, fontFace: B, fontSize: 9, color: C.muted });

  s.addNotes([
    "Humana is already acting. Here is what they are doing, and what each move leaves untouched.",
    "Volume. Humana is cutting about a third of its outpatient approval requirements: diagnostic colonoscopies, heart monitoring tests, some CT and MRI scans. Fewer requests. But complex and inpatient requests, like the surgeries I am using, still need a full review.",
    "Exemption. A gold card for physicians with a proven record. They skip the review for certain services. Everyone else is still reviewed.",
    "Speed target. One business day for 95 percent of complete electronic requests. Note the word complete. As I read it, incomplete requests, and faxed or scanned ones, sit outside it.",
    "Transparency. Humana will publish approvals, denials, appeals, overturns and decision times. That makes a wrong decision visible. It does not prevent one.",
    "Volume. Who is reviewed. How fast. How visible. None of them changes the review itself. That is where I fit. My lever is faster, right first time. Faster means care starts sooner. Right first time means fewer pend loops and fewer overturned denials.",
  ].join(String.fromCharCode(10, 10)));

  await pres.writeFile({ fileName: path.join(__dirname, "Humana_Moves.pptx") });
  console.log("wrote Humana_Moves.pptx");
}
main().catch((e) => { console.error(e); process.exit(1); });
