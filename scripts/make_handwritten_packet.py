"""Handwritten, faxed bariatric packets: E (Morgan) is a clear approve; F1 + F2 (Bennett) are the pend loop:
F1 has no post-op plan so it pends, F2 is the provider's fax reply with the plan.
Each author writes in a different hand. Every letter is drawn with its own size, tilt and
baseline jitter, so it reads like a pen, not a font. Faxed in fine mode. Image only, no text layer.

Run: python scripts/make_handwritten_packet.py
Out: interview/01_bariatric_surgery/E_*.pdf, F1_*.pdf, F2_*.pdf
"""
import math, os, random
from PIL import Image, ImageDraw, ImageFilter, ImageFont

random.seed(11)
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
W, H, M = 1654, 2339, 130  # A4 at 200 dpi
F = "C:/Windows/Fonts/"
HANDS = {  # one hand per author
    "coordinator": (F + "Inkfree.ttf", 46),
    "surgeon": (F + "BRADHITC.TTF", 46),
    "program": (F + "segoepr.ttf", 38),
    "psych": (F + "mvboli.ttf", 40),
    "pcp": (F + "LHANDW.TTF", 34),
}
PRINT = ImageFont.truetype(F + "arial.ttf", 28)
PRINT_B = ImageFont.truetype(F + "arialbd.ttf", 40)
_fonts = {}


def font(path, size):
    if (path, size) not in _fonts:
        _fonts[(path, size)] = ImageFont.truetype(path, size)
    return _fonts[(path, size)]


def scrawl(img, x, y, text, hand, max_w=None):
    """Write text by hand from (x, y). Wraps at max_w. Returns the y below the last line."""
    path, size = HANDS[hand]
    max_w = max_w or (W - M - x)
    line_h = int(size * 1.75)
    x0, cx, cy = x, x, y
    slope = random.uniform(-0.012, 0.012)
    for word in text.split(" "):
        base = font(path, size)
        if cx + base.getlength(word) > x0 + max_w and cx > x0:
            cx, cy = x0 + random.randint(-6, 6), cy + line_h
            slope = random.uniform(-0.012, 0.012)
        for ch in word:
            s = int(size * random.uniform(0.92, 1.08))
            f = font(path, s)
            cw = max(int(f.getlength(ch)), 1)
            tile = Image.new("L", (cw + 30, s + 40), 255)
            ImageDraw.Draw(tile).text((14, 10), ch, font=f, fill=random.randint(0, 40), stroke_width=random.choice((0, 1)), stroke_fill=20)
            tile = tile.rotate(random.uniform(-4, 4), fillcolor=255, resample=Image.BICUBIC, expand=True)
            dy = (cx - x0) * slope + random.uniform(-2.5, 2.5) + 3 * math.sin(cx / 140.0)
            img.paste(0, (int(cx - 14), int(cy + dy - 10)), Image.eval(tile, lambda p: 255 - p))
            cx += cw * random.uniform(0.94, 1.04)
        cx += base.getlength(" ") * random.uniform(0.9, 1.4)
    return cy + line_h


def page(title, sub):
    img = Image.new("L", (W, H), 255)
    d = ImageDraw.Draw(img)
    d.text((M, 110), "Riverbend Bariatric Surgery Center", font=PRINT_B, fill=0)
    d.text((M, 165), "2200 Riverbend Pkwy, Dayton, OH 45431   ·   Ph (937) 555-0120   ·   Fax (937) 555-0121", font=PRINT, fill=0)
    d.line((M, 215, W - M, 215), fill=0, width=3)
    d.text((M, 240), title, font=PRINT_B, fill=0)
    if sub:
        d.text((M, 295), sub, font=PRINT, fill=0)
    d.text((M, H - 120), "Made-up data for a software prototype. Not a real patient.", font=PRINT, fill=0)
    return img, d


def field(img, d, y, label, value, hand="coordinator", lw=330):
    d.text((M, y + 18), label, font=PRINT, fill=0)
    d.line((M + lw, y + 62, W - M, y + 62), fill=0, width=2)
    scrawl(img, M + lw + 10, y, value, hand)
    return y + 88


def checkbox(img, d, x, y, label, ticked):
    d.rectangle((x, y + 4, x + 32, y + 36), outline=0, width=3)
    if ticked:
        scrawl(img, x + 2, y - 14, "X", "coordinator")
    d.text((x + 45, y + 4), label, font=PRINT, fill=0)


MORGAN = dict(name="Teresa Morgan", dob="06/11/1976", age=50, mid="MBR-41004", addr="41 Willow Bend Dr, Kettering OH 45429", phone="(937) 555-0177",
              ht=64, wt=268, bmi="46.0", start=274, a1c="8.2", ahi=31, bp="148/92", req="10/07/2026", admit="11/18/2026", stamp="OCT-07-2026 09:1")
BENNETT = dict(name="Gloria Bennett", dob="03/02/1972", age=54, mid="MBR-41005", addr="907 Shiloh Springs Rd, Dayton OH 45415", phone="(937) 555-0184",
               ht=63, wt=259, bmi="45.9", start=265, a1c="7.9", ahi=28, bp="150/94", req="10/07/2026", admit="11/24/2026", stamp="OCT-07-2026 10:2")


def request_form(P, n_pages):
    p1, d = page("Prior Authorization Request - Inpatient Admission", "Health plan: Humana Medicare Advantage   ·   Plan ID H5216-014-000   ·   Standard pre-service review")
    y = 360
    for lab, val in [("Date of request:", P["req"]), ("Member name:", P["name"]), ("Date of birth:", f"{P['dob']}   (age {P['age']})   Sex: F"),
                     ("Member ID:", P["mid"]), ("Address:", P["addr"]), ("Member phone:", P["phone"]),
                     ("Requesting MD:", "Dr. Alan Reyes, MD - Bariatric Surgery"), ("NPI:", "1457382096"),
                     ("Requested service:", "Lap Roux-en-Y gastric bypass"), ("CPT:", "43644"),
                     ("ICD-10:", "E66.01, Z68.43, E11.65, I10, G47.33"), ("Planned admit date:", P["admit"]),
                     ("Expected stay:", "2 midnights"), ("Submitted by:", "Sheila Brandt, Auth Coordinator  (937) 555-0120")]:
        y = field(p1, d, y, lab, val)
    d.text((M, y + 20), "Level of care requested:", font=PRINT, fill=0)
    checkbox(p1, d, M + 360, y + 16, "INPATIENT", True)
    checkbox(p1, d, M + 640, y + 16, "Outpatient", False)
    checkbox(p1, d, M + 920, y + 16, "Observation", False)
    d.text((M, y + 90), f"Place of service: hospital, inpatient (acute care). Supporting clinical documentation attached ({n_pages} pages incl. this request).", font=PRINT, fill=0)
    return p1


def consult(P):
    p2, d = page("Surgical Consultation - Bariatric Surgery", f"Date of consultation: 09/22/2026     Patient: {P['name']}, age {P['age']}, F")
    y = 370
    for para in [
        "Hx: Referred by PCP for surgical tx of severe obesity. Wt above 240 lb for 12 yrs. Type 2 diabetes (dx 2018) on metformin 1000 mg BID + semaglutide. Hypertension on lisinopril 20 mg daily. Obstructive sleep apnea on CPAP. Also GERD.",
        f"Ht {P['ht']} in. Wt {P['wt']} lb. BMI {P['bmi']} kg/m2 (measured in clinic 9/22/2026).",
        f"Prior tx: completed a 7-month physician-supervised weight mgmt program (Riverbend Medical Weight Mgmt) 1/20/2026 to 8/25/2026, monthly visits, RD counseling, documented calorie-controlled diet. {P['start']} lb to {P['wt']} lb. Unable to maintain a healthy weight despite adequate participation.",
        "Assessment: severe obesity with comorbidities (T2DM, HTN, OSA, GERD). No prior bariatric surgery. Non-smoker. No eating disorder. No cardiac, hepatic or autoimmune disease.",
        "Plan: Lap Roux-en-Y gastric bypass. Bypass over sleeve due to GERD + diabetes. Pt educated on the operation, risks, lifestyle changes and lifelong follow-up; understands and is willing. I certify pt made a diligent effort to achieve a healthy body weight.",
        "Dr. Alan Reyes, MD. Board certified, American Board of Surgery. Fellowship trained in bariatric surgery.",
    ]:
        y = scrawl(p2, M, y, para, "surgeon") + 22
    return p2


def visit_log(P):
    p3, d = page("Medical Weight Management Program - Visit Log", "Riverbend Medical Weight Management   ·   Dr. Nina Patel, MD   ·   Rachel Owens, RD")
    cols = [M, M + 330, M + 560]
    for x, h in zip(cols, ["Date", "Weight", "Visit"]):
        d.text((x, 370), h, font=PRINT_B, fill=0)
    d.line((M, 425, W - M, 425), fill=0, width=2)
    y, s, w = 445, P["start"], P["wt"]
    wts = [s, s - 2, s - 3, s - 2, s - 4, s - 4, w + 1, w]
    for (date, visit), wt in zip([("1/20/26", "Intake, 1500 kcal plan, RD"), ("2/24/26", "RD f/u, food log reviewed"), ("3/24/26", "MD visit, activity plan"),
                                  ("4/28/26", "RD f/u"), ("5/26/26", "MD visit"), ("6/23/26", "RD f/u"), ("7/28/26", "RD f/u"), ("8/25/26", "Final visit, program completed")], wts):
        for x, v in zip(cols, (date, f"{wt} lb", visit)):
            scrawl(p3, x, y, v, "program")
        d.line((M, y + 72, W - M, y + 72), fill=0, width=1)
        y += 92
    scrawl(p3, M, y + 30, f"Summary: attended 8 of 8 visits, kept a food log. Physician + RD supervised diet program. Wt loss not sustained beyond {s - w} lb despite adequate participation. - N. Patel MD", "program")
    return p3


def psych(P):
    p4, d = page("Psychological Evaluation - Pre-bariatric", "Date: 09/04/2026     Evaluator: Dr. Susan Lindgren, PhD, Clinical Psychologist")
    scrawl(p4, M, 380, "No history of psychiatric disorder. No psychotropic meds. PHQ-9 score 2, anxiety screen negative. No binge eating disorder or bulimia. No alcohol or substance use disorder. No tobacco use. Pt understands the operation, diet changes and need for lifelong follow-up; capable and willing. CLEARED from a psychological standpoint to proceed with bariatric surgery.  - S. Lindgren PhD", "psych")
    return p4


def pcp(P):
    p5, d = page("Primary Care Note - Comorbidity Documentation", "Date: 09/10/2026     Physician: Dr. Marcus Hill, MD")
    scrawl(p5, M, 380, f"Type 2 diabetes: A1c {P['a1c']}% on metformin + semaglutide. Hypertension: BP {P['bp']} on lisinopril. OSA: AHI {P['ahi']} on 2025 sleep study, CPAP nightly. Not easily controlled with non-invasive means; considerable risk to function and survival if untreated. EKG normal sinus rhythm, no cardiac hx. No COPD. Cleared for general anesthesia, ASA 3.  - M. Hill MD", "pcp")
    return p5


def postop(P, date="10/7/26"):
    p6, d = page("Postoperative Care Plan", f"Patient: {P['name']}   ·   Member ID {P['mid']}")
    y = scrawl(p6, M, 370, "Post-op care by the operating surgeon immediately after surgery and through the global period. Follow-up with the bariatric team at 2 wks, 3 mo, 6 mo and 12 mo (at least 3 visits in yr 1). Lifetime follow-up for diet, vitamin + mineral supplements, exercise and lifestyle, with counseling and a monthly support group supervised by Dr. Reyes.", "surgeon")
    scrawl(p6, M, y + 60, f"Alan Reyes MD   {date}", "surgeon")
    return p6


def reply_cover(P, question):
    """The provider's fax back to Humana: a handwritten cover note that answers the pend."""
    img = Image.new("L", (W, H), 255)
    d = ImageDraw.Draw(img)
    d.text((M, 110), "Riverbend Bariatric Surgery Center", font=PRINT_B, fill=0)
    d.text((M, 165), "2200 Riverbend Pkwy, Dayton, OH 45431   ·   Ph (937) 555-0120   ·   Fax (937) 555-0121", font=PRINT, fill=0)
    d.line((M, 215, W - M, 215), fill=0, width=3)
    d.text((M, 250), "FAX  -  RESPONSE TO REQUEST FOR INFORMATION", font=PRINT_B, fill=0)
    y = 340
    for lab, val in [("To:", "Humana UM / Prior Auth"), ("From:", "Sheila Brandt, Auth Coordinator"), ("Date:", "10/09/2026"),
                     ("Re member:", P["name"]), ("Member ID:", P["mid"]), ("Request:", "Lap Roux-en-Y gastric bypass, CPT 43644")]:
        y = field(img, d, y, lab, val)
    d.text((M, y + 30), "Your question:", font=PRINT, fill=0)
    y = scrawl(img, M, y + 75, question, "coordinator") + 20
    d.text((M, y + 10), "Our answer:", font=PRINT, fill=0)
    y = scrawl(img, M, y + 55, "Post-op care plan from Dr. Reyes is attached on the next page. He provides post-op care himself, 3+ follow-up visits in year 1, lifetime follow-up and a support group. Please call (937) 555-0120 with any other questions. Thanks!  - Sheila", "coordinator")
    d.text((M, H - 120), "Made-up data for a software prototype. Not a real patient.", font=PRINT, fill=0)
    return img


def fax(img, n, total, stamp):
    img = img.rotate(random.uniform(-0.9, 0.9), fillcolor=255, resample=Image.BILINEAR)
    img = img.resize((int(W * 204 / 200), int(H * 196 / 200)), Image.BILINEAR).resize((W, H), Image.BILINEAR)  # fine mode
    img = img.filter(ImageFilter.GaussianBlur(0.6))
    px = img.load()
    for _ in range(int(W * H * 0.0015)):
        px[random.randrange(W), random.randrange(H)] = 0
    img = img.point(lambda p: 0 if p < 160 else 255).convert("1")
    ImageDraw.Draw(img).text((30, 20), f"{stamp}{n}  FROM: RIVERBEND BARIATRIC  9375550121    TO: HUMANA UM    P.{n:03d}/{total:03d}",
                             font=ImageFont.truetype(F + "cour.ttf", 28), fill=0)
    return img




def save(pages, name, stamp):
    out = os.path.join(ROOT, "interview", "01_bariatric_surgery", name)
    faxed = [fax(p, i + 1, len(pages), stamp) for i, p in enumerate(pages)]
    faxed[0].save(out, save_all=True, append_images=faxed[1:], resolution=200)
    print("wrote", name, len(pages), "pages")


if __name__ == "__main__":
    P = MORGAN
    save([request_form(P, 6), consult(P), visit_log(P), psych(P), pcp(P), postop(P)], "E_handwritten_morgan_gastric_bypass.pdf", P["stamp"])
    P = BENNETT  # the pend loop: the packet has no post-op plan, so it pends; the provider's fax reply sends it
    save([request_form(P, 5), consult(P), visit_log(P), psych(P), pcp(P)], "F1_pend_bennett_no_postop_plan.pdf", P["stamp"])
    q = "Please send the postoperative care plan: who provides post-op care, the follow-up visits planned in the first year, and the lifetime follow-up plan."
    save([reply_cover(P, q), postop(P, "10/9/26")], "F2_fax_reply_bennett_postop_plan.pdf", "OCT-09-2026 14:0")
