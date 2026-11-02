/* 《微光小圃》 walkv3.js — #83：6b 散步 walk_bg V3（遊美 WALK_6B_V3.md／walk6b_v3.json）。原創代碼。
   300×360 @3x 層頂替原 walk_bg（同框 200×240 CSS）；時段跟現實時間 day 06–17、dusk 17–19、night 19–06。
   燈光已烘入層（lightmap／light_add／bloom／emissive）；即時：stone_glow pulse、mist drift、flares、粒子（花粉／金塵／螢火蟲）、寵物光池（× petGlow）。
   寵物 walk clip 係 DOM（照 6b.1），所以疊層拆做：後 canvas（sky→far→haze→mid→stone_glow→mist→pet_pool）＋ DOM 寵物／deco ＋
   前 canvas：fore（normal）→ lightmap（mix-blend multiply）→ add（plus-lighter：light_add、bloom、emissive、flares、粒子）→ top（fog、vignette）。 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else { root.Glimmer = root.Glimmer || {}; root.Glimmer.walkv3 = factory(); }
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';
  const W3 = 300, H3 = 360, K = 3;
  const LAYERS = ['sky', 'far', 'haze_far', 'mid', 'mist', 'fore', 'lightmap', 'light_add', 'bloom', 'emissive', 'vignette'];
  function variantOf(h) { h = ((+h % 24) + 24) % 24; return h >= 6 && h < 17 ? 'day' : h >= 17 && h < 19 ? 'dusk' : 'night'; }
  /* 踏腳石：PATH 由近到遠，tile 2i＝第 i 粒（近→遠）；grade stones 由遠到近 */
  function stoneOf(tile, n) { const i = Math.floor(tile / 2); return { cur: Math.min(n - 1, i), idx: (k) => n - 1 - k }; }
  const hex = (h) => { h = String(h || '#ffffff').replace('#', ''); return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)]; };
  function make(G, base, fxBase) {
    const img = (u) => new Promise((ok, no) => { const i = new Image(); i.onload = () => ok(i); i.onerror = () => no(new Error('img ' + u)); i.src = u; });
    const js = (u) => fetch(u).then(r => { if (!r.ok) throw new Error(u + ' ' + r.status); return r.json(); });
    const V = {}, ST = { loads: 0, draws: 0, missing: [], variant: null, parts: 0, flares: 0, pool: 0, stone: -1 };
    let FX = null, PT = null, STONE = null;
    const fxP = Promise.all([js(fxBase + 'fx_glow_v3@3x.json'), img(fxBase + 'fx_glow_v3@3x.png'), js(fxBase + 'particles_v3@3x.json'), img(fxBase + 'particles_v3@3x.png'), img(base + 'walk_bg/stone_glow@3x.png')])
      .then(([a, ai, b, bi, s]) => { FX = { f: a.frames, im: ai }; PT = { f: b.frames, im: bi }; STONE = s; }).catch(e => ST.missing.push(String(e.message)));
    function need(v) {
      if (V[v]) return V[v].ready ? V[v] : null;
      const o = V[v] = { ready: false, im: {}, g: null };
      Promise.all([js(base + 'walk_bg/' + v + '/grade.json'), fxP].concat(LAYERS.map(n => img(base + 'walk_bg/' + v + '/x3/' + n + '@3x.png').then(i => { o.im[n] = i; }).catch(() => ST.missing.push(v + '/' + n)))))
        .then(([g]) => { o.g = g; o.ready = true; ST.loads++; }).catch(e => ST.missing.push(v + ': ' + e.message));
      return null;
    }
    const tintC = {};
    function tinted(sheet, name, tint) {   // glow／flare 用 tint 預先上色（cache）
      const k = name + tint; if (tintC[k]) return tintC[k]; const f = sheet.f[name]; if (!f) return null;
      const c = document.createElement('canvas'); c.width = f.w; c.height = f.h; const g = c.getContext('2d'); g.drawImage(sheet.im, f.x, f.y, f.w, f.h, 0, 0, f.w, f.h);
      if (tint) { g.globalCompositeOperation = 'source-atop'; g.globalAlpha = 0.85; g.fillStyle = tint; g.fillRect(0, 0, f.w, f.h); }
      return (tintC[k] = c);
    }
    const parts = [], decoGlow = {};
    let last = 0, raf = 0, CV = null, info = null;
    function canvases(box, back) {
      const mk = (id, blend, before) => { let c = box.querySelector('[data-v3w="' + id + '"]'); if (!c) { c = document.createElement('canvas'); c.width = W3; c.height = H3; c.dataset.v3w = id; c.dataset.testid = 'l6b-v3-' + id;
        c.style.cssText = 'position:absolute;left:0;top:0;width:200px;height:240px;pointer-events:none;image-rendering:auto;' + (blend ? 'mix-blend-mode:' + blend + ';' : ''); box.appendChild(c); } return c; };
      back.width = W3; back.height = H3; back.style.imageRendering = 'auto'; back.dataset.v3 = '1';
      return { back, fore: mk('fore'), mul: mk('mul', 'multiply'), add: mk('add', 'plus-lighter'), top: mk('top') };
    }
    function step(o, dt) {
      const em = (o.g.v3.emitters || []);
      for (const e of em) { e._acc = (e._acc || 0) + dt * (e.rate || 1); const n = parts.filter(p => p.e === e).length;
        while (e._acc >= 1) { e._acc -= 1; if (n >= (e.max || 10)) break; const r = e.rect || [0, 0, 100, 120], L = e.life || [3, 6];
          parts.push({ e, x: r[0] + Math.random() * (r[2] - r[0]), y: r[1] + Math.random() * (r[3] - r[1]), vx: e.vx ? e.vx[0] + Math.random() * (e.vx[1] - e.vx[0]) : 0, vy: e.vy ? e.vy[0] + Math.random() * (e.vy[1] - e.vy[0]) : 0, t: 0, life: L[0] + Math.random() * (L[1] - L[0]), ph: Math.random() * 6.28 }); } }
      for (let i = parts.length - 1; i >= 0; i--) { const p = parts[i]; p.t += dt; p.x += p.vx * dt + (p.e.sway ? Math.sin(p.t * 1.7 + p.ph) * p.e.sway * dt : 0); p.y += p.vy * dt; if (p.t > p.life || !em.includes(p.e)) parts.splice(i, 1); }
    }
    function draw(now) {
      if (!CV || !info) return; const v = variantOf(G.hour ? G.hour() : new Date().getHours()), o = need(v); ST.variant = v;
      if (!o) return; const dt = Math.min(0.1, last ? (now - last) / 1000 : 0); last = now; step(o, dt); ST.draws++;
      const g3 = o.g.v3, t = now / 1000, I = o.im, d = info();
      // 後
      let c = CV.back.getContext('2d'); c.setTransform(1, 0, 0, 1, 0, 0); c.globalCompositeOperation = 'source-over'; c.globalAlpha = 1; c.clearRect(0, 0, W3, H3);
      for (const n of ['sky', 'far', 'haze_far', 'mid']) if (I[n]) c.drawImage(I[n], 0, 0);
      const sg = g3.stoneGlow; if (sg && STONE && d) { const n = sg.stones.length, cur = Math.min(n - 1, Math.floor(d.tile / 2)); ST.stone = cur; c.globalCompositeOperation = 'lighter';
        for (let k = 0; k <= cur; k++) { const s = sg.stones[n - 1 - k], pul = k === cur ? 1 + (sg.pulse ? sg.pulse.amp * Math.sin(t * 6.283 * sg.pulse.hz) : 0) : 1; c.globalAlpha = Math.max(0, Math.min(1, (k === cur ? sg.alpha : 0.3) * pul));
          c.drawImage(STONE, s[0] * K - STONE.width / 2, s[1] * K - STONE.height / 2); } c.globalCompositeOperation = 'source-over'; c.globalAlpha = 1; }
      if (I.mist) { const dx = ((t * 2) % W3 + W3) % W3; c.drawImage(I.mist, dx, 0); c.drawImage(I.mist, dx - W3, 0); }
      const pl = g3.petLight; if (pl && FX && d && d.pet) { const pool = tinted(FX, 'pet_pool', pl.tint), gl = G.v3 && G.v3.petGlow ? G.v3.petGlow(performance.now()) : 1, a = (pl.intensity || 0.3) * gl;
        ST.pool = +a.toFixed(3); if (pool && a > 0.004) { const [w, h] = pl.size3x || [150, 60]; c.globalCompositeOperation = 'lighter'; c.globalAlpha = Math.min(1, a); c.drawImage(pool, d.pet[0] * K - w / 2, d.pet[1] * K - h / 2 + 6, w, h); c.globalCompositeOperation = 'source-over'; c.globalAlpha = 1; } }
      // 前
      c = CV.fore.getContext('2d'); c.clearRect(0, 0, W3, H3); if (I.fore) c.drawImage(I.fore, 0, 0);
      c = CV.mul.getContext('2d'); c.clearRect(0, 0, W3, H3); if (I.lightmap) c.drawImage(I.lightmap, 0, 0);
      c = CV.add.getContext('2d'); c.clearRect(0, 0, W3, H3); c.globalCompositeOperation = 'lighter';
      if (I.light_add) c.drawImage(I.light_add, 0, 0);
      if (I.bloom) { const b = (o.g.bloom && o.g.bloom.intensity) || 0.3; c.globalAlpha = Math.min(1, b); c.drawImage(I.bloom, 0, 0); c.globalAlpha = 1; }
      if (I.emissive) { const fl = g3.lantern && g3.lantern.flicker; c.globalAlpha = fl ? Math.max(0, 1 - fl.amp + fl.amp * Math.sin(t * 6.283 * fl.hz)) : 1; c.drawImage(I.emissive, 0, 0); c.globalAlpha = 1; }
      ST.flares = 0; if (FX) for (const f of (g3.flares || [])) { const fr = 'flare_' + (f.size || 'm') + '_0' + (1 + (Math.floor(t * (f.fps || 2)) % 6)), im = tinted(FX, fr, f.tint); if (!im) continue; c.globalAlpha = Math.min(1, f.intensity || 0.5); c.drawImage(im, f.pos[0] * K - im.width / 2, f.pos[1] * K - im.height / 2); ST.flares++; }
      ST.parts = parts.length; if (PT && FX) for (const p of parts) { const e = p.e, fade = Math.min(1, p.t / 0.6, (p.life - p.t) / 0.8), a = Math.max(0, (e.add || 0.5) * fade);
        const gw = tinted(FX, e.glow || 'glow_12', e.tint); if (gw) { c.globalAlpha = a; c.drawImage(gw, p.x * K - gw.width / 2, p.y * K - gw.height / 2); }
        const sp = tinted(PT, e.type + '_0' + (1 + (Math.floor(p.t * 8 + p.ph) % 6)), null); if (sp) { c.globalAlpha = a; c.drawImage(sp, p.x * K - sp.width / 2, p.y * K - sp.height / 2); } }
      c.globalAlpha = 1; c.globalCompositeOperation = 'source-over';
      c = CV.top.getContext('2d'); c.clearRect(0, 0, W3, H3);
      if (o.g.fog && o.g.fog.density) { c.globalAlpha = Math.min(0.3, o.g.fog.density); c.fillStyle = o.g.fog.color || '#ffffff'; c.fillRect(0, 0, W3, H3); c.globalAlpha = 1; }
      if (I.vignette) c.drawImage(I.vignette, 0, 0);
      CV.back.dataset.art = '6b:walk_bg_v3'; CV.back.dataset.variant = v; delete CV.back.dataset.ph;
    }
    function loop(now) { raf = 0; if (!CV || !CV.back.isConnected) { CV = null; return; } try { draw(now); } catch (e) { ST.err = String(e && e.message); } raf = requestAnimationFrame(loop); }
    return {
      ST, variantOf, need, deco: (name) => base + 'deco/deco_' + name + '_v3@3x.png', decoGlow: (name) => base + 'deco/deco_' + name + '_glow@3x.png',
      ready: () => { const o = need(variantOf(G.hour ? G.hour() : new Date().getHours())); return !!o; },
      attach(box, back, infoFn) { CV = canvases(box, back); info = infoFn; parts.length = 0; last = 0; if (!raf) raf = requestAnimationFrame(loop); draw(performance.now()); },
      front: () => CV ? [CV.fore, CV.mul, CV.add, CV.top] : [],
    };
  }
  return { W3, H3, variantOf, stoneOf, make, hex };
});
