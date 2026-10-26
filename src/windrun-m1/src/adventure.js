/* adventure.js — 冒險切片「走路→傾偈→報名」膠水層（walk.html 用）。
   串：Save v1／Logic（旗標、動作）／Dialogue（執行器）／DialogueUI／World（Tiled 渲染）／SceneEvents（events 正規化）。
   比賽／結緣戰鬥 sim 未接：start_match／begin_capture 用「占位面板（勝／敗）」→ G.finishMatch 結算（標明 dev stub）。
   場景：town_morningmoss（主：遊美 batch2 tilemap_town.json；?town=adv 或載入失敗 → 遊程生成 fallback）、arena_windrun、trail_fernshadow。 */
(function (g) {
  'use strict';
  const W_ = g.WR, SCENES = { town_morningmoss: ['art/tiles/morningmoss/tilemap_town.json', 'art/adventure/town_morningmoss.json'], arena_windrun: ['art/adventure/arena_windrun.json'], trail_fernshadow: ['art/adventure/trail_fernshadow.json'] };
  const SCENE_IDS = Object.keys(SCENES), getJson = async u => { const r = await fetch(u); if (!r.ok) throw new Error(u + ' ' + r.status); return r.json(); };
  const sleep = ms => new Promise(r => setTimeout(r, ms));

  async function loadData(base) {
    base = base || 'data/'; const idx = await getJson(base + 'index.json'), D = { tuning: await getJson(base + 'tuning.json'), flags: await getJson(base + 'flags.json'), matches: {}, cups: {}, dialogues: {} };
    await Promise.all([].concat(idx.matches.map(async f => { const m = await getJson(base + 'matches/' + f); D.matches[m.id] = m; }), idx.cups.map(async f => { const m = await getJson(base + 'cups/' + f); D.cups[m.id] = m; }), idx.dialogue.map(async f => { const m = await getJson(base + 'dialogue/' + f); D.dialogues[m.id] = m; })));
    D.overlay = await getJson(base + 'overlay/town_morningmoss.json'); return D;
  }

  async function loadPortraits() {
    const j = await getJson('art/portraits/portraits.json'), map = {};
    await Promise.all(Object.keys(j.portraits).map(id => new Promise((res, rej) => { const e = j.portraits[id], im = new Image(); im.onload = () => { map[id] = { img: im, rects: Object.fromEntries(Object.entries(e.expressions).map(([k, v]) => [k, v.rect])), name: e.name }; res(); }; im.onerror = () => rej(new Error('portrait ' + id)); im.src = 'art/portraits/' + e.sheet; })));
    return { map, speakerMap: {}, emoteMap: {} };
  }
  async function create(opt) {
    const Q = new URLSearchParams(g.location.search), el = opt.el, A = { warnings: [], missing: [], log: [], townSource: '', busy: 0 };
    const D = await loadData(); A.D = D;
    const adapter = (() => { try { const t = '__wr_t'; g.localStorage.setItem(t, '1'); g.localStorage.removeItem(t); return g.localStorage; } catch (e) { const m = {}; return { getItem: k => m[k] || null, setItem: (k, v) => { m[k] = v; }, removeItem: k => { delete m[k]; } }; } })();
    const store = W_.Save.Store(adapter, Q.get('slot') || 'wr_walk_v1'); A.store = store;
    if (Q.get('new') === '1') store.clear();
    const loaded = store.load(Date.now()); let save = loaded.save, isNew = loaded.source === 'new';
    if (isNew) save = W_.Logic.newGame(D, { deviceId: 'dev-' + Math.random().toString(36).slice(2, 10), name: Q.get('name') || '阿風', now: Date.now() });
    A.isNew = isNew; A.loadedFrom = loaded.source;
    const hooks = {}; const G = W_.Logic.create({ save, data: D, hooks, store, now: () => Date.now() }); A.G = G; G.onWarn = m => { if (A.warnings.indexOf(m) < 0) A.warnings.push(m); };
    // 報名最少人數：正式流程 r1_min_team=2（tuning）；dev 旗標（?dev=1 或 ⚙ 面板）放寬到 1，只改運行時 tuning，唔入存檔、預設唔放寬
    const MIN_TEAM_DEFAULT = (D.tuning.r1_min_team | 0) || 2; A.devRelax = false; A.minTeamDefault = MIN_TEAM_DEFAULT;
    A.setRelax = on => { A.devRelax = !!on; G.tuning.r1_min_team = on ? 1 : MIN_TEAM_DEFAULT; return G.tuning.r1_min_team; }; if (Q.get('dev') === '1') A.setRelax(true);
    const R = W_.Dialogue.create(G, { sets: D.dialogues }); A.R = R;
    const UI = W_.DialogueUI.create(R, G, { cps: Q.get('cps') ? +Q.get('cps') : undefined }); A.UI = UI;
    const NPC_IDS = ['npc_elder', 'npc_fern', 'npc_registry'];
    const [assets] = await Promise.all([W_.World.loadAssets('art/sprites/', NPC_IDS), loadPortraits().then(P => { UI.setPortraits(P); }).catch(e => { A.warnings.push('頭像載入失敗：' + e.message); })]);
    const dpr = Q.get('dpr') ? +Q.get('dpr') : Math.min(2, g.devicePixelRatio || 1);
    const W = W_.World.create(el.canvas, assets, { dpr, tod: Q.get('tod') || null, zoom: Q.get('zoom') ? +Q.get('zoom') : 0, joyEl: el.joy, knobEl: el.knob, labels: Q.get('labels') !== '0' }); A.W = W;
    const fit = () => W.resize(+Q.get('w') || g.innerWidth, +Q.get('h') || g.innerHeight, dpr); fit(); g.addEventListener('resize', fit);
    W.hooks.cond = c => G.cond(c);
    if (UI.portraits) { UI.portraits.speakerMap = D.overlay.speaker_portrait || {}; UI.portraits.emoteMap = D.overlay.emote_map || {}; }

    const nodeIndex = {}; Object.keys(D.dialogues).forEach(id => { if (id === 'd_objects_town') Object.keys(D.dialogues[id].nodes).forEach(n => { nodeIndex[n] = id; }); });
    // ---------- 場景 ----------
    const cache = {}; A.sceneId = null;
    async function sceneOf(id) {
      if (cache[id]) return cache[id]; const urls = SCENES[id].slice(); if (id === 'town_morningmoss' && Q.get('town') === 'adv' && urls.length > 1) urls.reverse();
      let last; for (const u of urls) { try { const s = await W_.World.loadScene(u, { extrude: Q.get('extrude') !== '0' }); cache[id] = s; if (id === 'town_morningmoss') A.townSource = u === urls[0] && Q.get('town') !== 'adv' ? 'batch2' : 'fallback'; if (id === 'town_morningmoss' && u !== SCENES[id][0]) A.warnings.push('town 用 fallback 地圖：' + u); return s; } catch (e) { last = e; A.warnings.push('載入失敗 ' + u + '：' + e.message); } }
      throw last;
    }
    const isBatch2 = () => A.townSource === 'batch2';
    function posNow() { return { map: A.sceneId, x: +(W.P.x / 16).toFixed(2), y: +((W.P.y - 6) / 16).toFixed(2), dir: W.P.dir }; }
    function savePos() { if (A.sceneId) G.save.player.pos = posNow(); }
    function syncFollower() { const on = !!G.getFlag('got_mochi'); if (on && !W.cat.on) { W.cat.x = W.P.x - 16; W.cat.y = W.P.y; W.cat.hist = []; } W.cat.on = on; W.cat.species = (G.save.party[0] || {}).species || ''; }
    function applyWorldState() {   // spirit_follow：got_mochi 後先生成（遊策 §2），物種＝隊首；M1 只有 narrowcat 素材，其他物種用占位
      syncFollower();   // 場景進入後按存檔狀態套用 blocker／NPC
      const sc = W.scene; for (const e of sc.events) if (e.kind === 'blocker') W.setBlocker(e.name, !!(e.openCond ? G.cond(e.openCond) : false));
      objectiveHud();
    }
    async function enterScene(id, at, from) {
      const s = await sceneOf(id); A.sceneId = id; at = at || {};
      A.arriving = true; W.enter(s, at, { overlay: D.overlay, sceneIds: SCENE_IDS, dialogIds: Object.keys(D.dialogues), nodeIndex });
      A.missing = A.missing.concat((W.scene.norm.missing || []).filter(m => A.missing.indexOf(m) < 0).map(m => id + '：' + m)); A.arriving = false; applyWorldState(); savePos(); if (from) void from; return s;
    }
    function resolveArrival(destId, a, fromId) {
      if (a.x != null && a.y != null) {
        const ov = D.overlay, bv = ov.arrive_by_var; let ar = null;
        if (destId === 'town_morningmoss' && isBatch2()) { if (bv && bv.from === fromId) ar = bv.map[G.getVar(bv.var) || bv.default]; if (!ar && ov.arrive) ar = ov.arrive[fromId]; }
        if (ar) return { tx: ar.x, ty: ar.y, dir: ar.dir }; return { tx: a.x, ty: a.y, dir: a.dir || 'd' }; }
      const ent = a.entry || ''; const sc = cache[destId]; const names = SE_spawnNames(sc);
      let n = names.find(x => x === ent) || names.find(x => x === 'spawn_' + ent) || names.find(x => /^spawn_from_/.test(x)); if (!n) n = names[0]; if (ent && n !== ent && n !== 'spawn_' + ent) A.warnings.push('entry「' + ent + '」搵唔到同名 spawn → 用「' + n + '」');
      return { spawn: n };
    }
    const SE_spawnNames = sc => Object.keys(W_.SceneEvents.normalize(sc.dec, { overlay: D.overlay }).spawns);

    // ---------- UI／HUD ----------
    const hud = { toastT: 0 };
    function toast(t, ms) { if (!el.toast) return; el.toast.textContent = t; el.toast.style.display = 'block'; clearTimeout(hud.toastT); hud.toastT = setTimeout(() => { el.toast.style.display = 'none'; }, ms || 2400); A.lastToast = t; }
    function refreshBlockers() { const sc = W.scene; if (!sc) return; for (const e of sc.events) if (e.kind === 'blocker' && e.openCond && sc.col[e.ty * sc.dec.w + e.tx] === 1 && G.cond(e.openCond)) W.setBlocker(e.name, true); }   // 報名後閘口即時開（open_cond 變真）；唔會重新關閉已開嘅 blocker
    function objectiveHud() { if (W.scene) { syncFollower(); refreshBlockers(); } const id = G.save.chapter.step, txt = (D.flags.objectives || {})[id] || (id === 'start' ? '（去廣場）' : id); if (el.obj) el.obj.textContent = '目標：' + txt; if (el.leaf) el.leaf.textContent = '🍃 ' + G.save.player.leaf; if (el.party) el.party.textContent = '隊伍 ' + G.save.party.length + (G.save.party.length ? '（' + G.save.party.map(c => c.nick || c.species).join('、') + '）' : ''); }
    function lockAdd(d) { A.busy += d; W.lock(A.busy > 0); if (el.act) el.act.style.visibility = A.busy > 0 ? 'hidden' : (W.nearT ? 'visible' : 'hidden'); }
    W.hooks.interactable = n => { if (!el.act) return; if (n && A.busy === 0) { el.act.textContent = n.kind === 'npc' ? '💬 對話' : '🔍 調查'; el.act.style.display = 'block'; el.act.style.visibility = 'visible'; el.act.dataset.target = n.name; } else el.act.style.display = 'none'; };
    const after = [];
    function flushAfter() { while (after.length && !R.active) { const f = after.shift(); f(); } if (after.length) setTimeout(flushAfter, 30); }   // R.active 仍真（對白 end 事件早過 active 清除）時重試，避免後續對白拖到下一次 run 先播
    // ---------- 動作執行（事件／對話共用）----------
    async function runActions(actions, ctx) {
      lockAdd(1); try { const r = G.runAll(actions, ctx); if (r.blocked) await r.blocked; } finally { lockAdd(-1); } objectiveHud(); flushAfter();
    }
    A.run = runActions;
    async function runDialog(id, opts) { lockAdd(1); try { await UI.start(id, opts); } finally { lockAdd(-1); } objectiveHud(); flushAfter(); }
    A.dialog = runDialog;
    const stubPanel = (title, lines, buttons) => new Promise(res => { const p = el.panel; p.innerHTML = ''; const h = document.createElement('div'); h.className = 't'; h.textContent = title; p.appendChild(h); lines.forEach(l => { const d = document.createElement('div'); d.textContent = l; d.className = 'l'; p.appendChild(d); }); const row = document.createElement('div'); row.className = 'row'; buttons.forEach(b => { const x = document.createElement('button'); x.textContent = b.t; x.dataset.k = b.k; x.addEventListener('click', () => { p.style.display = 'none'; res(b.k); }); row.appendChild(x); }); p.appendChild(row); p.style.display = 'block'; });
    A.stubPanel = stubPanel;
    async function runMatchStub(matchId, kind) {
      const m = D.matches[matchId]; if (!m) { G.onWarn('未知比賽：' + matchId); return; }
      const k = await stubPanel('〔占位〕' + (m.name || matchId), [(kind === 'capture' ? '結緣戰' : '比賽') + '尚未接上 sim（dev stub）：揀結果', '隊伍：' + (G.save.party.map(c => c.nick || c.species).join('、') || '（無）')], [{ t: '勝（dev）', k: 'win' }, { t: '敗（dev）', k: 'lose' }]);
      const r = G.finishMatch(matchId, { win: k === 'win' }); A.lastResult = r; toast((k === 'win' ? '勝' : '敗') + ' ' + matchId + ' ｜ 葉 ' + (r.leaf >= 0 ? '+' + r.leaf : r.leaf), 3000);
      if (r.dialogue && D.dialogues[r.dialogue]) after.push(() => runDialog(r.dialogue)); objectiveHud(); flushAfter();
    }
    // host hooks（logic.js HOST_DOS＋EXT_DOS）
    Object.assign(hooks, {
      bubble: a => { toast(a.text || '', 2200); },
      say: a => UI.say(a.speaker || 'narrator', a.text || ''),
      dialog: a => UI.start(a.id, a.node ? { node: a.node } : undefined),
      push: (a, ctx) => { const ev = ctx && ctx.event; if (!ev) return; ev._from = ev._fromCell || (ctx && ctx.from) || null; const ok = W.pushAway(ev, a.tiles || 2, a.dir || 'auto'); if (!ok) return; return new Promise(res => { const t = setInterval(() => { if (!W.P.path) { clearInterval(t); res(); } }, 30); }); },
      play_cue: a => { toast('〔演出 cue：' + a.id + '（占位）〕', 1500); },
      open_gate: () => { W.setBlocker('gate', true); toast('閘口開啟', 1500); },
      npc_face: a => { W.faceNpc(a.npc, a.dir); },
      npc_move: () => {}, camera: () => {}, play_sfx: () => {}, play_bgm: () => {}, stop_bgm: () => {},
      wait: a => sleep(a.ms || 300),
      give_spirit: c => { toast('獲得野靈：' + c.species + ' Lv' + c.lv, 2200); if (G.getFlag('got_mochi')) { syncFollower(); if (!W.cat.on) W.cat.on = true; } objectiveHud(); },
      set_objective: () => { objectiveHud(); },
      show_hint: id => { toast((D.flags.hints || {})[id] || id, 3000); },
      autosave: () => { savePos(); const r = G.autosave(); A.lastSave = r; toast(r.ok ? '已自動存檔' : '存檔失敗：' + r.reason, 1200); },
      register_failed: r => { A.lastRegisterFail = r; },
      begin_capture: a => runMatchStub(a.match, 'capture'),
      start_match: a => runMatchStub(a.match, 'cup'),
      open_ui: async a => {
        if (a.name === 'naming') { const c = G.save.party[G.save.party.length - 1]; if (!c) return; const nm = await UI.prompt('幫「' + c.species + '」改個名（最多 8 字，留空＝唔改）', c.nick || '', 8); c.nick = nm.slice(0, 12); objectiveHud(); return; }
        if (a.name === 'formation') { const k = await stubPanel('佈陣（占位）', ['隊伍：' + (G.save.party.map(c => c.nick || c.species).join('、') || '（無）'), '完整佈陣 UI 未做（dev stub）'], [{ t: '確定佈陣', k: 'ok' }]); void k; G.setFlag('formation_done', true); toast('已佈陣', 1500); return; }
        G.onWarn('未知 open_ui：' + a.name);
      },
      teleport: async (a, ctx) => {
        const from = A.sceneId; const el2 = el.fade; if (el2) { el2.style.opacity = '1'; await sleep(160); }
        const s = await sceneOf(a.scene); const at = resolveArrival(a.scene, a, from); await enterScene(a.scene, at, from); void s; if (el2) { await sleep(40); el2.style.opacity = '0'; await sleep(140); }
      }
    });
    // ---------- 事件／互動 ----------
    const evKey = (e, pre) => (pre + ':' + A.sceneId.slice(0, 4) + ':' + e.name).slice(0, 48).toLowerCase();
    W.hooks.touch = (e, info) => {
      if (A.busy > 0 && !(A.arriving && !(e.actions || []).some(x => x.do === 'teleport'))) return; if (e.cond && !G.cond(e.cond)) return;
      if (e.once) { const k = evKey(e, e.once === 'match' ? 'match' : 'ev'); if (G.isDone(k)) return; G.markDone(k); }
      e._fromCell = info && info.from; A.log.push('touch ' + e.name); runActions(e.actions, { event: e, from: info && info.from });
    };
    W.hooks.interact = t => {
      if (A.busy > 0 || !t) return; W.facePlayerTo(t.kind === 'npc' ? t.ref.x : (t.ref.tx + t.ref.tw / 2) * 16, t.kind === 'npc' ? t.ref.y - 8 : (t.ref.ty + t.ref.th / 2) * 16);
      if (t.kind === 'npc') { const n = t.ref, d = (n.ev.dialogs || []).find(x => !x.cond || G.cond(x.cond)); if (!d) { toast('（' + n.display + ' 冇嘢講）'); return; } const back = n.dir; const dx = W.P.x - n.x, dy = W.P.y - n.y; n.dir = Math.abs(dx) > Math.abs(dy) ? (dx < 0 ? 'l' : 'r') : (dy < 0 ? 'u' : 'd'); A.log.push('talk ' + n.name); runDialog(d.id, d.node ? { node: d.node } : undefined).then(() => { void back; }); }
      else { A.log.push('interact ' + t.name); runActions(t.ref.actions, { event: t.ref }); }
    };
    if (el.act) el.act.addEventListener('click', () => W.hooks.interact(W.nearest()));
    g.addEventListener('keydown', e => { if ((e.key === 'e' || e.key === 'E' || e.key === ' ') && A.busy === 0 && !UI.open) { const n = W.nearest(); if (n) { e.preventDefault(); W.hooks.interact(n); } } });
    // ---------- 開始／新遊戲 ----------
    A.autosaveTimer = setInterval(() => { if (A.busy === 0 && A.sceneId) { savePos(); G.autosave(); } }, 20000);
    A.start = async function () {
      const pos = G.save.player.pos || {}; const id = pos.map && SCENES[pos.map] ? pos.map : 'town_morningmoss';
      if (isNew || !pos.map) await enterScene('town_morningmoss', { spawn: 'spawn_start' }); else await enterScene(id, { x: pos.x * 16, y: pos.y * 16, dir: pos.dir });
      W.start(); objectiveHud();
      if (!G.getFlag('intro_p1_done')) { runDialog('d_prologue'); }
    };
    A.newGame = () => { store.clear(); const u = new URLSearchParams(g.location.search); u.set('new', '1'); g.location.search = u.toString(); };
    A.state = () => Object.assign(W.state(), { minTeam: G.tuning.r1_min_team, devRelax: A.devRelax, scene: A.sceneId, busy: A.busy, townSource: A.townSource, leaf: G.save.player.leaf, party: G.save.party.map(c => c.species), flags: Object.keys(G.save.flags).filter(k => G.save.flags[k]), objective: G.save.chapter.step, registered: G.save.vars.registered_match || '', dialog: UI.state(), lastToast: A.lastToast || '' });
    A.savePos = savePos; A.toast = toast; A.objectiveHud = objectiveHud; A.sceneOf = sceneOf; A.enterScene = enterScene; A.runMatchStub = runMatchStub;
    return A;
  }
  g.WR.Adventure = { create, loadData, SCENES, SCENE_IDS };
})(typeof globalThis !== 'undefined' ? globalThis : this);
