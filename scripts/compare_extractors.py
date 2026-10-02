"""M7: side-by-side comparison of the rule-based and LLM extractors on both eval sets.
Run: PYTHONPATH=. python scripts/compare_extractors.py
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline.ingest import ingest
from pipeline.extract import extract_facts as rule_based
from pipeline.extract_llm import extract_facts as llm_based
from pipeline.engine import analyze

ROOT = os.path.join(os.path.dirname(__file__), "..")


def run_both(packet_path):
    els, eng = ingest(packet_path)
    rb_facts = rule_based(els)
    llm_facts = llm_based(els)
    return els, rb_facts, llm_facts, analyze(rb_facts), analyze(llm_facts)


def classify(truth, status, expected_value, extracted_value):
    found = status in ("found",)
    if truth == "present":
        if not found:
            return "false_negative"
        if expected_value is not None and extracted_value is not None and extracted_value != expected_value:
            return "wrong_value"
        return "correct"
    return "false_positive_hallucination" if found else "correct"


def score_holdout(extractor_name, extractor_fn):
    manifest = json.load(open(os.path.join(ROOT, "evals", "holdout_manifest.json"), encoding="utf-8"))
    rows = []
    for m in manifest:
        els, eng = ingest(os.path.join(ROOT, "packets", m["file"]))
        facts = extractor_fn(els)
        res = analyze(facts)
        fact_outcomes = []
        for key, gt in m["facts"].items():
            f = facts.get(key, {"status": "missing"})
            fact_outcomes.append(classify(gt["truth"], f["status"], gt.get("value"), f.get("value")))
        rows.append(dict(member=m["member"], expected=m["expected_action"], actual=res["action"],
                         action_ok=res["action"] == m["expected_action"], fact_outcomes=fact_outcomes))
    present_n = sum(1 for m in manifest for g in m["facts"].values() if g["truth"] == "present")
    guarded_n = sum(1 for m in manifest for g in m["facts"].values() if g["truth"] in ("absent", "negated"))
    correct_present = sum(1 for r in rows for o in r["fact_outcomes"] if o == "correct") - \
        sum(1 for r, m in zip(rows, manifest) for (key, gt), o in zip(m["facts"].items(), r["fact_outcomes"]) if gt["truth"] != "present" and o == "correct")
    # simpler: recompute directly
    recall_hits = sum(1 for r, m in zip(rows, manifest) for (key, gt), o in zip(m["facts"].items(), r["fact_outcomes"]) if gt["truth"] == "present" and o == "correct")
    hallucinations = sum(1 for r, m in zip(rows, manifest) for (key, gt), o in zip(m["facts"].items(), r["fact_outcomes"]) if gt["truth"] in ("absent", "negated") and o == "false_positive_hallucination")
    print(f"\n--- {extractor_name} on M6 held-out set ---")
    for r in rows:
        print(f"  {'PASS' if r['action_ok'] else 'FAIL'}  {r['member']:16s} expected={r['expected']:10s} actual={r['actual']}")
    print(f"  action matched: {sum(r['action_ok'] for r in rows)}/{len(rows)}")
    print(f"  completeness recall: {recall_hits}/{present_n} ({100*recall_hits/present_n:.1f}%)")
    print(f"  hallucination rate: {hallucinations}/{guarded_n} ({100*hallucinations/guarded_n:.1f}%)")
    return dict(action_matched=sum(r['action_ok'] for r in rows), total=len(rows),
               recall=recall_hits / present_n, hallucination=hallucinations / guarded_n)


def score_sanity(extractor_name, extractor_fn):
    manifest = json.load(open(os.path.join(ROOT, "evals", "manifest.json"), encoding="utf-8"))
    print(f"\n--- {extractor_name} on M1-M5 sanity set ---")
    ok = 0
    for m in manifest:
        els, eng = ingest(os.path.join(ROOT, "packets", m["file"]))
        facts = extractor_fn(els)
        res = analyze(facts)
        missing = sorted(q["fact"] for q in res["gate"]["questions"])
        passed = res["action"] == m["expected"]["action"] and missing == sorted(m["expected"]["missing"])
        ok += passed
        print(f"  {'PASS' if passed else 'FAIL'}  {m['file']:35s} expected={m['expected']['action']:10s} actual={res['action']}")
    print(f"  {ok}/{len(manifest)}")
    return ok, len(manifest)


if __name__ == "__main__":
    for name, fn in (("RULE-BASED", rule_based), ("LLM", llm_based)):
        score_sanity(name, fn)
    rb = score_holdout("RULE-BASED", rule_based)
    llm = score_holdout("LLM", llm_based)
    print("\n=== Summary ===")
    print(f"{'Metric':<28s}{'Rule-based':>12s}{'LLM':>12s}")
    print(f"{'Held-out action match':<28s}{rb['action_matched']}/{rb['total']:>10s}{llm['action_matched']}/{llm['total']:>9s}" if False else
          f"{'Held-out action match':<28s}{str(rb['action_matched'])+'/'+str(rb['total']):>12s}{str(llm['action_matched'])+'/'+str(llm['total']):>12s}")
    print(f"{'Completeness recall':<28s}{rb['recall']*100:>11.1f}%{llm['recall']*100:>11.1f}%")
    print(f"{'Hallucination rate':<28s}{rb['hallucination']*100:>11.1f}%{llm['hallucination']*100:>11.1f}%")
