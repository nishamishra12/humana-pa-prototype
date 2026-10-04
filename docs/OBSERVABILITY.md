# Observability: names and metrics

One Honeycomb board: **PA Desk: AI quality, speed and cost**. This page says what the names mean, so the board can be read cold.

## The two numbers

| Plain name | What it answers | Target | Data name |
|---|---|---|---|
| **Missed risk rate** | Of the cases that needed a person, how many did the AI approve anyway? | 0% | 1 minus recall of "needs a person" |
| **Extra review rate** | Of the clean cases, how many did the AI send for review? | As low as possible, second | 1 minus approve recall |

Optimize the first one first. A wrong approval is silent and can hurt a patient. An extra review costs a nurse a few minutes.
The nurse sees every case. A flagged case forces her to look. An approved case may not get a second look.

"Needs a person" means the right answer was pend, escalate or verify. "Clean" means the right answer was approve.

## The four outcomes (`eval.class`, `human.class`, `truth.class`)

| Code | Meaning | What it costs |
|---|---|---|
| TP | Needed a person, AI flagged it | Nothing. This is the system working. |
| FN | Needed a person, AI approved it | **Wrong approval. The dangerous one.** |
| FP | Clean, AI flagged it | Extra review: nurse time. |
| TN | Clean, AI approved it | Nothing. Time saved. |

## Other board panels

- **Facts found when they were there**: of the facts really in the packet, how many the AI found with the right value.
- **Facts claimed that were not there**: of the facts absent or ruled out, how many the AI claimed anyway. Target 0.
- **Facts sent to the nurse as "not sure"**: share the AI would not guess. Safe, costs nurse time.
- **Time per step** and **AI tokens per step**: speed and cost. Tokens times the model price is cost per case.

## Naming rules

- **Spans** are `<stage>.<action>`: `ingest.read_pages`, `extract.reads`, `extract.read`, `evidence.verify_meaning`, `rules.analyze`, `pa.analyze_packet`.
- **Attributes** use a short prefix that says who or what they describe:
  - `eval.*` a test run (run id, packet, category, class)
  - `case.*` a live case
  - `ai.*` what the AI recommended
  - `human.*` what a person decided
  - `truth.*` the known right answer for a test packet
  - Version tags on every trace: `app.version`, `policy.library_version`, `extract.model`, `verify.model`, `extract.prompt_hash`
- Names are plain English words, lowercase, dots between parts.

## Privacy rule

No names, dates of birth, member ids, packet text, quotes or free-text notes go to Honeycomb. Only made-up case ids, counts, codes, statuses, versions, timings and token counts. The code that sends events is `pipeline/telemetry.py`.

## To test with people in the UI

Save the right answers as `evals/live_truth.json`, for example `{"adv_041.pdf": "pend"}`. The app then records the AI's own class against the key (`truth.class`) and the nurse's decision against both (`human.class`, `truth.human_was_right`).

## Naming a run

Give every test run a human name, so the board reads in plain words:

    python scripts/run_evals.py --adversarial --label "Run 6: what changed"

The board shows this name in the first column of every history table. A run with no label shows as "Run" plus its id.

## How the board is laid out

- **Top = right now.** Current recall, current precision, speed (p50, p95, p99), estimated cost per case, errors. Each uses the latest run only.
- **Middle = live app.** Nurse and director decisions, once cases are decided in the app.
- **Bottom = history.** Every run, then every packet in every run, with a link to the trace.

## Known Honeycomb quirks

- Tables and cards add an **OTHER** and a **TOTAL** row. For a rate (recall, precision) the TOTAL row adds the rates of every group together, so it is meaningless (for example 3.96). Ignore it. Cards that show one number have no breakdown, so they are clean.
- The "Right now" cards use a start time (the start of the latest run), so they cover that run only. After a new run, the start time is moved to the new run.
