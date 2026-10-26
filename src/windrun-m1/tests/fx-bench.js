/* fx-lab 量度＋截圖：BASE=http://localhost:8131/ node tests/fx-bench.js
   Playwright-core＋系統 Chrome headless，視窗 390×844。注意：headless 桌面 Chrome，唔係真 Android。 */
const { chromium } = require('playwright-core');
const path = require('path'), fs = require('fs');
(async () => {
  const base = process.env.BASE || 'http://localhost:8131/';
  const out = path.join(__dirname, '../screens') + '/';
  const browser = await chromium.launch({ executablePath: '/usr/bin/google-chrome', args: ['--no-sandbox'] });
  const errs = [];
  const result = { env: { chrome: browser.version(), cpus: require('os').cpus().length + 'x ' + require('os').cpus()[0].model, note: 'headless desktop Chrome；非真 Android' }, runs: {} };
  for (const dpr of [1, 2]) {
    const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: dpr });
    const page = await ctx.newPage();
    page.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') errs.push(m.type() + ': ' + m.text()); });
    page.on('pageerror', e => errs.push('pageerror: ' + e.message));
    await page.goto(base + 'fx-lab.html?bench=1&hud=0&dpr=' + dpr);
    await page.waitForFunction(() => window.__fxBench, null, { timeout: 180000 });
    if (dpr === 1) result.env.webgl = await page.evaluate(() => { const g = document.createElement('canvas').getContext('webgl'); if (!g) return 'no webgl'; const e = g.getExtension('WEBGL_debug_renderer_info'); return e ? g.getParameter(e.UNMASKED_RENDERER_WEBGL) : 'n/a'; });
    result.runs['dpr' + dpr] = await page.evaluate(() => window.__fxBench);
    // rAF fps（會被 vsync 限制，只作參考）
    if (dpr === 1) {
      result.raf = {};
      for (const q of ['off', 'low', 'mid', 'high']) {
        const p2 = await ctx.newPage();
        await p2.goto(base + 'fx-lab.html?hud=0&fx=' + q + '&dpr=1');
        await p2.waitForTimeout(500);
        result.raf[q] = await p2.evaluate(() => new Promise(res => { let n = 0, t0 = performance.now(); (function f() { n++; if (performance.now() - t0 > 3000) res(+(n / ((performance.now() - t0) / 1000)).toFixed(1)); else requestAnimationFrame(f); })(); }));
        await p2.close();
      }
    }
    // 截圖（凍結時間，同一幀）
    if (dpr === 1) for (const q of ['off', 'low', 'mid', 'high']) {
      const p3 = await ctx.newPage();
      await p3.goto(base + 'fx-lab.html?fx=' + q + '&t=7.3&dpr=1&hud=0');
      await p3.waitForTimeout(700);
      await p3.screenshot({ path: out + 'fx-' + q + '.png' });
      await p3.close();
    }
    await ctx.close();
  }
  await browser.close();
  fs.writeFileSync(path.join(__dirname, 'fx-bench-result.json'), JSON.stringify(result, null, 2));
  console.log(JSON.stringify(result, null, 2));
  console.log(errs.length ? 'CONSOLE:\n' + errs.join('\n') : 'NO CONSOLE ERRORS / WARNINGS');
})();
