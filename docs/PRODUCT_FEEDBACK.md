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

## F-003 -- Admin needs a case-to-nurse overview (UX, open)
2026-10-03, from testing the Admin flow.

Observed: the admin nav splits cases by status (Needs assignment, Pended, Escalated, Decided,
Everything). That split is correct for intake and should stay. What is missing is the other
axis: which cases each nurse holds. "Everything" is a list of cases, but it does not make the
case-to-nurse relationship easy to see or act on.

Wanted: one place that shows every case and who it is assigned to, as a summary or table.

Proposed design (front-end call, open to change):
- New admin nav item, "Team", with two parts:
  1. Workload table, one row per nurse: open cases, and the same split by status (new, pended,
     escalated), at-risk count (soon-due or breached), and the soonest CMS deadline they hold.
     Expanding a row lists that nurse's cases. This is also the data F-002 needs next to the
     assign control.
  2. A case table underneath (or as the upgraded "Everything" view): member, procedure, status,
     assigned nurse, medical director if escalated, time left on the clock. Sortable, filter by
     nurse, click a row to open the case.
- Reassign inline from the table (nurse dropdown on the row). Reassigning is the main thing
  intake does, so it should not need opening each case.
- Cases escalated to a physician show the medical director in the "with" column, so ownership is
  clear even when it is no longer with the nurse.

Notes for the build:
- No new clinical logic. Everything needed is already in the cases list (assignee, medical
  director, status, SLA state, priority). Counting per nurse can be done in the browser at this
  scale; add a small summary endpoint if the case count grows.
- Admin stays unable to make clinical decisions. The server blocks admin from escalating, so
  anything beyond routing is a persona-rule change, not a UI change (see open question below).

Open question for her: she mentioned intake being able to escalate. Today the server rejects
that for admin (escalating to a medical director is a clinical call). Options: keep it blocked
and let intake reassign or flag a case instead, or deliberately allow a non-clinical "flag for
review" that does not go through the medical director path. Needs a decision before building.

## F-004 -- Combine user name and Sign out into one profile menu (UX, open)
2026-10-03, from testing the Admin flow.

Observed: the top bar shows the user's name and a separate "Sign out" button side by side.

Wanted: one profile control (avatar or initials plus name, with a dropdown arrow). Clicking it
opens a small menu containing Sign out. Room for later items in the same menu (switch demo
account, theme, notification settings) without crowding the top bar.

Notes: applies to all three personas. The role title (Intake Coordinator, UM Nurse, Medical
Director) can live in the menu header rather than in the bar, which also frees top-bar space
for F-005.

## F-005 -- Make search prominent (UX, open)
2026-10-03, from testing the Admin flow (A9).

Observed: search works, but it did not read as a search. Test A9 looked broken because the field
was not noticed.

Wanted: a clearly visible search control. Candidates: a wider field with a magnifier icon and
a stronger border, a keyboard shortcut hint (press / to focus), and a visible placeholder that
says what it searches ("Search member, case ID or procedure"). Consider showing result count
as you type.

## F-006 -- Export and the Activity tab are hard to find (UX, open)
2026-10-03, from testing the Admin flow (A10). Not a defect: the export endpoint and download
work (verified: 200, correct download headers, about 12.7 KB), and the Activity tab renders
when a case is opened in the preview pane. The tester could not find the Activity tab, so the
export action inside it was out of reach.

Wanted: make both discoverable.
- Move "Export case record" out of the Activity tab into the case header, as a visible action
  or an overflow menu ("..."), so it is reachable from any tab.
- Make the Review / Packet / Activity tabs more obvious (larger, clearer selected state).

Not reproduced: I could not see the tab row going missing in my own browser pane. If it is
hidden at a particular window size or zoom in the tester's browser, a screenshot of that
screen would pin down whether it is a layout problem as well as a discoverability one.

Update, 2026-10-03: the tester found the Activity tab and A10 passes (export downloads). The
discoverability point above still stands as UX feedback; the "not reproduced" note is closed.

## F-007 -- A nurse should see only her own cases (done)
2026-10-03, from testing the nurse flow (N1).

Observed: a signed-in nurse could open "Everything" and see every nurse's cases, and the API
returned all cases to any logged-in user.

Done (not deferred, because it is an access rule that the rest of the nurse tests depend on):
- Server-enforced, not just hidden in the nav. A nurse's case list, counts and search are
  limited to cases assigned to her. Every case endpoint (open, export, comment, assign, action,
  provider reply) answers 404 for another nurse's case, the same as a case that does not exist,
  so the API does not confirm it is there.
- Nurse nav drops "Everything"; "All mine" is the full view. Admin keeps "Everything"
  (intake needs the whole picture) and medical directors are unchanged.
- Covered by scripts/nurse_scope_test.py: two nurses see disjoint sets, scoped counts, 404 on
  all six endpoints, search cannot reach the other nurse's cases, admin and medical director
  views unchanged. Reading of the request: "keep it all" taken as "All mine only".

Open question: should a medical director also be limited to cases escalated to them, or keep
seeing every case? Left unchanged for now (minimum-necessary access argues for limiting them
too). Note: a nurse who escalates a case keeps seeing it in her Escalated view, since it stays
assigned to her.

Also fixed in this change: scripts/smoke_test.py now runs on a temporary database. It used to
write to the live demo database, which is how a regression run changed demo cases earlier.

## Round 3 (2026-10-04), after the canvas review

- **Menu.** It should open and close, icons only or icons with labels. Done.
- **Button colors.** Approve green, Deny red, other main buttons blue. Done.
- **Read the whole packet.** A nurse can read all pages on her own, not only cited pages. Done (Full packet tab and original PDF).
- **Upload screen.** Keep "Reading the packet". Remove technical wording. Done.
- **No technical words anywhere.** The UM team does not care how the check works. Done across the screens, notes, and activity log.
