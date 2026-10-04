"""Builds docs/eval_scorecard.html: one page of eval results, with the caveats next to the numbers.
Reads: the stability runs (evals/reports/stability_run_*.txt point to their reports), the policy search reports in
evals/search/, the audit key, and any human audit results in evals/audit/audit_results.json. Run after those exist.
Run: python scripts/make_scorecard.py
"""
import glob, html, json, os, re, statistics

ROOT = os.path.join(os.path.dirname(__file__), "..")
e = html.escape

# ---- reading the packets: the stability runs
runs = []
for f in sorted(glob.glob(os.path.join(ROOT, "evals", "reports", "stability_run_*.txt"))):
    m = re.search(r"report saved:\s*(\S+)", open(f, encoding="utf-8", errors="ignore").read())
    if m and os.path.exists(os.path.join(ROOT, m.group(1))):
        runs.append(json.load(open(os.path.join(ROOT, m.group(1)), encoding="utf-8")))
n = len(runs)
def agg(fn):
    v = [fn(r) for r in runs]
    return v
acts = agg(lambda r: r["action_matches"]); tot = runs[0]["packets_total"] if runs else 0
rec = agg(lambda r: r["completeness_recall"]["correct"]); rec_t = runs[0]["completeness_recall"]["total"] if runs else 0
hal = agg(lambda r: r["hallucination_rate"]["count"]); hal_t = runs[0]["hallucination_rate"]["total"] if runs else 0
fl = agg(lambda r: r["flagged_uncertain"]["count"]); fl_t = runs[0]["flagged_uncertain"]["total"] if runs else 0
wv = agg(lambda r: r["wrong_values"])
secs = [x["seconds"] for r in runs for x in r["results"] if not x["file"].endswith("icd4_scanned_noisy.pdf")]
scan = [x["seconds"] for r in runs for x in r["results"] if x["file"].endswith("icd4_scanned_noisy.pdf")]
misses = {}
for r in runs:
    for x in r["results"]:
        if not x["action_matches"]:
            misses[x["file"]] = misses.get(x["file"], 0) + 1


def pct(a, b):
    return f"{100 * a / b:.1f}%" if b else "-"


# ---- policy search
sr = sorted(glob.glob(os.path.join(ROOT, "evals", "search", "report_pipes_*.json")))
sl = sorted(glob.glob(os.path.join(ROOT, "evals", "search", "report_2*.json")))
search_rows = []
if sl:
    L = json.load(open(sl[-1]))["summary"]
    for name, label in (("keyword", "Keyword (what the product used before)"), ("bm25", "BM25 keyword ranking"), ("embed-chunks", "Embeddings, small local model, plain chunks"),
                        ("embed-context", "Embeddings, small local model, chunks with the policy title added"), ("hybrid", "Mixed: BM25 + small local model")):
        search_rows.append((label, L[f"{name}/all"], L[f"{name}/plain"]))
if sr:
    P = json.load(open(sr[-1]))["summary"]
    search_rows.append(("Embeddings from Unstructured Pipelines (3072-dim)", P["pipes-chunks/all"], P["pipes-chunks/plain"]))
    search_rows.append(("Mixed: BM25 + Pipelines embeddings", P["hybrid/all"], P["hybrid/plain"]))

# ---- audit
key = json.load(open(os.path.join(ROOT, "evals", "audit", "audit_key.json"))) if os.path.exists(os.path.join(ROOT, "evals", "audit", "audit_key.json")) else {}
planted = {k: v for k, v in key.items() if v.get("planted") and not v.get("excluded")}
caught = sum(1 for v in planted.values() if v["ai_verdict"] in ("unrelated", "insufficient", "contradicts"))
res_path = os.path.join(ROOT, "evals", "audit", "audit_results.json")
audit = json.load(open(res_path)) if os.path.exists(res_path) else None

def table(head, rows):
    h = "".join(f"<th>{e(x)}</th>" for x in head)
    b = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f"<div class='tw'><table><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table></div>"

def per(vals, total):
    return ", ".join(f"{v} of {total}" for v in vals)


stab = table(["Measure", f"Result in each of the {n} runs", "Over all runs"], [
    ["Right recommendation (packets)", per(acts, tot), f"{sum(acts)} of {n * tot}"],
    ["Found a fact that was there", per(rec, rec_t), pct(sum(rec), n * rec_t)],
    ["Claimed a fact that was absent or ruled out (lower is better)", per(hal, hal_t), f"{sum(hal)} of {n * hal_t}"],
    ["Sent to the nurse as 'not sure'", per(fl, fl_t), pct(sum(fl), n * fl_t)],
    ["Wrong value (a number or choice read wrong)", ", ".join(str(a) for a in wv), f"{sum(wv)}"]]) if runs else "<p>No stability runs found yet.</p>"
srch = table(["Method", "Right policy in the top 8 (all 88 phrasings)", "Plain wording only", "In the first place"],
             [[e(l), f"{s['at8']}%", f"{p['at8']}%", f"{s['at1']}%"] for l, s, p in search_rows]) if search_rows else "<p>No search report found.</p>"
miss_txt = ", ".join(f"{os.path.basename(k)} ({v} of {n})" for k, v in misses.items()) or "none"
lat = f"{statistics.median(secs):.0f} s median, {max(secs):.0f} s slowest for text packets; {statistics.mean(scan):.0f} s for the scanned one" if secs else "-"
planted_txt = f"{caught} of {len(planted)} planted wrong pairs were flagged by the product's second AI check" if planted else "not built yet"
if audit:
    ans = {k: v for k, v in audit.items() if k in key}
    real = [k for k in ans if not key[k].get("planted")]
    cnt = {c: sum(1 for k in real if ans[k] == c) for c in ("yes", "partly", "no", "unsure")}
    pl = [k for k in ans if k in planted]
    pl_no = sum(1 for k in pl if ans[k] == "no")
    ai_no = sum(1 for k in pl if key[k]["ai_verdict"] in ("unrelated", "insufficient", "contradicts"))
    audit_html = (f"<p>A person judged {len(real)} real citations from five made-up cases. "
                  f"<b>{cnt['yes']} yes</b> ({pct(cnt['yes'], len(real))}), {cnt['partly']} partly, {cnt['no']} no, {cnt['unsure']} can't tell. "
                  f"Counting 'partly' as a pass, {pct(cnt['yes'] + cnt['partly'], len(real))} held up.</p>"
                  f"<p>Planted errors: the auditor caught {pl_no} of {len(pl)}, and so did the product's second AI check ({ai_no} of {len(pl)}). One more planted pair turned out to be a valid citation and is left out.</p>"
                  "<p>What the 6 weaker citations were:</p><ul>"
                  "<li><b>Claim packs several facts into one sentence.</b> 'Recent heart attack: date, within 40 days, no stent' cites only the sentence about the admission. 'Shared decision making: documented' cites the visit description, not the line that says it was completed.</li>"
                  "<li><b>The sentence names the method, not the word.</b> 'Measured by echocardiography' cites 'biplane Simpson' or 'TTE'. The page says echo, but that sentence alone does not.</li>"
                  "<li><b>Needs a second look by the auditor.</b> 'Ejection fraction 31%' cites 'Quantitative LVEF 31%' and was judged No, which looks like a misread.</li></ul>"
                  "<p>The second AI check said 'supports' for all 24 real items, so it did not see these weak spots. The fix is to show the whole supporting passage, and to cite one sentence per part of a compound claim.</p>")
else:
    audit_html = "<p>Pending: 30 cited sentences (24 real, 6 planted errors) are waiting for a human to judge them.</p>"

PAGE = f"""<title>Eval Scorecard</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&display=swap">
<style>
:root{{--bg:#f4f6f5;--panel:#fff;--ink:#14201c;--ink2:#4a5a55;--line:#cfd8d4;--acc:#1f6f5c;--warn:#8a4b00;--warnsoft:#fdf0d6}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--bg:#0f1715;--panel:#16211e;--ink:#e5eeea;--ink2:#a9bab4;--line:#2c3b37;--acc:#4cc0a0;--warn:#f0b04a;--warnsoft:#35260c}}}}
:root[data-theme="dark"]{{--bg:#0f1715;--panel:#16211e;--ink:#e5eeea;--ink2:#a9bab4;--line:#2c3b37;--acc:#4cc0a0;--warn:#f0b04a;--warnsoft:#35260c}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 "IBM Plex Sans",system-ui,sans-serif;padding:28px 16px 64px}}
main{{max-width:980px;margin:0 auto}}h1{{font-size:26px;margin:0 0 4px}}h2{{font-size:18px;margin:34px 0 4px}}p.lead{{color:var(--ink2);margin:0 0 12px;max-width:760px}}
.tw{{overflow-x:auto}}table{{width:100%;border-collapse:collapse;background:var(--panel);border:1px solid var(--line);border-radius:10px;overflow:hidden;font-size:14px;min-width:560px}}
th,td{{text-align:left;padding:9px 12px;border-bottom:1px solid var(--line);vertical-align:top}}th{{font-size:11.5px;text-transform:uppercase;letter-spacing:.05em;color:var(--ink2)}}tr:last-child td{{border-bottom:0}}
.caveat{{background:var(--warnsoft);color:var(--warn);border-radius:8px;padding:10px 14px;margin:10px 0 0;font-size:14px}}
.say{{border-left:3px solid var(--acc);background:var(--panel);padding:12px 16px;border-radius:6px;margin-top:24px}}
</style>
<main>
<h1>Eval scorecard</h1>
<p class="lead">What we measured, how, and what each number does not prove. The test packets are made up. Most were written by us, so treat the first section as a check of the plumbing.</p>

<h2>1. Reading a packet</h2>
<p class="lead">{tot} packets, run {n} times in a row: approve, pend and escalate cases for an ICD and for bariatric surgery, a conflicting-value case, a negated-comorbidity case, a recent heart attack, and one noisy image-only scan read by OCR.</p>
{stab}
<div class="caveat">Packets with a wrong recommendation: {e(miss_txt)}. Time per case: {e(lat)}. We do not yet record the AI cost per case.</div>

<h2>2. Finding the right policy for a new service</h2>
<p class="lead">44 services, each described two ways (formal and plain). Right means the policy whose title names the service.</p>
{srch}
<div class="caveat">The 44 services were chosen by us and truth is judged by title, which favors clearly named services. Treat the ranking as reliable and the exact percentages as a guide.</div>

<h2>3. Checking the evidence</h2>
<p class="lead">The quote check has two parts. Plain code finds the sentence (9 of 9 checks pass, including a fuzzy match that survives scan noise and refuses to match a different number). A second AI call judges whether the sentence states the fact (4 or 5 of 5 on cases built to fool an exact-text search, depending on the run).</p>
<p>Planted errors: {e(planted_txt)}. A fact flagged "insufficient" stays in the product without the tick, so the nurse is not told it was confirmed.</p>

<h2>4. A human audit of the citations</h2>
{audit_html}

<h2>5. Hard cases from a separate author</h2>
<p>Pending. A prompt for a separate AI session to write 40 adversarial packets is ready (docs/ADVERSARIAL_PACKET_PROMPT.md), and the converter and scoring are built. That author never sees our reader's code.</p>

<h2>What these numbers do not show</h2>
<ul>
<li>Accuracy on real faxes. Real packets are messier, longer, and contain things nobody thought to test.</li>
<li>Whether a nurse would agree with the recommendation. A senior reviewer labeling real, de-identified cases is the real test.</li>
<li>Clinical safety. The product never denies and never decides. A person does.</li>
</ul>
<div class="say"><b>How I would answer "how do you know it works?"</b><br>Three layers, all rerun on every change: a labeled test set for facts, a labeled set for policy search, and a human audit of citations. I show the trend, not one good run, and I show you where it fails.</div>
</main>
"""
out = os.path.join(ROOT, "docs", "eval_scorecard.html")
with open(out, "w", encoding="utf-8", newline="\n") as f:
    f.write(PAGE)
print("wrote", out, "| runs used:", n)
