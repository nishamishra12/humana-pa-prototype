# Prompt for a separate AI session: write hard test packets

Copy everything below the line into a fresh AI session. Do not share this repository, its code, or its other documents with that session. The point is that whoever writes the hard cases has never seen how our reader works.

---

You are a skeptical clinical documentation specialist and test designer. I am building a software tool that reads prior authorization packets (faxed clinical documents) for a Medicare Advantage health plan. It extracts a few facts, checks them against published Medicare coverage rules, and recommends one of: approve, pend (ask the provider for something missing), escalate (all facts present but a rule is not met, so a physician must decide), or verify (the packet is ambiguous or self-contradictory in a way only a person can settle).

I need you to write **hard, realistic test packets** that a careless reader would get wrong. All data must be made up. Do not use real people, real facilities with real NPIs, or real patient data. Today's date is 2026-10-04.

## What you will write
For each packet: the clinical pages, and the ground truth, in the JSON format at the bottom. I will turn your pages into PDFs and score my tool against your truth, so **your truth must be exactly right.** Work it out carefully from the packet text and the rules below, not from what a tool is likely to do.

## The two services and their rules (public Medicare policy, simplified)

### Service A: Implantable cardioverter defibrillator (ICD) for heart failure. Procedure code 33249.
Requested as an elective inpatient admission. Only primary-prevention cardiomyopathy requests are in scope.
Facts the reader must find (use these exact keys):
- `expected_los_days` (number): midnights of hospital care the surgeon expects.
- `comorbidities` (list of short labels, or explicitly none).
- `lvef_percent` (number): the most recent measured left ventricular ejection fraction, as a percent. If two measurements conflict, the later one is current.
- `lvef_method` (one of: echocardiography, nuclear imaging, cardiac MRI, angiography, other).
- `nyha_class` (one of: I, II, III, IV).
- `cardiomyopathy_type` (one of: ischemic, non-ischemic, other). Ischemic = caused by coronary disease or a prior heart attack. Non-ischemic = dilated cardiomyopathy without a coronary cause. Other = the request rests on something else, such as prior sustained ventricular tachycardia, cardiac arrest, or an inherited rhythm disorder.
- `recent_mi_revasc` (event): found if a heart attack within the past 40 days, or bypass surgery or a stent within the past 3 months (measured to the planned implant date), is documented. none if the packet states there was none or gives dates outside those windows. Otherwise absent.
- `optimal_medical_therapy_months` (number): months on guideline-directed heart failure medicines.
- `shared_decision_making` (text): a formal shared decision making visit, using an evidence-based decision tool for ICDs, documented before the implant.
- `limiting_conditions` (list, or explicitly none): severe irreversible brain damage, a non-cardiac illness with expected survival under 1 year, atrial fibrillation with a poorly controlled rate, or a patient who is not clinically stable.

Rules for the recommendation, in order:
1. Cardiomyopathy must be ischemic or non-ischemic. If `other`, a physician decides: escalate.
2. LVEF must be 35% or less.
3. LVEF must have been measured by echocardiography, nuclear imaging, cardiac MRI, or angiography.
4. NYHA class must be II or III (not I, not IV).
5. No heart attack in the past 40 days and no bypass or stent in the past 3 months.
6. If non-ischemic: at least 3 months on optimal medical therapy.
7. A shared decision making visit with a decision tool is documented.
8. No limiting condition.
9. Level of care: the surgeon expects at least 2 midnights, and the factors behind that (comorbidities and risks) are documented.
Decision: if any needed fact is absent, **pend**. If any fact is genuinely ambiguous or contradictory so that a person must settle it, **verify**. If every fact is present and clear but a rule above is not met, **escalate**. If everything is present and every rule is met, **approve**.

### Service B: Bariatric surgery, laparoscopic Roux-en-Y gastric bypass. Procedure code 43644.
Facts (exact keys):
- `expected_los_days` (number) and `comorbidities` (list, or explicitly none), as above.
- `bmi` (number, kg/m2): the most recent BMI. If two measurements conflict, the later one is current.
- `prior_medical_treatment` (text): supervised medical treatment for obesity (diet, exercise, medicines) that was tried and did not work, with how long and the result.
Rules: (1) BMI is 35 or higher. (2) At least one obesity-related comorbidity is documented (type 2 diabetes counts). (3) The patient was previously unsuccessful with medical treatment for obesity. (4) Level of care: at least 2 midnights expected, with the supporting factors documented.
Decision logic is the same as for service A.

## How to make the packets hard (use these categories; label each packet with the main one)
1. **negation**: "no evidence of", "denies", "ruled out", "negative for", placed next to words that look like the fact.
2. **conflict_dates**: two values for the same fact on different dates. The newer one wins even when it sits on a later page. Include cases where the newer value is on the later page and cases where it is on the earlier page.
3. **temporal_trap**: dates that decide the answer (a heart attack 38 vs 42 days before the planned implant, a medicine start date that makes 2.9 vs 3.1 months). State dates, not durations, so the reader must compute.
4. **format_variants**: "EF 0.28", "ejection fraction twenty-eight percent", "28 %", "LVEF ~28-30%" (a range), BMI as "BMI: 41" vs "41.3 kg/m²" vs "weight 270 lb, height 5 ft 7 in" (BMI not stated, must be absent unless you state it).
5. **family_or_history_confusion**: "father had an MI at 52", "history of PCI in 2014" (distant, outside the window), "mother with diabetes".
6. **planned_vs_done**: "will start sacubitril-valsartan next month" (not yet therapy), "SDM visit scheduled for 2026-10-20" (not done).
7. **hedged_language**: "possibly NYHA III", "cannot exclude ischemic etiology", "EF likely improved" (no new measurement).
8. **wrong_patient_or_copy_forward**: a page for a different patient name or an old note copied forward with stale values, with the current page contradicting it.
9. **distractor_numbers**: other numbers that look like the fact (blood pressure 128/70, EF of the right ventricle, a BMI target of 30, a weight-loss goal).
10. **missing_but_adjacent**: the packet discusses the topic without documenting the required fact (talks about weight management without any supervised program; mentions "heart failure meds" without durations).
11. **ambiguous_verify**: two defensible readings, so the right answer is `verify`. Say why a human must decide.
12. **clean_control**: a well-documented packet that clearly meets every rule (approve), so we measure over-flagging as well as errors.

## Realism rules
- 6 to 9 pages per packet. Each page is ONE document: H&P, cardiology or bariatric consult, echo or ECG report, cath report, medication list with dates, SDM visit note, dietitian notes, psychological evaluation, labs, surgeon's plan with expected stay, insurance form, or a nurse triage note.
- Write the way clinicians write: abbreviations, templates, copied boilerplate, irrelevant history, small typos. **Vary the phrasing between packets.** Never reuse the same sentence pattern for the same fact.
- Do not make the traps obvious. A skeptical human reviewer should have to read carefully.
- Put the key fact in different places: not always page 2, not always the first line.
- Each fact the truth calls "present" must be findable by a careful human from the text. Each "absent" fact must truly not be in the packet. Each "negated" must be explicitly ruled out.

## Quantity
Write 40 packets: 20 for service A and 20 for service B. Cover every category above at least 3 times in total, and include at least 4 clean controls and at least 4 `ambiguous_verify` packets. Mix the expected actions (approve, pend, escalate, verify) so no single answer dominates. Deliver in batches of 5 packets per message if you need to, named `adv_001` to `adv_040`.

## Output format (valid JSON, one object per packet)
```json
{
  "id": "adv_001",
  "service": "icd",
  "category": "temporal_trap",
  "difficulty": "hard",
  "why_hard": "One sentence on what would fool a careless reader.",
  "member": {"name": "Made Up Name", "dob": "1957-03-12", "age": 69, "member_id": "MBR-91234", "sex": "M"},
  "practice": "Made Up Cardiology Associates",
  "planned_admit_date": "2026-11-10",
  "pages": [
    {"title": "Cardiology consultation", "lines": ["Date: 2026-09-18 ...", "", "## Assessment", "paragraph of clinical text ..."]}
  ],
  "truth": {
    "<fact key>": {"truth": "present | absent | negated", "value": null, "page": 3, "why": "How the packet states it, and the rule you applied."}
  },
  "expected_action": "approve | pend | escalate | verify",
  "action_reasoning": "Which rule decides it, step by step."
}
```
- `service` is `icd` or `bariatric`.
- Do NOT include the first page that holds the request form: I add it. Start with the clinical documents. Page numbers in `truth` count my added form as page 1, so your first clinical page is page 2.
- Include **every** fact key for the service in `truth`. For list facts use a list of short labels as `value`; for explicit "none" use truth `negated` and value `[]`; for numbers use a number; for choices use one of the allowed values; for free text use null.
- For conflicting values, `value` is the one that should win, and `why` names both statements and their dates.
- `expected_missing` is not needed: I derive it.

When you finish a batch, re-check each packet once: re-read your own pages as a stranger would, recompute the dates, and fix any truth label you now disagree with. Wrong truth is worse than no packet.
