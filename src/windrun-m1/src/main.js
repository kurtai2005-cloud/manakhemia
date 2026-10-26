/* main.js — 遊戲狀態、存檔、場景切換、主迴圈。 */
(function () {
  'use strict';
  const Data = WR.Data, Sim = WR.Sim, Api = WR.Api, UI = WR.UI, P = Data.PARAMS;
  const KEY = 'windrun_save_v1';

  function newSave() {
    const s = { v: 1, creatures: {}, ribbons: 0, turn: 1, actionsLeft: P.actions_per_turn, cleared: {}, races: 0, sound: true };
    Data.CREATURES.forEach(c => { s.creatures[c.id] = Sim.newCreatureState(3); });
    return s;
  }
  function loadSave() {
    try {
      const raw = window.localStorage.getItem(KEY);
      if (!raw) return newSave();
      const s = JSON.parse(raw), base = newSave();
      if (!s || s.v !== 1) return base;
      Data.CREATURES.forEach(c => { if (s.creatures && s.creatures[c.id]) base.creatures[c.id] = Object.assign(Sim.newCreatureState(1), s.creatures[c.id]); });
      ['ribbons', 'turn', 'actionsLeft', 'races'].forEach(k => { if (typeof s[k] === 'number') base[k] = s[k]; });
      base.cleared = s.cleared || {}; base.sound = s.sound !== false;
      return base;
    } catch (e) { return newSave(); }
  }

  const G = {
    scene: 'menu', save: loadSave(), sel: 'mochi', trainPick: false, stageSel: 1, teamPick: [],
    race: null, result: null, lastReplay: null, toasts: [], confirmReset: false,

    persist() { try { window.localStorage.setItem(KEY, JSON.stringify(G.save)); } catch (e) { /* 私隱模式：唔存檔 */ } },
    toast(text, color, y) { G.toasts.push({ text, color, t0: UI.t, y: y || 760 }); },
    go(scene, keep) {
      if (scene === 'team' && !keep) {
        const open = Data.STAGES.filter(s => s.id === 1 || G.save.cleared[s.id - 1]);
        const next = open.filter(s => !G.save.cleared[s.id])[0] || open[open.length - 1];
        G.stageSel = next.id; G.teamPick = [];
      }
      G.scene = scene; G.trainPick = false; G.toasts = []; UI.SFX.tap();
    },
    resetSave() { G.save = newSave(); G.persist(); G.confirmReset = false; G.sel = 'mochi'; G.toast('存檔已重置', '#ffb347', 500); },

    // 養成行動
    act(kind, stat) {
      const S = G.save;
      if (S.actionsLeft <= 0) return;
      const st = S.creatures[G.sel], cr = Data.CREATURES_BY_ID[G.sel];
      let msg = '', ok = true;
      if (kind === 'feed') {
        const cap = P.train_cap.stamina, cur = st.bonus.stamina || 0;
        if (cur >= cap) { ok = false; msg = '耐力上限已到頂'; } else { st.bonus.stamina = Math.min(cap, cur + P.feed_gain); msg = cr.name + ' 耐力上限 +' + P.feed_gain; }
      } else if (kind === 'train') {
        const cap = P.train_cap[stat], cur = st.bonus[stat] || 0, nm = { speed: '基礎速度', power: '力量', calm: '冷靜' }[stat];
        if (cur >= cap) { ok = false; msg = nm + ' 已到訓練上限'; } else { st.bonus[stat] = Math.min(cap, cur + P.train_gain[stat]); msg = cr.name + ' ' + nm + ' +' + P.train_gain[stat]; }
      } else if (kind === 'rest') {
        if (st.cond >= 100) { ok = false; msg = '狀態已滿，唔使休息'; } else { st.cond = Math.min(100, st.cond + P.rest_restore); msg = cr.name + ' 狀態 +' + P.rest_restore; }
      }
      G.trainPick = false;
      if (!ok) { G.toast(msg, '#ffb347'); return; }
      const lv = Sim.addExp(st, P.action_exp[kind], P);
      S.actionsLeft--;
      G.toast(msg + '（經驗 +' + P.action_exp[kind] + ')', '#ffd166');
      if (lv > 0) { G.toast(cr.name + ' 升級！Lv' + st.lv, '#6ee7a0', 730); UI.SFX.win(); } else UI.SFX.tap();
      G.persist();
    },

    // 開賽：只經 Api 建立比賽（表現層唔直接碰 Sim.createRace／Sim.step）
    startRace() {
      const stage = Data.STAGES[G.stageSel - 1];
      if (G.teamPick.length !== stage.teamSize) return;
      const setup = {
        seed: (Date.now() ^ (G.save.races * 7919)) & 0xffffff,   // 種子喺「比賽外」產生，之後全部由 sim 內 RNG 決定
        terrains: stage.terrains,
        teams: [G.teamPick.map(id => { const st = G.save.creatures[id]; return { id, lv: st.lv, bonus: Object.assign({}, st.bonus), cond: st.cond }; }),
                stage.opp.team.map(d => ({ id: d.id, lv: d.lv }))],
        ctrls: [{ kind: 'player' }, stage.opp.kind === 'shadow' ? { kind: 'shadow', script: stage.opp.script } : { kind: 'ai' }],
        meta: { stageId: stage.id }
      };
      G.race = G.newRaceState(Api.createMatch(setup), stage, G.teamPick.slice(), 3.2, false);
      G.scene = 'race'; UI.SFX.tap();
    },
    newRaceState(match, stage, teamIds, countdown, isReplay) {
      return { match, sim: match.race /* 只供除錯／測試讀取 */, view: Api.view(match), stage, teamIds, countdown, mul: 1, pops: [], evIdx: 0, endHandled: false, lastCount: 4, isReplay };
    },
    // 重播上一場（只按決策記錄；唔影響存檔／獎勵）
    startReplay() {
      if (!G.lastReplay) return;
      let match;
      try { match = Api.createPlayback(G.lastReplay, { mode: 'log' }); } catch (e) { G.toast('重播無法載入：' + e.message, '#ff6b6b', 500); return; }
      const stage = Data.STAGES[G.lastReplay.meta.stageId - 1];
      G.race = G.newRaceState(match, stage, [], 0.6, true);
      G.scene = 'race'; UI.SFX.tap();
    },
    onRaceEvents() {
      const R = G.race, evs = Api.events(R.match);
      while (R.evIdx < evs.length) {
        const e = evs[R.evIdx++], who = e.side === 0 ? '我方' : '對手', col = e.side === 0 ? '#6cb6ff' : '#ff8a7a';
        if (e.type === 'swap') { R.pops.push({ text: who + ' 換人', color: col, t0: UI.t, y: 200 }); UI.SFX.swap(); }
        else if (e.type === 'skill') {
          const nm = Data.SKILLS[e.skill].name;
          R.pops.push({ text: who + ' ' + nm + (e.blocked ? '（被風罩擋住）' : '！'), color: e.blocked ? '#9be3ff' : '#ffd166', t0: UI.t, y: 230 }); UI.SFX.skill();
        } else if (e.type === 'exhaust' && e.side === 0) { R.pops.push({ text: '耐力見底！換人？', color: '#ff6b6b', t0: UI.t, y: 260 }); UI.SFX.warn(); }
      }
    },
    finishRace() {
      const R = G.race, race = R.view, S = G.save;
      if (R.isReplay) { G.scene = 'result'; return; }
      if (G.result && G.result.raceRef === R) { G.scene = 'result'; return; }
      const win = race.winner === 0, rw = R.stage.reward, me = race.sides[0];
      const firstClear = win && !S.cleared[R.stage.id];
      const members = R.teamIds.map((id, i) => {
        const st = S.creatures[id], ran = me.team[i].onField, base = win ? rw.expWin : rw.expLose, exp = ran ? base : Math.round(base / 2);
        const before = st.lv; Sim.addExp(st, exp, P);
        if (ran) st.cond = Math.max(0, st.cond - P.cond_cost_per_race);
        return { id, exp, ran, lvBefore: before, lvAfter: st.lv };
      });
      Data.CREATURES.forEach(c => { const st = S.creatures[c.id]; st.cond = Math.min(100, st.cond + P.cond_regen_per_turn); });
      const ribbons = win ? rw.ribbonWin + (firstClear ? rw.ribbonFirst : 0) : rw.ribbonLose;
      S.ribbons += ribbons;
      if (win) S.cleared[R.stage.id] = true;
      S.races++; S.turn++; S.actionsLeft = P.actions_per_turn;
      let unlocked = '';
      if (firstClear) unlocked = R.stage.id < 3 ? '第 ' + (R.stage.id + 1) + ' 關「' + Data.STAGES[R.stage.id].name + '」' : '進化試煉（後續版本開放）';
      G.result = { raceRef: R, win, stage: R.stage, duration: race.duration, swaps: me.swaps, skills: me.skills, ribbons, members, firstClear, unlocked, allClear: !!(S.cleared[1] && S.cleared[2] && S.cleared[3]) };
      G.persist(); G.scene = 'result';
      G.stageSel = R.stage.id; G.teamPick = R.teamIds.slice();
    },

    tick(dt) {
      UI.t += dt;
      if (G.scene !== 'race') return;
      const R = G.race;
      if (R.countdown > 0) {
        R.countdown -= dt;
        const n = Math.ceil(R.countdown);
        if (n < R.lastCount) { R.lastCount = n; if (!R.isReplay) { if (n > 0) UI.SFX.count(); else UI.SFX.go(); } }
        return;
      }
      Api.advance(R.match, dt, R.mul);            // 固定步長累加器：幀率只影響畫面，唔影響結果
      R.view = Api.view(R.match);
      G.onRaceEvents();
      if (R.match.race.over && !R.endHandled) {
        R.endHandled = true;
        if (!R.isReplay) G.lastReplay = Api.getReplay(R.match);
        (R.view.winner === 0 ? UI.SFX.win : UI.SFX.lose)();
      }
    }
  };

  UI.sound = G.save.sound;
  UI.init(document.getElementById('game'), G);
  let last = performance.now();
  function frame(now) {
    const dt = Math.min(0.1, (now - last) / 1000); last = now;
    G.tick(dt); UI.draw(G);
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
  window.__wr = { G, UI, Sim, Api, Data };
})();
