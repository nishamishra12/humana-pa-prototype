"""Copies the CMS billing articles and their codes into the database, so the screens never call CMS while someone waits.

  python scripts/refresh_cms_index.py            first run: about 1,300 articles, a few minutes. Later runs only read new or changed articles.
  python scripts/refresh_cms_index.py --limit 20 try it on 20 articles

Run it by hand, or on a schedule (nightly or weekly is plenty: CMS articles change rarely). An article that fails is left alone and tried again next run.
"""
import argparse, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app import db
from pipeline.policy_build import cms_index

ap = argparse.ArgumentParser()
ap.add_argument("--limit", type=int, default=None)
ap.add_argument("--workers", type=int, default=6)
a = ap.parse_args()
db.init()
c = db.conn()
cms_index.sync(c, limit=a.limit, workers=a.workers)
