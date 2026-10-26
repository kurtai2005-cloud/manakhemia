/* sim.js — 比賽邏輯（無 DOM）。固定時間步長＋可種子 RNG，結果可重現。 */
(function (g) {
  'use strict';
  const Data = (typeof module !== 'undefined' && module.exports) ? require('./data.js') : g.WR.Data;
  const TIDX = Data.TERRAIN_INDEX;

  function clamp(v, a, b) { return v < a ? a : (v > b ? b : v); }

  // mulberry32 可種子 RNG
  function makeRng(seed) {
    let a = (seed >>> 0) || 1;
    return function () {
      a = (a + 0x6D2B79F5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  // ===== 成長（純函數） =====
  function expToNext(lv, P) { P = P || Data.PARAMS; return P.exp_base + P.exp_per_level * lv; }
  function newCreatureState(lv) { return { lv: lv || 1, exp: 0, bonus: { speed: 0, power: 0, calm: 0, stamina: 0 }, cond: 100 }; }
  function statsOf(cid, st, P) {
    P = P || Data.PARAMS;
    const cr = Data.CREATURES_BY_ID[cid];
    st = st || newCreatureState(1);
    const m = P.growth_star_mult[cr.star - 1], n = st.lv - 1, b = st.bonus || {};
    return {
      speed: cr.base.speed + P.growth_per_level.speed * n * m + (b.speed || 0),
      power: cr.base.power + P.growth_per_level.power * n * m + (b.power || 0),
      calm: cr.base.calm + P.growth_per_level.calm * n * m + (b.calm || 0),
      stamina: cr.base.stamina + P.growth_per_level.stamina * n * m + (b.stamina || 0)
    };
  }
  // 加經驗；回傳升咗幾級
  function addExp(st, amount, P) {
    P = P || Data.PARAMS;
    let gained = 0;
    if (st.lv >= P.level_cap) { st.exp = 0; return 0; }
    st.exp += amount;
    while (st.lv < P.level_cap && st.exp >= expToNext(st.lv, P)) {
      st.exp -= expToNext(st.lv, P); st.lv++; gained++;
    }
    if (st.lv >= P.level_cap) st.exp = 0;
    return gained;
  }

  // ===== 單位／賽事建立 =====
  function makeUnit(cid, st, P) {
    P = P || Data.PARAMS;
    const cr = Data.CREATURES_BY_ID[cid];
    st = st || newCreatureState(1);
    const s = statsOf(cid, st, P);
    const max = clamp(s.stamina, P.stamina_max_range[0], P.stamina_max_range[1]);
    const cond = st.cond == null ? 100 : st.cond;
    const frac = P.cond_stamina_floor + (1 - P.cond_stamina_floor) * clamp(cond, 0, 100) / 100;
    return {
      cid, name: cr.name, lv: st.lv, stats: { speed: s.speed, power: s.power, calm: s.calm, stamina: max },
      apt: cr.apt.slice(), skill: cr.skill, trait: cr.trait,
      stamina: max * frac, max, skillUsed: false, onField: false, exhaustedFlag: false
    };
  }

  function makeSide(team, ctrl) {
    team[0].onField = true;
    return {
      team, active: 0, pos: 0, phase: 'run', phaseT: 0, pending: -1, cooldown: 0,
      effect: null, shield: 0, swaps: 0, skills: 0, ctrl: ctrl || null,
      speed: 0, A: 1, C: 1, G: 1, S: 1, fieldTime: 0, finishT: -1, lastSkillT: -99
    };
  }

  /* opts: { terrains:[5 id], teams:[[unit],[unit]], ctrls:[null|ctrl,null|ctrl], P, seed, noSwap:[bool,bool], noSkill:[bool,bool] } */
  function createRace(opts) {
    const P = opts.P || Data.PARAMS;
    const seed = opts.seed == null ? 1 : opts.seed;
    const race = {
      P, terrains: opts.terrains, t: 0, over: false, winner: -1, duration: 0, seed,
      events: [], noSwap: opts.noSwap || [false, false], noSkill: opts.noSkill || [false, false],
      rngs: [makeRng(seed * 2 + 1), makeRng(seed * 2 + 2)],
      sides: [makeSide(opts.teams[0], opts.ctrls && opts.ctrls[0]), makeSide(opts.teams[1], opts.ctrls && opts.ctrls[1])]
    };
    return race;
  }

  // ===== 計算 =====
  function segOf(race, pos) {
    return clamp(Math.floor(pos / race.P.segment_len), 0, race.terrains.length - 1);
  }
  function gustoOfStamina(u, P) {
    const gv = P.gusto_values, th = P.gusto_thresholds;
    if (u.stamina <= 0) return gv[3];
    const pct = u.stamina / u.max;
    if (pct > th[0]) return gv[0];
    if (pct > th[1]) return gv[1] + (gv[0] - gv[1]) * (pct - th[1]) / (th[0] - th[1]);
    return gv[2] + (gv[1] - gv[2]) * (pct / th[1]);
  }
  function swapOutTime(calm, P) {
    return clamp(P.swap_out_base - calm * P.swap_out_calm_coeff, P.swap_out_min, P.swap_out_base);
  }
  function aptMult(u, terrainId, P) { return P.aptitude_mult[u.apt[TIDX[terrainId]] - 1]; }
  function catchupC(gapM, u, P) {
    if (gapM <= 0) return 1;
    const cap = P.catchup_cap + (u.trait === 'tough' ? P.catchup_cap_bonus_trait : 0);
    return 1 + Math.min(cap, P.catchup_per_m * gapM);
  }
  function computeSide(race, s) {
    const P = race.P, side = race.sides[s], other = race.sides[1 - s];
    const u = side.team[side.active];
    const terrain = race.terrains[segOf(race, side.pos)];
    const A = aptMult(u, terrain, P);
    let G = gustoOfStamina(u, P);
    if (side.phase === 'out') G = Math.min(G, P.swap_out_gusto);
    else if (side.phase === 'in') {
      const k = 1 - side.phaseT / P.swap_in_time;
      G = Math.min(G, P.swap_in_gusto_start + (1 - P.swap_in_gusto_start) * clamp(k, 0, 1));
    }
    const S = side.effect ? side.effect.mult : 1;
    const C = catchupC(other.pos - side.pos, u, P);
    side.A = A; side.G = G; side.S = S; side.C = C;
    side.speed = u.stats.speed * P.speed_scale_K * A * C * G * S;
    return side.speed;
  }

  // ===== 操作（玩家／AI 共用） =====
  function canSwap(race, s) {
    const side = race.sides[s];
    return !race.over && side.phase === 'run' && side.cooldown <= 0 && side.team.length > 1 && !race.noSwap[s];
  }
  function requestSwap(race, s, idx) {
    const side = race.sides[s];
    if (!canSwap(race, s) || idx === side.active || idx < 0 || idx >= side.team.length) return false;
    side.phase = 'out';
    side.phaseT = swapOutTime(side.team[side.active].stats.calm, race.P);
    side.pending = idx;
    side.cooldown = race.P.swap_cooldown;
    side.swaps++;
    race.events.push({ t: race.t, side: s, type: 'swap', from: side.active, to: idx });
    return true;
  }
  function canSkill(race, s) {
    const side = race.sides[s], u = side.team[side.active];
    return !race.over && side.phase === 'run' && !u.skillUsed && !race.noSkill[s];
  }
  function requestSkill(race, s) {
    if (!canSkill(race, s)) return false;
    const P = race.P, side = race.sides[s], foe = race.sides[1 - s], u = side.team[side.active];
    u.skillUsed = true; side.skills++; side.lastSkillT = race.t;
    const ev = { t: race.t, side: s, type: 'skill', skill: u.skill, blocked: false };
    switch (u.skill) {
      case 'boost': side.effect = { type: 'boost', mult: P.skill_mult.boost, t: P.skill_duration.boost }; break;
      case 'trip':
        if (foe.shield > 0) ev.blocked = true;
        else foe.effect = { type: 'trip', mult: P.skill_mult.trip, t: P.skill_duration.trip };
        break;
      case 'recover': u.stamina = Math.min(u.max, u.stamina + P.stamina_restore_skill); break;
      case 'shield': side.shield = P.skill_duration.shield; break;
    }
    race.events.push(ev);
    return true;
  }

  // ===== 推進 =====
  function step(race, dt) {
    if (race.over) return;
    const P = race.P;
    for (let s = 0; s < 2; s++) { const c = race.sides[s].ctrl; if (c) controllerAct(race, s, c); }
    const sp = [computeSide(race, 0), computeSide(race, 1)];
    const prev = [race.sides[0].pos, race.sides[1].pos];
    for (let s = 0; s < 2; s++) {
      const side = race.sides[s], u = side.team[side.active];
      // 位移
      side.pos += sp[s] * dt;
      // 耐力
      const terrain = race.terrains[segOf(race, prev[s])];
      const drain = P.stamina_drain[terrain] * (1 - u.stats.power * P.power_drain_coeff);
      u.stamina = Math.max(0, u.stamina - drain * dt);
      if (u.stamina <= 0 && !u.exhaustedFlag) { u.exhaustedFlag = true; race.events.push({ t: race.t, side: s, type: 'exhaust', unit: side.active }); }
      for (let i = 0; i < side.team.length; i++) {
        if (i !== side.active) side.team[i].stamina = Math.min(side.team[i].max, side.team[i].stamina + P.bench_regen * dt);
      }
      side.fieldTime += dt;
      // 計時器
      if (side.effect) { side.effect.t -= dt; if (side.effect.t <= 0) side.effect = null; }
      if (side.shield > 0) side.shield = Math.max(0, side.shield - dt);
      if (side.cooldown > 0) side.cooldown = Math.max(0, side.cooldown - dt);
      if (side.phase === 'out') {
        side.phaseT -= dt;
        if (side.phaseT <= 0) {
          side.active = side.pending; side.pending = -1;
          side.team[side.active].onField = true;
          side.phase = 'in'; side.phaseT = P.swap_in_time; side.fieldTime = 0;
        }
      } else if (side.phase === 'in') {
        side.phaseT -= dt;
        if (side.phaseT <= 0) { side.phase = 'run'; side.phaseT = 0; }
      }
    }
    race.t += dt;
    // 終點判定（同一步內以交越時間分先後）
    const L = P.track_len;
    const fin = [-1, -1];
    for (let s = 0; s < 2; s++) {
      const side = race.sides[s];
      if (side.pos >= L) {
        const frac = sp[s] > 0 ? (L - prev[s]) / (sp[s] * dt) : 1;
        side.finishT = race.t - dt + clamp(frac, 0, 1) * dt;
        fin[s] = side.finishT;
      }
    }
    if (fin[0] >= 0 || fin[1] >= 0) {
      race.over = true;
      race.winner = fin[1] < 0 || (fin[0] >= 0 && fin[0] <= fin[1]) ? 0 : 1;
      race.duration = fin[race.winner];
      race.events.push({ t: race.t, type: 'finish', winner: race.winner });
    } else if (race.t >= P.race_timeout) {
      race.over = true; race.winner = race.sides[0].pos >= race.sides[1].pos ? 0 : 1; race.duration = race.t;
    }
  }

  // ===== 對手控制（AI／影子隊腳本） =====
  function expectedScore(u, tIdx, P) {
    return u.stats.speed * P.aptitude_mult[u.apt[tIdx] - 1] * gustoOfStamina(u, P);
  }
  function aiSwapDecision(race, s) {
    const P = race.P, side = race.sides[s], u = side.team[side.active];
    if (!canSwap(race, s)) return -1;
    if (P.track_len - side.pos <= P.ai_no_swap_last_m) return -1;
    const seg = segOf(race, side.pos), rem = (seg + 1) * P.segment_len - side.pos;
    const near = seg < race.terrains.length - 1 && rem <= P.ai_swap_lead_m;
    const aheadSeg = near ? seg + 1 : seg;
    const aheadT = TIDX[race.terrains[aheadSeg]];
    let best = -1, bestV = -1;
    const stPct = u.stamina / u.max;
    // 1) 耐力 < 30%：換上最啱嘅後備
    if (stPct < P.ai_swap_stamina_pct) {
      const cur = expectedScore(u, aheadT, P);
      for (let i = 0; i < side.team.length; i++) {
        if (i === side.active) continue;
        const c = side.team[i];
        if (c.stamina / c.max < P.ai_bench_min_pct) continue;
        const v = expectedScore(c, aheadT, P);
        if (v > cur && v > bestV) { best = i; bestV = v; }
      }
      if (best >= 0) return best;
    }
    // 2) 下一段適性差 ≥ 2 級
    if (near) {
      const nT = TIDX[race.terrains[seg + 1]];
      for (let i = 0; i < side.team.length; i++) {
        if (i === side.active) continue;
        const c = side.team[i];
        if (c.stamina / c.max < P.ai_bench_min_pct) continue;
        const gap = c.apt[nT] - u.apt[nT];
        if (gap >= P.ai_swap_apt_gap) {
          const v = gap * 1000 + expectedScore(c, nT, P);
          if (v > bestV) { best = i; bestV = v; }
        }
      }
    }
    return best;
  }
  function aiSkillDecision(race, s) {
    const P = race.P, side = race.sides[s], foe = race.sides[1 - s], u = side.team[side.active];
    if (!canSkill(race, s)) return false;
    if (side.fieldTime < P.ai_skill_delay) return false;
    const lenLeft = P.track_len - side.pos;
    if (lenLeft < P.ai_force_skill_m) return true;
    const tIdx = TIDX[race.terrains[segOf(race, side.pos)]];
    switch (u.skill) {
      case 'boost': return u.apt[tIdx] >= 3 && u.stamina / u.max > 0.3;
      case 'trip': return foe.phase === 'run' && foe.shield <= 0 && !(foe.effect && foe.effect.type === 'trip');
      case 'recover': return u.stamina / u.max < 0.5;
      case 'shield': { const fu = foe.team[foe.active]; return fu.skill === 'trip' && !fu.skillUsed && side.shield <= 0; }
    }
    return false;
  }
  function controllerAct(race, s, c) {
    if (race.over) return;
    if (c.kind === 'shadow') return shadowAct(race, s, c);
    if (race.t < (c.next || 0)) return;
    const P = race.P;
    c.next = race.t + P.ai_think_interval * (0.7 + 0.6 * race.rngs[s]());
    const sw = aiSwapDecision(race, s);
    if (sw >= 0) { requestSwap(race, s, sw); return; }
    if (aiSkillDecision(race, s)) requestSkill(race, s);
  }
  // 影子隊：預錄腳本，按距離觸發；對手放技後 2 秒內反制
  function shadowAct(race, s, c) {
    const P = race.P, side = race.sides[s], foe = race.sides[1 - s], sc = c.script;
    c.ei = c.ei || 0;
    while (c.ei < sc.events.length && side.pos >= sc.events[c.ei].m) {
      const ev = sc.events[c.ei];
      let ok;
      if (ev.swap != null) ok = requestSwap(race, s, ev.swap);
      else ok = requestSkill(race, s);
      if (ok || side.pos >= ev.m + 80) c.ei++; else break;
    }
    if (sc.counter && foe.lastSkillT > -50 && c.counterFor !== foe.lastSkillT &&
        race.t - foe.lastSkillT <= P.shadow_counter_window && race.t - foe.lastSkillT >= 0.5) {
      const u = side.team[side.active];
      if ((u.skill === 'boost' || u.skill === 'trip') && requestSkill(race, s)) c.counterFor = foe.lastSkillT;
    }
  }

  // ===== 便利：由隊伍定義建立賽事 =====
  // teamDef: [{id, lv, bonus?, cond?}]
  function unitsFromDef(def, P) {
    return def.map(d => makeUnit(d.id, { lv: d.lv || 1, exp: 0, bonus: d.bonus || { speed: 0, power: 0, calm: 0, stamina: 0 }, cond: d.cond == null ? 100 : d.cond }, P));
  }
  function makeOppCtrl(stageOpp) {
    if (stageOpp.kind === 'shadow') return { kind: 'shadow', script: stageOpp.script, ei: 0 };
    return { kind: 'ai', next: 0 };
  }

  // 無 DOM 跑完一場；兩邊都 AI（teamDefs[i] = [{id, lv}]）
  function runMatch(o) {
    const P = o.P || Data.PARAMS;
    const race = createRace({
      terrains: o.terrains, P, seed: o.seed,
      teams: [unitsFromDef(o.teams[0], P), unitsFromDef(o.teams[1], P)],
      ctrls: [{ kind: 'ai', next: 0 }, { kind: 'ai', next: 0 }],
      noSwap: o.noSwap, noSkill: o.noSkill
    });
    const dt = P.sim_dt;
    while (!race.over) step(race, dt);
    return {
      winner: race.winner, duration: race.duration, swaps: [race.sides[0].swaps, race.sides[1].swaps],
      skills: [race.sides[0].skills, race.sides[1].skills], margin: Math.abs(race.sides[0].pos - race.sides[1].pos)
    };
  }

  const Sim = {
    makeRng, expToNext, newCreatureState, statsOf, addExp, makeUnit, createRace, step, segOf,
    gustoOfStamina, swapOutTime, catchupC, computeSide, canSwap, requestSwap, canSkill, requestSkill,
    aiSwapDecision, unitsFromDef, makeOppCtrl, runMatch, clamp
  };
  if (typeof module !== 'undefined' && module.exports) module.exports = Sim;
  else { g.WR = g.WR || {}; g.WR.Sim = Sim; }
})(typeof window !== 'undefined' ? window : globalThis);
