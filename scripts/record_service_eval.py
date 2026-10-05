"""For the ML team. Evaluates one service on labelled test packets and records the result, so the policy owner sees its status on the service page.

  python scripts/record_service_eval.py --service icd --manifest evals/multi_manifest.json --by "ML team"      runs the packets (AI calls) and records
  python scripts/record_service_eval.py --service icd --report evals/reports/multi_20261004_0408.json --by "ML team"   records an earlier run, no AI calls

The manifest has the same shape as evals/multi_manifest.json: one entry per packet, with the procedure (service key) and the right answer for each key fact.
Run it again after any change to the service's policies or key facts, or to the AI reader. The service page shows when the policies changed since the last run.
"""
import argparse, json, os, re, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app import db
from pipeline import service_eval as ev

ap = argparse.ArgumentParser()
ap.add_argument("--service", required=True)
ap.add_argument("--manifest")
ap.add_argument("--report")
ap.add_argument("--by", default="ML team")
ap.add_argument("--label", default="")
a = ap.parse_args()
if bool(a.manifest) == bool(a.report):
    sys.exit("Give either --manifest (runs the packets) or --report (records an earlier run)")
db.init()  # makes the evaluation table on a database that does not have it yet
c = db.conn()
if a.report:
    res = ev.for_service(json.load(open(a.report, encoding="utf-8")), a.service)
    if not res:
        sys.exit(f"No packets for {a.service} in {a.report}")
    m = re.search(r"(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})", os.path.basename(a.report))
    when = f"{m[1]}-{m[2]}-{m[3]}T{m[4]}:{m[5]}:00+00:00" if m else None  # the run's own time, from the report's file name
    ev.record(c, a.service, res, os.path.basename(a.report), a.by, a.label or "From an earlier run", "report", when)
else:
    res = ev.run(a.service, a.manifest, a.label)
    ev.record(c, a.service, res, os.path.basename(a.manifest), a.by, a.label, "run")
m = ev.metrics(res)
print(f"Recorded for {a.service}: {m['decisions_right']} of {m['packets']} decisions right, {m['wrong_approvals']} wrong approvals, {m['over_flags']} over-flags, "
      f"{m['facts_right_pct']}% key facts read right, {m['made_up_pct']}% made up")
