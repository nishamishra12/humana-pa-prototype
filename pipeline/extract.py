"""Rule-based fact extraction with page-and-quote grounding.

This is the fallback extractor: deterministic, no API key, and every fact carries the
page and the exact line it came from. An LLM extractor can replace it behind the same
interface (extract_facts) and must return the same shape.

Fact status:
  found    - stated in the packet, with page and quote
  implied  - suggested but not stated in usable form (e.g. "multi-day stay")
  none     - the packet explicitly says there is nothing (e.g. "no significant comorbidities")
  missing  - not in the packet
"""
import re
from .ingest import Element

COMORBID = [
    ("heart failure", r"heart failure|\bCHF\b"),
    ("COPD", r"\bCOPD\b"),
    ("diabetes", r"diabetes"),
    ("coronary artery disease", r"coronary artery disease|\bCAD\b"),
    ("chronic kidney disease", r"chronic kidney disease|\bCKD\b"),
    ("obesity", r"obesity|BMI\s*(?:3[5-9]|[4-9]\d)"),
    ("sleep apnea", r"sleep apnea|\bOSA\b"),
]
IMAGING = r"radiograph|x-ray|xray|flexion-extension|\bMRI\b|\bCT\b|imaging"
FINDING = {
    "instability": r"instability|anterolisthesis|retrolisthesis|translation",
    "deformity": r"imbalance|scolio|kyphosis|deformity",
    "pseudarthrosis": r"pseudarthrosis|nonunion",
    "neural compression": r"stenosis|herniat|nerve root compression|neural compression",
}
POSTOP = r"telemetry|monitoring|cardiology co-management|respiratory therapy|step-down|\bICU\b"
POSTOP_NONE = r"routine recovery|routine post|no special post|no post-operative needs"
CONS = r"physical therapy|\bPT\b|NSAID|epidural|injection|bracing|conservative|non-operative|nonoperative"
NONE_COMORB = r"no significant comorbidit|no comorbidit|healthy \d+"


def _lines(elements):
    for e in elements:
        for ln in e.text.split("\n"):
            ln = ln.strip()
            if ln:
                yield e.page, ln


def _fact(status, value=None, page=None, quote=None, note=None):
    return dict(status=status, value=value, page=page, quote=quote, note=note)


def _months(text):
    m = re.search(r"(\d+)\s*(months?|weeks?|years?)", text, re.I)
    if not m:
        return None
    n, unit = int(m.group(1)), m.group(2).lower()
    return n if unit.startswith("month") else n * 12 if unit.startswith("year") else round(n / 4.33, 1)


def _flatten_tables(text: str) -> str:
    """OCR output sometimes returns a form as a markdown table ("| Member | Jane Doe |"). Turn each row into "Member: Jane Doe"
    so the same patterns read it. Rows that are only dashes or empty are dropped."""
    out = []
    for ln in text.split("\n"):
        m = re.match(r"^\s*\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*$", ln)
        if m and not re.fullmatch(r"[-: ]+", m.group(1)):
            out.append(f"{m.group(1)}: {m.group(2)}")
        elif not re.fullmatch(r"\s*\|[\s|:-]*", ln):
            out.append(ln)
    return "\n".join(out)


def extract_header(full: str) -> dict:
    """Header fields (member, facility, CPT, procedure, admit date, setting) are boilerplate with a fixed format.
    Regex gets these right on typed packets. A scan read by OCR often puts a whole form on one line and drops the
    colons ("Planned admit date 2026-11-19"), so every colon here is optional and each field stops at the next label."""
    full = _flatten_tables(full)
    facts = {}
    m = re.search(r"(?:^|\s)Member:?\s+((?:(?!Member\b).)+?)\s+DOB:?\s*([\d/-]+)\s*\(age (\d+)\)\s+Member ID:?\s*(\S+)", full, re.S)
    facts["_member"] = dict(name=m.group(1).strip(), dob=m.group(2), age=int(m.group(3)), member_id=m.group(4)) if m else {}
    if not m:  # a form with one labelled line per field ("Member name:", "Date of birth:", "Member ID:"), often handwritten
        name = re.search(r"Member name:?\s*(.+?)(?=\s+(?:Date of birth|DOB|Member ID)\b|\n|$)", full)
        dob = re.search(r"(?:Date of birth|DOB):?\s*([\d/-]+)", full)
        age = re.search(r"\(age (\d+)\)", full)
        mid = re.search(r"Member ID:?\s*([A-Z]{2,4}-?\d+)", full)
        if name and mid:
            facts["_member"] = dict(name=name.group(1).strip(), dob=dob.group(1) if dob else None, age=int(age.group(1)) if age else None, member_id=mid.group(1))
    m = (re.search(r"Requesting facility:?\s*(.+?),\s*Utilization", full)
         or re.search(r"Practice:?\s*(.+?)(?=\s+Phone\b|\n|$)", full))  # longer packets label the facility "Practice:"
    facts["_facility"] = m.group(1).strip() if m else None
    m = re.search(r"(?:CPT|HCPCS)(?:\s*/\s*(?:CPT|HCPCS))?:?\s*(\d{5}|[A-Z]\d{4})(?![\dA-Za-z])", full)
    facts["_cpt"] = m.group(1) if m else None
    m = (re.search(r"Requested service:?\s*(.+?)(?=\s+CPT\b|\n|$)", full)
         or re.search(r"^(Elective inpatient admission,.+?)(?=\s+CPT\b|\n|$)", full, re.M))  # same text, under a heading
    facts["_procedure"] = m.group(1).strip().rstrip(".") if m else None
    m = re.search(r"Planned admi(?:t|ssion) date:?\s*([\d/-]+)", full)
    facts["_admit"] = m.group(1) if m else None
    m = re.search(r"Level of care requested:?\s*(?:[Xx✓☑]\s+)?(\w+)", full)  # skip a ticked box's mark on a form
    facts["_setting"] = m.group(1).lower() if m else None
    return facts




def extract_facts(elements: list[Element]) -> dict:
    lines = list(_lines(elements))
    full = "\n".join(l for _, l in lines)
    facts = extract_header(full)
    facts["_extractor"] = "rule_based"

    # expected length of stay (midnights)
    los = _fact("missing")
    for pg, ln in lines:
        if re.search(r"not documented|not stated|unknown", ln, re.I) and re.search(r"length of stay|LOS", ln, re.I):
            continue
        m = re.search(r"(?:expected|anticipated|planned)\s+(?:length of stay|LOS|hospital stay|stay)\b[^0-9]{0,40}(\d+)\s*(?:midnights?|nights?|days?)", ln, re.I)
        if m:
            los = _fact("found", int(m.group(1)), pg, ln)
            break
        if re.search(r"multi-day|several days|extended stay", ln, re.I) and los["status"] == "missing":
            los = _fact("implied", None, pg, ln, "Suggests more than one day but gives no number of midnights.")
    facts["expected_los_days"] = los

    # comorbidities
    found, first = [], None
    for pg, ln in lines:
        for label, pat in COMORBID:
            if re.search(pat, ln, re.I) and label not in [f[0] for f in found]:
                found.append((label, pg, ln))
    if found:
        facts["comorbidities"] = _fact("found", [f[0] for f in found], found[0][1], found[0][2])
        facts["comorbidities"]["all_cites"] = [dict(label=l, page=p, quote=q) for l, p, q in found]
    else:
        none_line = next(((pg, ln) for pg, ln in lines if re.search(NONE_COMORB, ln, re.I)), None)
        facts["comorbidities"] = _fact("none", [], *none_line) if none_line else _fact("missing")

    # post-operative needs
    po = None
    for pg, ln in lines:
        if re.search(POSTOP_NONE, ln, re.I):
            po = _fact("none", None, pg, ln)
            break
    if po is None:
        for pg, ln in lines:
            if re.search(POSTOP, ln, re.I):
                po = _fact("found", ln, pg, ln)
                break
    facts["post_op_needs"] = po or _fact("missing")

    # indication evidence: an imaging line that reports a qualifying finding
    ind = _fact("missing")
    for pg, ln in lines:
        if re.search(IMAGING, ln, re.I):
            for cat, pat in FINDING.items():
                if re.search(pat, ln, re.I):
                    ind = _fact("found", cat, pg, ln)
                    break
        if ind["status"] == "found":
            break
    if ind["status"] == "missing":
        for pg, ln in lines:
            if re.search(r"|".join(FINDING.values()), ln, re.I) and re.search(r"diagnosis", ln, re.I):
                ind = _fact("implied", None, pg, ln, "A diagnosis is named but no imaging or exam finding documents it.")
                break
    facts["indication_evidence"] = ind

    # conservative treatment
    cons = _fact("missing")
    for pg, ln in lines:
        if re.search(CONS, ln, re.I) and re.search(r"fail|tried|non-?responsive|completed|history of", ln, re.I):
            cons = _fact("found", ln, pg, ln)
            cons["duration_months"] = _months(ln)
            break
    facts["conservative_treatment"] = cons

    sdm = _fact("missing")
    for pg, ln in lines:
        if re.search(r"shared decision", ln, re.I):
            sdm = _fact("found", ln, pg, ln)
            break
    facts["shared_decision_making"] = sdm
    return facts
