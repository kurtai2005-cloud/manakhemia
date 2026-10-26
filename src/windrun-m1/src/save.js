/* save.js — 存檔 JSON v1（plan 6H／A.1）。DOM-free：Node／瀏覽器／日後伺服器共用。
   職責：預設存檔、清洗正規化（normalize：永不拋錯、補預設、截斷越界）、遷移鏈（v0＝MVP 舊存檔 → v1）、
   規範化序列化（鍵排序）、存檔碼匯出入（WRS1.<base64url>.<FNV 校驗>）、儲存轉接器（主檔＋備份）、雲端衝突判斷輔助。
   欄位表／遷移策略見 docs/save-format.md。 */
(function (g) {
  'use strict';
  const VERSION = 1, FORMAT = 'windrun-save', LIM = { party: 6, habitat: 60, presets: 3, presetLen: 3, name: 12, nick: 12, flags: 400, vars: 64, seen: 400, done: 200, cleared: 200, dex: 200, skills: 4, str: 32, leaf: 99999999, lv: 99, bonus: 999 };
  const RE = { species: /^[a-z][a-z0-9_]{0,31}$/, iid: /^c[0-9]{1,8}$/, flag: /^[a-z][a-z0-9_]*(\.[a-z0-9_]+){0,4}$/, node: /^[a-z][a-z0-9_]{0,47}$/, evKey: /^[a-z][a-z0-9_:.]{0,47}$/, matchId: /^[a-z][a-z0-9_]*(\.[a-z0-9_]+){0,4}$/, map: /^[a-z][a-z0-9_]{0,31}$/, skill: /^[a-z][a-z0-9_]{0,23}$/ };
  const SEALS = ['seal_1', 'seal_2', 'seal_3'], DIRS = 'dlru', TOUCH = ['tap', 'joystick'], FXQ = ['auto', 'off', 'low', 'mid', 'high'], LANGS = ['zh-HK', 'en', 'ja'];

  const isObj = v => v && typeof v === 'object' && !Array.isArray(v);
  const own = (o, k) => isObj(o) && Object.prototype.hasOwnProperty.call(o, k) && k !== '__proto__' ? o[k] : undefined;
  const int = (v, lo, hi, d) => { const n = typeof v === 'number' ? v : (typeof v === 'string' && v.trim() !== '' ? Number(v) : NaN); return Number.isFinite(n) ? Math.max(lo, Math.min(hi, Math.trunc(n))) : d; };
  const num = (v, lo, hi, d) => { const n = typeof v === 'number' ? v : NaN; return Number.isFinite(n) ? Math.max(lo, Math.min(hi, n)) : d; };
  const str = (v, max, d) => typeof v === 'string' ? Array.from(v.replace(/[\u0000-\u001f\u007f]/g, '')).slice(0, max).join('') : d;
  const id = (v, re, d) => typeof v === 'string' && re.test(v) ? v : d;
  const oneOf = (v, arr, d) => arr.indexOf(v) >= 0 ? v : d;
  const uniq = a => { const s = new Set(), o = []; for (const x of a) if (!s.has(x)) { s.add(x); o.push(x); } return o; };

  function newCreature(species, iid, o) { o = o || {}; return { iid, species, nick: o.nick || '', lv: o.lv || 1, exp: o.exp || 0, bonus: Object.assign({ speed: 0, power: 0, calm: 0, stamina: 0 }, o.bonus), cond: o.cond == null ? 100 : o.cond, skills: o.skills || [], evo: { done: [], flags: [] }, caught: { map: 'town_morningmoss', t: 0 } }; }
  function create(o) {
    o = o || {};
    return { format: FORMAT, version: VERSION, rev: 0, deviceId: o.deviceId || 'dev-' + Math.random().toString(36).slice(2, 10), createdAt: o.now || 0, savedAt: o.now || 0,
      player: { name: o.name || '旅人', leaf: 0, seals: [], pos: { map: 'town_morningmoss', x: 20, y: 22, dir: 'u' }, appearance: 'default' },
      party: [], habitat: [], presets: [[], [], []], seq: 1,
      dex: { seen: [], owned: [] }, cleared: [], flags: {}, vars: {}, dialogue: { seen: [] }, events: { done: [] }, chapter: { id: 'ch1', step: 'start' },
      stats: { races: 0, wins: 0, playSec: 0, ribbons: 0, turn: 1, actionsLeft: 3 },
      settings: { sound: true, lang: 'zh-HK', touchMode: 'tap', fxQuality: 'auto', textSpeed: 2 } };
  }
  function normCreature(c) {
    if (!isObj(c)) return null; const species = id(own(c, 'species'), RE.species, null), iid = id(own(c, 'iid'), RE.iid, null); if (!species || !iid) return null;
    const b = own(c, 'bonus'), e = own(c, 'evo'), cg = own(c, 'caught');
    return { iid, species, nick: str(own(c, 'nick'), LIM.nick, ''), lv: int(own(c, 'lv'), 1, LIM.lv, 1), exp: int(own(c, 'exp'), 0, 1e7, 0),
      bonus: { speed: int(own(b, 'speed'), 0, LIM.bonus, 0), power: int(own(b, 'power'), 0, LIM.bonus, 0), calm: int(own(b, 'calm'), 0, LIM.bonus, 0), stamina: int(own(b, 'stamina'), 0, LIM.bonus, 0) },
      cond: int(own(c, 'cond'), 0, 100, 100), skills: uniq((Array.isArray(own(c, 'skills')) ? c.skills : []).filter(s => typeof s === 'string' && RE.skill.test(s))).slice(0, LIM.skills),
      evo: { done: uniq((Array.isArray(own(e, 'done')) ? e.done : []).filter(s => typeof s === 'string' && RE.species.test(s))).slice(0, 8), flags: uniq((Array.isArray(own(e, 'flags')) ? e.flags : []).filter(s => typeof s === 'string' && RE.flag.test(s))).slice(0, 8) },
      caught: { map: id(own(cg, 'map'), RE.map, 'town_morningmoss'), t: int(own(cg, 't'), 0, 4e12, 0) } };
  }
  function normFlags(f) {
    const out = {}; if (!isObj(f)) return out; let n = 0;
    for (const k of Object.keys(f).sort()) { if (n >= LIM.flags) break; if (!RE.flag.test(k)) continue; const v = f[k]; if (typeof v === 'boolean') out[k] = v; else if (typeof v === 'number' && Number.isFinite(v)) out[k] = Math.trunc(v); else if (typeof v === 'string') out[k] = str(v, LIM.str, ''); else continue; n++; }
    return out;
  }
  /** vars（對話／事件變數，dialogue-format §3）：int（±1e9）或 string（≤32）；名＝flag 命名規則。leaf／party_size／seals 唔入呢度（派生自 player／party）。 */
  function normVars(f) {
    const out = {}; if (!isObj(f)) return out; let n = 0;
    for (const k of Object.keys(f).sort()) { if (n >= LIM.vars) break; if (!RE.flag.test(k)) continue; const v = f[k]; if (typeof v === 'number' && Number.isFinite(v)) out[k] = Math.max(-1e9, Math.min(1e9, Math.trunc(v))); else if (typeof v === 'string') out[k] = str(v, LIM.str, ''); else continue; n++; }
    return out;
  }
  function idList(a, re, max) { return uniq((Array.isArray(a) ? a : []).filter(s => typeof s === 'string' && re.test(s))).sort().slice(0, max); }
  /** 清洗到 v1 形狀。唔拋錯。回傳新物件（唔改輸入）。 */
  function sanitize(raw, now) {
    const d = create({ now: 0, deviceId: 'dev-unknown' }), r = isObj(raw) ? raw : {}, p = own(r, 'player'), pos = own(p, 'pos'), st = own(r, 'stats'), se = own(r, 'settings'), ch = own(r, 'chapter');
    const s = d;
    s.rev = int(own(r, 'rev'), 0, 1e9, 0); s.deviceId = id(own(r, 'deviceId'), /^[A-Za-z0-9_-]{3,40}$/, 'dev-unknown'); s.createdAt = int(own(r, 'createdAt'), 0, 4e12, 0); s.savedAt = int(own(r, 'savedAt'), 0, 4e12, 0);
    s.player = { name: str(own(p, 'name'), LIM.name, '旅人') || '旅人', leaf: int(own(p, 'leaf'), 0, LIM.leaf, 0), seals: idList(own(p, 'seals'), /^seal_[1-9]$/, 9).filter(x => SEALS.indexOf(x) >= 0),
      pos: { map: id(own(pos, 'map'), RE.map, 'town_morningmoss'), x: num(own(pos, 'x'), 0, 4096, 20), y: num(own(pos, 'y'), 0, 4096, 22), dir: oneOf(own(pos, 'dir'), DIRS.split(''), 'u') }, appearance: id(own(p, 'appearance'), RE.skill, 'default') };
    const seen = new Set(), list = a => (Array.isArray(a) ? a : []).map(normCreature).filter(c => c && !seen.has(c.iid) && seen.add(c.iid));
    s.party = list(own(r, 'party')).slice(0, LIM.party); const hab = list(own(r, 'habitat')); s.habitat = hab.slice(0, LIM.habitat);
    const have = new Set(s.party.concat(s.habitat).map(c => c.iid)), pr = own(r, 'presets');
    s.presets = [0, 1, 2].map(i => uniq((Array.isArray(pr) && Array.isArray(pr[i]) ? pr[i] : []).filter(x => typeof x === 'string' && have.has(x))).slice(0, LIM.presetLen));
    let mx = 0; for (const c of s.party.concat(s.habitat)) mx = Math.max(mx, Number(c.iid.slice(1))); s.seq = Math.max(int(own(r, 'seq'), 1, 1e9, 1), mx + 1);
    const dx = own(r, 'dex'); s.dex = { seen: idList(own(dx, 'seen'), RE.species, LIM.dex), owned: idList(own(dx, 'owned'), RE.species, LIM.dex) };
    for (const c of s.party.concat(s.habitat)) { if (s.dex.owned.indexOf(c.species) < 0) s.dex.owned.push(c.species); if (s.dex.seen.indexOf(c.species) < 0) s.dex.seen.push(c.species); } s.dex.owned.sort(); s.dex.seen.sort();
    s.cleared = idList(own(r, 'cleared'), RE.matchId, LIM.cleared); s.flags = normFlags(own(r, 'flags'));
    s.vars = normVars(own(r, 'vars')); s.dialogue = { seen: idList(own(own(r, 'dialogue'), 'seen'), RE.node, LIM.seen) }; s.events = { done: idList(own(own(r, 'events'), 'done'), RE.evKey, LIM.done) };
    s.chapter = { id: id(own(ch, 'id'), RE.map, 'ch1'), step: id(own(ch, 'step'), RE.map, 'start') };
    s.stats = { races: int(own(st, 'races'), 0, 1e7, 0), wins: int(own(st, 'wins'), 0, 1e7, 0), playSec: int(own(st, 'playSec'), 0, 1e9, 0), ribbons: int(own(st, 'ribbons'), 0, 1e7, 0), turn: int(own(st, 'turn'), 1, 1e6, 1), actionsLeft: int(own(st, 'actionsLeft'), 0, 99, 3) };
    s.settings = { sound: own(se, 'sound') !== false, lang: oneOf(own(se, 'lang'), LANGS, 'zh-HK'), touchMode: oneOf(own(se, 'touchMode'), TOUCH, 'tap'), fxQuality: oneOf(own(se, 'fxQuality'), FXQ, 'auto'), textSpeed: int(own(se, 'textSpeed'), 1, 3, 2) };
    return s;
  }
  // ---------- 遷移鏈：每步 vN → vN+1，純函數 ----------
  const MIGRATIONS = {
    0: function v0to1(o) {   // MVP 舊存檔：{v:1, creatures:{id:{lv,exp,bonus,cond}}, ribbons, turn, actionsLeft, cleared:{1:true}, races, sound}
      const n = create({ now: 0, deviceId: 'dev-migrated' }); let seq = 1; const all = [];
      if (isObj(o.creatures)) for (const sp of Object.keys(o.creatures).sort()) { const c = o.creatures[sp]; if (!RE.species.test(sp) || !isObj(c)) continue; all.push(Object.assign(newCreature(sp, 'c' + (seq++), c), { lv: int(c.lv, 1, LIM.lv, 1), exp: int(c.exp, 0, 1e7, 0), bonus: isObj(c.bonus) ? c.bonus : {}, cond: int(c.cond, 0, 100, 100) })); }
      n.party = all.slice(0, LIM.party); n.habitat = all.slice(LIM.party); n.seq = seq;
      n.stats.ribbons = int(o.ribbons, 0, 1e7, 0); n.stats.turn = int(o.turn, 1, 1e6, 1); n.stats.actionsLeft = int(o.actionsLeft, 0, 99, 3); n.stats.races = int(o.races, 0, 1e7, 0);
      n.cleared = isObj(o.cleared) ? Object.keys(o.cleared).filter(k => o.cleared[k] && /^[0-9]+$/.test(k)).map(k => 'legacy.stage' + k).sort() : []; n.settings.sound = o.sound !== false; n.flags = { 'meta.migrated_from_v0': true };
      return n;
    }
  };
  function detect(o) { if (!isObj(o)) return -1; if (typeof o.version === 'number') return Math.trunc(o.version); if (o.v === 1 && isObj(o.creatures)) return 0; return -1; }
  /** 讀任何輸入（物件）→ {ok, save, from, warnings} ；version 比現行新 → ok:false,reason:'too_new'（唔准覆寫） */
  function normalize(raw, now) {
    const w = []; let v = detect(raw);
    if (v < 0) { w.push('unrecognized'); return { ok: true, save: Object.assign(sanitize({}), {}), from: -1, warnings: w, fresh: true }; }
    if (v > VERSION) return { ok: false, reason: 'too_new', from: v, warnings: ['too_new'] };
    let o = raw; for (let i = v; i < VERSION; i++) { o = MIGRATIONS[i](o); w.push('migrated v' + i + '→v' + (i + 1)); }
    const s = sanitize(o); if (now != null) s.savedAt = int(now, 0, 4e12, 0);
    return { ok: true, save: s, from: v, warnings: w };
  }
  // ---------- 序列化（鍵排序＝同一內容同一字串，方便比對／校驗／diff）----------
  function canon(v) { if (Array.isArray(v)) return '[' + v.map(canon).join(',') + ']'; if (isObj(v)) return '{' + Object.keys(v).sort().map(k => JSON.stringify(k) + ':' + canon(v[k])).join(',') + '}'; return JSON.stringify(v); }
  function serialize(s) { return canon(s); }
  function parse(text) { let o; try { o = JSON.parse(text); } catch (e) { return { ok: false, reason: 'bad_json', warnings: ['bad_json'] }; } return normalize(o); }
  function fnv(str) { let h = 0x811c9dc5; const b = utf8(str); for (let i = 0; i < b.length; i++) { h ^= b[i]; h = Math.imul(h, 0x01000193) >>> 0; } return ('00000000' + (h >>> 0).toString(16)).slice(-8); }
  function utf8(s) { if (typeof TextEncoder !== 'undefined') return new TextEncoder().encode(s); return Uint8Array.from(Buffer.from(s, 'utf8')); }
  function b64u(bytes) { let s; if (typeof Buffer !== 'undefined') s = Buffer.from(bytes).toString('base64'); else { let t = ''; for (let i = 0; i < bytes.length; i++) t += String.fromCharCode(bytes[i]); s = btoa(t); } return s.replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, ''); }
  function unb64u(t) { t = t.replace(/-/g, '+').replace(/_/g, '/'); while (t.length % 4) t += '='; if (typeof Buffer !== 'undefined') return Uint8Array.from(Buffer.from(t, 'base64')); const bin = atob(t), a = new Uint8Array(bin.length); for (let i = 0; i < bin.length; i++) a[i] = bin.charCodeAt(i); return a; }
  function utf8dec(b) { if (typeof TextDecoder !== 'undefined') return new TextDecoder('utf-8', { fatal: true }).decode(b); return Buffer.from(b).toString('utf8'); }
  // 存檔碼：WRS1.<base64url(JSON)>.<fnv8>；校驗只防手誤／複製殘缺，唔係防作弊（防作弊靠伺服器重算，見 plan 6）
  function toCode(s) { const j = serialize(s); return 'WRS1.' + b64u(utf8(j)) + '.' + fnv(j); }
  function fromCode(code) {
    const m = /^WRS1\.([A-Za-z0-9_-]+)\.([0-9a-f]{8})$/.exec(String(code || '').trim().replace(/\s+/g, '')); if (!m) return { ok: false, reason: 'bad_code' };
    let j; try { j = utf8dec(unb64u(m[1])); } catch (e) { return { ok: false, reason: 'bad_code' }; } if (fnv(j) !== m[2]) return { ok: false, reason: 'checksum' }; return parse(j);
  }
  // ---------- 儲存轉接器：adapter＝{getItem,setItem,removeItem}（localStorage 或假物件）----------
  function Store(adapter, key) {
    key = key || 'windrun_save'; const bak = key + '.bak', legacy = 'windrun_save_v1';
    return {
      key, bak,
      /** 讀：主檔 → 備份 → MVP 舊鍵 → 新存檔。回傳 {save, source, warnings, tooNew?} */
      load(now) {
        for (const [k, src] of [[key, 'main'], [bak, 'backup'], [legacy, 'legacy']]) { let t; try { t = adapter.getItem(k); } catch (e) { continue; } if (!t) continue; const r = parse(t); if (r.ok) return { save: r.save, source: src, warnings: r.warnings, from: r.from }; if (r.reason === 'too_new') return { tooNew: true, source: src, save: null, warnings: r.warnings }; }
        const f = create({ now }); return { save: f, source: 'new', warnings: [] };
      },
      /** 存：先將舊主檔複製去備份（只備份有效 JSON），再寫新主檔；quota 滿唔拋錯，回 {ok:false} */
      save(s, now) {
        const t = Object.assign({}, s, { rev: (s.rev | 0) + 1, savedAt: now != null ? now : s.savedAt }); const n = normalize(t); if (!n.ok) return { ok: false, reason: n.reason };
        try { const old = adapter.getItem(key); if (old && parse(old).ok) adapter.setItem(bak, old); adapter.setItem(key, serialize(n.save)); } catch (e) { return { ok: false, reason: 'storage' }; }
        return { ok: true, rev: n.save.rev, save: n.save };
      },
      clear() { try { adapter.removeItem(key); adapter.removeItem(bak); } catch (e) { /* ignore */ } }
    };
  }
  // ---------- 雲端衝突（接 plan 4.5）：只提供判斷輔助，唔自動覆寫 ----------
  function progressScore(s) { return s.cleared.length * 1000 + s.player.seals.length * 5000 + s.dex.owned.length * 50 + s.party.concat(s.habitat).reduce((a, c) => a + c.lv, 0) * 3 + s.stats.races + Object.keys(s.flags).length * 5; }
  function conflict(local, remote) {
    // 規則：同 deviceId 且 rev 更大＝直接取較新；不同裝置時：一邊進度分數 ≥ 另一邊且 cleared/seals/dex 為超集＝取之；否則 'ask'（兩份都保留，由玩家揀）。
    if (local.deviceId === remote.deviceId) return { winner: local.rev >= remote.rev ? 'local' : 'remote', reason: 'same_device_rev' };
    const sup = (a, b) => b.cleared.every(x => a.cleared.indexOf(x) >= 0) && b.player.seals.every(x => a.player.seals.indexOf(x) >= 0) && b.dex.owned.every(x => a.dex.owned.indexOf(x) >= 0);
    if (sup(local, remote) && !sup(remote, local)) return { winner: 'local', reason: 'superset' }; if (sup(remote, local) && !sup(local, remote)) return { winner: 'remote', reason: 'superset' };
    if (sup(local, remote) && sup(remote, local)) return { winner: progressScore(local) >= progressScore(remote) ? 'local' : 'remote', reason: 'equal_sets_score' };
    return { winner: 'ask', reason: 'diverged', scores: [progressScore(local), progressScore(remote)] };
  }
  const api = { VERSION, FORMAT, LIM, RE, create, newCreature, normalize, sanitize, parse, serialize, toCode, fromCode, fnv, Store, progressScore, conflict, detect, MIGRATIONS };
  g.WR = g.WR || {}; g.WR.Save = api; if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
