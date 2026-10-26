/* fx.js — HD-2D 後處理實驗（只供 fx-lab.html；唔影響 index.html 遊戲）。
   純 Canvas2D：分層視差（遠／中／跑道／前景）＋低解析度模糊層做景深／bloom／tilt-shift＋預烘焙暈影。
   畫質檔：off（只有視差，無後處理）｜low（預烘焙模糊＋加色光暈貼圖）｜mid（1/4 解析度前景＋自發光緩衝 bloom＋邊緣 tilt-shift）｜high（金字塔模糊＋3 層 bloom＋體積光＋live 遠景景深）。
   全部原創向量／程序繪圖，無外部素材。座標＝邏輯 390×844（直向手機），內部按 dpr 放大。 */
(function (g) {
  'use strict';
  const LW = 390, LH = 844;
  const QUALITIES = ['off', 'low', 'mid', 'high'];
  const TWO_PI = Math.PI * 2;
  function hash(n) { const s = Math.sin(n * 127.1 + 311.7) * 43758.5453; return s - Math.floor(s); }
  function mod(a, b) { return ((a % b) + b) % b; }

  // ===== 像素精靈（ASCII → 烘焙成細畫布，整數倍放大、唔插值）=====
  const SPRITE_MAP = [
    '....GGGGGG....',
    '..GGgGGGGGGG..',
    '.GGGgGGGGgGGG.',
    'GGGGGGGGGGGGGG',
    'GGGWWGGGGWWGGG',
    'GGGWKGGGGWKGGG',
    'GGGGGGGGGGGGGG',
    'GGGGGGDDGGGGGG',
    '.GGGGGGGGGGGG.',
    '..GGGGGGGGGG..'
  ];
  const FEET = [['..DD......DD..', '.DDD......DDD.'], ['...DD....DD...', '..DDD....DDD..']];
  function bakeSprite(mk, pal, frame) {
    const rows = SPRITE_MAP.concat(FEET[frame]);
    const c = mk(14, rows.length), x = c.getContext('2d');
    rows.forEach((r, j) => { for (let i = 0; i < 14; i++) { const ch = r[i]; if (ch === '.') continue; x.fillStyle = pal[ch]; x.fillRect(i, j, 1, 1); } });
    return c;
  }
  const PAL_A = { G: '#6cc25a', g: '#9be58a', D: '#2f6e2a', W: '#ffffff', K: '#14202e' };
  const PAL_B = { G: '#4aa9e8', g: '#85cdf7', D: '#1d5f94', W: '#ffffff', K: '#14202e' };

  function create(canvas, opts) {
    opts = opts || {};
    const dpr = opts.dpr || 1, RW = Math.round(LW * dpr), RH = Math.round(LH * dpr);
    canvas.width = RW; canvas.height = RH;
    const ctx = canvas.getContext('2d', { alpha: false, willReadFrequently: !!opts.willRead });
    const fx = { quality: 'mid', dpr, RW, RH, stats: { px: 0, passes: 0, texBytes: 0 }, canvas };
    let texBytes = 0;
    function mk(w, h) { const c = document.createElement('canvas'); c.width = Math.max(1, Math.round(w)); c.height = Math.max(1, Math.round(h)); texBytes += c.width * c.height * 4; return c; }
    // 以邏輯座標繪畫嘅低解析度畫布：k＝縮細倍數
    function lowCanvas(k, lw, lh) {
      const c = mk(lw * dpr / k, lh * dpr / k), x = c.getContext('2d');
      x.setTransform(c.width / lw, 0, 0, c.height / lh, 0, 0); return { c, x, k };
    }
    function smooth(x, on) { x.imageSmoothingEnabled = on; if (on) x.imageSmoothingQuality = 'high'; }
    const st = fx.stats;
    function pass(wL, hL) { st.px += (wL * hL) / (LW * LH); st.passes++; }

    // ---- 預烘焙資源 ----
    const spr = [[bakeSprite(mk, PAL_A, 0), bakeSprite(mk, PAL_A, 1)], [bakeSprite(mk, PAL_B, 0), bakeSprite(mk, PAL_B, 1)]];
    // 光暈貼圖（徑向漸層）：暖／冷
    function bakeGlow(r, g0, g1) {
      const c = mk(128, 128), x = c.getContext('2d'), gr = x.createRadialGradient(64, 64, 0, 64, 64, 64);
      gr.addColorStop(0, g0); gr.addColorStop(0.35, g1); gr.addColorStop(1, 'rgba(0,0,0,0)');
      x.fillStyle = gr; x.fillRect(0, 0, 128, 128); return c;
    }
    const glowWarm = bakeGlow(64, 'rgba(255,226,150,1)', 'rgba(255,170,70,0.35)');
    const glowCool = bakeGlow(64, 'rgba(190,235,255,1)', 'rgba(90,170,255,0.35)');
    const glowMoon = bakeGlow(64, 'rgba(255,248,224,1)', 'rgba(210,225,255,0.30)');
    // 暈影（1/4 解析度烘焙，放大使用）
    const vig = (function () {
      const c = mk(LW / 4, LH / 4), x = c.getContext('2d');
      const gr = x.createRadialGradient(c.width / 2, c.height * 0.5, c.height * 0.28, c.width / 2, c.height * 0.5, c.height * 0.72);
      gr.addColorStop(0, 'rgba(6,10,24,0)'); gr.addColorStop(1, 'rgba(6,10,24,0.62)');
      x.fillStyle = gr; x.fillRect(0, 0, c.width, c.height); return c;
    })();

    // ---- 場景元件（邏輯座標）----
    const Y_FAR0 = 0, Y_FAR1 = 480, Y_TRACK0 = 470, Y_TRACK1 = 700, FG_Y = 650, FG_H = LH - FG_Y;
    const MTN_P = 780, MTN_Y = 190, MTN_H = 290;
    function drawSky(x) {
      const gr = x.createLinearGradient(0, 0, 0, Y_FAR1);
      gr.addColorStop(0, '#0f1a3a'); gr.addColorStop(0.55, '#27407a'); gr.addColorStop(0.85, '#b8728a'); gr.addColorStop(1, '#f0b878');
      x.fillStyle = gr; x.fillRect(0, 0, LW, Y_FAR1);
      x.fillStyle = 'rgba(255,255,255,0.8)';
      for (let i = 0; i < 70; i++) { const sx = hash(i) * LW, sy = hash(i + 50) * 260, s = hash(i + 9) > 0.85 ? 2 : 1; x.globalAlpha = 0.35 + hash(i + 3) * 0.55; x.fillRect(sx, sy, s, s); }
      x.globalAlpha = 1;
      // 月亮
      x.fillStyle = '#fff4d6'; x.beginPath(); x.arc(292, 118, 30, 0, TWO_PI); x.fill();
      x.fillStyle = 'rgba(200,190,160,0.5)'; x.beginPath(); x.arc(282, 112, 6, 0, TWO_PI); x.arc(300, 128, 4, 0, TWO_PI); x.arc(298, 106, 3, 0, TWO_PI); x.fill();
    }
    function ridge(x, ox, amp, base, ph, col, step) {
      x.fillStyle = col; x.beginPath(); x.moveTo(ox, MTN_H);
      for (let px = 0; px <= MTN_P + step; px += step) {
        const a = TWO_PI * px / MTN_P;
        const h = base + amp * (0.55 * Math.sin(a + ph) + 0.3 * Math.sin(3 * a + ph * 2) + 0.15 * Math.sin(7 * a + ph * 3));
        x.lineTo(ox + px, h);
      }
      x.lineTo(ox + MTN_P + step, MTN_H); x.closePath(); x.fill();
    }
    function drawMountainsTile(x, ox) { ridge(x, ox, 70, 120, 0.7, '#33497a', 6); ridge(x, ox, 55, 175, 2.1, '#26385f', 6); }
    // 遠景（只有天空＋山）— 連續絕對座標版（live 用）
    function drawFarLive(x, cam, t) {
      drawSky(x);
      // 緩慢漂移雲帶（令 live 遠景有動畫）
      x.fillStyle = 'rgba(255,200,170,0.16)';
      for (let i = 0; i < 4; i++) { const cx = mod(i * 190 - t * (6 + i * 2) - cam * 0.04, LW + 220) - 110, cy = 300 + i * 26; x.beginPath(); x.ellipse(cx, cy, 90, 9, 0, 0, TWO_PI); x.fill(); }
      const par = 0.08, off = -mod(cam * par, MTN_P);
      x.save(); x.translate(0, MTN_Y); drawMountainsTile(x, off); drawMountainsTile(x, off + MTN_P); x.restore();
    }
    function bakeFar(blurK) { // 靜態天空 + 山條，blurK=0 → 清晰；否則先縮細再放大＝烘焙模糊
      const sky = mk(LW * dpr, Y_FAR1 * dpr), sx = sky.getContext('2d'); sx.scale(dpr, dpr); drawSky(sx);
      const strip = mk(MTN_P * dpr, MTN_H * dpr), mx = strip.getContext('2d'); mx.scale(dpr, dpr); drawMountainsTile(mx, 0);
      if (!blurK) return { sky, strip };
      function blur(src, w, h) { // 烘焙一次：逐級對半縮細再逐級放大（比一步 4× 放大平滑得多）
        let cur = src; const made = [];
        for (let k = 2; k <= blurK; k *= 2) { const c = mk(w * dpr / k, h * dpr / k); const x = c.getContext('2d'); smooth(x, true); x.drawImage(cur, 0, 0, c.width, c.height); made.push(c); cur = c; }
        for (let k = blurK / 2; k >= 1; k /= 2) { const c = mk(w * dpr / k, h * dpr / k); const x = c.getContext('2d'); smooth(x, true); x.drawImage(cur, 0, 0, c.width, c.height); made.push(c); cur = c; }
        made.slice(0, -1).forEach(c => { texBytes -= c.width * c.height * 4; });
        return cur;
      }
      return { sky: blur(sky, LW, Y_FAR1), strip: blur(strip, MTN_P, MTN_H) };
    }
    function lanterns(cam) {
      const out = [], par = 0.32, sp = 250, first = Math.floor(cam * par / sp) - 1;
      for (let i = first; i < first + 4; i++) { const px = i * sp - cam * par + 40; if (px > -30 && px < LW + 30) out.push({ x: px, y: 438 }); }
      return out;
    }
    function drawMid(x, cam, t) {
      const par = 0.32;
      // 丘陵
      x.fillStyle = '#1a2a4a'; x.beginPath(); x.moveTo(0, 520);
      for (let px = 0; px <= LW + 8; px += 8) { const w = px + cam * par; x.lineTo(px, 462 + 18 * Math.sin(w * 0.011) + 9 * Math.sin(w * 0.031 + 1.3)); }
      x.lineTo(LW, 520); x.closePath(); x.fill();
      // 松樹剪影
      const sp = 38, first = Math.floor(cam * par / sp) - 1;
      for (let i = first; i < first + Math.ceil(LW / sp) + 3; i++) {
        const px = i * sp - cam * par, h = 34 + hash(i) * 40, by = 482 + hash(i + 7) * 6;
        x.fillStyle = hash(i + 2) > 0.5 ? '#12203a' : '#16284a';
        x.beginPath(); x.moveTo(px, by); x.lineTo(px + 14, by - h * 0.55); x.lineTo(px + 6, by - h * 0.55); x.lineTo(px + 12, by - h); x.lineTo(px, by - h * 0.72); x.lineTo(px - 12, by - h); x.lineTo(px - 6, by - h * 0.55); x.lineTo(px - 14, by - h * 0.55); x.closePath(); x.fill();
      }
      // 燈籠柱
      lanterns(cam).forEach(l => { x.fillStyle = '#0d1426'; x.fillRect(l.x - 2, l.y, 4, 52); x.fillStyle = '#ffdca0'; x.fillRect(l.x - 7, l.y - 12, 14, 16); x.fillStyle = '#ffb347'; x.fillRect(l.x - 5, l.y - 10, 10, 12); });
    }
    function laneY(i) { return [560, 646][i]; }
    function drawTrack(x, cam, t) {
      const gr = x.createLinearGradient(0, Y_TRACK0, 0, Y_TRACK1);
      gr.addColorStop(0, '#4a8a42'); gr.addColorStop(1, '#2a5a2e'); x.fillStyle = gr; x.fillRect(0, Y_TRACK0, LW, Y_TRACK1 - Y_TRACK0);
      x.fillStyle = '#86cd70'; x.fillRect(0, Y_TRACK0, LW, 3);
      // 苔蘚點（像素塊）
      for (let wx = Math.floor(cam / 7) * 7; wx < cam + LW + 8; wx += 7) {
        const px = Math.round(wx - cam), hh = hash(wx);
        const py = Y_TRACK0 + 8 + hash(wx + 9) * (Y_TRACK1 - Y_TRACK0 - 16);
        x.fillStyle = hh > 0.5 ? '#2f6e2a' : '#8fdc7a'; x.fillRect(px, Math.round(py), hh > 0.5 ? 6 : 3, hh > 0.5 ? 3 : 3);
      }
      x.setLineDash([10, 10]); x.strokeStyle = 'rgba(255,255,255,0.4)'; x.lineWidth = 2; x.beginPath(); x.moveTo(0, 603); x.lineTo(LW, 603); x.stroke(); x.setLineDash([]);
      // 地面暗角（跑道下緣）
      const sh = x.createLinearGradient(0, Y_TRACK1 - 30, 0, Y_TRACK1); sh.addColorStop(0, 'rgba(0,0,0,0)'); sh.addColorStop(1, 'rgba(0,0,0,0.35)'); x.fillStyle = sh; x.fillRect(0, Y_TRACK1 - 30, LW, 30);
      // 跑手
      const frame = Math.floor(t * 9) % 2;
      [[0, 150, 0], [1, 110, 1]].forEach(a => {
        const lane = a[0], rx = Math.round(a[1] + Math.sin(t * 0.7 + lane) * 8), bob = frame ? -3 : 0, ry = laneY(lane) - 30 + bob;
        x.fillStyle = 'rgba(0,0,0,0.3)'; x.beginPath(); x.ellipse(rx + 36, laneY(lane) + 28, 30, 6, 0, 0, TWO_PI); x.fill();
        smooth(x, false); x.drawImage(spr[a[2]][frame], rx, ry, 14 * 5, spr[a[2]][frame].height * 5); smooth(x, true);
      });
    }
    function fireflies(t) { const o = []; for (let i = 0; i < 9; i++) o.push({ x: 20 + hash(i * 3) * (LW - 40) + Math.sin(t * 0.8 + i * 2) * 14, y: 600 + hash(i * 3 + 1) * 190 + Math.cos(t * 0.6 + i) * 10, r: 2 + hash(i + 4) * 2, a: 0.5 + 0.5 * Math.sin(t * 2.2 + i * 1.7) }); return o; }
    // 前景（只佔下方條帶 y>=FG_Y）；x 已平移成條帶局部座標
    function drawFG(x, cam, t) {
      const par = 1.7, cs = cam * par;
      x.save(); x.translate(0, -FG_Y);
      x.fillStyle = '#0c2417';
      for (let i = -1; i < LW / 15 + 3; i++) {
        const wx = Math.floor(cs / 15) + i, px = wx * 15 - cs, hgt = 70 + hash(wx) * 80, sway = Math.sin(t * 1.4 + wx) * 6;
        x.beginPath(); x.moveTo(px - 10, LH); x.quadraticCurveTo(px + sway * 0.4, LH - hgt * 0.6, px + sway + 2, LH - hgt); x.quadraticCurveTo(px + 6, LH - hgt * 0.5, px + 12, LH); x.closePath(); x.fill();
      }
      x.fillStyle = '#12341f';
      for (let i = 0; i < 3; i++) { const wx = Math.floor(cs / 160) + i, px = wx * 160 - cs + hash(wx) * 40; x.beginPath(); x.ellipse(px, LH - 14, 58 + hash(wx + 3) * 30, 26, -0.25 + hash(wx + 5) * 0.5, 0, TWO_PI); x.fill(); }
      fireflies(t).forEach(f => { x.fillStyle = 'rgba(255,240,150,' + (0.4 + f.a * 0.6) + ')'; x.beginPath(); x.arc(f.x, f.y, f.r, 0, TWO_PI); x.fill(); });
      x.restore();
    }
    // 自發光點清單（bloom 來源）
    function emitters(cam, t, lite) {
      const e = [{ x: 292, y: 118, r: lite ? 80 : 120, s: glowMoon, a: 0.9 }];
      lanterns(cam).forEach(l => e.push({ x: l.x, y: l.y - 2, r: 74, s: glowWarm, a: 1 }));
      [[0, 150, glowWarm], [1, 110, glowCool]].forEach(a => e.push({ x: a[1] + 35, y: laneY(a[0]) - 6, r: 52 + 4 * Math.sin(t * 5 + a[0]), s: a[2], a: 0.28 }));
      if (!lite) fireflies(t).forEach(f => e.push({ x: f.x, y: f.y, r: 22 + f.r * 4, s: glowWarm, a: 0.5 + 0.5 * f.a }));
      return e;
    }
    function drawEm(x, e, areaCount) {
      x.globalCompositeOperation = 'lighter';
      e.forEach(m => { x.globalAlpha = m.a; x.drawImage(m.s, m.x - m.r, m.y - m.r, m.r * 2, m.r * 2); if (areaCount) pass(m.r * 2, m.r * 2); });
      x.globalAlpha = 1; x.globalCompositeOperation = 'source-over';
    }
    function drawRays(x, t) { // 體積光：月光斜光柱（加色、3 條）
      x.globalCompositeOperation = 'lighter';
      for (let i = 0; i < 3; i++) {
        const sway = Math.sin(t * 0.25 + i * 2) * 8, x0 = 260 + i * 26 + sway;
        const gr = x.createLinearGradient(x0, 120, x0 - 150, 560); gr.addColorStop(0, 'rgba(210,225,255,0.11)'); gr.addColorStop(1, 'rgba(210,225,255,0)');
        x.fillStyle = gr; x.beginPath(); x.moveTo(x0 - 10, 130); x.lineTo(x0 + 22, 130); x.lineTo(x0 - 110, 560); x.lineTo(x0 - 220, 560); x.closePath(); x.fill();
        pass(230, 430);
      }
      x.globalCompositeOperation = 'source-over';
    }
    function drawHUD(x, t, q) {
      x.fillStyle = 'rgba(10,18,32,0.78)'; x.fillRect(0, 0, LW, 52);
      x.fillStyle = '#f2f6fa'; x.font = '700 18px "Noto Sans CJK HK","Noto Sans HK",sans-serif'; x.textBaseline = 'middle'; x.fillText('苔坡入門賽・fx-lab', 14, 26);
      x.fillStyle = '#ffd166'; x.textAlign = 'right'; x.fillText(q.toUpperCase(), LW - 14, 26); x.textAlign = 'left';
      x.fillStyle = 'rgba(10,18,32,0.78)'; x.fillRect(0, LH - 44, LW, 44);
      x.fillStyle = '#9fb3c8'; x.font = '600 13px sans-serif'; x.fillText('HUD 喺後處理之後繪畫（唔受模糊／bloom 影響）', 14, LH - 22);
      pass(LW, 96);
    }

    // ---- 低解析度緩衝（按畫質建立）----
    const buf = {};
    function ensureBuffers(q) {
      if (buf.q === q) return;
      texBytes = 0; Object.keys(buf).forEach(k => delete buf[k]); buf.q = q;
      // 烘焙資源（精靈／光暈／暈影）
      texBytes += spr.reduce((s, p) => s + p[0].width * p[0].height * 8, 0) + 3 * 128 * 128 * 4 + vig.width * vig.height * 4;
      if (q === 'off') buf.far = bakeFar(0);
      if (q === 'low' || q === 'mid') buf.far = bakeFar(4);
      if (q === 'low' || q === 'mid') buf.fg = lowCanvas(4, LW, FG_H);
      if (q === 'high') { buf.far1 = lowCanvas(2, LW, Y_FAR1); buf.far2 = lowCanvas(4, LW, Y_FAR1); buf.fg1 = lowCanvas(2, LW, FG_H); buf.fg2 = lowCanvas(4, LW, FG_H); }
      if (q === 'mid') { buf.em = lowCanvas(4, LW, LH); buf.em2 = lowCanvas(8, LW, LH); }
      if (q === 'high') { buf.e1 = lowCanvas(2, LW, LH); buf.e2 = lowCanvas(4, LW, LH); buf.e3 = lowCanvas(8, LW, LH); buf.e4 = lowCanvas(16, LW, LH); }
      if (q === 'mid' || q === 'high') {
        const bandH = 150, k = q === 'mid' ? 4 : 2;
        buf.bandH = bandH;
        buf.tsT = [lowCanvas(k, LW, bandH), lowCanvas(k * 2, LW, bandH), lowCanvas(k * 4, LW, bandH)];
        buf.tsB = [lowCanvas(k, LW, bandH), lowCanvas(k * 2, LW, bandH), lowCanvas(k * 4, LW, bandH)];
        // 遮罩（上條：邊緣 1 → 內側 0；下條相反），烘焙喺小解析度
        buf.maskT = mk(buf.tsT[0].c.width, buf.tsT[0].c.height); buf.maskB = mk(buf.tsB[0].c.width, buf.tsB[0].c.height);
        [[buf.maskT, 0], [buf.maskB, 1]].forEach(a => { const c = a[0], x = c.getContext('2d'), gr = x.createLinearGradient(0, 0, 0, c.height); if (a[1] === 0) { gr.addColorStop(0, 'rgba(0,0,0,1)'); gr.addColorStop(1, 'rgba(0,0,0,0)'); } else { gr.addColorStop(0, 'rgba(0,0,0,0)'); gr.addColorStop(1, 'rgba(0,0,0,1)'); } x.fillStyle = gr; x.fillRect(0, 0, c.width, c.height); });
      }
      fx.stats.texBytes = texBytes;
    }
    function down(dst, src, sx, sy, sw, sh) { // src canvas 區域 → dst 全幅
      dst.x.save(); dst.x.setTransform(1, 0, 0, 1, 0, 0); smooth(dst.x, true); dst.x.clearRect(0, 0, dst.c.width, dst.c.height);
      dst.x.drawImage(src, sx, sy, sw, sh, 0, 0, dst.c.width, dst.c.height); dst.x.restore();
    }
    function upAdd(dst, src, alpha) { dst.x.save(); dst.x.setTransform(1, 0, 0, 1, 0, 0); smooth(dst.x, true); dst.x.globalCompositeOperation = 'lighter'; dst.x.globalAlpha = alpha; dst.x.drawImage(src.c, 0, 0, dst.c.width, dst.c.height); dst.x.restore(); }

    function tiltShift(q) {
      const bandH = buf.bandH, sets = [[buf.tsT, buf.maskT, 0], [buf.tsB, buf.maskB, LH - bandH]];
      sets.forEach(s => {
        const b = s[0], y0 = s[2];
        down(b[0], canvas, 0, Math.round(y0 * dpr), RW, Math.round(bandH * dpr)); pass(LW / b[0].k * 1, bandH / b[0].k);
        let top = b[0];
        if (q === 'high') { down(b[1], b[0].c, 0, 0, b[0].c.width, b[0].c.height); down(b[2], b[1].c, 0, 0, b[1].c.width, b[1].c.height); b[1].x.save(); b[1].x.setTransform(1, 0, 0, 1, 0, 0); smooth(b[1].x, true); b[1].x.globalAlpha = 0.65; b[1].x.drawImage(b[2].c, 0, 0, b[1].c.width, b[1].c.height); b[1].x.restore(); top = b[1]; pass(LW / b[1].k, bandH / b[1].k * 2); }
        top.x.save(); top.x.setTransform(1, 0, 0, 1, 0, 0); top.x.globalCompositeOperation = 'destination-in'; smooth(top.x, true);
        top.x.drawImage(s[1], 0, 0, top.c.width, top.c.height); top.x.restore(); pass(LW / top.k, bandH / top.k);
        ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0); smooth(ctx, true); ctx.drawImage(top.c, 0, Math.round(y0 * dpr), RW, Math.round(bandH * dpr)); ctx.restore(); pass(LW, bandH);
      });
    }

    fx.setQuality = function (q) { if (QUALITIES.indexOf(q) < 0) q = 'mid'; fx.quality = q; ensureBuffers(q); };
    fx.setQuality(opts.quality || 'mid');

    fx.render = function (t) {
      const q = fx.quality, cam = t * 110;
      st.px = 0; st.passes = 0;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0); smooth(ctx, true);
      // 1. 遠景
      if (q === 'off' || q === 'low' || q === 'mid') {
        ctx.drawImage(buf.far.sky, 0, 0, LW, Y_FAR1); pass(LW, Y_FAR1);
        const off = -mod(cam * 0.08, MTN_P);
        ctx.drawImage(buf.far.strip, off, MTN_Y, MTN_P, MTN_H); ctx.drawImage(buf.far.strip, off + MTN_P, MTN_Y, MTN_P, MTN_H); pass(LW, MTN_H);
      } else { // high：live 渲染遠景 → 1/2 → 1/4 金字塔模糊 → 放大
        buf.far1.x.clearRect(0, 0, LW, Y_FAR1); drawFarLive(buf.far1.x, cam, t); pass(LW / 2, Y_FAR1 / 2);
        down(buf.far2, buf.far1.c, 0, 0, buf.far1.c.width, buf.far1.c.height); pass(LW / 4, Y_FAR1 / 4);
        buf.far1.x.save(); buf.far1.x.setTransform(1, 0, 0, 1, 0, 0); smooth(buf.far1.x, true); buf.far1.x.globalAlpha = 0.7; buf.far1.x.drawImage(buf.far2.c, 0, 0, buf.far1.c.width, buf.far1.c.height); buf.far1.x.restore(); pass(LW / 2, Y_FAR1 / 2);
        ctx.drawImage(buf.far1.c, 0, 0, LW, Y_FAR1); pass(LW, Y_FAR1);
      }
      // 2. 中景、3. 跑道
      drawMid(ctx, cam, t); pass(LW, 80 + 60); pass(LW, 60);
      drawTrack(ctx, cam, t); pass(LW, Y_TRACK1 - Y_TRACK0);
      // 3b. 體積光（high）
      if (q === 'high') drawRays(ctx, t);
      // 4. 前景
      if (q === 'off') { ctx.save(); ctx.translate(0, FG_Y); drawFG(ctx, cam, t); ctx.restore(); pass(LW, FG_H); }
      else if (q === 'low' || q === 'mid') {
        buf.fg.x.clearRect(0, 0, LW, FG_H); drawFG(buf.fg.x, cam, t); pass(LW / 4, FG_H / 4);
        ctx.drawImage(buf.fg.c, 0, FG_Y, LW, FG_H); pass(LW, FG_H);
      } else {
        buf.fg1.x.clearRect(0, 0, LW, FG_H); drawFG(buf.fg1.x, cam, t); pass(LW / 2, FG_H / 2);
        down(buf.fg2, buf.fg1.c, 0, 0, buf.fg1.c.width, buf.fg1.c.height); pass(LW / 4, FG_H / 4);
        buf.fg1.x.save(); buf.fg1.x.setTransform(1, 0, 0, 1, 0, 0); smooth(buf.fg1.x, true); buf.fg1.x.globalAlpha = 0.7; buf.fg1.x.drawImage(buf.fg2.c, 0, 0, buf.fg1.c.width, buf.fg1.c.height); buf.fg1.x.restore(); pass(LW / 2, FG_H / 2);
        ctx.drawImage(buf.fg1.c, 0, FG_Y, LW, FG_H); pass(LW, FG_H);
      }
      // 5. bloom
      if (q === 'low') { drawEm(ctx, emitters(cam, t, true), true); } // 低檔：月亮縮細、唔畫螢火蟲光暈（省 fill）
      else if (q === 'mid') {
        const e = emitters(cam, t);
        buf.em.x.clearRect(0, 0, LW, LH); drawEm(buf.em.x, e, false); pass(LW / 4, LH / 4 * 0.4);
        down(buf.em2, buf.em.c, 0, 0, buf.em.c.width, buf.em.c.height); pass(LW / 8, LH / 8);
        upAdd(buf.em, buf.em2, 0.8); pass(LW / 4, LH / 4);
        ctx.globalCompositeOperation = 'lighter'; ctx.globalAlpha = 0.9; ctx.drawImage(buf.em.c, 0, 0, LW, LH); ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over'; pass(LW, LH);
      } else if (q === 'high') {
        const e = emitters(cam, t);
        buf.e1.x.clearRect(0, 0, LW, LH); drawEm(buf.e1.x, e, false); pass(LW / 2, LH / 2 * 0.4);
        down(buf.e2, buf.e1.c, 0, 0, buf.e1.c.width, buf.e1.c.height); down(buf.e3, buf.e2.c, 0, 0, buf.e2.c.width, buf.e2.c.height); down(buf.e4, buf.e3.c, 0, 0, buf.e3.c.width, buf.e3.c.height);
        pass(LW / 4, LH / 4); pass(LW / 8, LH / 8); pass(LW / 16, LH / 16);
        upAdd(buf.e3, buf.e4, 0.9); upAdd(buf.e2, buf.e3, 0.8); upAdd(buf.e1, buf.e2, 0.7); pass(LW / 8, LH / 8); pass(LW / 4, LH / 4); pass(LW / 2, LH / 2);
        ctx.globalCompositeOperation = 'lighter'; ctx.globalAlpha = 0.95; ctx.drawImage(buf.e1.c, 0, 0, LW, LH); ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over'; pass(LW, LH);
      }
      // 6. tilt-shift（讀取已含 bloom 嘅畫面）
      if (q === 'mid' || q === 'high') tiltShift(q);
      // 7. 暈影
      if (q !== 'off') { ctx.drawImage(vig, 0, 0, LW, LH); pass(LW, LH); }
      // 8. HUD（後處理之後）
      drawHUD(ctx, t, q);
    };
    // 強制 GPU／光柵同步（量度用）：讀回 1×1
    fx.flush = function () { ctx.getImageData(0, 0, 1, 1); };

    // 逐檔量度：連續跑 N 幀（唔經 rAF，無 vsync 上限），每幀後 flush
    fx.bench = function (frames, warm) {
      frames = frames || 240; warm = warm == null ? 30 : warm;
      const ms = [];
      for (let i = 0; i < frames + warm; i++) {
        const t0 = performance.now(); fx.render(2 + i / 60); fx.flush(); const d = performance.now() - t0;
        if (i >= warm) ms.push(d);
      }
      ms.sort((a, b) => a - b);
      const sum = ms.reduce((a, b) => a + b, 0);
      return { quality: fx.quality, frames: ms.length, avg: sum / ms.length, p50: ms[ms.length >> 1], p95: ms[Math.floor(ms.length * 0.95)], max: ms[ms.length - 1], px: st.px, passes: st.passes, texMB: st.texBytes / 1048576 };
    };
    return fx;
  }

  // 校準：量度本機「1 次全螢幕 pass」嘅成本（normal／additive／縮細），供 fillRatio 估算 frame ms
  function calibrate(dpr, n) {
    n = n || 60;
    const RW = Math.round(LW * dpr), RH = Math.round(LH * dpr);
    const a = document.createElement('canvas'), b = document.createElement('canvas');
    a.width = b.width = RW; a.height = b.height = RH;
    const ax = a.getContext('2d', { alpha: false, willReadFrequently: true }), bx = b.getContext('2d', { alpha: false, willReadFrequently: true });
    ax.fillStyle = '#446'; ax.fillRect(0, 0, RW, RH); bx.fillStyle = '#242'; bx.fillRect(0, 0, RW, RH);
    function timeIt(fn) { for (let i = 0; i < 8; i++) { fn(); bx.getImageData(0, 0, 1, 1); } const t0 = performance.now(); for (let i = 0; i < n; i++) { fn(); bx.getImageData(0, 0, 1, 1); } return (performance.now() - t0) / n; }
    const normal = timeIt(() => { bx.globalCompositeOperation = 'source-over'; bx.globalAlpha = 0.5; bx.drawImage(a, 0, 0); bx.globalAlpha = 1; });
    const add = timeIt(() => { bx.globalCompositeOperation = 'lighter'; bx.drawImage(a, 0, 0); bx.globalCompositeOperation = 'source-over'; });
    const small = document.createElement('canvas'); small.width = RW / 4; small.height = RH / 4; const sx = small.getContext('2d');
    const downq = timeIt(() => { sx.drawImage(a, 0, 0, small.width, small.height); bx.drawImage(small, 0, 0, RW, RH); });
    return { dpr, msPerScreenPassNormal: normal, msPerScreenPassAdditive: add, msDownUp4: downq };
  }

  g.WR = g.WR || {};
  g.WR.Fx = { create, calibrate, QUALITIES, LW, LH };
})(typeof globalThis !== 'undefined' ? globalThis : this);
