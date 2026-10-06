"use strict";
/* The policy owner's screens. Loaded after app.js, which owns S, api, esc, ic, toast, guard and render.
   The owner starts from a service (one kind of request, such as acute back pain) and builds it up in this order:
   billing codes, policies, key facts, pilot, live. Key facts belong to the policy. A service shows the combined list.
   Views: Services (list, then one service), Requests without a policy, Policies (the catalog), Version history. A draft policy opens full screen. */
S.pol = { data: null, svcKey: null, svc: null, step: 0, sug: null, build: null, sel: null, edit: null, confirm: false, note: "", asks: {}, audit: null, demand: null, revert: null, check: {}, busy: null, msg: null,
  newSvc: { open: false, name: "", scope: "", code: "", source: "" }, code: { code: "", source: "" }, cs: { q: "", data: null, cons: null, art: {}, rows: {}, picked: {}, busy: null }, sv: { open: null, note: "" }, q: "", more: false, form: { source: "cfr", ident: "", pid: "", title: "", level: "HUMANA_INTERNAL" } };
let polTimer = null;

const LEVEL = { REGULATION: "Federal regulation", NCD: "National coverage (NCD)", LCD: "Local coverage (LCD)", HUMANA_INTERNAL: "Humana policy", MCG: "MCG guideline" };
const TEST_WORDS = { gte: "at least", lte: "at most", in: "one of", absent: "must be none", present: "must be documented", informational: "information only" };

function polTarget(pid) {
  if (pid.startsWith("NCD-")) return { kind: "ncd", ident: pid.slice(4) };
  if (pid.startsWith("LCD-")) return { kind: "lcd", ident: pid.slice(4) };
  const m = pid.match(/^CFR-(\d+)-(.+)$/);
  return m ? { kind: "cfr", ident: `${m[1]} CFR ${m[2]}` } : null;
}
/* Long text is shown in full behind a "Show all" click instead of being cut off in the middle of a word. */
const more = (text, n) => {
  const t = String(text || "");
  if (t.length <= n) return esc(t);
  const cut = t.slice(0, n).replace(/\s+\S*$/, "");
  return `<details class="more"><summary>${esc(cut)}… <u>Show all</u></summary>${esc(t)}</details>`;
};
const when = (iso) => (iso ? ago(iso) : "never");
const small = (html, extra) => `<div class="faint" style="font-size:12.5px;${extra || ""}">${html}</div>`;
const testText = (c) => {
  const t = c.test || {};
  const v = Array.isArray(t.value) ? t.value.join(", ") : t.value;
  return `${esc((c.required_fact || "key fact").replace(/_/g, " "))} ${esc(TEST_WORDS[t.type] || t.type)}${v !== undefined && v !== null && t.type !== "absent" && t.type !== "present" ? " <b>" + esc(v) + "</b>" : ""}`;
};
const fullTime = (iso) => { try { return new Date(iso).toLocaleString([], { dateStyle: "medium", timeStyle: "short" }); } catch (e) { return iso || ""; } };
const shortName = (name) => name.replace(/\s+/g, " ").trim().slice(0, 40);

async function loadPolicies() {
  S.pol.data = await api("/policies");
  S.counts = Object.assign(S.counts || {}, { services: S.pol.data.n_drafts, demand: S.pol.data.demand_count });
  if (S.view === "history") S.pol.audit = await api("/policies/audit");
  if (S.view === "demand") S.pol.demand = await api("/policies/demand");
  if (S.view === "services" && S.pol.svcKey) S.pol.svc = await api("/policies/services/" + S.pol.svcKey);
}

async function openService(key) {
  S.pol.svcKey = key; S.pol.build = null; S.pol.msg = null; S.pol.q = ""; S.pol.sug = null; S.pol.sv = { open: null, note: "" }; S.pol.more = false;
  S.pol.cs = { q: "", data: null, cons: null, art: {}, rows: {}, picked: {}, busy: null };
  S.pol.svc = await api("/policies/services/" + key);
  S.pol.step = wizStart(S.pol.svc);
  render(); window.scrollTo(0, 0);
  loadSug(); loadCodeSug();
}
async function loadCodeSug() {
  if (!S.pol.svcKey || (S.pol.svc && S.pol.svc.status === "live")) return;
  const cs = S.pol.cs, key = S.pol.svcKey;
  const r = await api(`/policies/services/${key}/code-suggestions?q=${encodeURIComponent(cs.q || "")}`);
  if (key !== S.pol.svcKey) return;
  cs.data = r; cs.cons = null;
  const box = document.getElementById("csbox"); if (box) { box.innerHTML = codeSugHtml(); bindCodeSug(); }
  if (r.articles.length) {
    const q = cs.q;
    const c = await api(`/policies/services/${key}/code-consensus?q=${encodeURIComponent(q || "")}`);
    if (key !== S.pol.svcKey || q !== cs.q) return;
    cs.cons = c;
    const b2 = document.getElementById("csbox"); if (b2) { b2.innerHTML = codeSugHtml(); bindCodeSug(); }
  }
}
async function loadSug() {
  if (!S.pol.svcKey) return;
  S.pol.sug = await api(`/policies/services/${S.pol.svcKey}/suggestions?q=${encodeURIComponent(S.pol.q || "")}`);
  const box = document.getElementById("sugbox"); if (box) { box.innerHTML = sugHtml(); bindSug(); }
}

async function openBuild(id) {
  clearInterval(polTimer);
  S.pol.build = await api("/policies/builds/" + id);
  S.pol.sel = null; S.pol.edit = null; S.pol.confirm = false; S.pol.note = ""; S.pol.asks = {};
  if (S.pol.build.status === "running") {
    polTimer = setInterval(guard(async () => {
      const b = await api("/policies/builds/" + id);
      S.pol.build = b;
      if (b.status !== "running") { clearInterval(polTimer); await loadPolicies(); }
      render();
    }), 2500);
  }
  render(); window.scrollTo(0, 0);
}

/* ---------- services: the list ---------- */
const SVC_STATUS = { live: ["Live", "ok"], pilot: ["Pilot", "warn"], planned: ["Planned", "plain"] };
const SVC_STATUS_HELP = { planned: "Not switched on. No request is sent to it.", pilot: "Switched on. A nurse checks every recommendation.", live: "Switched on and tested." };

/* The one thing the owner should do next on a service, worked out from what the service has so far. */
function nextStep(s) {
  if (s.status === "live") return ["Live", "ok"];
  if (s.status === "pilot") return ["Check the pilot, then make it live", "warn"];
  if (!s.cpts.length) return ["Add billing codes", "new"];
  if (!s.policies.length && !s.n_drafts) return ["Add policies", "new"];
  if (s.n_drafts) return ["Review a policy", "warn"];
  if (!s.n_rules) return ["Add a policy with rules", "new"];
  return ["Start the pilot", "ok"];
}

function polServicesList() {
  const d = S.pol.data, n = S.pol.newSvc;
  const rows = d.services_detail.map((s) => {
    const st = SVC_STATUS[s.status] || SVC_STATUS.live, nx = nextStep(s);
    return `<tr class="clickrow" data-psvc="${esc(s.key)}"><td><b>${esc(s.name)}</b>${s.scope ? small(esc(s.scope)) : small(esc(s.full))}</td>
      <td><span class="chip ${st[1]}">${st[0]}</span></td>
      <td>${s.cpts.length}</td><td>${s.policies.length}${s.n_drafts ? small(s.n_drafts + " to review") : ""}</td><td>${s.n_details}</td><td>${s.n_cases}</td>
      <td><span class="chip ${nx[1]}">${esc(nx[0])}</span></td></tr>`;
  }).join("");
  if (n.open) return newServiceHtml();
  return `<div class="page" style="display:grid;gap:20px;max-width:1180px">
    <div class="page-head"><div><h1>Services</h1><p>A service is one kind of request, such as acute back pain. Start here: add the service, then its billing codes and policies.</p></div>
      <div style="display:flex;gap:18px;align-items:center;flex-wrap:wrap"><div class="stat" style="margin:0"><div><b>${d.services_detail.filter((s) => s.status === "live").length}</b><span>live</span></div><div><b>${d.services_detail.filter((s) => s.status === "pilot").length}</b><span>pilot</span></div><div><b>${d.services_detail.filter((s) => s.status === "planned").length}</b><span>planned</span></div></div>
      ${n.open ? "" : `<button class="btn primary" id="nsopen">+ New service</button>`}</div></div>
    ${S.pol.msg ? `<div class="banner">${esc(S.pol.msg)}</div>` : ""}
    <div class="tbl"><table><thead><tr><th>Service</th><th>Status</th><th>Billing codes</th><th>Policies</th><th>Key facts</th><th>Requests seen</th><th>Next step</th></tr></thead><tbody>${rows}</tbody></table></div></div>`;
}

/* ---------- services: one service ---------- */
const AUDIT_WORDS = { service_created: "Added the service", service_status: "Changed the status", service_policy_added: "Added a policy", service_policy_removed: "Removed a policy", service_code_added: "Added a billing code", service_code_removed: "Removed a billing code",
  draft_started: "Started a policy", rule_approved: "Approved a rule", rule_rejected: "Rejected a rule", rule_pending: "Undid a decision", published: "Approved a policy", reverted: "Went back to a version", checked_for_update: "Checked CMS for changes" };
const AUDIT_CHIP = { service_created: "new", service_status: "warn", service_policy_added: "ok", service_policy_removed: "warn", service_code_added: "ok", service_code_removed: "warn", published: "ok", rule_approved: "ok", rule_rejected: "bad", reverted: "warn", rule_pending: "plain", draft_started: "new", checked_for_update: "plain" };

function sugRow(x, key) {
  const lib = x.in_library;
  return `<tr><td><b>${esc(x.title)}</b>${small(esc(x.policy_id) + " · " + esc(LEVEL[x.level] || x.level) + (x.effective ? " · effective " + esc(x.effective) : ""))}</td>
    <td>${lib ? (x.verified ? `${x.rules} rules approved` : `<span class="faint">Placeholder, no rules</span>`) : `<span class="faint">Not built yet</span>`}</td>
    <td style="text-align:right">${lib ? `<button class="btn small" data-sugadd="${esc(x.policy_id)}">Add to this service</button>` : `<button class="btn small primary" data-sugbuild="${esc(x.kind)}" data-sugid="${esc(x.ident)}">Build this policy</button>`}</td></tr>`;
}
function sugHtml() {
  const g = S.pol.sug;
  if (!g) return `<div class="faint" style="padding:8px 0">Looking for policies…</div>`;
  const head = (t, sub) => `<div style="margin:10px 0 4px"><b style="font-size:13.5px">${t}</b>${sub ? small(sub) : ""}</div>`;
  const near = g.library.filter((x) => x.match), rest = g.library.filter((x) => !x.match);
  const tbl = (rows) => `<div class="tbl"><table><tbody>${rows.map((x) => sugRow(x)).join("")}</tbody></table></div>`;
  return `${near.length ? head("Already in your library", "Policies you have built for other services.") + tbl(near) : ""}
    ${g.cms.length ? head(g.asked ? "From CMS" : "Suggested from CMS", g.asked ? "" : "Matched from the service name. Matching from billing codes comes next.") + tbl(g.cms) : g.asked ? `<div class="faint" style="padding:8px 0">No CMS policy matches. Try one word of the title, or a number.</div>` : ""}
    ${rest.length ? `<details class="more" style="margin-top:8px"><summary><u>Other policies in your library (${rest.length})</u></summary><div style="margin-top:6px">${tbl(rest)}</div></details>` : ""}`;
}

/* Billing codes the owner can pick, each with its CMS source already attached. Nothing is typed. */
function codeRows(rows, of) {
  const cs = S.pol.cs;
  const mk = (r0) => { const r = of ? Object.assign({}, r0, { of }) : r0; cs.rows[r.code] = r0; return `<tr><td style="width:34px"><input type="checkbox" data-cspick="${esc(r.code)}" ${cs.picked[r.code] ? "checked" : ""} ${r.taken ? "disabled" : ""} aria-label="Use code ${esc(r.code)}"></td>
    <td style="width:80px"><b>${esc(r.code)}</b></td><td>${r.short ? `<div>${esc(r.short)}</div>${small(more(r.description, 90))}` : more(r.description, 90)}${r.group > 1 ? `<span class="chip plain" title="CMS lists this code in a separate group on the article, not with the main codes" style="margin-top:4px">Separate group on the article</span>` : ""}</td><td class="faint" style="font-size:12.5px">${r.of ? `<b>${r.n_articles} of ${r.of} articles</b><br>` : ""}${r.taken === "this" ? "Already on this service" : r.taken ? "Sends packets to " + esc(r.taken) : (r.sources || []).slice(0, 2).map((z) => `<a href="${esc(z.url)}" target="_blank" rel="noopener">${esc(z.id)}</a>`).join(" · ")}</td></tr>`; };
  const first = rows.slice(0, 10), rest = rows.slice(10);
  return `<div class="tbl"><table><tbody>${first.map(mk).join("")}</tbody></table></div>${rest.length ? `<details class="more" style="margin-top:6px"><summary><u>Show ${rest.length} more codes</u></summary><div class="tbl" style="margin-top:6px"><table><tbody>${rest.map(mk).join("")}</tbody></table></div></details>` : ""}`;
}
function codeSugHtml() {
  const cs = S.pol.cs, g = cs.data;
  if (!g) return `<div class="faint" style="padding:8px 0">Finding billing codes…</div>`;
  const head = (t, sub) => `<div style="margin:10px 0 4px"><b style="font-size:13.5px">${t}</b>${sub ? small(sub) : ""}</div>`;
  const pol = g.from_policies.map((p) => head("Listed for " + esc(p.title), "CMS lists these codes beside the policy.") + codeRows(p.codes)).join("");
  const found = cs.cons && cs.cons.codes.length;
  const main = !g.articles.length ? `<div class="faint" style="padding:6px 0">${esc(g.note || "No billing codes found.")}</div>`
    : !cs.cons ? `<div class="faint" style="padding:8px 0">Finding billing codes…</div>`
    : found ? head("Suggested billing codes", `The number shows how many of ${cs.cons.read} CMS articles list the code. More articles means more likely. Each code you add keeps its article as its source. Check the descriptions.`) + codeRows(cs.cons.codes, cs.cons.read)
    : `<div class="faint" style="padding:6px 0">CMS lists no codes on the matching articles. Open one below, or add a code yourself.</div>`;
  const arts = g.articles.map((a) => { const d = cs.art[a.aid], open = d && d.open;
    return `<div style="border:1px solid var(--line);border-radius:10px;padding:8px 12px;margin-bottom:6px"><div style="display:flex;gap:8px;justify-content:space-between;align-items:center;flex-wrap:wrap"><div><b>${esc(a.title)}</b>${small(esc(a.id) + " · " + esc((a.mac || "").replace(/\s*\(.*$/, "")) + ` · <a href="${esc(a.url)}" target="_blank" rel="noopener">open on CMS</a>`)}</div>
      <button class="btn small" data-csart="${esc(a.aid)}" data-csver="${esc(a.version)}">${cs.busy === a.aid ? "Loading…" : open ? "Hide codes" : "See codes"}</button></div>
      ${open && d.codes ? `<div style="margin-top:8px">${d.codes.length ? codeRows(d.codes) : `<div class="faint">CMS lists no codes on this article.</div>`}</div>` : ""}</div>`; }).join("");
  const n = Object.keys(cs.picked).length;
  return `${pol}${main}
    ${arts ? `<details class="more" style="margin-top:8px" ${cs.cons && !found ? "open" : ""}><summary><u>See the ${g.articles.length} CMS articles these come from</u></summary>${small("On the CMS page, the code table under \"CPT/HCPCS Codes\" stays hidden until you accept the AMA license. Click \"Accept\" there to see it.", "margin-top:6px")}<div style="margin-top:8px">${arts}</div></details>` : ""}
    ${g.as_of ? small("CMS data copied on " + esc(g.as_of) + ".", "margin-top:8px") : ""}<div style="margin-top:10px"><button class="btn primary small" id="csadd" ${n ? "" : "disabled"}>${n ? "Add " + n + " selected code" + (n > 1 ? "s" : "") : "Tick the codes to add"}</button></div>`;
}
/* The Next button on the codes step follows the ticks: with codes ticked it adds them and moves on. */
function csNextUpdate() {
  const cs = S.pol.cs, n = Object.keys(cs.picked).length, b = document.getElementById("csnext"), w = document.getElementById("stepwhy");
  if (!b) return;
  const has = b.dataset.has === "1";
  b.textContent = n ? `Add ${n} code${n > 1 ? "s" : ""} and continue` : "Next: policies";
  b.disabled = !n && !has;
  if (w) w.innerHTML = n || has ? "" : small("Add at least one billing code to continue.");
}
function bindCodeSug() {
  const cs = S.pol.cs, on = (sel, fn) => document.querySelectorAll(sel).forEach((el) => (el.onclick = guard((e) => fn(el, e))));
  document.querySelectorAll("[data-cspick]").forEach((el) => (el.onchange = () => {
    if (el.checked) cs.picked[el.dataset.cspick] = cs.rows[el.dataset.cspick]; else delete cs.picked[el.dataset.cspick];
    document.querySelectorAll(`[data-cspick="${el.dataset.cspick}"]`).forEach((o) => (o.checked = el.checked));
    const b = document.getElementById("csadd"), n = Object.keys(cs.picked).length; if (b) { b.disabled = !n; b.textContent = n ? `Add ${n} selected code${n > 1 ? "s" : ""}` : "Tick the codes to add"; }
    csNextUpdate();
  }));
  on("[data-csart]", async (el) => {
    const aid = el.dataset.csart, d = cs.art[aid];
    if (d && d.codes) { d.open = !d.open; const box = document.getElementById("csbox"); box.innerHTML = codeSugHtml(); bindCodeSug(); return; }
    cs.busy = aid; document.getElementById("csbox").innerHTML = codeSugHtml(); bindCodeSug();
    try { const r = await api(`/policies/services/${S.pol.svcKey}/code-article?aid=${encodeURIComponent(aid)}&ver=${encodeURIComponent(el.dataset.csver)}`); cs.art[aid] = { open: true, codes: r.codes }; }
    finally { cs.busy = null; const box = document.getElementById("csbox"); if (box) { box.innerHTML = codeSugHtml(); bindCodeSug(); } }
  });
  on("#csnext", async () => {
    if (Object.keys(cs.picked).length) {
      const codes = Object.values(cs.picked).map((r) => ({ code: r.code, description: r.description, sources: r.sources }));
      await api(`/policies/services/${S.pol.svcKey}/codes/from-cms`, { method: "POST", body: { codes } });
      cs.picked = {}; cs.art = {}; await loadPolicies();
    }
    S.pol.step = 3; S.pol.msg = null; render(); window.scrollTo(0, 0);
  });
  on("#csadd", async () => {
    const codes = Object.values(cs.picked).map((r) => ({ code: r.code, description: r.description, sources: r.sources }));
    const r = await api(`/policies/services/${S.pol.svcKey}/codes/from-cms`, { method: "POST", body: { codes } });
    S.pol.msg = `Added ${r.added.length} billing code${r.added.length > 1 ? "s" : ""}, each with its CMS source.`; cs.picked = {}; cs.art = {}; await loadPolicies(); render(); loadCodeSug();
  });
}

/* ---------- setting up a service, one step at a time ---------- */
const WIZ = ["Describe", "Billing codes", "Policies", "Key facts", "Go live"];
function wizBar(cur, done, clickable) {
  return `<div class="wiz" role="list" aria-label="Setup steps">${WIZ.map((l, i) => { const n = i + 1, on = n === cur, ok = done.includes(n);
    return `<button class="wizstep ${on ? "on" : ""} ${ok ? "done" : ""}" role="listitem" ${on ? 'aria-current="step"' : ""} ${clickable && n > 1 ? `data-step="${n}"` : "disabled"}><span class="wizdot">${ok && !on ? "✓" : n}</span><span class="wiztxt">${l}</span></button>`; }).join("")}</div>`;
}
/* Where a service stands: which steps are finished. */
function wizDone(s) {
  const ok = [1];
  if (s.codes.length) ok.push(2);
  if (s.policies.some((p) => p.rules > 0)) ok.push(3);
  if (s.facts.length) ok.push(4);
  if (s.status !== "planned") ok.push(5);
  return ok;
}
function wizStart(s) {
  if (s.status !== "planned") return 5;
  const ok = wizDone(s);
  return [2, 3, 4].find((n) => !ok.includes(n)) || 5;
}

function newServiceHtml() {
  const n = S.pol.newSvc;
  return `<div class="page" style="display:grid;gap:18px;max-width:760px">
    <div class="page-head"><div><button class="btn small ghost" id="nscancel" style="margin-left:-8px">${ic("left", 16)}Services</button><h1 style="margin-top:4px">New service</h1><p>A service is one kind of request, such as acute back pain.</p></div></div>
    ${wizBar(1, [], false)}
    <div class="card" style="display:grid;gap:14px">
      <div><h3 style="margin:0">Describe the service</h3><p class="muted" style="margin:2px 0 0">Say what this service covers. You add its billing codes and policies on the next steps.</p></div>
      <div class="field" style="margin:0"><label for="nsname">Name</label><input id="nsname" type="text" placeholder="Allergen immunotherapy" value="${esc(n.name)}" autofocus></div>
      <div class="field" style="margin:0"><label for="nsscope">What requests does it cover? (one sentence)</label><textarea id="nsscope" style="min-height:64px" placeholder="Allergy shots and prepared allergen extracts for adults with confirmed allergies. It does not cover allergy testing.">${esc(n.scope)}</textarea></div>
      ${n.code ? `<div class="faint" style="font-size:12.5px">First billing code, from the request that arrived: <b>${esc(n.code)}</b>. ${esc(n.source)}</div>` : ""}</div>
    <div class="wizbar"><button class="btn" id="nscancel2">Cancel</button><button class="btn primary" id="nscreate" ${n.name.trim() ? "" : "disabled"}>Next: billing codes</button></div></div>`;
}

function serviceHtml() {
  const s = S.pol.svc;
  if (!s) return `<div class="page"><div class="empty">Loading…</div></div>`;
  const st = SVC_STATUS[s.status] || SVC_STATUS.live, locked = s.status === "live", sv = S.pol.sv, step = S.pol.step || wizStart(s);
  const done = wizDone(s), ready = { codes: done.includes(2), pol: done.includes(3), facts: done.includes(4) };
  const missing = [!ready.codes && "a billing code", !ready.pol && "a policy with approved rules", !ready.facts && "key facts"].filter(Boolean);
  const btn = (to, label, cls, off) => `<button class="btn ${cls || ""}" data-svstatus="${to}" ${off ? "disabled" : ""}>${label}</button>`;
  const acts = s.status === "planned" ? btn("pilot", "Start the pilot", "primary", missing.length > 0) : s.status === "pilot" ? btn("live", "Make it live", "primary") + " " + btn("planned", "Back to planned") : btn("pilot", "Pause (back to pilot)");
  const confirm = sv.open ? `<div class="card" style="border-color:var(--line2);display:grid;gap:8px;max-width:640px"><b>Move ${esc(s.short)} from ${esc(s.status)} to ${esc(sv.open)}</b>
      <div class="field" style="margin:0"><label for="svnote">${sv.open === "live" ? "What did the pilot show? (required)" : "Note (optional)"}</label><textarea id="svnote" style="min-height:56px" placeholder="${sv.open === "live" ? "For example: ran 3 weeks, nurses agreed with the recommendation on 28 of 30 requests" : ""}">${esc(sv.note)}</textarea></div>
      <div style="display:flex;gap:8px"><button class="btn primary small" data-svgo>Confirm</button><button class="btn small" data-svcancel>Cancel</button></div></div>` : "";
  const lockNote = locked ? `<div class="banner">This service is live. To change its codes or policies, pause it back to pilot first.</div>` : "";

  const codes = s.codes.map((c) => { const x = c.source;
    return `<tr><td style="width:90px"><b>${esc(c.code)}</b></td><td>${x && x.description ? more(x.description, 80) : `<span class="faint">No description</span>`}
      ${small(x && x.sources && x.sources.length ? "CMS: " + x.sources.slice(0, 2).map((z) => `<a href="${esc(z.url)}" target="_blank" rel="noopener">${esc(z.article)}</a>`).join(" · ") + (x.sources.length > 2 ? ` · +${x.sources.length - 2} more` : "") : x && x.note ? esc(x.note) : "<b>No source on file. Check before use.</b>")}</td>
      <td style="text-align:right">${locked ? "" : `<button class="btn small ghost" data-codedel="${esc(c.code)}">Remove</button>`}</td></tr>`; }).join("");
  const pols = s.policies.map((p) => `<tr><td><b>${esc(p.title)}</b>${small(esc(p.id) + " · " + esc(LEVEL[p.level] || p.level))}</td>
      <td>${p.verified ? `<span class="chip ok">Approved</span>` : `<span class="chip plain">Placeholder</span>`}<div class="faint" style="font-size:12.5px;margin-top:3px">${p.verified ? p.rules + " rules" + (p.waiting ? ", " + p.waiting + " waiting" : "") : "No rules yet"}</div></td>
      <td style="text-align:right;white-space:nowrap">${p.build ? `<button class="btn small ${p.build.status === "draft" ? "primary" : ""}" data-pbuild="${esc(p.build.id)}">${p.build.status === "draft" ? "Review rules" : "Rules and quotes"}</button> ` : ""}${p.url && p.url.startsWith("http") ? `<a class="btn small ghost" href="${esc(p.url)}" target="_blank" rel="noopener">Source</a> ` : ""}${locked ? "" : `<button class="btn small ghost" data-poldel="${esc(p.id)}">Remove</button>`}</td></tr>`).join("");
  const drafts = s.drafts.map((d) => { const run = d.status === "running", err = d.status === "error";
    return `<tr><td><b>${esc(d.policy_id || d.ident)}</b>${small(esc((d.kind || "").toUpperCase()))}</td><td><span class="chip ${err ? "bad" : run ? "new" : "warn"}">${err ? "Failed" : run ? esc(d.stage || "Building") : "Ready for your review"}</span></td>
      <td style="text-align:right"><button class="btn small ${run || err ? "" : "primary"}" data-pbuild="${esc(d.id)}">${run || err ? "Open" : "Review"}</button></td></tr>`; }).join("");
  const facts = s.facts.map((f) => `<tr><td><b>${esc(f.label)}</b></td><td>${esc(f.ask || "")}</td><td class="faint" style="font-size:12.5px">${f.used_by.length ? f.used_by.map(esc).join(", ") : "Not used by a rule yet"}</td></tr>`).join("");
  const act = s.activity.length ? s.activity.map((r) => `<tr><td class="faint" style="font-size:12.5px;white-space:nowrap">${esc(fullTime(r.at))}</td><td>${esc(r.who || "")}</td><td><span class="chip ${AUDIT_CHIP[r.action] || "plain"}">${esc(AUDIT_WORDS[r.action] || r.action)}</span></td><td class="faint" style="font-size:12.5px">${esc(r.detail || "")}</td></tr>`).join("") : "";
  const f = S.pol.form, up = f.source === "pdf";
  const sec = (title, sub, body) => `<div class="card"><div><h3 style="margin:0">${title}</h3>${sub ? `<p class="muted" style="margin:2px 0 0">${sub}</p>` : ""}</div><div style="margin-top:12px">${body}</div></div>`;
  const row = (ok, label, detail) => `<div style="display:flex;gap:10px;align-items:center;padding:8px 0;border-bottom:1px solid var(--line)"><span class="chip ${ok ? "ok" : "plain"}">${ok ? "Done" : "Missing"}</span><b>${label}</b><span class="faint">${detail}</span></div>`;

  let body = "", why = "";
  if (step === 2) {
    why = !ready.codes ? "Add at least one billing code to continue." : "";
    body = sec("Billing codes", "A request reaches this service through the billing code on it. A code can belong to one service.",
      `${codes ? `<div class="tbl"><table><tbody>${codes}</tbody></table></div>` : `<div class="faint">No billing codes yet.</div>`}
       ${s.other_codes ? small("CMS lists " + s.other_codes + " more related codes that are not turned on.", "margin-top:6px") : ""}
       ${locked ? "" : `<div style="margin-top:14px"><div class="field" style="margin:0;max-width:520px"><label for="csq">Find billing codes</label><input id="csq" type="search" placeholder="Search by words, for example lumbar or sleep apnea" value="${esc(S.pol.cs.q)}"></div>
        <div id="csbox">${codeSugHtml()}</div>
        <details class="more" style="margin-top:10px"><summary><u>Add a code CMS did not list</u></summary>
         <div style="display:grid;grid-template-columns:130px minmax(0,1fr) auto;gap:8px;margin-top:8px;align-items:end">
          <div class="field" style="margin:0"><label for="ccode">Billing code</label><input id="ccode" type="text" placeholder="72148" value="${esc(S.pol.code.code)}"></div>
          <div class="field" style="margin:0"><label for="csrc">Where did this code come from?</label><input id="csrc" type="text" placeholder="For example: the plan's own policy, page 3" value="${esc(S.pol.code.source)}"></div>
          <button class="btn small" id="cadd">Add code</button></div></details></div>`}`);
  } else if (step === 3) {
    why = !ready.pol ? (s.drafts.some((d) => d.status === "draft") ? "Review the draft policy to continue." : "Add a policy and approve its rules to continue.") : "";
    body = sec("Policies", "The policies a nurse checks a request against. The system builds each one from its official text. You review every rule.",
      `${pols || drafts ? `<div class="tbl"><table><tbody>${pols}${drafts}</tbody></table></div>` : `<div class="faint">No policies yet.</div>`}
       ${locked ? "" : `<div style="margin-top:14px"><div class="field" style="margin:0;max-width:520px"><label for="sugq">Find a policy</label><input id="sugq" type="search" placeholder="Search CMS by title or number, for example acupuncture or 30.3.3" value="${esc(S.pol.q)}"></div>
        <div id="sugbox">${sugHtml()}</div>
        <details class="more" style="margin-top:10px" ${S.pol.more ? "open" : ""} id="moredet"><summary><u>Add a federal regulation, or upload a policy PDF</u></summary>
          <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin-top:8px">
            <div class="field" style="margin:0"><label for="psrc">Source</label><select id="psrc"><option value="cfr" ${up ? "" : "selected"}>Federal regulation (eCFR)</option><option value="pdf" ${up ? "selected" : ""}>Upload a policy PDF</option></select></div>
            ${up ? `<div class="field" style="margin:0"><label for="ppid">Policy id</label><input id="ppid" type="text" placeholder="HUM-BACK-2026" value="${esc(f.pid)}"></div><div class="field" style="margin:0"><label for="ptitle">Title</label><input id="ptitle" type="text" value="${esc(f.title)}"></div>
              <div class="field" style="margin:0"><label for="plevel">What kind of policy is it?</label><select id="plevel"><option value="HUMANA_INTERNAL" ${f.level === "HUMANA_INTERNAL" ? "selected" : ""}>Humana policy</option><option value="MCG" ${f.level === "MCG" ? "selected" : ""}>MCG guideline</option><option value="LCD" ${f.level === "LCD" ? "selected" : ""}>Local coverage (LCD)</option><option value="NCD" ${f.level === "NCD" ? "selected" : ""}>National coverage (NCD)</option></select></div>
              <div class="field" style="margin:0"><label for="pfile">PDF file</label><input id="pfile" type="file" accept="application/pdf"></div>`
            : `<div class="field" style="margin:0"><label for="pid">Regulation</label><input id="pid" type="text" placeholder="42 CFR 412.3" value="${esc(f.ident)}"></div>`}</div>
          <div style="margin-top:10px"><button class="btn small primary" id="pgo" ${S.pol.busy ? "disabled" : ""}>${S.pol.busy ? "Starting…" : "Build this policy"}</button></div></details></div>`}`);
  } else if (step === 4) {
    why = !ready.facts ? "Key facts appear when you approve a policy. Go back to the policies step." : "";
    body = sec("Key facts", "The things the AI reader finds in a packet to check the rules. They come from the policies you approved and are combined here. To change one, change the policy.",
      facts ? `<div class="tbl"><table><thead><tr><th>Key fact</th><th>Question to the provider if it is missing</th><th>Checked by</th></tr></thead><tbody>${facts}</tbody></table></div>` : `<div class="faint">None yet.</div>`);
  } else {
    body = sec("Go live", s.status === "planned" ? "Check that the service is ready, then start the pilot. In a pilot, a nurse checks every recommendation." : SVC_STATUS_HELP[s.status] + (s.note ? " Note: " + esc(s.note) : ""),
      `<div style="max-width:680px">${row(ready.codes, "Billing codes", s.codes.length + " added")}${row(ready.pol, "Policies", s.policies.filter((p) => p.rules > 0).length + " with approved rules")}${row(ready.facts, "Key facts", s.facts.length + " found in the policies")}</div>
       <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-top:14px">${acts}${s.status === "planned" && missing.length ? small("Before the pilot, add " + missing.join(", ") + ".") : ""}</div>
       ${confirm ? `<div style="margin-top:12px">${confirm}</div>` : ""}`)
      + (act ? sec("Activity", "", `<div class="tbl"><table><tbody>${act}</tbody></table></div>`) : "");
  }
  const picked = Object.keys(S.pol.cs.picked).length;
  const nav = step < 5 ? `<div class="wizbar"><button class="btn" data-stepto="${step - 1 < 2 ? 0 : step - 1}">${step === 2 ? "Back to services" : "Back"}</button>
      <div style="display:flex;gap:10px;align-items:center"><span id="stepwhy">${step === 2 && picked ? "" : why && !locked ? small(esc(why)) : ""}</span>${step === 2 ? `<button class="btn primary" id="csnext" data-has="${ready.codes ? 1 : 0}" ${!picked && why && !locked ? "disabled" : ""}>${picked ? "Add " + picked + " code" + (picked > 1 ? "s" : "") + " and continue" : "Next: " + WIZ[step].toLowerCase()}</button>` : `<button class="btn primary" data-stepto="${step + 1}" ${why && !locked ? "disabled" : ""}>Next: ${WIZ[step].toLowerCase()}</button>`}</div></div>`
    : `<div class="wizbar"><button class="btn" data-stepto="4">Back</button><button class="btn" data-stepto="0">Done, back to services</button></div>`;

  return `<div class="page" style="display:grid;gap:16px;max-width:1080px">
    <div class="page-head"><div><button class="btn small ghost" data-psvcback style="margin-left:-8px">${ic("left", 16)}Services</button>
      <h1 style="margin-top:4px">${esc(s.short)} <span class="chip ${st[1]}" style="vertical-align:middle">${st[0]}</span></h1>
      <p>${esc(s.scope || s.name)}</p></div></div>
    ${S.pol.msg ? `<div class="banner">${esc(S.pol.msg)}</div>` : ""}
    ${wizBar(step, done, true)}
    ${lockNote}
    ${body}
    ${nav}</div>`;
}

const polServicesHtml = () => {
  const d = S.pol.data;
  if (!d) return `<div class="page"><div class="empty">Loading…</div></div>`;
  return S.pol.svcKey ? serviceHtml() : polServicesList();
};

/* ---------- policies: the catalog ---------- */
function polLibraryHtml() {
  const d = S.pol.data;
  if (!d) return `<div class="page"><div class="empty">Loading the library…</div></div>`;
  const rows = d.policies.map((p) => {
    const t = polTarget(p.id), ck = S.pol.check[p.id];
    return `<tr><td><b>${esc(p.title)}</b>${small(esc(p.id) + " · " + esc(LEVEL[p.level] || p.level) + (p.verified ? "" : " · placeholder"))}</td>
      <td>${p.criteria}${p.waiting ? small("+ " + p.waiting + " waiting") : ""}</td><td>${p.n_facts || "-"}</td>
      <td class="faint" style="font-size:12.5px">${p.services.length ? esc(p.services.join(", ")) : "No service yet"}</td>
      <td style="white-space:nowrap">${ck ? `<span class="chip ${ck.changed ? "warn" : ck.changed === false ? "ok" : "plain"}" title="${esc(ck.note)}">${ck.changed ? "CMS text changed" : ck.changed === false ? "No change since last review" : "No earlier copy"}</span> ` : ""}
        ${t ? `<button class="btn small" data-pcheck="${esc(p.id)}">Check CMS for changes</button> <button class="btn small" data-pupdate="${esc(p.id)}">Update from CMS</button>` : `<span class="faint" style="font-size:12.5px">No online source. Upload a new PDF on a service.</span>`}</td></tr>`;
  }).join("");
  const open = d.builds.filter((b) => b.status !== "published");
  const drows = open.map((b) => {
    const st = b.status === "draft" ? ["Ready for your review", "warn"] : b.status === "error" ? ["Failed", "bad"] : [b.stage || "Building", "new"];
    return `<tr><td><b>${esc(b.policy_id || b.ident)}</b>${small(esc(b.kind === "earlier run" ? "earlier run" : b.kind.toUpperCase()) + (b.version ? " · " + esc(b.version) : "") + (b.service ? " · for " + esc((d.services.find((x) => x.key === b.service) || {}).name || b.service) : ""))}</td>
      <td><span class="chip ${st[1]}">${esc(st[0])}</span></td>
      <td>${b.total ? `<div>${b.decided} of ${b.total} rules decided</div><div class="bar"><i style="width:${Math.round((100 * b.decided) / b.total)}%"></i></div>` : "-"}</td>
      <td class="faint" style="font-size:12.5px">${esc(b.who || "")} · ${when(b.created_at)}</td>
      <td><button class="btn small ${b.status === "draft" ? "primary" : ""}" data-pbuild="${esc(b.id)}">${b.status === "draft" ? "Review" : "Open"}</button></td></tr>`;
  }).join("");
  return `<div class="page" style="display:grid;gap:22px;max-width:1180px">
    <div class="page-head"><div><h1>Policies</h1><p>Every policy the system knows, shared by the services that use it. To add a policy, open a service and add it there.</p></div>
      <div class="stat" style="margin:0"><div><b>${esc(d.version)}</b><span>live library version</span></div></div></div>
    ${S.pol.msg ? `<div class="banner">${esc(S.pol.msg)}</div>` : ""}
    ${open.length ? `<div><h3 style="margin:0 0 8px">Drafts in progress</h3><div class="tbl"><table><thead><tr><th>Policy</th><th>Status</th><th>Your progress</th><th>Started</th><th></th></tr></thead><tbody>${drows}</tbody></table></div></div>` : ""}
    <div><h3 style="margin:0 0 8px">Approved policies</h3><div class="tbl"><table><thead><tr><th>Policy</th><th>Rules</th><th>Key facts</th><th>Used by</th><th>CMS</th></tr></thead><tbody>${rows}</tbody></table></div>
      <p class="faint" style="font-size:12.5px;margin:8px 0 0">Updating from CMS builds a new draft. Nothing changes until you approve it. Key facts are listed here only for policies approved in the new flow.</p></div></div>`;
}

function polHistoryHtml() {
  const a = S.pol.audit, d = S.pol.data;
  if (!a || !d) return `<div class="page"><div class="empty">Loading…</div></div>`;
  const vers = a.versions.length ? a.versions.map((v) => `<tr><td><b>${esc(v.version)}</b> <span class="chip ${v.kind === "revert" ? "warn" : v.kind === "service" ? "plain" : "ok"}">${v.kind === "revert" ? "Went back" : v.kind === "service" ? "Service" : "Policy approved"}</span></td>
      <td>${esc(v.policy_id || "")}</td><td class="faint" style="font-size:12.5px">${v.changelog ? `${v.changelog.approved} rules approved${v.changelog.waiting ? " (" + v.changelog.waiting + " waiting for a key fact)" : ""}, ${v.changelog.rejected} rejected. ${v.changelog.added.length} new, ${v.changelog.removed.length} removed, ${v.changelog.unchanged} unchanged.${v.note ? " Note: " + esc(v.note) : ""}` : esc(v.note || "")}</td>
      <td class="faint" style="font-size:12.5px">${esc(v.who || "")}<div>${esc(fullTime(v.at))}</div></td>
      <td style="white-space:nowrap">${v.build_id ? `<button class="btn small" data-pbuild="${esc(v.build_id)}">See what was approved</button> ` : ""}${S.pol.revert === v.version ? `<button class="btn small danger" data-prevert-go="${esc(v.version)}">Confirm: go back to ${esc(v.version)}</button>` : v.version !== a.version ? `<button class="btn small" data-prevert="${esc(v.version)}">Go back to this</button>` : `<span class="chip ok">Live</span>`}</td></tr>`).join("")
    : `<tr><td colspan="5" class="faint">Nothing approved yet. The live library is the one that shipped with the app.</td></tr>`;
  const log = a.rows.length ? a.rows.map((r) => `<tr><td class="faint" style="font-size:12.5px;white-space:nowrap">${esc(fullTime(r.at))}</td><td>${esc(r.who || "")}</td><td><span class="chip ${AUDIT_CHIP[r.action] || "plain"}">${esc(AUDIT_WORDS[r.action] || r.action)}</span></td><td>${esc(r.policy_id || "")}</td><td class="faint" style="font-size:12.5px">${esc(r.detail || "")}</td></tr>`).join("")
    : `<tr><td colspan="5" class="faint">No activity yet.</td></tr>`;
  return `<div class="page" style="display:grid;gap:22px;max-width:1180px">
    <div class="page-head"><div><h1>Version history</h1><p>Every version of the policy library, and a record of everything done to it. Nothing here can be changed or deleted.</p></div>
      <div class="stat" style="margin:0"><div><b>${esc(a.version)}</b><span>live library version</span></div></div></div>
    ${S.pol.msg ? `<div class="banner">${esc(S.pol.msg)}</div>` : ""}
    <div><h3 style="margin:0 0 8px">Library versions</h3><div class="tbl"><table><thead><tr><th>Version</th><th>Policy</th><th>What changed</th><th>By</th><th></th></tr></thead><tbody>${vers}</tbody></table></div></div>
    <div><h3 style="margin:0 0 8px">Activity</h3><div class="tbl"><table><thead><tr><th>When</th><th>Who</th><th>What</th><th>Policy</th><th>Detail</th></tr></thead><tbody>${log}</tbody></table></div></div></div>`;
}

/* ---------- requests without a policy ---------- */
function polDemandHtml() {
  const d = S.pol.data, dm = S.pol.demand;
  if (!d || !dm) return `<div class="page"><div class="empty">Loading…</div></div>`;
  const rows = dm.rows.map((g) => `<tr><td><b>${esc(g.code)}</b></td><td>${esc(g.what || "")}</td><td><b>${g.n}</b></td><td class="faint" style="font-size:12.5px">${esc(when(g.oldest))}</td><td class="faint" style="font-size:12.5px">${g.cases.map(esc).join(", ")}</td>
      <td>${g.service ? (g.service_status === "planned" ? `<span class="chip plain">Planned: ${esc(g.service)}</span>` : `<span class="chip ok">Now covered by ${esc(g.service)} (${esc(g.service_status)})</span>${small("A nurse checks these requests again")}`) : `<button class="btn small primary" data-svprefill="${esc(g.code)}" data-svwhat="${esc(g.what || "")}" data-svn="${g.n}">Start a service</button>`}</td></tr>`).join("");
  return `<div class="page" style="display:grid;gap:18px;max-width:1180px">
    <div class="page-head"><div><h1>Requests without a policy</h1><p>Open requests for a service we do not cover yet. The packet could not be checked. The billing codes that come in most often are the next services to build.</p></div></div>
    <div class="tbl"><table><thead><tr><th>Billing code</th><th>What was requested</th><th>Requests waiting</th><th>Oldest</th><th>Cases</th><th></th></tr></thead><tbody>${rows || `<tr><td colspan="6" class="faint">Nothing waiting. Every open request has a policy.</td></tr>`}</tbody></table></div>
    <p class="faint" style="font-size:12.5px;margin:0">After a service is built, a nurse opens each waiting request and clicks "Check again with the current policies".</p></div>`;
}

/* ---------- one draft policy ---------- */
const BUILD_STEPS = [
  ["Getting the policy", "Getting the policy", "From the official source, or your PDF"],
  ["Reading the policy", "Reading the policy", "Turning every page into text, with its sections"],
  ["Drafting the rules", "Drafting the rules", "Writing each rule with the exact sentence it comes from"],
  ["Checking every rule", "Checking every rule", "Every quote and number is checked against the policy text"],
  ["Comparing with the live rules", "Comparing with the live rules", "What is the same, different or new"],
];
const escRe = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
function sourceHtml(b) {
  const sel = b.criteria.find((c) => c.id === S.pol.sel);
  const pieces = sel ? sel.source_quote.split(/\.\.\.|…/).map((p) => p.trim()).filter((p) => p.length > 7) : [];
  const res = pieces.map((p) => new RegExp(p.split(/\s+/).map(escRe).join("\\s+"), "i"));
  return b.elements.map((e) => {
    const t = e.text;
    let hit = [];
    res.forEach((re) => { const m = re.exec(t); if (m) hit.push([m.index, m.index + m[0].length]); });
    hit.sort((a, c) => a[0] - c[0]);
    let out = "", pos = 0;
    hit.forEach(([s, en]) => { if (s >= pos) { out += esc(t.slice(pos, s)) + `<mark data-hit>${esc(t.slice(s, en))}</mark>`; pos = en; } });
    out += esc(t.slice(pos));
    const title = /Title|Header/.test(e.type);
    return `<div class="src-el ${title ? "src-title" : ""}"${hit.length ? ' data-hit-el="1"' : ""}>${out}</div>`;
  }).join("");
}

function ruleHtml(c, b) {
  const open = S.pol.edit === c.id, sel = S.pol.sel === c.id;
  const chk = { pass: ["Matches the policy text", "ok"], review: ["Check this one", "warn"], fail: ["Does not match the policy text", "bad"] }[c.check];
  const dec = { approved: ["Approved", "ok"], rejected: ["Rejected", "bad"], pending: ["Needs your decision", "plain"] }[c.decision];
  const v = Array.isArray(c.test.value) ? c.test.value.join(", ") : c.test.value ?? "";
  const canEditValue = ["gte", "lte", "in"].includes(c.test.type);
  return `<div class="card rule ${sel ? "sel" : ""}" data-psel="${esc(c.id)}">
    <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;justify-content:space-between"><div><b>${esc(c.id)}</b> <span class="faint" style="font-size:12.5px">${esc(c.cite)}</span></div>
      <div style="display:flex;gap:6px;flex-wrap:wrap"><span class="chip ${chk[1]}">${chk[0]}</span><span class="chip ${c.confidence === "high" ? "ok" : "warn"}">AI confidence: ${esc(c.confidence)}</span><span class="chip ${dec[1]}">${dec[0]}${c.edited ? " · edited" : ""}</span></div></div>
    <p style="margin:8px 0 4px">${esc(c.text)}</p>
    <div class="quote">${more(c.source_quote, 260)}</div>
    <div class="faint" style="font-size:12.5px;margin-top:6px">The check: ${testText(c)}${c.applies_if ? ` · only when ${esc(String(c.applies_if.fact).replace(/_/g, " "))} is ${esc(c.applies_if.equals)}` : ""}</div>
    ${c.if_missing ? `<div class="faint" style="font-size:12.5px">If it is missing, ask: ${esc(c.if_missing.replace(/^Ask:\s*/, ""))}</div>` : ""}
    ${c.issues.length ? `<div class="banner" style="margin-top:8px">${esc(c.issues.join(" · "))}</div>` : ""}
    ${c.waiting ? `<div class="banner" style="margin-top:8px">${esc(c.waiting)}</div>` : ""}
    ${c.blocked ? `<div class="banner" style="margin-top:8px;border-color:var(--bad);color:var(--bad)">${esc(c.blocked)}</div>` : ""}
    ${open ? `<div style="display:grid;gap:8px;margin-top:10px;padding-top:10px;border-top:1px dashed var(--line2)">
      <div class="field" style="margin:0"><label>Rule in plain words</label><textarea id="ed-text" style="min-height:56px">${esc(c.text)}</textarea></div>
      ${canEditValue ? `<div class="field" style="margin:0"><label>${c.test.type === "in" ? "Allowed values, separated by commas" : "Threshold (" + esc(TEST_WORDS[c.test.type]) + ")"}</label><input id="ed-val" type="text" value="${esc(v)}"></div>` : ""}
      <div class="field" style="margin:0"><label>Question for the provider if it is missing</label><textarea id="ed-miss" style="min-height:52px">${esc(c.if_missing || "")}</textarea></div>
      <div style="display:flex;gap:8px"><button class="btn small primary" data-psave="${esc(c.id)}">Save and approve</button><button class="btn small" data-pedit="">Cancel</button></div></div>`
    : `<div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:10px">
      ${b.status === "draft" ? `<button class="btn small approve ${c.decision === "approved" ? "" : "outline"}" data-pdec="approved" data-pcid="${esc(c.id)}" ${c.blocked ? "disabled" : ""}>Approve</button>
      <button class="btn small danger ${c.decision === "rejected" ? "" : "outline"}" data-pdec="rejected" data-pcid="${esc(c.id)}">Reject</button>
      <button class="btn small" data-pedit="${esc(c.id)}" ${c.blocked ? "disabled" : ""}>Edit</button>
      ${c.decision !== "pending" ? `<button class="btn small ghost" data-pdec="pending" data-pcid="${esc(c.id)}">Undo</button>` : ""}` : ""}
      <button class="btn small ghost" data-psel="${esc(c.id)}">Show in the source</button></div>`}
  </div>`;
}

/* Key facts the approved rules need that the service does not have yet. They are saved on the policy when you approve. */
function newFacts(b) {
  const s = b.services.find((x) => x.key === b.service_ctx);
  if (!s) return [];
  const have = {}; (b.new_facts || []).forEach((f) => (have[f.key] = f));
  const need = [];
  b.criteria.filter((c) => c.decision !== "rejected").forEach((c) => [c.required_fact, c.applies_if && c.applies_if.fact].forEach((k) => { if (k && have[k] && !s.fact_keys.includes(k) && !need.some((f) => f.key === k)) need.push(have[k]); }));
  return need;
}

function approveHtml(b, t) {
  const svc = b.service_ctx_name, nf = newFacts(b), live = b.service_ctx_status === "live";
  const ready = b.status === "draft" && t.pending === 0 && t.approved > 0 && S.pol.confirm && !(live && nf.length);
  const rows = nf.map((f) => `<tr><td><b>${esc(f.label)}</b></td><td><input type="text" data-pask="${esc(f.key)}" value="${esc(S.pol.asks[f.key] ?? f.ask)}" aria-label="Question about ${esc(f.label)}"></td></tr>`).join("");
  return `<div class="card"><h3 style="margin:0 0 4px">${svc ? "Approve for " + esc(svc) : "Approve this version"}</h3>
    ${nf.length ? `<div style="margin:8px 0 12px"><b style="font-size:13.5px">${nf.length} new key fact${nf.length > 1 ? "s" : ""} for ${esc(svc)}</b>
      ${small("The approved rules need these. The AI reader will look for them in every packet. Change a question if it is unclear.", "margin-bottom:6px")}
      ${live ? `<div class="banner">${esc(svc)} is live, so it cannot take new key facts. Pause it back to pilot first.</div>` : `<div class="tbl"><table><thead><tr><th>Key fact</th><th>Question to the provider if it is missing</th></tr></thead><tbody>${rows}</tbody></table></div>`}</div>` : ""}
    ${(b.used_by || []).filter((n) => n !== svc).length ? `<div class="banner" style="margin-bottom:10px">This policy is also used by ${b.used_by.filter((n) => n !== svc).map(esc).join(", ")}. Approving changes their rules too.</div>` : ""}
    <p class="muted" style="margin:0 0 10px">${svc ? `This adds the approved rules to ${esc(svc)}.` : (b.used_by && b.used_by.length ? "This policy is used by " + b.used_by.map(esc).join(", ") + "." : "No service uses this policy yet. Open a service and add it there.")} It makes a new version of the policy library. New requests are checked against it from that moment. Requests already in progress keep their recommendation. You can go back to the previous version at any time.</p>
    <label style="display:flex;gap:8px;align-items:flex-start;margin-bottom:10px"><input type="checkbox" id="pconf" ${S.pol.confirm ? "checked" : ""} style="margin-top:3px"><span>I reviewed every rule and I understand this changes how new requests are checked.</span></label>
    ${b.waiting_approved ? `<p class="faint" style="margin:0 0 10px;font-size:12.5px">${b.waiting_approved} approved rule(s) are saved but wait for a key fact no service has yet. They change nothing until a service has it.</p>` : ""}
    <div class="field" style="margin:0 0 12px"><label for="pnote">Note for the history (optional)</label><input id="pnote" type="text" value="${esc(S.pol.note)}" placeholder="Why this change"></div>
    <button class="btn primary" id="ppub" ${ready ? "" : "disabled"}>${svc ? "Approve for " + esc(svc) : "Approve a new version"}</button>
    <span class="faint" style="margin-left:10px;font-size:12.5px">${t.pending ? t.pending + " rule(s) still need a decision." : t.approved ? "" : "Approve at least one rule."}</span></div>`;
}

function polBuildHtml() {
  const b = S.pol.build;
  const back = b.service_ctx_name ? b.service_ctx_name : S.view === "services" && S.pol.svc ? S.pol.svc.short : S.view === "history" ? "Version history" : "Policies";
  const head = (inner) => `<div class="page" style="max-width:1260px"><div class="page-head"><div><button class="btn small ghost" data-pback style="margin-left:-8px">${ic("left", 16)}${esc(back)}</button><h1 style="margin-top:4px">${inner}</h1></div></div>`;
  if (b.status === "running") {
    const cur = Math.max(0, BUILD_STEPS.findIndex((s) => s[0] === b.stage));
    return head(esc(b.ident || "Draft")) + `<div class="card" style="max-width:560px"><h3 style="margin:0 0 2px">Building the policy</h3><div class="faint" style="margin:0 0 10px">${esc(b.ident || "")}</div>
      ${BUILD_STEPS.map(([k, t, sub], i) => `<div class="step ${i < cur ? "done" : i === cur ? "now" : "todo"}"><span class="dot">${i < cur ? ic("check", 14) : ""}</span><div><b>${t}</b>${sub}</div></div>`).join("")}
      <div class="faint" style="margin-top:12px;font-size:12.5px">This usually takes about a minute. You can leave this page. The draft waits for you on the service page.</div></div></div>`;
  }
  if (b.status === "error") return head(esc(b.ident || "Draft")) + `<div class="banner" style="border-color:var(--bad);color:var(--bad)">The policy could not be built. ${esc(b.error || "")}</div></div>`;
  const m = b.meta, t = b.tally, n = b.criteria.length;
  const cr = b.change_report;
  const crRows = cr ? cr.rows.map((r) => `<tr><td>${esc(r.id)}</td><td>${esc((r.fact || "").replace(/_/g, " "))}</td><td>${esc(r.approved || "")}</td><td>${esc(r.draft || "")}</td><td><span class="chip ${r.result === "same" ? "ok" : r.result === "differs" ? "warn" : r.result === "missed" ? "bad" : "plain"}">${r.result === "same" ? "Same" : r.result === "differs" ? "Different" : r.result === "missed" ? "Not in the new version" : "Information"}</span></td></tr>`).join("") : "";
  return head(esc(m.title)) + `<p class="muted" style="margin:-8px 0 14px">${esc(m.policy_id)} · ${esc(LEVEL[m.level] || m.level)} · ${esc(m.source)} ${esc(m.version)}${m.effective ? " · effective " + esc(m.effective) : ""}${m.url && m.url.startsWith("http") ? ` · <a href="${esc(m.url)}" target="_blank" rel="noopener">official source</a>` : ""}</p>
    ${b.status === "published" ? `<div class="banner" style="border-color:var(--ok);color:var(--ok)">This policy was approved. These are its rules and the exact quotes they come from. To change a rule, update the policy from CMS. That makes a new draft you can approve or reject again.</div>` : ""}
    ${S.pol.msg ? `<div class="banner">${esc(S.pol.msg)}</div>` : ""}
    <div class="stat" style="margin-bottom:14px"><div><b>${n}</b><span>rules the AI drafted</span></div><div><b>${b.counts.pass} / ${b.counts.review} / ${b.counts.fail}</b><span>automatic checks: matched / check / failed</span></div>
      <div><b>${t.approved} · ${t.rejected} · ${t.pending}</b><span>your decisions: approved · rejected · waiting</span></div>${cr ? `<div><b>${cr.counts.same} of ${cr.approved_count}</b><span>live rules the new version matches exactly</span></div>` : ""}</div>
    <div class="pol-grid"><div class="srcpane"><h4 style="margin:0 0 8px;font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--ink3)">The official text</h4><div id="srcbody">${sourceHtml(b)}</div></div>
      <div style="display:grid;gap:12px;align-content:start">${b.criteria.map((c) => ruleHtml(c, b)).join("")}</div></div>
    <div style="display:grid;gap:16px;margin-top:20px">
      ${b.not_modeled.length ? `<div class="card"><h3 style="margin:0 0 4px">Left for a person (${b.not_modeled.length})</h3><p class="muted" style="margin:0 0 8px">Parts of the policy the AI did not turn into rules, with its reason. A nurse or physician still handles these.</p><ul class="plist">${b.not_modeled.map((x) => `<li>${more(x.quote, 160)}${small(esc(x.why))}</li>`).join("")}</ul></div>` : ""}
      ${b.uncovered.length ? `<div class="card"><h3 style="margin:0 0 4px">Might be missing (${b.uncovered.length})</h3><p class="muted" style="margin:0 0 8px">Sentences that sound like a requirement but have no rule and no note. Check that nothing important is left out.</p><ul class="plist">${b.uncovered.map((x) => `<li>${more(x, 200)}</li>`).join("")}</ul></div>` : ""}
      ${cr ? `<div class="card"><h3 style="margin:0 0 4px">What changes from the live policy</h3><p class="muted" style="margin:0 0 8px">Each live rule, matched by the key fact it checks. ${cr.extra.length ? cr.extra.length + " new rule(s) check key facts the live policy does not check." : "No new rules."}</p><div class="tbl"><table><thead><tr><th>Live rule</th><th>Key fact</th><th>Live threshold</th><th>New threshold</th><th></th></tr></thead><tbody>${crRows}</tbody></table></div></div>` : `<div class="card"><h3 style="margin:0 0 4px">A new policy</h3><p class="muted" style="margin:0">This policy is not in the live library yet, so there is nothing to compare it with.</p></div>`}
      ${b.status === "draft" ? approveHtml(b, t) : ""}</div></div>`;
}

const policyHtml = () => (S.pol.build ? polBuildHtml() : S.view === "history" ? polHistoryHtml() : S.view === "services" ? polServicesHtml() : S.view === "demand" ? polDemandHtml() : polLibraryHtml());

/* ---------- actions ---------- */
function bindSug() {
  const on = (sel, fn) => document.querySelectorAll(sel).forEach((el) => (el.onclick = guard((e) => fn(el, e))));
  on("[data-sugadd]", async (el) => {
    const r = await api(`/policies/services/${S.pol.svcKey}/policies`, { method: "POST", body: { policy_id: el.dataset.sugadd } });
    S.pol.msg = `Policy added with its ${r.rules} approved rules${r.brings.length ? " and " + r.brings.length + " key fact" + (r.brings.length > 1 ? "s" : "") : ""}. Nothing was fetched, read or reviewed again.`; await loadPolicies(); render(); loadSug(); loadCodeSug();
  });
  on("[data-sugbuild]", async (el) => {
    const r = await api("/policies/builds", { method: "POST", body: { kind: el.dataset.sugbuild, ident: el.dataset.sugid, service: S.pol.svcKey } });
    S.pol.msg = null; await openBuild(r.id);
  });
}

function bindPolicy() {
  const on = (sel, fn) => document.querySelectorAll(sel).forEach((el) => (el.onclick = guard((e) => fn(el, e))));
  const val = (id) => (document.getElementById(id) || {}).value;
  const back = async () => { clearInterval(polTimer); const ctx = S.pol.build && (S.pol.build.service_ctx || S.pol.svcKey); S.pol.build = null; S.pol.msg = null; await loadPolicies(); if (ctx && S.view === "services") { S.pol.svcKey = ctx; S.pol.step = 3; S.pol.svc = await api("/policies/services/" + ctx); render(); loadSug(); loadCodeSug(); } else render(); };
  const f = S.pol.form, keepForm = () => { f.source = val("psrc") ?? f.source; f.ident = val("pid") ?? f.ident; f.pid = val("ppid") ?? f.pid; f.title = val("ptitle") ?? f.title; f.level = val("plevel") ?? f.level; };

  /* services list */
  on("[data-psvc]", async (el) => { await openService(el.dataset.psvc); });
  on("#nsopen", () => { S.pol.newSvc.open = true; render(); });
  const closeNew = () => { S.pol.newSvc = { open: false, name: "", scope: "", code: "", source: "" }; render(); window.scrollTo(0, 0); };
  on("#nscancel", closeNew); on("#nscancel2", closeNew);
  const nsn = document.getElementById("nsname"), nss = document.getElementById("nsscope");
  if (nsn) nsn.oninput = () => { S.pol.newSvc.name = nsn.value; const b = document.getElementById("nscreate"); if (b) b.disabled = !nsn.value.trim(); };
  if (nss) nss.oninput = () => (S.pol.newSvc.scope = nss.value);
  on("#nscreate", async () => {
    const n = S.pol.newSvc; if (!n.name.trim()) throw new Error("Give the service a name");
    const r = await api("/policies/services", { method: "POST", body: { name: n.name.trim(), short: shortName(n.name), scope: n.scope, codes: n.code ? [{ code: n.code, source: n.source }] : [] } });
    S.pol.newSvc = { open: false, name: "", scope: "", code: "", source: "" }; await loadPolicies(); await openService(r.key);
  });
  on("[data-svprefill]", async (el) => {
    S.view = "services"; go("#/view/services"); S.pol.svcKey = null; S.pol.svc = null;
    S.pol.newSvc = { open: true, name: el.dataset.svwhat, scope: "", code: el.dataset.svprefill, source: `Seen on ${el.dataset.svn} incoming request(s). Check it against the CMS billing article before use.` };
    await loadPolicies(); render();
  });

  /* one service: the steps */
  on("[data-step]", (el) => { S.pol.step = Number(el.dataset.step); S.pol.msg = null; render(); window.scrollTo(0, 0); });
  on("[data-stepto]", async (el) => {
    const n = Number(el.dataset.stepto);
    if (n === 0) { S.pol.svcKey = null; S.pol.svc = null; S.pol.msg = null; await loadPolicies(); render(); window.scrollTo(0, 0); return; }
    S.pol.step = n; S.pol.msg = null; render(); window.scrollTo(0, 0);
  });
  /* one service */
  on("[data-psvcback]", async () => { S.pol.svcKey = null; S.pol.svc = null; S.pol.msg = null; await loadPolicies(); render(); window.scrollTo(0, 0); });
  on("[data-svstatus]", (el) => { S.pol.sv = { open: el.dataset.svstatus, note: "" }; render(); });
  on("[data-svcancel]", () => { S.pol.sv.open = null; render(); });
  const svn = document.getElementById("svnote"); if (svn) svn.oninput = () => (S.pol.sv.note = svn.value);
  on("[data-svgo]", async () => {
    const r = await api(`/policies/services/${encodeURIComponent(S.pol.svcKey)}/status`, { method: "POST", body: { status: S.pol.sv.open, note: S.pol.sv.note, confirm: true } });
    S.pol.msg = "Service updated. Library version " + r.version + "."; S.pol.sv = { open: null, note: "" }; await loadPolicies(); render();
  });
  const cc = document.getElementById("ccode"), cs = document.getElementById("csrc");
  if (cc) cc.oninput = () => (S.pol.code.code = cc.value);
  if (cs) cs.oninput = () => (S.pol.code.source = cs.value);
  on("#cadd", async () => {
    const r = await api(`/policies/services/${S.pol.svcKey}/codes`, { method: "POST", body: { code: S.pol.code.code, source: S.pol.code.source } });
    S.pol.code = { code: "", source: "" }; S.pol.msg = null; await loadPolicies(); render();
  });
  on("[data-codedel]", async (el) => { await api(`/policies/services/${S.pol.svcKey}/codes/${encodeURIComponent(el.dataset.codedel)}/remove`, { method: "POST" }); await loadPolicies(); render(); });
  on("[data-poldel]", async (el) => { await api(`/policies/services/${S.pol.svcKey}/policies/${encodeURIComponent(el.dataset.poldel)}/remove`, { method: "POST" }); await loadPolicies(); render(); loadSug(); });
  const sq = document.getElementById("sugq");
  if (sq) { let tm; sq.oninput = () => { S.pol.q = sq.value; clearTimeout(tm); tm = setTimeout(guard(loadSug), 250); }; }
  bindSug(); bindCodeSug();
  const cq = document.getElementById("csq");
  if (cq) { let tm; cq.oninput = () => { S.pol.cs.q = cq.value; S.pol.cs.art = {}; clearTimeout(tm); tm = setTimeout(guard(loadCodeSug), 400); }; }
  const psrc = document.getElementById("psrc"); if (psrc) psrc.onchange = () => { keepForm(); S.pol.more = true; render(); };
  ["pid", "ppid", "ptitle", "plevel"].forEach((id) => { const el = document.getElementById(id); if (el) el.onchange = keepForm; });
  on("#pgo", async () => {
    keepForm(); S.pol.busy = true; S.pol.more = true; render();
    try {
      let r;
      if (f.source === "pdf") {
        const file = document.getElementById("pfile").files[0];
        if (!file || !f.pid || !f.title) throw new Error("Add the PDF, a policy id and a title");
        const fd = new FormData(); fd.append("file", file); fd.append("policy_id", f.pid); fd.append("title", f.title); fd.append("level", f.level); fd.append("service", S.pol.svcKey);
        r = await api("/policies/builds/upload", { method: "POST", body: fd });
      } else r = await api("/policies/builds", { method: "POST", body: { kind: "cfr", ident: f.ident, service: S.pol.svcKey } });
      S.pol.busy = null; await openBuild(r.id);
    } catch (e) { S.pol.busy = null; render(); throw e; }
  });

  /* policies and history */
  on("[data-pback]", back);
  on("[data-pbuild]", async (el) => { S.pol.msg = null; await openBuild(el.dataset.pbuild); });
  on("[data-pcheck]", async (el) => { const id = el.dataset.pcheck; el.textContent = "Checking…"; S.pol.check[id] = await api(`/policies/${encodeURIComponent(id)}/check-update`, { method: "POST" }); render(); });
  on("[data-pupdate]", async (el) => { const t = polTarget(el.dataset.pupdate); const r = await api("/policies/builds", { method: "POST", body: { kind: t.kind, ident: t.ident, service: "" } }); await openBuild(r.id); });
  on("[data-prevert]", (el) => { S.pol.revert = el.dataset.prevert; render(); });
  on("[data-prevert-go]", async (el) => { const r = await api("/policies/revert", { method: "POST", body: { version: el.dataset.prevertGo, confirm: true } }); S.pol.revert = null; S.pol.msg = "The live library is back to version " + r.version + "."; await loadPolicies(); render(); });

  /* one draft policy */
  on("[data-psel]", (el, e) => { if (e.target.closest("button:not([data-psel])")) return; S.pol.sel = el.dataset.psel; render(); const h = document.querySelector("#srcbody [data-hit]"); if (h) h.scrollIntoView({ block: "center", behavior: "smooth" }); });
  on("[data-pdec]", async (el, e) => { e.stopPropagation(); await api(`/policies/builds/${S.pol.build.id}/criteria/${encodeURIComponent(el.dataset.pcid)}`, { method: "POST", body: { decision: el.dataset.pdec } }); await openBuildKeep(); });
  on("[data-pedit]", (el, e) => { e.stopPropagation(); S.pol.edit = el.dataset.pedit || null; render(); });
  on("[data-psave]", async (el, e) => {
    e.stopPropagation();
    const c = S.pol.build.criteria.find((x) => x.id === el.dataset.psave); const body = { decision: "approved", text: val("ed-text"), if_missing: val("ed-miss") };
    if (document.getElementById("ed-val")) { const raw = val("ed-val"); body.value = c.test.type === "in" ? raw.split(",").map((x) => x.trim()).filter(Boolean) : Number(raw); }
    await api(`/policies/builds/${S.pol.build.id}/criteria/${encodeURIComponent(c.id)}`, { method: "POST", body }); S.pol.edit = null; await openBuildKeep();
  });
  document.querySelectorAll("[data-pask]").forEach((el) => (el.oninput = () => (S.pol.asks[el.dataset.pask] = el.value)));
  const conf = document.getElementById("pconf"); if (conf) conf.onchange = () => { S.pol.confirm = conf.checked; S.pol.note = val("pnote") || ""; render(); };
  const note = document.getElementById("pnote"); if (note) note.oninput = () => { S.pol.note = note.value; };
  on("#ppub", async () => {
    const b = S.pol.build, ctx = b.service_ctx, nf = newFacts(b);
    const attach = ctx ? { service: ctx, codes: [], new_service: null, details: nf.map((x) => ({ key: x.key, ask: S.pol.asks[x.key] ?? x.ask })) } : null;
    const r = await api(`/policies/builds/${b.id}/publish`, { method: "POST", body: { confirm: true, note: S.pol.note, attach } });
    S.pol.msg = `Approved. The policy library is now version ${r.version}. ${r.change.added.length} new rule(s) live, ${r.change.removed.length} removed, ${r.change.unchanged} unchanged.${r.waiting ? " " + r.waiting + " approved rule(s) are saved and wait for a key fact." : ""}${ctx ? "" : r.attached ? "" : " No service uses this policy yet."}`;
    await loadPolicies(); await openBuildKeep();
  });
}
async function openBuildKeep() { const sel = S.pol.sel, edit = S.pol.edit, conf = S.pol.confirm, note = S.pol.note, msg = S.pol.msg, asks = S.pol.asks; await openBuild(S.pol.build.id); S.pol.asks = asks; S.pol.sel = sel; S.pol.edit = edit; S.pol.confirm = conf; S.pol.note = note; S.pol.msg = msg; render(); }
