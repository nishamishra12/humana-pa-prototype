# PA Desk: UX critique, by workflow

2026-10-03. A flow-first review, not a style review. Method: walked the running app as each of
the three personas at 1440x900, measured what the flow costs, and checked the code behind
anything suspicious. Items already in docs/PRODUCT_FEEDBACK.md (F-001 to F-007) are referenced,
not repeated. Not covered: mobile or small screens, accessibility, real-user testing. Findings
marked (measured) or (proven) were checked directly; the rest are judgment.

## Overall impression

The core idea works and reads clearly: one recommendation, one reason, evidence with page
citations, and a single drafted question when something is missing. The three role views are
correctly separated, permissions are enforced, and the clock is visible. The weak point is not
how it looks. It is that each person works in isolation. Work moves between people (intake to
nurse, nurse to provider, nurse to director, director back to nurse) and almost none of those
handoffs tell the receiver anything. Inside a single case, the page makes the nurse hunt for
the two things she needs together: the evidence and the action.

## The journey, and where it breaks

| Step | Who | What the product does | Break |
|---|---|---|---|
| Upload and route | Intake | Case lands unassigned; admin picks a nurse | Nurse is not told (proven: 0 notifications on assignment). No workload view to choose well (F-002, F-003). |
| Pick up work | Nurse | "Needs my review" list | Not ordered by urgency (measured, below). |
| Review | Nurse | Recommendation, facts, criteria, citations | Evidence and action are two screens apart (measured). |
| Pend | Nurse | One drafted question to the provider | Drafted even when the model was merely unsure (proven, below). |
| Provider replies | Provider | Simulated, re-runs the analysis | Nurse is not told the case is back (proven). |
| Escalate | Nurse | Tags a director with a note | Works, and the director is notified. The note is then hard to find (below). |
| Decide | Director | Approve, deny with rationale, or return | Nurse is not told the outcome of her own escalated case (proven). |

## Findings, most important first

### 1. Handoffs are silent (critical, proven)
Three of seven handoffs notify no one: intake assigning a case, the provider replying to a
pend, and a director deciding an escalated case. Tested on a throwaway database: Maria's
notifications stayed at 0 after all three. Only @mentions, escalation to a director, a
director returning a case, and clock alerts notify today.
Impact: a nurse learns a case is hers, or is back, or was decided, only if she happens to open
the right queue. With a 7-day clock that keeps running during a pend, silence is the failure
mode that causes breaches.
Fix: treat each handoff as an event with a receiver. Notify on assignment, provider reply,
and final decision. Show "new" and "back from provider" markers on the case in the list.

### 2. The nurse's queue is not ordered by what is urgent (critical, measured)
Maria's "Needs my review" lists newest first. Her breached case (Theresa Nakamura, overdue)
is fifth of five, below a case with 6 days left. A case due in under 6 hours (expedited) is
fourth. The "At risk" queue exists but is a second place to look.
Fix: default order by time remaining, expedited first, breached pinned at the top. One queue
should answer "what do I do next".

### 2b. The nurse works a queue but the product treats each case as a one-off (moderate)
After approving, pending or escalating, the screen stays on the finished case. There is no
"next case". Throughput depends on re-selecting from the list every time.

### 3. Evidence and action are in different places (critical, measured)
The decision buttons sit 1,684 px down a page that is 848 px tall: about two full screens of
scrolling below the recommendation. Clicking a citation switches to the Packet tab and, when
she returns, the Review tab is back at the top (scroll position 800 before, 0 after).
Impact: the loop "check the evidence, decide, act" repeatedly loses her place.
Fix: a decision workspace. Evidence on one side, the packet page that a citation opens beside
it (not instead of it), and the action controls always in view. This is the single biggest
change for the nurse's day.

### 4. "The model is unsure" is shown as "the provider didn't send it" (critical, proven)
The self-consistency check marks a fact missing when the model disagrees with itself, with a
note saying so. The screen shows "Not in packet" and hides the note. The engine then drafts a
question to the provider asking for information that may already be in the packet. Tested: a
disagreement-flagged imaging fact produced a drafted provider question about imaging.
Impact: this breaks the product's central promise (a pend is one specific, correct question)
and can send providers pointless requests, which is the exact friction we are selling against.
The deck also says "uncertain" is a first-class state; the product does not show it.
Fix: a distinct third state, "Couldn't confirm, please read the packet", shown with its
reason and a link to the likely page. It must not draft a provider question until the nurse
confirms the fact is truly absent.

### 5. The director's decision lacks its own context (critical)
The nurse's note to the director ("packet is complete but the stay is 1 midnight... can you
make the call?") lives only on the Activity tab; it is not on the Review tab where the
director decides (proven: absent from the Review tab). The director lands on the nurse-style
page with the AI recommendation first.
Fix: the director's case view leads with the question being asked and who asked, then the
evidence, then approve / deny / return.

### 6. Role fit: navigation shows things that do not belong (moderate)
- Director nav: "Needs my review" is always 0 for a director, "At risk" shows other people's
  cases, and the default view is labelled "All mine" (it is "Escalated to me").
- "Upload packet" is visible to directors (and nurses), though intake owns that step.
- "Evals" is in everyone's operational nav; it is an engineering and QA page.
Fix: build each role's home around its job (director: decisions waiting for me; nurse: my
next case; intake: unassigned and workload). Move Evals out of the operational nav.

### 7. Waiting states and errors say too little (moderate)
- A pended case shows time left on the clock but not "waiting on provider since", and the
  CMS clock does not stop for a pend. No reminder or nudge on stale pends. (F-001 covers the
  upload wait only.)
- Opening another nurse's case by link shows a blank "Select a case to review." with no
  explanation. A server restart returns the user to sign-in with no message.

### 8. The product records the process but not the quality signals (revised)
Original version of this finding proposed an in-app "mark this decision correct" workflow.
That was wrong for a demo: "correct" is a lagging fact and would be mock data. See
docs/METRICS_FRAMEWORK.md. What remains true: the audit trail already supports several leading
indicators (first-pass rate, RFI cycles per case, pend duration, escalation outcomes) but no
screen shows them, and two of the best near-term signals are not captured at all: a
structured provider reply ("already in the packet, page N") and a nurse correction when the AI
called a fact missing that was present.
Fix: four small events (structured provider reply, nurse fact correction, director return
reason, packet page opened) and a small leading-indicators view, labelled as demo data. The
metric set itself is in docs/METRICS_FRAMEWORK.md.

### 9. Missing for real work, by design for now
Provider-facing side of the pend loop (replies are simulated); member view (deliberately
deferred, D-003); reassignment when a nurse is out; any reporting for the CMS annual metrics.
Named so they are chosen, not discovered.

## What works well
- Recommendation plus plain-language rationale first, with the one-click jump to the quoted
  page. Nurses can verify rather than trust.
- Override of the recommendation requires a reason; denial requires a rationale.
- Server-enforced roles, with clear messages when a role cannot do something.
- Clock and SLA state on every row and a breach banner on the case.
- Case export and an append-only activity trail.

## What this changes about the redesign

Do the flow fixes before the visual pass, because a nicer-looking version of these screens
would still lose the nurse's place and still send the wrong provider questions.

1. Notifications and "back from provider" markers for every handoff (finding 1).
2. Urgency-ordered queues and a "next case" action (2, 2b).
3. A decision workspace: evidence beside packet page beside actions (3).
4. A real "unsure" state that does not auto-generate a provider question (4).
5. Role-built homes: director leads with the question, intake gets workload, Evals moved out
   (5, 6, F-002, F-003).
6. Then the visual system, profile menu, search and the staged upload progress (F-001,
   F-004, F-005, F-006).
7. A small leading-indicators view, plus the four small events (8), once the flow is stable.

Rough size, my estimate: 1 and 2 small; 4 small to medium (touches the engine, the extractor
note and the screen); 3 and 5 medium (they restructure the case page); 8 small to medium.
