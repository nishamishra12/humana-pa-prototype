# Bariatric surgery

- **Service to create:** Bariatric surgery
- **Describe it as:** Weight-loss surgery for morbid obesity: sleeve, bypass and band.
- **Billing code to start with:** 43775
- **Policy to build:** NCD 100.1, plus LCD L35022 (Novitas)

## The two packets

### A_straightforward_carter_sleeve.pdf  (Straightforward)

**What it contains:** BMI 42 with diabetes, hypertension and sleep apnea. A 6-month supervised diet program with a dietitian, a psychological clearance, no contraindications, a surgeon certification and a postoperative plan are all in the packet. A stand-alone sleeve.

**What to expect:** Approve. Every requirement is met and has a quote.

### B_complex_hayes_sleeve.pdf  (Complex)

**What it contains:** BMI 36.8 in the consult but 34.4 three weeks later at the primary care visit. Prediabetes and a controlled blood pressure instead of a clear comorbidity. Only self-directed diets, no supervised program. A depression history with the psychological evaluation still pending. The sleeve is described as the first stage of a longer plan, not stand-alone. No surgeon credentials or postoperative plan.

**What to expect:** Pend or escalate. Conflicting BMI and several missing items, each with a question for the provider.

### C_approve_walker_gastric_bypass.pdf  (Straightforward, nationally covered procedure)

**What it contains:** A laparoscopic Roux-en-Y gastric bypass (43644), which the national policy covers. BMI 45.9 with diabetes, hypertension and sleep apnea, a 7-month supervised diet program, psychological clearance, no contraindications, a surgeon certification and a postoperative plan.

**What to expect:** Approve, once the rule NONCOVERED-PROCEDURE-ABSENT is rejected in the NCD review. That rule's check ('procedure type must be none') fails every packet that names a procedure, so with it approved even this packet escalates.

### D_bad_fax_walker_gastric_bypass.pdf  (Walker, as a bad fax)

**What it contains:** Packet C turned into a bad fax: fax resolution, black and white, tilted, speckled, with a handwritten cover sheet and handwritten margin notes. No text layer.

**What to expect:** Same as C. Unstructured found 21 of 21 key facts, including all 10 handwritten ones.

### E_handwritten_morgan_gastric_bypass.pdf  (Handwritten, clear approve)

**What it contains:** Teresa Morgan, MBR-41004. A laparoscopic Roux-en-Y gastric bypass (43644). Every page is handwritten by a different author and then faxed: the request form, the surgeon's consult, the diet program's visit log, the psychological clearance, the primary care note and the post-op plan. BMI 46.0 with diabetes (A1c 8.2%), hypertension and sleep apnea (AHI 31), a 7-month supervised diet program (8 of 8 visits), psychological clearance, no contraindications, a surgeon certification and a post-op plan.

**What to expect:** Approve, with the same NONCOVERED-PROCEDURE-ABSENT caveat as packet C. Unstructured read 20 of 20 key facts from the handwriting.

### F1_pend_bennett_no_postop_plan.pdf + F2_fax_reply_bennett_postop_plan.pdf  (Handwritten, the pend loop)

**F1:** Gloria Bennett, MBR-41005, gastric bypass (43644), handwritten and faxed. Everything is there except the post-op care plan. **Expect: pend**, asking for the post-op plan.

**F2:** the provider's fax reply: a handwritten cover note that names the member and answers the question, plus the post-op plan page. Upload it as intake. **Expect:** "This fax answers a pended case: PA-xxxx, pended by <the nurse>", with that nurse picked. Attach it. The nurse then sees the question, the reply's pages, and the answers quoted from the new page. **Expect: approve**, with the same NONCOVERED-PROCEDURE-ABSENT caveat as packet C.

The expected result is a guide. It depends on which rules you approved when you reviewed the policy.

All patient data is made up.
