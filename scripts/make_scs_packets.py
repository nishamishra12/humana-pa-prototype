"""Faxed spinal cord stimulator packets for LCD L36204 (Noridian), CPT 63685. Typed forms and notes (the codes stay clean),
with handwritten notes and signatures on top. One per outcome:
C approve · D pend (no psychological screening) · E1 pend (trial report not attached) + E2 the provider's fax reply -> approve ·
F escalate, clinically not met (failed trial, active substance use) · G escalate, clinically met but the permanent implant is planned in an office.

Run: python scripts/make_scs_packets.py
Out: interview/03_spinal_cord_stimulator/C_*.pdf ... G_*.pdf
"""
import os, random
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from make_handwritten_packet import scrawl, W, H, M, F, PRINT, PRINT_B

random.seed(31)
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "interview", "03_spinal_cord_stimulator")
PRACTICE = "Lakeview Pain and Spine Center"
ADDR = "4100 Monroe St, Toledo, OH 43606   ·   Ph (419) 555-0140   ·   Fax (419) 555-0141"
MD = "Dr. Meera Iyer, MD"
BODY = ImageFont.truetype(F + "arial.ttf", 30)
BOLD = ImageFont.truetype(F + "arialbd.ttf", 30)


def page(title, sub=""):
    img = Image.new("L", (W, H), 255)
    d = ImageDraw.Draw(img)
    d.text((M, 110), PRACTICE, font=PRINT_B, fill=0)
    d.text((M, 165), ADDR, font=PRINT, fill=0)
    d.line((M, 215, W - M, 215), fill=0, width=3)
    d.text((M, 240), title, font=PRINT_B, fill=0)
    if sub:
        d.text((M, 295), sub, font=PRINT, fill=0)
    d.text((M, H - 120), "Made-up data for a software prototype. Not a real patient.", font=PRINT, fill=0)
    return img, d


def typed(d, x, y, text, font=BODY, width=W - 2 * M):
    """Typed paragraph, wrapped. Returns the y below it."""
    line = ""
    for word in text.split(" "):
        test = (line + " " + word).strip()
        if d.textlength(test, font=font) > width and line:
            d.text((x, y), line, font=font, fill=0)
            y, line = y + 42, word
        else:
            line = test
    if line:
        d.text((x, y), line, font=font, fill=0)
    return y + 42


def note(title, sub, sections, sign, margin=None):
    """A typed clinical note: (heading, paragraph) sections, a handwritten signature, an optional handwritten margin note."""
    img, d = page(title, sub)
    y = 370
    for head, text in sections:
        if head:
            d.text((M, y), head, font=BOLD, fill=0)
            y += 46
        y = typed(d, M, y, text) + 18
    if margin:
        y = scrawl(img, M, y + 20, margin, "surgeon") + 10
    scrawl(img, M, y + 30, sign, "surgeon")
    return img


def request_form(P, setting, n_pages):
    img, d = page("Prior Authorization Request - Procedure", "Health plan: Humana Medicare Advantage   ·   Standard pre-service review")
    rows = [("Date of request:", "10/07/2026"), ("Member name:", P["name"]), ("Date of birth:", f"{P['dob']} (age {P['age']})   Sex: {P['sex']}"),
            ("Member ID:", P["mid"]), ("Requesting MD:", MD + " - Pain Medicine"), ("NPI:", "1588203741"), ("Practice:", PRACTICE),
            ("Requested service:", "Permanent spinal cord stimulator implant (pulse generator and percutaneous leads)"), ("CPT:", "63685"),
            ("ICD-10:", P["icd"]), ("Planned procedure date:", "11/12/2026"), ("Place of service:", setting),
            ("Submitted by:", "Dana Pruitt, Authorization Coordinator  (419) 555-0140")]
    y = 360
    for lab, val in rows:
        d.text((M, y), lab, font=BOLD, fill=0)
        y = typed(d, M + 380, y, val, width=W - 2 * M - 380) + 14
    d.text((M, y + 10), f"Supporting clinical documentation attached ({n_pages} pages including this request).", font=PRINT, fill=0)
    scrawl(img, M, y + 80, "Pt eager to proceed. - DP", "coordinator")
    return img


def fax(img, n, total, stamp):
    img = img.rotate(random.uniform(-0.8, 0.8), fillcolor=255, resample=Image.BILINEAR)
    img = img.resize((int(W * 204 / 200), int(H * 196 / 200)), Image.BILINEAR).resize((W, H), Image.BILINEAR)
    img = img.filter(ImageFilter.GaussianBlur(0.5))
    px = img.load()
    for _ in range(int(W * H * 0.0012)):
        px[random.randrange(W), random.randrange(H)] = 0
    img = img.point(lambda p: 0 if p < 160 else 255).convert("1")
    ImageDraw.Draw(img).text((30, 20), f"{stamp}{n}  FROM: LAKEVIEW PAIN SPINE  4195550141    TO: HUMANA UM    P.{n:03d}/{total:03d}",
                             font=ImageFont.truetype(F + "cour.ttf", 28), fill=0)
    return img


def save(pages, name, stamp="OCT-07-2026 13:4"):
    faxed = [fax(p, i + 1, len(pages), stamp) for i, p in enumerate(pages)]
    faxed[0].save(os.path.join(OUT, name), save_all=True, append_images=faxed[1:], resolution=200)
    print("wrote", name, len(pages), "pages")


HOSPITAL = "Hospital outpatient department, St. Anne Regional Hospital (outpatient surgery)"
OFFICE = "Physician office procedure suite, Lakeview Pain and Spine Center"


def consult(P, conservative, screening, substance, plan_setting):
    return note("Pain Medicine Consultation", f"Date: 08/18/2026     Patient: {P['name']}, age {P['age']}", [
        ("History", f"{P['history']} Chronic intractable low back and leg pain for {P['years']} years. Pain is neuropathic, radiating down the left leg. Average pain NRS 8/10."),
        ("Conservative treatment tried", conservative),
        ("Screening", screening),
        ("Substance use", substance),
        ("Education", "We had an extensive discussion of the risks and benefits of spinal cord stimulation, the trial, the permanent implant and the alternatives. Written materials given. Patient understands and wants to proceed."),
        ("Plan", f"Spinal cord stimulator trial, then a permanent implant if the trial is positive. The permanent implant will be done in: {plan_setting}."),
    ], "Meera Iyer MD   8/18/26")


def psych(P):
    return note("Psychological Evaluation - Pre-SCS", f"Date: 08/26/2026     Patient: {P['name']}     Evaluator: Dr. Paul Grant, PhD, Clinical Psychologist", [
        ("", "Psychological screening for spinal cord stimulation completed: clinical interview, PHQ-9 (6, mild), GAD-7 (4), Pain Catastrophizing Scale (18)."),
        ("", "No untreated major depression, psychosis or cognitive impairment. Realistic expectations of the therapy. No current or past substance use disorder."),
        ("Conclusion", "Psychologically cleared to proceed with a spinal cord stimulator trial and implant."),
    ], "P. Grant PhD")


def trial(P, before, during, pct, meds, function, positive):
    return note("Spinal Cord Stimulator Trial Report", f"Trial dates: 09/14/2026 to 09/21/2026 (7 days)     Patient: {P['name']}     Member ID {P['mid']}", [
        ("Trial", "Percutaneous trial with two temporary epidural leads at T8 to T10, placed in the hospital outpatient department. This was the patient's first spinal cord stimulator trial. No prior SCS trials in any spinal region."),
        ("Pain", f"Target pain NRS {before}/10 before the trial and {during}/10 during the trial: a {pct}% reduction in target pain."),
        ("Medication", meds),
        ("Function", function),
        ("Result", positive),
    ], "Meera Iyer MD   9/22/26")


def person(name, dob, age, sex, mid, history="Failed back surgery syndrome after L4-L5 fusion in 2022.", years=3, icd="G89.4, M96.1 (Post-laminectomy syndrome)"):
    return dict(name=name, dob=dob, age=age, sex=sex, mid=mid, history=history, years=years, icd=icd)


CONSERVATIVE = ("Gabapentin and duloxetine for over 12 months, physical therapy 24 visits in 2025, two epidural steroid injections and a medial branch "
                "block, and 8 sessions of pain psychology (CBT for chronic pain). None gave lasting relief.")
SCREEN = ("Evaluated by our multidisciplinary team: pain medicine (history and full physical and neurologic exam), physical therapy, and a "
          "psychological evaluation by Dr. Paul Grant, PhD (report attached). MRI reviewed: no new surgical lesion.")
SCREEN_NO_PSYCH = ("Evaluated by our multidisciplinary team: pain medicine (history and full physical and neurologic exam) and physical therapy. "
                   "MRI reviewed: no new surgical lesion.")
CONSERVATIVE_NO_PSYCH = ("Gabapentin and duloxetine for over 12 months, physical therapy 24 visits in 2025, and two epidural steroid injections and a "
                         "medial branch block. None gave lasting relief.")
CLEAN = "No current or past substance use disorder. Urine drug screen 8/18/26 consistent with prescribed medicines only."
GOOD_MEDS = "Oxycodone reduced from 30 mg a day before the trial to 10 mg a day during the trial (a 67% reduction)."
GOOD_FUNC = "Functional improvement: walking tolerance went from 2 blocks to 1 mile, sitting from 20 minutes to 1 hour, and sleep from 4 to 7 hours."
GOOD_RESULT = "Positive trial. The patient experienced a clear positive response and wants to proceed to the permanent implant."


if __name__ == "__main__":
    # C: approve
    P = person("Gary Novak", "05/02/1960", 66, "M", "MBR-43003")
    save([request_form(P, HOSPITAL, 4), consult(P, CONSERVATIVE, SCREEN, CLEAN, HOSPITAL), psych(P),
          trial(P, 8, 3, 63, GOOD_MEDS, GOOD_FUNC, GOOD_RESULT)], "C_approve_novak_scs.pdf")

    # D: pend. No psychological screening anywhere in the packet.
    P = person("Brenda Ellis", "12/11/1964", 61, "F", "MBR-43004")
    save([request_form(P, HOSPITAL, 3), consult(P, CONSERVATIVE_NO_PSYCH, SCREEN_NO_PSYCH, CLEAN, HOSPITAL),
          trial(P, 8, 3, 63, GOOD_MEDS, GOOD_FUNC, GOOD_RESULT)], "D_pend_ellis_no_psych_screening.pdf")

    # E1 + E2: the pend loop. The trial was done, but the report is not attached. E2 is the provider's fax with it.
    P = person("Luis Ortega", "03/27/1956", 70, "M", "MBR-43005")
    c = consult(P, CONSERVATIVE, SCREEN, CLEAN, HOSPITAL)
    save([request_form(P, HOSPITAL, 3), c, psych(P)], "E1_pend_ortega_no_trial_report.pdf")
    cover, d = page("FAX - RESPONSE TO REQUEST FOR INFORMATION")
    y = 330
    for lab, val in [("To:", "Humana UM / Prior Auth"), ("From:", "Dana Pruitt, Authorization Coordinator"), ("Date:", "10/09/2026"),
                     ("Re member:", P["name"]), ("Member ID:", P["mid"]), ("Request:", "Permanent spinal cord stimulator implant, CPT 63685")]:
        d.text((M, y), lab, font=BOLD, fill=0)
        y = typed(d, M + 300, y, val, width=W - 2 * M - 300) + 14
    d.text((M, y + 30), "Your question:", font=BOLD, fill=0)
    y = typed(d, M, y + 80, "Please send the spinal cord stimulator trial documentation: the trial dates, the change in pain and medication, and any functional improvement.") + 20
    d.text((M, y + 10), "Our answer:", font=BOLD, fill=0)
    scrawl(cover, M, y + 60, "Sorry, the trial report was left out. It's on the next page. Call (419) 555-0140 with questions. - Dana", "coordinator")
    save([cover, trial(P, 8, 3, 63, GOOD_MEDS, GOOD_FUNC, GOOD_RESULT)], "E2_fax_reply_ortega_trial_report.pdf", "OCT-09-2026 16:2")

    # F: escalate, clinically not met. The trial failed, and there is active substance use.
    P = person("Kimberly Shaw", "08/19/1968", 58, "F", "MBR-43006")
    save([request_form(P, HOSPITAL, 4),
          consult(P, CONSERVATIVE, SCREEN,
                  "Active opioid use disorder, not in treatment. Urine drug screen 8/18/26 positive for non-prescribed fentanyl and methamphetamine.", HOSPITAL),
          note("Psychological Evaluation - Pre-SCS", f"Date: 08/26/2026     Patient: {P['name']}     Evaluator: Dr. Paul Grant, PhD, Clinical Psychologist", [
              ("", "Psychological screening for spinal cord stimulation completed: clinical interview, PHQ-9 (14), GAD-7 (12)."),
              ("", "Active substance use: non-prescribed fentanyl and methamphetamine. Not engaged in treatment."),
              ("Conclusion", "Not psychologically cleared. I recommend substance use treatment before any spinal cord stimulator therapy.")], "P. Grant PhD"),
          trial(P, 8, 7, 12, "Medication unchanged: oxycodone 30 mg a day before and during the trial (no reduction).",
                "No functional improvement: walking tolerance stayed at 1 block, sitting at 15 minutes.",
                "The trial was not successful. Only a 12% reduction in pain, no medication reduction and no functional gain. Patient still requests the permanent implant.")],
         "F_escalate_shaw_failed_trial.pdf")

    # G: escalate, clinically met but the permanent implant is planned in the physician's office (the LCD requires an ASC or hospital).
    P = person("Victor Hale", "01/30/1962", 64, "M", "MBR-43007")
    save([request_form(P, OFFICE, 4), consult(P, CONSERVATIVE, SCREEN, CLEAN, OFFICE), psych(P),
          trial(P, 8, 3, 63, GOOD_MEDS, GOOD_FUNC, GOOD_RESULT)], "G_escalate_hale_office_setting.pdf")
