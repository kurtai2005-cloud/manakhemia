#!/usr/bin/env node
/* trace_capture.js — 自動錄 Chrome Performance trace（可拖入 DevTools → Performance → Load profile 睇火焰圖／frames／GPU）
 * 用法：node trace_capture.js --url http://localhost:8000/ [--seconds 20] [--cpu 4] [--out out/trace.json]
 * 會自動開一場（如頁面有 window.__wr）再錄 N 秒。 */
'use strict';
const fs = require('fs'), path = require('path');
const arg = (n, d) => { const i = process.argv.indexOf('--' + n); return i > 0 ? process.argv[i + 1] : d; };
function loadPW() { for (const p of [process.env.PW_PATH, '/workspace/tools/pw/node_modules/playwright-core', 'playwright-core']) { if (!p) continue; try { return require(p); } catch (e) {} } console.error('需要 playwright-core（或設 PW_PATH）'); process.exit(2); }
const { chromium } = loadPW();
(async () => {
  const url = arg('url', 'http://localhost:8000/'), sec = +arg('seconds', 20), cpu = +arg('cpu', 4), out = arg('out', path.join(__dirname, 'out', 'trace.json'));
  const b = await chromium.launch({ executablePath: process.env.CHROME_PATH || '/usr/bin/google-chrome', args: ['--no-sandbox'] });
  const ctx = await b.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, hasTouch: true, isMobile: true });
  const page = await ctx.newPage(); const cdp = await ctx.newCDPSession(page);
  await cdp.send('Emulation.setCPUThrottlingRate', { rate: cpu });
  await page.goto(url);
  await page.evaluate(() => { if (window.__wr) { const { G } = window.__wr; G.stageSel = 1; G.teamPick = ['mochi', 'gravelbadger']; G.startRace(); } });
  await page.waitForTimeout(4000); // 過倒數
  await b.startTracing(page, { path: out, categories: ['devtools.timeline', 'disabled-by-default-devtools.timeline', 'disabled-by-default-devtools.timeline.frame', 'v8.execute', 'blink.user_timing', 'gpu'] });
  await page.waitForTimeout(sec * 1000);
  await b.stopTracing(); await b.close();
  console.log('trace 已寫入 ' + out + '（' + (fs.statSync(out).size / 1048576).toFixed(1) + ' MB）');
})().catch(e => { console.error(e); process.exit(2); });
