# PA Desk architecture documents

Everything that explains how PA Desk is built, in one place. Open the HTML pages in a browser.

## Start here
| Read this | What it is |
|---|---|
| [architecture_walkthrough.html](architecture_walkthrough.html) | The path of one case in seven steps, what is plain code and what is an AI model, the policy library lane above it, and a say-it-out-loud card for each step. |
| [inner_workings.html](inner_workings.html) | Real input and output for each step. Steps A to E: how a policy becomes rules (the NCD 20.4 run). Steps 2 to 6: one scanned packet, step by step. Includes a map from each step to its file on GitHub. |
| [PROCESS.md](PROCESS.md) | The process today (fax, manual reading) against the new process. |
| [POLICY_BUILD.md](POLICY_BUILD.md) | How a policy becomes approved rules: fetch, parse, AI draft, code checks, compare, owner approval. What is built and what is not. |

## Engineering depth
| Read this | What it is |
|---|---|
| [engineering_architecture.html](engineering_architecture.html) | The earlier engineering diagram: components, data stores, trust boundary, and the production target. |
| [PRODUCTION_DESIGN.md](PRODUCTION_DESIGN.md) | The production system design the prototype stands in for. |
| [../docs/OBSERVABILITY.md](../docs/OBSERVABILITY.md) | Honeycomb names, the two numbers to optimize (recall first, then precision), and the privacy rule. |
| [../docs/METRICS_FRAMEWORK.md](../docs/METRICS_FRAMEWORK.md) | The North Star, early signals, guardrails and eval metrics. |
| [../docs/dashboard_views.sql](../docs/dashboard_views.sql) | The executive and utilization management views as warehouse SQL. |
| [../docs/DEPLOY.md](../docs/DEPLOY.md) | Putting the app online with data that survives restarts. |

## Product notes
| Read this | What it is |
|---|---|
| [../docs/PRODUCT_FEEDBACK.md](../docs/PRODUCT_FEEDBACK.md) | The running log of product improvements, including F-008 (cited sentence on the page image) and F-009 (policy owner and library screen). |
| [../docs/DECK_NOTES.md](../docs/DECK_NOTES.md) | Notes behind the deck. |
| [../deck/journey/](../deck/journey/) | The one-slide-at-a-time decks: journey, friction, federal rules, numbers, value, evals. |

## How these pages are made
Each HTML page is generated from real data by a script in `scripts/`:
`make_architecture_walkthrough.py`, `make_inner_workings.py` (needs the trace from `trace_case.py` and a run of `build_policy.py`), and `make_architecture_page.py`.
