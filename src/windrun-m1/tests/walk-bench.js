/* walk.html（batch2 晨苔鎮＋NPC＋對白頭像 UI）逐幀量度：BASE=http://localhost:8131/ node tests/walk-bench.js
   headless 桌面 Chrome（軟件光柵），非真機。update＋render＋getImageData(1px) 同步成本；240 幀（暖機 30）；路線＝世界內往返。 */
const { chromium } = require('playwright-core'); const fs = require('fs'), path = require('path');
const base = process.env.BASE || 'http://localhost:8131/';
(async () => {
  const browser = await chromium.launch({ executablePath: '/usr/bin/google-chrome', args: ['--no-sandbox'] }); const R = { env: { note: 'headless, not a real device（桌面 Chrome 軟件光柵）', date: new Date().toISOString(), chrome: browser.version() }, runs: [] };
  for (const set of [{ name: 'phone 390×844 dpr2', w: 390, h: 844, dpr: 2 }, { name: 'phone 390×844 dpr1', w: 390, h: 844, dpr: 1 }, { name: 'desktop 960×540 dpr1', w: 960, h: 540, dpr: 1 }]) {
    for (const tod of ['day', 'night']) {
      const ctx = await browser.newContext({ viewport: { width: set.w, height: set.h }, deviceScaleFactor: set.dpr, hasTouch: true }); const p = await ctx.newPage();
      await p.goto(base + `walk.html?new=1&slot=bench&cps=9999&tod=${tod}`); await p.waitForFunction(() => window.__walkReady || window.__walkErr, null, { timeout: 60000 });
      await p.evaluate(() => window.__adv.UI.skipAll()); await p.waitForTimeout(300);
      const r = await p.evaluate(() => { const W = window.__world; const out = []; for (let k = 0; k < 3; k++) out.push(W.bench({ frames: 240, warm: 30 })); return out; });
      const best = r.slice().sort((a, b) => a.avg - b.avg)[1]; R.runs.push({ set: set.name, tod, runs: r, median: best });
      console.log(set.name.padEnd(22), tod.padEnd(6), 'avg', r.map(x => x.avg.toFixed(2)).join('/'), 'p95', r.map(x => x.p95.toFixed(2)).join('/'), 'max', r.map(x => x.max.toFixed(1)).join('/')); await ctx.close();
    }
  }
  fs.writeFileSync(path.join(__dirname, 'walk-bench-result.json'), JSON.stringify(R, null, 1)); await browser.close();
})();
