# Solution slides

One slide per file, one click per step, nothing plays by itself. Import each into Google Slides with File, Import slides. The talking points for each click are in the speaker notes.

Order after the problem slides (deck/journey slides 2 to 6):
| # | File | What it shows |
|---|---|---|
| 7 | `Two_Parts.pptx` | The product has two parts: build the policy library, then read every packet with it |
| 8 | `Part1_Policy_Library.pptx` | Part 1 step by step, ending in "what we get" |
| 9 | `Service_Link.pptx` | What a service is, and how it ties codes, policies and details together |
| 10 | `Part2_Packet_Journey.pptx` | Part 2: a packet from upload to a recommendation, including the "no policy yet" branch |
| 11 | `Product_Flow.pptx` | The flow today against the flow with PA Desk |
| 12 | `Prototype_Walkthrough.pptx` | Each persona, Honeycomb, and the live operations dashboard |
| 13 | `Metrics.pptx` | North star, early signals, guardrails, AI metrics |
| 14 | `Evals_Current.pptx` | The evals, with the numbers from docs/eval_scorecard.html |
| 15 | `Not_Built_Member_Status.pptx` | The member status view we chose not to build, and why |

Build one: `node build_part1.js` (needs `pptxgenjs` and `jszip`). Shared code is in `kit.js`. `preview/` holds a static HTML layout check for each slide.
Refresh `Evals_Current` after the live packets are run: the numbers are in `build_evals2.js`.
