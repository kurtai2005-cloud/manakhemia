/* 《微光小圃》 e2e-5c — 第 5 批 5c 承傳（遊策 5a–5c spec §5c＋遊美 art/series2_long/5c）：
   新蛋 →「揀上一代」（候選卡、預覽花紋／招式／加速 pill、改揀、rail 再開）、蛋花紋、孵化 →「遺傳咗！」、花紋 strip、家傳招式、
   團絨傳授規則（最多／打和最近／未示範隨機）、家族 Lv3 成長快 20%（×0.8）、團絨蛋、族譜、存檔、字清晰度（FP12 24px、對比 ≥4.5）、熱區 ≥48、🛠「5c」、?l5c=0。
   截圖 360×780 DPR3 → SHOTS（5c-*.png）。node tests/e2e-5c.js */
const path = require('path');
let chromium;
for (const p of [process.env.PW, 'playwright-core', '/workspace/qa-live-s1/node_modules/playwright-core']) { try { if (p) { chromium = require(p).chromium; break; } } catch (e) { } }
if (!chromium) { console.error('找不到 playwright-core'); process.exit(2); }
const { audit } = require('./readaudit');
const BASE = process.env.BASE || 'http://localhost:8240/index.html';
const SHOTS = process.env.SHOTS || process.env.OUT || path.join(__dirname, '..', '..', '..', 'screens') + '/';
require('fs').mkdirSync(SHOTS, { recursive: true });
let pass = 0, fail = 0;
const ok = (c, n, info) => { if (c) { pass++; console.log('  ✓ ' + n); } else { fail++; console.log('  ✗ ' + n + (info !== undefined ? ' → ' + JSON.stringify(info) : '')); } };
const T0 = new Date(2026, 10, 2, 13, 0).getTime(), H = 3600e3, DAY = 86400e3;

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROME || '/usr/bin/google-chrome', args: ['--no-sandbox', '--autoplay-policy=no-user-gesture-required'] });
  const ctx = await browser.newContext({ viewport: { width: 360, height: 780 }, deviceScaleFactor: 3 });
  const page = await ctx.newPage();
  const errs = [];
  page.on('console', m => { if (m.type() === 'error') errs.push(m.type() + ': ' + m.text()); });
  page.on('pageerror', e => errs.push('pageerror: ' + e.message));
  const req5c = new Set(); page.on('request', r => { const m = decodeURIComponent(r.url()).match(/series2_long\/5c\/ui\/([^?#]+)/); if (m) req5c.add(m[1]); });   // 5c.1：runtime 載咗邊啲 5c UI
  const E = (fn, arg) => page.evaluate(fn, arg);
  const W = (ms) => page.waitForTimeout(ms);
  const shot = (n) => page.screenshot({ path: SHOTS + '5c-' + n + '.png' });
  const Q = () => E(() => __qa.l5c.st());
  const setT = (t) => E((t) => { __glimmer.clock.fake = true; __glimmer.clock.t = t; }, t);
  const vis = (tid) => page.locator('[data-testid=' + tid + ']').first().isVisible().catch(() => false);
  const click = (tid) => page.locator('[data-testid=' + tid + ']').first().click();
  const txt = (tid) => page.locator('[data-testid=' + tid + ']').first().innerText().catch(() => '');
  const prep = () => E(() => { window.__noSaveOnHide = true; const s = __glimmer.state; s.stage = 'adult'; s.form = 'dust'; s.sleeping = false; Object.assign(s.needs, { mood: 50, energy: 100, hunger: 100, clean: 100 }); s.poops = 0; });
  const hookToast = () => E(() => { window.__toasts = []; const U = Glimmer.ui, t = U.toast; if (U._h5b) return; U._h5b = 1; U.toast = function (m) { window.__toasts.push(String(m)); return t.apply(this, arguments); }; });
  const toasts = () => E(() => window.__toasts.slice());
  const load = async (qs, clear) => {
    if (clear !== false) { await page.goto(BASE + '?' + qs); await E(() => { window.__noSaveOnHide = true; localStorage.clear(); }); }
    await page.goto(BASE + '?' + qs); await page.waitForFunction(() => window.__glimmer && __glimmer.liveLoad).catch(() => { }); await E(() => __glimmer.liveLoad);
    await E(() => __glimmer.s2Load); await E(() => __glimmer.houseLoad); await E(() => __glimmer.l5bLoad).catch(() => { }); await E(() => __glimmer.l5cLoad).catch(() => { }); await setT(T0); if (clear !== false) await prep(); await hookToast(); await W(400);
  };
  const devRun = (k) => E((k) => __qa.l5c.dev().items.find(i => i.k === k).run(), k);
  const rows = () => E(() => __qa.l5b.rows());
  const wallet = () => E(() => Glimmer.sys12.st(__glimmer.state).wallet.total);
  const readOk = async (name, sel) => { const a = await audit(page, sel); ok(a.items.length > 0 && a.bad.length === 0, name + '：字 ' + a.items.length + ' 段全部合格（FP12 24px、對比 ≥4.5）', a.bad.slice(0, 3).map(b => [b.t, b.eff, b.cr, b.fam])); };

  const hit = (sel) => E((sel) => { const ui = document.getElementById('ui'), k = ui.getBoundingClientRect().width / ui.offsetWidth;
      return [...document.querySelectorAll(sel)].filter(e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden'; }).map(e => {
        e.scrollIntoView({ block: 'center', inline: 'nearest' }); const r = e.getBoundingClientRect(), cx = r.left + r.width / 2, cy = r.top + r.height / 2, h = 24 * k - 0.75; let n = 0, miss = [];
        for (const [dx, dy] of [[-1, -1], [1, -1], [-1, 1], [1, 1], [0, -1], [0, 1], [-1, 0], [1, 0]]) { const t = document.elementFromPoint(cx + dx * h, cy + dy * h); if (t && (t === e || e.contains(t))) n++; else miss.push(dx + ',' + dy + '→' + (t ? (t.dataset.testid || t.id || t.className || t.tagName) : '-')); }
        return { id: e.dataset.testid || e.id, n, miss: miss.slice(0, 2), lay: [Math.round(r.width / k), Math.round(r.height / k)] }; }); }, sel);
  const hitOk = async (label, sel, min) => { const L = await hit(sel); ok(L.length >= (min || 1), label + '：搵到 ' + L.length + ' 個');
    const bad = L.filter(x => x.n < 8); ok(bad.length === 0, label + '：熱區 ≥48' + (bad.length ? ' ← ' + JSON.stringify(bad.slice(0, 3)) : '（' + L.slice(0, 3).map(x => x.id + ' ' + x.lay.join('×')).join('，') + '）')); };

  const S5 = () => E(() => __qa.l5c.st());
  const cands = () => E(() => __qa.l5c.cands());
  const clean = () => E(() => { const t = document.getElementById('toast'); if (t) t.style.display = 'none'; });
  const statD = async (fn, ms) => { const a = (await S5()).stat; await fn(); await W(ms || 900); const b = (await S5()).stat; const d = {}; for (const k in b) d[k] = b[k] - (a[k] || 0); return d; };

  console.log('# 載入');
  await load('q=high&hour=13&seed=21&ev=0');
  ok(await E(() => !!(Glimmer.long5c && Glimmer.long5cui && window.__qa && __qa.l5c && __glimmer.l5c && __glimmer.pat5c)), 'long5c＋long5cui 裝咗');
  ok(await E(() => /^6[a-d]$/.test(Glimmer.data.PARAMS.series2.version)), '版本 5c');
  ok((await S5()).json, 'long_5c.json 載入');
  ok(await E(() => !!Glimmer.long5a.LIVE.inherit_fast && !Glimmer.long5a.LATER.inherit_fast), 'inherit_fast 轉 LIVE');
  ok(await E(() => Glimmer.devmode.sections().some(s => s.id === 'l5c' && s.title.includes('5c'))), '🛠 開發者模式有「5c」分組');
  ok(await E(() => !document.querySelector('#mbox [data-testid^=l5c]')), '設定冇 5c 測試掣');
  ok((await S5()).ov === null && !(await vis('l5c-rail')), 'QUIET：冇自動彈、冇 rail 掣');

  console.log('# 揀上一代（細佬蛋）');
  let r = await devRun('prep'); ok(r.ok, '準備：成年＋新細佬蛋', r); await W(700); await clean();
  let q = await S5(); ok(q.ov === 'pick' && q.pend.length === 1, '「揀上一代」彈出（1 隻等緊）', [q.ov, q.pend]);
  let C = await cands(); const main = C.find(c => c.main), kidC = C.find(c => c.kind === 'kid');
  ok(C.length >= 2 && main && C[0].id === main.id, '候選 ≥2，主團絨排頭', C.map(c => c.id));
  ok(main && main.kind === 'tr', '主團絨係候選');
  ok((await txt('l5c-pick-title')).includes('揀上一代') && (await txt('l5c-pick-sub')).includes('上一代'), '標題＋副題');
  ok(await E((n) => document.querySelectorAll('#l5cov .l5ccard').length === n, C.length), '每隻候選一張卡');
  ok(await E((id) => document.querySelector('[data-testid=l5c-card-' + id + ']').dataset.sel === '1', main.id), '預設揀主團絨');
  ok((await txt('l5c-preview-pat')).length >= 2 && (await txt('l5c-preview-trick')).length >= 1, '預覽：花紋＋招式');
  ok(await E(() => document.querySelector('[data-testid=l5c-preview-fast]').dataset.fast === 'locked'), '家族未到 Lv3 → pill「Lv3 先解鎖」');
  await readOk('揀上一代', '#l5cov');
  await hitOk('卡', '#l5cov .l5ccard', 2); await hitOk('就佢喇／閂', '[data-testid=l5c-pick-ok],[data-testid=l5c-pick-close]', 2);
  await E(() => { const g = document.querySelector('[data-testid=l5c-pick-grid]'); if (g) g.scrollTop = 0; });
  await shot('pick');
  // 揀細佬做上一代
  await click('l5c-card-' + kidC.id); await W(300);
  ok(await E((id) => document.querySelector('[data-testid=l5c-card-' + id + ']').dataset.sel === '1', kidC.id), '撳卡 → 改揀');
  ok((await txt('l5c-preview-pat')).includes((await E((p) => Glimmer.long5c.PAT[p].zh, kidC.pattern))), '預覽跟住改');
  await click('l5c-pick-ok'); await W(400);
  q = await S5(); const child = await E(() => __qa.l5c.child());
  ok(q.ov === null && q.inh[child] && q.inh[child].parent === kidC.id && !q.inh[child].hatched, '撳「就佢喇！」→ 記低上一代（未孵）', q.inh[child]);
  ok(q.inh[child].pattern === kidC.pattern && q.inh[child].trick === kidC.trick, '花紋＋招式＝候選', [q.inh[child], kidC]);
  // 閂咗再開：rail
  ok(await vis('l5c-rail'), '未孵 → rail「上一代」掣');
  await hitOk('rail 掣', '[data-testid=l5c-rail]');
  await click('l5c-rail'); await W(400); ok((await S5()).ov === 'pick', 'rail 掣再開「揀上一代」');
  ok(await E((id) => document.querySelector('[data-testid=l5c-card-' + id + ']').dataset.sel === '1', kidC.id), '再開記得揀咗邊隻');
  await click('l5c-pick-close'); await W(300); ok((await S5()).ov === null, '閂掣');
  // 蛋花紋
  let d = await statD(() => W(10), 1200); ok(d.egg > 0, '細佬蛋畫上一代花紋（egg_kid）', d);

  console.log('# 孵化 → 遺傳咗！');
  r = await devRun('hatch'); ok(r.ok && !/自動/.test(r.msg), '孵：' + r.msg, r); await W(800); await clean();
  q = await S5(); ok(q.ov === 'result' && q.inh[child].hatched, '「遺傳咗！」彈出', q.ov);
  ok((await txt('l5c-result-title')).includes('遺傳') && (await txt('l5c-result-pat')).length > 2 && (await txt('l5c-result-trick')).includes('家傳招式'), '結果：花紋＋家傳招式兩行');
  await W(600); await readOk('遺傳咗', '#l5cov'); await hitOk('好可愛', '[data-testid=l5c-result-ok]');
  await shot('result');
  await click('l5c-result-ok'); await W(300); ok((await S5()).ov === null && !(await vis('l5c-rail')), '閂結果；rail 掣收埋');
  d = await statD(() => W(10), 1500); ok(d.strip > 0, '花園細佬 strip 畫花紋', d);
  // 有／冇花紋像素唔同
  ok(await E(() => { const t = __qa.l5c.st().stat; return t.built > 0; }), '染色 cache 有建');

  console.log('# 家傳招式');
  r = await devRun('trick'); ok(r.ok || r.msg.includes('busy'), '細佬做招式：' + r.msg, r);
  if (!r.ok) { await E(() => { document.body.classList.remove('s2-scene'); }); await W(3000); r = await devRun('trick'); }
  ok(r.ok, '細佬做家傳招式（照抄 clip）', r); await W(1200); await clean(); await shot('trick');
  q = await S5(); ok(q.n.tricks >= 1, '招式次數記低', q.n);
  await W(4000);
  // 團絨教咗嘅課：示範 → 傳最多嗰課
  ok(await E(() => { const C5 = Glimmer.long5c, s = __glimmer.state, id = 'tr' + (s.gen || 1); C5.reset(s); C5.noteDemo(s, id, 'C', 1000); C5.noteDemo(s, id, 'C', 2000); C5.noteDemo(s, id, 'E', 3000); return C5.trickOf(s, { kind: 'tr', id }).L === 'C'; }), '團絨：示範最多嗰課');
  ok(await E(() => { const C5 = Glimmer.long5c, s = __glimmer.state, id = 'tr' + (s.gen || 1); C5.noteDemo(s, id, 'E', 4000); return C5.trickOf(s, { kind: 'tr', id }).L === 'E'; }), '團絨：打和 → 最近嗰課');
  ok(await E(() => { const C5 = Glimmer.long5c, s = __glimmer.state, id = 'tr' + (s.gen || 1); C5.reset(s); const t = C5.trickOf(s, { kind: 'tr', id }); return /^[A-H]$/.test(t.L) && t.src === 'random'; }), '團絨：未示範 → 8 課隨機');

  console.log('# 家族 Lv3 → 成長快 20%');
  await load('q=high&hour=13&seed=21&ev=0');
  r = await devRun('fast'); ok(r.ok && r.msg.includes('開'), r.msg, r);
  r = await devRun('prep'); ok(r.ok, '再準備細佬蛋', r); await W(500); await clean();
  ok(await E(() => document.querySelector('[data-testid=l5c-preview-fast]').dataset.fast === 'on') && (await txt('l5c-preview-fast')).includes('20%'), 'pill「成長快 20%」');
  await readOk('揀上一代（加速）', '#l5cov'); await shot('pick-fast');
  await click('l5c-pick-ok'); await W(300); r = await devRun('hatch'); await W(600);
  q = await S5(); const ch2 = await E(() => __qa.l5c.child() || Object.keys(__qa.l5c.st().inh).pop());
  ok(Object.values(q.inh).some(h => h.hatched && h.fast === true), '孵化鎖定加速', q.inh);
  ok(q.fast === 0.8, '細佬 S1／S2 ×0.8', q.fast);
  ok(await E(() => document.querySelector('[data-testid=l5c-result-fast]') && document.querySelector('[data-testid=l5c-result-fast]').dataset.fast === 'on'), '結果 pill 加速開');
  await E(() => __qa.l5c.close());

  console.log('# 團絨蛋（第二代）＋族譜');
  r = await devRun('prepTr'); ok(r.ok, '準備新團絨蛋：' + r.msg, r); await W(500); await clean();
  if (r.ok) {
    ok(await E(() => document.querySelector('[data-testid=l5c-preview-fast]').dataset.fast === 'tr'), '團絨蛋 pill「團絨蛋唔計」');
    await readOk('揀上一代（團絨蛋）', '#l5cov');
    await click('l5c-pick-ok'); await W(300); q = await S5(); ok(Object.values(q.inh).some(h => h.kind === 'tr' && !h.hatched), '團絨蛋記低上一代');
    r = await devRun('hatch'); ok(r.ok, '團絨蛋孵：' + r.msg, r); await W(600); await E(() => __qa.l5c.close());
    let d2 = await statD(() => W(10), 1500); ok(d2.tr > 0, '花園主團絨（第二代）畫上一代花紋', d2);
  }
  await E(() => __qa.l5c.close());
  const tree = await E(() => { if (!window.__qa.l5 || !__qa.l5.tree) return null; __qa.l5.tree(); return true; }); await W(600);
  if (tree) { ok(await E(() => !!document.querySelector('[data-testid^=l5c-node-]')), '族譜卡有上一代花紋＋招式'); await E(() => __qa.l5 && __qa.l5.close && __qa.l5.close()); }

  console.log('# 屋仔');
  await E(() => __glimmer.house5 && __glimmer.house5.open && __glimmer.house5.open()); await W(1500);
  { const d3 = await statD(() => W(10), 1500); ok(d3.house > 0, '屋仔入面細佬／團絨畫花紋', d3); await clean(); await shot('house'); }
  await E(() => __glimmer.house5 && __glimmer.house5.close && __glimmer.house5.close()); await W(400);

  console.log('# 存檔');
  const raw0 = await E(() => __qa.l5c.raw()); await E(() => __glimmer.save());
  await load('q=high&hour=13&seed=21&ev=0', false); const raw1 = await E(() => __qa.l5c.raw());
  ok(JSON.stringify(raw1.inh) === JSON.stringify(raw0.inh), '重開：承傳資料仲喺度', [Object.keys(raw0.inh), Object.keys(raw1.inh)]);

  console.log('# ?l5c=0');
  await load('q=high&hour=13&seed=21&ev=0&l5c=0');
  ok(await E(() => !(window.__qa && __qa.l5c) && !__glimmer.pat5c && !Glimmer.long5a.LIVE.inherit_fast), '?l5c=0：5c 全停');
  ok(await E(() => !Glimmer.devmode.sections().some(s => s.id === 'l5c')), '?l5c=0：冇 5c 分組');
  ok(!(await vis('l5c-rail')) && await E(() => !document.getElementById('l5cov')), '?l5c=0：冇 5c UI');
  ok(await E(() => !!(window.__qa && __qa.l5 && __qa.l5b)), '?l5c=0：5a／5b 照用');

  ok(errs.length === 0, '冇 console error', errs.slice(0, 5));
  console.log('# 5c.1 未用 UI 冇載入');
  { const SKIP = ['parent_card_A3', 'parent_card_evo_still_moon', 'inherit_preview_bar', 'icon_trick', 'icon_pattern', 'pill_fast_on', 'pill_fast_tr', 'pill_fast_locked'].map(n => n + '@3x.png').concat('layout.json'), got = [...req5c];
    ok(got.some(n => /^chip_trick_/.test(n)) && got.includes('icon_fast@3x.png'), 'runtime 有載 5c UI（' + got.length + ' 個：' + got.slice(0, 4).join('、') + '…）');
    const bad = got.filter(n => SKIP.includes(n)); ok(!bad.length, 'runtime 冇載 build-single 跳過嘅 9 個 5c 檔', bad); }
  console.log(`\n結果：${pass} 通過，${fail} 失敗`);
  await browser.close(); process.exit(fail ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
