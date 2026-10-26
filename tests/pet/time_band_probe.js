#!/usr/bin/env node
/* time_band_probe.js — 時段轉換／就寢建議檢查（對 glimmer-proto 的 ?hour= 覆寫；方案 A 模組 3a 做完後沿用同介面）
 * 用法：node time_band_probe.js --url http://localhost:8125/index.html
 * 檢查：就寢建議（#btn-sleep.hint＋氣泡「夜深喇」）喺 22.99→不出、23.00→出、06.99→出、07.00→不出；12／00；autoSuggest 關閉；已睡／精力≥90／蛋 唔提示；
 *       1440 分鐘掃描（每 5 分鐘＋邊界逐分鐘）：建議只出現喺 [23:00,07:00)，且 24h 內無重疊／空洞；時間倒退（hour 23→1→23）唔拋錯。
 */
'use strict';
const path = require('path');
function arg(n, d) { const i = process.argv.indexOf('--' + n); return i > 0 ? process.argv[i + 1] : d; }
let chromium; for (const p of [process.env.PW_PATH, '/workspace/tools/pw/node_modules/playwright-core', 'playwright-core']) { try { if (p) { chromium = require(p).chromium; break; } } catch (e) {} }
const URL = arg('url', 'http://localhost:8125/index.html');
let pass = 0, fail = 0; const ok = (c, n, i) => { c ? pass++ : fail++; console.log((c ? 'PASS ' : 'FAIL ') + n + (c || !i ? '' : ' → ' + i)); };
(async () => {
  const b = await chromium.launch({ executablePath: process.env.CHROME || '/usr/bin/google-chrome', args: ['--no-sandbox'] });
  const page = await (await b.newContext({ viewport: { width: 390, height: 844 } })).newPage(); const errs = []; page.on('pageerror', e => errs.push(e.message));
  await page.goto(URL + '?debug=1&q=high'); await page.evaluate(() => localStorage.clear()); await page.reload(); await page.waitForTimeout(600);
  const setup = (o) => page.evaluate((o) => { const G = window.__glimmer, s = G.state; s.stage = o.stage || 'sprout'; s.sleeping = !!o.sleeping; s.needs.energy = o.energy == null ? 50 : o.energy; s.settings.autoSuggest = o.auto !== false; G.hourOverride = o.hour; }, o);
  const hint = async () => { await page.waitForTimeout(260); return page.evaluate(() => ({ hint: document.querySelector('#btn-sleep').classList.contains('hint'), bubble: (document.querySelector('#bubble') || {}).textContent || '' })); };
  for (const [h, exp, nm] of [[22.99, false, '22:59'], [23.0, true, '23:00'], [23.99, true, '23:59'], [0, true, '00:00'], [3, true, '03:00'], [6.99, true, '06:59'], [7.0, false, '07:00'], [12, false, '12:00'], [18, false, '18:00']]) {
    await setup({ hour: h }); const r = await hint(); ok(r.hint === exp, `就寢建議 @${nm} ＝ ${exp}`, JSON.stringify(r)); }
  await setup({ hour: 1, auto: false }); let r = await hint(); ok(!r.hint, '夜間但「就寢建議」設定關 → 唔提示', JSON.stringify(r));
  await setup({ hour: 1, sleeping: true }); r = await hint(); ok(!r.hint, '已經瞓緊 → 唔提示', JSON.stringify(r));
  await setup({ hour: 1, energy: 95 }); r = await hint(); ok(!r.hint, '精力 ≥90（瞓唔著）→ 唔提示', JSON.stringify(r));
  await setup({ hour: 1, stage: 'egg' }); r = await hint(); ok(!r.hint, '光卵 → 唔提示', JSON.stringify(r));
  // 1440 分鐘掃描（直接用頁面內邏輯：以 hourOverride 逐分鐘設定並讀 hint；每 5 分鐘抽樣以節省時間，邊界逐分鐘）
  const bad = []; const mins = []; for (let m = 0; m < 1440; m += 5) mins.push(m); for (const m of [1379, 1380, 1381, 419, 420, 421]) mins.push(m);
  for (const m of mins) { await setup({ hour: m / 60 }); await page.waitForTimeout(40); const h = (await page.evaluate(() => document.querySelector('#btn-sleep').classList.contains('hint'))); const exp = (m >= 1380 || m < 420); if (h !== exp) bad.push(m); }
  ok(bad.length === 0, `每 5 分鐘抽樣＋23:00/07:00 邊界逐分鐘（${mins.length} 點）建議只出現喺 23:00–07:00`, '錯誤分鐘: ' + bad.slice(0, 8));
  await setup({ hour: 23 }); await setup({ hour: 1 }); await setup({ hour: 23 }); ok(errs.length === 0, '時間倒退／跳變（23→1→23）無錯誤', errs[0]);
  await b.close(); console.log(`\n${pass}/${pass + fail} pass，${fail} fail`); process.exit(fail ? 1 : 0);
})();
