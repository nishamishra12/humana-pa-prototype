"""Two packets to upload before the demo and keep: a bariatric approve and a TMS escalation.
New patients, so they never clash with test cases. Same generators as the tested sets.

Run: python scripts/make_demo_preload.py
Out: interview/01_bariatric_surgery/DEMO_approve_martinez_gastric_bypass.pdf
     interview/06_tms_depression/DEMO_escalate_pierce_right_sided_not_covered.pdf
"""
import os, random
import make_handwritten_packet as B
import make_tms_packets as T

# bariatric: handwritten and faxed like Morgan, every requirement met, gastric bypass (nationally covered)
random.seed(41)
P = dict(name="Angela Martinez", dob="09/14/1969", age=57, mid="MBR-41006", addr="2215 Salem Ave, Dayton OH 45406", phone="(937) 555-0191",
         ht=63, wt=262, bmi="46.4", start=268, a1c="8.4", ahi=33, bp="152/94", req="10/07/2026", admit="11/20/2026", stamp="OCT-07-2026 08:5")
pages = [B.request_form(P, 6), B.consult(P), B.visit_log(P), B.psych(P), B.pcp(P), B.postop(P)]
out = os.path.join(B.ROOT, "interview", "01_bariatric_surgery", "DEMO_approve_martinez_gastric_bypass.pdf")
faxed = [B.fax(p, i + 1, len(pages), P["stamp"]) for i, p in enumerate(pages)]
faxed[0].save(out, save_all=True, append_images=faxed[1:], resolution=200)
print("wrote", os.path.basename(out), len(pages), "pages")

# TMS: meets every clinical rule, but the request is right prefrontal 1 Hz rTMS. The LCD covers left prefrontal rTMS only.
random.seed(43)
Q = T.person("Lorraine Pierce", "06/22/1973", 53, "F", "MBR-46008", "(614) 555-0176")
T.save([T.request_form(Q, "Right prefrontal low-frequency (1 Hz) rTMS, initial course", 4),
        T.psych_eval(Q, T.TWO_MEDS, "Psychotherapy: 16 sessions of CBT, no significant improvement (records attached).",
                     "Plan: I examined the patient and reviewed the full record. Because of her severe comorbid anxiety and chronic migraine, I order RIGHT prefrontal low-frequency (1 Hz) rTMS, 36 sessions, not left-sided high-frequency stimulation. I am experienced in TMS and will directly supervise every treatment.",
                     T.SAFE),
        T.therapy(Q, T.CBT_ROWS, T.CBT_SUM), T.safety(Q, T.SAFE_PAGE)], "DEMO_escalate_pierce_right_sided_not_covered.pdf")
