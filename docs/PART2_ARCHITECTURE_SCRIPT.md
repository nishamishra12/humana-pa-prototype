# Part 2 architecture: speaker script

In my own voice. Plain, active sentences. For the one-page Part 2 architecture slide.

## What Part 2 is
Part 1 gave us the library. Part 2 is what happens every time a request comes in. A packet arrives, and the system helps the nurse decide.

Quick reminder. For each service, the library has a list of key facts, with a rule attached to each one. Part 2 checks every incoming packet against that list. The AI reads. Code checks. A person decides.

## Stage 1: intake and read
The provider sends the packet by fax or portal. The intake coordinator uploads it as one PDF and assigns it to a nurse. They can see each nurse's workload, so they pick the nurse with room.

The first thing the app does is the same ETL step we saw in Part 1. The PDF goes through the Unstructured API. It reads every page and gives back elements as JSON. Each element keeps its text and its page number. That page number is how a nurse later sees "page 6 of 14".

Then we find the billing code. Plain pattern matching finds the code on the request. We look that code up in the library to find the service that owns it. This is why we collected the billing codes in Part 1. The code is the doorway. It sends the packet to the right service.

If no service owns the code, the system doesn't guess. It says "no policy yet". That request shows up on the policy owner's list as the next service to build.

When a service is found, we pull its key facts and the rules attached to them from the library.

## Stage 2: the AI reads the packet and checks its own work
Now the AI part. Claude Sonnet reads the packet. It has a prompt and a fixed output form. The form is built from that service's key facts. So the AI fills in one entry per key fact. It does not go looking for anything else.

The prompt has guardrails, same idea as Part 1:
- Be literal and conservative.
- Negation counts. "No evidence of instability" means absent, not found.
- If the packet says the same thing twice with different values, the later, dated one wins.
- Copy the exact sentence word for word.
- Never guess a value that isn't written.
- This patient only. A page about someone else is not evidence.
- Planned is not done. A scheduled visit hasn't happened.
- For dates, the AI reads them and our code does the counting.

It reads the packet three times, in parallel. All three reads must agree on the status and on the value. If they don't, we don't take a majority vote. We mark that fact unsure and the nurse checks it. I did this because a language model can answer differently on each run, and I don't want one lucky read to decide a case.

Then we check its work, in two steps.
- **Step one is code.** For each key fact, it finds the exact quote in the packet. It tries an exact match first, then fuzzy matching with the same numbers. It gives us the page and the real text from the packet. So the nurse sees what the packet says, not the AI's version.
- **Step two is a second, smaller model, Claude Haiku.** It reads the quote in its page and says whether it supports the fact, contradicts it, is unrelated, or isn't enough. This catches a quote like "no evidence of instability" being used as evidence of instability. If this check ever fails to run, we keep the exact-text result. We never block a case because the checker was down.

## Stage 3: decide
Now the rules engine. This is code, not AI. For each rule, it looks at the key fact and says met, not met, missing, or unsure. Then it picks the next step:
- If a key fact is unsure, it says verify. The nurse confirms it before anything else.
- If a key fact is missing, it says pend. And here is the question from Part 1. The system tells the nurse this was required for the policy and it is missing. She sends the provider that exact question.
- If everything is there but a rule isn't met, it escalates to a medical director.
- If everything is there and every rule is met, it recommends approve.

It never denies.

The nurse sees a checklist with the evidence beside each item. She isn't hunting through fourteen pages. She can follow the recommendation or override it, and an override is recorded. If she pends, the provider's reply comes in, the packet is read again, and it comes back to her.

The medical director gets the escalated cases, with the evidence and the nurse's note attached. They approve, send it back with a reason, or deny with a written reason. They are the only role that can deny.

Everything is saved in the case database: the cases, the evidence, the comments and the audit trail. A live dashboard shows intake and the directors what is happening. And every step is traced so we can open a wrong answer and read it step by step.

That is Part 2. The AI reads, finds the evidence and recommends. A person decides.

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
