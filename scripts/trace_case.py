"""Runs one packet through PA Desk and saves what every step saw and produced, so the inner workings can be shown.
Writes evals/trace/<name>.json. Costs one real run (about $0.15 and the pages for the Unstructured call).
Run: PYTHONPATH=. python scripts/trace_case.py packets/multi/icd4_scanned_noisy.pdf
Then: python scripts/make_inner_workings.py
"""
import json, os, re, sys, time
from dotenv import load_dotenv

load_dotenv(".env")
from pipeline import evidence as ev
from pipeline.engine import analyze
from pipeline.extract import extract_header
from pipeline.extract_llm import extract_facts
from pipeline.ingest import ingest
from pipeline.procedures import library, procedure_for_cpt

path = sys.argv[1]
name = os.path.splitext(os.path.basename(path))[0]
out = {"file": os.path.basename(path)}

# 2. Unstructured
t0 = time.time()
elements, engine = ingest(path)
out["ingest"] = dict(engine=engine, seconds=round(time.time() - t0, 1), elements=[dict(page=e.page, type=e.type, text=e.text) for e in elements])
full = "\n".join(e.text for e in elements)

# 3. pick the policy
head = extract_header(full)
m = None
from pipeline.extract import _flatten_tables
for e in sorted(elements, key=lambda x: x.page):  # the request form is on page 1
    flat = _flatten_tables(e.text)
    m = re.search(r"CPT:?\s*(\d{5})", flat)
    if m:
        out["cpt_source"] = dict(page=e.page, type=e.type, text=flat, start=m.start(), end=m.end())
        break
pkey, proc = procedure_for_cpt(head.get("_cpt"))
lib = library()
pols = lib["policies"] if isinstance(lib["policies"], dict) else {p["id"]: p for p in lib["policies"]}
out["registry"] = dict(
    header={k: v for k, v in head.items() if k != "_member"}, member_fields=sorted((head.get("_member") or {}).keys()),
    matched=pkey, covered_cpts=lib.get("covered_cpt_codes", []),
    procedures=[dict(key=k, name=p["name"], cpts=p.get("cpts", []), policies=[dict(id=i, title=pols[i]["title"], level=pols[i]["level"], verified=pols[i].get("verified"), criteria=len(pols[i].get("criteria", []))) for i in p["policies"]])
                for k, p in lib["procedures"].items()],
    hierarchy=lib.get("hierarchy"),
    criteria=[dict(policy=i, id=c["id"], text=c["text"], fact=c.get("required_fact"), cite=c.get("cite"), check=c.get("check"))
              for i in proc["policies"] for c in pols[i].get("criteria", [])])

# 4 and 5. read, locate, check
trace = {}
t0 = time.time()
facts = extract_facts(elements, pkey, n_votes=3, trace=trace)
out["read_seconds"] = round(time.time() - t0, 1)
runs = trace.pop("runs")
out["reads"] = [{k: dict(status=v["status"], value=v["value"], note=v.get("note"), calc=v.get("calc"), quotes=[q["quote"] for q in v["evidence"]]) for k, v in r.items()} for r in runs]
out["trace"] = trace
out["facts"] = {k: v for k, v in facts.items() if not k.startswith("_")}
out["pages"] = {str(k): v for k, v in ev.page_texts(elements).items()}

# 5b. two small tests of the matcher, with the real function
pages = ev.page_texts(elements)
demo = []
for k, f in sorted(out["facts"].items(), key=lambda kv: kv[0] != "lvef_percent"):  # the ejection fraction makes the clearest example
    for x in (f.get("evidence") or []):
        q = x.get("quote") or ""
        if x.get("supports", True) and re.search(r"\d", q) and len(q) > 25 and x["page"] in pages:
            raw = pages[x["page"]]
            num = re.search(r"\d+(?:\.\d+)?", q).group(0)
            changed = str(int(float(num)) + 10)
            altered_q = q.replace(num, changed, 1)
            hit_same = ev.locate_quote(q, pages)
            noisy = q.replace("e", "c", 2).replace("l", "I", 1)  # letters only, like a scan: no digit may change
            hit_noisy = ev.locate_quote(noisy, pages)
            hit_num = ev.locate_quote(altered_q, pages)
            demo = dict(fact=k, original=q, noisy=noisy, noisy_hit=dict(method=hit_noisy["method"], score=hit_noisy["score"], text=hit_noisy["text"]) if hit_noisy else None,
                        number_changed=altered_q, number_hit=dict(method=hit_num["method"], score=hit_num["score"], text=hit_num["text"]) if hit_num else None,
                        original_hit=dict(method=hit_same["method"], score=hit_same["score"]) if hit_same else None, changed_from=num, changed_to=changed)
            break
    if demo:
        break
out["matcher_demo"] = demo

# 6. rules
res = analyze(facts)
out["analysis"] = dict(action=res["action"], rationale=res.get("rationale"), gate=res.get("gate"),
                       checklist=[dict(policy=c["policy_id"], layer=c["layer"], cite=c["cite"], id=c["criterion_id"], text=c["text"], status=c["status"], fact=c["fact_key"], note=c.get("note")) for c in res["checklist"]])
os.makedirs("evals/trace", exist_ok=True)
dest = f"evals/trace/{name}.json"
json.dump(out, open(dest, "w", encoding="utf-8"), indent=1, ensure_ascii=False, default=str)
print("saved", dest, "| action:", res["action"], "| facts:", len(out["facts"]), "| matcher demo:", bool(demo))
