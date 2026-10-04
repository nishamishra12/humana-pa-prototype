// Shared helpers for the solution slides. One slide per file, one click per step, nothing plays by itself.
// The animation is written straight into the slide XML (pptxgenjs cannot do animations). Same method as ../journey/build_friction.js.
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");
const JSZip = require("jszip");

const C = {
  ink: "16211E", muted: "5C6B66", green: "1F6F5C", greenSoft: "E3F0EB", line: "CBD5D1",
  coral: "B8452F", coralSoft: "FBE9E4", amber: "8A5A00", amberSoft: "FCEFD0",
  purple: "5F3AA8", purpleSoft: "EBE2F8", ok: "18764A", okSoft: "DDF3E7", white: "FFFFFF", grey: "F3F5F4",
};
const H = "Cambria", B = "Calibri";
// who does the work in a step
const KIND = {
  ext: { fill: C.coralSoft, line: C.coral, tag: "OUTSIDE SOURCE", tc: C.coral },
  etl: { fill: C.coralSoft, line: C.coral, tag: "ETL + AI", tc: C.coral },
  ai: { fill: C.purpleSoft, line: C.purple, tag: "AI", tc: C.purple },
  code: { fill: C.greenSoft, line: C.green, tag: "CODE", tc: C.green },
  person: { fill: C.amberSoft, line: C.amber, tag: "PERSON", tc: C.amber },
  data: { fill: C.greenSoft, line: C.green, tag: "CODE + DATA", tc: C.green },
  mix: { fill: C.greenSoft, line: C.green, tag: "CODE + AI", tc: C.green },
  plain: { fill: C.white, line: C.line, tag: "", tc: C.muted },
};

class Slide {
  constructor(o) {
    this.o = o; // { file, title(deck title), eyebrow, heading, sub, footer }
    this.items = [];
    this.slots = [];
    this.notes = [];
    this.frame();
  }
  add(o) { this.items.push(o); return o.name; }
  runs(parts) { return parts; }
  text(name, x, y, w, h, runs, o = {}) { return this.add({ name, kind: "text", x, y, w, h, runs, align: o.align, valign: o.valign, static: o.static }); }
  frame() {
    const { eyebrow, heading, sub, footer } = this.o;
    this.text("eyebrow", 0.5, 0.3, 6, 0.28, [{ text: eyebrow, options: { bold: true, fontSize: 11, color: C.green, fontFace: B, charSpacing: 3 } }], { static: true });
    this.text("heading", 0.5, 0.55, 8.4, 0.75, [{ text: heading, options: { fontSize: 26, color: C.ink, fontFace: H } }], { valign: "middle", static: true });
    if (sub) this.text("sub", 8.2, 0.55, 4.63, 0.75, [{ text: sub, options: { fontSize: 14, color: C.muted, fontFace: B } }], { align: "right", valign: "middle", static: true });
    if (footer) this.text("footer", 0.5, 7.1, 12.33, 0.25, [{ text: footer, options: { fontSize: 9, color: C.muted, fontFace: B } }], { static: true });
  }
  // a rounded box with text
  node(name, x, y, w, h, runs, o = {}) {
    return this.add({ name, kind: "node", x, y, w, h, runs, fill: o.fill || C.white, line: o.line || C.line, lineW: o.lineW || 1.25, radius: o.radius ?? 0.08, align: o.align || "left", valign: o.valign || "middle", margin: o.margin || [0.08, 0.14, 0.08, 0.14] });
  }
  // a step: tag, title, one short line. kind picks the colour.
  step(name, x, y, w, h, kind, title, sub, o = {}) {
    const k = KIND[kind];
    const r = [];
    if (k.tag) r.push({ text: k.tag, options: { bold: true, fontSize: 8.5, color: k.tc, fontFace: B, charSpacing: 1.5, breakLine: true, paraSpaceAfter: 3 } });
    r.push({ text: title, options: { bold: true, fontSize: o.ts || 13.5, color: C.ink, fontFace: B, breakLine: !!sub, paraSpaceAfter: 3 } });
    if (sub) r.push({ text: sub, options: { fontSize: o.ss || 10.5, color: C.muted, fontFace: B } });
    return this.node(name, x, y, w, h, r, { fill: k.fill, line: k.line, valign: o.valign || "top", margin: o.margin || [0.2, 0.14, 0.08, 0.14], radius: 0.1 });
  }
  badge(name, n, cx, cy, fill = C.green) {
    return this.add({ name, kind: "node", x: cx - 0.17, y: cy - 0.17, w: 0.34, h: 0.34, fill, line: fill, lineW: 1, radius: 0.17, align: "center", margin: [0, 0, 0, 0], runs: [{ text: String(n), options: { bold: true, fontSize: 11, color: C.white, fontFace: B } }] });
  }
  chip(name, x, y, w, h, text, o = {}) {
    return this.node(name, x, y, w, h, [{ text, options: { fontSize: o.fs || 10.5, color: o.color || C.muted, fontFace: B, bold: !!o.bold, italic: !!o.italic } }], { fill: o.fill || C.white, line: o.line || C.line, lineW: o.lineW || 0.75, radius: o.radius ?? 0.06, align: o.align || "left", valign: o.valign, margin: o.margin || [0.04, 0.1, 0.04, 0.1] });
  }
  hline(name, x, y, len, o = {}) { return this.add({ name, kind: "line", x, y, w: len, h: 0, color: o.color || C.muted, lineW: o.lineW || 1.75, arrow: o.arrow !== false, dash: o.dash, flipH: !!o.left }); }
  vline(name, x, y, len, o = {}) { return this.add({ name, kind: "line", x, y, w: 0, h: len, color: o.color || C.muted, lineW: o.lineW || 1.75, arrow: o.arrow !== false, dash: o.dash, flipV: !!o.up }); }
  // one click: everything named here fades in together. The note is what you say before the next click.
  click(note, ...names) {
    this.slots.push({ fx: names.flat().map((n, i) => ({ t: "fadeIn", name: n, delay: i === 0 ? 0 : 120, dur: 450 })) });
    this.notes.push(note);
  }

  // ---- output
  visible(k) {
    const vis = new Set();
    this.slots.slice(0, k).forEach((sl) => sl.fx.forEach((e) => vis.add(e.name)));
    return vis;
  }
  draw(pres, s) {
    const m2 = (m) => m.map((v) => v * 72);
    this.items.forEach((o) => {
      if (o.kind === "line") {
        s.addShape(pres.ShapeType.line, { x: o.x, y: o.y, w: o.w, h: o.h, flipH: !!o.flipH, flipV: !!o.flipV, objectName: o.name, line: { color: o.color, width: o.lineW, dashType: o.dash || "solid", ...(o.arrow ? { endArrowType: "triangle" } : {}) } });
      } else if (o.kind === "node") {
        const m = o.margin;
        s.addText(o.runs, { shape: pres.ShapeType.roundRect, rectRadius: o.radius, x: o.x, y: o.y, w: o.w, h: o.h, fill: { color: o.fill }, line: { color: o.line, width: o.lineW }, align: o.align, valign: o.valign, margin: m2([m[3], m[1], m[2], m[0]]), objectName: o.name, isTextBox: false });
      } else {
        s.addText(o.runs, { x: o.x, y: o.y, w: o.w, h: o.h, align: o.align || "left", valign: o.valign || "top", margin: 0, objectName: o.name, isTextBox: true, fit: "none" });
      }
    });
  }
  timing(ids) {
    let n = 3;
    const id = () => n++;
    const byName = Object.fromEntries(this.items.map((o) => [o.name, o]));
    const setVis = (spid, val, delay) => `<p:set><p:cBhvr><p:cTn id="${id()}" dur="1" fill="hold"><p:stCondLst><p:cond delay="${delay}"/></p:stCondLst></p:cTn><p:tgtEl><p:spTgt spid="${spid}"/></p:tgtEl><p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst></p:cBhvr><p:to><p:strVal val="${val}"/></p:to></p:set>`;
    const fade = (spid, dur) => `<p:animEffect transition="in" filter="fade"><p:cBhvr><p:cTn id="${id()}" dur="${dur}"/><p:tgtEl><p:spTgt spid="${spid}"/></p:tgtEl></p:cBhvr></p:animEffect>`;
    const effect = (e, nodeType) => {
      const spid = ids[e.name], o = byName[e.name];
      const grp = o.kind === "line" ? "" : ' grpId="0"';
      return `<p:par><p:cTn id="${id()}" presetID="10" presetClass="entr" presetSubtype="0" fill="hold"${grp} nodeType="${nodeType}"><p:stCondLst><p:cond delay="${e.delay}"/></p:stCondLst><p:childTnLst>${setVis(spid, "visible", 0)}${fade(spid, e.dur)}</p:childTnLst></p:cTn></p:par>`;
    };
    let clicks = "";
    this.slots.forEach((sl) => {
      const outer = id(), slot = id();
      const inner = sl.fx.map((e, k) => effect(e, k === 0 ? "clickEffect" : "withEffect")).join("");
      clicks += `<p:par><p:cTn id="${outer}" fill="hold"><p:stCondLst><p:cond delay="indefinite"/></p:stCondLst><p:childTnLst><p:par><p:cTn id="${slot}" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>${inner}</p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn></p:par>`;
    });
    const names = [...new Set(this.slots.flatMap((sl) => sl.fx.map((e) => e.name)))].filter((nm) => byName[nm].kind !== "line");
    const bld = names.map((nm) => `<p:bldP spid="${ids[nm]}" grpId="0"${byName[nm].kind === "node" ? ' animBg="1"' : ""}/>`).join("");
    return `<p:timing><p:tnLst><p:par><p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot"><p:childTnLst><p:seq concurrent="1" nextAc="seek"><p:cTn id="2" dur="indefinite" nodeType="mainSeq"><p:childTnLst>${clicks}</p:childTnLst></p:cTn><p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst><p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst></p:seq></p:childTnLst></p:cTn></p:par></p:tnLst><p:bldLst>${bld}</p:bldLst></p:timing>`;
  }
  preview() {
    const px = 96, pt = (v) => v * 1.3333, esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;");
    const html = this.items.map((o) => {
      const base = `left:${o.x * px}px;top:${o.y * px}px;width:${o.w * px}px;height:${o.h * px}px;`;
      if (o.kind === "line") {
        const horiz = o.h === 0, col = "#" + o.color;
        return `<div data-n="${o.name}" style="position:absolute;${base}${horiz ? `border-top:${o.lineW}px ${o.dash ? "dashed" : "solid"} ${col}` : `border-left:${o.lineW}px ${o.dash ? "dashed" : "solid"} ${col}`}"></div>`;
      }
      const inner = o.runs.map((r) => `<span style="font-family:${r.options.fontFace || B};font-size:${pt(r.options.fontSize || 12)}px;font-weight:${r.options.bold ? 700 : 400};font-style:${r.options.italic ? "italic" : "normal"};color:#${r.options.color || C.ink};letter-spacing:${r.options.charSpacing ? r.options.charSpacing * 0.0133 : 0}em">${esc(r.text)}</span>${r.options.breakLine ? "<br>" : ""}`).join("");
      const m = o.margin ? o.margin.map((v) => v * px) : [0, 0, 0, 0];
      const box = o.kind === "node" ? `background:#${o.fill};border:${o.lineW}px solid #${o.line};border-radius:${o.radius * px}px;` : "";
      return `<div data-n="${o.name}" style="position:absolute;${base}${box}box-sizing:border-box;overflow:hidden;display:flex;flex-direction:column;justify-content:${o.valign === "top" ? "flex-start" : "center"};text-align:${o.align || "left"};padding:${m[0]}px ${m[1]}px ${m[2]}px ${m[3]}px;line-height:1.15"><div>${inner}</div></div>`;
    }).join("\n");
    const data = JSON.stringify(this.slots.map((sl) => sl.fx.map((e) => e.name)));
    const script = `<script>const S=${data};const q=new URLSearchParams(location.search).get("step");if(q!==null){const k=+q;const vis=new Set();S.slice(0,k).forEach(sl=>sl.forEach(n=>vis.add(n)));const all=new Set(S.flat());document.querySelectorAll("[data-n]").forEach(el=>{const n=el.dataset.n;if(all.has(n)&&!vis.has(n))el.style.display="none"})}</script>`;
    return `<!doctype html><meta charset="utf-8"><body style="margin:0;background:#fff"><div style="position:relative;width:${13.333 * px}px;height:${7.5 * px}px;background:#fff">${html}</div>${script}<script>document.body.style.zoom=Math.min(1,innerWidth/1280)</script>`;
  }
  async build() {
    const out = path.join(__dirname, this.o.file + ".pptx");
    const pres = new pptxgen();
    pres.layout = "LAYOUT_WIDE";
    pres.title = this.o.title;
    pres.author = "Nisha Mishra";
    const s = pres.addSlide();
    s.background = { color: C.white };
    this.draw(pres, s);
    s.addNotes(["One slide. One click per step. Finish the talking point, then click."].concat(this.notes.map((t, i) => "Click " + (i + 1) + ": " + t)).join(String.fromCharCode(10, 10)));
    await pres.writeFile({ fileName: out });
    const zip = await JSZip.loadAsync(fs.readFileSync(out));
    const f = "ppt/slides/slide1.xml";
    let xml = await zip.file(f).async("string");
    const ids = {};
    for (const m of xml.matchAll(/<p:cNvPr id="(\d+)" name="([^"]*)"/g)) ids[m[2]] = m[1];
    const missing = new Set();
    this.slots.forEach((sl) => sl.fx.forEach((e) => { if (!ids[e.name]) missing.add(e.name); }));
    if (missing.size) throw new Error("No shape for: " + [...missing].join(", "));
    xml = xml.replace("</p:sld>", this.timing(ids) + "</p:sld>");
    zip.file(f, xml);
    fs.writeFileSync(out, await zip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" }));
    fs.mkdirSync(path.join(__dirname, "preview"), { recursive: true });
    fs.writeFileSync(path.join(__dirname, "preview", this.o.file + ".html"), this.preview());
    console.log("wrote", path.relative(process.cwd(), out), "|", this.slots.length, "clicks");
  }
}

module.exports = { Slide, C, H, B, KIND };
