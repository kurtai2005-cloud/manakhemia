/* 《微光小圃》 hd2d.js — HD-2D 時段場景（遊美 art-pet/scenes/hd2d，FORMAT.md canvas2D 版）。原創代碼。
   自成一體：純邏輯（時段→H 映射、雨、crossfade 狀態、引擎疊層開關）DOM-free、Node 可 require；
   Scene 類（瀏覽器）負責載入資產、寵物 tint＋rim、逐層合成、粒子、雨。render.js 只需：
     ① frame() 開頭 hd = this.hd && this.hd.on() → 跳過程序化 L0/L1/L3、drawL2 用透明底（c.hd=true）
     ② drawPetBeh tint 一行：draw = hd.tintPet(draw, { mir, form, frame })
     ③ 合成：hd.draw(ctx, k, { pet: L2, offs, lights, quality, dt, t, dim })
   直向：美術格 195×422、層 223×446（邊距 14/12）、寵物腳底 art (97,292)。 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else { root.Glimmer = root.Glimmer || {}; root.Glimmer.hd2d = factory(); }
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';
  const W = 195, H = 422, MX = 14, MY = 12, LW = W + MX * 2, LH = H + MY * 2;
  const VARIANTS = ['H1', 'H2', 'H3', 'H3rain', 'H4'];
  const CYCLE = ['auto', 'H1', 'H2', 'H3', 'H3rain', 'H4'];
  const LABEL = { auto: 'Auto', H1: 'H1 晨', H2: 'H2 黃昏', H3: 'H3 日', H3rain: 'H3 雨', H4: 'H4 夜' };
  const CFG = { fadeSec: 2, rainLightAdd: 0.3, rainAlpha: 0.55, particleMax: 24, rimLowOff: true };

  // ── 純邏輯 ──
  /* 時段：06–10 H1｜10–16 H3（落雨 → H3rain）｜16–19 H2｜19–06 H4 */
  function variantFor(hour, weather) {
    const h = ((hour % 24) + 24) % 24;
    if (h >= 6 && h < 10) return 'H1';
    if (h >= 10 && h < 16) return weather === 'rain' ? 'H3rain' : 'H3';
    if (h >= 16 && h < 19) return 'H2';
    return 'H4';
  }
  function baseOf(v) { return v === 'H3rain' ? 'H3' : v; }
  /* 引擎自己嘅程序化疊層（月 (150,76)、燈籠串、燈柱、星、螢火、蘑菇光）：HD-2D 場景已畫，全部關，避免疊兩次（H4 尤其：月＋燈串已喺 sky/mid） */
  function engineOverlays(v) {
    if (!v) return { moon: true, lantern: true, lampPost: true, stars: true, fireflies: true, mushroom: true };
    return { moon: false, lantern: false, lampPost: false, stars: false, fireflies: false, mushroom: false };
  }
  function createState(o) { o = o || {}; return { mode: 'auto', cur: null, prev: null, mix: 1, fadeSec: o.fadeSec || CFG.fadeSec, switches: 0 }; }
  function target(st, ctx) { return st.mode !== 'auto' ? st.mode : variantFor(ctx.hour, ctx.weather); }
  /* 每幀：target 變 → 由 cur crossfade 去新款（fadeSec 秒）；淡緊途中再變 → 由當前畫面主體（cur）重新淡 */
  function update(st, dt, ctx) {
    const tg = target(st, ctx || {});
    if (st.cur == null) { st.cur = tg; st.prev = null; st.mix = 1; }
    else if (tg !== st.cur) { st.prev = st.mix < 0.5 && st.prev ? st.prev : st.cur; st.cur = tg; st.mix = 0; st.switches++; }
    if (st.mix < 1) { st.mix = Math.min(1, st.mix + (dt || 0) / st.fadeSec); if (st.mix >= 1) st.prev = null; }
    return st;
  }
  function set(st, mode) { if (CYCLE.indexOf(mode) < 0) throw new Error('hd2d.set: ' + mode); st.mode = mode; return st; }
  function next(st) { return set(st, CYCLE[(CYCLE.indexOf(st.mode) + 1) % CYCLE.length]); }
  function hex(c) { const n = parseInt(String(c || '#ffffff').replace('#', ''), 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255]; }
  function mulc(a, b) { return [a[0] * b[0] / 255, a[1] * b[1] / 255, a[2] * b[2] / 255]; }
  function mixc(a, b, t) { return [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t]; }
  /* 寵物 tint：sprite × petTint × ambientTint（唔過 LUT） */
  function petColor(g, lumi) { const c = mulc(hex(g.petTint), hex(g.ambientTint)); return lumi ? mulc(c, LUMI) : c; }
  const LUMI = [200, 255, 188];   // 螢絨（隱藏形態，未有專屬美術）：同一次 multiply 入面加螢綠，唔加 tint 次數
  /* rim 權重：w = max(0, n·dir)；scaleX −1（mir<0）時 nx 取反 */
  function rimW(nx, ny, dir, mir) { return Math.max(0, nx * (mir < 0 ? -1 : 1) * dir[0] + ny * dir[1]); }
  /* 雨／weather hook（lighting.addModifier）：light.hd2d＝{variant, weather}；落雨唔曬太陽 */
  function lightModifier() {
    return function (light, ctx) {
      light.hd2d = { variant: variantFor(ctx.hour, ctx.weather), weather: ctx.weather || 'clear' };
      if (ctx.weather === 'rain' && light.beh) light.beh.sunbathe = 0;
      return light;
    };
  }

  // ── 瀏覽器：Scene ──
  function mk(w, h) { const c = document.createElement('canvas'); c.width = Math.max(1, w | 0); c.height = Math.max(1, h | 0); return c; }
  const rgb = (c, a) => a == null ? 'rgb(' + (c[0] | 0) + ',' + (c[1] | 0) + ',' + (c[2] | 0) + ')' : 'rgba(' + (c[0] | 0) + ',' + (c[1] | 0) + ',' + (c[2] | 0) + ',' + a + ')';
  const h01 = (n) => { const s = Math.sin(n * 12.9898 + 78.233) * 43758.5453; return s - Math.floor(s); };

  class Scene {
    constructor(o) {
      o = o || {};
      this.base = o.base || 'art/hd2d/'; this.rimBase = o.rimBase || 'art/rim/';
      this.st = createState(o); this.enabled = o.enabled !== false; this.ready = false; this.error = null;
      this.v = {}; this.rim = {}; this.rimCache = {}; this.layout = null; this.part = null; this.rain = null; this.ripple = null;
      this.ps = []; this.rips = []; this.ripT = 0; this.spawnAcc = 0; this.lastPV = null; this.t = 0;
      this.buf = null; this.bufB = null; this.tint = null; this.rimC = null; this.glow = {};
      this.stat = { draws: 0, tints: 0, rimMask: 0, rimFallback: 0, composites: 0, fades: 0 };
    }
    on() { return this.enabled && this.ready; }
    load() {
      const img = (u) => new Promise((res, rej) => { const im = new Image(); im.onload = () => res(im); im.onerror = () => rej(new Error(u)); im.src = u; });
      const js = (u) => fetch(u).then(r => { if (!r.ok) throw new Error(u + ' ' + r.status); return r.json(); });
      const B = this.base, jobs = [];
      const L = ['sky', 'far', 'mid', 'fore', 'lightmap', 'light_add', 'emissive_blur', 'vignette'];
      ['H1', 'H2', 'H3', 'H4'].forEach(h => {
        const o = this.v[h] = { id: h, img: {} };
        L.forEach(n => jobs.push(img(B + h + '/' + n + '.png').then(im => { o.img[n] = im; })));
        jobs.push(js(B + h + '/grade.json').then(j => { o.g = j; }));
      });
      const r = this.v.H3rain = { id: 'H3rain', img: {}, rain: true };
      ['sky', 'far', 'mid', 'fore'].forEach(n => jobs.push(img(B + 'H3/rain/' + n + '.png').then(im => { r.img[n] = im; })));
      jobs.push(js(B + 'H3/grade_rain.json').then(j => { r.g = j; }));
      jobs.push(js(B + 'layout.json').then(j => { this.layout = j; }));
      jobs.push(Promise.all([js(B + 'particles/particles.json'), img(B + 'particles/particles.png')]).then(([j, im]) => { this.part = { j, im }; }));
      jobs.push(Promise.all([js(B + 'rain/rain_tile.json'), img(B + 'rain/rain_tile.png')]).then(([j, im]) => { this.rain = { j, im }; }));
      jobs.push(Promise.all([js(B + 'rain/ripple.json'), img(B + 'rain/ripple.png')]).then(([j, im]) => { this.ripple = { j, im }; }));
      ['sprout', 'radiant', 'soft', 'sprout_live', 'radiant_live', 'soft_live'].forEach(f => jobs.push(Promise.all([js(this.rimBase + 'rim_' + f + '.json'), img(this.rimBase + 'rim_' + f + '.png')]).then(([j, im]) => { this.rim[f] = { j, im }; }).catch(() => { /* rim mask 可選：冇就用 alpha 位移 fallback */ })));
      return Promise.all(jobs).then(() => {
        ['lightmap', 'light_add', 'emissive_blur', 'vignette'].forEach(n => { r.img[n] = this.v.H3.img[n]; });   // 雨：lightmap 等沿用 H3
        this.buf = mk(W, H); this.bufB = mk(W, H); this.tint = mk(96, 112); this.rimC = mk(96, 112);
        this.rainPat = this.rain ? Object.keys(this.rain.j.frames).sort().map(k => { const f = this.rain.j.frames[k].frame, c = mk(f.w, f.h); c.getContext('2d').drawImage(this.rain.im, f.x, f.y, f.w, f.h, 0, 0, f.w, f.h); return c; }) : null;
        this.ready = true;
      }).catch(e => { this.error = String(e && e.message || e); this.ready = false; });
    }
    set(mode) { set(this.st, mode); return this.current(); }
    next() { next(this.st); return this.current(); }
    current() { const s = this.st; return { mode: s.mode, variant: s.cur, prev: s.prev, mix: +s.mix.toFixed(3), fading: s.mix < 1, ready: this.ready, enabled: this.enabled, error: this.error, label: LABEL[s.mode] + (s.mode === 'auto' && s.cur ? '（' + s.cur + '）' : ''), overlays: engineOverlays(this.on() ? s.cur : null), switches: s.switches }; }
    update(dt, ctx) { this.t += dt; update(this.st, dt, ctx); }
    grade(v) { return (this.v[v || this.st.cur] || this.v.H3).g; }

    /* 寵物 tint＋rim（每次畫寵物只叫一次；生命感五官已喺之前合成入 src）。rimKey：'soft'（motion atlas）／'soft_live'（生命感 noface atlas）。
       每次 ≤4 合成：sprite、multiply、destination-in、rim）。src={img,sx,sy,sw,sh,px,py,bud}；o={mir, form, frame, quality} */
    tintPet(src, o) {
      o = o || {}; this.stat.tints++;
      const s = this.st, gc = this.grade(s.cur), gp = s.prev && s.mix < 1 ? this.grade(s.prev) : null;
      const col = gp ? mixc(petColor(gp, o.lumi), petColor(gc, o.lumi), s.mix) : petColor(gc, o.lumi);
      const T = this.tint, g = T.getContext('2d'), PX = 48, PY = 100, ox = PX - src.px, oy = PY - src.py;
      g.setTransform(1, 0, 0, 1, 0, 0); g.globalAlpha = 1; g.imageSmoothingEnabled = false; g.globalCompositeOperation = 'source-over'; g.clearRect(0, 0, 96, 112);
      g.drawImage(src.img, src.sx, src.sy, src.sw, src.sh, ox, oy, src.sw, src.sh);
      g.globalCompositeOperation = 'multiply'; g.fillStyle = rgb(col); g.fillRect(ox, oy, src.sw, src.sh);
      g.globalCompositeOperation = 'destination-in'; g.drawImage(src.img, src.sx, src.sy, src.sw, src.sh, ox, oy, src.sw, src.sh);
      const low = o.quality === 'low' || o.quality === 'off';
      if (!(low && CFG.rimLowOff) && gc.rim && gc.rim.intensity > 0) {
        const rm = this.rimFor(o.rimKey || o.form, o.frame, s.cur, o.mir || 1);
        g.globalCompositeOperation = 'source-atop'; g.globalAlpha = Math.min(1, gc.rim.intensity) * (gp ? 0.5 + 0.5 * s.mix : 1);
        if (rm) { this.stat.rimMask++; g.drawImage(rm.c, rm.x, rm.y, src.sw, src.sh, ox, oy, src.sw, src.sh); }
        else { this.stat.rimFallback++; this.rimFallback(g, src, ox, oy, gc.rim, o.mir || 1); }
        g.globalAlpha = 1;
      }
      g.globalCompositeOperation = 'source-over';
      return { img: T, sx: ox, sy: oy, sw: src.sw, sh: src.sh, px: src.px, py: src.py, bud: src.bud, name: src.name };
    }
    /* 方向 rim atlas（按 form×款×朝向 lazy 預計一次）：rim 色、alpha = 255·w */
    rimFor(form, frame, v, mir) {
      const R = this.rim[form]; if (!R || !frame) return null;
      const f = R.j.frames[frame]; if (!f) return null;
      const g = this.grade(v), key = form + '|' + v + '|' + (mir < 0 ? -1 : 1);
      let c = this.rimCache[key];
      if (c === undefined) {
        try {
          c = mk(R.im.width, R.im.height); const x = c.getContext('2d'); x.drawImage(R.im, 0, 0);
          const d = x.getImageData(0, 0, c.width, c.height), p = d.data, rc = hex(g.rim.color), dir = g.rim.dir;
          for (let i = 0; i < p.length; i += 4) {
            if (!p[i + 3]) continue;
            const w = rimW(p[i] / 127.5 - 1, p[i + 1] / 127.5 - 1, dir, mir);
            p[i] = rc[0]; p[i + 1] = rc[1]; p[i + 2] = rc[2]; p[i + 3] = Math.round(255 * Math.min(1, w * 1.15));
          }
          x.putImageData(d, 0, 0);
        } catch (e) { c = null; }   // file:// 污染畫布 → fallback
        this.rimCache[key] = c;
      }
      return c ? { c, x: f.frame.x, y: f.frame.y } : null;
    }
    /* 冇 rim mask（例：生命感 noface atlas 未補 rim）：sprite − sprite 向光方向位移 1px＝向光內緣 */
    rimFallback(g, src, ox, oy, rim, mir) {
      const R = this.rimC, r = R.getContext('2d'), dx = Math.round(rim.dir[0] * (mir < 0 ? -1 : 1)), dy = Math.round(rim.dir[1]);
      r.setTransform(1, 0, 0, 1, 0, 0); r.globalAlpha = 1; r.imageSmoothingEnabled = false; r.globalCompositeOperation = 'source-over'; r.clearRect(0, 0, 96, 112);
      r.drawImage(src.img, src.sx, src.sy, src.sw, src.sh, ox, oy, src.sw, src.sh);
      r.globalCompositeOperation = 'destination-out'; r.drawImage(src.img, src.sx, src.sy, src.sw, src.sh, ox - dx, oy - dy, src.sw, src.sh);
      r.globalCompositeOperation = 'source-in'; r.fillStyle = rim.color; r.fillRect(0, 0, 96, 112); r.globalCompositeOperation = 'source-over';
      g.drawImage(R, 0, 0);
    }
    glowSprite(col) {
      const key = (col[0] >> 3) + '_' + (col[1] >> 3) + '_' + (col[2] >> 3); let g = this.glow[key];
      if (!g) { g = mk(32, 32); const x = g.getContext('2d'), gr = x.createRadialGradient(16, 16, 0, 16, 16, 16); gr.addColorStop(0, rgb(col, 1)); gr.addColorStop(0.3, rgb(col, 0.45)); gr.addColorStop(0.65, rgb(col, 0.12)); gr.addColorStop(1, rgb(col, 0)); x.fillStyle = gr; x.fillRect(0, 0, 32, 32); this.glow[key] = g; }
      return g;
    }

    /* 一款完整合成到 1x 畫布（FORMAT.md §2） */
    /* P1-4：靜態層 cache——每款（H1…H4／H3rain＝時段＋雨）各自一張 offscreen；key＝該層用到嘅整數視差位移（＋畫質）。
       時段／雨轉款＝換另一套 cache；視差只喺整數位移變先重建（約每秒幾次），其餘 frame 一張 drawImage 搞掂。 */
    layer(v, name, key, build) {
      const C = this.lc || (this.lc = {}), V = C[v] || (C[v] = {});
      let e = V[name]; if (!e) e = V[name] = { c: mk(W, H), key: null };
      if (e.key !== key) {
        const g = e.c.getContext('2d'); g.setTransform(1, 0, 0, 1, 0, 0); g.globalCompositeOperation = 'source-over'; g.globalAlpha = 1; g.imageSmoothingEnabled = false; g.clearRect(0, 0, W, H);
        build(g); e.key = key; this.stat.cacheBuilds = (this.stat.cacheBuilds || 0) + 1;
      } else this.stat.cacheHits = (this.stat.cacheHits || 0) + 1;
      return e.c;
    }
    compose(x, v, c) {
      const o = this.v[v], g = o.g, I = o.img, offs = c.offs, q = c.quality;
      const P = (oi) => [Math.round(-MX + offs[oi][0]), Math.round(-MY + offs[oi][1])];
      const put = (im, oi, a) => { if (a != null) x.globalAlpha = a; const p = P(oi); x.drawImage(im, p[0], p[1]); x.globalAlpha = 1; this.stat.composites++; };
      x.globalCompositeOperation = 'source-over'; x.globalAlpha = 1; x.imageSmoothingEnabled = false;
      const bloomA = Math.min(1, g.bloom ? g.bloom.intensity : 0.5), addA = o.rain ? CFG.rainLightAdd : 1;
      if (this.cacheOn !== false) {
        const p0 = P(0), p1 = P(1), p2 = P(2);
        const back = this.layer(v, 'back', p0 + '|' + p1 + '|' + p2, (b) => { b.drawImage(I.sky, p0[0], p0[1]); b.drawImage(I.far, p1[0], p1[1]); b.drawImage(I.mid, p2[0], p2[1]); });
        x.drawImage(back, 0, 0); this.stat.composites++;
        put(c.pet, 2);                                                 // 寵物＋引擎動態物件（L2，透明底）
        put(I.fore, 3);
        x.globalCompositeOperation = 'multiply'; put(I.lightmap, 2);
        const add = this.layer(v, 'add', p2 + '|' + (q === 'off' ? 0 : 1), (b) => { b.globalAlpha = addA; b.drawImage(I.light_add, p2[0], p2[1]); b.globalAlpha = 1; if (q !== 'off') { b.globalCompositeOperation = 'lighter'; b.globalAlpha = bloomA; b.drawImage(I.emissive_blur, p2[0], p2[1]); b.globalAlpha = 1; } });
        x.globalCompositeOperation = 'lighter'; x.drawImage(add, 0, 0); this.stat.composites++;
      } else {                                                         // ?hdcache=0：逐層（對照／bench 用）
        put(I.sky, 0); put(I.far, 1); put(I.mid, 2);
        put(c.pet, 2);
        put(I.fore, 3);
        x.globalCompositeOperation = 'multiply'; put(I.lightmap, 2);
        x.globalCompositeOperation = 'lighter'; put(I.light_add, 2, addA);
        if (q !== 'off') put(I.emissive_blur, 2, bloomA);
      }
      // 引擎光：寵物燈泡 glow（bulbGlowTint）、球、事件
      x.imageSmoothingEnabled = true;
      const bt = hex(g.bulbGlowTint || '#ffe9a0');
      for (const l of c.lights || []) {
        const col = l.bud ? mixc(l.col, bt, 0.6) : l.col, r = l.r;
        x.globalAlpha = Math.max(0, Math.min(1, l.a)); x.drawImage(this.glowSprite(col), l.x - r, l.y - r, r * 2, r * 2);
      }
      x.globalAlpha = 1;
      // 粒子（lighter：螢火／光塵／金塵；花瓣 source-over）
      if (q !== 'off') this.drawParticles(x, g, offs);
      x.imageSmoothingEnabled = false;
      x.globalCompositeOperation = 'source-over';
      if (o.rain) this.drawRain(x, offs, q);                           // 雨（FORMAT §7）：emissive_blur 之後、fog 之前，唔食 lightmap
      if (g.fog && g.fog.density > 0) { x.globalAlpha = g.fog.density; x.fillStyle = g.fog.color; x.fillRect(0, 0, W, H); x.globalAlpha = 1; }
      if (c.dim > 0.005) { x.fillStyle = 'rgba(8,12,44,' + Math.min(0.6, c.dim).toFixed(3) + ')'; x.fillRect(0, 0, W, H); }   // 睡眠／飢餓／不適暗角
      x.drawImage(I.vignette, 0, 0);
    }
    stepParticles(dt, g, q) {
      const P = g.particles; if (!P || !this.part) { this.ps.length = 0; return; }
      const type = P.type, pv = this.st.cur;
      if (this.lastPV !== pv) { this.lastPV = pv; this.ps = this.ps.filter(p => p.type === type); const n = Math.round((P.rate || 0) * 5); for (let i = 0; i < n; i++) this.spawnP(type, true); }
      const max = q === 'low' ? CFG.particleMax / 2 : CFG.particleMax;
      this.spawnAcc += dt * (P.rate || 0) * (q === 'low' ? 0.5 : 1);
      while (this.spawnAcc >= 1) { this.spawnAcc -= 1; if (this.ps.length < max) this.spawnP(type, false); }
      for (const p of this.ps) {
        p.age += dt;
        if (type === 'petal') { p.x += (p.vx + Math.sin(p.age * 1.6 + p.ph) * 6) * dt; p.y += p.vy * dt; }
        else if (type === 'firefly') { p.x += Math.sin(p.age * 0.7 + p.ph) * 4 * dt; p.y += Math.cos(p.age * 0.5 + p.ph * 2) * 3 * dt; }
        else { p.x += (p.vx + Math.sin(p.age * 0.9 + p.ph) * 2) * dt; p.y += p.vy * dt; }
      }
      this.ps = this.ps.filter(p => p.age < p.life && p.y < H + 10 && p.y > -12);
    }
    spawnP(type, warm) {
      const r = (k) => h01(this.t * 13.1 + this.ps.length * 7.7 + k + Math.random());
      const L = { mote: 6, gold: 5, petal: 8, firefly: 7 }[type] || 6;
      const p = { type, age: warm ? r(1) * L * 0.8 : 0, life: L, ph: r(2) * 6.28, x: r(3) * W, y: 0, vx: 0, vy: 0, fr: Math.floor(r(4) * 6) };
      if (type === 'mote') { p.y = 150 + r(5) * 190; p.vy = -(2 + r(6) * 2); }
      else if (type === 'gold') { p.y = 120 + r(5) * 200; p.vx = 2 + r(6) * 2; p.vy = -(1.5 + r(7) * 1.5); }
      else if (type === 'petal') { p.y = warm ? r(5) * 300 : -8; p.vx = 3 + r(6) * 4; p.vy = 8 + r(7) * 4; }
      else { p.y = 120 + r(5) * 210; }
      this.ps.push(p);
    }
    drawParticles(x, g, offs) {
      const P = g.particles; if (!P || !this.part || !this.ps.length) return;
      const T = this.part.j.types && this.part.j.types[P.type], F = this.part.j.frames, fps = T ? T.fps : 6;
      const add = P.type !== 'petal'; x.globalCompositeOperation = add ? 'lighter' : 'source-over'; x.imageSmoothingEnabled = false;
      for (const p of this.ps) {
        const u = p.age / p.life, fade = Math.min(1, u / 0.15, (1 - u) / 0.2);
        const br = P.type === 'firefly' ? 0.45 + 0.55 * Math.max(0, Math.sin(p.age * 2.2 + p.ph * 3)) : 1;
        const names = T ? T.frames : [P.type + '_01']; const f = F[names[(p.fr + Math.floor(p.age * fps)) % names.length]]; if (!f) continue;
        const px = Math.round(p.x + offs[2][0] - 4), py = Math.round(p.y + offs[2][1] - 4);
        if (add && P.type !== 'gold') { x.imageSmoothingEnabled = true; x.globalAlpha = 0.35 * fade * br; x.drawImage(this.glowSprite(hex(P.color)), px - 4, py - 4, 16, 16); x.imageSmoothingEnabled = false; }
        x.globalAlpha = Math.max(0, fade * br); x.drawImage(this.part.im, f.frame.x, f.frame.y, f.frame.w, f.frame.h, px, py, f.frame.w, f.frame.h);
      }
      x.globalAlpha = 1; x.globalCompositeOperation = 'source-over';
    }
    stepRain(dt, on) {
      if (!on || !this.ripple) { this.rips.length = 0; return; }
      const wk = this.layout && this.layout.ground && this.layout.ground.walkable || [[17, 278], [178, 278], [178, 318], [17, 318]];
      this.ripT -= dt;
      if (this.ripT <= 0) { this.ripT = 0.1 + Math.random() * 0.2; this.rips.push({ x: wk[0][0] + Math.random() * (wk[1][0] - wk[0][0]), y: wk[0][1] + Math.random() * (wk[2][1] - wk[0][1]), age: 0 }); }
      for (const r of this.rips) r.age += dt; this.rips = this.rips.filter(r => r.age < 0.4);
    }
    drawRain(x, offs, q) {
      if (!this.rainPat) return;
      const fps = this.rain.j.meta.fps || 12, fr = Math.floor(this.t * fps) % this.rainPat.length;
      // 4 幀循環（每幀向下 16px、無縫）；兩層：1x 速／0.6x 速＋偏移 32px
      const layer = (spd, ox, a) => {
        const c = this.rainPat[Math.floor(this.t * fps * spd) % this.rainPat.length] || this.rainPat[fr], pat = x.createPattern(c, 'repeat');
        x.save(); x.globalCompositeOperation = 'source-over'; x.globalAlpha = a; x.translate(ox + Math.round(offs[3][0] * 0.5), ox ? 32 : 0); x.fillStyle = pat; x.fillRect(-ox - 64, -64, W + 128, H + 128); x.restore();
      };
      layer(1, 0, CFG.rainAlpha); if (q !== 'low' && q !== 'off') layer(0.6, 32, CFG.rainAlpha * 0.55);
      const RJ = this.ripple.j, names = Object.keys(RJ.frames).sort(), pv = RJ.meta.pivot || [8, 4];
      x.globalAlpha = 0.8;
      for (const r of this.rips) { const f = RJ.frames[names[Math.min(names.length - 1, Math.floor(r.age * (RJ.meta.fps || 10)))]].frame; x.drawImage(this.ripple.im, f.x, f.y, f.w, f.h, Math.round(r.x - pv[0] + offs[2][0]), Math.round(r.y - pv[1]), f.w, f.h); }
      x.globalAlpha = 1;
    }
    /* 合成到顯示畫布：1x 合成 → 整數倍 Nearest 放大。crossfade 時兩套各合成一次再 alpha 混 */
    draw(ctx, k, c) {
      this.stat.draws++;
      const s = this.st, dt = c.dt || 0;
      this.stepParticles(dt, this.grade(s.cur), c.quality); this.stepRain(dt, s.cur === 'H3rain' || s.prev === 'H3rain');
      const A = this.buf.getContext('2d');
      this.compose(A, s.cur, c);
      if (s.prev && s.mix < 1 && this.v[s.prev]) {
        this.stat.fades++;
        const B = this.bufB.getContext('2d'); this.compose(B, s.prev, c);
        B.globalCompositeOperation = 'source-over'; B.globalAlpha = s.mix; B.drawImage(this.buf, 0, 0); B.globalAlpha = 1;
        ctx.imageSmoothingEnabled = false; ctx.drawImage(this.bufB, 0, 0, W * k, H * k);
      } else { ctx.imageSmoothingEnabled = false; ctx.drawImage(this.buf, 0, 0, W * k, H * k); }
    }
  }

  /* 開發用切換：window.__qa.hd2d（set／current／next／weather／enable） */
  function install(G, NS) {
    const P = NS.data.PARAMS, qs = new URLSearchParams(location.search);
    const sc = new Scene({ base: P.art.base + 'hd2d/', rimBase: P.art.base + 'rim/', enabled: qs.get('hd2d') !== '0' && qs.get('hd') !== '0' && P.art.hd2d !== false });
    G.hd = sc; G.renderer.hd = sc;
    sc.cacheOn = qs.get('hdcache') !== '0';                              // P1-4：?hdcache=0 停用靜態層 cache（對照用）
    NS.light.addModifier('hd2d', lightModifier());
    if (qs.get('weather')) G.weather = qs.get('weather');
    if (qs.get('scene') && CYCLE.indexOf(qs.get('scene')) >= 0) sc.set(qs.get('scene'));   // ?scene=H1|H2|H3|H3rain|H4
    G.hdReady = sc.load();
    window.__qa = window.__qa || {};
    window.__qa.hd2d = {
      set(m) { const r = sc.set(m); if (G.dev) G.dev.sync && G.dev.sync(); return r; }, next() { return sc.next(); }, current() { return sc.current(); },
      weather(w) { if (w !== undefined) G.weather = w || null; return G.weather || 'clear'; },
      enable(on) { sc.enabled = on !== false; return sc.enabled; },
      skipFade() { sc.st.mix = 1; sc.st.prev = null; }, stat() { return Object.assign({}, sc.stat); }, cache(on) { if (on !== undefined) { sc.cacheOn = on !== false; sc.lc = {}; } return { on: sc.cacheOn !== false, variants: Object.keys(sc.lc || {}), builds: sc.stat.cacheBuilds || 0, hits: sc.stat.cacheHits || 0 }; }, CYCLE: CYCLE.slice(), LABEL,
    };
    return sc;
  }

  return { W, H, MX, MY, LW, LH, VARIANTS, CYCLE, LABEL, CFG, variantFor, baseOf, engineOverlays, createState, update, set, next, target, petColor, rimW, hex, lightModifier, Scene, install };
});
