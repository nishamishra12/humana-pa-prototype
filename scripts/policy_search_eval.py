"""Which search finds the right coverage policy? Compares five ways to search the CMS corpus (1,314 LCDs and NCDs)
for a service described the way a PA request would describe it.

  keyword       what the product uses today: count shared words, title counts triple (pipeline/policy_retrieval.py)
  bm25          the standard improved keyword ranking
  embed-doc     one vector per policy (title + first 1,000 characters), local model bge-small
  embed-chunks  the policy cut into ~900-character pieces, one vector each; a policy scores as its best piece
  embed-context the same pieces, each with a short header ("NCD 20.4: Implantable Cardioverter Defibrillators")
                added before embedding. This is contextual chunking, with the policy title as the context.
  hybrid        bm25 and embed-context combined by reciprocal rank fusion

Two phrasings per service: formal (how a request describes it) and plain (how a person says it).
A result is right if its title matches the service's pattern (see scripts/search_queries.py).
Run: python scripts/policy_search_eval.py        Writes evals/search/report_<date>.json
"""
import json, os, re, sys, time
import numpy as np
from rank_bm25 import BM25Okapi
from fastembed import TextEmbedding

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from search_queries import SERVICES
from pipeline.policy_retrieval import _tokens, _score

ROOT = os.path.join(os.path.dirname(__file__), "..")
CACHE = os.path.join(ROOT, "evals", "search")
os.makedirs(CACHE, exist_ok=True)

docs = [d for f in ("lcds", "ncds") for d in json.load(open(os.path.join(ROOT, "policies", "corpus", f"{f}.json"), encoding="utf-8")) if "error" not in d]
for d in docs:
    d["text"] = (d.get("indications") or d.get("description") or d.get("summary") or "").strip()[:8000]  # same cap as the Pipelines run
N = len(docs)
print(N, "policies")

# ---- queries and truth
queries = []
for key, pat, formal, plain in SERVICES:
    truth = {i for i, d in enumerate(docs) if re.search(pat, d["title"], re.I)}
    if truth:
        queries += [(key, "formal", formal, truth), (key, "plain", plain, truth)]
print(len(queries), "queries over", len(queries) // 2, "services")


# ---- rankings
def rank_keyword(q):
    qt = _tokens(q)
    sc = np.array([_score(qt, d) for d in docs], dtype=float)
    return list(np.argsort(-sc, kind="stable"))


bm = BM25Okapi([_tokens(d["title"] + " " + d["title"] + " " + d["text"]) for d in docs])
def rank_bm25(q):
    return list(np.argsort(-bm.get_scores(_tokens(q)), kind="stable"))


model = TextEmbedding("BAAI/bge-small-en-v1.5")


def embed(texts, path):
    if os.path.exists(path):
        return np.load(path)
    t0 = time.time()
    v = np.array(list(model.embed(texts, batch_size=64)), dtype=np.float32)
    np.save(path, v)
    print(f"  embedded {len(texts)} texts in {time.time() - t0:.0f}s")
    return v


def pieces(text, size=900):
    paras, out, cur = [p.strip() for p in re.split(r"\n+", text) if p.strip()], [], ""
    for p in paras:
        if cur and len(cur) + len(p) > size:
            out.append(cur)
            cur = ""
        cur = (cur + " " + p).strip()
        while len(cur) > size * 1.5:  # a single very long paragraph
            out.append(cur[:size])
            cur = cur[size - 100:]
    if cur:
        out.append(cur)
    return out or [""]


chunk_text, chunk_doc = [], []
for i, d in enumerate(docs):
    for c in pieces(d["text"]):
        chunk_text.append(c)
        chunk_doc.append(i)
chunk_doc = np.array(chunk_doc)
print(len(chunk_text), "pieces")

print("embedding (cached after the first run)")
E_doc = embed([d["title"] + ". " + d["text"][:1000] for d in docs], os.path.join(CACHE, "cache_doc.npy"))
E_chunk = embed(chunk_text, os.path.join(CACHE, "cache_chunk.npy"))
E_ctx = embed([f"{docs[chunk_doc[j]]['kind']} {docs[chunk_doc[j]]['id']}: {docs[chunk_doc[j]]['title']}. {c}" for j, c in enumerate(chunk_text)], os.path.join(CACHE, "cache_ctx.npy"))


def norm(m):
    return m / np.linalg.norm(m, axis=1, keepdims=True)


E_doc, E_chunk, E_ctx = norm(E_doc), norm(E_chunk), norm(E_ctx)
QV = {q[2]: v for q, v in zip(queries, norm(np.array(list(model.query_embed([q[2] for q in queries])), dtype=np.float32)))}


def best_by_doc(sim):
    out = np.full(N, -1.0)
    np.maximum.at(out, chunk_doc, sim)
    return out


def rank_embed_doc(q):
    return list(np.argsort(-(E_doc @ QV[q]), kind="stable"))


def rank_embed_chunks(q):
    return list(np.argsort(-best_by_doc(E_chunk @ QV[q]), kind="stable"))


def rank_embed_ctx(q):
    return list(np.argsort(-best_by_doc(E_ctx @ QV[q]), kind="stable"))


def rank_hybrid(q, k=60):
    score = np.zeros(N)
    for r in (rank_bm25(q), rank_embed_ctx(q)):
        for pos, i in enumerate(r):
            score[i] += 1.0 / (k + pos + 1)
    return list(np.argsort(-score, kind="stable"))


METHODS = [("keyword", rank_keyword), ("bm25", rank_bm25), ("embed-doc", rank_embed_doc), ("embed-chunks", rank_embed_chunks),
           ("embed-context", rank_embed_ctx), ("hybrid", rank_hybrid)]

results = {}
for name, fn in METHODS:
    rows = []
    for key, kind, q, truth in queries:
        r = fn(q)
        first = next((pos for pos, i in enumerate(r) if i in truth), None)
        rows.append(dict(service=key, kind=kind, rank=None if first is None else first + 1))
    results[name] = rows


def summarize(rows):
    rs = [r["rank"] for r in rows]
    n = len(rs)
    at = lambda k: round(100 * sum(1 for x in rs if x is not None and x <= k) / n, 1)
    mrr = round(sum(1 / x for x in rs if x) / n, 3)
    return dict(n=n, at1=at(1), at5=at(5), at8=at(8), mrr=mrr)


report = {}
print("\n%-14s | %-8s | %6s %6s %6s %6s" % ("method", "phrasing", "top1", "top5", "top8", "MRR"))
for name, _ in METHODS:
    for kind in ("formal", "plain", "all"):
        rows = [r for r in results[name] if kind == "all" or r["kind"] == kind]
        s = summarize(rows)
        report[f"{name}/{kind}"] = s
        print("%-14s | %-8s | %5.1f%% %5.1f%% %5.1f%% %6.3f" % (name, kind, s["at1"], s["at5"], s["at8"], s["mrr"]))
    print()

# where does today's keyword search miss in the top 8, and what do the others do?
print("Services the current keyword search misses in the top 8:")
for key in sorted({q[0] for q in queries}):
    miss = [(kind) for (k2, kind, q, t), r in zip(queries, results["keyword"]) if k2 == key and (r["rank"] is None or r["rank"] > 8)]
    if miss:
        others = {name: [r["rank"] for (k2, kind, q, t), r in zip(queries, results[name]) if k2 == key] for name in ("bm25", "embed-context", "hybrid")}
        print(f"  {key:16s} missed on {miss} | ranks bm25={others['bm25']} embed-context={others['embed-context']} hybrid={others['hybrid']}")

path = os.path.join(CACHE, f"report_{time.strftime('%Y%m%d_%H%M')}.json")
json.dump(dict(summary=report, rows=results, queries=[dict(service=q[0], kind=q[1], text=q[2]) for q in queries]), open(path, "w", encoding="utf-8"), indent=1)
print("\nreport saved:", path)
