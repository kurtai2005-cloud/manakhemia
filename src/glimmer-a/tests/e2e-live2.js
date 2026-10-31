/* 生命感第二段 E2E：node tests/e2e-live2.js   需要 playwright-core＋系統 Chrome，並喺 glimmer-a 開 http server（例：python3 -m http.server 8138）。
   涵蓋：7 個新 live clip ready、真 noface 身體＋逐幀五官（三形態，0 placeholder）、A3 蓬跳／拖步顯示替身、B1 抓癢、B2 打噴嚏、A2 嗅地／望天／拍蟲、
   個性組合（撲空得意 pose／嗅到打噴嚏扮冷靜／望天後仰起身扮冷靜）、sfx（scratch／sneeze／bug_pat／step_hop／step_drag）；s2b：真 smug_pose／act_cool／lookup_tip／getup／sniff_itch＋fx bug sprite、?live=0 fallback、console 無錯誤。
   截圖 screens/live2-*.png（全屏 390×844）＋ live2-*-zoom.png（寵物特寫）。 */
const path = require('path');
let chromium;
for (const p of [process.env.PW, 'playwright-core', '/workspace/qa-live-s1/node_modules/playwright-core']) { try { if (p) { chromium = require(p).chromium; break; } } catch (e) { } }
if (!chromium) { console.error('找不到 playwright-core'); process.exit(2); }
const BASE = process.env.BASE || 'http://localhost:8138/index.html';
const OUT = process.env.OUT || path.join(__dirname, '..', 'screens') + '/';
require('fs').mkdirSync(OUT, { recursive: true });
let pass = 0, fail = 0;
const ok = (c, n, info) => { if (c) { pass++; console.log('  ✓ ' + n); } else { fail++; console.log('  ✗ ' + n + (info !== undefined ? ' → ' + info : '')); } };

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROME || '/usr/bin/google-chrome', args: ['--no-sandbox', '--autoplay-policy=no-user-gesture-required'] });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2 });
  const page = await ctx.newPage();
  const errs = [];
  page.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') errs.push(m.type() + ': ' + m.text()); });
  page.on('pageerror', e => errs.push('pageerror: ' + e.message));
  const E = (fn, arg) => page.evaluate(fn, arg);
  const shot = async (n) => {
    await page.waitForTimeout(160);
    await page.screenshot({ path: OUT + 'live2-' + n + '.png' });
    const cl = await E(() => { const r = __glimmer.renderer, R = r.canvas.getBoundingClientRect(), k = R.width / 195, p = r.petRect || { x: 80, y: 230, w: 34, h: 60 };
      const cx = R.left + (p.x + p.w / 2) * k, cy = R.top + (p.y + p.h / 2 - 6) * k, s = 100 * k; return { x: Math.max(0, cx - s / 2), y: Math.max(0, cy - s / 2), width: s, height: s }; });
    await page.screenshot({ path: OUT + 'live2-' + n + '-zoom.png', clip: cl });
    console.log('  📷 live2-' + n);
  };
  const fresh = async (qs, form, needs) => {
    await page.goto(BASE + '?' + qs); await E(() => { window.__noSaveOnHide = true; localStorage.clear(); }); await page.goto(BASE + '?' + qs);
    await page.waitForFunction(() => window.__glimmer && __glimmer.liveLoad).catch(() => { });
    await E(() => __glimmer.liveLoad); await page.waitForTimeout(300);
    await E(([form, needs]) => { const s = __glimmer.state; if (form === 'sprout') { s.stage = 'sprout'; s.form = null; s.growthSec = 100; } else { s.stage = 'adult'; s.form = form; s.growthSec = 3600; } Object.assign(s.needs, { hunger: 100, mood: 100, clean: 100, energy: 100 }, needs || {}); s.poops = 0; s.settings.sound = true; }, [form || 'soft', needs]);
    await page.waitForTimeout(200);
  };
  const st = () => E(() => __qa.pet.state());
  const F = () => E(() => __qa.pet.face());
  // 暫停實時迴圈，用 __qa.pet.step 確定性快進（渲染照跑）
  const forceAt = (name, sec, needs) => E(([n, s, nd]) => { __qa.pet.pause(true); if (nd) Object.assign(__glimmer.state.needs, nd); __qa.pet.force('stay'); __qa.pet.step(0.5); __glimmer.beh.x = 0; __glimmer.beh.dir = 1; __qa.pet.force(n); __qa.pet.step(s, 1 / 60); return __qa.pet.state(); }, [name, sec, needs]);
  const keepNeeds = (nd) => E((nd) => { __glimmer.__keep = setInterval(() => Object.assign(__glimmer.state.needs, nd), 50); }, nd);
  const stopKeep = () => E(() => clearInterval(__glimmer.__keep));

  console.log('# 載入：第二段 7 個 live clip');
  await fresh('debug=1&q=high&hour=13&seed=11&ev=0', 'soft', { mood: 55 });
  const miss = await E(() => ['walk_happy', 'walk_drag', 'sniff', 'lookup', 'swat', 'scratch', 'sneeze'].filter(k => !(Glimmer.data.CLIPS[k] && Glimmer.data.CLIPS[k].ready && Glimmer.data.CLIPS[k].live)));
  ok(miss.length === 0, '7 個 clip（walk_happy／walk_drag／sniff／lookup／swat／scratch／sneeze）ready（3 形態 live atlas 齊）', JSON.stringify(miss));

  console.log('# B1／B2／A2：真 noface 身體＋逐幀五官（三形態）');
  for (const form of ['soft', 'bright', 'sprout']) {
    await fresh('debug=1&q=high&hour=13&seed=11&ev=0', form, { mood: 55 });
    for (const [name, sec, want, tag] of [['scratch', 0.3, 'scratch', 'scratch'], ['sneeze', 0.3, 'sneeze', 'sneeze'], ['sniff', 0.35, 'sniff', 'sniff'], ['lookup', 0.9, 'lookup', 'lookup'], ['swat_hit', 0.75, 'swat', 'swat']]) {
      const s = await forceAt(name, sec, { mood: 55 }); await E(() => __qa.pet.faceStatReset()); await page.waitForTimeout(140); const f = await F();
      const exp = await E(([c, fr]) => Glimmer.data.PARAMS.face.clipFrames[c][fr], [want, s.showFrame]);
      ok(s.show === want && f.live && f.clip === want && f.placeholder.length === 0 && f.eyes === exp[0] && f.mouth === exp[2], form + '：' + name + ' → 真 ' + want + '_noface 第 ' + s.showFrame + ' 幀＋art 五官 ' + exp.join('/'), JSON.stringify({ s: [s.state, s.show, s.showFrame], f: [f.live, f.clip, f.eyes, f.mouth, f.placeholder] }));
      if (form === 'soft' || (form === 'sprout' && name === 'scratch')) await shot(form + '-' + tag);
    }
  }

  console.log('# A3：心情步姿（顯示替身）');
  for (const [nm, needs, want] of [['happy', { mood: 100 }, 'walk_happy'], ['drag', { mood: 55, energy: 20 }, 'walk_drag'], ['plain', { mood: 55 }, 'walk']]) {
    await fresh('debug=1&q=high&hour=13&seed=11&ev=0', 'soft', needs);
    const s = await E((nd) => { __qa.pet.pause(true); Object.assign(__glimmer.state.needs, nd); const b = __glimmer.beh; b.x = -50; __qa.pet.force('walk'); b.tx = 50; b.stopAt = null; __qa.pet.step(0.45, 1 / 60); return __qa.pet.state(); }, needs);
    await page.waitForTimeout(140); const f = await F();
    ok(s.state === 'walk' && s.clip === 'walk' && s.show === want && f.clip === want && f.live, 'A3 ' + nm + '：狀態 walk，顯示 ' + want + '（live）', JSON.stringify([s.state, s.clip, s.show, f.clip, f.live]));
    await shot('gait-' + nm);
  }
  // 腳步聲：真實時間跑 2.5s
  for (const [needs, re] of [[{ mood: 100 }, /^pet_step_hop_[ab]$/], [{ mood: 55, energy: 20 }, /^pet_step_drag_[ab]$/]]) {
    await fresh('debug=1&q=high&hour=13&seed=11&ev=0', 'soft', needs);
    const n0 = await E(() => __qa.pet.audioLog().length);
    await keepNeeds(needs);
    await E(() => { const b = __glimmer.beh; b.x = -60; __qa.pet.force('walk'); b.tx = 60; b.stopAt = null; });
    await page.waitForTimeout(2500); await stopKeep();
    const cues = await E((n) => __qa.pet.audioLog().slice(n).map(x => x.name), n0);
    const steps = cues.filter(c => re.test(c)); const alt = steps.every((c, i) => !i || c !== steps[i - 1]);
    ok(steps.length >= 3 && alt, '腳步聲 ' + re.source + '：' + steps.length + ' 下，a/b 交替', JSON.stringify(cues.slice(0, 12)));
  }

  console.log('# 個性：蠢蠢地但覺得自己好醒');
  await fresh('debug=1&q=high&hour=13&seed=11&ev=0', 'soft', { mood: 55 });
  const until = (pred, max) => E(([src, max]) => { const p = new Function('r', 'return ' + src); let r = __qa.pet.state(); for (let i = 0; i < (max || 120) && !p(r); i++) r = __qa.pet.step(1 / 30, 1 / 60); return r; }, [pred, max]);
  ok(await E(() => ['smug_pose', 'act_cool', 'lookup_tip', 'getup', 'sniff_itch'].every(k => Glimmer.data.CLIPS[k].ready) && ['sprout', 'radiant', 'soft'].every(f => __glimmer.renderer.lv.atlas[f].json.parts.length >= 3)   /* systems12：再加 _live_wx（撐葉／打冷震）→ 4 */ && !!__glimmer.renderer.lv.fx), 's2 美術：5 個新 clip ready（3 形態 _live＋_live_s2＋_live_s3 合併）＋fx atlas 載入');
  let s = await forceAt('swat_miss', 0.3, { mood: 55 }); await page.waitForTimeout(120); let f = await F();
  ok(s.micro === 'notice' && s.bug === 'buzz' && f.bugArt === true, '拍蟲：蟲仔喺頭邊飛（遊美 fx_bug sprite，唔係程序化點）', JSON.stringify([s.micro, s.bug, f.bugArt])); await shot('swat-bug');
  s = await E(() => __qa.pet.step(0.5, 1 / 60)); ok(s.bug === 'flee', '撲空：蟲仔飛走', JSON.stringify(s));
  s = await until("r.micro === 'smug' && r.showFrame === 3"); await page.waitForTimeout(140); f = await F();
  ok(s.micro === 'smug' && s.show === 'smug_pose' && f.clip === 'smug_pose' && f.eyes === 'sleepy' && f.mouth === 'squint' && f.live, '撲空後真 smug_pose（尾幀 preset smug：sleepy 眼＋ω 嘴）', JSON.stringify([s.micro, s.show, f.clip, f.eyes, f.mouth])); await shot('swat-smug');
  { const h = await E(() => { let n = 0; for (let i = 0; i < 90; i++) { const r = __qa.pet.step(1 / 60, 1 / 60); if (r.show === 'smug_pose' && r.showFrame === 3) n++; else break; } return n / 60; }); ok(h >= 0.7, 'smug_pose 尾幀 hold ≈0.8s（量到再 hold ' + h.toFixed(2) + 's）'); }
  s = await forceAt('sniff_sneeze', 0.4, { mood: 55 }); await page.waitForTimeout(120); await shot('sniff-sneeze-1');
  s = await until("r.show === 'sniff_itch'"); await page.waitForTimeout(120); f = await F();
  ok(s.micro === 'itch' && f.clip === 'sniff_itch' && f.live, '嗅地 → sniff_itch（鼻癢過渡，真 clip）', JSON.stringify([s.micro, s.show, f.clip])); await shot('sniff-itch');
  s = await until("r.show === 'sneeze'"); f = await F(); ok(s.show === 'sneeze' && s.showFrame === 0, 'sniff_itch → 直接接 sneeze_01', JSON.stringify([s.show, s.showFrame]));
  s = await until("r.micro === 'act_cool'", 200); await page.waitForTimeout(140); f = await F();
  ok(s.micro === 'act_cool' && s.show === 'act_cool' && f.clip === 'act_cool' && f.live, '打完噴嚏扮冷靜（真 act_cool）', JSON.stringify([s.micro, s.show, f.clip, f.eyes, s.face.gaze])); await shot('sniff-sneeze-cool');
  s = await forceAt('lookup_tip', 1.2, { mood: 55 }); await page.waitForTimeout(120); await shot('lookup-hold');
  s = await until("r.micro === 'tip' && r.showFrame === 3", 200); await page.waitForTimeout(140); f = await F();
  ok(s.micro === 'tip' && s.show === 'lookup_tip' && s.pose === 0 && f.live && f.clip === 'lookup_tip', '望天望到坐低（真 lookup_tip，冇程序化後仰）', JSON.stringify([s.micro, s.show, s.pose, f.clip])); await shot('lookup-tip');
  s = await until("r.micro === 'getup'", 200); await page.waitForTimeout(120); ok(s.micro === 'getup' && s.show === 'getup', '起返身（真 getup）', JSON.stringify([s.micro, s.show])); await shot('lookup-getup');
  s = await until("r.micro === 'act_cool'", 200); ok(s.show === 'act_cool', 'getup → act_cool', s.show);

  console.log('# 音效：scratch／sneeze／bug_pat');
  await fresh('debug=1&q=high&hour=13&seed=11&ev=0', 'soft', { mood: 55 });
  for (const [name, re] of [['scratch', /^pet_scratch_[ab]$/], ['sneeze', /^pet_sneeze_[ab]$/], ['swat_hit', /^pet_bug_pat_[ab]$/]]) {
    const n0 = await E(() => __qa.pet.audioLog().length);
    await E((n) => { __qa.pet.pause(false); __qa.pet.force(n); }, name); await page.waitForTimeout(1500);
    const cues = await E((n) => __qa.pet.audioLog().slice(n), n0); const hit = cues.filter(c => re.test(c.name));
    ok(hit.length === 1, name + ' → ' + (hit[0] ? hit[0].name : '無') + (hit[0] && hit[0].played ? '（played）' : ''), JSON.stringify(cues.map(c => c.name)));
  }

  console.log('# ?live=0 fallback（無 live atlas → idle＋程序化佔位）');
  await fresh('debug=1&q=high&hour=13&seed=11&ev=0&live=0', 'soft', { mood: 100 });
  ok(await E(() => ['walk_happy', 'sniff', 'scratch', 'sneeze', 'swat'].every(k => Glimmer.data.CLIPS[k].ready === false)), '?live=0：第二段 clip 唔 ready');
  s = await forceAt('scratch', 0.3); await page.waitForTimeout(140); f = await F();
  ok(s.micro === 'scratch' && !f.live, '?live=0：抓癢照行（行為唔變，渲染退 placeholder）', JSON.stringify([s.micro, f.live])); await shot('fallback-scratch');
  s = await forceAt('lookup_tip', 1.7); await page.waitForTimeout(120); ok(s.micro === 'tip' || s.micro === 'getup', '?live=0：後仰序列照行', s.micro);
  s = await forceAt('swat_miss', 0.3); await page.waitForTimeout(120); f = await F(); ok(s.bug === 'buzz' && f.bugArt === false, '?live=0：蟲仔退返程序化點', JSON.stringify([s.bug, f.bugArt]));
  s = await E(() => { let r; for (let i = 0; i < 60; i++) { r = __qa.pet.step(1 / 30, 1 / 60); if (r.micro === 'smug') break; } return r; }); ok(s.micro === 'smug' && s.show === 'emo_happy', '?live=0：smug 退返 emo_happy fallback', JSON.stringify([s.micro, s.show]));

  console.log('# 開發面板按鈕');
  await fresh('debug=1&q=high&hour=13&seed=11&ev=0', 'soft', { mood: 55 });
  ok(await E(() => ['scratch', 'sneeze', 'sniff_sneeze', 'lookup_tip', 'swat_miss'].every(n => document.querySelector('[data-testid="dbg-beh-' + n + '"]'))), 'debug 面板有「生命感第二段」按鈕');
  await E(() => { __qa.pet.pause(false); document.querySelector('[data-testid="dbg-beh-scratch"]').click(); }); await page.waitForTimeout(200);
  s = await st(); ok(s.state === 'micro' && s.micro === 'scratch', '撳 dbg-beh-scratch → 抓癢', JSON.stringify([s.state, s.micro]));

  ok(errs.length === 0, 'console 無錯誤／警告', errs.slice(0, 5).join(' | '));
  await browser.close();
  console.log(`\n結果：${pass} 通過，${fail} 失敗`);
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
