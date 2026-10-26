#!/usr/bin/env node
/* touch_move_probe.js — 觸控移動手感自動測試（Playwright + CDP Input.dispatchTouchEvent 真觸控事件）
 * 用法：node touch_move_probe.js --url file:///.../mock/index.html [--out out/touch.json] [--lat 67]
 * 協議：被測頁面需暴露 window.__qa（見 QA/touch-move-feel-test.md §0）。量度＝頁面層延遲（pointerdown → 玩家座標首次改變嘅幀）。
 */
'use strict';
const fs = require('fs'), path = require('path');
function arg(n, d) { const i = process.argv.indexOf('--' + n); return i > 0 ? process.argv[i + 1] : d; }
function loadPW() { for (const p of [process.env.PW_PATH, '/workspace/tools/pw/node_modules/playwright-core', 'playwright-core']) { if (!p) continue; try { return require(p); } catch (e) {} } console.error('搵唔到 playwright-core'); process.exit(2); }
const { chromium } = loadPW();
const URL = arg('url', 'file://' + path.join(__dirname, 'mock/index.html')), LAT = parseFloat(arg('lat', '67')), OUT = arg('out', path.join(__dirname, 'out/touch.json'));
const sleep = ms => new Promise(r => setTimeout(r, ms));
const res = [];
function rec(id, name, pass, val, crit) { res.push({ id, name, pass, val, crit }); console.log((pass ? 'PASS ' : 'FAIL ') + id + ' ' + name + '  [' + val + ' ; 準則 ' + crit + ']'); }
const med = a => { const s = [...a].sort((x, y) => x - y); return s[Math.floor(s.length / 2)]; };
const p95 = a => { const s = [...a].sort((x, y) => x - y); return s[Math.min(s.length - 1, Math.ceil(s.length * 0.95) - 1)]; };
(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROME_PATH || '/usr/bin/google-chrome', args: ['--no-sandbox'] });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, hasTouch: true, isMobile: true, deviceScaleFactor: 2 });
  const page = await ctx.newPage(); const cdp = await ctx.newCDPSession(page);
  await page.goto(URL); await page.waitForTimeout(300);
  const Q = (e) => page.evaluate(e);
  const touch = (type, pts) => cdp.send('Input.dispatchTouchEvent', { type, touchPoints: pts });
  const pt = (x, y, id = 0) => ({ x, y, id });
  // 頁面層量度器
  await Q(`(() => { const q = window.__qa; window.__m = { arm2: () => { tc = q.teleports(); sc0 = q.scene(); window.__m.t0 = 0; window.__m.tr = 0; window.__m.tw = true; }, down: 0, up: 0, first: 0, p0: null, track: false, moved: 0, log: [] };
    addEventListener('pointerdown', e => { if (!window.__m.track) return; window.__m.down = performance.now(); window.__m.p0 = q.player(); window.__m.first = 0; }, true);
    addEventListener('pointerup', e => { const m = window.__m; m.up = performance.now(); m.pu = q.player(); if (m.tap) { m.down = m.up; m.p0 = q.player(); m.first = 0; } }, true);
    let tc = 0, sc0 = q.scene(); (function loop() { const m = window.__m; if (m.tw) { if (q.teleports() > tc && !m.t0) m.t0 = performance.now(); if (m.t0 && !m.tr && q.scene() !== sc0 && !q.locked()) m.tr = performance.now(); } if (m.track && m.down && !m.first && m.p0) { const p = q.player(); if (Math.hypot(p.x - m.p0.x, p.y - m.p0.y) > 0.3) m.first = performance.now(); } requestAnimationFrame(loop); })(); })()`);
  const arm = (tap) => Q(`(() => { const m = window.__m; m.tap = ${!!tap}; m.track = true; m.down = 0; m.first = 0; m.p0 = null; })()`);
  const lat = () => Q(`(() => { const m = window.__m; return m.first && m.down ? m.first - m.down : -1; })()`);
  const reset = async () => { await Q(`__qa.reset()`); await sleep(60); await Q(`__qa.setPlayer(120,104)`); await sleep(60); };
  const jr = await Q(`__qa.joystickRegion()`); const params = await Q(`__qa.params`);
  const POS = async () => Q(`__qa.player()`);
  // ---- M1 點擊移動 ----
  { const L = []; let maxErr = 0;
    for (let i = 0; i < 10; i++) { await reset(); await arm(true); const tx = 120 + 40 + (i % 3) * 10, ty = 104; const s = await Q(`__qa.worldToScreen(${tx},${ty})`);
      await touch('touchStart', [pt(s.x, s.y)]); await sleep(30); await touch('touchEnd', []); await sleep(1500);
      L.push(await lat()); const p = await POS(); maxErr = Math.max(maxErr, Math.hypot(p.x - tx, p.y - ty)); }
    const ok = L.filter(x => x >= 0); rec('M1a', '點擊移動啟動延遲 median（放手→移動）', ok.length === 10 && med(ok) <= LAT, med(ok).toFixed(0) + ' ms', '≤' + LAT + ' ms');
    rec('M1b', '點擊移動啟動延遲 p95（放手→移動）', p95(ok) <= LAT + 17, p95(ok).toFixed(0) + ' ms', '≤' + (LAT + 17) + ' ms');
    rec('M1c', '點擊移動到達誤差', maxErr <= 4, maxErr.toFixed(1) + ' px', '≤4 px'); }
  // ---- M2 死區 ----
  { await reset(); const dz = params.deadzone; const p0 = await POS();
    await touch('touchStart', [pt(jr.x, jr.y)]); await sleep(30); await touch('touchMove', [pt(jr.x + dz - 2, jr.y)]); await sleep(500); const p1 = await POS(); await touch('touchEnd', []);
    rec('M2a', '死區內唔郁', Math.hypot(p1.x - p0.x, p1.y - p0.y) <= 0.5, Math.hypot(p1.x - p0.x, p1.y - p0.y).toFixed(2) + ' px', '≤0.5 px');
    await reset(); const q0 = await POS();
    await touch('touchStart', [pt(jr.x, jr.y)]); await sleep(30); await touch('touchMove', [pt(jr.x + dz + 6, jr.y)]); await sleep(500); const q1 = await POS(); await touch('touchEnd', []);
    rec('M2b', '越過死區有反應', Math.hypot(q1.x - q0.x, q1.y - q0.y) > 0.5, Math.hypot(q1.x - q0.x, q1.y - q0.y).toFixed(1) + ' px', '>0.5 px'); }
  // ---- M3 搖桿延遲 ----
  { const L = []; for (let i = 0; i < 8; i++) { await reset(); await touch('touchStart', [pt(jr.x, jr.y)]); await sleep(40); await arm();
      await Q(`(() => { const m = window.__m; m.down = performance.now(); m.p0 = __qa.player(); })()`);
      await touch('touchMove', [pt(jr.x + params.deadzone + 20, jr.y)]); await sleep(300); L.push(await lat()); await touch('touchEnd', []); await sleep(50); }
    const ok = L.filter(x => x >= 0); rec('M3', '搖桿越過死區→移動延遲 median', ok.length >= 7 && med(ok) <= LAT, med(ok).toFixed(0) + ' ms', '≤' + LAT + ' ms'); }
  // ---- M4 速度線性 ----
  { async function speed(off) { await reset(); await Q(`__qa.setPlayer(60,104)`); await touch('touchStart', [pt(jr.x, jr.y)]); await sleep(30); await touch('touchMove', [pt(jr.x + off, jr.y)]); await sleep(150);
      const a = await POS(), t0 = Date.now(); await sleep(600); const b = await POS(), dt = (Date.now() - t0) / 1000; await touch('touchEnd', []); return (b.x - a.x) / dt; }
    const full = await speed(params.maxRadius + 10), half = await speed(params.deadzone + (params.maxRadius - params.deadzone) / 2);
    rec('M4a', '滿推速度 vs 規格', Math.abs(full / params.speed - 1) <= 0.12, full.toFixed(1) + ' px/s', params.speed + ' ±12%');
    rec('M4b', '半推速度比例（類比）', half / full > 0.3 && half / full < 0.7, (half / full).toFixed(2), '0.3–0.7'); }
  // ---- M5 放手即停 ----
  { await reset(); await touch('touchStart', [pt(jr.x, jr.y)]); await sleep(30); await touch('touchMove', [pt(jr.x + params.maxRadius, jr.y)]); await sleep(400);
    await touch('touchEnd', []); await sleep(400); const pu = await Q(`__m.pu`), pe = await POS(); const d = Math.hypot(pe.x - pu.x, pe.y - pu.y);
    const lim = 2 * params.speed / 60 + 0.2; rec('M5', '放手後滑行距離', d <= lim, d.toFixed(2) + ' px', '≤' + lim.toFixed(2) + ' px（2 幀）'); }
  // ---- M6 貼牆 ----
  { await reset(); await Q(`__qa.setPlayer(120,24)`); await sleep(50); // 近上牆（row1 y=16..32）
    let clip = 0, prev = await POS(); const x0 = prev.x;
    await touch('touchStart', [pt(jr.x, jr.y)]); await sleep(30); await touch('touchMove', [pt(jr.x + 40, jr.y - 40)]); // 右上
    const t0 = Date.now(); for (let i = 0; i < 40; i++) { await sleep(15); const p = await POS(); const hw = params.hitW / 2, hh = params.hitH / 2;
      for (const [a, b] of [[p.x - hw, p.y - hh], [p.x + hw, p.y - hh], [p.x - hw, p.y + hh], [p.x + hw, p.y + hh]]) if (await Q(`__qa.solid(${Math.floor(a / 16)},${Math.floor(b / 16)})`)) clip++; }
    const dt = (Date.now() - t0) / 1000, p2 = await POS(); await touch('touchEnd', []);
    const eff = (p2.x - x0) / dt, nominal = params.speed * Math.min(1, (Math.hypot(40, 40) - params.deadzone) / (params.maxRadius - params.deadzone)) * Math.SQRT1_2;
    rec('M6a', '貼牆斜推：碰撞盒入牆幀數', clip === 0, String(clip), '=0');
    rec('M6b', '貼牆斜推：沿牆速度／名義', eff / nominal >= 0.4, (eff / nominal * 100).toFixed(0) + '%', '≥40%'); }
  // ---- M7 傳送 ----
  { await reset(); await Q(`__qa.setPlayer(17*16-2,10*16+8)`); await sleep(50); await Q(`__m.arm2()`);
    await touch('touchStart', [pt(jr.x, jr.y)]); await sleep(30); await touch('touchMove', [pt(jr.x + params.maxRadius, jr.y)]);
    let tReady = -1, lockedSeen = false, scn0 = await Q(`__qa.scene()`), pLock = null;
    for (let i = 0; i < 80; i++) { await sleep(15); const s = await Q(`({s:__qa.scene(),l:__qa.locked(),p:__qa.player()})`); if (s.l) { lockedSeen = true; if (!pLock) pLock = s.p; else if (Math.hypot(s.p.x - pLock.x, s.p.y - pLock.y) > 0.5 && s.s === scn0) pLock = 'moved'; }
      }
    tReady = await Q(`__m.tr && __m.t0 ? __m.tr - __m.t0 : -1`);
    await sleep(500); const n = await Q(`__qa.teleports()`); await touch('touchEnd', []);
    rec('M7a', '傳送後可操作時間', tReady > 0 && tReady <= 600, tReady.toFixed(0) + ' ms', '≤600 ms');
    rec('M7b', '持續推搖桿只傳送 1 次', n === 1, String(n), '=1');
    rec('M7c', '傳送淡出期間輸入鎖', lockedSeen && pLock !== 'moved', String(lockedSeen), '鎖定且唔郁'); }
  // ---- M8 NPC 對話 ----
  { await reset(); const n0 = (await Q(`__qa.npcs()`))[0]; await Q(`__qa.setPlayer(${n0.x - 40},${n0.y})`); await sleep(50); const s = await Q(`__qa.worldToScreen(${n0.x},${n0.y})`);
    await touch('touchStart', [pt(s.x, s.y)]); await sleep(30); await touch('touchEnd', []); await sleep(1200); let d = await Q(`__qa.dialog()`);
    rec('M8a', '點擊 NPC→走近→對話開啟', d.open, JSON.stringify(d), 'open');
    await sleep(100); const tap = async () => { await touch('touchStart', [pt(195, 400)]); await sleep(40); await touch('touchEnd', []); await sleep(120); };
    d = await Q(`__qa.dialog()`); const before = d; await tap(); d = await Q(`__qa.dialog()`);
    rec('M8b', '打字中點擊：完成成句、唔跳句', before.shown < before.total ? (d.line === before.line && d.shown === d.total) : true, `line ${before.line}→${d.line}`, 'line 不變、shown=total');
    await tap(); d = await Q(`__qa.dialog()`); rec('M8c', '句完再點擊→下一句', d.line === before.line + 1, 'line ' + d.line, 'line+1');
    const t0 = Date.now(); await touch('touchStart', [pt(195, 400)]); let closed = -1; for (let i = 0; i < 150; i++) { await sleep(20); if (!(await Q(`__qa.dialog().open`))) { closed = Date.now() - t0; break; } } await touch('touchEnd', []);
    rec('M8d', '長按快進完成對話', closed > 0 && closed <= 1500, closed + ' ms', '≤1500 ms');
    await reset(); await Q(`__qa.setPlayer(${n0.x - 40},${n0.y})`); await sleep(50); await touch('touchStart', [pt(s.x, s.y)]); await sleep(30); await touch('touchEnd', []); await sleep(1200);
    await touch('touchStart', [pt(370, 30)]); await sleep(40); await touch('touchEnd', []); await sleep(150); rec('M8e', '跳過鍵一點即關', !(await Q(`__qa.dialog().open`)), 'closed', 'open=false'); }
  // ---- M9 多指 ----
  { await reset(); await touch('touchStart', [pt(jr.x, jr.y, 0)]); await sleep(30); await touch('touchMove', [pt(jr.x + params.maxRadius, jr.y, 0)]); await sleep(100); const a = await POS();
    await touch('touchStart', [pt(jr.x + params.maxRadius, jr.y, 0), pt(300, 300, 1)]); await sleep(40); await touch('touchEnd', [pt(jr.x + params.maxRadius, jr.y, 0)]); await sleep(300); const b = await POS();
    rec('M9', '搖桿按住時第二指點擊唔令搖桿失效', b.x - a.x > 3, (b.x - a.x).toFixed(1) + ' px', '仍然移動'); await touch('touchEnd', []); }
  await browser.close();
  fs.mkdirSync(path.dirname(OUT), { recursive: true }); fs.writeFileSync(OUT, JSON.stringify(res, null, 1));
  const nf = res.filter(r => !r.pass).length; console.log(`\n${res.length - nf}/${res.length} pass，${nf} fail`); process.exit(nf ? 1 : 0);
})();
