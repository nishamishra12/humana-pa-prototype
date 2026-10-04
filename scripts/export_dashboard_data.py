"""Builds the two dashboard pages from scripts/dashboard_template.html:
  web/ops.html         live page, served by the app at /ops.html. It reads /api/dashboard and refreshes itself every few seconds.
  docs/dashboard.html  a static snapshot (data embedded), for sharing as a published page.
Run after changing the template:  python scripts/export_dashboard_data.py
The numbers come from app/dashboard.py (computed from the app database, no patient names)."""
import json, os, sqlite3, sys

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, ROOT)
from app.dashboard import compute

c = sqlite3.connect(os.path.join(ROOT, "app", "pa.db"))
c.row_factory = sqlite3.Row
data = compute(c)
tpl = open(os.path.join(os.path.dirname(__file__), "dashboard_template.html"), encoding="utf-8").read()


def write(path, live):
    html = tpl.replace("__LIVE__", "true" if live else "false").replace("__DATA__", "null" if live else json.dumps(data).replace("</", "<\\/"))
    with open(os.path.join(ROOT, path), "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    print("wrote", path)


write("web/ops.html", True)
write("docs/dashboard.html", False)
print(data["n"], "cases |", data["exec"]["decided"], "decided")
