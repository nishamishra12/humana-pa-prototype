"""Writes docs/architecture_walkthrough.html: the path of one case through PA Desk, what is AI and what is plain code,
what surrounds the case (data, traces, evals, dashboards, hosting), and a say-it-out-loud explainer for each step.
Run: python scripts/make_architecture_walkthrough.py
"""
import html, os

OUT = os.path.join(os.path.dirname(__file__), "..", "docs", "architecture_walkthrough.html")
e = html.escape
P = []  # svg parts


def box(x, y, w, h, title, lines, kind, tag=None, dashed=False):
    P.append(f'<rect class="b {kind}{" dsh" if dashed else ""}" x="{x}" y="{y}" width="{w}" height="{h}" rx="8"/>')
    if tag:
        P.append(f'<text class="tg {kind}" x="{x + 10}" y="{y - 7}">{e(tag)}</text>')
    P.append(f'<text class="t" x="{x + 10}" y="{y + 21}">{e(title)}</text>')
    for i, ln in enumerate(lines):
        P.append(f'<text class="s" x="{x + 10}" y="{y + 41 + i * 16}">{e(ln)}</text>')


def arrow(pts, dashed=False):
    d = " ".join(f"{a},{b}" for a, b in pts)
    P.append(f'<polyline class="a{" dsh" if dashed else ""}" points="{d}" marker-end="url(#ah)"/>')


def badge(n, x, y):
    P.append(f'<circle class="bd" cx="{x}" cy="{y}" r="12"/><text class="bt" x="{x}" y="{y + 4}">{n}</text>')


W = 156
GAP = 22
X0 = 24
OFF = 232  # the existing diagram moves down to make room for the library lane

P_main, P = P, []
P.append(f'<text class="zt" x="{X0}" y="22">Built before any case: the policy library</text>')
lane = [
    ("Policy sources", ["CMS coverage API,", "eCFR, or your PDF"], "ext", "OUTSIDE SOURCE", False),
    ("ETL + AI", ["Unstructured turns", "each policy into", "structured elements"], "ext", "OUTSIDE SERVICE + AI", False),
    ("AI drafts the rules", ["Claude fills a form:", "each rule carries its", "exact source quote"], "ai", "AI MODEL", False),
    ("Code checks", ["every quote, number", "and fact is checked;", "compared with ours"], "code", "CODE", False),
    ("Policy owner approves", ["NOT BUILT YET", "owner reviews, edits,", "and publishes a version"], "human", "PERSON", True),
    ("Policy library", ["versioned: CPT code,", "policies, rules, and", "the source of each"], "code", "CODE + DATA", False),
]
LX = []
for i, (t, lines, kind, tag, dsh) in enumerate(lane):
    x = X0 + i * (W + GAP)
    LX.append(x)
    box(x, 56, W, 100, t, lines, kind, tag, dashed=dsh)
    if i:
        arrow([(x - GAP + 2, 106), (x - 2, 106)])
P.append(f'<text class="s" x="{X0}" y="184">Built and tested on 5 policies (15 of 17 approved rules reproduced). The gap: owner approval and publishing. The library in use today is still the hand-written one.</text>')
P_lane, P = P, P_main
Y = 70
H = 118
stages = [
    ("Intake", ["Intake uploads a PDF", "PDF only, 15 MB max", "40 new packets a day"], "code", "CODE"),
    ("ETL + AI", ["Unstructured service:", "OCR + vision models", "pages to elements"], "ext", "OUTSIDE SERVICE + AI"),
    ("Pick the policy", ["CPT code on the form", "picks the policy set:", "ICD, bariatric, spine"], "code", "CODE"),
    ("Read the packet", ["Claude reads all pages", "fills the fact form", "3 reads must agree"], "ai", "AI MODEL"),
    ("Check evidence", ["find each quote (fuzzy)", "2nd AI checks meaning", "numbers must match"], "ai", "CODE + AI"),
    ("Apply the rules", ["facts vs criteria", "approve, pend, escalate", "or verify. Never deny"], "code", "CODE"),
    ("A person decides", ["nurse confirms or fixes", "only a director denies", "every step is logged"], "human", "PERSON"),
]
xs = []
for i, (t, lines, kind, tag) in enumerate(stages):
    x = X0 + i * (W + GAP)
    xs.append(x)
    box(x, Y, W, H, t, lines, kind, tag)
    badge(i + 1, x + W - 14, Y + 14)
    if i:
        arrow([(x - GAP + 2, Y + H // 2), (x - 2, Y + H // 2)])

P_lane.append(f'<polyline class="a" points="{LX[5] + W // 2},158 {LX[5] + W // 2},{OFF - 18} {xs[2] + W // 2},{OFF - 18} {xs[2] + W // 2},{OFF + Y - 4}" marker-end="url(#ah)"/>')
P_lane.append(f'<text class="s" x="{xs[2] + W // 2 + 8}" y="{OFF - 24}">step 3 and step 6 read the approved library</text>')

# branch: no policy for this code
bx = xs[2]
box(bx, 250, 330, 92, "No policy for this code", ["today: the case says no policy,", "and goes to a person", "planned: draft one for the owner to approve"], "ai", None, dashed=True)
arrow([(xs[2] + W // 2, Y + H + 2), (xs[2] + W // 2, 248)], dashed=True)
arrow([(bx + 330 + 2, 296), (xs[6] + W // 2, 296), (xs[6] + W // 2, Y + H + 2)], dashed=True)
P.append(f'<text class="s" x="{bx + 340}" y="288">a person decides today, with no policy help</text>')

# around the case
P.append(f'<text class="zt" x="{X0}" y="392">Around every case</text>')
around = [
    ("Data", ["SQLite on a persistent disk", "cases, audit trail, sign-ins"]),
    ("Traces", ["Honeycomb gets every step", "versions tagged, no patient data"]),
    ("Evals", ["made-up packets, known answers", "recall and precision per run"]),
    ("Dashboards", ["AI quality: Honeycomb", "Operations: /ops.html, live"]),
    ("Hosting", ["one service plus its disk", "keys held as secrets"]),
]
AW = 218
for i, (t, lines) in enumerate(around):
    box(X0 + i * (AW + 16), 408, AW, 78, t, lines, "plat")
P.append(f'<text class="s" x="{X0 + 5 * (AW + 16) - 6}" y="506" text-anchor="end">Every step above reports a trace. The nurse and director screens run on the same data.</text>')

SVG_W, SVG_H = 1280, 524 + OFF
defs = ('<defs><marker id="ah" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
        '<path d="M2 1L8 5L2 9" fill="none" stroke="context-stroke" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></marker></defs>')
SVG = f'<svg viewBox="0 0 {SVG_W} {SVG_H}" role="img" aria-label="The path of one case through PA Desk">{defs}{"".join(P_lane)}<g transform="translate(0,{OFF})">{"".join(P)}</g></svg>'

cards = [
    ("1 - What Unstructured does (the partitioner)",
     ["It turns a PDF into pieces a program can use. Each piece is a labeled element: a title, a paragraph, a table, a form, a header or a footer. Each one keeps its page number and where it sits on the page.",
      "Unstructured's own partitioner has four methods. <b>Auto</b> picks per page. <b>Fast</b> reads clean typed text with plain rules and no model. <b>High Res</b> looks at the page layout and runs OCR, so it handles scans and tables. <b>VLM</b> sends the page image to a vision-language model, the slowest and most accurate, best for handwriting and messy pages. Auto sends text-only pages to Fast and complex pages to High Res or VLM.",
      "<b>That is why I label this step ETL plus AI.</b> Fast is plain rules, but the other methods read the page image with OCR, and VLM uses a vision-language model. <b>Our app calls their Transform service, and it hides that choice.</b> It only has two settings, balanced (the default, which we use) and best. Their docs do not say which method it picks, so I do not claim one. I can say what it returned: labeled elements with coordinates, and readable text from a scanned packet. In my separate search experiment I did choose VLM myself."]),
    ("2 - What OCR does",
     ["OCR means optical character recognition. A scanned page is only a picture. OCR finds the lines of text in the picture and works out which letter each shape is, so the page becomes text again.",
      "It makes small mistakes: an O for a zero, an l for a one, a smudged word. That is why the next steps never trust the text blindly. They match quotes with a similarity score and refuse a match if a number is different."]),
    ("3 - What the reader (the main AI model) does",
     ["It does not search. It <b>reads</b>. The whole packet, seven to fourteen pages, goes into one request with page markers, the member's name and date of birth, the planned procedure date, and, for each fact, the policy rule that fact feeds.",
      "It must answer through a fixed form (a forced tool call), so the reply is structured data, not free text. For every fact it gives a status (found, none, missing, implied, ambiguous), the value, and every sentence in the packet that states it, copied word for word, with dates.",
      "It reads three times in parallel. If the three reads disagree on a status or a value, the fact becomes 'not sure' and goes to the nurse. It returns dates, and plain code does the counting, because models count days badly."]),
    ("4 - How the fuzzy match works",
     ["After the reader gives a quote, code looks for it in the real page text. First it tries an exact match, ignoring case and extra spaces. If that fails, it uses fuzzy matching.",
      "Fuzzy matching is <b>letter-level similarity, not meaning</b>. It slides the quote along the page and, for the best-fitting stretch, counts how many single-letter edits (add, delete, change) turn one into the other. Few edits give a score near 100. We accept 88 or more.",
      "One rule overrides the score: the numbers in the quote must be the same as the numbers in the matched text. 'LVEF 28%' never matches 'LVEF 38%', even at 95% similar. The screen then highlights the real text from the page, not the model's version."]),
    ("5 - What the second AI check does",
     ["A smaller, cheaper model gets the claim ('the ejection fraction is 28') plus the sentence and the text around it. It answers one of four words: <b>supports</b>, <b>contradicts</b>, <b>unrelated</b> or <b>insufficient</b>.",
      "It catches what text matching cannot: 'no evidence of instability' quoted as if instability was found. Contradicts or unrelated turns the fact into 'not sure'. Insufficient keeps the fact but removes the green tick."]),
    ("6 - What the rules engine does, and where RAG appears",
     ["The rules are plain code. Each policy criterion names a fact and a test, such as 'LVEF is 35% or less'. The engine checks the facts, builds the checklist, and picks approve, pend, escalate or verify. The same facts give the same answer every time, and there is no 'deny' in its vocabulary.",
      "<b>The decision path uses no RAG.</b> The packet is read whole and the policies are a curated, versioned library, each criterion tied to its source. Nothing is searched while a case runs. The policy library is built before any case: Unstructured parses the official policy, an AI drafts the rules, code checks them, and a policy owner approves them. The library in use today was written once by hand. The build now drafts rules from the official text, tested on five policies, and the owner approval is missing. The planned side branch for a service with no policy would search the 1,314 CMS policies and draft one for the owner to approve. In my test, embedding search found the right policy more often than keyword search (97.7% against 79.5%). It is measured and not connected."]),
]
card_html = "".join(f'<section class="card"><h3>{e(t)}</h3>' + "".join(f"<p>{p}</p>" for p in ps) + "</section>" for t, ps in cards)

NOTCLAIM = [
    "The policy library in use was written by Claude from the official text, with your review. The build pipeline drafts the same kind of rules and was tested on five policies. No policy owner has approved any of it yet.",
    "The search over 1,314 CMS policies is not connected to the app. A code we do not cover goes to a person.",
    "The policies are public Medicare policies. The Humana policy and MCG slots are placeholders, marked illustrative.",
    "All packets are made up. Nothing here has seen a real patient.",
    "We do not know which Unstructured method the Transform service uses on a page. We know what it returned.",
    "The AI never denies and never decides. A person does.",
    "The test scores are on small, mostly self-chosen sets. They show direction, not real-world accuracy.",
]

PAGE = f"""<meta charset="utf-8"><title>PA Desk Walkthrough</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&display=swap">
<style>
:root{{--bg:#f3f6f4;--panel:#fff;--ink:#14201c;--ink2:#51605b;--line:#cfd9d4;
--code:#1f6f5c;--codesoft:#e1efe9;--ai:#5f3aa8;--aisoft:#ebe2f8;--ext:#4a5a64;--extsoft:#e8edf0;--human:#8a5a00;--humansoft:#fcefd0;--plat:#2b5d86;--platsoft:#e3eef7}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{color-scheme:dark;--bg:#0e1614;--panel:#16211e;--ink:#e6efeb;--ink2:#a6b8b1;--line:#2b3a36;--code:#4cc0a0;--codesoft:#12302a;--ai:#b79cf0;--aisoft:#2a2046;--ext:#a7b6bf;--extsoft:#1f2a30;--human:#f0b04a;--humansoft:#35260c;--plat:#7fb6e6;--platsoft:#14283a}}}}
:root[data-theme="dark"]{{color-scheme:dark;--bg:#0e1614;--panel:#16211e;--ink:#e6efeb;--ink2:#a6b8b1;--line:#2b3a36;--code:#4cc0a0;--codesoft:#12302a;--ai:#b79cf0;--aisoft:#2a2046;--ext:#a7b6bf;--extsoft:#1f2a30;--human:#f0b04a;--humansoft:#35260c;--plat:#7fb6e6;--platsoft:#14283a}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 "IBM Plex Sans",system-ui,sans-serif;padding-inline:16px;padding-block:24px 70px}}
main{{max-width:1180px;margin:0 auto}}
h1{{font-size:26px;margin:0 0 4px;font-weight:600;text-wrap:balance}}
.lead{{color:var(--ink2);max-width:760px;margin:0 0 14px}}
.legend{{display:flex;gap:16px;flex-wrap:wrap;margin:0 0 14px;font-size:13px}}
.legend span{{display:inline-flex;align-items:center;gap:6px}}
.legend i{{width:14px;height:14px;border-radius:4px;border:2px solid;display:inline-block}}
.dg{{overflow-x:auto;background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px 10px}}
svg{{display:block;min-width:1040px;width:100%;height:auto;font-family:"IBM Plex Sans",system-ui,sans-serif}}
.b{{stroke-width:2;fill:var(--panel)}}
.b.code{{stroke:var(--code);fill:var(--codesoft)}}.b.ai{{stroke:var(--ai);fill:var(--aisoft)}}.b.ext{{stroke:var(--ext);fill:var(--extsoft)}}.b.human{{stroke:var(--human);fill:var(--humansoft)}}.b.plat{{stroke:var(--plat);fill:var(--platsoft)}}
.b.dsh{{stroke-dasharray:6 4}}
.t{{font-size:14px;font-weight:600;fill:var(--ink)}}.s{{font-size:12px;fill:var(--ink2)}}
.tg{{font-size:10px;font-weight:600;letter-spacing:.08em}}
.tg.code{{fill:var(--code)}}.tg.ai{{fill:var(--ai)}}.tg.ext{{fill:var(--ext)}}.tg.human{{fill:var(--human)}}
.zt{{font-size:12px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;fill:var(--ink2)}}
.a{{fill:none;stroke:var(--ink2);stroke-width:1.8}}.a.dsh{{stroke-dasharray:5 4}}
.bd{{fill:var(--ink)}}.bt{{font-size:12px;font-weight:600;fill:var(--bg);text-anchor:middle}}
h2{{font-size:13px;letter-spacing:.08em;text-transform:uppercase;color:var(--ink2);margin:30px 0 12px;font-weight:600}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:14px}}
.card{{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px 18px}}
.card h3{{font-size:15px;margin:0 0 8px}}.card p{{margin:0 0 10px}}.card p:last-child{{margin-bottom:0}}
.not{{background:var(--humansoft);border-radius:10px;padding:12px 18px}}.not ul{{margin:6px 0 0;padding-left:20px}}.not li{{margin:4px 0}}
</style>
<main>
<h1>How one case flows through PA Desk</h1>
<p class="lead">Seven steps from a faxed packet to a human decision, with what is plain code and what is an AI model. Below the diagram, each step in plain words you can say out loud.</p>
<div class="legend">
<span><i style="border-color:var(--code);background:var(--codesoft)"></i>Plain code</span>
<span><i style="border-color:var(--ai);background:var(--aisoft)"></i>AI model</span>
<span><i style="border-color:var(--ext);background:var(--extsoft)"></i>Service outside our app</span>
<span><i style="border-color:var(--human);background:var(--humansoft)"></i>A person</span>
<span><i style="border-color:var(--plat);background:var(--platsoft)"></i>Platform around the case</span>
</div>
<div class="dg">{SVG}</div>
<h2>Say it out loud</h2>
<div class="cards">{card_html}</div>
<h2>Do not claim</h2>
<div class="not"><b>Say these before you are asked.</b><ul>{"".join(f"<li>{e(x)}</li>" for x in NOTCLAIM)}</ul></div>
</main>
"""
with open(OUT, "w", encoding="utf-8", newline="\n") as f:
    f.write(PAGE)
print("wrote", OUT)
