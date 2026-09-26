# Humana Take-Home: Prior Authorization Decision Support

Running notes and decision log. Keep entries short. Add the **why**, not just the what.

Use case: **UC1, Prior Authorization Decision Support** (Utilization Management)
Deliverables: 7 (problem brief, service design, working prototype, roadmap, key tradeoff,
business case + ROI, evals framework)
Format: 45 min call, ~30 min present, ~15 min Q&A, with two Directors.

---

## Personas (final)

| Persona | Role | In prototype? |
|---|---|---|
| **UM nurse** | Primary user. Reads the packet, applies medical policy and clinical rules, decides or pends. **Main character of the demo.** | Yes, primary |
| **Provider staff** | Opposite end of the loop. Submits the request, receives the pend, sends what is missing. Direct to and fro with the nurse. | Yes, as the recipient of outbound requests |
| **Medical director** | Where escalation goes. The human in the loop. **Only they can deny.** | Yes, escalation view |
| **Member (John Doe)** | The person whose clock is running. Waiting on the procedure. | **No.** Journey map only. See D-003 |

---

## Decisions

### D-001 — Chose UC1 over the other six
2026-09-24. Closest match to prior work: unstructured documents in, structured and cited
output out, matched against a governed policy hierarchy, human decides. UC1 is also the only
brief asking for a business case and an evals framework, which are differentiators rather
than gaps. Ruled out UC4/5/6/7 on domain risk (HCC, HEDIS, FWA, admission drivers) and
because their advanced tiers need predictive modelling that cannot be defended.

### D-002 — Core thesis is the avoidable pend, not reading speed
2026-09-25. In Humana's own scenario the nurse does not decide wrongly. She **pends** because
one fact (expected length of stay) is missing, and then the plan and hospital trade faxes for
days while the admission date slips. So the product is not a faster reader. It is a
**completeness gate** that turns a vague pend into one specific question, asked immediately.
ROI should lead on avoidable pend rate, not on nurse minutes saved.

### D-003 — Member is in the journey, not in the prototype
2026-09-25. Scope cut, deliberate, defensible on two grounds.

1. **Accuracy of current state.** Today the member genuinely is blind. PA is a payer to
   provider transaction. Most members do not know a request was submitted and find out when
   the provider's office calls to move the date. Showing him invisible is the honest map.
2. **Regulation puts him on the roadmap, not in v1.** CMS-0057-F requires a Patient Access
   API including prior authorization status by **1 Jan 2027**. So member-facing status is a
   dated, required later phase, not a nice-to-have we invented.

Effect on deliverables: John Doe appears in the current-state journey with an elapsed-days
clock, and appears on the roadmap as a named phase with the CMS date as the reason.

### D-004 — AI may auto-approve, never auto-deny
2026-09-25. Error costs are not symmetric. A wrong approval means paying for care that
probably met criteria anyway, and it is recoverable. A wrong denial means a member does not
get care they were entitled to: irreversible, appealable, and a regulated event. So the
system may auto-approve only where every criterion is clearly met with high-confidence
citations, routes everything else to the nurse, and a denial can only be issued by a medical
director. This is the key tradeoff answer: we give up most of the automation headline to
keep the error asymmetry right.

---

## Regulatory notes

Everything here is public rule text. Verify before quoting a number on the call.

### CMS-4201-F, MA final rule (issued 5 Apr 2023, effective CY2024)
- PA may only be used for medical-necessity benefit determinations based on presence or
  absence of diagnoses / clinical criteria.
- **MA plans must follow the same coverage criteria as Traditional Medicare**: NCDs, LCDs,
  and general coverage conditions. Internal criteria only where Medicare criteria are not
  fully established. **This is exactly the hierarchy the brief describes**
  (NCD > LCD > Humana internal policy > MCG).
- Approvals must be **valid for the duration of the course of treatment**.
- **90-day continuity of care**: no PA on an active course of treatment for new enrollees.
- Every MA plan must run a **Utilization Management Committee** reviewing policies annually
  for consistency with Traditional Medicare.
- Timeliness under this rule: **72 hours expedited, 14 days standard**.

### CMS-0057-F, Interoperability and Prior Authorization final rule (finalised 2024)
- **From 1 Jan 2026**: decisions within **72 hours expedited, 7 calendar days standard**
  (tightens the 14 days above), a **specific reason** required on denials, and **annual public
  reporting** of PA metrics (first report was due 31 Mar 2026 covering CY2025).
- **By 1 Jan 2027**: four FHIR APIs live. Patient Access (now including PA status), Provider
  Access, Payer-to-Payer, and the Prior Authorization API.

### Why this is the "why now"
Not "manual review is slow." It is: a hard external clock, a public reporting obligation on
PA metrics, and a member-facing API fifteen months out. Turnaround stops being an efficiency
metric and becomes a compliance metric.

**Sources**
- https://www.cms.gov/initiatives/burden-reduction/overview/interoperability/policies-regulations/cms-interoperability-prior-authorization-final-rule-cms-0057-f
- https://www.cms.gov/newsroom/fact-sheets/2024-medicare-advantage-and-part-d-final-rule-cms-4201-f

### CMS-4201-F, the MCG / InterQual limit (important)
CMS stated MA plans **may not use InterQual or MCG to change coverage or payment criteria
already established under Traditional Medicare.** They may only use those products to help
*create internal coverage criteria* where Medicare criteria are not fully established, and
only under specific conditions.

So the hierarchy in the brief is not a preference order, it is a legal constraint. If an NCD
or LCD covers the service, that governs. MCG only enters where Medicare is silent.
**Product consequence:** the AI must show which source in the hierarchy drove each
recommendation, and must never let a commercial criteria set override an NCD or LCD.

### Two-midnight rule
Set in 2013 for Traditional Medicare. CMS-4201-F confirmed **MA plans must follow it.**
If the physician expects the member to need hospital care crossing two midnights, inpatient
admission is generally appropriate. Shorter than that belongs in outpatient or observation,
which is a different level of care and pays differently. This is why the sample policy hinges
on expected length of stay.

### The clock and pends (answer to the open question)
A pend does not silently stop the clock. Under 42 CFR 422 an MA plan may take an
**extension of up to 14 calendar days** when it needs more information, but only if it
justifies that the delay is in the member's interest, and it must **notify the member in
writing**, including their right to disagree with the extension.

**Why this matters for the business case:** every avoidable pend is a documented,
member-notified delay, not an invisible pause. Pend rate is therefore a compliance number,
not only an efficiency one.

**Still open:** how the extension provision interacts with the new 7-day standard clock from
Jan 2026, since the extension language was written against the older 14-day timeframe.

---

## Policy and standards landscape

Things that govern or touch this use case. Tier 1 is load-bearing for the prototype.

**Tier 1, must be right**
| Item | Why it matters here |
|---|---|
| **CMS-4201-F** (MA final rule, CY2024) | PA only for medical necessity; must follow NCD/LCD; internal criteria only where Medicare is silent; MCG/InterQual cannot override Medicare; approvals valid for the course of treatment; 90-day continuity of care; annual UM Committee review |
| **CMS-0057-F** (Interoperability and PA) | From Jan 2026: 72hr expedited / 7 calendar days standard, specific denial reason, annual public PA metrics. By Jan 2027: Patient Access, Provider Access, Payer-to-Payer and Prior Authorization FHIR APIs |
| **42 CFR 422 Subpart M** | Organization determinations. Timeframes, the 14-day extension and its member-notification requirement, appeal rights |
| **Two-midnight rule** | The inpatient vs observation test the sample policy depends on |
| **NCD / LCD** | The top of the evidence hierarchy. NCDs are national, LCDs are set by regional MACs |

**Tier 2, useful context**
| Item | Why |
|---|---|
| **MCG and InterQual** | Commercial criteria sets. Bounded use only, see above |
| **X12 278** | The HIPAA standard transaction for PA request and response. The electronic alternative to the fax |
| **Da Vinci FHIR IGs (CRD, DTR, PAS)** | The implementation guides underpinning the CMS-0057-F PA API. CRD tells a provider whether PA is needed, DTR gathers the documentation, PAS submits it |
| **Gold carding** | Exempting consistently-compliant providers from PA. Several state laws; worth a roadmap phase |
| **Appeals and overturn rates** | ROI lever. A denial that gets overturned cost the plan the review, the appeal, and the delay |

**Research still open**
- [ ] Extension interaction with the 7-day clock (above)
- [ ] Whether Humana has published PA metrics under the 2026 reporting requirement
- [ ] Public benchmark for appeal overturn rates in MA
- [ ] Whether gold carding applies to MA or is state-commercial only

---

## Terminology (use consistently)

- **Case** is the unit of work. One request, one member, one service. Cases get approved,
  denied or pended.
- **Packet** is the clinical documentation attached to the case.
- **Pend** is a held status, not a queue and not a denial.
- **Organization determination** is the formal name for the plan's coverage decision.
- **Length of stay** only matters for inpatient, SNF and rehab. A drug or imaging request has
  completely different required facts. **Product consequence:** the completeness check cannot
  be a hardcoded checklist, it has to be derived from whichever policy applies.

### D-005 — Keep plan intake as a lane, relabelled
2026-09-25. Intake is a persona in the brief ("the people who receive requests and check them
for completeness"), but it only earns a lane if we say what it actually checks. It runs an
**administrative** completeness check: right member, right form, right codes. It cannot run a
**clinical** one. So the current state has two completeness gates and neither catches the gap
that causes the pend. Ours is the third and the first that is clinical.

---

## Research queue

- [ ] Confirm whether the 7-day standard clock supersedes the 14-day one for MA specifically,
      or whether both apply in different contexts. **Matters if quoted on the call.**
- [ ] What MCG actually is, and how it sits below NCD/LCD in the hierarchy.
- [ ] Two-midnight rule, since the sample policy leans on "expected stay crosses at least two
      midnights."
- [ ] Typical inpatient level-of-care criteria, enough to make the checklist credible.
- [ ] What "gold carding" is, and whether it belongs on the roadmap.
- [ ] Humana's own published PA stats, if any exist post the 2026 reporting requirement.
- [ ] Appeals and overturn rates as an ROI lever. Is there a public benchmark?

### D-006 — Phase 1 is recommend-only, not auto-approve
2026-09-25. D-004 said the AI "may auto-approve." Refined: auto-approve is **Phase 2**,
gated on evals proving zero false approvals on the highest-confidence subset. Phase 1
recommends approve with citations, nurse confirms with one click. Reasoning: zero evals
history on day one makes a live auto-approve claim hard to defend to a Directors panel.
A gated rollout is a stronger judgment answer than a leap of faith, and it gives Phase 1
vs Phase 2 a clean story: Phase 1 removes the pend, Phase 2 removes the read.

### D-007 — Precision and recall are FR, not NFR, and there are two signals, not one
2026-09-25. Confirmed as FR (consistent with the position already taken in
[[Humana - Fit and Leadership Answers]], T4: "I'd write it as acceptance criteria now").
Two distinct signals, different error tolerance each, plus a separate action gate.

**Signal 1, completeness (is the packet complete).** Tune to catch gaps. A missed gap
(system says complete when it is not) means a case gets judged on incomplete evidence,
which can go wrong in either direction. An over-flag costs a few minutes of provider
time. Err toward asking.

**Signal 2, criteria-met (does the evidence support the clinical criteria).** Tune for
recall. Under-detecting evidence that is actually there routes an approvable case to
escalation, and if the medical director defers to a flawed "does not meet" read, that is
the path to a wrong denial. This is the specific mechanism behind "a false negative leads
to denial in care."

**The action layer, separate from both.** Whether the system actually recommends
approve is gated on precision, stricter than the detection underneath it. High recall on
detecting support, a stricter confidence bar before acting on it. Two knobs, two
pipeline stages, not in tension.

Numeric thresholds for both signals become acceptance criteria on the FR, not a
freestanding NFR.

---

## Market landscape

**Cohere Health** is the direct payer-side comparable. Cohere Unify does AI extraction
and matching against clinical criteria for health plan UM teams. Reported: automates up
to 90% of requests, 35-40% reduction in clinical review time.

**Load-bearing quote:** "No request is denied exclusively by AI. Only human clinical
experts can make that call." Validates D-004/D-006 as market-standard positioning, not
excess caution.

**Provider-side tools**, a different problem from ours: Rhyme (formerly PriorAuthNow),
Myndshft (part of Waystar), Innovaccer Flow, Availity AuthAI. These submit and track
requests rather than deciding them.

**Regulatory direction confirms never-auto-deny is becoming the floor, not a choice.**
California SB 1120 (2024) and Texas SB 815 (effective Sep 2025) both prohibit AI being
the sole basis of an adverse determination. 11+ states have introduced similar bills; 37
states have some form of AI utilization-review legislation as of 2026.

**Differentiation to state explicitly:** deriving which facts a policy requires rather
than checking a fixed list, and turning a vague pend into one targeted question. Cohere's
public material talks about review-time reduction broadly; ours is one sharp mechanism,
which suits a take-home better than a platform pitch.

**Sources**
- https://www.coherehealth.com/platform
- https://www.darkdaily.com/2025/04/23/states-pursue-legislation-limiting-ais-growing-role-in-payer-prior-authorization-denials-and-claims-processing/
- https://breakingnewsaba.com/policy/six-states-restrict-ai-claim-denials-as-aba-audits-tighten

---

## Deck structure, phase 2

Slides 1-8 built (Humana_PA_Deck.pptx). Adding, in rough order after slide 6 (North Star):

- **Market Landscape** — Cohere Health comparable, provider-side tools, the state-law
  trend, our differentiation
- **Scope & Phasing** — Phase 1 targets avoidable pend rate + first-pass determination
  rate. Phase 2 targets reviewer minutes via gated auto-approve. Ties directly to D-006.
- **Requirements (FR/NFR)** — built from D-007, before Current State or right before the
  prototype walkthrough

Tradeoff and Constraint slides stay as built. Tradeoff slide gets one added line: this is
ahead of where several states already require plans to be, not just our own caution.

---

## Build notes

- Prototype: single self-contained HTML file, React from CDN, fake data inline, published as
  an Artifact. No dev server at demo time.
- Source in a git repo for history. Local tooling confirmed: git 2.33, Node v16.15.1,
  Python 3.13. No `gh` CLI.
- Screens planned: queue, packet + extraction, criteria match, completeness gate, decision,
  audit trail. Medical director escalation view.
- Service design (current vs future journey) to be rendered in Claude Design. Current state
  early, future state after the prototype is built.

## Deck v2, built and QA'd — 14 slides

Movie structure: three dark "stakes" beats (title, burden, reckoning) inside a light,
analytical build. Order:

1. Title
2. The burden (dark) — AMA 13hrs/wk, 93% delay, 26% serious adverse event
3. The cast
4. Current state (diagram placeholder)
5. The reckoning (dark) — OIG June 2026, 95% SNF overturn, 43% IRF, 36% LTCH
6. Why now — three walls: 2026 clock, 2027 visibility, state AI-denial bans
7. What the market is doing — R1 maturity model, Cohere Health quote
8. North Star & KPIs
9. The money — revenue vs profit (MLR), the overturn-rate trap, Star Ratings footnote
10. Scope & Phasing — mapped onto R1's Fragmented/Managed/Intelligent
11. FR — five, strict
12. NFR — five
13. Tradeoff — now four rows, appeals/peer-review boundary added
14. Constraint — policy hierarchy

All validated (schema, content, visual QA at 1600x900 via PowerPoint COM export).
Two layout bugs found and fixed in QA: slide 9 left-card text was overlapping (fixed by
combining two money stats into one and correcting hardcoded y-coordinates), slide 13
overflowed the slide bottom after the appeals row was added (fixed by compressing row
heights and shortening two descriptions).

**New sources used**
- AMA, 2025 Prior Authorization Physician Survey (ama-assn.org)
- HHS OIG, two reports, June 2026 (oig.hhs.gov)
- R1 RCM, "The Future of Utilization Management" (r1rcm.com)
- Cohere Health platform page (coherehealth.com/platform)
- 42 CFR 422.2410, CMS minimum MLR
- CMS CY2027 MA & Part D Final Rule (Star Ratings appeals-measure retirement, SY2029)

Prototype (screens 5-6 per NOTES build section) still not started. Next real blocker:
build the current-state flow diagram artifact for slide 4's placeholder.

## Deck v3 — reordered, retitled, full speaking scripts (feedback round 2)

Applied:
- Slide 2 rebuilt: "Ask any physician" dropped, replaced with proper AMA citation
  preamble, provider-vs-payer attribution stated on-slide, three stats given a
  narrative arc (cost -> consequence -> worst case) instead of floating numbers.
- Cast renamed to "User Personas," moved to AFTER current-state flow (was before).
  Old disjointed bridge line to the burden slide removed; subtitle now calls back
  to the diagram just shown instead.
- Reckoning slide eyebrow reframed: "THIS ALREADY HAPPENS" -> "WHAT THIS CURRENT
  STATE IS CAUSING" — causal tie back to the flow diagram, not a standalone shock.
- KPI slide retitled: "One number, three levers, one guardrail" (cheesy) ->
  "How we will know this is working."
- Money slide right column reframed: "THE TRAP TO REJECT" (internal reasoning,
  shouldn't be presented as a headline) -> "HOW EFFICIENCY BECOMES MARGIN"
  (positive, forward framing of the same OIG evidence).
- Scope & Phasing: member-facing visibility (2027 API) explicitly folded into the
  Intelligent/Phase 2 tier, alongside gated auto-approve and the feedback loop.
  Title now states the transition directly: "Today is fragmented. This prototype
  makes it managed."
- Every one of the 14 slides now carries a full first-person speaking script in
  its notes (not presenter shorthand) — written to be read/adapted as the actual
  talk track, explaining the regulation, the number, or the tradeoff in the room.

New order: Title, Burden(reframed), Current State(moved up), User Personas
(moved down), Reckoning(reframed), Why Now, Market, KPI(retitled),
Money(reframed), Scope&Phasing(enhanced), FR, NFR, Tradeoff, Constraint.

Rebuilt, revalidated, all 14 visually re-QA'd. Clean.

## Open feedback, round 3 (paused mid-review — come back to this)

Three real issues raised, not yet fixed:

1. **OIG timeframe is buried.** "95% overturned" only carries its date (data from
   June 2024, reported June 2026) in small source text at the bottom of slide 5.
   Needs to be visible/prominent, not a footnote — a Director shouldn't have to
   hunt for when the data is from.
2. **We never explain what prior authorization actually IS before the stats.**
   Slide 2 jumps straight into "13 hours / 93% / 26%" without first stating, in
   plain terms, what the process is and why it's structurally slow. Add that
   explanation before the numbers, not just a title.
3. **The through-line itself may need rework, not individual slides.** She tried
   narrating the deck out loud unprompted and it didn't flow cleanly even for
   her: "I chose this because it's industry-wide -> AMA numbers -> current state
   -> four personas -> this costs 95%..." If the story doesn't come out as one
   clean sentence leading to the next when she says it herself, it won't land
   presented either. Do not guess at a restructure from here — when she's back,
   have her narrate the story she actually wants to tell, out loud, and find
   where it breaks from that, rather than proposing another reorder blind.

Paused here — she's stepping away to talk it through with her husband before
giving fuller direction. No slide changes made against this feedback yet.

## Flow diagram embedded — slide "Current State" (Deck v3)

Final swimlane flow diagram image dropped into the Current State slide, replacing
the placeholder frame. Sized to the placeholder's height (3.85"), width derived
from the image's native aspect ratio (1916x1044) to avoid distortion, centered
horizontally. Validated, single-slide visual QA passed, no overlap.
