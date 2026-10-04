// Slide: the product has two parts. Run: node build_overview.js
const { Slide, C, B } = require("./kit");

const s = new Slide({ file: "Two_Parts", title: "The product has two parts", eyebrow: "THE PRODUCT", heading: "The product has two parts.", sub: "Build the library once. Read every packet with it.", footer: "AI is used in both parts. Code decides. A person signs. The AI never denies." });

const lane = (id, y, h, tag, title, sub, chips, kinds) => {
  s.node(id + "Card", 0.5, y, 12.33, h, [{ text: "", options: { fontSize: 8 } }], { fill: C.white, line: C.line, lineW: 1.25, radius: 0.1 });
  s.text(id + "Tag", 0.75, y + 0.3, 2.6, 0.25, [{ text: tag, options: { bold: true, fontSize: 10, color: C.green, fontFace: B, charSpacing: 2 } }]);
  s.text(id + "Title", 0.75, y + 0.58, 2.7, 0.9, [{ text: title, options: { bold: true, fontSize: 18, color: C.ink, fontFace: B } }]);
  s.text(id + "Sub", 0.75, y + 1.35, 2.7, h - 1.5, [{ text: sub, options: { fontSize: 11, color: C.muted, fontFace: B } }]);
  const w = chips.length === 4 ? 1.95 : 1.62, gap = 0.2, x0 = 3.75;
  const names = [id + "Card", id + "Tag", id + "Title", id + "Sub"];
  chips.forEach(([t, d], i) => {
    const x = x0 + i * (w + gap);
    s.step(id + "C" + i, x, y + 0.35, w, h - 0.7, kinds[i], t, d, { ts: 13, ss: 10.5, margin: [0.14, 0.12, 0.06, 0.12] });
    names.push(id + "C" + i);
    if (i) { s.hline(id + "A" + i, x - gap + 0.01, y + h / 2, gap - 0.02); names.push(id + "A" + i); }
  });
  return names;
};

const p1 = lane("P1", 1.45, 2.15, "PART 1", "Build the policy library", "Policy owner. Once per service, and whenever a policy changes.", [
  ["Official policy", "CMS, federal rules, Humana documents"],
  ["Read and draft", "ETL + AI reads it, AI drafts the rules"],
  ["Check and approve", "Code checks, a person approves"],
  ["Link and publish", "Policy to codes to a service, versioned"],
], ["ext", "ai", "person", "data"]);

s.vline("Link", 6.67, 3.62, 0.5);
s.text("LinkLbl", 6.95, 3.68, 5.5, 0.4, [{ text: "Part 2 only ever uses what Part 1 approved", options: { bold: true, fontSize: 12, color: C.green, fontFace: B } }], { valign: "middle" });

const p2 = lane("P2", 4.15, 2.15, "PART 2", "Read every packet", "Intake, nurse and medical director. Every request.", [
  ["Upload", "Intake uploads the PDF"],
  ["Read the pages", "ETL + AI makes typed pieces"],
  ["Find the service", "The procedure code picks it"],
  ["Read and check", "AI reads details, code checks the evidence"],
  ["Recommend", "Rules engine: approve, pend or escalate"],
], ["person", "etl", "code", "ai", "code"]);

s.node("Bar", 0.5, 6.45, 12.33, 0.55, [{ text: "Same AI, two jobs. One prepares knowledge before any case. The other reads cases.", options: { bold: true, fontSize: 13, color: C.white, fontFace: B } }], { fill: C.green, line: C.green, align: "center", margin: [0.04, 0.2, 0.04, 0.2] });

s.click("The product has two parts. Part one builds the policy library. It is done once for each service, and again whenever a policy changes. A policy owner is accountable for it. Part two reads every packet that arrives, using that library.", ...p1);
s.click("The link between them is simple. Part two only ever uses what part one approved. The nurse's rules are never made up at the moment a case arrives.", "Link", "LinkLbl");
s.click("Part two is the daily work. Intake uploads the packet. We read the pages, find the service from the procedure code, read the details the policy cares about, check the evidence, and apply the rules to recommend approve, pend or escalate. Part one is the foundation. Part two is the flow most people picture.", ...p2);
s.click("Same AI, two jobs. One prepares knowledge before any case. The other reads cases. In both, the AI drafts or reads, plain code decides, and a person signs. The AI never denies.", "Bar");

s.build();
