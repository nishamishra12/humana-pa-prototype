"""Scores the multi-illness test packets (ICD and bariatric) against hand-written ground truth.

Same idea as the held-out set (pipeline/holdout_eval.py): completeness recall and hallucination rate are
reported separately, never blended. Ground truth lives in evals/multi_manifest.json. For each fact the
packet either has it (present), says nothing (absent), or rules it out (negated).

Outcomes per fact:
  correct                    read it right (right value if present; "missing" if absent; "none" if negated)
  flagged_uncertain          the AI said "not sure" and sent it to the nurse. Safe, but a cost.
  false_negative             it was there, and we said missing (or missed that it was ruled out)
  wrong_value                found, but the wrong number or choice
  false_positive             it was absent or ruled out, and we claimed it was found. The dangerous one.
"""
import json, os, time
from concurrent.futures import ThreadPoolExecutor
from .ingest import _ingest_local, ingest
from .run import extract
from .engine import analyze
from .procedures import library, defs_by_key
from . import telemetry as tel

ROOT = os.path.join(os.path.dirname(__file__), "..")
MANIFEST = os.path.join(ROOT, "evals", "multi_manifest.json")
ADVERSARIAL = os.path.join(ROOT, "evals", "adversarial_manifest.json")  # written by a separate AI session, see docs/ADVERSARIAL_PACKET_PROMPT.md


def _value_ok(kind, want, got):
    if want is None:
        return True
    if kind == "number":
        try:
            return abs(float(want) - float(got)) < 0.051
        except (TypeError, ValueError):
            return False
    if kind == "enum":
        return str(want).lower() == str(got).lower()
    if kind == "list":
        got_l = [str(x).lower() for x in (got or [])]
        return any(str(w).lower() in g or g in str(w).lower() for w in want for g in got_l) if want else True
    return True  # free text is judged by the status, and a human reads the page


def classify(kind, truth, want, status, got):
    if status == "unsure":
        return "flagged_uncertain"
    if status == "implied" and truth == "absent":
        return "implied_not_stated"  # 'implied' is the product's own state for "gestured at, no usable value". The nurse is asked, so it is not a claim.
    if truth == "present":
        if status != "found":
            return "false_negative"
        return "correct" if _value_ok(kind, want, got) else "wrong_value"
    if truth == "negated":
        return "correct" if status == "none" else "false_positive" if status == "found" else "false_negative"
    return "correct" if status == "missing" else "false_positive"  # absent


def case_class(expected, actual):
    """Positive group = 'needs a person' (pend, escalate or verify). Flagged = the system did not approve.
    TP caught a case that needed a person. FN approved a case that needed a person (the dangerous miss).
    FP flagged a clean case (costs nurse time). TN approved a clean case."""
    needs, flagged = expected != "approve", actual != "approve"
    return ("TP" if flagged else "FN") if needs else ("FP" if flagged else "TN")


def decision_metrics(results):
    c = {k: 0 for k in ("TP", "FN", "FP", "TN")}
    for r in results:
        c[case_class(r["expected_action"], r["actual_action"])] += 1
    pct = lambda a, b: round(100 * a / b, 1) if b else None
    return dict(counts=c,
                recall_needs_person=pct(c["TP"], c["TP"] + c["FN"]),   # of the cases that needed a person, how many were flagged
                precision_needs_person=pct(c["TP"], c["TP"] + c["FP"]),  # of the cases flagged, how many really needed a person
                wrong_approvals=c["FN"], over_flags=c["FP"],
                approve_precision=pct(c["TN"], c["TN"] + c["FN"]),     # of the cases approved, how many were clean
                approve_recall=pct(c["TN"], c["TN"] + c["FP"]),        # of the clean cases, how many were approved
                exact_match=pct(sum(1 for r in results if r["action_matches"]), len(results)))


def run_one(m, run_id=None, eval_set="multi", label=None):
    """Runs one packet. When Honeycomb is on, the case trace and the scored result land in the same trace,
    so a wrong answer can be opened and read step by step."""
    with tel.span("eval.packet", **{"eval.run_id": run_id, "eval.run_label": label, "eval.set": eval_set, "eval.file": m["file"], "eval.category": m.get("category"),
                                    "eval.expected_action": m["expected_action"]}):
        out = _run_one(m)
        cls = case_class(m["expected_action"], out["actual_action"])
        tel.add(**{"eval.action_matches": out["action_matches"], "eval.actual_action": out["actual_action"], "eval.seconds": out["seconds"],
                   "eval.class": cls, "eval.needs_person": m["expected_action"] != "approve", "eval.flagged": out["actual_action"] != "approve"})
        for f in out["facts"]:
            tel.event("eval.fact", **{"eval.run_id": run_id, "eval.set": eval_set, "eval.fact_key": f["fact"], "eval.truth": f["truth"],
                                      "eval.outcome": f["outcome"], "eval.status": f["status"], "eval.category": m.get("category"),
                                      "eval.is_error": f["outcome"] in ("false_positive", "false_negative", "wrong_value")})
        return out


def _run_one(m):
    t0 = time.time()
    path = os.path.join(ROOT, "packets", m["file"])
    els = ingest(path)[0] if m.get("needs_ocr") else _ingest_local(path)
    facts = extract(els)
    res = analyze(facts)
    defs = defs_by_key(library()["procedures"][m["procedure"]])
    rows = []
    for key, gt in m["facts"].items():
        if key not in defs:
            continue  # an author may add a key we do not read; ignore it
        f = facts.get(key, {"status": "missing"})
        rows.append(dict(fact=key, truth=gt["truth"], expected=gt.get("value"), why=gt.get("why"), status=f["status"], got=f.get("value"),
                         page=f.get("page"), checked=bool(f.get("checked")), outcome=classify(defs[key]["kind"], gt["truth"], gt.get("value"), f["status"], f.get("value"))))
    return dict(file=m["file"], label=m["label"], member=m["member"], procedure=m["procedure"], note=m["note"], seconds=round(time.time() - t0, 1),
                expected_action=m["expected_action"], actual_action=res["action"], action_matches=res["action"] == m["expected_action"],
                extractor=facts.get("_extractor"), category=m.get("category"), facts=rows)


def run_multi(workers=3, manifest_path=MANIFEST, label=None):
    manifest = json.load(open(manifest_path, encoding="utf-8"))
    tel.init()
    run_id = time.strftime("%Y%m%d-%H%M%S")
    eval_set = "adversarial" if manifest_path == ADVERSARIAL else "multi"
    tel.set_defaults(**{"eval.run_id": run_id, "eval.set": eval_set, "eval.run_label": label})
    try:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            results = list(pool.map(tel.bind(lambda m: run_one(m, run_id, eval_set, label)), manifest))
    finally:
        tel.flush()
        tel.set_defaults()
    allf = [f for r in results for f in r["facts"]]
    present = [f for f in allf if f["truth"] == "present"]
    guarded = [f for f in allf if f["truth"] in ("absent", "negated")]
    hits = sum(1 for f in present if f["outcome"] == "correct")
    flagged = sum(1 for f in allf if f["outcome"] == "flagged_uncertain")
    halluc = [f for f in guarded if f["outcome"] == "false_positive"]
    return dict(
        results=results, decision=decision_metrics(results), packets_total=len(results), action_matches=sum(1 for r in results if r["action_matches"]),
        completeness_recall=dict(correct=hits, total=len(present), pct=round(100 * hits / len(present), 1) if present else None),
        hallucination_rate=dict(count=len(halluc), total=len(guarded), pct=round(100 * len(halluc) / len(guarded), 1) if guarded else None),
        flagged_uncertain=dict(count=flagged, total=len(allf), pct=round(100 * flagged / len(allf), 1) if allf else None),
        wrong_values=sum(1 for f in allf if f["outcome"] == "wrong_value"),
        by_category={c: dict(packets=len(rs), action_matches=sum(1 for r in rs if r["action_matches"]))
                     for c in sorted({r["category"] for r in results if r.get("category")})
                     for rs in [[r for r in results if r.get("category") == c]]},
        zero_denials=all(r["actual_action"] in ("approve", "pend", "escalate", "verify") for r in results))
