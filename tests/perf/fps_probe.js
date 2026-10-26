#!/usr/bin/env node
/* fps_probe.js — 風野競走 HTML5 基準 fps／frame time／記憶體／載入 量度（Playwright + Chrome DevTools Protocol）
 *
 * 用法：
 *   node fps_probe.js --url http://localhost:8000/ --tier mid [--stage 1] [--team mochi,gravelbadger] [--mul 1] [--runs 1] [--out out/fps-mid.json]
 *   --tier high|mid|low  ：以 CDP 限速 CPU 模擬檔位（high=1×、mid=4×、low=6×）；亦可用 --cpu <倍數> 自訂
 *   --viewport 390x844   ：預設手機直向；--dpr 2（預設）
 *   --chrome <path>      ：預設 /usr/bin/google-chrome（或 $CHROME_PATH）；用 playwright-core（$PW_PATH 或 npm 全域）
 *
 * 依賴遊戲暴露 window.__wr = { G, UI, Sim, Data }（遊程原型已有）；若冇，會 fallback 只量主頁 5 秒 idle。
 * 量度重點（對應 QA/perf-budget-wind-race.md）：
 *   avg fps、p50/p95/p99 frame time、1% low fps、>33.3 ms／>50 ms 長幀比例、UI.draw／G.tick 耗時、JS heap、載入時間、一場完賽時長（遊戲內秒）。
 * 注意：headless 預設用軟體繪圖，數值偏悲觀；CPU 限速只係「相對」模擬，真機 fps 一定要用真實 Android 裝置再驗（見預算文件第 5 節）。
 */
'use strict';
const fs = require('fs'), path = require('path');
function arg(n, d) { const i = process.argv.indexOf('--' + n); return i > 0 ? process.argv[i + 1] : d; }
function loadPW() {
  const c = [process.env.PW_PATH, '/workspace/tools/pw/node_modules/playwright-core', 'playwright-core', 'playwright'];
  for (const p of c) { if (!p) continue; try { return require(p); } catch (e) { /* next */ } }
  console.error('搵唔到 playwright-core：npm i -D playwright-core 或設定 PW_PATH'); process.exit(2);
}
const { chromium } = loadPW();
const URL = arg('url', 'http://localhost:8000/');
const TIER = arg('tier', 'mid');
const CPU = parseFloat(arg('cpu', { high: 1, mid: 4, low: 6 }[TIER] || 1));
const [VW, VH] = arg('viewport', '390x844').split('x').map(Number);
const DPR = parseFloat(arg('dpr', '2'));
const STAGE = parseInt(arg('stage', '1'), 10);
const TEAM = arg('team', 'mochi,gravelbadger').split(',');
const MUL = parseFloat(arg('mul', '1'));
const RUNS = parseInt(arg('runs', '1'), 10);
const OUT = arg('out', path.join(__dirname, 'out', 'fps-' + TIER + '.json'));
const BUDGET = { // 預算：見 QA/perf-budget-wind-race.md 第 1 節
  high: { fps: 58, p95: 20, longPct: 1, heapMB: 150 },
  mid: { fps: 55, p95: 22, longPct: 2, heapMB: 150 },
  low: { fps: 30, p95: 40, longPct: 5, heapMB: 100 },
}[TIER] || { fps: 30, p95: 40, longPct: 5, heapMB: 100 };

const pct = (a, p) => { if (!a.length) return NaN; const s = a.slice().sort((x, y) => x - y); return s[Math.min(s.length - 1, Math.floor(p / 100 * s.length))]; };
const mean = a => a.reduce((x, y) => x + y, 0) / Math.max(a.length, 1);

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROME_PATH || '/usr/bin/google-chrome', headless: true,
    args: ['--no-sandbox', '--enable-precise-memory-info', '--disable-background-timer-throttling', '--disable-renderer-backgrounding'] });
  const results = [];
  for (let r = 0; r < RUNS; r++) {
    const ctx = await browser.newContext({ viewport: { width: VW, height: VH }, deviceScaleFactor: DPR, hasTouch: true, isMobile: true });
    const page = await ctx.newPage();
    const cdp = await ctx.newCDPSession(page);
    await cdp.send('Emulation.setCPUThrottlingRate', { rate: CPU });
    const errs = [];
    page.on('pageerror', e => errs.push(e.message));
    page.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
    // 喺頁面載入前注入 frame time 取樣（rAF）
    await page.addInitScript(() => {
      window.__fp = { frames: [], t0: 0, on: false, draw: [], tick: [] };
      const loop = (now) => { const f = window.__fp; if (f.on) { if (f.last) f.frames.push(now - f.last); f.last = now; } requestAnimationFrame(loop); };
      requestAnimationFrame(loop);
    });
    const t0 = Date.now();
    await page.goto(URL, { waitUntil: 'load' });
    const nav = await page.evaluate(() => { const n = performance.getEntriesByType('navigation')[0]; return { dcl: n.domContentLoadedEventEnd, load: n.loadEventEnd, transferKB: Math.round(performance.getEntriesByType('resource').reduce((a, e) => a + (e.transferSize || 0), n.transferSize || 0) / 1024) }; });
    const hasWR = await page.evaluate(() => !!window.__wr);
    let gameSec = null, started = false;
    if (hasWR) {
      // 包裝 UI.draw／G.tick 取耗時
      await page.evaluate(() => {
        const { G, UI } = window.__wr, f = window.__fp;
        const d = UI.draw, k = G.tick;
        UI.draw = function (g) { const s = performance.now(); d.call(UI, g); f.draw.push(performance.now() - s); };
        G.tick = function (dt) { const s = performance.now(); k.call(G, dt); f.tick.push(performance.now() - s); };
      });
      started = await page.evaluate(({ stage, team, mul }) => {
        const { G } = window.__wr; G.stageSel = stage; G.teamPick = team; G.startRace();
        if (G.scene !== 'race') return false; G.race.mul = mul; window.__fp.on = true; return true;
      }, { stage: STAGE, team: TEAM, mul: MUL });
      if (started) {
        await page.waitForFunction(() => { const R = window.__wr.G.race; return R && R.sim.over; }, null, { timeout: 400000, polling: 500 });
        gameSec = await page.evaluate(() => window.__wr.G.race.sim.duration);
      }
    }
    if (!started) { await page.evaluate(() => { window.__fp.on = true; }); await page.waitForTimeout(5000); }
    const data = await page.evaluate(() => { const f = window.__fp; f.on = false; const m = performance.memory; return { frames: f.frames, draw: f.draw, tick: f.tick, heapMB: m ? m.usedJSHeapSize / 1048576 : null }; });
    const fr = data.frames.slice(3);                        // 去掉頭 3 幀（暖機）
    const sorted = fr.slice().sort((a, b) => b - a), worst1 = sorted.slice(0, Math.max(1, Math.floor(fr.length * 0.01)));
    const res = {
      tier: TIER, cpuThrottle: CPU, viewport: VW + 'x' + VH + '@' + DPR, started, url: URL, frames: fr.length,
      avgFps: +(1000 / mean(fr)).toFixed(1), p50ms: +pct(fr, 50).toFixed(1), p95ms: +pct(fr, 95).toFixed(1), p99ms: +pct(fr, 99).toFixed(1),
      low1pctFps: +(1000 / mean(worst1)).toFixed(1),
      over33pct: +(100 * fr.filter(x => x > 33.4).length / fr.length).toFixed(2), over50pct: +(100 * fr.filter(x => x > 50).length / fr.length).toFixed(2),
      drawAvgMs: +mean(data.draw).toFixed(2), drawP95Ms: +pct(data.draw, 95).toFixed(2), tickAvgMs: +mean(data.tick).toFixed(3),
      heapMB: data.heapMB && +data.heapMB.toFixed(1), domContentLoadedMs: Math.round(nav.dcl), loadMs: Math.round(nav.load), transferKB: nav.transferKB,
      raceGameSeconds: gameSec && +gameSec.toFixed(1), wallSeconds: +((Date.now() - t0) / 1000).toFixed(1), consoleErrors: errs.length,
    };
    res.pass = { fps: res.avgFps >= BUDGET.fps, p95: res.p95ms <= BUDGET.p95, longFrames: res.over33pct <= BUDGET.longPct, heap: res.heapMB == null || res.heapMB <= BUDGET.heapMB, raceLen: gameSec == null || gameSec <= 120, noErrors: errs.length === 0 };
    res.budget = BUDGET;
    results.push(res);
    await ctx.close();
  }
  await browser.close();
  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  fs.writeFileSync(OUT, JSON.stringify(results, null, 2));
  console.log(JSON.stringify(results, null, 2));
  process.exit(results.every(r => Object.values(r.pass).every(Boolean)) ? 0 : 1);
})().catch(e => { console.error(e); process.exit(2); });
