# Prompt for the other AI session: 10 fresh packets for the live test

Paste everything below the line into the same session that wrote the 40 hard packets (or a new one, along with the original prompt).

---

Thank you for the 40 packets. I need **10 new packets** for a live test. A person will upload each one in the app and compare what the AI recommends against your answer. This is a clean test, so these must be new.

**Rules**
1. Same two services, same fact keys, same decision rules and same JSON format as before. Name them `live_001` to `live_010`. Today's date is 2026-10-04. All data is made up.
2. They must be **new**. Do not reuse a patient, a date pattern, a sentence pattern or a trap from the 40 earlier packets. Invent fresh ones.
3. Mix: **6 ICD and 4 bariatric**. Expected actions: **3 approve, 2 pend, 3 escalate, 2 verify**. Make at least **2 of them genuinely hard** (a careful reviewer could get them wrong) and **2 plain clean controls**.
4. Pick traps from the categories before, but also try **two kinds that were not on the list**, for example: a value written in the wrong unit, a corrected addendum that reverses the main note, a signed note by a clinician with no authority for that statement, or an OCR-style typo (an "O" for a zero, an "l" for a one) in a number.
5. Same realism rules: 6 to 8 clinical pages, one document per page, clinician-style writing, the key fact in different places, small typos.
6. Your truth must be exactly right. Recompute every date. Re-read every packet once as a stranger, then fix your own labels. Wrong truth is worse than no packet.

**What to return**
- The 10 JSON objects in the same format as before (I convert them to PDFs).
- **Then, in the chat, a table with one row per packet**: `id | service | expected action | the one-sentence reason | the trap in it`. I will use this table to check the AI in the app one case at a time, so keep each reason to one plain sentence.
- Do not tell me how the AI might behave. Only what the right answer is and why.
