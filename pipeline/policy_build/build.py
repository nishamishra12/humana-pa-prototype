"""Runs the whole policy build for one policy: fetch, parse, draft, check, compare. Writes everything to policies/work/<id>/<version>/.

    from pipeline.policy_build.build import run
    run("ncd", "20.4")            # CMS national coverage determination
    run("lcd", "L37848")          # CMS local coverage determination
    run("cfr", (42, 412, "412.3"))  # eCFR section

Output files in the work folder: source.txt, source.pdf, meta.json, elements.json, draft.json, report.json, compare.json.
The draft goes to a policy owner for review. It does not change the live library.
"""
import json, os, time

from . import sources as S
from .parse import parse
from .draft import draft as make_draft
from .validate import validate
from .compare import compare

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")


def vocab_for(policy_id):
    """Facts the packet reader can already find for the services that use this policy. A policy shared by all services (the regulation)
    gets the union. For a service we have not built yet this is empty and the AI proposes the facts."""
    lib = json.load(open(os.path.join(ROOT, "policies", "policy_library.json"), encoding="utf-8"))
    out = {}
    for proc in lib["procedures"].values():
        if policy_id in proc.get("policies", []):
            for d in proc["facts"]:
                out.setdefault(d["key"], d)
    return list(out.values())


def run(kind, ident, fetch=True, vocab=None, version=None, log=print):
    t0 = time.time()
    if fetch:
        src = {"ncd": S.fetch_ncd, "lcd": S.fetch_lcd}[kind](ident) if kind in ("ncd", "lcd") else S.fetch_cfr(*ident)
        folder = S.save(src)
        meta = {k: v for k, v in src.items() if k not in ("text", "html")}
        log(f"1 fetched   {src['policy_id']} {src['version']} from {src['source']} ({len(src['text']):,} chars)")
    else:
        pid = {"ncd": f"NCD-{ident}", "lcd": f"LCD-{ident}"}.get(kind) or f"CFR-{ident[0]}-{ident[2]}"
        ver = version or sorted(os.listdir(os.path.join(S.WORK, pid)))[-1]
        folder = os.path.join(S.WORK, pid, ver)
        meta = json.load(open(os.path.join(folder, "meta.json"), encoding="utf-8"))
    pid, ver = meta["policy_id"], meta["version"]
    els, info = parse(pid, ver)
    log(f"2 parsed    {len(els)} elements with {info['engine']}" + (f" ({info.get('note')})" if info.get("note") else ""))
    vocab = vocab_for(pid) if vocab is None else vocab
    d = make_draft(els, meta, vocab)
    json.dump(d, open(os.path.join(folder, "draft.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    log(f"3 drafted   {len(d['criteria'])} criteria, {len(d['new_facts'])} new facts, {len(d['not_modeled'])} not modeled ({d['_usage']['input_tokens']} in / {d['_usage']['output_tokens']} out tokens)")
    rep = validate(d, els, vocab)
    json.dump(rep, open(os.path.join(folder, "report.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    log(f"4 checked   pass {rep['counts']['pass']}, review {rep['counts']['review']}, fail {rep['counts']['fail']}; possible misses: {len(rep['uncovered'])}")
    cmp_ = compare(d, pid)
    if cmp_:
        json.dump(cmp_, open(os.path.join(folder, "compare.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        c = cmp_["counts"]
        log(f"5 compared  against the approved rules: same {c['same']}, differs {c['differs']}, missed {c['missed']} of {cmp_['approved_count']}; extra in the draft: {len(cmp_['extra'])}")
    log(f"done in {time.time() - t0:.0f}s -> {os.path.relpath(folder, ROOT)}")
    return dict(folder=folder, meta=meta, elements=els, draft=d, report=rep, compare=cmp_)
