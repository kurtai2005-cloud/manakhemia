/* e2e-sprite48 — 新蛋系列 48px ⚙「試新寵」純預覽：主寵＝evo6 原樣（唔載 80px、唔換圖）；預覽 canvas 畫 48px（pivot、燈泡 glow、影）；唔改存檔；switchSeries hook not-ready。 */
const path = require('path');
let chromium;
for (const p of [process.env.PW, 'playwright-core', '/workspace/qa-live-s1/node_modules/playwright-core']) { try { if (p) { chromium = require(p).chromium; break; } } catch (e) { } }
if (!chromium) { console.error('找不到 playwright-core'); process.exit(2); }
const BASE = process.env.BASE || 'http://localhost:8138/index.html';
const SHOTS = process.env.OUT || path.join(__dirname, '..', '..', '..', 'screens') + '/';
require('fs').mkdirSync(SHOTS, { recursive: true });
let pass = 0, fail = 0;
const ok = (c, n, info) => { if (c) { pass++; console.log('  ✓ ' + n); } else { fail++; console.log('  ✗ ' + n + (info !== undefined ? ' → ' + JSON.stringify(info) : '')); } };
(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROME || '/usr/bin/google-chrome', args: ['--no-sandbox'] });
  const page = await (await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2 })).newPage();
  const errs = []; page.on('console', m => { if (m.type() === 'error') errs.push(m.text()); }); page.on('pageerror', e => errs.push('pageerror: ' + e.message));
  const E = (fn, a) => page.evaluate(fn, a);
  const Q = 'q=high&hour=13&seed=21&ev=0';
  await page.goto(BASE + '?' + Q); await E(() => { window.__noSaveOnHide = true; localStorage.clear(); });
  await page.goto(BASE + '?' + Q); await page.waitForFunction(() => window.__glimmer && __glimmer.nsLoad && __glimmer.evoLoad);
  await E(() => Promise.all([__glimmer.liveLoad.catch(() => null), __glimmer.evoLoad, __glimmer.nsLoad, __glimmer.spr80Load])); await E(() => { window.__noSaveOnHide = true; });
  let I = await E(() => __glimmer.newSeries.info());
  ok(I.enabled && I.loaded && !I.error && I.atlas.w === 192 && I.atlas.h === 1152 && I.atlas.frames === 96, '48px atlas 載入 192×1152／96 幀', I);
  ok(I.activeSeries === 'tuanrong' && I.preview === null, '主系列仍係團絨、預設冇預覽', I);
  const S80 = await E(() => __glimmer.sprites80.info()); ok(!S80.enabled && !S80.loaded && S80.key === null, '主寵 80px path 停用（唔載、唔換）', S80);
  for (const [st, br, fk] of [['adult', 'ember', 'evo_guard_ember'], ['elder', 'moon', null], ['juvenile', null, null]]) {
    await E(([a, b]) => __glimmer.evo.setStage(a, b), [st, br]); await page.waitForTimeout(400); await E(() => __glimmer.forceBeh('idle')); await page.waitForTimeout(250);
    const ev = await E(() => __glimmer.evo.info()), pd = await E(() => ({ s80: (__glimmer.renderer.petDraw || {}).s80 || null }));
    ok(!pd.s80 && (!fk || ev.drawForm === fk) && /^evo_/.test(ev.drawForm || ''), st + (br ? ' ' + br : '') + ' → 舊 evo sprite（' + ev.drawForm + '）', [ev.drawForm, pd]); }
  const save0 = await E(() => { __glimmer.save(); return localStorage.getItem(window.Glimmer.data.PARAMS.saveKey); });
  const st0 = await E(() => JSON.stringify({ st: __glimmer.state.stage, f: __glimmer.state.form, tp: __glimmer.state.settings.tryPet || null }));
  const openPanel = async () => { await page.click('#gear'); await page.waitForSelector('[data-testid=trypet-open]'); await page.click('[data-testid=trypet-open]'); await page.waitForSelector('[data-testid=trypet-panel]'); await page.waitForTimeout(250); };
  const isOpen = () => E(() => !!document.querySelector('[data-testid=trypet-panel]'));
  const mainBack = () => E(() => !document.querySelector('[data-testid=trypet-panel]') && getComputedStyle(document.getElementById('modal')).display === 'none');
  await openPanel();
  ok(await E(() => getComputedStyle(document.getElementById('modal')).display === 'none'), '開預覽：設定已關（面板直接疊喺主畫面）');
  const geo = await E(() => { const st = document.getElementById('modal').parentNode.getBoundingClientRect(), bx = document.querySelector('[data-testid=trypet-box]').getBoundingClientRect(), x = document.querySelector('[data-testid=trypet-close]').getBoundingClientRect();
    return { stH: st.height, stW: st.width, bxH: bx.height, bxTop: bx.top, bxBot: bx.bottom, bxR: bx.right, xw: x.width, xh: x.height, xTop: x.top, xR: x.right, vh: innerHeight }; });
  ok(geo.bxH <= geo.stH * 0.6 + 1 && geo.bxH <= geo.vh * 0.6 + 1, '面板高 ≤ 60%（' + Math.round(geo.bxH) + '／' + Math.round(geo.stH) + '）', geo);
  ok(geo.xw >= 44 && geo.xh >= 44, '✕ ≥44px', [geo.xw, geo.xh]);
  ok(geo.xTop >= geo.bxTop && geo.xTop - geo.bxTop < 12 && geo.bxR - geo.xR < 12 && geo.xTop >= 0 && geo.xR <= geo.stW + 1, '✕ 喺面板右上角、畫面內', geo);
  const bx = await E(() => ['trypet-prev', 'trypet-next', 'trypet-close'].map(t => { const r = document.querySelector('[data-testid=' + t + ']').getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height)]; }));
  ok(bx.every(([w, h]) => w >= 48 && h >= 48), '◀ ▶ ✕ ≥48px', bx);
  const lab = () => E(() => document.querySelector('[data-testid=trypet-label]').textContent);
  ok((await lab()) === 'A1 滴滴', '開面板預設 A1 滴滴', await lab());
  const BA = await E(() => fetch('art/sprites48/bulb_anchors_48.json').then(r => r.json()));
  { const seen = new Set(), good = []; for (let i = 0; i < 30; i++) { await page.waitForTimeout(47); const L = (await E(() => __glimmer.newSeries.info())).last; if (!L) continue; seen.add(L.frame);
      const pf = BA.creatures[L.key].perFrame[L.frame]; good.push(L.key === 'A1' && L.scale === 3 && Math.abs(L.bulb[0] - (L.ox + (pf[0] + 0.5) * 3)) < 1e-6 && Math.abs(L.bulb[1] - (L.oy + (pf[1] + 0.5) * 3)) < 1e-6 && L.glowR === 27 && L.glowA >= 0.24 - 1e-6 && L.glowA <= 0.6 + 1e-6); }
    ok(good.length > 15 && good.every(Boolean), '預覽：燈泡 glow 喺 perFrame anchor、r 9×3、alpha 0.42±0.18', good.length);
    ok([0, 1, 2, 3].every(f => seen.has(f)), 'idle 4 幀都出', [...seen]); }
  { const px = await E(() => { const NS = __glimmer.newSeries, cv = document.querySelector('[data-testid=trypet-canvas]'), L = NS.info().last; const d = cv.getContext('2d').getImageData(L.ox, L.oy, 144, 144).data; let op = 0; for (let i = 3; i < d.length; i += 4) if (d[i] === 255) op++; return { op }; });
    ok(px.op > 600 * 9 * 0.9, '預覽畫布有實體像素', px); }
  await page.click('[data-testid=trypet-next]'); await page.click('[data-testid=trypet-next]'); await page.click('[data-testid=trypet-prev]'); await page.waitForTimeout(200);
  ok((await lab()).indexOf('A2') === 0, '▶▶◀ → A2', await lab());
  await page.click('[data-testid=trypet-prev]'); await page.click('[data-testid=trypet-prev]'); await page.waitForTimeout(300);
  ok((await lab()).indexOf('H3') === 0, '◀ 循環 H3', await lab());
  const pd1 = await E(() => ({ s80: (__glimmer.renderer.petDraw || {}).s80 || null, fk: __glimmer.evo.info().drawForm }));
  ok(!pd1.s80 && /^evo_/.test(pd1.fk || ''), '預覽緊：主寵照畫舊 evo sprite', pd1);
  await page.click('[data-testid=trypet-close]'); await page.waitForTimeout(250);
  ok(await mainBack(), '✕ → 即返主畫面（冇設定、冇面板）');
  ok((await E(() => __glimmer.newSeries.info())).preview === null, '關咗：預覽 key 清走');
  await openPanel(); await page.mouse.click(10, 830); await page.waitForTimeout(250);
  ok(await mainBack(), '撳面板外面 → 關、返主畫面');
  await openPanel(); await page.click('[data-testid=trypet-canvas]'); await page.waitForTimeout(150);
  ok(await isOpen(), '撳面板入面唔會關');
  await page.goBack(); await page.waitForTimeout(400);
  ok(await mainBack() && /index\.html/.test(page.url()), '返回鍵（history back）→ 關、仍喺遊戲', page.url());
  await openPanel(); await page.keyboard.press('Escape'); await page.waitForTimeout(200);
  ok(await mainBack(), 'Esc → 關');
  { await openPanel(); await page.click('[data-testid=trypet-close]'); await page.waitForTimeout(300); ok(await mainBack() && /index\.html/.test(page.url()), '✕ 之後 history 已退返（唔會留低空返回步）', page.url());
    ok(await E(() => !(history.state && history.state.nspanel)), 'history 冇殘留 nspanel entry'); }
  await page.goto(BASE + '?' + Q); await page.waitForFunction(() => window.__glimmer && __glimmer.nsLoad); await E(() => Promise.all([__glimmer.nsLoad, __glimmer.evoLoad])); await E(() => { window.__noSaveOnHide = true; });
  // 細畫面（360×640）都放得入
  await page.setViewportSize({ width: 360, height: 640 }); await page.waitForTimeout(200); await openPanel();
  { const g = await E(() => { const st = document.getElementById('modal').parentNode.getBoundingClientRect(), x = document.querySelector('[data-testid=trypet-close]').getBoundingClientRect(), bx = document.querySelector('[data-testid=trypet-box]').getBoundingClientRect(); return { x: [x.left, x.top, x.right, x.bottom], vw: innerWidth, vh: innerHeight, bh: bx.height, sh: st.height }; });
    ok(g.x[0] >= 0 && g.x[1] >= 0 && g.x[2] <= g.vw && g.x[3] <= g.vh && g.bh <= g.sh * 0.6 + 1, '360×640：✕ 喺畫面內、面板 ≤60%', g); }
  await page.screenshot({ path: SHOTS + 'sprite48-panel-small.png' });
  await page.click('[data-testid=trypet-close]'); await page.setViewportSize({ width: 390, height: 844 });
  const st1 = await E(() => JSON.stringify({ st: __glimmer.state.stage, f: __glimmer.state.form, tp: __glimmer.state.settings.tryPet || null }));
  ok(st0 === st1, '唔改 stage／form／settings.tryPet', [st0, st1]);
  const save1 = await E(() => localStorage.getItem(window.Glimmer.data.PARAMS.saveKey));
  ok(!/nspanel|preview/.test(save1 || '') && (JSON.parse(save1).settings || {}).tryPet == null, '存檔冇寫入預覽');
  const sw = await E(() => __glimmer.newSeries.switchSeries('fromref48'));
  ok(sw.ok === false && sw.reason === 'not-ready' && sw.active === 'tuanrong', 'switchSeries hook：not-ready（等遊策）', sw);
  // 設定 modal 本身都要捲得到「關閉」
  await page.setViewportSize({ width: 360, height: 640 }); await page.click('#gear'); await page.waitForSelector('[data-testid=modal-btn-0]');
  { const g = await E(() => { const m = document.getElementById('mbox'); return { sh: m.scrollHeight, ch: m.clientHeight, ov: getComputedStyle(m).overflowY, mb: m.getBoundingClientRect().bottom, vh: innerHeight }; });
    ok(g.mb <= g.vh + 1 && (g.sh <= g.ch || g.ov === 'auto'), '設定框唔超出畫面（入面 scroll）', g); }
  await page.click('[data-testid=modal-btn-0]'); await page.waitForTimeout(200); ok(await mainBack(), '設定「關閉」撳得到');
  await page.setViewportSize({ width: 390, height: 844 });
  // 舊存檔有 settings.tryPet（sprite80 版留低）→ 主寵都唔換
  await E(() => { __glimmer.state.settings.tryPet = 'C2'; __glimmer.save(); });
  await page.goto(BASE + '?' + Q); await page.waitForFunction(() => window.__glimmer && __glimmer.nsLoad); await E(() => Promise.all([__glimmer.nsLoad, __glimmer.evoLoad])); await E(() => { window.__noSaveOnHide = true; __glimmer.forceBeh('idle'); }); await page.waitForTimeout(400);
  const pd2 = await E(() => ({ s80: (__glimmer.renderer.petDraw || {}).s80 || null, p: __glimmer.newSeries.info().preview }));
  ok(!pd2.s80 && pd2.p === null, '舊存檔 tryPet=C2 → 主寵唔換、預覽唔自動開', pd2);
  await page.goto(BASE + '?' + Q + '&ns=0'); await page.waitForFunction(() => window.__glimmer && __glimmer.nsLoad); await E(() => __glimmer.nsLoad); await E(() => { window.__noSaveOnHide = true; });
  ok(!(await E(() => __glimmer.newSeries.info())).enabled, '?ns=0 停用新系列預覽');
  ok(errs.length === 0, '冇 console error', errs.slice(0, 5));
  console.log(`結果：${pass} 通過，${fail} 失敗`); await browser.close(); process.exit(fail ? 1 : 0);
})().catch(e => { console.error('Error', e); process.exit(1); });
