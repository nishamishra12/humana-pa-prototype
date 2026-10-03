# Metrics framework: North Star, leading and lagging indicators

2026-10-03. Replaces the "quality view" idea in UX_CRITIQUE finding 8, which over-reached (see
section 1). Builds on D-008. Figures about Humana come from its own CY2025 CMS-0057-F reports
(docs/humana-metrics); everything marked "verify" should be checked before it goes on a slide.

## 1. What changed in my thinking

The North Star is first-pass correct determination rate. Two problems, both raised in testing:

- **It cannot be shown live.** "Correct" is only knowable after the fact. A demo can describe it
  and instrument toward it; it cannot display it as a real number.
- **The slow signals cover only part of it.** A first-pass decision is one of three things:
  approve, pend, or deny. Appeals, complaints and court cases can only ever see denials (and
  some pends). A wrong approval is never appealed by anyone. Humana's data shows how thin this
  is even for denials: 2.71% of MA denials are appealed, so 97% produce no outcome signal at
  all, and Humana itself notes an overturn "may be the result of additional information
  received", so an overturn is not proof the first decision was wrong.

One correction to the slow end: it is not only courts. When an MA plan upholds a denial on
reconsideration it must forward the case file to the CMS-contracted independent review entity
(42 CFR 422.590: within 60 calendar days for standard, 7 for expedited; verified against the
eCFR section). That outcome arrives in weeks to a few months, not years, and is a structured
independent second opinion. It still covers denials only, and only those that get that far.

So the honest design is a ladder, with in-app leading indicators carrying the demo and the slow
signals confirming the North Star after launch.

## 2. The ladder: how fast can we know a first-pass decision was right?

| Speed | Signal | Covers | In the prototype? |
|---|---|---|---|
| Minutes | Nurse overrides or corrects the AI; nurse finds a fact the AI called missing | All three outcomes | Partly (override logged; corrections not yet) |
| Days | Provider reply to a pend says "already in the packet, page N" | Pends | No (provider side is simulated; reply is free text) |
| Days | Director returns an escalation as "not needed" | Escalations | Partly (return is logged, no reason) |
| Weeks | Internal over-read: a senior reviewer re-reviews a sample of decisions (existing UM practice in general; confirm with Humana) | All three | No, and would be mock data in a demo |
| Weeks to months | Plan appeals unit result; independent review entity result | Denials | No (needs Humana internal data) |
| Months to years | Grievances and complaints, CMS or OIG audit findings, post-payment recoveries (the only window on wrong approvals) | Mixed | No |
| Rare tail | Litigation | Denials | Not a metric, a tail risk |

## 3. Leading indicators (observable inside the product, near real time)

"Today" is checked against the stored data: the audit trail already has assigned, pended,
provider_reply, escalated, approved, received, analyzed and clock-alert events with timestamps.

| # | Metric | Definition | Source | Today? | Reads as |
|---|---|---|---|---|---|
| L1 | First-pass determination rate | Decided cases with zero pend cycles / decided cases | pended events | Yes | Proxy for the North Star: fast, but "no pend" is not the same as "correct" |
| L2 | RFI cycles per case | Pend events per case | pended events | Yes | Direct lever; every extra cycle is the gate failing once |
| L3 | Avoidable-pend rate (strict) | Pends where the provider replies the information was already in the packet / all pends | structured provider reply | **No** | The cleanest in-product answer to "was this pend avoidable", within days. Needs a structured reply: attached / already in packet (page) / cannot provide |
| L4 | False-missing rate | Facts the AI called missing that the nurse marks as present / facts called missing | nurse correction action | **No** | Completeness recall measured in production, at decision time |
| L5 | AI agreement and override rate | Final first action equals the recommendation / cases; split by direction (approve against a pend or escalate; pend or escalate against an approve) | recommendation vs first action | Partly | Whether the recommendation is trusted, and which way it errs |
| L6 | Uncertainty rate | Cases with a model self-disagreement flag / LLM-read cases | stored notes | Partly (uploads) | Reliability of the reader, tracked over time |
| L7 | Escalation appropriateness | Escalations the director decides / escalations (versus returned) | director action | Yes | Whether nurses escalate the right cases |
| L8 | Avoidable escalation | Escalations returned for missing information / escalations | director return reason | **No** | Gate leakage into the physician's time |
| L9 | Intake wait | Received to assigned | received and assigned events | Yes | Intake's own speed |
| L10 | Pend duration | Pended to provider reply | pended and provider_reply events | Yes | Provider friction, and the clock cost of a pend |
| L11 | Within-clock rate | Decided inside 72 h / 7 days | received, due, decided | Yes | Guardrail: already met by Humana (MA standard mean 1 day) |
| L12 | Reviewer minutes | Active time per case | active-time instrumentation | **No** | Phase 2 hypothesis only; no baseline |

**Guardrails** (watch for gaming by approving more): approval share over time, override-to-
approve rate, whether a nurse opened any citation before approving (automation bias), clock
breach rate, denial share by director.

## 4. Lagging indicators (confirm the North Star after launch)

| # | Metric | Source | Latency | Baseline we have | Limits |
|---|---|---|---|---|---|
| G1 | Appeal rate (appealed / denied) | Plan appeals unit | Weeks | Humana CY2025: MA 2.71%, Medicaid 7.19% | Most denials are never appealed |
| G2 | Overturn rate on appeal | Plan appeals unit | Weeks | Humana CY2025: MA 64.72%, Medicaid 12.65%; OIG SNF 95% (June 2024 data, reported June 2026) | Overturn can reflect new information, not a first-pass error |
| G3 | Overturn on information already in the original packet | Appeal reason code | Weeks | None public | The only version of G2 that maps to our North Star; needs a reason code Humana would have to add or already hold |
| G4 | Independent review entity outcomes | Plan and CMS data | Weeks to months | None public that I verified | Denials only |
| G5 | Grievances and complaints | Plan complaint system, CMS tracking | Months | None | Noisy, underreported |
| G6 | Audit findings (CMS or OIG) | Regulator | Years | OIG reports in the deck | Rare, sample-based |
| G7 | Post-payment recoveries on approved cases | Payment integrity | Months to years | None | The only signal on wrong approvals |
| G8 | Provider burden and abrasion | Provider survey | Annual | AMA 2025 (13 h/week; physicians surveyed) | Industry-wide, not attributable |
| G9 | Time to care and downstream utilization | Claims | Quarters | None | Confounded |
| G10 | Admin cost per case; effect on medical loss ratio | Finance | Quarters | Illustrative only | Needs real cost data |

## 5. Can we get the data? Three routes

1. **Instrument the prototype** (cheap, honest, demoable). Add events for: structured provider
   reply type (L3), nurse fact correction (L4), director return reason (L8), "opened packet
   page" (guardrail), first-open timestamp. Compute L1 to L11 from events in a small
   metrics view for a lead or director. Label seeded and demo data as demo data.
2. **Public and baseline data** (already in hand). Humana's CMS-0057-F reports give G1 and
   G2 as the baseline to beat; OIG and AMA frame the problem.
3. **Pilot design** (what we would do with Humana's data, described not built):
   - **Step 0, backtest.** Replay historical packets whose eventual outcomes are known (denials
     later overturned or upheld) through the system in shadow mode, and measure how many it would
     have pended, escalated or approved differently. This produces a North Star estimate before
     any live decision depends on it.
   - **Shadow then assist.** Run beside nurses, compare agreement (L5), then turn on.
   - **Over-read sample** for ground truth on a small slice, with confirmation from G3 and G4
     over time.

## 6. What to show in a product demo

- The North Star, its definition, and why it cannot be a live number (the ladder in section 2).
- The metric tree: North Star, the levers beneath it, guardrails, and the slow confirmers.
- The leading indicators the prototype already computes, labelled as demo data, plus the two
  new ones (L3, L4) that need only small changes.
- Baselines from Humana's own reports, and the pilot plan including the backtest.
- Not a made-up "first-pass correct" percentage.

## 7. Decisions needed

1. Build the instrumentation and a small metrics view (route 1), and drop the "mark correct"
   audit workflow from the near-term build? My recommendation: yes.
2. Define avoidable pend strictly (provider says it was already supplied) or broadly (also
   nurse corrections)? Suggest strict as the headline, broad as a secondary.
3. Is the backtest part of the pitch? It is the strongest answer to "how do you know it works".
4. Confirm with a UM practitioner that sampled over-reads of decisions are standard practice
   before claiming it on a slide.
