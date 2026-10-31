/* 《微光小圃》 e2e-s3 — 生命感第三段：D3 長按磨蹭（nuzzle＋purr）／D5 久別重逢（rush＋衝過頭＋act_cool＋重逢）／G1 燈泡跟心情（5 tint）＋開發面板「生命感」行 3 個新掣。
   截圖 → SHOTS（預設 /workspace/live-s2/screens/）s3-*.png。 */
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
  page.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') errs.push(m.type() + ': ' + m.text()); });
  page.on('pageerror', e => errs.push('pageerror: ' + e.message));
  const E = (fn, arg) => page.evaluate(fn, arg);
  const shot = async (n, clip) => { await page.waitForTimeout(180); await page.screenshot({ path: SHOTS + 's3-' + n + '.png', clip }); console.log('  📷 s3-' + n); };
  const petClip = async () => { const h = await E(() => __qa.pet.hitBox()); return { x: Math.max(0, h.css.x - 60), y: Math.max(0, h.css.y - 70), width: h.css.w + 120, height: h.css.h + 110 }; };
  const adult = () => E(() => { window.__noSaveOnHide = true; const s = __glimmer.state; s.stage = 'adult'; s.form = 'soft'; s.growthSec = 1e6; Object.assign(s.needs, { hunger: 100, mood: 55, clean: 100, energy: 100 }); s.poops = 0; s.sleeping = false; });
  const load = async (qs, clear) => {
    if (clear) { await page.goto(BASE + '?' + qs); await E(() => { window.__noSaveOnHide = true; localStorage.clear(); }); }
    await page.goto(BASE + '?' + qs); await page.waitForFunction(() => window.__glimmer && __glimmer.liveLoad).catch(() => { }); await E(() => __glimmer.liveLoad); await page.waitForTimeout(300);
    await adult(); await page.waitForTimeout(200);
  };
  const prep = () => E(() => { __qa.pet.pause(true); __qa.pet.force('stay'); __qa.pet.step(0.4); const b = __glimmer.beh; b.x = 0; b.dir = 1; b.bulbForce = null; Object.assign(__glimmer.state.needs, { mood: 55, energy: 100, hunger: 100 }); });
  const LIVE = ['sniff', 'lookup', 'swat', 'scratch', 'sneeze', 'happy', 'drag', 'smug', 'nuzzle', 'reunion', 'bulb'];
  const tl = (sec, dt) => E(([sec, dt]) => { const o = []; let r; for (let i = 0; i < Math.round(sec / dt); i++) { r = __qa.pet.step(dt, 1 / 60); const k = r.show + ':' + (r.micro || r.phase || ''); if (o[o.length - 1] !== k) o.push(k); } return o; }, [sec, dt || 1 / 30]);

  console.log('# 開發面板「生命感」行：原有 8 個＋s3 磨蹭／久未見／燈泡（直向）');
  await load('q=high&hour=13&seed=11&ev=0&dev=1', true);
  const vis = await E((L) => L.map(k => { const el = document.querySelector('[data-testid="dev-live-' + k + '"]'); return [k, !!el && el.offsetParent !== null, el ? el.textContent : null]; }), LIVE);
  ok(vis.every(v => v[1]), '11 個即刻觸發掣全部可見（冇刪舊掣）', vis.filter(v => !v[1]));
  ok(vis.find(v => v[0] === 'nuzzle')[2] === '磨蹭' && vis.find(v => v[0] === 'reunion')[2] === '久未見' && /^燈泡/.test(vis.find(v => v[0] === 'bulb')[2]), '新掣：磨蹭／久未見／燈泡', vis.slice(8));
  ok(await E(() => innerWidth < innerHeight && document.querySelector('[data-testid=dev-live-row]').getBoundingClientRect().right <= innerWidth + 1), '直向：生命感行唔超出畫面闊度');
  await shot('panel');

  console.log('# D3 長按磨蹭（真手勢：實時迴圈撳住 1.7s）');
  await E(() => { __qa.pet.pause(false); __qa.pet.force('stay'); const b = __glimmer.beh; b.x = 0; b.dir = 1; }); await page.waitForTimeout(250);
  { const h = await E(() => __qa.pet.hitBox()); const x = h.css.x + h.css.w * 0.8, y = h.css.y + h.css.h * 0.45;
    await page.mouse.move(x, y); await page.mouse.down(); await page.waitForTimeout(280);
    const early = await E(() => __glimmer.beh.state);
    await page.waitForTimeout(500); const mid = await E(() => ({ s: __glimmer.beh.state, ph: __glimmer.beh.phase, dir: __glimmer.beh.dir, f: __qa.pet.face(), att: __glimmer.beh.attach.map(a => a.prop) }));
    await shot('nuzzle', await petClip());
    await page.waitForTimeout(500); const at13 = await E(() => ({ ph: __glimmer.beh.phase, held: +(__glimmer.beh.t - __glimmer.beh.nuzzleSince).toFixed(2) }));   // 落手後 ~1.3s
    ok(at13.ph === 'purr' && at13.held >= 1.2, 'QA P1①：由落手計 1.2s 就呼嚕（~1.3s 已 purr；唔再要 1.7s）', at13);
    await page.waitForTimeout(400); const late = await E(() => ({ s: __glimmer.beh.state, ph: __glimmer.beh.phase, f: __qa.pet.face(), purr: __glimmer.beh.journal.filter(j => j.ev === 'sfx' && j.name === 'nuzzle_purr').length }));
    await shot('nuzzle-purr', await petClip());
    ok(early !== 'nuzzle' && mid.s === 'nuzzle' && mid.dir === 1, '撳住 <0.4s 未蹭；≥0.4s → nuzzle（手指喺右 → 面向右）', [early, mid.s, mid.dir]);
    ok(mid.f.live && mid.f.drawnClip === 'nuzzle', '畫真 nuzzle_noface＋疊五官', mid.f);
    ok(late.s === 'nuzzle' && late.ph === 'purr' && late.purr >= 1 && late.f.live && late.f.drawnClip === 'nuzzle_purr' && late.f.eyes === 'happy' && late.f.mouth === 'squint', '撳 ≥1.2s → 呼嚕：purr 聲＋真 nuzzle_purr_noface（s3 美術）＋合眼笑 ω', late);
    await page.mouse.up(); await page.waitForTimeout(450);
    const after = await E(() => ({ s: __glimmer.beh.state, m: __qa.pet.state().micro, press: __glimmer.lastPetPress, end: __glimmer.beh.journal.filter(j => j.name === 'nuzzle_end').map(j => j.ph) }));
    ok(after.s !== 'nuzzle' && after.press.nuzzle && after.end.length === 1, '鬆手 → 播完當前幀停磨蹭（' + after.end[0] + (after.m ? '：' + after.m : '') + '）', after);
    ok(after.end[0] === 'cool', '遊策 P2：有呼嚕先鬆手 → 必扮冇事（act_cool）', after.end); }

  console.log('# QA P1③ 多指：全部 pointer 抬起（含 pointercancel）先當鬆手');
  for (const [order, label] of [[['up2', 'up1'], '先放第 2 隻'], [['up1', 'up2'], '先放第 1 隻'], [['cancel1', 'up2'], '第 1 隻 pointercancel']]) {
    await E(() => { __qa.pet.pause(false); __qa.pet.force('stay'); const b = __glimmer.beh; b.x = 0; b.dir = 1; }); await page.waitForTimeout(250);
    const pe = (type, id, prim) => E(([type, id, prim]) => { const h = __qa.pet.hitBox(), r = document.getElementById('hit').getBoundingClientRect(), sc = r.width / 320;
      document.getElementById('hit').dispatchEvent(new PointerEvent(type, { pointerId: id, isPrimary: prim, pointerType: 'touch', bubbles: true, clientX: h.css.x + h.css.w * (0.6 + id * 0.1), clientY: h.css.y + h.css.h * 0.45 })); }, [type, id, prim]);
    await pe('pointerdown', 1, true); await page.waitForTimeout(650); await pe('pointerdown', 2, false); await page.waitForTimeout(150);
    const st1 = await E(() => __glimmer.beh.state);
    const [a1, a2] = order; await pe(a1.startsWith('cancel') ? 'pointercancel' : 'pointerup', +a1.slice(-1), a1.endsWith('1')); await page.waitForTimeout(300);
    const mid2 = await E(() => ({ s: __glimmer.beh.state, held: __glimmer.beh.nuzzleHeld, ptr: window.Glimmer.ui.activePointers ? window.Glimmer.ui.activePointers() : null }));
    await pe(a2.startsWith('cancel') ? 'pointercancel' : 'pointerup', +a2.slice(-1), a2.endsWith('1')); await page.waitForTimeout(450);
    const end2 = await E(() => ({ s: __glimmer.beh.state, held: __glimmer.beh.nuzzleHeld, ptr: window.Glimmer.ui.activePointers ? window.Glimmer.ui.activePointers().length : -1 }));
    ok(st1 === 'nuzzle' && mid2.s === 'nuzzle' && mid2.held === true && end2.s !== 'nuzzle' && end2.held === false && end2.ptr === 0, '多指（' + label + '）：仲有手指 → 繼續磨蹭；全部抬起 → 停（nuzzleHeld=false）', [st1, mid2, end2]); }

  console.log('# 磨蹭掣（自動撳住 2.6s）→ 扮冇事');
  await prep(); await page.click('[data-testid=dev-live-nuzzle]');
  { const t = await tl(4.2); const s = t.join('>');
    ok(/^nuzzle:rub>nuzzle_purr:purr>nuzzle_purr:end>idle:blank>act_cool:act_cool>/.test(s), '磨蹭掣：rub → purr（真 nuzzle_purr） → 鬆手 → 呆一呆 → act_cool（' + s + '）'); }

  console.log('# D5 久未見掣：衝埋嚟 → 衝過頭 → 煞停 → act_cool → 行返 → 重逢');
  await prep(); await E(() => { __glimmer.beh.x = 10; }); await page.click('[data-testid=dev-live-reunion]');
  { const st0 = await E(() => __qa.pet.state()); ok(st0.micro === 'rush_start' && st0.x === 62 && st0.dir === -1, '即刻開始：由右邊場邊起步（rush 第 1 幀）', st0);
    const seen = []; const grab = async (tag, n) => { const r = await E((tag) => { for (let i = 0; i < 400; i++) { const s = __qa.pet.step(1 / 60, 1 / 60); if (s.micro === tag) return s; if (s.state !== 'micro') return s; } return __qa.pet.state(); }, tag); seen.push(r.micro); if (r.micro === tag) { await page.waitForTimeout(60); await shot(n); } return r; };
    const r1 = await E(() => __qa.pet.step(0.35, 1 / 60)); await shot('rush'); const f1 = await E(() => __qa.pet.face());
    ok(r1.micro === 'rush' && f1.live && f1.drawnClip === 'rush' && r1.showFrame >= 1 && r1.showFrame <= 4, '跑緊：真 rush 2–5 幀循環', [r1.micro, r1.showFrame, f1.drawnClip]);
    const r2 = await grab('brake', 'rush-brake'); ok(r2.micro === 'brake' && r2.showFrame === 5 && r2.x < -10, '衝過頭（x=' + r2.x + '）→ 第 6 幀煞停', r2);
    const r3 = await grab('act_cool', 'rush-cool'); ok(r3.micro === 'act_cool', '煞停後扮冷靜 act_cool');
    const r4 = await grab('reunion_happy', 'reunion-happy'); const f40 = await E(() => __qa.pet.face());
    const r4b = await E(() => __qa.pet.step(0.3, 1 / 60)); await shot('reunion-happy-2'); const f4 = await E(() => __qa.pet.face());
    ok(r4.micro === 'reunion_happy' && Math.abs(r4.x) < 1.5 && r4.dir === 1 && f40.drawnClip === 'reunion_happy' && f40.eyes === 'squint' && r4b.showFrame === 2 && f4.eyes === 'happy', '行返中間 → 真 reunion_happy（播前轉身面向玩家：由右衝入衝過頭 → scaleX 轉返向右；扮冷靜回望 → 開心）', [r4.dir, f40.drawnClip, f40.eyes, r4b.showFrame, f4.eyes]);
    const end = await E(() => { for (let i = 0; i < 300; i++) { const s = __qa.pet.step(1 / 60, 1 / 60); if (s.state !== 'micro') return s; } return __qa.pet.state(); });
    ok(end.state === 'stay' && await E(() => __qa.pet.reunion().day === null), '完返 stay；開發掣唔佔每日 1 次', end.state); }

  console.log('# D5 真流程：存檔 lastSeen 離線 8h → 開 app → 摘要 → 關咗即衝埋嚟；同日唔再；<8h 唔衝');
  const reopen = async (h) => {
    await E((h) => { window.__noSaveOnHide = true; const k = 'glimmer_save_v1', o = JSON.parse(localStorage.getItem(k)); o.lastSeen = Date.now() - h * 3600e3; o.sleeping = false; localStorage.setItem(k, JSON.stringify(o)); }, h);
    await page.goto(BASE + '?q=high&hour=13&seed=11&ev=0&dev=1'); await page.waitForFunction(() => window.__glimmer && __glimmer.liveLoad); await E(() => __glimmer.liveLoad); await page.waitForTimeout(250);
    return E(() => ({ r: __qa.pet.reunion(), modal: getComputedStyle(document.getElementById('modal')).display !== 'none', st: __qa.pet.state() }));
  };
  await E(() => { __glimmer.save(); }); await E(() => { const s = __glimmer.state; s.sleeping = false; __glimmer.save(); });
  { let o = await reopen(8.2);
    ok(o.r.pending && o.r.pending.T >= 8 * 3600 && o.modal && o.st.micro !== 'rush_start', '離線 8h：有回歸摘要，重逢排隊（摘要開住時唔衝）', o);
    await page.click('[data-testid=modal-btn-0]').catch(() => { }); for (let i = 0; i < 4; i++) { if (await E(() => getComputedStyle(document.getElementById('modal')).display === 'none')) break; await page.click('[data-testid=modal-btn-0]').catch(() => { }); await page.waitForTimeout(120); }
    await page.waitForTimeout(300); const mid = await E(() => ({ p: !!__qa.pet.reunion().pending, s: __glimmer.beh.state }));
    ok(mid.p && mid.s === 'override', '關摘要：先做「收下光粒」開心反應（現有功能保留），重逢仲排緊', mid);
    await page.waitForFunction(() => !__qa.pet.reunion().pending, null, { timeout: 4000 }).catch(() => { }); await page.waitForTimeout(150);
    const r = await E(() => ({ r: __qa.pet.reunion(), st: __qa.pet.state() }));
    ok(!r.r.pending && r.r.last && r.r.last.src === 'offline' && /rush|brake|act_cool|back|reunion/.test(r.st.micro || ''), '關摘要 → 衝埋嚟（' + r.st.micro + '）；今日已記（' + r.r.day + '）', r);
    await shot('reunion-open');
    await page.waitForTimeout(5000);
    o = await reopen(8.2); ok(!o.r.pending && o.r.skip === 'today', '同日再離線 8h：唔再衝（每日最多 1 次）', o.r);
    await E(() => localStorage.removeItem('glimmer.reunionDay'));
    o = await reopen(7.9); ok(!o.r.pending && o.r.skip === 'short', 'QA P1②：離線 7.9h（<8h）：唔衝', o.r);
  }

  console.log('# G1 燈泡：掣循環 5 心情 tint → 自動');
  await load('q=high&hour=13&seed=11&ev=0&dev=1', true); await prep();
  const moods = await E(() => window.Glimmer.data.PARAMS.face.bulb.moods);
  const seq = []; let rgbOk = true;
  for (let i = 0; i < 6; i++) {
    await page.click('[data-testid=dev-live-bulb]');
    const r = await E(() => { __qa.pet.step(1.6, 1 / 60); return { b: __qa.pet.bulb(), txt: document.querySelector('[data-testid=dev-live-bulb]').textContent }; });
    await page.waitForTimeout(700); const r2 = await E(() => __qa.pet.bulb());   // render 0.4s 漸變
    seq.push((r.b.force || 'auto') + '/' + (r2.drawn && r2.drawn.mood) + '/' + r.txt);
    if (r.b.force) { const t = moods[r.b.force].tint, hx = [1, 3, 5].map(k => parseInt(t.slice(k, k + 2), 16)); if (!r2.drawn || r2.drawn.mood !== r.b.force || r2.drawn.rgb.some((v, k) => Math.abs(v - hx[k]) > 24)) rgbOk = false; await shot('bulb-' + r.b.force, await petClip()); }
  }
  ok(seq.map(s => s.split('/')[0]).join() === 'happy,neutral,sleepy,hungry,grumpy,auto', '燈泡掣循環：' + seq.join(' → '));
  ok(rgbOk, '每款畫出嚟嘅燈泡 tint ≈ 心情色（bulb_glow 灰階 × tint）', seq);
  { const a = await E(() => { Object.assign(__glimmer.state.needs, { hunger: 30, mood: 55, energy: 100, clean: 100 }); __qa.pet.step(1.5, 1 / 60); return [__glimmer.beh.expr, __qa.pet.bulb().auto]; }); await page.waitForTimeout(700); const ad = await E(() => __qa.pet.bulb());
    const c = await E(() => { Object.assign(__glimmer.state.needs, { hunger: 100, mood: 100, energy: 100, clean: 100 }); __qa.pet.step(1.5, 1 / 60); return [__glimmer.beh.expr, __qa.pet.bulb().auto]; }); await page.waitForTimeout(700); const cd = await E(() => __qa.pet.bulb());
    ok(a[1] === 'hungry' && ad.drawn && ad.drawn.mood === 'hungry' && c[1] === 'happy' && cd.drawn && cd.drawn.mood === 'happy' && ad.force === null, '自動：肚餓 → hungry 橙；全滿 → happy 黃（跟心情變）', [a, ad.drawn, c, cd.drawn]); }
  { const r = await E(() => { __glimmer.beh.bulbForce = null; __qa.pet.force('now_nuzzle'); __qa.pet.step(0.8, 1 / 60); return __qa.pet.bulb(); });
    ok(r.drawn && r.drawn.mood === 'happy', '磨蹭中燈泡 happy', r); }

  console.log('# ?live=0（冇遊美 live 圖）：三樣都行 fallback，唔死');
  await load('q=high&hour=13&seed=11&ev=0&dev=1&live=0', true); await prep();
  { await page.click('[data-testid=dev-live-nuzzle]'); const a = await tl(4.2);
    await prep(); await page.click('[data-testid=dev-live-reunion]'); const c = await tl(8);
    await prep(); await page.click('[data-testid=dev-live-bulb]'); const d = await E(() => { __qa.pet.step(0.5, 1 / 60); return [__qa.pet.bulb().force, __qa.pet.state().state]; });
    ok(a.some(k => /^emo_cuddly:/.test(k)) && a.some(k => /act_cool/.test(k)), 'live=0 磨蹭 → emo_cuddly fallback＋扮冇事', a.join('>'));
    ok(c.some(k => /reunion_happy/.test(k)) && !c.some(k => /^rush:/.test(k)), 'live=0 久未見 → walk fallback 衝＋重逢', c.join('>'));
    ok(d[0] === 'happy' && d[1] === 'stay', 'live=0 燈泡掣唔影響（冇燈泡圖就唔畫）', d); }

  console.log('# 錯誤');
  ok(errs.filter(e => !/favicon|AudioContext|autoplay/i.test(e)).length === 0, '冇 console error／pageerror', errs.slice(0, 5));
  console.log(`\n結果：${pass} 通過，${fail} 失敗`);
  await browser.close(); process.exit(fail ? 1 : 0);
})().catch(e => { console.error('Error', e); process.exit(1); });
