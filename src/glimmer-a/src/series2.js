/* 《微光小圃》 series2.js — 第 4 批 4a（docs-gdd/series2-4a4b-spec.md v1.1 §4a）：細佬（新蛋系列 48px）＋關係＋孵夢＋教錯課。原創代碼。
   DOM-free、Node 可 require（純邏輯）：存檔 s.pet2（sanitize；唔郁團絨資料）、攞蛋（團絨首次靜光 → 翌日蝸牛郵差）、時間線（蛋 3 晚 → S1 1 日 → S2 2 日 → S3／S4／S5 各 3 日 → S6）、
   孵夢（每晚當日最多照顧類型 → 8 系 +1，最多 3 分）、教錯課（S1–S2，每日 2 堂、最多 6 堂，每堂 +1）、S3 結算（最高／打和最近一堂／冇堂最近一夢／乜都冇隨機）、
   親密度（每日上限 10：哄喊 +2、一齊食 +1、教錯課 +2、一齊瞓 +2 每晚 1 次、雙人彈彈葉 +2 每日 2 局）、關係級（跟班 → 朋友 30 → 家人 80＋S6）、雙人 clip／升級小場面時間軸數學。
   唔經 sim.noteCare、唔加路線分、唔出碎、唔食小遊戲額 → §7 平衡唔郁；細佬冇肚餓／便便；永遠最多 1 隻；浮動只顯示團絨（呢度唔掂 overlay）。 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory(require('./data.js'));
  else { root.Glimmer = root.Glimmer || {}; root.Glimmer.series2 = factory(root.Glimmer.data); }
})(typeof self !== 'undefined' ? self : this, function (D) {
  'use strict';
  const clamp = (v, a, b) => v < a ? a : v > b ? b : v;
  const obj = (o) => o && typeof o === 'object' && !Array.isArray(o);
  const DAY = 86400000;
  const dayNum = (ms) => { const d = new Date(ms); return Math.round(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()) / DAY); };
  const dayKey = (ms) => { const d = new Date(ms); return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0'); };
  const hourOf = (ms) => { const d = new Date(ms); return d.getHours() + d.getMinutes() / 60; };
  const inPlace = (a, b) => { if (a.length !== b.length || a.some((x, i) => x !== b[i])) { a.length = 0; for (const x of b) a.push(x); } return a; };
  const hash = (str) => { let h = 2166136261 >>> 0; for (let i = 0; i < str.length; i++) { h ^= str.charCodeAt(i); h = Math.imul(h, 16777619) >>> 0; } return h >>> 0; };

  const LINES = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'];
  const LINE_ZH = { A: '潮', B: '螢', C: '火', D: '晶', E: '辣', F: '陽', G: '月', H: '塵' };
  const PROP = { A: 'prop_can', B: 'prop_wand', C: 'prop_match', D: 'prop_pebble', E: 'prop_chili', F: 'prop_scope', G: 'prop_book', H: 'prop_moonlamp' };
  const PROP_ZH = { A: '水壺', B: '泡泡棒', C: '火柴', D: '石仔', E: '辣椒', F: '望遠鏡', G: '書', H: '月亮燈' };
  const WRONG = { A: '水壺淋自己個頭', B: '自己入咗泡泡，浮起再跌', C: '用個頭擦火柴，冒煙', D: '坐喺石仔上面孵', E: '當士多啤梨咁食辣椒，噴火', F: '望遠鏡拎倒轉，撞嘢暈', G: '本書拎倒轉讀，讀到瞓著', H: '月亮燈當帽戴，跌落遮住眼' };
  const CARE_ZH = { A: '淋花／飲水', B: '沖涼／吹泡泡', C: '取暖／點燈', D: '執石仔／砌嘢', E: '食嘢（辣）', F: '睇星', G: '講故仔', H: '開夜燈陪瞓' };
  const STAGES = ['egg', 'S1', 'S2', 'S3', 'S4', 'S5', 'S6'];
  const STAGE_ZH = { egg: '細佬蛋', S1: '蛋殼仔', S2: 'BB', S3: '初現', S4: '少年', S5: '成長', S6: '成年' };
  const REL = ['none', 'follow', 'friend', 'family'];
  const REL_ZH = { none: '—', follow: '跟班', friend: '朋友', family: '家人' };

  /* 遊策可調（PARAMS.series2 覆寫） */
  const CFG0 = {
    eggNights: 3,                                       // 蛋 3 晚（孵夢）
    stageDays: { S1: 1, S2: 2, S3: 3, S4: 3, S5: 3 },     // 由孵化日起計；S6 之後一直
    dreamFrom: 21, dreamCatchup: 6,                     // 21:00 後團絨瞓 → 即時發夢；翌日 06:00 未發 → 補記（當日照顧）
    sleepTogether: [21, 3],                             // 一齊瞓窗口（跨午夜）
    lessonsPerDay: 2, lessonsMax: 6, dreamMax: 3,
    intimacyCap: 10, gain: { comfort: 2, eat: 1, lesson: 2, sleep: 2, duo: 2 },
    friendAt: 30, familyAt: 80, duoPerDay: 2,
    cry: { perDay: [2, 3], firstDelaySec: [60, 180], gapSec: [900, 2400], timeoutSec: 600, hours: [7, 21] },
    // 照顧類型 → 8 系（夢泡泡 CARE_ZH）：A 淋花、B 沖涼／清便便、C 長撳挨挨（取暖）、D 散步收集、E 餵食、F 小遊戲（睇星）、G 逗玩／摸頭（講故仔）、H 關燈／哄瞓
    care: { water: 'A', rinse: 'B', poop: 'B', hold: 'C', walk: 'D', feed: 'E', mg: 'F', play: 'G', pat: 'G', sleep: 'H', lull: 'H' },
    deliverDelaySec: 6, careKeepDays: 6, logMax: 40,
  };
  const CFG = JSON.parse(JSON.stringify(CFG0));
  { const P = D && D.PARAMS && D.PARAMS.series2; if (P && obj(P.cfg)) for (const k in P.cfg) CFG[k] = obj(P.cfg[k]) && obj(CFG[k]) ? Object.assign({}, CFG[k], P.cfg[k]) : P.cfg[k]; }

  const LINES_OUT = {
    deliver: '蝸牛郵差：「有團絨嘅包裹！」…係一隻細細嘅蛋。', deliverToast: '收到一隻細佬蛋！夜晚團絨會攬住佢瞓',
    dream: '團絨夢見「{care}」…蛋暖咗少少', noDream: '團絨今晚瞓得好熟，冇發夢',
    hatch: '細佬出世喇！第一眼就見到團絨', lessonDone: '細佬學識咗（錯嘅）{prop}！', lessonFull: '今日教夠喇，聽日再教', lessonDone6: '細佬已經學滿 6 堂',
    lessonNot: '而家唔係上堂時間', cry: '細佬喊喊…拖團絨過去哄下佢', comfort: '團絨挨住細佬，細佬收聲喇', cryStop: '細佬自己收咗聲',
    eat: '細佬都一齊食！', sleep: '兩隻一齊瞓…', capFull: '今日親密度滿咗（10）',
    reveal: '細佬變咗「{zh}系」！', lvFriend: '細佬同團絨做咗朋友！可以玩雙人彈彈葉', lvFamily: '細佬同團絨成為家人！一齊搬入屋仔', lvFollow: '細佬會跟住團絨周圍行',
    duoDone: '雙人彈彈葉：細佬好開心（親密 +{n}）', duoFull: '今日雙人彈彈葉玩夠 2 局',
  };

  /* ── 存檔 s.pet2 ── */
  function st(s) {
    let o = s.pet2; if (!obj(o)) o = s.pet2 = {};
    o.v = 1;
    if (!['none', 'due', 'egg', 'kid'].includes(o.phase)) o.phase = 'none';
    o.elderAt = +o.elderAt || 0; o.dueDay = o.dueDay | 0; o.gotAt = +o.gotAt || 0; o.d0 = o.d0 | 0;
    if (o.phase !== 'none' && !o.elderAt) o.elderAt = o.gotAt || 1;
    if ((o.phase === 'egg' || o.phase === 'kid') && !o.d0) o.d0 = o.gotAt ? dayNum(o.gotAt) : 0;
    if (!Array.isArray(o.dreams)) o.dreams = [];
    inPlace(o.dreams, o.dreams.filter(x => obj(x) && Number.isFinite(+x.day)).slice(0, CFG.eggNights)); for (const x of o.dreams) { x.day |= 0; if (!LINES.includes(x.line)) x.line = null; x.at = +x.at || 0; x.live = !!x.live; }
    if (!Array.isArray(o.lessons)) o.lessons = [];
    inPlace(o.lessons, o.lessons.filter(x => obj(x) && LINES.includes(x.line)).slice(0, CFG.lessonsMax)); for (const x of o.lessons) { x.day |= 0; x.at = +x.at || 0; x.stage = x.stage === 'S2' ? 'S2' : 'S1'; }
    o.hatchAt = +o.hatchAt || 0; o.hatchDay = o.hatchDay | 0; if (o.phase === 'kid' && !o.hatchDay) o.hatchDay = o.hatchAt ? dayNum(o.hatchAt) : o.d0 + CFG.eggNights;
    if (o.line != null && !LINES.includes(o.line)) o.line = null; if (o.line === undefined) o.line = null;
    if (o.settle != null && !obj(o.settle)) o.settle = null; if (o.settle === undefined) o.settle = null;
    o.intim = clamp(+o.intim || 0, 0, 9999);
    if (!REL.includes(o.rel)) o.rel = o.phase === 'kid' ? 'follow' : 'none';
    if (!Array.isArray(o.relQ)) o.relQ = []; inPlace(o.relQ, o.relQ.filter(r => REL.includes(r) && r !== 'none').slice(-3));
    if (!obj(o.day)) o.day = {}; const d = o.day; if (typeof d.k !== 'string') d.k = '';
    for (const k of ['n', 'lessons', 'duo', 'cries', 'comforts', 'eat']) d[k] = Math.max(0, d[k] | 0);
    d.cryPlan = clamp(d.cryPlan | 0, 0, 5);
    if (!obj(o.care)) o.care = {}; for (const k of Object.keys(o.care)) { const c = o.care[k]; if (!obj(c) || !/^\d+$/.test(k)) { delete o.care[k]; continue; } for (const L of Object.keys(c)) if (!LINES.includes(L) && L !== '_last') delete c[L]; else if (L !== '_last') c[L] = Math.max(0, c[L] | 0); if (!obj(c._last)) c._last = {}; }
    o.sleepNight = o.sleepNight | 0;
    if (o.stageSeen != null && !STAGES.includes(o.stageSeen)) o.stageSeen = null; if (o.stageSeen === undefined) o.stageSeen = null;
    if (!Array.isArray(o.log)) o.log = []; inPlace(o.log, o.log.filter(x => obj(x) && typeof x.k === 'string').slice(-CFG.logMax));
    if (!obj(o.stats)) o.stats = {}; for (const k of ['comfort', 'eat', 'sleep', 'duo', 'lesson', 'cries', 'cryTimeout', 'capHit']) o.stats[k] = Math.max(0, o.stats[k] | 0);
    return o;
  }
  const note = (o, k, x, now) => { o.log.push(Object.assign({ k, at: now || 0 }, x || {})); if (o.log.length > CFG.logMax) o.log.splice(0, o.log.length - CFG.logMax); };

  /* ── 攞蛋 ── */
  function noteElder(s, now) {                // 團絨首次到靜光 → 翌日送蛋（每個存檔一次；永遠最多 1 隻）
    const o = st(s); if (o.phase !== 'none' || s.stage !== 'elder' || (s.fam && s.fam.km)) return false;   // 5a.1：細佬做主養 → pet2 空位等 5a 新蛋（唔再郵差送）
    o.elderAt = now; o.dueDay = dayNum(now) + 1; o.phase = 'due'; note(o, 'elder', { day: o.dueDay }, now); return true;
  }
  const canDeliver = (s, now) => { const o = st(s); return o.phase === 'due' && dayNum(now) >= o.dueDay; };
  function deliver(s, now) {
    const o = st(s); if (o.phase !== 'due') return { ok: false, reason: o.phase === 'none' ? 'notDue' : 'have' };
    o.phase = 'egg'; o.gotAt = now; o.d0 = dayNum(now); note(o, 'egg', {}, now); return { ok: true };
  }

  /* ── 照顧記錄（只用嚟揀夢；唔入 sim.noteCare）── */
  function careNote(s, kind, now) {
    const o = st(s), L = CFG.care[kind]; if (!L || o.phase === 'none' || o.phase === 'kid') return null;
    const k = String(dayNum(now)); const c = o.care[k] || (o.care[k] = { _last: {} }); c[L] = (c[L] | 0) + 1; c._last[L] = now;
    const ks = Object.keys(o.care).map(Number).sort((a, b) => a - b); while (ks.length > CFG.careKeepDays) delete o.care[String(ks.shift())];
    return L;
  }
  function topCare(s, day) {                  // 當日最多嘅照顧系；打和揀最近；冇 → null
    const c = st(s).care[String(day)]; if (!c) return null; let best = null, bn = 0, bt = -1;
    for (const L of LINES) { const n = c[L] | 0, t = (c._last && c._last[L]) || 0; if (n > bn || (n === bn && n > 0 && t > bt)) { best = L; bn = n; bt = t; } }
    return best;
  }

  /* ── 孵夢 ── */
  const eggNights = (o) => Array.from({ length: CFG.eggNights }, (_, i) => o.d0 + i);
  const nightOf = (now) => { const h = hourOf(now), dn = dayNum(now); return h < 12 ? dn - 1 : dn; };   // 凌晨＝前一晚
  function dreamDue(s, now, sleeping) {        // 回傳要記嘅夜（日號）陣列：live（而家 21:00 後瞓緊）＋補記（過咗翌日 06:00）
    const o = st(s); if (o.phase !== 'egg') return []; const have = new Set(o.dreams.map(d => d.day)), out = [], dn = dayNum(now), h = hourOf(now);
    for (const n of eggNights(o)) {
      if (have.has(n)) continue;
      const past = dn > n + 1 || (dn === n + 1 && h >= CFG.dreamCatchup);
      const live = sleeping && nightOf(now) === n && (dn === n ? h >= CFG.dreamFrom : h < CFG.dreamCatchup);
      if (past || live) out.push({ day: n, live: !!live && !past });
    }
    return out;
  }
  function dream(s, day, now, live) {
    const o = st(s); if (o.phase !== 'egg' || o.dreams.some(d => d.day === day) || o.dreams.length >= CFG.dreamMax) return null;
    const line = topCare(s, day), d = { day, line, at: now, live: !!live }; o.dreams.push(d); o.dreams.sort((a, b) => a.day - b.day);
    note(o, 'dream', { line }, now); return d;
  }
  const hatchReady = (s, now) => { const o = st(s); return o.phase === 'egg' && o.dreams.length >= CFG.eggNights && dayNum(now) >= o.d0 + CFG.eggNights; };
  function hatch(s, now) {
    const o = st(s); if (o.phase !== 'egg') return { ok: false, reason: 'phase' };
    o.phase = 'kid'; o.hatchAt = now; o.hatchDay = dayNum(now); o.rel = 'follow'; o.relQ.push('follow'); o.stageSeen = 'S1'; note(o, 'hatch', {}, now); return { ok: true };
  }

  /* ── 時間線 ── */
  function stageOf(s, now) {
    const o = st(s); if (o.phase === 'none' || o.phase === 'due') return null; if (o.phase === 'egg') return 'egg';
    const dd = dayNum(now) - o.hatchDay, SD = CFG.stageDays; let acc = 0;
    for (const k of ['S1', 'S2', 'S3', 'S4', 'S5']) { acc += SD[k]; if (dd < acc) return k; }
    return 'S6';
  }
  const stageIdx = (k) => STAGES.indexOf(k);
  function formOf(s, now) {                    // 美術 key：S1／S2／A1（S3）／S4A（S4）／A2（S5）／A3（S6）；系未定（理論上唔會）→ S2
    const o = st(s), sk = stageOf(s, now); if (!sk) return null; if (sk === 'egg') return 'egg'; if (sk === 'S1' || sk === 'S2') return sk;
    const L = o.line; if (!L) return 'S2';
    return sk === 'S3' ? L + '1' : sk === 'S4' ? 'S4' + L : sk === 'S5' ? L + '2' : L + '3';
  }
  function settle(s, now, rnd) {               // S3 結算（一次）：夢分＋堂分；打和 → 最近一堂；冇堂 → 最近一夢；乜都冇 → 隨機
    const o = st(s); if (o.line) return o.settle; const r = settlePick(o.dreams, o.lessons, rnd || Math.random);
    o.line = r.line; o.settle = { how: r.how, pts: r.pts, at: now }; note(o, 'reveal', { line: r.line, how: r.how }, now); return o.settle;
  }
  function settlePick(dreams, lessons, rnd) {
    const pts = {}; for (const L of LINES) pts[L] = 0;
    for (const d of dreams) if (d.line) pts[d.line]++; for (const l of lessons) pts[l.line]++;
    const max = Math.max(...LINES.map(L => pts[L]));
    if (max <= 0) return { line: LINES[Math.floor(clamp(rnd(), 0, 0.9999) * LINES.length)], how: 'random', pts };
    const tied = LINES.filter(L => pts[L] === max); if (tied.length === 1) return { line: tied[0], how: 'max', pts };
    for (let i = lessons.length - 1; i >= 0; i--) if (tied.includes(lessons[i].line)) return { line: lessons[i].line, how: 'tieLesson', pts };
    const ds = dreams.filter(d => d.line).slice().sort((a, b) => a.day - b.day || a.at - b.at);
    for (let i = ds.length - 1; i >= 0; i--) if (tied.includes(ds[i].line)) return { line: ds[i].line, how: 'tieDream', pts };
    return { line: tied[Math.floor(clamp(rnd(), 0, 0.9999) * tied.length)], how: 'random', pts };
  }

  /* ── 每日（親密度上限／課／局／喊）── */
  function today(s, now) {
    const o = st(s), k = dayKey(now), d = o.day;
    if (d.k !== k) { o.day = { k, n: 0, lessons: 0, duo: 0, cries: 0, comforts: 0, eat: 0, cryPlan: CFG.cry.perDay[0] + (hash(k + ':' + (o.hatchDay | 0)) % (CFG.cry.perDay[1] - CFG.cry.perDay[0] + 1)) }; }
    return o.day;
  }
  function gain(s, kind, now) {                // 回傳 {n, level}；n＝實際加咗幾多（每日上限 10）
    const o = st(s); if (o.phase !== 'kid') return { n: 0, level: null, reason: 'phase' }; const d = today(s, now), want = CFG.gain[kind] | 0;
    const n = Math.max(0, Math.min(want, CFG.intimacyCap - d.n)); if (want && !n) o.stats.capHit++;
    o.intim += n; d.n += n; if (o.stats[kind] != null) o.stats[kind]++;
    return { n, level: checkLevel(s, now), reason: n ? null : 'cap' };
  }
  function checkLevel(s, now) {                // 跟班 → 朋友（30）→ 家人（80＋S6；S6 未夠 80 停喺朋友）
    const o = st(s); if (o.phase !== 'kid') return null; let up = null;
    if (o.rel === 'follow' && o.intim >= CFG.friendAt) { o.rel = 'friend'; up = 'friend'; o.relQ.push('friend'); note(o, 'rel', { rel: 'friend' }, now); }
    if (o.rel === 'friend' && o.intim >= CFG.familyAt && stageOf(s, now) === 'S6') { o.rel = 'family'; up = 'family'; o.relQ.push('family'); note(o, 'rel', { rel: 'family' }, now); }
    return up;
  }
  function canLesson(s, now) {
    const o = st(s); if (o.phase !== 'kid') return { ok: false, reason: 'phase' }; const sk = stageOf(s, now);
    if (sk !== 'S1' && sk !== 'S2') return { ok: false, reason: 'stage' };
    if (o.lessons.length >= CFG.lessonsMax) return { ok: false, reason: 'max' };
    if (today(s, now).lessons >= CFG.lessonsPerDay) return { ok: false, reason: 'today' };
    if (s.stage === 'egg') return { ok: false, reason: 'trEgg' }; if (s.sleeping) return { ok: false, reason: 'sleep' };
    return { ok: true, left: CFG.lessonsPerDay - today(s, now).lessons };
  }
  function lesson(s, line, now) {
    const c = canLesson(s, now); if (!c.ok) return Object.assign({ ok: false }, c); if (!LINES.includes(line)) return { ok: false, reason: 'line' };
    const o = st(s); o.lessons.push({ line, day: dayNum(now), at: now, stage: stageOf(s, now) }); today(s, now).lessons++; note(o, 'lesson', { line }, now);
    return Object.assign({ ok: true }, gain(s, 'lesson', now));
  }
  const inSleepWin = (now) => { const h = hourOf(now), W = CFG.sleepTogether; return W[0] > W[1] ? (h >= W[0] || h < W[1]) : (h >= W[0] && h < W[1]); };
  function sleepTogether(s, now) {             // 21:00–03:00 兩隻都瞓 → +2（每晚 1 次）
    const o = st(s); if (o.phase !== 'kid' || !s.sleeping || !inSleepWin(now)) return null; const n = nightOf(now); if (o.sleepNight === n) return null;
    o.sleepNight = n; note(o, 'sleep', {}, now); return gain(s, 'sleep', now);
  }
  function canDuo(s, now) {
    const o = st(s); if (o.phase !== 'kid') return { ok: false, reason: 'phase' }; if (o.rel !== 'friend' && o.rel !== 'family') return { ok: false, reason: 'rel' };
    if (today(s, now).duo >= CFG.duoPerDay) return { ok: false, reason: 'today' }; return { ok: true, left: CFG.duoPerDay - today(s, now).duo };
  }
  function duoDone(s, now, score) { const c = canDuo(s, now); if (!c.ok) return Object.assign({ ok: false }, c); today(s, now).duo++; note(st(s), 'duo', { v: score | 0 }, now); return Object.assign({ ok: true }, gain(s, 'duo', now)); }
  function eatTogether(s, now) { const o = st(s); if (o.phase !== 'kid') return null; today(s, now).eat++; return gain(s, 'eat', now); }
  /* 喊：每日 2–3 次；上線時排（第一次 60–180s，之後 15–40 分鐘）；07–21 先喊；10 分鐘冇人理自己停 */
  function cryWanted(s, now) {
    const o = st(s); if (o.phase !== 'kid' || s.sleeping) return false; const d = today(s, now), h = hourOf(now), W = CFG.cry.hours;
    return d.cries < d.cryPlan && h >= W[0] && h < W[1];
  }
  function cryStart(s, now) { const o = st(s); today(s, now).cries++; o.stats.cries++; note(o, 'cry', {}, now); return true; }
  function comfort(s, now) { const o = st(s); today(s, now).comforts++; note(o, 'comfort', {}, now); return gain(s, 'comfort', now); }
  function cryTimeout(s) { st(s).stats.cryTimeout++; }

  /* ── 雙人 clip／升級小場面（遊美 duo.json／levelup.json）：actor track＋overlay 喺 ms ── */
  function trackAt(tr, ms) {                    // [{t, clip?, x?, y?, loop?}] → {clip, t0(呢個 clip 開始), x, y, loop}
    let clip = 'idle', t0 = 0, loop = true, x = 0, y = 0;
    const xs = tr.filter(k => k.x != null), ys = tr.filter(k => k.y != null);
    for (const k of tr) { if (k.t > ms) break; if (k.clip != null && k.clip !== clip) { clip = k.clip; t0 = k.t; } else if (k.clip != null && k.t > t0 && k.loop === false) t0 = k.t; if (k.clip != null) loop = k.loop !== false; }
    const lerp = (arr, key) => { if (!arr.length) return 0; if (ms <= arr[0].t) return arr[0][key]; for (let i = 1; i < arr.length; i++) if (ms <= arr[i].t) { const a = arr[i - 1], b = arr[i], u = (ms - a.t) / Math.max(1e-6, b.t - a.t); return a[key] + (b[key] - a[key]) * u; } return arr[arr.length - 1][key]; };
    x = lerp(xs, 'x'); y = lerp(ys, 'y');
    return { clip, t0, x, y, loop };
  }
  function moveAt(mv, e) { if (!mv || !mv.length) return [0, 0]; if (e <= mv[0][0]) return [mv[0][1], mv[0][2]]; for (let i = 1; i < mv.length; i++) { const a = mv[i - 1], b = mv[i]; if (e <= b[0]) { const u = (e - a[0]) / Math.max(1e-6, b[0] - a[0]); return [a[1] + (b[1] - a[1]) * u, a[2] + (b[2] - a[2]) * u]; } } const l = mv[mv.length - 1]; return [l[1], l[2]]; }
  function sceneAt(clip, ms, frameCount) {      // frameCount(id) → 疊層幀數
    const dur = clip.durationMs || clip.dur || 1000, t = clip.loop ? ((ms % dur) + dur) % dur : Math.min(ms, dur), actors = {};
    for (const k in clip.actors || {}) { const a = clip.actors[k], tr = trackAt(a.track || [], t); actors[k] = { who: a.who, flip: (a.flip | 0) === 1, clip: tr.clip, ct: t - tr.t0, loop: tr.loop, x: (a.dx || 0) + tr.x, y: (a.dy || 0) + tr.y, z: a.z | 0 }; }
    const ov = [];
    for (const o of clip.overlays || []) {
      const t0 = o.t0 || 0, t1 = o.t1 == null ? dur : o.t1; if (t < t0 || t > t1) continue; const e = t - t0, n = (frameCount && frameCount(o.id)) || 1, f = Math.floor(e / (o.ms || 150));
      const mv = moveAt(o.move, e), seq = Array.isArray(o.frames) && o.frames.length ? o.frames : null, m = seq ? seq.length : n, i = o.loop === false ? Math.min(m - 1, f) : f % m;
      ov.push({ id: o.id, x: (o.x || 0) + mv[0], y: (o.y || 0) + mv[1], frame: seq ? seq[i] : i, z: o.z | 0, e });
    }
    ov.sort((a, b) => a.z - b.z);
    return { t, dur, done: !clip.loop && ms >= dur, actors, overlays: ov };
  }
  /* 孵化第一眼（duo.json hatch_first_glance.timeline 嘅數學；全畫面 2s，可跳去最後一格） */
  function hatchFrame(ms) {
    const t = clamp(ms, 0, 2000), o = { t, egg: null, rays: null, shell: [], kid: null, tr: null, heart: null, flash: 0 };
    if (t < 800) { const crack = Math.min(3, Math.floor(t / 200)), sh = t > 150 && t < 600 ? (Math.floor(t / 50) % 2 ? 2 : -2) : 0; o.egg = { crack, dx: sh }; }
    if (t >= 500 && t < 1400) { const a = t < 1100 ? 1 : 1 - (t - 1100) / 300; o.rays = { f: Math.floor(t / 100) % 4, a: clamp(a, 0, 1) }; }
    if (t >= 600 && t < 800) o.flash = 1 - Math.abs(t - 700) / 100;
    if (t >= 800) {
      const u = clamp((t - 800) / 500, 0, 1); for (let i = 0; i < 4; i++) { const vx = [-38, -16, 18, 40][i], vy = [-46, -60, -58, -44][i]; o.shell.push({ i, x: vx * u, y: vy * u + 90 * u * u, f: i % 2, a: 1 - Math.max(0, u - 0.7) / 0.3 }); }
      o.kid = { blink: t >= 1000 && t < 1120, f: Math.floor((t - 800) / 200) % 4 };
    }
    if (t >= 1300) { const u = clamp((t - 1300) / 400, 0, 1), e = 1 - (1 - u) * (1 - u); o.tr = { x: -60 + (47 - -60) * e, clip: t < 1650 ? 'emo_surprised' : 'emo_happy', ct: t < 1650 ? t - 1300 : t - 1650 }; }
    if (t >= 1700) o.heart = { f: t < 1850 ? 0 : 1, dy: -(t - 1700) / 300 * 6 };
    return o;
  }

  return { CFG, CFG0, LINES, LINE_ZH, PROP, PROP_ZH, WRONG, CARE_ZH, STAGES, STAGE_ZH, REL, REL_ZH, LINES_OUT, dayNum, dayKey, hourOf, nightOf,
    st, noteElder, canDeliver, deliver, careNote, topCare, dreamDue, dream, hatchReady, hatch, stageOf, stageIdx, formOf, settle, settlePick,
    today, gain, checkLevel, canLesson, lesson, inSleepWin, sleepTogether, canDuo, duoDone, eatTogether, cryWanted, cryStart, comfort, cryTimeout,
    trackAt, moveAt, sceneAt, hatchFrame };
});
