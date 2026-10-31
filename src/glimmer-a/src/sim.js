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
      gen: 1, memorial: [], dex: [], careDays: [], fadeReady: false,   // evo6：第幾代；化光紀念；靜光完咗等玩家確認化光
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

  function decideForm(cq) {                              // 淨睇 CQ（DEV 預覽用）；正式判定睇 decideBranch
    const C = P.evo6.branch; return cq >= C.brightCQ ? 'bright' : cq >= C.softCQ ? 'soft' : 'dust';
  }

  // ── evo6 六階段（pet-template-v1 §6）：egg 光卵 → newborn 絨點 → sprout 芽崽 → juvenile 跳跳期 →（分支）adult 守夜者 → elder 靜光 →（玩家確認）化光 ──
  const STAGES = ['egg', 'newborn', 'sprout', 'juvenile', 'adult', 'elder'];
  const EV6 = P.evo6;
  const nextStage = (st) => STAGES[STAGES.indexOf(st) + 1] || null;
  function evoOf(s) { if (!s.evo || typeof s.evo !== 'object') s.evo = { evIn: {}, care: {} }; s.evo.evIn = s.evo.evIn || {}; s.evo.care = s.evo.care || {}; s.evo.b5 = s.evo.b5 || {}; s.evo.cl = s.evo.cl || {}; return s.evo; }
  let hourFn = null;                                     // 本機鐘點（main 設做遊戲時鐘 G.hour；Node 測試可注入）
  function setHourFn(fn) { hourFn = typeof fn === 'function' ? fn : null; }
  function nowHour() { return hourFn ? hourFn() : new Date().getHours() + new Date().getMinutes() / 60; }
  function isNightHour(h) { return h >= EV6.nightFrom || h < EV6.nightTo; }
  // v4 天氣狀態：clear／overcast／rain（main 設做 G.weather；天氣系統未做 → DEV／?weather=；Node 測試可注入）
  let weatherFn = null;
  function normWeather(w) { return w === true ? 'rain' : (BR().weather.states.includes(w) ? w : 'clear'); }
  function setWeatherFn(fn) { weatherFn = typeof fn === 'function' ? fn : null; }
  function setRainFn(fn) { weatherFn = typeof fn === 'function' ? () => (fn() ? 'rain' : 'clear') : null; }   // 舊介面（true＝落雨）
  function weatherNow() { return normWeather(weatherFn ? weatherFn() : 'clear'); }
  function isRaining() { return weatherNow() === 'rain'; }
  // v4 照顧日（燦光要連續照顧）：s.careDays＝有照顧嘅本機日（YYYY-MM-DD，跨世代保留，最多 60 個）；時間可注入（Node 測試／sim）
  let nowFn = null;
  function setNowFn(fn) { nowFn = typeof fn === 'function' ? fn : null; }
  function nowMs() { return nowFn ? nowFn() : Date.now(); }
  function noteDay(s) { const k = dayKey(nowMs()), a = Array.isArray(s.careDays) ? s.careDays : (s.careDays = []); if (!a.includes(k)) { a.push(k); a.sort(); if (a.length > 60) a.splice(0, a.length - 60); } const E = evoOf(s); if (!E.day0) E.day0 = k; }
  function careDaysCheck(s) {                            // 最近 window 日（包括今日）有幾多日有照顧；scaleToAge → 由呢隻出世（day0）計起
    const C = BR().brightDays, E = evoOf(s), now = nowMs(), keys = [];
    for (let i = 0; i < C.window; i++) { const k = dayKey(now - i * 86400000); keys.push(k); if (C.scaleToAge && E.day0 && k <= E.day0) break; }
    const have = new Set(Array.isArray(s.careDays) ? s.careDays : []), n = keys.filter(k => have.has(k)).length;
    const need = C.scaleToAge ? Math.ceil(C.min * keys.length / C.window) : C.min;
    return { days: n, span: keys.length, need, ok: n >= need };
  }
  const BR = () => EV6.branch;                          // §7 判定 config（data.js PARAMS.evo6.branch）
  function inWindow(w, h) { return w.from <= w.to ? h >= w.from && h < w.to : h >= w.from || h < w.to; }
  function careWindow(h) { return BR().windows.find(w => inWindow(w, h)) || null; }   // 時段規則（21–03 月眠、06–09 水珠…）
  function isMoonHour(h) { const w = BR().windows.find(x => x.id === 'moon'); return !!w && inWindow(w, h); }
  // §7 新支線分數：每次照顧 all +1；本身類型照計；v4：陰天／落雨時任何照顧再計菇傘（config weather.route；feed 本身已歸菇傘 → 只計一次）；時段規則（config windows）：21–03 只計月眠、06–09 只計水珠；瞓覺撫摸只計月眠
  const B5_KIND = { feed: 'shroom', play: 'ember', mg: 'ember', rinse: 'tide', poop: 'crystal' };
  function noteB5(s, kind, h, wx) {
    if (s.stage === 'egg') return; const E = evoOf(s), b = E.b5[s.stage] || (E.b5[s.stage] = { all: 0, tide: 0, shroom: 0, crystal: 0, moon: 0, ember: 0 });
    h = h == null ? nowHour() : h; wx = wx == null ? weatherNow() : normWeather(wx === false ? 'clear' : wx);
    b.all++;
    if (kind === 'petSleep') { b.moon++; return; }          // 瞓覺撫摸 → 月眠
    const w = careWindow(h); if (w) { b[w.only]++; return; }   // §7 修訂／v2：時段內只計嗰條（21–03 月眠、06–09 水珠），唔計本身類型／落雨
    const own = B5_KIND[kind]; if (own) b[own]++;
    const wr = BR().weather.route[wx]; if (wr && wr !== own) b[wr]++;   // v4：陰天／落雨 → 菇傘（唔再計水珠）
  }
  // 照顧（餵／玩／沖洗／清便便／接星屑）：記入當前階段 care.all，夜晚（17:00–07:00）再記 care.night；kind＝feed／play／rinse／poop／mg（§7 分數）
  function noteCare(s, h, kind, rain) {
    if (s.stage === 'egg') return; const E = evoOf(s), c = E.care[s.stage] || (E.care[s.stage] = { all: 0, night: 0 });
    c.all++; if (isNightHour(h == null ? nowHour() : h)) c.night++;
    noteB5(s, kind, h, rain); noteDay(s);
    cqCare(s);
  }
  // §7 月眠：瞓緊覺時撫摸（點寵物＝輕喚醒，所以每次瞓覺最多一次）；只入 §7 分數，唔改螢絨嘅夜晚照顧比例
  function notePetSleep(s, h, rain) { if (!s || s.stage === 'egg' || !s.sleeping) return false; noteB5(s, 'petSleep', h, rain); noteDay(s); return true; }
  function noteClean(s, dt) {                            // 晶角：清潔度時間加權平均（每階段）
    if (s.stage === 'egg' || !(dt > 0)) return; const E = evoOf(s), c = E.cl[s.stage] || (E.cl[s.stage] = { sum: 0, sec: 0 });
    c.sum += s.needs.clean * dt; c.sec += dt;
  }
  function branch5Check(s) {                             // §7：CQ ≥ b5CQ、最高分 ≥ b5TopPct%；v3：同第二名差 < drawGapPt → 兩者比例抽；唔夠 → null（config）
    const C = BR();
    const E = evoOf(s), T = { all: 0, tide: 0, shroom: 0, crystal: 0, moon: 0, ember: 0 }; let cs = 0, cn = 0;
    EV6.careStages.forEach(st => { const b = E.b5[st]; if (b) for (const k in T) T[k] += +b[k] || 0; const c = E.cl[st]; if (c) { cs += c.sum; cn += c.sec; } });
    const cleanAvg = cn > 0 ? cs / cn : null, crystalOk = cleanAvg != null && cleanAvg >= C.crystalCleanAvg;
    const score = { tide: T.tide, shroom: T.shroom, crystal: crystalOk ? T.crystal : 0, moon: T.moon, ember: T.ember };
    const rank = D.BRANCH5.map(id => ({ id, n: score[id], share: T.all ? score[id] / T.all : 0 })).sort((a, b) => b.n - a.n || D.BRANCH5.indexOf(a.id) - D.BRANCH5.indexOf(b.id));
    const top = rank[0], second = rank[1], N = T.all;
    const r = { all: N, score, raw: { crystal: T.crystal }, cleanAvg: cleanAvg == null ? null : +cleanAvg.toFixed(1), crystalOk, cq: s.cq, cqOk: s.cq >= C.b5CQ,
      top: top.id, topN: top.n, topShare: +top.share.toFixed(4), second: second.id, secondShare: +second.share.toFixed(4),
      topOk: N > 0 && top.n * 100 >= C.b5TopPct * N, gapOk: N > 0 && (top.n - second.n) * 100 >= C.drawGapPt * N, tie: top.n === second.n,
      brightTopOk: !(N > 0 && top.n * 100 >= C.brightMaxTopPct * N) };
    // v3：差 ≥ drawGapPt → 最高分贏；差 < drawGapPt（包括平手）→ 按兩者分數比例抽（seed）
    r.draw = null; let pick = top.id;
    if (N > 0 && !r.gapOk && top.n + second.n > 0) { const u = branchRoll(s, 'b5draw'), pTop = top.n / (top.n + second.n); pick = u < pTop ? top.id : second.id; r.draw = { a: top.id, b: second.id, pTop: +pTop.toFixed(4), roll: +u.toFixed(4) }; }
    r.ok = r.cqOk && r.topOk; r.form = r.ok ? pick : null; return r;
  }
  function noteEvent(s, id) { if (!s || s.stage === 'egg') return; const E = evoOf(s), m = E.evIn[s.stage] || (E.evIn[s.stage] = {}); m[id] = (m[id] || 0) + 1; }   // events.js trigger 掛
  function careShare(s) {                                // 夜晚照顧佔比（careStages＝芽崽＋跳跳期）
    const E = evoOf(s); let all = 0, night = 0; EV6.careStages.forEach(st => { const c = E.care[st]; if (c) { all += c.all; night += c.night; } });
    return { all, night, share: all ? night / all : 0 };
  }
  // v3：判定用嘅隨機數（seed 決定，同一隻寵物同一個 tag 永遠一樣 → 測試／重開一致；測試可 setBranchRoll 注入）
  let rollFn = null;
  function setBranchRoll(fn) { rollFn = typeof fn === 'function' ? fn : null; }
  function branchRoll(s, tag) {
    if (rollFn) { const v = rollFn(tag, s); if (v != null) return v; }   // 注入嘅回 null → 用返 seed
    let h = 2166136261; const k = tag + ':' + (s.seed >>> 0) + ':' + (s.gen || 1); for (let i = 0; i < k.length; i++) h = Math.imul(h ^ k.charCodeAt(i), 16777619);
    return makeRng(h >>> 0)();
  }
  function lumiCheck(s) {                                // v3 螢絨：機率（firefly_walk 資格；夜晚佔比 30→50% ⇒ 0→25%；CQ < 40 冇）
    const E = evoOf(s), LC = BR().lumi, ev = EV6.lumiEvStages.reduce((a, st) => a + ((E.evIn[st] && E.evIn[st][EV6.lumiEvent]) || 0), 0), cs = careShare(s);
    const r = { firefly: ev, fireflyOk: ev > 0, cq: s.cq, cqOk: s.cq >= LC.minCQ, night: +cs.share.toFixed(3), nightAll: cs.all };
    const t = cs.all > 0 ? clamp((cs.share * 100 - LC.fromPct) / (LC.toPct - LC.fromPct), 0, 1) : 0;
    r.chance = r.fireflyOk && r.cqOk ? +(t * LC.maxChancePct / 100).toFixed(4) : 0; r.nightOk = r.chance > 0;
    r.roll = +branchRoll(s, 'lumi').toFixed(4); r.ok = r.chance > 0 && r.roll < r.chance; return r;
  }
  function decideBranch(s) {                             // 次序（§7 修訂）：DEV 強制 → 螢絨 → 燦光（CQ ≥ brightCQ 且最高分 < brightMaxTopPct%）→ 新 5 條 → 柔光（CQ ≥ softCQ）→ 微塵（數值見 config）
    const E = evoOf(s), L = lumiCheck(s), B = branch5Check(s);
    if (E.force && D.BRANCHES.includes(E.force)) return { form: E.force, why: 'dev', lumi: L, b5: B };
    if (L.ok) return { form: 'lumi', why: 'lumi', lumi: L, b5: B };
    return Object.assign(openBranch(s, B), { lumi: L });
  }
  function openBranch(s, B) {                            // 螢絨以外嘅判定（燦光 → 新 5 條 → 柔光 → 微塵）
    const C = BR();                                      // §7 修訂：燦光（全面照顧＝最高分 < 上限）先過新 5 條；專注某類就去新支線
    const days = careDaysCheck(s); B.days = days;           // v4：燦光要連續照顧（最近 7 日 ≥5 日）
    if (s.cq >= C.brightCQ && days.ok && B.brightTopOk) return { form: 'bright', why: 'cq', b5: B };
    if (B.ok) return { form: B.form, why: 'b5', b5: B };
    return { form: s.cq >= C.softCQ ? 'soft' : 'dust', why: 'cq', b5: B };   // 照次序：燦光／新 5 條都唔成立 → 柔光（CQ ≥ softCQ）→ 微塵
  }
  // §7 路線清晰化：而家「領先」嘅路線（用而家嘅 CQ＋分數試判；螢絨隱藏 → 永遠唔返 lumi；DEV 強制都唔洩露）
  function routeLead(s) { const r = openBranch(s, branch5Check(s)); return { form: r.form, why: r.why, b5: r.b5 }; }
  function routeBulb(s) {                                // 燈泡路線色：{ form, color, mix }（唔係跳跳期／config 冇 → null）
    const R = EV6.route; if (!R || s.stage !== R.bulbStage) return null;
    const L = routeLead(s), col = R.colors[L.form]; if (!col) return null;
    const ramp = R.bulbRampProgress > 0 ? clamp(stageProgress(s) / R.bulbRampProgress, 0, 1) : 1;
    return { form: L.form, color: col, mix: +(R.bulbMaxMix * ramp).toFixed(4) };
  }
  function checkForeshadow(s) {                          // 判定前 foreshadowLeadSec 做一次預告（每隻跳跳期一次）
    const R = EV6.route, sec = P.stageSec.juvenile; if (!R || s.stage !== 'juvenile' || !sec) return;
    const E = evoOf(s); if (E.fore) return;
    if (s.growthSec >= sec - R.foreshadowLeadSec && s.growthSec < sec) {
      const L = routeLead(s); E.fore = { form: L.form, at: Math.round(s.growthSec) }; s.ev.push({ type: 'foreshadow', form: L.form, act: R.foreshadow[L.form] || null });
    }
  }
  function dexList(s) {                                  // 圖鑑：9 條支線，解鎖＝曾經成為守夜者（s.dex）
    const got = new Set(s.dex || []); return D.BRANCHES.map(id => ({ id, unlocked: got.has(id), name: got.has(id) ? D.FORM_NAME[id] : '？？？', hint: D.ROUTE_HINT[id] || '' }));
  }
  function unlockDex(s, f) { if (!D.BRANCHES.includes(f)) return false; s.dex = Array.isArray(s.dex) ? s.dex : []; if (s.dex.includes(f)) return false; s.dex.push(f); return true; }
  function enterStage(s, st) {
    s.stage = st;
    if (st === 'newborn') { evoOf(s).day0 = dayKey(nowMs()); s.form = null; s.needs = Object.assign({}, P.startNeedsSprout); s.cq = P.cqStart; s.cqTimer = 0; s.stats.hatches++; s.ev.push({ type: 'hatch' }); return; }
    if (st === 'sprout' || st === 'juvenile') { s.ev.push({ type: 'grow', stage: st, cq: s.cq }); return; }
    if (st === 'adult') { const d = decideBranch(s); s.form = d.form; delete evoOf(s).force; unlockDex(s, s.form); s.ev.push({ type: 'evolve', form: s.form, cq: s.cq, why: d.why, lumi: d.lumi, b5: d.b5 }); s.cq = P.cqStart; s.cqTimer = 0; return; }
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

  function settleCQ(s) {                                 // 每個鐘結算（v3：部分照顧按比例加；扣分唔會跌穿 floor）
    const Q = BR().cq, avg = (s.needs.hunger + s.needs.mood + s.needs.clean + s.needs.energy) / 4, c0 = s.cq;
    if (avg >= P.cqGoodAt) s.cq += 1;
    else if (avg >= P.cqBadBelow) s.cq += Q.partialMax * (avg - P.cqBadBelow) / (P.cqGoodAt - P.cqBadBelow);
    else s.cq -= 1;
    if (isUnwell(s)) s.cq -= P.cqSickPenalty;
    if (s.cq < c0) s.cq = Math.max(s.cq, Math.min(c0, Q.floor));
    s.cq = clamp(Math.round(s.cq * 1e4) / 1e4, P.cqMin, P.cqMax); s.cqCareH = 0;
  }
  function cqCare(s) {                                   // v3：每次照顧都計分（每個鐘上限）＋重置「冇理」計時
    const Q = BR().cq; s.cqIdleSec = 0; if (s.stage === 'egg') return;
    const g = Math.min(Q.careGain, Math.max(0, Q.careGainPerHourMax - (s.cqCareH || 0))); s.cqCareH = (s.cqCareH || 0) + g; s.cq = clamp(s.cq + g, P.cqMin, P.cqMax);
  }
  function cqDecay(s, dt) {                              // v3：連續 decayAfterH 個鐘冇照顧 → 慢慢跌（線上＋離線），唔跌穿 floor
    const Q = BR().cq, before = s.cqIdleSec || 0, after = before + dt; s.cqIdleSec = after;
    const over = Math.max(0, after - Math.max(before, Q.decayAfterH * 3600)); if (!(over > 0) || s.cq <= Q.floor) return;
    s.cq = Math.max(Q.floor, s.cq - Q.decayPerH * over / 3600);
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
    noteClean(s, dt);
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
    if (s.stage !== 'egg') cqDecay(s, dt);
    checkForeshadow(s);

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
    s.stats.feeds++; noteFed(s); noteCare(s, null, 'feed');
    s.ev.push({ type: 'fed', food: f.id });
    return { ok: true, food: f };
  }
  function play(s) {
    if (s.stage === 'egg') return { ok: false, reason: 'egg' };
    if (s.sleeping) return { ok: false, reason: 'sleeping' };
    s.needs.mood = clamp(s.needs.mood + P.playTease, 0, 100);
    s.needs.energy = clamp(s.needs.energy - P.playEnergyCost, 0, 100);
    s.stats.plays++; notePlayed(s); noteCare(s, null, 'play');
    s.ev.push({ type: 'played' });
    return { ok: true };
  }
  function rinse(s) {
    if (s.stage === 'egg') return { ok: false, reason: 'egg' };
    if (s.sleeping) return { ok: false, reason: 'sleeping' };
    s.needs.clean = clamp(s.needs.clean + P.rinse, 0, 100);
    s.stats.rinses++; noteCare(s, null, 'rinse');
    s.ev.push({ type: 'rinsed' });
    return { ok: true };
  }
  function clearPoop(s) {
    if (s.poops <= 0) return { ok: false };
    s.poops--; s.stats.poopsCleared++; noteCare(s, null, 'poop');
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
    s.stats.mgPlays++; notePlayed(s); noteCare(s, null, 'mg');
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
      if ((s.stage === 'adult' || s.stage === 'elder') && !D.BRANCHES.includes(s.form)) s.form = s.form === 'radiant' ? 'bright' : 'dust';
      evoOf(s); s.memorial = Array.isArray(s.memorial) ? s.memorial : []; s.gen = +s.gen || 1;
      s.careDays = Array.isArray(s.careDays) ? s.careDays.filter(k => typeof k === 'string' && /^\d{4}-\d\d-\d\d$/.test(k)).sort().slice(-60) : [];   // v4 照顧日
      s.dex = Array.isArray(s.dex) ? s.dex.filter(f => D.BRANCHES.includes(f)) : []; s.memorial.forEach(m => unlockDex(s, m.form)); if (s.stage === 'adult' || s.stage === 'elder') unlockDex(s, s.form);   // 圖鑑：舊存檔由紀念＋而家形態補返
      return s;
    } catch (e) { return null; }
  }

  return {
    makeRng, newState, effectiveOffline, isUnwell, lowestNeed, needBand, decideForm, overlayStatus,
    step, advance, applyOffline, offlineGrow, addStepHook, addOfflineHook, hourOf, fmtDur, feed, play, rinse, clearPoop, toggleSleep, tapEgg,
    eggProgress, stageProgress, dayKey, STAGES, nextStage, enterStage, checkStage, decideBranch, lumiCheck, branch5Check, notePetSleep, noteClean, setRainFn, isRaining, isMoonHour, careWindow, inWindow, routeLead, routeBulb, checkForeshadow, setWeatherFn, weatherNow, setNowFn, careDaysCheck, noteDay, setBranchRoll, branchRoll, cqCare, cqDecay, dexList, unlockDex, careShare, noteCare, noteEvent, isNightHour, setHourFn, fade, migrate, Minigame, mgReward, mgApply, serialize, deserialize, sanitizeSaveTime, settleCQ,
  };
});
