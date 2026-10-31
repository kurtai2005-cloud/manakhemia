/* 《微光小圃》 e2e-evo6 — 六階段／四分支真美術（遊美 A+B+C+D @ d267b4e）、DEV 跳階段／分支掣、螢絨條件顯示、化光、舊存檔遷移、浮動 overlay 大細。
   截圖 → SHOTS（預設 /workspace/live-s2/screens/）evo6-*.png。直向 390×844。 */
const path = require('path');
let chromium;
for (const p of [process.env.PW, 'playwright-core', '/workspace/qa-live-s1/node_modules/playwright-core']) { try { if (p) { chromium = require(p).chromium; break; } } catch (e) { } }
if (!chromium) { console.error('找不到 playwright-core'); process.exit(2); }
const BASE = process.env.BASE || 'http://localhost:8138/index.html';
const SHOTS = process.env.SHOTS || path.join(__dirname, '..', '..', '..', 'screens') + '/';
require('fs').mkdirSync(SHOTS, { recursive: true });
let pass = 0, fail = 0;
const ok = (c, n, info) => { if (c) { pass++; console.log('  ✓ ' + n); } else { fail++; console.log('  ✗ ' + n + (info !== undefined ? ' → ' + JSON.stringify(info) : '')); } };

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROME || '/usr/bin/google-chrome', args: ['--no-sandbox', '--autoplay-policy=no-user-gesture-required'] });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2 });
  const page = await ctx.newPage();
  const errs = [];
  page.on('console', m => { if (m.type() === 'error') errs.push(m.type() + ': ' + m.text()); });
  page.on('pageerror', e => errs.push('pageerror: ' + e.message));
  const E = (fn, arg) => page.evaluate(fn, arg);
  const shot = async (n) => { await page.waitForTimeout(250); await page.screenshot({ path: SHOTS + 'evo6-' + n + '.png' }); console.log('  📷 evo6-' + n); };
  const ready = async () => { await page.waitForFunction(() => window.__glimmer && __glimmer.evoLoad).catch(() => { }); await E(() => Promise.all([__glimmer.liveLoad, __glimmer.evoLoad])); await page.waitForTimeout(300); };
  const load = async (qs, clear) => {
    if (clear) { await page.goto(BASE + '?' + qs); await E(() => { window.__noSaveOnHide = true; localStorage.clear(); }); }
    await page.goto(BASE + '?' + qs); await ready(); await E(() => { window.__noSaveOnHide = true; });
  };
  const closeModals = async () => { for (let i = 0; i < 6; i++) { const v = await E(() => getComputedStyle(document.getElementById('modal')).display !== 'none'); if (!v) break; await page.click('[data-testid="modal-btn-' + (await E(() => document.querySelectorAll('#mbox .btn').length > 1 ? 1 : 0)) + '"]').catch(() => { }); await page.waitForTimeout(120); } };
  const settle = () => E(() => { const s = __glimmer.state; Object.assign(s.needs, { hunger: 100, mood: 80, clean: 100, energy: 100 }); s.poops = 0; s.sleeping = false; __qa.pet.force('stay'); const b = __glimmer.beh; b.x = 0; b.dir = 1; });
  const dev = (tid) => page.click('[data-testid="' + tid + '"]');

  console.log('# 載入 evo 美術（12 form）');
  await load('q=high&hour=13&seed=21&ev=0&dev=1', true);
  const ld = await E(() => ({ ok: Object.keys(__glimmer.renderer.evoOK || {}).sort(), err: __glimmer.renderer.evoError, ready: __glimmer.evoReady, lv: __glimmer.renderer.lv ? Object.keys(__glimmer.renderer.lv.atlas) : [] }));
  ok(ld.ok.length === 12 && !ld.err && ld.ready, '12 個 evo form atlas 全部載入', ld);
  ok(['evo_dot', 'evo_guard_soft', 'evo_still_lumi'].every(k => ld.lv.includes(k)), 'evo form 掛入生命感 lv.atlas（noface＋kit 五官）', ld.lv);

  console.log('# DEV 抽屜：階段／分支掣（舊「形態」「進化」掣保留）');
  const btns = await E(() => [...document.querySelectorAll('[data-testid^="dev-stage-"],[data-testid^="dev-branch-"],[data-testid^="dev-form-"],[data-testid^="dev-evolve-"],[data-testid="dev-fade"]')].map(b => [b.dataset.testid, b.offsetParent !== null]));
  const want = ['dev-stage-egg', 'dev-stage-newborn', 'dev-stage-sprout', 'dev-stage-juvenile', 'dev-stage-adult', 'dev-stage-elder', 'dev-stage-next', 'dev-fade', 'dev-branch-lumi', 'dev-branch-bright', 'dev-branch-soft', 'dev-branch-dust', 'dev-form-egg', 'dev-form-sprout', 'dev-form-bright', 'dev-form-lumi', 'dev-evolve-soft'];
  ok(want.every(t => btns.some(b => b[0] === t && b[1])), '新掣（6 階段＋下一階段＋化光＋4 分支）同舊掣都喺度', want.filter(t => !btns.some(b => b[0] === t && b[1])));
  ok(await E(() => document.querySelector('[data-testid=dev-stage-row]').getBoundingClientRect().right <= innerWidth + 1 && document.querySelector('[data-testid=dev-branch-row]').getBoundingClientRect().right <= innerWidth + 1), '直向：階段／分支行唔超出闊度');
  await E(() => document.querySelector('[data-testid=dev-branch-row]').scrollIntoView({ block: 'end' })); await shot('dev-panel');

  console.log('# 每階段（DEV 掣跳）→ 正確 evo form、大細、overlay info、截圖');
  const SZ = { egg: ['evo_egg', 24], newborn: ['evo_dot', 28], sprout: ['evo_sprout', 32], juvenile: ['evo_hop', 38] };
  for (const st of ['egg', 'newborn', 'sprout', 'juvenile']) {
    await dev('dev-stage-' + st); await closeModals(); await settle(); await page.waitForTimeout(450);
    const r = await E(() => ({ info: __glimmer.evo.info(), ov: __glimmer.evo.overlayInfo(), f: __qa.pet.face(), pd: __glimmer.renderer.petDraw, name: document.getElementById('stagename').textContent, on: [...document.querySelectorAll('[data-testid^="dev-stage-"].on')].map(b => b.dataset.testid) }));
    const [fk, sz] = SZ[st];
    ok(r.info.stage === st && r.info.drawForm === fk && r.on.includes('dev-stage-' + st), `${st}：DEV 掣跳到 → 畫 ${fk}`, [r.info.stage, r.info.drawForm, r.on]);
    ok(r.ov.size === sz && r.ov.pivot[0] === sz / 2 && r.ov.pivot[1] === sz - 3 && r.ov.evoForm === fk && r.ov.sizeDp === Math.round(sz * 1.625), `${st}：overlayInfo ${sz}px pivot (${sz / 2},${sz - 3})`, r.ov);
    if (st === 'egg') ok(r.pd && r.pd.evo === 'evo_egg' && r.pd.w === 24, '光卵畫 evo_egg（24px）', r.pd);
    else ok(r.f.form === fk && r.f.evo && r.f.live && r.f.faceVisible !== undefined, `${st}：生命感 noface＋kit（form ${r.f.form}）`, r.f);
    ok(r.name === ({ egg: '光卵', newborn: '絨點', sprout: '芽崽', juvenile: '跳跳期' })[st], `${st}：階段名「${r.name}」`);
    await shot(st);
  }
  for (const stg of ['adult', 'elder']) {
    for (const [f, k] of [['lumi', 'lumi'], ['bright', 'radiant'], ['soft', 'soft'], ['dust', 'dust']]) {
      await dev('dev-stage-' + stg); await dev('dev-branch-' + f); await closeModals(); await settle(); await page.waitForTimeout(450);
      const r = await E(() => ({ info: __glimmer.evo.info(), ov: __glimmer.evo.overlayInfo(), f: __qa.pet.face(), on: [...document.querySelectorAll('[data-testid^="dev-branch-"].on')].map(b => b.dataset.testid) }));
      const fk = (stg === 'adult' ? 'evo_guard_' : 'evo_still_') + k, sz = stg === 'adult' ? 44 : 48;
      ok(r.info.stage === stg && r.info.form === f && r.f.form === fk && r.f.live && r.on.includes('dev-branch-' + f), `${stg}/${f} → ${fk}（真美術，生命感五官）`, [r.info.stage, r.info.form, r.f.form, r.f.live, r.on]);
      ok(r.ov.size === sz && r.ov.pivot[1] === sz - 3, `${stg}/${f} overlay ${sz}px`, r.ov);
      if (f === 'lumi' || f === 'bright') ok(r.f.bulb && r.f.stat.bulb > 0, `${stg}/${f} 燈泡 glow 跟 bulb anchor`, r.f.bulb);
      await shot(stg + '-' + k);
    }
  }

  console.log('# 生命感 clip 喺 evo form：有就真 clip，冇就最近 clip（placeholder 清單）');
  await dev('dev-stage-adult'); await dev('dev-branch-soft'); await closeModals(); await settle();
  await E(() => __qa.pet.pause(true));
  let r = await E(() => { const b = __glimmer.beh; b.show.clip = 'nuzzle_purr'; b.show.frame = 1; return new Promise(res => requestAnimationFrame(() => requestAnimationFrame(() => res(__qa.pet.face())))); });
  ok(r.form === 'evo_guard_soft' && r.drawnClip === 'nuzzle' && r.fallbackFrom === 'nuzzle_purr', '守夜者・柔光冇 nuzzle_purr → 畫 nuzzle（fallback）', r);
  await dev('dev-branch-dust'); await settle(); await E(() => __qa.pet.pause(true));
  r = await E(() => { const b = __glimmer.beh; b.show.clip = 'nuzzle_purr'; b.show.frame = 1; return new Promise(res => requestAnimationFrame(() => requestAnimationFrame(() => res(__qa.pet.face())))); });
  ok(r.form === 'evo_guard_dust' && r.drawnClip === 'nuzzle_purr' && !r.fallbackFrom, '守夜者・微塵有自己 nuzzle_purr（取代舊微塵 fallback）', r);
  await dev('dev-stage-elder'); await dev('dev-branch-soft'); await settle(); await E(() => __qa.pet.pause(true));
  r = await E(() => { const b = __glimmer.beh; b.show.clip = 'reunion_happy'; b.show.frame = 2; return new Promise(res => requestAnimationFrame(() => requestAnimationFrame(() => res(__qa.pet.face())))); });
  ok(r.form === 'evo_still_soft' && r.drawnClip === 'reunion_happy' && !r.fallbackFrom, '靜光（batch D 全套）有 reunion_happy，唔靠 MVP fallback', r);
  await E(() => { __qa.pet.pause(false); });
  // 實時跑一陣：唔同 clip 都冇錯
  await settle(); for (const k of ['walk', 'jump', 'play', 'nap']) { await E((k) => __glimmer.forceBeh(k), k); await page.waitForTimeout(500); }
  ok(errs.length === 0, '各階段／分支實時畫：冇 console error', errs.slice(0, 5));

  console.log('# DEV 下一階段（正常規則判分支）＋螢絨條件顯示');
  await dev('dev-stage-juvenile'); await closeModals();
  await E(() => { const s = __glimmer.state; s.cq = 60; s.evo.evIn.sprout = { firefly_walk: 1 }; s.evo.care.sprout = { all: 5, night: 2 }; __qa.dev.sync(); });
  const lumiTxt = await E(() => document.querySelector('[data-testid=dev-lumi-state]').textContent);
  ok(/螢火1✓/.test(lumiTxt) && /CQ60✓/.test(lumiTxt) && /夜40%\/5✓/.test(lumiTxt), '螢絨條件讀數（螢火／CQ／夜晚 %）', lumiTxt);
  await dev('dev-stage-next'); await page.waitForTimeout(300);
  r = await E(() => ({ i: __glimmer.evo.info(), kind: document.getElementById('mbox').dataset.kind, title: document.querySelector('#mbox h2').textContent }));
  ok(r.i.stage === 'adult' && r.i.form === 'lumi' && r.kind === 'evolve' && /螢絨/.test(r.title), '跳跳期 ▶下一階段 → 守夜者・螢絨（隱藏分支）＋進化彈窗', r);
  await shot('evolve-lumi'); await closeModals();
  await dev('dev-stage-next'); await page.waitForTimeout(300);
  r = await E(() => ({ i: __glimmer.evo.info(), kind: document.getElementById('mbox').dataset.kind }));
  ok(r.i.stage === 'elder' && r.i.form === 'lumi' && r.kind === 'elder', '守夜者 ▶ → 靜光（分支保留）＋靜光彈窗', r); await closeModals();

  console.log('# 化光（要確認；冇壞結局）');
  await dev('dev-stage-next'); await page.waitForTimeout(300);
  r = await E(() => ({ i: __glimmer.evo.info(), kind: document.getElementById('mbox').dataset.kind, n: document.querySelectorAll('#mbox .btn').length }));
  ok(r.i.fadeReady && r.i.stage === 'elder' && r.kind === 'fade' && r.n === 2, '靜光完 → 問「陪佢化光／再陪多陣」', r);
  await shot('fade-ask');
  await page.click('[data-testid="modal-btn-1"]'); await page.waitForTimeout(200);
  ok(await E(() => __glimmer.state.stage === 'elder' && __glimmer.state.fadeReady), '揀「再陪多陣」→ 仲係靜光');
  await dev('dev-fade'); await page.waitForTimeout(400);
  r = await E(() => ({ i: __glimmer.evo.info(), kind: document.getElementById('mbox').dataset.kind }));
  ok(r.i.stage === 'egg' && r.i.gen === 2 && r.i.memorial.length === 1 && r.i.memorial[0].form === 'lumi' && r.kind === 'fadeDone', 'DEV 化光 → 新光卵（第 2 代）＋紀念', r);
  await shot('fade-done'); await closeModals();

  console.log('# 舊存檔（v1）→ 遷移最近階段（瀏覽器）');
  await page.goto(BASE + '?q=high&hour=13&seed=21&ev=0'); await E(() => { window.__noSaveOnHide = true; const now = Date.now(); const s = JSON.parse(localStorage.getItem('glimmer_save_v1') || 'null') || {}; Object.assign(s, { v: 1, stage: 'sprout', form: null, growthSec: 10 * 3600, lastSeen: now, lastSaveTime: now }); delete s.evo; delete s.gen; delete s.memorial; localStorage.setItem('glimmer_save_v1', JSON.stringify(s)); });
  await page.goto(BASE + '?q=high&hour=13&seed=21&ev=0'); await ready();
  r = await E(() => ({ i: __glimmer.evo.info(), v: __glimmer.state.v }));
  ok(r.v === 2 && r.i.stage === 'sprout' && Math.abs(r.i.growthH - 4) < 0.05 && r.i.migrated && r.i.migrated.stage === 'sprout', '舊 v1 芽崽 10h → v2 芽崽 4h（migrated 標記）', r);
  ok(await E(() => document.getElementById('stagename').textContent === '芽崽'), 'UI 顯示新階段名');

  console.log('# ?evo=0 → 舊 form（fallback 路徑仍可用）');
  await page.goto(BASE + '?q=high&hour=13&seed=21&ev=0&evo=0'); await ready(); await E(() => { window.__noSaveOnHide = true; __glimmer.evo.setStage('adult', 'soft'); }); await page.waitForTimeout(400);
  r = await E(() => __qa.pet.face());
  ok(r.form === 'soft' && !r.evo, '停用 evo → 用返舊柔光 atlas', [r.form, r.evo]);
  ok(errs.length === 0, '全程冇 console error', errs.slice(0, 5));
  await browser.close();
  console.log(`\n結果：${pass} 通過，${fail} 失敗`);
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error('Error', e); process.exit(1); });
