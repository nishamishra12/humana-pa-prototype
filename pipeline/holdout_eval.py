"""M6: scores the held-out adversarial set against hand-annotated ground truth.

Reports completeness recall and a hallucination rate as two separate numbers (per D-007),
not one blended accuracy figure. Reused by scripts/run_holdout.py (CLI) and the /api/evals
endpoint (UI) so both see identical results.
"""
import json, os
from .run import process

ROOT = os.path.join(os.path.dirname(__file__), "..")
MANIFEST = os.path.join(ROOT, "evals", "holdout_manifest.json")


def _classify(truth, status, expected_value, extracted_value):
    found = status == "found"
    if truth == "present":
        if not found:
            return "false_negative_implied" if status in ("implied", "unsure") else "false_negative"
        if expected_value is not None and extracted_value is not None and extracted_value != expected_value:
            return "wrong_value"
        return "correct"
    # truth is "absent" or "negated": extractor must NOT claim found
    return "false_positive_hallucination" if found else "correct"


def run_holdout(local_only=False):
    manifest = json.load(open(MANIFEST, encoding="utf-8"))
    results = []
    for m in manifest:
        path = os.path.join(ROOT, "packets", m["file"])
        els, engine, facts, analysis = process(path, local=local_only)
        fact_results = []
        for key, gt in m["facts"].items():
            status = facts.get(key, {"status": "missing"})["status"]
            extracted_value = facts.get(key, {}).get("value")
            fact_results.append(dict(fact=key, truth=gt["truth"], expected_value=gt.get("value"),
                                     why=gt["why"], critical=gt.get("critical"), extractor_status=status,
                                     extracted_value=extracted_value,
                                     outcome=_classify(gt["truth"], status, gt.get("value"), extracted_value)))
        results.append(dict(file=m["file"], label=m["label"], member=m["member"], note=m["note"],
                            engine=engine, expected_action=m["expected_action"], actual_action=analysis["action"],
                            action_matches=analysis["action"] == m["expected_action"], facts=fact_results))

    all_facts = [f for r in results for f in r["facts"]]
    present = [f for f in all_facts if f["truth"] == "present"]
    guarded = [f for f in all_facts if f["truth"] in ("absent", "negated")]
    recall_hits = sum(1 for f in present if f["outcome"] == "correct")
    hallucinations = [f for f in guarded if f["outcome"] == "false_positive_hallucination"]

    return dict(
        results=results,
        packets_total=len(results),
        action_matches=sum(1 for r in results if r["action_matches"]),
        completeness_recall=dict(correct=recall_hits, total=len(present),
                                 pct=round(100 * recall_hits / len(present), 1) if present else None),
        hallucination_rate=dict(hallucinated=len(hallucinations), total=len(guarded),
                                pct=round(100 * len(hallucinations) / len(guarded), 1) if guarded else None),
        hallucination_detail=[dict(file=r["file"], member=r["member"], fact=f["fact"], why=f["why"], critical=f["critical"])
                              for r in results for f in r["facts"] if f["outcome"] == "false_positive_hallucination"],
    )


if __name__ == "__main__":
    import sys
    out = run_holdout(local_only="--local" in sys.argv)
    print(f"Action matched expectation: {out['action_matches']}/{out['packets_total']}")
    cr = out["completeness_recall"]
    print(f"Completeness recall (found it when it was really there): {cr['correct']}/{cr['total']} ({cr['pct']}%)")
    hr = out["hallucination_rate"]
    print(f"Hallucination rate (claimed found when absent/negated): {hr['hallucinated']}/{hr['total']} ({hr['pct']}%)")
    print()
    for r in out["results"]:
        mark = "PASS" if r["action_matches"] else "FAIL"
        print(f"[{mark}] {r['member']} ({r['label']}) -- engine={r['engine']} expected={r['expected_action']} actual={r['actual_action']}")
        for f in r["facts"]:
            if f["outcome"] != "correct":
                print(f"         {f['outcome']:28s} {f['fact']:22s} truth={f['truth']:8s} extractor={f['extractor_status']}")
