// ONE plain slide: why now. Four cards, no animation, no transitions.
// Run:  node build_why_now.js   -> Why_Now.pptx
const path = require("path");
const pptxgen = require("pptxgenjs");

const C = { ink: "16211E", muted: "5C6B66", green: "1F6F5C", coral: "B8452F", amber: "8A5A00", purple: "5F3AA8", white: "FFFFFF" };
const H = "Cambria", B = "Calibri";
const m2 = (m) => m.map((v) => v * 72); // top, right, bottom, left (inches) -> points

async function main() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5 in
  pres.title = "Why now";
  pres.author = "Nisha Mishra";
  const s = pres.addSlide();
  s.background = { color: C.white };

  s.addText("WHY NOW", { x: 0.5, y: 0.3, w: 4, h: 0.28, margin: 0, isTextBox: true, fontFace: B, fontSize: 11, bold: true, color: C.green, charSpacing: 3, objectName: "eyebrow" });
  s.addText("Why now?", { x: 0.5, y: 0.55, w: 6, h: 0.75, margin: 0, isTextBox: true, valign: "middle", fontFace: H, fontSize: 28, color: C.ink, objectName: "title" });
  s.addText("Applies to Medicare Advantage plans, including Humana's.", { x: 6.6, y: 0.55, w: 6.23, h: 0.75, margin: 0, isTextBox: true, align: "right", valign: "middle", fontFace: B, fontSize: 14, color: C.muted, objectName: "sub" });

  // four cards across: the volume, the clock, the rule on pending, the member window
  const CARDS = [
    ["THE VOLUME", C.green, "+20%", "more members since January.", "Roughly 2.3 million more requests a year."],
    ["IN EFFECT SINCE JANUARY 2026", C.coral, "72 hours", "to decide an expedited request.", "Standard: 7 days."],
    ["THE RULE ON PENDING", C.amber, "+14 days", "the most a pend can add.", "A pend does not stop the clock."],
    ["COMING JANUARY 2027", C.purple, "Jan 2027", "the member can see where a request stands.", ""],
  ];
  const GAP = 0.2, W = (12.33 - 3 * GAP) / 4, Y = 1.65, H2 = 3.7;
  CARDS.forEach(([label, color, big, line, sub], i) => {
    const runs = [
      { text: label, options: { bold: true, fontSize: 10.5, color, fontFace: B, charSpacing: 1.5, breakLine: true, paraSpaceAfter: 14 } },
      { text: big, options: { fontSize: 40, color, fontFace: H, breakLine: true, paraSpaceAfter: 8 } },
      { text: line, options: { bold: true, fontSize: 16, color: C.ink, fontFace: B, breakLine: !!sub, paraSpaceAfter: 8 } },
      ...(sub ? [{ text: sub, options: { fontSize: 14, color: C.muted, fontFace: B } }] : []),
    ];
    s.addText(runs, { shape: pres.ShapeType.roundRect, rectRadius: 0.1, x: 0.5 + i * (W + GAP), y: Y, w: W, h: H2, fill: { color: C.white }, line: { color, width: 2 }, align: "left", valign: "top", margin: m2([0.3, 0.22, 0.15, 0.22]), objectName: "Card" + (i + 1), isTextBox: false });
  });

  s.addText(
    [
      { text: "More requests. A harder clock. Public results.  ", options: { bold: true, fontSize: 20, color: C.white, fontFace: B } },
      { text: "That is why this matters now.", options: { fontSize: 16, color: "D5EBE3", fontFace: B } },
    ],
    { shape: pres.ShapeType.roundRect, rectRadius: 0.08, x: 0.5, y: 5.65, w: 12.33, h: 0.95, fill: { color: C.green }, line: { color: C.green, width: 1 }, align: "center", valign: "middle", margin: m2([0.05, 0.25, 0.05, 0.25]), objectName: "Bar", isTextBox: false }
  );

  s.addText("Sources: CMS-0057-F final rule and fact sheet (cms.gov). 42 CFR 422.568(b). Humana member counts from its Q4 2025 financial tables (SEC). KFF, 2024: about 2.2 requests per Humana member a year, on average. The 2.3 million is an estimate.", { x: 0.5, y: 7.05, w: 12.33, h: 0.3, margin: 0, isTextBox: true, fontFace: B, fontSize: 9, color: C.muted, objectName: "footer" });

  s.addNotes([
    "Why now? Three pressures at once.",
    "The volume. About a million members joined Humana in January, roughly 20 percent more, all at once. KFF found Humana averages about 2.2 requests per member a year. That is an average: most members make none, and some make many. If the new members look like the current ones, that is roughly 2.3 million more requests a year, about 190,000 a month. A nurse reads every one.",
    "The clock. Since January 2026, a decision is due in 72 hours for an expedited request and 7 calendar days for a standard one. That means an approval or a denial, not a pend. Every denial needs a specific reason. And plans publish their results every year. The first report was due March 31, 2026.",
    "The rule on pending. A plan can add up to 14 calendar days, but only if it justifies the delay as in the member's interest and tells the member in writing. A pend does not stop the clock.",
    "Coming January 2027, about three months away. Four data interfaces go live. The Patient Access API must show the member where a prior authorization stands.",
    "So: more requests, a harder clock, and public results. That is why this matters now.",
  ].join(String.fromCharCode(10, 10)));

  await pres.writeFile({ fileName: path.join(__dirname, "Why_Now.pptx") });
  console.log("wrote Why_Now.pptx");
}
main().catch((e) => { console.error(e); process.exit(1); });
