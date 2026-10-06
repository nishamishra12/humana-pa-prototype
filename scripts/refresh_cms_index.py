"""Copies CMS data into the database, so the screens never call CMS while someone waits:
  - the billing articles and their codes (cms_articles, cms_article_codes)
  - the national and local coverage policies (cms_policies)

  python scripts/refresh_cms_index.py            first run: about 1,300 articles, a few minutes. Later runs only read what is new or changed.
  python scripts/refresh_cms_index.py --limit 20 try it on 20 of each
  python scripts/refresh_cms_index.py --only policies     or --only articles

Run it by hand, or on a schedule (nightly or weekly is plenty: CMS articles change rarely). An article that fails is left alone and tried again next run.
"""
import argparse, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app import db
from pipeline.policy_build import cms_index

ap = argparse.ArgumentParser()
ap.add_argument("--limit", type=int, default=None)
ap.add_argument("--workers", type=int, default=6)
ap.add_argument("--only", choices=["articles", "policies"], default=None)
a = ap.parse_args()
db.init()
c = db.conn()
if a.only != "articles":
    if not c.execute("SELECT 1 FROM cms_policies LIMIT 1").fetchone():
        print(f"Loaded {cms_index.import_corpus_json(c)} policies from the files already downloaded")  # a first run needs no 1,300 calls
    cms_index.sync_policies(c, limit=a.limit)
if a.only != "policies":
    cms_index.sync(c, limit=a.limit, workers=a.workers)
