# Metrics for the demo

Short version. One North Star, three early signals, two long-term checks, and a few eval
metrics for the AI. Plain English on purpose.

## North Star: Right-First-Time rate

**What it means.** Out of every 100 requests, how many get the right answer the first time,
with no back and forth?

**How we count it.** Cases with no rework, divided by all decided cases. A case has rework when:
- The nurse asks the provider for something they already sent.
- The director sends the case back to the nurse.
- Someone overturns a denial because we missed information that was in the packet.

**Why this one.**
- The provider does not send things twice.
- The patient gets care sooner.
- The nurse does less work.
- Humana pays for fewer appeals.

**What it is worth.** Humana had about 9.5 million standard MA requests in 2025 (from its own
report). One point of Right-First-Time means 95,000 fewer requests come back. If each one costs
$50, Humana saves about $4.8 million a year. The $50 is my guess. Humana has the real number.

**We cannot show it live.** We only know the full answer months later. In the demo we show the
early signals instead.

## Early signals (we see them in days)

| Signal | What it means | Better when |
|---|---|---|
| First-review rate | Cases decided on the first review, with no pend | Higher |
| Avoidable pend rate | Pends where the provider says "I already sent that" | Lower |
| Avoidable escalation rate | Escalations the director sends back to the nurse | Lower |

**Clean case rate** (the combined signal). Cases with none of the three problems. We compare it
to the rate before launch. We do not rank nurses or cases.

## Long-term checks (we watch these for six months)

| Check | What it means |
|---|---|
| Overturned because the info was in the packet | Someone appeals a denial and wins. We count the wins where the packet already had the answer. Humana's public data does not show why appeals win, so we would ask Humana for this. |
| Cost per decision | Total money spent on the case, divided by decided cases. We want it to drop. |

Humana's public number for context: 64.72% of appealed MA denials were overturned in 2025.
That number mixes new information with our kind of mistake, so we do not use it as our check.

## Guardrails (so we do not cheat)

- **Time limit.** Humana already decides inside the CMS time limit. We must not slow it down.
- **Approvals.** If the share of approvals jumps, we may be approving too much to look good.
- **No AI denials.** The AI never denies. A director denies, and writes the reason.

## Eval metrics (is the AI doing its job)

| Metric | What it means | Where we are |
|---|---|---|
| Finds facts that are there | Of the facts in the packet, how many the AI finds | 15 of 15 on our hard test set. The set is small (4 packets). |
| Makes up facts | How often the AI says a fact is there when it is not | 0 of 3 on the same set |
| Changes its mind | How often the 3 AI reads disagree on a fact. Lower is better. | Not measured as a rate yet. We saw it happen in testing. |
| Nurse agrees | How often the nurse takes the AI's recommendation | Needs a small change to measure |
| Speed | Seconds to read one packet | About 27 seconds in testing |

## What the demo can show today

| Item | Can we show it? |
|---|---|
| First-review rate | Yes. The case history has it. |
| Avoidable pend rate | After one change: the provider reply needs a type ("sent new info" or "already sent") |
| Avoidable escalation rate | After one change: the director gives a reason when sending a case back |
| Eval metrics | Mostly yes. The Evals page shows facts found and made up. "Nurse agrees" needs one more button. |
| North Star and long-term checks | No. We show the meaning and Humana's public numbers. |

## Three small changes to build

1. Provider reply type.
2. Director reason when sending a case back.
3. A nurse button: "this fact is in the packet" (when the AI said it was missing).

## One open question

Does Humana record why an appeal wins? If not, the first long-term check needs a data request.
We say that in the pitch.
