/* 《微光小圃》 long5b.js — 第 5 批 5b（docs-gdd/series2-4a4b-spec.md v1.1 §5b＋「5a–5c 玩法位定案 2026-11-01 17:50」；遊美 art/series2_long/5b/long_5b.json）：遠足＋小職業。原創代碼。
   DOM-free、Node 可 require（純邏輯）：存檔 s.fam.b5（sanitize；唔郁 §7 判定、唔加團絨路線分）。
   ・每日（05:00 換日，跟遊美 layout）屋內每隻非主養成年揀 1 樣：遠足／工作／休息。
   ・遠足：只限團絨靜光（evo_still_*）同細佬 S6（A3–H3）；每日最多出發 2 隻；24 小時後返，或者翌日第一次開遊戲返。
     返屋：碎 5–10、家族經驗 +3、一格「團絨日記」故事（手信圖）；30% 手信入家具庫（未有嗰啲先）。
   ・小職業 4 款：郵差助手／園丁／守夜／廚師；每日 Lv＋1 碎（Lv1＝2 碎…Lv5＝6 碎、Lv6＝7 碎；遊策「2 碎＋每級 +1」）；每做滿 5 日升 1 級；Lv5 封頂，家族 Lv7 開 Lv6。
     郵差：25% 委託家具進度 +1；園丁：15% 送 1 件未有嘅花圃擺設；守夜：夜晚（21:00–05:00）先出糧＋夢泡泡貼紙；廚師：細佬一齊食飯親密 +1（每日上限 10 不變）。
   ・經濟：遠足＋工作合共每日最多 12 碎（獨立於 sys12 委託／小遊戲上限）。 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory(require('./series2.js'), require('./house.js'), require('./long5a.js'), require('./systems.js'), require('./visit.js'));
  else { root.Glimmer = root.Glimmer || {}; root.Glimmer.long5b = factory(root.Glimmer.series2, root.Glimmer.house, root.Glimmer.long5a, root.Glimmer.sys12, root.Glimmer.visit); }
})(typeof self !== 'undefined' ? self : this, function (SR, HS, FAM, X, VS) {
  'use strict';
  const obj = (o) => o && typeof o === 'object' && !Array.isArray(o);
  const clamp = (v, a, b) => v < a ? a : v > b ? b : v;
  const hash = (str) => { let h = 2166136261 >>> 0; for (let i = 0; i < str.length; i++) { h ^= str.charCodeAt(i); h = Math.imul(h, 16777619) >>> 0; } return h >>> 0; };
  const H = 3600000, DAY = 86400000, RESET_H = 5;

  /* 同 long_5b.json 一致（long5b.test.js 對數） */
  const CFG = { maxPerDay: 2, durationH: 24, shards: [5, 10], furnitureChance: 0.3, capPerDay: 12, daysPerLevel: 5, maxLv: 5, maxLvFam7: 6, famLvForLv6: 7,
    postChance: 0.25, gardenChance: 0.15, nightFrom: 21, xpReturn: FAM.XP.expedition_return };
  const JOBS = [
    { id: 'post', zh: '郵差助手', icon: 'ui/icon_job_post@3x.png', perk: '有機會出委託獎家具' },
    { id: 'garden', zh: '園丁', icon: 'ui/icon_job_garden@3x.png', perk: '有機會送花圃擺設' },
    { id: 'watch', zh: '守夜', icon: 'ui/icon_job_watch@3x.png', perk: '夜晚出糧＋夢泡泡貼紙' },
    { id: 'chef', zh: '廚師', icon: 'ui/icon_job_chef@3x.png', perk: '細佬一齊食飯親密 +1' },
  ];
  const JOB = Object.fromEntries(JOBS.map(j => [j.id, j])), JOB_IDS = JOBS.map(j => j.id);
  const ACTS = ['expedition', 'job', 'rest'], ACT_ZH = { expedition: '遠足', job: '工作', rest: '休息' };
  /* 夢泡泡貼紙（用返 4a 孵夢泡泡圖 art/series2/ui/dream_bubbles） */
  const STICKERS = ['dream_A_can', 'dream_B_wand', 'dream_C_match', 'dream_D_pebble', 'dream_E_chili', 'dream_F_scope', 'dream_G_book', 'dream_H_moonlamp'];
  const STK_ZH = { dream_A_can: '水壺夢', dream_B_wand: '魔法棒夢', dream_C_match: '火柴夢', dream_D_pebble: '石仔夢', dream_E_chili: '辣椒夢', dream_F_scope: '望遠鏡夢', dream_G_book: '書仔夢', dream_H_moonlamp: '月亮燈夢' };
  /* 遠足地點（手信 → 地點＋一句；日記 3 行） */
  const PLACE = {
    sv_shell: ['海邊', '喺沙灘執到一隻七彩貝殼', '仲同寄居蟹比賽行路'], sv_pinecone: ['森林深處', '喺大樹腳執到一粒松果', '仲同松鼠玩咗成個下晝'],
    sv_starstone: ['星星山丘', '喺草叢見到一粒會發光嘅星星石', '數住星星行返屋'], sv_feather: ['雲端草原', '撿到一條藍羽毛', '追住風跑咗好遠'],
    sv_mushroom: ['蘑菇谷', '同蘑菇婆婆傾偈，攞咗一粒細蘑菇', '學識咗分邊粒食得'], sv_maple: ['紅葉坡', '拾到一塊好紅好紅嘅楓葉', '喺葉堆度打咗幾個滾'],
    sv_bottle: ['海灣', '海浪送嚟一個樽中信', '入面寫住「你好呀」'], sv_cloud: ['雲朵山頂', '摘咗一朵甜甜嘅雲朵糖', '捨唔得食，帶返屋'],
    sv_lantern: ['夜市小巷', '螢火小販送咗一盞細燈', '一路照住返屋'], sv_rainbow: ['彩虹瀑布', '喺水花入面撈到彩虹糖', '全身濕晒都好開心'],
  };
  const SCENES = ['H1', 'H2', 'H3', 'H4'];
  const LINES = {
    depart: '{name}揹住背囊去遠足喇！', back: '{name}返嚟喇！', backTitle: '滴滴返嚟喇！', busy: '遠足中', full: '今日遠足 2/2 用晒', notHike: '只有團絨靜光同細佬 S6 先去得遠足',
    done: '今日已經揀咗（每日揀 1 樣）', paid: '{name}做{job}：+{n} 碎', lvUp: '{name}嘅{job}升到 Lv{lv}！', cap: '今日 12 碎上限到咗', main: '主養喺花園，唔使揀',
    perkPost: '郵差助手幫手派信：委託家具進度 +1', perkGarden: '園丁送咗「{decor}」，擺咗喺花圃', perkWatch: '守夜收到夢泡泡貼紙「{stk}」', perkChef: '廚師加菜：細佬親密 +1',
  };
  const dayKey = (now) => SR.dayNum((now || 0) - RESET_H * H);   // 05:00 換日
  const hourOf = (now) => new Date(now || 0).getHours();
  const isNight = (now) => { const h = hourOf(now); return h >= CFG.nightFrom || h < RESET_H; };
  let ON = true;
  const setOn = (v) => { ON = !!v; if (FAM.LIVE) { if (ON) FAM.LIVE.job_cap_plus1 = 1; else delete FAM.LIVE.job_cap_plus1; } if (FAM.LATER) { if (ON) delete FAM.LATER.job_cap_plus1; else FAM.LATER.job_cap_plus1 = '5b'; } };
  setOn(true);

  function st(s) {
    const F = FAM.st(s); let o = F.b5; if (!obj(o)) o = F.b5 = {};
    o.v = 1;
    if (!obj(o.day)) o.day = {}; const d = o.day; d.k = d.k | 0; d.sh = clamp(d.sh | 0, 0, CFG.capPerDay); d.ex = clamp(d.ex | 0, 0, CFG.maxPerDay);
    if (!obj(d.done)) d.done = {}; for (const k of Object.keys(d.done)) if (!ACTS.includes(d.done[k])) delete d.done[k];
    if (!obj(d.paid)) d.paid = {};
    if (!obj(o.plan)) o.plan = {}; for (const k of Object.keys(o.plan)) { const p = o.plan[k]; if (!obj(p) || !ACTS.includes(p.a)) { delete o.plan[k]; continue; } if (p.a === 'job' && !JOB[p.job]) p.job = 'post'; if (p.a !== 'job') delete p.job; }
    if (!obj(o.away)) o.away = {}; for (const k of Object.keys(o.away)) { const a = o.away[k]; if (!obj(a) || !Number.isFinite(+a.at)) { delete o.away[k]; continue; } a.at = +a.at; a.dk = a.dk | 0; if (!FAM.SV[a.sv]) a.sv = FAM.SOUV[hash(k + ':' + a.at) % FAM.SOUV.length].id; }
    if (!obj(o.jobs)) o.jobs = {}; for (const k of Object.keys(o.jobs)) { const j = o.jobs[k]; if (!obj(j)) { delete o.jobs[k]; continue; } for (const id of Object.keys(j)) if (!JOB[id]) delete j[id]; else j[id] = Math.max(0, j[id] | 0); }
    if (!Array.isArray(o.trips)) o.trips = []; o.trips = o.trips.filter(t => obj(t) && FAM.SV[t.sv] && Array.isArray(t.lines)).slice(-40);
    if (!obj(o.stk)) o.stk = {}; for (const k of Object.keys(o.stk)) if (!STICKERS.includes(k)) delete o.stk[k];
    if (!Array.isArray(o.q)) o.q = []; o.q = o.q.filter(obj).slice(-12);
    if (!obj(o.n)) o.n = {}; for (const k of ['trips', 'shards', 'jobDays', 'chef', 'post', 'garden', 'watch', 'furn']) o.n[k] = Math.max(0, o.n[k] | 0);
    return o;
  }
  /* 換日（舊日未出糧嘅守夜：補出返嗰晚，計舊日上限） */
  function today(s, now, ev) {
    const o = st(s), k = dayKey(now);
    if (o.day.k !== k) {
      const old = o.day;
      if (old.k && old.k < k) for (const r of residents(s)) { const p = o.plan[r.id]; if (p && p.a === 'job' && p.job === 'watch' && !old.paid[r.id] && !o.away[r.id]) payJob(s, r, now, ev, old); }
      o.day = { k, sh: 0, ex: 0, done: {}, paid: {} };
    }
    return o.day;
  }
  /* 屋內非主養成年（住客；主養／細佬做主養唔計） */
  function residents(s) { const F = FAM.st(s), km = F.km ? F.km.id : null; return F.res.filter(r => r.id !== km); }
  const resById = (s, id) => residents(s).find(r => r.id === id) || null;
  const canHike = (r) => !!r && ((r.kind === 'tr' && /^evo_still_/.test(r.fk)) || (r.kind === 'kid' && /^[A-H]3$/.test(r.fk)));
  const maxLv = (s) => (ON && FAM.lvInfo(s).lv >= CFG.famLvForLv6 ? CFG.maxLvFam7 : CFG.maxLv);
  const lvOfDays = (s, d) => clamp(1 + Math.floor((d | 0) / CFG.daysPerLevel), 1, maxLv(s));
  const payOf = (lv) => lv + 1;
  function jobInfo(s, id, job) {
    const o = st(s), d = (o.jobs[id] && o.jobs[id][job]) | 0, ml = maxLv(s), lv = lvOfDays(s, d), capped = lv >= ml, hardCap = lv >= CFG.maxLvFam7;
    const into = d - (lv - 1) * CFG.daysPerLevel;
    return { job, zh: JOB[job].zh, days: d, lv, pay: payOf(lv), capped, lv6Locked: capped && ml < CFG.maxLvFam7, hardCap, toNext: capped ? 0 : CFG.daysPerLevel - into, pct: capped ? 1 : clamp(into / CFG.daysPerLevel, 0, 1), never: d === 0, perk: JOB[job].perk };
  }
  /* 入碎（遠足＋工作合共每日 12）；直接入 sys12 錢包 */
  function earn(s, n, now, why, day) {
    const d = day || today(s, now), g = Math.max(0, Math.min(Math.floor(n), CFG.capPerDay - d.sh)); if (!g) return 0;
    d.sh += g; const w = X.st(s).wallet; w.total += g; w.earned = (w.earned | 0) + g; if (Array.isArray(w.log)) { w.log.push({ t: now || 0, d: SR.dayNum(now || 0), src: '5b:' + (why || ''), n: g }); if (w.log.length > 40) w.log.shift(); }
    st(s).n.shards += g; return g;
  }
  function payJob(s, r, now, ev, day) {
    const o = st(s), d = day || today(s, now, ev), p = o.plan[r.id]; if (!p || p.a !== 'job' || d.paid[r.id]) return null;
    const job = p.job, J = o.jobs[r.id] || (o.jobs[r.id] = {}), lv0 = lvOfDays(s, J[job] | 0), want = payOf(lv0), got = earn(s, want, now, job, d);
    d.paid[r.id] = job; d.done[r.id] = 'job'; J[job] = (J[job] | 0) + 1; o.n.jobDays++; const lv1 = lvOfDays(s, J[job]);
    const e = { type: 'l5b', what: 'pay', id: r.id, name: r.name, job, n: got, want, lv: lv1, at: now }; if (ev) ev.push(e);
    if (lv1 > lv0 && ev) ev.push({ type: 'l5b', what: 'lvUp', id: r.id, name: r.name, job, lv: lv1 });
    perk(s, r, job, now, ev); return e;
  }
  function perk(s, r, job, now, ev) {
    const o = st(s), roll = (hash(r.id + ':' + job + ':' + dayKey(now) + ':' + (o.n.jobDays | 0)) % 10000) / 10000;
    if (job === 'post' && roll < CFG.postChance) { const h = HS.st(s); if (h.at && (HS.commissionLeft(s, 'wall_frame') > 0 || HS.commissionLeft(s, 'win_star') > 0)) { h.qb = (h.qb | 0) + 1; o.n.post++; const got = HS.syncRewards(s, now); if (ev) ev.push({ type: 'l5b', what: 'perk', job, id: r.id, furn: got }); } }
    if (job === 'garden' && roll < CFG.gardenChance && VS) { const v = VS.st(s), left = Object.keys(VS.DECOR_NAME).filter(k => !v.decor[k]); if (left.length) { const k = left[hash(r.id + ':' + dayKey(now)) % left.length]; v.decor[k] = now || 1; o.n.garden++; if (ev) ev.push({ type: 'l5b', what: 'perk', job, id: r.id, decor: k, decorName: VS.DECOR_NAME[k] }); } }
    if (job === 'watch') { const left = STICKERS.filter(k => !o.stk[k]); if (left.length) { const k = left[hash(r.id + ':w:' + dayKey(now)) % left.length]; o.stk[k] = now || 1; o.n.watch++; if (ev) ev.push({ type: 'l5b', what: 'perk', job, id: r.id, stk: k, stkName: STK_ZH[k] }); } }
  }
  /* 揀：act＝expedition／job／rest；job＝post／garden／watch／chef */
  function choose(s, id, act, job, now) {
    if (!ON) return { ok: false, reason: 'off' };
    const r = resById(s, id); if (!r) return { ok: false, reason: FAM.st(s).km && FAM.st(s).km.id === id ? 'main' : 'who' };
    if (!ACTS.includes(act)) return { ok: false, reason: 'act' };
    const o = st(s), d = today(s, now), ev = []; if (o.away[id]) return { ok: false, reason: 'away' };
    const cur = o.plan[id] || { a: 'rest' }, done = d.done[id];
    if (act === 'job' && !JOB[job]) job = cur.job || 'post';
    if (done && !(act === cur.a && (act !== 'job' || job === cur.job))) return { ok: false, reason: 'done' };
    if (act === 'expedition') {
      if (!canHike(r)) return { ok: false, reason: 'notHike' }; if (d.ex >= CFG.maxPerDay) return { ok: false, reason: 'full' };
      const sv = FAM.SOUV[hash(id + ':' + (now || 0) + ':' + o.n.trips) % FAM.SOUV.length].id;
      o.away[id] = { at: now || 1, dk: d.k, sv, room: r.room }; d.ex++; d.done[id] = 'expedition'; o.plan[id] = { a: 'rest' };
      ev.push({ type: 'l5b', what: 'depart', id, name: r.name, room: r.room, sv }); return { ok: true, ev };
    }
    o.plan[id] = act === 'job' ? { a: 'job', job } : { a: 'rest' };
    if (act === 'job' && (job !== 'watch' || isNight(now))) payJob(s, r, now, ev, d);
    return { ok: true, ev };
  }
  /* 每秒／開機掃：換日、遠足返屋、工作出糧。ctx.boot＝今次開遊戲第一次掃（翌日第一次開 → 返屋） */
  function scan(s, now, ctx) {
    const o = st(s), ev = []; ctx = ctx || {}; if (!ON) return ev;
    const d = today(s, now, ev), ids = new Set(residents(s).map(r => r.id));
    for (const id of Object.keys(o.away)) { const a = o.away[id];
      if (!ids.has(id)) { delete o.away[id]; continue; }
      if ((now || 0) - a.at >= CFG.durationH * H || (ctx.boot && dayKey(now) > a.dk)) ev.push(back(s, resById(s, id), now)); }
    for (const id of Object.keys(o.plan)) if (!ids.has(id)) delete o.plan[id];
    for (const r of residents(s)) { const p = o.plan[r.id]; if (p && p.a === 'job' && !o.away[r.id] && !d.paid[r.id] && (p.job !== 'watch' || isNight(now))) payJob(s, r, now, ev, d); }
    return ev;
  }
  function back(s, r, now) {
    const o = st(s), a = o.away[r.id]; delete o.away[r.id];
    const seed = hash(r.id + ':' + a.at), lo = CFG.shards[0], hi = CFG.shards[1], want = lo + (seed % (hi - lo + 1)), got = earn(s, want, now, 'expedition');
    let furn = null; if (((seed >>> 8) % 1000) / 1000 < CFG.furnitureChance) { const F = FAM.st(s); if (!F.sv[a.sv]) { F.sv[a.sv] = now || 1; furn = a.sv; } else { const left = FAM.SOUV.filter(x => !F.sv[x.id]); if (left.length) { furn = left[seed % left.length].id; F.sv[furn] = now || 1; } } if (furn) o.n.furn++; }
    FAM.addXp(s, 'expedition_return', CFG.xpReturn, now, '遠足返');
    const P = PLACE[a.sv], name = r.name || '佢';
    const t = { id: r.id, name, kind: r.kind, fk: r.fk, sv: a.sv, sh: got, want, furn, at: a.at, back: now || 0, day: FAM.st(s).init ? Math.max(1, Math.floor(((now || 0) - FAM.st(s).init) / DAY) + 1) : 1,
      scene: SCENES[seed % SCENES.length], place: P[0], lines: [name + '行到' + P[0] + '，', P[1] + '，', P[2] + '。'] };
    o.trips.push(t); if (o.trips.length > 40) o.trips.shift(); o.n.trips++;
    const e = { type: 'l5b', what: 'back', id: r.id, name, sv: a.sv, n: got, furn, room: r.room, trip: o.trips.length - 1 }; o.q.push({ id: r.id, name, sv: a.sv, n: got, furn, at: now || 0 }); if (o.q.length > 12) o.q.shift();
    return e;
  }
  /* 廚師：細佬一齊食飯 → 有人做緊廚師（今日返工）就 +1 親密（照 series2 每日上限 10） */
  function chefBonus(s, now) {
    if (!ON) return 0; const o = st(s), d = today(s, now), p2 = SR.st(s); if (p2.phase !== 'kid') return 0;
    const chef = residents(s).some(r => o.plan[r.id] && o.plan[r.id].a === 'job' && o.plan[r.id].job === 'chef' && d.paid[r.id] === 'chef'); if (!chef) return 0;
    const dd = SR.today(s, now), n = Math.max(0, Math.min(1, SR.CFG.intimacyCap - dd.n)); if (!n) return 0;
    p2.intim += n; dd.n += n; o.n.chef++; if (SR.checkLevel) SR.checkLevel(s, now); return n;
  }
  { const eat0 = SR.eatTogether; if (eat0 && !eat0.l5b) { SR.eatTogether = function (s, now) { const r = eat0.apply(this, arguments); try { if (r && s) { const b = chefBonus(s, now); if (b) { r.n = (r.n | 0) + b; r.chef = b; } } } catch (e) { } return r; }; SR.eatTogether.l5b = true; } }
  /* 每日安排面板資料 */
  function plan(s, now) {
    const o = st(s), d = today(s, now), F = FAM.st(s), out = [];
    for (const r of residents(s)) { const p = o.plan[r.id] || { a: 'rest' }, a = o.away[r.id], done = d.done[r.id] || null;
      const row = { id: r.id, name: r.name, kind: r.kind, fk: r.fk, room: r.room, a: a ? 'expedition' : p.a, job: p.job || null, away: a ? { at: a.at, left: Math.max(0, a.at + CFG.durationH * H - (now || 0)), sv: a.sv } : null, done, hike: canHike(r),
        lock: { expedition: !!a || !canHike(r) || (!!done && done !== 'expedition') || (d.ex >= CFG.maxPerDay && done !== 'expedition'), job: !!a || (!!done && done !== 'job'), rest: !!a || (!!done) } };
      if (p.a === 'job') row.info = jobInfo(s, r.id, p.job);
      row.paid = !!d.paid[r.id]; out.push(row); }
    return { day: d.k, ex: d.ex, exMax: CFG.maxPerDay, sh: d.sh, shMax: CFG.capPerDay, rows: out, km: F.km ? F.km.id : null, maxLv: maxLv(s) };
  }
  const away = (s, id) => !!st(s).away[id];
  function summary(s, now) { const o = st(s), d = today(s, now); return { day: d.k, ex: d.ex, sh: d.sh, away: Object.keys(o.away), plan: JSON.parse(JSON.stringify(o.plan)), jobs: JSON.parse(JSON.stringify(o.jobs)), trips: o.trips.length, stk: Object.keys(o.stk), n: Object.assign({}, o.n), q: o.q.length, maxLv: maxLv(s) }; }
  /* 開發：即刻返屋（當 24h 過咗） */
  function devReturn(s, id, now) { const o = st(s), ids = id ? [id] : Object.keys(o.away), ev = []; for (const k of ids) if (o.away[k]) { const r = resById(s, k); if (r) ev.push(back(s, r, now)); else delete o.away[k]; } return ev; }
  function devDays(s, id, job, n) { const o = st(s), J = o.jobs[id] || (o.jobs[id] = {}); J[job] = Math.max(0, (J[job] | 0) + (n | 0)); return jobInfo(s, id, job); }
  function devNewDay(s, now) { const o = st(s); o.day.k = 0; return today(s, now); }

  return { CFG, JOBS, JOB, JOB_IDS, ACTS, ACT_ZH, STICKERS, STK_ZH, PLACE, SCENES, LINES, RESET_H, dayKey, isNight, setOn, isOn: () => ON,
    st, today, residents, canHike, maxLv, lvOfDays, payOf, jobInfo, earn, choose, scan, back, chefBonus, plan, away, summary, devReturn, devDays, devNewDay };
});
