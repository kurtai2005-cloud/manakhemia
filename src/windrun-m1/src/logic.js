/* logic.js — 冒險切片遊戲狀態（DOM-free）：旗標／變數／條件求值／動作執行／報名／賽後結算，直接讀寫 save v1（src/save.js）。
   對應：遊策 dialogue-format.md §3–§4、match-data-format.md §3.1／§4、tuning-params-v2.2.md。
   host 提供 hooks（teleport／bubble／open_ui…）處理非狀態類動作；hook 回傳 Promise＝阻塞型（對話暫停至完成）。 */
(function (g) {
  'use strict';
  const Save = (typeof require !== 'undefined' && typeof module !== 'undefined') ? require('./save.js') : g.WR.Save;
  const SESSION_VARS = { fee: 1 }, READONLY = { leaf: 0, party_size: 1, seals: 1, r1_min_team: 1, capture_cd: 1, objective: 0 };
  const STATE_DOS = ['set_flag', 'clear_flag', 'set_var', 'add_var', 'give_spirit', 'register_match', 'set_objective', 'show_hint', 'autosave'];
  const HOST_DOS = ['teleport', 'npc_move', 'npc_face', 'camera', 'play_sfx', 'play_bgm', 'stop_bgm', 'wait', 'open_ui', 'start_match', 'begin_capture'];
  const EXT_DOS = ['bubble', 'say', 'push', 'play_cue', 'open_gate', 'dialog'];   // 遊程擴充（地圖事件用）；dialogue-format §4 未列
  const ALL_DOS = STATE_DOS.concat(HOST_DOS, EXT_DOS);
  const OPS = { '==': (a, b) => a === b, '!=': (a, b) => a !== b, '<': (a, b) => a < b, '<=': (a, b) => a <= b, '>': (a, b) => a > b, '>=': (a, b) => a >= b };

  function create(o) {
    o = o || {}; const data = o.data || {}, tun = Object.assign({}, data.tuning, o.tuning), hooks = o.hooks || {}, warns = [];
    const G = { save: o.save || Save.create({ now: 0, deviceId: 'dev-local' }), data, tuning: tun, hooks, warns, session: {}, rt: { captureCdUntil: 0 }, log: [], now: o.now || (() => Date.now()), store: o.store || null, lastMatch: null };
    const warn = m => { if (warns.indexOf(m) < 0) warns.push(m); if (G.onWarn) G.onWarn(m); };
    const flagReg = (data.flags && data.flags.flags) || null, varReg = (data.flags && data.flags.vars) || null;
    const matchDef = id => (data.matches || {})[id];

    // ---------- 旗標／變數 ----------
    G.getFlag = n => { if (flagReg && !flagReg[n]) warn('未登記旗標：' + n); return G.save.flags[n] === true; };
    G.setFlag = (n, v) => { if (flagReg && !flagReg[n]) warn('未登記旗標：' + n); if (!Save.RE.flag.test(n)) { warn('旗標名不合法：' + n); return; } G.save.flags[n] = !!v; };
    G.getVar = n => {
      if (varReg && !varReg[n]) warn('未登記變數：' + n);
      switch (n) {
        case 'leaf': return G.save.player.leaf;
        case 'party_size': return G.save.party.length;
        case 'seals': return G.save.player.seals.length;
        case 'r1_min_team': return tun.r1_min_team | 0;
        case 'capture_cd': return Math.max(0, Math.ceil((G.rt.captureCdUntil - G.now()) / 1000));
        case 'objective': return G.save.chapter.step;
        case 'fee': return n in G.session ? G.session[n] : ((matchDef('c1_r1') || {}).fee | 0);
        case 'registered_match': return typeof G.save.vars.registered_match === 'string' ? G.save.vars.registered_match : '';
        default: { const v = G.save.vars[n]; return v === undefined ? (varReg && varReg[n] && varReg[n].type === 'string' ? '' : 0) : v; }
      }
    };
    G.setVar = (n, v) => {
      if (varReg && !varReg[n]) warn('未登記變數：' + n);
      if (n === 'leaf') { G.save.player.leaf = Math.max(0, Math.min(Save.LIM.leaf, Math.trunc(Number(v) || 0))); return; }
      if (READONLY[n] === 1) { warn('唯讀變數被寫入（已忽略）：' + n); return; }
      if (SESSION_VARS[n]) { G.session[n] = v; return; }
      if (!Save.RE.flag.test(n)) { warn('變數名不合法：' + n); return; }
      G.save.vars[n] = typeof v === 'number' ? Math.trunc(v) : String(v).slice(0, Save.LIM.str);
    };
    G.addVar = (n, d) => { if (n === 'party_size') return; /* 遊策定案：party_size 由引擎按隊伍人數自動維護（派生值）；舊資料嘅 add_var party_size 靜默忽略，唔警告 */ const cur = G.getVar(n); if (typeof cur !== 'number') { warn('add_var 對非數值變數：' + n); return; } G.setVar(n, cur + (Number(d) | 0)); };

    // ---------- 條件 ----------
    G.cond = c => {
      if (c === undefined || c === null) return true;
      if (typeof c !== 'object') { warn('條件非物件'); return false; }
      if ('flag' in c) return G.getFlag(c.flag);
      if ('not' in c) return !G.cond(c.not);
      if ('all' in c) return c.all.every(x => G.cond(x));
      if ('any' in c) return c.any.some(x => G.cond(x));
      if ('var' in c) { const a = G.getVar(c.var), b = 'var2' in c ? G.getVar(c.var2) : c.value, f = OPS[c.op]; if (!f) { warn('未知 op：' + c.op); return false; } return f(a, b); }
      if ('has_value' in c) { const v = G.getVar(c.has_value); return v !== '' && v !== 0 && v !== null && v !== undefined; }
      if ('seen' in c) return G.save.dialogue.seen.indexOf(c.seen) >= 0;
      if ('done' in c) return G.save.events.done.indexOf(c.done) >= 0;
      warn('未知條件：' + JSON.stringify(c)); return false;
    };
    /** 文字模板：{player}{leaf}{fee}{var:名}；未知欄位原樣保留。 */
    G.text = t => String(t == null ? '' : t).replace(/\{(player|leaf|fee|var:[a-z0-9_]+)\}/g, (m, k) => k === 'player' ? G.save.player.name : k === 'leaf' ? String(G.getVar('leaf')) : k === 'fee' ? String(G.getVar('fee')) : String(G.getVar(k.slice(4))));
    G.markSeen = id => { if (G.save.dialogue.seen.indexOf(id) < 0 && G.save.dialogue.seen.length < Save.LIM.seen) { G.save.dialogue.seen.push(id); G.save.dialogue.seen.sort(); } };
    G.markDone = k => { if (G.save.events.done.indexOf(k) < 0 && G.save.events.done.length < Save.LIM.done) { G.save.events.done.push(k); G.save.events.done.sort(); } };
    G.isDone = k => G.save.events.done.indexOf(k) >= 0;
    G.clearDone = prefix => { G.save.events.done = G.save.events.done.filter(k => k.indexOf(prefix) !== 0); };

    // ---------- 野靈／報名 ----------
    G.giveSpirit = (species, lv) => {
      const s = G.save, c = Save.newCreature(species, 'c' + s.seq, { lv: lv | 0 || 1 }); s.seq++;
      if (s.party.length < 6) s.party.push(c); else s.habitat.push(c);
      if (s.dex.owned.indexOf(species) < 0) s.dex.owned.push(species); if (s.dex.seen.indexOf(species) < 0) s.dex.seen.push(species); s.dex.owned.sort(); s.dex.seen.sort(); return c;
    };
    G.canRegister = id => {
      const m = matchDef(id); if (!m) return { ok: false, reason: 'no_match' }; const r = m.req || {}, s = G.save;
      if (m.m_milestone === 'M2' && !tun.allow_m2) return { ok: false, reason: 'locked' };
      if (r.not_done && s.cleared.indexOf(id) >= 0) return { ok: false, reason: 'done' };
      if ((r.done || []).some(x => s.cleared.indexOf(x) < 0)) return { ok: false, reason: 'need_done' };
      if ((r.flags || []).some(f => !G.getFlag(f))) return { ok: false, reason: 'need_flag' };
      if ((r.not_flags || []).some(f => G.getFlag(f))) return { ok: false, reason: 'blocked_flag' };
      if (r.seals_min && s.player.seals.length < r.seals_min) return { ok: false, reason: 'seals' };
      const pm = id === 'c1_r1' ? Math.min(r.party_min | 0, tun.r1_min_team | 0 || 99) : (r.party_min | 0);   // r1_min_team 覆寫初戰（1–2）
      if (s.party.length < pm) return { ok: false, reason: 'party', need: pm };
      if (s.player.leaf < (m.fee | 0)) return { ok: false, reason: 'leaf', need: m.fee };
      return { ok: true };
    };
    const FAIL_GOTO = { party: 'sang_need_two', leaf: 'sang_no_leaf', done: 'sang_won' };
    G.registerMatch = id => {
      const c = G.canRegister(id); if (!c.ok) return c; const m = matchDef(id);
      G.save.player.leaf -= m.fee | 0; G.save.vars.registered_match = id; G.setFlag('formation_done', false); G.clearDone('match:');
      G.rt.lastRegistered = id; return { ok: true, fee: m.fee | 0 };
    };

    // ---------- 動作 ----------
    /** 執行單個動作；回傳 {goto?, blocked?:Promise, fail?}。state 類同步完成；host 類交 hooks。 */
    G.run = (a, ctx) => {
      if (!a || typeof a !== 'object') { warn('動作非物件'); return {}; }
      G.log.push(a.do + (a.flag || a.var || a.match || a.id || a.scene || ''));
      switch (a.do) {
        case 'set_flag': G.setFlag(a.flag, true); return {};
        case 'clear_flag': G.setFlag(a.flag, false); return {};
        case 'set_var': G.setVar(a.var, a.value); return {};
        case 'add_var': G.addVar(a.var, a.delta); return {};
        case 'give_spirit': { const c = G.giveSpirit(a.species, a.lv); const h = hooks.give_spirit && hooks.give_spirit(c, a); return h && h.then ? { blocked: h } : {}; }
        case 'register_match': { const r = G.registerMatch(a.match); if (r.ok) return {}; const fg = Object.assign({}, FAIL_GOTO, a.fail_goto)[r.reason]; if (hooks.register_failed) hooks.register_failed(r); return fg ? { goto: fg, fail: r.reason } : { fail: r.reason }; }
        case 'set_objective': G.save.chapter.step = Save.RE.map.test(a.id) ? a.id : G.save.chapter.step; if (data.flags && data.flags.objectives && !data.flags.objectives[a.id]) warn('未登記任務：' + a.id); { const h = hooks.set_objective && hooks.set_objective(a.id); void h; } return {};
        case 'show_hint': { const k = 'hint_' + a.id; if (!G.isDone(k)) { G.markDone(k); const h = hooks.show_hint && hooks.show_hint(a.id); return h && h.then ? { blocked: h } : {}; } return {}; }
        case 'autosave': if (hooks.autosave) hooks.autosave(); else G.autosave(); return {};
        default:
          if (ALL_DOS.indexOf(a.do) < 0) { warn('未知動作：' + a.do); return {}; }
          if (hooks[a.do]) { const h = hooks[a.do](a, ctx); if (h && typeof h.then === 'function') return { blocked: h }; if (h && typeof h === 'object' && h.goto) return { goto: h.goto }; }
          else warn('host 未實作動作：' + a.do);
          return {};
      }
    };
    /** 依序執行動作陣列；遇阻塞型收集 Promise，後續動作排在阻塞完成後（async）。回傳 {goto?, blocked?}。 */
    G.runAll = (list, ctx) => {
      list = list || []; let i = 0; const out = {};
      const step = () => { while (i < list.length) { const r = G.run(list[i++], ctx); if (r.goto) out.goto = r.goto; if (r.blocked) return Promise.resolve(r.blocked).then(step); } return null; };
      const p = step(); if (p) out.blocked = p; return out;
    };
    G.autosave = () => { if (!G.store) return { ok: false, reason: 'no_store' }; G.save.player.pos = G.save.player.pos; const r = G.store.save(G.save, G.now()); if (r.ok) { G.save.rev = r.rev; } return r; };

    // ---------- 賽後（match-data-format §3.1）----------
    G.expNeed = lv => (tun.exp_base | 0) + (tun.exp_per_level | 0) * lv;
    G.addExp = (c, exp) => { c.exp += exp; let up = 0; while (c.lv < (tun.level_cap | 0 || 20) && c.exp >= G.expNeed(c.lv)) { c.exp -= G.expNeed(c.lv); c.lv++; up++; } return up; };
    /** result：{win:bool, margin_m?, ran?:[iid…]}（ran＝出過場；缺省＝隊伍全部，結緣戰＝首隻）。回傳結算摘要。 */
    G.finishMatch = (id, result) => {
      const m = matchDef(id); if (!m) return { ok: false, reason: 'no_match' }; const s = G.save, win = !!result.win, first = win && s.cleared.indexOf(id) < 0, rw = m.reward || {};
      if (m.kind === 'cup') delete G.save.vars.registered_match;   // 先清 registered_match，再執行 on_end（§3.1-4）
      const ranIds = result.ran || (m.kind === 'capture' ? s.party.slice(0, 1).map(c => c.iid) : s.party.map(c => c.iid));
      const leaf = (win ? rw.leaf_win : rw.leaf_lose) | 0, bonus = first ? (rw.first_win_leaf_bonus | 0) : 0;
      s.player.leaf = Math.min(Save.LIM.leaf, s.player.leaf + leaf + bonus);
      const exp = (win ? rw.exp_win : rw.exp_lose) | 0, ups = [];
      for (const c of s.party) if (ranIds.indexOf(c.iid) >= 0) { const up = G.addExp(c, exp); ups.push({ iid: c.iid, species: c.species, exp, up, lv: c.lv }); }
      s.stats.races++; if (win) s.stats.wins++; if (win && m.kind === 'cup' && s.cleared.indexOf(id) < 0) { s.cleared.push(id); s.cleared.sort(); }
      G.runAll((m.on_end || {})[win ? 'win' : 'lose']);
      if (m.kind === 'capture' && !win) G.rt.captureCdUntil = G.now() + (tun.capture_retry_cd_s | 0) * 1000;
      G.clearDone('match:'); G.lastMatch = { id, win, first, leaf: leaf + bonus, ups, margin_m: result.margin_m };
      return Object.assign({ ok: true }, G.lastMatch, { dialogue: m.dialogue && (win ? m.dialogue.post_win : m.dialogue.post_lose) });
    };
    return G;
  }
  /** 新遊戲存檔（tuning.start_leaf）。 */
  function newGame(data, o) { o = o || {}; const s = Save.create({ now: o.now || 0, deviceId: o.deviceId || 'dev-' + Math.random().toString(36).slice(2, 10), name: o.name || '旅人' }); s.player.leaf = ((data.tuning || {}).start_leaf | 0); s.player.pos = { map: 'town_morningmoss', x: 20.5, y: 26.5, dir: 'u' }; s.chapter = { id: 'ch1', step: 'start' }; return s; }
  const api = { create, newGame, ALL_DOS, STATE_DOS, HOST_DOS, EXT_DOS, OPS };
  g.WR = g.WR || {}; g.WR.Logic = api; if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
