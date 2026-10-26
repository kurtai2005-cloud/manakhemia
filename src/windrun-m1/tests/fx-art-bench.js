/* fx-lab ?art=1 量度＋截圖：BASE=http://localhost:8131/ node tests/fx-art-bench.js
   headless 桌面 Chrome（SwiftShader／軟件光柵），視窗 960×540；數字只作相對比較，**非真機**。輸出 tests/fx-art-bench-result.json、screens/fx-art-*.png */
const { chromium } = require('playwright-core');
const path = require('path'), fs = require('fs');
(async () => {
  const base = process.env.BASE || 'http://localhost:8131/', out = path.join(__dirname, '../screens') + '/';
  const browser = await chromium.launch({ executablePath: '/usr/bin/google-chrome', args: ['--no-sandbox'] });
  const errs = [], os = require('os');
  const result = { env: { chrome: browser.version(), cpus: os.cpus().length + 'x ' + os.cpus()[0].model, note: 'headless 桌面 Chrome（軟件光柵）；非真 Android／非真機', date: new Date().toISOString() }, bench: {}, memory: {} };
  const hook = p => { p.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') errs.push(m.type() + ': ' + m.text()); }); p.on('pageerror', e => errs.push('pageerror: ' + e.message)); };
  for (const dpr of [1, 2]) {
    const ctx = await browser.newContext({ viewport: { width: 960, height: 540 }, deviceScaleFactor: dpr }), page = await ctx.newPage(); hook(page);
    await page.goto(base + 'fx-lab.html?art=1&bench=1&hud=0&dpr=' + dpr);
    await page.waitForFunction(() => window.__fxBench || window.__fxError, null, { timeout: 240000 });
    const r = await page.evaluate(() => window.__fxBench); if (!r) throw new Error('bench failed ' + await page.evaluate(() => window.__fxError));
    result.bench['dpr' + dpr] = r;
    if (dpr === 1) result.env.webgl = await page.evaluate(() => { const g = document.createElement('canvas').getContext('webgl'); if (!g) return 'no webgl'; const e = g.getExtension('WEBGL_debug_renderer_info'); return e ? g.getParameter(e.UNMASKED_RENDERER_WEBGL) : 'n/a'; });
    await ctx.close();
  }
  // 截圖＋專題量度（dpr1）
  const ctx = await browser.newContext({ viewport: { width: 960, height: 540 }, deviceScaleFactor: 1 });
  const shot = async (name, qs, opt) => { const p = await ctx.newPage(); hook(p); await p.goto(base + 'fx-lab.html?art=1&hud=0&' + qs); await p.waitForFunction(() => window.__fxReady || window.__fxError, null, { timeout: 60000 }); await p.waitForTimeout(400); await p.screenshot(Object.assign({ path: out + name + '.png' }, opt || {})); await p.close(); };
  for (const q of ['off', 'low', 'mid', 'high']) await shot('fx-art-' + q + '-night', 'fx=' + q + '&tod=night&t=7.3');
  for (const td of ['day', 'dusk']) await shot('fx-art-high-' + td, 'fx=high&tod=' + td + '&t=7.3');
  await shot('fx-art-shreds', 'fx=high&tod=night&t=7.0', { clip: { x: 160, y: 340, width: 360, height: 180 } });
  // cat pivot：spec vs fix，畫地面基準線 y=470（＝track.y 320＋跑道線 150）
  for (const pv of ['spec', 'fix']) { const p = await ctx.newPage(); hook(p); await p.goto(base + 'fx-lab.html?art=1&hud=0&fx=low&pivot=' + pv + '&t=7.2'); await p.waitForFunction(() => window.__fxReady); await p.evaluate(() => { const d = document.createElement('div'); d.style.cssText = 'position:fixed;left:0;right:0;top:470px;height:1px;background:#ff2bd6;z-index:9'; document.body.appendChild(d); }); await p.screenshot({ path: out + 'fx-art-pivot-' + pv + '.png', clip: { x: 200, y: 380, width: 280, height: 110 } }); await p.close(); }
  // 專題量度（moire／sigma／白化）
  const mp = await ctx.newPage(); hook(mp); await mp.goto(base + 'fx-lab.html?art=1&moire=1&hud=0'); await mp.waitForFunction(() => window.__moire, null, { timeout: 120000 });
  result.moire = await mp.evaluate(() => window.__moire);
  result.pyramidSigma = await mp.evaluate(() => { const F = WR.FxArt, o = {}; o.quarter_only = +F.pyramidSigma('quarter').toFixed(2); o.half_only = +F.pyramidSigma('half').toFixed(2); [0.3, 0.5, 0.7, 1.0].forEach(a => { o['half+quarter_a' + a] = +F.pyramidSigma('half+quarter', a).toFixed(2); }); return o; });
  result.catWhite = await mp.evaluate(async () => {
    const res = {};
    for (const q of ['mid', 'high']) { const A = await WR.FxArt.load({ quality: q }); for (const cb of [1, 0.7, 0.4, 0]) { const c = document.createElement('canvas'), fx = WR.FxArt.create(c, A, { dpr: 1, willRead: true, params: { catBloom: cb, shreds: false } }); fx.render(7.3); const d = c.getContext('2d').getImageData(236, 340, 170, 120).data; let n = 0, nw = 0, ml = 0; for (let i = 0; i < d.length; i += 4) { const lum = 0.3 * d[i] + 0.59 * d[i + 1] + 0.11 * d[i + 2]; ml += lum; n++; if (Math.min(d[i], d[i + 1], d[i + 2]) > 200) nw++; } res[q + '_catBloom' + cb] = { meanLum: +(ml / n).toFixed(1), nearWhitePct: +(100 * nw / n).toFixed(2) }; } }
    return res;
  });
  await ctx.close(); await browser.close();
  fs.writeFileSync(path.join(__dirname, 'fx-art-bench-result.json'), JSON.stringify(result, null, 2));
  console.log(JSON.stringify(result, null, 2)); console.log(errs.length ? 'CONSOLE:\n' + errs.join('\n') : 'NO CONSOLE ERRORS / WARNINGS');
})();
