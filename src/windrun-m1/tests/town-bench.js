/* town-lab 量幀時：BASE=http://localhost:8131/ node tests/town-bench.js
   headless 桌面 Chrome（軟件渲染，SwiftShader），唔係真 Android／iOS。方法：不受 vsync 限制連續渲染 240 幀（先熱身 30），每幀 getImageData flush。
   輸出 tests/town-bench-result.json */
const { chromium } = require('playwright-core'); const fs = require('fs'), path = require('path');
(async () => {
  const base = process.env.BASE || 'http://localhost:8131/';
  const browser = await chromium.launch({ executablePath: '/usr/bin/google-chrome', args: ['--no-sandbox'] });
  const os = require('os'); const R = { env: { chrome: browser.version(), cpus: os.cpus().length + 'x ' + os.cpus()[0].model, note: 'headless 桌面 Chrome（軟件渲染）；非真機', node: process.version }, runs: [] };
  const sets = [{ name: 'phone390x844@dpr1', w: 390, h: 844, dpr: 1 }, { name: 'phone390x844@dpr2', w: 390, h: 844, dpr: 2 }, { name: 'desktop1280x720@dpr1', w: 1280, h: 720, dpr: 1 }];
  const variants = [];
  for (const q of ['off', 'low', 'mid', 'high']) for (const chunk of [1, 0]) variants.push({ q, chunk });
  variants.push({ q: 'high', chunk: 1, extra: 'dof=0', label: 'high−dof' }, { q: 'high', chunk: 1, extra: 'light=baked&dof=0', label: 'high→baked light，無 dof' });
  for (const set of sets) {
    const ctx = await browser.newContext({ viewport: { width: set.w, height: set.h }, deviceScaleFactor: set.dpr });
    for (const v of variants) {
      const p = await ctx.newPage(); const qs = `bench=1&hud=0&q=${v.q}&chunk=${v.chunk}&dpr=${set.dpr}&tod=night` + (v.extra ? '&' + v.extra : '');
      await p.goto(base + 'town-lab.html?' + qs); await p.waitForFunction(() => window.__townReady || window.__townErr, null, { timeout: 60000 });
      const r = await p.evaluate(() => { const T = window.__town; const b = T.bench({ frames: 240, warm: 30 }); return { b, tilesDrawn: T.stats.tilesDrawn, chunkMs: T.stats.chunkMs, chunkPx: T.stats.chunkPx, mapLoadMs: T.S.mapLoadMs, W: T.S.W, H: T.S.H, cfg: T.cfg() }; });
      R.runs.push({ set: set.name, label: v.label || v.q + (v.chunk ? '' : ' 無chunk'), q: v.q, chunk: v.chunk, ...r }); await p.close();
      console.log(set.name.padEnd(22), (v.label || v.q).padEnd(24), 'chunk', v.chunk, 'avg', r.b.avg.toFixed(2), 'p95', r.b.p95.toFixed(2), 'max', r.b.max.toFixed(1));
    }
    await ctx.close();
  }
  // A*、載入、chunk 預渲染、記憶體（一次）
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 1 }); const p = await ctx.newPage(); await p.goto(base + 'town-lab.html?bench=1&hud=0&q=high'); await p.waitForFunction(() => window.__townReady);
  R.astar = await p.evaluate(() => { const T = window.__town; const o = {}; o.town = T.astarBench(500); T.enter('route_fernshade'); o.route = T.astarBench(500); T.enter('town_morningmoss'); return o; });
  R.load = await p.evaluate(() => { const T = window.__town, t0 = performance.now(); T.enter('town_morningmoss'); const t1 = performance.now() - t0; const t2 = performance.now(); T.enter('route_fernshade'); return { enterTownMs: t1, enterRouteMs: performance.now() - t2, chunkMsTown: null }; });
  R.load.assetsMs = await p.evaluate(async () => { const t0 = performance.now(); await WR.Town.load('art/town/'); return performance.now() - t0; });
  R.mem = await p.evaluate(() => { const T = window.__town; T.enter('town_morningmoss'); return { chunkPx: T.stats.chunkPx, chunkMB: T.stats.chunkPx * 4 / 1048576, bakedLightPx: T.M.baked.width * T.M.baked.height, bakedLightMB: T.M.baked.width * T.M.baked.height * 4 / 1048576, tilesetMB: 256 * 48 * 4 / 1048576 }; });
  const files = fs.readdirSync(path.join(__dirname, '../art/town/props')).concat(fs.readdirSync(path.join(__dirname, '../art/town')).filter(f => /\.(png|json)$/.test(f)));
  R.diskKB = {}; for (const f of fs.readdirSync(path.join(__dirname, '../art/town'))) { const fp = path.join(__dirname, '../art/town', f); if (fs.statSync(fp).isFile()) R.diskKB[f] = +(fs.statSync(fp).size / 1024).toFixed(1); }
  fs.writeFileSync(path.join(__dirname, 'town-bench-result.json'), JSON.stringify(R, null, 1)); console.log(JSON.stringify({ astar: R.astar, load: R.load, mem: R.mem }, null, 1));
  await browser.close();
})();
