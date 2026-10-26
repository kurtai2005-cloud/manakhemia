/* fx-art.js — fx-lab 真素材版（遊美「窄樑貓＋苔坡」）。純 Canvas2D；只供 fx-lab.html?art=1。
   邏輯畫面 960×540（＝1080p 的一半；1 美術 px＝1 邏輯 px；dpr2＝整數 2×），貓 64px 以 3×（＝1080p 6×）。
   分層／視差／光圖／畫質檔全部跟 art/docs/ASSET_SPEC.md §B 與 STYLE_GUIDE §3、§5、§6。
   畫質：off＝只有視差＋調色｜low＝全預烘（lowfx／預模糊 sky／只 warm 光圖／無 bloom）｜mid＝sky 預模糊＋mid_lowfx＋fore 即時 1/4＋bloom 單 pass｜high＝全即時（1/2、1/4 金字塔模糊）＋2 層 bloom＋tilt-shift。
   引擎驅動：腳步粒子（run_02／run_05 落地幀）、螢火 α 閃爍（位置由 fore.png 像素偵測，art/derived/）、草葉 α 呼吸（8 條帶、相位隨世界座標）。
   量度（headless，非真機）見 tests/fx-bench.js → tests/fx-art-bench-result.json。 */
(function (g) {
  'use strict';
  const LW = 960, LH = 540, TILE_W = 1024, QUALITIES = ['off', 'low', 'mid', 'high'];
  const TOD = {
    day: { tint: [1, .99, .94], br: 1, warm: 0, moon: 0, bloom: .22, vig: .3 },
    dusk: { tint: [1, .76, .70], br: .86, warm: .75, moon: .12, bloom: .42, vig: .38 },
    night: { tint: [.5, .6, .98], br: .78, warm: 1, moon: .55, bloom: .62, vig: .45 }
  };
  const STRENGTH = { sky: .55, mid: 1, track: 1, fore: .9, cat: .45 };
  const mod = (a, b) => ((a % b) + b) % b;
  const hash = n => { const s = Math.sin(n * 127.1 + 311.7) * 43758.5453; return s - Math.floor(s); };
  const cvs = (w, h) => { const c = document.createElement('canvas'); c.width = Math.max(1, Math.round(w)); c.height = Math.max(1, Math.round(h)); return c; };
  const loadImg = src => new Promise((res, rej) => { const im = new Image(); im.onload = () => res(im); im.onerror = () => rej(new Error('img ' + src)); im.src = src; });
  const supportsFilter = (() => { try { const c = cvs(2, 2).getContext('2d'); return typeof c.filter === 'string'; } catch (e) { return false; } })();

  // 調色（逐像素一次，載入時）：mult＝lerp(1, tint*br, strength)；回傳新 canvas
  function grade(src, mul, erase) {
    const c = cvs(src.width, src.height), x = c.getContext('2d', { willReadFrequently: true }); x.drawImage(src, 0, 0);
    if (mul[0] !== 1 || mul[1] !== 1 || mul[2] !== 1 || erase) {
      const id = x.getImageData(0, 0, c.width, c.height), d = id.data;
      for (let i = 0; i < d.length; i += 4) { d[i] = Math.min(255, d[i] * mul[0]); d[i + 1] = Math.min(255, d[i + 1] * mul[1]); d[i + 2] = Math.min(255, d[i + 2] * mul[2]); }
      if (erase) for (const m of erase) { const w = c.width; for (let dy = -m.r; dy <= m.r; dy++) for (let dx = -m.r; dx <= m.r; dx++) { const px = Math.round(m.x) + dx, py = Math.round(m.y) + dy; if (px < 0 || py < 0 || px >= w || py >= c.height) continue; const o = (py * w + px) * 4; if (d[o] > 200 && d[o + 1] > 190) d[o + 3] = 0; } }
      x.putImageData(id, 0, 0);
    }
    return c;
  }
  const mulOf = (td, k) => { const s = STRENGTH[k], t = TOD[td]; return t.tint.map(v => 1 + (v * t.br - 1) * s); };
  // 一次性預模糊（載入時）：Chrome／Firefox 用 ctx.filter；否則金字塔近似。回傳 canvas
  function blurOnce(src, sigma, wrapX) {
    const w = src.width, h = src.height; const pad = wrapX ? Math.ceil(sigma * 4) : 0;
    const big = cvs(w + pad * 2, h), bx = big.getContext('2d');
    if (wrapX) { bx.drawImage(src, pad - w, 0); bx.drawImage(src, pad, 0); bx.drawImage(src, pad + w, 0); } else bx.drawImage(src, 0, 0);
    const out = cvs(w, h), ox = out.getContext('2d');
    if (supportsFilter) { const t = cvs(big.width, h), tx = t.getContext('2d'); tx.filter = 'blur(' + sigma + 'px)'; tx.drawImage(big, 0, 0); ox.drawImage(t, pad, 0, w, h, 0, 0, w, h); }
    else { const k = Math.max(2, Math.round(sigma * 1.6)), s1 = cvs(big.width / k, h / k), sx = s1.getContext('2d'); sx.imageSmoothingQuality = 'high'; sx.drawImage(big, 0, 0, s1.width, s1.height); ox.imageSmoothingQuality = 'high'; ox.drawImage(s1, 0, 0, s1.width, s1.height, -pad, 0, big.width, h); }
    return out;
  }
  // 去 Bayer：4×4 箱型平均（只用於不整數縮放的 sky；量度見 moire()）
  function box4(src) {
    const w = src.width, h = src.height, c = cvs(w, h), x = c.getContext('2d', { willReadFrequently: true }); x.drawImage(src, 0, 0);
    const id = x.getImageData(0, 0, w, h), s = id.data, o = new Uint8ClampedArray(s.length);
    for (let y = 0; y < h; y++) for (let xx = 0; xx < w; xx++) for (let ch = 0; ch < 3; ch++) {
      let a = 0; for (let dy = 0; dy < 4; dy++) for (let dx = 0; dx < 4; dx++) a += s[(Math.min(h - 1, y + dy - 1) * w + (xx + dx - 1 + w) % w) * 4 + ch]; o[(y * w + xx) * 4 + ch] = a / 16;
    }
    for (let i = 3; i < o.length; i += 4) o[i] = 255; id.data.set(o); x.putImageData(id, 0, 0); return c;
  }

  const NEED = {
    off: { sky: 'raw', mid: 'mid', fore: 'fore', lights: [], emissive: false, vig: 'none' },
    low: { sky: 'blur', mid: 'mid_lowfx', fore: 'fore_lowfx', lights: ['warm'], emissive: false, vig: 'png' },
    mid: { sky: 'blur', mid: 'mid_lowfx', fore: 'fore', lights: ['warm', 'track', 'cool'], emissive: true, vig: 'png' },
    high: { sky: 'raw', mid: 'mid', fore: 'fore', lights: ['warm', 'track', 'cool'], emissive: true, vig: 'live' }
  };
  const BASE_DEFAULT = 'art/tracks/mossy_slope/';

  async function load(opt) {
    opt = opt || {}; const q = opt.quality || 'mid', tod = opt.tod || 'night', base = opt.base || BASE_DEFAULT, sbase = opt.spriteBase || 'art/sprites/narrowcat/', need = NEED[q];
    const heap0 = (performance.memory && performance.memory.usedJSHeapSize) || 0, t0 = performance.now();
    const files = { sky: 'sky_far_' + tod, mid: need.mid, track: 'track', fore: need.fore };
    need.lights.forEach(k => { files['lm_' + k] = k === 'warm' ? 'lightmap_warm' : k === 'track' ? 'lightmap_track' : 'lightmap_cool'; });
    if (need.emissive) files.emissive = 'emissive_mid';
    if (need.vig === 'png') files.vignette = 'vignette';
    ['01', '02', '03', '04'].forEach(n => { files['shred' + n] = 'fx_grass_shred_' + n; });
    const keys = Object.keys(files), imgs = await Promise.all(keys.map(k => loadImg(base + files[k] + '.png')));
    const atlasImg = await loadImg(sbase + 'spirit_narrowcat_atlas.png'), atlas = await (await fetch(sbase + 'spirit_narrowcat_atlas.json')).json();
    const ff = await (await fetch(opt.fireflies || 'art/derived/mossy_slope_fireflies.json')).json();
    const I = {}; keys.forEach((k, i) => { I[k] = imgs[i]; });
    const erase = (need.fore === 'fore') ? ff.items.map(f => ({ x: f.x, y: f.y, r: 3 })) : null;
    const L = {}; let bytes = 0; const tally = c => { bytes += c.width * c.height * 4; return c; };
    const sky = grade(I.sky, mulOf(tod, 'sky')); L.sky = tally(need.sky === 'blur' ? blurOnce(sky, 2.5, true) : sky); L.skyRawForMoire = need.sky === 'raw' ? null : null;
    L.mid = tally(grade(I.mid, mulOf(tod, 'mid'))); L.track = tally(grade(I.track, mulOf(tod, 'track'))); L.fore = tally(grade(I.fore, mulOf(tod, 'fore'), erase));
    ['warm', 'track', 'cool'].forEach(k => { if (I['lm_' + k]) L['lm_' + k] = tally(grade(I['lm_' + k], [1, 1, 1])); });
    if (I.emissive) L.emissive = tally(grade(I.emissive, [1, 1, 1])); if (I.vignette) L.vignette = tally(grade(I.vignette, [1, 1, 1]));
    const sheet = cvs(96, 24), shx = sheet.getContext('2d'); ['01', '02', '03', '04'].forEach((n, i) => shx.drawImage(I['shred' + n], i * 24, 0)); L.shreds = tally(sheet);
    const cat = tally(grade(atlasImg, mulOf(tod, 'cat'))); L.cat = cat;
    const rec = performance.getEntriesByType ? performance.getEntriesByType('resource').filter(r => r.name.indexOf(base) >= 0 || r.name.indexOf(sbase) >= 0).reduce((s, r) => s + (r.encodedBodySize || 0), 0) : 0;
    const heap1 = (performance.memory && performance.memory.usedJSHeapSize) || 0;
    return { L, atlas, ff, tod, quality: q, files: Object.values(files), mem: { decodedRGBA_MB: bytes / 1048576, pngBytes_MB: rec / 1048576, jsHeapDelta_MB: (heap1 - heap0) / 1048576, note: '解碼後 RGBA＝寬×高×4 加總（估）；png＝resource timing encodedBodySize（實測）；heap＝performance.memory（Chrome 專有，canvas 後備緩衝唔計入）' }, loadMs: performance.now() - t0 };
  }

  function create(canvas, A, opts) {
    opts = opts || {}; const dpr = opts.dpr || 1, RW = Math.round(LW * dpr), RH = Math.round(LH * dpr), q = A.quality, need = NEED[q], td = TOD[A.tod], L = A.L;
    canvas.width = RW; canvas.height = RH;
    const ctx = canvas.getContext('2d', { alpha: false, willReadFrequently: !!opts.willRead });
    const P = Object.assign({ catBloom: 0.7, catPivot: 'spec', shreds: true, fireflies: true, breathe: true, speed: 190, catX: 330, bloomOn: true, tiltShift: true }, opts.params || {});
    const fx = { quality: q, dpr, RW, RH, A, P, stats: { texBytes: 0, shredsLive: 0 } };
    let bytes = A.mem.decodedRGBA_MB * 1048576; const buf = {};
    function low(k, w, h) { const c = cvs(w * dpr / k, h * dpr / k); bytes += c.width * c.height * 4; return { c, x: c.getContext('2d'), k }; }
    const sm = (x, on) => { x.imageSmoothingEnabled = on; if (on) x.imageSmoothingQuality = 'high'; };
    // 緩衝
    if (q === 'high') { buf.sky1 = low(2, LW, LH); buf.sky2 = low(4, LW, LH); buf.mid1 = low(2, LW, 320); buf.mid2 = low(4, LW, 320); buf.fore1 = low(2, LW, 540); buf.fore2 = low(4, LW, 540); }
    if (q === 'mid') { buf.fore1 = low(4, LW, 540); }
    if (q === 'mid') { buf.e1 = low(4, LW, LH); buf.e2 = low(8, LW, LH); }
    if (q === 'high') { buf.e1 = low(4, LW, LH); buf.e2 = low(8, LW, LH); buf.e3 = low(16, LW, LH); }
    if (q === 'high') { buf.tsB = [low(2, LW, 162), low(4, LW, 162)]; buf.tsU = [low(2, LW, 108), low(4, LW, 108)]; buf.maskT = cvs(buf.tsB[0].c.width, buf.tsB[0].c.height); buf.maskU = cvs(buf.tsU[0].c.width, buf.tsU[0].c.height);
      [[buf.maskT, 0], [buf.maskU, 1]].forEach(a => { const c = a[0], x = c.getContext('2d'), gr = x.createLinearGradient(0, 0, 0, c.height); if (a[1] === 0) { gr.addColorStop(0, 'rgba(0,0,0,1)'); gr.addColorStop(1, 'rgba(0,0,0,0)'); } else { gr.addColorStop(0, 'rgba(0,0,0,0)'); gr.addColorStop(1, 'rgba(0,0,0,1)'); } x.fillStyle = gr; x.fillRect(0, 0, c.width, c.height); bytes += c.width * c.height * 4; }); }
    if (q === 'high') { const c = cvs(LW / 4 * dpr, LH / 4 * dpr), x = c.getContext('2d'), gr = x.createRadialGradient(c.width / 2, c.height / 2, c.height * 0.3, c.width / 2, c.height / 2, c.height * 0.85); gr.addColorStop(0, 'rgba(10,12,40,0)'); gr.addColorStop(1, 'rgba(10,12,40,1)'); x.fillStyle = gr; x.fillRect(0, 0, c.width, c.height); buf.vig = c; bytes += c.width * c.height * 4; }
    // 光暈／影子貼圖
    function glow(r, c0, c1) { const c = cvs(r * 2, r * 2), x = c.getContext('2d'), gr = x.createRadialGradient(r, r, 0, r, r, r); gr.addColorStop(0, c0); gr.addColorStop(0.4, c1); gr.addColorStop(1, 'rgba(0,0,0,0)'); x.fillStyle = gr; x.fillRect(0, 0, r * 2, r * 2); bytes += c.width * c.height * 4; return c; }
    const glowFF = glow(16, 'rgba(255,251,208,1)', 'rgba(255,233,138,.35)');
    const shadow = (function () { const c = cvs(160, 24), x = c.getContext('2d'); x.filter = 'none'; const gr = x.createRadialGradient(80, 12, 2, 80, 12, 78); gr.addColorStop(0, 'rgba(36,24,52,.45)'); gr.addColorStop(.6, 'rgba(36,24,52,.28)'); gr.addColorStop(1, 'rgba(36,24,52,0)'); x.save(); x.translate(80, 12); x.scale(1, 12 / 78); x.translate(-80, -12 * 78 / 12); x.fillStyle = gr; x.fillRect(0, 0, 160, 24 * 78 / 12); x.restore(); bytes += c.width * c.height * 4; return c; })();
    fx.stats.texBytes = bytes;
    // 貓：腳底接地偏移（spec＝atlas pivot (32,61)；fix＝按 run 幀實際腳底 y=56）
    const RUN = A.atlas.animations.run.frames, FR = A.atlas.frames;
    const catFrame = (name) => { const f = FR[name].frame; return f; };
    const PIV = { spec: { run: 61, idle: 61 }, fix: { run: 55, idle: 62 } };
    // 腳步粒子
    const shreds = []; let lastRunIdx = -1;
    function emitShred(t, footX, footY) { shreds.push({ t0: t, wx: footX, y: footY, vx: -26 - hash(t * 31) * 16, vy: -4 - hash(t * 17) * 8 }); if (shreds.length > 6) shreds.shift(); }
    // 一幀
    function layerX(par, cam) { return -mod(cam * par, TILE_W); }
    function snapX(v) { return Math.round(v * dpr) / dpr; }
    function drawLoop(x, img, y, par, cam, alpha, sy, sh) { const x0 = snapX(layerX(par, cam)); if (alpha != null) x.globalAlpha = alpha; sy = sy || 0; sh = sh || img.height; x.drawImage(img, 0, sy, img.width, sh, x0, y + sy, TILE_W, sh); if (x0 + TILE_W < LW) x.drawImage(img, 0, sy, img.width, sh, x0 + TILE_W, y + sy, TILE_W, sh); x.globalAlpha = 1; }
    function down(dst, src, sx, sy, sw, sh) { dst.x.save(); dst.x.setTransform(1, 0, 0, 1, 0, 0); sm(dst.x, true); dst.x.globalCompositeOperation = 'copy'; dst.x.drawImage(src, sx, sy, sw, sh, 0, 0, dst.c.width, dst.c.height); dst.x.restore(); }
    function upAdd(dst, src, a) { dst.x.save(); dst.x.setTransform(1, 0, 0, 1, 0, 0); sm(dst.x, true); dst.x.globalCompositeOperation = 'lighter'; dst.x.globalAlpha = a; dst.x.drawImage(src.c, 0, 0, dst.c.width, dst.c.height); dst.x.restore(); }
    // 即時模糊（金字塔）：把 draw(x) 畫入 1/2 緩衝 a，再 1/4 b，a += b×0.7，回 ctx（放大平滑）
    function liveBlurDraw(a, b, drawFn, dx, dy, dw, dh) {
      a.x.setTransform(a.c.width / dw, 0, 0, a.c.height / dh, 0, -dy * a.c.height / dh); a.x.clearRect(0, dy, dw, dh); sm(a.x, true); drawFn(a.x);
      down(b, a.c, 0, 0, a.c.width, a.c.height);
      a.x.save(); a.x.setTransform(1, 0, 0, 1, 0, 0); sm(a.x, true); a.x.globalAlpha = 0.7; a.x.drawImage(b.c, 0, 0, a.c.width, a.c.height); a.x.restore();
      ctx.save(); sm(ctx, true); ctx.drawImage(a.c, dx, dy, dw, dh); ctx.restore();
    }
    function fireflyPos(t, cam) { const out = []; A.ff.items.forEach((f, i) => { const wx = f.x, px = mod(wx - cam * 1.6, TILE_W); if (px > LW + 20) return; out.push({ x: px + Math.sin(t * 0.7 + i * 2) * 2, y: f.y + Math.cos(t * 0.9 + i) * 2.5, a: 0.55 + 0.45 * Math.sin(t * (1.3 + hash(i) * 1.9) + i * 1.7), i }); }); return out; }
    function drawCat(x, t, forBloom) {
      const idx = Math.floor(t * 12) % 6, name = RUN[idx], f = catFrame(name), S = 3, piv = PIV[P.catPivot].run, fx0 = P.catX, fy = 470;
      x.drawImage(L.cat, f.x, f.y, 64, 64, Math.round(fx0 - 32 * S), Math.round(fy - piv * S), 64 * S, 64 * S);
      return { idx, f, piv };
    }
    fx.setParams = function (o) { Object.assign(P, o); };
    fx.render = function (t) {
      const cam = t * P.speed, s = dpr; ctx.setTransform(s, 0, 0, s, 0, 0); sm(ctx, false); ctx.globalCompositeOperation = 'source-over'; ctx.globalAlpha = 1;
      // 1 sky（par .05；high＝即時模糊 σ5）
      if (q === 'high') liveBlurDraw(buf.sky1, buf.sky2, x => drawLoop(x, L.sky, 0, 0.05, cam), 0, 0, LW, LH);
      else drawLoop(ctx, L.sky, 0, 0.05, cam);
      // 1b 月光 lightmap_cool（par .2）
      if (L.lm_cool && td.moon > 0) { ctx.globalCompositeOperation = 'lighter'; drawLoop(ctx, L.lm_cool, 0, 0.2, cam, td.moon); ctx.globalCompositeOperation = 'source-over'; }
      // 2 mid（par .35；high＝即時 σ2.6）
      if (q === 'high') liveBlurDraw(buf.mid1, buf.mid2, x => drawLoop(x, L.mid, 160, 0.35, cam), 0, 160, LW, 320); else drawLoop(ctx, L.mid, 160, 0.35, cam);
      if (L.lm_warm && td.warm > 0) { ctx.globalCompositeOperation = 'lighter'; drawLoop(ctx, L.lm_warm, 160, 0.35, cam, td.warm); ctx.globalCompositeOperation = 'source-over'; }
      // 3 track
      drawLoop(ctx, L.track, 320, 1.0, cam);
      if (L.lm_track && td.warm > 0) { ctx.globalCompositeOperation = 'lighter'; drawLoop(ctx, L.lm_track, 320, 1.0, cam, td.warm); ctx.globalCompositeOperation = 'source-over'; }
      // 4 貓：blob shadow → sprite
      ctx.drawImage(shadow, P.catX - 80, 470 - 8, 160, 24);
      const ci = drawCat(ctx, t);
      // 5 腳步粒子（run_02／run_05＝idx 1／4 落地幀）
      if (P.shreds) {
        if (ci.idx !== lastRunIdx && (ci.idx === 1 || ci.idx === 4)) { emitShred(t, cam + P.catX - 6 + (ci.idx === 1 ? -30 : 24), 470); }
        lastRunIdx = ci.idx; let live = 0;
        for (const s of shreds) { const age = t - s.t0; if (age < 0 || age >= 0.4) continue; live++; const fr = Math.min(3, Math.floor(age * 10)), px = s.wx - cam + s.vx * age, py = s.y + s.vy * age; ctx.globalAlpha = 1 - age / 0.4 * 0.5; ctx.drawImage(L.shreds, fr * 24, 0, 24, 24, Math.round(px - 12 * 3), Math.round(py - 22 * 3), 72, 72); }
        ctx.globalAlpha = 1; fx.stats.shredsLive = live;
      }
      // 6 fore（par 1.6）：8 條帶 α 呼吸；high 即時 σ7、mid 即時 1/4
      const foreA = 0.92, cs = cam * 1.6;
      const drawFore = (x) => {
        for (let k = Math.floor(cs / 128) - 0; k <= Math.floor((cs + LW) / 128); k++) { const x0 = k * 128, a = P.breathe ? foreA + 0.05 * Math.sin(t * 1.1 + k * 0.9) : foreA; x.globalAlpha = a; x.drawImage(L.fore, mod(x0, TILE_W), 0, 128, 540, snapX(x0 - cs), 0, 128, 540); }
        x.globalAlpha = 1;
      };
      if (q === 'high') liveBlurDraw(buf.fore1, buf.fore2, drawFore, 0, 0, LW, 540);
      else if (q === 'mid') { const b = buf.fore1; b.x.setTransform(b.c.width / LW, 0, 0, b.c.height / LH, 0, 0); b.x.clearRect(0, 0, LW, LH); sm(b.x, true); drawFore(b.x); ctx.save(); sm(ctx, true); ctx.drawImage(b.c, 0, 0, LW, LH); ctx.restore(); }
      else drawFore(ctx);
      // 螢火閃爍（光暈 ADD＋亮核；位置同 fore 視差）
      const ffs = P.fireflies ? fireflyPos(t, cam) : [];
      if (P.fireflies && q !== 'off') { ctx.globalCompositeOperation = 'lighter'; for (const f of ffs) { ctx.globalAlpha = f.a * 0.9; ctx.drawImage(glowFF, Math.round(f.x - 16), Math.round(f.y - 16)); } ctx.globalCompositeOperation = 'source-over'; }
      if (P.fireflies && need.fore === 'fore') { ctx.fillStyle = '#FFFBD0'; for (const f of ffs) { ctx.globalAlpha = 0.35 + f.a * 0.65; ctx.fillRect(Math.round(f.x) - 1, Math.round(f.y) - 1, 2, 2); } }
      ctx.globalAlpha = 1;
      // 7 bloom（emissive_mid＋螢火＋貓×catBloom）
      if (P.bloomOn && (q === 'mid' || q === 'high')) {
        const e1 = buf.e1, e2 = buf.e2; e1.x.setTransform(e1.c.width / LW, 0, 0, e1.c.height / LH, 0, 0); e1.x.clearRect(0, 0, LW, LH); sm(e1.x, false);
        e1.x.globalCompositeOperation = 'lighter'; drawLoop(e1.x, L.emissive, 160, 0.35, cam, 1);
        sm(e1.x, true); for (const f of ffs) { e1.x.globalAlpha = f.a * 0.8; e1.x.drawImage(glowFF, f.x - 16, f.y - 16); }
        if (P.catBloom > 0) { e1.x.globalAlpha = 0.5 * P.catBloom; sm(e1.x, false); drawCat(e1.x, t); }
        e1.x.globalAlpha = 1; e1.x.globalCompositeOperation = 'source-over';
        down(e2, e1.c, 0, 0, e1.c.width, e1.c.height);
        let strength;
        if (q === 'high') { down(buf.e3, e2.c, 0, 0, e2.c.width, e2.c.height); upAdd(e2, buf.e3, 0.9); upAdd(e1, e2, 0.8); strength = td.bloom * 0.9; }
        else { upAdd(e1, e2, 0.8); strength = td.bloom * 0.7; }
        ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0); sm(ctx, true); ctx.globalCompositeOperation = 'lighter'; ctx.globalAlpha = Math.min(1, strength); ctx.drawImage(e1.c, 0, 0, RW, RH); ctx.restore();
      }
      // 8 tilt-shift（high；焦點帶 y 30%–90%＝162–486；上下漸變）
      if (q === 'high' && P.tiltShift) {
        const bands = [[buf.tsB, buf.maskT, 0, 162], [buf.tsU, buf.maskU, 432, 108]];
        for (const bd of bands) {
          const b = bd[0], y0 = bd[2], h = bd[3];
          down(b[0], canvas, 0, Math.round(y0 * dpr), RW, Math.round(h * dpr)); down(b[1], b[0].c, 0, 0, b[0].c.width, b[0].c.height);
          b[0].x.save(); b[0].x.setTransform(1, 0, 0, 1, 0, 0); sm(b[0].x, true); b[0].x.globalAlpha = 0.65; b[0].x.drawImage(b[1].c, 0, 0, b[0].c.width, b[0].c.height); b[0].x.restore();
          b[0].x.save(); b[0].x.setTransform(1, 0, 0, 1, 0, 0); b[0].x.globalCompositeOperation = 'destination-in'; sm(b[0].x, true); b[0].x.drawImage(bd[1], 0, 0, b[0].c.width, b[0].c.height); b[0].x.restore();
          ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0); sm(ctx, true); ctx.drawImage(b[0].c, 0, Math.round(y0 * dpr), RW, Math.round(h * dpr)); ctx.restore();
        }
      }
      // 9 vignette
      ctx.setTransform(1, 0, 0, 1, 0, 0); sm(ctx, true);
      if (q === 'high') { ctx.globalAlpha = td.vig; ctx.drawImage(buf.vig, 0, 0, RW, RH); ctx.globalAlpha = 1; }
      else if (L.vignette) { ctx.drawImage(L.vignette, 0, 0, RW, RH); }
    };
    fx.flush = () => ctx.getImageData(0, 0, 1, 1);
    fx.bench = function (frames, warm) {
      frames = frames || 240; warm = warm == null ? 30 : warm; const ms = [];
      for (let i = 0; i < frames + warm; i++) { const t0 = performance.now(); fx.render(2 + i / 30); fx.flush(); const d = performance.now() - t0; if (i >= warm) ms.push(d); }
      ms.sort((a, b) => a - b); const sum = ms.reduce((a, b) => a + b, 0);
      return { quality: q, dpr, canvas: RW + 'x' + RH, frames: ms.length, avg: sum / ms.length, p50: ms[ms.length >> 1], p95: ms[Math.floor(ms.length * 0.95)], max: ms[ms.length - 1], texMB: fx.stats.texBytes / 1048576, mem: A.mem };
    };
    fx.catFootInfo = function (t) { const idx = Math.floor(t * 12) % 6; return { idx, name: RUN[idx], pivot: PIV[P.catPivot].run }; };
    return fx;
  }

  // 摩爾紋量度：sky 以 scale S 縮放繪畫（模擬 css／dpr 非整數縮放），量度「週期性殘差」峰值
  function moire(skyImg, scales, variants) {
    const out = [];
    function peak(c) {
      // 取天空頂部平滑區（y 6–46 art px×S，只有漸層＋Bayer 抖動點、冇雲／樹）；逐列：去 33px 移動平均（高通）→ DFT 週期 2–32px；逐列取振幅再平均（Bayer 4×4 各列相位唔同，唔可先疊加訊號）
      const x = c.getContext('2d', { willReadFrequently: true }), w = c.width, h = c.height, S = h / 540, y0 = Math.floor(6 * S), y1 = Math.floor(46 * S), N = Math.min(480, w - 80), M = 16;
      const amps = new Float32Array(61); let rows = 0, rms = 0;
      for (let y = y0; y < y1; y++) {
        const d = x.getImageData(40, y, N, 1).data, row = new Float32Array(N), hp = new Float32Array(N);
        for (let i = 0; i < N; i++) row[i] = 0.3 * d[i * 4] + 0.59 * d[i * 4 + 1] + 0.11 * d[i * 4 + 2];
        for (let i = M; i < N - M; i++) { let m = 0; for (let k = -M; k <= M; k++) m += row[i + k]; hp[i] = row[i] - m / (2 * M + 1); }
        let e = 0; for (let i = M; i < N - M; i++) e += hp[i] * hp[i]; rms += Math.sqrt(e / (N - 2 * M));
        for (let pi = 0; pi < 61; pi++) { const f = 1 / (2 + pi * 0.5); let re = 0, im = 0; for (let i = M; i < N - M; i++) { const ang = 2 * Math.PI * f * i; re += hp[i] * Math.cos(ang); im += hp[i] * Math.sin(ang); } amps[pi] += 2 * Math.hypot(re, im) / (N - 2 * M); }
        rows++;
      }
      let best = 0, bp = 0; for (let pi = 0; pi < 61; pi++) { const a = amps[pi] / rows; if (a > best) { best = a; bp = 2 + pi * 0.5; } }
      return { amp: best, period: bp, rms: rms / rows };
    }
    for (const S of scales) for (const v of variants) {
      const c = cvs(Math.round(1024 * S), Math.round(540 * S)), x = c.getContext('2d', { willReadFrequently: true }); x.imageSmoothingEnabled = v.smooth !== false; x.imageSmoothingQuality = v.q || 'low';
      x.drawImage(v.src || skyImg, 0, 0, c.width, c.height); const r = peak(c); out.push({ scale: S, variant: v.name, amp: +r.amp.toFixed(3), period: r.period, rms: +r.rms.toFixed(3) });
    }
    return out;
  }

  // 即時金字塔模糊等效 σ（美術 px）：用 1px 白線做脈衝響應，量度輪廓標準差。levels：'half'＝只 1/2；'quarter'＝只 1/4；'half+quarter'＝1/2 疊 1/4×alpha
  function pyramidSigma(levels, alpha) {
    const W = 192, H = 8, src = cvs(W, H), sx = src.getContext('2d'); sx.fillStyle = '#000'; sx.fillRect(0, 0, W, H); sx.fillStyle = '#fff'; sx.fillRect(W / 2, 0, 1, H);
    const k1 = levels === 'quarter' ? 4 : 2, a = cvs(W / k1, H / k1 < 1 ? 1 : H / k1), ax = a.getContext('2d'); ax.imageSmoothingQuality = 'high'; ax.drawImage(src, 0, 0, a.width, a.height);
    if (levels === 'half+quarter') { const b = cvs(W / 4, 1), bx = b.getContext('2d'); bx.imageSmoothingQuality = 'high'; bx.drawImage(a, 0, 0, b.width, b.height); ax.globalAlpha = alpha; ax.imageSmoothingQuality = 'high'; ax.drawImage(b, 0, 0, a.width, a.height); ax.globalAlpha = 1; }
    const out = cvs(W, H), ox = out.getContext('2d', { willReadFrequently: true }); ox.imageSmoothingQuality = 'high'; ox.drawImage(a, 0, 0, W, H);
    const d = ox.getImageData(0, 0, W, 1).data; let sw = 0, m = 0, v = 0; for (let i = 0; i < W; i++) { const w = d[i * 4]; sw += w; m += w * i; } m /= sw; for (let i = 0; i < W; i++) v += d[i * 4] * (i - m) * (i - m); return Math.sqrt(v / sw);
  }
  g.WR = g.WR || {};
  g.WR.FxArt = { pyramidSigma, load, create, moire, blurOnce, box4, grade, QUALITIES, TOD, LW, LH };
})(typeof globalThis !== 'undefined' ? globalThis : this);
