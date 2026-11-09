/* 《微光小圃》 long5c.js — 第 5 批 5c 承傳（docs-gdd/series2-4a4b-spec.md v1.1 §5c＋「5a–5c 玩法位定案」；遊美 art/series2_long/5c/long_5c.json）。原創代碼。
   DOM-free、Node 可 require（純邏輯）：存檔 s.fam.c5（sanitize；唔郁 §7 判定、唔加團絨路線分、唔出碎）。
   ・新蛋（細佬蛋／團絨蛋）一到 → 排「揀上一代」：屋內成年（團絨靜光／細佬 S5–S6；主養、遠足中都得）；冇成年＝跳過（冇遺傳）。
     未揀就孵 → 自動揀第一隻（主養優先）。孵之前可以改。
   ・遺傳：花紋 ×1（上一代系／路線 → 8 款）＋家傳招式 ×1：
       團絨上一代＝佢示範最多嗰課（runtime 記錄：每堂教錯課記落 c5.demo[大佬]）；打和揀最近；從未示範過 → 8 課隨機（種子）。
       細佬上一代＝佢教錯課學過嘅：有學過自己系嗰課 → 用自己系（遊美 json）；否則學得最多嗰課（打和揀最近）；乜都冇學過 → 自己系。
   ・家族 Lv3（inherit_fast）起：細佬蛋孵出嘅頭 2 階（S1、S2）快 20%（pet2.fast＝0.8，孵化嗰刻鎖定）；團絨蛋唔計（保 §7）。
   ・屋仔／家具／圖鑑／家族等級／工作全部照留（5c 只加 c5，唔郁其他）。 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory(require('./series2.js'), require('./long5a.js'));
  else { root.Glimmer = root.Glimmer || {}; root.Glimmer.long5c = factory(root.Glimmer.series2, root.Glimmer.long5a); }
})(typeof self !== 'undefined' ? self : this, function (SR, FAM) {
  'use strict';
  const obj = (o) => o && typeof o === 'object' && !Array.isArray(o);
  const clamp = (v, a, b) => v < a ? a : v > b ? b : v;
  const hash = (str) => { let h = 2166136261 >>> 0; for (let i = 0; i < str.length; i++) { h ^= str.charCodeAt(i); h = Math.imul(h, 16777619) >>> 0; } return h >>> 0; };

  /* 同 long_5c.json 一致（long5c.test.js 對數） */
  const PATTERNS = [{ id: 'wave', zh: '波紋' }, { id: 'bubble', zh: '泡泡' }, { id: 'spark', zh: '火花' }, { id: 'spot', zh: '斑點' }, { id: 'flame', zh: '火焰' }, { id: 'star', zh: '星星' }, { id: 'diamond', zh: '菱格' }, { id: 'crescent', zh: '月牙' }];
  const PAT = Object.fromEntries(PATTERNS.map(p => [p.id, p]));
  const BY_SERIES = { A: 'wave', B: 'bubble', C: 'spark', D: 'spot', E: 'flame', F: 'star', G: 'diamond', H: 'crescent' };
  const BY_ROUTE = { tide: 'wave', soft: 'bubble', ember: 'spark', dust: 'spark', shroom: 'spot', radiant: 'star', lumi: 'star', crystal: 'diamond', moon: 'crescent' };
  const TRICK = { A: '淋花 → 淋自己個頭', B: '吹泡泡 → 自己入咗泡泡', C: '點火柴 → 用個頭擦', D: '孵蛋 → 坐喺石仔上面孵', E: '食辣椒 → 當士多啤梨', F: '望遠鏡 → 拎倒轉睇', G: '讀故仔 → 拎倒轉本書，讀到瞓著', H: '月亮燈 → 當帽戴' };
  const FAST = { fromLv: 3, stages: 2, speedup: 0.2, factor: 0.8, excludeEgg: 'tr' };
  const LINES = { fastOn: '頭 2 階成長快 20%', fastTr: '團絨蛋唔計', fastLocked: '家族 Lv3 解鎖', none: '屋企未有成年，今次冇遺傳', auto: '自動揀咗{name}做上一代' };
  const LMAX = SR.LINES;

  function st(s) {
    const F = FAM.st(s); let o = F.c5; if (!obj(o)) o = F.c5 = {};
    o.v = 1;
    if (!obj(o.demo)) o.demo = {};
    for (const t of Object.keys(o.demo)) { const d = o.demo[t]; if (!obj(d)) { delete o.demo[t]; continue; } for (const L of Object.keys(d)) { const e = d[L]; if (!LMAX.includes(L) || !obj(e)) { delete d[L]; continue; } e.n = Math.max(0, e.n | 0); e.at = +e.at || 0; } }
    if (!obj(o.dseen)) o.dseen = {}; const dk = Object.keys(o.dseen); if (dk.length > 600) for (const k of dk.slice(0, dk.length - 600)) delete o.dseen[k];
    if (!obj(o.seen)) o.seen = {}; for (const k of Object.keys(o.seen)) if (!['pend', 'done', 'skip'].includes(o.seen[k])) delete o.seen[k];
    if (!obj(o.pend)) o.pend = {}; for (const k of Object.keys(o.pend)) { const p = o.pend[k]; if (!obj(p) || (p.kind !== 'kid' && p.kind !== 'tr')) delete o.pend[k]; else p.at = +p.at || 0; }
    if (!obj(o.inh)) o.inh = {};
    for (const k of Object.keys(o.inh)) { const h = o.inh[k]; if (!obj(h) || typeof h.parent !== 'string' || !PAT[h.pattern] || !LMAX.includes(h.trick)) { delete o.inh[k]; continue; } h.kind = h.kind === 'tr' ? 'tr' : 'kid'; h.pkind = h.pkind === 'tr' ? 'tr' : 'kid'; h.at = +h.at || 0; }
    if (!obj(o.n)) o.n = {}; for (const k of ['picks', 'auto', 'skip', 'tricks', 'fast']) o.n[k] = Math.max(0, o.n[k] | 0);
    return o;
  }

  /* 路線／系 → 花紋 */
  function routeOf(fk, form) {
    const m = /^evo_(?:still|guard)_([a-z]+)$/.exec(fk || ''); if (m && BY_ROUTE[m[1]]) return m[1];
    if (BY_ROUTE[fk]) return fk; if (BY_ROUTE[form]) return form; return null;
  }
  function patternOf(c, art) {
    const P = art && art.parents && art.parents[c.fk]; if (P && PAT[P.pattern]) return P.pattern;
    if (c.kind === 'kid') return BY_SERIES[c.line] || 'spot';
    const r = routeOf(c.fk, c.form); return (r && BY_ROUTE[r]) || 'spot';
  }

  /* runtime 示範記錄：每堂教錯課（pet2／住客／主養細佬嘅 lessons）→ demo[大佬 id][課]；用 kid:index 去重 */
  function teachers(s) {
    const o = FAM.st(s), p = SR.st(s), out = [];
    if ((p.phase === 'kid' || p.phase === 'egg') && p.lessons && p.lessons.length) out.push({ kid: p.fid || 'pet2', bro: p.bro || FAM.trId(s), lessons: p.lessons });
    for (const r of o.res) if (r.kind === 'kid' && r.snap && Array.isArray(r.snap.lessons)) out.push({ kid: r.id, bro: r.bro || r.snap.bro || null, lessons: r.snap.lessons });
    if (o.km && o.km.snap && Array.isArray(o.km.snap.lessons)) out.push({ kid: o.km.id, bro: o.km.bro || o.km.snap.bro || null, lessons: o.km.snap.lessons });
    return out;
  }
  function noteDemo(s, tid, L, at) {
    const o = st(s); if (!tid || !LMAX.includes(L)) return false; const d = o.demo[tid] || (o.demo[tid] = {}), e = d[L] || (d[L] = { n: 0, at: 0 });
    e.n++; e.at = Math.max(e.at, +at || 0); return true;
  }
  function syncDemo(s) {
    const o = st(s); let n = 0;
    for (const t of teachers(s)) { if (!t.bro) continue; t.lessons.forEach((x, i) => { if (!x || !LMAX.includes(x.line)) return; const k = t.kid + ':' + i; if (o.dseen[k]) return; o.dseen[k] = 1; if (noteDemo(s, t.bro, x.line, x.at)) n++; }); }
    return n;
  }
  const demoOf = (s, tid) => Object.assign({}, st(s).demo[tid] || {});

  /* 家傳招式 */
  function trickOf(s, c, art) {
    if (c.kind === 'tr') {
      const d = st(s).demo[c.id] || {}; let best = null;
      for (const L of LMAX) { const e = d[L]; if (!e || !e.n) continue; if (!best || e.n > best.n || (e.n === best.n && e.at > best.at)) best = { L, n: e.n, at: e.at }; }
      if (best) return { L: best.L, src: 'demo', n: best.n };
      return { L: LMAX[hash(c.id + ':' + ((s.seed >>> 0) || 0)) % LMAX.length], src: 'random', n: 0 };
    }
    const ls = (c.lessons || []).filter(x => x && LMAX.includes(x.line)), cnt = {};
    ls.forEach((x, i) => { const e = cnt[x.line] || (cnt[x.line] = { n: 0, at: 0, i: -1 }); e.n++; e.at = Math.max(e.at, +x.at || 0); e.i = i; });
    const own = (art && art.parents && art.parents[c.fk] && art.parents[c.fk].trick) || c.line || null;
    if (own && cnt[own]) return { L: own, src: 'own', n: cnt[own].n };
    let best = null; for (const L of Object.keys(cnt)) { const e = cnt[L]; if (!best || e.n > best.n || (e.n === best.n && (e.at > best.at || (e.at === best.at && e.i > best.i)))) best = Object.assign({ L }, e); }
    if (best) return { L: best.L, src: 'most', n: best.n };
    return { L: own && LMAX.includes(own) ? own : LMAX[hash(c.id) % LMAX.length], src: 'series', n: 0 };
  }

  /* 候選上一代（成年）：主養 → 花園成年細佬 → 住客（最近搬入先） */
  function candidates(s, now, ctx, child) {
    ctx = ctx || {}; const o = FAM.st(s), p = SR.st(s), out = [], away = (o.b5 && o.b5.away) || {};
    const push = (c) => { if (!c.id || c.id === child || out.some(x => x.id === c.id)) return; c.away = !!away[c.id]; c.pattern = patternOf(c, ctx.art); const t = trickOf(s, c, ctx.art); c.trick = t.L; c.tsrc = t.src; out.push(c); };
    if (o.km) push({ id: o.km.id, kind: 'kid', fk: o.km.fk, line: o.km.line || null, name: o.km.name, main: true, lessons: (o.km.snap && o.km.snap.lessons) || [] });
    else if (FAM.trAdult(s)) push({ id: FAM.trId(s), kind: 'tr', fk: ctx.trFk || null, form: s.form, gen: s.gen || 1, name: FAM.trName(s.form), main: true });
    if (p.phase === 'kid' && FAM.kidAdult(s, now)) push({ id: FAM.kidId(s), kind: 'kid', fk: ctx.kidFk || (p.line ? p.line + '3' : 'S2'), line: p.line, name: FAM.kidName(p.line), main: false, lessons: p.lessons || [] });
    const res = o.res.slice().sort((a, b) => (b.at || 0) - (a.at || 0));
    for (const r of res) push(r.kind === 'tr' ? { id: r.id, kind: 'tr', fk: r.fk, form: r.form, gen: r.gen, name: r.name, room: r.room, main: false } : { id: r.id, kind: 'kid', fk: r.fk, line: r.line || (r.snap && r.snap.line) || null, name: r.name, room: r.room, main: false, lessons: (r.snap && r.snap.lessons) || [] });
    return out;
  }

  /* 而家有邊隻蛋等緊上一代 */
  function eggs(s) {
    const o = FAM.st(s), p = SR.st(s), out = [];
    if (p.phase === 'egg') out.push({ id: FAM.kidId(s), kind: 'kid' });
    if (s.stage === 'egg' && !o.km) out.push({ id: FAM.trId(s), kind: 'tr' });
    return out;
  }
  const fastOk = (s) => FAM.has(s, 'inherit_fast');
  function fastState(s, kind) { return kind === 'tr' ? 'tr' : fastOk(s) ? 'on' : 'locked'; }

  /* 6d：揀完上一代之後嘅 hook（long6d 用嚟套朋友蛋碼花紋；5c 本身唔理） */
  const HOOKS = []; const onChoose = (fn) => { if (typeof fn === 'function' && !HOOKS.includes(fn)) HOOKS.push(fn); };
  /* 揀（孵之前可以改） */
  function choose(s, child, pid, now, ctx, auto) {
    const o = st(s), pd = o.pend[child], prev = o.inh[child]; if (!pd && !(prev && !prev.hatched)) return { ok: false, reason: 'notPending' };
    const kind = pd ? pd.kind : prev.kind, c = candidates(s, now, ctx, child).find(x => x.id === pid); if (!c) return { ok: false, reason: 'notCand' };
    o.inh[child] = { parent: c.id, pkind: c.kind, pfk: c.fk || null, pname: c.name, pline: c.kind === 'kid' ? c.line || null : routeOf(c.fk, c.form), pattern: c.pattern, trick: c.trick, tsrc: c.tsrc, kind, at: now || 1, auto: !!auto };
    delete o.pend[child]; o.seen[child] = 'done'; o.n[auto ? 'auto' : 'picks']++;
    for (const f of HOOKS) { try { f(s, o.inh[child], child, now); } catch (e) { } }   // 6d：朋友蛋碼（下一隻細佬蛋帶朋友嘅花紋）
    return { ok: true, child, inh: Object.assign({}, o.inh[child]), fast: fastState(s, kind) };
  }

  /* 每 tick：補示範記錄、新蛋排隊、孵化（未揀 → 自動揀）、細佬鎖定加速 */
  function scan(s, now, ctx) {
    const o = st(s), ev = []; const dn = syncDemo(s); if (dn) ev.push({ k: 'demo', n: dn });
    for (const e of eggs(s)) {
      if (!e.id || o.seen[e.id]) continue;
      if (!candidates(s, now, ctx, e.id).length) { o.seen[e.id] = 'skip'; o.n.skip++; ev.push({ k: 'skip', child: e.id }); continue; }
      o.seen[e.id] = 'pend'; o.pend[e.id] = { kind: e.kind, at: now || 1 }; ev.push({ k: 'pend', child: e.id, kind: e.kind });
    }
    const live = new Set(eggs(s).map(e => e.id));
    for (const id of Object.keys(o.pend)) {
      if (live.has(id)) continue; const c = candidates(s, now, ctx, id)[0];
      if (c) { const r = choose(s, id, c.id, now, ctx, true); if (r.ok) ev.push({ k: 'auto', child: id, parent: c.id, name: c.name }); }
      else { delete o.pend[id]; o.seen[id] = 'skip'; o.n.skip++; ev.push({ k: 'skip', child: id }); }
    }
    for (const id of Object.keys(o.inh)) {
      const h = o.inh[id]; if (h.hatched || live.has(id)) continue;
      const p = SR.st(s), hatchedKid = h.kind === 'kid' && p.phase === 'kid' && p.fid === id, hatchedTr = h.kind === 'tr' && s.stage !== 'egg' && FAM.trId(s) === id;
      if (!hatchedKid && !hatchedTr) { h.hatched = now || 1; continue; }   // 已經唔喺花園／唔係而家嗰隻（搬咗入屋、換咗主養）→ 當孵咗（唔彈結果）
      h.hatched = now || 1;
      if (hatchedKid) { const on = fastOk(s); h.fast = on; if (on) { p.fast = FAST.factor; o.n.fast++; } }
      ev.push({ k: 'hatched', child: id, kind: h.kind, fast: !!h.fast });
    }
    return ev;
  }
  const inhOf = (s, id) => (id && st(s).inh[id]) || null;
  const pendOf = (s) => Object.keys(st(s).pend).map(id => Object.assign({ child: id }, st(s).pend[id]));
  function reset(s) { const F = FAM.st(s); delete F.c5; const p = SR.st(s); delete p.fast; return st(s); }

  /* 顏色：上一代主色（hi／lo）；細佬自己主色太近（|ΔRGB|<90）→ hi 推白 60%、lo ×0.7（遊美 tint_pair） */
  const hx = (h) => { const m = /^#?([0-9a-f]{6})$/i.exec(h || ''); if (!m) return [192, 160, 224]; const v = parseInt(m[1], 16); return [v >> 16 & 255, v >> 8 & 255, v & 255]; };
  const toHex = (c) => '#' + c.map(v => clamp(Math.round(v), 0, 255).toString(16).padStart(2, '0')).join('');
  const dist = (a, b) => { const A = hx(a), B = hx(b); return Math.abs(A[0] - B[0]) + Math.abs(A[1] - B[1]) + Math.abs(A[2] - B[2]); };
  function tintPair(art, h, childFk) {
    const P = art && art.parents && h && art.parents[h.pfk]; let hi, lo, base;
    if (P && P.tint) { hi = P.tint.hi; lo = P.tint.lo; base = P.tint.base; }
    else { base = (art && art.tint && art.tint.childDominant && h && art.tint.childDominant[h.pfk]) || '#c0a0e0'; const b = hx(base); hi = toHex(b.map(v => v + (255 - v) * 0.45)); lo = toHex(b.map(v => v * 0.6)); }
    const dom = art && art.tint && art.tint.childDominant && art.tint.childDominant[childFk]; let near = false;
    if (dom && dist(base, dom) < 90) { near = true; hi = toHex(hx(hi).map(v => v + (255 - v) * 0.6)); lo = toHex(hx(lo).map(v => v * 0.7)); }
    return { hi, lo, base, near };
  }
  function summary(s) { const o = st(s); return { pend: pendOf(s), inh: JSON.parse(JSON.stringify(o.inh)), demo: JSON.parse(JSON.stringify(o.demo)), seen: Object.assign({}, o.seen), n: Object.assign({}, o.n), fastOk: fastOk(s), fast: SR.st(s).fast || 0 }; }

  return { PATTERNS, PAT, BY_SERIES, BY_ROUTE, TRICK, FAST, LINES, st, routeOf, patternOf, teachers, noteDemo, syncDemo, demoOf, trickOf, candidates, eggs, fastOk, fastState, choose, scan, inhOf, pendOf, reset, hx, toHex, dist, tintPair, summary, onChoose };
});
