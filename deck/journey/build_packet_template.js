// Builds ONE template slide: the packet workflow across the top, two empty frames below for input and output screenshots.
// Duplicate it once per step, colour the active box, and paste the screenshots from architecture/inner_workings.html.
// Run:  node build_packet_template.js   -> Packet_Decision_Template.pptx
const path = require("path");
const pptxgen = require("pptxgenjs");

const C = { ink: "16211E", muted: "5C6B66", green: "1F6F5C", line: "B9C4C0", frame: "9AA8A3", white: "FFFFFF" };
const H = "Cambria", B = "Calibri";
const m2 = (m) => m.map((v) => v * 72); // top, right, bottom, left (inches) -> points

const STEPS = [
  ["1", "Intake uploads", "One PDF in"],
  ["2", "ETL + AI reads the pages", "Typed pieces with boxes"],
  ["3", "Find the service", "The code picks it"],
  ["4", "Read the details", "AI fills one form"],
  ["5", "Check the evidence", "Quote on its page"],
  ["6", "Apply the rules", "Plain code. No deny"],
];

async function main() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5 in
  pres.title = "How the AI decided the packet";
  pres.author = "Nisha Mishra";
  const s = pres.addSlide();
  s.background = { color: C.white };

  s.addText("HOW THE AI DECIDED THE PACKET", { x: 0.52, y: 0.25, w: 8, h: 0.28, margin: 0, isTextBox: true, fontFace: B, fontSize: 11, bold: true, color: C.green, charSpacing: 3, objectName: "eyebrow" });

  // the workflow: six plain boxes. Colour the one you are explaining.
  const W = 1.95, G = 0.12, X0 = 0.52, Y = 0.65, BH = 0.95;
  STEPS.forEach(([n, title, sub], i) => {
    const x = X0 + i * (W + G);
    s.addText(
      [
        { text: n + "  ", options: { bold: true, fontSize: 13, color: C.green, fontFace: B } },
        { text: title, options: { bold: true, fontSize: 13, color: C.ink, fontFace: B, breakLine: true } },
        { text: sub, options: { fontSize: 10, color: C.muted, fontFace: B } },
      ],
      { shape: pres.ShapeType.roundRect, rectRadius: 0.08, x, y: Y, w: W, h: BH, fill: { color: C.white }, line: { color: C.line, width: 1.25 }, align: "left", valign: "middle", margin: m2([0.06, 0.1, 0.06, 0.14]), objectName: "Step" + n, isTextBox: false }
    );
    if (i) s.addText("›", { x: x - G - 0.0, y: Y + 0.3, w: G, h: 0.35, margin: 0, isTextBox: true, align: "center", valign: "middle", fontFace: B, fontSize: 16, bold: true, color: C.frame, objectName: "Chevron" + n });
  });

  // two empty frames for the screenshots
  const FY = 1.95, FH = 4.95, FW = 6.05;
  [["INPUT", 0.52, "InputFrame"], ["OUTPUT", 0.52 + FW + 0.2, "OutputFrame"]].forEach(([label, x, name]) => {
    s.addShape(pres.ShapeType.roundRect, { x, y: FY, w: FW, h: FH, rectRadius: 0.08, fill: { color: C.white }, line: { color: C.frame, width: 1.25, dashType: "dash" }, objectName: name });
    s.addText(label, { x: x + 0.15, y: FY + 0.1, w: 3, h: 0.28, margin: 0, isTextBox: true, fontFace: B, fontSize: 11, bold: true, color: C.muted, charSpacing: 3, objectName: name + "Label" });
  });

  s.addText("Frames and boxes are plain shapes. Delete the frames when you paste a screenshot.", { x: 0.52, y: 7.08, w: 12.3, h: 0.25, margin: 0, isTextBox: true, fontFace: B, fontSize: 9, color: C.muted, objectName: "footer" });

  s.addNotes([
    "Template. Duplicate this slide once for each of the six steps.",
    "On each copy, colour the box you are explaining, then paste the input screenshot on the left and the output screenshot on the right from architecture/inner_workings.html (steps 2 to 6; step 1 is the uploaded PDF).",
    "Colours used on the other slides: coral for ETL + AI, purple for AI, green for plain code, amber for a person.",
  ].join(String.fromCharCode(10, 10)));

  await pres.writeFile({ fileName: path.join(__dirname, "Packet_Decision_Template.pptx") });
  console.log("wrote Packet_Decision_Template.pptx");
}
main().catch((e) => { console.error(e); process.exit(1); });
