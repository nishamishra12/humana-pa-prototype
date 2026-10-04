"""Writes docs/inner_workings.html: what happens inside steps 3 to 6 for one real packet, shown the way Unstructured's own
screen shows the parse: an input pane on the left and an output pane on the right, with real data from evals/trace/<name>.json.
Make the trace first:  PYTHONPATH=. python scripts/trace_case.py packets/multi/icd4_scanned_noisy.pdf
Then:                  python scripts/make_inner_workings.py
"""
import collections, difflib, html, json, os, re
from datetime import date

ROOT = os.path.join(os.path.dirname(__file__), "..")
T = json.load(open(os.path.join(ROOT, "evals", "trace", "icd4_scanned_noisy.json"), encoding="utf-8"))
OUT = os.path.join(ROOT, "docs", "inner_workings.html")
e = html.escape


def mark(text, spans, cls="hl"):
    """spans: list of (start, end, label). Returns escaped html with <mark> around each, non-overlapping."""
    out, pos = [], 0
    for s, t, lab in sorted(spans):
        if s < pos:
            continue
        out.append(e(text[pos:s]))
        out.append(f'<mark class="{cls}">{e(text[s:t])}<sup>{e(lab)}</sup></mark>')
        pos = t
    out.append(e(text[pos:]))
    return "".join(out)


def badge(txt, kind):
    return f'<span class="bg {kind}">{e(str(txt))}</span>'


def show(v):
    if v is None:
        return "-"
    if isinstance(v, list):
        return ", ".join(map(str, v)) or "-"
    return str(v)


# ---------- step 2 (summary)
els = T["ingest"]["elements"]
types = collections.Counter(x["type"] for x in els)
pages = len({x["page"] for x in els})
s2 = f"""<div class="two"><div class="pane"><h4>Input</h4><p>The packet PDF: {pages} pages, a made-up patient. Every page is a picture, with no text in the file.</p></div>
<div class="pane"><h4>Output: {len(els)} elements in {T['ingest']['seconds']} s</h4><p>{" ".join(badge(f"{k} {v}", "gray") for k, v in types.most_common())}</p>
<p class="note">This is the part Unstructured's screen already shows well. Everything below starts from these elements.</p></div></div>"""

# ---------- step 3
src = T["cpt_source"]
txt = src["text"]
spans = []
for lab, rx in [("CPT code", r"CPT:?\s*\d{5}"), ("planned date", r"Planned admi(?:t|ssion) date:?\s*[\d-]+"), ("member", r"Member:?\s+[A-Z][\w' -]+?(?=\s*[\n|]|\s+DOB)"),
                ("DOB", r"DOB:?\s*[\d-]+"), ("level of care", r"Level of care requested:?\s*\w+")]:
    m = re.search(rx, txt)
    if m:
        spans.append((m.start(), m.end(), lab))
snippet_end = min(len(txt), 1700)
spans = [x for x in spans if x[1] <= snippet_end]
reg = T["registry"]
hdr = reg["header"]
rows = [("CPT code", hdr.get("_cpt")), ("Procedure as written", hdr.get("_procedure")), ("Planned admit date", hdr.get("_admit")), ("Level of care", hdr.get("_setting")), ("Facility", hdr.get("_facility"))]
mem = "name, date of birth, member id"
tbl = "".join(f"<tr><td>{e(k)}</td><td><b>{e(show(v))}</b></td></tr>" for k, v in rows)
lookup = "".join(
    f'<tr class="{"on" if p["key"] == reg["matched"] else ""}"><td>{e(", ".join(p["cpts"]))}</td><td>{e(p["name"])}</td><td>{" ".join(badge(x["id"], "gray") for x in p["policies"] if x["criteria"])}</td></tr>'
    for p in reg["procedures"])
crit_by = collections.OrderedDict()
for c in reg["criteria"]:
    crit_by.setdefault(c["policy"], []).append(c)
pol_names = {p["id"]: (p["title"], p["level"]) for pr in reg["procedures"] for p in pr["policies"]}
crit_html = ""
for pid, cs in crit_by.items():
    t, lvl = pol_names.get(pid, (pid, ""))
    crit_html += f'<h5>{badge(lvl, "ai")} {e(t)} <span class="note">({len(cs)} criteria)</span></h5><ul class="crit">' + "".join(
        f'<li><b>{e(c["id"])}</b> {e(c["text"])} <span class="note">needs: {e(show(c["fact"]))}. {e(c.get("cite") or "")}</span></li>' for c in cs) + "</ul>"
NAMES = {"REGULATION": "Regulation", "NCD": "NCD", "LCD": "LCD", "HUMANA_INTERNAL": "Humana policy", "MCG": "MCG"}
hier = " &gt; ".join(e(NAMES.get(h, h)) for h in (reg.get("hierarchy") or []))
s3 = f"""<div class="two"><div class="pane"><h4>Input: page {src['page']} from Unstructured</h4><pre class="pg">{mark(txt[:snippet_end], spans)}{'...' if len(txt) > snippet_end else ''}</pre>
<p class="note">Plain pattern matching finds the labeled fields. No AI. The member's name and date of birth are kept only to check later that each page belongs to this patient ({e(mem)}).</p></div>
<div class="pane"><h4>Output 1: what the code read</h4><table class="kv">{tbl}</table>
<h4>Output 2: the lookup</h4><p>The CPT code is looked up in a short list of services we have policies for. It is a dictionary, not a search. If the code is not in the list, the case says "no policy" and goes to a person.</p>
<table class="kv look"><thead><tr><th>CPT</th><th>Service</th><th>Policy stack</th></tr></thead><tbody>{lookup}</tbody></table>
<p>Match: <b>{e(hdr.get('_cpt'))}</b> gives <b>{e(next(p['name'] for p in reg['procedures'] if p['key'] == reg['matched']))}</b>.</p></div></div>
<div class="pane wide"><h4>Output 3: the policy stack for this service, {len(reg['criteria'])} criteria</h4>
<p class="note">Order of authority: {hier}. A Humana policy and MCG are placeholders, shown only as slots. Each criterion names the one fact the reader must find.</p>{crit_html}</div>"""

# ---------- step 4
tf = T["trace"]["tool_facts"]
reads = T["reads"]
comb = T["trace"]["combined"]
ptests = T["trace"]["policy_tests"]
rows4 = ""
for f in tf:
    k = f["key"]
    cells = "".join(f"<td>{badge(r[k]['status'], 'green' if r[k]['status'] in ('found', 'none') else 'amber')} {e(show(r[k]['value']))}</td>" for r in reads)
    ok = comb[k]["agreed"]
    rows4 += f"<tr><td><b>{e(f['label'])}</b></td>{cells}<td>{badge('agree', 'green') if ok else badge('not sure', 'amber')}</td></tr>"
srcs = re.sub(r"^\s+", "", T["trace"]["system_prompt"])
rules4 = [x.strip() for x in re.split(r"\n\s*\n", srcs) if x.strip()][:9]
def rule_li(x):
    x = re.sub(r"^\d+\.\s*", "", " ".join(x.split()))
    title, _, body = x.partition(". ")
    body = body[:118].rsplit(" ", 1)[0] + "..." if len(body) > 118 else body
    return f"<li><b>{e(title.capitalize())}.</b> {e(body)}</li>"


rules_html = "".join(rule_li(x) for x in rules4[1:])
omt = next((r["optimal_medical_therapy_months"] for r in reads if r["optimal_medical_therapy_months"].get("calc")), None)
date_note = ""
if omt and omt["calc"].get("start_date") and hdr.get("_admit"):
    a, b = date.fromisoformat(omt["calc"]["start_date"]), date.fromisoformat(hdr["_admit"])
    date_note = (f'<div class="callout"><b>Dates are counted by code, not by the AI.</b> The reader copied the start date <b>{a}</b> from the page. '
                 f'The planned procedure date is <b>{b}</b> (read in step 3). Code counts {(b - a).days} days, which is <b>{round((b - a).days / 30.4375, 1)} months</b>. '
                 f'The same rule decides "heart attack in the last 40 days" and "stay of at least 2 midnights".</div>')
pv = e(T["trace"]["packet_preview"][:900])
s4 = f"""<div class="two"><div class="pane"><h4>Input: one request to the reader (Claude Sonnet)</h4>
<p class="note">Sent three times, in parallel, with the same content.</p>
<div class="msg"><b>Rules it must follow</b><ol>{rules_html}</ol></div>
<div class="msg"><b>The packet</b> ({T['trace']['packet_chars']:,} characters, {pages} pages, each element tagged with its page)<pre class="pg">Procedure: Implantable cardioverter defibrillator
Member: (name and date of birth from step 3)
Planned procedure date: {e(show(hdr.get('_admit')))}

Packet:
{pv}...</pre></div>
<div class="msg"><b>The form it must fill</b>, one entry per fact, each with the policy test it feeds{"".join(f'<div class="fr"><b>{e(f["label"])}</b> {e(f["ask"][:130])}<div class="note">Policy test: {e(ptests.get(f["key"], ["none"])[0][:110])}</div></div>' for f in tf[:3])}<p class="note">...and {len(tf) - 3} more facts. It must answer by filling this form (a forced tool call), so the reply is data, not prose.</p></div></div>
<div class="pane"><h4>Output: three independent reads, side by side</h4>
<table class="reads"><thead><tr><th>Fact</th><th>Read 1</th><th>Read 2</th><th>Read 3</th><th></th></tr></thead><tbody>{rows4}</tbody></table>
<p class="note">If the three reads disagree on a status or a value, the fact becomes "not sure" and goes to the nurse. Here they all agree. For each fact the reader also returns every sentence that states it, copied word for word, with its date. Free-text wording can differ between reads (compare the comorbidities). The status and any number must match.</p>{date_note}</div></div>"""

# ---------- step 5
items = {i["id"]: i for i in T["trace"]["items"]}
ev_rows = ""
for f in tf:
    k = f["key"]
    fct = T["facts"][k]
    claim = next((i["claim"] for ik, i in items.items() if ik.startswith(k + "#")), "The packet says there is none." if fct["status"] == "none" else "(not checked)")
    for x in (fct.get("evidence") or [])[:1]:
        v = x.get("verdict") or "-"
        ev_rows += (f"<tr><td><b>{e(f['label'])}</b><div class='note'>{e(claim)}</div></td><td class='q'>{e(x['quote'][:170])}{'...' if len(x['quote']) > 170 else ''}<div class='note'>page {x['page']}</div></td>"
                    f"<td>{badge(x['match'] + ' ' + str(x['score']), 'green' if x['match'] == 'exact' else 'amber')}</td>"
                    f"<td>{badge(v, 'green' if v == 'supports' else 'amber')}<div class='note'>{e((x.get('reason') or '')[:150])}</div></td></tr>")
D = T["matcher_demo"]
def diff_html(a, b):
    sm = difflib.SequenceMatcher(None, a, b)
    A, B = [], []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            A.append(e(a[i1:i2])); B.append(e(b[j1:j2]))
        else:
            A.append(f"<del>{e(a[i1:i2])}</del>" if i2 > i1 else ""); B.append(f"<ins>{e(b[j1:j2])}</ins>" if j2 > j1 else "")
    return "".join(A), "".join(B)
def short(s, n=95):
    return s[:n] + ("..." if len(s) > n else "")
da, db_ = diff_html(short(D["original"]), short(D["noisy"]))
na, nb = diff_html(short(D["original"]), short(D["number_changed"]))
fz = (f"<table class='demo'><tbody>"
      f"<tr><td>{badge('1', 'gray')} The quote exactly as on the page</td><td>{e(short(D['original']))}</td><td>{badge('exact 100', 'green')} accepted</td></tr>"
      f"<tr><td>{badge('2', 'gray')} The quote with scan-style typos (changed letters shown)</td><td>{db_}</td><td>{badge('fuzzy ' + str(D['noisy_hit']['score']), 'amber') if D['noisy_hit'] else badge('refused', 'red')} {'accepted: 88 or more, same numbers' if D['noisy_hit'] else ''}</td></tr>"
      f"<tr><td>{badge('3', 'gray')} The quote with one number changed, {e(D['changed_from'])} to {e(D['changed_to'])}</td><td>{nb}</td><td>{badge('refused', 'red') if not D['number_hit'] else badge('matched', 'amber')} {'refused: the numbers differ, however similar the letters' if not D['number_hit'] else ''}</td></tr></tbody></table>")
gd = T["facts"]["optimal_medical_therapy_months"]["evidence"][0]
pg = T["pages"][str(gd["page"])]
i0 = pg.find(gd["quote"])
ctx_a, ctx_b = max(0, i0 - 260), min(len(pg), i0 + len(gd["quote"]) + 160)
pgmark = mark(pg[ctx_a:ctx_b], [(i0 - ctx_a, i0 - ctx_a + len(gd["quote"]), "found")]) if i0 >= 0 else e(pg[:400])
s5 = f"""<div class="pane wide"><h4>Every quote the reader gave is looked up on the real page, then read by a second AI</h4>
<table class="ev"><thead><tr><th>Claim being checked</th><th>The sentence the reader quoted</th><th>Found on the page by</th><th>Second AI check</th></tr></thead><tbody>{ev_rows}</tbody></table></div>
<div class="two"><div class="pane"><h4>How the page lookup works, tested with the real function</h4><p>First an exact match, ignoring case and extra spaces. If that fails, fuzzy matching: it slides the quote along the page and counts the single-letter edits needed to turn the best-fitting stretch into the quote. Fewer edits give a score closer to 100, and 88 or more is accepted. <b>It compares letters, not meaning.</b> The numbers must be identical.</p>{fz}</div>
<div class="pane"><h4>What the nurse sees: the real text on page {gd['page']}, highlighted</h4><pre class="pg">{pgmark}</pre><p class="note">The screen highlights the text from the page, not the AI's version. The second AI then answers one word per quote: supports, contradicts, unrelated or insufficient. It checked "{e(show(T['facts']['optimal_medical_therapy_months']['value']))} months" against the start date, not against a count.</p></div></div>"""

# ---------- step 6
cl = T["analysis"]["checklist"]
rows6 = "".join(f"<tr><td>{badge(c['layer'], 'ai')}</td><td>{e(c['text'])}<div class='note'>{e(c.get('cite') or '')}</div></td><td>{e(show(T['facts'].get(c['fact'], {}).get('value') if c['fact'] else None) if c['fact'] else '-')}</td><td>{badge(c['status'], 'green' if c['status'] == 'met' else ('gray' if c['status'] == 'info' else 'amber'))}</td></tr>" for c in cl)
act = T["analysis"]["action"]
s6 = f"""<div class="two"><div class="pane"><h4>Input: the facts and the policy criteria</h4><p>Each criterion names one fact and a test, for example "ejection fraction is 35% or less". The engine compares the found value with the test. It is plain code.</p>
<div class="callout"><b>Decision order, always the same.</b><ol><li>A fact is missing: <b>pend</b>, with one question for the provider.</li><li>A fact is unclear or contradicts itself: <b>verify</b>, a person settles it.</li><li>Every fact is present and clear but a rule is not met: <b>escalate</b> to a medical director.</li><li>Everything is present and every rule is met: <b>approve</b>.</li></ol>There is no "deny". Only a medical director can deny.</div></div>
<div class="pane"><h4>Output: the checklist and the recommendation</h4><table class="ev"><thead><tr><th>Layer</th><th>Criterion</th><th>Value found</th><th>Result</th></tr></thead><tbody>{rows6}</tbody></table>
<div class="rec">Recommendation: <b>{e(act)}</b>. A nurse still confirms it. The same facts always give the same answer.</div></div></div>"""

# ---------- found while looking
found = """<ul><li><b>The request form on a scan.</b> Unstructured read this form two different ways on two calls: once as one long line with no colons, once as a table. My header reader only understood typed forms, so on scans it missed the member, the facility and the planned date, and the date counting never switched on. It now handles both layouts. On the 76 typed packets it gives identical results.</li>
<li><b>The meaning check against a counted number.</b> The packet says "8 months as of today". Code counts 9.5 months to the planned procedure date. The second AI called that a contradiction and the case was flagged. The check now tests the start date the packet gives, and the case is approved.</li></ul>
<p class="note">Neither would have been found from the score alone. Looking inside each step is how I found them.</p>"""

STEPS = [("2", "ETL + AI", s2), ("3", "Pick the policy", s3), ("4", "Read the packet", s4), ("5", "Check the evidence", s5), ("6", "Apply the rules", s6)]
nav = "".join(f'<a href="#s{n}"><span class="n">{n}</span>{e(t)}</a>' for n, t, _ in STEPS)
sections = "".join(f'<section id="s{n}"><h2><span class="n">{n}</span>{e(t)}</h2>{body}</section>' for n, t, body in STEPS)

PAGE = f"""<meta charset="utf-8"><title>PA Desk Inner Workings</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400&display=swap">
<style>
:root{{--bg:#f3f6f4;--panel:#fff;--ink:#14201c;--ink2:#51605b;--line:#cfd9d4;--acc:#1f6f5c;--accsoft:#e1efe9;--ai:#5f3aa8;--aisoft:#ebe2f8;--amber:#8a5a00;--ambersoft:#fcefd0;--red:#b8452f;--redsoft:#fbe8e3;--gray:#4a5a64;--graysoft:#e8edf0;--mark:#ffe98a}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{color-scheme:dark;--bg:#0e1614;--panel:#16211e;--ink:#e6efeb;--ink2:#a6b8b1;--line:#2b3a36;--acc:#4cc0a0;--accsoft:#12302a;--ai:#b79cf0;--aisoft:#2a2046;--amber:#f0b04a;--ambersoft:#35260c;--red:#f08a73;--redsoft:#3a1f19;--gray:#a7b6bf;--graysoft:#1f2a30;--mark:#5a4b00}}}}
:root[data-theme="dark"]{{color-scheme:dark;--bg:#0e1614;--panel:#16211e;--ink:#e6efeb;--ink2:#a6b8b1;--line:#2b3a36;--acc:#4cc0a0;--accsoft:#12302a;--ai:#b79cf0;--aisoft:#2a2046;--amber:#f0b04a;--ambersoft:#35260c;--red:#f08a73;--redsoft:#3a1f19;--gray:#a7b6bf;--graysoft:#1f2a30;--mark:#5a4b00}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);font:14px/1.55 "IBM Plex Sans",system-ui,sans-serif;padding-inline:16px;padding-block:22px 80px}}
main{{max-width:1180px;margin:0 auto}}
h1{{font-size:25px;margin:0 0 4px;font-weight:600}}.lead{{color:var(--ink2);max-width:780px;margin:0 0 14px}}
nav{{position:sticky;top:0;background:var(--bg);display:flex;gap:6px;flex-wrap:wrap;padding:10px 0;border-bottom:1px solid var(--line);margin-bottom:6px;z-index:3}}
nav a{{display:inline-flex;align-items:center;gap:8px;padding:6px 12px;border:1px solid var(--line);border-radius:999px;color:var(--ink);text-decoration:none;font-weight:500;background:var(--panel)}}
.n{{display:inline-grid;place-items:center;width:22px;height:22px;border-radius:50%;background:var(--acc);color:var(--bg);font-size:12px;font-weight:600}}
section{{margin-top:30px}}h2{{display:flex;align-items:center;gap:10px;font-size:19px;margin:0 0 12px}}
h4{{margin:0 0 8px;font-size:12px;letter-spacing:.07em;text-transform:uppercase;color:var(--ink2)}}h5{{margin:14px 0 4px;font-size:14px}}
.two{{display:grid;grid-template-columns:repeat(auto-fit,minmax(380px,1fr));gap:14px;margin-bottom:14px}}
.pane{{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px 16px;min-width:0}}.pane.wide{{margin-bottom:14px}}
.pane p{{margin:0 0 10px}}.note{{color:var(--ink2);font-size:12.5px}}
pre.pg{{white-space:pre-wrap;word-break:break-word;font:12.5px/1.6 "IBM Plex Mono",ui-monospace,monospace;background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:12px;margin:0 0 10px;max-height:340px;overflow:auto}}
mark.hl{{background:var(--mark);color:inherit;border-radius:3px;padding:0 2px}}mark.hl sup{{font:600 9px "IBM Plex Sans",sans-serif;color:var(--ai);margin-left:3px;text-transform:uppercase;letter-spacing:.04em}}
table{{width:100%;border-collapse:collapse;font-size:13px}}th,td{{text-align:left;padding:7px 9px;border-bottom:1px solid var(--line);vertical-align:top}}th{{font-size:11px;letter-spacing:.05em;text-transform:uppercase;color:var(--ink2)}}
tr:last-child td{{border-bottom:0}}table.look tr.on td{{background:var(--accsoft);font-weight:500}}
.tw{{overflow-x:auto}}.q{{font:12px/1.5 "IBM Plex Mono",monospace}}
.bg{{display:inline-block;border-radius:999px;padding:1px 9px;font-size:12px;font-weight:500;margin:1px 2px 1px 0}}
.bg.green{{background:var(--accsoft);color:var(--acc)}}.bg.amber{{background:var(--ambersoft);color:var(--amber)}}.bg.red{{background:var(--redsoft);color:var(--red)}}.bg.gray{{background:var(--graysoft);color:var(--gray)}}.bg.ai{{background:var(--aisoft);color:var(--ai)}}
.msg{{border:1px solid var(--line);border-radius:8px;padding:10px 12px;margin:0 0 10px;background:var(--bg)}}.msg ol{{margin:6px 0 0;padding-left:20px}}.fr{{margin:6px 0;padding-top:6px;border-top:1px dashed var(--line)}}
.callout{{background:var(--accsoft);border-radius:8px;padding:10px 14px;margin-top:10px}}.callout ol{{margin:6px 0;padding-left:20px}}
.rec{{margin-top:12px;background:var(--acc);color:var(--bg);border-radius:8px;padding:10px 14px;font-size:15px}}
ul.crit{{margin:4px 0 0;padding-left:18px}}ul.crit li{{margin:3px 0}}
del{{background:var(--redsoft);color:var(--red);text-decoration:none}}ins{{background:var(--ambersoft);color:var(--amber);text-decoration:none;font-weight:600}}
table.demo td:first-child{{width:28%}}
.found{{background:var(--ambersoft);border-radius:10px;padding:14px 18px;margin-top:30px}}
</style>
<main>
<h1>Inside the case: what each step does</h1>
<p class="lead">One real, made-up packet (<b>{e(T['file'])}</b>, a scan) run through PA Desk. Each step shows what goes in on the left and what comes out on the right, the way Unstructured's screen shows its parse. The data on this page is the real output of that run.</p>
<nav>{nav}</nav>
{sections}
<div class="found"><h2 style="margin-top:0">What I found by looking inside</h2>{found}</div>
</main>
"""
with open(OUT, "w", encoding="utf-8", newline="\n") as f:
    f.write(PAGE)
print("wrote", OUT)
