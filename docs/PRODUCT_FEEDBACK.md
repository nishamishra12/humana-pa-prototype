# Product feedback log

Running list from hands-on testing. Each entry: what was observed, what to do, and when.
Status: `open` (not started), `done`. Phase: `UX` = the planned UI/UX/flow pass after testing.

## F-001 -- Upload wait should show what is actually happening (UX, open)
2026-10-03, from testing the Admin upload (A2).

Observed: after clicking Upload, the generic "Analyzing packet... (Ns)" banner is fine for now,
but a 25-30 second wait with one static message feels long.

Wanted: during the UX pass, replace the single banner with an animated, staged view of the real
work -- breaking the packet into pages, then moving through the next steps -- so the wait feels
less like dead time.

Design constraints so the animation stays honest (it should show what really runs, not a
story):
- The real stages today, with measured timing: (1) parse the PDF into page-tagged elements via
  Unstructured, about 17s; (2) read the six clinical facts, three model reads run in parallel
  and cross-checked, about 10s; (3) check the facts against the curated policy criteria, a
  deterministic lookup, instant; (4) produce the recommendation and checklist, instant.
- "RAG" is not one of those stages for lumbar fusion: the policy comes from a curated table, not
  retrieval. Retrieval over the full CMS corpus only runs in the no-curated-policy fallback.
  Label stages with what happens; show a retrieval step only when it actually runs.
- Needs real progress from the server (server-sent events or polling a job status), not a
  timed fake animation, so the display is correct when a stage is slow or fails.
- Keep the elapsed-time counter and the "keep this tab open" note. On failure, say which stage
  failed.

Done so far (not the animation): persistent banner with live seconds counter, parallel model
reads (45s down to about 27s), non-blocking upload endpoint (commit e51fcff).

## F-002 -- Admin case view should be about routing, not review (UX, open)
2026-10-03, from testing the Admin flow (A2/A3).

Observed: after an upload, Carla Mendez (Intake Coordinator) lands on the full clinical review
screen. The "Intake" note that tells her what to do is at the very bottom, the Assigned dropdown
is a small control in the top right, and the page leads with the AI recommendation and the full
extracted facts and criteria, none of which an intake coordinator acts on.

Wanted, for the admin persona only:
1. Move the intake action to the top of the case view. The first thing on the page should be
   "Assign this case", as a prominent control, not the small dropdown in the header.
2. Drop the recommendation banner for admin. It is not relevant to deciding who gets the case.
3. Collapse the extracted facts and criteria checklist by default (expandable if she wants it),
   so the page is a short summary plus the assignment action. The Packet and Activity tabs stay.
4. Show nurse workload next to the assignment choice: each nurse and how many cases they
   currently hold, so she can pick whom to assign to without leaving the screen.

Notes for the build:
- Workload data is already derivable from the cases list (open cases per assignee); no new
  clinical logic needed. Open = new, in review, pended, escalated. Worth showing at-risk
  (soon-due or breached) count per nurse too, since routing a case to someone already holding
  breached cases is the thing intake would want to avoid.
- Keep a minimal case summary at the top so she can sanity-check what she is routing: member,
  procedure and CPT, requested priority (expedited vs standard), and the CMS clock remaining.
- Open question for her: should intake see the recommendation at all, even collapsed? Current
  call is no, per the feedback above. Easy to flip back if needed.
- Does not change nurse or medical director views. Server-side rule stays: admin cannot make
  clinical decisions.
