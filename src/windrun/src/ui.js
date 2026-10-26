/* ui.js — Canvas 繪圖＋輸入（觸控／滑鼠）。所有美術＝原創向量圖形，無外部素材。 */
(function (g) {
  'use strict';
  const Data = g.WR.Data, Sim = g.WR.Sim, P = Data.PARAMS;
  const W = 540, H = 960;
  const FONT = '"PingFang HK","Noto Sans HK","Noto Sans CJK HK","Noto Sans CJK TC","Microsoft JhengHei","Heiti TC",sans-serif';
  const COL = { bg: '#14202e', panel: '#1f3347', panel2: '#27425c', line: '#3b5c7c', text: '#f2f6fa', dim: '#9fb3c8', gold: '#ffd166', red: '#ff6b6b', green: '#6ee7a0', blue: '#6cb6ff', btn: '#2f7fd1', btnDis: '#3a4756' };
  const APT_COL = ['#7d8590', '#5aa0e6', '#52c97d', '#ffc83d'];
  const UI = { W, H, hits: [], down: null, t: 0, scale: 1, canvas: null, ctx: null, audioCtx: null, sound: true };

  // ---------- 基本繪圖工具 ----------
  function font(sz, w) { return (w || '600') + ' ' + sz + 'px ' + FONT; }
  function txt(c, s, x, y, o) {
    o = o || {};
    c.font = font(o.size || 18, o.weight); c.fillStyle = o.color || COL.text;
    c.textAlign = o.align || 'left'; c.textBaseline = o.base || 'middle';
    c.fillText(s, x, y);
  }
  function wrap(c, s, x, y, maxW, lh, o) {
    o = o || {}; c.font = font(o.size || 16, o.weight);
    let line = '', yy = y;
    for (const ch of s) {
      if (ch === '\n' || c.measureText(line + ch).width > maxW) { txt(c, line, x, yy, o); yy += lh; line = ch === '\n' ? '' : ch; }
      else line += ch;
    }
    if (line) { txt(c, line, x, yy, o); yy += lh; }
    return yy;
  }
  function rr(c, x, y, w, h, r) {
    c.beginPath(); c.moveTo(x + r, y); c.arcTo(x + w, y, x + w, y + h, r); c.arcTo(x + w, y + h, x, y + h, r);
    c.arcTo(x, y + h, x, y, r); c.arcTo(x, y, x + w, y, r); c.closePath();
  }
  function ell(c, x, y, rx, ry, rot) { c.beginPath(); c.ellipse(x, y, rx, ry, rot || 0, 0, Math.PI * 2); c.fill(); }
  function panel(c, x, y, w, h, fill, stroke) {
    rr(c, x, y, w, h, 12); c.fillStyle = fill || COL.panel; c.fill();
    if (stroke) { c.lineWidth = 2; c.strokeStyle = stroke; c.stroke(); }
  }
  function hit(id, x, y, w, h, cb) { UI.hits.push({ id, x, y, w, h, cb }); }
  function btn(c, id, x, y, w, h, label, o, cb) {
    o = o || {};
    const pressed = UI.down && UI.down.id === id;
    rr(c, x, y + (pressed ? 2 : 0), w, h, 14);
    c.fillStyle = o.disabled ? COL.btnDis : (o.color || COL.btn);
    c.fill();
    if (!o.disabled) { c.lineWidth = 2; c.strokeStyle = 'rgba(255,255,255,0.25)'; c.stroke(); }
    const cy = y + (pressed ? 2 : 0) + h / 2;
    if (o.sub) {
      txt(c, label, x + w / 2, cy - 9, { size: o.size || 22, align: 'center', color: o.disabled ? '#7f8c99' : COL.text, weight: '700' });
      txt(c, o.sub, x + w / 2, cy + 15, { size: 13, align: 'center', color: o.disabled ? '#6b7885' : 'rgba(255,255,255,0.8)' });
    } else txt(c, label, x + w / 2, cy, { size: o.size || 22, align: 'center', color: o.disabled ? '#7f8c99' : COL.text, weight: '700' });
    if (!o.disabled && cb) hit(id, x, y, w, h, cb);
  }
  function bar(c, x, y, w, h, frac, color, bg) {
    rr(c, x, y, w, h, h / 2); c.fillStyle = bg || 'rgba(0,0,0,0.35)'; c.fill();
    if (frac > 0) { rr(c, x, y, Math.max(h, w * Math.min(1, frac)), h, h / 2); c.fillStyle = color; c.fill(); }
  }
  function hash(n) { const s = Math.sin(n * 127.1 + 311.7) * 43758.5453; return s - Math.floor(s); }
  function mmss(t) { t = Math.max(0, t); const m = Math.floor(t / 60), s = Math.floor(t % 60), d = Math.floor((t % 1) * 10); return (m < 10 ? '0' : '') + m + ':' + (s < 10 ? '0' : '') + s + '.' + d; }
  const TER = Data.TERRAINS, TIDX = Data.TERRAIN_INDEX;

  // ---------- 音效（WebAudio 嘟嘟聲，可關） ----------
  function beep(freq, dur, type, vol, delay) {
    if (!UI.sound) return;
    try {
      if (!UI.audioCtx) { const AC = window.AudioContext || window.webkitAudioContext; if (!AC) return; UI.audioCtx = new AC(); }
      const a = UI.audioCtx, o = a.createOscillator(), gn = a.createGain(), t0 = a.currentTime + (delay || 0);
      o.type = type || 'square'; o.frequency.setValueAtTime(freq, t0);
      gn.gain.setValueAtTime(vol || 0.05, t0); gn.gain.exponentialRampToValueAtTime(0.0001, t0 + dur);
      o.connect(gn); gn.connect(a.destination); o.start(t0); o.stop(t0 + dur + 0.02);
    } catch (e) { /* 音效失敗唔影響遊戲 */ }
  }
  const SFX = {
    tap() { beep(660, 0.06, 'square', 0.04); },
    swap() { beep(440, 0.08, 'triangle', 0.07); beep(660, 0.1, 'triangle', 0.07, 0.08); },
    skill() { beep(500, 0.1, 'sawtooth', 0.05); beep(800, 0.12, 'sawtooth', 0.05, 0.08); beep(1100, 0.15, 'sawtooth', 0.05, 0.16); },
    warn() { beep(220, 0.15, 'square', 0.05); },
    count() { beep(520, 0.1, 'square', 0.05); },
    go() { beep(880, 0.25, 'square', 0.06); },
    win() { [523, 659, 784, 1047].forEach((f, i) => beep(f, 0.18, 'triangle', 0.08, i * 0.13)); },
    lose() { [392, 330, 262].forEach((f, i) => beep(f, 0.25, 'triangle', 0.07, i * 0.18)); }
  };
  UI.SFX = SFX;

  // ---------- 原創野靈造型（向量） ----------
  function drawCreature(c, cr, x, y, s, o) {
    o = o || {};
    const t = o.t || 0, ph = t * (o.rate || 9), alpha = o.alpha == null ? 1 : o.alpha;
    c.save(); c.globalAlpha = alpha; c.translate(x, y);
    const bob = o.run ? -Math.abs(Math.sin(ph)) * s * 0.09 : 0;
    c.translate(0, bob);
    const body = cr.color, acc = cr.accent, k = s;
    // 腳
    const lx = o.run ? Math.sin(ph) * k * 0.14 : 0;
    c.fillStyle = acc;
    ell(c, -k * 0.2 + lx, k * 0.4, k * 0.09, k * 0.12);
    ell(c, k * 0.2 - lx, k * 0.4, k * 0.09, k * 0.12);
    if (cr.shape === 'heron') { c.strokeStyle = '#e8a23a'; c.lineWidth = k * 0.05; c.beginPath(); c.moveTo(-k * 0.15, k * 0.3); c.lineTo(-k * 0.15 + lx, k * 0.52); c.moveTo(k * 0.15, k * 0.3); c.lineTo(k * 0.15 - lx, k * 0.52); c.stroke(); }
    // 後部／身後裝飾
    c.fillStyle = body; c.strokeStyle = body;
    if (cr.shape === 'cat') { c.lineWidth = k * 0.1; c.lineCap = 'round'; c.beginPath(); c.moveTo(-k * 0.42, k * 0.05); c.quadraticCurveTo(-k * 0.75, -k * 0.1 + Math.sin(ph) * k * 0.1, -k * 0.62, -k * 0.4); c.stroke(); }
    if (cr.shape === 'fin') { c.fillStyle = acc; c.beginPath(); c.moveTo(-k * 0.42, 0); c.lineTo(-k * 0.72, -k * 0.2 + Math.sin(ph) * k * 0.05); c.lineTo(-k * 0.72, k * 0.2); c.closePath(); c.fill(); c.beginPath(); c.moveTo(-k * 0.1, -k * 0.36); c.lineTo(k * 0.05, -k * 0.62); c.lineTo(k * 0.22, -k * 0.34); c.closePath(); c.fill(); }
    if (cr.shape === 'weasel') { c.lineWidth = k * 0.16; c.lineCap = 'round'; c.beginPath(); c.moveTo(-k * 0.45, 0); c.quadraticCurveTo(-k * 0.8, k * 0.1, -k * 0.78, -k * 0.2 + Math.sin(ph) * k * 0.08); c.stroke(); }
    // 身體
    c.fillStyle = body;
    const bw = cr.shape === 'weasel' ? 0.56 : 0.5;
    ell(c, 0, 0, k * bw, k * 0.4);
    c.fillStyle = 'rgba(255,255,255,0.28)'; ell(c, k * 0.04, k * 0.1, k * bw * 0.7, k * 0.2);
    // 頭部／特徵
    if (cr.shape === 'tuft') { c.fillStyle = acc; [[-0.22, -0.36, 0.14], [0.02, -0.46, 0.17], [0.26, -0.34, 0.13]].forEach(a => { ell(c, k * a[0], k * a[1], k * a[2], k * a[2]); }); c.fillStyle = '#9be37f'; ell(c, k * 0.02, -k * 0.5, k * 0.08, k * 0.08); }
    if (cr.shape === 'cat' || cr.shape === 'weasel' || cr.shape === 'badger') { c.fillStyle = acc; [[-0.12, -0.5], [0.2, -0.5]].forEach(a => { c.beginPath(); c.moveTo(k * (a[0] - 0.1), -k * 0.3); c.lineTo(k * a[0], k * a[1]); c.lineTo(k * (a[0] + 0.1), -k * 0.3); c.closePath(); c.fill(); }); }
    if (cr.shape === 'badger') { c.fillStyle = acc; ell(c, k * 0.22, -k * 0.02, k * 0.1, k * 0.3); c.fillStyle = '#f2ece6'; ell(c, k * 0.34, k * 0.06, k * 0.1, k * 0.14); }
    if (cr.shape === 'deer') { c.strokeStyle = acc; c.lineWidth = k * 0.05; c.lineCap = 'round'; c.beginPath(); c.moveTo(k * 0.1, -k * 0.34); c.lineTo(k * 0.05, -k * 0.68); c.moveTo(k * 0.05, -k * 0.55); c.lineTo(-k * 0.1, -k * 0.7); c.moveTo(k * 0.2, -k * 0.32); c.lineTo(k * 0.3, -k * 0.64); c.moveTo(k * 0.27, -k * 0.52); c.lineTo(k * 0.44, -k * 0.6); c.stroke(); c.fillStyle = '#fff'; ell(c, k * 0.05, -k * 0.7, k * 0.04, k * 0.04); ell(c, k * 0.3, -k * 0.66, k * 0.04, k * 0.04); }
    if (cr.shape === 'heron') { c.fillStyle = '#f2a33a'; c.beginPath(); c.moveTo(k * 0.44, -k * 0.06); c.lineTo(k * 0.72, k * 0.02); c.lineTo(k * 0.44, k * 0.1); c.closePath(); c.fill(); c.strokeStyle = acc; c.lineWidth = k * 0.06; c.lineCap = 'round'; c.beginPath(); c.moveTo(k * 0.05, -k * 0.38); c.quadraticCurveTo(-k * 0.1, -k * 0.62, -k * 0.28, -k * 0.55); c.moveTo(k * 0.12, -k * 0.38); c.quadraticCurveTo(k * 0.05, -k * 0.66, -k * 0.12, -k * 0.66); c.stroke(); }
    if (cr.shape === 'fern') { c.fillStyle = acc; [-0.6, -0.2, 0.25].forEach((a, i) => { c.save(); c.translate(k * (-0.15 + i * 0.2), -k * 0.34); c.rotate(a + Math.sin(ph + i) * 0.08); ell(c, 0, -k * 0.2, k * 0.07, k * 0.22); c.restore(); }); }
    // 眼
    c.fillStyle = '#fff'; ell(c, k * 0.24, -k * 0.08, k * 0.1, k * 0.11);
    c.fillStyle = '#16212c'; ell(c, k * 0.27, -k * 0.07, k * 0.05, k * 0.06);
    c.fillStyle = '#fff'; ell(c, k * 0.29, -k * 0.09, k * 0.015, k * 0.015);
    c.restore();
  }

  // 適性圖示：4 級訊號格（顏色＋格數；乘風＝金色＋光暈）
  function drawApt(c, x, y, lv, s) {
    s = s || 28;
    const bw = s / 5, gap = s / 12;
    if (lv === 4) { c.save(); c.shadowColor = '#ffd166'; c.shadowBlur = 10; c.fillStyle = 'rgba(255,200,61,0.25)'; rr(c, x - 3, y - 3, s + 6, s + 6, 6); c.fill(); c.restore(); }
    for (let i = 0; i < 4; i++) {
      const bh = s * (0.3 + 0.7 * (i + 1) / 4);
      c.fillStyle = i < lv ? APT_COL[lv - 1] : 'rgba(255,255,255,0.12)';
      rr(c, x + i * (bw + gap), y + s - bh, bw, bh, 2); c.fill();
    }
    if (lv === 4) { c.fillStyle = '#fff'; txt(c, '★', x + s - 2, y + 2, { size: s * 0.45, color: '#fff3c4', align: 'center' }); }
  }
  // 地形圖章（細色塊）
  function terrainChip(c, x, y, w, h, tid, label) {
    const T = TER[TIDX[tid]]; rr(c, x, y, w, h, 6); c.fillStyle = T.color; c.fill();
    c.lineWidth = 1.5; c.strokeStyle = T.dark; c.stroke();
    if (label !== false) txt(c, T.name, x + w / 2, y + h / 2, { size: Math.min(15, h * 0.7), align: 'center', color: tid === 'frost' ? '#2a4a5c' : '#fff' });
  }

  // ---------- 賽道繪製 ----------
  const SC = 1.8; // px / m
  function drawTerrainBand(c, race, y, h, camX, t) {
    const L = P.segment_len;
    for (let i = 0; i < race.terrains.length; i++) {
      const T = TER[TIDX[race.terrains[i]]];
      const sx0 = (i * L - camX) * SC, sx1 = ((i + 1) * L - camX) * SC;
      if (sx1 < 0 || sx0 > W) continue;
      const x0 = Math.max(0, sx0), x1 = Math.min(W, sx1);
      c.save(); c.beginPath(); c.rect(x0, y, x1 - x0, h); c.clip();
      c.fillStyle = T.color; c.fillRect(x0, y, x1 - x0, h);
      const w0 = camX + x0 / SC, w1 = camX + x1 / SC;
      const id = T.id;
      if (id === 'moss') {
        c.strokeStyle = T.dark; c.lineWidth = 2;
        for (let wx = Math.floor(w0 / 4) * 4; wx < w1; wx += 4) { const hh = hash(wx), px = (wx - camX) * SC, py = y + 8 + hash(wx + 9) * (h - 16); c.beginPath(); c.arc(px, py, 4 + hh * 3, Math.PI, 0); c.stroke(); }
        c.fillStyle = T.light; for (let wx = Math.floor(w0 / 7) * 7; wx < w1; wx += 7) { c.fillRect((wx - camX) * SC, y + 6 + hash(wx + 3) * (h - 12), 3, 3); }
      } else if (id === 'gravel') {
        for (let wx = Math.floor(w0 / 2.5) * 2.5; wx < w1; wx += 2.5) { const hh = hash(wx * 3); c.fillStyle = hh > 0.5 ? T.dark : T.light; const r = 1.5 + hash(wx + 5) * 2.5; c.beginPath(); c.arc((wx - camX) * SC, y + 5 + hash(wx + 1) * (h - 10), r, 0, 6.3); c.fill(); }
      } else if (id === 'shallows') {
        c.strokeStyle = T.light; c.lineWidth = 2;
        for (let r = 0; r < 4; r++) { c.beginPath(); for (let px = x0; px <= x1; px += 6) { const py = y + (r + 0.6) * h / 4 + Math.sin(px * 0.05 + t * 2 + r * 1.7) * 3; if (px === x0) c.moveTo(px, py); else c.lineTo(px, py); } c.stroke(); }
      } else if (id === 'frost') {
        c.strokeStyle = T.dark; c.lineWidth = 1;
        for (let wx = Math.floor(w0 / 5) * 5; wx < w1; wx += 5) { const px = (wx - camX) * SC, py = y + 6 + hash(wx + 2) * (h - 12); c.beginPath(); c.moveTo(px - 5, py + 3); c.lineTo(px + 5, py - 3); c.stroke(); }
        c.fillStyle = '#fff'; for (let wx = Math.floor(w0 / 9) * 9; wx < w1; wx += 9) { const px = (wx - camX) * SC, py = y + 8 + hash(wx + 4) * (h - 16), tw = 1 + Math.sin(t * 4 + wx) * 0.5; c.fillRect(px - tw * 2, py - 0.5, tw * 4, 1.5); c.fillRect(px - 0.5, py - tw * 2, 1.5, tw * 4); }
      } else if (id === 'bridge') {
        c.fillStyle = '#2a1d12'; c.fillRect(x0, y + h * 0.78, x1 - x0, h * 0.22);
        c.fillStyle = T.color; c.fillRect(x0, y, x1 - x0, h * 0.78);
        c.strokeStyle = T.dark; c.lineWidth = 2;
        for (let wx = Math.floor(w0 / 3) * 3; wx < w1; wx += 3) { const px = (wx - camX) * SC; c.beginPath(); c.moveTo(px, y); c.lineTo(px, y + h * 0.78); c.stroke(); }
        c.strokeStyle = T.light; c.lineWidth = 3; c.beginPath(); c.moveTo(x0, y + 3); c.lineTo(x1, y + 3); c.stroke();
        c.strokeStyle = T.dark; c.lineWidth = 3; c.beginPath(); c.moveTo(x0, y + h * 0.78 - 2); c.lineTo(x1, y + h * 0.78 - 2); c.stroke();
      }
      c.restore();
    }
  }
  function drawLane(c, race, s, y, h, camX, t, label) {
    const side = race.sides[s];
    c.save(); c.beginPath(); c.rect(0, y, W, h); c.clip();
    const sky = c.createLinearGradient(0, y, 0, y + h); sky.addColorStop(0, '#2b4a6b'); sky.addColorStop(1, '#4d7396');
    c.fillStyle = sky; c.fillRect(0, y, W, h);
    // 遠山
    c.fillStyle = 'rgba(20,40,60,0.35)';
    for (let i = -1; i < 8; i++) { const bx = i * 120 - ((camX * 0.4) * SC) % 120; c.beginPath(); c.moveTo(bx, y + 52); c.lineTo(bx + 60, y + 18 + hash(i + Math.floor(camX * 0.4 * SC / 120)) * 14); c.lineTo(bx + 120, y + 52); c.closePath(); c.fill(); }
    const gy = y + 52, gh = h - 58;
    drawTerrainBand(c, race, gy, gh, camX, t);
    // 段界線＋里程
    c.setLineDash([6, 6]); c.strokeStyle = 'rgba(255,255,255,0.55)'; c.lineWidth = 1.5;
    for (let i = 1; i < race.terrains.length; i++) { const x = (i * P.segment_len - camX) * SC; c.beginPath(); c.moveTo(x, gy); c.lineTo(x, gy + gh); c.stroke(); if (x > 36) txt(c, (i * P.segment_len) + 'm', x, gy - 8, { size: 12, align: 'center', color: 'rgba(255,255,255,0.8)' }); }
    c.setLineDash([]);
    // 起點／終點
    const fx = (P.track_len - camX) * SC;
    for (let r = 0; r < 8; r++) for (let q = 0; q < 2; q++) { c.fillStyle = (r + q) % 2 ? '#111' : '#fff'; c.fillRect(fx + q * 8, gy + r * gh / 8, 8, gh / 8); }
    const sx0 = (0 - camX) * SC; c.fillStyle = '#fff'; c.fillRect(sx0 - 3, gy, 4, gh);
    // 跑手
    const u = side.team[side.active], cr = Data.CREATURES_BY_ID[u.cid];
    const px = (side.pos - camX) * SC, py = gy + gh * 0.62;
    c.fillStyle = 'rgba(0,0,0,0.3)'; ell(c, px, py + 30, 26, 6);
    let alpha = 1;
    if (side.phase === 'out') alpha = 0.55 + 0.25 * Math.sin(t * 25);
    if (side.phase === 'in') alpha = 0.6 + 0.4 * (1 - side.phaseT / P.swap_in_time);
    // 加速線
    if (side.effect && side.effect.type === 'boost') { c.strokeStyle = 'rgba(255,230,120,0.85)'; c.lineWidth = 3; for (let i = 0; i < 5; i++) { const ly = py - 22 + i * 12, off = (t * 160 + i * 31) % 50; c.beginPath(); c.moveTo(px - 36 - off, ly); c.lineTo(px - 60 - off, ly); c.stroke(); } }
    drawCreature(c, cr, px, py, 64, { run: true, t, rate: 1.1 * side.speed, alpha });
    if (side.effect && side.effect.type === 'trip') { c.strokeStyle = '#2e8b3a'; c.lineWidth = 3; for (let i = 0; i < 3; i++) { c.beginPath(); c.arc(px, py + 26, 20 + i * 5, 0.2 + i, 2.6 + i); c.stroke(); } }
    if (side.shield > 0) { c.strokeStyle = 'rgba(180,240,255,0.9)'; c.lineWidth = 3; c.fillStyle = 'rgba(160,230,255,0.18)'; c.beginPath(); c.arc(px, py, 46 + Math.sin(t * 6) * 2, 0, 6.3); c.fill(); c.stroke(); }
    // 名牌
    c.fillStyle = 'rgba(0,0,0,0.5)'; rr(c, px - 44, py - 58, 88, 20, 8); c.fill();
    txt(c, u.name + ' Lv' + u.lv, px, py - 48, { size: 13, align: 'center' });
    c.restore();
    // 車道標籤
    c.fillStyle = s === 0 ? 'rgba(47,127,209,0.9)' : 'rgba(209,80,70,0.9)'; rr(c, 8, y + 8, 64, 24, 8); c.fill();
    txt(c, label, 40, y + 20, { size: 15, align: 'center', weight: '700' });
  }

  // ---------- 賽事畫面 ----------
  function gTier(G_) { return G_ >= 0.999 ? ['×1.00', COL.green] : G_ >= 0.9 ? ['×' + G_.toFixed(2), '#d6e86a'] : G_ >= 0.8 ? ['×' + G_.toFixed(2), '#ffb347'] : ['×' + G_.toFixed(2), COL.red]; }
  function chips(race, side) {
    const out = [], u = side.team[side.active];
    if (side.phase === 'out') out.push(['交棒中', '#ffb347']);
    if (side.phase === 'in') out.push(['入場加速', '#ffd166']);
    if (side.effect && side.effect.type === 'boost') out.push(['疾風衝', '#ffd166']);
    if (side.effect && side.effect.type === 'trip') out.push(['被絆', '#7bd36b']);
    if (side.shield > 0) out.push(['風罩', '#9be3ff']);
    if (u.stamina <= 0) out.push(['力竭', COL.red]);
    if (side.C > 1.0001) out.push(['追趕 +' + Math.round((side.C - 1) * 100) + '%', '#c9a6ff']);
    return out;
  }
  function drawSidePanel(c, race, s, x, y, w, h) {
    const side = race.sides[s], u = side.team[side.active], cr = Data.CREATURES_BY_ID[u.cid];
    panel(c, x, y, w, h, COL.panel, s === 0 ? COL.btn : '#b45a52');
    txt(c, (s === 0 ? '我方 ' : '對手 ') + u.name, x + 12, y + 16, { size: 16, weight: '700' });
    txt(c, 'Lv' + u.lv, x + w - 12, y + 16, { size: 14, align: 'right', color: COL.dim });
    const pct = u.stamina / u.max;
    const tier = gTier(side.G);
    bar(c, x + 12, y + 32, w - 24, 12, pct, pct > 0.3 ? COL.green : pct > 0.1 ? '#ffb347' : COL.red);
    txt(c, '耐力 ' + Math.ceil(u.stamina) + '/' + Math.round(u.max), x + 12, y + 56, { size: 13, color: COL.dim });
    txt(c, '氣勢 ' + tier[0], x + w - 12, y + 56, { size: 14, align: 'right', color: tier[1], weight: '700' });
    // 現段適性
    const seg = Sim.segOf(race, side.pos), ai = u.apt[TIDX[race.terrains[seg]]];
    drawApt(c, x + 12, y + 68, ai, 22);
    txt(c, Data.APT_NAMES[ai - 1], x + 40, y + 79, { size: 12, color: APT_COL[ai - 1] });
    txt(c, (side.speed).toFixed(1) + ' m/s', x + w - 12, y + 79, { size: 13, align: 'right', color: COL.text });
    // 狀態標籤（疊喺頂部右側不夠位 → 放喺名稱列下方小字）
    const ch = chips(race, side); let cx = x + 80;
    ch.slice(0, 3).forEach(a => { c.font = font(11); const tw = c.measureText(a[0]).width + 10; rr(c, cx, y + 70, tw, 18, 9); c.fillStyle = a[1]; c.fill(); txt(c, a[0], cx + tw / 2, y + 79, { size: 11, align: 'center', color: '#1b2a38', weight: '700' }); cx += tw + 4; });
  }
  function drawRace(c, G) {
    const R = G.race, race = R.sim, t = UI.t, stage = R.stage;
    c.fillStyle = COL.bg; c.fillRect(0, 0, W, H);
    // 頂欄
    txt(c, stage.name, 16, 26, { size: 20, weight: '700' });
    txt(c, mmss(R.countdown > 0 ? 0 : race.t), W / 2 + 30, 26, { size: 22, align: 'center', color: COL.gold, weight: '700' });
    btn(c, 'spd', W - 88, 8, 76, 36, R.mul + 'x 速度', { size: 16, color: R.mul === 2 ? '#d1822f' : COL.panel2 }, () => { R.mul = R.mul === 1 ? 2 : 1; SFX.tap(); });
    // 迷你進度條
    const mx = 20, mw = W - 40, my = 62;
    for (let i = 0; i < 5; i++) { const T = TER[TIDX[race.terrains[i]]]; c.fillStyle = T.color; c.fillRect(mx + i * mw / 5, my, mw / 5 - 1, 16); txt(c, T.name, mx + (i + 0.5) * mw / 5, my + 8, { size: 11, align: 'center', color: T.id === 'frost' ? '#2a4a5c' : '#fff' }); }
    [[0, '#4da3ff'], [1, '#ff7a6b']].forEach(a => { const px = mx + mw * Math.min(1, race.sides[a[0]].pos / P.track_len); c.fillStyle = a[1]; c.beginPath(); c.moveTo(px, my + (a[0] ? 24 : -4)); c.lineTo(px - 6, my + (a[0] ? 34 : -14)); c.lineTo(px + 6, my + (a[0] ? 34 : -14)); c.closePath(); c.fill(); });
    const d = race.sides[0].pos - race.sides[1].pos;
    txt(c, d >= 0 ? '領先 ' + d.toFixed(0) + ' m' : '落後 ' + (-d).toFixed(0) + ' m', W - 20, my + 44, { size: 12, align: 'right', color: d >= 0 ? COL.green : '#ffb347' });
    txt(c, Math.floor(race.sides[0].pos) + ' / ' + P.track_len + ' m', 20, my + 44, { size: 12, color: COL.dim });
    // 跑道
    const camX = Sim.clamp((race.sides[0].pos + race.sides[1].pos) / 2 - 110, -20, P.track_len - W / SC + 20);
    drawLane(c, race, 1, 112, 138, camX, t, '對手');
    drawLane(c, race, 0, 254, 138, camX, t, '我方');
    // 事件浮字
    R.pops = R.pops.filter(p => t - p.t0 < 1.8);
    R.pops.forEach(p => { const a = 1 - (t - p.t0) / 1.8; c.globalAlpha = Math.max(0, a); txt(c, p.text, W / 2, p.y - (t - p.t0) * 18, { size: 24, align: 'center', color: p.color, weight: '800' }); c.globalAlpha = 1; });
    // 狀態面板
    drawSidePanel(c, race, 0, 12, 400, 258, 96);
    drawSidePanel(c, race, 1, 270, 400, 258, 96);
    // 地形適性條
    const me = race.sides[0], mu = me.team[me.active], op = race.sides[1], ou = op.team[op.active];
    const cseg = Sim.segOf(race, me.pos);
    txt(c, '各段地形適性（左＝我方現役 ' + mu.name + '，右＝對手現役）', 16, 514, { size: 13, color: COL.dim });
    for (let i = 0; i < 5; i++) {
      const bx = 14 + i * 102, T = TER[TIDX[race.terrains[i]]], cur = i === cseg;
      panel(c, bx, 526, 98, 70, cur ? '#34506b' : COL.panel, cur ? COL.gold : null);
      c.fillStyle = T.color; rr(c, bx + 4, 530, 90, 18, 6); c.fill();
      txt(c, T.name, bx + 49, 539, { size: 13, align: 'center', color: T.id === 'frost' ? '#2a4a5c' : '#fff', weight: '700' });
      drawApt(c, bx + 12, 556, mu.apt[TIDX[T.id]], 26);
      drawApt(c, bx + 62, 560, ou.apt[TIDX[T.id]], 20);
      if (cur) txt(c, '▼', bx + 49, 521, { size: 12, align: 'center', color: COL.gold });
    }
    // 技能鈕
    const canSk = Sim.canSkill(race, 0) && R.countdown <= 0;
    const sk = Data.SKILLS[mu.skill];
    const label = mu.skillUsed ? '技能已用（' + sk.name + '）' : '技能：' + sk.name;
    const sub = mu.skillUsed ? '呢隻野靈今場已經用過' : (me.phase !== 'run' ? '交棒／入場期間唔可放' : Data.skillDesc(mu.skill, P));
    btn(c, 'skill', 20, 606, W - 40, 72, label, { disabled: !canSk, color: '#c9722b', sub, size: 24 }, () => { if (Sim.requestSkill(race, 0)) { G.onRaceEvents(); } });
    // 後備
    txt(c, '後備（點頭像換人）', 20, 700, { size: 15, color: COL.dim });
    const bench = []; me.team.forEach((u2, i) => { if (i !== me.active) bench.push(i); });
    if (me.phase === 'out' || me.phase === 'in') txt(c, '交棒／入場中…', W - 20, 700, { size: 13, align: 'right', color: '#ffb347' });
    else if (me.cooldown > 0) txt(c, '換人冷卻 ' + me.cooldown.toFixed(1) + ' s', W - 20, 700, { size: 13, align: 'right', color: '#ffb347' });
    else txt(c, '可以換人', W - 20, 700, { size: 13, align: 'right', color: COL.green });
    const n = Math.max(1, bench.length), gap = 10, tw = Math.min(160, (W - 40 - gap * (n - 1)) / n), tx0 = (W - (tw * n + gap * (n - 1))) / 2;
    const nextSeg = Math.min(4, cseg + 1);
    bench.forEach((idx, k) => {
      const u2 = me.team[idx], cr = Data.CREATURES_BY_ID[u2.cid], bx = tx0 + k * (tw + gap), by = 712;
      const can = Sim.canSwap(race, 0) && R.countdown <= 0;
      panel(c, bx, by, tw, 212, can ? COL.panel2 : COL.panel, can ? COL.blue : null);
      drawCreature(c, cr, bx + tw / 2, by + 52, 62, { t, run: false });
      txt(c, u2.name, bx + tw / 2, by + 100, { size: 17, align: 'center', weight: '700' });
      txt(c, 'Lv' + u2.lv + (u2.skillUsed ? '・技能已用' : '・' + Data.SKILLS[u2.skill].name), bx + tw / 2, by + 118, { size: 12, align: 'center', color: COL.dim });
      const pc = u2.stamina / u2.max;
      bar(c, bx + 10, by + 130, tw - 20, 10, pc, pc > 0.3 ? COL.green : pc > 0.1 ? '#ffb347' : COL.red);
      txt(c, '耐力 ' + Math.ceil(u2.stamina) + '/' + Math.round(u2.max), bx + tw / 2, by + 150, { size: 12, align: 'center', color: COL.dim });
      const a1 = u2.apt[TIDX[race.terrains[cseg]]], a2 = u2.apt[TIDX[race.terrains[nextSeg]]];
      txt(c, '現段', bx + 12, by + 175, { size: 12, color: COL.dim }); drawApt(c, bx + 44, by + 163, a1, 24);
      txt(c, '下段', bx + tw / 2 + 4, by + 175, { size: 12, color: COL.dim }); drawApt(c, bx + tw / 2 + 36, by + 163, a2, 24);
      const tc = TER[TIDX[race.terrains[nextSeg]]];
      txt(c, '下段 ' + tc.name + (cseg === 4 ? '（已係最後段）' : ''), bx + tw / 2, by + 198, { size: 11, align: 'center', color: tc.color });
      if (!can) { c.fillStyle = 'rgba(10,18,28,0.55)'; rr(c, bx, by, tw, 212, 12); c.fill(); if (me.cooldown > 0 && me.phase === 'run') txt(c, me.cooldown.toFixed(1), bx + tw / 2, by + 106, { size: 36, align: 'center', color: '#ffb347', weight: '800' }); }
      else hit('bench' + idx, bx, by, tw, 212, () => { if (Sim.requestSwap(race, 0, idx)) G.onRaceEvents(); });
    });
    // 提示
    if (R.countdown > 0) txt(c, stage.tip, W / 2, 946, { size: 13, align: 'center', color: COL.gold });
    else txt(c, race.over ? '' : stage.tip, W / 2, 946, { size: 13, align: 'center', color: COL.dim });
    // 倒數／結束遮罩
    if (R.countdown > 0) {
      c.fillStyle = 'rgba(8,14,22,0.55)'; c.fillRect(0, 112, W, 280);
      const n2 = Math.ceil(R.countdown);
      txt(c, n2 > 0 ? String(n2) : '開跑！', W / 2, 250, { size: 96, align: 'center', color: COL.gold, weight: '800' });
      txt(c, stage.name + '・對手：' + stage.opp.name, W / 2, 330, { size: 18, align: 'center' });
    }
    if (race.over) {
      const win = race.winner === 0;
      c.fillStyle = 'rgba(8,14,22,0.7)'; c.fillRect(0, 150, W, 300);
      txt(c, win ? '勝利！' : '落敗…', W / 2, 235, { size: 72, align: 'center', color: win ? COL.gold : COL.red, weight: '800' });
      txt(c, '時間 ' + mmss(race.duration) + '・換人 ' + me.swaps + ' 次・技能 ' + me.skills + ' 次', W / 2, 300, { size: 18, align: 'center' });
      btn(c, 'toResult', W / 2 - 110, 340, 220, 60, '看結算', { color: '#2f9e5b' }, () => G.finishRace());
    }
  }

  // ---------- 養成畫面 ----------
  function creatureCard(c, id, x, y, w, h, selected, G, extra) {
    const cr = Data.CREATURES_BY_ID[id], st = G.save.creatures[id];
    panel(c, x, y, w, h, selected ? '#34506b' : COL.panel, selected ? COL.gold : null);
    drawCreature(c, cr, x + 40, y + h / 2 + 2, 54, { t: selected ? UI.t : 0, run: selected, rate: 8 });
    txt(c, cr.name, x + 80, y + 20, { size: 18, weight: '700' });
    txt(c, 'Lv' + st.lv, x + w - 12, y + 20, { size: 15, align: 'right', color: COL.gold, weight: '700' });
    if (!extra) {
      const need = Sim.expToNext(st.lv, P);
      bar(c, x + 80, y + 36, w - 94, 8, st.lv >= P.level_cap ? 1 : st.exp / need, '#6cb6ff');
      txt(c, st.lv >= P.level_cap ? '已滿級' : '經驗 ' + Math.floor(st.exp) + '/' + need, x + 80, y + 56, { size: 12, color: COL.dim });
      bar(c, x + 80, y + 70, w - 94, 8, st.cond / 100, st.cond > 50 ? COL.green : '#ffb347');
      txt(c, '狀態 ' + Math.round(st.cond), x + 80, y + 90, { size: 12, color: COL.dim });
    }
  }
  function drawTrain(c, G) {
    const S = G.save;
    c.fillStyle = COL.bg; c.fillRect(0, 0, W, H);
    txt(c, '養成', 20, 28, { size: 28, weight: '800' });
    txt(c, '第 ' + S.turn + ' 回合', 100, 30, { size: 16, color: COL.dim });
    txt(c, '彩帶 ' + S.ribbons, W - 20, 20, { size: 16, align: 'right', color: '#ff9ecf', weight: '700' });
    txt(c, '行動 ', W - 100, 46, { size: 15, align: 'right', color: COL.dim });
    for (let i = 0; i < P.actions_per_turn; i++) { c.fillStyle = i < S.actionsLeft ? COL.gold : '#3a4756'; c.beginPath(); c.arc(W - 86 + i * 24, 46, 9, 0, 6.3); c.fill(); }
    Data.CREATURES.forEach((cr, i) => {
      const x = 20 + (i % 2) * 260, y = 68 + Math.floor(i / 2) * 108;
      creatureCard(c, cr.id, x, y, 250, 100, G.sel === cr.id, G);
      hit('card' + cr.id, x, y, 250, 100, () => { G.sel = cr.id; G.trainPick = false; SFX.tap(); });
    });
    // 詳情
    const cr = Data.CREATURES_BY_ID[G.sel], st = S.creatures[G.sel], stats = Sim.statsOf(G.sel, st, P);
    const py = 504;
    panel(c, 20, py, W - 40, 262, COL.panel);
    txt(c, cr.name + '  Lv' + st.lv, 36, py + 22, { size: 20, weight: '800' });
    wrap(c, cr.desc, 36, py + 48, 300, 17, { size: 13, color: COL.dim });
    drawCreature(c, cr, 440, py + 62, 96, { t: UI.t, run: true, rate: 7 });
    const rows = [['基礎速度', stats.speed, 'speed', 120], ['力量', stats.power, 'power', 120], ['冷靜', stats.calm, 'calm', 120], ['耐力上限', stats.stamina, 'stamina', 220]];
    rows.forEach((r, i) => {
      const yy = py + 84 + i * 22, b = st.bonus[r[2]] || 0;
      txt(c, r[0], 36, yy, { size: 14, color: COL.dim });
      bar(c, 112, yy - 5, 170, 10, r[1] / r[3], '#6cb6ff');
      txt(c, r[1].toFixed(1) + (b ? ' (+' + b + ')' : ''), 292, yy, { size: 14 });
    });
    const sk = Data.SKILLS[cr.skill];
    txt(c, '技能 ' + sk.name, 380, py + 120, { size: 15, color: COL.gold, weight: '700' });
    wrap(c, Data.skillDesc(cr.skill, P), 380, py + 142, 130, 16, { size: 12, color: COL.dim });
    if (cr.trait) txt(c, '特質：韌性', 380, py + 186, { size: 13, color: '#c9a6ff' });
    for (let i = 0; i < 5; i++) {
      const bx = 30 + i * 100, T = TER[i];
      c.fillStyle = T.color; rr(c, bx, py + 186, 92, 18, 6); c.fill();
      txt(c, T.name, bx + 46, py + 195, { size: 13, align: 'center', color: T.id === 'frost' ? '#2a4a5c' : '#fff', weight: '700' });
      drawApt(c, bx + 8, py + 211, cr.apt[i], 26);
      txt(c, Data.APT_NAMES[cr.apt[i] - 1], bx + 44, py + 226, { size: 13, color: APT_COL[cr.apt[i] - 1] });
    }
    // 行動
    const ay = 776, noAct = S.actionsLeft <= 0;
    if (!G.trainPick) {
      btn(c, 'feed', 20, ay, 160, 66, '餵食', { disabled: noAct, sub: '耐力上限 +' + P.feed_gain, color: '#3b9a5b' }, () => G.act('feed'));
      btn(c, 'train', 190, ay, 160, 66, '訓練', { disabled: noAct, sub: '揀屬性提升', color: '#c9722b' }, () => { G.trainPick = true; SFX.tap(); });
      btn(c, 'rest', 360, ay, 160, 66, '休息', { disabled: noAct, sub: '狀態 +' + P.rest_restore, color: '#5b6fd1' }, () => G.act('rest'));
    } else {
      btn(c, 't_speed', 20, ay, 120, 66, '速度', { sub: '+' + P.train_gain.speed + '（上限 ' + P.train_cap.speed + '）', color: '#c9722b', size: 20 }, () => G.act('train', 'speed'));
      btn(c, 't_power', 148, ay, 120, 66, '力量', { sub: '+' + P.train_gain.power + '（上限 ' + P.train_cap.power + '）', color: '#c9722b', size: 20 }, () => G.act('train', 'power'));
      btn(c, 't_calm', 276, ay, 120, 66, '冷靜', { sub: '+' + P.train_gain.calm + '（上限 ' + P.train_cap.calm + '）', color: '#c9722b', size: 20 }, () => G.act('train', 'calm'));
      btn(c, 't_x', 404, ay, 116, 66, '取消', { color: COL.panel2, size: 20 }, () => { G.trainPick = false; SFX.tap(); });
    }
    txt(c, noAct ? '今回合行動用晒。出賽後會開新一回合（行動回復 ' + P.actions_per_turn + ' 次）' : '每回合 ' + P.actions_per_turn + ' 個行動：餵食／訓練／休息，都會加經驗。', W / 2, 858, { size: 13, align: 'center', color: noAct ? '#ffb347' : COL.dim });
    btn(c, 'back', 20, 876, 120, 60, '主頁', { color: COL.panel2, size: 20 }, () => G.go('menu'));
    btn(c, 'toTeam', 150, 876, 370, 60, '去組隊 ▶', { color: '#2f9e5b', size: 24 }, () => G.go('team'));
  }

  // ---------- 組隊畫面 ----------
  function drawTeam(c, G) {
    const S = G.save, stage = Data.STAGES[G.stageSel - 1];
    c.fillStyle = COL.bg; c.fillRect(0, 0, W, H);
    txt(c, '組隊', 20, 28, { size: 28, weight: '800' });
    txt(c, '彩帶 ' + S.ribbons, W - 20, 28, { size: 16, align: 'right', color: '#ff9ecf', weight: '700' });
    Data.STAGES.forEach((sg, i) => {
      const y = 56 + i * 80, unlocked = sg.id === 1 || S.cleared[sg.id - 1], sel = G.stageSel === sg.id;
      panel(c, 20, y, W - 40, 72, sel ? '#34506b' : COL.panel, sel ? COL.gold : null);
      txt(c, sg.id + '．' + sg.name, 34, y + 20, { size: 19, weight: '800', color: unlocked ? COL.text : '#7f8c99' });
      txt(c, sg.sub, 34, y + 44, { size: 12, color: COL.dim });
      const st2 = !unlocked ? '未解鎖（先通關上一關）' : (S.cleared[sg.id] ? '已通關' : '未通關');
      txt(c, st2 + '・對手 ' + sg.opp.team.length + ' 隻 Lv' + sg.opp.team[0].lv, 34, y + 61, { size: 12, color: S.cleared[sg.id] ? COL.green : COL.dim });
      for (let k = 0; k < 5; k++) terrainChip(c, 300 + k * 44, y + 14, 40, 22, sg.terrains[k], false);
      for (let k = 0; k < 5; k++) { const T = TER[TIDX[sg.terrains[k]]]; txt(c, T.name, 320 + k * 44, y + 50, { size: 11, align: 'center', color: COL.dim }); }
      if (unlocked) hit('stage' + sg.id, 20, y, W - 40, 72, () => { G.stageSel = sg.id; G.teamPick = []; SFX.tap(); });
    });
    // 出戰次序
    const sy = 304;
    txt(c, '出戰次序（首發＋後備）：揀 ' + stage.teamSize + ' 隻，點已揀嘅可取消', 20, sy, { size: 14, color: COL.dim });
    const names = ['首發', '後備一', '後備二', '後備三', '後備四', '後備五'];
    const sw = (W - 40 - 10 * (stage.teamSize - 1)) / stage.teamSize;
    for (let i = 0; i < stage.teamSize; i++) {
      const x = 20 + i * (sw + 10), id = G.teamPick[i];
      panel(c, x, sy + 14, sw, 70, id ? COL.panel2 : COL.panel, id ? COL.blue : COL.line);
      txt(c, names[i], x + 10, sy + 30, { size: 12, color: COL.gold });
      if (id) { const cr = Data.CREATURES_BY_ID[id]; drawCreature(c, cr, x + 36, sy + 56, 42, {}); txt(c, cr.name, x + 66, sy + 52, { size: 16, weight: '700' }); txt(c, 'Lv' + S.creatures[id].lv, x + 66, sy + 72, { size: 12, color: COL.dim }); hit('slot' + i, x, sy + 14, sw, 70, () => { G.teamPick.splice(i, 1); SFX.tap(); }); }
      else txt(c, '空', x + sw / 2, sy + 58, { size: 18, align: 'center', color: '#52667b' });
    }
    // 野靈格（顯示呢關 5 段適性）
    const gy = 404;
    txt(c, '呢關各段地形（上）同每隻嘅適性（下）', 20, gy, { size: 13, color: COL.dim });
    Data.CREATURES.forEach((cr, i) => {
      const x = 20 + (i % 2) * 260, y = gy + 14 + Math.floor(i / 2) * 104, picked = G.teamPick.indexOf(cr.id);
      panel(c, x, y, 250, 98, picked >= 0 ? '#34506b' : COL.panel, picked >= 0 ? COL.gold : null);
      drawCreature(c, cr, x + 32, y + 36, 46, {});
      txt(c, cr.name, x + 62, y + 18, { size: 16, weight: '700' });
      txt(c, 'Lv' + S.creatures[cr.id].lv + '・' + Data.SKILLS[cr.skill].name, x + 62, y + 38, { size: 12, color: COL.dim });
      for (let k = 0; k < 5; k++) {
        const tid = stage.terrains[k], T = TER[TIDX[tid]], bx = x + 10 + k * 46;
        c.fillStyle = T.color; rr(c, bx, y + 54, 42, 6, 3); c.fill();
        drawApt(c, bx + 9, y + 64, cr.apt[TIDX[tid]], 24);
      }
      if (picked >= 0) { c.fillStyle = COL.gold; c.beginPath(); c.arc(x + 232, y + 18, 13, 0, 6.3); c.fill(); txt(c, String(picked + 1), x + 232, y + 19, { size: 16, align: 'center', color: '#1b2a38', weight: '800' }); }
      hit('pick' + cr.id, x, y, 250, 98, () => {
        const k = G.teamPick.indexOf(cr.id);
        if (k >= 0) G.teamPick.splice(k, 1); else if (G.teamPick.length < stage.teamSize) G.teamPick.push(cr.id);
        SFX.tap();
      });
    });
    const ready = G.teamPick.length === stage.teamSize;
    btn(c, 'back', 20, 876, 120, 60, '返回', { color: COL.panel2, size: 20 }, () => G.go('train'));
    btn(c, 'go', 150, 876, 370, 60, ready ? '出賽！' : '仲要揀 ' + (stage.teamSize - G.teamPick.length) + ' 隻', { disabled: !ready, color: '#c93b3b', size: 24 }, () => G.startRace());
    txt(c, '提示：首發跑第一段，其餘留喺後備，比賽中點頭像換人。', W / 2, 858, { size: 12, align: 'center', color: COL.dim });
  }

  // ---------- 結算畫面 ----------
  function drawResult(c, G) {
    const r = G.result;
    c.fillStyle = COL.bg; c.fillRect(0, 0, W, H);
    txt(c, r.win ? '勝利！' : '落敗…', W / 2, 90, { size: 72, align: 'center', color: r.win ? COL.gold : COL.red, weight: '800' });
    txt(c, r.stage.name + (r.firstClear ? '・首次通關！' : ''), W / 2, 150, { size: 20, align: 'center', color: COL.text });
    txt(c, '時間 ' + mmss(r.duration) + '・換人 ' + r.swaps + ' 次・技能 ' + r.skills + ' 次', W / 2, 184, { size: 16, align: 'center', color: COL.dim });
    panel(c, 20, 210, W - 40, 56, COL.panel);
    txt(c, '獲得彩帶', 40, 238, { size: 18 });
    txt(c, '+' + r.ribbons + '（共 ' + G.save.ribbons + '）', W - 40, 238, { size: 22, align: 'right', color: '#ff9ecf', weight: '800' });
    txt(c, '經驗', 20, 296, { size: 16, color: COL.dim });
    r.members.forEach((m, i) => {
      const y = 312 + i * 88, cr = Data.CREATURES_BY_ID[m.id];
      panel(c, 20, y, W - 40, 80, COL.panel);
      drawCreature(c, cr, 62, y + 40, 56, { t: UI.t, run: r.win, rate: 8 });
      txt(c, cr.name, 108, y + 22, { size: 19, weight: '700' });
      txt(c, 'Lv' + m.lvBefore + (m.lvAfter > m.lvBefore ? ' → Lv' + m.lvAfter + '  升級！' : ''), 108, y + 48, { size: 15, color: m.lvAfter > m.lvBefore ? COL.gold : COL.dim, weight: '700' });
      txt(c, '+' + m.exp + ' 經驗', W - 36, y + 22, { size: 18, align: 'right', color: COL.blue, weight: '700' });
      txt(c, m.ran ? '出場・狀態 −' + P.cond_cost_per_race : '未出場', W - 36, y + 50, { size: 13, align: 'right', color: COL.dim });
      const st = G.save.creatures[m.id];
      bar(c, 108, y + 62, W - 40 - 108 - 16, 8, st.lv >= P.level_cap ? 1 : st.exp / Sim.expToNext(st.lv, P), '#6cb6ff');
    });
    if (r.unlocked) txt(c, '已解鎖：' + r.unlocked, W / 2, 600, { size: 18, align: 'center', color: COL.green, weight: '700' });
    if (r.allClear) txt(c, '三關全數通關！可以繼續重玩刷經驗、調整隊伍。', W / 2, 630, { size: 15, align: 'center', color: COL.gold });
    btn(c, 'again', 20, 760, 250, 70, '再戰同一關', { color: '#c93b3b', size: 22 }, () => G.go('team', true));
    btn(c, 'train', 280, 760, 240, 70, '返回養成', { color: '#2f9e5b', size: 22 }, () => G.go('train'));
    btn(c, 'menu', 20, 846, W - 40, 56, '主頁', { color: COL.panel2, size: 20 }, () => G.go('menu'));
  }

  // ---------- 主頁／說明 ----------
  function drawMenu(c, G) {
    const t = UI.t;
    const g1 = c.createLinearGradient(0, 0, 0, H); g1.addColorStop(0, '#0f2a44'); g1.addColorStop(1, '#2b5a70');
    c.fillStyle = g1; c.fillRect(0, 0, W, H);
    // 風線
    c.strokeStyle = 'rgba(255,255,255,0.12)'; c.lineWidth = 3;
    for (let i = 0; i < 9; i++) { const y = 80 + i * 60, off = (t * (60 + i * 14)) % (W + 200); c.beginPath(); c.moveTo(W - off, y); c.lineTo(W - off + 120, y); c.stroke(); }
    txt(c, '風野競走', W / 2, 200, { size: 92, align: 'center', weight: '900', color: '#f6f1d7' });
    txt(c, '養野靈・換人・放技能　1 對 1 接力賽', W / 2, 270, { size: 19, align: 'center', color: '#bcd4e6' });
    // 跑道裝飾
    const gy = 640;
    for (let i = 0; i < 5; i++) { c.fillStyle = TER[i].color; c.fillRect(i * W / 5, gy, W / 5 + 1, 50); }
    c.fillStyle = 'rgba(0,0,0,0.25)'; c.fillRect(0, gy + 50, W, 6);
    Data.CREATURES.slice(0, 5).forEach((cr, i) => { const x = ((t * (70 + i * 9) + i * 130) % (W + 100)) - 50; drawCreature(c, cr, x, gy - 20, 56, { t: t + i, run: true, rate: 11 }); });
    const done = G.save.cleared;
    btn(c, 'start', 90, 360, 360, 78, '開始遊戲', { color: '#2f9e5b', size: 30 }, () => G.go('train'));
    btn(c, 'how', 90, 452, 360, 60, '玩法說明', { color: COL.btn, size: 22 }, () => G.go('howto'));
    btn(c, 'snd', 90, 524, 172, 52, UI.sound ? '音效：開' : '音效：關', { color: COL.panel2, size: 18 }, () => { UI.sound = !UI.sound; G.save.sound = UI.sound; G.persist(); SFX.tap(); });
    btn(c, 'reset', 278, 524, 172, 52, G.confirmReset ? '再撳一次確認' : '重置存檔', { color: G.confirmReset ? '#c93b3b' : COL.panel2, size: 18 }, () => { if (G.confirmReset) { G.resetSave(); } else { G.confirmReset = true; setTimeout(() => { G.confirmReset = false; }, 3000); } });
    txt(c, '彩帶 ' + G.save.ribbons + '・通關 ' + [1, 2, 3].filter(i => done[i]).length + '/3・已跑 ' + G.save.races + ' 場', W / 2, 720, { size: 16, align: 'center', color: '#e8d9a8' });
    txt(c, '原型版本（MVP）・所有美術為原創向量圖形', W / 2, 930, { size: 12, align: 'center', color: 'rgba(255,255,255,0.45)' });
  }
  function drawHowto(c, G) {
    c.fillStyle = COL.bg; c.fillRect(0, 0, W, H);
    txt(c, '玩法說明', 20, 30, { size: 28, weight: '800' });
    const lines = [
      ['目標', '1000 米接力賽，分 5 段（每段 200 米），每段一種地形。先過終點者勝。'],
      ['自動跑', '你唔使控制跑動，只做場邊決策：幾時換人、幾時放技能。'],
      ['地形適性', '每隻野靈對每種地形有 4 級適性：陌路 ×0.65／識路 ×0.90／熟路 ×1.00／乘風 ×1.12。揀啱地形差距好大。'],
      ['換人', '點後備頭像即換。現役會先「交棒減速」，新人再「入場加速」1.5 秒，換人有 4 秒冷卻，太頻密必虧。後備每秒回 0.5 耐力。'],
      ['耐力與氣勢', '耐力見底氣勢會跌（最低 ×0.7）。耗耐力：苔坡 1.6／碎礫 2.0／淺灘 2.4／霜面 2.0／懸橋 2.8 每秒。'],
      ['技能', '每隻野靈每場只可用一次：疾風衝（加速）、絆草（拖慢對手）、回氣（回耐力）、風罩（免疫對手技能）。交棒／入場期間唔可放。'],
      ['追趕', '落後一方會有小幅補正（最多 +8%），領先方唔受影響。'],
      ['養成', '每回合 3 個行動：餵食、訓練、休息。賽後得經驗升級，再挑戰下一關。']
    ];
    let y = 70;
    lines.forEach(l => { txt(c, l[0], 24, y + 4, { size: 17, color: COL.gold, weight: '800' }); y = wrap(c, l[1], 24, y + 30, W - 48, 22, { size: 15, color: COL.text, weight: '500' }) + 10; });
    btn(c, 'back', 20, 876, W - 40, 60, '返回', { color: COL.btn, size: 22 }, () => G.go('menu'));
  }

  // ---------- 主繪製／輸入 ----------
  UI.draw = function (G) {
    const c = UI.ctx;
    UI.hits = [];
    c.setTransform(UI.scale * UI.dpr, 0, 0, UI.scale * UI.dpr, 0, 0);
    c.clearRect(0, 0, W, H);
    ({ menu: drawMenu, howto: drawHowto, train: drawTrain, team: drawTeam, race: drawRace, result: drawResult })[G.scene](c, G);
    // 浮動提示
    G.toasts = G.toasts.filter(tt => UI.t - tt.t0 < 1.6);
    G.toasts.forEach(tt => { const a = 1 - (UI.t - tt.t0) / 1.6; c.globalAlpha = Math.max(0, Math.min(1, a * 2)); txt(c, tt.text, W / 2, tt.y - (UI.t - tt.t0) * 24, { size: 22, align: 'center', color: tt.color || COL.gold, weight: '800' }); c.globalAlpha = 1; });
  };
  UI.resize = function () {
    const sc = Math.min(window.innerWidth / W, window.innerHeight / H);
    UI.scale = sc; UI.dpr = Math.min(window.devicePixelRatio || 1, 3);
    const cv = UI.canvas;
    cv.style.width = Math.floor(W * sc) + 'px'; cv.style.height = Math.floor(H * sc) + 'px';
    cv.width = Math.floor(W * sc * UI.dpr); cv.height = Math.floor(H * sc * UI.dpr);
  };
  function toLogical(e) {
    const r = UI.canvas.getBoundingClientRect();
    return { x: (e.clientX - r.left) / r.width * W, y: (e.clientY - r.top) / r.height * H };
  }
  function findHit(p) {
    for (let i = UI.hits.length - 1; i >= 0; i--) { const h = UI.hits[i]; if (p.x >= h.x && p.x <= h.x + h.w && p.y >= h.y && p.y <= h.y + h.h) return h; }
    return null;
  }
  UI.init = function (canvas, G) {
    UI.canvas = canvas; UI.ctx = canvas.getContext('2d'); UI.G = G;
    UI.resize(); window.addEventListener('resize', UI.resize);
    canvas.addEventListener('pointerdown', e => { e.preventDefault(); UI.down = findHit(toLogical(e)); });
    canvas.addEventListener('pointerup', e => { e.preventDefault(); const h = findHit(toLogical(e)); const d = UI.down; UI.down = null; if (h && d && h.id === d.id) h.cb(); });
    canvas.addEventListener('pointercancel', () => { UI.down = null; });
    canvas.addEventListener('contextmenu', e => e.preventDefault());
  };
  UI.drawCreature = drawCreature;
  g.WR.UI = UI;
})(window);
