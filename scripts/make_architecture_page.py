"""Writes docs/architecture.html: the engineering-level architecture of PA Desk.
Two diagrams: what is built today (components, data stores, trust boundary, numbered hops) and the production
target. Run: python scripts/make_architecture_page.py
"""
import html, os

OUT = os.path.join(os.path.dirname(__file__), "..", "docs", "architecture.html")
e = html.escape


class Svg:
    def __init__(self):
        self.parts = []

    def zone(self, x, y, w, h, title, kind="z"):
        self.parts.append(f'<rect class="{kind}" x="{x}" y="{y}" width="{w}" height="{h}" rx="10"/>')
        self.parts.append(f'<text class="zt" x="{x + 12}" y="{y + 20}">{e(title)}</text>')

    def box(self, x, y, w, h, title, lines=(), kind="b"):
        self.parts.append(f'<rect class="{kind}" x="{x}" y="{y}" width="{w}" height="{h}" rx="6"/>')
        self.parts.append(f'<text class="t" x="{x + 10}" y="{y + 19}">{e(title)}</text>')
        for i, ln in enumerate(lines):
            self.parts.append(f'<text class="s" x="{x + 10}" y="{y + 36 + i * 15}">{e(ln)}</text>')

    def arrow(self, pts, dashed=False):
        d = " ".join(f"{px},{py}" for px, py in pts)
        self.parts.append(f'<polyline class="a{" dash" if dashed else ""}" points="{d}" marker-end="url(#ah)"/>')

    def badge(self, n, x, y):
        self.parts.append(f'<circle class="bd" cx="{x}" cy="{y}" r="11"/><text class="bt" x="{x}" y="{y + 4}">{n}</text>')

    def label(self, x, y, text, anchor="start"):
        self.parts.append(f'<text class="s" x="{x}" y="{y}" text-anchor="{anchor}">{e(text)}</text>')

    def render(self, w, h, title):
        defs = ('<defs><marker id="ah" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
                '<path d="M2 1L8 5L2 9" fill="none" stroke="context-stroke" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></marker></defs>')
        return f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="{e(title)}">{defs}{"".join(self.parts)}</svg>'


# ------------------------------------------------------------------ as built
s = Svg()
s.zone(20, 40, 190, 460, "Browser")
s.box(35, 70, 160, 150, "Single-page app", ["vanilla JS, static files", "Views: intake, nurse,", "medical director", "fetch + cookie session"])
s.zone(240, 40, 290, 460, "App service (FastAPI, one process)")
s.box(255, 70, 260, 70, "REST API", ["auth, cases, action, upload,", "jobs, notifications (JSON)"])
s.box(255, 155, 260, 65, "Access control", ["cookie session (in memory)", "role gates; nurse sees own cases"])
s.box(255, 235, 260, 65, "Case service", ["status, SLA clocks, audit,", "notifications"])
s.box(255, 315, 260, 55, "Job tracker", ["in memory, upload stage:", "reading, facts, policy"])
s.box(255, 385, 260, 55, "Static file server", ["serves web/, no-store cache"])
s.zone(560, 40, 340, 460, "Pipeline (in-process Python modules)")
s.box(575, 70, 310, 50, "run.py", ["orchestrates one packet, with progress"])
s.box(575, 135, 310, 55, "ingest.py", ["packet PDF to Element[ ]: page, type, text"])
s.box(575, 205, 310, 75, "extract_llm.py", ["3 parallel AI reads, forced JSON form", "facts + every supporting sentence"], "ai")
s.box(575, 295, 310, 75, "evidence.py", ["5  locate: exact, then fuzzy, numbers must match", "6  verify: second AI reads each sentence"], "ai")
s.box(575, 385, 310, 45, "engine.py", ["rules in code, no AI, no 'deny' value"])
s.box(575, 445, 310, 45, "policy_retrieval.py", ["no policy: keyword search + AI drafts a checklist"], "ai")
s.zone(960, 40, 340, 460, "Outside our boundary (data leaves)", "zx")
s.box(975, 135, 310, 55, "Unstructured Transform API", ["partition + OCR over HTTPS"], "ex")
s.box(975, 205, 310, 165, "Anthropic API", ["Sonnet: reads the packet (3 calls)", "Haiku: checks each sentence", "tool use, forced JSON schema", "prototype: made-up data only", "production: BAA, private endpoint"], "ex")
s.box(975, 385, 310, 45, "Traces: OpenTelemetry to Honeycomb", ["not built yet"], "nx")
s.box(975, 445, 310, 45, "CMS Coverage API and eCFR", ["used offline to build the corpus"], "ex")
s.zone(240, 540, 1060, 240, "Data stores (local files and SQLite in the prototype)")
s.box(255, 575, 230, 185, "SQLite  app/pa.db", ["users, cases, elements,", "comments, audit,", "notifications", "", "cases hold facts and", "analysis as JSON"], "db")
s.box(500, 575, 190, 185, "Files", ["uploads/  (packet PDFs)", "packets/  demo, multi,", "holdout, fixtures"], "db")
s.box(705, 575, 230, 185, "Policy library", ["policy_library.json v0.2.0", "procedures: facts + policies", "raw/  source text, for audit", "versioned in git"], "db")
s.box(950, 575, 165, 185, "CMS corpus", ["969 LCDs + 345 NCDs", "JSON, searched by", "keyword"], "db")
s.box(1130, 575, 155, 185, "Evals", ["manifests (truth)", "reports/*.json", "", "12  run_evals.py runs", "the same pipeline"], "db")
# arrows
s.arrow([(195, 105), (255, 105)]); s.badge(1, 225, 105)
s.arrow([(515, 100), (575, 100)]); s.badge(2, 545, 100)
for y0, y1 in ((120, 135), (190, 205), (280, 295), (370, 385)):
    s.arrow([(730, y0), (730, y1)])
s.arrow([(885, 162), (975, 162)]); s.badge(3, 930, 162)
s.arrow([(885, 242), (975, 242)]); s.badge(4, 930, 242)
s.arrow([(885, 332), (975, 332)]); s.badge(6, 930, 332)
s.arrow([(730, 500), (730, 535), (820, 535), (820, 575)]); s.badge(7, 775, 535)
s.arrow([(385, 500), (385, 575)]); s.badge(8, 385, 538)
s.arrow([(860, 500), (860, 552), (1030, 552), (1030, 575)]); s.badge(11, 945, 552)
s.arrow([(1100, 490), (1100, 575)], dashed=True)
s.arrow([(110, 220), (110, 342), (255, 342)], dashed=True); s.badge(9, 110, 290)
s.arrow([(150, 220), (150, 267), (255, 267)]); s.badge(10, 150, 245)
AS_BUILT = s.render(1320, 800, "PA Desk architecture as built")

# ------------------------------------------------------------------ production target
t = Svg()
t.zone(20, 40, 250, 330, "People and channels")
t.box(35, 70, 220, 70, "Fax / e-fax and provider portal", ["image or PDF lands in the queue"])
t.box(35, 155, 220, 70, "Staff web app", ["intake, nurse, medical director"])
t.box(35, 240, 220, 70, "Member app (phase 2)", ["Patient Access API, Jan 2027"], "nx")
t.zone(290, 40, 200, 330, "Edge")
t.box(305, 70, 170, 70, "API gateway + WAF", ["rate limits, TLS"])
t.box(305, 155, 170, 70, "Identity provider", ["OIDC single sign-on, MFA"])
t.zone(510, 40, 790, 480, "Private network (PHI zone, covered by a BAA)")
t.box(525, 70, 150, 70, "Intake queue", ["durable, retries"])
t.box(695, 70, 200, 70, "Ingestion workers", ["self-hosted Unstructured", "OCR, page-cited elements"])
t.box(915, 70, 370, 70, "Model gateway", ["Claude on a BAA-covered endpoint", "pinned model + prompt versions, PII redaction"], "ai")
t.box(525, 165, 250, 75, "Evidence service", ["locate (fuzzy, numbers must match)", "verify (second model)"], "ai")
t.box(795, 165, 240, 75, "Policy service", ["versioned library, owner sign-off", "routes by procedure + region"], "db")
t.box(1055, 165, 230, 75, "Rules engine", ["deterministic, no 'deny' value"])
t.box(525, 265, 250, 75, "Case service", ["Postgres: cases, queues, SLA clocks"])
t.box(795, 265, 240, 75, "Audit log", ["append-only, immutable, long retention"], "db")
t.box(1055, 265, 230, 75, "Object store", ["packets + page images, KMS, retention"], "db")
t.box(525, 365, 380, 75, "Outbound integrations", ["provider notice: X12 278 / FHIR PA", "CMS public metrics export"])
t.box(925, 365, 360, 75, "Feature flags", ["one switch per service line:", "on only after its evals pass"])
t.zone(20, 550, 1280, 190, "Quality and data platform (no PHI)", "zx")
t.box(35, 580, 300, 145, "OpenTelemetry collector", ["to Honeycomb: one trace per case", "stage timings, model + policy versions,", "agreement rates. Counts and ids only."], "ex")
t.box(355, 580, 300, 145, "Warehouse (Snowflake)", ["de-identified metric tables", "north star, leading and", "lagging measures, dashboards"], "ex")
t.box(675, 580, 300, 145, "Eval service", ["golden set labeled by senior nurses", "run on every change", "CI gate per service line"], "ex")
t.box(995, 580, 290, 145, "Policy update watch", ["tracks CMS and contractor changes", "opens a review for the owner"], "ex")
t.arrow([(255, 105), (305, 105)]); t.arrow([(255, 190), (305, 190)])
t.arrow([(475, 105), (525, 105)])
t.arrow([(675, 105), (695, 105)]); t.arrow([(895, 105), (915, 105)])
t.arrow([(1100, 140), (1100, 165)]); t.arrow([(1055, 202), (1035, 202)]); t.arrow([(795, 202), (775, 202)])
t.arrow([(650, 240), (650, 265)])
t.arrow([(775, 302), (795, 302)]); t.arrow([(1035, 302), (1055, 302)])
t.arrow([(650, 340), (650, 365)])
t.arrow([(1100, 340), (1100, 365)], dashed=True)
t.arrow([(1000, 520), (1000, 550)], dashed=True)
TARGET = t.render(1320, 760, "PA Desk production target architecture")

HOPS = [
    ("1", "Browser to API", "HTTPS, JSON. Cookie session (httponly, same-site).", "Session expired: 401, back to sign-in. Production: single sign-on."),
    ("2", "API to pipeline", "Upload endpoint saves the PDF, runs the pipeline in a worker thread, reports progress by job id.", "Pipeline error returns a plain message. Nothing half-saved: the case is written only at the end."),
    ("3", "Ingest to Unstructured", "HTTPS, partition with OCR, output = elements. Result: Element{page, type, text}.", "Service down or key missing: falls back to local pdftotext (text PDFs only). The engine used is recorded on the case."),
    ("4", "Extract to Anthropic (Sonnet)", "Forced tool call. The JSON schema is generated from the procedure's fact list. 3 parallel calls.", "Reads must agree on status and, for numbers and choices, on value, or the fact is 'not sure'. Unreadable reply is repaired, then retried once."),
    ("5", "Locate quote (code)", "Exact match on normalized text, then fuzzy (partial ratio 88 or higher). Numbers in the quote must equal numbers in the match.", "No match: the quote is dropped. No supporting quote left: 'not sure'."),
    ("6", "Verify meaning (Haiku)", "One batched tool call: supports, contradicts, unrelated, insufficient, with a reason.", "All sentences contradict or are unrelated: 'not sure'. Checker down: retried once, then the fact is kept without a tick."),
    ("7", "Engine reads the library", "Pure function: facts + policy_library.json to Analysis{checklist, gate, action, fact_schema}. Tests: gte, lte, in, present, absent, applies_if.", "Unknown procedure code: action 'no policy', never scored against another service's criteria."),
    ("8", "Persist", "SQLite. cases.facts and cases.analysis are JSON. Elements, comments, notifications, and an audit table.", "Prototype only. Production: Postgres plus an immutable audit store."),
    ("9", "UI polling", "GET /api/jobs/{id} returns the stage (reading, facts, policy, done), then GET /api/cases/{id}.", "Unknown job id: 'waiting'. Case access is checked on every read."),
    ("10", "Decisions", "POST /api/cases/{id}/action. Role gate: nurse or director. Only a director can deny. Writes the audit row and notifications.", "Intake gets 403 on clinical actions. A nurse gets 404 on another nurse's case."),
    ("11", "Fallback for new services", "Keyword score over about 1,300 policies, an AI picks one of the top 8, then drafts a checklist.", "Output is marked unverified and is never used by the engine. A person must confirm it."),
    ("12", "Evals", "scripts/run_evals.py runs the same pipeline on the labeled packets and saves a report.", "Reports are dated JSON files, so runs can be compared over time."),
]
rows = "".join(f"<tr><td><span class='n'>{n}</span></td><td><b>{e(a)}</b></td><td>{e(b)}</td><td>{e(c)}</td></tr>" for n, a, b, c in HOPS)

PAGE = f"""<!doctype html>
<meta charset="utf-8">
<title>PA Desk Architecture</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap">
<style>
:root {{
  --bg:#f4f6f5; --panel:#ffffff; --ink:#14201c; --ink2:#4a5a55; --line:#cfd8d4; --line2:#9fb0aa; --zone:#eef3f1;
  --ai:#5f3aa8; --ai-soft:#ece5f8; --db:#1f6f5c; --db-soft:#e2f0eb; --ex:#a15c00; --ex-soft:#fdf0d6; --accent:#1f6f5c;
}}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{
  --bg:#0f1715; --panel:#16211e; --ink:#e5eeea; --ink2:#a9bab4; --line:#2c3b37; --line2:#4f6761; --zone:#121c19;
  --ai:#b79af0; --ai-soft:#251d3d; --db:#4cc0a0; --db-soft:#12302a; --ex:#f0b04a; --ex-soft:#35260c; --accent:#4cc0a0; }} }}
:root[data-theme="dark"] {{
  --bg:#0f1715; --panel:#16211e; --ink:#e5eeea; --ink2:#a9bab4; --line:#2c3b37; --line2:#4f6761; --zone:#121c19;
  --ai:#b79af0; --ai-soft:#251d3d; --db:#4cc0a0; --db-soft:#12302a; --ex:#f0b04a; --ex-soft:#35260c; --accent:#4cc0a0; }}
* {{ box-sizing: border-box; }}
body {{ margin:0; background:var(--bg); color:var(--ink); font:14px/1.5 "IBM Plex Sans", system-ui, sans-serif; padding:28px 24px 64px; }}
main {{ max-width:1320px; margin:0 auto; }}
h1 {{ font-size:26px; font-weight:600; margin:0 0 4px; letter-spacing:-.01em; }}
h2 {{ font-size:18px; font-weight:600; margin:40px 0 6px; }}
p.lead {{ color:var(--ink2); margin:0 0 14px; max-width:880px; }}
.wrap {{ background:var(--panel); border:1px solid var(--line); border-radius:12px; padding:12px; overflow-x:auto; }}
.wrap svg {{ display:block; min-width:960px; width:100%; height:auto; }}
.legend {{ display:flex; gap:18px; flex-wrap:wrap; margin:10px 2px 0; color:var(--ink2); font-size:12.5px; }}
.legend i {{ display:inline-block; width:14px; height:14px; border-radius:3px; border:1.5px solid; vertical-align:-2px; margin-right:6px; }}
svg text {{ font-family:"IBM Plex Sans", system-ui, sans-serif; fill:var(--ink); }}
.z {{ fill:var(--zone); stroke:var(--line); }} .zx {{ fill:none; stroke:var(--ex); stroke-width:1.5; stroke-dasharray:6 4; }}
.zt {{ font-size:12px; font-weight:600; fill:var(--ink2); letter-spacing:.04em; }}
.b {{ fill:var(--panel); stroke:var(--line2); }} .ai {{ fill:var(--ai-soft); stroke:var(--ai); }} .db {{ fill:var(--db-soft); stroke:var(--db); }}
.ex {{ fill:var(--ex-soft); stroke:var(--ex); }} .nx {{ fill:none; stroke:var(--ex); stroke-dasharray:4 3; }}
.t {{ font-size:13px; font-weight:600; }} .s {{ font-size:11.5px; fill:var(--ink2); }}
.a {{ fill:none; stroke:var(--ink2); stroke-width:1.5; }} .a.dash {{ stroke-dasharray:5 4; }}
.bd {{ fill:var(--ink); }} .bt {{ font-size:11px; font-weight:600; fill:var(--bg); text-anchor:middle; }}
table {{ width:100%; border-collapse:collapse; background:var(--panel); border:1px solid var(--line); border-radius:12px; overflow:hidden; font-size:13px; }}
th, td {{ text-align:left; vertical-align:top; padding:10px 12px; border-bottom:1px solid var(--line); }}
th {{ font-size:11.5px; text-transform:uppercase; letter-spacing:.05em; color:var(--ink2); }}
tr:last-child td {{ border-bottom:0; }}
.n {{ display:inline-grid; place-items:center; width:22px; height:22px; border-radius:50%; background:var(--ink); color:var(--bg); font-size:11px; font-weight:600; }}
.tw {{ overflow-x:auto; }} .tw table {{ min-width:860px; }}
.note {{ background:var(--panel); border:1px solid var(--line); border-left:3px solid var(--accent); border-radius:6px; padding:12px 14px; margin:14px 0 0; max-width:980px; }}
</style>
<main>
<h1>PA Desk architecture</h1>
<p class="lead">What runs today, then what ships. Numbers on the arrows match the table below, so we can go one hop at a time.</p>

<h2>1. As built</h2>
<p class="lead">One FastAPI process serves the screens and runs the pipeline in-process. The only things that leave it are calls to Unstructured and Anthropic. Everything else is local files and SQLite.</p>
<div class="wrap">{AS_BUILT}</div>
<div class="legend">
  <span><i style="background:var(--ai-soft);border-color:var(--ai)"></i>Uses AI</span>
  <span><i style="background:var(--panel);border-color:var(--line2)"></i>Plain code</span>
  <span><i style="background:var(--db-soft);border-color:var(--db)"></i>Data store</span>
  <span><i style="background:var(--ex-soft);border-color:var(--ex)"></i>Outside our boundary</span>
  <span><i style="border-color:var(--ex);border-style:dashed"></i>Not built yet</span>
</div>

<h2>2. The hops</h2>
<div class="tw"><table>
<thead><tr><th>#</th><th>Hop</th><th>Protocol and data</th><th>What happens when it fails</th></tr></thead>
<tbody>{rows}</tbody></table></div>
<div class="note"><b>Trust boundary.</b> The packet text leaves the process in hops 3, 4 and 6. That is fine for made-up data. With real patient data, those two calls move to a self-hosted parsing service and a model endpoint covered by a business associate agreement, inside the private network on the next diagram.</div>

<h2>3. Production target</h2>
<p class="lead">Same five stages, split into services with a queue between them, so each can be scaled, replayed and measured on its own. The quality platform receives counts and timings only, never patient text.</p>
<div class="wrap">{TARGET}</div>
<div class="note"><b>What changes, and why.</b> Ingestion and the model call move behind a queue so a slow scan can't block a nurse. The policy library becomes a service with versions and an approval step, so every decision records which policy version it used. Feature flags turn each service line on only after its labeled test set passes. Traces and warehouse tables carry no patient text.</div>
</main>
"""
with open(OUT, "w", encoding="utf-8", newline="\n") as f:
    f.write(PAGE)
print("wrote", os.path.abspath(OUT))
