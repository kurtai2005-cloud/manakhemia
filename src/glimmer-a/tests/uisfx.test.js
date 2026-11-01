/* HD-2D UI 音效 hook 時間（遊音 README §7.11 ＋ 遊美 MOTION_HD2D；0 ms ＝ hook）。node tests/uisfx.test.js */
const U = require('../src/uisfx.js'), D = require('../src/data.js'), fs = require('fs'), path = require('path');
let pass = 0, fail = 0; const ok = (c, m, x) => { if (c) { pass++; console.log('  ✓ ' + m); } else { fail++; console.log('  ✗ ' + m + (x !== undefined ? '  → ' + JSON.stringify(x) : '')); } };
const nm = (l) => l.map(x => x.file.replace('sfx_ui8_', '') + '@' + x.t);
const st0 = () => U.create(11);

console.log('① 轉場／返回');
{ const s = st0(); const l = U.plan(s, 'transition', { screen: 'journal' }, 1000);
  ok(JSON.stringify(nm(l)) === JSON.stringify(['transition_veil_close@0', 'transition_veil_open@420']), '轉場：veil_close t=0、veil_open t=420', nm(l));
  ok(l.every(x => x.rate === 1), '轉場 rate 1');
  const b = U.plan(s, 'back', {}, 5000); ok(JSON.stringify(nm(b)) === '["transition_veil_open@0"]', '返回：只播 veil_open t=0', nm(b));
  ok(b[0].rate === 1 && b[0].rate !== 1.12, '返回冇 rate 1.12');
  const c = U.plan(U.create(3), 'transition', { cards: 5 }, 0).filter(x => /popup_open/.test(x.file));
  ok(c.length === 3, '卡 pop 只播頭 3 張', c.length);
  ok(c.map(x => x.t).join() === '520,560,600', '卡 pop t=520＋40·i（MOTION §6）', c.map(x => x.t));
  ok(c.every(x => x.gain === 0.5 && x.rate >= 0.95 && x.rate <= 1.08), '卡 pop 音量 0.5、rate 0.95–1.08', c);
  const rates = new Set(); const s2 = U.create(5); for (let i = 0; i < 20; i++) U.plan(s2, 'cards', { n: 3 }, i * 1000).forEach(x => rates.add(x.rate)); ok(rates.size > 5, 'rate 隨機（唔係固定值）', rates.size);
  ok(U.plan(s, 'cardUp', {}, 9000).length === 0, 'pointerup 冇聲');
  ok(U.plan(U.create(1), 'cards', { n: 2, t0: 100 }, 0).map(x => x.t).join() === '100,140', 'cards hook 用自訂 t0'); }

console.log('② toast／貨幣');
{ const s = st0(); let l = U.plan(s, 'toast', {}, 0); ok(JSON.stringify(nm(l)) === '["toast_in@0"]', 'toast：toast_in t=0', nm(l));
  l = U.plan(s, 'toast', { currency: true }, 2000); ok(JSON.stringify(nm(l)) === '["toast_in@0","coin@140"]', '貨幣 toast：加 coin t=140', nm(l));
  ok(nm(U.plan(s, 'coin', {}, 4000)).join() === 'coin@0', 'legacy coin → ui8_coin');
  ok(U.LEGACY.coin === 'coin' && D.AUDIO.cues.coin.file === 'sfx_ui8_coin', 'sfx_coin cue 指去 ui8_coin'); }

console.log('③ 主掣／stamp');
{ const s = st0(); const l = U.plan(s, 'primary', {}, 0); ok(nm(l).sort().join() === 'btn_sparkle@0,confirm@0', '主掣：confirm＋btn_sparkle 同時 t=0', nm(l));
  const t = U.plan(s, 'stamp', {}, 1000); ok(nm(t).join() === 'btn_sparkle@0,confirm@20', 'stamp：sparkle t=0、confirm t=20', nm(t));
  const after = U.plan(s, 'toast', { currency: true }, 1200); ok(nm(after).join() === 'coin@140', 'stamp 後即刻嘅貨幣 toast 唔疊 toast_in，只留 coin t=140', nm(after));
  const off = U.create(1, { stampSparkle: false }); ok(nm(U.plan(off, 'stamp', {}, 0)).join() === 'confirm@20', 'stampSparkle 可關（README 只列 confirm）'); }

console.log('④ badge_wiggle 冷卻／一畫面一次');
{ const s = st0(); ok(U.plan(s, 'badge', { screen: 'home' }, 0).length === 1, '第一次 wiggle 有聲');
  ok(U.plan(s, 'badge', { screen: 'home' }, 6000).length === 0, '同一畫面第二次 wiggle（6 s 後）冇聲');
  const s3 = st0(); U.plan(s3, 'badge', { screen: 'home' }, 0); U.plan(s3, 'transition', { screen: 'journal' }, 1000);
  ok(U.plan(s3, 'badge', { screen: 'journal' }, 3000).length === 0, '換畫面但距上次 <5 s 冷卻 → 冇聲');
  ok(U.plan(s3, 'badge', { screen: 'journal' }, 5001).length === 1, '換畫面＋冷卻 ≥5 s → 有聲');
  ok(U.plan(s, 'appear', {}, 13000).length === 0, '紅點出現冇聲'); }

console.log('⑤ tab／squish／sparkle 唔疊 sfx_tap');
{ for (const h of ['tab', 'press', 'primary', 'stamp', 'medal']) { const s = st0(); U.plan(s, h, {}, 1000); ok(U.plan(s, 'tap', {}, 1100).length === 0, h + ' 之後 legacy tap 唔疊'); }
  const s = st0(); ok(U.plan(s, 'tap', {}, 0)[0].file === 'sfx_ui8_tap_a' && U.plan(s, 'tap', {}, 1000)[0].file === 'sfx_ui8_tap_b', 'legacy tap → ui8_tap_a／_b 交替');
  ok(D.AUDIO.cues.tap.file === 'sfx_ui8_tap_a' && D.AUDIO.cues.tap.alt === 'sfx_ui8_tap_b', 'sfx_tap cue 指去 ui8_tap_a／b');
  const t = st0(); ok(U.plan(t, 'tab', {}, 0)[0].file === 'sfx_ui8_tab_switch_a' && U.plan(t, 'tab', {}, 1000)[0].file === 'sfx_ui8_tab_switch_b', 'tab（含返回）tab_switch a／b 交替（冇 tab_pop 檔）');
  ok(U.plan(st0(), 'medal', { seg: true }, 0)[0].file === 'sfx_ui8_tap_a', 'seg 固定 tap_a');
  const p = st0(); ok(/btn_press_[ab]/.test(U.plan(p, 'press', {}, 0)[0].file), '一般掣 pointerdown → btn_press a／b'); }

console.log('⑥ 其他 §7.11');
{ const s = st0(); ok(nm(U.plan(s, 'disabled', {}, 0)).join() === 'error@0', 'disabled → error');
  ok(U.plan(s, 'disabled', {}, 300).length === 0, 'disabled pointerdown＋legacy error 600 ms 內唔疊');
  ok(nm(U.plan(s, 'popupClose', {}, 0)).join() === 'popup_close@0' && nm(U.plan(s, 'cancel', {}, 0)).join() === 'cancel@0', '✕／背景 popup_close；取消 cancel');
  ok(nm(U.plan(s, 'toggle', { on: true }, 0)).join() === 'toggle_on@0' && nm(U.plan(s, 'toggle', { on: false }, 500)).join() === 'toggle_off@0', 'toggle on／off');
  const q = st0(); U.plan(q, 'tab', {}, 0); ok(U.plan(q, 'popupOpen', {}, 100).length === 0, 'tab／轉場同一下嘅 popup_open 唔疊'); ok(U.plan(q, 'popupOpen', {}, 1000).length === 1, '之後 popup_open 照播');
  const d = st0(); U.plan(d, 'press', {}, 0); ok(U.plan(d, 'press', {}, 50).length === 0 && U.plan(d, 'press', {}, 200).length === 1, '同 hook 120 ms 內去重'); }

console.log('⑦ 檔案');
{ const dir = path.join(__dirname, '../audio/sfx'); const miss = U.FILES.filter(f => !fs.existsSync(path.join(dir, f + '.ogg')));
  ok(!miss.length && U.FILES.length === 19, '19 個 ui8 檔齊', miss);
  ok(!fs.existsSync(path.join(dir, '_preview_ui8_all.ogg')) && !fs.readdirSync(dir).some(f => /preview/.test(f)), '_preview_ui8_all.ogg 冇入 build');
  ok(U.FILES.every(f => D.AUDIO.cues[f.replace('sfx_ui8_', 'ui8_')] && D.AUDIO.cues[f.replace('sfx_ui8_', 'ui8_')].bus === 'ui'), '全部 ui8 cue 登記（ui bus，預載）'); }
console.log(`\n結果：${pass} 通過，${fail} 失敗`); process.exit(fail ? 1 : 0);
