/* 生命感第一段 E2E：node tests/e2e-live.js   需要 playwright-core＋系統 Chrome，並喺 glimmer-live 開 http server（例：python3 -m http.server 8138）。
   涵蓋：真生命感 atlas 載入、F1 overlay（三形態真五官、零 placeholder、每次畫寵物只 tint 一次）、faceVisible=false（turn_back 第 0 幀背面）唔畫臉、
   臉 mode off／native、F2 gaze 強制＋量化讀數、A1 行路望方向、D2 點背後→turn_back＋sfx_pet_turn_huh_a/b、燈泡情緒、?live=0 fallback、debug 面板、console 無錯誤。
   截圖 screens/live-*.png（390×844）。 */
const path = require('path');
let chromium;
for (const p of [process.env.PW, 'playwright-core', '/workspace/tools/pw/node_modules/playwright-core']) { try { if (p) { chromium = require(p).chromium; break; } } catch (e) { } }
if (!chromium) { console.error('找不到 playwright-core'); process.exit(2); }
const BASE = process.env.BASE || 'http://localhost:8138/index.html';
const OUT = process.env.OUT || path.join(__dirname, '..', 'screens') + '/';
require('fs').mkdirSync(OUT, { recursive: true });
let pass = 0, fail = 0;
const ok = (c, n, info) => { if (c) { pass++; console.log('  ✓ ' + n); } else { fail++; console.log('  ✗ ' + n + (info !== undefined ? ' → ' + info : '')); } };

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROME || '/usr/bin/google-chrome', args: ['--no-sandbox', '--autoplay-policy=no-user-gesture-required'] });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 1 });
  const page = await ctx.newPage();
  const errs = [];
  page.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') errs.push(m.type() + ': ' + m.text()); });
  page.on('pageerror', e => errs.push('pageerror: ' + e.message));
  const E = (fn, arg) => page.evaluate(fn, arg);
  const shot = async (n) => { await page.waitForTimeout(150); await page.screenshot({ path: OUT + 'live-' + n + '.png' }); console.log('  📷 live-' + n); };
  const fresh = async (qs, form) => {
    await page.goto(BASE + '?' + qs); await E(() => { window.__noSaveOnHide = true; localStorage.clear(); }); await page.goto(BASE + '?' + qs);
    await page.waitForFunction(() => window.__glimmer && __glimmer.liveLoad).catch(() => { });
    await E(() => __glimmer.liveLoad); await page.waitForTimeout(400);
    await E((form) => { const s = __glimmer.state; if (form === 'sprout') { s.stage = 'sprout'; s.form = null; s.growthSec = 100; } else { s.stage = 'adult'; s.form = form; s.growthSec = 3600; } Object.assign(s.needs, { hunger: 100, mood: 100, clean: 100, energy: 100 }); s.poops = 0; s.settings.sound = true; }, form || 'soft');
    await page.waitForTimeout(300);
  };
  const F = () => E(() => __qa.pet.face());
  // 逐幀記錄 renderer.faceStat.last（rAF），用嚟捉 turn_back 第 0 幀
  const record = (ms) => E((ms) => new Promise(res => { const out = []; const t0 = performance.now(); const f = () => { const l = __glimmer.renderer.faceStat.last; if (l) out.push({ clip: l.clip, frame: l.frame, vis: l.faceVisible, eyes: l.eyes, live: l.live }); if (performance.now() - t0 < ms) requestAnimationFrame(f); else res(out); }; requestAnimationFrame(f); }), ms);

  console.log('# 載入：生命感 atlas＋face_anchors');
  await fresh('debug=1&q=high&hour=13&seed=11&ev=0');
  let f = await F();
  ok(f.liveReady && !f.liveError, '生命感資產載入（3 atlas＋anchors，無錯）', JSON.stringify([f.liveReady, f.liveError]));
  ok(await E(() => Glimmer.data.CLIPS.turn_back.ready === true), 'CLIPS.turn_back.ready＝true（三形態都有 turn_back_noface）');
  ok(await E(() => ['sprout', 'radiant', 'soft'].every(k => __glimmer.renderer.lv.atlas[k] && __glimmer.renderer.lv.anchors[k])), '三形態 atlas＋anchors 齊');

  console.log('# F1：真五官 overlay（三形態）＋單次 tint');
  for (const form of ['soft', 'bright', 'sprout']) {
    await fresh('debug=1&q=high&hour=13&seed=11&ev=0', form);
    await E(() => __qa.pet.faceStatReset()); await page.waitForTimeout(700);
    f = await F();
    ok(f.live && f.faceVisible && f.pieces.length === 3 && f.placeholder.length === 0 && !f.derived, form + '：真 noface 身體＋eyeL/eyeR/mouth（0 placeholder、用 anchors）', JSON.stringify(f));
    ok(f.stat.draws > 5 && f.stat.tints === f.stat.draws && f.stat.overlays === f.stat.draws, form + '：每次畫寵物 tint 剛好 1 次（overlay 唔加多一次）draws ' + f.stat.draws + ' tints ' + f.stat.tints, JSON.stringify(f.stat));
    if (form === 'sprout') ok(!f.bulb && f.form === 'evo_sprout', 'sprout：evo6 芽崽（evo_sprout）美術冇燈泡 anchor → 唔畫燈泡（跳跳期起先有）', JSON.stringify([f.form, f.bulb]));
    else ok(f.bulb && f.bulb.mood === 'happy', form + '：燈泡情緒 happy（需求全滿）', JSON.stringify(f.bulb));
    await shot('f1-' + form);
  }

  console.log('# F1：表情款式（強制）＋wink 規則');
  await fresh('debug=1&q=high&hour=13&seed=11&ev=0', 'soft');
  for (const [eyes, mouth] of [['neutral', 'neutral'], ['surprised', 'surprised'], ['sleepy', 'sleepy'], ['wink', 'wink'], ['sad', 'sad'], ['angry', 'angry'], ['squint', 'squint'], ['happy', 'happy']]) {
    await E(([e, m]) => { __qa.pet.setFace({ eyes: e, mouth: m }); __qa.pet.setGaze('L'); }, [eyes, mouth]); await page.waitForTimeout(450);
    f = await F();
    const closed = ['happy', 'sleepy', 'wink'].includes(eyes);
    const wantL = eyes === 'wink' ? /^eyes_neutral_[A-Z]+_l$/ : new RegExp('^eyes_' + eyes + '_' + (closed ? 'C' : '[A-Z]+') + '_l$');
    const wantR = eyes === 'wink' ? /^eyes_wink_C_r$/ : new RegExp('^eyes_' + eyes + '_' + (closed ? 'C' : '[A-Z]+') + '_r$');
    ok(f.eyes === eyes && f.mouth === mouth && wantL.test(f.pieces[0] || '') && wantR.test(f.pieces[1] || '') && f.pieces[2] === 'mouth_' + mouth && f.placeholder.length === 0, '表情 ' + eyes + '/' + mouth + ' → ' + f.pieces.join(','), JSON.stringify(f));
  }
  await E(() => { __qa.pet.setFace({ eyes: 'neutral', mouth: 'happy' }); }); await page.waitForTimeout(300); await shot('f1-neutral-gazeL');
  await E(() => { __qa.pet.setFace(null); __qa.pet.setGaze(null); });

  console.log('# F2：gaze 強制、量化 7 格、讀數');
  await E(() => { __qa.pet.setFace({ eyes: 'neutral', mouth: 'neutral' }); __glimmer.beh.dir = 1; });
  for (const g of ['L', 'CL', 'C', 'CR', 'R', 'U', 'D']) {
    await E((g) => __qa.pet.setGaze(g), g); await page.waitForTimeout(350);
    const r = await E(() => ({ gz: __qa.pet.gaze(), f: __qa.pet.face() }));
    const exp = r.gz.dir < 0 ? ({ L: 'R', CL: 'CR', CR: 'CL', R: 'L' }[g] || g) : g;   // 朝左成個合成鏡像 → 幀內 gaze 互換
    ok(r.f.gaze === exp && (r.f.pieces[0] || '').indexOf('_' + exp + '_') > 0, 'gaze ' + g + '（dir ' + r.gz.dir + '）→ 幀內 ' + r.f.gaze + ' 件 ' + r.f.pieces[0], JSON.stringify(r));
  }
  await E(() => { __qa.pet.setGaze(null); __qa.pet.setFace(null); });
  const gz = await E(() => __qa.pet.gaze());
  ok(['L', 'CL', 'C', 'CR', 'R', 'U', 'D'].includes(gz.q) && typeof gz.x === 'number' && typeof gz.src === 'string', '__qa.pet.gaze() 讀數 {q,ql,src,x,y}', JSON.stringify(gz));

  console.log('# A1：邊行邊望（walk 時 gaze 跟方向）');
  await fresh('debug=1&q=high&hour=13&seed=11&ev=0', 'soft');
  const walk = await E(() => new Promise(res => { __qa.pet.force('walk'); const out = []; const t0 = performance.now(); const f = () => { const b = __glimmer.beh; if (b.state === 'walk') out.push({ src: b.look.src, q: b.look.q, dir: b.dir }); if (performance.now() - t0 < 2500) requestAnimationFrame(f); else res(out); }; requestAnimationFrame(f); }));
  const wsrc = walk.filter(w => w.src === 'walk' || w.src === 'cam');
  const fwd = walk.filter(w => w.src === 'walk' && w.q !== 'C');
  ok(walk.length > 20 && wsrc.length / walk.length > 0.9, 'walk 期間 gaze 來源＝walk／cam（' + wsrc.length + '/' + walk.length + '）');
  ok(fwd.length > 0 && fwd.every(w => ['R', 'CR'].includes(w.q)), 'walk gaze（幀內，向前）＝R／CR', JSON.stringify(fwd.slice(0, 5)));
  await shot('a1-walk');

  console.log('# D2：點一下回頭（turn_back clip＋咦？音效）');
  await fresh('debug=1&q=high&hour=13&seed=11&ev=0', 'soft');
  await page.mouse.click(195, 760); await page.waitForTimeout(1200);   // 手勢解鎖音訊（點底部空位）
  await E(() => { const b = __glimmer.beh; b.dir = 1; });
  await page.waitForTimeout(100);
  const st0 = await E(() => __qa.pet.audioLog().length);
  const recP = record(900);
  await E(() => { const b = __glimmer.beh; __qa.pet.tap(b.x - 14, -20); });
  const frames = await recP;
  const tb = frames.filter(x => x.clip === 'turn_back');
  const tb0 = tb.filter(x => x.frame === 0), tb1 = tb.filter(x => x.frame > 0);
  ok(tb.length > 0, '點背後 → 播 turn_back clip（' + tb.length + ' 幀）', JSON.stringify(frames.slice(0, 6)));
  ok(tb0.length > 0 && tb0.every(x => x.vis === false && !x.eyes), 'turn_back 第 0 幀 faceVisible=false → 唔畫眼／口', JSON.stringify(tb0));
  ok(tb1.length > 0 && tb1.every(x => x.vis === true && x.eyes), 'turn_back 第 1–3 幀轉返正面 → 有臉', JSON.stringify(tb1.slice(0, 3)));
  const gzT = await E(() => __qa.pet.gaze());
  ok(gzT.dir === -1, 'D2 後 dir 轉向觸點（-1）', JSON.stringify(gzT));
  const huh = await E((n) => __qa.pet.audioLog().slice(n).filter(x => /^pet_turn_huh_[ab]$/.test(x.name)), st0);
  ok(huh.length === 1 && huh[0].played, 'D2 播 sfx_pet_turn_huh_a/b（' + (huh[0] && huh[0].name) + '，played）', JSON.stringify(huh));
  ok(await E(() => __qa.pet.audio().sfxLoaded >= 52), 'SFX 解碼數（含 16 個生命感）' + await E(() => __qa.pet.audio().sfxLoaded));
  ok(await E(() => __qa.pet.log.some(x => x.ev === 'clip' && x.name === 'turn_back')), '行為日誌記錄 clip turn_back');
  // 前面點：唔轉身、唔播 huh
  await page.waitForTimeout(1600);
  const n1 = await E(() => __qa.pet.audioLog().length);
  await E(() => { const b = __glimmer.beh; __qa.pet.tap(b.x + b.dir * 8, -20); }); await page.waitForTimeout(300);
  ok(await E((n) => !__qa.pet.audioLog().slice(n).some(x => /pet_turn_huh/.test(x.name)), n1), '點前面：唔轉身、唔播 huh');
  await E(() => { const b = __glimmer.beh; b.dir = 1; __qa.pet.tap(b.x - 14, -20); }); await page.waitForTimeout(60); await shot('d2-turn');

  console.log('# 臉 mode：off／native');
  await fresh('debug=1&q=high&hour=13&seed=11&ev=0', 'soft');
  await E(() => { __qa.pet.faceMode('off'); __qa.pet.faceStatReset(); }); await page.waitForTimeout(500);
  f = await F();
  ok(!f.faceVisible && f.pieces.length === 0 && f.stat.faceDrawn === 0 && f.stat.faceHidden > 0 && f.stat.tints === f.stat.draws, 'faceMode off → 唔畫臉（faceDrawn 0），tint 仍 1 次', JSON.stringify(f.stat));
  await shot('face-off');
  await E(() => { __qa.pet.faceMode('native'); __qa.pet.faceStatReset(); }); await page.waitForTimeout(500);
  f = await F();
  ok(!f.live && f.stat.overlays === 0 && f.stat.tints === f.stat.draws, 'faceMode native → 用 PR #17 原 atlas（無 overlay）', JSON.stringify(f.stat));
  await E(() => __qa.pet.faceMode('auto'));

  console.log('# 燈泡情緒');
  await E(() => { __qa.pet.pause(); Object.assign(__glimmer.state.needs, { hunger: 30 }); __qa.pet.pause(false); }); await page.waitForTimeout(1500);
  f = await F();
  ok(f.bulb && ['hungry', 'neutral'].includes(f.bulb.mood), '肚餓 → 燈泡 ' + (f.bulb && f.bulb.mood), JSON.stringify([f.bulb, await E(() => __glimmer.beh.expr)]));

  console.log('# ?live=0 fallback');
  await fresh('debug=1&q=high&hour=13&seed=11&ev=0&live=0', 'soft');
  f = await F();
  ok(!f.liveReady && !f.live && await E(() => Glimmer.data.CLIPS.turn_back.ready === false), '?live=0：唔載生命感、turn_back 唔 ready（點背後只翻轉＋gaze）');
  await E(() => { const b = __glimmer.beh; b.dir = 1; __qa.pet.tap(b.x - 14, -20); }); await page.waitForTimeout(50);
  ok(await E(() => __glimmer.beh.turn && __glimmer.beh.turn.clip == null && __glimmer.beh.dir === -1), '?live=0：D2 翻轉（無 clip）');

  console.log('# debug 面板');
  await fresh('debug=1&q=high&hour=13&seed=11&ev=0', 'soft');
  await page.click('#dbgT');
  await page.click('[data-testid=dbg-eye-surprised]'); await page.click('[data-testid=dbg-gaze-U]'); await page.waitForTimeout(400);
  f = await F(); ok(f.eyes === 'surprised' && f.gaze === 'U', 'debug 面板：眼款 surprised＋gaze U', JSON.stringify([f.eyes, f.gaze]));
  await shot('debug-panel');
  await page.click('[data-testid=dbg-eye-auto]'); await page.click('[data-testid=dbg-gaze-auto]');

  ok(errs.length === 0, 'console 無錯誤／警告', errs.join(' | '));
  console.log(`\n${pass} passed, ${fail} failed`);
  await browser.close(); process.exit(fail ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
