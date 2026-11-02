/* 《微光小圃》 housev3.js — #83：屋仔 V3-A 光影（遊美 HOUSE_V3.md／house_v3.json／furniture_v3.json／souvenir_v3.json）。原創代碼。
   房間喺 @3x（585×1266）合成，再縮落 390×844（smooth）。幾何／slot／pivot 同 4b 一樣（1x art 座標 ×3）；
   燈光預烘：x3 sky far mid floor_reflect fore lightmap light_add emissive bloom vignette；即時：燈 lift／pool／halo／flare、窗光 beam＋patch（跟窗 slot 家具）、
   紀念品光、寵物光（× petGlow：醒 1／sleepy .6／瞓床 0；燈、窗光、手信光唔熄）、浮塵、倒影（家具）、霧。
   窗光喺寵物身只加 40%（grade.v3.windowBeam.petAtten .6 → destination-out 寵物剪影）。 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else { root.Glimmer = root.Glimmer || {}; root.Glimmer.housev3 = factory(); }
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';
  const K = 3, SW = 585, SH = 1266, LW = 669, LH = 1338;
  const LAYERS = ['sky', 'far', 'mid', 'floor_reflect', 'fore', 'lightmap', 'light_add', 'bloom', 'emissive', 'vignette'];
  const houseState = (p, sleepy) => (p && p.mode === 'sleep' ? 'sleep' : sleepy ? 'sleepy' : 'awake');
  function inPoly(x, y, P) { let c = false; for (let i = 0, j = P.length - 1; i < P.length; j = i++) { const a = P[i], b = P[j]; if ((a[1] > y) !== (b[1] > y) && x < (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]) + a[0]) c = !c; } return c; }
  function flick(fl, t, ph) { if (!fl) return 1; const s = Math.sin(t * 6.283 * (fl.hz || 0.3) + (ph || 0)); if (fl.type === 'glint') return Math.max(0, 0.55 + 0.45 * Math.pow(Math.max(0, s), 6) * (fl.amp || 1) * 2 - 0.1); if (fl.type === 'twinkle') return 1 - (fl.amp || 0.3) * (0.5 + 0.5 * s); return 1 - (fl.amp || 0.05) + (fl.amp || 0.05) * s; }
  function make(C) {
    const { G, NS, base } = C;
    const img = (u) => new Promise((ok, no) => { const i = new Image(); i.onload = () => ok(i); i.onerror = () => no(new Error('img ' + u)); i.src = u; });
    const js = (u) => fetch(u).then(r => { if (!r.ok) throw new Error(u + ' ' + r.status); return r.json(); });
    const ST = { loads: 0, draws: 0, missing: [], pool: 0, halos: 0, lamp: 0, win: null, sv: 0, parts: 0, glow: { tr: 1, kid: 1 }, fallback: 0, reflect: 0, ao: 0 };
    const I = {}, R = {}; let FV = null, SV = null, HJ = null;
    const im = (f) => { if (!f) return null; if (I[f]) return I[f] === 1 ? null : I[f]; I[f] = 1; img(base + f).then(i => { I[f] = i; }).catch(() => { ST.missing.push(f); }); return null; };
    const meta = Promise.all([js(base + 'house_v3.json'), js(base + 'furniture_v3.json'), js(base + 'souvenir_v3.json')]).then(([h, f, s]) => { HJ = h; FV = f; SV = s; }).catch(e => ST.missing.push(String(e.message)));
    function need(room, v) {
      const k = room + ':' + v; if (R[k]) return R[k].ready ? R[k] : null;
      const o = R[k] = { ready: false, im: {}, g: null }, d = 'rooms/' + room + '/' + v + '/';
      Promise.all([js(base + d + 'grade.json'), meta].concat(LAYERS.map(n => img(base + d + 'x3/' + n + '@3x.png').then(i => { o.im[n] = i; }).catch(() => ST.missing.push(d + n)))))
        .then(([g]) => { o.g = g; o.ready = true; ST.loads++; }).catch(e => ST.missing.push(k + ': ' + e.message));
      return null;
    }
    const V3 = NS.v3, now0 = () => performance.now();
    const GL = { tr: V3 ? new V3.Glow('awake', 0) : null, kid: V3 ? new V3.Glow('awake', 0) : null };
    const tmp = {}; const cv = (k, w, h) => { let c = tmp[k]; if (!c) { c = tmp[k] = document.createElement('canvas'); c.width = w; c.height = h; } return c; };
    const parts = []; let lastT = 0;
    const scene = () => G.hd2dv3 || null;
    const tintFx = (name, tint) => { const s = scene(); return s && s.tinted ? s.tinted(name, tint) : null; };
    function stepParts(g3, dt) {
      for (const e of (g3.emitters || [])) {
        e._acc = (e._acc || 0) + dt * (e.rate || 0.3); const n = parts.filter(p => p.e === e).length;
        while (e._acc >= 1) { e._acc -= 1; if (n >= (e.max || 6)) break; let x = 0, y = 0;
          if (e.polygon) { const xs = e.polygon.map(p => p[0]), ys = e.polygon.map(p => p[1]); for (let i = 0; i < 12; i++) { x = Math.min(...xs) + Math.random() * (Math.max(...xs) - Math.min(...xs)); y = Math.min(...ys) + Math.random() * (Math.max(...ys) - Math.min(...ys)); if (inPoly(x, y, e.polygon)) break; } }
          else { const r = e.rect || [0, 0, 195, 422]; x = r[0] + Math.random() * (r[2] - r[0]); y = r[1] + Math.random() * (r[3] - r[1]); }
          const L = e.life || [4, 8]; parts.push({ e, x, y, vx: e.vx ? e.vx[0] + Math.random() * (e.vx[1] - e.vx[0]) : 0, vy: e.vy ? e.vy[0] + Math.random() * (e.vy[1] - e.vy[0]) : 0, t: 0, life: L[0] + Math.random() * (L[1] - L[0]), ph: Math.random() * 6.28 }); }
      }
      const em = g3.emitters || []; for (let i = parts.length - 1; i >= 0; i--) { const p = parts[i]; p.t += dt; p.x += p.vx * dt + (p.e.sway ? Math.sin(p.t * 1.3 + p.ph) * p.e.sway * dt : 0); p.y += p.vy * dt; if (p.t > p.life || !em.includes(p.e)) parts.splice(i, 1); }
    }
    /* 返 true＝V3 畫咗；false＝未 load 完（houseui 用舊 v2 合成） */
    function compose(v, x) {
      const room = C.room(), o = need(room, v), sc = scene(); if (!o || !FV || !sc || !sc.fx) { ST.fallback++; return false; }
      const gr = o.g, g3 = gr.v3 || {}, amb = gr.ambientTint, pt = C.mulHex(gr.petTint, amb), L = o.im, t = now0() / 1000, nowP = now0();
      const dt = Math.min(0.1, lastT ? (nowP - lastT) / 1000 : 0); lastT = nowP; stepParts(g3, dt); ST.draws++;
      const id = () => x.setTransform(1, 0, 0, 1, 0, 0), one = () => x.setTransform(K, 0, 0, K, 0, 0);
      const op = (m, a) => { x.globalCompositeOperation = m || 'source-over'; x.globalAlpha = a == null ? 1 : Math.max(0, Math.min(1, a)); };
      const lay = (n, m, a, X) => { const i = L[n]; if (!i) return; (X || x).globalCompositeOperation = m || 'source-over'; (X || x).globalAlpha = a == null ? 1 : Math.min(1, a); (X || x).drawImage(i, i.width === SW ? 0 : C.LX * K, i.width === SW ? 0 : C.LY * K); (X || x).globalCompositeOperation = 'source-over'; (X || x).globalAlpha = 1; };
      id(); op(); x.clearRect(0, 0, SW, SH); x.imageSmoothingEnabled = false;
      const lampsK = (g3.lamps && g3.lamps.scale != null) ? g3.lamps.scale : (v === 'night' ? 1 : 0.35), FU = FV.furniture;
      const fv = (k) => { const n = C.idOf(k); return n && FU[n] ? Object.assign({ id: n }, FU[n]) : null; };
      const at = (a, f) => [Math.round(a[0] - f.pivot[0]) * K, Math.round(a[1] - f.pivot[1]) * K];
      const furn = (k, part, alpha, flipY) => { const f = C.furnOf(k); if (!f) return; const a = C.slotAnchor(k), m = fv(k), src = m && im(part === 'front' ? m.x3Front : m.x3);
        if (!src) { one(); if (!flipY) C.drawFurn(x, f, a, amb, part); id(); return; } const [X0, Y0] = at(a, f), s = C.tinted(src, amb);
        if (flipY) { x.save(); op('source-over', alpha); x.translate(0, 2 * a[1] * K); x.scale(1, -1); x.drawImage(s, X0, Y0); x.restore(); op(); ST.reflect++; return; }
        x.drawImage(s, X0, Y0); };
      // ① 窗外／牆
      lay('sky'); lay('far'); for (const k of ['window', 'wall']) furn(k); lay('mid'); lay('floor_reflect');
      // ② 即時倒影（家具；地氈之前）
      const rf = g3.reflection && g3.reflection.realtime; if (rf) for (const k of ['lamp', 'bed', 'table']) { const m = fv(k); if (m && m.reflect) furn(k, null, rf.alpha || 0.12, true); }
      furn('rug');
      // ③ AO
      for (const k of ['rug', 'bed', 'table', 'lamp']) { const f = C.furnOf(k), m = fv(k), a = f && C.slotAnchor(k); if (!f) continue; const ao = m && m.ao && im(m.ao.png);
        if (ao) { op('source-over', m.ao.alpha); x.drawImage(ao, Math.round(a[0] * K - ao.width / 2), Math.round((a[1] + 1) * K - ao.height / 2)); op(); ST.ao++; } else if (f.shadow && k !== 'rug') { one(); C.shadowAt(x, a[0], a[1], f.shadow[0], f.shadow[1]); id(); } }
      one(); for (const k in C.PET) { const p = C.PET[k]; if (!C.vis(k)) continue; if (p.mode !== 'sleep' || !C.Z.bed) C.shadowAt(x, p.x + p.dx, p.y, k === 'kid' ? 18 : 20, 4); }
      for (const p of C.RS.values()) C.shadowAt(x, p.x + p.dx, p.y, p.kind === 'kid' ? 18 : 20, 4); id();
      const dv = C.decoNow(), S0 = dv && C.FAM && C.FAM.SV[dv], svm = S0 && SV && SV.souvenirs[dv], DA = C.FAM && C.FAM.DECO_ANCHOR;
      if (S0) { const ao = im('souvenir/sv_ao@3x.png'); if (ao) { op('source-over', (svm && svm.ao && svm.ao.alpha) || 0.8); x.drawImage(ao, Math.round(DA[0] * K - ao.width / 2), Math.round((DA[1] + 1) * K - ao.height / 2)); op(); } }
      // ④ 燈地面光池
      const lm = fv('lamp'), lf = C.furnOf('lamp'), la = lf && C.slotAnchor('lamp'), LL = lm && lm.light, lc = la && lm ? [(la[0] + (lm.lightCenter || [0, -30])[0]) * K, (la[1] + (lm.lightCenter || [0, -30])[1]) * K] : null;
      if (LL && LL.pool) { const pl = im(LL.pool.png); if (pl) { op('lighter', 0.85 * lampsK); x.drawImage(pl, la[0] * K - pl.width / 2, (la[1] - 1) * K - pl.height / 2); op(); ST.lamp++; } }
      // ⑤ ysort（寵物光池喺寵物前畫）
      const pl3 = g3.petLight, hK = (pl3 && pl3.houseScale != null) ? pl3.houseScale : (v === 'night' ? 1 : 0.5), sleepy = !!(G.v3 && G.v3.glow && G.v3.glow.state === 'sleepy');
      if (GL.tr) { GL.tr.set(houseState(C.PET.tr, sleepy), nowP); GL.kid.set(houseState(C.PET.kid, false), nowP); }
      const gv = { tr: GL.tr ? GL.tr.value(nowP) : 1, kid: GL.kid ? GL.kid.value(nowP) : 1 }; ST.glow = { tr: +gv.tr.toFixed(3), kid: +gv.kid.toFixed(3), trS: GL.tr && GL.tr.state, kidS: GL.kid && GL.kid.state };
      const blits = [], ys = [];
      for (const k of ['lamp', 'bed', 'table']) { const f = C.furnOf(k); if (f) { const a = C.slotAnchor(k); ys.push({ y: a[1], d: () => furn(k) }); if (k === 'bed' && f.front) ys.push({ y: a[1] + 0.1, d: () => furn(k, 'front') }); } }
      const bedY = C.furnOf('bed') ? C.slotAnchor('bed')[1] : 0;
      for (const k of ['tr', 'kid']) { const p = C.PET[k]; if (!C.vis(k)) continue;
        ys.push({ y: p.mode === 'sleep' && C.Z.bed ? bedY + (k === 'tr' ? 0.01 : 0.02) : p.y, d: () => {
          if (pl3) { sc.drawPool(x, Object.assign({}, pl3, { intensity: (pl3.intensity || 0.9) * hK * (k === 'kid' ? 0.7 : 1) }), [(p.x + p.dx) * K, p.y * K], gv[k], null, 1); ST.pool++; }
          one(); C.drawPet(x, p, pt); id(); if (p.blit) blits.push(p.blit); } }); }
      for (const p of C.RS.values()) ys.push({ y: p.y, d: () => { one(); C.drawRes(x, p, pt); id(); if (p.blit) blits.push(p.blit); } });
      if (S0) ys.push({ y: DA[1], d: () => { const s3 = svm && im(svm.x3); if (s3) x.drawImage(C.tinted(s3, amb), Math.round(DA[0] - S0.pv[0]) * K, Math.round(DA[1] - S0.pv[1]) * K); else { one(); C.drawDeco(x, amb); id(); } ST.sv++; } });
      ys.sort((a, b) => a.y - b.y); for (const e of ys) e.d();
      one(); C.blanket(x); id();
      // ⑥ fore → lightmap（＋燈 lift）→ light_add
      lay('fore');
      if (L.lightmap) { const c = cv('lm', L.lightmap.width, L.lightmap.height), g = c.getContext('2d'); g.globalCompositeOperation = 'source-over'; g.globalAlpha = 1; g.drawImage(L.lightmap, 0, 0);
        if (LL && LL.lift) { const li = im(LL.lift.png); if (li) { g.globalCompositeOperation = 'lighter'; g.globalAlpha = Math.min(1, lampsK); g.drawImage(li, lc[0] - C.LX * K - li.width / 2, lc[1] - C.LY * K - li.height / 2); g.globalCompositeOperation = 'source-over'; g.globalAlpha = 1; } }
        op('multiply'); x.drawImage(c, C.LX * K, C.LY * K); op(); }
      lay('light_add', 'lighter');
      // ⑦ 窗光 beam＋patch（跟窗 slot 家具；寵物身 × (1 − petAtten)）
      const wb = g3.windowBeam; if (wb) { const wm = fv('window'), wl = (wm && wm.windowLight) || FV.windowNone, bi = im(wl.beam), pi = im(wl.patch); ST.win = wm ? wm.id : 'none';
        if (bi || pi) { const c = cv('wl', LW, LH), g = c.getContext('2d'); g.setTransform(1, 0, 0, 1, 0, 0); g.globalCompositeOperation = 'source-over'; g.globalAlpha = 1; g.clearRect(0, 0, LW, LH);
          const sh = 1 + (wb.shimmer ? wb.shimmer.amp * Math.sin(t * 6.283 * wb.shimmer.hz) : 0);
          const put = (im2, tint, a) => { if (!im2) return; const tc = cv('wt' + (im2 === bi ? 'b' : 'p'), LW, LH), tg = tc.getContext('2d'); tg.globalCompositeOperation = 'source-over'; tg.clearRect(0, 0, LW, LH); tg.drawImage(im2, 0, 0);
            tg.globalCompositeOperation = 'multiply'; tg.fillStyle = tint || '#ffffff'; tg.fillRect(0, 0, LW, LH); tg.globalCompositeOperation = 'destination-in'; tg.drawImage(im2, 0, 0); tg.globalCompositeOperation = 'source-over';
            g.globalCompositeOperation = 'lighter'; g.globalAlpha = Math.min(1, a * sh); g.drawImage(tc, 0, 0); g.globalAlpha = 1; };
          put(bi, wb.tint, wb.intensity); put(pi, wb.patchTint || wb.tint, wb.patchIntensity != null ? wb.patchIntensity : wb.intensity);
          if (wb.petAtten && blits.length) { g.globalCompositeOperation = 'destination-out'; g.globalAlpha = wb.petAtten; g.setTransform(K, 0, 0, K, -C.LX * K, -C.LY * K);
            for (const b of blits) { g.save(); g.translate(b.X0, b.Y0); g.scale(b.fx, b.fy); g.drawImage(b.img, b.sx, b.sy, b.sw, b.sh, -b.px, -b.py, b.sw, b.sh); g.restore(); }
            g.setTransform(1, 0, 0, 1, 0, 0); g.globalCompositeOperation = 'source-over'; g.globalAlpha = 1; ST.winAtten = blits.length; }
          op('lighter'); x.drawImage(c, C.LX * K, C.LY * K); op(); } }
      // ⑧ bloom／emissive
      lay('bloom', 'lighter', gr.bloom ? gr.bloom.intensity : 0.5);   // emissive@3x 係 bloom 用嘅 mask（house_v3.json#stack 冇直接畫）
      // ⑨ 燈 halo＋emissive＋flare（場景燈，唔跟 petGlow）
      if (LL && lc) { const fl = flick(LL.flicker, t); const ha = LL.halo && im(LL.halo.png); if (ha) { op('lighter', 0.4 * lampsK * fl); x.drawImage(ha, lc[0] - ha.width / 2, lc[1] - ha.height / 2); }
        const em = LL.bloom && im(LL.bloom.src); if (em) { op('lighter', (gr.bloom ? gr.bloom.intensity : 0.5) * Math.max(0.35, lampsK)); x.drawImage(em, at(la, lf)[0], at(la, lf)[1]); }
        const F = LL.flare; if (F) { const fr = tintFx('flare_' + (F.size || 'm') + '_0' + (1 + (Math.floor(t * (F.fps || 3)) % 6)), F.tint); if (fr) { op('lighter', (F.intensity || 0.6) * lampsK * fl); x.drawImage(fr, lc[0] - fr.width / 2, lc[1] - fr.height / 2); } } op(); }
      // ⑩ 紀念品光（場景光）
      if (S0 && svm && svm.light) { const gi = im(svm.light.glow); if (gi) { op('lighter', (v === 'night' ? (svm.light.nightScale || 1) : (svm.light.dayScale || 0.5)) * flick(svm.light.flicker, t)); x.drawImage(gi, DA[0] * K - gi.width / 2, (DA[1] - S0.pv[1] + 5) * K - gi.height / 2 - 6); op(); } }
      // ⑪ 寵物光（× petGlow × houseScale）
      for (const k of ['tr', 'kid']) { const p = C.PET[k]; if (!C.vis(k) || !p.blit || gv[k] <= 0.002) continue; const fk = k === 'tr' ? C.trForm() : (p.blit.fk || null), F = fk && sc.formJ(fk, k === 'kid');
        if (F) { sc.drawHalos(x, F, p.blit.name, [p.blit.X0 * K, p.blit.Y0 * K], p.blit.fx < 0 ? -1 : 1, gv[k], hK, t); ST.halos++; } }
      // ⑫ flares＋浮塵＋霧＋vignette
      for (const f of (g3.flares || [])) { const fr = tintFx('flare_' + (f.size || 's') + '_0' + (1 + (Math.floor(t * (f.fps || 2) + (f.phase || 0) * 6) % 6)), f.tint); if (fr) { op('lighter', f.intensity || 0.3); x.drawImage(fr, f.pos[0] * K - fr.width / 2, f.pos[1] * K - fr.height / 2); } }
      ST.parts = parts.length; for (const p of parts) { const e = p.e, fade = Math.min(1, p.t / 0.8, (p.life - p.t) / 1), a = Math.max(0, (e.add || 0.3) * fade * (e.alpha != null ? e.alpha : 1)), gw = tintFx(e.glow || 'glow_12', e.tint);
        if (gw) { op('lighter', a); x.drawImage(gw, p.x * K - gw.width / 2, p.y * K - gw.height / 2); } }
      op(); if (gr.fog) { op('source-over', gr.fog.density); x.fillStyle = gr.fog.color; x.fillRect(0, 0, SW, SH); op(); }
      lay('vignette');
      return true;
    }
    return { ST, need, compose, GL, SW, SH, ready: (room, v) => !!need(room, v) };
  }
  return { K, SW, SH, houseState, inPoly, flick, make };
});
