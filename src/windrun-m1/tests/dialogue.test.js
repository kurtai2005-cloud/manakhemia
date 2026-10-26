// node tests/dialogue.test.js —— 對話執行器／條件／動作／lint／資料完整性／報名流程／存檔往返
const assert = require('assert'); const { loadData } = require('./_data.js');
const Save = require('../src/save.js'), Logic = require('../src/logic.js'), Dlg = require('../src/dialogue.js');
const pend = []; let n = 0; const ok = (c, m) => { assert(c, m); n++; }; const eq = (a, b, m) => { assert.deepStrictEqual(a, b, m); n++; };
const D = loadData();
function mk(opts) {
  opts = opts || {}; const mem = {}; const store = Save.Store({ getItem: k => mem[k] || null, setItem: (k, v) => { mem[k] = v; }, removeItem: k => { delete mem[k]; } });
  let t = 1e6; const hooks = Object.assign({}, opts.hooks); const calls = []; for (const d of ['teleport', 'play_sfx', 'open_ui', 'begin_capture', 'start_match', 'bubble', 'play_cue', 'npc_face', 'say', 'push', 'open_gate']) hooks[d] = hooks[d] || (a => { calls.push(a); });
  const G = Logic.create({ save: opts.save || Logic.newGame(D, { deviceId: 'dev-test', name: '阿風' }), data: D, tuning: opts.tuning, hooks, store, now: () => t });
  G.warnList = G.warns; G.tick = ms => { t += ms; }; G.calls = calls; const R = Dlg.create(G, { sets: D.dialogues }); return { G, R, mem, calls };
}
const lines = (R, cap) => { const out = []; let st = R.state, g = 0; while (st && g++ < (cap || 200)) { out.push(st.node); if (st.hasChoices) break; st = R.advance(); } return out; };
const ctxLint = { flags: D.flags.flags, vars: D.flags.vars, speakers: D.flags.speakers, emotes: D.flags.emotes, maxChars: D.tuning.dialog_max_chars, allSets: D.dialogues, matches: D.matches };

// 1. lint：全部對話集 0 error；統計 warning
let nodes = 0, warnings = [];
for (const id of Object.keys(D.dialogues)) { const r = Dlg.lint(D.dialogues[id], ctxLint); nodes += Object.keys(D.dialogues[id].nodes).length; if (r.errors.length) console.log(id, r.errors); eq(r.errors.length, 0, 'lint ' + id); warnings = warnings.concat(r.warnings); }
console.log('lint：' + Object.keys(D.dialogues).length + ' 個對話集、' + nodes + ' 個節點、0 error、' + warnings.length + ' warning' + (warnings.length ? '（' + [...new Set(warnings.map(w => w.code))].join(',') + '）' : ''));
// 1b. lint 能抓到壞資料
const bad = { schema: 'dialogue/v1', id: 'bad', entry: [{ cond: { flag: 'x_unreg' }, goto: 'a' }], nodes: {
  a: { speaker: 'elder', text: 'x'.repeat(40), next: 'b' }, b: { speaker: 'nobody', emote: 'angry', text: 'hi', next: 'a', choices: [{ id: '1', text: 'y'.repeat(17), next: 'zz' }, { id: '2', text: 'a', next: 'a' }, { id: '3', text: 'a', next: 'a' }, { id: '4', text: 'a', next: 'a' }] },
  c: { speaker: 'elder', text: 'orphan', on_enter: [{ do: 'fly' }] } } };
const rb = Dlg.lint(bad, ctxLint), codes = new Set(rb.errors.concat(rb.warnings).map(x => x.code));
for (const c of ['E_ENTRY_LAST', 'E_TEXT_LEN', 'E_SPEAKER', 'E_EMOTE', 'E_CHOICES', 'E_CHOICE_LEN', 'E_GOTO', 'E_LOOP', 'E_DO_UNKNOWN', 'W_UNREACHABLE', 'W_FLAG_UNREG']) ok(codes.has(c), 'lint 應報 ' + c + '，實得 ' + [...codes].join(','));
// 1c. 資料交叉檢查：match.dialogue／flags／on_end
for (const m of Object.values(D.matches)) { for (const k of ['pre', 'post_win', 'post_lose']) if (m.dialogue && m.dialogue[k]) ok(D.dialogues[m.dialogue[k]], m.id + ' 對話集 ' + m.dialogue[k] + ' 存在'); for (const f of (m.req.flags || []).concat(m.req.not_flags || [])) ok(D.flags.flags[f], '旗標登記 ' + f);
  for (const side of ['win', 'lose']) for (const a of m.on_end[side]) { ok(Logic.ALL_DOS.indexOf(a.do) >= 0, 'on_end do ' + a.do); if (a.flag) ok(D.flags.flags[a.flag], 'on_end 旗標登記 ' + a.flag); } }

// 2. 條件
{ const { G } = mk(); G.setFlag('met_sang', true); G.setVar('fern_attitude', 'rival');
  ok(G.cond({ flag: 'met_sang' }) && !G.cond({ flag: 'met_fern' }) && G.cond({ not: { flag: 'met_fern' } }), 'flag/not'); ok(G.cond({ all: [{ flag: 'met_sang' }, { var: 'leaf', op: '>=', value: 50 }] }) && !G.cond({ all: [{ flag: 'met_sang' }, { flag: 'met_fern' }] }), 'all');
  ok(G.cond({ any: [{ flag: 'met_fern' }, { flag: 'met_sang' }] }) && !G.cond({ any: [] }), 'any'); ok(G.cond({ has_value: 'fern_attitude' }) && !G.cond({ has_value: 'registered_match' }), 'has_value'); ok(G.cond({ var: 'leaf', op: '==', value: 50 }), 'start_leaf=50');
  for (const [op, v, exp] of [['<', 51, true], ['<=', 50, true], ['>', 50, false], ['>=', 51, false], ['!=', 49, true]]) eq(G.cond({ var: 'leaf', op, value: v }), exp, 'op ' + op);
  ok(G.cond({ var: 'party_size', op: '<', var2: 'r1_min_team' }), 'var2；party_size 0 < 2'); ok(!G.cond({ seen: 'x' }), 'seen 初始 false'); G.markSeen('x'); ok(G.cond({ seen: 'x' }), 'seen');
  eq(G.text('{player}有{leaf}葉，費{fee}'), '阿風有50葉，費20', '模板'); ok(!G.cond({ flag: 'zzz_unknown' }) && G.warns.some(w => /zzz_unknown/.test(w)), '未登記旗標：false＋警告'); }
// 3. 序章：完整走一次（含選項）
{ const { G, R, calls } = mk(); R.start('d_prologue'); const a = lines(R); eq(a.length, 6 + 7, 'P0 6 句＋P1 7 句'); ok(!R.active && G.getFlag('intro_p1_done') && G.save.chapter.step === 'c1_start', 'P1 完結：旗標＋任務');
  R.start('d_prologue'); ok(!R.active, 'P1 只播一次（entry 保底 → 無內容）');
  R.start('d_elder_intro'); let l = lines(R); ok(R.state && R.state.node === 'e_react' && R.state.hasChoices, '停喺選項 e_react'); ok(G.getFlag('got_mochi') && G.save.party.length === 1 && G.save.party[0].species === 'mochi' && G.save.party[0].lv === 3, '已發苔團 Lv3'); ok(calls.some(c => c.do === 'open_ui' && c.name === 'naming'), '命名視窗事件');
  eq(R.state.choices.map(c => c.id), ['sleepy', 'care'], '選項'); R.choose(1); eq(R.state.node, 'e_rB', '選項 B 反應'); lines(R); ok(!R.active && G.getFlag('prologue_done'), 'P3 完結：prologue_done'); eq(G.getVar('party_size'), 1, 'party_size=1'); eq(G.save.chapter.step, 'c1_start');
  const rt = Save.normalize(JSON.parse(Save.serialize(G.save))); ok(rt.ok, '存檔往返'); eq(rt.save.flags.prologue_done, true); eq(rt.save.dialogue.seen.includes('e_give'), true, 'seen 存檔'); }
// 3b. 整段跳過：必須仍發苔團、設旗標（遊測重點）
{ const { G, R } = mk(); R.start('d_elder_intro'); R.skip(); ok(R.state.hasChoices, '快進停喺選項'); R.skip({ choices: 'first' }); ok(!R.active, '整段跳過走到尾'); ok(G.getFlag('prologue_done') && G.getFlag('got_mochi') && G.save.party.length === 1, '跳過仍發野靈＋旗標'); }
// 4. 老鐘 hub 分流
{ const cases = [[{}, 'elder_capture'], [{ captured_badger: 1 }, 'elder_ready'], [{ captured_badger: 1, reg: 1 }, 'elder_registered'], [{ c1r1_won: 1, captured_badger: 1 }, 'elder_won']];
  for (const [fl, exp] of cases) { const { G, R } = mk(); G.setFlag('prologue_done', true); for (const k of ['captured_badger', 'c1r1_won']) if (fl[k]) G.setFlag(k, true); if (fl.reg) G.setVar('registered_match', 'c1_r1'); R.start('d_elder_hub'); eq(R.state.node, exp, '老鐘入口 ' + JSON.stringify(fl)); } }
// 4b. 老鐘贈款：leaf<20 才顯示，最多 3 次
{ const { G, R } = mk(); G.setFlag('prologue_done', true); G.setFlag('captured_badger', true); G.setVar('leaf', 5); let gifts = 0;
  for (let i = 0; i < 5; i++) { R.start('d_elder_hub'); R.advance(); ok(R.state.node === 'elder_ready_menu', 'menu'); const has = R.state.choices.some(c => c.id === 'short'); if (has) { R.choose(1); gifts++; lines(R); G.setVar('leaf', 5); } else { R.choose(0); } }
  eq(gifts, 3, '贈款上限 3'); eq(G.getVar('elder_gift_count'), 3); G.setVar('leaf', 50); R.start('d_elder_hub'); R.advance(); ok(!R.state.choices.some(c => c.id === 'short'), 'leaf≥20 唔顯示「唔夠喎」'); }
// 5. 蕨生
{ const { G, R } = mk(); G.setFlag('prologue_done', true); R.start('d_fern_first'); eq(R.state.node, 'ff1'); lines(R); R.choose(0); eq(G.getVar('fern_attitude'), 'rival'); lines(R); ok(G.getFlag('met_fern'), 'met_fern'); R.start('d_fern_first'); eq(R.state.node, 'fi1', '再傾＝fi1');
  R.start('d_fern_idle'); eq(R.state.node, 'fi1'); G.setFlag('captured_badger', true); R.start('d_fern_idle'); eq(R.state.node, 'fi2'); R.start('d_fern_prematch'); eq(R.state.node, 'fp1'); lines(R); ok(G.getFlag('seen_fern_prematch')); R.start('d_fern_prematch'); eq(R.state.node, 'fp3');
  G.setFlag('c1r1_lost_last', true); R.start('d_fern_after_r1'); eq(R.state.node, 'fl1'); G.setFlag('c1r1_won', true); R.start('d_fern_after_r1'); eq(R.state.node, 'fw1'); }
// 6. 桑姨：首見、資格不足指路、葉幣不足、報名成功（扣費／旗標／任務／存檔）、已報名、勝後、敗後
{ const { G, R, mem } = mk(); G.setFlag('prologue_done', true); G.setFlag('got_mochi', true); G.giveSpirit('mochi', 3);
  R.start('d_sang_hub'); eq(R.state.node, 'sang_first'); R.advance(); R.advance(); eq(R.state.node, 'sang_menu'); ok(G.getFlag('met_sang'));
  R.choose(0); eq(R.state.node, 'sang_need_two', '只得 1 隻＝去向提示（唔係單純拒絕）'); ok(/結緣/.test(R.state.text), '提示去小徑結緣'); R.advance(); eq(R.state.node, 'sang_menu');
  G.giveSpirit('gravelbadger', 4); G.setVar('leaf', 10); R.choose(0); eq(R.state.node, 'sang_no_leaf'); ok(/老鐘/.test(R.state.text), '葉幣不足提示老鐘'); R.advance(); eq(G.getVar('leaf'), 10);
  G.setVar('leaf', 50); R.choose(0); eq(R.state.node, 'sang_reg_ok'); ok(/20 葉幣/.test(R.state.text), '{fee} 展開');
  eq(G.getVar('leaf'), 30, '扣報名費 20'); eq(G.getVar('registered_match'), 'c1_r1'); ok(!G.getFlag('formation_done'), 'formation_done=false'); eq(G.save.chapter.step, 'c1_enter'); ok(mem['windrun_save'], 'autosave 已寫入 Store');
  const saved = JSON.parse(mem['windrun_save']); eq(saved.vars.registered_match, 'c1_r1', '存檔含 registered_match'); eq(saved.player.leaf, 30);
  lines(R); ok(!R.active); R.start('d_sang_hub'); eq(R.state.node, 'sang_registered'); ok(G.isDone('hint_fast_entry'), '快速入場提示只出一次');
  // 賽後：敗
  let res = G.finishMatch('c1_r1', { win: false }); ok(res.ok && !res.win && res.leaf === 10, '敗：+10 葉'); ok(G.getFlag('c1r1_lost_last') && G.getVar('registered_match') === '', '敗：旗標＋清報名'); eq(G.getVar('leaf'), 40);
  R.start('d_sang_hub'); eq(R.state.node, 'sang_lost'); lines(R); R.choose(0); eq(R.state.node, 'sang_reg_ok', '敗後可即刻再報（付費）'); eq(G.getVar('leaf'), 20, '再扣 20'); lines(R);
  res = G.finishMatch('c1_r1', { win: true, margin_m: 30 }); ok(res.win && res.first && res.leaf === 45 && res.ups.length === 2, '勝：+45、兩隻出場者各加 exp'); ok(G.getFlag('c1r1_won') && !G.getFlag('c1r1_lost_last') && G.save.cleared.includes('c1_r1'), '勝：旗標／cleared'); eq(G.save.chapter.step, 'c1_done_m1');
  eq(G.save.stats.races, 2); eq(G.save.stats.wins, 1); const mo = G.save.party[0]; ok(mo.lv >= 3 && mo.exp >= 0, '經驗結算'); R.start('d_sang_hub'); eq(R.state.node, 'sang_won'); }
// 6b. register_match 失敗時 goto（action 層）
{ const { G, R } = mk(); G.giveSpirit('mochi', 3); G.setFlag('got_mochi', true); G.setVar('leaf', 20); const r = G.run({ do: 'register_match', match: 'c1_r1' }); eq(r.goto, 'sang_need_two'); G.giveSpirit('gravelbadger', 4); G.setVar('leaf', 19); eq(G.run({ do: 'register_match', match: 'c1_r1' }).goto, 'sang_no_leaf'); eq(G.getVar('leaf'), 19, '失敗唔扣費'); }
// 6c. r1_min_team=1（備案）：單隻亦可報名
{ const { G, R } = mk({ tuning: { r1_min_team: 1 } }); G.giveSpirit('mochi', 3); G.setFlag('got_mochi', true); ok(G.canRegister('c1_r1').ok, 'r1_min_team=1 單隻可報'); }
// 7. 結緣：冷卻、勝出
{ const { G, R, calls } = mk(); G.setFlag('got_mochi', true); G.giveSpirit('mochi', 3); R.start('d_capture_intro'); lines(R); eq(R.state.node, 'cap3'); R.choose(0); ok(calls.some(c => c.do === 'begin_capture' && c.match === 'cap_trail_badger'), 'begin_capture');
  const r = G.finishMatch('cap_trail_badger', { win: false }); ok(r.ok && r.leaf === 0, '結緣敗：無獎金'); R.start('d_capture_intro'); eq(R.state.node, 'cap_panting', '冷卻中'); G.tick(10001); R.start('d_capture_intro'); eq(R.state.node, 'cap1', '冷卻完（10 s）');
  const w = G.finishMatch('cap_trail_badger', { win: true }); ok(w.win && G.getFlag('captured_badger') && G.save.party.length === 2 && G.save.party[1].species === 'gravelbadger' && G.save.party[1].lv === 4, '結緣勝：得碎石獾 Lv4'); eq(G.getVar('party_size'), 2, 'party_size 派生＝2（match 資料已刪 add_var party_size，由引擎按隊伍人數維護）'); ok(!G.warns.some(x => /party_size/.test(x)), '無 party_size 警告'); eq(G.save.chapter.step, 'c1_register'); ok(G.save.dex.owned.includes('gravelbadger')); }
// 8. 阻塞型事件：wait 令 R.blocked，advance 無效直至完成
{ let res; const hooks = { wait: a => new Promise(r => { res = r; }) }; const { G, R } = mk({ hooks }); const set = { schema: 'dialogue/v1', id: 't', entry: [{ goto: 'a' }], nodes: { a: { speaker: 'narrator', text: 'A', on_enter: [{ do: 'wait', ms: 10 }, { do: 'set_flag', flag: 'met_sang' }], next: 'b' }, b: { speaker: 'narrator', text: 'B', next: null } } };
  R.load(set); R.start('t'); ok(R.blocked, '阻塞中'); const st = R.state; R.advance(); eq(R.state.node, 'a', '阻塞期間 advance 無效'); ok(!G.getFlag('met_sang'), '阻塞型後嘅動作未執行'); res(); pend.push((async () => { await R.whenReady(); ok(G.getFlag('met_sang'), '阻塞完成後，後續動作執行'); ok(!R.blocked); R.advance(); eq(R.state.node, 'b', '解除阻塞後可推進'); })()); }
// 9. once／seen／迴圈保護／未知節點
{ const { G, R } = mk(); R.load({ schema: 'dialogue/v1', id: 'o', entry: [{ goto: 'a' }], nodes: { a: { speaker: 'narrator', text: 'once', once: true, next: 'b', on_enter: [{ do: 'add_var', var: 'elder_gift_count', delta: 1 }] }, b: { speaker: 'narrator', text: 'B', next: null } } });
  R.start('o'); eq(R.state.node, 'a'); lines(R); R.start('o'); eq(R.state.node, 'b', 'once：再入直走 next'); eq(G.getVar('elder_gift_count'), 1, 'once：事件唔重播');
  const w = []; G.onWarn = m => w.push(m); R.load({ schema: 'dialogue/v1', id: 'l', entry: [{ goto: 'x' }], nodes: { x: { speaker: 'system', next: 'y' }, y: { speaker: 'system', next: 'x' } } }); R.start('l'); ok(!R.active && w.some(m => /迴圈/.test(m)), '純邏輯迴圈保護');
  R.load({ schema: 'dialogue/v1', id: 'm', entry: [{ goto: 'nope' }], nodes: {} }); R.start('m'); ok(!R.active && w.some(m => /不存在/.test(m)), '節點不存在唔崩潰'); R.start('no_such_set'); ok(w.some(m => /對話集不存在/.test(m))); }
// 10. 選項 cond：hidden／disabled_hint
{ const { G, R } = mk(); R.load({ schema: 'dialogue/v1', id: 'c', entry: [{ goto: 'a' }], nodes: { a: { speaker: 'narrator', text: 'q', choices: [{ id: 'x', text: 'X', cond: { flag: 'met_fern' }, next: null }, { id: 'y', text: 'Y', cond: { flag: 'met_fern' }, disabled_hint: '未解鎖', next: null }, { id: 'z', text: 'Z', next: null }] } } });
  R.start('c'); eq(R.state.choices.map(c => [c.id, c.enabled, c.hint]), [['y', false, '未解鎖'], ['z', true, '']], 'hidden／disabled'); const before = R.state; R.choose(1); eq(R.state, before, '灰化選項唔可揀'); R.choose(2); ok(!R.active); }
// 11. 存檔 v1 對齊：vars／dialogue.seen／events.done 往返＋惡意輸入
{ const s = Save.create({ now: 5, deviceId: 'dev-a' }); s.vars = { registered_match: 'c1_r1', elder_gift_count: 2, fern_attitude: 'rival', 'BAD KEY': 1, __proto__x: 1 }; s.dialogue = { seen: ['sang_first', 'x y', 'a'] }; s.events = { done: ['ev_elder_intro', 'hint_fast_entry', 'BAD'] }; s.flags = { prologue_done: true, 'story.ch1.x': true, 'Bad': true };
  const r = Save.normalize(s).save; eq(r.vars, { elder_gift_count: 2, fern_attitude: 'rival', registered_match: 'c1_r1' }, 'vars 清洗'); eq(r.dialogue.seen, ['a', 'sang_first'], 'seen 清洗排序'); eq(r.events.done, ['ev_elder_intro', 'hint_fast_entry']); eq(r.flags, { prologue_done: true, 'story.ch1.x': true }, '扁平＋命名空間旗標並存');
  eq(Save.serialize(Save.normalize(r).save), Save.serialize(r), '冪等'); const old = Save.create({ now: 1, deviceId: 'dev-b' }); delete old.vars; delete old.dialogue; delete old.events; const o2 = Save.normalize(old).save; eq(o2.vars, {}); eq(o2.dialogue.seen, [], '舊 v1 存檔（無新欄位）補預設，唔使升版');
  ok(Save.fromCode(Save.toCode(r)).ok, '存檔碼往返含新欄位'); }
// 12. 決定性：同一輸入同一路徑
{ const run = () => { const { G, R } = mk(); R.start('d_elder_intro'); R.skip({ choices: 'first' }); return Save.serialize(Object.assign({}, G.save, { deviceId: 'x', createdAt: 0, savedAt: 0 })); }; eq(run(), run(), '決定性'); }
// 13. 遊策 11:25 決定：資料一致性（party_size／alias／老鐘石伯／顯示名／碰撞盒）
{ const fs = require('fs'), path = require('path'), root = path.join(__dirname, '..');
  const allJson = []; (function walk(d) { for (const f of fs.readdirSync(d)) { const q = path.join(d, f); if (fs.statSync(q).isDirectory()) walk(q); else if (/\.json$/.test(f)) allJson.push(q); } })(path.join(root, 'data'));
  for (const f of allJson) { const t = fs.readFileSync(f, 'utf8'); ok(!/"var"\s*:\s*"party_size"\s*,\s*"delta"/.test(t), f + ' 無 add_var party_size'); ok(!/石伯/.test(t), f + ' 無「石伯」（ch2 老隊長，唔屬 ch1 資料）'); ok(!/borrow|借野靈|借用野靈/.test(t), f + ' 無借野靈對白'); }
  const ov = JSON.parse(fs.readFileSync(path.join(root, 'data/overlay/town_morningmoss.json'), 'utf8')); ok(!('dialog_alias' in ov), 'overlay 無 dialog_alias'); eq(ov.npcs.npc_elder.display, '老鐘', 'npc_elder 顯示＝老鐘（ch1 村長）'); eq(ov.npcs.npc_elder.dialogs.map(d => d.id), ['d_elder_intro', 'd_elder_hub'], 'npc_elder 對話清單：序章前 d_elder_intro、之後 d_elder_hub（獨立集，非 alias）');
  ok(D.dialogues.d_elder_intro && D.dialogues.d_elder_intro.nodes.e_p2_1 && D.dialogues.d_elder_intro.nodes.p3_end && !D.dialogues.d_elder_hub.nodes.e_p2_1, 'd_elder_intro＝序章 P2/P3 獨立集；d_elder_hub 只含常駐節點');
  ok(/我係老鐘，呢條鎮嘅村長/.test(JSON.stringify(D.dialogues.d_elder_intro)), 'd_elder_intro：老鐘＝村長');
  ok(D.dialogues.d_opponent_misc && D.dialogues.d_capture_intro, 'd_opponent_misc／d_capture_intro 保留');
  const sp = JSON.parse(fs.readFileSync(path.join(root, 'data/dialogue/d_objects_town.json'), 'utf8')).nodes.registry_counter_01; eq(sp.text, '櫃台後有位職員低頭整理名冊，見你近前，點頭示意：想報名，就入迴風場。', 'registry_counter_01 旁白（遊策 11:27 單句）'); eq(sp.next, null, 'registry_counter_01 單節點');
  const wsrc = fs.readFileSync(path.join(root, 'src/world.js'), 'utf8'); ok(/HW = 6, HH = 4/.test(wsrc), '碰撞盒 HW=6,HH=4 → 12×8 px');
  ok(/name: '颯鼬'/.test(fs.readFileSync(path.join(root, 'src/data.js'), 'utf8')) && !/風鼬/.test(fs.readFileSync(path.join(root, 'src/data.js'), 'utf8')), '顯示名 風鼬→颯鼬（id windweasel 不變）');
  { const dl = ov.npcs.npc_elder.dialogs, pick = G0 => dl.find(x => !x.cond || G0.cond(x.cond)).id; const a = mk(); eq(pick(a.G), 'd_elder_intro', '序章前老鐘 → d_elder_intro'); a.G.setFlag('prologue_done', true); eq(pick(a.G), 'd_elder_hub', '序章後老鐘 → d_elder_hub'); }
  // party_size 靜默：add_var 被忽略、無警告；give_spirit 後自動 +1
  const { G } = mk(); const w0 = G.warns.length; G.addVar('party_size', 1); eq(G.warns.length, w0, 'add_var party_size 靜默忽略'); eq(G.getVar('party_size'), 0, 'party_size 派生＝隊伍人數 0'); G.giveSpirit('mochi', 3); eq(G.getVar('party_size'), 1, 'give_spirit 後 party_size＝1'); G.addVar('party_size', 1); eq(G.getVar('party_size'), 1, '仍然 1（無重複計）');
  // last_town_door＝字串變數
  G.setVar('last_town_door', 'door_arena'); eq(G.getVar('last_town_door'), 'door_arena', 'last_town_door 字串變數'); }
Promise.all(pend).then(() => console.log('dialogue 測試通過，斷言 ' + n), e => { console.error(e); process.exit(1); });
