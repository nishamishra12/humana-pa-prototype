# The process today and the new process

Source: the Humana case brief (Use Case 1) and the journey and friction decks in `deck/journey/`.

## Today
1. A provider faxes or portals a packet (often 14 pages of mixed documents) to ask for approval before a service.
2. Intake receives it and checks it is complete.
3. A UM nurse opens every page by hand, finds the facts, and matches them to policy (the order is regulation, NCD, LCD, Humana policy, MCG).
4. If a fact is missing, the nurse pends the case and the provider and the plan trade faxes. Admission dates are at risk while they do.
5. Hard cases go to a medical director. Only a medical director denies.
6. Results vary from reviewer to reviewer, and clear-cut cases take almost as long as hard ones because the reading is the same.

## New process
1. The packet is uploaded. Unstructured turns it into structured, page-cited elements (this includes OCR for scans).
2. Code reads the CPT code and picks the policy stack from the library.
3. The reader (an AI model) fills a fixed fact form three times from the packet. Disagreement becomes "not sure".
4. Each quote is found on the real page by code, then read by a second AI for meaning.
5. A rules engine compares the verified facts with each criterion and recommends approve, pend, escalate or verify. It never denies.
6. The nurse sees the checklist with each fact beside its page and confirms or fixes it. A missing fact becomes one specific question to the provider.
7. A medical director decides escalated cases. Every action is logged.

## What did not change
A person decides every case. The AI recommends and shows its evidence.

## What is new around it
- A policy library built through a controlled process, approved by a policy owner on the Policy library screen (see POLICY_BUILD.md).
- Traces and evals in Honeycomb, and an executive and utilization management dashboard.
