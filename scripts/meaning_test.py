"""Tests the second AI check (pipeline/evidence.verify_meaning) on cases where an exact-text match would be fooled.
Makes real AI calls (one batched). Run: python scripts/meaning_test.py"""
import os
from dotenv import load_dotenv
load_dotenv(".env")
import anthropic
from pipeline import evidence as ev

items = [
    dict(id="supports", claim="The value for the most recent ejection fraction is 28.", quote="LVEF 28% by TTE", context="Echo report: LVEF 28% by TTE. Severely reduced."),
    dict(id="negation", claim="The packet states that instability was found.", quote="No evidence of instability", context="Spine imaging, flexion-extension films: No evidence of instability at L4-L5."),
    dict(id="other_value", claim="The value for the most recent ejection fraction is 42.", quote="LVEF 30% by TTE", context="Echo from 2025-11: LVEF 30% by TTE."),
    dict(id="unrelated", claim="The packet documents a shared decision making visit with a decision tool.", quote="Patient counseled on smoking cessation", context="Counseling: Patient counseled on smoking cessation. Return in 2 weeks."),
    dict(id="none_stated", claim="The packet states that there is none: whether any condition rules out an ICD.", quote="No limiting comorbidities; clinically stable", context="Assessment: No limiting comorbidities; clinically stable for outpatient device implant."),
]
want = {"supports": {"supports"}, "negation": {"contradicts"}, "other_value": {"contradicts"}, "unrelated": {"unrelated", "insufficient"}, "none_stated": {"supports", "insufficient"}}  # insufficient is safe: the nurse is asked to check
got = ev.verify_meaning(items, anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"]))
ok = True
for k, w in want.items():
    v = got.get(k, ("(no answer)", ""))
    good = v[0] in w
    ok &= good
    print("PASS" if good else "FAIL", k.ljust(12), v[0].ljust(12), v[1][:90])
print("\nALL MEANING CHECKS PASSED" if ok else "\nSOME CHECKS FAILED")
