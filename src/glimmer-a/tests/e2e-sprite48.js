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
  await page.click('#gear'); await page.waitForSelector('[data-testid=trypet]');
  const bx = await E(() => ['trypet-prev', 'trypet-next', 'trypet-off'].map(t => { const r = document.querySelector('[data-testid=' + t + ']').getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height)]; }));
  ok(bx.every(([w, h]) => w >= 48 && h >= 48), '◀ ▶ 關 ≥48px', bx);
  const lab = () => E(() => document.querySelector('[data-testid=trypet-label]').textContent);
  const cvVis = () => E(() => getComputedStyle(document.querySelector('[data-testid=trypet-canvas]')).display !== 'none');
  ok(/^關/.test(await lab()) && !(await cvVis()), '預設「關」、冇預覽畫布', await lab());
  await page.click('[data-testid=trypet-next]'); await page.waitForTimeout(400);
  ok((await lab()) === 'A1 滴滴' && await cvVis(), '▶ → A1 滴滴、預覽畫布出現', await lab());
  const BA = await E(() => fetch('art/sprites48/bulb_anchors_48.json').then(r => r.json()));
  { const seen = new Set(), good = []; for (let i = 0; i < 30; i++) { await page.waitForTimeout(47); const L = (await E(() => __glimmer.newSeries.info())).last; if (!L) continue; seen.add(L.frame);
      const pf = BA.creatures[L.key].perFrame[L.frame]; good.push(L.key === 'A1' && L.scale === 3 && Math.abs(L.bulb[0] - (L.ox + (pf[0] + 0.5) * 3)) < 1e-6 && Math.abs(L.bulb[1] - (L.oy + (pf[1] + 0.5) * 3)) < 1e-6 && L.glowR === 27 && L.glowA >= 0.24 - 1e-6 && L.glowA <= 0.6 + 1e-6); }
    ok(good.length > 15 && good.every(Boolean), '預覽：燈泡 glow 喺 perFrame anchor、r 9×3、alpha 0.42±0.18', good.length);
    ok([0, 1, 2, 3].every(f => seen.has(f)), 'idle 4 幀都出', [...seen]); }
  { const px = await E(() => { const NS = __glimmer.newSeries, cv = document.querySelector('[data-testid=trypet-canvas]'), L = NS.info().last; const d = cv.getContext('2d').getImageData(L.ox, L.oy, 144, 144).data; let op = 0; for (let i = 3; i < d.length; i += 4) if (d[i] === 255) op++; return { op }; });
    ok(px.op > 600 * 9 * 0.9, '預覽畫布有 3x 實體像素', px); }
  await page.click('[data-testid=trypet-next]'); await page.click('[data-testid=trypet-next]'); await page.click('[data-testid=trypet-prev]'); await page.waitForTimeout(200);
  ok((await lab()).indexOf('A2') === 0, '▶▶◀ → A2', await lab());
  await page.click('[data-testid=trypet-off]'); await page.click('[data-testid=trypet-prev]'); await page.waitForTimeout(300);
  ok((await lab()).indexOf('H3') === 0, '關 → ◀ 循環 H3', await lab());
  await page.screenshot({ path: SHOTS + 'sprite48-preview-H3.png' });
  const pd1 = await E(() => ({ s80: (__glimmer.renderer.petDraw || {}).s80 || null, fk: __glimmer.evo.info().drawForm }));
  ok(!pd1.s80 && /^evo_/.test(pd1.fk || ''), '預覽緊：主寵照畫舊 evo sprite', pd1);
  const st1 = await E(() => JSON.stringify({ st: __glimmer.state.stage, f: __glimmer.state.form, tp: __glimmer.state.settings.tryPet || null }));
  ok(st0 === st1, '唔改 stage／form／settings.tryPet', [st0, st1]);
  const save1 = await E(() => localStorage.getItem(window.Glimmer.data.PARAMS.saveKey));
  ok(save1 === save0 || (JSON.parse(save1).settings || {}).tryPet == null, '存檔冇寫入預覽', null);
  const sw = await E(() => __glimmer.newSeries.switchSeries('fromref48'));
  ok(sw.ok === false && sw.reason === 'not-ready' && sw.active === 'tuanrong', 'switchSeries hook：not-ready（等遊策）', sw);
  await E(() => { const b = [...document.querySelectorAll('.btn')].find(x => x.textContent === '關閉'); if (b) b.click(); });
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
