/* 《微光小圃》 render.js — Canvas 渲染：程序化像素素材、4 層視差、後處理（暈影／bloom／景深／移軸）。
   全部圖像由代碼即場繪畫，冇外部素材。原創代碼。 */
(function (root, factory) {
  root.Glimmer = root.Glimmer || {};
  root.Glimmer.render = factory(root.Glimmer.data, root.Glimmer.sim);
})(typeof self !== 'undefined' ? self : this, function (D, SIM) {
  'use strict';
  const PAL = D.PAL, P = D.PARAMS;
  const W = 195, H = 422;               // 美術格（art px）；顯示 = 整數倍放大
  const MX = 14, MY = 12;               // 層畫布邊距（俾視差位移）
  const LW = W + MX * 2, LH = H + MY * 2;
  const GROUND_Y = 292, CX = 97;        // 寵物腳底位置（art 座標）
  const POOP_SLOTS = [[50, 304], [146, 302], [118, 318]];

  // ───────── 工具 ─────────
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const lerp = (a, b, t) => a + (b - a) * t;
  const hash = (n) => { const s = Math.sin(n * 12.9898 + 78.233) * 43758.5453; return s - Math.floor(s); };
  const hex = (c) => [parseInt(c.slice(1, 3), 16), parseInt(c.slice(3, 5), 16), parseInt(c.slice(5, 7), 16)];
  const mixc = (a, b, t) => [lerp(a[0], b[0], t), lerp(a[1], b[1], t), lerp(a[2], b[2], t)];
  const rgb = (c, a) => a == null ? `rgb(${c[0] | 0},${c[1] | 0},${c[2] | 0})` : `rgba(${c[0] | 0},${c[1] | 0},${c[2] | 0},${a})`;
  const BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]].map(r => r.map(v => (v + 0.5) / 16));
  function mk(w, h) { const c = document.createElement('canvas'); c.width = Math.max(1, w | 0); c.height = Math.max(1, h | 0); return c; }
  function disc(ctx, cx, cy, r, col) {
    if (col) ctx.fillStyle = col;
    for (let dy = -r; dy <= r; dy++) { const w = Math.floor(Math.sqrt(r * r - dy * dy + r * 0.6)); ctx.fillRect(cx - w, cy + dy, w * 2 + 1, 1); }
  }
  function spriteFromRows(rows, pal) {
    const h = rows.length, w = rows[0].length, c = mk(w, h), x = c.getContext('2d');
    for (let j = 0; j < h; j++) for (let i = 0; i < w; i++) { const ch = rows[j][i]; if (ch !== '.' && pal[ch]) { x.fillStyle = pal[ch]; x.fillRect(i, j, 1, 1); } }
    return c;
  }

  // ───────── 日夜色溫 ─────────
  const LOOK = [ // hour, 燈籠色, 天頂, 天邊, 日照 0–1
    [0, [255, 158, 72], [9, 13, 36], [30, 38, 84], 0],
    [5, [255, 168, 96], [14, 20, 52], [52, 50, 96], 0.04],
    [7.5, [255, 196, 140], [46, 58, 108], [214, 150, 138], 0.35],
    [10, [255, 232, 188], [62, 100, 150], [170, 204, 214], 0.8],
    [14, [255, 242, 214], [64, 108, 156], [182, 212, 216], 0.9],
    [17, [255, 206, 140], [52, 56, 106], [214, 142, 120], 0.45],
    [19, [255, 166, 84], [22, 24, 62], [86, 56, 100], 0.12],
    [21, [255, 160, 76], [12, 16, 42], [38, 42, 90], 0.02],
    [24, [255, 158, 72], [9, 13, 36], [30, 38, 84], 0],
  ];
  function lookAt(hour) {
    hour = ((hour % 24) + 24) % 24;
    let i = 0; while (i < LOOK.length - 2 && hour >= LOOK[i + 1][0]) i++;
    const a = LOOK[i], b = LOOK[i + 1], t = (hour - a[0]) / (b[0] - a[0]);
    return { lantern: mixc(a[1], b[1], t), top: mixc(a[2], b[2], t), bot: mixc(a[3], b[3], t), day: lerp(a[4], b[4], t) };
  }

  // ───────── 像素文字（數字）、細圖案 ─────────
  const FONT = { '0': '111101101101111', '1': '010110010010111', '2': '111001111100111', '3': '111001111001111', '4': '101101111001001', '5': '111100111001111', '6': '111100111101111', '7': '111001001001001', '8': '111101111101111', '9': '111101111001111', '+': '000010111010000', '-': '000000111000000' };
  function pixText(ctx, str, x, y, col) {
    ctx.fillStyle = col;
    for (let k = 0; k < str.length; k++) { const g = FONT[str[k]]; if (!g) continue; for (let j = 0; j < 5; j++) for (let i = 0; i < 3; i++) if (g[j * 3 + i] === '1') ctx.fillRect(x + k * 4 + i, y + j, 1, 1); }
  }
  const SPR = {};
  function initSprites() {
    SPR.poop = spriteFromRows([
      '....dd.....', '...dbbd....', '..dbbhbd...', '.dbbbbbbd..', '.dbebbebd..', 'dbbbmbbbbd.', 'dbbbbbbbbbd', '.dddddddddd'], { d: '#5c3a20', b: '#8a5a30', h: '#c08a50', e: '#2a1a10', m: '#e8606a' });
    SPR.cookie = spriteFromRows([
      '..dddddd..', '.dccccccd.', 'dcchcccccd', 'dccccdcccd', 'dcdcccccdd', 'dccccchccd', '.dccdcccd.', '..dddddd..'], { d: '#a8683a', c: '#e8b46a', h: '#ffe9a8' });
    SPR.meal = spriteFromRows([
      '...rr.rr...', '..rrrrrrr..', '.rrrwrrrrr.', 'rrrrrrrwrrr', 'bbbbbbbbbbb', '.bbbbbbbbb.', '..bbbbbbb..', '...ddddd...'], { r: '#d8744a', w: '#fff0d0', b: '#e8d8b0', d: '#a88a5a' });
    SPR.soup = spriteFromRows([
      '..s..s....', '.s..s.....', '..........', 'cccccccccc', 'cwwwwwwwwc', 'cwoooooowc', '.cwwwwwwc.', '..cccccc..'], { s: '#fff6d8', c: '#d8c8a8', w: '#f2c27e', o: '#e0a05e' });
    SPR.star = spriteFromRows(['..y..', '.yhy.', 'yhhhy', '.yhy.', '.y.y.'], { y: '#ffc83a', h: '#fff2a8' });
    SPR.bigstar = spriteFromRows(['....y....', '....y....', '...yhy...', 'yyyyhyyyy', '.yhhhhhy.', '..yhhhy..', '..yhyhy..', '.yy...yy.', '.y.....y.'], { y: '#ffb02e', h: '#fff6c0' });
    SPR.stone = spriteFromRows(['..dddd...', '.dgggdd..', 'dgggggdd.', 'dgvggvgdd', 'dggggggdd', '.dggvggd.', '..dddddd.'], { d: '#241c34', g: '#4a3c5a', v: '#7a4a8a' });
    SPR.basket = spriteFromRows([
      'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbb', 'dhhhhhhhhhhhhhhhhhhhhhhhhhhhhd', '.dwdwdwdwdwdwdwdwdwdwdwdwdwdwd.', '.dbwbwbwbwbwbwbwbwbwbwbwbwbwd.', '..dwdwdwdwdwdwdwdwdwdwdwdwdd..', '...dddddddddddddddddddddddd...'], { b: '#b87840', d: '#6a4020', h: '#e0a860', w: '#d29858' });
    SPR.heart = spriteFromRows(['.rr.rr.', 'rrrrrrr', 'rrhrrrr', '.rrrrr.', '..rrr..', '...r...'], { r: '#ff7a8a', h: '#ffc0c8' });
    SPR.spark = spriteFromRows(['..y..', '..y..', 'yyhyy', '..y..', '..y..'], { y: '#ffe27a', h: '#ffffff' });
    SPR.drop = spriteFromRows(['..b..', '.bbb.', 'bbhbb', 'bbbbb', '.bbb.'], { b: '#7ad0ff', h: '#e8f8ff' });
    SPR.zz = spriteFromRows(['zzzz', '..z.', '.z..', 'zzzz'], { z: '#cfe0ff' });
    SPR.ball = spriteFromRows(['.yyy.', 'yhhyy', 'yhyyy', 'yyyyy', '.yyy.'], { y: '#ffb86a', h: '#fff0c8' });
    SPR.sweat = spriteFromRows(['.g.', 'ggg', 'ggg', '.g.'], { g: '#a8e0a0' });
  }

  // ───────── 寵物像素生成 ─────────
  const petCache = {};
  function genPet(o) {
    const adult = o.stage === 'adult';
    const CW = adult ? 72 : 40, CH = adult ? 86 : 46;
    const pal = o.anim === 'unwell' ? PAL.sick : o.form === 'dust' ? PAL.dust : PAL.fur;
    const rx = adult ? (o.form === 'bright' ? 23 : 22) : 11, ry = adult ? 19 : 10;
    const feetH = adult ? 3 : 2, B = CH - 2, cx = CW / 2;
    const f = o.frame;
    let sy = 1;
    if (o.anim === 'idle') sy = [1, 0.96, 0.92, 1][f % 4];
    else if (o.anim === 'happy') sy = [0.9, 1.04, 1.08, 1.0][f % 4];
    else if (o.anim === 'eat') sy = [1, 0.96, 1, 0.96][f % 4];
    else if (o.anim === 'sleep') sy = [0.94, 0.98][f % 2];
    else if (o.anim === 'unwell') sy = [0.95, 0.97][f % 2];
    const cy = B - feetH - ry * sy;
    const buf = new Uint8ClampedArray(CW * CH * 4);
    const mask = new Uint8Array(CW * CH);
    const rgbp = pal.map(hex);
    const setc = (x, y, col) => { x |= 0; y |= 0; if (x < 0 || y < 0 || x >= CW || y >= CH) return; const c = typeof col === 'string' ? hex(col) : col; const i = (y * CW + x) * 4; buf[i] = c[0]; buf[i + 1] = c[1]; buf[i + 2] = c[2]; buf[i + 3] = 255; };
    const N = adult ? 28 : 16, seedv = adult ? 1 : 2;
    for (let y = 0; y < CH; y++) for (let x = 0; x < CW; x++) {
      const nx = (x + 0.5 - cx) / rx, ny = (y + 0.5 - cy) / (ry * sy);
      const d = Math.hypot(nx, ny), ang = Math.atan2(ny, nx);
      const sec = Math.floor((ang + Math.PI) / (2 * Math.PI) * N);
      const fz = (hash(sec * 3.7 + seedv + (o.form === 'bright' ? 5 : 0)) - 0.5) * (adult ? 0.16 : 0.22);
      if (d < 1 + fz) mask[y * CW + x] = 1;
    }
    const inM = (x, y) => x >= 0 && y >= 0 && x < CW && y < CH && mask[y * CW + x] === 1;
    for (let y = 0; y < CH; y++) for (let x = 0; x < CW; x++) {
      const nx = (x + 0.5 - cx) / rx, ny = (y + 0.5 - cy) / (ry * sy);
      const t = nx * 0.45 + ny * 0.65;
      if (inM(x, y)) {
        let v = (t + 1) * 1.45 + (BAYER[y & 3][x & 3] - 0.5) * 0.9;
        let idx = clamp(Math.round(v), 0, 3);
        const h = hash(x * 31 + y * 17 + seedv);
        if (h > 0.92 && idx > 0) idx--; else if (h < 0.05 && idx < 3) idx++;
        const edge = !inM(x - 1, y) || !inM(x + 1, y) || !inM(x, y - 1) || !inM(x, y + 1);
        if (edge) idx = t > -0.25 ? 4 : 3;
        setc(x, y, rgbp[idx]);
      } else {
        const nb = inM(x - 1, y) || inM(x + 1, y) || inM(x, y - 1) || inM(x, y + 1);
        if (nb && hash(x * 13 + y * 7 + seedv * 3) > 0.74) setc(x, y, rgbp[t < 0 ? 0 : 1]);
      }
    }
    // 腳
    const fw = adult ? 6 : 4, fdx = Math.round(rx * 0.45);
    for (const s of [-1, 1]) for (let j = 0; j < feetH; j++) { const w = j === 0 ? fw - 2 : fw; for (let i = 0; i < w; i++) setc(cx + s * fdx - w / 2 + i, B - feetH + j + 1, rgbp[j === feetH - 1 ? 5 : 4]); }
    // 表情
    const face = o.face || 'normal';
    let eyes = 'open', mouth = 'smile';
    if (o.anim === 'idle') { if (face === 'sad') { eyes = 'sad'; mouth = 'frown'; } else if (face === 'sleepy') { eyes = 'sleepy'; mouth = 'dot'; } else eyes = f % 4 === 3 ? 'closed' : 'open'; }
    else if (o.anim === 'happy') { eyes = 'happy'; mouth = 'big'; }
    else if (o.anim === 'eat') { eyes = f % 2 ? 'happy' : 'open'; mouth = f % 2 ? 'open' : 'smile'; }
    else if (o.anim === 'sleep') { eyes = 'closed'; mouth = f % 2 ? 'o' : 'dot'; }
    else if (o.anim === 'unwell') { eyes = 'x'; mouth = 'wavy'; }
    const ex = Math.round(rx * 0.42), ey = Math.round(cy + ry * sy * 0.02 - (adult ? 3 : 2));
    const ew = adult ? 4 : 3, eh = adult ? 6 : 4, E = PAL.eye, EH = PAL.eyeHi;
    for (const s of [-1, 1]) {
      const x0 = Math.round(cx + s * ex - ew / 2), y0 = ey;
      if (eyes === 'open' || eyes === 'sad' || eyes === 'sleepy') {
        const hh = eyes === 'sleepy' ? Math.ceil(eh / 2) : eh;
        const yy0 = eyes === 'sleepy' ? y0 + eh - hh : y0;
        for (let j = 0; j < hh; j++) for (let i = 0; i < ew; i++) { if ((j === 0 || j === hh - 1) && (i === 0 || i === ew - 1) && hh > 2) continue; setc(x0 + i, yy0 + j, E); }
        if (eyes !== 'sleepy') { setc(x0, y0 + 1, EH); if (adult) { setc(x0 + 1, y0 + 1, EH); setc(x0, y0 + 2, EH); setc(x0 + 1, y0 + 2, EH); } }
        if (eyes === 'sad') for (let i = 0; i < ew; i++) setc(x0 + i, y0 - 1 - ((s < 0 ? i : ew - 1 - i) >> 1), E);
        if (eyes === 'sleepy') for (let i = 0; i < ew; i++) setc(x0 + i, yy0 - 1, rgbp[4]);
      } else if (eyes === 'closed') { for (let i = 0; i < ew; i++) setc(x0 + i, y0 + eh - 2, E); if (adult) for (let i = 1; i < ew - 1; i++) setc(x0 + i, y0 + eh - 1, E); }
      else if (eyes === 'happy') { const w = ew; for (let i = 0; i < w; i++) { const up = (i === 0 || i === w - 1) ? 1 : 0; setc(x0 + i, y0 + eh - 3 + up, E); if (adult) setc(x0 + i, y0 + eh - 2 + up, E); } }
      else if (eyes === 'x') { const n = adult ? 5 : 3; for (let i = 0; i < n; i++) { setc(x0 + i - (n - ew) / 2, y0 + 1 + i, E); setc(x0 + n - 1 - i - (n - ew) / 2, y0 + 1 + i, E); } }
    }
    // 腮紅
    if (o.form !== 'dust' && o.anim !== 'unwell') {
      const bw = adult ? 4 : 2, bx = Math.round(rx * 0.68), by = Math.round(ey + eh + 1);
      for (const s of [-1, 1]) for (let j = 0; j < (adult ? 2 : 1); j++) for (let i = 0; i < bw; i++) setc(cx + s * bx - bw / 2 + i, by + j, PAL.blush);
    }
    // 嘴
    const my = Math.round(ey + eh + (adult ? 2 : 1)), M = PAL.mouth, mx = Math.round(cx);
    if (mouth === 'smile') { setc(mx - 2, my, M); setc(mx - 1, my + 1, M); setc(mx, my + 1, M); setc(mx + 1, my, M); if (adult) { setc(mx - 3, my - 1, M); setc(mx + 2, my - 1, M); } }
    else if (mouth === 'big') { for (let i = -2; i <= 2; i++) { setc(mx + i, my, M); } for (let i = -1; i <= 1; i++) setc(mx + i, my + 1, PAL.mouthIn); if (adult) { setc(mx - 2, my + 1, M); setc(mx + 2, my + 1, M); for (let i = -1; i <= 1; i++) setc(mx + i, my + 2, M); } }
    else if (mouth === 'open') { for (let j = 0; j < (adult ? 3 : 2); j++) for (let i = -1; i <= 1; i++) setc(mx + i, my + j, j === 0 ? M : PAL.mouthIn); }
    else if (mouth === 'frown') { setc(mx - 1, my + 1, M); setc(mx, my, M); setc(mx + 1, my + 1, M); if (adult) { setc(mx - 2, my + 2, M); setc(mx + 2, my + 2, M); } }
    else if (mouth === 'dot') { setc(mx, my, M); setc(mx + 1, my, M); }
    else if (mouth === 'o') { setc(mx, my, M); setc(mx + 1, my, M); setc(mx, my + 1, M); setc(mx + 1, my + 1, M); }
    else if (mouth === 'wavy') { for (let i = -2; i <= 2; i++) setc(mx + i, my + (i & 1), M); }
    // 絨芽
    const top = Math.round(cy - ry * sy);
    const sway = o.anim === 'idle' ? [0, 0, 1, 0][f % 4] : o.anim === 'happy' ? [-1, 0, 1, 0][f % 4] : 0;
    const form = o.form;
    const stemL = adult ? (form === 'bright' ? 10 : form === 'soft' ? 8 : 5) : 4;
    const lean = form === 'dust' ? -1 : 1;
    const dim = o.anim === 'sleep' || o.anim === 'unwell' || face === 'sleepy';
    let bx = cx, by = top;
    for (let i = 0; i < stemL; i++) {
      const dx = Math.round(lean * i * (form === 'dust' ? 0.35 : 0.18)) + (i > stemL / 2 ? sway : 0);
      const yy = top - i; bx = cx + dx; by = yy;
      setc(bx, yy, PAL.stem); if (adult) setc(bx + 1, yy, PAL.stemD);
    }
    if (adult && form !== 'dust') for (const s of [-1, 1]) { const ly = top - 3; for (let i = 1; i <= 3; i++) setc(cx + s * i + (s > 0 ? 1 : 0), ly - (i > 1 ? 1 : 0), i === 3 ? PAL.stemD : PAL.stem); }
    if (!adult) { setc(cx - 1, top - 2, PAL.stem); setc(cx - 2, top - 3, PAL.stem); }
    const br = adult ? (form === 'bright' ? 4 : form === 'soft' ? 3 : 1) : 1;
    by -= br + 1;
    const budCol = form === 'dust' ? '#d8cfa8' : dim ? PAL.budD : PAL.bud;
    for (let dy = -br; dy <= br; dy++) { const w = Math.floor(Math.sqrt(br * br - dy * dy + br * 0.6)); for (let dx = -w; dx <= w; dx++) setc(bx + dx, by + dy, dy === br || Math.abs(dx) === w && br > 1 ? PAL.budD : budCol); }
    if (!dim && form !== 'dust') { setc(bx - (br > 1 ? 1 : 0), by - (br > 1 ? 1 : 0), PAL.budHi); if (br > 2) { setc(bx, by - 1, PAL.budHi); setc(bx - 1, by, PAL.budHi); setc(bx, by, PAL.budHi); } }
    if (form === 'bright' && adult) {
      const rays = [[0, -1], [1, -1], [1, 0], [1, 1], [0, 1], [-1, 1], [-1, 0], [-1, -1]];
      rays.forEach((r, k) => { const L = k % 2 === 0 ? 4 : 2; for (let i = 0; i < L; i++) setc(bx + r[0] * (br + 2 + i), by + r[1] * (br + 2 + i), dim ? PAL.budD : (i === L - 1 ? PAL.bud : PAL.budHi)); });
    }
    // 燦光：身邊閃粒
    if (form === 'bright' && adult && !dim) {
      const sp = [[-30, -2], [30, 6], [-26, 16], [27, -10]];
      sp.forEach((p, k) => { if ((f + k) % 4 < 2) { const sx = Math.round(cx + p[0] * 1), sy2 = Math.round(cy + p[1]); setc(sx, sy2, PAL.budHi); setc(sx - 1, sy2, PAL.bud); setc(sx + 1, sy2, PAL.bud); setc(sx, sy2 - 1, PAL.bud); setc(sx, sy2 + 1, PAL.bud); } });
    }
    const c = mk(CW, CH); c.getContext('2d').putImageData(new ImageData(buf, CW, CH), 0, 0);
    c.anchor = { x: cx, y: B, bud: { x: bx, y: by }, top: top, w: CW, h: CH };
    return c;
  }
  function genEgg(frame, prog) {
    const CW = 40, CH = 48, cx = 20, cy = 27, rx = 12, ry = 16;
    const buf = new Uint8ClampedArray(CW * CH * 4);
    const pal = ['#fffbe0', '#ffeeb0', '#f8cf80', '#d99e5c', '#a8683a'].map(hex);
    const setc = (x, y, c) => { if (x < 0 || y < 0 || x >= CW || y >= CH) return; c = typeof c === 'string' ? hex(c) : c; const i = (y * CW + x) * 4; buf[i] = c[0]; buf[i + 1] = c[1]; buf[i + 2] = c[2]; buf[i + 3] = 255; };
    const mask = new Uint8Array(CW * CH);
    const sh = (y) => Math.round(Math.sin(frame * Math.PI / 2) * (1 - y / CH) * 1.6);
    for (let y = 0; y < CH; y++) for (let x = 0; x < CW; x++) {
      const ny = (y + 0.5 - cy) / ry, nx = (x + 0.5 - sh(y) - cx) / (rx * (1 + 0.14 * ny));
      if (nx * nx + ny * ny < 1) mask[y * CW + x] = 1;
    }
    const inM = (x, y) => x >= 0 && y >= 0 && x < CW && y < CH && mask[y * CW + x] === 1;
    for (let y = 0; y < CH; y++) for (let x = 0; x < CW; x++) if (inM(x, y)) {
      const nx = (x + 0.5 - cx) / rx, ny = (y + 0.5 - cy) / ry, t = nx * 0.5 + ny * 0.6;
      let idx = clamp(Math.round((t + 1) * 1.4 + (BAYER[y & 3][x & 3] - 0.5) * 0.9), 0, 3);
      if (!inM(x - 1, y) || !inM(x + 1, y) || !inM(x, y - 1) || !inM(x, y + 1)) idx = t > -0.2 ? 4 : 3;
      let c = pal[idx];
      if (hash(x * 7 + y * 19) > 0.93 && idx < 4) c = pal[0];
      setc(x, y, c);
    }
    // 光紋（星形）
    const gl = prog > 0.2 ? '#fff6b8' : '#ffe27a';
    for (const [dx, dy] of [[0, -3], [0, -2], [0, -1], [0, 0], [0, 1], [0, 2], [0, 3], [-3, 0], [-2, 0], [-1, 0], [1, 0], [2, 0], [3, 0], [-1, -1], [1, -1], [-1, 1], [1, 1]]) setc(cx + dx + sh(cy + dy), cy + dy + 3, gl);
    for (const [dx, dy] of [[-6, -6], [6, -3], [-7, 5], [5, 9], [-3, 11], [7, 4]]) setc(cx + dx, cy + dy, '#fff0a0');
    // 裂紋
    if (prog > 0.45) {
      const len = Math.ceil((prog - 0.45) / 0.55 * 13); let x = cx - 1, y = cy - ry + 2;
      for (let i = 0; i < len; i++) { setc(x + sh(y), y, '#7a4a2a'); setc(x + 1 + sh(y), y, '#fff0a0'); y++; if (i % 2 === 1) x += (i % 4 === 1 ? 1 : -1) * 2; setc(x + sh(y), y, '#7a4a2a'); }
    }
    const c = mk(CW, CH); c.getContext('2d').putImageData(new ImageData(buf, CW, CH), 0, 0);
    c.anchor = { x: cx, y: 43, bud: { x: cx, y: cy }, top: cy - ry, w: CW, h: CH };
    return c;
  }
  function petSprite(o) {
    if (o.stage === 'egg') { const p = Math.round(o.prog * 10) / 10; const key = 'egg' + (o.frame % 4) + '_' + p; return petCache[key] || (petCache[key] = genEgg(o.frame % 4, p)); }
    const key = [o.stage, o.form, o.anim, o.frame, o.face].join('|');
    return petCache[key] || (petCache[key] = genPet(o));
  }

  // ───────── 層畫布 ─────────
  function drawFar(look) {
    const c = mk(LW, LH), ctx = c.getContext('2d');
    const img = ctx.createImageData(LW, LH), d = img.data, N = 11;
    for (let y = 0; y < LH; y++) {
      const t = clamp(y / (MY + 262), 0, 1), tt = t * t * 0.5 + t * 0.5;
      for (let x = 0; x < LW; x++) {
        const lv = tt * (N - 1), i = Math.floor(lv), fr = lv - i;
        const j = i + (fr > BAYER[y & 3][x & 3] ? 1 : 0);
        const col = mixc(look.top, look.bot, clamp(j / (N - 1), 0, 1));
        const k = (y * LW + x) * 4; d[k] = col[0]; d[k + 1] = col[1]; d[k + 2] = col[2]; d[k + 3] = 255;
      }
    }
    ctx.putImageData(img, 0, 0);
    const dark = (t) => mixc(look.bot, [8, 12, 30], t);
    // 遠山
    const hills = (base, amp, seed, col, ph) => { ctx.fillStyle = rgb(col); for (let x = 0; x < LW; x++) { const y = Math.round(base + Math.sin(x * 0.045 + seed) * amp + Math.sin(x * 0.11 + seed * 2.3) * amp * 0.4 + Math.sin(x * 0.02 + ph) * amp * 0.8); ctx.fillRect(x, y, 1, LH - y); } };
    hills(MY + 232, 9, 1.3, dark(0.45), 0.4);
    // 遠處小屋同燈窗
    ctx.fillStyle = rgb(dark(0.62)); ctx.fillRect(MX + 138, MY + 218, 14, 12); ctx.fillRect(MX + 136, MY + 216, 18, 3); ctx.fillRect(MX + 141, MY + 212, 8, 4);
    ctx.fillStyle = rgb(mixc(look.lantern, [255, 255, 255], 0.2)); ctx.fillRect(MX + 141, MY + 222, 2, 3); ctx.fillRect(MX + 147, MY + 222, 2, 3);
    hills(MY + 246, 7, 4.1, dark(0.62), 1.9);
    // 遠處杉樹剪影
    ctx.fillStyle = rgb(dark(0.72));
    for (let k = 0; k < 11; k++) { const x = MX + 4 + k * 19 + Math.floor(hash(k) * 9), h = 12 + Math.floor(hash(k + 9) * 12), by = MY + 250; for (let r = 0; r < h; r++) { const w = Math.floor((r / h) * 5) + 1; ctx.fillRect(x - w, by - h + r, w * 2 + 1, 1); } }
    hills(MY + 258, 4, 7.7, dark(0.8), 3.1);
    return c;
  }
  function drawMid(look) {
    const c = mk(LW, LH), ctx = c.getContext('2d');
    const base = mixc(look.top, [10, 40, 52], 0.65), lit = mixc(base, look.lantern, 0.12), hi = mixc(base, [150, 190, 200], 0.28);
    const tree = (x, by, h, seed, sc) => {
      x += MX; by += MY;
      ctx.fillStyle = rgb(mixc(base, [20, 12, 10], 0.5)); ctx.fillRect(x - 2 * sc, by - h * 0.6, 4 * sc, h * 0.6 + 2);
      const blobs = [[0, -h * 0.78, 17], [-14, -h * 0.55, 13], [14, -h * 0.55, 13], [-6, -h * 0.98, 12], [8, -h * 0.9, 11], [-20, -h * 0.4, 8], [20, -h * 0.38, 8]];
      for (const b of blobs) disc(ctx, Math.round(x + b[0] * sc), Math.round(by + b[1]), Math.round(b[2] * sc), rgb(base));
      for (const b of blobs) disc(ctx, Math.round(x + b[0] * sc + 2 * sc), Math.round(by + b[1] - 2 * sc), Math.round(b[2] * sc * 0.72), rgb(lit));
      for (let i = 0; i < 26; i++) { const a = hash(seed + i) * 6.28, r = hash(seed * 3 + i) * 20 * sc; const px = Math.round(x + Math.cos(a) * r), py = Math.round(by - h * 0.7 + Math.sin(a) * r * 0.9); ctx.fillStyle = rgb(hi); ctx.fillRect(px, py, 2, 1); }
      for (let i = 0; i < 4; i++) { ctx.fillStyle = rgb(mixc(look.lantern, [255, 255, 255], 0.3)); ctx.fillRect(Math.round(x - 16 * sc + hash(seed + i * 5) * 32 * sc), Math.round(by - h * 0.9 + hash(seed + i * 9) * h * 0.5), 1, 1); }
    };
    tree(10, 238, 150, 3, 1.25); tree(188, 240, 136, 8, 1.15); tree(60, 244, 80, 14, 0.8); tree(140, 246, 86, 21, 0.85);
    // 後方矮籬／灌木帶
    ctx.fillStyle = rgb(mixc(base, [6, 20, 24], 0.5));
    for (let x = 0; x < LW; x++) { const y = Math.round(MY + 250 + Math.sin(x * 0.2) * 2 + Math.sin(x * 0.07) * 3); ctx.fillRect(x, y, 1, 30); }
    ctx.fillStyle = rgb(mixc(base, [60, 100, 90], 0.2)); for (let x = 0; x < LW; x += 3) { const y = Math.round(MY + 250 + Math.sin(x * 0.2) * 2 + Math.sin(x * 0.07) * 3); ctx.fillRect(x, y, 1, 1); }
    // 燈籠串嘅線
    ctx.fillStyle = rgb(mixc(base, [20, 14, 10], 0.7));
    for (let x = 30; x <= 168; x++) { const t = (x - 30) / 138; const y = Math.round(92 + Math.sin(t * Math.PI) * 28 + 0 * t); ctx.fillRect(x + MX, y + MY, 1, 1); }
    return c;
  }
  function drawStage(look) {
    const c = mk(LW, LH), ctx = c.getContext('2d');
    const gx = MX + CX, gy = MY + 296;
    const ell = (cx, cy, rx, ry, col) => { ctx.fillStyle = col; for (let dy = -ry; dy <= ry; dy++) { const w = Math.round(rx * Math.sqrt(1 - (dy * dy) / (ry * ry))); ctx.fillRect(cx - w, cy + dy, w * 2, 1); } };
    const soil = '#3a2a22', soil2 = '#291c18';
    ell(gx, gy + 7, 86, 24, soil2); ell(gx, gy + 5, 86, 23, soil);
    const g1 = mixc(hex('#2f5a4a'), look.top, 0.12), g2 = mixc(hex('#3f7058'), look.bot, 0.1), g3 = mixc(hex('#5a8a62'), look.lantern, 0.06);
    ell(gx, gy, 82, 22, rgb(g1)); ell(gx, gy - 1, 78, 19, rgb(g2)); ell(gx - 2, gy - 3, 66, 14, rgb(g3));
    for (let i = 0; i < 60; i++) { const a = hash(i) * 6.28, r = Math.sqrt(hash(i + 50)) * 74; ctx.fillStyle = rgb(mixc(g3, [190, 230, 170], 0.3 * hash(i + 7))); ctx.fillRect(Math.round(gx + Math.cos(a) * r), Math.round(gy - 1 + Math.sin(a) * r * 0.24), 1, 2); }
    // 邊緣石
    for (let i = 0; i < 28; i++) { const a = (i / 28) * 6.28, x = Math.round(gx + Math.cos(a) * 83), y = Math.round(gy + 4 + Math.sin(a) * 23); ctx.fillStyle = '#6a6a74'; ctx.fillRect(x - 1, y, 3, 2); ctx.fillStyle = '#8a8a94'; ctx.fillRect(x - 1, y, 2, 1); ctx.fillStyle = '#44444e'; ctx.fillRect(x, y + 2, 2, 1); }
    // 苔蘚小窩
    ell(gx, gy + 1, 32, 9, '#264a3c'); ell(gx, gy, 30, 8, rgb(hex('#4a7a5a'))); ell(gx, gy - 1, 24, 6, '#6a9a6a');
    for (let i = 0; i < 16; i++) { ctx.fillStyle = '#8aba7a'; ctx.fillRect(gx - 24 + Math.floor(hash(i + 3) * 48), gy - 5 + Math.floor(hash(i + 9) * 8), 2, 1); }
    // 燈柱（左）
    const lx = MX + 24, ly = MY + 306;
    ctx.fillStyle = '#4a3020'; ctx.fillRect(lx - 1, ly - 52, 3, 54); ctx.fillStyle = '#6a4a30'; ctx.fillRect(lx - 1, ly - 52, 1, 54);
    ctx.fillStyle = '#3a2418'; ctx.fillRect(lx - 4, ly - 56, 9, 2); ctx.fillRect(lx - 3, ly - 3, 7, 3);
    // 蘑菇群（右）
    const mx0 = MX + 168, my0 = MY + 304;
    for (const [dx, dy, r] of [[-9, 0, 4], [0, 2, 6], [10, -1, 3], [5, -6, 3]]) { ctx.fillStyle = '#f0e0c0'; ctx.fillRect(mx0 + dx - 1, my0 + dy - r + 2, 3, r); disc(ctx, mx0 + dx, my0 + dy - r, r, '#f0956a'); ctx.fillStyle = '#ffd0a0'; ctx.fillRect(mx0 + dx - 1, my0 + dy - r - 2, 2, 1); ctx.fillRect(mx0 + dx + 1, my0 + dy - r, 1, 1); }
    // 小花叢
    for (let i = 0; i < 14; i++) { const x = MX + 18 + Math.floor(hash(i + 70) * 160), y = MY + 300 + Math.floor(hash(i + 80) * 22); ctx.fillStyle = '#2a5a40'; ctx.fillRect(x, y, 1, 3); ctx.fillStyle = hash(i) > 0.5 ? '#ffd88a' : '#f8b0a0'; ctx.fillRect(x - 1, y - 1, 3, 1); ctx.fillRect(x, y - 2, 1, 3); }
    return c;
  }
  function drawFore() {
    const c = mk(LW, LH), ctx = c.getContext('2d');
    const col = '#07161a', col2 = '#0d2a2a', col3 = '#154038';
    for (let i = 0; i < 70; i++) {
      const x = Math.round(i * (LW / 70) + hash(i) * 4), h = 18 + Math.floor(hash(i + 20) * 34), by = LH - 2, lean = (hash(i + 40) - 0.5) * 8;
      for (let r = 0; r < h; r++) { const t = r / h, xx = Math.round(x + lean * t * t); ctx.fillStyle = r > h - 6 ? col3 : (i % 3 ? col : col2); ctx.fillRect(xx, by - r, r > h - 3 ? 1 : 2, 1); }
    }
    ctx.fillStyle = col; ctx.fillRect(0, LH - 10, LW, 10);
    // 兩側大葉
    const leaf = (x, y, dir, len) => { for (let i = 0; i < len; i++) { const t = i / len, w = Math.round(Math.sin(t * Math.PI) * 6 + 1), xx = x + dir * i, yy = y - Math.round(t * t * 40); ctx.fillStyle = i % 5 === 0 ? col3 : col; ctx.fillRect(xx, yy - w, 1, w * 2); } };
    leaf(0, LH - 40, 1, 46); leaf(0, LH - 10, 1, 40); leaf(LW, LH - 60, -1, 50); leaf(LW, LH - 14, -1, 44);
    return c;
  }

  // ───────── 寵物 clip 渲染輔助（真 atlas＋placeholder）─────────
  const DUST_HEAD = [13, -26];                    // 微塵形態冇圖集：程序化精靈嘅 head_r 錨點
  const formKeyOf = (s) => s.stage === 'adult' ? (s.form === 'bright' ? 'radiant' : (s.form === 'soft' || s.form === 'lumi') ? 'soft' : 'dust') : 'sprout';   // 螢絨（lumi）暫借柔光 atlas＋螢光 tint（未有專屬美術）
  // 待定／額外 clip 嘅程序化佔位：用 idle 幀＋簡單變形（dy＝上下、dx＝前後、sx／sy＝縮放）
  function placeholderXform(clip, b, t) {
    const T = { sx: 1, sy: 1, dx: 0, dy: 0 };
    switch (clip) {
      case 'walk': T.dy = -(Math.sin(t * 11) > 0.55 ? 1 : 0); T.sy = 1 - 0.03 * Math.abs(Math.sin(t * 11)); break;
      case 'play': T.dy = -Math.round(Math.abs(Math.sin(t * 6)) * 3); break;
      case 'sunbathe': T.sy = 0.82; T.sx = 1.1; break;
      case 'pot_bump': { const u = b.clipT; T.dx = u < 0.3 ? 1 : u < 0.5 ? -3 : u < 0.65 ? 1 : 0; T.sx = u >= 0.3 && u < 0.5 ? 1.08 : 1; break; }
      case 'jump': T.sy = b.lift === 0 ? 0.9 : 1.06; T.sx = b.lift === 0 ? 1.06 : 0.96; break;
      case 'grumpy': T.dx = Math.round(Math.sin(t * 55)); T.sy = 0.95; break;
      case 'dig': T.dy = Math.sin(t * 10) > 0 ? 1 : 0; T.sy = 0.94; break;
      case 'lookup': T.sy = 1.04; break;
      // 生命感第二段：冇 live atlas（?live=0／微塵）時嘅程序化佔位
      case 'sniff': T.sy = 0.9; T.dx = 1; T.dy = 1; break;
      case 'swat': T.dx = b.frame >= 2 ? 2 : 0; T.sy = b.frame >= 2 ? 1.05 : 0.96; break;
      case 'scratch': T.dx = Math.round(Math.sin(t * 40)); T.sy = 0.96; break;
      case 'sneeze': if (b.frame === 2) { T.sx = 1.1; T.sy = 0.88; } else T.sy = 1.03; break;
      case 'cheer_jump': case 'catch_reach': T.sy = b.lift === 0 ? 0.92 : 1.05; break;
      case 'droop': T.sy = 0.9; break;
    }
    return T;
  }
  function procAnim(clip) {
    if (clip === 'fall_asleep' || clip === 'sleep_loop' || clip === 'emo_sleepy') return 'sleep';
    if (clip === 'sick') return 'unwell';
    if (clip === 'emo_happy' || clip === 'celebrate' || clip === 'cheer_jump' || clip === 'emo_cuddly') return 'happy';
    if (clip === 'eat') return 'eat';
    return 'idle';
  }

  // ───────── Renderer ─────────
  class Renderer {
    constructor(canvas) {
      this.canvas = canvas; this.ctx = canvas.getContext('2d', { alpha: false });
      initSprites();
      this.k = 2; this.t = 0; this.frameNo = 0;
      this.par = { x: 0, y: 0 }; this.parT = { x: 0, y: 0, active: false, last: -99 };
      this.fx = []; this.pet = { act: null, until: 0, lift: 0 };
      this.sleepMix = 0; this.eggPulse = 0; this.flash = 0; this.shake = 0;
      this.atlas = {}; this.atlasReady = false; this.atlasError = null; this.petX = 0; this.sunMix = 0; this.tmpPet = mk(96, 112); this.tintPet = mk(96, 112); this.rimPet = mk(96, 112); this.dl = null; this.dlReady = false;
      this.lookKey = ''; this.layers = null; this.bl = {};
      this.lv = null; this.lvError = null; this.bulbCache = {}; this.bulbS = null;   // 生命感：noface 身體＋kit 五官＋燈泡
      this.ovStat = { moonStars: 0, lanterns: 0 };   // 引擎程序化疊層（月 (150,76)＋星／燈籠串）實際畫咗幾多幀（HD-2D 開時應為 0）
      this.faceStat = { draws: 0, tints: 0, overlays: 0, faceDrawn: 0, faceHidden: 0, placeholder: 0, bulb: 0, last: null };
      this.glowCache = {}; this.fireflies = []; this.stars = [];
      for (let i = 0; i < 9; i++) this.fireflies.push({ x: hash(i) * W, y: 150 + hash(i + 9) * 170, ph: hash(i + 3) * 6.28, sp: 0.2 + hash(i + 5) * 0.4 });
      for (let i = 0; i < 70; i++) this.stars.push({ x: Math.floor(hash(i + 100) * W), y: Math.floor(hash(i + 200) * 210), ph: hash(i + 300) * 6.28, b: hash(i + 400) });
      this.live = [mk(LW, LH), mk(LW, LH), mk(LW, LH), mk(LW, LH)];
      this.em = mk(W, H);
      this.work = [mk(W, H), mk(W / 2, H / 2), mk(W / 4, H / 4), mk(W / 8, H / 8)];
      this.bufs = {}; // 景深暫存
      this.perf = { n: 0, sum: 0, max: 0 };
      this.setScale(2);
    }
    setScale(k) {
      this.k = k; this.canvas.width = W * k; this.canvas.height = H * k;
      this.vig = null; this.tsA = mk(W * k / 2, H * k / 2); this.tsB = mk(W * k / 2, H * k / 2); this.tsMask = null;
    }
    // art → 層畫布座標
    screenToArt(cx, cy) { const r = this.canvas.getBoundingClientRect(); return { x: (cx - r.left) / r.width * W, y: (cy - r.top) / r.height * H }; }
    // 載入遊美 atlas（png＋json）。失敗就保持 atlasReady=false → 退回程序化精靈。
    loadAtlases(base) {
      base = base || P.art.base;
      const names = ['atlas_egg', 'atlas_sprout', 'atlas_radiant', 'atlas_soft', 'atlas_props', 'atlas_events'];   // atlas_egg 來自遊美 atlas_legacy（1024 寬、padding2／extrude1）；舊 2048 圖已棄用
      const jobs = names.map(n => Promise.all([
        fetch(base + n + '.json').then(r => { if (!r.ok) throw new Error(n + '.json ' + r.status); return r.json(); }),
        new Promise((res, rej) => { const im = new Image(); im.onload = () => res(im); im.onerror = () => rej(new Error(n + '.png')); im.src = base + n + '.png'; }),
      ]).then(([json, img]) => { this.atlas[n] = { json, img }; }));
      return Promise.all(jobs).then(() => { this.atlasReady = true; }).catch(e => { this.atlasError = String(e && e.message || e); });
    }
    // 生命感（遊美 10-31）：face_anchors.json＋atlas_<form>_live（<clip>_noface 身體、kit 五官、燈泡）。逐件容錯：缺乜就 fallback 乜。
    loadLive(cfg) {
      cfg = cfg || P.face.liveliness; const base = cfg.base; const lv = { atlas: {}, anchors: null, errors: [] };
      const img = (src) => new Promise((res, rej) => { const im = new Image(); im.onload = () => res(im); im.onerror = () => rej(new Error(src)); im.src = src; });
      const jget = (u) => fetch(u).then(r => { if (!r.ok) throw new Error(u + ' ' + r.status); return r.json(); });
      const jobs = [jget(base + cfg.anchors).then(j => { lv.anchors = j.anchors; lv.pivotPx = j.pivotPx; }).catch(e => lv.errors.push(String(e.message || e)))];
      // s2：每 form 可有多張 atlas（atlas_<form>_live＋atlas_<form>_live_s2）→ 合併 frames／animations（每幀記住自己張圖）；第一張（五官 kit）必須有，後面缺就照用 fallback
      Object.keys(cfg.atlases).forEach(f => { const ns = [].concat(cfg.atlases[f]);
        jobs.push(Promise.all(ns.map((n, i) => Promise.all([jget(base + n + '.json'), img(base + n + '.png')]).catch(e => { lv.errors.push(String(e.message || e)); if (i === 0) throw e; return null; }))).then(parts => {
          const m = { frames: {}, animations: {}, meta: parts[0][0].meta, parts: [] };
          parts.forEach((pt, i) => { if (!pt) return; const [json, im] = pt; m.parts.push(ns[i]); for (const k in json.frames) m.frames[k] = Object.assign({ _img: im }, json.frames[k]); Object.assign(m.animations, json.animations || {}); });
          lv.atlas[f] = { json: m, img: parts[0][1] };
        }).catch(() => { })); });
      if (cfg.fx) jobs.push(Promise.all([jget(base + cfg.fx + '.json'), img(base + cfg.fx + '.png')]).then(([json, im]) => { lv.fx = { json, img: im }; }).catch(e => lv.errors.push(String(e.message || e))));   // fx bug（8×8，3 幀，pivot (4,4)）
      return Promise.all(jobs).then(() => { this.lv = Object.keys(lv.atlas).length ? lv : null; this.lvError = lv.errors.length ? lv.errors.join('; ') : null; return this.lv; });
    }
    liveFrame(fk, name) {               // kit piece／幀：{img,sx,sy,sw,sh,px,py}
      const A = this.lv && this.lv.atlas[fk]; const f = A && A.json.frames[name]; if (!f) return null;
      const pv = f.pivotPx || { x: f.frame.w >> 1, y: f.frame.h >> 1 };
      return { img: f._img || A.img, sx: f.frame.x, sy: f.frame.y, sw: f.frame.w, sh: f.frame.h, px: pv.x, py: pv.y, name };
    }
    liveAnchors(fk, clip, frame, src) {  // 錨點：face_anchors；冇就由 FORMS.headR 推算
      const L = this.lv && this.lv.anchors && this.lv.anchors[fk] && this.lv.anchors[fk][clip];
      if (L && L.length) return L[((frame % L.length) + L.length) % L.length];
      const hr = (D.FORMS[fk] || D.FORMS.soft).headR, cx = src.px, cy = src.py;
      return { eyeL: [cx - Math.round(hr[0] * 0.44), cy + Math.round(hr[1] * 0.6)], eyeR: [cx + Math.round(hr[0] * 0.44), cy + Math.round(hr[1] * 0.6)], mouth: [cx, cy + Math.round(hr[1] * 0.4)], head_r: [cx + hr[0], cy + hr[1]], bulb: [cx, cy + Math.round(hr[1] * 1.45)], faceVisible: true, derived: true };
    }
    bulbMood(b) {
      if (b.bulbForce && P.face.bulb.moods[b.bulbForce]) return b.bulbForce;          // G1：開發者掣強制心情（循環 5 款）
      if (b.state === 'grumpy') return 'grumpy';
      if (b.clip === 'sleep_loop' || b.clip === 'fall_asleep' || b.expr === 'tired') return 'sleepy';
      if (b.expr === 'hungry') return 'hungry';
      if (b.expr === 'happy' || b.state === 'nuzzle' || /^(emo_happy|celebrate|cheer_jump|emo_cuddly|nuzzle|rush|reunion_happy)$/.test(b.clip)) return 'happy';   // s3：磨蹭／衝埋嚟／重逢都開心
      return 'neutral';
    }
    bulbGlow(fk, rgb) {                 // bulb_glow × tint（multiply，保留 alpha）；按色快取（量化 8 級）
      const g = this.liveFrame(fk, 'bulb_glow'); if (!g) return null;
      const q = rgb.map(v => Math.round(v / 8) * 8), key = fk + q.join(','); let c = this.bulbCache[key];
      if (!c) { c = mk(g.sw, g.sh); const x = c.getContext('2d'); x.imageSmoothingEnabled = false; x.drawImage(g.img, g.sx, g.sy, g.sw, g.sh, 0, 0, g.sw, g.sh);
        x.globalCompositeOperation = 'multiply'; x.fillStyle = 'rgb(' + q.join(',') + ')'; x.fillRect(0, 0, g.sw, g.sh); x.globalCompositeOperation = 'destination-in'; x.drawImage(g.img, g.sx, g.sy, g.sw, g.sh, 0, 0, g.sw, g.sh);
        this.bulbCache[key] = c; }
      return { c, px: g.px, py: g.py };
    }
    // 遊美 daylight：art/daylight/{bg,light}_<early|noon|dusk|night>.png（480×270，1x）；daylight.json 由 main fetch → LIGHT.setDaylight
    loadDaylight(base) {
      base = (base || P.art.base) + 'daylight/'; const ids = ['early', 'noon', 'dusk', 'night']; this.dl = { bg: {}, light: {}, edge: {} };
      const ld = (kind, id) => new Promise((res, rej) => { const im = new Image(); im.onload = () => { this.dl[kind][id] = im; res(); }; im.onerror = () => rej(new Error(kind + '_' + id)); im.src = base + kind + '_' + id + '.png'; });
      const jobs = []; ids.forEach(id => { jobs.push(ld('bg', id)); jobs.push(ld('light', id)); });
      return Promise.all(jobs).then(() => {
        ids.forEach(id => { const im = this.dl.bg[id], c = mk(1, 2), g = c.getContext('2d'); g.imageSmoothingEnabled = true; g.drawImage(im, 0, 0, im.width, 6, 0, 0, 1, 1); g.drawImage(im, 0, im.height - 6, im.width, 6, 0, 1, 1, 1); const d = g.getImageData(0, 0, 1, 2).data; this.dl.edge[id] = ['rgb(' + d[0] + ',' + d[1] + ',' + d[2] + ')', 'rgb(' + d[4] + ',' + d[5] + ',' + d[6] + ')']; });
        this.dlReady = true;
      }).catch(e => { this.dlError = String(e && e.message || e); });
    }
    // 寵物 tint（daylight.json pet.multiply／add／rim）：sprite → multiply → add → 以 sprite alpha 遮罩 → 窗光側 1px rim
    tintSprite(src, dl, mir, lumi) {
      this.faceStat.tints++;
      const T = this.tintPet, g = T.getContext('2d'), PX = 48, PY = 100, ox = PX - src.px, oy = PY - src.py, pm = dl.pet, c3 = (a) => 'rgb(' + (a[0] | 0) + ',' + (a[1] | 0) + ',' + (a[2] | 0) + ')';
      const mask = (gg, dx) => gg.drawImage(src.img, src.sx, src.sy, src.sw, src.sh, ox + dx, oy, src.sw, src.sh);
      g.setTransform(1, 0, 0, 1, 0, 0); g.clearRect(0, 0, 96, 112); g.imageSmoothingEnabled = false; g.globalCompositeOperation = 'source-over'; g.globalAlpha = 1; mask(g, 0);
      g.globalCompositeOperation = 'multiply'; g.fillStyle = c3(lumi ? [pm.mul[0] * 0.78, pm.mul[1], pm.mul[2] * 0.74] : pm.mul); g.fillRect(0, 0, 96, 112);
      g.globalCompositeOperation = 'lighter'; g.fillStyle = c3(pm.add); g.fillRect(0, 0, 96, 112);
      g.globalCompositeOperation = 'destination-in'; mask(g, 0);
      const R = this.rimPet, r = R.getContext('2d'); r.clearRect(0, 0, 96, 112); r.globalCompositeOperation = 'source-over'; r.fillStyle = c3(pm.rim); r.fillRect(0, 0, 96, 112);
      r.globalCompositeOperation = 'destination-in'; mask(r, 0); r.globalCompositeOperation = 'destination-out'; mask(r, mir > 0 ? 1 : -1); r.globalCompositeOperation = 'source-over';
      g.globalCompositeOperation = 'source-over'; g.globalAlpha = 0.8; g.drawImage(R, 0, 0); g.globalAlpha = 1;
      return { img: T, sx: ox, sy: oy, sw: src.sw, sh: src.sh, px: src.px, py: src.py, bud: src.bud };
    }
    // 幀實色框（相對幀左上；按 img+sx+sy cache，只 getImageData 一次）
    opaqueBox(src) {
      if (!src || !src.img) return null;
      const m = this._obox || (this._obox = new WeakMap()); let per = m.get(src.img); if (!per) { per = {}; m.set(src.img, per); }
      const key = src.sx + ',' + src.sy + ',' + src.sw + ',' + src.sh; if (key in per) return per[key];
      let r = null;
      try {
        const c = this._obC || (this._obC = document.createElement('canvas')); c.width = src.sw; c.height = src.sh; const g = c.getContext('2d', { willReadFrequently: true }); g.drawImage(src.img, src.sx, src.sy, src.sw, src.sh, 0, 0, src.sw, src.sh);
        const d = g.getImageData(0, 0, src.sw, src.sh).data; let l = 1e9, t = 1e9, rr = -1, bb = -1;
        for (let y = 0; y < src.sh; y++) for (let x = 0; x < src.sw; x++) if (d[(y * src.sw + x) * 4 + 3] > 24) { if (x < l) l = x; if (x > rr) rr = x; if (y < t) t = y; if (y > bb) bb = y; }
        if (rr >= 0) r = { l, t, r: rr + 1, b: bb + 1 };
      } catch (e) { r = null; }
      per[key] = r; return r;
    }
    petBox() { return { x: CX + this.petX - 38 + this.par.x * -1.5, y: GROUND_Y - 78, w: 76, h: 82 }; }
    // behavior 嘅 fx 請求 → 粒子（spark／steam 相對寵物；dust 相對 CX）
    behFx(b) {
      if (!b || !b.fx.length) return;
      for (const f of b.fx.splice(0)) {
        if (f.type === 'dust') for (let i = 0; i < 4; i++) this.spawn('dust', CX + f.x + (i - 1.5) * 3, GROUND_Y + f.y, { vx: (i - 1.5) * 9, vy: -8 - i * 2, max: 0.6 });
        else if (f.type === 'heart') this.burst('heart', CX + b.x + f.x, GROUND_Y + f.y, 2, 30);   // s3 重逢心心
        else if (f.type === 'steam') this.spawn('steam', CX + b.x + f.x, GROUND_Y + f.y, { vx: f.x * 0.5, vy: -16, max: 0.9 });
        else this.burst('spark', CX + b.x + f.x, GROUND_Y + f.y, 3, 40);
      }
    }
    poopPos(i) { return { x: POOP_SLOTS[i][0], y: POOP_SLOTS[i][1] }; }
    act(name, dur) { this.pet.act = name; this.pet.until = this.t + dur; }
    spawn(type, x, y, o) {
      o = o || {};
      this.fx.push(Object.assign({ type, x, y, vx: 0, vy: -14, life: 0, max: 1.2 }, o));
    }
    burst(type, x, y, n, spread) { for (let i = 0; i < n; i++) this.spawn(type, x + (hash(this.t * 7 + i) - 0.5) * 16, y + (hash(this.t * 5 + i) - 0.5) * 10, { vx: (hash(this.t + i * 3) - 0.5) * (spread || 40), vy: -10 - hash(this.t * 3 + i) * 26, max: 0.8 + hash(i + this.t) * 0.7 }); }
    glowSprite(col) {
      const key = (col[0] >> 3) + '_' + (col[1] >> 3) + '_' + (col[2] >> 3);
      let g = this.glowCache[key];
      if (!g) { g = mk(64, 64); const x = g.getContext('2d'); const gr = x.createRadialGradient(32, 32, 0, 32, 32, 32); gr.addColorStop(0, rgb(col, 1)); gr.addColorStop(0.25, rgb(col, 0.5)); gr.addColorStop(0.6, rgb(col, 0.14)); gr.addColorStop(1, rgb(col, 0)); x.fillStyle = gr; x.fillRect(0, 0, 64, 64); this.glowCache[key] = g; }
      return g;
    }
    moons() {
      if (this.moonSp) return this.moonSp;
      const full = mk(26, 26), fx = full.getContext('2d'); disc(fx, 13, 13, 11, '#f4f0d8'); disc(fx, 16, 15, 3, '#dcd8bc'); disc(fx, 9, 10, 2, '#e8e4c8'); disc(fx, 17, 8, 1, '#e0dcc0');
      const cres = mk(26, 26), cx = cres.getContext('2d'); cx.drawImage(full, 0, 0); cx.globalCompositeOperation = 'destination-out'; disc(cx, 8, 10, 9, '#000');
      return (this.moonSp = [cres, full]);
    }
    ensureLayers(look, hourKey) {
      if (this.lookKey !== hourKey || !this.layers) {
        this.lookKey = hourKey;
        this.layers = [drawFar(look), drawMid(look), drawStage(look), this.layers ? this.layers[3] : drawFore()];
      }
    }

    // 模糊（降解析度往返）。level 1 = ½；2 = ¼（較強）。結果喺 art 解析度畫布。
    blurLayer(idx, src, level, force) {
      const id = 'b' + idx; let b = this.bufs[id];
      if (!b) { b = this.bufs[id] = { out: mk(LW, LH), h: mk(LW / 2, LH / 2), q: mk(LW / 4, LH / 4), n: 0 }; }
      b.n++;
      if (!force && b.n % (this.blurEvery || 1) !== 0 && b.done) return b.out;
      const hx = b.h.getContext('2d'), qx = b.q.getContext('2d'), ox = b.out.getContext('2d');
      hx.imageSmoothingEnabled = qx.imageSmoothingEnabled = ox.imageSmoothingEnabled = true;
      hx.clearRect(0, 0, b.h.width, b.h.height); hx.drawImage(src, 0, 0, b.h.width, b.h.height);
      if (level >= 2) {
        qx.clearRect(0, 0, b.q.width, b.q.height); qx.drawImage(b.h, 0, 0, b.q.width, b.q.height);
        hx.clearRect(0, 0, b.h.width, b.h.height); hx.drawImage(b.q, 0, 0, b.h.width, b.h.height);
      }
      ox.clearRect(0, 0, LW, LH); ox.drawImage(b.h, 0, 0, LW, LH);
      b.done = true; return b.out;
    }

    // ───────── 主繪製 ─────────
    frame(dt, view) {
      const t0 = performance.now();
      dt = Math.min(dt, 0.1); this.t += dt; this.frameNo++;
      const t = this.t, s = view.state, q = view.quality || 'high', k = this.k;
      const hour = view.hour;
      const look = lookAt(hour);
      const lt = view.light || null;
      this.curDL = (lt && lt.daylight && P.art.daylight !== false) ? lt.daylight : null;
      const dlv = this.curDL, room = !!(dlv && P.art.daylightBg && this.dlReady);
      this.sunMix += (((view.beh && view.beh.state === 'sunbathe' && view.beh.phase === 'lie') ? 1 : 0) - this.sunMix) * Math.min(1, dt * 2);
      const hd = (this.hd && this.hd.on() && !room) ? this.hd : null;   // HD-2D 場景（src/hd2d.js）；off／未載入／?hd2d=0 → 舊程序化背景 fallback
      this.hdOn = !!hd;
      if (hd) hd.update(dt, { hour, weather: lt && lt.hd2d ? lt.hd2d.weather : view.weather });
      this.ensureLayers(look, Math.round(hour * 4) + '');
      // 視差
      const pt = this.parT;
      if (!pt.active || t - pt.last > 3) { pt.x = Math.sin(t * 0.21) * 0.55; pt.y = Math.sin(t * 0.13 + 1) * 0.35; }
      this.par.x += (pt.x - this.par.x) * Math.min(1, dt * 3.5); this.par.y += (pt.y - this.par.y) * Math.min(1, dt * 3.5);
      const px = this.par.x, py = this.par.y;
      const offs = [[-px * 3, -py * 2], [-px * 6, -py * 3], [-px * 1.5, 0], [px * 11, py * 5]];
      // 狀態光
      const sleeping = s.sleeping;
      this.sleepMix += ((sleeping ? 1 : 0) - this.sleepMix) * Math.min(1, dt * 2.2);
      const sm = this.sleepMix;
      const hunger = s.needs.hunger, hDim = s.stage === 'egg' ? 0 : clamp((50 - hunger) / 50, 0, 1);
      const unwell = SIM.isUnwell(s), wd = s.withdrawn.on && s.stage !== 'egg';
      this.eggPulse = Math.max(0, this.eggPulse - dt * 1.8); this.flash = Math.max(0, this.flash - dt * 1.4);
      const night = 1 - look.day;
      // 寵物動作
      let anim = sleeping ? 'sleep' : unwell ? 'unwell' : 'idle';
      let face = 'normal'; if (anim === 'idle') { if (wd) face = 'sleepy'; else if (SIM.needBand(s.needs[SIM.lowestNeed(s)]) === 'warn') face = 'sad'; }
      let lift = 0;
      if (this.pet.act && t < this.pet.until) {
        anim = this.pet.act; const ph = (this.pet.until - t);
        if (anim === 'happy') lift = -Math.abs(Math.sin(t * 9)) * (s.stage === 'adult' ? 9 : 5);
      } else this.pet.act = null;
      const fps = anim === 'idle' ? 3.2 : anim === 'sleep' ? 1 : anim === 'unwell' ? 2 : 7;
      let frame;
      if (anim === 'idle') frame = [0, 1, 2, 1, 0, 1, 2, 1, 0, 1, 2, 3][Math.floor(t * fps) % 12]; else frame = Math.floor(t * fps);
      const isMG = view.mode === 'minigame';

      // ── 畫各層 live ──
      const L = this.live; const em = this.em.getContext('2d');
      em.clearRect(0, 0, W, H);
      const lights = []; // {x,y,r,col,a,layer}
      // L0
      if (!hd) { this.ovStat.moonStars++; const x = L[0].getContext('2d'); x.clearRect(0, 0, LW, LH); x.drawImage(this.layers[0], 0, 0);   // HD-2D：引擎月 (150,76)／星唔畫（H4 場景已畫）
        const sa = clamp(1 - look.day * 1.3, 0, 1);
        if (sa > 0.02) for (const st of this.stars) { const tw = 0.55 + 0.45 * Math.sin(t * (1 + st.b * 2) + st.ph); const a = sa * (0.35 + 0.65 * tw) * (0.5 + st.b * 0.5); x.fillStyle = `rgba(255,248,220,${a.toFixed(2)})`; x.fillRect(st.x + MX, st.y + MY, 1, 1); if (st.b > 0.85 && tw > 0.8) { x.fillRect(st.x + MX - 1, st.y + MY, 3, 1); x.fillRect(st.x + MX, st.y + MY - 1, 1, 3); } if (st.b > 0.6) { em.fillStyle = `rgba(255,240,200,${(a * 0.7).toFixed(2)})`; em.fillRect(Math.round(st.x + offs[0][0]), Math.round(st.y + offs[0][1]), 1, 1); } }
        // 月亮（彎月／滿月兩張預製圖，睡眠時漸變滿月）
        const mx = 150 + MX, my = 76 + MY, ma = clamp(0.35 + night * 0.4 + sm * 0.5, 0, 1);
        const mo = this.moons();
        x.globalAlpha = ma * (1 - sm); x.drawImage(mo[0], mx - 13, my - 13);
        x.globalAlpha = ma * sm; x.drawImage(mo[1], mx - 13, my - 13); x.globalAlpha = 1;
        em.fillStyle = `rgba(255,250,220,${(ma * 0.8).toFixed(2)})`; em.beginPath(); em.arc(mx - MX + offs[0][0], my - MY + offs[0][1], 4 + sm * 4, 0, 6.3); em.fill();
        lights.push({ x: mx - MX + offs[0][0], y: my - MY + offs[0][1], r: 42 + sm * 34, col: [200, 215, 255], a: (0.28 + sm * 0.45) * (0.4 + night * 0.6) });
      }
      // L1：燈籠串
      const lanternA = (1 - sm * 0.62) * (1 - hDim * 0.25) * (lt ? lt.lanternMul : 1);
      const lcol = mixc(lt ? mixc(look.lantern, lt.lantern, lt.lanternMix) : look.lantern, [255, 140, 60], sm * 0.5);
      if (!hd) { this.ovStat.lanterns++; const x = L[1].getContext('2d'); x.clearRect(0, 0, LW, LH); x.drawImage(this.layers[1], 0, 0);   // HD-2D：引擎燈籠串唔畫
        for (let i = 0; i < 6; i++) {
          const u = (i + 0.5) / 6, lx0 = 30 + u * 138, ly0 = 92 + Math.sin(u * Math.PI) * 28;
          const sw = Math.sin(t * 1.3 + i * 1.7) * 1.4, lx = Math.round(lx0 + sw), ly = Math.round(ly0 + 4);
          const fl = 0.85 + 0.15 * Math.sin(t * 7 + i * 3) * Math.sin(t * 3.1 + i);
          x.fillStyle = '#3a2418'; x.fillRect(lx - 2 + MX, ly - 1 + MY, 5, 1); x.fillRect(lx - 2 + MX, ly + 7 + MY, 5, 1);
          x.fillStyle = rgb(mixc(lcol, [90, 40, 20], 0.35 + (1 - lanternA) * 0.3 + 0.0)); x.fillRect(lx - 2 + MX, ly + MY, 5, 7);
          x.fillStyle = rgb(mixc(lcol, [255, 255, 235], 0.5 * fl * lanternA)); x.fillRect(lx - 1 + MX, ly + 1 + MY, 3, 5);
          const ax = lx + offs[1][0], ay = ly + 3 + offs[1][1];
          lights.push({ x: ax, y: ay, r: 26, col: lcol, a: 0.7 * lanternA * fl, layer: 1 });
          em.fillStyle = rgb(lcol, 0.9 * lanternA * fl); em.fillRect(Math.round(ax) - 1, Math.round(ay) - 2, 3, 5);
        }
      }
      // L2：舞台 + 寵物
      this.drawL2(L[2].getContext('2d'), view, { anim, frame, face, lift, lanternA, lcol, lights, em, offs, look, unwell, wd, hDim, sm, t, hd: !!hd, q });
      if (hd) {                                             // HD-2D 合成（sky→far→mid→寵物→fore→×lightmap→lighter→雨→霧→暈影）
        hd.draw(this.ctx, k, { pet: L[2], offs, lights, quality: q, dt, t, dim: 0.34 * sm + 0.2 * hDim + (unwell ? 0.08 : 0) });
        const ctx = this.ctx;
        if (this.flash > 0) { ctx.globalAlpha = Math.min(1, this.flash); ctx.fillStyle = '#fff6d0'; ctx.fillRect(0, 0, W * k, H * k); ctx.globalAlpha = 1; }
        const ms = performance.now() - t0; this.perf.n++; this.perf.sum += ms; this.perf.max = Math.max(this.perf.max, ms); this.perf.last = ms;
        return;
      }
      // L3
      { const x = L[3].getContext('2d'); x.clearRect(0, 0, LW, LH); x.drawImage(this.layers[3], 0, 0); }

      // ── 合成到顯示畫布 ──
      const ctx = this.ctx; ctx.imageSmoothingEnabled = false;
      const post = q !== 'off';
      const dof = q === 'high' || q === 'mid';
      this.blurEvery = q === 'mid' ? 3 : 1;
      const put = (src, i, smooth) => { ctx.imageSmoothingEnabled = !!smooth; ctx.drawImage(src, Math.round((-MX + offs[i][0]) * k), Math.round((-MY + offs[i][1]) * k), LW * k, LH * k); };
      ctx.globalCompositeOperation = 'source-over'; ctx.globalAlpha = 1;
      const RY = GROUND_Y - 232, RSX = 143;                 // 房間底圖：pivot (240,232) 對齊 GROUND_Y、x 以 240 為中心裁 195 寬
      const roomDraw = (kind, id, a) => { const im = this.dl[kind][id]; if (!im || a <= 0) return; ctx.imageSmoothingEnabled = false; ctx.globalAlpha = a; ctx.drawImage(im, RSX, 0, W, 270, 0, RY * k, W * k, 270 * k); ctx.globalAlpha = 1; };
      if (room) {                                           // 可選「房間」皮膚（PARAMS.art.daylightBg／?room=1）：bg 取代 L0/L1/L3，跨時段 cross-fade
        const pe = this.dl.edge[dlv.prev], ce = this.dl.edge[dlv.id];
        ctx.fillStyle = ce[0]; ctx.fillRect(0, 0, W * k, RY * k); ctx.fillStyle = ce[1]; ctx.fillRect(0, (RY + 270) * k, W * k, (H - RY - 270) * k + 1);
        if (dlv.mix < 1) { ctx.globalAlpha = 1 - dlv.mix; ctx.fillStyle = pe[0]; ctx.fillRect(0, 0, W * k, RY * k); ctx.fillStyle = pe[1]; ctx.fillRect(0, (RY + 270) * k, W * k, (H - RY - 270) * k + 1); ctx.globalAlpha = 1; }
        roomDraw('bg', dlv.prev, 1); roomDraw('bg', dlv.id, dlv.mix);
        put(L[2], 2, false);
        roomDraw('light', dlv.prev, 1 - dlv.mix); roomDraw('light', dlv.id, dlv.mix);   // overlay（暗角＋光暈＋環境色已烘入）
      } else {
        if (dof) { put(this.blurLayer(0, L[0], 2), 0, true); put(L[1], 1, false); ctx.globalAlpha = 0.8; put(this.blurLayer(1, L[1], 1), 1, true); ctx.globalAlpha = 1; }
        else { put(L[0], 0, false); put(L[1], 1, false); }
        put(L[2], 2, false);
      }
      // 環境暗角色（睡眠／飢餓／夜）
      const amb = clamp(0.1 * night + 0.34 * sm + 0.2 * hDim + (unwell ? 0.08 : 0) + (lt ? lt.ambient : 0), 0, 0.6);
      if (amb > 0.01) { ctx.fillStyle = `rgba(8,12,44,${amb.toFixed(3)})`; ctx.fillRect(0, 0, W * k, H * k); }
      if (dlv && !room) {                                   // 遊美 ambientMultiply（整屏 multiply，強度 PARAMS.light.dlAmbient）取代舊 grade 疊層
        const sA = P.light.dlAmbient, a = dlv.ambient; ctx.globalCompositeOperation = 'multiply';
        ctx.fillStyle = 'rgb(' + (255 + (a[0] - 255) * sA | 0) + ',' + (255 + (a[1] - 255) * sA | 0) + ',' + (255 + (a[2] - 255) * sA | 0) + ')'; ctx.fillRect(0, 0, W * k, H * k); ctx.globalCompositeOperation = 'source-over';
      } else if (!dlv && lt && lt.gradeA > 0.001) { ctx.fillStyle = rgb(lt.grade, lt.gradeA); ctx.fillRect(0, 0, W * k, H * k); }   // 時段色調疊層（冇 daylight.json 時 fallback）
      // 光暈（預製光圖疊加，所有畫質都有）
      ctx.globalCompositeOperation = 'lighter';
      ctx.imageSmoothingEnabled = true;
      for (const l of lights) {
        const g = this.glowSprite(l.col); const r = l.r * k;
        ctx.globalAlpha = clamp(l.a, 0, 1);
        ctx.drawImage(g, l.x * k - r, l.y * k - r, r * 2, r * 2);
      }
      // 光柱（月光／燈柱）
      this.drawBeams(ctx, view, { sm, lcol, lanternA, night, offs });
      ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over';
      // L3（前景）
      if (room) { /* 房間皮膚冇前景草 */ } else if (dof) put(this.blurLayer(3, L[3], 2), 3, true); else put(L[3], 3, false);
      // 前景虛化光點（bokeh）
      if (post) this.drawBokeh(ctx, t, offs, lcol, lanternA, q);
      // Bloom
      if (q === 'high' || q === 'mid') this.bloom(ctx, q);
      // 傾斜移軸
      if (q === 'high') this.tiltShift(ctx);
      // 暈影
      if (post) this.vignette(ctx);
      if (this.flash > 0) { ctx.globalAlpha = Math.min(1, this.flash); ctx.fillStyle = '#fff6d0'; ctx.fillRect(0, 0, W * k, H * k); ctx.globalAlpha = 1; }
      const ms = performance.now() - t0; this.perf.n++; this.perf.sum += ms; this.perf.max = Math.max(this.perf.max, ms); this.perf.last = ms;
    }

    drawL2(x, view, c) {
      const s = view.state, t = c.t, offs = c.offs;
      x.clearRect(0, 0, LW, LH);
      const ox = (px) => px + MX, oy = (py) => py + MY;
      if (!c.hd) {                                          // HD-2D：舞台／燈柱／蘑菇光／螢火已畫喺場景層（透明底 L2）
      x.drawImage(this.layers[2], 0, 0);
      // 燈柱燈籠
      const lx = 24, ly = 306 - 58;
      const fl = 0.88 + 0.12 * Math.sin(t * 6.3);
      x.fillStyle = '#3a2418'; x.fillRect(ox(lx - 4), oy(ly - 1), 9, 2); x.fillRect(ox(lx - 4), oy(ly + 9), 9, 2);
      x.fillStyle = rgb(mixc(c.lcol, [90, 40, 20], 0.4 + (1 - c.lanternA) * 0.3)); x.fillRect(ox(lx - 3), oy(ly + 1), 7, 8);
      x.fillStyle = rgb(mixc(c.lcol, [255, 255, 235], 0.5 * c.lanternA * fl)); x.fillRect(ox(lx - 2), oy(ly + 2), 5, 6);
      const lp = { x: lx + 0.5 + offs[2][0], y: ly + 5 };
      c.lights.push({ x: lp.x, y: lp.y, r: 38, col: c.lcol, a: 0.85 * c.lanternA * fl });
      c.em.fillStyle = rgb(c.lcol, 0.9 * c.lanternA); c.em.fillRect(Math.round(lp.x) - 2, Math.round(lp.y) - 3, 5, 6);
      // 蘑菇光
      c.lights.push({ x: 168 + offs[2][0], y: 292, r: 20, col: [255, 160, 110], a: 0.4 * (1 - c.sm * 0.5) * (1 - c.hDim * 0.3) });
      c.em.fillStyle = 'rgba(255,170,120,0.7)'; c.em.fillRect(Math.round(168 + offs[2][0]) - 3, 292, 6, 2);
      // 螢火蟲
      for (const f of this.fireflies) {
        const fx = f.x + Math.sin(t * f.sp + f.ph) * 20, fy = f.y + Math.sin(t * f.sp * 1.3 + f.ph * 2) * 12;
        const a = 0.45 + 0.55 * Math.max(0, Math.sin(t * 2.1 + f.ph * 3));
        x.fillStyle = `rgba(255,240,150,${a.toFixed(2)})`; x.fillRect(ox(Math.round(fx)), oy(Math.round(fy)), 2, 2);
        c.lights.push({ x: fx + offs[2][0], y: fy, r: 9, col: [255, 235, 120], a: 0.55 * a * (1 - c.sm * 0.4) });
        c.em.fillStyle = `rgba(255,240,150,${(a * 0.9).toFixed(2)})`; c.em.fillRect(Math.round(fx + offs[2][0]), Math.round(fy), 2, 2);
      }
      }
      if (view.mode === 'minigame') return this.drawMinigame(x, view, c);

      // ── 寵物 ──
      const ph = c.sm;
      const beh = view.beh, useBeh = !!(beh && s.stage !== 'egg');
      const gx = CX + (useBeh ? beh.x : 0), base = GROUND_Y;
      this.petX = gx - CX;
      if (beh) this.drawGarden(x, view, c, beh);
      const lift = useBeh ? beh.lift : c.lift;
      // 影子
      x.fillStyle = 'rgba(10,20,20,0.35)';
      const shw = s.stage === 'adult' ? 24 : s.stage === 'sprout' ? 13 : 12, shl = 1 - Math.min(1, Math.abs(lift) / 18) * 0.35;
      for (let dy = -3; dy <= 3; dy++) { const w = Math.round(shw * shl * Math.sqrt(1 - dy * dy / 16)); x.fillRect(ox(gx - w), oy(base - 1 + dy), w * 2, 1); }
      let an, sx, sy;
      if (useBeh) this.petDraw = this.drawPetBeh(x, s, view, c, gx, base);
      else if (s.stage === 'egg' && this.atlasReady && this.atlas.atlas_egg && P.art.useAtlas !== false) {
        // 光卵：遊美 atlas_egg（egg_idle 4 幀／egg_glow 2 幀；進度 ≥50% 或輕點時用 glow）
        const prog = SIM.eggProgress(s), glow = prog >= 0.5 || this.eggPulse > 0.05, clip = glow ? 'egg_glow' : 'egg_idle', an2 = this.atlas.atlas_egg.json.animations[clip];
        let es = this.atlasSrc('atlas_egg', clip, Math.floor(t * an2.fps));
        if (c.hd) { es = this.hd.tintPet(es, { mir: 1, form: null, quality: c.q }); this.faceStat.tints++; }
        const ex = Math.round(gx - es.px), ey = Math.round(base - es.py + c.lift + (this.eggPulse > 0.05 ? -Math.round(this.eggPulse * 2) : 0));
        x.imageSmoothingEnabled = false; x.drawImage(es.img, es.sx, es.sy, es.sw, es.sh, ox(ex), oy(ey), es.sw, es.sh);
        this.petDraw = { x: ex, y: ey, w: es.sw, h: es.sh, bud: { x: ex + es.sw / 2, y: ey + es.sh * 0.4 }, footY: base + c.lift };
      }
      else {
        const sprite = petSprite({ stage: s.stage, form: s.form, anim: c.anim, frame: c.frame, face: c.face, prog: SIM.eggProgress(s) });
        an = sprite.anchor; sx = Math.round(gx - an.x); sy = Math.round(base - an.y + c.lift);
        x.drawImage(sprite, ox(sx), oy(sy));
        this.petDraw = { x: sx, y: sy, w: an.w, h: an.h, bud: { x: sx + an.bud.x, y: sy + an.bud.y }, footY: base + c.lift };
      }
      const pd = this.petDraw;
      // 寵物光（絨芽）——狀態光色
      let gcol = s.form === 'dust' ? [210, 205, 190] : s.form === 'lumi' ? [200, 255, 140] : [255, 214, 110];
      let gint = s.stage === 'egg' ? 0.5 + SIM.eggProgress(s) * 0.5 + this.eggPulse * 0.6 : 1;
      gint *= (1 - c.hDim * 0.6);
      if (c.unwell) { gcol = mixc(gcol, [150, 220, 150], 0.65); gint *= 0.6 + 0.2 * Math.sin(t * 3); }
      if (c.sm > 0.01) { gcol = mixc(gcol, [190, 210, 255], c.sm * 0.8); gint *= 1 - c.sm * 0.55; }
      if (c.wd) gint *= 0.6;
      const gr = s.stage === 'adult' ? (s.form === 'bright' ? 60 : (s.form === 'soft' || s.form === 'lumi') ? 44 : 28) : s.stage === 'sprout' ? 30 : 34 + this.eggPulse * 16;
      c.lights.push({ x: pd.bud.x + offs[2][0], y: pd.bud.y, r: gr, col: gcol, a: 0.8 * gint, bud: 1 });
      c.lights.push({ x: gx + offs[2][0], y: pd.footY - pd.h * 0.33, r: gr * 1.4, col: mixc(gcol, [255, 170, 90], 0.4), a: 0.18 * gint });
      c.em.fillStyle = rgb(gcol, 0.9 * Math.min(1, gint)); const bx = Math.round(pd.bud.x + offs[2][0]), by = Math.round(pd.bud.y);
      c.em.fillRect(bx - 2, by - 2, 5, 5);
      if (s.form === 'bright' && s.stage === 'adult') { c.em.fillRect(bx - 5, by, 11, 1); c.em.fillRect(bx, by - 5, 1, 11); }
      // 便便
      for (let i = 0; i < s.poops; i++) { const p = POOP_SLOTS[i]; x.drawImage(SPR.poop, ox(p[0] - 5), oy(p[1] - 8)); const w = Math.floor(t * 6 + i) % 3; x.fillStyle = '#a8d890'; x.fillRect(ox(p[0] - 3 + w), oy(p[1] - 12 - (w & 1)), 1, 3); x.fillRect(ox(p[0] + 3 - w), oy(p[1] - 11), 1, 3); }
      // 圖集未載入時退回舊 zZz／汗滴
      if (!this.atlasReady) {
        if (c.anim === 'sleep') { for (let i = 0; i < 3; i++) { const u = ((t * 0.5 + i / 3) % 1); const zx = gx + 14 + u * 16, zy = base - (s.stage === 'adult' ? 52 : 34) - u * 24; x.globalAlpha = Math.sin(u * Math.PI); x.drawImage(SPR.zz, ox(Math.round(zx)), oy(Math.round(zy)), 4 + i, 4 + i); } x.globalAlpha = 1; }
        if (c.unwell) { const u = (t * 1.2) % 1; x.drawImage(SPR.sweat, ox(gx + (s.stage === 'adult' ? 18 : 10)), oy(Math.round(base - pd.h * 0.55 + u * 8))); }
      }
      if (view.event) this.drawEventFx(x, view, c, gx);
      // 食物
      if (this.food && t < this.food.until) { const f = this.food; const u = 1 - (f.until - t) / f.dur; const spr = SPR[f.id]; const fx = gx + 22 - u * 12, fy = base - 10 - Math.sin(u * 3.14) * 6; if (u < 0.75) x.drawImage(spr, ox(Math.round(fx)), oy(Math.round(fy - spr.height))); }
      // 玩耍小球
      if (this.ball && t < this.ball.until) { const b = this.ball, u = 1 - (b.until - t) / b.dur; const bx2 = gx + Math.sin(u * 12) * 34, by2 = base - 10 - Math.abs(Math.sin(u * 9)) * 26; x.drawImage(SPR.ball, ox(Math.round(bx2) - 2), oy(Math.round(by2) - 2)); c.lights.push({ x: bx2 + offs[2][0], y: by2, r: 12, col: [255, 200, 120], a: 0.6 }); }
      // 沖洗水泡
      if (this.wash && t < this.wash.until) { const w = this.wash, u = 1 - (w.until - t) / w.dur; for (let i = 0; i < 9; i++) { const bx2 = gx - 26 + hash(i * 5.1) * 52, by2 = base - 8 - ((u * 1.3 + hash(i)) % 1) * 56; x.globalAlpha = 0.85; x.drawImage(SPR.drop, ox(Math.round(bx2)), oy(Math.round(by2))); } x.globalAlpha = 1; }
      // 粒子
      for (const f of this.fx) {
        f.life += 1 / 60; f.x += f.vx / 60; f.y += f.vy / 60; f.vy += 4 / 60;
        const a = 1 - f.life / f.max; if (a <= 0) continue;
        x.globalAlpha = Math.min(1, a * 1.5);
        const spr = f.type === 'heart' ? SPR.heart : f.type === 'spark' ? SPR.spark : f.type === 'drop' ? SPR.drop : null;
        if (spr) x.drawImage(spr, ox(Math.round(f.x - spr.width / 2)), oy(Math.round(f.y)));
        else if (f.type === 'steam') { x.fillStyle = 'rgba(245,245,255,0.8)'; const r = 1 + Math.floor(f.life * 2.5); x.fillRect(ox(Math.round(f.x)) - r, oy(Math.round(f.y)) - r, r * 2 + 1, r * 2); }
        else if (f.type === 'dust') { x.fillStyle = '#a08a68'; x.fillRect(ox(Math.round(f.x)), oy(Math.round(f.y)), 2, 2); }
        else if (f.type === 'text') pixText(x, f.text, ox(Math.round(f.x)), oy(Math.round(f.y)), f.col || '#ffe27a');
        x.globalAlpha = 1;
      }
      this.fx = this.fx.filter(f => f.life < f.max);
    }

    // 取 atlas 幀：返回 {img,sx,sy,sw,sh,px,py}
    atlasSrc(aName, clip, idx) {
      const A = this.atlas[aName]; if (!A) return null;
      const an = A.json.animations[clip]; if (!an) return null;
      const f = A.json.frames[an.frames[((idx % an.frames.length) + an.frames.length) % an.frames.length]]; if (!f) return null;
      const pv = f.pivotPx || { x: f.frame.w / 2, y: f.frame.h - 3 };   // atlas_egg 冇 pivot → 用遊美標準：底部置中（w/2, h-3）
      return { img: A.img, sx: f.frame.x, sy: f.frame.y, sw: f.frame.w, sh: f.frame.h, px: pv.x, py: pv.y, name: an.frames[((idx % an.frames.length) + an.frames.length) % an.frames.length] };
    }
    // 事件 icon（遊美 fx/events：32×32、pivot 置中、動畫 animations[icon]）
    eventIconSrc(id, t) {
      const A = this.atlas.atlas_events, df = D.EVENTS.find(e => e.id === id) || (id === 'grumpy_tap' ? D.EVENTS.find(e => e.id === 'grumpy') : null); if (!A || !df || !df.icon) return null;
      const an = A.json.animations[df.icon]; if (!an) return null;
      return this.atlasSrc('atlas_events', df.icon, Math.floor(t * an.fps));
    }
    drawEventIcon(cv, id, t) {          // 畫落 DOM canvas（事件提示卡）
      if (!cv) return false; const src = this.eventIconSrc(id, t); const g = cv.getContext('2d'); g.clearRect(0, 0, cv.width, cv.height); if (!src) return false;
      g.imageSmoothingEnabled = false; g.drawImage(src.img, src.sx, src.sy, src.sw, src.sh, 0, 0, cv.width, cv.height); return true;
    }
    propSrc(name, t) {
      const A = this.atlas.atlas_props; if (!A) return null;
      const an = A.json.animations[name]; if (!an) return null;
      return this.atlasSrc('atlas_props', name, Math.floor(t * an.fps));
    }
    // 畫寵物（atlas clip＋placeholder＋anchor 疊層）。返回 petDraw。
    drawPetBeh(x, s, view, c, gx, base) {
      const b = view.beh, t = c.t, clip = b.clip, cdef = D.CLIPS[clip], fk = formKeyOf(s), art = P.art, FCP = P.face;
      const ox = (px) => px + MX, oy = (py) => py + MY;
      const real = cdef.ready || art.usePending;
      const sc = b.show || { clip, frame: b.frame }, dclip = sc.clip, dframe = sc.frame;
      let src = null, ph = null, live = null;
      this.faceStat.draws++;
      // F1：生命感 noface 身體（有就用；顯示 clip 可以係 turn_back）
      const lvA = this.lv && FCP.mode !== 'native' && fk !== 'dust' && art.useAtlas !== false ? this.lv.atlas[fk] : null;
      if (lvA) {
        const an = lvA.json.animations, dd = D.CLIPS[dclip];
        if (dd && (dd.ready || dd.live || art.usePending) && an[dclip + '_noface']) live = { clip: dclip, frame: dframe };
        else if (an.idle_noface) { live = { clip: 'idle', frame: Math.floor(t * 6) }; ph = placeholderXform(clip, b, t); }
        if (live) { const nm = an[live.clip + '_noface'].frames; src = this.liveFrame(fk, nm[((live.frame % nm.length) + nm.length) % nm.length]); if (!src) { live = null; ph = null; } }
      }
      if (src) { /* live */ }
      else if (this.atlasReady && art.useAtlas !== false && fk !== 'dust') {
        const A = this.atlas[D.FORMS[fk].atlas];
        if (real && A.json.animations[clip]) src = this.atlasSrc(D.FORMS[fk].atlas, clip, b.frame);
        if (!src) { src = this.atlasSrc(D.FORMS[fk].atlas, 'idle', Math.floor(t * 6)); ph = placeholderXform(clip, b, t); }
      } else {
        const pa = procAnim(clip), ex = b.expr;
        const face = ex === 'tired' ? 'sleepy' : (ex === 'hungry' || ex === 'bored') ? 'sad' : 'normal';
        const sp = petSprite({ stage: s.stage, form: s.form, anim: pa, frame: Math.floor(t * (pa === 'idle' ? 3.2 : pa === 'sleep' ? 1 : 7)), face });
        src = { img: sp, sx: 0, sy: 0, sw: sp.width, sh: sp.height, px: sp.anchor.x, py: sp.anchor.y, bud: sp.anchor.bud };
        if (!cdef.ready) ph = placeholderXform(clip, b, t);
      }
      if (b.pose) { ph = Object.assign({ sx: 1, sy: 1, dx: 0, dy: 0 }, ph || {}); ph.dx += b.pose.dx; ph.sy *= b.pose.sy; ph.rot = b.pose.rot; }   // 生命感第二段：望天後仰（缺 lookup_tip 美術 → 程序化）
      const PX = 48, PY = 100;
      let draw = src, anc = null; const fst = { live: !!live, clip: live ? live.clip : dclip, frame: live ? live.frame : dframe, faceVisible: false, eyes: null, mouth: null, placeholder: [], bulb: null, derived: false };
      const comp = () => { const T = this.tmpPet, tx = T.getContext('2d'); tx.setTransform(1, 0, 0, 1, 0, 0); tx.globalCompositeOperation = 'source-over'; tx.globalAlpha = 1; tx.clearRect(0, 0, 96, 112); tx.imageSmoothingEnabled = false; tx.drawImage(src.img, src.sx, src.sy, src.sw, src.sh, PX - src.px, PY - src.py, src.sw, src.sh); draw = { img: T, sx: PX - src.px, sy: PY - src.py, sw: src.sw, sh: src.sh, px: src.px, py: src.py, bud: src.bud, name: src.name }; return tx; };
      if (live) {
        // 疊五官（喺 tint 之前，同身體一齊做一次 tint；朝左由外層 scaleX −1 成個合成）
        const tx = comp(); this.faceStat.overlays++;
        anc = this.liveAnchors(fk, live.clip, live.frame, src); fst.derived = !!anc.derived;
        const f = b.face || { eyes: 'neutral', mouth: 'neutral', gaze: 'C', closed: false };
        const vis = anc.faceVisible !== false && FCP.mode !== 'off'; fst.faceVisible = vis;
        const HT = { L: [-1, 0], CL: [-1, 0], CR: [1, 0], R: [1, 0], U: [0, -1], D: [0, 1] }[f.head] || null;   // P2：開心閉眼 → 五官整組微移 1px＝頭部微轉
        const o0x = PX - src.px + (HT ? HT[0] : 0), o0y = PY - src.py + (HT ? HT[1] : 0);
        if (HT) { this.faceStat.headTurn = (this.faceStat.headTurn || 0) + 1; fst.headTurn = f.head; }
        const put = (name, at, kind) => {
          const pc = this.liveFrame(fk, name);
          if (pc) { tx.drawImage(pc.img, pc.sx, pc.sy, pc.sw, pc.sh, o0x + at[0] - pc.px, o0y + at[1] - pc.py, pc.sw, pc.sh); return true; }
          fst.placeholder.push(name); tx.fillStyle = FCP.ink;               // 缺件：色塊 placeholder
          const sm = fk === 'sprout' ? 1 : 2;
          if (kind === 'eye') tx.fillRect(o0x + at[0] - (sm >> 1), o0y + at[1] - sm, sm, sm + 1); else { tx.fillRect(o0x + at[0] - sm, o0y + at[1], sm * 2, 1); }
          return false;
        };
        if (vis) {
          const moving = FCP.closedEyes.indexOf(f.eyes) < 0, g = moving ? (f.gaze || 'C') : 'C';
          let nl = 'eyes_' + f.eyes + '_' + g + '_l', nr = 'eyes_' + f.eyes + '_' + g + '_r';
          if (f.eyes === 'wink') { const gg = f.gaze || 'C'; nl = 'eyes_neutral_' + gg + '_l'; nr = 'eyes_wink_C_r'; }
          put(nl, anc.eyeL, 'eye'); put(nr, anc.eyeR, 'eye'); put('mouth_' + (f.mouth || 'neutral'), anc.mouth, 'mouth');
          fst.eyes = [nl, nr]; fst.mouth = 'mouth_' + (f.mouth || 'neutral'); this.faceStat.faceDrawn++;
        } else this.faceStat.faceHidden++;
        if (fst.placeholder.length) this.faceStat.placeholder++;
        // 燈泡底（喺 tint 之前：跟時段光）；glow 喺 tint 之後（自發光）
        if (FCP.bulb && FCP.bulb.enabled && anc.bulb && live.clip !== 'sick') { const bb = this.liveFrame(fk, 'bulb_base'); if (bb) tx.drawImage(bb.img, bb.sx, bb.sy, bb.sw, bb.sh, o0x + anc.bulb[0] - bb.px, o0y + anc.bulb[1] - bb.py, bb.sw, bb.sh); }
      }
      // 污漬 overlay（dirty 表情：暫無美術，程序化佔位）
      if (D.EXPRESSIONS[b.expr].dirt) {
        const tx = live ? this.tmpPet.getContext('2d') : comp();
        tx.globalCompositeOperation = 'source-atop';
        const fs = src.sw;
        for (let k = 0; k < 7; k++) { const dx = Math.round((hash(k * 3.1) - 0.5) * fs * 0.6), dy = -Math.round(fs * (0.12 + hash(k * 5.3) * 0.38)); tx.fillStyle = k % 3 ? '#5a4632' : '#3e3024'; tx.fillRect(PX + dx, PY + dy, 2, 2); tx.fillStyle = '#7a6444'; tx.fillRect(PX + dx, PY + dy, 1, 1); }
        tx.globalCompositeOperation = 'source-over';
      }
      const mir = b.dir < 0 ? -1 : 1, prm = art.playRootMotion;
      // 時段 tint：五官已喺上面合成入 tmpPet → 呢度成個合成只 tint 一次（HD-2D 取代 daylight tint，唔加多一次）
      if (c.hd) { this.faceStat.tints++; draw = this.hd.tintPet(draw, { mir, form: fk, rimKey: live ? fk + '_live' : fk, frame: draw.name, quality: c.q, lumi: s.form === 'lumi' }); }   // petTint×ambientTint＋rim（唔過 LUT）
      else if (this.curDL && art.daylight !== false) draw = this.tintSprite(draw, this.curDL, mir, s.form === 'lumi');
      const rm = (prm && clip === 'play' && real && !ph && prm.frames.indexOf(b.frame) >= 0) ? (fk === 'sprout' ? prm.dx32 : prm.dx64) * mir : 0;   // play 前衝 root-motion（只喺真 clip 幀）
      const px = Math.round(gx + rm), py = Math.round(base + b.lift + (ph ? ph.dy : 0));
      { const sx = ph ? ph.sx : 1, sy = ph ? ph.sy : 1, w = draw.sw * Math.abs(sx), h = draw.sh * sy, l = px + (ph ? ph.dx * mir : 0) - (mir > 0 ? draw.px : draw.sw - draw.px) * Math.abs(sx); const ob = this.opaqueBox(src); if (ob) { const ax = Math.abs(sx); const l0 = mir > 0 ? ob.l : draw.sw - ob.r; this.petRect = { x: l + l0 * ax, y: py - draw.py * sy + ob.t * sy, w: (ob.r - ob.l) * ax, h: (ob.b - ob.t) * sy, opaque: true }; } else this.petRect = { x: l, y: py - draw.py * sy, w, h, opaque: false }; }   // P2：觸控用真身框（art 座標，未加視差）
      x.save(); x.imageSmoothingEnabled = false;
      x.translate(ox(px + (ph ? ph.dx * mir : 0)), oy(py)); x.scale(mir * (ph ? ph.sx : 1), ph ? ph.sy : 1); if (ph && ph.rot) x.rotate(-ph.rot);   // 以腳底 pivot 向後仰
      x.drawImage(draw.img, draw.sx, draw.sy, draw.sw, draw.sh, -draw.px, -draw.py, draw.sw, draw.sh);
      if (live && anc && anc.bulb && FCP.bulb && FCP.bulb.enabled && live.clip !== 'sick') {     // 燈泡 glow：情緒 tint（0.4s 漸變）× intensity（呼吸／閃）
        const BM = FCP.bulb.moods, mood = this.bulbMood(b), m = BM[mood] || BM.neutral, hx = (h) => [parseInt(h.slice(1, 3), 16), parseInt(h.slice(3, 5), 16), parseInt(h.slice(5, 7), 16)];
        const tgt = hx(m.tint), dt = Math.max(0, Math.min(0.1, this.bulbLastT == null ? 0 : t - this.bulbLastT)), kf = 1 - Math.exp(-dt * 3 / Math.max(0.05, FCP.bulb.fadeSec));
        this.bulbLastT = t; if (!this.bulbS) this.bulbS = { rgb: tgt.slice(), i: m.i };
        const S = this.bulbS; for (let i = 0; i < 3; i++) S.rgb[i] += (tgt[i] - S.rgb[i]) * kf;
        const pu = m.pulse, it = pu ? pu[1] + (pu[2] - pu[1]) * (0.5 + 0.5 * Math.sin(t * 6.283 / pu[0])) : m.i; S.i += (it - S.i) * kf;
        const gl = this.bulbGlow(fk, s.form === 'lumi' ? [S.rgb[0] * 0.75, 255, S.rgb[2] * 0.55] : S.rgb);   // 螢絨：燈泡偏螢綠
        if (gl) { x.globalAlpha = Math.max(0, Math.min(1, S.i)); x.drawImage(gl.c, -src.px + anc.bulb[0] - gl.px, -src.py + anc.bulb[1] - gl.py); x.globalAlpha = 1; this.faceStat.bulb++; fst.bulb = { mood, i: +S.i.toFixed(2), rgb: S.rgb.map(v => Math.round(v)) }; }
      }
      x.restore();
      if (b.bug) {                                    // A2 swat 蟲仔 fx：遊美 fx/atlas_fx_live（fx_bug 01→02→03→02，10fps，pivot (4,4)，朝右）；冇就程序化 2×2 點＋1px 翼閃
        const bx = Math.round(px + b.bug.x), by = Math.round(py + b.bug.y), FX = this.lv && this.lv.fx, an = FX && FX.json.animations && FX.json.animations.fx_bug;
        const fr = an && FX.json.frames[an.frames[Math.floor((b.bug.t || 0) * (an.fps || 10)) % an.frames.length]];
        if (fr) {
          const face = b.bug.st === 'flee' ? (b.bug.vx < 0 ? -1 : 1) : (b.bug.x > 0 ? -1 : 1), pv = fr.pivotPx || { x: 4, y: 4 };   // 飛走跟方向；buzz 時望住團絨
          x.save(); x.translate(ox(bx), oy(by)); x.scale(face, 1); x.drawImage(FX.img, fr.frame.x, fr.frame.y, fr.frame.w, fr.frame.h, -pv.x, -pv.y, fr.frame.w, fr.frame.h); x.restore();
          fst.bugArt = true;
        } else {
          const wf = Math.floor(t * 18) & 1;
          x.fillStyle = '#2a2230'; x.fillRect(ox(bx), oy(by), 2, 2);
          x.fillStyle = 'rgba(232,240,255,0.85)'; x.fillRect(ox(bx + (wf ? -1 : 2)), oy(by - 1), 1, 1);
          fst.bugArt = false;
        }
        fst.bug = b.bug.st;
      }
      this.faceStat.last = fst;
      const top = py - Math.round(src.py * (ph ? ph.sy : 1));
      const bud = (live && anc && anc.bulb) ? { x: px + (anc.bulb[0] - src.px) * mir, y: py - src.py + anc.bulb[1] } : src.bud ? { x: px + (src.bud.x - src.px) * mir, y: py - src.py + src.bud.y } : { x: px, y: top + Math.round(src.sw * 0.17) };
      // anchor 疊層（zzz／heart／sweat／exclaim／question：獨立圖層，按 head_r 錨點，mirror 錨點 x 唔 mirror 圖示）
      if (this.atlasReady) {
        const ho = (live && anc && anc.head_r) ? [anc.head_r[0] - src.px, anc.head_r[1] - src.py] : D.FORMS[fk] ? D.FORMS[fk].headR : DUST_HEAD;   // 生命感：用逐幀 head_r 錨點
        for (const a of b.attach) {
          if (a.anchor !== 'head_r') continue;
          const ps = this.propSrc(a.prop, t); if (!ps) continue;
          x.drawImage(ps.img, ps.sx, ps.sy, ps.sw, ps.sh, ox(px + mir * ho[0] - ps.px), oy(py + ho[1] - ps.py), ps.sw, ps.sh);
        }
      }
      return { x: px - src.px, y: py - src.py, w: src.sw, h: src.sh, bud, footY: py };
    }
    // 花園道具：日光斑、花盆（可搖）、被碰落嘅小物、小球
    drawGarden(x, view, c, beh) {
      const t = c.t, ox = (px) => px + MX, oy = (py) => py + MY, art = P.art;
      // 日光斑
      if (this.sunMix > 0.02) {
        const cx0 = CX + P.beh.sunSpotX, a = this.sunMix * Math.max(0.35, view.light ? view.light.sun : 1);
        const sp = art.usePending ? this.propSrc('sun_patch', t) : null;
        if (sp) { x.globalAlpha = a; x.drawImage(sp.img, sp.sx, sp.sy, sp.sw, sp.sh, ox(cx0 - sp.px), oy(GROUND_Y - sp.py + 2), sp.sw, sp.sh); x.globalAlpha = 1; }
        else for (let j = -4; j <= 4; j++) { const w = Math.round(24 * Math.sqrt(1 - j * j / 25)); x.fillStyle = `rgba(255,224,150,${(0.30 * a * (1 - Math.abs(j) / 7)).toFixed(3)})`; x.fillRect(ox(cx0 - w), oy(GROUND_Y + j + 1), w * 2, 1); }
        c.lights.push({ x: cx0 + c.offs[2][0], y: GROUND_Y - 4, r: 38, col: [255, 214, 140], a: 0.32 * a });
      }
      // 花盆
      const pxx = Math.round(CX + P.beh.potX), pyy = GROUND_Y + 1;
      const usePot = art.usePending && this.atlasReady && this.atlas.atlas_props && this.atlas.atlas_props.json.animations.flowerpot_idle;
      if (usePot) {
        const bumping = beh.state === 'bump' && beh.phase === 'hit' && beh.clipT >= P.beh.bumpImpactFrame / D.CLIPS.pot_bump.fps;
        const idx = bumping ? Math.floor((beh.clipT - P.beh.bumpImpactFrame / D.CLIPS.pot_bump.fps) * 8) : 0;
        const ps = this.atlasSrc('atlas_props', bumping && idx < 4 ? 'flowerpot_bump' : 'flowerpot_idle', Math.min(3, idx));
        if (ps) x.drawImage(ps.img, ps.sx, ps.sy, ps.sw, ps.sh, ox(pxx - ps.px), oy(pyy - ps.py), ps.sw, ps.sh);
      } else {
        const wob = beh.potWobble, sw = Math.sin(t * 22) * wob;
        const row = (j, w, col) => { const off = Math.round(sw * (j / 14) * 3); x.fillStyle = col; x.fillRect(ox(pxx - (w >> 1) + off), oy(pyy - j - 1), w, 1); };
        for (let j = 0; j < 9; j++) { const w = 8 + (j >> 2); row(j, w, '#b8603a'); x.fillStyle = '#d8804a'; x.fillRect(ox(pxx - (w >> 1) + Math.round(sw * (j / 14) * 3)), oy(pyy - j - 1), 2, 1); x.fillStyle = '#8a4428'; x.fillRect(ox(pxx + (w >> 1) - 2 + Math.round(sw * (j / 14) * 3)), oy(pyy - j - 1), 2, 1); }
        for (let j = 9; j < 12; j++) row(j, 12, j === 11 ? '#f0a060' : '#d8804a');
        row(12, 10, '#3a2418');
        for (let j = 13; j < 18; j++) { const off = Math.round(sw * (j / 14) * 3); x.fillStyle = '#4aa060'; x.fillRect(ox(pxx + off), oy(pyy - j - 1), 1, 1); }
        const off2 = Math.round(sw * 1.3 * 3); x.fillStyle = '#6ac078'; x.fillRect(ox(pxx - 3 + off2), oy(pyy - 16), 3, 1); x.fillRect(ox(pxx + 1 + off2), oy(pyy - 18), 3, 1);
        x.fillStyle = '#ffd36a'; x.fillRect(ox(pxx - 1 + off2), oy(pyy - 21), 3, 3); x.fillStyle = '#fff4b0'; x.fillRect(ox(pxx + off2), oy(pyy - 20), 1, 1);
      }
      c.lights.push({ x: pxx + c.offs[2][0], y: pyy - 20, r: 14, col: [255, 214, 110], a: 0.28 });
      // 被碰落嘅花瓣／小花／石仔
      for (const p of beh.props) {
        const a = Math.min(1, (p.life - p.age) / 3); if (a <= 0) continue;
        const qx = Math.round(CX + p.x), qy = Math.round(GROUND_Y + p.y);
        x.globalAlpha = a;
        if (p.kind === 'petal') { x.fillStyle = '#f8a8c0'; x.fillRect(ox(qx), oy(qy), 3, 2); x.fillStyle = '#ffd0dc'; x.fillRect(ox(qx), oy(qy), 1, 1); }
        else if (p.kind === 'flower') { x.fillStyle = '#ffe27a'; x.fillRect(ox(qx), oy(qy - 2), 1, 5); x.fillRect(ox(qx - 2), oy(qy), 5, 1); x.fillStyle = '#fff'; x.fillRect(ox(qx), oy(qy), 1, 1); }
        else { x.fillStyle = '#8a8a94'; x.fillRect(ox(qx), oy(qy), 3, 2); x.fillStyle = '#b4b4be'; x.fillRect(ox(qx), oy(qy), 2, 1); }
        x.globalAlpha = 1;
      }
      // 玩耍小球（behavior play 狀態）
      if (beh.item && beh.item.kind === 'ball') { const bx2 = Math.round(CX + beh.x + beh.item.x), by2 = Math.round(GROUND_Y - 10 + beh.item.y); x.drawImage(SPR.ball, ox(bx2 - 2), oy(by2 - 2)); c.lights.push({ x: bx2 + c.offs[2][0], y: by2, r: 12, col: [255, 200, 120], a: 0.6 }); }
    }
    // 事件視覺（EV.visual 嘅純函數結果）
    drawEventFx(x, view, c, gx) {
      const ev = view.event, v = ev.vis || {}, t = c.t, ox = (px) => px + MX, oy = (py) => py + MY, offs = c.offs;
      // 遊美事件 icon：事件頭 cardSec 秒喺寵物頭頂（整數像素、Nearest）；淡入淡出
      { const is = this.eventIconSrc(ev.id, ev.t || 0), cs = P.events.cardSec; if (is && (ev.t || 0) < cs) { const fa = Math.min(1, (ev.t || 0) / 0.3, (cs - (ev.t || 0)) / 0.4); const hy = (this.petDraw ? this.petDraw.y : GROUND_Y - 70) - 26 + Math.round(Math.sin(t * 3) * 1.5); x.globalAlpha = Math.max(0, fa); x.drawImage(is.img, is.sx, is.sy, is.sw, is.sh, ox(Math.round(gx + 22 - is.px)), oy(Math.round(hy - is.py)), is.sw, is.sh); x.globalAlpha = 1; } }
      if (ev.id === 'butterfly') {
        const bx = Math.round(v.bx), by = Math.round(v.by), f = v.flap;
        x.fillStyle = '#5a3a6a'; x.fillRect(ox(bx), oy(by - 1), 1, 3);
        x.fillStyle = '#8ad8ff'; x.fillRect(ox(bx - 2), oy(by - (f ? 2 : 1)), 2, f ? 3 : 2); x.fillRect(ox(bx + 1), oy(by - (f ? 2 : 1)), 2, f ? 3 : 2);
        x.fillStyle = '#e8f8ff'; x.fillRect(ox(bx - 2), oy(by - (f ? 2 : 1)), 1, 1); x.fillRect(ox(bx + 2), oy(by - (f ? 2 : 1)), 1, 1);
        c.lights.push({ x: bx + offs[2][0], y: by, r: 16, col: [160, 220, 255], a: 0.6 });
        c.em.fillStyle = 'rgba(190,235,255,0.9)'; c.em.fillRect(Math.round(bx + offs[2][0]) - 1, by - 1, 3, 3);
      } else if (ev.id === 'meteor') {
        for (const m of (v.streaks || [])) {
          const hx = m.x0 + (m.x1 - m.x0) * m.u, hy = m.y0 + (m.y1 - m.y0) * m.u, dx = m.x1 - m.x0, dy = m.y1 - m.y0, L = Math.hypot(dx, dy), al = Math.sin(m.u * Math.PI);
          for (let k = 0; k < 12; k++) { x.globalAlpha = al * (1 - k / 12); x.fillStyle = k < 2 ? '#ffffff' : '#ffe9a8'; x.fillRect(ox(Math.round(hx - dx / L * k * 2.4)), oy(Math.round(hy - dy / L * k * 2.4)), 2, 2); }
          x.globalAlpha = 1;
          c.lights.push({ x: hx + offs[0][0], y: hy, r: 22, col: [255, 236, 170], a: 0.7 * al });
          c.em.fillStyle = `rgba(255,245,200,${(0.9 * al).toFixed(2)})`; c.em.fillRect(Math.round(hx), Math.round(hy), 3, 3);
        }
      } else if (ev.id === 'rainbow') {
        if (v.rain > 0.02) { x.fillStyle = `rgba(170,200,255,${(0.5 * v.rain).toFixed(2)})`; for (let i = 0; i < 46; i++) { const rx = Math.round(hash(i * 1.7) * W), ry = Math.round((t * 150 + hash(i + 5) * 340) % 300); x.fillRect(ox(rx), oy(ry), 1, 4); } }
        if (v.arc > 0.02) {
          const cols = ['#ff7a7a', '#ffb06a', '#ffe27a', '#8adf8a', '#7ac8ff', '#8a8aff', '#c08aff'];
          x.save(); x.globalAlpha = 0.5 * v.arc; x.lineWidth = 3;
          cols.forEach((col, i) => { x.strokeStyle = col; x.beginPath(); x.arc(ox(CX), oy(262), 108 - i * 3, Math.PI * 1.04, Math.PI * 1.96); x.stroke(); });
          x.restore();
          c.lights.push({ x: CX + offs[1][0], y: 170, r: 80, col: [255, 230, 200], a: 0.18 * v.arc });
        }
      } else if (ev.id === 'gift') {
        if (v.show > 0.02) {
          const bx = Math.round(CX + v.x), h = Math.max(1, Math.round(7 * v.show)), by = Math.round(GROUND_Y - h - v.bounce * 8);
          x.fillStyle = '#e8607a'; x.fillRect(ox(bx - 4), oy(by), 9, h); x.fillStyle = '#ffd36a'; x.fillRect(ox(bx), oy(by), 1, h); x.fillRect(ox(bx - 4), oy(by + (h >> 1)), 9, 1);
          x.fillStyle = '#ffd36a'; x.fillRect(ox(bx - 2), oy(by - 2), 2, 2); x.fillRect(ox(bx + 1), oy(by - 2), 2, 2);
          c.lights.push({ x: bx + offs[2][0], y: by, r: 18, col: [255, 214, 120], a: 0.5 * v.show });
        }
      } else if (ev.id === 'treasure') {
        const mx = Math.round(CX + v.digX + 11), h = Math.round(1 + 5 * v.mound);
        for (let j = 0; j < h; j++) { const w = Math.round((h - j) * 1.8) + 1; x.fillStyle = j === 0 ? '#5a4030' : '#3e2c20'; x.fillRect(ox(mx - w), oy(GROUND_Y - j), w * 2, 1); }
        if (v.found) {
          const gy = Math.round(GROUND_Y - 8 - v.pop * 14 + Math.sin(t * 6) * 1);
          x.fillStyle = '#7ae0ff'; x.fillRect(ox(mx - 1), oy(gy - 3), 3, 7); x.fillRect(ox(mx - 3), oy(gy - 1), 7, 3); x.fillStyle = '#e8fbff'; x.fillRect(ox(mx - 1), oy(gy - 1), 2, 2);
          c.lights.push({ x: mx + offs[2][0], y: gy, r: 24, col: [140, 225, 255], a: 0.7 * v.pop });
          c.em.fillStyle = 'rgba(190,240,255,0.9)'; c.em.fillRect(Math.round(mx + offs[2][0]) - 1, gy - 1, 3, 3);
        }
      } else if (ev.id === 'firefly_walk') {     // placeholder：5 點暖黃綠螢火＋光暈（icon／專屬美術待遊美）
        const fade = 1 - (v.away || 0);
        for (const f of (v.flies || [])) {
          const fx2 = Math.round(f.x), fy2 = Math.round(f.y), a = (0.45 + 0.55 * f.tw) * fade;
          x.fillStyle = `rgba(214,255,120,${a.toFixed(2)})`; x.fillRect(ox(fx2), oy(fy2), 2, 2);
          x.fillStyle = `rgba(255,255,200,${a.toFixed(2)})`; x.fillRect(ox(fx2), oy(fy2), 1, 1);
          c.lights.push({ x: fx2 + offs[2][0], y: fy2, r: 14 + 6 * f.tw, col: [200, 255, 120], a: 0.55 * a });
          c.em.fillStyle = `rgba(230,255,170,${(0.9 * a).toFixed(2)})`; c.em.fillRect(Math.round(fx2 + offs[2][0]) - 1, fy2 - 1, 3, 3);
        }
      } else if (ev.id === 'flash') {
        for (let i = 0; i < 26; i++) {
          const fx = hash(i * 2.3) * W, fy = (t * (24 + hash(i) * 20) + hash(i + 9) * 330) % 330 - 10, tw = 0.5 + 0.5 * Math.sin(t * 6 + i);
          x.fillStyle = `rgba(255,236,150,${(0.5 + 0.5 * tw).toFixed(2)})`; x.fillRect(ox(Math.round(fx)), oy(Math.round(fy)), 2, 2);
          if (tw > 0.8) { x.fillRect(ox(Math.round(fx) - 1), oy(Math.round(fy)), 4, 1); x.fillRect(ox(Math.round(fx)), oy(Math.round(fy) - 1), 1, 4); }
        }
        c.lights.push({ x: gx + offs[2][0], y: GROUND_Y - 30, r: 90, col: [255, 226, 130], a: 0.3 + 0.1 * Math.sin(t * 4) });
      }
    }

    drawMinigame(x, view, c) {
      const mg = view.mg, s = view.state, t = c.t, offs = c.offs;
      const ox = (px) => px + MX, oy = (py) => py + MY;
      const bw = P.mg.basketW, by = P.mg.basketY;
      // 籃子 + 寵物探頭
      const form = s.form, stage = s.stage === 'egg' ? 'sprout' : s.stage;
      const anim = mg.stun > 0 ? 'unwell' : 'happy';
      const sprite = petSprite({ stage, form, anim: mg.stun > 0 ? 'idle' : 'idle', frame: Math.floor(t * 3) % 3, face: mg.stun > 0 ? 'sad' : 'normal' });
      const an = sprite.anchor, bx = Math.round(mg.basketX);
      x.save(); x.beginPath(); x.rect(0, 0, LW, oy(by + 2)); x.clip();
      x.drawImage(sprite, ox(Math.round(bx - an.x)), oy(Math.round(by + 12 - an.y)));
      x.restore();
      x.drawImage(SPR.basket, ox(bx - 15), oy(by));
      c.lights.push({ x: bx + offs[2][0], y: by - 10, r: 34, col: [255, 214, 110], a: 0.5 });
      for (const it of mg.items) {
        const spr = it.type === 'star' ? SPR.star : it.type === 'big' ? SPR.bigstar : SPR.stone;
        const ix = Math.round(it.x - spr.width / 2), iy = Math.round(it.y - spr.height / 2);
        x.drawImage(spr, ox(ix), oy(iy));
        if (it.type !== 'stone') {
          c.lights.push({ x: it.x + offs[2][0], y: it.y, r: it.type === 'big' ? 18 : 11, col: [255, 214, 100], a: 0.7 });
          c.em.fillStyle = 'rgba(255,225,120,0.9)'; c.em.fillRect(Math.round(it.x + offs[2][0]) - 1, Math.round(it.y) - 1, 3, 3);
          if ((Math.floor(t * 8 + it.rot * 3)) % 3 === 0) { x.fillStyle = '#fff'; x.fillRect(ox(ix + 2), oy(iy - 1), 1, 1); }
        } else c.lights.push({ x: it.x + offs[2][0], y: it.y, r: 10, col: [120, 60, 160], a: 0.25 });
      }
      for (const f of mg.fx) {
        if (f.type === 'stone') { this.burst('spark', f.x, f.y, 3, 30); this.spawn('text', f.x - 5, f.y - 14, { text: '-' + P.mg.stonePenalty, col: '#c898ff', vy: -20, max: 0.9 }); }
        else { this.spawn('spark', f.x, f.y - 6, { max: 0.6, vy: -22 }); this.spawn('text', f.x - 4, f.y - 12, { text: '+' + (f.type === 'big' ? P.mg.bigStarScore : P.mg.starScore), vy: -22, max: 0.7 }); }
      }
      mg.fx.length = 0;
      for (const f of this.fx) {
        f.life += 1 / 60; f.x += f.vx / 60; f.y += f.vy / 60; f.vy += 4 / 60;
        const a = 1 - f.life / f.max; if (a <= 0) continue; x.globalAlpha = Math.min(1, a * 1.5);
        if (f.type === 'spark') x.drawImage(SPR.spark, ox(Math.round(f.x - 2)), oy(Math.round(f.y)));
        else if (f.type === 'text') pixText(x, f.text, ox(Math.round(f.x)), oy(Math.round(f.y)), f.col || '#ffe27a');
        x.globalAlpha = 1;
      }
      this.fx = this.fx.filter(f => f.life < f.max);
      this.petDraw = { x: bx, y: by, w: 0, h: 0, bud: { x: bx, y: by - 20 } };
    }

    drawBeams(ctx, view, c) {
      const k = this.k;
      // 月光柱（睡眠時）
      if (c.sm > 0.02) {
        const x0 = (150 + c.offs[0][0]) * k, y0 = (80 + c.offs[0][1]) * k, x1 = CX * k - 30 * k, x2 = CX * k + 36 * k, y1 = (GROUND_Y - 6) * k;
        const gr = ctx.createLinearGradient(0, y0, 0, y1); gr.addColorStop(0, 'rgba(190,210,255,0.0)'); gr.addColorStop(0.25, `rgba(190,210,255,${(0.18 * c.sm).toFixed(3)})`); gr.addColorStop(1, `rgba(190,210,255,${(0.05 * c.sm).toFixed(3)})`);
        ctx.fillStyle = gr; ctx.globalAlpha = 1; ctx.beginPath(); ctx.moveTo(x0 - 6 * k, y0); ctx.lineTo(x0 + 8 * k, y0); ctx.lineTo(x2, y1); ctx.lineTo(x1, y1); ctx.closePath(); ctx.fill();
        // 光塵
        ctx.fillStyle = 'rgba(220,235,255,0.7)';
        for (let i = 0; i < 14; i++) { const u = (this.t * 0.04 + hash(i * 3.3)) % 1, bxp = lerp(x0, CX * k, u) + (hash(i) - 0.5) * 24 * k * u, byp = lerp(y0, y1, u); ctx.globalAlpha = c.sm * 0.6 * Math.sin(u * Math.PI); ctx.fillRect(Math.round(bxp / k) * k, Math.round(byp / k) * k, k, k); }
      }
      // 燈柱光錐
      const a = 0.16 * c.lanternA * (1 - c.sm * 0.3);
      if (a > 0.01) {
        const lx = (24 + c.offs[2][0]) * k, ly = 254 * k, gr = ctx.createLinearGradient(0, ly, 0, 310 * k);
        gr.addColorStop(0, rgb(c.lcol, a)); gr.addColorStop(1, rgb(c.lcol, 0));
        ctx.globalAlpha = 1; ctx.fillStyle = gr; ctx.beginPath(); ctx.moveTo(lx - 3 * k, ly); ctx.lineTo(lx + 3 * k, ly); ctx.lineTo(lx + 34 * k, 312 * k); ctx.lineTo(lx - 34 * k, 312 * k); ctx.closePath(); ctx.fill();
      }
    }
    drawBokeh(ctx, t, offs, lcol, lanternA, q) {
      const k = this.k; ctx.globalCompositeOperation = 'lighter'; ctx.imageSmoothingEnabled = true;
      for (let i = 0; i < 7; i++) {
        const x = (hash(i * 7) * W + Math.sin(t * 0.3 + i) * 10 + offs[3][0] * 1.2), y = 280 + hash(i * 3 + 1) * 120 + Math.sin(t * 0.4 + i * 2) * 8;
        const a = (0.1 + 0.12 * Math.max(0, Math.sin(t * 0.8 + i))) * (1 - this.sleepMix * 0.5); const r = (7 + hash(i) * 8) * k;
        ctx.globalAlpha = a; ctx.drawImage(this.glowSprite(i % 2 ? [255, 230, 140] : mixc(lcol, [255, 255, 255], 0.2)), x * k - r, y * k - r, r * 2, r * 2);
      }
      ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over';
    }
    bloom(ctx, q) {
      const k = this.k, w = this.work;
      const c0 = w[0].getContext('2d'); c0.clearRect(0, 0, W, H); c0.drawImage(this.em, 0, 0);
      for (let i = 1; i < (q === 'high' ? 4 : 3); i++) { const c = w[i].getContext('2d'); c.imageSmoothingEnabled = true; c.globalCompositeOperation = 'copy'; c.drawImage(w[i - 1], 0, 0, w[i].width, w[i].height); }
      const top = q === 'high' ? 3 : 2;
      for (let i = top; i >= 1; i--) { const c = w[i - 1].getContext('2d'); c.imageSmoothingEnabled = true; c.globalCompositeOperation = 'lighter'; c.globalAlpha = 0.8; c.drawImage(w[i], 0, 0, w[i - 1].width, w[i - 1].height); c.globalAlpha = 1; c.globalCompositeOperation = 'source-over'; }
      ctx.globalCompositeOperation = 'lighter'; ctx.imageSmoothingEnabled = true; ctx.globalAlpha = (q === 'high' ? 0.85 : 0.65) * (this.curDL ? Math.min(1.6, this.curDL.bloom / P.light.dlBloomRef) : 1);
      ctx.drawImage(w[0], 0, 0, W * k, H * k); ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over';
    }
    tiltShift(ctx) {
      const k = this.k, A = this.tsA, B = this.tsB, w = A.width, h = A.height;
      const a = A.getContext('2d'); a.imageSmoothingEnabled = true; a.clearRect(0, 0, w, h); a.drawImage(this.canvas, 0, 0, w, h);
      const b2 = B.getContext('2d'); b2.imageSmoothingEnabled = true; b2.globalCompositeOperation = 'copy'; b2.drawImage(A, 0, 0, w / 2 | 0, h / 2 | 0); a.globalCompositeOperation = 'copy'; a.drawImage(B, 0, 0, w / 2 | 0, h / 2 | 0, 0, 0, w, h); a.globalCompositeOperation = 'source-over';
      if (!this.tsMask || this.tsMask.width !== w) { const m = mk(w, h), x = m.getContext('2d'); const g = x.createLinearGradient(0, 0, 0, h); g.addColorStop(0, 'rgba(0,0,0,1)'); g.addColorStop(0.16, 'rgba(0,0,0,0)'); g.addColorStop(0.84, 'rgba(0,0,0,0)'); g.addColorStop(1, 'rgba(0,0,0,1)'); x.fillStyle = g; x.fillRect(0, 0, w, h); this.tsMask = m; }
      a.globalCompositeOperation = 'destination-in'; a.drawImage(this.tsMask, 0, 0); a.globalCompositeOperation = 'source-over';
      ctx.imageSmoothingEnabled = true; ctx.drawImage(A, 0, 0, W * k, H * k);
    }
    vignette(ctx) {
      const k = this.k;
      if (!this.vig) { const v = mk(W * k, H * k), x = v.getContext('2d'); const g = x.createRadialGradient(W * k / 2, H * k * 0.52, Math.min(W, H) * k * 0.28, W * k / 2, H * k * 0.52, H * k * 0.66); g.addColorStop(0, 'rgba(4,6,22,0)'); g.addColorStop(0.7, 'rgba(4,6,22,0.28)'); g.addColorStop(1, 'rgba(4,6,22,0.72)'); x.fillStyle = g; x.fillRect(0, 0, W * k, H * k); this.vig = v; }
      ctx.imageSmoothingEnabled = false; if (this.curDL) ctx.globalAlpha = Math.min(1.4, this.curDL.vignette / P.light.dlVigRef); ctx.drawImage(this.vig, 0, 0); ctx.globalAlpha = 1;
    }
    perfReset() { this.perf = { n: 0, sum: 0, max: 0 }; }
    // 用於 UI：寵物頭頂（art 座標）
    petHead() { const p = this.petDraw; return p ? { x: CX, y: p.y + (p.h ? (p.h - 60) * 0 : 0) + 6 } : { x: CX, y: GROUND_Y - 70 }; }
  }

  return { Renderer, W, H, GROUND_Y, CX, lookAt, petSprite, POOP_SLOTS };
});
