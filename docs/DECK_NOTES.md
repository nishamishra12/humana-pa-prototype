# Deck notes

Working notes for the interview deck. Updated as we decide things, slide by slide.

## Who the deck is for
Four people have to be convinced. Each asks one main question.

| Audience | Their question | They care about |
|---|---|---|
| Head of product | Will users adopt this, and does it improve the experience? | Customer experience measures, turnaround against the 72-hour and 7-day clocks, time to market, rollout path, phase two and the long-term vision |
| Head of compliance and security | Can this hurt us, and how do we prove it can't? | What the AI outputs, what it falls back to, a human on every decision, what the AI can see, PII, risk of a wrong conclusion, and a risk-to-mitigation table |
| Head of utilization management | What happens to my nurses' day and my numbers? | Hours saved, how the nurse's role changes, the fallback when the tool fails, fewer overturned denials, capacity for the hard cases |
| Engineering | Is this well scoped, and will it fit our systems? | Scope and phases, time to market, speed targets, how we test it, what the AI must output, resourcing, where it plugs into existing systems |

Status: these are a first pass. We have not finished striking items one by one.
Proposed strikes so far: revenue growth and go-to-market (internal tool, protects margin);
"reallocating resources" reworded as "capacity for the hard cases"; "where this fits versus other
projects" becomes a question, not a slide.
Thread that all four share: member visibility in phase two.

## Story order (agreed)
1. Title
2. How a prior authorization moves today (built: one slide, 14 clicks)
3. Six friction points in that process (built: one slide, 6 clicks)
4. How big the problem is: the AMA and OIG numbers, expedited and standard clocks
5. Why now: CMS clocks, January 2027 member access, state laws on AI denials

Each slide answers the question the last one raised. The closing line of slide 2 is
"every step is somebody doing their job correctly," and slide 3 says where the process hurts.

## The six friction points (agreed)
Pulled from the Humana Use Case 1 brief unless noted.
1. Reading by hand. The nurse reads all 14 pages. Clear-cut cases take almost as long as hard ones.
2. Messy input. Fax or portal, and format and quality vary.
3. Hunting, not deciding. Benefits, eligibility, policy, and provider systems sit apart.
4. Decisions vary from reviewer to reviewer.
5. The pend loop. A detail a cleaner read could catch sends the packet back. The case starts from zero and the clock keeps running (the clock point is from CMS-0057-F).
6. The member in the dark. The brief says members feel the stress of waiting. We name this and fix it in phase two.

No numbers on this slide. The brief gives no baseline numbers, so we keep invented figures out.
The real numbers go on slide 4.

## Phase two: why not build member visibility now?
Someone will ask, "why not just build it now with AI? It is easy." The answer has to hold up.
- A status shown to a member is only as good as the decision data behind it. We build the trusted decision record first.
- It touches member communications and a regulated status interface (the CMS Patient Access API, due January 2027). That needs its own compliance and security review.
- The record built in phase one is exactly what phase two reads from, so waiting costs nothing.
Rule for the whole deck: every phase has a reason, and we say it out loud.

## Open items
- **Intake checks.** In the prototype, intake only uploads the packet. It checks nothing. Decide the minimum checks intake should run (for example: member ID present, procedure code present, readable pages) and add them to the prototype and the process slides.
- Finish the audience list, striking what each person does not care about.
- Build slides 4 and 5 from the existing OIG, AMA, and CMS material.
- The old deck (14 slides) is out of date. Slides 4 to 14 need to be re-fit to this story.

## Files
- `deck/journey/build_journey.js` builds `Journey_Click_Through.pptx` (slide 2).
- `deck/journey/build_friction.js` builds `Friction_Click_Through.pptx` (slide 3).
- Each file is one slide with one click per step. Import into Google Slides with File, Import slides.
- To build: `node build_friction.js`. It needs the `@resvg/resvg-js` package to draw the character art.
