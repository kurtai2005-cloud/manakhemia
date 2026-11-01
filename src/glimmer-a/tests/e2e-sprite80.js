/* 《微光小圃》 e2e-sprite80 — 遊美 80px 正式版寵物 smoke：pets_idle_80 atlas 載入、pivot (40,77) 腳底落 art (97,292)、燈泡 glow 喺 bulb anchor（含 bob 幀）、
   idle 4 幀節奏、form/stage 對應、非 idle clip fallback、?spr=old 退舊、?spr80=KEY 強制。截圖 → OUT（預設 /workspace/live-s2/screens/）sprite80-*.png。 */
const path = require('path');
let chromium;
for (const p of [process.env.PW, 'playwright-core', '/workspace/qa-live-s1/node_modules/playwright-core']) { try { if (p) { chromium = require(p).chromium; break; } } catch (e) { } }
if (!chromium) { console.error('找不到 playwright-core'); process.exit(2); }
const BASE = process.env.BASE || 'http://localhost:8138/index.html';
const SHOTS = process.env.OUT || process.env.SHOTS || path.join(__dirname, '..', '..', '..', 'screens') + '/';
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
  const load = async (qs) => {
    await page.goto(BASE + '?' + qs); await E(() => { window.__noSaveOnHide = true; localStorage.clear(); });
    await page.goto(BASE + '?' + qs); await page.waitForFunction(() => window.__glimmer && __glimmer.spr80Load && __glimmer.evoLoad);
    await E(() => Promise.all([__glimmer.liveLoad.catch(() => null), __glimmer.evoLoad, __glimmer.spr80Load])); await E(() => { window.__noSaveOnHide = true; });
  };
  const stage = async (st, br) => { await E(([a, b]) => __glimmer.evo.setStage(a, b), [st, br]); await page.waitForTimeout(500); };
  const info = () => E(() => __glimmer.sprites80.info());
  const idle = async () => { await E(() => __glimmer.forceBeh('idle')); await page.waitForTimeout(250); };
  const Q = 'q=high&hour=13&seed=21&ev=0';

  console.log('# 預設開：atlas 載入');
  await load(Q);
  let I = await info();
  ok(I.enabled && I.loaded && !I.error, 'PARAMS.sprites80 預設開、atlas 載入', I);
  ok(I.atlas && I.atlas.w === 320 && I.atlas.h === 1920 && I.atlas.frames === 96, 'pets_idle_80 320×1920、96 幀', I.atlas);

  console.log('# 成年火系 → C2 火角獸：腳底 (97,292)、燈泡 anchor');
  await stage('adult', 'ember'); await idle(); I = await info();
  ok(I.key === 'C2' && I.used && I.drawn === 'C2', 'adult ember → C2（idle 用 80px）', I);
  ok(I.drawX === 57 && I.drawY === 215 && I.footY === 292, '80px 框畫喺 (57,215)＝腳底 pivot (40,77) 落 (97,292)', [I.drawX, I.drawY, I.footY]);
  const BA = await E(() => fetch('art/sprites80/bulb_anchors_80.json').then(r => r.json()));
  const seen = new Set(), budOk = [];
  for (let i = 0; i < 40; i++) { await page.waitForTimeout(53); const J = await info(); if (!J.used) continue; seen.add(J.frame);
    const pf = BA.creatures.C2.perFrame[J.frame], mirX = 97 + (pf[0] - 40) * -1, x0 = 57 + pf[0];
    budOk.push((J.bud.x === x0 || J.bud.x === mirX) && J.bud.y === 215 + pf[1] && J.glow && J.glow.r === 14 && Math.abs(J.glow.x - J.bud.x) < 0.01 && J.glow.pulse >= 0.24 - 1e-6 && J.glow.pulse <= 0.6 + 1e-6 && J.glow.a > 0 && !!J.glow.mood); }
  ok(budOk.length > 20 && budOk.every(Boolean), '燈泡 glow 喺 bulb anchor perFrame（幀 1 bob 低 1px）、r 14、alpha 0.42±0.18（× 燈泡情緒）', budOk.length);
  ok([0, 1, 2, 3].every(f => seen.has(f)), 'idle 4 幀都出（260/180/260/140）', [...seen]);
  const pr = await E(() => __glimmer.renderer.petRect);
  ok(pr && pr.opaque && pr.x >= 57 && pr.x + pr.w <= 137 && pr.y >= 215 && pr.y + pr.h <= 295, '觸控框＝80px 實體框', pr);
  await page.screenshot({ path: SHOTS + 'sprite80-C2.png' });

  console.log('# 像素：L2 寵物層 vs atlas 幀 alpha（pivot 對位）');
  { const px = await E(async () => { const r = __glimmer.renderer, L2 = r.live && r.live[2]; if (!L2) return { err: 'no L2' };
      const pd = r.petDraw, f = pd.s80f, mir = (__glimmer.beh.dir < 0) ? -1 : 1;
      const at = document.createElement('canvas'); at.width = 80; at.height = 80; const ag = at.getContext('2d'); ag.drawImage(r.s80.img, f * 80, 4 * 80 * 0 + 'ABCDEFGH'.indexOf(pd.s80[0]) * 240 + (+pd.s80[1] - 1) * 80, 80, 80, 0, 0, 80, 80);
      const A = ag.getImageData(0, 0, 80, 80).data, P = L2.getContext('2d').getImageData(pd.drawX + 14, pd.drawY + 12, 80, 80).data;
      const B = document.createElement('canvas'); B.width = 80; B.height = 80; const bg = B.getContext('2d'); bg.drawImage(r.layers[2], -(pd.drawX + 14), -(pd.drawY + 12)); const Bd = bg.getImageData(0, 0, 80, 80).data;
      let op = 0, hit = 0, clear = 0, clearSame = 0;
      for (let y = 0; y < 80; y++) for (let x = 0; x < 80; x++) { const sx = mir > 0 ? x : 79 - x, ai = (y * 80 + sx) * 4 + 3, i = (y * 80 + x) * 4;
        const diff = Math.abs(P[i] - Bd[i]) + Math.abs(P[i + 1] - Bd[i + 1]) + Math.abs(P[i + 2] - Bd[i + 2]) + Math.abs(P[i + 3] - Bd[i + 3]);
        if (A[ai] === 255) { op++; if (diff > 6) hit++; } else if (A[ai] === 0 && y < 60) { clear++; if (diff <= 6) clearSame++; } }
      return { op, hit, clear, clearSame, f, mir }; });
    ok(px.op > 600 && px.hit / px.op > 0.97, 'L2 畫布：80px 幀實體像素全部畫咗（腳底對位）', px);
    ok(px.clear > 0 && px.clearSame / px.clear > 0.9, 'L2 畫布：80px 幀透明位冇畫嘢（冇錯位）', px); }

  console.log('# 其他對應');
  await stage('elder', 'moon'); await idle(); I = await info(); ok(I.key === 'G3' && I.used, 'elder moon → G3', I.key);
  await stage('adult', 'tide'); await idle(); I = await info(); ok(I.key === 'A2' && I.used, 'adult tide → A2', I.key);
  await stage('adult', 'bright'); await idle(); I = await info(); ok(I.key === 'F2' && I.used, 'adult bright → F2', I.key);
  await stage('adult', 'soft'); await idle(); I = await info(); ok(I.key === null && !I.used, 'adult soft → 冇 80px（舊 evo sprite）', I);
  await stage('juvenile'); await idle(); I = await info(); ok(I.key === null && !I.used, 'juvenile → 舊 sprite', I);

  console.log('# 非 idle clip → fallback 舊 sprite');
  await stage('adult', 'ember');
  await E(() => __glimmer.forceBeh('walk')); await page.waitForTimeout(400); I = await info();
  ok(I.key === 'C2' && !I.used && I.clip !== 'idle', 'walk：有 key 但用返舊 sprite', I);
  const fs0 = await E(() => __glimmer.renderer.faceStat.last); ok(fs0 && !fs0.s80, 'faceStat.last.s80 = null（舊 path）', fs0 && fs0.s80);
  await idle(); I = await info(); ok(I.used, '返 idle → 再用 80px', I);

  console.log('# ?spr80=KEY 強制');
  await load(Q + '&spr80=H3'); await stage('juvenile'); await idle(); I = await info();
  ok(I.key === 'H3' && I.used, '?spr80=H3 → juvenile 都用 H3', I.key);
  await page.screenshot({ path: SHOTS + 'sprite80-H3.png' });
  await load(Q + '&spr80=C2&spr80idle=feel'); await stage('adult', 'ember'); await idle();
  { const fr = new Set(); for (let i = 0; i < 30; i++) { await page.waitForTimeout(37); const J = await info(); if (J.used) fr.add(J.frame); }
    I = await info(); ok(I.idleMode === 'feel' && fr.has(0) && fr.has(1) && !fr.has(2), '?spr80idle=feel：0↔1 bob（唔用幀 2）', [...fr]); }

  await load(Q + '&spr80hold=0'); await stage('adult', 'ember'); await idle();
  { const fr = new Set(); for (let i = 0; i < 15; i++) { await page.waitForTimeout(61); const J = await info(); if (J.used) fr.add(J.frame); } ok(fr.size === 1 && fr.has(0), '?spr80hold=0：定格幀 0（截圖用）', [...fr]); }

  console.log('# ?spr=old → 退返舊 sprite');
  await load(Q + '&spr=old'); await stage('adult', 'ember'); await idle(); I = await info();
  ok(!I.enabled && !I.loaded && !I.used && I.key === null, '?spr=old：唔載 80px、用舊 evo sprite', I);
  const ev = await E(() => __glimmer.evo.info()); ok(ev.drawForm === 'evo_guard_ember', '舊 evo_guard_ember 照畫', ev.drawForm);
  await page.screenshot({ path: SHOTS + 'sprite80-old.png' });

  ok(errs.length === 0, '冇 console error', errs.slice(0, 5));
  console.log(`結果：${pass} 通過，${fail} 失敗`);
  await browser.close(); process.exit(fail ? 1 : 0);
})().catch(e => { console.error('Error', e); process.exit(1); });
