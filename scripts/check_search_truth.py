"""Checks every service in search_queries.py has at least one matching policy title in the corpus."""
import json, re, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from search_queries import SERVICES

docs = [d for f in ("lcds", "ncds") for d in json.load(open(f"policies/corpus/{f}.json", encoding="utf-8")) if "error" not in d]
print(len(docs), "documents")
bad = []
for key, pat, q1, q2 in SERVICES:
    hits = [d for d in docs if re.search(pat, d["title"], re.I)]
    if not hits:
        bad.append(key)
    print(f"{key:16s} matches={len(hits):3d}  e.g. {hits[0]['kind'] + ' ' + hits[0]['id'] + ' ' + hits[0]['title'][:60] if hits else '-'}")
print("NO MATCH:", bad)
