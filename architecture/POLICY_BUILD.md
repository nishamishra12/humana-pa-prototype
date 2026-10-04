# How a policy becomes rules

The policy is the baseline every packet is checked against, so how it gets into the system matters as much as how a packet is read.

## The steps
| Step | What | AI? | Code | Status |
|---|---|---|---|---|
| A. Fetch | Pull the official text from the CMS Coverage API (NCDs, LCDs), the eCFR (regulations), or take an uploaded PDF. Save it with its URL, version, retrieval time and a hash. | No | `pipeline/policy_build/sources.py` | Built |
| A2. Codes | Find the procedure codes (CPT and HCPCS) that go with the policy, from the CMS Billing and Coding articles. An LCD is linked to its articles by CMS. An NCD is not, so articles are matched by title and checked for the NCD number. Every code keeps the article it came from. | No | `pipeline/policy_build/codes.py` | Built |
| B. Parse | Unstructured turns it into structured elements (title, narrative text, tables, page). | AI inside Unstructured | `pipeline/policy_build/parse.py` | Built |
| C. Draft | An AI model drafts the criteria through a fixed form. Each rule carries its exact source quote, the fact it tests, the test, the provider question and a confidence. The model never sees the existing hand-written rules. | Yes | `pipeline/policy_build/draft.py` | Built |
| D. Check | Plain code checks every quote is in the policy, every number is in its quote, every fact exists (or is declared new), and lists sentences nothing covers. | No | `pipeline/policy_build/validate.py` | Built |
| E. Compare | Match the draft with the approved rules by the fact each tests. This is our own eval of the drafting step. | No | `pipeline/policy_build/compare.py` | Built (dev tool) |
| F. Approve | A policy owner reviews each rule beside its source text, edits or rejects it, and publishes a versioned library. | Person | `app/policy_admin.py`, `web/policy.js` | Built (tested locally, not by a real policy owner) |
| G. Watch | A scheduled job compares each policy's hash with the last saved one and queues changed policies for A to F. | No | `sources.changed` | Hash check built, schedule not built |

## The owner screen (step F)
Sign in as the policy owner. There are three pages.

**Policy library.** What is live, and where new policies come in.
- Each live policy shows its rule count, the services that use it and its source. "Check for updates" asks the official source whether the text changed. "Draft from source" builds a new draft.
- To add a CMS policy, the owner searches the policy list by number or title and picks one. The list is the CMS corpus (`policies/corpus/`, 345 NCDs and 969 LCDs). The back end builds and refreshes it, so the screen never types in a number from memory. A regulation is typed (42 CFR 412.3). A plan policy with no API is an uploaded PDF.

**Policies to review.** The queue of drafts, with progress ("3 of 14 rules decided") and the code-check summary.
- Open a draft: the official text sits on the left, the drafted rules on the right. Each rule shows its quote, the code-check result and the AI's confidence. "Show in the source" highlights the sentence.
- Approve, edit the number or wording, or reject. A rule that failed the code checks cannot be approved. A rule that needs a detail the packet reader does not find yet can be approved. It is saved with the policy as "waiting" and changes no case until the reader learns the detail.
- Publish: every rule decided, tick the confirm box, add an optional note. The library gets a new version.

**Which cases use this policy.** Inside a draft, the owner picks the service the policy belongs to and ticks the procedure codes that should send a packet to it. CMS's codes are listed with their source articles. A code CMS did not list can be added, but needs a written source. A code can belong to one service only. On publish, the policy joins the service's stack and the codes join its list, each with its source. The Policy library page shows every service with its codes and where each came from.

**Creating a service.** If no service fits, the owner picks "Create a new service for this policy". The AI's proposed details become the service's details, each with the question the reader will use, which the owner can edit. The service gets a name, the chosen codes with their sources, and the policy. It starts as a pilot. A new service needs its own test packets before it is trusted. The made-up demo is in `DEMO_NEW_SERVICE.md`.

**Services.** Every service with its status, codes and where each code came from, its policies, its details and the cases seen. A service is **Planned** (on the rollout list, no packet is sent to it), **Pilot** (switched on, nurses check every recommendation) or **Live**. A planned service can be added by name and code alone. Starting a pilot needs a policy with live rules, a code and the details the reader looks for. Going live needs a written note on what was tested. Every change is a library version and an audit line, so it can be reversed.

**Requests without a policy.** The open cases that arrived for a procedure no service covers, grouped by procedure code, with the number waiting and the oldest wait. This is the owner's rollout list in practice. "Add to the rollout list" opens the Services form with the code filled in. After a service is onboarded, a nurse checks each waiting case again.

**Version history.** Every library version with who published it, what changed and a "go back to this" button, plus an audit trail. The trail records each draft started, each rule approved, rejected or undone, each publish, each go-back and each update check, with who and when. Rows are only ever added.

The server side is `app/policy_admin.py`. Only the policy owner role can reach it; nurses get a 403.

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
- Every published version is kept, so a change can be rolled back (the owner screen has a revert).
- Publishing needs every rule decided (approve or reject) and a tick on "I reviewed every rule". A rule that failed a code check, or needs a fact the reader cannot find yet, cannot be approved.
- A new policy that no service lists does not change any case. Attaching it to a service is a separate step.
- Live library changes apply to new cases only. Cases that already have a recommendation keep it.
