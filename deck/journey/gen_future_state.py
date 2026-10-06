"""Phase 1 future state: the SAME slide as build_journey.js (how a prior authorization moves today), with the AI added where it is.
It reads build_journey.js, swaps in the future-state content, and writes build_future.js, then runs it.
Run from deck/journey with NODE_PATH pointing at a folder that has @resvg/resvg-js, pptxgenjs and jszip:   python gen_future_state.py
Output: Future_State_Click_Through.pptx and preview_future.html
Purple = what changes. White = what stays the same. The policy library is not shown: it is a prerequisite, not part of the flow.
"""
import os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "build_journey.js"), encoding="utf-8").read()


def between(s, a, b):
    i = s.index(a)
    j = s.index(b, i)
    return i, j


# --- outputs
src = src.replace('"Journey_Click_Through.pptx"', '"Future_State_Click_Through.pptx"').replace('"Journey_Steps.pptx"', '"Future_State_Steps.pptx"')
src = src.replace('"preview.html"', '"preview_future.html"').replace("How a prior authorization moves today", "How it moves with Phase 1")
src = src.replace("// Builds ONE animated slide: how a prior authorization moves today.", "// Builds ONE animated slide: the Phase 1 future state, same layout as the current state.")

# --- the AI avatar
src = src.replace("  IcFax: faxIcon,", '  AvAI: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="48" fill="#EBE2F8"/><path d="M50 20 L57 43 L80 50 L57 57 L50 80 L43 57 L20 50 L43 43Z" fill="#5F3AA8"/><circle cx="74" cy="26" r="5" fill="#5F3AA8"/></svg>`,\n  IcFax: faxIcon,')

# --- the frame and every item
FRAME = r'''// static frame
add({ name: "eyebrow", kind: "text", static: true, x: 0.5, y: 0.3, w: 5, h: 0.28, runs: [{ text: "FUTURE STATE  ·  PHASE 1", options: { bold: true, fontSize: 11, color: C.purple, fontFace: B, charSpacing: 3 } }] });
add({ name: "title", kind: "text", static: true, x: 0.5, y: 0.55, w: 7.2, h: 0.75, valign: "middle", runs: [{ text: "How it moves with Phase 1.", options: { fontSize: 26, color: C.ink, fontFace: H } }] });
add({ name: "panelProv", kind: "node", static: true, x: 0.5, y: 1.45, w: 4.45, h: 4.85, fill: C.provPanel, line: C.line, lineW: 1, radius: 0.1, runs: [{ text: " ", options: { fontSize: 8 } }] });
add({ name: "panelPay", kind: "node", static: true, x: 5.55, y: 1.45, w: 7.28, h: 4.85, fill: C.payPanel, line: C.line, lineW: 1, radius: 0.1, runs: [{ text: " ", options: { fontSize: 8 } }] });
add({ name: "hdrProv", kind: "text", static: true, x: 0.85, y: 1.52, w: 3.9, h: 0.55, runs: [{ text: "PROVIDER", options: { bold: true, fontSize: 11, color: C.ink, fontFace: B, charSpacing: 3, breakLine: true } }, { text: "Hospital or physician office", options: { fontSize: 10, color: C.muted, fontFace: B } }] });
add({ name: "hdrPay", kind: "text", static: true, x: 5.8, y: 1.52, w: 6.5, h: 0.55, runs: [{ text: "PAYER", options: { bold: true, fontSize: 11, color: C.ink, fontFace: B, charSpacing: 3, breakLine: true } }, { text: "The health plan: Utilization Management (UM)", options: { fontSize: 10, color: C.muted, fontFace: B } }] });
add({ name: "footer", kind: "text", static: true, x: 0.5, y: 7.1, w: 12.33, h: 0.25, runs: [{ text: "The same elective inpatient lumbar spinal fusion request, with the AI in the flow. Purple is what changes. A person decides every case.", options: { fontSize: 9, color: C.muted, fontFace: B } }] });
const tagAI = (name, x, y, w, h, text, o = {}) => add({ name, kind: "node", x, y, w, h, fill: C.purpleSoft, line: C.purple, lineW: 1, runs: [{ text, options: { fontSize: 11, bold: true, color: C.purple, fontFace: B } }], margin: [0.05, 0.12, 0.05, 0.12], ...o });

// provider side. The start is the same as today.
node("L1", 0.85, 2.2, 3.85, 0.95, "Surgeon's office", "Staff assemble the packet.");
avatar("AvL1", 0.97, 2.32, 0.71);
pkt("P1", 3.55, 2.97);
node("Member", 0.85, 3.45, 3.85, 0.95, "The member: John Doe, 71", "Waiting on the surgery. Sees none of this.");
avatar("AvM", 0.97, 3.57, 0.71);
node("L3", 0.85, 4.75, 3.85, 0.7, "Provider gets one question", "Sends only what is missing.", { ts: 12, ds: 10, margin: [0.04, 0.12, 0.04, 0.85], line: C.purple });
avatar("AvL3", 0.95, 4.83, 0.54);
tagAI("T3", 0.85, 5.68, 3.85, 0.55, "No guessing. No full resend.");

// payer side
node("Intake", 5.8, 2.2, 3.5, 0.95, "Intake", "Checks member, form and codes. Uploads the packet.");
avatar("AvIntake", 5.92, 2.32, 0.71);
pkt("P2", 8.3, 2.97);
line("ArrAI", 9.3, 2.675, 0.2, 0, { color: C.purple });
node("AIbox", 9.5, 2.2, 3.1, 0.95, "AI reads at intake", "All 14 pages. Finds the facts.", { fill: C.purpleSoft, line: C.purple, tc: C.purple });
avatar("AvAI", 9.58, 2.32, 0.71);
tagAI("T5", 9.5, 2.2, 3.1, 0.95, "The reply goes back to the same nurse. No fax loop.");
node("Nurse", 5.8, 3.45, 3.5, 0.95, "UM nurse", "Reviews the evidence. No hunting.", { line: C.purple });
avatar("AvNurse", 5.92, 3.57, 0.71);
pkt("P3", 8.3, 3.27);
add({ name: "T2", kind: "text", x: 9.5, y: 3.4, w: 3.1, h: 0.28, runs: [{ text: "4 facts found, with page and quote", options: { bold: true, fontSize: 11, color: C.purple, fontFace: B } }] });
const chip = (n, x, y, t) => add({ name: n, kind: "node", x, y, w: 1.5, h: 0.3, fill: C.white, line: C.purple, lineW: 1, radius: 0.06, align: "center", margin: [0, 0.04, 0, 0.04], runs: [{ text: t, options: { fontSize: 9.5, color: C.ink, fontFace: B } }] });
chip("Chip1", 9.5, 3.72, "Expected stay · p.8"); chip("Chip2", 11.1, 3.72, "Risk factors · p.2");
chip("Chip3", 9.5, 4.06, "Imaging · p.5"); chip("Chip4", 11.1, 4.06, "Conservative · p.9");

// outcomes
add({ name: "OutPend", kind: "node", x: 5.8, y: 4.75, w: 2.1, h: 0.7, fill: C.amberSoft, line: C.amber, lineW: 1, runs: runs("Pend", "One precise question", C.amber, 13, 10, C.amber), margin: [0.04, 0.12, 0.04, 0.14] });
add({ name: "OutApprove", kind: "node", x: 8.0, y: 4.75, w: 2.1, h: 0.7, fill: C.okSoft, line: C.ok, lineW: 1, runs: runs("Approve", "Nurse confirms", C.ok, 13, 10, C.ok), margin: [0.04, 0.12, 0.04, 0.14] });
add({ name: "OutEsc", kind: "node", x: 10.25, y: 4.75, w: 2.3, h: 0.7, fill: C.purpleSoft, line: C.purple, lineW: 1, runs: runs("Escalate", "Evidence attached", C.purple, 13, 10, C.purple), margin: [0.04, 0.12, 0.04, 0.14] });
ring("RingPend", 5.8, 4.75, 2.1, 0.7, C.amber);
ring("RingApprove", 8.0, 4.75, 2.1, 0.7, C.ok);
ring("RingEsc", 10.25, 4.75, 2.3, 0.7, C.purple);
node("MD", 9.1, 5.62, 3.6, 0.62, "Medical director", "Decides, with the evidence.", { fill: C.purpleSoft, line: C.purple, ts: 12, ds: 10, tc: C.purple, margin: [0.03, 0.1, 0.03, 0.8] });
avatar("AvMD", 9.18, 5.67, 0.52);
tagAI("T4", 5.8, 5.62, 3.1, 0.62, "It arrives with the evidence. Only they can deny.");

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
line("ArrPend", 4.7, 5.05, 1.1, 0, { flipH: true, color: C.amber });
line("ArrReply", 4.7, 5.35, 1.1, 0, { color: C.purple });
add({ name: "LblReply", kind: "text", x: 4.72, y: 5.4, w: 1.06, h: 0.22, align: "center", runs: [{ text: "REPLY", options: { bold: true, fontSize: 10, color: C.purple, fontFace: B, charSpacing: 2 } }] });
line("ArrMD", 11.4, 5.45, 0, 0.17, { color: C.purple });

// labels + captions
label("LabelA", "PATH 1  ·  A COMPLETE PACKET", C.ok);
label("LabelB", "PATH 2  ·  SOMETHING IS MISSING", C.amber);
label("LabelC", "PATH 3  ·  NEEDS A PHYSICIAN", C.purple);
const CAPS = {
  c1: "Nothing changes at the start. A surgeon's office assembles the packet.",
  c2: "They still fax it to the plan. Fourteen pages.",
  c3: "Intake checks the member, the form and the codes, and uploads the packet.",
  c4: "This is where the AI comes in. During intake, it reads all fourteen pages and finds the facts.",
  c5: "The nurse picks it up. She is not hunting through fourteen pages.",
  c6: "She sees the four facts, each with its page and the exact words.",
  c7: "The AI recommends one of three ways out. The nurse confirms.",
  c8: "Path 1. Everything is there. She confirms the approval.",
  c9: "Path 2. A fact is missing. The system tells her exactly what to ask, and the provider gets one precise question.",
  c10: "They send only that. It goes back to the same nurse. No fax loop. No starting from zero.",
  c11: "Path 3. The facts are there but the case is borderline. It goes to a medical director.",
  c12: "The director gets the evidence and the nurse's note. Only they can deny.",
  c13: "Same people. Same decisions. What changes is the hunt, and the loop.",
};
Object.entries(CAPS).forEach(([k, v]) => caption(k, v));

'''
i, j = between(src, "// static frame", "/* ---------- timeline")
src = src[:i] + FRAME + src[j:]

# --- the clicks
SLOTS = r'''const slots = [
  { hold: 0, fx: [FI("L1"), FI("AvL1", 0), FI("Member", 200), FI("AvM", 200), FI("P1", 600), FI("c1", 300)] },
  { hold: 3.5, fx: [FO("c1"), FI("IcFax", 300), WI("ArrFax", "left", 300), FI("LblFax", 300), FO("P1", 900), FI("c2", 500)] },
  { hold: 2.2, fx: [FO("c2"), FI("Intake", 300), FI("AvIntake", 300), FI("P2", 700), FI("c3", 300)] },
  { hold: 3.0, fx: [FO("c3"), WI("ArrAI", "left", 300, 250), FI("AIbox", 500), FI("AvAI", 500), FI("c4", 300)] },
  { hold: 3.0, fx: [FO("c4"), WI("ArrIn", "down", 300), FO("P2", 300), FI("Nurse", 700), FI("AvNurse", 700), FI("P3", 1000), FI("c5", 300)] },
  { hold: 2.8, fx: [FO("c5"), FI("T2", 300), FI("Chip1", 600), FI("Chip2", 900), FI("Chip3", 1200), FI("Chip4", 1500), FI("c6", 300)] },
  { hold: 3.5, fx: [FO("c6"), WI("ForkStub", "down", 300, 250), WI("ForkBar", "left", 550, 500), WI("DropPend", "down", 1050, 250), WI("DropApprove", "down", 1050, 250), WI("DropEsc", "down", 1050, 250), FI("OutPend", 1300), FI("OutApprove", 1300), FI("OutEsc", 1300), FI("c7", 300)] },
  { hold: 2.2, fx: [FO("c7"), FI("LabelA", 300), FI("RingApprove", 300), FI("c8", 300)] },
  { hold: 3.8, fx: [FO("c8"), FO("LabelA"), FO("RingApprove"), FI("LabelB", 400), FI("RingPend", 400), FO("P3", 400), WI("ArrPend", "right", 300), FI("L3", 800), FI("AvL3", 800), FI("T3", 1500), FI("c9", 300)] },
  { hold: 3.0, fx: [FO("c9"), FO("AIbox"), FO("AvAI"), FO("ArrAI"), WI("ArrReply", "left", 300, 300), FI("LblReply", 500), FI("T5", 900), FI("c10", 300)] },
  { hold: 4.0, fx: [FO("c10"), FO("LabelB"), FO("RingPend"), FO("ArrPend"), FO("ArrReply"), FO("LblReply"), FO("L3"), FO("AvL3"), FO("T3"), FO("T5"), FI("LabelC", 500), FI("RingEsc", 500), FI("c11", 500)] },
  { hold: 3.2, fx: [FO("c11"), WI("ArrMD", "down", 300, 400), FI("MD", 700), FI("AvMD", 700), FI("T4", 1500), FI("c12", 300)] },
  { hold: 4.5, fx: [FO("c12"), FO("LabelC"), FO("RingEsc"), FI("c13", 400)] },
];
'''
i, j = between(src, "const slots = [", "\n/* ---------- build the slide")
src = src[:i] + SLOTS + src[j:]

# --- speaker notes, one per click
NOTES_JS = r'''const STEP_NOTES = [
  "Let me walk you through what Phase 1 looks like. It is the same case you saw earlier, so you can compare. And nothing changes at the start. A surgeon decides the patient needs a lumbar fusion. The office assembles the packet. Meet John Doe, 71.",
  "They still fax it to the plan. Fourteen pages. I did not try to change how providers send things. That is a big change I don't need to make to get the benefit.",
  "Intake checks the member, the form and the codes, same as today. And they upload the packet to our system. That upload is the moment everything changes.",
  "This is where the AI comes in. During intake, it reads all fourteen pages. It finds the billing code, which tells it which service this is, and it looks for the key facts that service requires. The AI does this work before a nurse touches the case.",
  "Intake assigns it to a UM nurse, same as today. The difference is what she opens. She is not hunting through fourteen pages.",
  "She sees four facts: the expected stay, the risk factors, the imaging, and the conservative treatment. Each one comes with its page and the exact words from the packet. She can check any of them in one click.",
  "The AI recommends one of three ways out: approve, pend, or escalate. The nurse confirms. The decision is still hers.",
  "Path one. Every fact is there and every rule is met. The AI recommends approve, and the nurse confirms. This is the good case, and it is faster because she is reviewing, not reading.",
  "Path two. A fact is missing. Today the nurse pends it and the provider has to work out what is missing. Here, the system tells her exactly what to ask. The provider gets one precise question, not a vague pend.",
  "They send only that. It goes back to the same nurse. There is no fax loop, no resending fourteen pages, and no starting from zero. This is where the right-first-time rate moves.",
  "Path three. The facts are there, but the case is borderline. The AI escalates it. It never makes that call.",
  "The medical director gets the case with the evidence and the nurse's note already attached. Only the director can deny, and they write the reason.",
  "Close on this. Same people. Same decisions. A person decides every case. What changes is the hunt and the loop. The AI finds the evidence, so the nurse reviews and the provider gets one question.",
];

const NOTES = `Same case as the current state, with the AI added where it is. Purple is what changes.`;

'''
i, j = between(src, "const STEP_NOTES = [", "main().catch")
src = src[:i] + NOTES_JS + src[j:]

out = os.path.join(HERE, "build_future.js")
open(out, "w", encoding="utf-8", newline="\n").write(src)
r = subprocess.run(["node", out], capture_output=True, text=True, cwd=HERE)
print(r.stdout.strip() or r.stderr.strip()[:600])
