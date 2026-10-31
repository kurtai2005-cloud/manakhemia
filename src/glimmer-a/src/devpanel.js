/* 《微光小圃》 devpanel.js — 隱藏開發模式（底部細抽屜、可摺）。原創代碼。
   開關：1.5 秒內喺標題（左上 #chip）或左上角點 5 下；?dev=1 預設打開。
   功能：時間 ×1/×10/×60、跳 1 日（行離線補抽＋日記）；進化（直接設／播進化場面，含隱藏螢絨）；四需求＋CQ 滑桿；性格；
         觸發任何事件（無視冷卻）；時段／天氣 Auto/H1/H2/H3/H3雨/H4；重設存檔（二次確認）。
   QA：window.__qa.dev（每個掣都經呢個 API；calls[] 記錄每次呼叫）。 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else { root.Glimmer = root.Glimmer || {}; root.Glimmer.devpanel = factory(); }
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';
  const TAPS = 5, WINDOW_MS = 1500, CORNER = 72;               // 左上角熱區（#ui 390×844 座標）
  const SCENES = ['auto', 'H1', 'H2', 'H3', 'H3rain', 'H4', 'H3overcast', 'H3fog'];   // systems12：H3 陰／霧
  const SCENE_LABEL = { auto: 'Auto', H1: 'H1 晨', H2: 'H2 黃昏', H3: 'H3 日', H3rain: 'H3 雨', H4: 'H4 夜', H3overcast: 'H3 陰', H3fog: 'H3 霧' };
  const SCENE_HOUR = { H1: 8, H2: 17.5, H3: 13, H3rain: 13, H4: 22, H3overcast: 13, H3fog: 13 };   // 舊背景（?hd2d=0）時用代表鐘點
  const PERS = {
    default: { label: '團絨（預設）', v: null },
    sticky: { label: '黏人', v: { sticky: 1, sleepy: 0.4, timid: 0.2 } },
    sleepy: { label: '愛睏', v: { sticky: 0.4, sleepy: 1, timid: 0.4 } },
    timid: { label: '膽小', v: { sticky: 0.3, sleepy: 0.5, timid: 1 } },
    bold: { label: '大膽獨立', v: { sticky: 0.1, sleepy: 0.3, timid: 0 } },
  };
  /* 手勢判定（純函數，Node 可測）：taps＝時間戳陣列（ms），回傳 {fire, taps} */
  function tapGesture(taps, now) {
    const t = taps.filter(x => now - x <= WINDOW_MS); t.push(now);
    if (t.length >= TAPS) return { fire: true, taps: [] };
    return { fire: false, taps: t };
  }

  const CSS = `
  #devp{position:absolute;left:6px;right:6px;bottom:6px;z-index:60;font:12px/1.35 system-ui,sans-serif;color:#eef;background:rgba(14,16,34,.92);border:1px solid #6b74c8;border-radius:10px;box-shadow:0 2px 10px rgba(0,0,0,.5);display:none;pointer-events:auto}
  #devp.open{display:block}
  #devp .dh{display:flex;align-items:center;gap:6px;padding:5px 8px;border-bottom:1px solid rgba(255,255,255,.12)}
  #devp .dh b{color:#ffd86b;letter-spacing:1px}
  #devp .dh span{flex:1;opacity:.8;font-size:11px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  #devp .db{max-height:196px;overflow-y:auto;padding:4px 8px 8px}
  #devp.fold .db{display:none}
  #devp .dr{display:flex;flex-wrap:wrap;align-items:center;gap:4px;margin:4px 0}
  #devp .dr>em.dmst{font-style:normal;font-size:11px;opacity:.75}
  #devp .dr.dlive button{background:#3a2c66}
  #devp .dr.dlive button.on{background:#c79a2c;border-color:#ffd86b;color:#1a1530}
  #devp .dr>i{font-style:normal;width:44px;opacity:.7;font-size:11px}
  #devp button{font:12px system-ui,sans-serif;color:#fff;background:#2c3266;border:1px solid #5560b0;border-radius:6px;padding:3px 9px;min-height:var(--devhit,48px);min-width:var(--devhit,48px)}   /* P2：熱區 ≥48dp（main.layout 按 uiScale 計 --devhit） */
  #devp button.on{background:#ffd86b;color:#222;border-color:#ffd86b}
  #devp button.warn{background:#7a2a3a;border-color:#d05068}
  #devp label{display:flex;align-items:center;gap:4px;width:100%}
  #devp label i{font-style:normal;width:40px;opacity:.75}
  #devp label input{flex:1}
  #devp label em{font-style:normal;width:26px;text-align:right}`;

  function install(G, NS) {
    const D = NS.data, P = D.PARAMS, SIM = NS.sim, EV = NS.events, qs = new URLSearchParams(location.search);
    const ui = document.getElementById('ui'); if (!ui) return null;
    const st = document.createElement('style'); st.textContent = CSS; document.head.appendChild(st);
    const el = document.createElement('div'); el.id = 'devp'; el.setAttribute('data-testid', 'devpanel'); ui.appendChild(el);
    const hour0 = G.hourOverride;
    const calls = [];
    let taps = [], resetArm = 0, resetTimer = null;
    const note = (name, arg) => { calls.push({ name, arg: arg === undefined ? null : arg, t: Date.now() }); if (calls.length > 200) calls.shift(); };
    const s = () => G.state;

    const api = {
      calls,
      isOpen() { return el.classList.contains('open'); },
      open() { note('open'); el.classList.add('open'); render(); return true; },
      close() { note('close'); el.classList.remove('open'); disarm(); return false; },
      toggle() { return api.isOpen() ? api.close() : api.open(); },
      fold(on) { note('fold', on); el.classList.toggle('fold', on == null ? !el.classList.contains('fold') : !!on); return el.classList.contains('fold'); },
      tapGesture(now) { const r = tapGesture(taps, now == null ? performance.now() : now); taps = r.taps; if (r.fire) { note('gesture'); api.toggle(); } return r.fire; },
      // ── 時間 ──
      speed(n) {
        note('speed', n); n = [1, 10, 60].indexOf(+n) >= 0 ? +n : 1; G.timeScale = n;
        if (n > 1) { if (!G.clock.fake) { G.clock.t = Date.now(); G.clock.fake = true; } G.clockRun = true; G.hourOverride = null; }
        else if (G.clockRun) { G.clockRun = false; G.clock.fake = false; }   // ×1：返實時鐘
        sync(); return n;
      },
      skipDay() {   // 跳 1 日：當 24h 離線 → 行 SIM.applyOffline（需求、成長、事件離線補抽、日記），出離線總結
        note('skipDay'); const ev0 = s().evs ? s().evs.stats.events : 0, d0 = s().evs ? s().evs.diary.length : 0;
        const rep = G.simOffline(24); sync();
        return { events: (s().evs ? s().evs.stats.events : 0) - ev0, diary: (s().evs ? s().evs.diary.length : 0) - d0, show: !!(rep && rep.show) };
      },
      // ── 進化 ──
      forms() { return ['egg', 'sprout'].concat(D.EVOLUTION.map(e => e.form)); },
      setForm(f) {
        note('setForm', f); const S = s();
        if (f === 'egg' || f === 'sprout') { S.stage = f; S.form = null; if (f === 'sprout' && S.growthSec > P.stageSec.sprout) S.growthSec = 0; }
        else { if (!D.EVOLUTION.some(e => e.form === f)) throw new Error('dev.setForm: ' + f); S.stage = 'adult'; S.form = f; }
        S.sleeping = false; G.save(); sync(); return { stage: S.stage, form: S.form };
      },
      playEvolve(f) {   // 播進化場面：同 sim.checkStage 一樣推 evolve 事件（UI 閃光＋彈窗＋慶祝）
        note('playEvolve', f); const S = s(); f = f || SIM.decideForm && SIM.decideForm(S.cq) || 'soft';
        if (!D.EVOLUTION.some(e => e.form === f)) throw new Error('dev.playEvolve: ' + f);
        S.stage = 'adult'; S.form = f; S.sleeping = false; if (SIM.unlockDex) SIM.unlockDex(S, f); S.ev.push({ type: 'evolve', form: f, cq: S.cq }); G.save(); sync(); return f;
      },
      // ── evo6：跳階段／分支（舊「形態」「進化」行保留）──
      stages() { return D.STAGES.slice(); },
      evoStage(st) { note('evoStage', st); const S = s(); const r = G.evo.setStage(st, D.isBig(st) ? (S.form || 'soft') : null); sync(); return r; },
      evoBranch(f) { note('evoBranch', f); const S = s(); const r = G.evo.setStage(D.isBig(S.stage) ? S.stage : 'adult', f); sync(); return r; },
      // §7：強制去某支線（9 條）。成年／靜光 → 即刻換；未到成年 → 記低，跳跳期完（enterStage adult）用，用完清走
      branches() { return D.BRANCHES.slice(); },
      forceBranch(f) {
        note('forceBranch', f); const S = s(), E = S.evo || (S.evo = { evIn: {}, care: {} });
        if (f == null || f === '' || f === 'off') { delete E.force; G.save(); sync(); return { force: null, stage: S.stage, form: S.form }; }
        if (!D.BRANCHES.includes(f)) throw new Error('dev.forceBranch: ' + f);
        if (D.isBig(S.stage)) { delete E.force; G.evo.setStage(S.stage, f); } else { E.force = f; G.save(); }
        sync(); return { force: E.force || null, stage: S.stage, form: S.form };
      },
      // §7 路線清晰化：領先路線／預告／圖鑑
      routeLead() { const S = s(); return { lead: SIM.routeLead(S).form, bulb: SIM.routeBulb(S), fore: (S.evo && S.evo.fore) || null }; },
      foreshadow(f) { note('foreshadow', f); const S = s(); f = f || SIM.routeLead(S).form; if (!D.BRANCHES.includes(f) || f === 'lumi') throw new Error('dev.foreshadow: ' + f);
        S.ev.push({ type: 'foreshadow', form: f, act: P.evo6.route.foreshadow[f] || null, dev: true }); sync(); return f; },
      drowsy() { note('drowsy'); const S = s(); if (S.stage === 'egg') throw new Error('dev.drowsy: egg'); S.sleeping = false; S.needs.energy = Math.max(0, D.PARAMS.evo6.branch.lull.drowsyEnergy - 5); G.save(); sync(); return SIM.isDrowsy(S); },   // v5：令團絨眼瞓（測哄瞓）
      lull() { note('lull'); const ok = G.lull ? G.lull() : false; sync(); return ok; },
      // v7 晶角：手動「上線」（開即清窗口）／出一粒便便；v8 火苗：模擬浮動團絨撳兩下開 game（＝一局）
      login() { note('login'); const L = G.login(); sync(); return L; },
      addPoop() { note('addPoop'); const S = s(); if (S.stage === 'egg') throw new Error('dev.addPoop: egg'); if (S.poops < P.poopMax) { S.poops++; SIM.poopAges(S).push(0); } G.save(); sync(); return S.poops; },
      overlayGame() { note('overlayGame'); const r = G.evo.overlayOpenGame(); sync(); return r; },
      weather(w) { note('weather', w); const W = D.PARAMS.evo6.branch.weather.states; if (G.weatherSet) G.weatherSet(w === 'auto' || W.includes(w) ? w : 'clear'); else G.weather = W.includes(w) && w !== 'clear' ? w : null; sync(); return SIM.weatherNow(); },   // systems12：自動天氣；DEV 揀 → 覆蓋（「自動」還原）
      s12(a) { note('s12', a); const Q = window.__qa && __qa.sys12; if (!Q) return null; let r = null;   // systems12 DEV：委託／星星碎（之後：親密／心聲／驚喜／日記）
        if (a === 'open') r = Q.open('quest'); else if (a === 'q0' || a === 'q1' || a === 'q2') r = Q.questDo(+a[1]); else if (a === 'qall') r = Q.questFill(); else if (a === 'qreset') r = Q.questReset(); else if (a === 'shard5') r = Q.grant(5, 'dev');
        else if (G.s12dev && G.s12dev[a]) r = G.s12dev[a](); sync(); return r; },
      season(m) { note('season', m); const r = G.seasonSet ? G.seasonSet(m) : null; sync(); return r; },   // systems12 季節：auto／spring／summer／autumn／winter／none（基本款）   // v4：天氣系統未做 → DEV 設定（之後由天氣系統驅動）
      careDays(n) { note('careDays', n); const S = s(); n = Math.max(0, n | 0); const now = G.now ? G.now() : Date.now(), have = new Set(S.careDays || []); for (let i = 0; i < n; i++) have.add(SIM.dayKey(now - i * 86400000)); if (n === 0) have.clear(); S.careDays = [...have].sort(); if (n && S.evo) S.evo.day0 = SIM.dayKey(now - (n - 1) * 86400000); G.save(); sync(); return SIM.careDaysCheck(S); },   // v4 燦光：補最近 n 日照顧日（0＝清）
      dexUnlock(f) { note('dexUnlock', f); const S = s(); if (f === 'none') S.dex = []; else (f === 'all' ? D.BRANCHES : [f]).forEach(x => SIM.unlockDex(S, x)); G.save(); sync(); return (S.dex || []).slice(); },
      openDex() { note('openDex'); window.Glimmer.ui.openDex(); return SIM.dexList(s()); },
      evoNext() { note('evoNext'); const r = G.evo.next(); sync(); return r; },
      evoFade() { note('evoFade'); const S = s(); if (S.stage !== 'elder') G.evo.setStage('elder', S.form || 'soft'); if (!S.fadeReady) G.evo.next(); const r = G.fade(); sync(); return r; },
      evoInfo() { return G.evo.info(); },
      // ── 需求／CQ／性格 ──
      setNeed(k, v) { note('setNeed', [k, v]); if (D.NEED_KEYS.indexOf(k) < 0) throw new Error('dev.setNeed: ' + k); s().needs[k] = Math.max(0, Math.min(100, +v)); if (s().evs && +v >= P.events.grumpyLowNeed) s().evs.low = 0; return s().needs[k]; },
      setCQ(v) { note('setCQ', v); s().cq = Math.max(P.cqMin, Math.min(P.cqMax, +v)); return s().cq; },
      personality(p) {
        note('personality', p); const pr = typeof p === 'string' ? PERS[p] : { v: p };
        if (!pr) throw new Error('dev.personality: ' + p);
        G.beh.pers = Object.assign({}, P.personality, pr.v || {}); G.devPers = typeof p === 'string' ? p : 'custom'; sync(); return Object.assign({}, G.beh.pers);
      },
      // ── 事件（全 EVENTS 表，無視冷卻／條件）──
      events() { return D.EVENTS.map(e => e.id); },
      trigger(id) {
        note('trigger', id);
        if (id === 'flash' && EV.setFlashDay) EV.setFlashDay(s(), true);
        const rec = G.forceEvent(id); if (!rec) throw new Error('dev.trigger: ' + id);
        if (id === 'grumpy' && G.beh && NS.behavior.force) { try { G.forceBeh('grumpy'); } catch (e) { /* 行為 grumpy 可選 */ } }
        return { id: rec.id, kind: rec.kind };
      },
      // ── 時段／天氣 ──
      scene(m) {
        note('scene', m); if (SCENES.indexOf(m) < 0) throw new Error('dev.scene: ' + m);
        G.weather = m === 'H3rain' ? 'rain' : m === 'H3overcast' ? 'overcast' : m === 'H3fog' ? 'fog' : null; if (G.wx) G.wx.manual = m !== 'auto';   // systems12：揀款＝覆蓋自動天氣
        if (m === 'auto') G.hourOverride = hour0; else { G.hourOverride = SCENE_HOUR[m]; G.clockRun = false; G.timeScale = 1; G.clock.fake = false; }
        if (G.hd) G.hd.set(m);
        sync(); return G.hd ? G.hd.current() : { mode: m };
      },
      hd2d(on) { note('hd2d', on); if (G.hd) G.hd.enabled = on !== false; sync(); return !!(G.hd && G.hd.enabled); },
      // ── 重設存檔（二次確認）──
      reset(confirm) {
        note('reset', !!confirm);
        if (!confirm && !resetArm) { resetArm = 1; clearTimeout(resetTimer); resetTimer = setTimeout(disarm, 3000); sync(); return 'armed'; }
        disarm(); G.resetSave(); return 'reset';
      },
      state() { const S = s(); return { open: api.isOpen(), folded: el.classList.contains('fold'), speed: G.timeScale, clockRun: !!G.clockRun, hour: +G.hour().toFixed(2), stage: S.stage, form: S.form, cq: Math.round(S.cq), needs: Object.assign({}, S.needs), pers: G.beh ? Object.assign({}, G.beh.pers) : null, scene: G.hd ? G.hd.current() : null, weather: G.weather || 'clear', resetArmed: !!resetArm }; },
      // ── 生命感第二段（s2b）：即刻觸發（唔理冷卻／機率，個性鏈照接）＋強制鏈＋展示模式 ──
      live(k) { note('live', k); const ok = G.liveNow ? G.liveNow(k) : false; sync(); if (k === 'bulb') return ok; if (k === 'nuzzle' && ok) return G.beh.state; if (k === 'reunion' && ok) return G.reunionPending ? 'pending' : 'reunion'; return ok ? (G.beh.gaitForce ? G.beh.gaitForce.g : G.beh.seq && G.beh.seq[G.beh.seqI] ? (G.beh.seq[G.beh.seqI].tag || G.beh.seq[G.beh.seqI].clip) : G.beh.state) : false; },
      chain(name) { note('chain', name); G.forceBeh(name); sync(); return name; },
      demo(on) { const v = on == null ? !G.liveDemo : (on === true || on === 'on' || on === '1' || on === 1); note('demo', v); G.setLiveDemo(v); sync(); return G.liveDemo; },
      sync: () => sync(),
    };
    function disarm() { resetArm = 0; clearTimeout(resetTimer); sync(); }

    // ── DOM ──
    const LIVE_NOW = [['sniff', '嗅地'], ['lookup', '望天'], ['swat', '拍蟲'], ['scratch', '抓癢'], ['sneeze', '打噴嚏'], ['happy', '開心步'], ['drag', '拖步'], ['smug', 'smug'], ['nuzzle', '磨蹭'], ['reunion', '久未見'], ['bulb', '燈泡']];   // s3：磨蹭（自動撳住 2.6s）／久未見（模擬離線 8h → 衝埋嚟）／燈泡（循環 5 心情）
    const LIVE_CHAIN = [['sniff_sneeze', '嗅→噴嚏'], ['lookup_tip', '望天→後倒'], ['swat_miss', '撲空→得意'], ['swat_hit', '拍中']];
    const BULB_ZH = { happy: '開心', neutral: '平常', sleepy: '睏', hungry: '肚餓', grumpy: '嬲' };
    const btn = (label, fn, tid, cls) => `<button data-a="${fn}" ${tid ? 'data-testid="' + tid + '"' : ''} class="${cls || ''}">${label}</button>`;
    function render() {
      const S = s(), N = D.NEED_LABEL;
      el.innerHTML = `<div class="dh"><b>DEV</b><span id="devst"></span>${btn('▾', 'fold', 'dev-fold')}${btn('✕', 'close', 'dev-close')}</div>
      <div class="db">
        <div class="dr"><i>時間</i>${[1, 10, 60].map(n => btn('×' + n, 'speed:' + n, 'dev-speed-' + n)).join('')}${btn('跳 1 日', 'skipDay', 'dev-skipday')}</div>
        <div class="dr dlive" data-testid="dev-live-row"><i>生命感</i>${LIVE_NOW.map(([k, l]) => btn(l, 'live:' + k, 'dev-live-' + k)).join('')}</div>
        <div class="dr dlive"><i>s2 鏈</i>${LIVE_CHAIN.map(([k, l]) => btn(l, 'chain:' + k, 'dev-chain-' + k)).join('')}${btn('展示模式', 'demo', 'dev-live-demo')}<em class="dmst" data-testid="dev-live-demo-state"></em></div>
        <div class="dr"><i>時段</i>${SCENES.map(m => btn(SCENE_LABEL[m], 'scene:' + m, 'dev-scene-' + m)).join('')}${btn('HD', 'hd2d', 'dev-hd2d')}</div>
        <div class="dr"><i>形態</i>${api.forms().map(f => btn(f === 'egg' ? '光卵' : f === 'sprout' ? '芽崽' : D.FORM_NAME[f] + (f === 'lumi' ? '★' : ''), 'setForm:' + f, 'dev-form-' + f)).join('')}</div>
        <div class="dr" data-testid="dev-stage-row"><i>階段</i>${D.STAGES.map(st => btn(D.STAGE_NAME[st], 'evoStage:' + st, 'dev-stage-' + st)).join('')}${btn('▶下一階段', 'evoNext', 'dev-stage-next')}${btn('化光', 'evoFade', 'dev-fade')}</div>
        <div class="dr" data-testid="dev-branch-row"><i>分支</i>${['lumi', 'bright', 'soft', 'dust'].map(f => btn(D.FORM_NAME[f] + (f === 'lumi' ? '★' : ''), 'evoBranch:' + f, 'dev-branch-' + f)).join('')}<em class="dmst" data-testid="dev-lumi-state"></em></div>
        <div class="dr" data-testid="dev-force-row"><i>強制支線</i>${D.BRANCHES.map(f => btn(D.FORM_NAME[f] + (f === 'lumi' ? '★' : ''), 'forceBranch:' + f, 'dev-force-' + f)).join('')}${btn('清除', 'forceBranch:off', 'dev-force-off')}<em class="dmst" data-testid="dev-b5-state"></em></div>
        <div class="dr" data-testid="dev-weather-row"><i>天氣</i>${D.PARAMS.evo6.branch.weather.states.map(w => btn({ clear: '晴', overcast: '陰', fog: '霧', rain: '雨' }[w] || w, 'weather:' + w, 'dev-weather-' + w)).join('')}${btn('自動', 'weather:auto', 'dev-weather-auto')}${btn('照顧日 7', 'careDays:7', 'dev-care-days-7')}${btn('清照顧日', 'careDays:0', 'dev-care-days-0')}<span data-testid="dev-weather-state"></span></div>
        <div class="dr" data-testid="dev-season-row"><i>季節</i>${['auto', 'spring', 'summer', 'autumn', 'winter', 'none'].map(m => btn({ auto: '自動', spring: '春', summer: '夏', autumn: '秋', winter: '冬', none: '基本' }[m], 'season:' + m, 'dev-season-' + m)).join('')}<span data-testid="dev-season-state"></span></div>
        <div class="dr" data-testid="dev-crystal-row"><i>晶角</i>${btn('上線', 'login', 'dev-login')}${btn('出便便', 'addPoop', 'dev-add-poop')}<span data-testid="dev-crystal-state"></span></div>
        <div class="dr" data-testid="dev-ember-row"><i>火苗</i>${btn('浮動開 game', 'overlayGame', 'dev-overlay-game')}<span data-testid="dev-ember-state"></span></div>
        <div class="dr" data-testid="dev-s12q-row"><i>委託</i>${btn('面板', 's12:open', 'dev-s12-open')}${btn('做#1', 's12:q0', 'dev-s12-q0')}${btn('做#2', 's12:q1', 'dev-s12-q1')}${btn('做#3', 's12:q2', 'dev-s12-q2')}${btn('全做', 's12:qall', 'dev-s12-qall')}${btn('重抽', 's12:qreset', 'dev-s12-qreset')}${btn('+5碎', 's12:shard5', 'dev-s12-shard5')}<span data-testid="dev-s12q-state"></span></div>
        <div class="dr" data-testid="dev-s12b-row"><i>親密</i>${btn('面板', 's12:bondOpen', 'dev-s12-bond-open')}${btn('+10', 's12:bondUp', 'dev-s12-bond-up')}${btn('−10', 's12:bondDown', 'dev-s12-bond-down')}${btn('心聲', 's12:voice', 'dev-s12-voice')}${btn('唔理一日', 's12:ignore', 'dev-s12-ignore')}<span data-testid="dev-s12b-state"></span></div>
        <div class="dr" data-testid="dev-s12s-row"><i>驚喜</i>${btn('面板', 's12:surpOpen', 'dev-s12-surp-open')}${btn('掉一粒', 's12:drop', 'dev-s12-drop')}${btn('掉 6 粒', 's12:drop5', 'dev-s12-drop6')}${btn('飲水', 's12:water', 'dev-s12-water')}${btn('早瞓', 's12:sleep', 'dev-s12-sleep')}${btn('碎開閂', 's12:surpDrop', 'dev-s12-tg-drop')}${btn('水開閂', 's12:surpWater', 'dev-s12-tg-water')}${btn('瞓開閂', 's12:surpSleep', 'dev-s12-tg-sleep')}<span data-testid="dev-s12s-state"></span></div>
        <div class="dr" data-testid="dev-s12d-row"><i>日記</i>${btn('面板', 's12:diaryOpen', 'dev-s12-diary-open')}${btn('寫今日', 's12:diaryWrite', 'dev-s12-diary-write')}${btn('進化頁', 's12:diaryEvolve', 'dev-s12-diary-evolve')}${btn('離線 3 日', 's12:diaryOffline', 'dev-s12-diary-offline')}${btn('填 40 日', 's12:diaryFill', 'dev-s12-diary-fill')}<span data-testid="dev-s12d-state"></span></div>
        <div class="dr" data-testid="dev-lull-row"><i>月眠</i>${btn('眼瞓', 'drowsy', 'dev-drowsy')}${btn('哄瞓', 'lull', 'dev-lull')}<span data-testid="dev-lull-state"></span></div>
        <div class="dr" data-testid="dev-route-row"><i>路線</i>${btn('預告', 'foreshadow', 'dev-foreshadow')}${btn('圖鑑', 'openDex', 'dev-dex')}${btn('解鎖全部', 'dexUnlock:all', 'dev-dex-all')}${btn('清圖鑑', 'dexUnlock:none', 'dev-dex-none')}</div>
        <div class="dr"><i>進化</i>${D.EVOLUTION.map(e => btn('▶' + e.name, 'playEvolve:' + e.form, 'dev-evolve-' + e.form)).join('')}</div>
        ${D.NEED_KEYS.map(k => `<label><i>${N[k]}</i><input type="range" min="0" max="100" step="1" data-need="${k}" data-testid="dev-need-${k}" value="${Math.round(S.needs[k])}"><em>${Math.round(S.needs[k])}</em></label>`).join('')}
        <label><i>CQ</i><input type="range" min="${P.cqMin}" max="${P.cqMax}" step="1" data-cq="1" data-testid="dev-cq" value="${Math.round(S.cq)}"><em>${Math.round(S.cq)}</em></label>
        <div class="dr"><i>性格</i>${Object.keys(PERS).map(k => btn(PERS[k].label, 'personality:' + k, 'dev-pers-' + k)).join('')}</div>
        <div class="dr"><i>事件</i>${D.EVENTS.map(e => btn(e.name || e.id, 'trigger:' + e.id, 'dev-ev-' + e.id)).join('')}</div>
        <div class="dr"><i>存檔</i>${btn('重設存檔', 'reset', 'dev-reset', 'warn')}</div>
      </div>`;
      sync();
    }
    function sync() {
      if (!api.isOpen()) return;
      const S = s(), sc = G.hd ? G.hd.current() : null, q = (sel) => el.querySelector(sel);
      const stEl = q('#devst'); if (stEl) stEl.textContent = `${G.hour().toFixed(1)}h ×${G.timeScale} ${sc ? (sc.enabled && sc.ready ? sc.variant || '-' : 'HD off') : ''} ${D.STAGE_NAME[S.stage] || S.stage}${S.form ? '/' + (D.FORM_NAME[S.form] || S.form) : ''} CQ${Math.round(S.cq)}`;
      el.querySelectorAll('button[data-a^="speed:"]').forEach(b => b.classList.toggle('on', +b.dataset.a.split(':')[1] === G.timeScale));
      el.querySelectorAll('button[data-a^="weather:"]').forEach(b => b.classList.toggle('on', SIM.weatherNow && b.dataset.a.split(':')[1] === SIM.weatherNow()));
      el.querySelectorAll('button[data-a^="scene:"]').forEach(b => b.classList.toggle('on', !!sc && b.dataset.a.split(':')[1] === sc.mode));
      el.querySelectorAll('button[data-a^="personality:"]').forEach(b => b.classList.toggle('on', b.dataset.a.split(':')[1] === (G.devPers || 'default')));
      el.querySelectorAll('button[data-a^="setForm:"]').forEach(b => { const f = b.dataset.a.split(':')[1]; b.classList.toggle('on', f === S.stage || (S.stage === 'adult' && f === S.form)); });
      el.querySelectorAll('button[data-a^="evoStage:"]').forEach(b => b.classList.toggle('on', b.dataset.a.split(':')[1] === S.stage));
      el.querySelectorAll('button[data-a^="evoBranch:"]').forEach(b => b.classList.toggle('on', D.isBig(S.stage) && b.dataset.a.split(':')[1] === S.form));
      const lsx = q('[data-testid="dev-lull-state"]'); if (lsx && SIM.isDrowsy) { const L = S.evo && S.evo.lull; lsx.textContent = `${SIM.isDrowsy(S) ? '眼瞓' : S.sleeping ? '瞓緊' : '醒'}｜今晚哄瞓 ${L ? L.n : 0}/${D.PARAMS.evo6.branch.lull.perNight}`; }
      const cs = q('[data-testid="dev-crystal-state"]'); if (cs && SIM.branch5Check) { const B = SIM.branch5Check(S), Lg = S.evo && S.evo.login, W = D.PARAMS.evo6.branch.crystal, left = Lg ? Math.max(0, Math.ceil(W.windowSec - (G.now() - Lg.at) / 1000)) : 0;
        cs.textContent = `便便${S.poops}｜窗口${Lg ? (Lg.done ? '已即清' : !Lg.had ? '（上線冇便便）' : left ? '剩' + left + 's' : '過咗') : '-'}｜即清 ${B.raw.quickLogin}/${B.raw.loginPoop} → ${B.score.crystal}分`; }
      const es = q('[data-testid="dev-ember-state"]'); if (es && SIM.branch5Check) { const B = SIM.branch5Check(S), O = D.PARAMS.evo6.branch.overlayMg, at = S.mg && S.mg.overlayAt, cd = at ? Math.max(0, Math.ceil(O.cooldownSec - (G.now() - at) / 1000)) : 0;
        es.textContent = `火苗${B.score.ember}分｜今日小遊戲 ${S.mg ? S.mg.plays : 0}｜冷卻${cd ? cd + 's' : '無'}`; }
      const s1q = q('[data-testid="dev-s12q-state"]'); if (s1q && window.__qa && __qa.sys12 && __qa.sys12.quests) { const Q = __qa.sys12.quests(), W = __qa.sys12.wallet(); s1q.textContent = `${Q.list.map(x => x.k + (x.route ? '*' : '') + ' ' + x.n + '/' + x.need).join('、') || '—'}${Q.paid ? '（已發）' : ''}｜碎 ${W.total}（今日 ${W.today}/${W.cap}）`; }
      const s1b = q('[data-testid="dev-s12b-state"]'); if (s1b && window.__qa && __qa.sys12 && __qa.sys12.bond) { const B = __qa.sys12.bond(), cd = Math.max(0, Math.ceil((B.lastVoice + B.cooldownSec * 1000 - G.now()) / 1000)); s1b.textContent = `${Math.round(B.v)}（第 ${B.tier} 段｜今日 +${B.todayGain}/${B.cap}｜心聲冷卻 ${cd}s）`; }
      const s1s = q('[data-testid="dev-s12s-state"]'); if (s1s && window.__qa && __qa.sys12 && __qa.sys12.surp) { const u = __qa.sys12.surp(), o = __qa.sys12.overlay().surp; s1s.textContent = `碎${u.on.drop ? '開' : '閂'}／水${u.on.water ? '開' : '閂'} ${u.waterH}h／瞓${u.on.sleep ? '開' : '閂'} ${u.sleepAt}｜今日餘 ${o.drop.room}`; }
      const s1d = q('[data-testid="dev-s12d-state"]'); if (s1d && window.__qa && __qa.sys12 && __qa.sys12.diary) { const d = __qa.sys12.diary(); s1d.textContent = `${d.list.length} 篇（留 ${d.keepDays} 日）${d.today ? '｜今日：' + d.today.kind : ''}`; }
      const ss = q('[data-testid="dev-season-state"]'); if (ss && G.wx) ss.textContent = `${G.wx.season || '基本'}（${G.wx.seasonMode}）`;
      el.querySelectorAll('button[data-a^="season:"]').forEach(b => b.classList.toggle('on', !!G.wx && b.dataset.a.split(':')[1] === G.wx.seasonMode));
      const wa = q('[data-a="weather:auto"]'); if (wa && G.wx) wa.classList.toggle('on', G.wx.auto && !G.wx.manual);
      const ws = q('[data-testid="dev-weather-state"]'); if (ws && SIM.weatherNow) { const C = SIM.careDaysCheck(S); ws.textContent = `${SIM.weatherNow()}${G.wx ? (G.wx.manual ? '（DEV）' : G.wx.auto ? '（自動 ' + G.wx.autoWeather + '）' : '') : ''}｜照顧日 ${C.days}/${C.need}（${C.span} 日）${C.ok ? '✓' : '✗'}`; }
      const ls = q('[data-testid="dev-lumi-state"]'); if (ls && SIM.lumiCheck) { const L = SIM.lumiCheck(S); ls.textContent = `螢絨：螢火${L.firefly}${L.fireflyOk ? '✓' : '✗'} CQ${Math.round(L.cq)}${L.cqOk ? '✓' : '✗'} 夜${Math.round(L.night * 100)}%/${L.nightAll} 機會${Math.round(L.chance * 100)}% roll${L.roll}${L.ok ? '✓' : '✗'}`; }
      el.querySelectorAll('button[data-a^="forceBranch:"]').forEach(b => { const f = b.dataset.a.split(':')[1], fo = S.evo && S.evo.force; b.classList.toggle('on', fo ? f === fo : D.isBig(S.stage) && f === S.form); });
      const b5 = q('[data-testid="dev-b5-state"]'); if (b5 && SIM.branch5Check) { const B = SIM.branch5Check(S), fo = S.evo && S.evo.force; b5.textContent = (fo ? '強制→' + D.FORM_NAME[fo] + '　' : '') + `新5：${D.FORM_NAME[B.top]}${Math.round(B.topShare * 100)}% 次${D.FORM_NAME[B.second]}${Math.round(B.secondShare * 100)}% /${B.all} CQ${Math.round(B.cq)}/${B.cqNeed}${B.cqOk ? '✓' : '✗'} ${B.ok ? '✓' : '✗'}`; }
      const bb = q('[data-a="live:bulb"]'); if (bb) { const m = G.beh && G.beh.bulbForce; bb.classList.toggle('on', !!m); bb.textContent = '燈泡 ' + (m ? BULB_ZH[m] || m : '自動'); }
      const dm = q('[data-a="demo"]'); if (dm) { dm.classList.toggle('on', !!G.liveDemo); dm.textContent = '展示模式 ' + (G.liveDemo ? '開' : '關'); }
      const dst = q('.dmst'); if (dst) dst.textContent = G.liveDemo ? '×' + (P.beh.live.demoMul || 5) + ' 頻率／冷卻 ÷' + (P.beh.live.demoMul || 5) : '正常頻率';
      const hb = q('[data-a="hd2d"]'); if (hb) hb.classList.toggle('on', !!(G.hd && G.hd.enabled));
      const rb = q('[data-a="reset"]'); if (rb) rb.textContent = resetArm ? '再撳一次確認重設' : '重設存檔';
      const fb = q('[data-a="fold"]'); if (fb) fb.textContent = el.classList.contains('fold') ? '▴' : '▾';
      el.querySelectorAll('input[data-need]').forEach(i => { if (document.activeElement !== i) { i.value = Math.round(S.needs[i.dataset.need]); i.nextElementSibling.textContent = i.value; } });
      const cq = q('input[data-cq]'); if (cq && document.activeElement !== cq) { cq.value = Math.round(S.cq); cq.nextElementSibling.textContent = cq.value; }
    }
    el.addEventListener('click', (e) => {
      const b = e.target.closest('button[data-a]'); if (!b) return; e.stopPropagation();
      const [fn, arg] = b.dataset.a.split(':');
      try {
        if (fn === 'hd2d') api.hd2d(!(G.hd && G.hd.enabled));
        else if (fn === 'reset') api.reset(false);
        else if (fn === 'fold') api.fold();
        else if (fn === 'demo') api.demo();
        else if (arg != null) api[fn](arg); else api[fn]();
      } catch (err) { note('error', String(err.message || err)); }
      sync();
    });
    el.addEventListener('input', (e) => {
      const i = e.target; if (i.dataset.need) api.setNeed(i.dataset.need, +i.value); else if (i.dataset.cq) api.setCQ(+i.value);
      if (i.nextElementSibling) i.nextElementSibling.textContent = i.value;
    });
    ['pointerdown', 'touchstart', 'mousedown'].forEach(t => el.addEventListener(t, (e) => e.stopPropagation()));   // 抽屜操作唔當點寵物

    // 手勢：標題（#chip）或左上角 5 下（capture，唔阻原本處理）
    ui.addEventListener('pointerdown', (e) => {
      if (el.contains(e.target)) return;
      const r = ui.getBoundingClientRect(), k = r.width / 390, x = (e.clientX - r.left) / k, y = (e.clientY - r.top) / k;
      const chip = document.getElementById('chip'), cr = chip && chip.getBoundingClientRect();
      const inChip = cr && e.clientX >= cr.left && e.clientX <= cr.right && e.clientY >= cr.top && e.clientY <= cr.bottom;
      if (inChip || (x <= CORNER && y <= CORNER)) api.tapGesture(e.timeStamp || performance.now());
    }, true);
    setInterval(sync, 500);

    G.dev = api;
    window.__qa = window.__qa || {}; window.__qa.dev = api;
    if (qs.get('dev') === '1') api.open();
    return api;
  }
  return { install, tapGesture, TAPS, WINDOW_MS, SCENES, PERS };
});
