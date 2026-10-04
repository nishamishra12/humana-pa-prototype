# How a policy becomes rules

The policy is the baseline every packet is checked against, so how it gets into the system matters as much as how a packet is read.

## The steps
| Step | What | AI? | Code | Status |
|---|---|---|---|---|
| A. Fetch | Pull the official text from the CMS Coverage API (NCDs, LCDs), the eCFR (regulations), or take an uploaded PDF. Save it with its URL, version, retrieval time and a hash. | No | `pipeline/policy_build/sources.py` | Built |
| B. Parse | Unstructured turns it into structured elements (title, narrative text, tables, page). | AI inside Unstructured | `pipeline/policy_build/parse.py` | Built |
| C. Draft | An AI model drafts the criteria through a fixed form. Each rule carries its exact source quote, the fact it tests, the test, the provider question and a confidence. The model never sees the existing hand-written rules. | Yes | `pipeline/policy_build/draft.py` | Built |
| D. Check | Plain code checks every quote is in the policy, every number is in its quote, every fact exists (or is declared new), and lists sentences nothing covers. | No | `pipeline/policy_build/validate.py` | Built |
| E. Compare | Match the draft with the approved rules by the fact each tests. This is our own eval of the drafting step. | No | `pipeline/policy_build/compare.py` | Built (dev tool) |
| F. Approve | A policy owner reviews each rule beside its source text, edits or rejects it, and publishes a versioned library. | Person | policy admin screen | In progress |
| G. Watch | A scheduled job compares each policy's hash with the last saved one and queues changed policies for A to F. | No | `sources.changed` | Hash check built, schedule not built |

## Where things live
- Run one policy: `PYTHONPATH=. python scripts/build_policy.py ncd 20.4` (also `lcd L37848`, `cfr 42 412 412.3`).
- Every run is saved in `policies/work/<policy>/<version>/`: source, elements, draft, checks, comparison.
- The library the engine uses: `policies/policy_library.json`.

## Results so far (five policies)
Fifteen of seventeen hand-written approved rules were reproduced exactly, one differed and one was missed. A policy never modeled (CPAP, NCD 240.4) drafted 13 rules and proposed 10 new facts, all flagged for review. The instructions were tuned after seeing the bariatric result, so treat the numbers as a consistency check, not independent accuracy.

## Rules of the road
- The AI drafts. It never publishes.
- A threshold the policy did not state is rejected.
- A rule needing a fact the packet reader does not find yet is marked "needs a new fact" and cannot be published until the fact exists.
- Every published version is kept, so a change can be rolled back.
