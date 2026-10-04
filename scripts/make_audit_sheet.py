"""Builds a human audit of the product's citations: 30 cited sentences for a person to judge.

For each item the auditor sees the claim ("Ejection fraction: 28%"), the page, and the cited sentence highlighted in
the page text. She answers: does this page support the claim? Yes, partly, no, or can't tell. The AI's own check is
kept in evals/audit/audit_key.json and is NOT shown, so the human answer is independent.
Output: evals/audit/audit_sheet.html (open in any browser) and evals/audit/audit_key.json.
Run: python scripts/make_audit_sheet.py
"""
import glob, html, json, os, random, sys

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, ROOT)
from pipeline.procedures import library, procedure_for_cpt, defs_by_key, display_for

items, key = [], {}
for f in sorted(glob.glob(os.path.join(ROOT, "packets", "fixtures", "*.json"))):
    d = json.load(open(f, encoding="utf-8"))
    facts = d["facts"]
    _, proc = procedure_for_cpt(facts.get("_cpt"))
    defs = defs_by_key(proc)
    pages = {}
    for e in d["elements"]:
        pages.setdefault(e["page"], []).append(e["text"])
    who = facts.get("_member", {}).get("name", d["file"])
    for k, df in defs.items():
        fact = facts.get(k)
        if not isinstance(fact, dict) or not fact.get("evidence") or fact["status"] not in ("found", "none"):
            continue
        ev = next((x for x in fact["evidence"] if x.get("supports", True)), None)
        if not ev or ev["page"] not in pages:
            continue
        claim = display_for(df, fact) if fact["status"] == "found" else f"The packet says there is none ({df['label'].lower()})"
        items.append(dict(case=who, procedure=proc["name"], fact=df["label"], claim=f"{df['label']}: {claim}" if fact["status"] == "found" else claim,
                          page=ev["page"], quote=ev["quote"], page_text="\n".join(pages[ev["page"]]), status=fact["status"],
                          ai_verdict=ev.get("verdict"), match=ev.get("match"), fact_key=k, file=d["file"]))
rng = random.Random(7)
rng.shuffle(items)
real = items[:24]
# six planted errors: a claim paired with a sentence about a different fact in the same case. The right answer is "No".
# They check that the auditor is reading, and they test whether the product's own meaning check catches a wrong pairing.
planted, used = [], set()
for it in real[:]:
    others = [o for o in items if o["case"] == it["case"] and o["fact_key"] != it["fact_key"] and o["quote"] != it["quote"]]
    if len(planted) < 6 and it["case"] + it["fact_key"] not in used and others:
        o = rng.choice(others)
        used.add(it["case"] + it["fact_key"])
        planted.append(dict(it, quote=o["quote"], page=o["page"], page_text=o["page_text"], planted=True, ai_verdict=None))
try:  # ask the product's second AI check about the planted pairs
    import anthropic
    from dotenv import load_dotenv
    load_dotenv(os.path.join(ROOT, ".env"))
    from pipeline import evidence as ev_mod
    got = ev_mod.verify_meaning([dict(id=f"p{i}", claim=f"The packet states: {x['claim']}", quote=x["quote"], context=x["page_text"][:700]) for i, x in enumerate(planted)],
                                anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"]))
    for i, x in enumerate(planted):
        x["ai_verdict"] = (got.get(f"p{i}") or (None,))[0]
except Exception as e:
    print("could not run the AI check on planted items:", e)
items = real + planted
rng.shuffle(items)
for i, it in enumerate(items, 1):
    it["id"] = f"c{i:02d}"
    key[it["id"]] = dict(case=it["case"], fact_key=it["fact_key"], file=it["file"], status=it["status"], ai_verdict=it["ai_verdict"], match=it["match"], page=it["page"], planted=bool(it.get("planted")))
os.makedirs(os.path.join(ROOT, "evals", "audit"), exist_ok=True)
json.dump(key, open(os.path.join(ROOT, "evals", "audit", "audit_key.json"), "w", encoding="utf-8"), indent=1)


def render(it):
    pt, q = html.escape(it["page_text"]), html.escape(it["quote"])
    pt = pt.replace(q, f"<mark>{q}</mark>") if q in pt else pt + f"<div class='nf'>The cited sentence: <mark>{q}</mark></div>"
    return f"""<section class="card" id="{it['id']}">
<div class="meta"><span>{html.escape(it['procedure'])}</span><span>{html.escape(it['case'])}</span><span>cited page {it['page']}</span></div>
<h3>{html.escape(it['claim'])}</h3>
<div class="ask">Does this page support that claim?</div>
<div class="opts" role="radiogroup" aria-label="Answer for {it['id']}">
<label><input type="radio" name="{it['id']}" value="yes"> Yes</label>
<label><input type="radio" name="{it['id']}" value="partly"> Partly</label>
<label><input type="radio" name="{it['id']}" value="no"> No</label>
<label><input type="radio" name="{it['id']}" value="unsure"> Can't tell</label></div>
<details><summary>Show the page</summary><pre class="page">{pt}</pre></details></section>"""


cards = "\n".join(render(i) for i in items)
PAGE = """<title>Citation Audit</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&display=swap">
<style>
:root{--bg:#f4f6f5;--panel:#fff;--ink:#14201c;--ink2:#4a5a55;--line:#cfd8d4;--acc:#1f6f5c;--accsoft:#e2f0eb;--mark:#ffe98a}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#0f1715;--panel:#16211e;--ink:#e5eeea;--ink2:#a9bab4;--line:#2c3b37;--acc:#4cc0a0;--accsoft:#12302a;--mark:#5a4b00}}
:root[data-theme="dark"]{--bg:#0f1715;--panel:#16211e;--ink:#e5eeea;--ink2:#a9bab4;--line:#2c3b37;--acc:#4cc0a0;--accsoft:#12302a;--mark:#5a4b00}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 "IBM Plex Sans",system-ui,sans-serif;padding:24px 16px 120px}
main{max-width:860px;margin:0 auto}h1{font-size:24px;margin:0 0 6px}p.lead{color:var(--ink2);margin:0 0 16px;max-width:680px}
.bar{position:sticky;top:0;z-index:5;background:var(--bg);padding:10px 0;display:flex;gap:12px;align-items:center;flex-wrap:wrap;border-bottom:1px solid var(--line);margin-bottom:16px}
.bar b{font-variant-numeric:tabular-nums}button{font:inherit;padding:8px 14px;border-radius:8px;border:1px solid var(--acc);background:var(--acc);color:var(--bg);font-weight:600;cursor:pointer}
button.alt{background:transparent;color:var(--acc)}
.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px 18px;margin-bottom:14px}
.card.done{border-color:var(--acc)}.meta{display:flex;gap:12px;flex-wrap:wrap;color:var(--ink2);font-size:12.5px}
h3{font-size:17px;margin:6px 0 8px;font-weight:600}.ask{color:var(--ink2);font-size:13px;margin-bottom:6px}
.opts{display:flex;gap:8px;flex-wrap:wrap}.opts label{border:1px solid var(--line);border-radius:8px;padding:8px 14px;cursor:pointer;background:var(--bg)}
.opts label:has(input:checked){border-color:var(--acc);background:var(--accsoft);font-weight:600}.opts input{margin-right:6px}
details{margin-top:12px}summary{cursor:pointer;color:var(--acc);font-weight:500}pre.page{white-space:pre-wrap;font:13px/1.55 "IBM Plex Sans",system-ui,sans-serif;background:var(--bg);border-radius:8px;padding:12px;margin:8px 0 0;max-height:360px;overflow:auto}
mark{background:var(--mark);color:inherit;padding:1px 2px;border-radius:3px}.nf{margin-top:8px;color:var(--ink2)}
#out{width:100%;min-height:90px;margin-top:10px;font:12px/1.4 ui-monospace,Consolas,monospace;background:var(--panel);color:var(--ink);border:1px solid var(--line);border-radius:8px;padding:8px}
</style>
<main>
<h1>Citation audit</h1>
<p class="lead">Each item shows a claim the product made and the page it cited. Open the page, find the highlighted sentence, and judge it yourself. Do not guess what the product meant. Answer only from what the page says. All data is made up. About 30 minutes.</p>
<div class="bar"><span>Answered <b id="n">0</b> of __N__</span><button id="copy">Copy my answers</button><button class="alt" id="reset">Clear</button></div>
__CARDS__
<h3>Your answers</h3>
<p class="lead">Press Copy, then paste the text into the chat. If copying is blocked, select the box below and copy by hand.</p>
<textarea id="out" readonly placeholder="Your answers appear here"></textarea>
</main>
<script>
const KEY="pa-audit-v1";let ans={};
try{ans=JSON.parse(localStorage.getItem(KEY)||"{}")}catch(e){}
function paint(){let n=0;document.querySelectorAll(".card").forEach(c=>{const v=ans[c.id];c.classList.toggle("done",!!v);if(v){n++;const r=c.querySelector('input[value="'+v+'"]');if(r)r.checked=true}});document.getElementById("n").textContent=n;
 document.getElementById("out").value=JSON.stringify(ans)}
document.addEventListener("change",e=>{if(e.target.type==="radio"){ans[e.target.name]=e.target.value;try{localStorage.setItem(KEY,JSON.stringify(ans))}catch(_){}paint()}});
document.getElementById("copy").onclick=async()=>{const t=JSON.stringify(ans);try{await navigator.clipboard.writeText(t);document.getElementById("copy").textContent="Copied"}catch(e){document.getElementById("out").select();document.getElementById("copy").textContent="Select and copy below"}setTimeout(()=>document.getElementById("copy").textContent="Copy my answers",1800)};
document.getElementById("reset").onclick=()=>{ans={};try{localStorage.removeItem(KEY)}catch(e){}document.querySelectorAll("input[type=radio]").forEach(r=>r.checked=false);paint()};
paint();
</script>
""".replace("__CARDS__", cards).replace("__N__", str(len(items)))
with open(os.path.join(ROOT, "evals", "audit", "audit_sheet.html"), "w", encoding="utf-8", newline="\n") as f:
    f.write(PAGE)
print(len(items), "items -> evals/audit/audit_sheet.html; answer key -> evals/audit/audit_key.json")
by = {}
for v in key.values():
    by[v["ai_verdict"]] = by.get(v["ai_verdict"], 0) + 1
print("AI check verdicts among the items:", by)
