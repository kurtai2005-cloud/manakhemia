/* dialogue.js — dialogue/v1 執行器＋lint（DOM-free）。格式：design/adventure-slice/dialogue-format.md。
   用法：const R = WR.Dialogue.create(G, { sets: {id: set} }); R.start('d_sang_hub'); R.state → 目前一句；R.advance()／R.choose(i)／R.skip()。
   事件（on_enter／on_exit／on_choose）由 G.runAll 執行；阻塞型（wait／camera／teleport…）令 R.blocked＝Promise，UI 需等待。
   進入節點即記入 save.dialogue.seen；once 節點之後直接走 next（唔再顯示、唔再執行事件）。 */
(function (g) {
  'use strict';
  const LogicM = (typeof require !== 'undefined' && typeof module !== 'undefined') ? require('./logic.js') : g.WR.Logic;
  const MAXSTEP = 400;
  const chars = t => Array.from(String(t || '')).length;

  function create(G, o) {
    o = o || {}; const sets = o.sets || {}, listeners = { end: [], line: [], start: [] }, R = { G, sets, active: false, state: null, blocked: null, visited: [], cur: null };
    const emit = (k, a) => listeners[k].forEach(f => f(a));
    R.on = (k, f) => { listeners[k].push(f); return R; };
    R.load = set => { sets[set.id] = set; return R; };
    function pickEntry(set) { for (const e of set.entry || []) if (G.cond(e.cond)) return e.goto; return null; }
    function lineState(set, id, node) {
      const choices = (node.choices || []).map((c, i) => { const ok = G.cond(c.cond); return { i, id: c.id, text: G.text(c.text), visible: ok || !!c.disabled_hint, enabled: ok, hint: ok ? '' : (c.disabled_hint || '') }; }).filter(c => c.visible);
      return { set: set.id, node: id, speaker: node.speaker || 'narrator', emote: node.emote || 'neutral', portrait: node.portrait_id || '', expression: node.expression || '', text: G.text(node.text), choices, hasChoices: choices.length > 0, canAdvance: choices.length === 0, autoMs: node.autoadvance_ms | 0, last: !choices.length && (node.next == null), _choiceSrc: (node.choices || []) };
    }
    function finish() { R.active = false; R.state = null; R.cur = null; emit('end', R); }
    function absorb(res) { if (res && res.blocked) { const p = res.blocked; R.blocked = p; p.then(() => { if (R.blocked === p) R.blocked = null; }, () => { if (R.blocked === p) R.blocked = null; }); } return res && res.goto; }
    /** 進入節點（會處理 once／on_enter／branch／純邏輯節點的連鎖），直到停喺一個要顯示嘅節點或結束。 */
    function enter(id) {
      for (let guard = 0; guard < MAXSTEP; guard++) {
        const set = R.cur; if (id == null) return finish();
        const node = set.nodes[id]; if (!node) { G.onWarn && G.onWarn('對話節點不存在：' + set.id + ':' + id); return finish(); }
        if (node.once && G.save.dialogue.seen.indexOf(id) >= 0) { id = node.next == null ? null : node.next; continue; }
        G.markSeen(id); R.visited.push(id);
        const go = absorb(G.runAll(node.on_enter, { set: set.id, node: id }));
        if (go) { id = go; continue; }
        if (node.branch) { let t = null; for (const b of node.branch) if (G.cond(b.cond)) { t = b.goto; break; } if (t == null) return finish(); id = t; continue; }
        const hasText = node.text != null && node.text !== '', hasCh = node.choices && node.choices.length;
        if (!hasText && !hasCh && (node.speaker === 'system' || !node.speaker)) { absorb(G.runAll(node.on_exit)); id = node.next == null ? null : node.next; continue; }
        R.state = lineState(set, id, node); emit('line', R.state); return R.state;
      }
      G.onWarn && G.onWarn('對話迴圈保護：' + R.cur.id); return finish();
    }
    /** 開始對話集 id（或直接傳 set 物件）；opts.node 指定入口節點（繞過 entry 規則）。回傳第一句狀態（或 null＝無內容）。 */
    R.start = (idOrSet, opts) => {
      const set = typeof idOrSet === 'string' ? sets[idOrSet] : idOrSet; if (!set) { G.onWarn && G.onWarn('對話集不存在：' + idOrSet); return null; }
      R.cur = set; R.active = true; R.visited = []; R.blocked = null; emit('start', set);
      const first = (opts && opts.node) || pickEntry(set); return enter(first);
    };
    R.advance = () => {
      if (!R.active || !R.state || R.blocked) return R.state; const st = R.state; if (st.hasChoices) return st;
      const node = R.cur.nodes[st.node]; const go = absorb(G.runAll(node.on_exit, { set: R.cur.id, node: st.node })); return enter(go || (node.next == null ? null : node.next));
    };
    R.choose = i => {
      if (!R.active || !R.state || R.blocked || !R.state.hasChoices) return R.state; const ch = R.state.choices.find(c => c.i === i); if (!ch || !ch.enabled) return R.state;
      const node = R.cur.nodes[R.state.node], c = node.choices[i]; let go = absorb(G.runAll(c.on_choose, { set: R.cur.id, node: R.state.node, choice: c.id })); go = absorb(G.runAll(node.on_exit)) || go;
      return enter(go || (c.next == null ? null : c.next));
    };
    /** 快進：連續推進至下一個選項或結束。opts.choices＝'stop'（預設，停喺選項）｜'first'（揀第一個可用選項，整段跳過用）。 */
    R.skip = opts => {
      const mode = (opts && opts.choices) || 'stop'; let n = 0;
      while (R.active && R.state && !R.blocked && n++ < MAXSTEP) { if (R.state.hasChoices) { if (mode === 'first') { const c = R.state.choices.find(x => x.enabled); if (!c) break; R.choose(c.i); } else break; } else R.advance(); }
      return R.state;
    };
    R.abort = () => { if (R.active) finish(); };
    R.whenReady = () => R.blocked || Promise.resolve();
    return R;
  }

  // ---------- lint（dialogue-format §5）----------
  function walkCond(c, fn) { if (!c || typeof c !== 'object') return; if ('flag' in c) fn('flag', c.flag); if ('var' in c) { fn('var', c.var); if (c.var2) fn('var', c.var2); } if ('has_value' in c) fn('var', c.has_value); if ('seen' in c) fn('seen', c.seen); if (c.not) walkCond(c.not, fn); for (const k of ['all', 'any']) if (Array.isArray(c[k])) c[k].forEach(x => walkCond(x, fn)); }
  /** ctx：{flags:{名:…}, vars:{名:…}, speakers:{id:名}, emotes:[…], maxChars, allSets?:{id:set}, nodeIds?:Set, matches?:{id:…}} → {errors:[], warnings:[]} */
  function lint(set, ctx) {
    ctx = ctx || {}; const E = [], W = [], e = (c, m) => E.push({ code: c, msg: m, set: set.id }), w = (c, m) => W.push({ code: c, msg: m, set: set.id });
    const maxC = ctx.maxChars || 38, nodes = set.nodes || {}, ids = Object.keys(nodes);
    if (set.schema !== 'dialogue/v1') e('E_SCHEMA', 'schema 必為 dialogue/v1');
    if (!set.id) e('E_ID', '缺 id'); if (!Array.isArray(set.entry) || !set.entry.length) e('E_ENTRY', 'entry 必填');
    else { if (set.entry[set.entry.length - 1].cond) e('E_ENTRY_LAST', 'entry 最後一條必須無 cond（保底）'); for (const en of set.entry) if (!nodes[en.goto]) e('E_GOTO', 'entry goto 不存在：' + en.goto); }
    const edges = {}, sinks = new Set(); let usedDos = [];
    const checkCond = (c, where) => walkCond(c, (k, n) => { if (k === 'flag' && ctx.flags && !ctx.flags[n]) w('W_FLAG_UNREG', where + ' 用咗未登記旗標 ' + n); if (k === 'var' && ctx.vars && !ctx.vars[n]) w('W_VAR_UNREG', where + ' 用咗未登記變數 ' + n); if (k === 'seen' && !nodes[n] && !(ctx.nodeIds && ctx.nodeIds.has(n))) w('W_SEEN_UNKNOWN', where + ' seen 節點不存在：' + n); });
    const checkActs = (list, where) => { for (const a of list || []) { if (!a || !a.do) { e('E_DO', where + ' 動作缺 do'); continue; } if (LogicM.ALL_DOS.indexOf(a.do) < 0) e('E_DO_UNKNOWN', where + ' 未知 do：' + a.do); else if (LogicM.EXT_DOS.indexOf(a.do) >= 0) w('W_DO_EXT', where + ' do=' + a.do + ' 係遊程擴充（遊策 §4 未列）'); usedDos.push(a.do);
        if ((a.do === 'set_flag' || a.do === 'clear_flag') && ctx.flags && !ctx.flags[a.flag]) w('W_FLAG_UNREG', where + ' 用咗未登記旗標 ' + a.flag);
        if ((a.do === 'set_var' || a.do === 'add_var') && ctx.vars && !ctx.vars[a.var]) w('W_VAR_UNREG', where + ' 用咗未登記變數 ' + a.var);
        if (a.do === 'register_match' && ctx.matches && !ctx.matches[a.match]) e('E_MATCH', where + ' register_match 場次不存在：' + a.match);
        if (a.do === 'dialog' && ctx.allSets && !ctx.allSets[a.id]) e('E_DIALOG', where + ' dialog 對話集不存在：' + a.id); } };
    for (const en of set.entry || []) checkCond(en.cond, 'entry');
    for (const id of ids) {
      const n = nodes[id], at = 'node ' + id; edges[id] = [];
      if (n.next != null) { if (!nodes[n.next]) e('E_GOTO', at + ' next 不存在：' + n.next); else edges[id].push(n.next); } else if (!n.choices && !n.branch) sinks.add(id);
      if (n.branch) { if (!n.branch.length) e('E_BRANCH', at + ' branch 為空'); else if (n.branch[n.branch.length - 1].cond) w('W_BRANCH_LAST', at + ' branch 最後一條應無 cond（保底）'); for (const b of n.branch) { checkCond(b.cond, at); if (!nodes[b.goto]) e('E_GOTO', at + ' branch goto 不存在：' + b.goto); else edges[id].push(b.goto); } }
      if (n.choices) {
        if (n.choices.length > 3) e('E_CHOICES', at + ' 選項 ' + n.choices.length + ' > 3'); if (n.next != null) w('W_NEXT_IGNORED', at + ' 有 choices 時 next 被忽略');
        for (const c of n.choices) { const ct = String(c.text).replace(/\{(player|leaf|fee|var:[a-z0-9_]+)\}/g, 'XX'); if (chars(ct) > 16) e('E_CHOICE_LEN', at + ' 選項「' + c.text + '」' + chars(ct) + ' 字（模板按 2 位數展開）> 16'); if (c.disabled_hint && chars(c.disabled_hint) > 14) w('W_HINT_LEN', at + ' disabled_hint > 14 字'); checkCond(c.cond, at); checkActs(c.on_choose, at + ' choice ' + c.id); if (c.next == null) sinks.add(id); else if (!nodes[c.next]) e('E_GOTO', at + ' choice next 不存在：' + c.next); else edges[id].push(c.next); }
      }
      if (n.text != null) { const t = String(n.text).replace(/\{(player|leaf|fee|var:[a-z0-9_]+)\}/g, 'XX'); if (chars(t.replace(/\\n|\n/g, '')) > maxC) e('E_TEXT_LEN', at + ' 對白 ' + chars(t.replace(/\n/g, '')) + ' 字 > ' + maxC + '：「' + String(n.text).slice(0, 14) + '…」'); }
      else if (n.speaker && n.speaker !== 'system' && !n.branch) w('W_NO_TEXT', at + ' 無 text');
      if (n.speaker && ctx.speakers && !ctx.speakers[n.speaker]) e('E_SPEAKER', at + ' speaker 不在表內：' + n.speaker);
      if (n.emote && ctx.emotes && ctx.emotes.indexOf(n.emote) < 0) e('E_EMOTE', at + ' emote 不在表內：' + n.emote);
      checkActs(n.on_enter, at); checkActs(n.on_exit, at);
    }
    // 可達性
    const reach = new Set(); const q = (set.entry || []).map(x => x.goto).filter(x => nodes[x]); while (q.length) { const x = q.pop(); if (reach.has(x)) continue; reach.add(x); (edges[x] || []).forEach(y => q.push(y)); }
    for (const id of ids) if (!reach.has(id)) w('W_UNREACHABLE', 'node ' + id + ' 無法由 entry 到達');
    // 必然無限迴圈：由某節點出發無任何路徑到結束
    const rev = {}; for (const id of ids) for (const y of edges[id]) (rev[y] = rev[y] || []).push(id);
    const can = new Set(sinks); const q2 = [...sinks]; while (q2.length) { const x = q2.pop(); for (const p of rev[x] || []) if (!can.has(p)) { can.add(p); q2.push(p); } }
    for (const id of ids) if (reach.has(id) && !can.has(id)) e('E_LOOP', 'node ' + id + ' 起必然無限迴圈（無路徑到結束）');
    return { errors: E, warnings: W };
  }
  const api = { create, lint, chars };
  g.WR = g.WR || {}; g.WR.Dialogue = api; if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
