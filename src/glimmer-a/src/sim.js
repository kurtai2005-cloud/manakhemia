/* 《微光小圃》 sim.js — DOM-free 邏輯：需求、CQ、階段、離線推算、迷你遊戲、存檔序列化。
   可喺瀏覽器（window.Glimmer.sim）或 Node（require）使用。原創代碼。 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory(require('./data.js'));
  else { root.Glimmer = root.Glimmer || {}; root.Glimmer.sim = factory(root.Glimmer.data); }
})(typeof self !== 'undefined' ? self : this, function (D) {
  'use strict';
  const P = D.PARAMS;
  const KEYS = D.NEED_KEYS;
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));

  // ── 可設種子嘅 RNG（mulberry32）──
  function makeRng(seed) {
    let a = (seed >>> 0) || 1;
    const f = function () {
      a = (a + 0x6D2B79F5) >>> 0;
      let t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
    f.getSeed = () => a;
    return f;
  }

  // ── step hook（方案 A：事件系統掛喺度；sim 本身唔依賴 events.js）──
  const stepHooks = [];
  function addStepHook(fn) { if (!stepHooks.includes(fn)) stepHooks.push(fn); }

  // ── 新存檔 ──
  function newState(nowMs, seed) {
    return {
      v: 2, createdAt: nowMs, lastSeen: nowMs, seed: seed || (nowMs % 1e9),
      stage: 'egg', form: null,
      gen: 1, memorial: [], fadeReady: false,   // evo6：第幾代；化光紀念；靜光完咗等玩家確認化光
      evo: { evIn: {}, care: {} },                // evo6：各階段事件次數（evIn[stage][id]）＋照顧次數（care[stage]={all,night}）
      needs: { hunger: 100, mood: 100, clean: 100, energy: 100 },
      sleeping: false, poops: 0, poopTimer: 0,
      growthSec: 0, ageSec: 0,
      cq: P.cqStart, cqTimer: 0,
      withdrawn: { on: false, fed: false, played: false },
      grains: 0,
      mg: { day: '', plays: 0, best: 0 },
      settings: { quality: 'high', autoSuggest: true, sound: true, volume: 'high' },
      stats: { hatches: 0, feeds: 0, plays: 0, rinses: 0, poopsCleared: 0, mgPlays: 0 },
      ev: [],
      evs: null,            // 事件系統狀態（events.js 惰性建立，會存檔）
    };
  }

  // ── 離線有效時間 E（GDD 第 7 節）──
  // E = min(T,8h)×100% + min(max(T−8h,0),16h)×25%；超過 24h 唔計。T<0 視為 0。
  function effectiveOffline(Tsec) {
    const T = Math.max(0, Tsec || 0);
    const H = 3600;
    const full = Math.min(T, P.offlineFullH * H);
    const disc = Math.min(Math.max(T - P.offlineFullH * H, 0), (P.offlineCapH - P.offlineFullH) * H);
    return full + disc * P.offlineDiscountRate;
  }

  function isUnwell(s) {
    if (s.stage === 'egg') return false;
    for (const k of KEYS) if (s.needs[k] < P.sickThreshold) return true;
    return false;
  }
  function lowestNeed(s) {
    let lk = KEYS[0];
    for (const k of KEYS) if (s.needs[k] < s.needs[lk]) lk = k;
    return lk;
  }
  function needBand(v) { return v > 60 ? 'good' : v >= 30 ? 'ok' : 'warn'; }

  // 浮動 overlay snapshot v3（Kurt 10-31 批：懸浮窗同步心情／瞌覺／需求）。純資料：
  //  moodBand：happy（心情 >60）／ok／sad（<30，同 needBand 一致）；sleeping＝遊戲入面瞓緊（關燈）；
  //  urgent＝最低嗰項需求（低過 warnAt=30 先提，同 HUD 泡泡「好肚餓…」一樣）；rate／rateAwake＝每小時變化（Kotlin 喺 app 背景時推算，
  //  同 step() 一樣：階段倍率、瞓覺 ×0.3、便便扣清潔；精力瞓覺回升）；floor＝離線保底 20（只喺原本高過先保）。
  // snapshot v4（Kurt 10-31 22:50：長按選單顯示遊戲狀態）：info＝名／階段名／形態名／進度／幾日大，同遊戲 HUD 階段標籤同一套字（只讀）。
  function overlayInfoText(s) {
    if (!s) return null;
    const st = s.stage, sec = P.stageSec[st], prog = stageProgress(s), age = Math.max(0, +s.ageSec || 0);
    const big = D.isBig(st), formName = big ? (D.FORM_NAME[s.form] || null) : null;
    const sub = st === 'egg' ? '光卵' : D.STAGE_SUB[st] ? D.STAGE_SUB[st] : (formName ? formName + '形態' + (s.fadeReady ? ' · 準備化光' : '') : '');
    return { name: '團絨', gen: s.gen || 1, stage: st, stageName: D.STAGE_NAME[st] || st, sub, form: big ? (s.form || null) : null, formName,
      evoForm: D.evoForm(st, s.form), progress: Math.round(prog * 1000) / 1000, stageH: sec ? Math.round(sec / 36) / 100 : null,
      leftH: sec ? Math.round(Math.max(0, sec - (+s.growthSec || 0)) / 36) / 100 : null,
      ageSec: Math.round(age), days: Math.floor(age / 86400), unwell: isUnwell(s), fadeReady: !!s.fadeReady };
  }
  function overlayStatus(s) {
    const warnAt = 30;
    const info = overlayInfoText(s);
    if (!s || s.stage === 'egg') return { info, egg: true, moodBand: 'ok', sleeping: false, urgent: null, level: null, warnAt, vals: null, rate: null, rateAwake: null, floor: P.offlineNeedFloor, wakeAt: P.sleepWakeAt };
    const n = s.needs, dm = P.stageDecayMul[s.stage] == null ? 1 : P.stageDecayMul[s.stage];
    const r1 = (v) => Math.round(v * 1000) / 1000;
    const rates = (slp) => { const mul = slp ? P.sleepDecayMul : 1; return {
      hunger: r1(-P.decayPerHour.hunger * dm * mul), mood: r1(-P.decayPerHour.mood * dm * mul),
      clean: r1(-(P.decayPerHour.clean * P.traitCleanDecayMul + (s.poops || 0) * P.poopCleanPenaltyPerH) * dm * mul),
      energy: r1(slp ? P.sleepRegenPerHour * P.traitSleepRegenMul : -P.decayPerHour.energy * dm) }; };
    const vals = {}; for (const k of KEYS) vals[k] = Math.round(clamp(+n[k] || 0, 0, 100) * 10) / 10;
    const lk = lowestNeed(s), mv = vals.mood;
    return { info, egg: false, moodBand: mv > 60 ? 'happy' : mv < 30 ? 'sad' : 'ok', sleeping: !!s.sleeping,
      urgent: vals[lk] < warnAt ? lk : null, level: vals[lk], warnAt, vals, rate: rates(!!s.sleeping), rateAwake: rates(false), floor: P.offlineNeedFloor, wakeAt: P.sleepWakeAt };
  }

  function decideForm(cq) {
    return cq >= P.branchBright ? 'bright' : cq >= P.branchSoft ? 'soft' : 'dust';
  }

  // ── evo6 六階段（pet-template-v1 §6）：egg 光卵 → newborn 絨點 → sprout 芽崽 → juvenile 跳跳期 →（分支）adult 守夜者 → elder 靜光 →（玩家確認）化光 ──
  const STAGES = ['egg', 'newborn', 'sprout', 'juvenile', 'adult', 'elder'];
  const EV6 = P.evo6;
  const nextStage = (st) => STAGES[STAGES.indexOf(st) + 1] || null;
  function evoOf(s) { if (!s.evo || typeof s.evo !== 'object') s.evo = { evIn: {}, care: {} }; s.evo.evIn = s.evo.evIn || {}; s.evo.care = s.evo.care || {}; return s.evo; }
  let hourFn = null;                                     // 本機鐘點（main 設做遊戲時鐘 G.hour；Node 測試可注入）
  function setHourFn(fn) { hourFn = typeof fn === 'function' ? fn : null; }
  function nowHour() { return hourFn ? hourFn() : new Date().getHours() + new Date().getMinutes() / 60; }
  function isNightHour(h) { return h >= EV6.nightFrom || h < EV6.nightTo; }
  // 照顧（餵／玩／沖洗／清便便／接星屑）：記入當前階段 care.all，夜晚（17:00–07:00）再記 care.night
  function noteCare(s, h) {
    if (s.stage === 'egg') return; const E = evoOf(s), c = E.care[s.stage] || (E.care[s.stage] = { all: 0, night: 0 });
    c.all++; if (isNightHour(h == null ? nowHour() : h)) c.night++;
  }
  function noteEvent(s, id) { if (!s || s.stage === 'egg') return; const E = evoOf(s), m = E.evIn[s.stage] || (E.evIn[s.stage] = {}); m[id] = (m[id] || 0) + 1; }   // events.js trigger 掛
  function careShare(s) {                                // 夜晚照顧佔比（careStages＝芽崽＋跳跳期）
    const E = evoOf(s); let all = 0, night = 0; EV6.careStages.forEach(st => { const c = E.care[st]; if (c) { all += c.all; night += c.night; } });
    return { all, night, share: all ? night / all : 0 };
  }
  function lumiCheck(s) {                                // 螢絨三條件
    const E = evoOf(s), ev = EV6.lumiEvStages.reduce((a, st) => a + ((E.evIn[st] && E.evIn[st][EV6.lumiEvent]) || 0), 0), cs = careShare(s);
    const r = { firefly: ev, fireflyOk: ev > 0, cq: s.cq, cqOk: s.cq >= EV6.lumiCQ, night: +cs.share.toFixed(3), nightAll: cs.all, nightOk: cs.all > 0 && cs.share >= EV6.lumiNightShare };
    r.ok = r.fireflyOk && r.cqOk && r.nightOk; return r;
  }
  function decideBranch(s) {                             // 次序：螢絨 → 燦光（CQ≥70）→ 柔光（CQ≥40）→ 微塵
    const L = lumiCheck(s); if (L.ok) return { form: 'lumi', why: 'lumi', lumi: L };
    const f = decideForm(s.cq); return { form: f, why: 'cq', lumi: L };
  }
  function enterStage(s, st) {
    s.stage = st;
    if (st === 'newborn') { s.form = null; s.needs = Object.assign({}, P.startNeedsSprout); s.cq = P.cqStart; s.cqTimer = 0; s.stats.hatches++; s.ev.push({ type: 'hatch' }); return; }
    if (st === 'sprout' || st === 'juvenile') { s.ev.push({ type: 'grow', stage: st, cq: s.cq }); return; }
    if (st === 'adult') { const d = decideBranch(s); s.form = d.form; s.ev.push({ type: 'evolve', form: s.form, cq: s.cq, why: d.why, lumi: d.lumi }); s.cq = P.cqStart; s.cqTimer = 0; return; }
    if (st === 'elder') { s.ev.push({ type: 'elder', form: s.form }); }
  }
  function checkStage(s) {
    for (let g = 0; g < 8; g++) {
      const sec = P.stageSec[s.stage]; if (sec == null || s.growthSec < sec) return;
      if (s.stage === 'elder') {                         // 靜光完：唔自動消失，等玩家確認化光（無壞結局）
        s.growthSec = sec; if (!s.fadeReady) { s.fadeReady = true; s.ev.push({ type: 'fadeReady', form: s.form }); } return;
      }
      s.growthSec -= sec; enterStage(s, nextStage(s.stage));
    }
  }
  // 化光：留低紀念（形態／代數／照顧數），生一粒新光卵（gen+1）；需求／CQ 重設，光粒／設定／統計保留
  function fade(s, nowMs) {
    if (s.stage !== 'elder' || !s.fadeReady) return { ok: false, reason: 'notReady' };
    const m = { gen: s.gen || 1, form: s.form, at: nowMs || Date.now(), ageSec: Math.round(s.ageSec) };
    s.memorial = (s.memorial || []).concat([m]); s.gen = (s.gen || 1) + 1;
    s.stage = 'egg'; s.form = null; s.growthSec = 0; s.fadeReady = false; s.sleeping = false; s.poops = 0; s.poopTimer = 0;
    s.needs = { hunger: 100, mood: 100, clean: 100, energy: 100 }; s.cq = P.cqStart; s.cqTimer = 0; s.withdrawn = { on: false, fed: false, played: false };
    s.evo = { evIn: {}, care: {} };
    s.ev.push({ type: 'fade', memorial: m });
    return { ok: true, memorial: m };
  }
  // 舊存檔（v1：egg／sprout 24h／adult）→ evo6 最近階段
  function migrate(o) {
    if (!o || o.v !== 1) return o;
    const H = 3600, from = o.stage, g = Math.max(0, +o.growthSec || 0);
    if (o.stage === 'sprout') { if (g < P.stageSec.newborn) { o.stage = 'newborn'; } else { o.stage = 'sprout'; o.growthSec = Math.min(g - P.stageSec.newborn, P.stageSec.sprout - 60); } }
    else if (o.stage === 'adult') { o.form = o.form === 'radiant' ? 'bright' : (o.form || 'dust'); o.growthSec = Math.min(g, P.stageSec.adult - EV6.migrateAdultKeepSec); }
    o.v = 2; o.migrated = { from: 1, stage: from, to: o.stage, growthH: +(g / H).toFixed(2) };
    return o;
  }

  function settleCQ(s) {
    const avg = (s.needs.hunger + s.needs.mood + s.needs.clean + s.needs.energy) / 4;
    if (avg >= P.cqGoodAt) s.cq += 1;
    else if (avg < P.cqBadBelow) s.cq -= 1;
    if (isUnwell(s)) s.cq -= P.cqSickPenalty;
    s.cq = clamp(s.cq, P.cqMin, P.cqMax);
  }

  /* 推進 dt 秒（建議 dt <= 60）。opts: { offline:bool, growthMul:number } */
  function step(s, dt, opts) {
    opts = opts || {};
    const gm = opts.growthMul == null ? 1 : opts.growthMul;
    s.ageSec += dt;
    if (opts.off) opts.off.done += dt;
    if (s.stage === 'egg') { s.growthSec += dt * gm; checkStage(s); return; }

    const hr = dt / 3600;
    const dm = P.stageDecayMul[s.stage];
    const slp = s.sleeping;
    const mul = slp ? P.sleepDecayMul : 1;
    const n = s.needs;
    const prev = { hunger: n.hunger, mood: n.mood, clean: n.clean, energy: n.energy };

    n.hunger -= P.decayPerHour.hunger * dm * mul * hr;
    n.mood -= P.decayPerHour.mood * dm * mul * hr;
    n.clean -= (P.decayPerHour.clean * P.traitCleanDecayMul + s.poops * P.poopCleanPenaltyPerH) * dm * mul * hr;
    if (slp) n.energy += P.sleepRegenPerHour * P.traitSleepRegenMul * hr;
    else n.energy -= P.decayPerHour.energy * dm * hr;
    for (const k of KEYS) n[k] = clamp(n[k], 0, 100);
    if (slp && n.energy >= P.sleepWakeAt) { s.sleeping = false; n.energy = 100; s.ev.push({ type: 'wake' }); }

    s.poopTimer += dt;
    const pi = P.poopIntervalH * 3600;
    while (s.poopTimer >= pi) {
      s.poopTimer -= pi;
      if (s.poops < P.poopMax) s.poops++;
      if (s.poops >= P.poopMax) s.poopTimer = 0;
    }

    if (opts.offline) {
      // 離線保底：最低只降至 20（原本已低過 20 就唔再降）
      for (const k of KEYS) n[k] = Math.max(n[k], Math.min(prev[k], P.offlineNeedFloor));
    }

    if (!isUnwell(s) || opts.offline) s.growthSec += dt * gm;

    if (!opts.offline) {
      s.cqTimer += dt;
      while (s.cqTimer >= 3600) { s.cqTimer -= 3600; settleCQ(s); }
    }
    checkStage(s);
    for (let i = 0; i < stepHooks.length; i++) stepHooks[i](s, dt, opts);
  }

  function advance(s, sec, opts, chunk) {
    chunk = chunk || 30;
    let left = Math.max(0, sec);
    while (left > 1e-9) { const d = Math.min(chunk, left); step(s, d, opts); left -= d; }
  }

  /* evo6 離線成長（遊策 10-31）：G = min(T, 24h) 真實時間；夠鐘就升 1 階，新階段由 0 開始、剩餘丟棄（唔跳階）。
     靜光尾 → 只會設 fadeReady（化光仍要玩家確認），同樣最多一次。分支照舊喺 enterStage('adult') 判。 */
  function offlineGrow(s, Tsec) {
    const G = Math.min(Math.max(0, Tsec || 0), P.offlineGrowCapH * 3600), from = s.stage, sec = P.stageSec[s.stage];
    const r = { G, from, to: from, up: false };
    if (!(G > 0) || sec == null) return r;
    if (s.stage === 'elder') {
      s.growthSec = Math.min(sec, s.growthSec + G);
      if (s.growthSec >= sec && !s.fadeReady) { s.fadeReady = true; s.ev.push({ type: 'fadeReady', form: s.form }); r.up = true; r.to = 'fade'; }
      return r;
    }
    if (s.growthSec + G < sec) { s.growthSec += G; return r; }
    enterStage(s, nextStage(s.stage)); s.growthSec = 0; r.up = true; r.to = s.stage;
    return r;
  }

  // ── 離線結算 ──
  function fmtDur(Tsec) {
    const h = Tsec / 3600;
    if (h < 1) return Math.max(1, Math.round(Tsec / 60)) + ' 分鐘';
    if (h < 48) return (Math.round(h * 10) / 10) + ' 個鐘';
    return Math.round(h / 24) + ' 日';
  }
  function hourOf(ms) { const d = new Date(ms); return d.getHours() + d.getMinutes() / 60; }
  // lastSaveTime（UTC ms）> now+24h → 無效（時鐘曾被撥前又改返）：重設為 now，lastSeen 一併設為 now → 該段唔派離線獎
  function sanitizeSaveTime(s, nowMs) {
    const A = D.PARAMS.events.lastSaveMaxAheadH * 3600e3;
    if (s.lastSaveTime && nowMs != null && s.lastSaveTime > nowMs + A) { s.lastSaveTime = nowMs; s.lastSeen = nowMs; s.saveTimeResets = (s.saveTimeResets || 0) + 1; s.saveResetAt = nowMs; return true; }   // saveResetAt：當日跳過保底（events）
    return false;
  }
  const offlineHooks = [];
  function addOfflineHook(fn) { offlineHooks.push(fn); }       // events.js 掛：離線事件按「日」補抽（info: {from, now, T, tampered}）
  function applyOffline(s, nowMs) {
    const reset = sanitizeSaveTime(s, nowMs);
    const T = Math.max(0, (nowMs - s.lastSeen) / 1000);
    const E = effectiveOffline(T);
    const before = { needs: Object.assign({}, s.needs), stage: s.stage, sleeping: s.sleeping, poops: s.poops };
    if (s.evs) { s.evs.offLog = []; s.evs.offPop = 0; }
    if (E > 0) {
      const off = { now: nowMs, hour0: hourOf(s.lastSeen), T: Math.min(T, P.offlineCapH * 3600), E, done: 0 };
      advance(s, E, { offline: true, growthMul: 0, off }, 60);   // 需求：照舊用有效時間 E（≤12h、保底 20）；成長唔喺度計
    }
    const grow = offlineGrow(s, T);
    for (let i = 0; i < offlineHooks.length; i++) offlineHooks[i](s, { from: s.lastSeen, now: nowMs, T, E, tampered: reset, before });
    s.lastSeen = reset ? nowMs : Math.max(+s.lastSeen || 0, nowMs);   // P1：回撥時鐘唔可以將 lastSeen 拉後（重設除外）
    const rep = { T, E, tampered: reset, show: T >= P.offlineMinAwaySec, summary: [], gift: 0, giftTotal: 0, eventGrains: 0, events: [], stageChanged: s.stage !== before.stage, withdrawn: false, grow };
    if (s.stage !== 'egg' && E > 0) {
      for (const k of KEYS) if (s.needs[k] <= P.offlineNeedFloor + 0.5 && before.needs[k] > P.offlineNeedFloor) { rep.withdrawn = true; }
      if (rep.withdrawn) s.withdrawn = { on: true, fed: false, played: false };
    }
    const evLog = (s.evs && s.evs.offLog) || [];
    rep.events = evLog.map(e => ({ id: e.id, grains: e.grains, mood: e.mood, off: e.off, diary: !!e.diary }));
    rep.eventGrains = evLog.reduce((a, e) => a + (e.diary ? 0 : e.grains), 0);      // 日記內嘅獎勵要玩家領，唔計入
    rep.diaryNew = evLog.filter(e => e.diary).length;
    rep.diaryTotal = (s.evs && s.evs.diary) ? s.evs.diary.length : 0;
    rep.popups = evLog.length - rep.diaryNew;
    if (rep.show) {
      rep.gift = clamp(Math.floor(T / 3600 * P.offlineGiftPerH), 1, P.offlineGiftMax);
      s.grains += rep.gift;
      rep.giftTotal = rep.gift + rep.eventGrains;
      const who = s.stage === 'egg' ? '光卵' : '團絨';
      const lines = [];
      lines.push('你離開咗 ' + fmtDur(T) + '，' + who + '乖乖等你返嚟。');
      let statusTxt = '';
      if (s.stage === 'egg') statusTxt = '光卵靜靜咁發住微光，又暖咗一啲';
      else if (rep.withdrawn) statusTxt = '佢有啲睏倦退縮，餵食同玩耍各一次就會恢復精神';
      else {
        const lk = lowestNeed(s);
        const t = { hunger: '肚仔開始有啲餓', mood: '自己玩玩下有啲悶', clean: '身上沾咗啲塵同絨毛', energy: '有啲眼瞓' }[lk];
        const extra = s.poops > before.poops ? '，仲留低咗 ' + (s.poops - before.poops) + ' 個便便' : '';
        statusTxt = s.needs[lk] >= 60 ? '佢自己過得好開心，仲好精神' + extra : '佢' + t + extra;
      }
      if (rep.events.length && s.stage !== 'egg') {
        // 有事件：第 2 句講事件；狀態併入第 3 句（總數永遠 ≤3 句，無任何懲罰性描述）
        const names = rep.events.filter(e => !e.diary).concat(rep.events.filter(e => e.diary)).slice(0, P.events.offlineSummaryNames).map(e => e.off);
        const more = rep.events.length > names.length ? '，仲有另外 ' + (rep.events.length - names.length) + ' 件小事' : '';
        lines.push('你唔喺度嘅時候，佢' + names.join('、') + more + '。');
        lines.push('佢送咗 ' + rep.giftTotal + ' 粒光粒俾你（' + statusTxt + '）' + (rep.diaryNew ? '，日記入面仲有 ' + rep.diaryNew + ' 件事等你領獎。' : '。'));
      } else {
        lines.push(statusTxt + '。');
        lines.push('佢送咗 ' + rep.gift + ' 粒光粒俾你，記得陪佢玩下接星屑。');
      }
      rep.summary = lines;
    }
    return rep;
  }

  // ── 行動 ──
  function noteFed(s) { if (s.withdrawn.on) { s.withdrawn.fed = true; if (s.withdrawn.played) s.withdrawn.on = false; } }
  function notePlayed(s) { if (s.withdrawn.on) { s.withdrawn.played = true; if (s.withdrawn.fed) s.withdrawn.on = false; } }

  function feed(s, foodId) {
    if (s.stage === 'egg') return { ok: false, reason: 'egg' };
    if (s.sleeping) return { ok: false, reason: 'sleeping' };
    if (s.needs.hunger >= P.feedRefuseAt) return { ok: false, reason: 'full' };
    const f = D.FOODS.find(x => x.id === foodId) || D.FOODS[0];
    let hunger = f.kind === 'snack' ? P.feedSnack : f.kind === 'meal' ? P.feedMeal : P.feedSoup;
    s.needs.hunger = clamp(s.needs.hunger + hunger, 0, 100);
    if (f.kind !== 'snack') s.needs.mood = clamp(s.needs.mood + P.foodMoodBonusWarm, 0, 100);
    s.stats.feeds++; noteFed(s); noteCare(s);
    s.ev.push({ type: 'fed', food: f.id });
    return { ok: true, food: f };
  }
  function play(s) {
    if (s.stage === 'egg') return { ok: false, reason: 'egg' };
    if (s.sleeping) return { ok: false, reason: 'sleeping' };
    s.needs.mood = clamp(s.needs.mood + P.playTease, 0, 100);
    s.needs.energy = clamp(s.needs.energy - P.playEnergyCost, 0, 100);
    s.stats.plays++; notePlayed(s); noteCare(s);
    s.ev.push({ type: 'played' });
    return { ok: true };
  }
  function rinse(s) {
    if (s.stage === 'egg') return { ok: false, reason: 'egg' };
    if (s.sleeping) return { ok: false, reason: 'sleeping' };
    s.needs.clean = clamp(s.needs.clean + P.rinse, 0, 100);
    s.stats.rinses++; noteCare(s);
    s.ev.push({ type: 'rinsed' });
    return { ok: true };
  }
  function clearPoop(s) {
    if (s.poops <= 0) return { ok: false };
    s.poops--; s.stats.poopsCleared++; noteCare(s);
    s.ev.push({ type: 'poopCleared' });
    return { ok: true };
  }
  function toggleSleep(s) {
    if (s.stage === 'egg') return { ok: false, reason: 'egg' };
    if (s.sleeping) { s.sleeping = false; return { ok: true, sleeping: false }; }
    if (s.needs.energy >= P.sleepMinEnergyToSleep) return { ok: false, reason: 'notSleepy' };
    s.sleeping = true; return { ok: true, sleeping: true };
  }
  function tapEgg(s) {
    if (s.stage !== 'egg') return { ok: false };
    s.growthSec += P.eggTapBoostSec; s.ev.push({ type: 'eggTap' });
    checkStage(s);
    return { ok: true, progress: eggProgress(s) };
  }
  function eggProgress(s) { return s.stage === 'egg' ? clamp(s.growthSec / P.stageSec.egg, 0, 1) : 1; }
  function stageProgress(s) {
    if (s.stage === 'egg') return eggProgress(s);
    const sec = P.stageSec[s.stage]; return sec ? clamp(s.growthSec / sec, 0, 1) : 1;
  }

  // ── 本機日期 key ──
  function dayKey(ms) {
    const d = new Date(ms);
    return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
  }

  // ── 迷你遊戲：接星屑 ──
  class Minigame {
    constructor(seed) {
      const M = P.mg;
      this.M = M; this.rng = makeRng(seed || 12345);
      this.t = 0; this.score = 0; this.over = false;
      this.items = []; this.fx = []; this.snd = [];   // snd：音訊事件佇列（catch／big／stone），UI 每幀清空
      this.basketX = M.fieldW / 2; this.spawnT = 0.6;
      this.caught = 0; this.stones = 0; this.stun = 0;
    }
    update(dt, targetX) {
      if (this.over) return;
      const M = this.M;
      this.t += dt;
      if (this.stun > 0) this.stun -= dt;
      // 籃子跟手（速度上限，stun 時變慢）
      const max = (this.stun > 0 ? 160 : 620) * dt;
      const tx = clamp(targetX == null ? this.basketX : targetX, M.basketW / 2, M.fieldW - M.basketW / 2);
      this.basketX += clamp(tx - this.basketX, -max, max);
      // 生成
      this.spawnT -= dt;
      const prog = clamp(this.t / M.durationSec, 0, 1);
      while (this.spawnT <= 0) {
        const r = this.rng();
        const type = r < M.stoneProb ? 'stone' : r < M.stoneProb + M.bigStarProb ? 'big' : 'star';
        const sp = M.fallSpeed[0] + (M.fallSpeed[1] - M.fallSpeed[0]) * (prog * 0.7 + this.rng() * 0.3);
        this.items.push({ type, x: 10 + this.rng() * (M.fieldW - 20), y: M.spawnTop, vy: sp, r: type === 'big' ? 6 : 5, rot: this.rng() * 6 });
        this.spawnT += M.spawnEvery[0] + (M.spawnEvery[1] - M.spawnEvery[0]) * prog;
      }
      for (const it of this.items) {
        it.y += it.vy * dt; it.rot += dt * 3;
        if (!it.dead && it.y >= M.basketY - 6 && it.y <= M.basketY + 8 && Math.abs(it.x - this.basketX) <= M.basketW / 2 + it.r - 2) {
          it.dead = true;
          if (it.type === 'stone') { this.score = Math.max(0, this.score - M.stonePenalty); this.stones++; this.stun = 0.7; this.fx.push({ type: 'stone', x: it.x, y: it.y }); this.snd.push('stone'); }
          else { this.score += it.type === 'big' ? M.bigStarScore : M.starScore; this.caught++; this.fx.push({ type: it.type, x: it.x, y: it.y }); this.snd.push(it.type === 'big' ? 'big' : 'catch'); }
        } else if (it.y > M.basketY + 40) it.dead = true;
      }
      this.items = this.items.filter(i => !i.dead);
      if (this.t >= M.durationSec) { this.over = true; this.t = M.durationSec; }
    }
  }

  // 結算獎勵（每日首 5 次全額，之後 50%）
  function mgReward(s, score, nowMs) {
    const M = P.mg;
    const dk = dayKey(nowMs);
    if (s.mg.day !== dk) { s.mg.day = dk; s.mg.plays = 0; }
    const full = s.mg.plays < M.dailyFull;
    const ratio = full ? 1 : M.afterRatio;
    const baseGrains = Math.min(M.grainsCap, Math.floor(score / M.grainsDivisor));
    const baseMood = score >= M.highScore ? M.moodHigh : score >= M.passScore ? M.moodPass : M.moodFail;
    return { score, ratio, full, playIndex: s.mg.plays + 1, grains: Math.floor(baseGrains * ratio), mood: Math.round(baseMood * ratio), baseGrains, baseMood };
  }
  function mgApply(s, score, nowMs) {
    const r = mgReward(s, score, nowMs);
    s.mg.plays++; s.mg.best = Math.max(s.mg.best || 0, score);
    s.grains += r.grains;
    s.needs.mood = clamp(s.needs.mood + r.mood, 0, 100);
    s.stats.mgPlays++; notePlayed(s); noteCare(s);
    return r;
  }

  // ── 存檔 ──
  function serialize(s) { const c = Object.assign({}, s); delete c.ev; return JSON.stringify(c); }
  function deserialize(str, nowMs) {
    try {
      const o = JSON.parse(str);
      if (!o || (o.v !== 1 && o.v !== 2) || !o.needs) return null;
      migrate(o);
      const base = newState(nowMs, o.seed);
      const s = Object.assign(base, o);
      s.needs = Object.assign(base.needs, o.needs);
      for (const k of KEYS) s.needs[k] = clamp(+s.needs[k] || 0, 0, 100);
      s.mg = Object.assign(base.mg, o.mg || {});
      s.settings = Object.assign(base.settings, o.settings || {});
      s.stats = Object.assign(base.stats, o.stats || {});
      s.withdrawn = Object.assign(base.withdrawn, o.withdrawn || {});
      s.evs = o.evs && typeof o.evs === 'object' ? o.evs : null;
      s.ev = [];
      if (!STAGES.includes(s.stage)) return null;
      if ((s.stage === 'adult' || s.stage === 'elder') && !['bright', 'soft', 'dust', 'lumi'].includes(s.form)) s.form = s.form === 'radiant' ? 'bright' : 'dust';
      evoOf(s); s.memorial = Array.isArray(s.memorial) ? s.memorial : []; s.gen = +s.gen || 1;
      return s;
    } catch (e) { return null; }
  }

  return {
    makeRng, newState, effectiveOffline, isUnwell, lowestNeed, needBand, decideForm, overlayStatus,
    step, advance, applyOffline, offlineGrow, addStepHook, addOfflineHook, hourOf, fmtDur, feed, play, rinse, clearPoop, toggleSleep, tapEgg,
    eggProgress, stageProgress, dayKey, STAGES, nextStage, enterStage, checkStage, decideBranch, lumiCheck, careShare, noteCare, noteEvent, isNightHour, setHourFn, fade, migrate, Minigame, mgReward, mgApply, serialize, deserialize, sanitizeSaveTime, settleCQ,
  };
});
