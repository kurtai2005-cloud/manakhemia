/* 《微光小圃》 behavior.js — 寵物自主行為狀態機（DOM-free）。
   - clip 名／幀數／fps／優先級／可中斷／冷卻／接續 全部對齊遊美 art/CLIPS.json（data.js CLIPS）。
   - 固定步長（PARAMS.beh.fixedDt）、可設種子 RNG（sim.makeRng）；唔用 Date／Math.random。
   - 輸出：clip 名＋frame、位置 x（相對 CX，art px）、lift、dir（朝向，-1＝鏡像）、表情 expr、attach（圖示層 zzz／sweat…）、props、fx 請求。
   - 渲染層只負責「clip → 圖」；換物種／換美術 = 換圖集（docs/clip-format.md）。原創代碼。 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory(require('./data.js'), require('./sim.js'));
  else { root.Glimmer = root.Glimmer || {}; root.Glimmer.behavior = factory(root.Glimmer.data, root.Glimmer.sim); }
})(typeof self !== 'undefined' ? self : this, function (D, SIM) {
  'use strict';
  const P = D.PARAMS.beh, CL = D.CLIPS, SICK = D.PARAMS.sickThreshold, LK = P.look, FC = D.PARAMS.face;
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const rf = (r, a) => a[0] + (a[1] - a[0]) * r();
  const ri = (r, a) => a[0] + Math.floor(r() * (a[1] - a[0] + 1));
  const FIX = P.fixedDt;
  const VARIANTS = ['blink', 'sway', 'yawn'];
  const NOATT = [];
  const COOL_CLIP = { play: 'play', sunbathe: 'sunbathe', bump: 'pot_bump' };   // 自主狀態 → 冷卻所屬 clip
  const NONINT = { play: 1, wake: 1, startle: 1, bump: 1, grumpy: 1 };           // 不可中斷（忽略觸摸）

  function clipLen(name) { const c = CL[name]; return c.frames * (c.repeat || 1); }
  function clipDur(name) { return clipLen(name) / CL[name].fps; }
  function frameOf(name, t) {
    const c = CL[name], k = Math.floor(t * c.fps + 1e-9);
    if (c.repeat) return k < c.frames * c.repeat ? k % c.frames : c.frames - 1;
    if (c.loop) {
      if (c.loopFrom != null && k >= c.frames) return c.loopFrom + (k - c.frames) % (c.frames - c.loopFrom);
      return k % c.frames;
    }
    return Math.min(k, c.frames - 1);
  }
  function exprFor(s) {
    const n = s.needs, mn = Math.min(n.hunger, n.mood, n.clean, n.energy);
    for (const r of D.EXPR_RULES) {
      if (r.unwell) { if (s.stage !== 'egg' && mn < SICK) return r.expr; continue; }
      if (r.need && r.below != null) { if (n[r.need] < r.below || (r.orPoops && (s.poops || 0) >= r.orPoops)) return r.expr; continue; }
      if (r.need && r.atLeast != null) { if (n[r.need] >= r.atLeast && mn >= r.allAtLeast) return r.expr; continue; }
      return r.expr;
    }
    return 'neutral';
  }
  function formKey(s) { return s.stage === 'adult' ? (s.form === 'bright' ? 'radiant' : (s.form === 'soft' || s.form === 'lumi') ? 'soft' : 'dust') : 'sprout'; }   // 螢絨借柔光 clip

  function create(seed, opts) {
    opts = opts || {};
    const rng = SIM.makeRng(((seed >>> 0) ^ P.seedSalt) || 1);
    const b = {
      rng, pers: Object.assign({}, P.personality, opts.personality || {}), stateWeights: Object.assign({}, P.stateWeights, opts.stateWeights || {}),
      t: 0, acc: 0, state: 'stay', stateT: 0, phase: '', clip: 'idle', clipT: 0, frame: 0,
      x: 0, lift: 0, dir: 1, gaze: 0, expr: 'neutral', base: 'idle', stage: 'sprout', fkey: 'sprout',
      variant: null, variantT: 0, nextVariant: 0, nextDecide: 0,
      tx: 0, speed: P.walkSpeed, dur: 0, hopsLeft: 0, hopT: 0, hopDx: 0,
      item: null, props: [], fx: [], attach: NOATT, taps: [], petTaps: [], lastTouch: -99, grumpyCool: -1, cuddlyUntil: 0, afterWake: null, holdUntil: 0, stir: 0, awaySign: 0,
      potWobble: 0, steamT: 0, cool: {}, lastOverride: null, hitDone: false,
      log: { variants: [], enters: {}, time: {}, ticks: 0 },
      journal: [], jn: 0,
      // 視線：x/y＝平滑後視線向量（世界座標，-1..1；y 負＝上），q＝量化格（世界），ql＝相對身體朝向嘅格（畫眼用），src＝目標來源
      lrng: SIM.makeRng((((seed >>> 0) ^ LK.lookSalt) >>> 0) || 7), look: { x: 0, y: 0, tx: 0, ty: 0, q: 'C', ql: 'C', src: 'idle', cand: 'C', candT: 0, qT: 9, tapX: 0, tapY: null, tapUntil: -1, dragX: 0, dragY: null, dragUntil: -1, camUntil: -1, nextCam: 0, wanderX: 0, wanderY: 0, nextWander: 0, force: null },
      turn: null, show: { clip: 'idle', frame: 0 }, face: { eyes: 'neutral', mouth: 'neutral', closed: false, gaze: 'C' }, faceForce: null,    // 行為日誌（給音訊 cue／__qa.pet 用）：{n, t, ev: state|phase|variant|clip|impact|tap, name, ph}
    };
    b.nextVariant = rf(rng, P.variantEvery); b.nextDecide = rf(rng, P.decideEvery);
    b.look.nextCam = rf(b.lrng, LK.camEvery); b.look.nextWander = rf(b.lrng, LK.wanderEvery);
    return b;
  }

  function note(b, ev, name, ph) {
    b.journal.push({ n: ++b.jn, t: +b.t.toFixed(3), ev, name, ph: ph || '' });
    if (b.journal.length > P.journalMax) b.journal.shift();
  }
  function setClip(b, name) { if (b.clip !== name) { b.clip = name; b.clipT = 0; note(b, 'clip', name); } }
  function setPhase(b, ph) { b.phase = ph; b.stateT = 0; note(b, 'phase', b.state, ph); }
  function loopClip(b, name) { setClip(b, name); const d = clipDur(name); if (b.clipT >= d) b.clipT -= d; }
  function enter(b, name, phase) { b.state = name; b.phase = phase || ''; b.stateT = 0; b.log.enters[name] = (b.log.enters[name] || 0) + 1; note(b, 'state', name, b.phase); }
  function fx(b, type, x, y) { b.fx.push({ type, x, y }); if (b.fx.length > P.fxMax) b.fx.shift(); }
  function moveTo(b, tx, speed) {
    tx = clamp(tx, P.rangeX[0], P.rangeX[1]);
    const dx = tx - b.x, st = speed * FIX;
    if (Math.abs(dx) <= Math.max(st, P.arriveEps)) { b.x = tx; return true; }
    b.x += Math.sign(dx) * st; b.dir = Math.sign(dx); return false;
  }
  function hopLift(b, H, dur) { const u = clamp(b.hopT / dur, 0, 1); b.lift = -H * 4 * u * (1 - u); return u; }
  const H_OF = (b) => P.jumpHeight[b.stage === 'adult' ? 'adult' : 'sprout'];

  // ── 自主狀態權重（個性＋時段＋需求＋clip 冷卻）──
  function weights(b, ctx) {
    const w = Object.assign({}, b.stateWeights), pm = P.persMul, pe = b.pers, s = ctx.s;
    w.walk *= 1 - pm.timidWalk * pe.timid; w.jump *= 1 - pm.timidJump * pe.timid; w.bump *= 1 - pm.timidBump * pe.timid;
    w.nap *= (1 + pm.sleepyNap * pe.sleepy) * clamp(1 + (P.napEnergyRef - s.needs.energy) / 30, 0.3, 3);
    w.sunbathe *= 1 + pm.sleepySun * pe.sleepy;
    w.stay *= 1 + pm.stickyStay * pe.sticky;
    if (s.needs.mood < 70) w.play *= 2;                            // art weightMods：心情<70 ×2
    const pw = ctx.pw && ctx.pw.beh;
    if (pw) for (const k in w) if (pw[k] != null) w[k] *= pw[k];
    if (ctx.sun == null || ctx.sun < P.sunMinLight) w.sunbathe = 0;
    if (s.needs.energy < 25) { w.play = 0; w.jump = 0; }
    if (b.expr === 'tired') w.nap *= 2;
    if (b.expr === 'hungry' || b.expr === 'dirty') w.play *= 0.4;
    if (s.withdrawn && s.withdrawn.on) { const m = P.withdrawnMul; w.walk *= m.walk; w.jump *= m.jump; w.play *= m.play; w.nap *= m.nap; }
    for (const k in COOL_CLIP) if (b.t < (b.cool[k] || 0)) w[k] = 0;
    return w;
  }
  function pickW(r, w) {
    let tot = 0; for (const k in w) tot += Math.max(0, w[k]);
    if (tot <= 0) return 'stay';
    let x = r() * tot;
    for (const k in w) { x -= Math.max(0, w[k]); if (x <= 0) return k; }
    return 'stay';
  }

  // ── 待機變體（只喺基礎層係 idle 時抽）──
  function startVariant(b, s) {
    const w = {}, e = s.needs.energy, m = P.variantEnergyMul;
    for (const v of VARIANTS) w[v] = P.variantWeights[v];
    if (e < 60) { w.sway *= m.swayBelow60; w.yawn *= m.yawnBelow60; }
    if (e < 30) w.yawn *= m.yawnBelow30 / m.yawnBelow60;
    b.variant = pickW(b.rng, w); b.variantT = 0; b.clipT = 0; b.clip = b.variant; note(b, 'variant', b.variant);
    b.log.variants.push({ name: b.variant, start: b.t, end: null });
    if (b.log.variants.length > 600) b.log.variants.shift();
  }
  function endVariant(b) {
    const v = b.log.variants[b.log.variants.length - 1]; if (v && v.end == null) v.end = b.t;
    b.variant = null; b.nextVariant = rf(b.rng, P.variantEvery);
  }

  function startState(b, name, ctx) {
    const r = b.rng, pe = b.pers, pm = P.persMul;
    switch (name) {
      case 'walk': {
        const dist = rf(r, P.walkDist) * (1 - pm.stickyRange * pe.sticky);
        let sign = r() < 0.5 ? -1 : 1;
        if (b.x + sign * dist < P.rangeX[0] || b.x + sign * dist > P.rangeX[1]) sign = -sign;
        b.tx = clamp(b.x + sign * dist, P.rangeX[0], P.rangeX[1]); b.speed = P.walkSpeed * (1 - pm.timidSpeed * pe.timid);
        enter(b, 'walk'); break;
      }
      case 'jump': b.hopsLeft = ri(r, P.jumpHops); b.hopT = 0; b.hopDx = (r() < 0.5 ? -1 : 1) * P.hopDx; enter(b, 'jump'); break;
      case 'play': b.dur = rf(r, P.playDur); b.item = { kind: 'ball', x: 0, y: 0 }; enter(b, 'play'); b.clipT = 0; break;
      case 'nap': b.dur = rf(r, P.napDur); enter(b, 'nap', 'fall'); b.clipT = 0; break;
      case 'sunbathe': b.tx = P.sunSpotX; b.speed = P.walkSpeed * (1 - pm.timidSpeed * pe.timid); b.dur = rf(r, P.sunDur); enter(b, 'sunbathe', 'go'); break;
      case 'bump': {
        const fk = b.fkey === 'dust' ? 'soft' : b.fkey;
        b.tx = P.potX + D.FORMS[fk].pot[0]; b.speed = P.walkSpeed * (1 - pm.timidSpeed * pe.timid); enter(b, 'bump', 'go'); break;
      }
      default: enter(b, 'stay'); b.nextDecide = rf(r, P.decideEvery);
    }
  }
  function backToStay(b) { b.item = null; b.lift = 0; enter(b, 'stay'); b.nextDecide = rf(b.rng, P.decideEvery); if (b.variant) endVariant(b); }
  function goWake(b, after) { b.item = null; b.afterWake = after || null; enter(b, 'wake'); b.clipT = 0; if (b.variant) endVariant(b); }
  function goReact(b) { enter(b, 'react'); b.dur = clipDur('emo_happy'); b.clipT = 0; }
  function goStartle(b, tapX) {
    enter(b, 'startle'); b.dur = P.tap.startleDur; b.clipT = 0; b.awaySign = tapX == null ? 0 : (b.x >= tapX ? 1 : -1); fx(b, 'spark', 0, -50);
  }

  function spawnProps(b) {
    const n = ri(b.rng, P.bumpProps);
    for (let i = 0; i < n; i++) {
      const kind = D.PROP_KINDS[Math.floor(b.rng() * D.PROP_KINDS.length)];
      b.props.push({ kind, x: P.potX + (b.rng() - 0.5) * 8, y: -14, vx: (b.rng() - 0.3) * 34, vy: -(26 + b.rng() * 22), gy: Math.floor(b.rng() * 9), age: 0, life: rf(b.rng, P.propLife), landed: false });
    }
    while (b.props.length > P.propsMax) b.props.shift();
    b.potWobble = 1;
  }
  function stepProps(b) {
    let dead = false;
    for (const p of b.props) {
      p.age += FIX; if (p.age >= p.life) dead = true;
      if (!p.landed) { p.x += p.vx * FIX; p.y += p.vy * FIX; p.vy += 140 * FIX; if (p.y >= p.gy && p.vy > 0) { p.y = p.gy; p.landed = true; p.vx = 0; } }
    }
    if (dead) b.props = b.props.filter(p => p.age < p.life);
  }

  // ── 觸摸 ──
  function tap(b, kind, x, y, opt) { b.taps.push({ kind, x: x || 0, y: y == null ? null : y, hold: !!(opt && opt.hold) }); if (b.taps.length > 12) b.taps.shift(); }
  // P2：拖動手指 → 眼神跟手指（每次 move 續期 dragHold 秒；放手後好快回復）
  function drag(b, x, y) { const L = b.look; L.dragX = x; L.dragY = y; L.dragUntil = b.t + (LK.dragHoldSec || 0.4); L.snap = true; b.log.enters.drag = (b.log.enters.drag || 0) + 1; }
  function dragEnd(b) { b.look.dragUntil = -1; }
  // D2：望向觸點；turn＝true 時觸點喺背後就轉身（有 turn_back clip 由渲染層播，冇就即刻翻轉）
  function lookAtTap(b, tp, turn) {
    const L = b.look; L.tapX = tp.x; L.tapY = tp.y; L.tapUntil = b.t + LK.tapLookSec; L.snap = true;
    if (!turn) return;
    const dx = tp.x - b.x;
    if (Math.abs(dx) > LK.turnMinDx && Math.sign(dx) !== b.dir) {
      const tb = CL.turn_back && CL.turn_back.ready;      // 有 turn_back 美術：播完先回原 clip（顯示層覆蓋，唔改狀態機）
      b.dir = Math.sign(dx); b.turn = { t0: b.t, until: b.t + (tb ? clipDur('turn_back') : LK.turnSec), to: b.dir, clip: tb ? 'turn_back' : null };
      if (tb) note(b, 'clip', 'turn_back');
      note(b, 'turn', b.dir > 0 ? 'R' : 'L'); b.log.enters.turn = (b.log.enters.turn || 0) + 1;
    }
  }
  function processTaps(b, ctx, forced) {
    const T = P.tap;
    while (b.taps.length) {
      const tp = b.taps.shift();
      if (tp.hold) {                               // P2：長按（≥300ms）唔觸發回頭／反應，只望住（蹭手留第三段）
        if (!((forced && ctx.s.sleeping) || b.state === 'nap')) lookAtTap(b, tp, false);
        note(b, 'tap', 'hold'); b.log.enters.hold = (b.log.enters.hold || 0) + 1; continue;
      }
      if (tp.kind === 'wake') {                    // 睡眠中點寵物＝輕喚醒（sim 已關燈起身）：睏睏表情 sleepyHold 秒，唔鬧脾氣、唔扣需求
        b.petTaps.length = 0; b.holdUntil = b.t + T.sleepyHold; note(b, 'tap', 'lightWake'); b.log.enters.lightWake = (b.log.enters.lightWake || 0) + 1;
        if (b.state !== 'wake' && b.state !== 'simsleep') goWake(b, null);
        continue;
      }
      if (forced && ctx.s.sleeping && tp.kind === 'pet') { b.petTaps.length = 0; b.stir = b.t + 1.2; note(b, 'tap', 'sleepStir'); b.log.enters.sleepStir = (b.log.enters.sleepStir || 0) + 1; continue; }   // 睡眠中連點：唔鬧脾氣，只係翻身（zzz 加快）
      // 不適／事件／撞花盆／已經鬧緊都會吞普通觸摸。連點 5 下仍然要出獨立事件請求。
      // wake 唔計：小睡輕喚醒嗰陣嘅連點要保持「唔鬧脾氣」（wake 動畫期間原本就忽略觸摸）。
      if (tp.kind === 'pet' && !ctx.s.sleeping && b.state !== 'nap' && b.state !== 'wake' && (forced || b.state === 'bump' || b.state === 'grumpy')) {
        lookAtTap(b, tp, false);   // 呢啲狀態唔轉身，但視線仍然跟觸點（D2）
        b.petTaps.push(b.t); b.petTaps = b.petTaps.filter(t => b.t - t <= T.rapidWindow);
        const rapid = b.petTaps.length; note(b, 'tap', 'pet', String(rapid));
        if (rapid >= T.rapidCount && b.t >= b.grumpyCool) {
          b.petTaps.length = 0; b.grumpyCool = b.t + T.grumpyDur + T.grumpyCooldown; b.tantrumReq = (b.tantrumReq || 0) + 1; note(b, 'tap', 'tantrum');
        }
        b.log.enters.tapIgnored = (b.log.enters.tapIgnored || 0) + 1; continue;
      }
      if (!forced && tp.kind === 'pet' && (b.state === 'startle' || b.state === 'play')) {      // 不可中斷動作期間嘅連點：照計，夠數就升級（撒嬌／鬧脾氣）
        b.lastTouch = b.t; b.petTaps.push(b.t); b.petTaps = b.petTaps.filter(t => b.t - t <= Math.max(T.cuddlyWindow, T.rapidWindow));
        const rapid = b.petTaps.length, quick = b.petTaps.filter(t => b.t - t <= T.cuddlyWindow).length; note(b, 'tap', 'pet', String(rapid));
        if (rapid >= T.rapidCount && b.t >= b.grumpyCool) { b.petTaps.length = 0; b.dur = T.grumpyDur; b.steamT = 0; b.item = null; enter(b, 'grumpy'); b.grumpyCool = b.t + T.grumpyDur + T.grumpyCooldown; b.tantrumReq = (b.tantrumReq || 0) + 1; note(b, 'tap', 'tantrum'); continue; }
        if (quick >= T.cuddlyCount && b.state === 'startle') { b.cuddlyUntil = b.t + 0.8; enter(b, 'cuddly'); b.clipT = 0; continue; }
      }
      const asleep = (forced && ctx.s.sleeping) || b.state === 'nap';
      if ((tp.kind === 'pet' || tp.kind === 'ground') && !asleep) lookAtTap(b, tp, tp.kind === 'pet' && !forced && !NONINT[b.state] && b.state !== 'cuddly');
      if (forced || NONINT[b.state] || (b.state === 'nap' && b.phase === 'fall')) { b.log.enters.tapIgnored = (b.log.enters.tapIgnored || 0) + 1; continue; }
      if (tp.kind === 'pet') {
        const gap = b.t - b.lastTouch; b.lastTouch = b.t;
        if (b.state === 'nap') { b.petTaps.length = 0; note(b, 'tap', 'sleepWake'); b.holdUntil = b.t + T.sleepyHold; goWake(b, null); continue; }   // 小睡中被點／連點：輕喚醒（睏睏表情），唔鬧脾氣
        b.petTaps.push(b.t); b.petTaps = b.petTaps.filter(t => b.t - t <= Math.max(T.cuddlyWindow, T.rapidWindow));
        const rapid = b.petTaps.length, quick = b.petTaps.filter(t => b.t - t <= T.cuddlyWindow).length;
        note(b, 'tap', 'pet', String(rapid));
        if (b.state === 'nap') { goWake(b, 'startle'); continue; }           // 睡中被點：wake → emo_surprised
        if (rapid >= T.rapidCount && b.t >= b.grumpyCool) {
          b.petTaps.length = 0; b.dur = T.grumpyDur; b.steamT = 0; enter(b, 'grumpy'); b.grumpyCool = b.t + T.grumpyDur + T.grumpyCooldown; b.tantrumReq = (b.tantrumReq || 0) + 1; note(b, 'tap', 'tantrum'); if (b.variant) endVariant(b);
        } else if (quick >= T.cuddlyCount) {
          b.cuddlyUntil = b.t + 0.8;
          if (b.state !== 'cuddly') { enter(b, 'cuddly'); b.clipT = 0; if (b.variant) endVariant(b); }
        } else if (b.state === 'cuddly') b.cuddlyUntil = b.t + 0.8;
        else if (gap > T.idleSurpriseSec) { goStartle(b, tp.x); if (b.variant) endVariant(b); }
        else { goReact(b); fx(b, 'spark', 0, -50); if (b.variant) endVariant(b); }
      } else if (tp.kind === 'ground') {
        b.lastTouch = b.t; note(b, 'tap', 'ground');
        const p = clamp(T.followBase + P.persMul.stickyFollow * b.pers.sticky - P.persMul.timidFollowPenalty * b.pers.timid, 0, 1);
        b.dir = tp.x >= b.x ? 1 : -1;
        if (b.state === 'nap') { goWake(b, null); continue; }
        if (b.rng() < p) { b.tx = tp.x; b.speed = P.followSpeed; enter(b, 'follow'); if (b.variant) endVariant(b); }
        else if (b.state === 'stay' && !b.variant && b.base === 'idle') { b.variant = 'blink'; b.variantT = 0; b.clipT = 0; b.clip = 'blink'; b.log.variants.push({ name: 'blink', start: b.t, end: null }); }
      }
    }
  }

  // ── 單一固定步 ──
  function step(b, ctx) {
    b.t += FIX; b.stateT += FIX; b.clipT += FIX; b.log.ticks++;
    const s = ctx.s;
    b.stage = s.stage === 'adult' ? 'adult' : 'sprout'; b.fkey = formKey(s);
    b.expr = exprFor(s); if (b.t < b.holdUntil && b.expr !== 'sick') b.expr = 'tired'; b.base = D.EXPRESSIONS[b.expr].clip;
    b.lift = 0; b.gaze = 0;
    b.potWobble = Math.max(0, b.potWobble - P.potWobbleDecay * FIX);
    stepProps(b);
    if (s.stage === 'egg') { b.taps.length = 0; setClip(b, 'idle'); b.frame = 0; b.attach = NOATT; return; }
    const unwell = b.expr === 'unwell';
    if (b.state === 'simsleep' && !s.sleeping && !ctx.override) { enter(b, 'wake'); b.afterWake = null; b.clipT = 0; }
    const forcedKind = ctx.override ? 'override' : s.sleeping ? 'simsleep' : unwell ? 'unwell' : ctx.event ? 'event' : null;
    const hold = forcedKind && forcedKind !== 'override' && b.state === 'wake';     // wake 不可中斷
    processTaps(b, ctx, !!forcedKind);
    b.log.time[b.state] = (b.log.time[b.state] || 0) + FIX;
    if (forcedKind && !hold) forcedStep(b, ctx, forcedKind);
    else {
      if (b.state === 'override' || b.state === 'simsleep' || b.state === 'unwell' || b.state === 'event') {
        const eat = b.state === 'override' && b.lastOverride === 'eat';
        b.item = null; b.lift = 0; if (eat) goReact(b); else backToStay(b);   // eat → emo_happy（art next）
      }
      autoStep(b, ctx);
    }
    b.frame = frameOf(b.clip, b.clipT);
    b.attach = attachOf(b);
    if (b.turn && b.t >= b.turn.until) b.turn = null;
    const tc = b.turn && b.turn.clip && !s.sleeping ? b.turn.clip : null;
    b.show.clip = tc || b.clip; b.show.frame = tc ? Math.min(CL[tc].frames - 1, Math.floor((b.t - b.turn.t0) * CL[tc].fps + 1e-6)) : b.frame;
    stepLook(b, ctx); b.face = faceFor(b);
  }
  function attachOf(b) {
    const a = CL[b.clip].attach; if (!a) return NOATT;
    let all = true; for (const x of a) if (b.frame < x.from) { all = false; break; }
    return all ? a : a.filter(x => b.frame >= x.from);
  }

  function forcedStep(b, ctx, kind) {
    const s = ctx.s;
    if (b.state !== kind) { enter(b, kind, kind === 'event' ? '' : 'go'); b.item = null; if (b.variant) endVariant(b); }
    if (kind === 'override') {
      const nm = CL[ctx.override] ? ctx.override : 'emo_happy'; b.lastOverride = nm;
      const hop = nm === 'celebrate' || ctx.override === 'happy';
      const arrived = moveTo(b, 0, P.retreatSpeed); setClip(b, nm);
      if (hop && arrived) { b.hopT += FIX; if (b.hopT >= P.hopDur) b.hopT = 0; hopLift(b, H_OF(b) * 0.5, P.hopDur); }
      return;
    }
    if (kind === 'simsleep' || kind === 'unwell') {
      if (b.phase === 'go') { const arrived = moveTo(b, 0, P.walkSpeed * 1.3); setClip(b, 'walk'); if (arrived) { setPhase(b, kind === 'simsleep' ? 'fall' : 'sick'); b.clipT = 0; } return; }
      if (b.phase === 'fall') { setClip(b, 'fall_asleep'); if (b.stateT >= clipDur('fall_asleep')) setPhase(b, 'loop'); return; }
      if (b.phase === 'loop') { setClip(b, 'sleep_loop'); return; }
      setClip(b, 'sick'); return;
    }
    // event 腳本
    const ev = ctx.event, v = ev.vis || {}, id = ev.id;
    if (b.evId !== id) { b.evId = id; note(b, 'event', id); }      // 日誌：事件開始（__qa.pet.log 可見 firefly_walk 等）
    if (id === 'butterfly') {
      const dx = v.rx - b.x; b.gaze = Math.sign(dx);
      if (Math.abs(dx) > 14) { moveTo(b, v.rx, P.followSpeed); setClip(b, 'walk'); }
      else { b.hopT += FIX; const u = hopLift(b, H_OF(b) * 0.7, P.hopDur); setClip(b, 'jump'); b.clipT = u * clipDur('jump'); if (b.hopT >= P.hopDur) b.hopT = 0; }
    } else if (id === 'firefly_walk') {
      const dx = v.rx - b.x; b.gaze = Math.sign(dx) || b.gaze;
      if (Math.abs(dx) > 8) { moveTo(b, v.rx, P.walkSpeed * 1.4); setClip(b, 'walk'); }
      else { b.hopT += FIX; if (b.hopT >= P.hopDur) b.hopT = 0; hopLift(b, H_OF(b) * 0.4, P.hopDur); loopClip(b, 'play'); }   // play＝現有玩耍 clip（待定→placeholder）
    } else if (id === 'meteor') setClip(b, 'lookup');
    else if (id === 'rainbow') { b.hopT += FIX; if (b.hopT >= P.hopDur) b.hopT = 0; hopLift(b, H_OF(b) * 0.5, P.hopDur); loopClip(b, 'emo_happy'); }
    else if (id === 'flash') { b.hopT += FIX; if (b.hopT >= P.hopDur) b.hopT = 0; hopLift(b, H_OF(b) * 0.5, P.hopDur); loopClip(b, 'celebrate'); if (b.hopT < FIX) fx(b, 'spark', (b.rng() - 0.5) * 30, -50); }
    else if (id === 'gift') {
      if (ev.t < 0.7) { moveTo(b, -10, P.followSpeed); setClip(b, 'walk'); }
      else { b.hopT += FIX; if (b.hopT >= P.hopDur) b.hopT = 0; hopLift(b, H_OF(b) * 0.6, P.hopDur); loopClip(b, 'cheer_jump'); }
    } else if (id === 'treasure') {
      if (!v.found) { const a = moveTo(b, v.digX, P.walkSpeed * 1.6); setClip(b, a ? 'dig' : 'walk'); if (a) loopClip(b, 'dig'); }
      else { b.hopT += FIX; if (b.hopT >= P.hopDur) b.hopT = 0; hopLift(b, H_OF(b) * 0.6, P.hopDur); loopClip(b, 'cheer_jump'); }
    } else if (id === 'grumpy' || id === 'grumpy_tap') {
      b.steamT += FIX; if (b.steamT >= 0.45) { b.steamT = 0; fx(b, 'steam', (b.rng() - 0.5) * 18, -40); } loopClip(b, 'grumpy'); b.x += Math.sin(b.t * 50) * 0.15;
    } else if (id === 'sleeptalk') {
      if (b.phase === 'go' || b.phase === '') { const a = moveTo(b, 0, P.walkSpeed * 1.3); setClip(b, 'walk'); if (a) { setPhase(b, 'fall'); b.clipT = 0; } }
      else if (b.phase === 'fall') { setClip(b, 'fall_asleep'); if (b.stateT >= clipDur('fall_asleep')) setPhase(b, 'loop'); }
      else loopClip(b, 'sleep_loop');
    } else setClip(b, 'idle');
  }

  function autoStep(b, ctx) {
    const r = b.rng, s = ctx.s;
    switch (b.state) {
      case 'stay': {
        const idleBase = b.base === 'idle';
        setClip(b, b.variant || b.base);
        if (b.clip === b.base && b.base !== 'idle') loopClip(b, b.base);
        if (b.variant) { b.variantT += FIX; if (b.variantT >= clipDur(b.variant)) endVariant(b); }
        else {
          if (idleBase) {
            b.nextVariant -= FIX;
            if (b.nextVariant <= 0) { startVariant(b, s); break; }
          }
          if (b.expr === 'tired' && b.stateT >= 10) { startState(b, 'nap', ctx); break; }   // 精力<30 且閒置>10s 必定入睡（art weightMods）
          b.nextDecide -= FIX;
          if (b.nextDecide <= 0) { const n = pickW(r, weights(b, ctx)); if (n === 'stay') b.nextDecide = rf(r, P.decideEvery); else startState(b, n, ctx); }
        }
        break;
      }
      case 'walk': case 'follow': {
        loopClip(b, 'walk'); b.gaze = b.dir;
        if (moveTo(b, b.tx, b.speed)) { if (b.state === 'follow') goReact(b); else backToStay(b); }
        break;
      }
      case 'jump': {
        b.hopT += FIX; const u = hopLift(b, H_OF(b), P.hopDur); setClip(b, 'jump'); b.clipT = u * clipDur('jump');
        b.x = clamp(b.x + b.hopDx * FIX / P.hopDur, P.rangeX[0], P.rangeX[1]);
        if (b.hopT >= P.hopDur) { b.hopT = 0; b.hopsLeft--; b.lift = 0; if (b.hopsLeft <= 0) backToStay(b); }
        break;
      }
      case 'play': {
        loopClip(b, 'play'); const u = b.stateT;
        b.item.x = b.dir * 16 + Math.sin(u * 2.4) * 10; b.item.y = -Math.abs(Math.sin(u * 4.8)) * 22;
        b.gaze = b.dir;
        if (b.stateT >= b.dur) { b.cool.play = b.t + CL.play.cooldown; backToStay(b); }
        break;
      }
      case 'nap': {
        if (b.phase === 'fall') { setClip(b, 'fall_asleep'); if (b.stateT >= clipDur('fall_asleep')) setPhase(b, 'loop'); }
        else { loopClip(b, 'sleep_loop'); if (b.stateT >= b.dur) goWake(b, null); }
        break;
      }
      case 'wake': {
        setClip(b, 'wake');
        if (b.stateT >= clipDur('wake')) { const a = b.afterWake; b.afterWake = null; if (a === 'startle') goStartle(b, null); else backToStay(b); }
        break;
      }
      case 'sunbathe': {
        if (b.phase === 'go') { const a = moveTo(b, b.tx, b.speed); loopClip(b, 'walk'); b.gaze = b.dir; if (a) { setPhase(b, 'lie'); b.cool.sunbathe = b.t + P.envCooldown; } }
        else {
          loopClip(b, 'sunbathe');
          if (ctx.sun != null && ctx.sun < P.sunMinLight * 0.5) b.stateT = b.dur;  // 日落就起身
          if (b.stateT >= b.dur) backToStay(b);
        }
        break;
      }
      case 'bump': {
        if (b.phase === 'go') { const a = moveTo(b, b.tx, b.speed); loopClip(b, 'walk'); b.gaze = b.dir; if (a) { setPhase(b, 'hit'); b.clip = 'pot_bump'; b.clipT = 0; note(b, 'clip', 'pot_bump'); b.dir = -1; b.cool.bump = b.t + P.envCooldown; } }
        else {
          setClip(b, 'pot_bump');
          if (!b.hitDone && b.clipT >= P.bumpImpactFrame / CL.pot_bump.fps) { b.hitDone = true; note(b, 'impact', 'pot_bump'); spawnProps(b); fx(b, 'dust', P.potX + 8, -4); }
          if (b.clipT >= clipDur('pot_bump')) { b.hitDone = false; backToStay(b); }
        }
        break;
      }
      case 'grumpy': {
        loopClip(b, 'grumpy'); b.steamT += FIX; b.x += Math.sin(b.t * 50) * 0.15;
        if (b.steamT >= 0.4) { b.steamT = 0; fx(b, 'steam', (r() - 0.5) * 18, -40); }
        if (b.stateT >= b.dur) backToStay(b);
        break;
      }
      case 'react': { setClip(b, 'emo_happy'); if (b.stateT >= b.dur) backToStay(b); break; }
      case 'cuddly': { loopClip(b, 'emo_cuddly'); if (b.t >= b.cuddlyUntil && b.stateT >= P.tap.cuddlyMin) backToStay(b); break; }
      case 'startle': {
        setClip(b, 'emo_surprised');
        if (b.stateT >= b.dur) {
          if (b.awaySign && b.pers.timid >= 0.5 && r() < P.tap.timidAwayChance) {     // 膽小：60% 走開
            b.tx = clamp(b.x + b.awaySign * rf(r, P.walkDist), P.rangeX[0], P.rangeX[1]); b.speed = P.followSpeed * 0.7; enter(b, 'walk');
          } else backToStay(b);
        }
        break;
      }
      default: backToStay(b);
    }
  }

  // ── F2 視線：揀目標 → 平滑 → 量化（L/CL/C/CR/R/U/D）──
  const MIRROR = { L: 'R', CL: 'CR', C: 'C', CR: 'CL', R: 'L', U: 'U', D: 'D' };
  function quantGaze(gx, gy) {
    const q = LK.quant;
    if (gy <= -q.v && -gy >= Math.abs(gx)) return 'U';
    if (gy >= q.v && gy >= Math.abs(gx)) return 'D';
    if (gx <= -q.side) return 'L'; if (gx < -q.center) return 'CL';
    if (gx >= q.side) return 'R'; if (gx > q.center) return 'CR';
    return 'C';
  }
  const SLEEPCLIP = { sleep_loop: 1, fall_asleep: 1 };
  function lookTarget(b, ctx) {
    const L = b.look, r = b.lrng, t = b.t, headY = LK.headY[b.stage === 'adult' ? 'adult' : 'sprout'] + b.lift;
    const pt = (x, y, src) => { L.src = src; return [clamp((x - b.x) / LK.rangeX, -1, 1), clamp((y - headY) / LK.rangeY, -1, 1)]; };
    const cam = () => { L.src = 'camera'; return [0, 0]; };
    if (L.force) { L.src = 'force'; return null; }
    if (SLEEPCLIP[b.clip] || b.state === 'simsleep') { L.src = 'closed'; return [0, 0.2]; }
    if (t < L.dragUntil) return pt(L.dragX, L.dragY == null ? headY : L.dragY, 'finger');
    if (t < L.tapUntil) return pt(L.tapX, L.tapY == null ? headY : L.tapY, 'tap');
    const ev = ctx && ctx.event, v = ev && ev.vis;
    if (b.state === 'event' && ev) {
      if ((ev.id === 'firefly_walk' || ev.id === 'butterfly') && v && v.rx != null) return pt(v.rx, ev.id === 'butterfly' && v.by != null ? -40 : -34, ev.id === 'firefly_walk' ? 'firefly' : 'butterfly');
      if (ev.id === 'meteor' || ev.id === 'rainbow') { L.src = 'sky'; return [0, -1]; }
    }
    if (b.state === 'bump') return pt(P.potX, -12, 'pot');
    if (b.state === 'sunbathe' && b.phase === 'lie') { L.src = 'sky'; return [b.dir * 0.2, -0.8]; }
    if (b.state === 'play' && b.item) return pt(b.x + b.item.x, b.item.y, 'item');
    if (b.state === 'override') return cam();
    const moving = b.clip === 'walk';
    if (moving) {                               // A1：邊行邊望——望前面，間中望鏡頭
      if (t < L.camUntil) return cam();
      if (t >= L.nextCam) { L.camUntil = t + rf(r, LK.walkCamDur); L.nextCam = L.camUntil + rf(r, LK.walkCamEvery); return cam(); }
      L.src = 'walk'; return [b.dir * LK.walkGx, LK.walkGy];
    }
    if (b.state === 'startle' || b.state === 'grumpy' || b.state === 'cuddly' || b.state === 'react') return cam();
    if (t < L.camUntil) return cam();           // 待機：間中望鏡頭、東張西望
    if (t >= L.nextCam) { L.camUntil = t + rf(r, LK.camDur); L.nextCam = L.camUntil + rf(r, LK.camEvery); return cam(); }
    if (t >= L.nextWander) { L.wanderX = (r() * 2 - 1) * LK.wanderGx; L.wanderY = (r() * 2 - 1) * LK.wanderGy; L.nextWander = t + rf(r, LK.wanderEvery); }
    L.src = 'idle'; return [L.wanderX, L.wanderY];
  }
  function stepLook(b, ctx) {
    const L = b.look, tg = lookTarget(b, ctx);
    if (!tg) {                                  // QA 強制格
      const q = L.force; L.q = q; L.cand = q; L.ql = b.dir < 0 ? MIRROR[q] : q;
      const v = { L: [-1, 0], CL: [-0.4, 0], C: [0, 0], CR: [0.4, 0], R: [1, 0], U: [0, -1], D: [0, 1] }[q] || [0, 0]; L.x = L.tx = v[0]; L.y = L.ty = v[1]; return;
    }
    L.tx = tg[0]; L.ty = tg[1];
    const k = 1 - Math.exp(-(L.snap ? LK.smoothTap : LK.smooth) * FIX);
    L.x += (L.tx - L.x) * k; L.y += (L.ty - L.y) * k;
    if (L.snap && Math.abs(L.tx - L.x) < 0.05 && Math.abs(L.ty - L.y) < 0.05) L.snap = false;
    const c = quantGaze(L.x, L.y);
    if (c !== L.cand) { L.cand = c; L.candT = 0; } else L.candT += FIX;
    L.qT += FIX;
    if (c !== L.q && L.candT >= LK.holdSec - 1e-9 && L.qT >= (LK.dwellSec || 0) - 1e-9) { L.q = c; L.qT = 0; }
    L.ql = b.dir < 0 ? MIRROR[L.q] : L.q;
    if (b.clip === 'walk' || b.state === 'play') b.gaze = b.dir;      // 舊 b.gaze（-1/0/1）保持兼容
  }
  // F1：clip／需求 → 眼款＋嘴款（閉眼款只得 C）
  function faceFor(b) {
    const f = b.face, ff = b.faceForce, clip = b.show.clip, frame = b.show.frame;
    let em = (FC.clipMap[clip]) || (clip === 'blink' && FC.blinkFrames.includes(frame) ? ['sleepy', null] : null) || FC.exprMap[b.expr] || FC.exprMap.neutral;
    if (clip === 'blink' && !FC.clipMap.blink) em = FC.blinkFrames.includes(frame) ? ['sleepy', (FC.exprMap[b.expr] || FC.exprMap.neutral)[1]] : (FC.exprMap[b.expr] || FC.exprMap.neutral);
    if (clip === 'fall_asleep' && frame < 2) em = ['sleepy', 'neutral'];
    f.eyes = (ff && ff.eyes) || em[0]; f.mouth = (ff && ff.mouth) || em[1] || 'neutral';
    f.closed = FC.closedEyes.includes(f.eyes);
    f.gaze = f.closed ? 'C' : b.look.ql;
    f.head = (f.eyes === 'happy' && b.look.ql && b.look.ql !== 'C') ? b.look.ql : 'C';   // P2：開心閉眼冇得轉眼珠 → 頭部微轉表達視線
    f.clip = clip; f.frame = frame;
    f.blink = clip === 'blink' && FC.blinkFrames.includes(frame);
    return f;
  }

  /* 每幀呼叫：dt 實時秒；ctx = { s（sim state）, pw（lighting.compute 結果）, sun（0–1）, override（'eat'|'happy'|'celebrate'|null）, event（{id,t,dur,vis}|null） } */
  function update(b, dt, ctx) {
    b.acc += Math.min(dt, 0.25);
    let n = 0;
    while (b.acc >= FIX - 1e-9 && n < 40) { step(b, ctx); b.acc -= FIX; n++; }
    if (b.acc < 0 || n >= 40) b.acc = 0;
  }

  // debug／測試：強制進入狀態或變體
  function force(b, name, ctx) {
    if (VARIANTS.includes(name)) { if (b.state !== 'stay') backToStay(b); if (b.variant) endVariant(b); b.variant = name; b.variantT = 0; b.clipT = 0; b.clip = name; note(b, 'variant', name); b.log.variants.push({ name, start: b.t, end: null }); return; }
    if (b.variant) endVariant(b);
    if (name === 'grumpy') { b.dur = P.tap.grumpyDur; b.steamT = 0; enter(b, 'grumpy'); return; }
    if (name === 'react') { goReact(b); return; }
    if (name === 'startle') { goStartle(b, null); return; }
    if (name === 'cuddly') { b.cuddlyUntil = b.t + 1.5; enter(b, 'cuddly'); b.clipT = 0; return; }
    if (name === 'wake') { goWake(b, null); return; }
    startState(b, name, ctx || {});
  }

  return { create, update, step, tap, drag, dragEnd, note, force, exprFor, frameOf, clipDur, clipLen, formKey, weights, quantGaze, faceFor, MIRROR, FIX, VARIANTS };
});
