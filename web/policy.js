"use strict";
/* The policy owner's screens. Loaded after app.js, which owns S, api, esc, ic, toast, guard and render.
   Three views: the library (what is live, add or update a policy, drafts, versions), one draft under review, and the result of a publish. */
S.pol = { svc: { name: "", short: "", codes: [], cform: { code: "", source: "" }, open: null, note: "" }, demand: null, attach: { service: "", picked: {}, custom: [], cform: { code: "", source: "" }, newName: "", newShort: "", asks: {}, extend: false }, data: null, build: null, sel: null, form: { source: "ncd", ident: "", service: "", title: "", pid: "", level: "HUMANA_INTERNAL", q: "", picked: null }, pick: null, audit: null, edit: null, confirm: false, note: "", revert: null, check: {}, busy: null, msg: null };
let polTimer = null;

const LEVEL = { REGULATION: "Regulation", NCD: "NCD", LCD: "LCD", HUMANA_INTERNAL: "Humana policy", MCG: "MCG" };
const SRC_HELP = { ncd: ["NCD number", "20.4"], lcd: ["LCD id", "L37848"], cfr: ["Regulation", "42 CFR 412.3"] };
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
const testText = (c) => {
  const t = c.test || {};
  const v = Array.isArray(t.value) ? t.value.join(", ") : t.value;
  return `${esc((c.required_fact || "no detail").replace(/_/g, " "))} ${esc(TEST_WORDS[t.type] || t.type)}${v !== undefined && v !== null && t.type !== "absent" && t.type !== "present" ? " <b>" + esc(v) + "</b>" : ""}`;
};

async function loadPolicies() {
  S.pol.data = await api("/policies");
  S.counts = Object.assign(S.counts || {}, { review: S.pol.data.builds.filter((b) => b.status === "draft").length, demand: S.pol.data.demand_count });
  if (S.view === "history") S.pol.audit = await api("/policies/audit");
  if (S.view === "demand") S.pol.demand = await api("/policies/demand");
}

async function openBuild(id) {
  clearInterval(polTimer);
  S.pol.build = await api("/policies/builds/" + id);
  S.pol.sel = null; S.pol.edit = null; S.pol.confirm = false; S.pol.note = "";
  S.pol.attach = { service: S.pol.build.service_now || "", picked: {}, custom: [], cform: { code: "", source: "" }, newName: "", newShort: "", asks: {}, extend: false };
  if (S.pol.build.status === "running") {
    polTimer = setInterval(guard(async () => {
      const b = await api("/policies/builds/" + id);
      S.pol.build = b;
      if (b.status !== "running") { clearInterval(polTimer); await loadPolicies(); }
      render();
    }), 2500);
  }
  render();
}

/* ---------- the library ---------- */
const PICK_KIND = (src) => (src === "ncd" || src === "lcd" ? src : null);
const AUDIT_WORDS = { service_created: "Added a service", service_status: "Changed a service", draft_started: "Started a draft", rule_approved: "Approved a rule", rule_rejected: "Rejected a rule", rule_pending: "Undid a decision", published: "Published a version", reverted: "Went back to a version", checked_for_update: "Checked for updates" };
const AUDIT_CHIP = { service_created: "new", service_status: "warn", published: "ok", rule_approved: "ok", rule_rejected: "bad", reverted: "warn", rule_pending: "plain", draft_started: "new", checked_for_update: "plain" };
const fullTime = (iso) => { try { return new Date(iso).toLocaleString([], { dateStyle: "medium", timeStyle: "short" }); } catch (e) { return iso || ""; } };

function pickHtml() {
  const f = S.pol.form, k = PICK_KIND(f.source), p = S.pol.pick;
  if (f.ident && f.picked) return `<div class="pickpicked"><div><b>${esc(k.toUpperCase())} ${esc(f.ident)}</b> <span class="faint">${esc(f.picked.title)}</span></div><button class="btn small" data-ppick-clear>Change</button></div>`;
  if (!p || p.kind !== k) return `<div class="faint" style="padding:8px 0">Loading the list…</div>`;
  const rows = p.results.map((r) => `<button type="button" class="pickrow" data-ppick="${esc(r.id)}" data-ptitle="${esc(r.title)}"><span><b>${esc(r.id)}</b> ${esc(r.title)}</span><span class="faint">${r.in_library ? "In the library · " : ""}${esc(r.effective || "")}</span></button>`).join("");
  return `${rows || `<div class="faint" style="padding:8px 0">No policy matches. Try a number or one word of the title.</div>`}<div class="faint" style="font-size:12.5px;margin-top:6px">${p.matches > p.results.length ? `Showing ${p.results.length} of ${p.matches} matches. Type more to narrow the list. ` : ""}This is the full CMS list (${p.total} policies), refreshed by the back end. Last refreshed ${esc(p.as_of)}.</div>`;
}
async function loadPick() {
  const f = S.pol.form, k = PICK_KIND(f.source);
  if (!k) return;
  const r = await api(`/policies/corpus?kind=${k}&q=${encodeURIComponent(f.q || "")}`);
  S.pol.pick = Object.assign(r, { kind: k });
  const box = document.getElementById("pres"); if (box) { box.innerHTML = pickHtml(); bindPick(); }
}
function bindPick() {
  document.querySelectorAll("[data-ppick]").forEach((el) => (el.onclick = () => { S.pol.form.ident = el.dataset.ppick; S.pol.form.picked = { title: el.dataset.ptitle }; render(); }));
  document.querySelectorAll("[data-ppick-clear]").forEach((el) => (el.onclick = () => { S.pol.form.ident = ""; S.pol.form.picked = null; render(); }));
}

function polLibraryHtml() {
  const d = S.pol.data;
  if (!d) return `<div class="page"><div class="empty">Loading the library…</div></div>`;
  const f = S.pol.form, up = f.source === "pdf", pk = PICK_KIND(f.source);
  const help = SRC_HELP[f.source];
  const waiting = d.builds.filter((b) => b.status === "draft").length;
  const rows = d.policies.map((p) => {
    const t = polTarget(p.id), ck = S.pol.check[p.id];
    return `<tr><td><b>${esc(p.title)}</b><div class="faint" style="font-size:12.5px">${esc(p.id)} · ${esc(LEVEL[p.level] || p.level)}${p.verified ? "" : " · placeholder"}</div></td>
      <td>${p.criteria}${p.waiting ? `<div class="faint" style="font-size:12.5px">+ ${p.waiting} waiting</div>` : ""}</td><td class="faint" style="font-size:12.5px">${p.services.length ? esc(p.services.join(", ")) : "no service yet"}</td>
      <td style="white-space:nowrap">${ck ? `<span class="chip ${ck.changed ? "warn" : ck.changed === false ? "ok" : "plain"}" title="${esc(ck.note)}">${ck.changed ? "Source changed" : ck.changed === false ? "Same as saved" : "No saved copy"}</span> ` : ""}
        ${t ? `<button class="btn small" data-pcheck="${esc(p.id)}">Check for updates</button> <button class="btn small" data-pupdate="${esc(p.id)}">Draft from source</button>` : `<span class="faint" style="font-size:12.5px">No online source. Upload a PDF.</span>`}</td></tr>`;
  }).join("");
  return `<div class="page" style="display:grid;gap:22px;max-width:1180px">
    <div class="page-head"><div><h1>Policy library</h1><p>The policies and rules every packet is checked against.</p></div>
      <div class="stat" style="margin:0"><div><b>${esc(d.version)}</b><span>live library version</span></div></div></div>
    ${S.pol.msg ? `<div class="banner">${esc(S.pol.msg)}</div>` : ""}
    ${waiting ? `<div class="banner" style="display:flex;gap:10px;align-items:center;justify-content:space-between;flex-wrap:wrap"><span>${waiting} draft${waiting > 1 ? "s are" : " is"} waiting for your review.</span><button class="btn small primary" data-view="review">Go to policies to review</button></div>` : ""}
    <div><h3 style="margin:0 0 8px">Live policies</h3><div class="tbl"><table><thead><tr><th>Policy</th><th>Rules</th><th>Used by</th><th>Source</th></tr></thead><tbody>${rows}</tbody></table></div></div>
    <div><h3 style="margin:0 0 4px">Services and their procedure codes</h3><p class="muted" style="margin:0 0 8px">A packet reaches a service through the procedure code on its request. Each code shows where it comes from.</p>
      <div class="tbl"><table><thead><tr><th>Service</th><th>Codes in use, and their source</th><th>Policies it checks against</th></tr></thead><tbody>${d.services_detail.map((s) => `<tr><td><b>${esc(s.name)}</b></td>
        <td>${s.cpts.map((c) => { const x = s.sources.find((y) => y.code === c); return `<div style="margin-bottom:6px"><b>${esc(c)}</b> <span class="faint" style="font-size:12.5px">${esc(x && x.description ? x.description.slice(0, 80) : "no description on file")}</span>
          <div class="faint" style="font-size:12.5px">${x && x.sources && x.sources.length ? "CMS: " + x.sources.slice(0, 3).map((z) => `<a href="${esc(z.url)}" target="_blank" rel="noopener">${esc(z.article)}</a> ${esc(z.mac.replace(/\s*\(.*$/, ""))}`).join(" · ") + (x.sources.length > 3 ? ` · +${x.sources.length - 3} more` : "") : x && x.note ? esc(x.note) : "<b>No source on file. Verify before use.</b>"}</div></div>`; }).join("")}
          ${s.other_codes.length ? `<div class="faint" style="font-size:12.5px">CMS lists ${s.other_codes.length} more related codes that are not turned on.${s.checked ? " Checked " + esc(s.checked) + "." : ""}</div>` : ""}</td>
        <td class="faint" style="font-size:12.5px">${s.policies.map(esc).join(", ")}</td></tr>`).join("")}</tbody></table></div></div>
    <div class="card"><h3 style="margin:0 0 4px">Add or update a policy</h3>
      <p class="muted" style="margin:0 0 10px">Pick a policy. We get it, draft the rules, and check every one against the policy text. It takes about a minute. Nothing changes until you publish.</p>
      <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px">
        <div class="field"><label for="psrc">Source</label><select id="psrc"><option value="ncd" ${f.source === "ncd" ? "selected" : ""}>CMS national coverage (NCD)</option><option value="lcd" ${f.source === "lcd" ? "selected" : ""}>CMS local coverage (LCD)</option><option value="cfr" ${f.source === "cfr" ? "selected" : ""}>Federal regulation (eCFR)</option><option value="pdf" ${f.source === "pdf" ? "selected" : ""}>Upload a policy PDF</option></select></div>
        ${up ? `<div class="field"><label for="ppid">Policy id</label><input id="ppid" type="text" placeholder="HUM-CARDIO-2026" value="${esc(f.pid)}"></div><div class="field"><label for="ptitle">Title</label><input id="ptitle" type="text" placeholder="Name of the policy" value="${esc(f.title)}"></div>
          <div class="field"><label for="plevel">Where it sits in the order of authority</label><select id="plevel"><option value="HUMANA_INTERNAL" ${f.level === "HUMANA_INTERNAL" ? "selected" : ""}>Humana policy</option><option value="MCG" ${f.level === "MCG" ? "selected" : ""}>MCG</option><option value="LCD" ${f.level === "LCD" ? "selected" : ""}>LCD</option><option value="NCD" ${f.level === "NCD" ? "selected" : ""}>NCD</option></select></div>
          <div class="field"><label for="pfile">PDF file</label><input id="pfile" type="file" accept="application/pdf"></div>`
        : pk ? "" : `<div class="field"><label for="pid">${help[0]}</label><input id="pid" type="text" placeholder="${help[1]}" value="${esc(f.ident)}"></div>`}
        <div class="field"><label for="psvc">Service it applies to</label><select id="psvc"><option value="">Match by policy (known policies)</option>${d.services.map((s) => `<option value="${esc(s.key)}" ${f.service === s.key ? "selected" : ""}>${esc(s.name)}</option>`).join("")}<option value="new" ${f.service === "new" ? "selected" : ""}>A new service (the AI proposes the details it needs)</option></select></div>
      </div>
      ${pk ? `<div class="field" style="margin-top:12px"><label for="pq">Find a ${pk === "ncd" ? "national" : "local"} coverage policy</label>${f.ident && f.picked ? "" : `<input id="pq" type="search" placeholder="Search by number or title, for example ${pk === "ncd" ? "30.3.3 or acupuncture" : "L37848 or spinal fusion"}" value="${esc(f.q || "")}">`}<div id="pres" style="margin-top:6px">${pickHtml()}</div></div>` : ""}
      <div style="margin-top:14px"><button class="btn primary" id="pgo" ${S.pol.busy || (pk && !f.ident) ? "disabled" : ""}>${S.pol.busy ? "Starting…" : "Build a draft"}</button></div></div></div>`;
}

function polReviewHtml() {
  const d = S.pol.data;
  if (!d) return `<div class="page"><div class="empty">Loading…</div></div>`;
  const open = d.builds.filter((b) => b.status !== "published");
  const rows = open.map((b) => {
    const st = b.status === "draft" ? ["Ready to review", "warn"] : b.status === "error" ? ["Failed", "bad"] : [b.stage || "Running", "new"];
    const prog = b.total ? `${b.decided} of ${b.total} rules decided` : "";
    return `<tr><td><b>${esc(b.policy_id || b.ident)}</b><div class="faint" style="font-size:12.5px">${esc(b.kind === "earlier run" ? "earlier run" : b.kind.toUpperCase())}${b.version ? " · " + esc(b.version) : ""}</div></td>
      <td><span class="chip ${st[1]}">${esc(st[0])}</span></td>
      <td>${prog ? `<div>${esc(prog)}</div><div class="bar"><i style="width:${Math.round((100 * b.decided) / b.total)}%"></i></div>` : "-"}</td>
      <td class="faint" style="font-size:12.5px">${b.summary ? `${b.summary.pass} pass · ${b.summary.review} look closely · ${b.summary.fail} fail` : "-"}</td>
      <td class="faint" style="font-size:12.5px">${esc(b.who || "")} · ${when(b.created_at)}</td>
      <td><button class="btn small ${b.status === "draft" ? "primary" : ""}" data-pbuild="${esc(b.id)}">${b.status === "draft" ? "Review" : "Open"}</button></td></tr>`;
  }).join("");
  return `<div class="page" style="display:grid;gap:18px;max-width:1180px">
    <div class="page-head"><div><h1>Policies to review</h1><p>Drafts the system built from an official policy. Nothing here is live until you publish it.</p></div></div>
    ${S.pol.msg ? `<div class="banner">${esc(S.pol.msg)}</div>` : ""}
    <div class="tbl"><table><thead><tr><th>Policy</th><th>Status</th><th>Your progress</th><th>Code checks</th><th>Built</th><th></th></tr></thead><tbody>${rows || `<tr><td colspan="6" class="faint">Nothing to review. Start a draft from the Policy library.</td></tr>`}</tbody></table></div></div>`;
}

function polHistoryHtml() {
  const a = S.pol.audit, d = S.pol.data;
  if (!a || !d) return `<div class="page"><div class="empty">Loading…</div></div>`;
  const vers = a.versions.length ? a.versions.map((v) => `<tr><td><b>${esc(v.version)}</b> <span class="chip ${v.kind === "revert" ? "warn" : v.kind === "service" ? "plain" : "ok"}">${v.kind === "revert" ? "Went back" : v.kind === "service" ? "Service" : "Published"}</span></td>
      <td>${esc(v.policy_id || "")}</td><td class="faint" style="font-size:12.5px">${v.changelog ? `${v.changelog.approved} rules approved${v.changelog.waiting ? " (" + v.changelog.waiting + " waiting for the packet reader)" : ""}, ${v.changelog.rejected} rejected. ${v.changelog.added.length} new live, ${v.changelog.removed.length} removed, ${v.changelog.unchanged} unchanged.${v.note ? " Note: " + esc(v.note) : ""}` : esc(v.note || "")}</td>
      <td class="faint" style="font-size:12.5px">${esc(v.who || "")}<div>${esc(fullTime(v.at))}</div></td>
      <td style="white-space:nowrap">${v.build_id ? `<button class="btn small" data-pbuild="${esc(v.build_id)}">See what was approved</button> ` : ""}${S.pol.revert === v.version ? `<button class="btn small danger" data-prevert-go="${esc(v.version)}">Confirm: go back to ${esc(v.version)}</button>` : v.version !== a.version ? `<button class="btn small" data-prevert="${esc(v.version)}">Go back to this</button>` : `<span class="chip ok">Live</span>`}</td></tr>`).join("")
    : `<tr><td colspan="5" class="faint">Nothing published yet. The live library is the one that shipped with the app.</td></tr>`;
  const log = a.rows.length ? a.rows.map((r) => `<tr><td class="faint" style="font-size:12.5px;white-space:nowrap">${esc(fullTime(r.at))}</td><td>${esc(r.who || "")}</td><td><span class="chip ${AUDIT_CHIP[r.action] || "plain"}">${esc(AUDIT_WORDS[r.action] || r.action)}</span></td><td>${esc(r.policy_id || "")}</td><td class="faint" style="font-size:12.5px">${esc(r.detail || "")}</td></tr>`).join("")
    : `<tr><td colspan="5" class="faint">No activity yet.</td></tr>`;
  return `<div class="page" style="display:grid;gap:22px;max-width:1180px">
    <div class="page-head"><div><h1>Version history</h1><p>Every version of the policy library, and a record of everything done to it. Nothing here can be changed or deleted.</p></div>
      <div class="stat" style="margin:0"><div><b>${esc(a.version)}</b><span>live library version</span></div></div></div>
    ${S.pol.msg ? `<div class="banner">${esc(S.pol.msg)}</div>` : ""}
    <div><h3 style="margin:0 0 8px">Library versions</h3><div class="tbl"><table><thead><tr><th>Version</th><th>Policy</th><th>What changed</th><th>By</th><th></th></tr></thead><tbody>${vers}</tbody></table></div></div>
    <div><h3 style="margin:0 0 8px">Audit trail</h3><div class="tbl"><table><thead><tr><th>When</th><th>Who</th><th>What</th><th>Policy</th><th>Detail</th></tr></thead><tbody>${log}</tbody></table></div></div></div>`;
}


/* ---------- services ---------- */
const SVC_STATUS = { live: ["Live", "ok"], pilot: ["Pilot", "warn"], planned: ["Planned", "plain"] };
const SVC_STATUS_HELP = { planned: "On the rollout list. No packet is sent to it.", pilot: "Switched on. Nurses check every recommendation.", live: "Switched on and tested." };

function svcCodes(s) {
  return s.cpts.length ? s.cpts.map((c) => { const x = s.sources.find((y) => y.code === c); return `<div style="margin-bottom:6px"><b>${esc(c)}</b> <span class="faint" style="font-size:12.5px">${esc(x && x.description ? x.description.slice(0, 70) : "")}</span>
    <div class="faint" style="font-size:12.5px">${x && x.sources && x.sources.length ? "CMS: " + x.sources.slice(0, 2).map((z) => `<a href="${esc(z.url)}" target="_blank" rel="noopener">${esc(z.article)}</a>`).join(" · ") + (x.sources.length > 2 ? ` · +${x.sources.length - 2} more` : "") : x && x.note ? esc(x.note.slice(0, 110)) : "<b>No source on file</b>"}</div></div>`; }).join("") : `<span class="faint">No codes yet</span>`;
}

function polServicesHtml() {
  const d = S.pol.data, sv = S.pol.svc;
  if (!d) return `<div class="page"><div class="empty">Loading…</div></div>`;
  const rows = d.services_detail.map((s) => {
    const st = SVC_STATUS[s.status] || SVC_STATUS.live, open = sv.open && sv.open.key === s.key ? sv.open : null;
    const btn = (to, label, cls) => `<button class="btn small ${cls || ""}" data-svto="${esc(s.key)}" data-svstatus="${to}">${label}</button>`;
    const acts = s.status === "planned" ? btn("pilot", "Start pilot", "primary") : s.status === "pilot" ? btn("live", "Make live", "primary") + " " + btn("planned", "Back to planned") : btn("pilot", "Pause (back to pilot)");
    return `<tr><td><b>${esc(s.name)}</b><div class="faint" style="font-size:12.5px">${esc(s.full)}</div></td>
      <td><span class="chip ${st[1]}">${st[0]}</span><div class="faint" style="font-size:12.5px;margin-top:4px">${esc(SVC_STATUS_HELP[s.status] || "")}</div>${s.note ? `<div class="faint" style="font-size:12.5px;margin-top:4px">Note: ${esc(s.note)}</div>` : ""}</td>
      <td>${svcCodes(s)}</td>
      <td class="faint" style="font-size:12.5px">${s.policies.length} polic${s.policies.length === 1 ? "y" : "ies"}, ${s.n_rules} rules<br>${s.n_details} details the reader looks for<br>${esc(s.policies.join(", "))}</td>
      <td>${s.n_cases}</td><td style="white-space:nowrap">${acts}</td></tr>
      ${open ? `<tr><td colspan="6"><div style="display:grid;gap:8px;max-width:640px"><b>Move ${esc(s.name)} from ${esc(s.status)} to ${esc(open.to)}</b>
        <div class="field" style="margin:0"><label for="svnote">${open.to === "live" ? "What was tested before this goes live? (required)" : "Note (optional)"}</label><textarea id="svnote" style="min-height:56px" placeholder="${open.to === "live" ? "For example: 30 labeled packets, no wrong approvals, nurses agreed on 28" : ""}">${esc(sv.note)}</textarea></div>
        <div style="display:flex;gap:8px"><button class="btn primary small" data-svgo>Confirm</button><button class="btn small" data-svcancel>Cancel</button></div></div></td></tr>` : ""}`;
  }).join("");
  const codes = sv.codes.map((c, i) => `<tr><td><b>${esc(c.code)}</b></td><td>${esc(c.source)}</td><td><button class="btn small ghost" data-svcdel="${i}">Remove</button></td></tr>`).join("");
  return `<div class="page" style="display:grid;gap:22px;max-width:1180px">
    <div class="page-head"><div><h1>Services</h1><p>A service is one kind of request the system handles: its procedure codes, its policies and the details the packet reader looks for. A new service starts on the rollout list, moves to a pilot, then goes live.</p></div>
      <div class="stat" style="margin:0"><div><b>${d.services_detail.filter((s) => s.status === "live").length}</b><span>live</span></div><div><b>${d.services_detail.filter((s) => s.status === "pilot").length}</b><span>pilot</span></div><div><b>${d.services_detail.filter((s) => s.status === "planned").length}</b><span>planned</span></div></div></div>
    ${S.pol.msg ? `<div class="banner">${esc(S.pol.msg)}</div>` : ""}
    <div class="tbl"><table><thead><tr><th>Service</th><th>Status</th><th>Procedure codes and where they come from</th><th>Policies</th><th>Cases seen</th><th></th></tr></thead><tbody>${rows}</tbody></table></div>
    <div class="card"><h3 style="margin:0 0 4px">Add a service to the rollout list</h3>
      <p class="muted" style="margin:0 0 10px">Give it a name and the procedure codes that identify it, with where each code came from. Then bring in its policy from the Policy library and attach it here. No packet is sent to a planned service.</p>
      <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px">
        <div class="field" style="margin:0"><label for="svname">Service name</label><input id="svname" type="text" placeholder="Total knee replacement, inpatient" value="${esc(sv.name)}"></div>
        <div class="field" style="margin:0"><label for="svshort">Short name</label><input id="svshort" type="text" placeholder="Knee replacement" value="${esc(sv.short)}"></div></div>
      <div style="display:grid;grid-template-columns:140px minmax(0,1fr) auto;gap:8px;margin-top:12px;align-items:end">
        <div class="field" style="margin:0"><label for="svcode">Procedure code</label><input id="svcode" type="text" placeholder="27447" value="${esc(sv.cform.code)}"></div>
        <div class="field" style="margin:0"><label for="svsrc">Where did this code come from?</label><input id="svsrc" type="text" placeholder="For example: CMS billing article A56390, or claims history" value="${esc(sv.cform.source)}"></div>
        <button class="btn small" id="svcadd">Add code</button></div>
      ${codes ? `<div class="tbl" style="margin-top:8px"><table><tbody>${codes}</tbody></table></div>` : ""}
      <div style="margin-top:14px"><button class="btn primary" id="svcreate">Add to the rollout list</button></div></div></div>`;
}

function polDemandHtml() {
  const d = S.pol.data, dm = S.pol.demand;
  if (!d || !dm) return `<div class="page"><div class="empty">Loading…</div></div>`;
  const rows = dm.rows.map((g) => `<tr><td><b>${esc(g.code)}</b></td><td>${esc(g.what || "")}</td><td><b>${g.n}</b></td><td class="faint" style="font-size:12.5px">${esc(when(g.oldest))}</td><td class="faint" style="font-size:12.5px">${g.cases.map(esc).join(", ")}</td>
      <td>${g.service ? (g.service_status === "planned" ? `<span class="chip plain">On the rollout list: ${esc(g.service)}</span>` : `<span class="chip ok">Now covered by ${esc(g.service)} (${esc(g.service_status)})</span><div class="faint" style="font-size:12.5px">A nurse checks these cases again</div>`) : `<button class="btn small primary" data-svprefill="${esc(g.code)}" data-svwhat="${esc(g.what || "")}" data-svn="${g.n}">Add to the rollout list</button>`}</td></tr>`).join("");
  return `<div class="page" style="display:grid;gap:18px;max-width:1180px">
    <div class="page-head"><div><h1>Requests without a policy</h1><p>Open cases that arrived for a procedure we do not cover. The packet could not be checked. The codes that come in most often are the next services to onboard.</p></div></div>
    <div class="tbl"><table><thead><tr><th>Procedure code</th><th>What was requested</th><th>Cases waiting</th><th>Oldest</th><th>Cases</th><th></th></tr></thead><tbody>${rows || `<tr><td colspan="6" class="faint">Nothing waiting. Every open case has a policy.</td></tr>`}</tbody></table></div>
    <p class="faint" style="font-size:12.5px;margin:0">After a service is onboarded, a nurse opens each waiting case and clicks "Check again with the current policies".</p></div>`;
}

function extendHtml(b) {
  const a = S.pol.attach, s = b.services.find((x) => x.key === a.service);
  if (!s || a.service === "__new__") return "";
  const have = {};
  (b.new_facts || []).forEach((f) => (have[f.key] = f));
  const need = [];
  b.criteria.filter((c) => c.decision !== "rejected").forEach((c) => [c.required_fact, c.applies_if && c.applies_if.fact].forEach((k) => { if (k && have[k] && !s.fact_keys.includes(k) && !need.includes(k)) need.push(k); }));
  if (!need.length) return "";
  if (s.status === "live") return `<div class="banner" style="margin-top:10px">${need.length} of these rules need details the reader does not look for yet. ${esc(s.name)} is live, so new details cannot be added. Move it to pilot on the Services page first.</div>`;
  const rows = need.map((k) => `<tr><td><b>${esc(have[k].label)}</b></td><td><input type="text" data-pask="${esc(k)}" value="${esc(a.asks[k] ?? have[k].ask)}" aria-label="Question for the reader about ${esc(have[k].label)}"></td></tr>`).join("");
  return `<div style="margin-top:12px;padding:12px;border:1px dashed var(--line2);border-radius:10px"><label style="display:flex;gap:8px;align-items:flex-start"><input type="checkbox" id="aext" ${a.extend ? "checked" : ""} style="margin-top:3px"><span><b>Add ${need.length} new detail${need.length > 1 ? "s" : ""} to ${esc(s.name)}</b><br><span class="faint" style="font-size:12.5px">These rules need things the packet reader does not look for yet. Add them to this service so the rules can run. Otherwise the rules are saved and wait.</span></span></label>
    ${a.extend ? `<div class="tbl" style="margin-top:8px"><table><thead><tr><th>Detail</th><th>Question for the reader</th></tr></thead><tbody>${rows}</tbody></table></div>` : ""}</div>`;
}

/* ---------- one draft ---------- */


function newServiceHtml(b) {
  const a = S.pol.attach, have = {};
  (b.new_facts || []).forEach((f) => (have[f.key] = f));
  const used = [];
  b.criteria.filter((c) => c.decision !== "rejected").forEach((c) => [c.required_fact, c.applies_if && c.applies_if.fact].forEach((k) => { if (k && have[k] && !used.includes(k)) used.push(k); }));
  const KIND = { number: "a number", enum: "a choice", list: "a list", text: "free text", event: "an event" };
  const rows = used.map((k) => { const f = have[k]; return `<tr><td><b>${esc(f.label)}</b><div class="faint" style="font-size:12.5px">${esc(KIND[f.kind] || f.kind)}${f.values && f.values.length ? ": " + esc(f.values.join(", ")) : ""}</div></td>
    <td><input type="text" data-pask="${esc(k)}" value="${esc(a.asks[k] ?? f.ask)}" aria-label="Question for the reader about ${esc(f.label)}"></td></tr>`; }).join("");
  return `<div style="margin-top:14px;padding:14px;border:1px dashed var(--line2);border-radius:10px;display:grid;gap:12px">
    <div><b>New service</b><div class="faint" style="font-size:12.5px">A service is the set of things the system needs to handle one kind of request: its codes, its policies, and the details the packet reader must find. It starts as a pilot. Nurses check every recommendation.</div></div>
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px">
      <div class="field" style="margin:0"><label for="nsname">Service name</label><input id="nsname" type="text" placeholder="CPAP therapy for obstructive sleep apnea" value="${esc(a.newName)}"></div>
      <div class="field" style="margin:0"><label for="nsshort">Short name</label><input id="nsshort" type="text" placeholder="CPAP (sleep apnea)" value="${esc(a.newShort)}"></div></div>
    <div><b style="font-size:13.5px">What the packet reader will look for (${used.length})</b><div class="faint" style="font-size:12.5px;margin-bottom:6px">The AI proposed these details from the policy. Change a question if it is unclear. A rule you reject drops the details only it needs.</div>
      ${rows ? `<div class="tbl"><table><thead><tr><th>Detail</th><th>Question for the reader</th></tr></thead><tbody>${rows}</tbody></table></div>` : `<div class="faint">None of the rules needs a new detail.</div>`}</div></div>`;
}

function attachHtml(b) {
  const a = S.pol.attach, cd = b.codes || { articles: [], codes: [], note: "" };
  const owner = {};
  b.services.forEach((s) => s.cpts.forEach((c) => (owner[c] = s)));
  const rows = cd.codes.map((c) => {
    const o = owner[c.code], other = o && o.key !== a.service, same = o && o.key === a.service;
    return `<tr><td><input type="checkbox" data-pcode="${esc(c.code)}" data-pdesc="${esc(c.description)}" ${a.picked[c.code] ? "checked" : ""} ${!a.service || other || same ? "disabled" : ""} aria-label="Use code ${esc(c.code)}"></td>
      <td><b>${esc(c.code)}</b></td><td>${more(c.description, 90)}</td><td class="faint" style="font-size:12.5px">${c.n_articles} article${c.n_articles > 1 ? "s" : ""}${other ? ` · already sends packets to ${esc(o.name)}` : same ? " · already on this service" : ""}</td></tr>`;
  }).join("");
  const arts = cd.articles.map((x) => `<li><a href="${esc(x.url)}" target="_blank" rel="noopener">${esc(x.id)} v${x.version}</a> ${esc(x.title)} <span class="faint">· ${esc(x.mac)} · ${x.n_codes} codes${x.cites_ncd === true ? " · names this NCD" : x.cites_ncd === false ? " · does not name this NCD" : ""}</span></li>`).join("");
  const custom = a.custom.map((c, i) => `<tr><td></td><td><b>${esc(c.code)}</b></td><td>${esc(c.source)}</td><td><button class="btn small ghost" data-pcdel="${i}">Remove</button></td></tr>`).join("");
  return `<div class="card"><h3 style="margin:0 0 4px">Which cases use this policy?</h3>
    <p class="muted" style="margin:0 0 10px">A packet reaches a policy through the procedure code on its request. Pick the service this policy belongs to, then choose the codes that should send a packet to it. CMS lists codes in the Billing and Coding articles that go with a policy. Each code you add keeps its source.</p>
    <div class="field" style="max-width:420px"><label for="asvc">Service</label><select id="asvc"><option value="">Do not attach yet (no case will use this policy)</option>${b.services.map((s) => `<option value="${esc(s.key)}" ${a.service === s.key ? "selected" : ""}>${esc(s.name)}${s.status !== "live" ? " [" + esc(s.status) + "]" : ""}${s.cpts.length ? " (codes " + esc(s.cpts.join(", ")) + ")" : ""}</option>`).join("")}<option value="__new__" ${a.service === "__new__" ? "selected" : ""}>Create a new service for this policy</option></select></div>${a.service === "__new__" ? newServiceHtml(b) : extendHtml(b)}
    ${a.service ? "" : `<div class="banner" style="margin-top:10px">No service yet. The approved rules are saved with the policy and change no case. A brand-new service goes through onboarding first: its details are defined, test packets pass, then a pilot, then live.</div>`}
    <p class="faint" style="font-size:12.5px;margin:10px 0 6px">${esc(cd.note || "")}</p>
    ${rows ? `<div class="tbl"><table><thead><tr><th></th><th>Code</th><th>What it is</th><th>Listed by</th></tr></thead><tbody>${rows}</tbody></table></div>` : ""}
    ${arts ? `<details class="more" style="margin-top:8px"><summary><u>Where these codes come from (${cd.articles.length} CMS articles)</u></summary><ul class="plist" style="margin-top:8px">${arts}</ul></details>` : ""}
    <div style="margin-top:12px"><b style="font-size:13.5px">Add a code CMS did not list</b>
      <div style="display:grid;grid-template-columns:140px minmax(0,1fr) auto;gap:8px;margin-top:6px;align-items:end">
        <div class="field" style="margin:0"><label for="acode">Code</label><input id="acode" type="text" placeholder="97810" value="${esc(a.cform.code)}" ${a.service ? "" : "disabled"}></div>
        <div class="field" style="margin:0"><label for="asrc">Where did this code come from?</label><input id="asrc" type="text" placeholder="For example: CMS Physician Fee Schedule, or the plan's own policy page 3" value="${esc(a.cform.source)}" ${a.service ? "" : "disabled"}></div>
        <button class="btn small" id="acadd" ${a.service ? "" : "disabled"}>Add</button></div>
      ${custom ? `<div class="tbl" style="margin-top:8px"><table><tbody>${custom}</tbody></table></div>` : ""}</div></div>`;
}
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
  const chk = { pass: ["Checks passed", "ok"], review: ["Look closely", "warn"], fail: ["Failed the checks", "bad"] }[c.check];
  const dec = { approved: ["Approved", "ok"], rejected: ["Rejected", "bad"], pending: ["Needs your decision", "plain"] }[c.decision];
  const v = Array.isArray(c.test.value) ? c.test.value.join(", ") : c.test.value ?? "";
  const canEditValue = ["gte", "lte", "in"].includes(c.test.type);
  return `<div class="card rule ${sel ? "sel" : ""}" data-psel="${esc(c.id)}">
    <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;justify-content:space-between"><div><b>${esc(c.id)}</b> <span class="faint" style="font-size:12.5px">${esc(c.cite)}</span></div>
      <div style="display:flex;gap:6px;flex-wrap:wrap"><span class="chip ${chk[1]}">${chk[0]}</span><span class="chip ${c.confidence === "high" ? "ok" : "warn"}">AI confidence: ${esc(c.confidence)}</span><span class="chip ${dec[1]}">${dec[0]}${c.edited ? " · edited" : ""}</span></div></div>
    <p style="margin:8px 0 4px">${esc(c.text)}</p>
    <div class="quote">${more(c.source_quote, 260)}</div>
    <div class="faint" style="font-size:12.5px;margin-top:6px">Tests: ${testText(c)}${c.applies_if ? ` · only when ${esc(String(c.applies_if.fact).replace(/_/g, " "))} is ${esc(c.applies_if.equals)}` : ""}</div>
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

function polBuildHtml() {
  const b = S.pol.build;
  const head = (inner) => `<div class="page" style="max-width:1260px"><div class="page-head"><div><button class="btn small ghost" data-pback style="margin-left:-8px">${ic("left", 16)}${S.view === "review" ? "Policies to review" : S.view === "history" ? "Version history" : "Policy library"}</button><h1 style="margin-top:4px">${inner}</h1></div></div>`;
  if (b.status === "running") {
    const cur = Math.max(0, BUILD_STEPS.findIndex((s) => s[0] === b.stage));
    return head(esc(b.ident || "Draft")) + `<div class="card" style="max-width:560px"><h3 style="margin:0 0 2px">Building the draft</h3><div class="faint" style="margin:0 0 10px">${esc(b.ident || "")}</div>
      ${BUILD_STEPS.map(([k, t, sub], i) => `<div class="step ${i < cur ? "done" : i === cur ? "now" : "todo"}"><span class="dot">${i < cur ? ic("check", 14) : ""}</span><div><b>${t}</b>${sub}</div></div>`).join("")}
      <div class="faint" style="margin-top:12px;font-size:12.5px">This usually takes about a minute. You can leave this page. The draft will wait in the Drafts list.</div></div></div>`;
  }
  if (b.status === "error") return head(esc(b.ident || "Draft")) + `<div class="banner" style="border-color:var(--bad);color:var(--bad)">The draft failed. ${esc(b.error || "")}</div></div>`;
  const m = b.meta, t = b.tally, n = b.criteria.length;
  const cr = b.change_report;
  const crRows = cr ? cr.rows.map((r) => `<tr><td>${esc(r.id)}</td><td>${esc((r.fact || "").replace(/_/g, " "))}</td><td>${esc(r.approved || "")}</td><td>${esc(r.draft || "")}</td><td><span class="chip ${r.result === "same" ? "ok" : r.result === "differs" ? "warn" : r.result === "missed" ? "bad" : "plain"}">${r.result === "same" ? "Same" : r.result === "differs" ? "Different test" : r.result === "missed" ? "Not in the draft" : "Information"}</span></td></tr>`).join("") : "";
  const publishReady = b.status === "draft" && t.pending === 0 && t.approved > 0 && S.pol.confirm;
  return head(esc(m.title)) + `<p class="muted" style="margin:-8px 0 14px">${esc(m.policy_id)} · ${esc(LEVEL[m.level] || m.level)} · ${esc(m.source)} ${esc(m.version)}${m.effective ? " · effective " + esc(m.effective) : ""}${m.url && m.url.startsWith("http") ? ` · <a href="${esc(m.url)}" target="_blank" rel="noopener">official source</a>` : ""}</p>
    ${b.status === "published" ? `<div class="banner" style="border-color:var(--ok);color:var(--ok)">This draft was published.</div>` : ""}
    ${S.pol.msg ? `<div class="banner">${esc(S.pol.msg)}</div>` : ""}
    <div class="stat" style="margin-bottom:14px"><div><b>${n}</b><span>rules the AI drafted</span></div><div><b>${b.counts.pass} / ${b.counts.review} / ${b.counts.fail}</b><span>code checks: pass / look closely / fail</span></div>
      <div><b>${t.approved} · ${t.rejected} · ${t.pending}</b><span>your decisions: approved · rejected · waiting</span></div>${cr ? `<div><b>${cr.counts.same} of ${cr.approved_count}</b><span>of the live rules match the draft exactly</span></div>` : ""}</div>
    <div class="pol-grid"><div class="srcpane"><h4 style="margin:0 0 8px;font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--ink3)">The official text</h4><div id="srcbody">${sourceHtml(b)}</div></div>
      <div style="display:grid;gap:12px;align-content:start">${b.criteria.map((c) => ruleHtml(c, b)).join("")}</div></div>
    <div style="display:grid;gap:16px;margin-top:20px">
      ${b.not_modeled.length ? `<div class="card"><h3 style="margin:0 0 4px">Left for a person (${b.not_modeled.length})</h3><p class="muted" style="margin:0 0 8px">Parts of the policy the AI did not turn into rules, with its reason. These cases will keep going to a physician.</p><ul class="plist">${b.not_modeled.map((x) => `<li>${more(x.quote, 160)}<div class="faint" style="font-size:12.5px">${esc(x.why)}</div></li>`).join("")}</ul></div>` : ""}
      ${b.uncovered.length ? `<div class="card"><h3 style="margin:0 0 4px">Possible misses (${b.uncovered.length})</h3><p class="muted" style="margin:0 0 8px">Sentences with rule words that no rule and no note covers. Check that nothing important is missing.</p><ul class="plist">${b.uncovered.map((x) => `<li>${more(x, 200)}</li>`).join("")}</ul></div>` : ""}
      ${cr ? `<div class="card"><h3 style="margin:0 0 4px">Change report: this draft against the live rules</h3><p class="muted" style="margin:0 0 8px">Each live rule, matched by the fact it tests. ${cr.extra.length ? cr.extra.length + " draft rule(s) test facts the live library does not test yet." : "Nothing extra in the draft."}</p><div class="tbl"><table><thead><tr><th>Live rule</th><th>Detail</th><th>Live test</th><th>Draft test</th><th></th></tr></thead><tbody>${crRows}</tbody></table></div></div>` : `<div class="card"><h3 style="margin:0 0 4px">A new policy</h3><p class="muted" style="margin:0">This policy is not in the live library, so there is nothing to compare. If you publish it, it is stored but affects no case until a service lists it.</p></div>`}
      ${b.status === "draft" ? attachHtml(b) : ""}
      ${b.status === "draft" ? `<div class="card"><h3 style="margin:0 0 4px">Publish</h3><p class="muted" style="margin:0 0 10px">Publishing makes a new version of the library. New cases are checked against it from that moment. Cases that already have a recommendation keep it. You can go back to the previous version at any time.</p>
        <label style="display:flex;gap:8px;align-items:flex-start;margin-bottom:10px"><input type="checkbox" id="pconf" ${S.pol.confirm ? "checked" : ""} style="margin-top:3px"><span>I reviewed every rule and I understand this changes how new cases are checked.</span></label>
        ${b.waiting_approved ? `<p class="faint" style="margin:0 0 10px;font-size:12.5px">${b.waiting_approved} approved rule(s) are waiting for the packet reader. They are saved with the policy and change nothing until the reader can find the detail they need.</p>` : ""}
        <div class="field" style="margin:0 0 12px"><label for="pnote">Note for the history (optional)</label><input id="pnote" type="text" value="${esc(S.pol.note)}" placeholder="Why this change"></div>
        <button class="btn primary" id="ppub" ${publishReady ? "" : "disabled"}>Publish ${esc(b.library_version ? "a new version" : "")}</button>
        <span class="faint" style="margin-left:10px;font-size:12.5px">${t.pending ? t.pending + " rule(s) still need a decision." : t.approved ? "" : "Approve at least one rule."}</span></div>` : ""}</div></div>`;
}

const policyHtml = () => (S.pol.build ? polBuildHtml() : S.view === "review" ? polReviewHtml() : S.view === "history" ? polHistoryHtml() : S.view === "services" ? polServicesHtml() : S.view === "demand" ? polDemandHtml() : polLibraryHtml());

/* ---------- actions ---------- */
function bindPolicy() {
  const on = (sel, fn) => document.querySelectorAll(sel).forEach((el) => (el.onclick = guard((e) => fn(el, e))));
  const val = (id) => (document.getElementById(id) || {}).value;
  const keep = () => { const f = S.pol.form; f.source = val("psrc") ?? f.source; f.ident = val("pid") ?? f.ident; f.service = val("psvc") ?? f.service; f.pid = val("ppid") ?? f.pid; f.title = val("ptitle") ?? f.title; f.level = val("plevel") ?? f.level; };
  const psrc = document.getElementById("psrc");
  if (psrc) psrc.onchange = () => { keep(); S.pol.form.ident = ""; S.pol.form.picked = null; S.pol.form.q = ""; S.pol.pick = null; render(); };
  const pq = document.getElementById("pq");
  if (pq) { let tm; pq.oninput = () => { S.pol.form.q = pq.value; clearTimeout(tm); tm = setTimeout(guard(loadPick), 250); }; }
  bindPick();
  if (S.view === "policies" && !S.pol.build && PICK_KIND(S.pol.form.source) && (!S.pol.pick || S.pol.pick.kind !== S.pol.form.source)) guard(loadPick)();
  ["pid", "ppid", "ptitle", "psvc", "plevel"].forEach((id) => { const el = document.getElementById(id); if (el) el.onchange = keep; });
  on("[data-pback]", async () => { clearInterval(polTimer); S.pol.build = null; S.pol.msg = null; await loadPolicies(); render(); });
  on("[data-pbuild]", async (el) => { S.pol.msg = null; await openBuild(el.dataset.pbuild); });
  on("#pgo", async () => {
    keep(); const f = S.pol.form; S.pol.busy = true; render();
    try {
      let r;
      if (f.source === "pdf") {
        const file = document.getElementById("pfile").files[0];
        if (!file || !f.pid || !f.title) throw new Error("Add the PDF, a policy id and a title");
        const fd = new FormData(); fd.append("file", file); fd.append("policy_id", f.pid); fd.append("title", f.title); fd.append("level", f.level); fd.append("service", f.service);
        r = await api("/policies/builds/upload", { method: "POST", body: fd });
      } else r = await api("/policies/builds", { method: "POST", body: { kind: f.source, ident: f.ident, service: f.service } });
      S.pol.busy = null; await openBuild(r.id);
    } catch (e) { S.pol.busy = null; render(); throw e; }
  });
  on("[data-pcheck]", async (el) => { const id = el.dataset.pcheck; el.textContent = "Checking…"; S.pol.check[id] = await api(`/policies/${encodeURIComponent(id)}/check-update`, { method: "POST" }); render(); });
  on("[data-pupdate]", async (el) => { const t = polTarget(el.dataset.pupdate); const r = await api("/policies/builds", { method: "POST", body: { kind: t.kind, ident: t.ident, service: "" } }); await openBuild(r.id); });
  on("[data-prevert]", (el) => { S.pol.revert = el.dataset.prevert; render(); });
  on("[data-prevert-go]", async (el) => { const r = await api("/policies/revert", { method: "POST", body: { version: el.dataset.prevertGo, confirm: true } }); S.pol.revert = null; S.pol.msg = "The live library is back to version " + r.version + "."; await loadPolicies(); render(); });
  on("[data-psel]", (el, e) => { if (e.target.closest("button:not([data-psel])")) return; S.pol.sel = el.dataset.psel; render(); const h = document.querySelector("#srcbody [data-hit]"); if (h) h.scrollIntoView({ block: "center", behavior: "smooth" }); });
  on("[data-pdec]", async (el, e) => { e.stopPropagation(); await api(`/policies/builds/${S.pol.build.id}/criteria/${encodeURIComponent(el.dataset.pcid)}`, { method: "POST", body: { decision: el.dataset.pdec } }); await openBuildKeep(); });
  on("[data-pedit]", (el, e) => { e.stopPropagation(); S.pol.edit = el.dataset.pedit || null; render(); });
  on("[data-psave]", async (el, e) => {
    e.stopPropagation();
    const c = S.pol.build.criteria.find((x) => x.id === el.dataset.psave); const body = { decision: "approved", text: val("ed-text"), if_missing: val("ed-miss") };
    if (document.getElementById("ed-val")) { const raw = val("ed-val"); body.value = c.test.type === "in" ? raw.split(",").map((x) => x.trim()).filter(Boolean) : Number(raw); }
    await api(`/policies/builds/${S.pol.build.id}/criteria/${encodeURIComponent(c.id)}`, { method: "POST", body }); S.pol.edit = null; await openBuildKeep();
  });
  const asvc = document.getElementById("asvc"); if (asvc) asvc.onchange = () => { S.pol.attach.service = asvc.value; S.pol.attach.picked = {}; S.pol.attach.extend = false; render(); };
  const sv = S.pol.svc, valv = (id) => (document.getElementById(id) || {}).value;
  const keepSv = () => { if (document.getElementById("svname")) { sv.name = valv("svname"); sv.short = valv("svshort"); sv.cform = { code: valv("svcode") || "", source: valv("svsrc") || "" }; } if (document.getElementById("svnote")) sv.note = valv("svnote"); };
  on("#svcadd", () => {
    keepSv(); const code = (sv.cform.code || "").trim().toUpperCase();
    if (!/^([0-9]{5}|[A-Z][0-9]{4})$/.test(code)) throw new Error("A procedure code is 5 digits, or a letter and 4 digits");
    if (!(sv.cform.source || "").trim()) throw new Error("Say where this code came from");
    sv.codes.push({ code, source: sv.cform.source.trim() }); sv.cform = { code: "", source: "" }; render();
  });
  on("[data-svcdel]", (el) => { keepSv(); sv.codes.splice(Number(el.dataset.svcdel), 1); render(); });
  on("#svcreate", async () => {
    keepSv();
    const r = await api("/policies/services", { method: "POST", body: { name: sv.name, short: sv.short, codes: sv.codes.map((c) => ({ code: c.code, source: c.source })) } });
    S.pol.svc = { name: "", short: "", codes: [], cform: { code: "", source: "" }, open: null, note: "" };
    S.pol.msg = "Added to the rollout list. Library version " + r.version + ". Bring in its policy from the Policy library and attach it when you publish."; await loadPolicies(); render();
  });
  on("[data-svstatus]", (el) => { keepSv(); sv.open = { key: el.dataset.svto, to: el.dataset.svstatus }; sv.note = ""; render(); });
  on("[data-svcancel]", () => { sv.open = null; render(); });
  on("[data-svgo]", async () => {
    keepSv();
    const r = await api(`/policies/services/${encodeURIComponent(sv.open.key)}/status`, { method: "POST", body: { status: sv.open.to, note: sv.note, confirm: true } });
    S.pol.msg = "Service updated. Library version " + r.version + "."; sv.open = null; sv.note = ""; await loadPolicies(); render();
  });
  on("[data-svprefill]", (el) => {
    S.view = "services"; go("#/view/services");
    sv.name = el.dataset.svwhat; sv.short = el.dataset.svwhat.slice(0, 40); sv.codes = [{ code: el.dataset.svprefill, source: `Seen on ${el.dataset.svn} incoming request(s). Confirm against the CMS billing article before use.` }]; render();
  });

  document.querySelectorAll("[data-pcode]").forEach((el) => (el.onchange = () => { if (el.checked) S.pol.attach.picked[el.dataset.pcode] = el.dataset.pdesc; else delete S.pol.attach.picked[el.dataset.pcode]; }));
  const aext = document.getElementById("aext"); if (aext) aext.onchange = () => { S.pol.attach.extend = aext.checked; render(); };
  const nsn = document.getElementById("nsname"), nss = document.getElementById("nsshort");
  if (nsn) nsn.oninput = () => (S.pol.attach.newName = nsn.value);
  if (nss) nss.oninput = () => (S.pol.attach.newShort = nss.value);
  document.querySelectorAll("[data-pask]").forEach((el) => (el.oninput = () => (S.pol.attach.asks[el.dataset.pask] = el.value)));
  const acode = document.getElementById("acode"), asrc = document.getElementById("asrc");
  if (acode) acode.oninput = () => (S.pol.attach.cform.code = acode.value);
  if (asrc) asrc.oninput = () => (S.pol.attach.cform.source = asrc.value);
  on("#acadd", () => {
    const f = S.pol.attach.cform, code = (f.code || "").trim().toUpperCase();
    if (!/^([0-9]{5}|[A-Z][0-9]{4})$/.test(code)) throw new Error("A procedure code is 5 digits, or a letter and 4 digits");
    if (!(f.source || "").trim()) throw new Error("Say where this code came from");
    S.pol.attach.custom.push({ code, source: f.source.trim() }); S.pol.attach.cform = { code: "", source: "" }; render();
  });
  on("[data-pcdel]", (el) => { S.pol.attach.custom.splice(Number(el.dataset.pcdel), 1); render(); });
  const conf = document.getElementById("pconf"); if (conf) conf.onchange = () => { S.pol.confirm = conf.checked; S.pol.note = val("pnote") || ""; render(); };
  const note = document.getElementById("pnote"); if (note) note.oninput = () => { S.pol.note = note.value; };
  on("#ppub", async () => {
    const at = S.pol.attach, codes = [...Object.entries(at.picked).map(([code, description]) => ({ code, description })), ...at.custom.map((c) => ({ code: c.code, source: c.source }))];
    const r = await api(`/policies/builds/${S.pol.build.id}/publish`, { method: "POST", body: { confirm: true, note: S.pol.note, attach: at.service ? { service: at.service, extend: !!at.extend && at.service !== "__new__", codes, new_service: at.service === "__new__" ? { name: at.newName, short: at.newShort } : null, details: Object.entries(at.asks).map(([key, ask]) => ({ key, ask })) } : null } });
    S.pol.msg = `Published. The live library is now version ${r.version}. ${r.change.added.length} new rule(s) live, ${r.change.removed.length} removed, ${r.change.unchanged} unchanged.${r.waiting ? " " + r.waiting + " approved rule(s) are saved and waiting for the packet reader." : ""}${r.codes && r.codes.length ? " Codes " + r.codes.join(", ") + " now send packets to this policy." : ""}${r.attached ? "" : " This policy is not attached to a service yet, so no case uses it."}`;
    await loadPolicies(); await openBuildKeep();
  });
}
async function openBuildKeep() { const sel = S.pol.sel, edit = S.pol.edit, conf = S.pol.confirm, note = S.pol.note, msg = S.pol.msg, att = S.pol.attach; await openBuild(S.pol.build.id); S.pol.attach = att; S.pol.sel = sel; S.pol.edit = edit; S.pol.confirm = conf; S.pol.note = note; S.pol.msg = msg; render(); }
