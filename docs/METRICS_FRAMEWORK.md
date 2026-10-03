# Metrics: North Star, leading, lagging, health, eval

2026-10-03, version 3 (v1 was a long catalog, v2 was circular; both in git history).
Method follows the EnergySage lead-quality work: one outcome, early signals that read it, later
results that confirm it, guardrails around it.

## North Star: Right-First-Time rate

Right-First-Time = decided cases with no rework / decided cases.

A case has rework if any of these happens:
1. **Avoidable pend.** The provider replies that the information was already in the packet.
2. **Avoidable escalation.** The medical director returns the case to the nurse.
3. **Overturned later.** A denial is overturned on information that was already in the packet.

Overall pend rate is not the measure: a pend for information that is genuinely missing is the
system working. Only avoidable pends count.

Why a director returns a case: the director's job is approve or deny, so a return means the
case should not have reached them. Reasons: information is missing (should have been a pend);
criteria were clearly met (could have been approved); other (for example wrong policy applied).
The first two are avoidable. The app stores only a free-text note today; it needs a reason code.

Year-horizon goal, reviewed quarterly. Target set after a 60-day pilot baseline. Not a live
number in a demo. Why not the CMS clock (already met), reviewer minutes (winnable by reading
less), approval rate (winnable by approving more).

Items 1 and 2 are known within days, item 3 in months. Same metric at two speeds: the fast part
is the leading indicator, the slow part is the lagging confirmation.

## Leading indicators (days)

| Metric | Definition (lower is better) |
|---|---|
| Avoidable pend rate | Pends the provider says were already answered / all pends |
| Avoidable escalation rate | Escalations the director returns / all escalations |
| RFI cycles per case | Pend rounds per pended case (target: 1) |
| **Composite: Early Right-First-Time** | Decided cases with none of the three problems above / decided cases |

Tracked as a before-and-after on the composite, not a ranking.

## Lagging indicators (months)

| Metric | Definition | Baseline |
|---|---|---|
| Overturn-on-packet-information rate | Denials overturned on appeal because the information was already in the packet / all denials | None public. Overall MA overturn is 64.72% (Humana CY2025) but mixes new information with first-pass error. Needs an appeal reason code. |
| Independent-review overturn rate | Plan-upheld denials overturned by the independent review entity / upheld denials forwarded (42 CFR 422.590) | None public that I verified |
| Provider satisfaction score | Quarterly provider survey on the prior authorization experience | AMA 2025 frames it (13 h/week); not Humana-specific |
| Cost per determination | Total review, pend and appeal cost / determinations | Illustrative only |

### Is avoidable pend rate really leading? Depends on provider reply time (unknown)

It is leading only if the label arrives long before the lagging results (months). The label
arrives when the provider replies, so reply time decides it.

- **No public benchmark found.** CMS-0057-F metrics and Humana's reports do not include
  provider response time to a pend. The sources I found give effort per request (CAQH: about
  16 to 24 minutes per manual or portal request), not how long a reply takes. Practitioner
  advice is to chase pends at 48 hours and five days (weak source).
- The ~3-day pend loop in our own current-state diagram was an illustrative assumption from the
  service design, not data. Do not quote it.
- The standard clock bounds the answer: the plan has to resolve within the standard window
  plus a limited extension (exact extension length under the 2026 rule is still unverified in
  our notes). So a pend that gets a reply is labelled within weeks, against months for appeals.
  Structurally leading, if replies actually arrive.
- Two weaknesses to design around: pends that never get a reply cannot be labelled (report
  reply rate and median time-to-reply next to the metric), and "already in the packet" is
  self-reported by the provider (cross-check against the nurse's "this fact is present"
  correction on a sample).
- Test in the pilot's first weeks: median pend-to-reply time and share answered within 7 days
  (the prototype already logs pend and reply timestamps). Proposed rule, my threshold: leading
  if most pends are answered inside the 7-day window; if typical replies take longer than two
  weeks, move the nurse-side correction signal to the front.

## Health metrics (must not get worse)

| Metric | Guards against |
|---|---|
| CMS clock compliance % | Speed bought at the cost of the clock. Humana already meets it. |
| Approval-share change vs baseline | Winning by approving more. Reference: MA standard denial 6.86% weighted (CY2025). |
| Approvals where the nurse opened a cited page / approvals | Accepting the recommendation unread |
| AI denials | Must stay at 0, with a rationale on every denial |

## Eval and observability metrics (is the AI doing its job)

Not product outcomes; these tell us whether the reader and recommender are trustworthy.

| Metric | Definition | Where it comes from |
|---|---|---|
| Extraction recall | Facts found when present / facts present | Eval sets; in production, nurse corrections |
| Hallucination rate | Facts claimed found when absent or negated / absent or negated facts | Eval sets (M7: 0% on the held-out set) |
| Self-disagreement rate | Cases where the 3 model reads disagree on a fact / LLM-read cases | Stored notes |
| Nurse correction rate | Cases where the nurse corrects an AI fact or recommendation / cases | New event |
| Latency and cost per case | Seconds and model cost to analyze one packet | Request timing |

## What the prototype needs

Four small events, then a small view labelled demo data:
1. Provider reply type: attached / already in packet (page) / cannot provide (avoidable pend)
2. Director return reason code (avoidable escalation)
3. Nurse "this fact is present" correction on an AI-missing fact (eval: nurse correction rate)
4. Packet page opened (health: citation check)

Already available from the audit trail: RFI cycles, pend duration, clock compliance, escalation
outcomes, decision times.

## Validating the set

The leading indicators are a hypothesis until they predict the lagging ones. In the pilot, keep
an indicator only if cases that fail it are also the ones overturned later. Before live use,
replay historical packets with known outcomes through the system in shadow mode.

## Decisions needed

1. Is the structured version above clear and right? Anything to cut?
2. Build the four events and the small view next, ahead of the flow fixes?
3. Does Humana's appeals unit record why an appeal was overturned? If not, lagging metric 1 is
   a data request, and the pitch should say so.
