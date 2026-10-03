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
