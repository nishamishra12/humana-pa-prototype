"use strict";
const S = { user: null, view: "attention", caseId: null, tab: "review", cases: [], counts: {}, detail: null, users: [], q: "", cites: [], highlight: null, pop: null, notifs: [], evals: null };
const $app = document.getElementById("app");

const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const initials = (n) => n.replace("Dr. ", "").split(" ").map((x) => x[0]).join("").slice(0, 2);

async function api(path, opts = {}) {
  const o = { headers: {}, credentials: "same-origin", ...opts };
  if (o.body && !(o.body instanceof FormData)) { o.headers["Content-Type"] = "application/json"; o.body = JSON.stringify(o.body); }
  const r = await fetch("/api" + path, o);
  if (r.status === 401 && !path.startsWith("/login")) { S.user = null; renderLogin(); throw new Error("signed out"); }
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(j.detail || "Something went wrong");
  return j;
}
function toast(msg, err = false) {
  const t = document.getElementById("toast");
  t.textContent = msg; t.className = "show" + (err ? " err" : "");
  clearTimeout(toast._t); toast._t = setTimeout(() => (t.className = ""), 3200);
}
const guard = (fn) => async (...a) => { try { await fn(...a); } catch (e) { if (e.message !== "signed out") toast(e.message, true); } };

/* ---------- time ---------- */
function ago(iso) {
  const m = Math.round((Date.now() - new Date(iso)) / 60000);
  if (m < 60) return Math.max(m, 1) + "m ago";
  if (m < 1440) return Math.round(m / 60) + "h ago";
  return Math.round(m / 1440) + "d ago";
}
function clock(c) {
  if (c.decided_at) return { text: "Decided " + ago(c.decided_at), cls: "" };
  const ms = new Date(c.due_at) - Date.now(), h = ms / 3600000;
  const label = c.priority === "expedited" ? "72h clock" : "7d clock";
  if (ms < 0) return { text: label + " overdue", cls: "late" };
  const t = h >= 48 ? Math.floor(h / 24) + "d " + Math.floor(h % 24) + "h" : Math.floor(h) + "h " + Math.floor((h % 1) * 60) + "m";
  return { text: t + " left · " + label, cls: h < (c.priority === "expedited" ? 24 : 48) ? "soon" : "" };
}
const STATUS = { new: "New", in_review: "In review", pended: "Pended", escalated: "Escalated", approved: "Approved", denied: "Denied" };
const AI = { approve: ["Recommends approve", "ok", "✓"], pend: ["Missing info", "warn", "?"], escalate: ["Needs physician", "escalated", "↑"], no_policy: ["No curated policy", "bad", "!"] };
const ROLE_CHIP = { admin: ["Intake", "plain"], nurse: ["Nurse", "new"], medical_director: ["Medical director", "escalated"] };

/* ---------- login ---------- */
async function renderLogin() {
  const accts = await fetch("/api/demo-accounts").then((r) => r.json());
  $app.innerHTML = `<div class="login"><div class="login-card">
    <div class="brand"><span class="brand-mark">PA</span> PA Desk</div>
    <p class="muted" style="margin:10px 0 0;line-height:1.5">Prior authorization decision support. Every case is made-up data.</p>
    <form id="lf"><div class="field"><label for="em">Email</label><input id="em" type="email" autocomplete="username" required></div>
    <div class="field"><label for="pw">Password</label><input id="pw" type="password" autocomplete="current-password" required></div>
    <button class="btn primary" style="margin-top:16px;width:100%" type="submit">Sign in</button></form>
    <div class="demo-list"><div class="faint" style="font-size:12px">Demo accounts (password: demo1234)</div>
    ${accts.map((a) => `<button class="demo-btn" data-email="${esc(a.email)}"><span><b>${esc(a.name)}</b><br><span class="faint" style="font-size:12px">${esc(a.title)}</span></span><span class="chip ${ROLE_CHIP[a.role][1]}">${ROLE_CHIP[a.role][0]}</span></button>`).join("")}</div>
  </div></div>`;
  const doLogin = guard(async (email, password) => { S.user = await api("/login", { method: "POST", body: { email, password } }); S.view = S.user.role === "medical_director" ? "mine" : S.user.role === "admin" ? "unassigned" : "attention"; S.caseId = null; await boot(); });
  document.getElementById("lf").onsubmit = (e) => { e.preventDefault(); doLogin(document.getElementById("em").value, document.getElementById("pw").value); };
  document.querySelectorAll(".demo-btn").forEach((b) => (b.onclick = () => doLogin(b.dataset.email, "demo1234")));
}

/* ---------- shell ---------- */
async function boot() {
  const [me, users] = await Promise.all([api("/me"), api("/users")]);
  S.user = me; S.users = users;
  parseHash();
  if (S.view === "evals") await runEvals();
  else await loadList();
  if (S.caseId) await loadCase(S.caseId);
  render();
}
function parseHash() {
  const h = location.hash.replace(/^#\/?/, "").split("/");
  if (h[0] === "case" && h[1]) { S.caseId = h[1]; S.view = S.view === "evals" ? "all" : S.view; }
  else if (h[0] === "view" && h[1]) { S.view = h[1]; S.caseId = null; }
}
window.addEventListener("hashchange", guard(async () => { parseHash(); if (S.view !== "evals") { await loadList(); if (S.caseId) await loadCase(S.caseId); } else if (!S.evals) await runEvals(); render(); }));

async function loadList() {
  if (S.view === "evals") return;
  const d = await api(`/cases?view=${S.view}&q=${encodeURIComponent(S.q)}`);
  S.cases = d.cases; S.counts = d.counts;
}
async function loadCase(id) { S.detail = await api("/cases/" + id); }
async function runEvals() {
  S.evals = await api("/evals");
  render();
  S.holdout = await api("/evals/holdout");
}

function render() {
  if (!S.user) return renderLogin();
  const isMD = S.user.role === "medical_director";
  const isAdmin = S.user.role === "admin";
  const views = isAdmin
    ? [["unassigned", "Needs assignment"], ["pended", "Pended, waiting on provider"], ["escalated", "Escalated to physician"], ["done", "Decided"], ["all", "Everything"]]
    : [["attention", "Needs my review"], ["at_risk", "At risk"], ["mine", "All mine"], ["pended", "Pended, waiting on provider"], ["escalated", "Escalated to physician"], ["done", "Decided"], ["all", "Everything"]];
  $app.innerHTML = `<div class="shell">
    <header class="topbar">
      <div class="brand"><span class="brand-mark">PA</span> PA Desk</div>
      <input class="search" id="q" type="search" placeholder="Search member, case, procedure" value="${esc(S.q)}" aria-label="Search cases">
      <div class="spacer"></div>
      <label class="btn small" style="cursor:pointer">Upload packet<input type="file" id="up" accept="application/pdf" class="sr"></label>
      <div class="bell" style="position:relative"><button class="btn ghost small" id="bell" aria-label="Notifications">🔔</button>${S.user.unread ? `<span class="badge-dot">${S.user.unread}</span>` : ""}${S.pop === "notif" ? notifPop() : ""}</div>
      <div class="userchip"><span class="avatar ${isMD ? "md" : isAdmin ? "admin" : ""}">${esc(initials(S.user.name))}</span><div style="line-height:1.2"><b>${esc(S.user.name)}</b><br><span class="faint" style="font-size:12px">${esc(S.user.title)}</span></div><button class="btn ghost small" id="out">Sign out</button></div>
    </header>
    <div class="main">
      <nav class="nav" aria-label="Queues"><h4>Queues</h4>
        ${views.map(([v, l]) => `<button class="nav-item ${S.view === v ? "on" : ""}" data-view="${v}"><span>${l}</span><span class="count">${S.counts[v] ?? ""}</span></button>`).join("")}
        <h4>Quality</h4><button class="nav-item ${S.view === "evals" ? "on" : ""}" data-view="evals"><span>Evals</span></button></nav>
      ${S.view === "evals" ? `<div style="grid-column: 2 / 4; overflow:auto">${evalsHtml()}</div>` : `<section class="list">${listHtml()}</section><section class="detail">${S.caseId && S.detail ? detailHtml() : `<div class="empty">Select a case to review.</div>`}</section>`}
    </div></div>`;
  bind();
}

function listHtml() {
  const title = { attention: "Needs my review", at_risk: "At risk", mine: "All mine", unassigned: "Needs assignment", pended: "Pended", escalated: "Escalated", done: "Decided", all: "Everything" }[S.view];
  return `<div class="list-head"><h3>${title}</h3><div class="faint" style="font-size:12.5px;margin-top:2px">${S.cases.length} case${S.cases.length === 1 ? "" : "s"}</div></div>` +
    (S.cases.length ? S.cases.map((c) => {
      const k = clock(c), ai = AI[c.ai_action];
      return `<button class="row ${S.caseId === c.id ? "on" : ""}" data-case="${c.id}">
        <div class="row-top"><span class="row-name">${esc(c.member_name)}</span><span class="clock ${k.cls}">${esc(k.text)}</span></div>
        <div class="row-sub">${esc(c.id)} · CPT ${esc(c.cpt || "-")} · ${esc(c.procedure.replace("Elective inpatient admission, ", ""))}</div>
        <div class="row-meta"><span class="chip ${c.status}">${STATUS[c.status]}</span>
          ${["approved", "denied"].includes(c.status) ? "" : `<span class="chip ${ai[1]}">${ai[2]} ${ai[0]}${c.ai_action === "pend" ? " (" + c.ai_missing + ")" : ""}</span>`}
          ${c.sla === "breached" ? `<span class="chip bad">Breached clock</span>` : c.sla === "soon" ? `<span class="chip warn">Due soon</span>` : ""}
          ${c.priority === "expedited" ? `<span class="chip bad">Expedited</span>` : ""}
          <span class="faint" style="font-size:12px">${c.assignee ? esc(c.assignee.name) : "Unassigned"}</span></div></button>`;
    }).join("") : `<div class="empty">Nothing here.</div>`);
}

/* ---------- detail ---------- */
function citeBtn(page, quote) {
  if (!page) return "";
  S.cites.push({ page, quote });
  return `<button class="cite" data-cite="${S.cites.length - 1}" title="Open page ${page} in the packet">p.${page}</button>`;
}
const FACTS = [
  ["expected_los_days", "Expected stay", (f) => (f.status === "found" ? `${f.value} midnight${f.value === 1 ? "" : "s"}` : null)],
  ["comorbidities", "Comorbidities", (f) => (f.status === "found" ? f.value.join(", ") : f.status === "none" ? "None documented as present" : null)],
  ["post_op_needs", "Post-op care needs", (f) => (f.status === "found" ? f.quote : f.status === "none" ? "Routine recovery only" : null)],
  ["indication_evidence", "Surgical indication", (f) => (f.status === "found" ? `Imaging shows ${f.value}` : null)],
  ["conservative_treatment", "Conservative care", (f) => (f.status === "found" ? f.quote : null)],
  ["shared_decision_making", "Shared decision making", (f) => (f.status === "found" ? "Documented" : null)],
];
const FSTATUS = { found: "Stated", implied: "Implied only", none: "Stated: none", missing: "Not in packet" };

function detailHtml() {
  S.cites = [];
  const d = S.detail, k = clock(d), a = d.analysis, ai = AI[a.action];
  const done = ["approved", "denied"].includes(d.status);
  return `<div class="detail-head">
    <div class="dh-top"><div><div class="faint mono">${esc(d.id)}</div><h2 class="dh-name">${esc(d.member_name)} <span class="faint" style="font-weight:500;font-size:14px">${d.age ? d.age + "y · " : ""}${esc(d.member_id)}</span></h2>
      <div class="dh-meta"><span>${esc(d.procedure.replace("Elective inpatient admission, ", "Inpatient admission, "))}</span><span>CPT ${esc(d.cpt || "-")}</span><span>${esc(d.facility)}</span></div>
      <div class="faint" style="font-size:11.5px;margin-top:4px">Ingested via ${esc(d.engine)} · extracted via ${d.extractor === "llm" ? "Claude (3-vote consistency check)" : "rule-based"}</div></div>
      <div style="display:grid;gap:6px;justify-items:end"><span class="chip ${d.status}">${STATUS[d.status]}</span><span class="clock ${k.cls}">${esc(k.text)}</span>
        <label class="faint" style="font-size:12px">Assigned <select id="assign" style="width:auto;padding:3px 6px;margin-left:4px">${["", ...S.users.filter((u) => u.role === "nurse").map((u) => u.id)].map((id) => { const u = S.users.find((x) => x.id === id); return `<option value="${id}" ${d.assignee_id === id ? "selected" : ""}>${u ? esc(u.name) : "Unassigned"}</option>`; }).join("")}</select></label></div></div>
    <div class="tabs" role="tablist">${[["review", "Review"], ["packet", `Packet (${new Set(d.elements.map((e) => e.page)).size} pages)`], ["activity", `Activity (${d.comments.length})`]].map(([t, l]) => `<button class="tab ${S.tab === t ? "on" : ""}" role="tab" data-tab="${t}">${l}</button>`).join("")}</div></div>
  <div class="body">${S.tab === "review" ? reviewHtml(d, a, ai, done) : S.tab === "packet" ? packetHtml(d) : activityHtml(d)}</div>`;
}

function reviewHtml(d, a, ai, done) {
  const isMD = S.user.role === "medical_director";
  const isAdmin = S.user.role === "admin";
  const adminNote = `<div class="card"><h3>Intake</h3><p class="muted" style="line-height:1.6">Intake routes cases, it doesn't make clinical calls. Use the <b>Assigned</b> dropdown above to send this to a nurse${!d.assignee ? " — it isn't assigned yet" : ""}.</p></div>`;
  if (a.action === "no_policy") {
    return `<div class="banner" style="background:var(--bad-soft);color:var(--bad)"><b>No curated policy covers this procedure.</b> ${esc(a.rationale)}</div>
      <div class="card"><h3>What happens next</h3><p class="muted" style="line-height:1.6">This isn't a clinical judgment call -- it's a gap in the curated policy table, which today only covers lumbar spinal fusion (CPT ${esc((a.covered_cpt_codes || []).join(", "))}). A reviewer needs to find the real policy for this procedure before anything can be checked. The retrieval fallback (<span class="mono">pipeline/policy_retrieval.py</span>) can search the full downloaded CMS corpus and draft a candidate checklist from it, but that draft is never trusted automatically -- it still needs a person to confirm it's the right policy.</p></div>
      ${done ? "" : isAdmin ? adminNote : actionsHtml(d, a, isMD)}`;
  }
  const groups = {};
  a.checklist.forEach((c) => (groups[c.policy_id] ||= { c, items: [] }).items.push(c));
  const pol = Object.fromEntries(a.policies.map((p) => [p.id, p]));
  const mk = { met: "✓", missing: "?", advisory: "!", not_met: "✕", info: "i" };
  const stLabel = { met: "Met", missing: "Missing", advisory: "Advisory", not_met: "Not met", info: "Info" };
  return `
  ${d.sla === "breached" ? `<div class="banner">This case has passed its ${d.priority === "expedited" ? "72-hour expedited" : "7-day standard"} CMS decision clock. The clock is a guardrail, not a target: it should never be breached, so this needs attention now.</div>` : ""}
  <div class="reco ${a.action}"><div class="icon">${ai[2]}</div><div><h3>${a.action === "approve" ? "Recommendation: approve" : a.action === "pend" ? "Recommendation: pend and ask one specific question" : "Recommendation: escalate to a medical director"}</h3>
    <p>${esc(a.rationale)}</p><div class="note">The system can recommend approve, pend or escalate. It cannot deny. Only a medical director can.</div></div></div>

  <div class="card"><h3>What the packet says</h3><div class="facts">
    ${FACTS.map(([key, label, fmt]) => { const f = d.facts[key] || { status: "missing" }; const v = fmt(f);
      return `<div class="fact-label">${label}</div><div><span class="status-dot dot-${f.status}"></span>${v ? esc(v) : `<span class="muted">${FSTATUS[f.status]}</span>`}${f.status === "implied" ? `<div class="quote">“${esc(f.quote)}” — ${esc(f.note || "")}</div>` : ""}</div><div>${citeBtn(f.page, f.quote)}</div>`; }).join("")}
  </div></div>

  <div class="card"><h3>Criteria checked, in order of authority</h3>
    ${Object.values(groups).map(({ c, items }) => { const p = pol[c.policy_id]; return `<div class="group"><div class="group-head"><b>${esc(c.layer)}: ${esc(c.policy_title)}</b>
      <span>${p && p.verified ? `<span class="chip ok">Verified source</span>` : `<span class="chip plain">Illustrative</span>`} ${p && p.url ? `<a href="${esc(p.url)}" target="_blank" rel="noopener">Open policy</a>` : ""}</span></div>
      ${items.map((i) => `<div class="crit"><span class="mk ${i.status}" title="${stLabel[i.status]}">${mk[i.status]}</span><div><div class="crit-text">${esc(i.text)}</div><div class="crit-cite">${esc(i.cite)}${i.note ? " · " + esc(i.note) : ""}</div>${i.evidence ? `<div class="quote">“${esc(i.evidence.quote)}”</div>` : ""}</div><div>${i.evidence ? citeBtn(i.evidence.page, i.evidence.quote) : `<span class="chip ${i.status === "not_met" ? "bad" : i.status === "info" ? "plain" : "warn"}">${stLabel[i.status]}</span>`}</div></div>`).join("")}</div>`; }).join("")}
    <div class="note">MCG and InterQual are licensed content and are not included. That is where a licensed feed would plug in.</div></div>

  ${done ? `<div class="card"><h3>Decision recorded</h3><div class="muted">This case is ${STATUS[d.status].toLowerCase()}. See the Activity tab for who decided and why.</div></div>` : isAdmin ? adminNote : actionsHtml(d, a, isMD)}`;
}

const SAMPLE_REPLY = {
  expected_los_days: "Surgeon addendum: Expected length of stay: 3 midnights.",
  indication_evidence: "Flexion-extension radiographs show dynamic instability at the operative level.",
  conservative_treatment: "Failed 8 months of conservative care: physical therapy, NSAIDs and epidural injections.",
  comorbidities: "Past medical history: heart failure, type 2 diabetes.",
  post_op_needs: "Post-operative plan: telemetry monitoring and cardiology co-management.",
};
function actionsHtml(d, a, isMD) {
  const qs = a.gate.questions.map((q) => q.question);
  const drafted = qs.length > 1 ? qs.map((q, i) => `${i + 1}. ${q}`).join("\n") : qs[0] || "";
  const reply = a.gate.questions.map((q) => SAMPLE_REPLY[q.fact]).filter(Boolean).join(" ");
  const mds = S.users.filter((u) => u.role === "medical_director");
  const open = S.act;
  const pended = d.status === "pended";
  return `<div class="card actions"><h3>${isMD ? "Medical director decision" : "Your action"}</h3>
    <div class="action-row">
      <button class="btn ${a.action === "approve" ? "primary" : ""}" data-act="approve">${a.action === "approve" ? "Approve" : "Approve (override)"}</button>
      ${isMD ? `<button class="btn danger" data-act="deny">Deny…</button><button class="btn" data-act="return">Return to nurse…</button>`
             : `<button class="btn ${a.action === "pend" ? "primary" : ""}" data-act="pend">Pend with question…</button><button class="btn ${a.action === "escalate" ? "primary" : ""}" data-act="escalate">Escalate to medical director…</button>`}
    </div>
    ${open === "approve" && a.action !== "approve" ? `<div class="form"><label>The system did not recommend approval. Your reason:</label><textarea id="note"></textarea><div class="action-row"><button class="btn primary" data-go="approve">Confirm approval</button></div></div>` : ""}
    ${open === "pend" ? `<div class="form"><label>Question to the provider (one specific ask)</label><textarea id="question">${esc(drafted)}</textarea><div class="action-row"><button class="btn primary" data-go="pend">Send to provider and pend</button></div></div>` : ""}
    ${open === "escalate" ? `<div class="form"><label>Tag a medical director</label><select id="mdsel">${mds.map((m) => `<option value="${m.id}">${esc(m.name)}</option>`).join("")}</select><label>What you need decided</label><textarea id="note">${esc(a.action === "escalate" ? a.rationale : "")}</textarea><div class="action-row"><button class="btn primary" data-go="escalate">Escalate and tag</button></div></div>` : ""}
    ${open === "deny" ? `<div class="form"><label>Clinical rationale (required for a denial)</label><textarea id="note"></textarea><div class="action-row"><button class="btn danger" data-go="deny">Confirm denial</button></div></div>` : ""}
    ${open === "return" ? `<div class="form"><label>Note back to the nurse</label><textarea id="note"></textarea><div class="action-row"><button class="btn primary" data-go="return">Return to nurse</button></div></div>` : ""}
    ${pended ? `<div class="form"><label>Demo: simulate the provider's reply (adds a page to the packet and re-runs the analysis)</label><textarea id="reply">${esc(reply || "Provider reply: additional documentation attached.")}</textarea><div class="action-row"><button class="btn" data-go="reply">Simulate provider reply</button></div></div>` : ""}
  </div>`;
}

function packetHtml(d) {
  const byPage = {};
  d.elements.forEach((e) => (byPage[e.page] ||= []).push(e));
  const hl = S.highlight;
  return Object.keys(byPage).map((p) => `<div class="page-block ${hl && hl.page == p ? "flash" : ""}" id="pg${p}"><div class="page-tag">Page ${p} of ${Object.keys(byPage).length}</div><div class="page-body">${byPage[p].map((e) => {
    let t = esc(e.text);
    if (hl && hl.page == p && hl.quote) { const q = esc(hl.quote.trim()); t = t.split(q).join(`<mark>${q}</mark>`); }
    return e.type === "Title" ? `<div class="h">${t}</div>` : `<div>${t}</div>`; }).join("")}</div></div>`).join("");
}

function activityHtml(d) {
  const items = [
    ...d.comments.map((c) => ({ t: c.created_at, kind: "c", c })),
    ...d.audit.filter((a) => !["commented", "escalated", "pended", "provider_reply"].includes(a.action)).map((a) => ({ t: a.created_at, kind: "a", a })),
  ].sort((x, y) => x.t.localeCompare(y.t));
  const label = { comment: "", escalation: "Escalation", provider_request: "Question to provider", provider_reply: "Provider reply" };
  const body = (s) => esc(s).replace(/@(\w+)/g, '<span class="mention">@$1</span>').replace(/\n/g, "<br>");
  return `<div class="card" style="display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap">
    <div><h3>Case record</h3><div class="faint" style="font-size:12.5px;margin-top:2px">The facts, the criteria checklist, the decision, and this full audit trail, as one file.</div></div>
    <a class="btn small" href="/api/cases/${d.id}/export" download="${d.id}_record.json">Export case record</a></div>
  <div class="card"><div class="tl">${items.map((i) => i.kind === "c" ? `<div class="tl-item"><span class="avatar ${i.c.user && i.c.user.role === "medical_director" ? "md" : ""}">${i.c.user ? esc(initials(i.c.user.name)) : "PR"}</span>
      <div class="tl-body"><span class="tl-who">${i.c.user ? esc(i.c.user.name) : "Provider office"}</span><span class="tl-time">${ago(i.c.created_at)}</span>${label[i.c.kind] ? ` <span class="chip plain">${label[i.c.kind]}</span>` : ""}<div class="bubble ${i.c.kind}">${body(i.c.body)}</div></div></div>`
    : `<div class="tl-item"><span class="sys-dot"></span><div class="tl-body muted"><b>${esc(i.a.user ? i.a.user.name : "System")}</b> · ${esc(i.a.action.replace("_", " "))}<span class="tl-time">${ago(i.a.created_at)}</span><div class="faint" style="font-size:13px">${esc(i.a.detail)}</div></div></div>`).join("")}</div></div>
  <div class="card"><h3>Add a comment</h3><textarea id="cbody" placeholder="Write a note. Use @patel or @brooks to tag a medical director."></textarea>
    <div class="action-row" style="margin-top:8px"><button class="btn primary" data-go="comment">Post</button>${S.users.filter((u) => u.id !== S.user.id).map((u) => `<button class="btn small" data-tag="${u.handle}">@${u.handle}</button>`).join("")}</div></div>`;
}

/* ---------- evals ---------- */
function evalsHtml() {
  const e = S.evals;
  if (!e) return `<div class="evals"><div class="empty">Loading evals…</div></div>`;
  return `<div class="evals">
    <div><h2>Evals</h2><p class="muted" style="margin:6px 0 0;line-height:1.5">Two separate sets. The first proves the pipeline runs end to end. The second tries to break it.</p></div>

    <div><h3 style="margin-bottom:4px">M1-M5 sanity set</h3><p class="faint" style="font-size:12.5px;margin:0 0 10px">6 packets. Written alongside the extractor, so a pass proves plumbing, not accuracy.</p></div>
    <div class="stat"><div><b>${e.passed} / ${e.total}</b><span>packets match the expected outcome</span></div><div><b>${e.zero_denials ? "0" : "!"}</b><span>denials produced by the system (must be zero)</span></div></div>
    <div class="banner"><b>Read this before quoting the result.</b> ${esc(e.caveat)}</div>
    <div class="card" style="padding:0;overflow:auto"><table><thead><tr><th>Packet</th><th>Expected</th><th>Actual</th><th>Missing item(s)</th><th></th></tr></thead><tbody>
      ${e.results.map((r) => `<tr><td><b>${esc(r.label)}</b><div class="faint mono">${esc(r.file)}</div></td><td>${esc(r.expected_action)}</td><td>${esc(r.actual_action)}</td><td>${r.actual_missing.length ? esc(r.actual_missing.join(", ")) : "<span class='faint'>none</span>"}</td><td><span class="chip ${r.passed ? "ok" : "bad"}">${r.passed ? "Pass" : "Fail"}</span></td></tr>`).join("")}</tbody></table></div>

    ${holdoutHtml()}
    <div><button class="btn" id="rerun">Run both again</button></div></div>`;
}

function holdoutHtml() {
  const h = S.holdout;
  const head = `<div style="margin-top:8px"><h3 style="margin-bottom:4px">M6 held-out set</h3><p class="faint" style="font-size:12.5px;margin:0 0 10px">4 adversarial packets, written without looking at extract.py. Each targets one specific real-world failure mode. One needs the live OCR API and has no text layer at all.</p></div>`;
  if (!h) return head + `<div class="card"><div class="empty">Running the held-out set — the OCR packet calls the live API, so this takes longer…</div></div>`;
  const outcomeLabel = { correct: "Correct", false_negative: "Missed it", false_negative_implied: "Flagged uncertain, not found", false_positive_hallucination: "Hallucinated", wrong_value: "Found, but wrong value" };
  return head + `
    <div class="stat">
      <div><b>${h.action_matches} / ${h.packets_total}</b><span>final recommendation matched expectation</span></div>
      <div><b>${h.completeness_recall.pct}%</b><span>completeness recall — found it when it was really there (${h.completeness_recall.correct}/${h.completeness_recall.total})</span></div>
      <div><b>${h.hallucination_rate.pct}%</b><span>hallucination rate — claimed found when absent or negated (${h.hallucination_rate.hallucinated}/${h.hallucination_rate.total})</span></div>
    </div>
    <div class="banner"><b>Read this before quoting the result.</b> ${esc(h.caveat)}</div>
    ${h.hallucination_detail.filter((x) => x.critical).map((x) => `<div class="banner" style="background:var(--bad-soft);color:var(--bad)"><b>Critical finding — ${esc(x.member)}, ${esc(x.fact)}.</b> ${esc(x.critical)}</div>`).join("")}
    <div style="display:grid;gap:10px">
      ${h.results.map((r) => `<div class="card">
        <div style="display:flex;justify-content:space-between;gap:10px;align-items:baseline;flex-wrap:wrap">
          <div><b>${esc(r.member)}</b> — ${esc(r.label)}<div class="faint mono" style="font-size:11.5px">${esc(r.file)} · ingested via ${esc(r.engine)}</div></div>
          <div style="display:flex;gap:6px;align-items:center"><span class="faint" style="font-size:12.5px">expected ${esc(r.expected_action)}, got ${esc(r.actual_action)}</span><span class="chip ${r.action_matches ? "ok" : "bad"}">${r.action_matches ? "Pass" : "Fail"}</span></div>
        </div>
        <p class="faint" style="font-size:12.5px;margin:6px 0 0">${esc(r.note)}</p>
        ${r.facts.filter((f) => f.outcome !== "correct").length ? `<table style="margin-top:10px"><thead><tr><th>Fact</th><th>Truth</th><th>Extractor said</th><th>Outcome</th></tr></thead><tbody>
          ${r.facts.filter((f) => f.outcome !== "correct").map((f) => `<tr><td>${esc(f.fact)}</td><td>${esc(f.truth)}${f.expected_value != null ? " (" + esc(f.expected_value) + ")" : ""}</td><td>${esc(f.extractor_status)}${f.extracted_value != null ? ": " + esc(String(f.extracted_value)) : ""}</td><td><span class="chip ${f.outcome === "correct" ? "ok" : f.outcome === "false_positive_hallucination" || f.outcome === "wrong_value" ? "bad" : "warn"}">${outcomeLabel[f.outcome]}</span></td></tr>
          <tr><td colspan="4" class="faint" style="font-size:12.5px;padding-top:0">${esc(f.why)}</td></tr>`).join("")}</tbody></table>` : `<div class="faint" style="font-size:12.5px;margin-top:8px">Every fact in this packet was read correctly.</div>`}
      </div>`).join("")}
    </div>`;
}

function notifPop() {
  return `<div class="pop">${S.notifs.length ? S.notifs.map((n) => `<button class="pop-item ${n.read ? "" : "unread"}" data-case="${n.case_id}"><b>${esc(n.case_id)}</b> · ${esc(n.body)}<div class="faint" style="font-size:12px">${ago(n.created_at)}</div></button>`).join("") : `<div class="empty">No notifications.</div>`}</div>`;
}

/* ---------- events ---------- */
function bind() {
  const on = (sel, fn) => document.querySelectorAll(sel).forEach((el) => (el.onclick = guard((e) => fn(el, e))));
  on("[data-view]", async (el) => { S.view = el.dataset.view; S.caseId = null; S.detail = null; S.act = null; location.hash = "#/view/" + S.view; if (S.view === "evals") await runEvals(); else await loadList(); render(); });
  on("[data-case]", async (el) => { S.pop = null; S.caseId = el.dataset.case; S.tab = "review"; S.act = null; S.highlight = null; if (S.view === "evals") S.view = "all"; history.replaceState(null, "", "#/case/" + S.caseId); await loadList(); await loadCase(S.caseId); render(); });
  on("[data-tab]", (el) => { S.tab = el.dataset.tab; render(); });
  on("[data-cite]", (el) => { const c = S.cites[+el.dataset.cite]; S.highlight = c; S.tab = "packet"; render(); const pg = document.getElementById("pg" + c.page); if (pg) pg.scrollIntoView({ block: "center" }); });
  on("[data-act]", (el) => { S.act = S.act === el.dataset.act ? null : el.dataset.act; if (el.dataset.act === "approve" && S.detail.analysis.action === "approve") return submit("approve"); render(); });
  on("[data-go]", (el) => submit(el.dataset.go));
  on("[data-tag]", (el) => { const t = document.getElementById("cbody"); t.value += (t.value && !t.value.endsWith(" ") ? " " : "") + "@" + el.dataset.tag + " "; t.focus(); });
  const out = document.getElementById("out"); if (out) out.onclick = guard(async () => { await api("/logout", { method: "POST" }); S.user = null; S.detail = null; S.caseId = null; renderLogin(); });
  const q = document.getElementById("q"); if (q) q.oninput = guard(debounce(async () => { S.q = q.value; await loadList(); render(); const nq = document.getElementById("q"); nq.focus(); nq.setSelectionRange(nq.value.length, nq.value.length); }, 250));
  const up = document.getElementById("up"); if (up) up.onchange = guard(async () => { const file = up.files[0]; if (!file) return; const fd = new FormData(); fd.append("file", file); setBusy("Analyzing " + file.name + ". Reading the document, then checking it against policy. Takes 20 to 40 seconds. Keep this tab open."); let d; try { d = await api("/cases", { method: "POST", body: fd }); } finally { setBusy(null); } S.caseId = d.id; S.view = S.user.role === "admin" ? "unassigned" : "attention"; history.replaceState(null, "", "#/case/" + d.id); await loadList(); S.detail = d; toast(S.user.role === "admin" ? "Packet analyzed. Assign it to a nurse below." : "Packet analyzed: " + d.id); render(); });
  const asg = document.getElementById("assign"); if (asg) asg.onchange = guard(async () => { if (!+asg.value) return; S.detail = await api(`/cases/${S.caseId}/assign`, { method: "POST", body: { user_id: +asg.value } }); await loadList(); render(); });
  const bell = document.getElementById("bell"); if (bell) bell.onclick = guard(async () => { if (S.pop === "notif") { S.pop = null; return render(); } S.notifs = await api("/notifications"); S.pop = "notif"; render(); await api("/notifications/read", { method: "POST" }); S.user.unread = 0; });
  const rr = document.getElementById("rerun"); if (rr) rr.onclick = guard(async () => { await runEvals(); render(); toast("Evals re-run"); });
}

let _busyTimer = null;
function setBusy(msg) {
  const el = document.getElementById("busy");
  clearInterval(_busyTimer);
  if (!msg) { el.hidden = true; return; }
  const t0 = Date.now();
  const paint = () => { el.textContent = msg + " (" + Math.round((Date.now() - t0) / 1000) + "s)"; };
  el.hidden = false; paint(); _busyTimer = setInterval(paint, 1000);
}
function debounce(fn, ms) { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; }

const submit = guard(async (kind) => {
  const v = (id) => (document.getElementById(id) || {}).value || "";
  const id = S.caseId;
  let d;
  if (kind === "comment") d = await api(`/cases/${id}/comments`, { method: "POST", body: { body: v("cbody") } });
  else if (kind === "reply") d = await api(`/cases/${id}/addendum`, { method: "POST", body: { text: v("reply") } });
  else if (kind === "pend") d = await api(`/cases/${id}/action`, { method: "POST", body: { action: "pend", question: v("question") } });
  else if (kind === "escalate") d = await api(`/cases/${id}/action`, { method: "POST", body: { action: "escalate", md_id: +v("mdsel"), note: v("note") } });
  else d = await api(`/cases/${id}/action`, { method: "POST", body: { action: kind, note: v("note") } });
  S.detail = d; S.act = null;
  if (kind === "comment") S.tab = "activity";
  const msgs = { approve: "Approved", pend: "Question sent. Case pended", escalate: "Escalated and tagged", deny: "Denied with rationale recorded", return: "Returned to nurse", reply: "Provider reply added and case re-analyzed", comment: "Comment posted" };
  toast(msgs[kind]);
  await loadList(); S.user = await api("/me"); render();
});

(async () => { try { await boot(); } catch (e) { if (e.message === "signed out" || !S.user) renderLogin(); } })();
