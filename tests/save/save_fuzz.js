#!/usr/bin/env node
/* save_fuzz.js — 存檔損毀／版本／往返／quota 模糊測試（Playwright）
 * 用法：node save_fuzz.js --url http://localhost:8124/index.html [--key windrun_save_v1] [--out out/save-fuzz.json] [--act "G.act('feed')"]
 * 需要遊戲暴露 window.__wr.G（G.save、G.act、G.persist）。冒險 build 請用 --act 指定一個「存檔後再玩一步」嘅動作。
 * 每案：載入前以 addInitScript 注入 localStorage → 檢查 ①無未捕獲錯誤 ②數值有限且在範圍 ③原型未污染 ④可再玩一步 ⑤（BAK 組）有 *bak* 備份鍵
 */
'use strict';
const fs = require('fs'), path = require('path');
function arg(n, d) { const i = process.argv.indexOf('--' + n); return i > 0 ? process.argv[i + 1] : d; }
function loadPW() {
  for (const p of [process.env.PW_PATH, '/workspace/tools/pw/node_modules/playwright-core', 'playwright-core']) { if (!p) continue; try { return require(p); } catch (e) {} }
  console.error('搵唔到 playwright-core'); process.exit(2);
}
const { chromium } = loadPW();
const URL = arg('url', 'http://localhost:8124/index.html'), KEY = arg('key', 'windrun_save_v1');
const OUT = arg('out', path.join(__dirname, 'out', 'save-fuzz.json'));
const ACT = arg('act', "G.act('feed')");
const mk = (o) => JSON.stringify(Object.assign({ v: 1, creatures: {}, ribbons: 0, turn: 1, actionsLeft: 3, cleared: {}, races: 0, sound: true }, o));
const cr = (o) => ({ lv: 1, exp: 0, cond: 100, bonus: { speed: 0, power: 0, calm: 0, stamina: 0 }, ...o });
const CASES = [
  ['F01', '無存檔', null, 0],
  ['F02', '非 JSON "{"', '{', 1],
  ['F03', 'null', 'null', 0], ['F04', '[]', '[]', 0], ['F05', '空字串', '', 0],
  ['F06', '最小有效 {"v":1}', '{"v":1}', 0],
  ['F07', '未來版本 v:99', JSON.stringify({ v: 99, future: { x: 1 }, ribbons: 5 }), 1],
  ['F08', '舊版 v:0', JSON.stringify({ v: 0, ribbons: 5 }), 1],
  ['F09', '缺 v', JSON.stringify({ ribbons: 5 }), 0],
  ['F10', 'ribbons 字串／turn 負數／actionsLeft null', mk({ ribbons: 'abc', turn: -7, actionsLeft: null }), 0],
  ['F11', '極端數值 ribbons -1e12／races 1e15', mk({ ribbons: -1e12, races: 1e15 }), 0],
  ['F12', '野靈欄位損毀 lv 字串／exp 負／cond 1e9／bonus null', mk({ creatures: { mochi: { lv: 'x', exp: -5, cond: 1e9, bonus: null } } }), 0],
  ['F13', 'creatures 為陣列／未知 id', mk({ creatures: [1, 2, 3] }), 0],
  ['F14', 'cleared 型別錯', mk({ cleared: 'yes' }), 0],
  ['F15', '__proto__ 污染', '{"v":1,"__proto__":{"polluted":1},"creatures":{"__proto__":{"polluted2":1},"constructor":{"prototype":{"polluted3":1}}}}', 0],
  ['F16', '3 MB 垃圾欄位', mk({ junk: 'x'.repeat(3 * 1024 * 1024) }), 0],
  ['F17', 'JSON 截斷', mk({ ribbons: 123 }).slice(0, 40), 1],
];
const PROBE = `(() => {
  const r = { errs: [], nonfinite: [], range: [] };
  const G = window.__wr && window.__wr.G; if (!G) return { noG: true };
  const walk = (o, p, d) => { if (d > 6 || o == null) return; for (const k of Object.keys(o)) { const v = o[k], q = p + '.' + k;
    if (typeof v === 'number') { if (!Number.isFinite(v)) r.nonfinite.push(q); else if (Math.abs(v) > 1e9) r.range.push(q + '=' + v); else if (v < 0 && !/^\\.(ribbons)$/.test(q) ) r.range.push(q + '=' + v); }
    else if (typeof v === 'object') walk(v, q, d + 1); } };
  walk(G.save, '', 0);
  r.polluted = ({}).polluted !== undefined || ({}).polluted2 !== undefined || ({}).polluted3 !== undefined;
  r.scene = G.scene; r.ribbons = G.save && G.save.ribbons; r.typeBad = [];
  if (typeof G.save.ribbons !== 'number') r.typeBad.push('ribbons');
  if (G.save.cleared === null || typeof G.save.cleared !== 'object') r.typeBad.push('cleared=' + G.save.cleared);
  if (G.save.ribbons < 0) r.range.push('ribbons<0');
  if (G.save.turn < 1) r.range.push('turn<1=' + G.save.turn);
  if (G.save.actionsLeft == null || typeof G.save.actionsLeft !== 'number') r.typeBad.push('actionsLeft');
  const m = G.save.creatures && G.save.creatures.mochi;
  if (m) { if (typeof m.lv !== 'number' || !(m.lv >= 1)) r.typeBad.push('mochi.lv=' + m.lv); if (!(m.cond >= 0 && m.cond <= 100)) r.range.push('mochi.cond=' + m.cond); if (!(m.exp >= 0)) r.range.push('mochi.exp=' + m.exp); if (!m.bonus || typeof m.bonus !== 'object') r.typeBad.push('mochi.bonus'); }
  try { ${ACT}; r.actOk = true; } catch (e) { r.actOk = false; r.actErr = String(e.message || e); }
  return r;
})()`;
(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROME_PATH || '/usr/bin/google-chrome', args: ['--no-sandbox'] });
  const results = [];
  async function runCase(id, name, raw, bak) {
    const ctx = await browser.newContext({ viewport: { width: 390, height: 844 } });
    const page = await ctx.newPage(); const errs = [];
    page.on('pageerror', e => errs.push(String(e.message || e)));
    if (raw !== null) await page.addInitScript(([k, v]) => { try { if (!sessionStorage.getItem('__seeded')) { localStorage.setItem(k, v); sessionStorage.setItem('__seeded', '1'); } } catch (e) {} }, [KEY, raw]);
    await page.goto(URL); await page.waitForTimeout(400);
    const r = await page.evaluate(PROBE);
    await page.waitForTimeout(200);
    const keys = await page.evaluate(() => Object.keys(localStorage));
    const hasBak = keys.some(k => /bak|backup|corrupt/i.test(k));
    const fails = [];
    if (r.noG) fails.push('冇 window.__wr.G');
    if (errs.length) fails.push('載入時未捕獲錯誤: ' + errs[0]);
    if (r.nonfinite && r.nonfinite.length) fails.push('非有限數: ' + r.nonfinite.slice(0, 3));
    if (r.range && r.range.length) fails.push('超範圍: ' + r.range.slice(0, 3));
    if (r.typeBad && r.typeBad.length) fails.push('型別錯: ' + r.typeBad.slice(0, 3));
    if (r.polluted) fails.push('原型被污染');
    if (r.actOk === false) fails.push('再玩一步崩潰: ' + r.actErr);
    if (bak && !hasBak) fails.push('玩家存檔被覆蓋但無 *bak* 備份');
    await ctx.close();
    results.push({ id, name, pass: fails.length === 0, fails });
  }
  for (const c of CASES) await runCase(...c);
  // R01 往返一致
  { const ctx = await browser.newContext({ viewport: { width: 390, height: 844 } }); const page = await ctx.newPage();
    await page.goto(URL); await page.waitForTimeout(300);
    const a = await page.evaluate(`(() => { const G = window.__wr.G; try { ${ACT}; } catch (e) {} G.persist(); return localStorage.getItem(${JSON.stringify(KEY)}); })()`);
    await page.reload(); await page.waitForTimeout(300);
    const b = await page.evaluate(`(() => { const G = window.__wr.G; G.persist(); return localStorage.getItem(${JSON.stringify(KEY)}); })()`);
    results.push({ id: 'R01', name: '往返一致（存→重載→存）', pass: !!a && a === b, fails: a === b ? [] : ['存檔字串不一致'] });
    // R02 quota
    const q = await page.evaluate(`(() => { const G = window.__wr.G; const o = Storage.prototype.setItem; Storage.prototype.setItem = function () { throw new DOMException('quota', 'QuotaExceededError'); }; let thrown = null; try { G.persist(); ${ACT}; } catch (e) { thrown = String(e.message); } Storage.prototype.setItem = o; return thrown; })()`);
    results.push({ id: 'R02', name: 'QuotaExceeded 唔令遊戲崩', pass: q === null, fails: q === null ? [] : ['拋錯: ' + q], note: '是否有 UI 提示需人手確認' });
    const size = await page.evaluate(`(localStorage.getItem(${JSON.stringify(KEY)}) || '').length`);
    results.push({ id: 'R03', name: '存檔大小（bytes）', pass: size < 200 * 1024, fails: [], note: size + ' B' });
    await ctx.close(); }
  await browser.close();
  fs.mkdirSync(path.dirname(OUT), { recursive: true }); fs.writeFileSync(OUT, JSON.stringify(results, null, 1));
  let nf = 0; for (const r of results) { if (!r.pass) nf++; console.log((r.pass ? 'PASS ' : 'FAIL ') + r.id + ' ' + r.name + (r.fails.length ? ' → ' + r.fails.join('; ') : '') + (r.note ? ' [' + r.note + ']' : '')); }
  console.log(`\n${results.length - nf}/${results.length} pass，${nf} fail`); process.exit(nf ? 1 : 0);
})();
