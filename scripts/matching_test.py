"""Tests the evidence matcher (pipeline/evidence.py): fuzzy match, number guard, real text span.
No AI calls. Run: python scripts/matching_test.py"""
from pipeline.ingest import Element
from pipeline import evidence as ev

pages = ev.page_texts([
    Element(1, "NarrativeText", "Echo report. LVEF   28%\nby TTE. Severely reduced systolic function."),
    Element(2, "NarrativeText", "The patient\u2019s hospital-\nization was uneventful.  EF \u2013 30%."),
    Element(3, "NarrativeText", "Surgeon expects a rnulti-day stay for pain control and mobilization."),
    Element(4, "NarrativeText", "Repeat study: LVEF 28 % by TTE after treatment."),
])
ok = True
def check(name, cond):
    global ok
    ok &= bool(cond)
    print(("PASS" if cond else "FAIL"), name)

h = ev.locate_quote("LVEF 28% by TTE", pages)
check("1  exact despite extra spaces and a line break", h and h["page"] == 1 and h["method"] == "exact")
check("2  returns the real text from the page", h and "LVEF   28%\nby TTE" in h["text"])
h = ev.locate_quote("hospitalization was uneventful", pages)
check("3  rejoins a word split across lines", h and h["page"] == 2 and h["method"] == "exact")
h = ev.locate_quote("patient's hospitalization was uneventful. EF - 30%", pages)
check("4  smart quotes and dashes", h and h["page"] == 2)
h = ev.locate_quote("Surgeon expects a multi-day stay for pain control", pages)
check("5  scan noise (rn for m) matches fuzzily", h and h["page"] == 3 and h["method"] == "fuzzy" and h["score"] >= 88)
h = ev.locate_quote("LVEF 38% by TTE", pages)
check("6  a different number never matches", h is None or h["page"] != 1)
h = ev.locate_quote("LVEF 28 % by TTE after treatment", pages)
check("7  spacing around the percent sign still matches (same number)", h and h["page"] == 4)
check("8  an unrelated sentence does not match", ev.locate_quote("Patient denies chest pain at rest and has no syncope.", pages) is None)
check("9  too-short quotes are refused", ev.locate_quote("EF", pages) is None)
print("\nALL MATCHING CHECKS PASSED" if ok else "\nSOME CHECKS FAILED")
