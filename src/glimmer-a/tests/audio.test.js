/* 音訊導演測試（Node 無依賴）：node tests/audio.test.js ——cue 表／檔案存在／規則（間隔、事件優先、連擊、loop、BGM 時段） */
const fs = require('fs'), path = require('path'), crypto = require('crypto');
const SIM = require('../src/sim.js'); const D = require('../src/data.js'); const BEH = require('../src/behavior.js'); const LT = require('../src/lighting.js');
const AUD = require('../src/audio.js');
const A = D.PARAMS.audio, AU = D.AUDIO;
let pass = 0, fail = 0;
function ok(c, name, info) { if (c) { pass++; console.log('  ✓ ' + name); } else { fail++; console.log('  ✗ ' + name + (info !== undefined ? '  → ' + info : '')); } }
const root = path.join(__dirname, '..');
const mkS = (needs, o) => { const s = SIM.newState(1e12, 5); s.stage = 'adult'; s.form = 'soft'; Object.assign(s.needs, { hunger: 90, mood: 90, clean: 90, energy: 90 }, needs || {}); return Object.assign(s, o || {}); };
function world(s, b, hour, extra) { const pw = LT.compute(hour); return Object.assign({ beh: b, s, period: pw.period, ev: null, mode: 'main' }, extra || {}); }
function drive(d, sec, w, dt) { const out = []; dt = dt || 1 / 30; for (let t = 0; t < sec; t += dt) { const r = AUD.update(d, dt, w); out.push(...r.cues); } return out; }

console.log('# cue 表／檔案');
{
  const files = new Set(Object.values(AU.cues).map(c => c.file).concat(Object.values(AU.loops).map(l => l.file)));
  const miss = [...files].filter(f => !fs.existsSync(path.join(root, 'audio/sfx', f + '.ogg')));
  ok(miss.length === 0, 'cue 表 ' + Object.keys(AU.cues).length + ' 個 cue／' + files.size + ' 個檔全部存在於 audio/sfx', miss.join(','));
  const bm = Object.values(AU.bgm).filter(f => !fs.existsSync(path.join(root, 'audio/bgm', f + '.ogg')));
  ok(bm.length === 0 && Object.keys(AU.bgm).join() === 'morning,noon,evening,night', '4 條時段 BGM 都存在');
  ok(Math.abs(AU.barSec - 3.5294) < 1e-3 && AU.bgmBars.noon === 20 && AU.bgmBars.night === 12, '小節長 3.5294s（68 BPM 4/4），小節數 16/20/16/12');
  ok(Object.keys(AU.eventCue).length === 10 && AU.eventCue.grumpy_tap === AU.eventCue.grumpy && Object.values(AU.eventCue).every(c => AU.cues[c]), '池內 9 個事件各有 cue（含 firefly_walk）；grumpy_tap 共用 sulk 音、唔係新文案');
  // 音訊檔勿改：同遊音 staging 逐檔 sha256 比對（staging 唔存在就跳過）
  const stg = '/workspace/遊音-staging/audio'; let diff = [];
  if (fs.existsSync(stg)) {
    const sh = (f) => crypto.createHash('sha256').update(fs.readFileSync(f)).digest('hex');
    for (const sub of ['bgm', 'sfx']) for (const f of fs.readdirSync(path.join(root, 'audio', sub))) { const o = path.join(stg, sub, f); if (!fs.existsSync(o) || sh(o) !== sh(path.join(root, 'audio', sub, f))) diff.push(sub + '/' + f); }
    ok(diff.length === 0, '音訊檔同遊音最新版逐檔相同（未被改動）', diff.join(','));
  } else console.log('  - staging 不存在，跳過 sha 比對');
  const unused = fs.readdirSync(path.join(root, 'audio/sfx')).map(f => f.replace('.ogg', '')).filter(f => !files.has(f));
  console.log('    未接駁嘅 sfx：' + unused.join(', '));
}

console.log('# 規則');
{
  const s = mkS(), b = BEH.create(1), d = AUD.createDirector(1);
  // UI／照顧
  AUD.notify(d, 'tap', {}, s); AUD.notify(d, 'fed', { kind: 'meal' }, s); let o = drive(d, 3, world(s, b, 14));
  const names = o.map(c => c.name);
  ok(names[0] === 'tap' && names.includes('feed_meal') && names.includes('pet_content'), '點擊→tap；餵飯→feed_meal＋稍後 pet_content', names.join(','));
  AUD.notify(d, 'played', {}, s); AUD.notify(d, 'rinsed', {}, s); AUD.notify(d, 'poop', {}, s); AUD.notify(d, 'sleep', { on: true }, s); AUD.notify(d, 'hatch', {}, s); AUD.notify(d, 'evolve', {}, s); AUD.notify(d, 'reward', {}, s);
  o = drive(d, 8, world(s, b, 14)).map(c => c.name);
  ok(['play_tease', 'clean_wash', 'clean_poop', 'sleep_on', 'hatch', 'evolve', 'reward_orb'].every(n => o.includes(n)), '玩／洗／便便／關燈／孵化／進化／獎勵 cue 全部出', o.join(','));
}
{
  // 寵物聲間隔 ≥ 4s、事件優先
  const s = mkS(), b = BEH.create(2), d = AUD.createDirector(2); const w = world(s, b, 14);
  const out = []; for (let i = 0; i < 12; i++) { AUD.emit(d, out, 'pet_happy'); drive(d, 1, w); }
  const ts = out.map(c => c.t); ok(out.length >= 2 && out.length <= 4, '寵物聲最短間隔 ' + A.petMinGap + 's（12 秒內 ' + out.length + ' 次）');
  const rs = out.map(c => c.rate); ok(rs.every(r => r >= 0.95 && r <= 1.05) && new Set(rs).size > 1, '寵物聲 playbackRate ±5% 隨機');
  const d2 = AUD.createDirector(3); const o2 = []; const ew = world(s, b, 14, { ev: { id: 'butterfly', t: 0, dur: 7 } });
  const r = drive(d2, 1, ew).map(c => c.name); AUD.emit(d2, o2, 'pet_happy');
  ok(r.includes(AU.eventCue.butterfly) && o2.length === 0, '事件音播放期間寵物聲靜音（事件優先）', r.join(','));
}
{
  // 連擊 rate
  const s = mkS(), b = BEH.create(2), d = AUD.createDirector(2); AUD.notify(d, 'mg-start', {}, s);
  for (let i = 0; i < 11; i++) AUD.notify(d, 'mg-catch', {}, s);
  const o = drive(d, 1, world(s, b, 14, { mode: 'minigame' })).filter(c => c.name === 'mg_catch');
  ok(o.length === 11 && o[0].rate === 1 && o[3].rate > 1.18 && o[10].rate > 1.58 && o[10].rate > o[6].rate, '接星屑連擊音高遞升（1 → ' + o[10].rate.toFixed(3) + '）');
  AUD.notify(d, 'mg-stone', {}, s); AUD.notify(d, 'mg-catch', {}, s); const o2 = drive(d, 1, world(s, b, 14, { mode: 'minigame' }));
  ok(o2.some(c => c.name === 'mg_miss') && o2.find(c => c.name === 'mg_catch').rate === 1, '碰石頭→mg_miss，連擊歸零');
  AUD.notify(d, 'mg-result', { win: true }, s); ok(drive(d, 2, world(s, b, 14, { mode: 'minigame' })).some(c => c.name === 'mg_win'), '勝出→mg_win');
}
{
  // 行為日誌 → cue（呵欠／摸／鬧脾氣／撞花盆）、loops
  const s = mkS(), ctx = (h) => { const pw = LT.compute(h); return { s, pw, sun: pw.sun, override: null, event: null }; };
  const b = BEH.create(4), d = AUD.createDirector(4), c = ctx(14);
  BEH.force(b, 'yawn', c); for (let i = 0; i < 120; i++) BEH.step(b, c);
  let o = drive(d, 0.1, world(s, b, 14)).map(x => x.name); ok(o.includes('pet_yawn'), '呵欠 → pet_yawn', o.join(','));
  BEH.force(b, 'wake', c); for (let i = 0; i < 120; i++) BEH.step(b, c); b.state = 'stay'; b.phase = '';
  for (let i = 0; i < 700; i++) BEH.step(b, c);
  BEH.tap(b, 'pet', b.x + b.dir * 5); for (let i = 0; i < 20; i++) BEH.step(b, c); o = drive(d, 8, world(s, b, 14)).map(x => x.name);   // 點正面（唔觸發回頭）
  ok(o.includes('pet_touch_a') || o.includes('pet_touch_b'), '摸 → pet_touch_a／b', o.join(','));
  const b2 = BEH.create(5), d2 = AUD.createDirector(5); BEH.force(b2, 'wake', c); for (let i = 0; i < 120; i++) BEH.step(b2, c); b2.state = 'stay'; b2.phase = ''; for (let i = 0; i < 700; i++) BEH.step(b2, c);
  for (let i = 0; i < 6; i++) { BEH.tap(b2, 'pet', 0); for (let k = 0; k < 90; k++) BEH.step(b2, c); }
  o = drive(d2, 0.1, world(s, b2, 14)).map(x => x.name);
  ok(o.includes('pet_grumpy') && o.filter(n => /touch/.test(n)).length <= 3, '連點 → pet_grumpy；第 4 下起唔再播 touch（' + o.join(',') + '）');
  const b3 = BEH.create(6), d3 = AUD.createDirector(6); BEH.force(b3, 'bump', c); for (let i = 0; i < 60 * 25; i++) BEH.step(b3, c);
  o = drive(d3, 0.1, world(s, b3, 14)).map(x => x.name); ok(o.includes('env_pot_bump'), '撞花盆 → env_pot_bump', o.join(','));
  const b4 = BEH.create(7), d4 = AUD.createDirector(7); BEH.force(b4, 'sunbathe', c); for (let i = 0; i < 60 * 7; i++) BEH.step(b4, c);
  const r = AUD.update(d4, 0.03, world(s, b4, 14)); ok(r.loops.sunbathe === true, '曬太陽躺低 → sunbathe loop 開');
  const ss = mkS({}, { sleeping: true }); const r2 = AUD.update(AUD.createDirector(8), 0.03, world(ss, BEH.create(8), 23)); ok(r2.loops.sleep_breath === true && r2.bgm === 'night', '瞓覺 → sleep_breath loop＋night BGM');
}
{
  // 需求警告冷卻、時段 BGM、egg 唔出聲
  const s = mkS({ hunger: 10 }), b = BEH.create(9), d = AUD.createDirector(9);
  const o = drive(d, 200, world(s, b, 14)).filter(c => c.name === 'pet_hungry' || c.name === 'pet_uncomfortable');
  ok(o.length >= 1 && o.length <= Math.ceil(200 / A.needWarnEvery) + 1, '需求警告聲有冷卻 ' + A.needWarnEvery + 's（200 秒 ' + o.length + ' 次）');
  const per = { 7: 'morning', 10.9: 'morning', 11: 'noon', 16.9: 'noon', 17: 'evening', 22.9: 'evening', 23: 'night', 3: 'night', 6.9: 'night' };
  const bad = Object.keys(per).filter(h => AUD.update(AUD.createDirector(1), 0.03, world(mkS(), BEH.create(1), +h)).bgm !== per[h]);
  ok(bad.length === 0, 'BGM 跟時段（早07／午11／晚17／夜23）', bad.join(','));
  const e = mkS(); e.stage = 'egg'; let thr = false; try { drive(AUD.createDirector(1), 3, world(e, BEH.create(1), 14)); } catch (x) { thr = true; } ok(!thr, '蛋階段唔會拋錯');
}

{
  // 第一段：D2 點一下回頭 → sfx_pet_turn_huh_a／b（隨機；共用冷卻 1.5s；代替 touch 聲）；其餘 14 個生命感音效已註冊但未觸發
  const fs = require('fs'), path = require('path');
  const LIVE = ['sneeze', 'scratch', 'step_hop', 'step_drag', 'turn_huh', 'nuzzle_purr', 'reunion_happy', 'bug_pat'];
  const names = []; LIVE.forEach(n => ['a', 'b'].forEach(v => names.push('pet_' + n + '_' + v)));
  const miss = names.filter(n => !AU.cues[n] || !fs.existsSync(path.join(__dirname, '..', 'audio', 'sfx', AU.cues[n].file + '.ogg')));
  ok(miss.length === 0, '16 個生命感音效已註冊＋檔案喺 audio/sfx', miss.join(','));
  ok(names.filter(n => !/turn_huh/.test(n)).every(n => AU.cues[n].reserved), '第一段只觸發 turn_huh：其餘 14 個標 reserved');
  const s = mkS(), c = { s, pw: LT.compute(14), sun: 1, override: null, event: null };
  let seen = { a: 0, b: 0 }, touchWithTurn = 0, turns = 0, cdOk = true;
  for (let seed = 1; seed <= 40; seed++) {
    const b = BEH.create(seed), d = AUD.createDirector(seed);
    for (let i = 0; i < 30; i++) BEH.step(b, c);
    b.state = 'stay'; b.phase = ''; b.dir = 1; b.x = 0; b.lastTouch = b.t;
    BEH.tap(b, 'pet', -12); BEH.step(b, c);           // 背後點 → 回頭
    const o = drive(d, 0.5, world(s, b, 14)).map(x => x.name);
    if (b.dir === -1) turns++;
    if (o.includes('pet_turn_huh_a')) seen.a++; if (o.includes('pet_turn_huh_b')) seen.b++;
    if (o.some(n => /touch/.test(n))) touchWithTurn++;
    // 0.5s 內再回頭一次（冷卻中）→ 唔再出 huh
    b.state = 'stay'; b.lastTouch = b.t; BEH.tap(b, 'pet', 12); BEH.step(b, c);
    const o2 = drive(d, 0.3, world(s, b, 14)).map(x => x.name);
    if (o2.some(n => /turn_huh/.test(n))) cdOk = false;
  }
  ok(turns === 40, '背後點 → 轉身（40/40）', turns);
  ok(seen.a > 0 && seen.b > 0 && seen.a + seen.b === 40, 'turn_huh a/b 隨機（a ' + seen.a + '／b ' + seen.b + '）');
  ok(touchWithTurn === 0, '回頭嗰下唔疊 touch 聲', touchWithTurn);
  ok(cdOk && AU.cues.pet_turn_huh_a.cd >= 1.5 && AU.cues.pet_turn_huh_a.cdKey === AU.cues.pet_turn_huh_b.cdKey, 'turn_huh 共用冷卻 ≥1.5s');
}

console.log(`\n結果：${pass} 通過，${fail} 失敗`);
process.exit(fail ? 1 : 0);
