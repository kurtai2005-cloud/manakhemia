#!/usr/bin/env node
/* pet_fps_probe.js — 《微光小圃》fps／frame time 基準（Playwright + CDP CPU 限速）
 * 用法：node pet_fps_probe.js --url http://localhost:8125/index.html --tier mid --quality high|mid|low|off --seconds 20 [--hour 23] [--eval "<js 事前設定>"] [--auto 1] [--out out/petfps-<tier>-<q>.json]
 * 預設 ?debug=1（關閉自動降畫質，量真實 fps）；--auto 1 則唔加 debug，量自動降畫質行為（記錄畫質變化次數，防止來回跳）。
 * 檔位：high 1×／mid 4×／low 6×（相對限速，唔等於真機；真機驗收見 QA/pet-deepening-test-plan.md §5）。
 * 預算（提案）：high avg≥58 p95≤20ms；mid avg≥55 p95≤22ms；low avg≥30 p95≤40ms 且 >50ms 幀 ≤5%。
 */
'use strict';
const fs = require('fs'), path = require('path');
function arg(n, d) { const i = process.argv.indexOf('--' + n); return i > 0 ? process.argv[i + 1] : d; }
let chromium; for (const p of [process.env.PW_PATH, '/workspace/tools/pw/node_modules/playwright-core', 'playwright-core']) { try { if (p) { chromium = require(p).chromium; break; } } catch (e) {} }
const TIER = arg('tier', 'mid'), CPU = parseFloat(arg('cpu', { high: 1, mid: 4, low: 6 }[TIER] || 1)), Q = arg('quality', 'high'), SECS = parseFloat(arg('seconds', '20'));
const BASE = arg('url', 'http://localhost:8125/index.html'), AUTO = arg('auto', '0') === '1', HOUR = arg('hour', null), EVAL = arg('eval', null);
const OUT = arg('out', path.join(__dirname, 'out', `petfps-${TIER}-${Q}${AUTO ? '-auto' : ''}.json`));
const BUD = { high: [58, 20, 0.02], mid: [55, 22, 0.03], low: [30, 40, 0.05] }[TIER] || [30, 40, 0.05];
(async () => {
  const b = await chromium.launch({ executablePath: process.env.CHROME || '/usr/bin/google-chrome', args: ['--no-sandbox', '--enable-precise-memory-info'] });
  const ctx = await b.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, hasTouch: true });
  const page = await ctx.newPage(); const errs = []; page.on('pageerror', e => errs.push(e.message));
  const cdp = await ctx.newCDPSession(page);
  const qs = (AUTO ? '?q=' + Q : '?debug=1&q=' + Q) + (HOUR != null ? '&hour=' + HOUR : '');
  const t0 = Date.now(); await page.goto(BASE + qs); await page.evaluate(() => localStorage.clear()); await page.goto(BASE + qs);
  await page.waitForFunction(() => window.__glimmer && window.__glimmer.state, null, { timeout: 15000 }); const load = Date.now() - t0;
  await page.evaluate(() => { const G = window.__glimmer, s = G.state; if (s.stage === 'egg') { s.stage = 'sprout'; s.form = s.form || null; } });
  if (EVAL) await page.evaluate(EVAL);
  await cdp.send('Emulation.setCPUThrottlingRate', { rate: CPU }); await page.waitForTimeout(800);
  const r = await page.evaluate((secs) => new Promise(res => {
    const d = []; let last = performance.now(); const end = last + secs * 1000; const q0 = window.__glimmer.state.settings.quality; const qs = [q0];
    const heap0 = performance.memory ? performance.memory.usedJSHeapSize : 0;
    (function f(t) { d.push(t - last); last = t; const q = window.__glimmer.state.settings.quality; if (q !== qs[qs.length - 1]) qs.push(q); if (t < end) requestAnimationFrame(f); else res({ d: d.slice(5), qs, heap0, heap1: performance.memory ? performance.memory.usedJSHeapSize : 0, perf: window.__glimmer.renderer && window.__glimmer.renderer.perf ? { avg: window.__glimmer.renderer.perf.sum / Math.max(1, window.__glimmer.renderer.perf.n), max: window.__glimmer.renderer.perf.max } : null }); })(last);
  }), SECS);
  const d = r.d.slice().sort((a, b) => a - b); const pc = p => d[Math.min(d.length - 1, Math.floor(p * d.length))]; const avg = d.reduce((a, b) => a + b, 0) / d.length;
  const res = { tier: TIER, cpu: CPU, quality: Q, auto: AUTO, seconds: SECS, frames: d.length, avgFps: +(1000 / avg).toFixed(1), p50: +pc(0.5).toFixed(1), p95: +pc(0.95).toFixed(1), p99: +pc(0.99).toFixed(1),
    onePctLowFps: +(1000 / d.slice(Math.floor(d.length * 0.99)).reduce((a, b) => a + b, 0) * d.slice(Math.floor(d.length * 0.99)).length).toFixed(1),
    over33pct: +(100 * d.filter(x => x > 33.4).length / d.length).toFixed(2), over50pct: +(100 * d.filter(x => x > 50).length / d.length).toFixed(2),
    heapMB: +(r.heap1 / 1048576).toFixed(1), heapGrowMB: +((r.heap1 - r.heap0) / 1048576).toFixed(2), rendererMs: r.perf, qualityPath: r.qs, loadMs: load, pageErrors: errs.length };
  const fails = []; if (res.avgFps < BUD[0]) fails.push(`avg ${res.avgFps} < ${BUD[0]}`); if (res.p95 > BUD[1]) fails.push(`p95 ${res.p95} > ${BUD[1]} ms`); if (res.over50pct / 100 > BUD[2]) fails.push(`>50ms ${res.over50pct}% > ${BUD[2] * 100}%`);
  if (errs.length) fails.push('pageerror: ' + errs[0]); if (AUTO && r.qs.length > 3) fails.push('畫質來回跳 ' + r.qs.join('>'));
  res.pass = fails.length === 0; res.fails = fails; fs.mkdirSync(path.dirname(OUT), { recursive: true }); fs.writeFileSync(OUT, JSON.stringify(res, null, 1));
  console.log(JSON.stringify(res)); console.log(res.pass ? 'PASS' : 'FAIL ' + fails.join('; ')); await b.close(); process.exit(res.pass ? 0 : 1);
})();
