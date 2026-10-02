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
- [x] Whether Humana has published PA metrics under the 2026 reporting requirement
- [x] Public benchmark for appeal overturn rates in MA
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
- [x] Humana's own published PA stats, if any exist post the 2026 reporting requirement.
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

## D-008 — North Star is first-pass correct determination rate (2026-09-26)

**Slide language (use as written on the KPI slide):**
- Complete packet, criteria met: approved.
- Genuinely missing something: pended, and the follow-up asks for exactly that.
- Denied by the medical director: the evidence in the file really supports the denial.

**Why this and not approval share or the CMS clock**
- Approval share depends on packet quality, which the payer does not control. What the payer
  controls is whether its first-pass decision was correct.
- The CMS clock is a guardrail, not a goal. Humana CY2025 (own CMS-0057-F reports): MA standard
  TAT mean 1 day, median 0; expedited mean 4-11 hours vs the 72h limit. Already met.
- Humana publishes no first-pass, pend, RFI or missing-document metrics. These are pilot-measured
  baselines, shown as placeholders in the ROI model.

**Metric structure**
- North Star: first-pass correct determination rate. Checked by sampled audit (senior nurse/MD).
  An overturn only counts against it if the info was already in the original packet.
- KPIs (inputs): avoidable pend rate, RFI cycles per case, missing-document rate at intake,
  pend-to-complete time, avoidable escalation rate (escalated only for missing info).
- Monitored, not targeted: total escalation rate; track escalation appropriateness (MD agrees).
- Guardrails: CMS clock, no wrong approvals, no AI denial (output enum {approve, escalate}).
- Eval metrics (FR per D-007): completeness recall, criteria-met recall, policy-citation accuracy.
- Public proxy (not a KPI): overturned denials per 1,000 standard requests, about 1.2 (MA).
- Phase 2: reviewer minutes via gated auto-approve; a hypothesis, no baseline.

**Humana CY2025 baselines (primary source, 32 MA contracts, 9 Medicaid states)**
MA: 9.53M standard requests; denial 6.86% weighted / 7.35% median; 2.71% of denials appealed;
64.7% of appeals overturned; extensions ~0%. Medicaid: 1.21M; denial 5.85% weighted / 10.86%
median; 7.19% appealed; 12.7% overturned; extensions ~3.1%. H5216 is ~45% of MA volume, so quote
the median too. Indiana Medicaid is the outlier (5.25% overturn, 47h mean expedited TAT).

**AMA wording:** 93% and 26% are shares of physicians surveyed, not patients. Slide must say
"physicians report". Re-check exact wording against the AMA page before presenting.

**Scenario coverage**
- KPIs: approve, pend, escalate. Evals: false "complete", wrong policy.
- Guardrail: expedited, CMS clock. Reproducibility NFR covers reviewer variation.
- Outside Phase 1: appeals (audit signal only). Deliberately out of scope: Medicaid/dual
  (different rules), member waiting (member view is 2027, D-003), provider burden (a benefit,
  not owned; levers are pend-to-complete time and RFI cycles).

**To do on the deck:** put the three lines above on slide 8 (KPIs); rename North Star; add the
OIG data date prominently (open feedback round 3, item 1).

## D-009 — Sequencing: prototype and AI layer first, slides after (2026-09-26)

She now understands the problem better and the slides and their order will change. Decision:
build the prototype and the AI/extraction/decision side first, then rework the deck around what
was built and measured. Do not restructure slides yet (this supersedes the paused round-3
feedback; its three issues are folded into the rework, not fixed piecemeal now).

Deck changes already known, to apply later:
- KPI slide: three lines from D-008; North Star renamed to first-pass correct determination rate.
- Burden slide: "physicians report" wording; explain what PA is before the stats.
- Reckoning slide: OIG data date (June 2024, reported June 2026) made prominent.
- Add a "why the clock is a guardrail" beat using the Humana CY2025 numbers below.
- Reconsider slide order around: burden -> current state -> what Humana already does well
  (clock) -> what is still broken (first-pass correctness) -> product -> metrics.

Working principle: notes are working drafts made by both of us and change as better evidence
arrives. Nothing here is gospel, including earlier decisions.

## Evidence log, 2026-09-26 (Humana CY2025 PA metrics, primary source)

Source: 41 PDFs in `humana metrics/` (26 H-contracts, 6 R-contracts, 9 state Medicaid), Reporting
Period 2025, Humana's own CMS-0057-F disclosures. Parsed with pdftotext; H1036, R0110, KY checked
by hand. Virginia uses a revised template (combined extension count, decimal TATs). Per-contract
extremes: MA standard denial 3.36%-12.63%; Medicaid 2.56% (FL) to 15.06% (OH).

| Metric | MA (32) | Medicaid (9) |
|---|---|---|
| Standard requests | 9,530,027 | 1,205,167 |
| Standard denial, weighted / median | 6.86% / 7.35% | 5.85% / 10.86% |
| Expedited denial | 7.83% | 19.82% |
| Appeals / denials | 2.71% (17,690 / 653,593) | 7.19% (5,066 / 70,484) |
| Appeal overturn | 64.72% | 12.65% |
| Extension use | 13 cases (~0.0001%) | 3.12% |
| Standard TAT | mean 1 day, median 0 | mean 0-4 days |
| Expedited TAT | mean 4-11 h | 5-47 h |

Reading notes:
- Extension = the 42 CFR 422 pend-extension provision, not internal nurse-to-MD escalation.
  Internal pend/escalation rate is not public. This answers the current-state doc's open question
  on extension vs the 7-day clock: for MA it is essentially never used.
- Humana's own note: an overturn "may be the result of additional information received."
- Illustrative only: ~11,450 MA denials overturned on appeal (~1.2 per 1,000 standard requests).
  97% of denials are not appealed, so do not extrapolate the 65% to all denials.
- Medicaid contrast: appealed 2.6x as often, overturned far less. Indiana worst (12.65% denial,
  5.25% overturn, 47 h mean expedited). Scope the "avoidable denial" story to MA.
- Not in any public data: first-pass rate, pend rate, RFI cycles, missing-document rate, nurse
  minutes or cost per case, inpatient/outpatient split, reviewer variability.
- Humana's Use Case 1 brief (Prep docs) has no baseline numbers; it asks for placeholder numbers
  with sound ROI logic, "think beyond admin savings", and names reviewer variability and member
  waiting as pains. Provider-side burden (AMA) is physician-reported, not member-reported.
- Cost/time per UM nurse case cannot be sourced; keep as a labeled assumption.

## ROI framing implied by the above
Drivers to name (placeholders, replaced by pilot measurement in the first 30 days): first-pass
correct rate, avoidable pend rate, RFI cycles per case, avoidable escalation rate, reviewer
minutes (Phase 2), overturn-on-info-in-packet rate. Value by stakeholder: member (fewer waits),
provider (fewer resubmission loops), nurse/MD (fewer avoidable pends and escalations), plan
(fewer avoidable denials and appeals, better decision consistency).

## Next: prototype and AI side
Tune extraction and the completeness gate for recall (D-007); build the eval set with expected
outcomes per scenario (approve / pend / escalate / false-complete / wrong-policy); define the
correctness audit and escalation appropriateness. Set up the GitHub remote.

## Build log, 2026-09-26: working prototype (PA Desk)

**What exists now** (all runs locally, made-up data only)
- Ingestion: Unstructured Transform API (key in `.env`, `UNSTRUCTURED_API_KEY`), page-tagged
  elements, local pdftotext fallback. Upload path tested live.
- Extraction: rule-based, every fact carries page + exact quote; a missing fact stays missing.
  Unstructured's built-in schema extraction also works (returns values only, no page or
  confidence), so citations are attached by our own code. LLM extractor plugs in later.
- Policy library `policies/policy_library.json`: real LCD L37848 (lumbar fusion, Palmetto GBA),
  42 CFR 412.3 (two-midnight), Humana illustrative internal policy (from the brief, labeled),
  MCG stub (licensed, not reproducible). Full CMS corpus downloadable via `scripts/build_corpus.py`
  and `scripts/build_ncds.py` (969 LCDs, 345 NCDs, ~2.2M tokens; 482 distinct LCD titles, 8 MACs).
- Decision engine: deterministic, output approve | pend | escalate, no deny value. Nurse cannot
  deny (server enforced 403). Approving against the recommendation needs a written reason.
- App: inbox by queue, case review (facts, criteria, citations that jump to the packet page),
  pend with drafted question, simulated provider reply that re-runs analysis, escalate with
  @-tag and notification, medical director queue (approve, deny with rationale, return), audit
  trail, evals page. Demo logins are on the sign-in screen (password demo1234).

**Findings that change earlier assumptions**
- LCD L38795, cited in the first prototype, is not in CMS's active final LCD list. Replaced.
- Two separate questions per case: level of care (two-midnight, internal policy) and medical
  necessity of the procedure (LCD). Humana's brief only tests the first; the LCD adds imaging
  evidence of instability, conservative care, shared decision making as further pend triggers.
- LCDs are regional. The policy table must key by service + MAC jurisdiction.
- Evals pass 6/6 but packets and extractor were written together: plumbing proof, not accuracy.

**Not done yet**
- Anthropic key / LLM extraction and criteria drafting across the full corpus (deliberately last).
- Messier eval packets (scans, inconsistent wording), extraction recall and precision reported
  separately per D-007, correctness audit and escalation-appropriateness metrics (D-008).
- Retrieval fallback over the full corpus; only lumbar fusion is curated.
- Unverified: whether CPT 22612 is on the inpatient-only list; other MACs' fusion LCDs.
- Deck rework (D-009) waits for the prototype.

## M6 -- held-out eval set, built and run (2026-10-01)

4 adversarial packets (`packets/holdout/`, `evals/holdout_manifest.json`), written without
looking at extract.py's patterns, each targeting one named failure mode. Ground truth is
annotated per fact (present/absent/negated), scored separately from the final action, per
D-007's "two signals" framing. Exposed on the Evals page below the original M1-M5 sanity set,
and via `GET /api/evals/holdout`. Live run (Unstructured API):

- Action matched expectation: 2/4
- Completeness recall (found it when it was really there): 11/15 (73.3%)
- Hallucination rate (claimed found when absent/negated): 1/3 (33.3%)

**Findings, each traced to a specific extract.py gap:**
1. **Ambiguous phrasing (Patricia Reyes).** 3 of 4 facts present in the text were missed,
   because real dictation ("remain hospitalized for 3 nights", "significant cardiac history",
   "nonsurgical management... physiotherapy") never matches the fixed keyword list. This is the
   clearest evidence for M7: a regex-based extractor has a hard ceiling on real-world phrasing.
2. **Conflicting values (Marcus Webb).** Two LOS statements exist; the later, clinically
   correct one (3 midnights) is superseded by an earlier draft (1 midnight). The extractor
   takes the first match and stops, so it reports 1 -- found, confident, and wrong. Wrong
   recommendation (escalate instead of approve). The eval harness originally missed this too
   (it only checked "was something found", not "was the value right") until patched to compare
   extracted vs. expected values -- recall dropped from a false 80% to the real 73.3% once fixed.
3. **Negation, most severe finding (Angela Petrov).** "No evidence of segmental instability on
   flexion-extension radiographs" contains both an imaging keyword and the finding keyword, so
   it is read as positive evidence of instability -- the opposite of what it says. extract.py
   already handles one negation correctly (comorbidities' "no significant comorbidities" ->
   status "none"); it has no equivalent for indication_evidence. **Confirmed by counterfactual**
   (isolated test, not in the eval set): in a packet where every other criterion is genuinely
   met, this single hallucination alone flips the recommendation from escalate to approve,
   citing the negated sentence as the supporting quote. In the actual holdout packet this is
   masked because comorbidities also fail for an unrelated reason -- masked by luck, not caught
   by design. This is the one finding that argues for a fix before relying on this extractor for
   anything beyond a demo, not just a reason to prefer the LLM path.
4. **Degraded scan, real OCR (Walter Kim).** Image-only PDF (rotated ~1.6 degrees, Gaussian
   blur, noise blended in, contrast reduced) -- confirmed zero embedded text via pdftotext, so
   local fallback cannot pass this one at all. The live Unstructured API read it correctly: all
   5 facts found, correct action. Positive evidence for the ingestion layer under realistic
   fax-like conditions, not just clean text.

**What this does and doesn't say:** per the eval page's own caveat, this set was written to be
hard, not representative -- a failure here names a real gap, not a claim about how often it
fires on real packets. No regex patches were added in response to 1-3; patching each one as
found is the whack-a-mole anti-pattern this exercise exists to argue against. The findings are
the evidence for M7 (LLM extraction), not a punch list for extract.py.

## M7 -- LLM extraction, self-consistency, and bounded retrieval (2026-10-02)

### Part 1: LLM extractor (pipeline/extract_llm.py)

Behind the same extract_facts() interface as the rule-based extractor (pipeline/run.py picks
whichever is available; local flag forces rule-based). Header fields (member, CPT, procedure,
etc.) stay on the existing regex -- that's boilerplate text regex already gets right 100% of
the time; only the six clinical facts, where the real ambiguity lives, go to the model. Two
things it does that regex structurally cannot:
- Every claimed quote is checked against the real packet text before being trusted. A quote
  that doesn't appear verbatim is downgraded to "missing" with a note -- the model's own page
  number is never trusted; the real page comes from where the verified quote actually sits.
- The prompt explicitly teaches the two lessons M6 found: negation ("no evidence of X" is
  status "none", not "found" -- reread what the sentence asserts, not just its keywords) and
  conflicting values (prefer the later, more specific, or post-review figure; name the
  conflict in "note" rather than silently picking the first match).

Comparison, same M6 held-out set, both extractors, full pipeline (ingest -> extract -> engine):

| Metric | Rule-based | LLM (voted) |
|---|---|---|
| Action matched expectation | 3/4 | 4/4 |
| Completeness recall | 73.3% | 100.0% |
| Hallucination rate | 33.3% | 0.0% |

(H1/Patricia Reyes's expected_action was originally mislabeled "approve" in the manifest --
one of her 5 facts is genuinely absent (imaging read pending), so "pend" is actually correct
regardless of extractor quality. Fixed the label; both extractors now correctly pend on her,
which is right. The real signal for that packet is the other 4 facts, all now read correctly
by the LLM, 3 of 4 missed by regex.)

All three of M6's named failures are fixed directly: Patricia Reyes's ambiguous phrasing
(cardiac history, "3 nights", nonsurgical management -- all found now), Marcus Webb's
conflicting LOS (now correctly reports 3 midnights with a note explaining why 1 was
superseded), and Angela Petrov's negation (now correctly "none", with a note that imaging
rules out the finding). The critical hallucination from M6 is gone on this set.

A new problem, found and fixed in the same session. The client in this environment exposes no
temperature parameter at all (confirmed: not in the installed SDK's messages.create()
signature) -- can't be dialed down. Direct testing found real run-to-run variance: on
p03_missing_imaging.pdf, which the rule-based extractor gets right deterministically every
time, 1 of 8 single-shot LLM runs decided a bare diagnosis ("spondylolisthesis") counted as
sufficient imaging evidence on its own, when it should not (the LCD requires imaging or exam
evidence, not just the surgeon's diagnostic label) -- flipping a correct "pend" to a wrong
"approve". Fix: self-consistency voting. extract_facts(elements, n_votes=3) runs the
extraction 3 times; a fact is only trusted if every run agrees on its status. On disagreement,
the fact is marked "missing" with a visible note ("the model disagreed with itself across 3
runs... flagged for human review"), not guessed at. Retested the same borderline packet 3
times with voting on: 3/3 correct. This is the reproducibility NFR from ARCHITECTURE.md
applied to the one place the model measurably disagrees with itself. n_votes defaults to 3 for
the live app path (pipeline/run.py); n_votes=1 is available for fast iteration in scripts.

Honest limitation, not hidden: voting sharply reduces variance but doesn't guarantee perfect
stability run-to-run -- a full comparison run (scripts/compare_extractors.py) showed one
sanity-set case (p04, Susan Whitfield) resolve to "pend" instead of the correct "escalate" due
to a 3-vote split on comorbidities; 3 immediate manual reruns of that exact packet all came
back correct (3/3 "escalate"). The safety net is doing its job -- disagreement converts to
"ask a human" rather than a wrong clinical call -- but it means this path can occasionally cost
an extra pend on a packet the deterministic regex never struggled with. Net effect is a clear
improvement (73%->100% recall, 33%->0% hallucination on the targeted hard set), not a strictly
dominant one. The eval harness is how this gets monitored going forward, not a one-time check.

Extraction engine is now visible per case (facts["_extractor"]), surfaced via the API and
shown in the case header: "Ingested via X - extracted via Y".

### Part 2: bounded retrieval fallback (pipeline/policy_retrieval.py)

Per ARCHITECTURE.md section 5: used only when a procedure has no curated entry, output always
unverified and routed to a human, never substituted into the automated decision. Two steps:
1. Keyword search narrows the full corpus (969 LCDs + 345 NCDs, policies/corpus/) to the top
   ~8 candidates by term overlap (title weighted 3x over indications text).
2. Claude picks among just those few, bounded and auditable, not an open-ended search -- and
   is told explicitly that admitting no match is better than a wrong one.

Tested against 3 real procedures, live:
- "spinal cord stimulator implant for chronic pain" -> correctly matched LCD L36204 (Spinal
  Cord Stimulators for Chronic Pain), drafted a real checklist (conservative treatment tried,
  multidisciplinary psych/physical screening, etc.) from the actual policy text.
- "screening colonoscopy" -> correctly matched NCD 210.3 (Colorectal Cancer Screening Tests)
  over several diagnostic-colonoscopy LCDs that also scored well on keywords -- the model
  correctly used "screening" to pick the NCD specifically, not just the top keyword hit.
- "treatment of warts on the sole of the foot" -> correctly found no genuine match among 8
  keyword-adjacent candidates (routine foot care, orthotics, skin-cancer radiation) and said
  so, with real clinical reasoning for why each candidate doesn't fit. (First attempt hit a
  real bug: max_tokens=300 cut off the model mid-explanation on this harder case, silently
  dropping the required "reasoning" field. Fixed: raised to 600, added defensive .get() so a
  truncated response degrades to "no match" instead of crashing.)

Real correctness bug found and fixed in the same pass: the decision engine previously applied
the curated lumbar-fusion criteria to any submitted procedure unconditionally -- there was no
check at all. Verified directly: a total knee arthroplasty packet (CPT 27447) was asked for
"imaging or exam evidence for the surgical indication" in the spinal sense. Not hypothetical --
confirmed by direct test before the fix. Fix: policy_library.json now declares
covered_cpt_codes (currently ["22612"]); engine.analyze() checks this first and returns a
distinct action: "no_policy" result -- skipping the lumbar-fusion criteria entirely -- when the
CPT isn't covered, rather than silently misapplying them. This stays in the deterministic
engine (a lookup, not a model call), keeping with ARCHITECTURE.md section 6; the
retrieval+drafting call itself is a separate, explicit step one layer up, never invoked
automatically from inside the engine. Verified end-to-end through the real upload, list, and
case-detail API endpoints -- all handle the new state without error. Frontend shows a plain
"no curated policy" banner for this state; it does not yet inline the retrieved candidate
policy into that view -- that polish is deferred to the later UX pass, consistent with the
agreed sequencing (M7/M8 first, UX improvements after).

### What's still open after M7
- Retrieval's drafted criteria aren't wired into the live UI for a no_policy case yet (the
  mechanism is proven standalone; inline display is UX-phase work).
- Only lumbar fusion has curated, human-reviewable criteria. The other ~1,313 corpus documents
  are searchable and draftable on demand, not pre-drafted in bulk -- a deliberate scope choice,
  not an oversight: pre-drafting everything without a human in the loop would contradict the
  "never silently substitute for the curated table" rule this whole mechanism exists to honor.
- The eval harness itself had two bugs found and fixed this session: the holdout scorer
  originally couldn't detect a right-status-wrong-value answer (Marcus Webb's case silently
  read as "correct" until patched), and one manifest label was internally inconsistent (H1).
  Both are fixed; worth remembering that the eval harness needs the same scrutiny as the code
  it is scoring.

## M8 -- deck rework (2026-10-02)

Edited deck/Humana_PA_Deck.pptx directly (unzip, edit slide XML, rezip), not regenerated from
scratch, so every slide this touch didn't is untouched. No LibreOffice on this machine, so no
visual thumbnail/render QA was possible this round -- validated structurally instead
(scripts/office/validate.py: all passed against the original; python-pptx opens all 14 slides
with the expected shape counts) and by reading the packaged text back with markitdown to
confirm every edit landed as intended. Flagging this limitation plainly: a visual pass in
PowerPoint itself is still worth doing before presenting, especially slide 8's two touched text
boxes (the North Star description and the guardrail description both grew close to or slightly
past their proven character budget -- see the per-edit notes below).

**Slide 2 (burden).** Added a plain-language definition of what PA actually is before the
stats, per the still-open round-3 feedback item. Made room by cutting the survey date detail
from the subtitle (it's already on the bottom source line, so this was a duplicate, not a
loss): "Prior authorization is the approval a provider must get from the plan before a service
is covered -- today, a largely manual, fax-based process." leads the line now.

**Slide 5 (reckoning).** The OIG data's date (June 2024, reported June 2026) was previously
only in small source text at the bottom -- the other still-open round-3 feedback item. Put it
directly in the eyebrow title instead, which can't be missed: "WHAT THIS IS CAUSING -- DATA
FROM 2024, REPORTED 2026." Shortened "CURRENT STATE" out of the title to make safe room for it
in the same single-line box.

**Slide 8 (KPI/North Star) -- the real rework, per D-008.** This was backwards before: the CMS
clock was the North Star and "no increase in appeals overturned" was the only guardrail.
Fixed to match the reasoning actually worked out in this conversation:
- North Star renamed to first-pass correct determination rate, with the three lines from D-008
  on the slide, each its own line: "Complete packet, criteria met: approved." / "Missing
  something real: pended for exactly that." / "Denied: only when the file's evidence supports
  it." (lightly tightened from the verbatim wording to fit the proven-safe character budget of
  that text box -- the exact verbatim lines are in the speaker notes in full, with no space
  constraint there.)
- The three "levers" are no longer "avoidable pend rate / first-pass determination rate /
  reviewer minutes" (that middle one is now the North Star itself, so keeping it there would
  have been circular). Swapped in RFI cycles per case, tagged "NO PUBLIC BASELINE" to match
  the evidence log honestly. Avoidable pend rate and reviewer minutes (Phase 2) unchanged --
  already correct.
- Guardrails, now plural: the CMS clock (already met -- Humana's CY2025 MA standard TAT
  averages 1 day against the 7-day limit) and no increase in appeals overturned (today's real
  number, ~65% of appealed MA denials, per the evidence log). Both the clock-already-met
  evidence and the overturn baseline are now stated on the slide, not just implied.
- Speaker notes rewritten in full to carry the actual reasoning: why the clock can't be a North
  Star if it's already met, the verbatim three lines, the correctness-by-audit-sample point,
  and the overturn-rate number reframed as a second argument for the North Star (a lot of those
  overturns are first-pass-correctness failures, not appeals-process failures).

Checked the rest of the deck for now-inconsistent references to the old framing (slide 10's
Scope & Phasing already correctly lists avoidable pend rate and first-pass determination rate
as Phase 1 targets -- that held up unchanged) -- nothing else in the deck referenced "CMS
clock" or "North Star" outside slide 8, so no other slide needed a matching edit.

The pre-M8 version is preserved in git history (commit 679650c) if a side-by-side comparison
is ever needed -- `git show 679650c:deck/Humana_PA_Deck.pptx > old_deck.pptx`.

## Test setup: Admin persona + realistic demo packets (2026-10-02)

Deck work paused (per her instruction) to set up for end-to-end testing. Three personas, not
four -- confirmed directly: Admin (intake), UM Nurse, Medical Director. No separate "doctor"
role; the medical director is the doctor.

**Admin role added** (`app/db.py` seed: Carla Mendez, Intake Coordinator). Job is routing only,
never a clinical call:
- `POST /api/cases/{id}/action` now rejects approve/pend/escalate/deny/return for any role
  other than nurse/medical_director -- server-enforced, not just hidden in the UI. Verified: a
  403 with a clear message, tested directly against the API.
- Upload (`POST /api/cases`) no longer auto-assigns to the uploader when the uploader is an
  admin. Takes an optional `assignee_id` form field; without one the case lands unassigned.
  Admin routes it afterward using the same `/assign` endpoint nurses and MDs already use (no
  new endpoint needed there).
- New `unassigned` queue view (open cases with no assignee), sorted oldest-first.
- Frontend: admin's nav swaps the reviewer-centric views (Needs my review, At risk, All mine)
  for `Needs assignment`; the case review tab replaces the approve/pend/escalate buttons with a
  plain note pointing at the Assigned dropdown, for every role, including the `no_policy` case.
- Verified end-to-end through the real API: admin uploads -> unassigned, correct analysis still
  runs -> blocked from approving (403) -> assigns to a nurse -> unassigned count drops to 0 ->
  that nurse immediately sees it in her own queue. A second upload with no assignee lands in
  `unassigned` correctly.

**Realistic demo packets** (`packets/demo/`, `scripts/make_realistic_packets.py`) -- not part
of any eval set, for manual click-through only. Longer and more realistic than the eval
fixtures: full demographics, insurance, referring provider (name, NPI, practice, phone/fax),
and multi-section clinical narrative (HPI, PMH/PSH, meds, allergies, exam, a formatted imaging
report, a conservative-care timeline). Three outcomes: `demo_alvarez_approve.pdf`,
`demo_okonkwo_pend.pdf` (missing LOS, worded ambiguously on purpose), `demo_yun_escalate.pdf`
(short stay, low risk, worded to need a physician's judgment). All verified against the live
pipeline (real Unstructured ingestion + LLM extraction) to produce the intended action before
handing off.

One live finding while verifying demo_yun_escalate.pdf: one of five wrapper calls (self-
consistency voting, n_votes=3) came back with all five facts flagged missing, when 3 direct
reruns right after came back clean or with at most one fact flagged. Traced to the individual
votes themselves (not a bug in the voting/aggregation code -- read it closely, it's correct);
this matches the known, already-documented M7 behavior (the voting safety net occasionally
flags a borderline fact for review rather than guessing), just a more visible instance of it.
Noting here rather than treating it as a new bug: if this shows up again during her testing,
it's expected behavior, not something broken.
