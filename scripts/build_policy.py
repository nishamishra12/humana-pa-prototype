"""Build (draft) the criteria for one policy. Costs one AI call. Example:
    PYTHONPATH=. python scripts/build_policy.py ncd 20.4
    PYTHONPATH=. python scripts/build_policy.py cfr 42 412 412.3
    PYTHONPATH=. python scripts/build_policy.py lcd L37848
Add --saved to reuse the source already fetched."""
import sys
from dotenv import load_dotenv
load_dotenv(".env")
from pipeline.policy_build.build import run

a = [x for x in sys.argv[1:] if not x.startswith("--")]
saved = "--saved" in sys.argv
if a[0] == "cfr":
    run("cfr", (int(a[1]), int(a[2]), a[3]), fetch=not saved)
else:
    run(a[0], a[1], fetch=not saved)
