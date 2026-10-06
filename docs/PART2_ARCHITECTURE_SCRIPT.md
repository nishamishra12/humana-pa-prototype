# Part 2 architecture: speaker script

In my own voice. Plain, active sentences. For the one-page Part 2 architecture slide.

## Part 2 starts with the packet
Part 2 runs every time a request comes in. The provider sends a packet. The intake coordinator uploads it as one PDF and assigns a nurse.

Our system gets that API call and runs the packet through a pipeline very similar to Part 1. In Part 1, a policy goes in and key facts with rules come out. In Part 2, a packet goes in and the values for those key facts come out, each with evidence.

## Stage 1: parse and find the service
Same ETL. The PDF goes through the Unstructured API. Its partitioner extracts the elements, with text and page number, as JSON.

Then plain pattern matching finds the billing code, and we look it up in the library to find the service. That is why we collected codes in Part 1. No service means "no policy yet". We never guess.

## Stage 2: the AI and the validator
The JSON goes to Claude Sonnet. This is a different job from Part 1. It reads a patient's packet and fills in values.

It has two guardrails. First, the output dictionary. The keys are the key facts from Part 1. If the service has several policies, it is the unique key facts across them. For each key, it fills in the status, the value, the exact quotes and a note. Second, eight prompt rules: negation, conflicts, exact quotes, never guess, this patient only, planned is not done, ambiguous is rare, and dates. The AI reads the dates. Our code counts them.

It runs three times, in parallel, because a model can answer differently each time. All three must agree on status and value. If one differs, there is no majority vote. The fact is marked unsure, and the nurse checks it.

If all three are wrong the same way, the validator catches it. It checks the answers against the packet. Code finds each quote, exact first, then fuzzy with the same numbers. A quote that isn't in the packet goes to unsure. Then Claude Haiku checks that the quote really supports the fact.

## Stage 3: decide
The rules engine is code. Unsure means verify. Missing means pend, with the exact question from Part 1. A rule not met means escalate. All met means approve. It never denies.

The nurse sees the evidence beside each item and decides. The director decides escalations, and is the only one who can deny.

That is Part 2. The AI reads and recommends. A person decides.

## Endpoints
- `POST /api/cases` upload a packet, then `GET /api/jobs/{job}` to watch progress
- `POST /api/cases/{id}/assign` assign a nurse
- `GET /api/cases/{id}` open a case with its checklist and evidence
- `POST /api/cases/{id}/facts/{key}` the nurse corrects a key fact
- `POST /api/cases/{id}/action` approve, pend, escalate, deny, return
- `POST /api/cases/{id}/addendum` the provider's reply
- `POST /api/cases/{id}/recheck` read it again with the current policies
- `GET /api/dashboard` live numbers

## Check before you say it
- The rules engine runs the rules in the library, but one lumbar fusion rule is written in code (`pipeline/engine.py`, deformity needs 12 months of non-operative treatment). If someone asks if it is fully generic, say that rule is still hardcoded and moves into the library next.
- When a provider replies, the packet is read again with one read, not three.
- If the AI reader is not available, every key fact is marked unsure, so a person reads the packet. Nothing is guessed.
