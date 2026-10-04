"""Date arithmetic for the reader. The model reads dates off the page. This code does the counting.

A language model reads "NSTEMI on 08/27/2026" well and counts "41 days before 10/07/2026" badly. So the model returns
the dates it found, and these functions decide what is inside a window. The window rules come from the policy (NCD 20.4:
no heart attack in the last 40 days, no bypass or stent in the last 3 months, measured to the planned implant date).
"""
import re
from datetime import date, datetime

MI_DAYS = 40
REVASC_MONTHS = 3


def parse(s):
    """Accepts 2026-08-27, 08/27/2026, 8/27/26. Returns a date or None. Never guesses a day or a month it cannot see."""
    if not s or not isinstance(s, str):
        return None
    s = s.strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%B %d, %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", s)
    return date(int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None


def months_before(d, n):
    """The date n calendar months earlier (day clamped to the month's length)."""
    y, mo = d.year, d.month - n
    while mo < 1:
        mo += 12
        y -= 1
    for day in (d.day, 30, 29, 28):
        try:
            return date(y, mo, day)
        except ValueError:
            continue


def months_between(start, end):
    return round((end - start).days / 30.4375, 1)


def recent_event(events, admit):
    """events: list of dict(type: heart_attack|stent|bypass, date, what). admit: date of the planned procedure.
    Returns (inside_window: list of described events, outside_window: list, undated: list)."""
    inside, outside, undated = [], [], []
    cutoff_revasc = months_before(admit, REVASC_MONTHS)
    for e in events or []:
        d = parse(e.get("date"))
        if not d:
            undated.append(e)
            continue
        days = (admit - d).days
        if days < 0:
            continue  # after the planned date: not a past event
        hit = days <= MI_DAYS if e.get("type") == "heart_attack" else d > cutoff_revasc
        (inside if hit else outside).append(dict(e, days=days))
    return inside, outside, undated
