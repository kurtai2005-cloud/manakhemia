/* 《微光小圃》 hd2dv3.js — #83 花園 HD-2D V3 合成（遊美 scenes/hd2d_v3：FORMAT_V3.md／SEASONS_V3.md／PETGLOW_V3.md）。原創代碼。
   SceneV3 extends hd2d.Scene：v3 開（G.v3.on()）→ 喺 @3x buffer（585×1266）合成；關／未 load 好 → 照用 v2 1x 合成（6b.3 樣）。
   引擎規則：燈光已預烘入 @3x 層（lightmap／light_add／bloom），即時嘅只有粒子、flare、glow（寵物光 × petGlow）。
   stack：sky → far → haze_far → mid → mist(drift) → [寵物光池] → 寵物(L2 ×3 nearest) → fore → ×lightmap → [光池 ×postLightmap]
          → light_add → emissive(flicker) → bloom(× bloom3x) → 寵物光暈／core／粒子 → flares → 粒子 → 雨／霧 → 暗角 → vignette。
   記憶體：@3x 層每款 ~40MB decode → 只 keep 最近 3 款（LRU），其餘放走；未 load 好嗰款先用 v2 畫（唔會黑畫面）。 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else { root.Glimmer = root.Glimmer || {}; root.Glimmer.hd2dv3 = factory(); }
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';
  const W = 195, H = 422, MX = 14, MY = 12, LW = 223, LH = 446, K3 = 3, W3 = W * K3, H3 = H * K3, LRU = 3;
  const PAR = (p) => p <= 0.2 ? 0 : p <= 0.5 ? 1 : p <= 1.2 ? 2 : 3;    // grade parallax → hd2d offs index（sky／far／mid／fore）
  function hex(c) { const n = parseInt(String(c || '#ffffff').replace('#', ''), 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255]; }
  function mixc(a, b, t) { return [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t]; }
  function mk(w, h) { const c = document.createElement('canvas'); c.width = Math.max(1, w | 0); c.height = Math.max(1, h | 0); return c; }
  const img = (u) => new Promise((res, rej) => { const im = new Image(); im.onload = () => res(im); im.onerror = () => rej(new Error(u)); im.src = u; });
  const js = (u) => fetch(u).then(r => { if (!r.ok) throw new Error(u + ' ' + r.status); return r.json(); });
  /* variant id → V3 目錄＋grade 檔（H3rain → H3/grade_rain.json，層喺 H3/rain/x3） */
  function dirOf(v) {
    const m = /^(H\d)(rain|overcast|fog)?(?:@([a-z]+))?$/.exec(String(v)); if (!m) return null;
    if (m[3]) return { dir: 'seasons/' + m[3] + '/' + m[1] + '/', grade: 'grade.json', base: m[1], season: m[3] };
    if (m[2]) return { dir: 'H3/', grade: 'grade_' + m[2] + '.json', base: 'H3', wx: m[2] };
    return { dir: m[1] + '/', grade: 'grade.json', base: m[1] };
  }
  /* 每幀 anchor（'same' 跟返另一幀） */
  function frameOf(J, name) { let f = J && J.frames && J.frames[name], n = 0; while (f && f.same && n++ < 4) f = J.frames[f.same]; return f && f.a ? f : null; }
  function haloFor(r3) { return r3 <= 24 ? 'halo_s' : r3 <= 40 ? 'halo_m' : 'halo_l'; }
  function flickerOf(F, t) { if (!F) return 1; const w = Math.sin(t * Math.PI * 2 * (F.hz || 0.5)); return F.type === 'blink' ? 1 - (F.amp || 0.3) * (0.5 - 0.5 * w) : 1 + (F.amp || 0.1) * w; }

  function extend(Base, HD) {
    return class SceneV3 extends Base {
      constructor(o) {
        super(o); o = o || {};
        this.v3base = o.v3base || 'art/v3/'; this.v3on = o.v3on || (() => true); this.R = o.renderer || null; this.G = o.G || null;
        this.v3v = {}; this.fx = null; this.forms = {}; this.kids = {}; this.tc = {}; this.ems = []; this.fps3 = []; this.kps = []; this.use = 0;
        this.buf3 = null; this.bufB3 = null; this.lc3 = {};
        this.s3 = { draws: 0, fallback: 0, loads: 0, evict: 0, missing: [], pool: 0, halos: 0, flares: 0, emit: 0, kid: 0, emissive: 0, lastGlow: 1, lastKidGlow: 1 };
      }
      load() {
        const B = this.v3base + 'garden/fx/', P = this.v3base + 'petglow/';
        const fx = Promise.all([js(B + 'fx_glow_v3@3x.json'), img(B + 'fx_glow_v3@3x.png'), js(B + 'particles_v3@3x.json'), img(B + 'particles_v3@3x.png')])
          .then(([gj, gi, pj, pi]) => { this.fx = { gj, gi, pj, pi }; }).catch(e => { this.s3.missing.push('fx:' + e.message); });
        const ix = Promise.all([js(P + 'tuanrong/index.json').catch(() => null), js(P + 'kid/index.json').catch(() => null)]).then(([a, b]) => {
          this.formIx = new Set(((a && a.forms) || []).map(f => f.form)); this.kidIx = new Set(((b && b.forms) || []).map(f => f.form)); });
        return Promise.all([super.load(), fx, ix]).then(() => { this.buf3 = mk(W3, H3); this.bufB3 = mk(W3, H3); });
      }
      /* @3x 層 lazy load（LRU 3 款） */
      need3(v) {
        if (!v || !this.v3on()) return null;
        let e = this.v3v[v]; if (e) { e.use = ++this.use; return e.ready ? e : null; }
        const d = dirOf(v); if (!d) return null;
        e = this.v3v[v] = { id: v, d, ready: false, use: ++this.use, img: {}, g: null };
        const B = this.v3base + 'garden/' + d.dir; this.s3.loads++;
        js(B + d.grade).then(g => {
          e.g = g; const st = (g.v3 && g.v3.stack) || [];
          return Promise.all(st.filter(L => L.file && !/^scenes\//.test(L.file)).map(L => img(B + L.file).then(im => { e.img[L.layer] = im; })));
        }).then(() => { e.ready = true; this.evict(); }).catch(err => { e.failed = String(err && err.message || err); this.s3.missing.push(v + ':' + e.failed); });
        return null;
      }
      evict() {
        const ks = Object.keys(this.v3v).filter(k => this.v3v[k].ready);
        if (ks.length <= LRU) return; ks.sort((a, b) => this.v3v[a].use - this.v3v[b].use);
        const keep = new Set([this.st.cur, this.st.prev]);
        for (const k of ks.slice(0, ks.length - LRU)) if (!keep.has(k)) { delete this.v3v[k]; delete this.lc3[k]; this.s3.evict++; }
      }
      ready3(v) { const e = this.v3v[v]; return !!(e && e.ready); }
      tinted(name, tint) {                                   // 白色 sprite → tint 色版（cache）
        const key = name + tint; let c = this.tc[key]; if (c) return c; const f = this.fx && this.fx.gj.frames[name]; if (!f) return null;
        c = this.tc[key] = mk(f.w, f.h); const g = c.getContext('2d'); g.drawImage(this.fx.gi, f.x, f.y, f.w, f.h, 0, 0, f.w, f.h);
        g.globalCompositeOperation = 'multiply'; g.fillStyle = 'rgb(' + hex(tint).join(',') + ')'; g.fillRect(0, 0, f.w, f.h); g.globalCompositeOperation = 'destination-in'; g.drawImage(this.fx.gi, f.x, f.y, f.w, f.h, 0, 0, f.w, f.h);
        return c;
      }
      cache3(v, name, key, build) {
        const V = this.lc3[v] || (this.lc3[v] = {}); let e = V[name]; if (!e) e = V[name] = { c: mk(W3, H3), key: null };
        if (e.key !== key) { const g = e.c.getContext('2d'); g.setTransform(1, 0, 0, 1, 0, 0); g.globalCompositeOperation = 'source-over'; g.globalAlpha = 1; g.imageSmoothingEnabled = false; g.clearRect(0, 0, W3, H3); build(g); e.key = key; this.s3.cacheBuilds = (this.s3.cacheBuilds || 0) + 1; }
        else this.s3.cacheHits = (this.s3.cacheHits || 0) + 1;
        return e.c;
      }
      /* 寵物（團絨）光：petBlit（render.js L2 座標）＋形態 petglow json */
      petInfo() {
        const R = this.R, b = R && R.petBlit; if (!b || b.fn !== R.frameNo) return null;
        return { X: b.X, Y: b.Y, mir: b.scx < 0 ? -1 : 1, fk: b.fk, name: b.nm, img: b.img, sx: b.sx, sy: b.sy, sw: b.sw, sh: b.sh, px: b.px, py: b.py };
      }
      kidInfo() { const R = this.R, b = R && R.kidBlit; return b && b.fn === R.frameNo ? b : null; }
      formJ(fk, kid) {
        const M = kid ? this.kids : this.forms, ix = kid ? this.kidIx : this.formIx; if (!fk || !ix || !ix.has(fk)) return null;
        let e = M[fk]; if (e) return e.ready ? e : null;
        e = M[fk] = { ready: false }; const B = this.v3base + 'petglow/' + (kid ? 'kid/' : 'tuanrong/');
        js(B + fk + '.json').then(j => Promise.all([js(B + j.sheet), img(B + j.sheet.replace(/\.json$/, '.png'))]).then(([sj, si]) => { e.j = j; e.sj = sj; e.si = si; e.ready = true; }))
          .catch(err => { e.failed = String(err && err.message); this.s3.missing.push('petglow:' + fk); });
        if (!kid) img((this.artBase || 'art/') + 'evo6/atlas_' + fk + '_emissive.png').then(im => { e.em = im; }).catch(() => { });
        return null;
      }
      drawPool(x, pl, foot, glow, form, scale) {
        if (!pl || !this.fx || glow <= 0.002) return;
        let tint = hex(pl.tint), sz = pl.size3x || [240, 96], off = pl.offset3x || [0, 6], k = 1;
        if (form && form.pool && form.pool.tint) { tint = mixc(tint, hex(form.pool.tint), form.pool.mixWithScene != null ? form.pool.mixWithScene : 0.5); if (form.pool.size3x) { sz = form.pool.size3x; k = 0.7 * (scale || 1); } }
        const c = this.tinted('pet_pool', '#' + tint.map(v => ('0' + Math.round(v).toString(16)).slice(-2)).join('')); if (!c) return;
        x.globalCompositeOperation = 'lighter'; x.globalAlpha = Math.max(0, Math.min(1, (pl.intensity != null ? pl.intensity : 0.5) * glow * k));
        x.drawImage(c, foot[0] + off[0] - sz[0] / 2, foot[1] + off[1] - sz[1] / 2, sz[0], sz[1]); x.globalAlpha = 1; x.globalCompositeOperation = 'source-over'; this.s3.pool++;
      }
      drawHalos(x, F, name, foot, mir, glow, sceneK, t) {
        if (!F || glow <= 0.002) return; const fr = frameOf(F.j, name) || frameOf(F.j, String(name || '').replace(/_noface/, '')) || frameOf(F.j, 'idle_01'); if (!fr) return;
        const fl = flickerOf(F.j.flicker, t), e = fr.e != null ? fr.e : 1, S = F.sj.frames, pk = Math.max(1, glow);
        x.globalCompositeOperation = 'lighter'; x.imageSmoothingEnabled = true; let big = null;
        for (const a of fr.a) {
          const hn = haloFor(a[2]), f = S[hn]; if (!f) continue; const r = a[2] * pk;
          x.globalAlpha = Math.max(0, Math.min(1, a[3] * e * fl * sceneK * glow));
          x.drawImage(F.si, f.x, f.y, f.w, f.h, foot[0] + a[0] * mir - r, foot[1] + a[1] - r, r * 2, r * 2); this.s3.halos++;
          if (!big || a[2] > big[2]) big = a;
        }
        const cf = S.core_12; if (big && cf) { x.globalAlpha = Math.max(0, Math.min(1, glow * fl)); x.drawImage(F.si, cf.x, cf.y, cf.w, cf.h, foot[0] + big[0] * mir - 6, foot[1] + big[1] - 6, 12, 12); }
        x.globalAlpha = 1; x.globalCompositeOperation = 'source-over'; x.imageSmoothingEnabled = false;
      }
      stepFormParts(list, F, foot, mir, glow, dt, name) {
        const E = F && F.j.emitter; if (!E || glow <= 0.002) { list.length = 0; return; }
        const fr = frameOf(F.j, name) || frameOf(F.j, 'idle_01'); const an = fr && fr.a[0]; if (!an) return;
        if (list.length < (E.max || 3) && Math.random() < (E.rate || 0.5) * dt) {
          const r = (a, b) => a + Math.random() * (b - a), sp = E.spread3 || 20;
          list.push({ x: foot[0] + an[0] * mir + r(-sp, sp), y: foot[1] + an[1] + r(-sp, sp), vx: r(...(E.vx3 || [-8, 8])), vy: r(...(E.vy3 || [-10, -4])), age: 0, life: r(...(E.life || [2, 3])), fi: (Math.random() * 4) | 0 });
        }
        for (const p of list) { p.age += dt; p.x += p.vx * dt; p.y += p.vy * dt; }
        for (let i = list.length - 1; i >= 0; i--) if (list[i].age >= list[i].life) list.splice(i, 1);
      }
      drawFormParts(x, list, F, glow) {
        const E = F && F.j.emitter; if (!E || !list.length) return; const S = F.sj.frames, gs = S[E.glow || 'halo_s'];
        for (const p of list) {
          const u = p.age / p.life, a = Math.sin(Math.PI * u) * glow * (E.blink ? 0.6 + 0.4 * Math.sin(p.age * 9) : 1); if (a <= 0.01) continue;
          const fr = S[(E.frames || [])[(p.fi + Math.floor(p.age * 6)) % Math.max(1, (E.frames || []).length)]];
          x.globalCompositeOperation = 'lighter';
          if (gs) { x.globalAlpha = Math.min(1, a * (E.glowAlpha || 0.3)); x.drawImage(F.si, gs.x, gs.y, gs.w, gs.h, p.x - gs.w / 2, p.y - gs.h / 2, gs.w, gs.h); }
          x.globalCompositeOperation = 'source-over';
          if (fr) { x.globalAlpha = Math.min(1, a); x.drawImage(F.si, fr.x, fr.y, fr.w, fr.h, Math.round(p.x - fr.w / 2), Math.round(p.y - fr.h / 2), fr.w, fr.h); }
        }
        x.globalAlpha = 1; x.globalCompositeOperation = 'source-over';
      }
      /* 場景 emitter（gold／bokeh／dust…；rect = 1x art 座標） */
      stepEmit(dt, g3, v) {
        const E = (g3 && g3.emitters) || []; if (this.emV !== v) { this.ems = []; this.emV = v; }
        E.forEach((e, i) => {
          const n = this.ems.filter(p => p.i === i).length, r = (a, b) => a + Math.random() * (b - a);
          if (n < (e.max || 6) && Math.random() < (e.rate || 0.5) * dt * 3) {
            const R = e.rect || [0, 0, W, H], L = e.life || [4, 6], vy = e.vy || [-2, 0];
            this.ems.push({ i, x: r(R[0], R[2]) * K3, y: r(R[1], R[3]) * K3, vy: r(vy[0], vy[1]) * K3, age: 0, life: r(L[0], L[1]), ph: Math.random() * 6.28, fi: (Math.random() * 6) | 0 });
          }
        });
        for (const p of this.ems) { p.age += dt; p.y += p.vy * dt; }
        this.ems = this.ems.filter(p => p.age < p.life && E[p.i]);
      }
      drawEmit(x, g3, t) {
        const E = (g3 && g3.emitters) || [], F = this.fx; if (!F || !this.ems.length) return; const GF = F.gj.frames, PF = F.pj.frames;
        for (const p of this.ems) {
          const e = E[p.i]; if (!e) continue; const u = p.age / p.life, a = Math.sin(Math.PI * u), sx = p.x + Math.sin(t * 0.8 + p.ph) * (e.sway || 0) * K3;
          if (e.sprite && GF[e.sprite]) { const c = this.tinted(e.sprite, e.tint || '#ffffff'); if (c) { x.globalCompositeOperation = 'lighter'; x.globalAlpha = Math.min(1, a * (e.alpha != null ? e.alpha : 0.3)); x.drawImage(c, sx - c.width / 2, p.y - c.height / 2); } }
          else {
            const core = PF[e.type + '_0' + (1 + (p.fi + Math.floor(p.age * 4)) % 6)];
            if (e.glow && GF[e.glow]) { const c = this.tinted(e.glow, e.tint || '#ffffff'); if (c) { x.globalCompositeOperation = 'lighter'; x.globalAlpha = Math.min(1, a * (e.add != null ? e.add : 0.5)); x.drawImage(c, sx - c.width, p.y - c.height, c.width * 2, c.height * 2); } }
            if (core) { x.globalCompositeOperation = e.type === 'petal' ? 'source-over' : 'lighter'; x.globalAlpha = Math.min(1, a); x.drawImage(F.pi, core.x, core.y, core.w, core.h, Math.round(sx - core.w / 2), Math.round(p.y - core.h / 2), core.w, core.h); }
          }
          this.s3.emit++;
        }
        x.globalAlpha = 1; x.globalCompositeOperation = 'source-over';
      }
      drawFlares(x, g3, t, P2) {
        const FL = (g3 && g3.flares) || [], F = this.fx; if (!F || !FL.length) return;
        x.globalCompositeOperation = 'lighter';
        for (const f of FL) {
          const fr = Math.floor(t * (f.fps || 6) + (f.phase || 0) * 6) % 6, nm = 'flare_' + (f.size || 's') + '_0' + (fr + 1), c = this.tinted(nm, f.tint || '#ffffff'); if (!c) continue;
          x.globalAlpha = Math.min(1, f.intensity != null ? f.intensity : 0.8);
          x.drawImage(c, Math.round(f.pos[0] * K3 + P2[0] + MX * K3 - c.width / 2), Math.round(f.pos[1] * K3 + P2[1] + MY * K3 - c.height / 2)); this.s3.flares++;
        }
        x.globalAlpha = 1; x.globalCompositeOperation = 'source-over';
      }
      compose3(x, v, c) {
        const e = this.v3v[v], g3 = e.g.v3 || {}, I = e.img, L = this.v[v], offs = c.offs, q = c.quality, t = this.t;
        const P = (oi) => [Math.round(-MX + offs[oi][0]) * K3, Math.round(-MY + offs[oi][1]) * K3];
        const put = (im, oi, a, dx) => { if (!im) return; if (a != null) x.globalAlpha = Math.max(0, Math.min(1, a)); const p = P(oi); x.drawImage(im, p[0] + (dx || 0), p[1]); x.globalAlpha = 1; this.stat.composites++; };
        const st = g3.stack || [], P2 = P(2), G = this.G, glow = G && G.v3 ? G.v3.petGlow() : 1, kglow = G && G.v3 ? G.v3.kidGlow() : 1, base = e.d.base;
        this.s3.lastGlow = glow; this.s3.lastKidGlow = kglow;
        const pi = this.petInfo(), ki = this.kidInfo(), foot = pi ? [pi.X * K3 + P2[0], pi.Y * K3 + P2[1]] : null, kfoot = ki ? [ki.X * K3 + P2[0], ki.Y * K3 + P2[1]] : null;
        const F = pi ? this.formJ(pi.fk, false) : null, KF = ki ? this.formJ(ki.fk, true) : null, pl = g3.petLight;
        const sceneK = (j) => j && j.sceneScale ? (j.sceneScale[base] != null ? j.sceneScale[base] : 1) : 1;
        x.setTransform(1, 0, 0, 1, 0, 0); x.globalCompositeOperation = 'source-over'; x.globalAlpha = 1; x.imageSmoothingEnabled = false;
        // 背景 cache：pet 之前、冇 drift／realtime 嘅 source-over 層
        let i = 0; const back = []; for (; i < st.length; i++) { const Lr = st[i]; if (Lr.layer === 'pet' || Lr.realtime || Lr.drift3x || !I[Lr.layer] || (Lr.blend && Lr.blend !== 'source-over')) break; back.push(Lr); }
        const bk = back.map(Lr => P(PAR(Lr.parallax || 1)).join(',')).join('|');
        x.drawImage(this.cache3(v, 'back', bk, (b) => { for (const Lr of back) { const p = P(PAR(Lr.parallax || 1)); b.drawImage(I[Lr.layer], p[0], p[1]); } }), 0, 0); this.stat.composites++;
        let petDone = false; const afterBloom = () => {
          if (petDone) return; petDone = true; if (q === 'off') return;
          if (F && foot) { this.drawHalos(x, F, pi.name, foot, pi.mir, glow, sceneK(F.j), t); this.drawFormParts(x, this.fps3, F, glow); }
          if (KF && kfoot) { this.drawHalos(x, KF, ki.fk && ki.clip + '_0' + (1 + (ki.f | 0)), kfoot, ki.mir, kglow, sceneK(KF.j), t); this.drawFormParts(x, this.kps, KF, kglow); this.s3.kid++; }
        };
        for (; i < st.length; i++) {
          const Lr = st[i], n = Lr.layer, oi = PAR(Lr.parallax || 1), im = I[n];
          if (n === 'pet') {
            if (foot) this.drawPool(x, pl, foot, glow, F && F.j, 1);
            if (kfoot && pl) this.drawPool(x, Object.assign({}, pl, { intensity: (pl.intensity || 0.5) * 0.7 * sceneK(KF && KF.j) }), kfoot, kglow, KF && KF.j, 1);
            x.imageSmoothingEnabled = false; x.drawImage(c.pet, P2[0], P2[1], LW * K3, LH * K3); this.stat.composites++;
            if (F && F.em && pi && pi.img && glow > 0.002) {                 // emissive（sprite 自帶）lighter ×.33×petGlow
              x.save(); x.globalCompositeOperation = 'lighter'; x.globalAlpha = Math.min(1, 0.33 * glow); x.translate(foot[0], foot[1]); x.scale(pi.mir * K3, K3);
              x.drawImage(F.em, pi.sx, pi.sy, pi.sw, pi.sh, -pi.px, -pi.py, pi.sw, pi.sh); x.restore(); this.s3.emissive++;
            }
            continue;
          }
          if (/^fog_bank_(far|near)$/.test(n)) { if (this.wxArt && L) { x.setTransform(K3, 0, 0, K3, 0, 0); this.drawBand(x, this.wxArt.fb, this.wxArt.j.fog_bank.frames[n.slice(9)], HD.CFG.fog[n.slice(9)], offs); x.setTransform(1, 0, 0, 1, 0, 0); } continue; }
          if (n === 'overcast_clouds') { if (this.wxArt) { x.setTransform(K3, 0, 0, K3, 0, 0); this.drawBand(x, this.wxArt.oc, null, HD.CFG.overcast, offs); x.setTransform(1, 0, 0, 1, 0, 0); } continue; }
          if (n === 'rain') { x.setTransform(K3, 0, 0, K3, 0, 0); this.drawRain(x, offs, q); x.setTransform(1, 0, 0, 1, 0, 0); continue; }
          if (n === 'flares') { afterBloom(); if (q !== 'off') this.drawFlares(x, g3, t, P2); continue; }
          if (n === 'particles') {
            afterBloom(); if (q === 'off') continue;
            this.drawEmit(x, g3, t);
            x.imageSmoothingEnabled = true; const bt = hex((L && L.g && L.g.bulbGlowTint) || '#ffe9a0');
            for (const l of c.lights || []) { const col = l.bud ? mixc(l.col, bt, 0.6) : l.col, r = l.r * K3; x.globalCompositeOperation = 'lighter'; x.globalAlpha = Math.max(0, Math.min(1, l.a)); x.drawImage(this.glowSprite(col), l.x * K3 - r, l.y * K3 - r, r * 2, r * 2); }
            x.globalAlpha = 1; x.globalCompositeOperation = 'source-over'; x.imageSmoothingEnabled = false;
            x.setTransform(K3, 0, 0, K3, 0, 0); this.drawSeasonParts(x, v, offs); x.setTransform(1, 0, 0, 1, 0, 0);
            continue;
          }
          if (n === 'fog') {
            x.globalCompositeOperation = 'source-over';
            if (e.d.wx === 'rain' && HD.CFG.rainDim > 0) { x.globalCompositeOperation = 'multiply'; const kk = Math.round(255 * (1 - HD.CFG.rainDim)); x.fillStyle = 'rgb(' + kk + ',' + kk + ',' + kk + ')'; x.fillRect(0, 0, W3, H3); x.globalCompositeOperation = 'source-over'; }
            const fg = L && L.g && L.g.fog; if (fg && fg.density > 0) { x.globalAlpha = fg.density; x.fillStyle = fg.color; x.fillRect(0, 0, W3, H3); x.globalAlpha = 1; }
            if (c.dim > 0.005) { x.fillStyle = 'rgba(8,12,44,' + Math.min(0.6, c.dim).toFixed(3) + ')'; x.fillRect(0, 0, W3, H3); }
            continue;
          }
          if (!im) continue;
          if (Lr.screen) { x.globalCompositeOperation = Lr.blend === 'multiply' ? 'multiply' : 'source-over'; x.drawImage(im, 0, 0, W3, H3); x.globalCompositeOperation = 'source-over'; continue; }
          x.globalCompositeOperation = Lr.blend || 'source-over';
          if (Lr.drift3x) { const p = P(oi), w = im.width, dx = ((t * Lr.drift3x) % w + w) % w; x.drawImage(im, p[0] + dx, p[1]); x.drawImage(im, p[0] + dx - w, p[1]); x.globalCompositeOperation = 'source-over'; continue; }
          let a = null;
          if (n === 'bloom') { if (q === 'off') { x.globalCompositeOperation = 'source-over'; continue; } const bi = g3.bloom3x ? g3.bloom3x.intensity : 0.6; put(im, oi, Math.min(1, bi)); if (bi > 1) put(im, oi, bi - 1); x.globalCompositeOperation = 'source-over'; continue; }
          if (n === 'emissive_flicker') a = 0.8 + 0.2 * Math.sin(t * 2.3) * Math.sin(t * 5.1 + 1);
          put(im, oi, a);
          x.globalCompositeOperation = 'source-over';
          if (n === 'lightmap' && foot && pl && pl.postLightmap) this.drawPool(x, Object.assign({}, pl, { intensity: (pl.intensity || 0.5) * pl.postLightmap }), foot, glow, F && F.j, 1);
        }
        afterBloom();
        x.globalAlpha = 1; x.globalCompositeOperation = 'source-over';
      }
      draw(ctx, k, c) {
        if (!this.v3on() || !this.buf3) { this.s3.off = (this.s3.off || 0) + 1; return super.draw(ctx, k, c); }
        const s = this.st, dt = c.dt || 0, cur = s.cur;
        this.need3(cur); if (s.prev && s.mix < 1) this.need3(s.prev);
        if (!this.ready3(cur)) { this.s3.fallback++; return super.draw(ctx, k, c); }
        this.stat.draws++; this.s3.draws++;
        this.stepParticles(dt, this.grade(cur), c.quality); this.stepSeasonParts(dt, cur, c.quality); this.stepRain(dt, cur === 'H3rain' || s.prev === 'H3rain');
        const g3 = this.v3v[cur].g.v3; this.stepEmit(dt, g3, cur);
        const pi = this.petInfo(), ki = this.kidInfo(), P2 = [Math.round(-MX + c.offs[2][0]) * K3, Math.round(-MY + c.offs[2][1]) * K3];
        if (pi) { const F = this.formJ(pi.fk, false); this.stepFormParts(this.fps3, F, [pi.X * K3 + P2[0], pi.Y * K3 + P2[1]], pi.mir, this.s3.lastGlow, dt, pi.name); }
        if (ki) { const F = this.formJ(ki.fk, true); this.stepFormParts(this.kps, F, [ki.X * K3 + P2[0], ki.Y * K3 + P2[1]], ki.mir, this.s3.lastKidGlow, dt, ki.clip + '_01'); }
        const A = this.buf3.getContext('2d'); this.compose3(A, cur, c);
        let out = this.buf3;
        if (s.prev && s.mix < 1 && this.ready3(s.prev)) {
          this.stat.fades++; const B = this.bufB3.getContext('2d'); this.compose3(B, s.prev, c);
          B.setTransform(1, 0, 0, 1, 0, 0); B.globalCompositeOperation = 'source-over'; B.globalAlpha = s.mix; B.drawImage(this.buf3, 0, 0); B.globalAlpha = 1; out = this.bufB3;
        }
        const r = W * k / W3; ctx.imageSmoothingEnabled = Math.abs(r - Math.round(r)) > 0.01; if (ctx.imageSmoothingEnabled) ctx.imageSmoothingQuality = 'high';
        ctx.drawImage(out, 0, 0, W * k, H * k); ctx.imageSmoothingEnabled = false;
      }
      v3stat() { return Object.assign({}, this.s3, { loaded: Object.keys(this.v3v).filter(k => this.v3v[k].ready), forms: Object.keys(this.forms).filter(k => this.forms[k].ready), kids: Object.keys(this.kids).filter(k => this.kids[k].ready), parts: this.ems.length, petParts: this.fps3.length }); }
    };
  }
  return { W3, H3, K3, LRU, dirOf, frameOf, haloFor, flickerOf, PAR, extend };
});
