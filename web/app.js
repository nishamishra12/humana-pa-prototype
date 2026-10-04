"use strict";
const S = {
  user: null, view: "attention", caseId: null, tab: "review", cases: [], counts: {}, detail: null, users: [], q: "",
  cites: [], highlight: null, pageNo: 1, activeKey: null, pop: null, notifs: [], evals: null, holdout: null,
  railOpen: false, team: [], teamOpen: null, fix: null, act: null, upload: null,
};
try { S.railOpen = localStorage.getItem("pa.rail") === "open" && window.innerWidth > 760; } catch (e) { /* storage can be blocked */ }
const $app = document.getElementById("app");

const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const initials = (n) => n.replace("Dr. ", "").split(" ").map((x) => x[0]).join("").slice(0, 2);

const ICONS = {
  menu: '<path d="M4 7h16"/><path d="M4 12h16"/><path d="M4 17h16"/>',
  search: '<circle cx="11" cy="11" r="6.5"/><path d="M16 16l4.5 4.5"/>',
  bell: '<path d="M6 17h12l-1.5-2v-4.2a4.5 4.5 0 0 0-9 0V15L6 17z"/><path d="M10 20h4"/>',
  down: '<path d="M6 9l6 6 6-6"/>', left: '<path d="M15 6l-6 6 6 6"/>', right: '<path d="M9 6l6 6-6 6"/>',
  inbox: '<path d="M4 13l2.5-7h11L20 13"/><path d="M4 13v5h16v-5h-5l-1 2h-4l-1-2H4z"/>',
  alert: '<path d="M12 4l9 16H3L12 4z"/><path d="M12 10v4"/><path d="M12 17.2v.1"/>',
  clock: '<circle cx="12" cy="12" r="8"/><path d="M12 8v4.5l3 1.5"/>',
  up: '<path d="M12 19V5"/><path d="M6 11l6-6 6 6"/>',
  checkc: '<circle cx="12" cy="12" r="8"/><path d="M8.5 12.5l2.5 2.5 4.5-5"/>',
  check: '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
  users: '<circle cx="9" cy="9" r="3"/><path d="M3.5 19c.6-3 2.8-4.5 5.5-4.5s4.9 1.5 5.5 4.5"/><circle cx="17" cy="10" r="2.3"/><path d="M16.5 14.6c2.3.1 3.7 1.4 4.2 3.9"/>',
  upload: '<path d="M12 16V5"/><path d="M7 9l5-5 5 5"/><path d="M5 19h14"/>',
  download: '<path d="M12 4v11"/><path d="M7 11l5 5 5-5"/><path d="M5 19h14"/>',
  x: '<path d="M6 6l12 12"/><path d="M18 6L6 18"/>',
  file: '<path d="M7 3.5h7l4 4V20H7z"/><path d="M14 3.5V8h4"/>',
  list: '<path d="M8 7h11"/><path d="M8 12h11"/><path d="M8 17h11"/><path d="M4.5 7h.1"/><path d="M4.5 12h.1"/><path d="M4.5 17h.1"/>',
  logout: '<path d="M10 5H6v14h4"/><path d="M15 8l4 4-4 4"/><path d="M9 12h10"/>',
  flask: '<path d="M9 4h6"/><path d="M10 4v5l-5 9a1.5 1.5 0 0 0 1.3 2.2h11.4A1.5 1.5 0 0 0 19 18l-5-9V4"/>',
  book: '<path d="M5 5h6a2 2 0 0 1 2 2v12a2 2 0 0 0-2-2H5z"/><path d="M19 5h-6"/><path d="M19 5v12h-6"/>',
};
const ic = (n, s = 18) => `<svg class="ic" width="${s}" height="${s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICONS[n]}</svg>`;

async function api(path, opts = {}) {
  const o = { headers: {}, credentials: "same-origin", ...opts };
  if (o.body && !(o.body instanceof FormData)) { o.headers["Content-Type"] = "application/json"; o.body = JSON.stringify(o.body); }
  const r = await fetch("/api" + path, o);
  if (r.status === 401 && !path.startsWith("/login")) { if (S.user) S.loginNote = "Your session ended. Sign in again."; S.user = null; renderLogin(); throw new Error("signed out"); }
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
function debounce(fn, ms) { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; }

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
  const label = c.priority === "expedited" ? "72-hour clock" : "7-day clock";
  if (ms < 0) return { text: label + " overdue", cls: "late" };
  const t = h >= 48 ? Math.floor(h / 24) + "d " + Math.floor(h % 24) + "h" : Math.floor(h) + "h " + Math.floor((h % 1) * 60) + "m";
  return { text: t + " left · " + label, cls: h < (c.priority === "expedited" ? 24 : 48) ? "soon" : "" };
}
const STATUS = { new: "New", in_review: "In review", pended: "Pended", escalated: "Escalated", approved: "Approved", denied: "Denied" };
const AI = { approve: ["Recommends approve", "ok", "✓"], pend: ["Missing info", "warn", "?"], escalate: ["Needs a physician", "escalated", "↑"], no_policy: ["No policy yet", "bad", "!"], verify: ["Check the packet", "warn", "?"] };
const ROLE_CHIP = { admin: ["Intake", "plain"], nurse: ["Nurse", "new"], medical_director: ["Medical director", "escalated"] };
const OPEN = ["new", "in_review", "pended", "escalated"];

/* ---------- login ---------- */
async function renderLogin() {
  const accts = await fetch("/api/demo-accounts").then((r) => r.json());
  $app.innerHTML = `<div class="login">
    <div class="login-art"><div class="brand"><span class="brand-mark">PA</span> PA Desk</div>
      <div><h2>Get to the right decision the first time.</h2><p>PA Desk reads each prior authorization packet, checks it against policy, and shows the nurse exactly what to do next.</p></div>
      <div class="steps"><div><b>1</b>Intake receives the packet and picks a nurse</div><div><b>2</b>The nurse reviews it and approves, asks, or escalates</div><div><b>3</b>A medical director decides the hard cases</div></div></div>
    <div class="login-side"><div class="login-card">
      <div class="brand"><span class="brand-mark">PA</span> PA Desk</div>
      <h1>Sign in</h1><p class="muted" style="margin:0;line-height:1.5">Prior authorization decision support. Every case is made-up data.</p>
      ${S.loginNote ? `<div class="banner" style="margin-top:12px">${esc(S.loginNote)}</div>` : ""}
      <form id="lf"><div class="field"><label for="em">Email</label><input id="em" type="email" autocomplete="username" required></div>
      <div class="field"><label for="pw">Password</label><input id="pw" type="password" autocomplete="current-password" required></div>
      <button class="btn primary lg" style="margin-top:16px;width:100%" type="submit">Sign in</button></form>
      <div class="demo-list"><div class="faint" style="font-size:12.5px">Demo accounts. Click one to sign in (password: demo1234)</div>
      ${accts.map((a) => `<button class="demo-btn" data-email="${esc(a.email)}"><span><b>${esc(a.name)}</b><br><span class="faint" style="font-size:12.5px">${esc(a.title)}</span></span><span class="chip ${ROLE_CHIP[a.role][1]}">${ROLE_CHIP[a.role][0]}</span></button>`).join("")}</div>
    </div></div></div>`;
  const doLogin = guard(async (email, password) => { S.loginNote = null; S.user = await api("/login", { method: "POST", body: { email, password } }); S.view = homeView(); S.caseId = null; S.detail = null; S.q = ""; await boot(); });
  document.getElementById("lf").onsubmit = (e) => { e.preventDefault(); doLogin(document.getElementById("em").value, document.getElementById("pw").value); };
  document.querySelectorAll(".demo-btn").forEach((b) => (b.onclick = () => doLogin(b.dataset.email, "demo1234")));
}
const homeView = () => (S.user.role === "medical_director" ? "decide" : S.user.role === "admin" ? "unassigned" : "attention");

/* ---------- loading ---------- */
async function boot() {
  const [me, users] = await Promise.all([api("/me"), api("/users")]);
  S.user = me; S.users = users;
  parseHash();
  if (S.view === "evals") await runEvals();
  else await loadList();
  if (S.user.role === "admin") await loadTeam();
  if (S.caseId) await loadCase(S.caseId);
  render();
}
function parseHash() {
  const h = location.hash.replace(/^#\/?/, "").split("/");
  if (h[0] === "case" && h[1]) { S.caseId = h[1]; if (S.view === "evals") S.view = homeView(); }
  else if (h[0] === "view" && h[1]) { S.view = h[1]; S.caseId = null; }
}
window.addEventListener("hashchange", guard(async () => {
  if (!S.user) return;
  parseHash();
  if (S.view !== "evals") { await loadList(); if (S.caseId) await loadCase(S.caseId); } else if (!S.evals) await runEvals();
  render();
}));
async function loadList() {
  if (S.view === "evals") return;
  const v = S.q || S.view === "team" ? "all" : S.view;
  const d = await api(`/cases?view=${v}&q=${encodeURIComponent(S.q)}`);
  S.cases = d.cases; S.counts = d.counts;
}
async function loadTeam() { S.team = (await api("/cases?view=all")).cases; }
async function loadCase(id) {
  S.detail = await api("/cases/" + id);
  const pages = [...new Set(S.detail.elements.map((e) => e.page))].sort((a, b) => a - b);
  S.pageNo = pages[0] || 1; S.highlight = null; S.activeKey = null;
}
async function runEvals() {
  S.evals = await api("/evals"); S.holdout = null;
  render();
  S.holdout = await api("/evals/holdout");
}
async function refresh() {
  await loadList();
  if (S.user.role === "admin") await loadTeam();
  S.user = await api("/me");
}
function go(hash) { history.replaceState(null, "", hash); }

/* ---------- shell ---------- */
function viewsFor() {
  const r = S.user.role;
  if (r === "admin") return [["unassigned", "Needs assignment", "inbox"], ["team", "Team", "users"], ["pended", "Waiting on provider", "clock"], ["escalated", "With a physician", "up"], ["done", "Decided", "checkc"], ["all", "Everything", "list"]];
  if (r === "nurse") return [["attention", "Needs my review", "inbox"], ["at_risk", "At risk", "alert"], ["pended", "Waiting on provider", "clock"], ["escalated", "With a physician", "up"], ["done", "Decided", "checkc"], ["mine", "All my cases", "list"]];
  return [["decide", "Waiting for my decision", "inbox"], ["done", "Decided", "checkc"], ["all", "Everything", "list"]];
}
const VIEW_TITLE = { attention: "Needs my review", at_risk: "At risk", mine: "All my cases", decide: "Waiting for my decision", unassigned: "Needs assignment", team: "Team", pended: "Pended, waiting on provider", escalated: "Escalated to physician", done: "Decided", all: "Everything" };
const VIEW_HELP = { attention: "Sorted by time left. The case closest to its clock is first.", at_risk: "Cases close to or past their CMS decision clock.", unassigned: "Pick a nurse for each packet. The oldest is first.", pended: "A question went to the provider. These return to the nurse when the provider replies.", escalated: "A medical director is deciding these.", decide: "Escalated to you. The case closest to its clock is first.", done: "Approved or denied.", all: "Every case you can see." };

function render() {
  if (!S.user) return renderLogin();
  const isMD = S.user.role === "medical_director", isAdmin = S.user.role === "admin";
  const views = viewsFor();
  const risk = S.counts.at_risk;
  const railBtn = ([v, l, i]) => {
    const n = v === "team" || v === "evals" ? "" : S.counts[v] ?? "";
    const red = v === "at_risk" && n > 0;
    return `<button class="rail-item ${S.view === v ? "on" : ""}" data-view="${v}" aria-label="${esc(l)}${n !== "" ? ", " + n : ""}" title="${esc(l)}">${ic(i, 20)}<span class="lab">${l}</span><span class="n ${red ? "red" : ""}">${n}</span>${n !== "" && n > 0 ? `<span class="rb ${red ? "red" : ""}">${n}</span>` : ""}</button>`;
  };
  $app.innerHTML = `<div class="shell">
    <header class="topbar">
      <button class="icon-btn" id="burger" aria-label="${S.railOpen ? "Collapse the menu" : "Expand the menu"}" aria-expanded="${S.railOpen}">${ic("menu", 22)}</button>
      <div class="brand"><span class="brand-mark">PA</span><span class="hide-sm">PA Desk</span></div>
      <label class="search">${ic("search", 18)}<input id="q" type="search" placeholder="Search by member, case number, or procedure" value="${esc(S.q)}" aria-label="Search cases"><kbd>/</kbd></label>
      <div class="spacer"></div>
      ${isMD ? "" : `<label class="btn primary" style="cursor:pointer">${ic("upload", 16)}Upload packet<input type="file" id="up" accept="application/pdf" class="sr"></label>`}
      <div class="menu-wrap"><button class="icon-btn" id="bell" aria-label="Notifications${S.user.unread ? ", " + S.user.unread + " new" : ""}">${ic("bell", 22)}${S.user.unread ? `<span class="badge-dot">${S.user.unread}</span>` : ""}</button>${S.pop === "notif" ? notifPop() : ""}</div>
      <div class="menu-wrap"><button class="profile" id="prof" aria-haspopup="menu"><span class="avatar ${isMD ? "md" : isAdmin ? "admin" : ""}">${esc(initials(S.user.name))}</span><span class="who"><b>${esc(S.user.name)}</b><small>${esc(S.user.title)}</small></span>${ic("down", 16)}</button>
        ${S.pop === "profile" ? `<div class="pop menu" role="menu"><div class="pop-head">${esc(S.user.name)}<div class="faint" style="font-weight:400;font-size:12.5px">${esc(S.user.title)}</div></div><button class="menu-item" id="out" role="menuitem">${ic("logout", 18)}Sign out</button></div>` : ""}</div>
    </header>
    <div class="main">
      <nav class="rail ${S.railOpen ? "open" : ""}" aria-label="Queues"><h4>${isAdmin ? "Intake" : isMD ? "Decisions" : "My queues"}</h4>
        ${views.map(railBtn).join("")}
        ${S.user.role === "nurse" ? "" : `<h4>Quality</h4><button class="rail-item ${S.view === "evals" ? "on" : ""}" data-view="evals" aria-label="Quality" title="Quality">${ic("flask", 20)}<span class="lab">Quality</span><span class="n"></span></button>`}</nav>
      <main class="content" id="content">${S.view === "evals" ? evalsHtml() : S.caseId && S.detail ? caseHtml() : S.view === "team" && !S.q ? teamHtml() : queueHtml()}</main>
    </div>${S.upload ? uploadModal() : ""}</div>`;
  bind();
}

/* ---------- queue ---------- */
function nurseLoad() {
  const out = {};
  S.users.filter((u) => u.role === "nurse").forEach((u) => (out[u.id] = { u, open: 0, risk: 0, pended: 0, escalated: 0, cases: [] }));
  S.team.filter((c) => OPEN.includes(c.status) && out[c.assignee_id]).forEach((c) => {
    const o = out[c.assignee_id]; o.open++; o.cases.push(c);
    if (["soon", "breached"].includes(c.sla)) o.risk++;
    if (c.status === "pended") o.pended++;
    if (c.status === "escalated") o.escalated++;
  });
  return out;
}
function assignButtons(cid) {
  const load = nurseLoad();
  const pick = S.pick && S.pick.cid === cid ? S.pick.uid : null;
  const chosen = pick && load[pick];
  return Object.values(load).map((o) => `<button class="btn small ${pick === o.u.id ? "primary" : ""}" data-pick="${o.u.id}" data-for="${cid}" aria-pressed="${pick === o.u.id}" title="${o.open} open, ${o.risk} at risk">${esc(o.u.name)} · ${o.open} open</button>`).join("") +
    (chosen ? `<button class="btn small approve" data-confirm="${cid}">Assign to ${esc(chosen.u.name)}</button>` : "");
}
function queueHtml() {
  const searching = !!S.q;
  const title = searching ? `Results for “${S.q}”` : VIEW_TITLE[S.view];
  const isAdmin = S.user.role === "admin";
  return `<div class="page"><div class="page-head"><div><h1>${esc(title)}</h1><p>${S.cases.length} case${S.cases.length === 1 ? "" : "s"}${!searching && VIEW_HELP[S.view] ? " · " + VIEW_HELP[S.view] : ""}</p></div></div>` +
    (S.cases.length ? S.cases.map((c) => {
      const k = clock(c), ai = AI[c.ai_action];
      const showAssign = isAdmin && S.view === "unassigned" && !searching;
      return `<div class="qrow" data-case="${c.id}" role="button" tabindex="0">
        <div><div class="nm">${esc(c.member_name)} <span class="faint mono" style="font-weight:400">${esc(c.id)}</span></div>
        <div class="sub">CPT ${esc(c.cpt || "-")} · ${esc(c.procedure.replace("Elective inpatient admission, ", "Inpatient admission, "))} · ${esc(c.facility)}</div>
        <div class="tags"><span class="chip ${c.status}">${STATUS[c.status]}</span>
          ${c.last_event === "provider_reply" && c.status === "in_review" ? `<span class="chip ok">Provider replied</span>` : ""}${c.last_event === "returned" && c.status === "in_review" ? `<span class="chip escalated">Returned by director</span>` : ""}
          ${isAdmin || ["approved", "denied"].includes(c.status) ? "" : `<span class="chip ${ai[1]}">${ai[2]} ${ai[0]}${c.ai_action === "pend" ? " (" + c.ai_missing + ")" : c.ai_action === "verify" ? " (" + c.ai_unsure + ")" : ""}</span>`}
          ${c.sla === "breached" ? `<span class="chip bad">Past its clock</span>` : c.sla === "soon" ? `<span class="chip warn">Due soon</span>` : ""}
          ${c.priority === "expedited" ? `<span class="chip bad">Expedited</span>` : ""}</div>
        ${showAssign ? `<div class="assign-inline"><span class="faint" style="font-size:12.5px">Assign to</span>${assignButtons(c.id)}</div>` : ""}</div>
        <div class="right"><span class="clock ${k.cls}">${esc(k.text)}</span><span class="faint" style="font-size:12.5px">${c.assignee ? esc(c.assignee.name) : "Not assigned"}</span></div></div>`;
    }).join("") : `<div class="empty">Nothing here.</div>`) + `</div>`;
}

function teamHtml() {
  const load = Object.values(nurseLoad());
  const max = Math.max(5, ...load.map((o) => o.open));
  const unassigned = S.team.filter((c) => OPEN.includes(c.status) && !c.assignee_id);
  return `<div class="page"><div class="page-head"><div><h1>Team</h1><p>Who has what. Use this to decide where the next packet goes.</p></div></div>
    <div class="tbl"><table><thead><tr><th>Nurse</th><th>Open cases</th><th>At risk</th><th>Pended</th><th>Escalated</th><th>Load</th></tr></thead><tbody>
    ${load.map((o) => `<tr style="cursor:pointer" data-teamopen="${o.u.id}"><td><b>${esc(o.u.name)}</b><div class="faint" style="font-size:12.5px">${esc(o.u.title)}</div></td><td>${o.open}</td><td>${o.risk ? `<span class="chip bad">${o.risk}</span>` : "0"}</td><td>${o.pended}</td><td>${o.escalated}</td><td><div class="load-bar"><i style="width:${Math.round((100 * o.open) / max)}%"></i></div></td></tr>
      ${S.teamOpen === o.u.id ? `<tr><td colspan="6" style="background:var(--hover)">${o.cases.length ? o.cases.map((c) => { const k = clock(c); return `<button class="btn small" style="margin:2px 6px 2px 0" data-case="${c.id}">${esc(c.member_name)} · <span class="clock ${k.cls}">${esc(k.text)}</span></button>`; }).join("") : `<span class="faint">No open cases.</span>`}</td></tr>` : ""}`).join("")}
    <tr><td><b>Not assigned yet</b></td><td>${unassigned.length}</td><td colspan="4">${unassigned.length ? `<button class="btn small" data-view="unassigned">Assign them</button>` : `<span class="faint">All caught up.</span>`}</td></tr></tbody></table></div></div>`;
}

/* ---------- case ---------- */
function citeBtn(page, quote, key) {
  if (!page) return "";
  S.cites.push({ page, quote, key });
  return `<button class="pg ${S.highlight && S.highlight.page == page && S.activeKey === key ? "on" : ""}" data-cite="${S.cites.length - 1}" title="Show page ${page} of the packet">p.${page}</button>`;
}
const schemaOf = (d) => (d.analysis && d.analysis.fact_schema) || [];
const factLabel = (d, key) => (schemaOf(d).find((x) => x.key === key) || {}).label || "this fact";
// one chip per page that backs a fact. A dashed chip is another statement in the packet that the AI did not choose.
function evidenceChips(f, key) {
  const ev = (f.evidence || []).filter((e) => e.page), seen = new Set(), out = [];
  ev.forEach((e) => {
    const sup = e.supports !== false, id = e.page + "|" + sup;
    if (seen.has(id) || out.length >= 4) return;
    seen.add(id); S.cites.push({ page: e.page, quote: e.quote, key });
    const on = S.highlight && S.highlight.page == e.page && S.activeKey === key;
    out.push(`<button class="pg ${on ? "on" : ""} ${sup ? "" : "alt"}" data-cite="${S.cites.length - 1}" title="${sup ? "Show page " + e.page : "Another statement in the packet. Show page " + e.page}${e.match === "fuzzy" ? ". Matched despite scan noise" : ""}">p.${e.page}</button>`);
  });
  return out.length ? out.join("") : citeBtn(f.page, f.quote, key);
}
const FSTATUS = { found: "Stated", implied: "Implied only", none: "Stated: none", missing: "Not in packet", unsure: "Not sure. Check the packet" };
const dotClass = (f, key) => (f.status === "found" ? "" : f.status === "none" ? (key === "indication_evidence" ? "n" : "g") : "w");

function caseHtml() {
  S.cites = [];
  const d = S.detail, k = clock(d), a = d.analysis;
  const role = S.user.role, isAdmin = role === "admin";
  const done = ["approved", "denied"].includes(d.status);
  const pages = new Set(d.elements.map((e) => e.page)).size;
  const idx = S.cases.findIndex((c) => c.id === d.id);
  const prev = idx > 0 ? S.cases[idx - 1] : null, next = idx >= 0 && idx < S.cases.length - 1 ? S.cases[idx + 1] : null;
  const where = S.q ? "Search results" : VIEW_TITLE[S.view];
  const showBar = !done && (role === "nurse" || (role === "medical_director" && d.status === "escalated"));
  return `<div class="case">
    <div class="chead">
      <div class="chead-nav"><button class="btn small" data-back="1">${ic("left", 14)}${esc(where)}</button>
        ${idx >= 0 ? `<button class="btn small" ${prev ? `data-case="${prev.id}"` : "disabled"} aria-label="Previous case">${ic("left", 14)}Previous</button><span class="muted" style="font-size:13px">Case ${idx + 1} of ${S.cases.length}</span><button class="btn small" ${next ? `data-case="${next.id}"` : "disabled"} aria-label="Next case">Next${ic("right", 14)}</button>` : ""}</div>
      <div class="chead-row">
        <div><div class="mono faint">${esc(d.id)}</div>
          <h1>${esc(d.member_name)} <span class="faint" style="font-size:15px;font-weight:500">${d.age ? d.age + "y · " : ""}${esc(d.member_id)}</span></h1>
          <div class="muted">${esc(d.procedure.replace("Elective inpatient admission, ", "Inpatient admission, "))} · CPT ${esc(d.cpt || "-")} · ${esc(d.facility)} ${a.procedure ? `<span class="chip plain" style="margin-left:6px">${esc(a.procedure.short)}</span>` : ""}</div></div>
        <div class="chead-right"><span class="chip ${d.status}">${STATUS[d.status]}</span>${d.priority === "expedited" ? `<span class="chip bad">Expedited</span>` : ""}<span class="chip">${ic("clock", 14)}${esc(k.text)}</span>
          <span class="muted" style="font-size:13px">${d.assignee ? esc(d.assignee.name) : "Not assigned"}</span></div></div>
      <div class="tabs" role="tablist">${[["review", isAdmin ? "Assign" : "Review"], ["packet", `Full packet · ${pages} page${pages === 1 ? "" : "s"}`], ["activity", `Chat · ${d.comments.length}`]].map(([t, l]) => `<button class="tab ${S.tab === t ? "on" : ""}" role="tab" data-tab="${t}">${l}</button>`).join("")}</div></div>
    <div class="cbody" id="cbody-scroll">${justActedHtml(d)}${S.tab === "review" ? (isAdmin ? adminHtml(d, a) : reviewHtml(d, a, done)) : S.tab === "packet" ? fullPacketHtml(d) : activityHtml(d)}</div>
    ${showBar ? decisionBar(d, a) : ""}</div>`;
}

function justActedHtml(d) {
  if (!S.justActed || S.justActed.id !== d.id) return "";
  const nxt = S.cases.find((c) => c.id !== d.id && OPEN.includes(c.status) && !["pended", "escalated"].includes(c.status));
  return `<div class="banner ok row" style="margin-bottom:16px"><span><b>Saved.</b> ${esc(S.justActed.msg)}</span>${nxt ? `<button class="btn small primary" data-case="${nxt.id}">Next case: ${esc(nxt.member_name)}</button>` : `<span>No more cases in this list.</span>`}</div>`;
}

/* admin: assign first */
function adminHtml(d, a) {
  const load = nurseLoad();
  const urgent = d.priority === "expedited";
  const pick = S.pick && S.pick.cid === d.id ? S.pick.uid : null;
  const unassignedNext = S.team.find((c) => c.id !== d.id && OPEN.includes(c.status) && !c.assignee_id);
  return `<div class="stack" style="max-width:860px">
    ${S.justAssigned === d.id ? `<div class="banner ok row"><span><b>Assigned.</b> ${esc(d.assignee ? d.assignee.name : "The nurse")} has been told.</span>${unassignedNext ? `<button class="btn small primary" data-case="${unassignedNext.id}">Next to assign: ${esc(unassignedNext.member_name)}</button>` : `<span>Nothing else waits for assignment.</span>`}</div>` : ""}
    <div class="card assign-card"><div><h3 style="margin-bottom:2px">${d.assignee ? "Assigned to " + esc(d.assignee.name) : "Who should review this packet?"}</h3><div class="faint">${urgent ? "This one is expedited. It has a 72-hour clock. " : ""}Pick the nurse with room. Each one is told right away.</div></div>
      ${Object.values(load).map((o) => { const sel = pick === o.u.id, cur = d.assignee_id === o.u.id; return `<button class="nurse-opt ${sel || (cur && !pick) ? "on" : ""}" data-pick="${o.u.id}" data-for="${d.id}" aria-pressed="${sel}"><span class="avatar">${esc(initials(o.u.name))}</span><span><b>${esc(o.u.name)}</b><br><span class="faint" style="font-size:12.5px">${o.open} open · ${o.risk} at risk · ${o.pended} pended</span></span><span class="chip ${sel ? "new" : cur ? "ok" : "plain"}">${sel ? "Selected" : cur ? "Assigned now" : "Select"}</span></button>`; }).join("")}
      <div class="action-row"><button class="btn primary lg" data-confirm="${d.id}" ${pick && pick !== d.assignee_id ? "" : "disabled"}>${pick && load[pick] ? (d.assignee_id ? "Reassign to " : "Assign to ") + esc(load[pick].u.name) : "Pick a nurse first"}</button>${pick ? `<button class="btn ghost" data-pick="">Cancel</button>` : ""}</div></div>
    <div class="card"><h3>The packet in brief</h3><div class="muted" style="line-height:1.7">${esc(d.member_name)}, ${d.age ? d.age + " years old, " : ""}member ${esc(d.member_id)}<br>${esc(d.procedure)} at ${esc(d.facility)}<br>${new Set(d.elements.map((e) => e.page)).size} pages · received ${ago(d.received_at)}</div>
      <div class="note">Intake routes cases. Nurses make the clinical calls.</div></div></div>`;
}

/* nurse / director review: facts + criteria left, packet right */
function questionCardHtml(d) {
  if (d.status !== "escalated") return "";
  const q = [...d.comments].reverse().find((c) => c.kind === "escalation");
  if (!q) return "";
  const by = q.user ? q.user.name : "the nurse", toMd = S.user.role === "medical_director";
  return `<div class="reco escalate"><span class="mk big up">↑</span><div><h3>${toMd ? "Escalated by " + esc(by) : "Escalated to " + esc(d.md ? d.md.name : "a medical director")}</h3><div class="esc-when">${ago(q.created_at)}</div><div class="esc-label">Reason</div><p>${esc(q.body.replace(/^@\w+\s*/, ""))}</p></div></div>`;
}
function fixForm(key) {
  const def = schemaOf(S.detail).find((x) => x.key === key) || { kind: "text", hint: "", can_be_none: false };
  const input = def.kind === "enum"
    ? `<select id="fixvalue" style="width:auto">${(def.values || []).map((v) => `<option>${esc(v)}</option>`).join("")}</select>`
    : def.kind === "number"
      ? `<input id="fixvalue" type="number" step="any" placeholder="${esc(def.hint || "")}" style="width:170px">`
      : `<input id="fixvalue" type="text" placeholder="${esc(def.hint || "")}" style="flex:1;min-width:200px">`;
  return `<div class="fixform"><b>What does the packet say?</b>
    <label><input type="radio" name="fixkind" value="found" checked> It is in the packet</label>
    ${def.can_be_none ? `<label><input type="radio" name="fixkind" value="none"> The packet says there is none</label>` : ""}
    <label><input type="radio" name="fixkind" value="missing"> It is not in the packet</label>
    <div style="display:flex;gap:8px;flex-wrap:wrap">${input}
      <input id="fixpage" type="number" min="1" placeholder="Page" style="width:90px"></div>
    <div class="faint" style="font-size:12.5px">This saves your answer and updates the recommendation. It also tells us how well we read the packet.</div>
    <div style="display:flex;gap:8px"><button class="btn small primary" data-savefix="${key}">Save</button><button class="btn small" data-fix="${key}">Cancel</button></div></div>`;
}
const RECO_TITLE = (a) => a.action === "approve" ? "Approve. Everything is supported." : a.action === "pend" ? (a.gate.questions.length > 1 ? `Pend: ${a.gate.questions.length} things are missing` : "Pend: one thing is missing") : a.action === "verify" ? "Check the packet first" : a.action === "escalate" ? "Escalate to a medical director" : "No policy for this procedure yet";
const RECO_MARK = { approve: ["ok", "✓"], pend: ["w", "?"], verify: ["w", "?"], escalate: ["up", "↑"], no_policy: ["not_met", "!"] };

function reviewHtml(d, a, done) {
  const canFix = !done && ["nurse", "medical_director"].includes(S.user.role);
  const mk = { met: "✓", missing: "?", unsure: "?", advisory: "!", not_met: "✕", info: "i" };
  const stLabel = { met: "Met", missing: "Missing", unsure: "Not sure", advisory: "Advisory", not_met: "Not met", info: "Info" };
  const reco = `<div class="reco ${a.action}"><span class="mk big ${RECO_MARK[a.action][0]}">${RECO_MARK[a.action][1]}</span><div><h3>${RECO_TITLE(a)}</h3><p>${esc(a.rationale)}</p></div></div>`;
  if (a.action === "no_policy") {
    return `<div class="stack" style="max-width:860px">${reco}<div class="card"><h3>What happens next</h3><p class="muted" style="line-height:1.6;margin:0">A reviewer needs to find the right policy for this procedure before anything can be checked. PA Desk checks a short list of procedures today (CPT ${esc((a.covered_cpt_codes || []).join(", "))}). You can still approve, ask the provider, or escalate below.</p></div></div>`;
  }
  const groups = {};
  a.checklist.forEach((c) => (groups[c.policy_id] ||= { c, items: [] }).items.push(c));
  const pol = Object.fromEntries(a.policies.map((p) => [p.id, p]));
  return `<div class="cols">
    <div class="stack">${questionCardHtml(d)}
      ${d.sla === "breached" ? `<div class="banner">This case is past its ${d.priority === "expedited" ? "72-hour expedited" : "7-day standard"} CMS decision clock. It needs attention now.</div>` : ""}
      ${d.status === "escalated" && questionCardHtml(d) ? "" : reco}
      <div class="card"><h3>What the packet says</h3>
        ${schemaOf(d).map(({ key, label }) => { const f = d.facts[key] || { status: "missing" }; const v = f.display;
          const fuzzy = (f.evidence || []).some((e) => e.match === "fuzzy" && e.supports !== false);
          return `<div class="fr ${S.activeKey === key ? "on" : ""}"><b>${esc(label)}</b><div><span class="sd ${dotClass(f, key)}"></span>${v ? esc(v) : `<span class="muted">${FSTATUS[f.status]}</span>`}${f.checked ? `<span class="tick" title="A second check read the sentence in context and confirmed it states this">✓</span>` : ""}${f.status === "implied" ? `<div class="q">“${esc(f.quote)}” ${esc(f.note || "")}</div>` : f.note && !f.confirmed_by ? `<div class="q">${esc(f.note)}</div>` : ""}${fuzzy ? `<div class="faint" style="font-size:12px">Matched despite scan noise. Check the page.</div>` : ""}${f.confirmed_by ? `<div class="faint" style="font-size:12.5px">Confirmed by ${esc(f.confirmed_by)}</div>` : ""}</div><div class="acts">${evidenceChips(f, key)}${canFix && f.status === "unsure" ? `<button class="btn small primary" data-fix="${key}">Check</button>` : ""}</div>${S.fix === key ? fixForm(key) : ""}</div>`; }).join("")}</div>
      <div class="card"><h3>Criteria, in order of authority</h3>
        ${Object.values(groups).map(({ c, items }) => { const p = pol[c.policy_id]; return `<div class="group"><div class="group-head"><b>${esc(c.layer)}: ${esc(c.policy_title)}</b>
          <span>${p && p.verified ? `<span class="chip ok">Verified source</span>` : `<span class="chip plain">Illustrative</span>`} ${p && p.url ? `<a href="${esc(p.url)}" target="_blank" rel="noopener">Open policy</a>` : ""}</span></div>
          ${items.map((i) => `<div class="crit"><span class="mk ${i.status}" title="${stLabel[i.status]}">${mk[i.status]}</span><div><div class="crit-text">${esc(i.text)}</div><div class="crit-cite">${esc(i.cite)}${i.note ? " · " + esc(i.note) : ""}</div>${i.evidence ? `<div class="q">“${esc(i.evidence.quote)}”</div>` : ""}</div><div class="acts">${i.evidence ? (i.evidence_all || [i.evidence]).filter((e, n, arr) => e.supports !== false && arr.findIndex((x) => x.page === e.page) === n).slice(0, 3).map((e) => citeBtn(e.page, e.quote, i.fact_key)).join("") : `<span class="chip ${i.status === "not_met" ? "bad" : i.status === "info" ? "plain" : "warn"}">${stLabel[i.status]}</span>`}</div></div>`).join("")}</div>`; }).join("")}
        <div class="note">MCG and InterQual are licensed content and are not included. A licensed feed would plug in here.</div></div>
      ${d.status === "pended" ? simulateReplyCard(a) : ""}
    </div>
    <div class="sticky">${viewerHtml(d)}</div></div>`;
}

function pagesOf(d) {
  const byPage = {};
  d.elements.forEach((e) => (byPage[e.page] ||= []).push(e));
  return byPage;
}
function pageBody(els, p) {
  const qs = [];
  if (S.highlight && S.highlight.page == p && S.highlight.quote) qs.push(S.highlight.quote.trim());
  const af = S.detail && S.activeKey ? S.detail.facts[S.activeKey] : null;
  ((af && af.evidence) || []).forEach((e) => { if (e.page == p && e.quote && !qs.includes(e.quote.trim())) qs.push(e.quote.trim()); });
  return els.map((e) => {
    let t = esc(e.text);
    qs.forEach((q) => { const eq = esc(q); t = t.split(eq).join(`<mark>${eq}</mark>`); });
    return e.type === "Title" ? `<div class="h">${t}</div>` : `<div>${t}</div>`;
  }).join("");
}
function viewerHtml(d) {
  const byPage = pagesOf(d), nums = Object.keys(byPage).map(Number).sort((a, b) => a - b);
  const i = nums.indexOf(S.pageNo);
  const label = S.activeKey ? factLabel(d, S.activeKey) : null;
  return `<div class="vhead"><div><b>Packet</b> <span class="faint">${label ? "· showing the evidence for " + esc(label) : "· page by page"}</span></div>
      <div style="display:flex;align-items:center;gap:6px"><button class="btn small" data-page="${nums[i - 1] ?? ""}" ${i > 0 ? "" : "disabled"} aria-label="Previous page">${ic("left", 14)}</button><span class="faint" style="font-size:13px">Page ${S.pageNo} of ${nums.length}</span><button class="btn small" data-page="${nums[i + 1] ?? ""}" ${i >= 0 && i < nums.length - 1 ? "" : "disabled"} aria-label="Next page">${ic("right", 14)}</button></div></div>
    <div class="chips">${nums.map((n) => `<button class="pg ${n === S.pageNo ? "on" : ""}" data-page="${n}">${n}</button>`).join("")}</div>
    <div class="paper" id="paper">${byPage[S.pageNo] ? pageBody(byPage[S.pageNo], S.pageNo) : `<span class="faint">No text on this page.</span>`}</div>
    <div style="display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;align-items:center"><span class="faint" style="font-size:12.5px">Click a page chip on the left and it opens here.</span><button class="btn small" data-tab="packet">${ic("book", 14)}Read the full packet</button></div>`;
}

function fullPacketHtml(d) {
  const byPage = pagesOf(d), nums = Object.keys(byPage).map(Number).sort((a, b) => a - b);
  return `<div class="stack" style="max-width:860px">
    <div class="card" style="display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;align-items:center"><div><h3 style="margin-bottom:2px">The full packet</h3><div class="faint" style="font-size:12.5px">All ${nums.length} pages, in order. Read it end to end if you want to check everything yourself.</div></div>
      <div class="action-row"><a class="btn small" href="/api/cases/${d.id}/pdf" target="_blank" rel="noopener">${ic("file", 14)}Open the original PDF</a></div></div>
    <div class="chips">${nums.map((n) => `<button class="pg" data-jump="${n}">Page ${n}</button>`).join("")}</div>
    <div>${nums.map((p) => `<div class="page-block" id="pg${p}"><div class="page-tag">Page ${p} of ${nums.length}</div><div class="page-body">${pageBody(byPage[p], p)}</div></div>`).join("")}</div></div>`;
}

const ACT_LABEL = { received: "Packet received", analyzed: "Packet checked", assigned: "Assigned", approved: "Approved", approved_override: "Approved against the recommendation", denied: "Denied", returned: "Returned to nurse", fact_corrected: "Fact corrected", sla_soon: "Clock warning", sla_breached: "Clock passed", commented: "Comment", escalated: "Escalated", pended: "Pended", provider_reply: "Provider replied" };
function activityHtml(d) {
  const items = [
    ...d.comments.map((c) => ({ t: c.created_at, kind: "c", c })),
    ...d.audit.filter((a) => !["commented", "escalated", "pended", "provider_reply"].includes(a.action)).map((a) => ({ t: a.created_at, kind: "a", a })),
  ].sort((x, y) => x.t.localeCompare(y.t));
  const label = { comment: "", escalation: "Escalation", provider_request: "Question to provider", provider_reply: "Provider reply" };
  const body = (s) => esc(s).replace(/@(\w+)/g, '<span class="mention">@$1</span>').replace(/\n/g, "<br>");
  return `<div class="stack" style="max-width:860px"><div class="card" style="display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap">
    <div><h3 style="margin-bottom:2px">Case record</h3><div class="faint" style="font-size:12.5px">The facts, the checklist, the decision, and every step below, as one file.</div></div>
    <a class="btn small" href="/api/cases/${d.id}/export" download="${d.id}_record.json">${ic("download", 14)}Export case record</a></div>
  <div class="card"><div>${items.map((i) => i.kind === "c" ? `<div class="tl-item"><span class="avatar sm ${i.c.user && i.c.user.role === "medical_director" ? "md" : ""}">${i.c.user ? esc(initials(i.c.user.name)) : "PR"}</span>
      <div class="tl-body"><span class="tl-who">${i.c.user ? esc(i.c.user.name) : "Provider office"}</span><span class="tl-time">${ago(i.c.created_at)}</span>${label[i.c.kind] ? ` <span class="chip plain">${label[i.c.kind]}</span>` : ""}<div class="bubble ${i.c.kind}">${body(i.c.body)}</div></div></div>`
    : `<div class="tl-item"><span class="sys-dot"></span><div class="tl-body muted"><b>${esc(i.a.user ? i.a.user.name : "PA Desk")}</b> · ${esc(ACT_LABEL[i.a.action] || i.a.action.replace(/_/g, " "))}<span class="tl-time">${ago(i.a.created_at)}</span><div class="faint" style="font-size:13px">${esc(i.a.detail)}</div></div></div>`).join("")}</div></div>
  <div class="card"><h3>Send a message</h3><textarea id="cbody" placeholder="Write a message. Use @patel or @brooks to tag a medical director."></textarea>
    <div class="action-row" style="margin-top:8px"><button class="btn primary" data-go="comment">Send</button>${S.users.filter((u) => u.id !== S.user.id).map((u) => `<button class="btn small" data-tag="${u.handle}">@${u.handle}</button>`).join("")}</div></div></div>`;
}

/* ---------- decision bar ---------- */
const SAMPLE_REPLY = {
  expected_los_days: "Surgeon addendum: Expected length of stay: 3 midnights.",
  indication_evidence: "Flexion-extension radiographs show dynamic instability at the operative level.",
  conservative_treatment: "Failed 8 months of conservative care: physical therapy, NSAIDs and epidural injections.",
  comorbidities: "Past medical history: heart failure, type 2 diabetes.",
  post_op_needs: "Post-operative plan: telemetry monitoring and cardiology co-management.",
  optimal_medical_therapy_months: "Medication history: on sacubitril-valsartan, carvedilol, spironolactone and dapagliflozin for 7 months.",
  shared_decision_making: "A shared decision making visit using an ICD decision aid was completed on 2026-09-30 and documented in the chart.",
  prior_medical_treatment: "Completed a 9-month physician-supervised weight management program with a registered dietitian and an anti-obesity medication. Weight was regained.",
  bmi: "Most recent BMI 39.4 kg/m2, measured 2026-09-22.",
  lvef_percent: "Repeat echocardiogram 2026-09-25: LVEF 30%.",
};
function simulateReplyCard(a) {
  const reply = a.gate.questions.map((q) => SAMPLE_REPLY[q.fact]).filter(Boolean).join(" ");
  return `<div class="card"><h3>Demo: the provider replies</h3><label class="faint" style="font-size:12.5px">This adds a page to the packet and checks the case again.</label><textarea id="reply" style="margin-top:6px">${esc(reply || "Provider reply: additional documentation attached.")}</textarea><div class="action-row" style="margin-top:8px"><button class="btn" data-go="reply">Simulate the reply</button></div></div>`;
}
const RETURN_REASONS = [["reconsider", "Please look at this again"], ["info_enough", "The packet already has what we need"], ["ask_provider", "Ask the provider for more first"], ["wrong_policy", "A different policy applies"], ["other", "Other"]];

function decisionBar(d, a) {
  const isMD = S.user.role === "medical_director";
  const mds = S.users.filter((u) => u.role === "medical_director");
  const open = S.act;
  const qs = a.gate.questions.map((q) => q.question);
  const drafted = qs.length > 1 ? qs.map((q, i) => `${i + 1}. ${q}`).join("\n") : qs[0] || "";
  const hint = isMD ? "Your decision" : a.action === "approve" ? "Recommended: approve" : a.action === "pend" ? "Recommended: pend and ask the provider" : a.action === "verify" ? "Check the facts marked “Check” first" : a.action === "escalate" ? "Recommended: escalate to a medical director" : "Choose what to do";
  const mark = RECO_MARK[a.action];
  const form = (() => {
    if (open === "approve" && (a.action !== "approve" || isMD)) return `<div class="dform"><label for="note">${isMD ? "Note for the record (optional)" : "PA Desk did not recommend approval. Your reason:"}</label><textarea id="note"></textarea><div class="action-row"><button class="btn approve" data-go="approve">Confirm approval</button></div></div>`;
    if (open === "pend") return `<div class="dform"><label for="question">Question to the provider (one specific ask)</label><textarea id="question">${esc(drafted)}</textarea><div class="action-row"><button class="btn primary" data-go="pend">Send question and pend</button></div></div>`;
    if (open === "escalate") return `<div class="dform"><label for="mdsel">Which medical director?</label><select id="mdsel">${mds.map((m) => `<option value="${m.id}">${esc(m.name)}</option>`).join("")}</select><label for="note">What do you need decided?</label><textarea id="note">${esc(a.action === "escalate" ? a.rationale : "")}</textarea><div class="action-row"><button class="btn primary" data-go="escalate">Escalate and tag</button></div></div>`;
    if (open === "deny") return `<div class="dform"><label for="note">Clinical reason for the denial (required)</label><textarea id="note"></textarea><div class="action-row"><button class="btn danger" data-go="deny">Confirm denial</button></div></div>`;
    if (open === "return") return `<div class="dform"><label for="reason">Why are you sending it back?</label><select id="reason">${RETURN_REASONS.map(([v, l]) => `<option value="${v}">${l}</option>`).join("")}</select><label for="note">Note to the nurse (optional)</label><textarea id="note"></textarea><div class="action-row"><button class="btn primary" data-go="return">Return to nurse</button></div></div>`;
    return "";
  })();
  const on = (v) => (open === v ? " outline" : "");
  return `<div class="dbar">${form}<div class="dbar-row">
    <div style="display:flex;align-items:center;gap:10px"><span class="mk big ${isMD ? "up" : mark[0]}">${isMD ? "↑" : mark[1]}</span><div><b>${hint}</b>${isMD ? "" : `<div class="faint" style="font-size:12.5px">${d.status === "pended" ? "Waiting on the provider. You can still decide." : "You make the call. Edit anything before you send it."}</div>`}</div></div>
    <div class="dbar-btns">
      ${isMD ? `<button class="btn" data-act="return">Return to nurse…</button><button class="btn danger outline" data-act="deny">Deny…</button><button class="btn approve lg" data-act="approve">Approve</button>`
        : `<button class="btn ${a.action === "escalate" ? "primary" : ""}" data-act="escalate">Escalate to a director…</button>
           <button class="btn ${a.action === "pend" ? "primary lg" : ""}" data-act="pend">Pend and ask the provider…</button>
           <button class="btn approve ${a.action === "approve" ? "lg" : "outline"}" data-act="approve">${a.action === "approve" ? "Approve" : "Approve anyway…"}</button>`}
    </div></div></div>`;
}

/* ---------- quality page ---------- */
const PLAIN_PACKET = { h1: "Odd phrasing", h2: "Two different stay lengths", h3: "A finding ruled out", h4: "Blurry scan" };
const PLAIN_FACT = { lvef_percent: "Ejection fraction", lvef_method: "How it was measured", nyha_class: "NYHA class", cardiomyopathy_type: "Cause of heart failure", recent_mi_revasc: "Recent heart attack, bypass, or stent", optimal_medical_therapy_months: "Months on heart failure medicines", limiting_conditions: "Conditions that rule out an ICD", bmi: "BMI", prior_medical_treatment: "Prior medical treatment", expected_los_days: "Expected stay", comorbidities: "Comorbidities", post_op_needs: "Post-op care needs", indication_evidence: "Surgical indication", conservative_treatment: "Conservative care", shared_decision_making: "Shared decision making" };
const plainPacket = (file) => PLAIN_PACKET[(file.match(/h\d/) || [])[0]] || file;
function evalsHtml() {
  const e = S.evals, h = S.holdout;
  if (!e) return `<div class="page"><div class="empty">Loading…</div></div>`;
  const out = { correct: "Read it right", false_negative: "Missed it", false_negative_implied: "Flagged, not sure", false_positive_hallucination: "Said it was there, but it was not", wrong_value: "Found it, wrong number" };
  return `<div class="page" style="display:grid;gap:18px"><div class="page-head"><div><h1>How well we read packets</h1><p>Two checks. The first shows the flow works. The second tries to trip us up.</p></div><button class="btn" id="rerun">Run both again</button></div>
    <div><h3 style="margin-bottom:4px">Everyday packets</h3><p class="faint" style="margin:0 0 10px;font-size:12.5px">${e.total} packets, each with a known right answer.</p>
    <div class="stat"><div><b>${e.passed} of ${e.total}</b><span>got the right recommendation</span></div><div><b>${e.zero_denials ? "0" : "!"}</b><span>denials made by PA Desk (always zero)</span></div></div></div>
    <div class="banner">${esc(e.caveat)}</div>
    <div class="tbl"><table><thead><tr><th>Packet</th><th>Right answer</th><th>Our answer</th><th></th></tr></thead><tbody>${e.results.map((r) => `<tr><td><b>${esc(r.label)}</b></td><td>${esc(r.expected_action)}</td><td>${esc(r.actual_action)}</td><td><span class="chip ${r.passed ? "ok" : "bad"}">${r.passed ? "Pass" : "Miss"}</span></td></tr>`).join("")}</tbody></table></div>
    <div><h3 style="margin:8px 0 4px">Tricky packets</h3><p class="faint" style="margin:0 0 10px;font-size:12.5px">Odd phrasing, conflicting numbers, ruled-out findings, and a blurry scan.</p>
    ${!h ? `<div class="card"><div class="empty">Running the tricky packets. The blurry scan takes a little longer…</div></div>` : `
    <div class="stat"><div><b>${h.action_matches} of ${h.packets_total}</b><span>got the right recommendation</span></div>
      <div><b>${h.completeness_recall.pct}%</b><span>of facts that were there, we found (${h.completeness_recall.correct} of ${h.completeness_recall.total})</span></div>
      <div><b>${h.hallucination_rate.pct}%</b><span>of the time we said something was there when it was not (${h.hallucination_rate.hallucinated} of ${h.hallucination_rate.total})</span></div></div>
    <div class="banner" style="margin-top:12px">${esc(h.caveat)}</div>
    <div style="display:grid;gap:10px;margin-top:12px">${h.results.map((r) => `<div class="card"><div style="display:flex;justify-content:space-between;gap:10px;align-items:baseline;flex-wrap:wrap"><div><b>${esc(plainPacket(r.file))}</b> <span class="faint">${esc(r.member)}</span></div><div style="display:flex;gap:8px;align-items:center"><span class="faint" style="font-size:12.5px">right answer ${esc(r.expected_action)}, ours ${esc(r.actual_action)}</span><span class="chip ${r.action_matches ? "ok" : "bad"}">${r.action_matches ? "Pass" : "Miss"}</span></div></div>
      ${r.facts.filter((f) => f.outcome !== "correct").length ? `<div style="margin-top:8px;display:grid;gap:4px">${r.facts.filter((f) => f.outcome !== "correct").map((f) => `<div class="muted" style="font-size:13px"><span class="chip ${f.outcome === "false_positive_hallucination" || f.outcome === "wrong_value" ? "bad" : "warn"}">${out[f.outcome]}</span> ${esc(PLAIN_FACT[f.fact] || f.fact)}</div>`).join("")}</div>` : `<div class="faint" style="font-size:12.5px;margin-top:8px">Every fact in this packet was read right.</div>`}</div>`).join("")}</div>`}</div></div>`;
}

function notifPop() {
  return `<div class="pop"><div class="pop-head">Notifications</div>${S.notifs.length ? S.notifs.map((n) => `<button class="pop-item ${n.read ? "" : "unread"}" data-case="${n.case_id}"><b>${esc(n.case_id)}</b> · ${esc(n.body)}<div class="faint" style="font-size:12.5px">${ago(n.created_at)}</div></button>`).join("") : `<div class="empty">No notifications.</div>`}</div>`;
}

/* ---------- upload ---------- */
const STEPS = [
  ["reading", "Reading the packet", "Turning every page into text"],
  ["facts", "Finding the key facts", "Expected stay, risk factors, imaging, conservative care"],
  ["policy", "Checking against policy", "Medicare rules and the Humana policy"],
];
function uploadModal() {
  const u = S.upload, cur = u.shown;
  return `<div class="overlay" role="dialog" aria-modal="true" aria-labelledby="upt"><div class="modal">
    <h2 id="upt">Reading the packet</h2><div class="faint" style="margin:2px 0 14px">${esc(u.name)}</div>
    ${u.error ? `<div class="banner bad">${esc(u.error)}</div><div class="action-row" style="margin-top:12px"><button class="btn" id="upclose">Close</button></div>` : `
    ${STEPS.map(([k, t, sub], i) => `<div class="step ${i < cur ? "done" : i === cur ? "now" : "todo"}"><span class="dot">${i < cur ? ic("check", 14) : ""}</span><div><b>${t}${k === "reading" && i < cur && u.pages ? ` · ${u.pages} pages` : ""}</b>${sub}</div></div>`).join("")}
    <div class="faint" style="margin-top:12px;font-size:12.5px">This usually takes under a minute. Keep this tab open.</div>`}</div></div>`;
}
async function startUpload(file) {
  const job = Math.random().toString(36).slice(2, 10);
  S.upload = { name: file.name, shown: 0, target: 0, pages: null, error: null };
  render();
  const order = STEPS.map((s) => s[0]);
  let finished = false;
  const poll = setInterval(async () => {
    try {
      const j = await api("/jobs/" + job);
      if (j.pages) S.upload.pages = j.pages;
      const i = order.indexOf(j.stage);
      if (i >= 0) S.upload.target = Math.max(S.upload.target, i);
      if (j.stage === "policy" || j.stage === "done") S.upload.target = 2;
    } catch (e) { /* keep waiting */ }
  }, 600);
  const pace = setInterval(() => {
    if (S.upload && !finished && S.upload.shown < S.upload.target) { S.upload.shown++; render(); }
  }, 900);
  const fd = new FormData(); fd.append("file", file); fd.append("job", job);
  let d;
  try { d = await api("/cases", { method: "POST", body: fd }); }
  catch (e) { clearInterval(poll); clearInterval(pace); finished = true; if (e.message !== "signed out") { S.upload.error = e.message; render(); const c = document.getElementById("upclose"); if (c) c.onclick = () => { S.upload = null; render(); }; } return; }
  clearInterval(poll); clearInterval(pace); finished = true;
  S.upload.shown = 3; S.upload.pages = new Set(d.elements.map((e) => e.page)).size; render();
  await new Promise((r) => setTimeout(r, 500));
  S.upload = null;
  S.caseId = d.id; S.tab = "review"; S.view = S.user.role === "admin" ? "unassigned" : "attention"; S.q = "";
  go("#/case/" + d.id);
  await refresh(); S.detail = d; S.pageNo = Math.min(...d.elements.map((e) => e.page)); S.highlight = null; S.activeKey = null; S.justAssigned = null;
  toast(S.user.role === "admin" ? "Packet read. Pick a nurse for it." : "Packet read: " + d.id);
  render();
}

/* ---------- events ---------- */
async function openCase(id) {
  S.pop = null; S.pick = null; S.caseId = id; S.tab = "review"; S.act = null; S.fix = null; S.justAssigned = null;
  go("#/case/" + id);
  await loadList(); await loadCase(id); render();
  const c = document.getElementById("content"); if (c) c.scrollTop = 0;
}
function bind() {
  const on = (sel, fn) => document.querySelectorAll(sel).forEach((el) => (el.onclick = guard((e) => fn(el, e))));
  on("[data-view]", async (el) => { S.pop = null; S.pick = null; S.view = el.dataset.view; S.caseId = null; S.detail = null; S.act = null; S.q = ""; go("#/view/" + S.view); if (S.view === "evals") await runEvals(); else { await loadList(); if (S.user.role === "admin") await loadTeam(); } render(); });
  on("[data-back]", async () => { S.pick = null; S.caseId = null; S.detail = null; S.act = null; go("#/view/" + S.view); await refresh(); render(); });
  on("[data-case]", (el) => openCase(el.dataset.case));
  document.querySelectorAll(".qrow").forEach((r) => (r.onkeydown = (e) => { if ((e.key === "Enter" || e.key === " ") && e.target === r) { e.preventDefault(); openCase(r.dataset.case); } }));
  on("[data-tab]", (el) => { S.tab = el.dataset.tab; render(); const c = document.getElementById("cbody-scroll"); if (c) c.scrollTop = 0; });
  on("[data-cite]", (el) => { const c = S.cites[+el.dataset.cite]; S.highlight = c; S.pageNo = c.page; S.activeKey = c.key; render(); const p = document.getElementById("paper"); if (p && window.innerWidth <= 1100) p.scrollIntoView({ block: "center" }); });
  on("[data-page]", (el) => { if (!el.dataset.page) return; S.pageNo = +el.dataset.page; if (S.highlight && S.highlight.page != S.pageNo) { S.highlight = null; S.activeKey = null; } render(); });
  on("[data-jump]", (el) => { const pg = document.getElementById("pg" + el.dataset.jump); if (pg) pg.scrollIntoView({ block: "start", behavior: "smooth" }); });
  on("[data-act]", (el) => { S.act = S.act === el.dataset.act ? null : el.dataset.act; if (el.dataset.act === "approve" && S.detail.analysis.action === "approve" && S.user.role === "nurse") return submit("approve"); render(); const t = document.querySelector(".dform textarea"); if (t) t.focus(); });
  on("[data-go]", (el) => submit(el.dataset.go));
  on("[data-fix]", (el) => { S.fix = S.fix === el.dataset.fix ? null : el.dataset.fix; render(); });
  on("[data-teamopen]", (el) => { S.teamOpen = S.teamOpen === +el.dataset.teamopen ? null : +el.dataset.teamopen; render(); });
  on("[data-pick]", (el) => { const same = S.pick && S.pick.cid === el.dataset.for && S.pick.uid === +el.dataset.pick; S.pick = el.dataset.pick && !same ? { cid: el.dataset.for || S.caseId, uid: +el.dataset.pick } : null; render(); });
  on("[data-confirm]", async (el) => {
    const cid = el.dataset.confirm;
    if (!S.pick || S.pick.cid !== cid) return;
    const d = await api(`/cases/${cid}/assign`, { method: "POST", body: { user_id: S.pick.uid } });
    S.pick = null;
    if (S.detail && S.detail.id === cid) S.detail = d;
    S.justAssigned = cid;
    await refresh(); render();
    toast("Assigned to " + d.assignee.name);
  });
  on("[data-savefix]", async (el) => {
    const key = el.dataset.savefix, kind = (document.querySelector('input[name="fixkind"]:checked') || {}).value || "found";
    const page = document.getElementById("fixpage").value;
    const d = await api(`/cases/${S.caseId}/facts/${key}`, { method: "POST", body: { kind, value: kind === "found" ? document.getElementById("fixvalue").value : "", page: page ? +page : null } });
    S.detail = d; S.fix = null; await refresh(); render();
    toast("Saved. The recommendation is now: " + ({ approve: "approve", pend: "pend", escalate: "escalate", verify: "check the packet" }[d.analysis.action] || d.analysis.action));
  });
  on("[data-tag]", (el) => { const t = document.getElementById("cbody"); t.value += (t.value && !t.value.endsWith(" ") ? " " : "") + "@" + el.dataset.tag + " "; t.focus(); });
  const out = document.getElementById("out"); if (out) out.onclick = guard(async () => { await api("/logout", { method: "POST" }); S.user = null; S.detail = null; S.caseId = null; S.pop = null; S.q = ""; renderLogin(); });
  const burger = document.getElementById("burger"); if (burger) burger.onclick = () => { S.railOpen = !S.railOpen; try { localStorage.setItem("pa.rail", S.railOpen ? "open" : "closed"); } catch (e) { /* ignore */ } render(); };
  const q = document.getElementById("q"); if (q) q.oninput = guard(debounce(async () => {
    S.q = q.value; S.caseId = S.q ? null : S.caseId; if (S.q) { S.detail = null; if (S.view === "evals") S.view = homeView(); }
    await loadList(); render(); const nq = document.getElementById("q"); nq.focus(); nq.setSelectionRange(nq.value.length, nq.value.length);
  }, 250));
  const up = document.getElementById("up"); if (up) up.onchange = guard(async () => { const file = up.files[0]; if (!file) return; await startUpload(file); });
  const bell = document.getElementById("bell"); if (bell) bell.onclick = guard(async (e) => { e.stopPropagation(); if (S.pop === "notif") { S.pop = null; return render(); } S.notifs = await api("/notifications"); S.pop = "notif"; render(); await api("/notifications/read", { method: "POST" }); S.user.unread = 0; });
  const prof = document.getElementById("prof"); if (prof) prof.onclick = (e) => { e.stopPropagation(); S.pop = S.pop === "profile" ? null : "profile"; render(); };
  const rr = document.getElementById("rerun"); if (rr) rr.onclick = guard(async () => { await runEvals(); render(); toast("Checks run again"); });
}
document.addEventListener("click", (e) => { if (S.pop && !e.target.closest(".pop")) { S.pop = null; if (S.user) render(); } });
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && S.pop) { S.pop = null; render(); }
  if (e.key === "/" && !/^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement.tagName)) { const q = document.getElementById("q"); if (q) { e.preventDefault(); q.focus(); } }
});

const submit = guard(async (kind) => {
  const v = (id) => (document.getElementById(id) || {}).value || "";
  const id = S.caseId;
  let d;
  if (kind === "comment") d = await api(`/cases/${id}/comments`, { method: "POST", body: { body: v("cbody") } });
  else if (kind === "reply") d = await api(`/cases/${id}/addendum`, { method: "POST", body: { text: v("reply") } });
  else if (kind === "pend") d = await api(`/cases/${id}/action`, { method: "POST", body: { action: "pend", question: v("question") } });
  else if (kind === "escalate") d = await api(`/cases/${id}/action`, { method: "POST", body: { action: "escalate", md_id: +v("mdsel"), note: v("note") } });
  else if (kind === "return") d = await api(`/cases/${id}/action`, { method: "POST", body: { action: "return", reason: v("reason"), note: v("note") } });
  else d = await api(`/cases/${id}/action`, { method: "POST", body: { action: kind, note: v("note") } });
  S.detail = d; S.act = null;
  if (kind === "comment") S.tab = "activity";
  if (["approve", "pend", "escalate", "deny", "return"].includes(kind)) { S.justActed = { id, msg: { approve: "Approved.", pend: "Question sent to the provider.", escalate: "Sent to the medical director.", deny: "Denied. Your reason is on the record.", return: "Returned to the nurse." }[kind] }; S.tab = "review"; }
  const msgs = { approve: "Approved", pend: "Question sent. Case pended", escalate: "Escalated and tagged", deny: "Denied with reason recorded", return: "Returned to nurse", reply: "Provider reply added. Case checked again", comment: "Message sent" };
  toast(msgs[kind]);
  await refresh(); render();
});

(async () => { try { await boot(); } catch (e) { if (e.message === "signed out" || !S.user) renderLogin(); } })();
