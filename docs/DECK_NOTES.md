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
3. Six friction points (built: one slide, 6 clicks)
4. The federal rules that make them urgent (built: one plain slide, no animation)
5. The numbers: fast is not the same as right (built: one plain slide, no animation)
6. The value: what solving this gets Humana and the member (built: one plain slide, no animation)
7. What the market is doing, then the solution

The separate "why now" slide is gone. Its content moved to slide 4, right after the friction
points, so the federal rules land together with the pain. Slide 2 ends on "every step is
somebody doing their job correctly." Slide 3 says where the process hurts. Slide 4 says it is now
federal.

## The six friction points (agreed)
Pulled from the Humana Use Case 1 brief unless noted.
1. Reading by hand. The nurse reads all 14 pages. Clear-cut cases take almost as long as hard ones.
2. Messy input. Fax or portal, and format and quality vary.
3. Hunting, not deciding. Benefits, eligibility, policy, and provider systems sit apart.
4. Decisions vary from reviewer to reviewer.
5. The pend loop. A detail a cleaner read could catch sends the packet back. The case starts from zero.
6. The member in the dark. The brief says members feel the stress of waiting.

The slide does not explain phase two. We say "I am not trying to solve point 6 first" and come
back to it when we show the solution. No numbers on this part: the brief gives no baseline numbers.

## The federal rules on slide 4 (checked against the sources on 2026-10-03)
Applies to Medicare Advantage plans, so it covers Humana.
- **In effect since January 1, 2026 (CMS-0057-F).** Decisions within 72 hours for expedited requests and 7 calendar days for standard requests. A specific reason on every denial. Prior authorization metrics published every year on the plan's website. The first report was due March 31, 2026.
- **A pend does not stop the clock (42 CFR 422.568(b)).** The plan may extend a standard decision by up to 14 calendar days, only if it justifies the delay as in the enrollee's interest (or the enrollee asks for it), and it must tell the enrollee in writing, including the right to file an expedited grievance. Requesting more information is not itself a pause. This settles the question we left open earlier: the extension still applies alongside the new 7-day clock.
- **January 1, 2027.** Four APIs go live: Patient Access, Provider Access, Payer-to-Payer, and Prior Authorization. The Patient Access API must include prior authorization information, excluding drugs. That is what gives the member a view of where a request stands.
- Sources: CMS-0057-F fact sheet on cms.gov; eCFR 42 CFR 422.568.

**Date fix.** The old deck says January 2027 is "fifteen months out." Today is October 2026, so it is about three months away. Slide 4 and the notes now say "about three months." Check the old slides for the same mistake.

Closing line on slide 4: "These are not just frictions we feel. Federal rules now set the clock, ask for the reason, and make the results public."

## The numbers on slide 5 (checked 2026-10-03)
The argument: Humana is fast, but when a denial is appealed it is often reversed, so we have to be right the first time. An overturned denial is care that was delayed.
- **Fast, at scale (Humana CY2025, own federal reports, 32 Medicare Advantage contracts):** standard decisions average 1 day (median 0) against a 7-day limit. Expedited decisions average 4 to 11 hours against 72 hours. 9.53 million standard requests.
- **Reversed on appeal:** 80.7% of appealed denials overturned across all Medicare Advantage in 2024 (KFF; about 53 million requests, 4.1 million denied, 7.7%; 11.5% of denials appealed). Humana's own 64.7% (17,690 appeals of 653,593 denials, so only 2.7% of denials were appealed). 95% of appealed skilled nursing denials (HHS OIG, 19 plans, data from June 2024; the OIG also found 43% for inpatient rehab and 36% for long-term care hospitals).
- **Physicians (AMA, 1,000 physicians, December 2025):** 93% say prior authorization can delay care at least some of the time. 26% report a serious adverse event for a patient. These are physician reports, not patient counts.
- **Dropped:** the 13 hours a week. It is provider time, and we are solving for the plan. No verified public number exists for plan-side reviewer time per request, so any hours-saved figure stays a labeled placeholder in the business case.

Speaking order (her version): fast (1 day, 4 to 11 hours, 9.5 million), then Humana's 64.7% with "I do not claim 65% of denials are wrong", then the wider picture (80.7%, 95%), then the physicians (93%, 26%) as "the other side of the coin, which we may not solve", then the gap: no public figure for plan reviewer hours. A physician reports 13 hours a week. Do not claim reviewers spend the same. With 9.5 million requests and 14 pages each, expect a large share of their shift, and measure it in a pilot (this last part is an inference, not data). Then land: right the first time, speed is a line we do not cross.

Careful wording:
- Say "an overturned denial is care that was delayed," not "a wrong denial." Humana's own note and KFF both say overturns can come from new information. That supports the point: the first look was missing something.
- Do not say 65% of all denials are wrong. 97% of Humana denials are never appealed.
- Humana already meets the clock on average, so the clock is a guardrail, not the problem. If asked "why fast-track it?", the answer is that we are not. The goal is right the first time, and speed is a line we do not cross.
- Skilled nursing is a short stay for rehab and nursing care after a hospital stay. Approving it needs prior authorization, so these are the same kind of request. A medical-necessity denial must be reviewed by a physician or other appropriate professional (42 CFR 422.566(d)). In Humana's setup it is the medical director.
- The 86% ("up to at some plans") figure for inpatient rehab in the old deck is not verified. Do not use it until checked.

## The value slide (slide 6): the math, checked 2026-10-03
Three reasons for Humana, in order of strength. The AI-only-denial laws are NOT a reason: they are a design rule (our tool never denies).
1. **Workload.** Humana had 5.25 million individual Medicare Advantage members at the end of 2025 and about 6.28 million in January 2026: about 1.03 million more, about 20%. KFF found Humana had the highest requests per member of the big plans (2.2 a year, 2024). So about 20% more requests, roughly 2.3 million (our arithmetic). Nurses do not grow 20% in a month. This one needs no guess about denials or Stars.
2. **Public and compared.** Results are posted yearly since March 2026, and KFF already compares plans by name.
3. **Revenue, as the size of the prize.** Humana 2025 individual MA premiums $90.4 billion (Q4 2025 SEC exhibit) across 5.25 million members, about $17,000 per member per year. Medicare pays most of it as a fixed monthly amount per member. Industry voluntary switching is about 9% a year (KFF, 6% to 12%): about $8 billion of premium in play. Winning back 1 in 1,000 members (5,250 people) is about $90 million, about 1 in 90 leavers. Humana does not publish its own leaving rate. Humana says its retention improved by more than 5 points for the 2026 enrollment period.
   - We cannot prove prior authorization causes members to leave. Say "size of the prize, a pilot would measure the link."
   - The two "90" figures differ: $90.4 billion is all premium, $90 million is 0.1% of it.
   - CMS is dropping the Part C appeals Star measures for 2027, so do not say overturned appeals hurt Stars.
Where the volume math appears: slide 3 (friction 1: "the pile just grew by about 20%"), slide 5 (next to the 9.5 million: "about 2.3 million more are coming"), slide 6 (first value point: +2.3 million requests, a nurse reads every one).
The old "Where the money actually is" slide is retired. Its good idea now sits visibly on slide 6, in the closing bar: Medicare pays per member and at least 85% must go to care (42 CFR 422.2410), so the room to save is in admin work like re-reading and rework, not in paying for less care. Do NOT say "denying more earns Humana nothing": revenue does not change, but denying care would lower medical cost, so the honest point is the 85% floor. Rebuild the old slide's worked example in the business case section (the brief asks for a business case and return-on-investment formula), with clearly labeled placeholder numbers. How utilization costs are classified under the 85% rule varies, so do not quote a dollar split.
Member and provider value: care on time, one clear ask instead of a fax loop, a reason you can see. Phase 2: members see where their request stands.

## Phase two: why not build member visibility now?
Someone will ask, "why not just build it now with AI?" Keep this answer for the solution section, not slides 3 or 4.
- A status shown to a member is only as good as the decision data behind it. We build the trusted decision record first.
- It touches member communications and a regulated status interface. That needs its own compliance and security review.
- The record built in phase one is exactly what phase two reads from, so waiting costs nothing.
Rule for the whole deck: every phase has a reason, and we say it out loud.

## Open items
- **Intake checks.** In the prototype, intake only uploads the packet. It checks nothing. Decide the minimum checks intake should run (for example: member ID present, procedure code present, readable pages) and add them to the prototype and the process slides.
- Finish the audience list, striking what each person does not care about.
- Build the market and solution slides.
- The old deck (14 slides) is out of date. Slides 4 to 14 need to be re-fit to this story.

## Files
- `deck/journey/build_journey.js` builds `Journey_Click_Through.pptx` (slide 2).
- `deck/journey/build_friction.js` builds `Friction_Click_Through.pptx` (slide 3).
- `deck/journey/build_federal.js` builds `Federal_Rules.pptx` (slide 4, a plain slide with no animation).
- `deck/journey/build_numbers.js` builds `Numbers.pptx` (slide 5, a plain slide with no animation).
- `deck/journey/build_value.js` builds `Value.pptx` (slide 6, a plain slide with no animation).
- Each file is one slide with one click per step. Import into Google Slides with File, Import slides.
- To build: `node build_friction.js`. It needs the `@resvg/resvg-js` package to draw the character art.
