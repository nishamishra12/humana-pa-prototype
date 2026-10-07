"""Handwritten, faxed TMS packets for LCD L34641 (WPS), CPT 90867. One per outcome:
C approve · D pend (no psychotherapy record) · E1 pend + E2 the provider's fax reply (medication history) -> approve ·
F escalate, clinically not met (a clear denial for the director) · G escalate, clinically met but right-sided rTMS (the LCD covers left prefrontal only).

Run: python scripts/make_tms_packets.py
Out: interview/06_tms_depression/C_*.pdf ... G_*.pdf
"""
import os, random
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from make_handwritten_packet import scrawl, field, checkbox, W, H, M, F, PRINT, PRINT_B

random.seed(23)
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "interview", "06_tms_depression")
PRACTICE = "Northcoast Psychiatry and TMS Center"
ADDR = "2750 Olentangy River Rd, Columbus, OH 43202   ·   Ph (614) 555-0160   ·   Fax (614) 555-0161"
MD = "Dr. Daniel Kim, MD"


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


def request_form(P, service, n_pages):
    img, d = page("Prior Authorization Request - Outpatient Treatment", "Health plan: Humana Medicare Advantage   ·   Standard pre-service review")
    y = 360
    for lab, val in [("Date of request:", "10/07/2026"), ("Member name:", P["name"]), ("Date of birth:", f"{P['dob']}   (age {P['age']})   Sex: {P['sex']}"),
                     ("Member ID:", P["mid"]), ("Member phone:", P["phone"]), ("Requesting MD:", MD + " - Psychiatry"), ("NPI:", "1932047658"),
                     ("Practice:", PRACTICE), ("Requested service:", service), ("CPT:", "90867"), ("ICD-10:", P["icd"]),
                     ("Planned start date:", "10/26/2026"), ("Sessions:", "36 over 6 weeks, then 6 taper"),
                     ("Submitted by:", "Imani Whitfield, Auth Coordinator  (614) 555-0160")]:
        y = field(img, d, y, lab, val, hand="program" if lab in ("CPT:", "Member ID:") else "coordinator")  # codes in the clearest hand: a misread 6 for 8 sends the case nowhere
    d.text((M, y + 20), "Level of care requested:", font=PRINT, fill=0)
    checkbox(img, d, M + 360, y + 16, "OUTPATIENT", True)
    checkbox(img, d, M + 660, y + 16, "Inpatient", False)
    d.text((M, y + 90), f"Place of service: office, outpatient TMS suite. Supporting documentation attached ({n_pages} pages incl. this request).", font=PRINT, fill=0)
    return img


def notes(title, sub, paras, hand, sign=None):
    img, d = page(title, sub)
    y = 380
    for p in filter(None, paras):
        y = scrawl(img, M, y, p, hand) + 22
    if sign:
        scrawl(img, M, y + 40, sign, hand)
    return img


def psych_eval(P, meds, therapy_line, order, safety_line):
    return notes("Psychiatric Evaluation", f"Date: 09/18/2026     Patient: {P['name']}, age {P['age']}     Evaluated by {MD}, Psychiatry", [
        f"Dx: {P['dx']}. PHQ-9 {P['phq']}, HAM-D {P['hamd']}. Current episode {P['episode']}. No psychosis, no mania. No alcohol or substance use disorder.",
        meds, therapy_line, safety_line, order], "surgeon", f"Daniel Kim MD   9/18/26")


def therapy(P, rows, summary):
    img, d = page("Psychotherapy Record - Cognitive Behavioral Therapy", f"Therapist: Dr. Hannah Brooks, PsyD     Patient: {P['name']}")
    cols = [M, M + 330, M + 560]
    for x, h in zip(cols, ["Date", "PHQ-9", "Session"]):
        d.text((x, 370), h, font=PRINT_B, fill=0)
    d.line((M, 425, W - M, 425), fill=0, width=2)
    y = 445
    for r in rows:
        for x, v in zip(cols, r):
            scrawl(img, x, y, v, "program")
        d.line((M, y + 72, W - M, y + 72), fill=0, width=1)
        y += 92
    scrawl(img, M, y + 30, summary, "program")
    return img


def safety(P, lines):
    return notes("TMS Safety Screening", f"Date: 09/25/2026     Patient: {P['name']}     Completed by {MD}", lines, "psych", "D. Kim MD")


def fax(img, n, total, stamp):
    img = img.rotate(random.uniform(-0.9, 0.9), fillcolor=255, resample=Image.BILINEAR)
    img = img.resize((int(W * 204 / 200), int(H * 196 / 200)), Image.BILINEAR).resize((W, H), Image.BILINEAR)
    img = img.filter(ImageFilter.GaussianBlur(0.6))
    px = img.load()
    for _ in range(int(W * H * 0.0015)):
        px[random.randrange(W), random.randrange(H)] = 0
    img = img.point(lambda p: 0 if p < 160 else 255).convert("1")
    ImageDraw.Draw(img).text((30, 20), f"{stamp}{n}  FROM: NORTHCOAST PSYCHIATRY  6145550161    TO: HUMANA UM    P.{n:03d}/{total:03d}",
                             font=ImageFont.truetype(F + "cour.ttf", 28), fill=0)
    return img


def save(pages, name, stamp="OCT-07-2026 11:2"):
    faxed = [fax(p, i + 1, len(pages), stamp) for i, p in enumerate(pages)]
    faxed[0].save(os.path.join(OUT, name), save_all=True, append_images=faxed[1:], resolution=200)
    print("wrote", name, len(pages), "pages")


LEFT = "Left prefrontal rTMS, initial course"
TWO_MEDS = ("Medication trials this episode, 2 different classes, each at an adequate dose and duration: sertraline (SSRI) up to 200 mg daily x 10 wks, "
            "no clinically significant response. Bupropion XL (NDRI) 300 mg daily x 8 wks, no response.")
ORDER_LEFT = ("Plan: I examined the patient and reviewed the full record. I order left prefrontal rTMS, 10 Hz, 36 sessions. I am experienced in "
              "administering TMS and will directly supervise every treatment on site.")
SAFE = ("Safety: no history of seizures or epilepsy. No psychotic symptoms. No stroke, dementia, head trauma or CNS tumor. "
        "No pacemaker, ICD, cochlear implant, VNS, aneurysm clips, stents or other metal in the head or neck. Dental fillings only.")
SAFE_PAGE = ["No history of seizures, epilepsy or febrile seizures. No psychotic disorder, no psychotic symptoms in this episode.",
             "No cerebrovascular disease, dementia, raised intracranial pressure, head trauma or tumor of the CNS.",
             "No implanted devices: no pacemaker, ICD, cochlear implant, VNS, deep brain stimulator. No aneurysm clips, coils, staples or stents. Dental amalgam fillings only (acceptable).",
             "Patient read and signed the TMS consent."]
CBT_ROWS = [("1/12/26", "21", "Session 1, intake"), ("2/09/26", "22", "Session 5"), ("3/09/26", "21", "Session 9"), ("4/06/26", "22", "Session 13"), ("5/04/26", "22", "Session 16, last")]
CBT_SUM = "Summary: weekly CBT, 16 sessions, 1/12/26 to 5/4/26. No significant improvement in depressive symptoms on the PHQ-9 (21 at start, 22 at end). - H. Brooks PsyD"


def person(name, dob, age, sex, mid, phone, **k):
    return dict(name=name, dob=dob, age=age, sex=sex, mid=mid, phone=phone, icd="F33.2 (MDD, recurrent, severe)",
                dx="Major depressive disorder, recurrent, severe, without psychotic features", phq=23, hamd=27, episode="14 months", **k)


if __name__ == "__main__":
    # C: approve. Every requirement is met and written down.
    P = person("Rachel Simmons", "04/14/1979", 47, "F", "MBR-46003", "(614) 555-0171")
    save([request_form(P, LEFT, 4), psych_eval(P, TWO_MEDS, "Psychotherapy: 16 sessions of CBT, no significant improvement (records attached).", ORDER_LEFT, SAFE),
          therapy(P, CBT_ROWS, CBT_SUM), safety(P, SAFE_PAGE)], "C_approve_simmons_left_rtms.pdf")

    # D: pend. No psychotherapy anywhere in the packet.
    P = person("Anthony Russo", "11/02/1966", 59, "M", "MBR-46004", "(614) 555-0172")
    save([request_form(P, LEFT, 3), psych_eval(P, TWO_MEDS, "", ORDER_LEFT, SAFE), safety(P, SAFE_PAGE)], "D_pend_russo_no_psychotherapy.pdf")

    # E1 + E2: the pend loop. E1 says the medication history is attached, but it is not. E2 is the provider's fax with it.
    P = person("Patricia Coleman", "07/30/1971", 55, "F", "MBR-46005", "(614) 555-0173")
    save([request_form(P, LEFT, 4), psych_eval(P, "Medication trials: see the attached medication history.", "Psychotherapy: 16 sessions of CBT, no significant improvement (records attached).", ORDER_LEFT, SAFE),
          therapy(P, CBT_ROWS, CBT_SUM), safety(P, SAFE_PAGE)], "E1_pend_coleman_no_medication_history.pdf")
    q = "Please send the medication trials in the current episode: each antidepressant, its class, dose, duration and response."
    cover, d = page("FAX - RESPONSE TO REQUEST FOR INFORMATION")
    y = 330
    for lab, val in [("To:", "Humana UM / Prior Auth"), ("From:", "Imani Whitfield, Auth Coordinator"), ("Date:", "10/09/2026"),
                     ("Re member:", P["name"]), ("Member ID:", P["mid"]), ("Request:", "Left prefrontal rTMS, CPT 90867")]:
        y = field(cover, d, y, lab, val)
    d.text((M, y + 30), "Your question:", font=PRINT, fill=0)
    y = scrawl(cover, M, y + 75, q, "coordinator") + 20
    d.text((M, y + 10), "Our answer:", font=PRINT, fill=0)
    scrawl(cover, M, y + 55, "Sorry, the medication history was left out. Dr. Kim's medication trial summary is on the next page. Call (614) 555-0160 with questions.  - Imani", "coordinator")
    meds = notes("Medication Trial Summary - Current Episode", f"Patient: {P['name']}   ·   Member ID {P['mid']}   ·   {MD}", [
        "1) Escitalopram (SSRI) up to 20 mg daily, 9/2025 to 11/2025, 10 weeks at full dose. No clinically significant response (PHQ-9 22 to 22).",
        "2) Mirtazapine (atypical / NaSSA) 45 mg nightly, 12/2025 to 2/2026, 8 weeks at full dose. No response (PHQ-9 23 to 23).",
        "Two trials from 2 different agent classes, each at an adequate dose and duration, in the current depressive episode. Both failed."], "surgeon", "Daniel Kim MD   10/9/26")
    save([cover, meds], "E2_fax_reply_coleman_medication_history.pdf", "OCT-09-2026 15:1")

    # F: escalate, clinically not met. Moderate (not severe) depression, one medication trial, therapy is helping, and epilepsy.
    P = person("Derek Holloway", "02/19/1984", 42, "M", "MBR-46006", "(614) 555-0174", )
    P.update(icd="F33.1 (MDD, recurrent, moderate)", dx="Major depressive disorder, recurrent, moderate", phq=12, hamd=16, episode="4 months")
    save([request_form(P, LEFT, 4),
          psych_eval(P, "Medication trials this episode: one only. Escitalopram (SSRI) 10 mg daily x 5 wks, responding well and tolerated. No other antidepressant tried. No prior rTMS. Not on ECT.",
                     "Psychotherapy: CBT in progress, 8 sessions so far, PHQ-9 improved from 17 to 12.",
                     "Plan: I examined the patient and reviewed the record. He is improving on escitalopram and CBT, but asks for TMS so he can stop medication. I order left prefrontal rTMS, 10 Hz, 36 sessions. I am experienced in administering TMS and will directly supervise every treatment.",
                     "Safety: epilepsy (generalized seizures), on levetiracetam, last seizure 3/2026. No psychosis. No implanted devices."),
          therapy(P, [("6/01/26", "17", "Session 1, intake"), ("7/06/26", "15", "Session 4"), ("8/10/26", "13", "Session 6"), ("9/14/26", "12", "Session 8, ongoing")],
                  "Summary: weekly CBT, 8 sessions so far. Steady improvement on the PHQ-9 (17 to 12). Recommend continuing CBT. - H. Brooks PsyD"),
          safety(P, ["History of epilepsy: generalized tonic-clonic seizures, on levetiracetam 1000 mg BID. Last seizure March 2026.",
                     "No psychotic disorder. No dementia, stroke or CNS tumor. No implanted devices. Dental fillings only.",
                     "Patient read and signed the TMS consent."])], "F_escalate_holloway_criteria_not_met.pdf")

    # G: escalate, clinically met but the wrong kind of TMS. Right prefrontal low-frequency rTMS; the LCD covers left prefrontal rTMS only.
    P = person("Sandra Whitaker", "09/08/1975", 51, "F", "MBR-46007", "(614) 555-0175")
    save([request_form(P, "Right prefrontal low-frequency (1 Hz) rTMS, initial course", 4),
          psych_eval(P, TWO_MEDS, "Psychotherapy: 16 sessions of CBT, no significant improvement (records attached).",
                     "Plan: I examined the patient and reviewed the full record. Because of her severe comorbid anxiety and chronic migraine, I order RIGHT prefrontal low-frequency (1 Hz) rTMS, 36 sessions, not left-sided high-frequency stimulation. I am experienced in TMS and will directly supervise every treatment.",
                     SAFE),
          therapy(P, CBT_ROWS, CBT_SUM), safety(P, SAFE_PAGE)], "G_escalate_whitaker_right_sided_not_covered.pdf")
