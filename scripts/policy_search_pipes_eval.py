"""Scores policy search when Unstructured Pipelines did the chunking and embedding (scripts/pipes_ingest.py).
Compares: keyword (today), bm25, pipes-chunks (text-embedding-3-large vectors from Pipelines, a policy scores as its
best chunk), and hybrid (bm25 + pipes-chunks by reciprocal rank fusion). Same queries and truth as policy_search_eval.py.
Run: python scripts/policy_search_pipes_eval.py
"""
import glob, json, os, re, sys, time
import numpy as np
from rank_bm25 import BM25Okapi

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from search_queries import SERVICES
from pipeline.policy_retrieval import _tokens, _score

ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT = os.path.join(ROOT, "evals", "search", "pipes_out")
docs = [d for f in ("lcds", "ncds") for d in json.load(open(os.path.join(ROOT, "policies", "corpus", f"{f}.json"), encoding="utf-8")) if "error" not in d]
for d in docs:
    d["text"] = (d.get("indications") or d.get("description") or d.get("summary") or "").strip()[:8000]
N = len(docs)

# ---- chunks and vectors from Pipelines
chunk_doc, chunk_vec, chunk_text, qvec = [], [], [], {}
for meta in sorted(glob.glob(os.path.join(OUT, "pol_*.json"))):
    m, v = json.load(open(meta, encoding="utf-8")), np.load(meta[:-5] + ".npy").astype(np.float32)
    for fname, chunks in m.items():
        di = int(re.search(r"pol_(\d+)", fname).group(1))
        for c in chunks:
            chunk_doc.append(di); chunk_vec.append(v[c["row"]]); chunk_text.append(c["text"])
for meta in sorted(glob.glob(os.path.join(OUT, "qry_*.json"))):
    m, v = json.load(open(meta, encoding="utf-8")), np.load(meta[:-5] + ".npy").astype(np.float32)
    for fname, chunks in m.items():
        qvec[re.sub(r"\.txt$", "", fname)] = v[chunks[0]["row"]]
chunk_doc, E = np.array(chunk_doc), np.array(chunk_vec)
E = E / np.linalg.norm(E, axis=1, keepdims=True)
covered = len(set(chunk_doc.tolist()))
print(f"{len(chunk_doc)} chunks from {covered} of {N} policies; {len(qvec)} query vectors")

queries = []
for key, pat, formal, plain in SERVICES:
    truth = {i for i, d in enumerate(docs) if re.search(pat, d["title"], re.I)}
    if truth:
        queries += [(key, "formal", formal, truth, f"q_{key}_formal"), (key, "plain", plain, truth, f"q_{key}_plain")]

bm = BM25Okapi([_tokens(d["title"] + " " + d["title"] + " " + d["text"]) for d in docs])


def r_keyword(q, k):
    qt = _tokens(q)
    return list(np.argsort(-np.array([_score(qt, d) for d in docs], dtype=float), kind="stable"))


def r_bm25(q, k):
    return list(np.argsort(-bm.get_scores(_tokens(q)), kind="stable"))


def r_pipes(q, k):
    v = qvec[k]
    v = v / np.linalg.norm(v)
    best = np.full(N, -1.0)
    np.maximum.at(best, chunk_doc, E @ v)
    return list(np.argsort(-best, kind="stable"))


def r_hybrid(q, k, kk=60):
    s = np.zeros(N)
    for r in (r_bm25(q, k), r_pipes(q, k)):
        for pos, i in enumerate(r):
            s[i] += 1.0 / (kk + pos + 1)
    return list(np.argsort(-s, kind="stable"))


METHODS = [("keyword", r_keyword), ("bm25", r_bm25), ("pipes-chunks", r_pipes), ("hybrid", r_hybrid)]
res = {}
for name, fn in METHODS:
    res[name] = []
    for key, kind, q, truth, qk in queries:
        r = fn(q, qk)
        first = next((p for p, i in enumerate(r) if i in truth), None)
        res[name].append(dict(service=key, kind=kind, rank=None if first is None else first + 1))


def summ(rows):
    rs, n = [r["rank"] for r in rows], len(rows)
    at = lambda k: round(100 * sum(1 for x in rs if x is not None and x <= k) / n, 1)
    return dict(n=n, at1=at(1), at5=at(5), at8=at(8), mrr=round(sum(1 / x for x in rs if x) / n, 3))


print("\n%-14s | %-8s | %6s %6s %6s %6s" % ("method", "phrasing", "top1", "top5", "top8", "MRR"))
summary = {}
for name, _ in METHODS:
    for kind in ("formal", "plain", "all"):
        s = summ([r for r in res[name] if kind == "all" or r["kind"] == kind])
        summary[f"{name}/{kind}"] = s
        print("%-14s | %-8s | %5.1f%% %5.1f%% %5.1f%% %6.3f" % (name, kind, s["at1"], s["at5"], s["at8"], s["mrr"]))
    print()
path = os.path.join(ROOT, "evals", "search", f"report_pipes_{time.strftime('%Y%m%d_%H%M')}.json")
json.dump(dict(summary=summary, rows=res, covered_policies=covered), open(path, "w", encoding="utf-8"), indent=1)
print("report saved:", path)
