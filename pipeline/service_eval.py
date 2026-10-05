"""Evaluation of one service, run by the ML team and shown to the policy owner as read-only status.

The ML team owns the labelled test packets and the tuning of the AI reader. The policy owner does not build packets or run this.
An evaluation is stored with a fingerprint of the service's key facts and rules, so the screen can say when the policies have changed since it ran.
"""
import hashlib, json, os, tempfile
from datetime import datetime, timezone

from . import multi_eval
from .procedures import library


def fingerprint(lib, key):
    """A short hash of what the AI reader looks for and what the rules check for this service. Wording of the questions is left out."""
    proc = lib["procedures"][key]
    pols = {p["id"]: p for p in lib["policies"]}
    facts = [{k: v for k, v in d.items() if k not in ("ask", "hint", "phrase", "from_policy")} for d in sorted(proc["facts"], key=lambda d: d["key"])]
    rules = {pid: sorted(pols[pid].get("criteria", []), key=lambda c: c["id"]) for pid in sorted(proc.get("policies", [])) if pid in pols}
    return hashlib.sha256(json.dumps([facts, rules], sort_keys=True, default=str).encode()).hexdigest()[:12]


def metrics(result):
    """The numbers the owner sees, from a run_multi result (or a saved report of one)."""
    d = result["decision"]
    return dict(packets=result["packets_total"], decisions_right=result["action_matches"], wrong_approvals=d["wrong_approvals"], over_flags=d["over_flags"],
                recall_needs_person=d["recall_needs_person"], facts_right_pct=result["completeness_recall"]["pct"], made_up_pct=result["hallucination_rate"]["pct"],
                wrong_values=result["wrong_values"], zero_denials=result["zero_denials"])


def for_service(result, key):
    """A result narrowed to one service, with its decision numbers worked out again."""
    rs = [r for r in result["results"] if r["procedure"] == key]
    if not rs:
        return None
    allf = [f for r in rs for f in r["facts"]]
    present = [f for f in allf if f["truth"] == "present"]
    guarded = [f for f in allf if f["truth"] in ("absent", "negated")]
    hits = sum(1 for f in present if f["outcome"] == "correct")
    bad = sum(1 for f in guarded if f["outcome"] == "false_positive")
    pct = lambda a, b: round(100 * a / b, 1) if b else None
    return dict(results=rs, decision=multi_eval.decision_metrics(rs), packets_total=len(rs), action_matches=sum(1 for r in rs if r["action_matches"]),
                completeness_recall=dict(correct=hits, total=len(present), pct=pct(hits, len(present))), hallucination_rate=dict(count=bad, total=len(guarded), pct=pct(bad, len(guarded))),
                wrong_values=sum(1 for f in allf if f["outcome"] == "wrong_value"), zero_denials=all(r["actual_action"] in ("approve", "pend", "escalate", "verify") for r in rs))


def run(key, manifest_path, label=None):
    """Runs the service's packets from a manifest through the whole pipeline. Makes AI calls. Returns the result narrowed to the service."""
    man = [m for m in json.load(open(manifest_path, encoding="utf-8")) if m.get("procedure") == key]
    if not man:
        raise SystemExit(f"No packets for {key} in {manifest_path}")
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(man, f)
    try:
        res = multi_eval.run_multi(manifest_path=f.name, label=label or f"service:{key}")
    finally:
        os.unlink(f.name)
    return for_service(res, key)


def record(conn, key, result, set_name, run_by, label="", source="run", when=None):
    lib = library()
    conn.execute("INSERT INTO service_evals(service,library_version,fingerprint,set_name,run_at,run_by,label,source,metrics) VALUES(?,?,?,?,?,?,?,?,?)",
                 (key, lib.get("version"), fingerprint(lib, key), set_name, when or datetime.now(timezone.utc).isoformat(timespec="seconds"), run_by, label, source, json.dumps(metrics(result))))
    conn.commit()
