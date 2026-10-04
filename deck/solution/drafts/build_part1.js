// Slide: Part 1, building the policy library. Run: node build_part1.js
const { Slide, C, B } = require("./kit");

const s = new Slide({ file: "Part1_Policy_Library", title: "Part 1: building the policy library", eyebrow: "THE PRODUCT, PART 1 OF 2", heading: "First, build the library the nurse checks against.", sub: "Done once per service, and on every policy change", footer: "Policies shown are public Medicare policies. The Humana policy and MCG slots are placeholders." });

s.node("Today", 0.5, 1.45, 12.33, 0.5, [{ text: "Today a nurse looks these up by hand, for every case: ", options: { bold: true, fontSize: 12, color: C.ink, fontFace: B } }, { text: "CMS national and local coverage policies, federal rules, and Humana's own documents.", options: { fontSize: 12, color: C.muted, fontFace: B } }], { fill: C.grey, line: C.line, lineW: 0.75, margin: [0.04, 0.16, 0.04, 0.16] });
s.items[s.items.length - 1].static = true;

const W = 1.9, GAP = 0.186, X = (i) => 0.5 + i * (W + GAP), Y = 2.3, H = 1.7;
const STEPS = [
  ["ext", "Official policy", "CMS national and local policies, federal rules, or a plan's own PDF", "NCD 20.4, LCD L37848, 42 CFR 412.3"],
  ["etl", "Read the policy", "Every page becomes typed pieces: titles, paragraphs, tables, with their pages", "A heading, a paragraph, a table. Page numbers kept"],
  ["ai", "Draft the rules", "AI turns each requirement into a rule and the detail a nurse must check", "\"LVEF 35% or less\" is checked on the detail 'ejection fraction'"],
  ["code", "Check the draft", "Code checks every quote, number and detail against the policy text", "Is the quote in the policy? Is the 35 in the quote?"],
  ["person", "Owner approves", "A policy owner approves, edits or rejects each rule", "Nothing is live until a person approves it"],
  ["data", "Link and publish", "Policy to procedure codes to a service. One versioned library", "Code 33249 leads to the ICD service and its rules"],
];
STEPS.forEach(([kind, title, sub, ex], i) => {
  s.step("S" + i, X(i), Y, W, H, kind, title, sub, { margin: [0.3, 0.14, 0.08, 0.14] });
  s.badge("B" + i, i + 1, X(i) + 0.2, Y, C.green);
  s.chip("E" + i, X(i), Y + H + 0.14, W, 0.72, ex, { italic: true, fs: 10, valign: "top" });
  if (i) s.hline("A" + i, X(i) - GAP + 0.01, Y + H / 2, GAP - 0.02);
});

// what we get
const RY = 5.3;
const GET = [
  "A versioned library of services. Each has its procedure codes, its policies and the details to look for.",
  "Every rule tied to the exact official sentence, and approved by a named owner.",
  "Every procedure code with its source, and every change in an audit trail.",
  "A new service moves from planned to pilot to live. Any version can be rolled back.",
];
s.node("GetBox", 0.5, RY, 12.33, 1.58, [{ text: "WHAT WE GET", options: { bold: true, fontSize: 10, color: C.green, fontFace: B, charSpacing: 2 } }], { fill: C.okSoft, line: C.ok, lineW: 1, valign: "top", margin: [0.1, 0.2, 0.05, 0.2], radius: 0.1 });
GET.forEach((t, i) => s.text("G" + i, 0.72 + (i % 2) * 6.08, RY + 0.4 + Math.floor(i / 2) * 0.55, 5.8, 0.5, [{ text: "✓  ", options: { bold: true, fontSize: 12, color: C.ok, fontFace: B } }, { text: t, options: { fontSize: 11.5, color: C.ink, fontFace: B } }]));

s.click("Today the nurse looks up the policy by hand for every case. We start there: the official policy. CMS publishes national and local coverage determinations. Federal rules sit above them. Humana has its own documents. Each one says what must be true for a service to be covered.", "S0", "B0", "E0");
s.click("We read the policy with an ETL step that has AI inside. It keeps the structure: titles, paragraphs, tables and the page each came from. A flat blob of text would lose the sections the rules hang on.", "A1", "S1", "B1", "E1");
s.click("An AI drafts the rules. Each requirement becomes one rule. For each rule it names the detail a nurse needs to check, and copies the exact sentence the rule came from. Those details are what we later look for in the packet.", "A2", "S2", "B2", "E2");
s.click("Plain code checks the draft. Is the quote really in the policy? Is every number in the quote? Does the detail exist? Anything that fails is shown to the owner, never dropped. No AI in this step.", "A3", "S3", "B3", "E3");
s.click("A policy owner approves, edits or rejects every rule, with the official text beside it. The AI drafts. It never publishes. A rule that needs a detail we cannot read yet waits.", "A4", "S4", "B4", "E4");
s.click("Then we link it. Each policy is tied to procedure codes. A code, a CPT or HCPCS code, is the short code on every request that names the procedure, for example 33249 for an implantable defibrillator. The policy joins a service. A service is any product or business name we choose for a kind of request. The service holds its codes, its policies and the details to look for. In production, historical Humana prior authorization volume decides which services we onboard first. We publish one versioned library.", "A5", "S5", "B5", "E5");
s.click("What we get: a versioned library of services. Every rule is tied to the official sentence and approved by a named person. Every code has a source. A new service goes from planned to pilot to live, and any version can be rolled back.", "GetBox", "G0", "G1", "G2", "G3");

s.build();
