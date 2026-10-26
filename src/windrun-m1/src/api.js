/* api.js — 模擬／表現之間嘅薄 API（M1 · 4.1）。無 DOM、無 Date／Math.random，Node 同瀏覽器通用。
   規則：main.js／ui.js 只可經呢度操作比賽——
     • 寫入：Api.submit(match, side, action)（玩家輸入 → 決策）
     • 推進：Api.advance(match, realDt, speedMul)（固定步長累加器；UI 唔直接叫 Sim.step）
     • 讀取：Api.view(match)（插值快照，純資料）、Api.events(match)、Api.canSwap／canSkill
   錄製：每個成功決策（玩家＋AI＋影子隊）記錄為 {k:步序,s:邊,a:類型,i:索引}；回放只按記錄套用。
   格式見 docs/replay-format.md。 */
(function (g) {
  'use strict';
  const Data = (typeof module !== 'undefined' && module.exports) ? require('./data.js') : g.WR.Data;
  const Sim = (typeof module !== 'undefined' && module.exports) ? require('./sim.js') : g.WR.Sim;
  const P0 = Data.PARAMS;
  const REPLAY_FORMAT = 'windrun-replay', REPLAY_VERSION = 1, SIM_VERSION = 1, CHECKPOINT_EVERY = 30;

  function hex8(n) { return ('00000000' + (n >>> 0).toString(16)).slice(-8); }
  function canon(v) { // 鍵排序嘅 JSON，供參數雜湊
    if (Array.isArray(v)) return '[' + v.map(canon).join(',') + ']';
    if (v && typeof v === 'object') return '{' + Object.keys(v).sort().map(k => JSON.stringify(k) + ':' + canon(v[k])).join(',') + '}';
    return JSON.stringify(v);
  }
  function fnvStr(s) {
    let h = 0x811c9dc5;
    for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 0x01000193) >>> 0; }
    return h >>> 0;
  }
  function paramsHash(P) { return hex8(fnvStr(canon(P))); }
  function clone(o) { return JSON.parse(JSON.stringify(o)); }

  /* setup（可 JSON 化）：
     { seed, terrains:[5 id], teams:[[{id,lv,bonus?,cond?}],[…]],
       ctrls:[{kind:'player'|'ai'|'shadow', script?}, …], noSwap?:[b,b], noSkill?:[b,b] }
     opts: { mode:'live'|'log'|'regen', replay?, P?, record?:true } */
  function buildRace(setup, P, ctrlMode) {
    const ctrls = setup.ctrls || [{ kind: 'player' }, { kind: 'ai' }];
    const rc = ctrls.map(c => {
      if (ctrlMode === 'log') return null;                 // 回放：唔跑控制器，全靠決策記錄
      if (c.kind === 'player') return null;
      if (c.kind === 'shadow') return { kind: 'shadow', script: c.script, ei: 0 };
      return { kind: 'ai', next: 0 };
    });
    return Sim.createRace({
      terrains: setup.terrains, P, seed: setup.seed,
      teams: [Sim.unitsFromDef(setup.teams[0], P), Sim.unitsFromDef(setup.teams[1], P)],
      ctrls: rc, noSwap: setup.noSwap, noSkill: setup.noSkill
    });
  }

  function snap(race) {
    const sides = race.sides.map(sd => ({
      pos: sd.pos, phase: sd.phase, phaseT: sd.phaseT, active: sd.active, pending: sd.pending, cooldown: sd.cooldown,
      effect: sd.effect ? { type: sd.effect.type, mult: sd.effect.mult, t: sd.effect.t } : null,
      shield: sd.shield, swaps: sd.swaps, skills: sd.skills, speed: sd.speed, A: sd.A, C: sd.C, G: sd.G, S: sd.S,
      finishT: sd.finishT, fieldTime: sd.fieldTime,
      team: sd.team.map(u => ({
        cid: u.cid, name: u.name, lv: u.lv, skill: u.skill, trait: u.trait, apt: u.apt, stats: u.stats, max: u.max,
        stamina: u.stamina, skillUsed: u.skillUsed, onField: u.onField
      }))
    }));
    return { t: race.t, stepN: race.stepN, over: race.over, winner: race.winner, duration: race.duration, terrains: race.terrains, sides };
  }
  function lerp(a, b, k) { return a + (b - a) * k; }
  // 插值：只對連續量（位置、耐力、速度、計時器）；離散量取最新
  function mix(a, b, k) {
    const out = { t: lerp(a.t, b.t, k), stepN: b.stepN, over: b.over, winner: b.winner, duration: b.duration, terrains: b.terrains, alpha: k, sides: [] };
    for (let s = 0; s < 2; s++) {
      const x = a.sides[s], y = b.sides[s], o = Object.assign({}, y);
      const sameUnit = x.active === y.active && x.phase === y.phase;
      o.pos = lerp(x.pos, y.pos, k); o.speed = lerp(x.speed, y.speed, k); o.cooldown = lerp(x.cooldown, y.cooldown, k);
      o.shield = lerp(x.shield, y.shield, k);
      if (sameUnit) o.phaseT = lerp(x.phaseT, y.phaseT, k);
      o.team = y.team.map((u, i) => Object.assign({}, u, { stamina: lerp(x.team[i].stamina, u.stamina, k) }));
      out.sides.push(o);
    }
    return out;
  }

  function createMatch(setup, opts) {
    opts = opts || {};
    const P = opts.P || P0, mode = opts.mode || 'live';
    const replay = opts.replay || null;
    const rec = mode === 'live' && opts.record !== false;
    const race = buildRace(setup, P, mode === 'log' ? 'log' : 'live');
    const m = {
      race, setup: clone(setup), P, mode, dt: P.sim_dt, acc: 0,
      log: [], cps: [], recording: rec,
      replay, di: 0, verifyError: null, checkpoints: replay && replay.checkpoints ? replay.checkpoints.h : null,
      prev: snap(race), curr: snap(race), evIdx: 0
    };
    if (mode === 'regen' && replay) {
      // 玩家邊用記錄，其餘邊用控制器
      m.logOnlySides = (replay.ctrls || []).map(c => c.kind === 'player');
    }
    race.onDecision = function (k, s, a, i) {
      if (m.recording) m.log.push({ k: k, s: s, a: a, i: i });
      if (m.mode !== 'live') { /* 回放時唔錄 */ }
    };
    if (rec) m.cps.push(hex8(Sim.hashState(race)));
    return m;
  }

  // 玩家輸入 → 決策（live 模式）。回傳是否成功。
  function submit(m, side, action) {
    if (m.mode !== 'live') return false;
    const r = m.race;
    if (action.type === 'swap') return Sim.requestSwap(r, side, action.i);
    if (action.type === 'skill') return Sim.requestSkill(r, side);
    return false;
  }

  // 套用回放記錄中屬於當前步嘅決策（步前）
  function applyReplayDecisions(m) {
    const dec = m.replay.decisions, r = m.race;
    while (m.di < dec.length && dec[m.di].k === r.stepN) {
      const d = dec[m.di];
      const skip = m.mode === 'regen' && !(m.logOnlySides && m.logOnlySides[d.s]);
      if (!skip) {
        const ok = d.a === 'swap' ? Sim.requestSwap(r, d.s, d.i) : Sim.requestSkill(r, d.s);
        if (!ok && !m.verifyError) m.verifyError = '決策套用失敗 k=' + d.k + ' s=' + d.s + ' a=' + d.a;
      }
      m.di++;
    }
    // 防呆：記錄中 k 已過但未套用
    if (m.di < dec.length && dec[m.di].k < r.stepN && !m.verifyError) m.verifyError = '決策步序亂序 k=' + dec[m.di].k;
  }

  // 前進一個固定步
  function stepOnce(m) {
    const r = m.race;
    if (r.over) return false;
    if (m.replay && (m.mode === 'log' || m.mode === 'regen')) applyReplayDecisions(m);
    Sim.step(r, m.dt);
    const n = r.stepN;
    if (m.recording && (n % CHECKPOINT_EVERY === 0 || r.over)) m.cps.push(hex8(Sim.hashState(r)));
    if (m.checkpoints && n % CHECKPOINT_EVERY === 0 && !m.verifyError) {
      const want = m.checkpoints[n / CHECKPOINT_EVERY];
      if (want && want !== hex8(Sim.hashState(r))) m.verifyError = '檢查點不符 step=' + n;
    }
    return true;
  }

  // 表現層每幀叫：累加真實時間，跑 0..N 個固定步，更新插值快照。
  function advance(m, realDt, mul) {
    const h = m.dt, r = m.race;
    m.acc += realDt * (mul || 1);
    let guard = 0, ran = 0;
    while (m.acc >= h && !r.over && guard++ < 20) {
      m.prev = m.curr; stepOnce(m); m.curr = snap(r); m.acc -= h; ran++;
    }
    if (m.acc > h * 20) m.acc = 0;
    if (r.over) m.acc = 0;
    return ran;
  }
  function view(m) { return mix(m.prev, m.curr, m.race.over ? 1 : Math.min(1, m.acc / m.dt)); }
  function events(m) { return m.race.events; }
  function canSwap(m, s) { return m.mode === 'live' && Sim.canSwap(m.race, s); }
  function canSkill(m, s) { return m.mode === 'live' && Sim.canSkill(m.race, s); }
  function segOf(terrains, pos, P) { P = P || P0; return Sim.clamp(Math.floor(pos / P.segment_len), 0, terrains.length - 1); }
  function runToEnd(m) { let n = 0; while (!m.race.over && n++ < 1e6) stepOnce(m); m.prev = m.curr = snap(m.race); return m; }

  // 匯出 replay（可喺賽中／賽後叫；賽後含 result＋checkpoints）
  function getReplay(m) {
    const r = m.race, s = m.setup;
    return {
      format: REPLAY_FORMAT, v: REPLAY_VERSION,
      sim: { version: SIM_VERSION, dt: m.dt, paramsHash: paramsHash(m.P) },
      seed: s.seed, terrains: s.terrains, teams: s.teams, ctrls: s.ctrls || [{ kind: 'player' }, { kind: 'ai' }],
      noSwap: s.noSwap || [false, false], noSkill: s.noSkill || [false, false], meta: s.meta || {},
      decisions: m.log.slice(),
      checkpoints: { every: CHECKPOINT_EVERY, h: m.cps.slice() },
      result: { over: r.over, steps: r.stepN, winner: r.winner, duration: r.duration, finalHash: hex8(Sim.hashState(r)) }
    };
  }
  function validateReplay(rp, P) {
    P = P || P0;
    if (!rp || rp.format !== REPLAY_FORMAT) return '唔係 windrun replay';
    if (rp.v !== REPLAY_VERSION) return '不支援嘅 replay 版本 ' + rp.v;
    if (!rp.sim || rp.sim.version !== SIM_VERSION) return '模擬版本不符';
    if (rp.sim.paramsHash !== paramsHash(P)) return '參數雜湊不符（PARAMS 已改）';
    if (Math.abs(rp.sim.dt - P.sim_dt) > 1e-15) return '步長不符';
    return null;
  }
  // mode: 'log'＝只按決策記錄（預設）；'regen'＝非玩家邊重新由 AI／影子隊腳本產生
  function createPlayback(rp, opts) {
    opts = opts || {};
    const P = opts.P || P0, err = validateReplay(rp, P);
    if (err) throw new Error(err);
    const setup = { seed: rp.seed, terrains: rp.terrains, teams: rp.teams, ctrls: rp.ctrls, noSwap: rp.noSwap, noSkill: rp.noSkill };
    return createMatch(setup, { P, mode: opts.mode || 'log', replay: rp, record: false });
  }
  // 驗證：跑完並同 replay 內嘅 result／checkpoints 比對。回傳 {ok, error, finalHash}
  function verifyReplay(rp, opts) {
    const m = createPlayback(rp, opts);
    runToEnd(m);
    const fh = hex8(Sim.hashState(m.race));
    let error = m.verifyError;
    if (!error && rp.result) {
      if (rp.result.finalHash !== fh) error = '最終雜湊不符';
      else if (rp.result.steps !== m.race.stepN) error = '步數不符';
      else if (rp.result.winner !== m.race.winner) error = '勝負不符';
    }
    if (!error && m.di !== rp.decisions.length) error = '有決策未套用 ' + m.di + '/' + rp.decisions.length;
    return { ok: !error, error: error, finalHash: fh, steps: m.race.stepN, winner: m.race.winner };
  }

  const Api = {
    REPLAY_FORMAT, REPLAY_VERSION, SIM_VERSION, CHECKPOINT_EVERY,
    createMatch, submit, stepOnce, advance, view, events, canSwap, canSkill, segOf, runToEnd,
    getReplay, validateReplay, createPlayback, verifyReplay, paramsHash, hex8
  };
  if (typeof module !== 'undefined' && module.exports) module.exports = Api;
  else { g.WR = g.WR || {}; g.WR.Api = Api; }
})(typeof globalThis !== 'undefined' ? globalThis : this);
