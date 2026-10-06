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
The elements JSON from the Unstructured API now goes to the AI. This is a different AI job from Part 1. In Part 1, the AI read a policy and drafted the rules. Here it reads a patient's packet and fills in the values. So the prompt is different, the output form is different, and the checks are different.

The AI is Claude Sonnet. It has two kinds of guardrails.

**Guardrail one: the output dictionary.** The AI has to answer through a fixed form. The keys of that form are the key facts we built in Part 1 for this service. If the service has more than one policy, the keys are the list of unique key facts across those policies. If two policies both need length of stay, it appears once.

For each key fact, the AI fills in four things:
- the status: found, none, implied or missing
- the value: a number, a choice, a list or text, depending on the key fact
- the evidence: the exact sentences from the packet, up to three, with their dates
- a note, if the packet contradicts itself

It also sees the question and the rule text for each key fact, so it knows what the value is for. And it can only use the statuses that key fact allows. So it can't wander off and report things we never asked for.

**Guardrail two: the prompt.** There are eight rules. I'll name them.
1. Negation. If the packet rules something out, like "no evidence of instability", that is none, never found.
2. Conflicts. If the packet says the same thing twice with different values, the later, dated or more specific one wins.
3. Quotes. For every fact it reports, it copies the exact sentence, word for word.
4. Never guess. If a value isn't written, it doesn't make one up. It doesn't calculate one either, like a BMI from height and weight.
5. This patient only. A page about someone else is not evidence. We give it the member's name and date of birth so it can tell.
6. Planned is not done. A scheduled visit hasn't happened. Only what was done counts.
7. Ambiguous is rare. It can only use it when it truly can't choose between two values.
8. Dates. The AI reads the dates. Our code does the counting.

**It runs three times, in parallel.** Why? A language model can answer differently each time you ask. A fact that comes back the same three times, I can trust. A fact that changes between runs is a warning sign. And running them in parallel means it isn't three times slower.

**What happens if one of the three finds a wrong item?** All three have to agree on the status and on the value. Numbers must match. Choices must match. For free text and lists, the status must match, and the evidence gets checked next.

If one run disagrees, we don't take a majority vote. We mark that key fact unsure, and we tell the nurse: we read this more than once and got different answers, please check the packet. I would rather send one doubtful fact to a nurse than let one lucky read decide a case. That is the recall-first design. It costs the nurse a little time, and it protects the member.

**What if all three are wrong in the same way?** That is why there is a second layer. The validator.

**The validator is different from Part 1.** In Part 1, the validator checked the AI's rules against the policy text. Here it checks the AI's answers against the packet. It does that in three steps.
1. Agreement, which we just covered.
2. The evidence matcher. It is code. It finds each quote in the packet. Exact match first. Then fuzzy matching, and a fuzzy match must carry the same numbers. It gives us the page and the real text. If the quote isn't in the packet at all, the AI made it up, and the fact goes to unsure. The nurse sees the packet's words, never the AI's version.
3. The meaning check. A second, smaller model, Claude Haiku, reads the quote in its page and says one of four things: it supports the fact, it contradicts it, it is unrelated, or it isn't enough. If every sentence contradicts or is unrelated, the fact goes to unsure. If it supports, the fact gets a tick. This catches a quote like "no evidence of instability" being used as evidence of instability. If this check ever fails to run, we keep the exact-text result. We never block a case because the checker was down.

Two safety nets on top. If the AI's reply is unreadable, we retry that read once. If the AI can't be reached at all, every key fact is marked unsure, so a person reads the packet. Nothing is guessed.

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
