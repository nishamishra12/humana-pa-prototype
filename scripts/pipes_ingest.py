"""Runs the CMS policy corpus (and the test queries) through Unstructured Pipelines: partition, chunk by title, embed.

Each policy becomes one small text file ("NCD 20.4: Implantable Cardioverter Defibrillators", then its text). Pipelines
returns chunks with a vector for each. The queries go through the same pipeline so they are embedded by the same model.
Output is cached per batch in evals/search/pipes_out/, so a re-run costs nothing for batches already done.

Run: python scripts/pipes_ingest.py            (needs UNSTRUCTURED_PLATFORM_API_KEY in .env)
     python scripts/pipes_ingest.py --limit 20 (try a few files first)
Limits from the docs: 10 files per job, 50 MB per file.
"""
import json, os, sys, time, hashlib
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
load_dotenv(".env")
from unstructured_client import UnstructuredClient
from unstructured_client.models.operations import CreateJobRequest, DownloadJobOutputRequest
from unstructured_client.models.shared import BodyCreateJob, InputFiles

sys.path.insert(0, os.path.dirname(__file__))
from search_queries import SERVICES

ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT = os.path.join(ROOT, "evals", "search", "pipes_out")
os.makedirs(OUT, exist_ok=True)
KEY = os.getenv("UNSTRUCTURED_PLATFORM_API_KEY")
URL = os.getenv("UNSTRUCTURED_API_URL") or "https://platform.unstructuredapp.io/api/v1"
TEXT_CAP = 8000  # first 8,000 characters of each policy, the same cap the local search test uses
NODES = [
    {"name": "Partitioner", "type": "partition", "subtype": "vlm", "settings": {"is_dynamic": True, "allow_fast": True}},
    {"name": "Chunker", "type": "chunk", "subtype": "chunk_by_title", "settings": {"max_characters": 1500, "new_after_n_chars": 1000, "overlap": 100}},
    {"name": "Embedder", "type": "embed", "subtype": "azure_openai", "settings": {"model_name": "text-embedding-3-large"}},
]


def client():
    return UnstructuredClient(api_key_auth=KEY, server_url=URL)


def run_batch(tag, files):
    """files: list of (file_name, text). Returns {file_name: [chunk elements]}. Cached on disk."""
    path = os.path.join(OUT, f"{tag}.json")
    if os.path.exists(path):
        return json.load(open(path, encoding="utf-8"))  # vectors are in {tag}.npy, in the same order as the chunks listed here
    for attempt in range(3):
        try:
            c = client()
            inputs = [InputFiles(content=text.encode("utf-8"), file_name=name, content_type="text/plain") for name, text in files]
            jid = c.jobs.create_job(request=CreateJobRequest(body_create_job=BodyCreateJob(request_data=json.dumps({"job_nodes": NODES}), input_files=inputs))).job_information.id
            for _ in range(120):
                ji = c.jobs.get_job(request={"job_id": jid}).job_information
                if ji.status == "COMPLETED":
                    break
                if ji.status in ("FAILED", "STOPPED"):
                    raise RuntimeError(f"job {jid} {ji.status}")
                time.sleep(4)
            else:
                raise RuntimeError("timed out")
            out, vecs = {}, []
            for f in ji.output_node_files or []:
                els = c.jobs.download_job_output(request=DownloadJobOutputRequest(job_id=jid, file_id=f.file_id)).any
                for e in els:
                    fn = (e.get("metadata") or {}).get("filename", "")
                    # Pipelines adds a hash to the file name; match back by prefix
                    key = next((n for n, _ in files if fn.startswith(n.rsplit(".", 1)[0])), fn)
                    out.setdefault(key, []).append(dict(text=e.get("text", ""), type=e.get("type"), row=len(vecs)))
                    vecs.append(e.get("embeddings") or [0.0] * 3072)
            np.save(os.path.join(OUT, f"{tag}.npy"), np.array(vecs, dtype=np.float16))  # half precision: plenty for ranking, 1/10 the size on disk
            json.dump(out, open(path, "w", encoding="utf-8"))
            return out
        except Exception as e:
            print(f"  batch {tag} attempt {attempt + 1} failed: {str(e)[:120]}")
            time.sleep(5)
    return {}


def main():
    limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else None
    docs = [d for f in ("lcds", "ncds") for d in json.load(open(os.path.join(ROOT, "policies", "corpus", f"{f}.json"), encoding="utf-8")) if "error" not in d]
    if limit:
        docs = docs[:limit]
    # policy files: name encodes position so we can map back
    pol = [(f"pol_{i:04d}.txt", f"{d['kind']} {d['id']}: {d['title']}\n\n" + (d.get("indications") or d.get("description") or d.get("summary") or "").strip()[:TEXT_CAP]) for i, d in enumerate(docs)]
    qs = []
    for key, pat, formal, plain in SERVICES:
        qs += [(f"q_{key}_formal.txt", formal), (f"q_{key}_plain.txt", plain)]
    jobs = [(f"pol_{i // 10:03d}", pol[i:i + 10]) for i in range(0, len(pol), 10)] + [(f"qry_{i // 10:03d}", qs[i:i + 10]) for i in range(0, len(qs), 10)]
    print(len(pol), "policy files,", len(qs), "query files,", len(jobs), "jobs of up to 10 files")
    t0 = time.time()
    done = 0
    with ThreadPoolExecutor(max_workers=6) as pool:
        for r in pool.map(lambda j: run_batch(*j), jobs):
            done += 1
            if done % 10 == 0 or done == len(jobs):
                print(f"  {done}/{len(jobs)} jobs done ({time.time() - t0:.0f}s)")
    print("finished. cached in", OUT)


if __name__ == "__main__":
    main()
