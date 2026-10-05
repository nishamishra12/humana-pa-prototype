# Talking points, from the start

The whole deck in order. One block per click. Say it in your own words. Keep the numbers exact.
Slides marked (draft) are not rebuilt in the final style yet. The points still apply.

---

## 1. Title: why I chose this case

Succinct. Say it in order: stakes, proof, why now, then the bridge.

**Say.**
This is Use Case 1: prior authorization decision support. I chose it for three reasons.

**One.** A prior authorization stands between a patient and their care. The faster and more accurate it is, the sooner they get what they need.

**Two.** Of denials that are appealed, about 80 percent are overturned across Medicare Advantage. Humana is better, at about 65 percent. An overturn means the first decision did not stand, and the patient's care waited.

**Three.** Humana reports its prior authorization results publicly every year since 2026: approvals, denials and appeals. So this step now shows up in a number that people can compare, and that touches member experience, satisfaction and brand trust.

**Bridge to the next slide.**
The judgement is not the slow part. Finding four facts in fourteen pages is. So let the machine find the facts and show where it found them, and keep a person in charge of every hard call.

**Delivery notes.**
- Land slowly on "the patient's care waited". It is the anchor. Bring it back on the numbers slide.
- Say "of denials that are appealed". Never say "80 percent of denials".

---

## 2. How a prior authorization moves today (14 clicks)

1. A surgeon decides a patient needs a lumbar fusion. The office assembles a packet: notes, imaging, history. Meet John Doe, 71. He is waiting and sees none of this.
2. They fax the packet to the plan. Fourteen pages. Fax is still how most of this moves.
3. Intake checks the member, the form and the codes. That is a paperwork check. Nobody has read the clinical pages yet.
4. Intake assigns it to a utilization management nurse.
5. The nurse reads all fourteen pages. They are hunting for four facts: expected stay, risk factors, imaging, and conservative treatment. Then they check each one against policy.
6. There are three ways out: approve, pend, or escalate.
7. Path one. Every fact is there and every rule is met. The nurse approves. This is the good case.
8. Path two. A fact is missing. The nurse pends it, and it goes back to the provider.
9. The provider has to work out what is missing. Nobody tells them in plain terms. And a pend does not stop the CMS clock.
10. They find it and resend. It goes through the fax all over again.
11. Back at intake, the case starts from zero. Maybe a different nurse reads it. The clock never stopped.
12. Path three. The facts are there, but the case is borderline. It goes to a medical director.
13. Only the medical director can deny. A denial can be appealed, and many are overturned.
14. Land it: every step is somebody doing their job correctly. The delay is built into the process.

---

## 3. Six places this process loses time (6 clicks)

1. Reading by hand. The nurse reads all fourteen pages to find the same few facts. Clear-cut cases take almost as long as hard ones.
2. Messy input. Fax or portal. Format and quality change from one office to the next.
3. Hunting, not deciding. Benefits, eligibility, policy and provider systems sit apart. No one view holds the full picture.
4. Decisions vary. Two reviewers can read the same packet and land in different places.
5. The pend loop. A detail a cleaner read could catch in minutes sends the packet back. The case starts from zero. This is the path you just watched.
6. The member in the dark. John waits and cannot see where his request stands. I am not solving that one first. I will come back to it, and say why.

---

## 4. Why now? (a plain slide, four cards)

Say it in order: the volume, the clock, the rule on pending, then January 2027. Each card has one number. Put the detail in your voice.

1. **The volume. +20 percent.** About a million members joined Humana in January, roughly 20 percent more, all at once. KFF found Humana averages about 2.2 requests per member a year. That is an average: most members make none, and some make many. If the new members look like the current ones, that is roughly 2.3 million more requests a year, about 190,000 a month. A nurse reads every one.
2. **The clock. 72 hours.** Since January 2026, a decision is due in 72 hours for an expedited request and 7 calendar days for a standard one. That means an approval or a denial, not a pend. Every denial needs a specific reason. And plans publish their results every year. The first report was due March 31, 2026.
3. **The rule on pending. 14 days.** A plan can add up to 14 calendar days, but only if it justifies the delay as in the member's interest and tells the member in writing. A pend does not stop the clock. So every avoidable pend is a documented delay.
4. **Coming January 2027.** About three months away. Four data interfaces go live. The Patient Access API must show the member where a prior authorization stands.

**Close.** More requests. A harder clock. Public results. That is why this matters now.

**Be careful.** The 2.3 million is an estimate. Say "roughly". It assumes new members look like current ones.

---

## 5. Humana is already acting. Here is the gap. (replaces the numbers slide, a plain table)

Succinct. One row at a time. Say the lever, then what it leaves untouched.

1. **Volume.** Humana is cutting about a third of its outpatient approval requirements: diagnostic colonoscopies, heart monitoring tests, some CT and MRI scans. Fewer requests. But the complex ones, and inpatient ones like my surgeries, still need a full review.
2. **Exemption.** A gold card for physicians with a proven record. They skip the review for certain services. Everyone else is still reviewed.
3. **Speed target.** One business day for 95 percent of complete electronic requests. Note the word complete. As I read it, incomplete requests, and faxed or scanned ones, sit outside it.
4. **Transparency.** Humana will publish approvals, denials, appeals, overturns and decision times. That makes a wrong decision visible. It does not prevent one.
5. **My prototype.** Volume. Who is reviewed. How fast. How visible. None of them changes the review itself. That is where I fit.
6. **The lever.** Faster, right first time. Faster means care starts sooner. Right first time means fewer pend loops and fewer overturned denials.

**Say out loud.** "Humana's moves change how many, who, how fast, and how visible. Mine changes the review itself."

**Be careful.**
- Say "complete electronic requests". That is Humana's wording. "Incomplete and faxed requests sit outside it" is my reading, so say "as I read it".
- Do not imply Humana ignores quality. Say these moves change how many reviews and how fast.
- I measured the machine's read time, about 17 seconds a packet. I have not measured the nurse's time saved. A pilot would show that.
- Source: Humana's announcement at policy.humana.com (2025).

---

## 6. Four people, two parts (the value slide is dropped)

A plain slide. Each person owns one decision. Part 1 is before go-live. Part 2 is every packet.

**Open.** These are the four people you will meet as I walk you through the prototype. Each one owns one decision.

1. **The policy owner. Part 1, before go-live.** This is the biggest piece of real work, and it happens before any packet arrives. The policy owner builds the library the AI checks against. They choose the policies and procedures we cover, and they approve every rule the AI drafts. They own what we check against.
2. **The intake coordinator. Part 2, every packet.** They receive the packet, check it in, and assign it to a nurse. They can see every nurse's workload. They own who reviews it.
3. **The UM nurse.** The star player. They review the packet with the AI's help. They confirm approve, ask the provider one precise question, or escalate. They own the recommendation.
4. **The medical director.** They decide the hard cases, with the evidence attached, and write the reason. They own any denial. Only they can deny.

**Close.** One more teammate: the AI. It reads, drafts and cites. It never decides.

---

## 6a. The solution has two parts (overview, 4 clicks)

1. **Part 1, before go-live. The biggest piece of work.** We pass in the policies for the procedures we want to cover, with their billing codes. The ETL step with AI inside reads them. The AI drafts the key facts to check for each procedure. The policy owner approves every rule. That is the human in the loop in part 1.
2. **The link.** Part 2 only uses what part 1 approved. The rules the nurse sees are never made up when a case arrives.
3. **Part 2, every packet.** The intake coordinator checks the packet and assigns a nurse. The ETL step reads it. The AI compares it with the key facts for this procedure and recommends. The nurse confirms. The director decides the hard cases. Those are the humans in the loop in part 2.
4. **Land it.** A person is in the loop in both parts. The AI never decides.

## 6b. The policy owner builds the library (Part 1, 8 clicks)

1. The owner picks a policy for a procedure we want to cover: a CMS policy from a list, or the plan's own PDF.
2. They add the billing codes that identify the procedure. A code is the short code on every request that names the procedure. Each code keeps its source, a CMS billing article. This is how a packet finds this policy later.
3. The ETL step with AI inside reads the policy and keeps its structure: titles, paragraphs, tables, pages.
4. The AI turns each requirement into a rule. For each rule it names the key fact a nurse must check, like the ejection fraction, and copies the exact sentence the rule came from. That list of key facts is what we look for in every packet for this procedure.
5. Plain code checks the draft. Is the quote in the policy? Is every number in the quote? Does the fact exist? Anything that fails goes to the owner. No AI here.
6. The owner reads each rule with the official text beside it. Approve, edit or reject. The AI drafts. A person signs.
7. They link the codes and the policy to a service, any name the business uses for a kind of request, and publish a version. Every version is kept and can be rolled back.
8. **Result.** For every procedure we cover, the key facts to check when a packet arrives. It is the biggest piece of real work, and it happens before go-live.

## 6c. The intake coordinator checks and assigns (Part 2, 7 clicks)

1. A provider sends the packet. Intake uploads it as one PDF. Nothing changes here.
2. The ETL step reads every page. Plain pattern matching finds the procedure code on the request form.
3. The screen shows what it found: member, code, planned date, pages. If no service uses the code, it says "No policy yet". Nothing is guessed.
4. Intake checks the packet. Right member, readable, a procedure we cover. A paperwork check, not a clinical one.
5. They open the team view. Each nurse's open cases, which are at risk, which are close to the CMS deadline.
6. They assign a nurse. The nurse is told. The clock is tracked.
7. **Land it.** Intake owns who reviews it. They never judge the clinical content.

## 6d. The UM nurse has less to read (Part 2, 8 clicks)

1. When a packet arrives, the AI compares it with the key facts for the policies that mention this procedure. It reads three times and the answers must agree. If it cannot tell, it says so.
2. For every fact it shows the page and the exact sentence. A second AI checks the sentence supports the claim.
3. It recommends. Approve, when every fact is there and every rule is met. Pend, with the exact question to ask. Or escalate, when a rule is not met. There is no deny.
4. The nurse reviews a checklist with the evidence beside each item. They review. They do not hunt through fourteen pages.
5. They decide. They can follow the recommendation or override it. An override is recorded.
6. If pended, the provider gets one precise question. When they reply, the packet is read again and returns to the nurse.
7. If escalated, the case goes to the director with the evidence and the nurse's note.
8. **Land it.** The nurse owns the recommendation. The AI never decides.

## 6e. The medical director decides the hard cases (Part 2, 6 clicks)

1. The case arrives in the director's queue, sorted by the clock, with the evidence and the nurse's note.
2. They read which rules were not met, and the page and sentence behind each.
3. They decide. Approve. Deny, with a written reason. Or send it back to the nurse, with a reason. Only a medical director can deny.
4. The decision, the reason and who made it are recorded in the audit trail.
5. The case closes, or returns to the nurse if it was sent back.
6. **Land it.** The director owns any denial. Only they can deny.

---

## 7. Building the library, then onboarding a service (Part 1, 9 clicks)

**Open.** The product has two parts. This is part one: build the library the nurse checks against. I do it once for each service, and again when a policy changes.

1. **Official sources.** Today a nurse checks every case against policy by hand: CMS national and local policies, federal rules, and Humana's own documents. I start from the same sources.
2. **Read the policy.** A document step with AI inside keeps the structure: titles, paragraphs, tables and pages. Flat text would lose the sections the rules hang on.
3. **Draft the rules.** An AI turns each requirement into a rule. It names the detail a nurse must check, like ejection fraction. And it copies the exact sentence from the policy.
4. **Check the draft.** Plain code checks every quote, number and detail. A failure goes to the owner. It never disappears. No AI in this step.
5. **The owner approves.** A person approves, edits or rejects every rule, with the official text beside it. The AI drafts. It never publishes.
6. **Codes and a service.** A procedure code is the short code on every request that names the procedure. A CPT code is five digits. 33249 is an implantable defibrillator. A HCPCS code is a letter and four digits, used for equipment. The policy gets its codes, with their source. Then it joins a service. A service is any product or business name we choose for a kind of request, like "ICD for heart failure." It holds three things: codes, policies, and the details to look for.
7. **Which services first.** In production, Humana's own request history, by procedure code, sets the rollout. In the prototype, the owner sees the same signal live as requests that arrived with no policy.
8. **Publish.** One versioned library. Every version is kept, so I can roll back. Every action is in an audit trail.
9. **What we get.** A library of services with codes, policies and details. Every rule tied to its official sentence and a named approver. Every code with its source. And a new service moves from planned, to pilot, to live.

---

## 8. Then every packet is read with that library (Part 2, 9 clicks)

**Open.** This is the daily work. It only uses what part one approved.

1. **Provider and intake.** The provider sends the packet. Intake uploads one PDF. Nothing changes here.
2. **Read the pages.** The document step with AI inside works out how to read each page, typed text or a scan. It splits the page into pieces, works out where each sits, and labels it: title, paragraph, table. The output is a list of typed pieces with their page and position.
3. **Find the service.** The procedure code picks the service. If no service uses it, the case is flagged "No policy yet." Nothing is guessed. The nurse decides, and the owner sees the demand.
4. **Read the details.** An AI fills one form, the details this service needs. It reads three times and the answers must agree. If it cannot tell, it says so.
5. **Check the evidence.** Plain code finds each quote on its page. A second AI checks the sentence supports the claim.
6. **Apply the rules.** Plain code. Missing: pend. Unclear: verify. A rule not met: escalate. All met: approve. There is no deny in this code.
7. **The nurse confirms.** A checklist with the evidence beside each item. Approve, pend with one question, or escalate.
8. **The medical director.** Hard cases arrive with the evidence attached. Only a medical director can deny, and writes the reason.
9. **Land it.** The AI reads and cites. Code decides. A nurse confirms. A medical director alone can deny.

---

## 9. With all of that underneath, the flow is simple (draft, 6 clicks)

1. The top row is today. Fax, intake, the nurse reads fourteen pages, a pend loops back. With the product, intake uploads the PDF. That is all intake does.
2. The system reads it, finds the details, cites each one, and checks the library.
3. The nurse opens a checklist with the evidence beside every item. They review. They do not hunt.
4. They approve, ask one precise question, or escalate. A missing detail is found at the start, not after a loop.
5. A medical director decides the hard cases with the evidence attached. Only they can deny.
6. What changes: a cited checklist instead of a stack of pages, a missing detail found at once, and hard cases reaching a physician early.

---

## 10. Walking through the prototype (draft, 5 clicks)

1. **Intake and nurse.** Upload a packet. Every detail has its page and sentence. Approve, pend with one question, or escalate.
2. **Policy owner.** Requests without a policy shows what to onboard. Add a service, draft and review a policy, publish. Planned, pilot, live. Every step in an audit trail.
3. **Medical director.** Only the hard cases. The only role that can deny, with a written reason.
4. **Honeycomb.** Every packet is a trace. Each step is timed. If a step slows down or fails, it shows at once. One board holds the numbers that matter.
5. **The live dashboard.** It refreshes every few seconds as cases move, and it reads the same events as Honeycomb. The shared link is a snapshot for reading afterwards. Move a case and watch the numbers change.

---

## 11. One number to win, guardrails so we do not cheat (Metrics, 5 clicks)

1. **North star.** Right-first-time rate. Of every 100 requests, how many get the right answer the first time, with no back and forth. It helps the member, the provider, the nurse and the plan. A case has rework if the nurse asks for something already sent, a director sends it back, or a denial is overturned because the packet had the answer.
2. **Leading indicators.** They move in days. First-review rate. Avoidable pends, where the provider says it was already sent. Avoidable escalations. And how often the nurse's first action matches the AI.
3. **Lagging indicators.** They take months and need Humana's data. Overturned because the info was in the packet. Cost per decision. Month over month. When it arrives, the early read becomes the full north star.
4. **Guardrails.** Never slower than the CMS clock. If approvals jump, I may be approving too much. The AI never denies.
5. **Decisions.** Is there enough nurse capacity before a deadline passes. Which service to onboard next. Does the owner have time for the drafts waiting. Does a pilot go live or pause.

---

## 12. We optimize for recall, and watch it every day (Evals and observability, 4 clicks)

1. **Why recall, not precision.** The group that matters is cases that need a person. Recall asks: of those, how many did I flag. A miss is a wrong approval. That is the dangerous failure. Precision asks: of the cases I flagged, how many really needed a person. A miss is an extra flag. A nurse spends a few minutes on a case that was fine. That costs time, not safety. So I push recall up and accept more extra flags. This also fits right-first-time. A quick check now beats a wrong approval that comes back as an appeal.
2. **Quality, every run.** Recall first. Wrong approvals, the alarm number, and the goal is zero. Precision and extra flags, which show what caution costs. Details found, and details made up. And whether the nurse's first action matches the recommendation. My release rule: if wrong approvals go up, I do not ship.
3. **Speed and health, every packet, in Honeycomb.** Every packet is a trace. I see each step's time at the 95th and 99th percentile, not just the average. Step errors show at once. I track when the three reads disagree, which is the AI changing its mind. I track cost per packet. And I track cases with no policy, which is demand for a new service.
4. **Proof so far.** On made-up packets. On 40 hard packets from another author, recall rose from 57 to 86 percent, and wrong approvals fell from 12 to 4. The standard nine were 45 of 45. I tuned on that set, so a fresh set is the final test. The real test is real, de-identified cases labeled by senior nurses.

---

## 13. What we did not build: the member's view (draft, 5 clicks)

1. The sixth friction: the member waits with no view. It is real. I chose not to build it first. Every phase has a reason I can say out loud.
2. A status is only as good as the record behind it. I build the trusted decision record first.
3. It touches a regulated interface. Member messages and a status screen need their own compliance and security review.
4. Waiting costs nothing. The record I build now is exactly what the member view will read.
5. And the timing works. From January 2027, plans must offer a Patient Access API with prior authorization information. About three months away. The record I build now feeds it.

---

## 14. Phase 1 builds the record. Phase 2 puts it to work. (6 clicks)

1. **Phase 1.** This is what you have seen. The AI recommends with citations. The nurse confirms. It removes the pend. A missing detail is found at the start, as one precise question. I add services one at a time: planned, pilot, live. And it builds something that matters next: a trusted record of every decision, with its evidence.
2. **The gate.** Phase 2 has a gate. I do not build the next layer on a record I have not tested. First, evals on real, labeled cases, not made-up ones. Second, a compliance review for anything the member sees. Until then, nothing in phase 2 goes live.
3. **The member's view.** Friction six: the member waits with no view. I did not build it first, because a status is only as good as the record behind it. The record from phase 1 is what the member view reads. And from January 2027, plans must offer a Patient Access API with prior authorization information.
4. **Learn from outcomes.** When a denial is appealed and overturned, I want to know if the packet already had the answer. That feeds back into the rules and the evals. This is the full version of right-first-time.
5. **More services.** I onboard them one at a time, ranked by Humana's own request history: volume, pends and reversals by procedure code. The process is the one you saw: policy, codes, service, pilot, live.
6. **Land it.** In every phase a person decides. The AI never denies, and it never approves on its own. A nurse confirms every recommendation. Only a medical director denies, and writes the reason.

---

## 15. How the AI decided the packet (5 slides, after the prototype)

Use the screenshots in `deck/journey/screenshots/`. The example is one made-up packet: an 8-page scanned ICD request for Beverly Tanaka-Holt. Policy is already explained, so these slides cover the packet only.

### Slide A. Steps 1 and 2: the packet comes in, and is read (same color)
**Input.** The intake coordinator uploads one PDF. Eight pages. Every page is a picture. There is no text in the file. It is a noisy scan, like a real fax.
**What happens.** The document step with AI inside looks at each page, works out how to read it, and splits it into pieces. It finds where each piece sits on the page, the box, and labels it: title, paragraph, table, header, footer.
**Output.** 48 elements in about 53 seconds. 19 paragraphs, 17 titles, 3 tables, plus headers and footers. We keep three things for each: the page, the type and the text. Look at the screenshot: the scan on the left with a box round each piece, the typed list on the right. Everything after this starts from that list.

### Slide B. Step 3: find the service
**Input.** Page 1, as text. The request form.
**What happens.** Plain pattern matching finds the labeled fields. No AI.
**Output.** The procedure code, 33249. The procedure as written. The planned date, 2026-11-19. Inpatient. The facility. Then the lookup. The code is looked up in the list of services. It is a dictionary, not a search. 33249 gives the implantable defibrillator service and its policies. If the code is not in the list, the case says "No policy yet" and goes to a person. Nothing is guessed.

### Slide C. Step 4: read the details
**Input.** The whole packet as text, 8 pages, about 11,600 characters, each piece tagged with its page. Plus the member's name and date of birth, so it can tell if a page belongs to someone else. And the rules the reader must follow: if the text rules something out, say none. If two statements conflict, use the later one. Copy the exact sentence. Never guess. A planned visit has not happened.
**What happens.** An AI fills in one form. The form is the list of details this service needs. I send the same request three times, in parallel.
**Output.** Three reads side by side. Look at the column on the right: agree, agree, agree. Ejection fraction 28. Measured by echocardiography. Class III. Non-ischemic. Nine and a half months on medicines. If the three reads disagree on a status or a number, the detail becomes "not sure" and goes to the nurse. The wording can differ, look at the comorbidities. The status and the numbers must match. And the months are counted by my code from the start date, not by the AI.

### Slide D. Step 5: check the evidence
**Input.** Each quote the reader gave, with the claim it supports.
**What happens.** Plain code looks for each quote on the real page. Then a second AI answers one word for each: supports, contradicts, unrelated or insufficient.
**Output.** A table. The claim, the sentence it relied on, the page where code found it, how well it matched, and the verdict. Ejection fraction 28: found on page 3, exact match, supports. Expected stay of 2 midnights: found on page 8, exact, supports. The nurse sees the real text from the page, highlighted. Not the AI's version. If a sentence does not support the claim, the detail loses its tick and the nurse sees that.

### Slide E. Step 6: apply the rules
**Input.** The details, and the approved rules. Each rule names one detail and a test. For example, ejection fraction is 35 or less.
**What happens.** Plain code compares the two. The order never changes. A missing detail: pend, with one question. Unclear: verify. A rule not met: escalate. Everything met: approve. There is no deny.
**Output.** The checklist. Each rule, the value found, and met or not met. Here every rule is met. The recommendation is approve, and a nurse still confirms it. The same details always give the same answer.

---

## If someone asks
- **Why a pilot?** The reader is an AI and these details are new. A service goes live only after test packets pass. Until then, nurses check every recommendation.
- **Who decides which services come first?** Humana's request history. Volume, pends and reversals by procedure code.
- **Where did the codes come from?** CMS billing articles. The screen stores the article next to each code.
- **Has a real policy owner used it?** No. I tested it myself on made-up data.
