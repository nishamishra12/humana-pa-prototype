"""Run the new reader on one packet and print what it found. Usage: python scripts/try_multi.py packets/multi/icd1_complete_nonischemic.pdf"""
import sys, time, json
from dotenv import load_dotenv
load_dotenv()
from pipeline.ingest import _ingest_local
from pipeline.run import extract
from pipeline.engine import analyze
from pipeline.procedures import procedure_for_cpt, display_for

path = sys.argv[1]
t0 = time.time()
els = _ingest_local(path)
facts = extract(els)
res = analyze(facts)
_, proc = procedure_for_cpt(facts.get("_cpt"))
print(f"{path}  |  {time.time()-t0:.1f}s  |  extractor={facts.get('_extractor')}  |  procedure={res.get('procedure') and res['procedure']['name']}")
for d in proc["facts"]:
    f = facts[d["key"]]
    ev = f.get("evidence", [])
    print(f"  {d['key']:32s} {f['status']:8s} {str(display_for(d, f))[:40]:40s} p.{f.get('page')} checked={f.get('checked', False)} ev={[(e['page'], e['match'], e.get('verdict'), e.get('supports')) for e in ev]}")
    if f.get("note"): print("      note:", f["note"][:200])
print("ACTION:", res["action"], "|", res["rationale"])
for c in res["checklist"]:
    print("   ", c["status"].ljust(8), c["criterion_id"].ljust(10), (c.get("short") or "")[:60])
