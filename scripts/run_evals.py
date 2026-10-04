"""Runs the multi-illness evals with the real reader and prints a plain report.
Usage:  python scripts/run_evals.py          (writes evals/reports/multi_<date>.json too)
Costs real AI calls: about 9 packets x (3 reads + 1 check). Takes a few minutes."""
import os, sys, json, time
from dotenv import load_dotenv
load_dotenv(".env")
from pipeline.multi_eval import run_multi, ADVERSARIAL

adv = "--adversarial" in sys.argv  # the hard packets written by a separate AI session
out = run_multi(manifest_path=ADVERSARIAL) if adv else run_multi()
os.makedirs("evals/reports", exist_ok=True)
path = f"evals/reports/{'adversarial' if adv else 'multi'}_{time.strftime('%Y%m%d_%H%M')}.json"
json.dump(out, open(path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
cr, hr, fl = out["completeness_recall"], out["hallucination_rate"], out["flagged_uncertain"]
print(f"Recommendation matched the expected one: {out['action_matches']}/{out['packets_total']}")
print(f"Found it when it was really there:       {cr['correct']}/{cr['total']} ({cr['pct']}%)")
print(f"Claimed it when absent or ruled out:     {hr['count']}/{hr['total']} ({hr['pct']}%)")
print(f"Sent to the nurse as 'not sure':         {fl['count']}/{fl['total']} ({fl['pct']}%)")
print(f"Wrong values:                            {out['wrong_values']}")
print(f"The system never denied:                 {out['zero_denials']}")
d = out["decision"]; c = d["counts"]
print()
print("DECISION METRICS  (positive group = 'needs a person': pend, escalate or verify)")
print(f"  Recall    (needed a person and was flagged):     {c['TP']}/{c['TP'] + c['FN']} = {d['recall_needs_person']}%   wrong approvals: {d['wrong_approvals']}")
print(f"  Precision (flagged and really needed a person):  {c['TP']}/{c['TP'] + c['FP']} = {d['precision_needs_person']}%   over-flags: {d['over_flags']}")
print(f"  Approve precision (approved and was clean):      {c['TN']}/{c['TN'] + c['FN']} = {d['approve_precision']}%")
print(f"  Approve recall    (clean and was approved):      {c['TN']}/{c['TN'] + c['FP']} = {d['approve_recall']}%")
print(f"  Exact recommendation match:                      {d['exact_match']}%")
print()
for r in out["results"]:
    print(("PASS" if r["action_matches"] else "FAIL"), r["file"], f"expected={r['expected_action']} actual={r['actual_action']} ({r['seconds']}s)")
    for f in r["facts"]:
        if f["outcome"] != "correct":
            print(f"      {f['outcome']:18s} {f['fact']:32s} truth={f['truth']:8s} status={f['status']:8s} got={f['got']} expected={f['expected']}")
if out.get("by_category"):
    print("\nBy category (recommendation matched / packets):")
    for c, v in out["by_category"].items():
        print(f"  {c:28s} {v['action_matches']}/{v['packets']}")
print("\nreport saved:", path)
