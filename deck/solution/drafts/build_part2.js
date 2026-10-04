// Slide: Part 2, how a packet moves through the product. Run: node build_part2.js
const { Slide, C, B } = require("./kit");

const s = new Slide({ file: "Part2_Packet_Journey", title: "Part 2: a packet's journey", eyebrow: "THE PRODUCT, PART 2 OF 2", heading: "Then every packet is read with that library.", sub: "The AI reads and cites. Code decides.", footer: "All packets are made up. The reader and the evidence check use an AI model. The rules engine is plain code and cannot deny." });

const W = 1.62, GAP = 0.165, X = (i) => 0.5 + i * (W + GAP), Y = 1.55, H = 1.95;
const STEPS = [
  ["person", "Intake uploads", "One PDF per request, up to 15 MB", "Fax, portal or scan. A packet of 14 pages"],
  ["etl", "Read the pages", "Chooses how to read each page, typed text or scan. Splits it into pieces with their boxes", "Title, paragraph, table. Each keeps its page and box"],
  ["code", "Find the service", "The procedure code on the request picks the service", "E0601 leads to CPAP. 33249 leads to ICD"],
  ["ai", "Read the details", "AI fills one form: the details this service needs. Three reads must agree", "Ejection fraction 28%, from page 3"],
  ["mix", "Check the evidence", "Code finds each quote on its page. A second AI checks it says that", "Is 'LVEF 28%' on page 3? Does it support the claim?"],
  ["code", "Apply the rules", "Plain code compares the details with the approved rules", "Missing: pend. Unsure: verify. Rule not met: escalate. All met: approve"],
  ["person", "A person decides", "The nurse sees a cited checklist and confirms", "A medical director decides the hard cases"],
];
STEPS.forEach(([kind, title, sub, ex], i) => {
  s.step("S" + i, X(i), Y, W, H, kind, title, sub, { ts: 13, ss: 10, margin: [0.3, 0.1, 0.06, 0.1] });
  s.badge("B" + i, i + 1, X(i) + 0.2, Y, C.green);
  s.chip("E" + i, X(i), Y + H + 0.12, W, 0.95, ex, { italic: true, fs: 9.5, valign: "top", margin: [0.06, 0.08, 0.04, 0.08] });
  if (i) s.hline("A" + i, X(i) - GAP + 0.01, Y + H / 2, GAP - 0.02);
});

// no service for this code
const BY = 4.95;
s.vline("ANo", X(2) + W / 2, Y + H + 1.07, 0.38, { dash: "dash", color: C.coral });
s.node("NoSvc", 0.5, BY + 0.0, 4.6, 1.0, [
  { text: "NO SERVICE FOR THIS CODE", options: { bold: true, fontSize: 9, color: C.coral, fontFace: B, charSpacing: 1.5, breakLine: true, paraSpaceAfter: 2 } },
  { text: "Flagged 'No policy yet'. Nothing is guessed. The nurse decides. The owner sees it in Requests without a policy.", options: { fontSize: 10.5, color: C.ink, fontFace: B } },
], { fill: C.coralSoft, line: C.coral, lineW: 1.25, radius: 0.1, valign: "top", margin: [0.08, 0.14, 0.04, 0.14] });

// the three outcomes
s.vline("AOut", X(6) + W / 2, Y + H + 1.07, 0.38, { dash: "dash", color: C.green });
const OUT = [["Approve", "The packet is complete and every rule is met", C.okSoft, C.ok, C.ok], ["Pend", "One precise question to the provider", C.amberSoft, C.amber, C.amber], ["Escalate", "To a medical director, who alone can deny", C.purpleSoft, C.purple, C.purple]];
OUT.forEach(([t, d, f, l, c], i) => s.node("Out" + i, 5.5 + i * 2.45, BY, 2.3, 1.0, [{ text: t, options: { bold: true, fontSize: 13, color: c, fontFace: B, breakLine: true, paraSpaceAfter: 2 } }, { text: d, options: { fontSize: 10, color: C.muted, fontFace: B } }], { fill: f, line: l, lineW: 1.25, radius: 0.1, valign: "top", margin: [0.08, 0.12, 0.04, 0.12] }));

s.node("Bar", 0.5, 6.2, 12.33, 0.7, [{ text: "The AI reads and cites. Code decides. A nurse confirms. Only a medical director can deny.", options: { bold: true, fontSize: 14, color: C.white, fontFace: B } }], { fill: C.green, line: C.green, align: "center", margin: [0.05, 0.2, 0.05, 0.2] });

s.click("The intake coordinator uploads the packet. One PDF, a fax or a scan. Today this is the same step. Nothing about intake changes except what happens next.", "S0", "B0", "E0");
s.click("The pages go through an ETL step with AI inside. It decides how to read each page, as typed text or as a scan, and splits the page into pieces: titles, paragraphs, tables. Each piece keeps its page and where it sits on the page, the bounding box. The output is a list of typed pieces with their positions. That is what everything later works from.", "A1", "S1", "B1", "E1");
s.click("Next we find the service. The procedure code on the request is matched to a service in the library. If no service uses that code, the packet is flagged 'No policy yet' and nothing is guessed. The nurse decides, and the policy owner sees the demand.", "A2", "S2", "B2", "E2", "ANo", "NoSvc");
s.click("An AI reads the packet and fills one form, the details this service needs. It reads three times and the answers must agree. Where it counts dates, our code does the counting. If it cannot tell, it says so. It never guesses.", "A3", "S3", "B3", "E3");
s.click("Then we check the evidence. For every detail, plain code finds the quoted sentence on its page. A second AI call checks the sentence really supports the claim. If not, the detail loses its tick and the nurse sees that.", "A4", "S4", "B4", "E4");
s.click("The rules engine is plain code. It compares the details with the approved rules. A missing detail means pend. An unclear one means verify. A rule that is not met means escalate. Everything met means approve. The same details always give the same answer. There is no deny in its vocabulary.", "A5", "S5", "B5", "E5");
s.click("The nurse sees a checklist with the evidence beside each item and confirms the recommendation. Hard cases go to a medical director. Only a medical director can deny, and writes the reason.", "A6", "S6", "B6", "E6", "AOut", "Out0", "Out1", "Out2");
s.click("The point to land: the AI reads and cites. Code decides. A nurse confirms. A medical director alone can deny.", "Bar");

s.build();
