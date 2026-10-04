"""Same as try_multi.py but uses the real upload path (Unstructured OCR when a key is set). Usage: python scripts/try_multi_full.py <pdf>"""
import sys, time
from dotenv import load_dotenv
load_dotenv(".env")
from pipeline.run import process
from pipeline.procedures import procedure_for_cpt, display_for
t0 = time.time()
els, engine, facts, res = process(sys.argv[1])
_, proc = procedure_for_cpt(facts.get("_cpt"))
print(f"{sys.argv[1]} | {time.time()-t0:.1f}s | ingest={engine} | pages={len({e.page for e in els})} | procedure={res.get('procedure') and res['procedure']['name']}")
for d in proc["facts"]:
    f = facts[d["key"]]
    print(f"  {d['key']:32s} {f['status']:8s} {str(display_for(d, f))[:36]:36s} p.{f.get('page')} checked={f.get('checked', False)} match={[e['match'] + ':' + str(e['score']) for e in f.get('evidence', [])][:4]}")
    if f.get("note"): print("      note:", f["note"][:160])
print("ACTION:", res["action"], "|", res["rationale"][:200])
