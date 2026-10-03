# Metrics: North Star, leading, lagging, health

2026-10-03, second version. The first version listed 12 leading and 10 lagging indicators;
that is a catalog, not a strategy, and it is in git history (commit 95e24f9). This version
commits to one North Star, four leading indicators that form one composite, four lagging
indicators, and four health metrics. Method follows the EnergySage lead-quality work: a
year-horizon outcome, early behaviors that predict it, a composite so no single ratio decides,
and lagging results that confirm it later.

## North Star: Right-First-Time rate

Share of prior authorization requests whose first determination did not need rework: no
avoidable pend, no return from the medical director for missing information, and, for denials,
no overturn on information that was already in the original packet.

- It is the outcome all four parties want: the member gets care sooner, the provider does not
  resubmit, the plan does not pay for review, appeal and reversal, the regulator sees fewer
  wrongful denials.
- It is a year-horizon goal, reviewed quarterly. It is not a number a demo can show live,
  because "needed rework" is only fully known weeks to months later.
- Target: set after a baseline in the first 60 days of a pilot. Stated ambition (mine, not
  data): halve avoidable rework in year one.

Why not the alternatives. Within the CMS clock: Humana already meets it (MA standard mean 1
day, CY2025), so it cannot move. Reviewer minutes saved: an efficiency number that can be won by
reading less. Approval rate: gameable by approving more. Overturn rate on its own: sees only
denials, and an overturn can come from new information.

## Leading indicators: one per handoff, combined into one composite

A case passes through four handoffs. Each gets exactly one early signal, observable within
days inside the product, the same way post-registration behaviors predicted lead quality.

| # | Handoff | Leading indicator | Reads as |
|---|---|---|---|
| 1 | Gate to provider | **Pend precision**: pends where the provider supplied something new / all pends (the opposite: provider replies "already in the packet, page N") | Was the question worth asking |
| 2 | Provider loop | **One-cycle resolution**: pended cases settled in a single provider reply / pended cases | Did the question get answered cleanly |
| 3 | AI to nurse | **Assist acceptance**: cases where the nurse took the recommendation with no fact corrected / cases | Did the reading and recommendation hold up |
| 4 | Nurse to director | **Escalation precision**: escalations the director decides / escalations (versus returns as unnecessary or incomplete) | Did the right cases reach a physician |

**Composite: Clean-First-Pass index.** Share of decided cases with no failure at any checkpoint
they reached (pend not avoidable, resolved in one cycle, nothing corrected, escalation upheld).
It is a case-level pass, not an average of four rates, so one indicator rising while another
falls cannot hide: a case either went through clean or it did not. The four components stay
visible for diagnosis. We do not rank users or cases; the question is whether the index is
higher this quarter than the pre-launch baseline.

## Lagging indicators: confirm the North Star (3 to 12 months)

| # | Indicator | Why it confirms | Baseline we have |
|---|---|---|---|
| 1 | **Overturn on information already in the original packet** (plan appeals reason code) | The direct lag of the North Star for denials | None public. Overall MA overturn is 64.72% (Humana CY2025), but it mixes new information with first-pass error |
| 2 | **Independent review entity overturn on plan-upheld denials** | Structured outside check, weeks to months (42 CFR 422.590 forwarding) | None public that I verified |
| 3 | **Provider PA experience** (survey plus repeat-submission rate) | The provider side of rework; the EnergySage installer-churn equivalent | AMA 2025 frames it (13 h/week), industry-wide not Humana-specific |
| 4 | **Cost per determination**, including review, pend, appeal and reversal | The plan's reason to fund it | Illustrative only; needs real cost data |

## Health metrics (guardrails: must not get worse)

| # | Metric | Guards against | Standing |
|---|---|---|---|
| 1 | **CMS clock compliance** (72 h expedited, 7 days standard) | Speed bought at the cost of the clock | Humana already meets it; hold the line |
| 2 | **Approval-share drift** vs baseline, plus post-payment error rate on approvals once available | Winning the North Star by approving more | MA standard denial 6.86% weighted (CY2025) is the reference |
| 3 | **Citation check before approve** (nurse opened a cited page) | Automation bias: accepting the recommendation without reading | New event |
| 4 | **Zero AI denials; rationale on 100% of denials** | The legal and ethical line | Already enforced in the product |

## Can the prototype show this?

| Item | Today | To build |
|---|---|---|
| Leading 1 pend precision | No | Structured provider reply: attached / already in packet (page) / cannot provide |
| Leading 2 one-cycle resolution | Yes | Pend events already logged |
| Leading 3 assist acceptance | Partly | Nurse action "this fact is present" on an AI-missing fact; recommendation vs first action |
| Leading 4 escalation precision | Partly | Director return reason |
| Composite | After the above | A small leading-indicators view, labelled demo data |
| Health 1 and 4 | Yes | Display only |
| Health 3 | No | Log "opened packet page" |
| North Star, lagging 1 to 4 | No | Described, with Humana baselines where they exist |

Four small events (provider reply type, nurse fact correction, director return reason, packet
page opened) unlock the whole leading and health set.

## How we would know the leading set is the right one

The leading indicators are a hypothesis until they predict the lagging ones. In the pilot:
compare cohorts of cases by composite pass or fail against later appeal and review-entity
outcomes, and keep a leading indicator only if it separates them. Step zero, before any live
use: replay historical packets with known outcomes through the system in shadow mode and
measure how often it would have caught the rework. EnergySage precedent: the leading
indicators moved first and moved together; the lagging result confirmed it months later.

## Decisions needed

1. Accept Right-First-Time as the North Star wording and the four-handoff leading set?
2. Build the four events and the small leading-indicators view next?
3. Keep the shadow-mode backtest as the first pilot step in the pitch?
4. Confirm lagging 1 is obtainable: does Humana's appeals unit record why an appeal was
   overturned? If not, say so in the pitch and treat it as a data request.
