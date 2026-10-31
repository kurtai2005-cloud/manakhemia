/* 《微光小圃》 audio.js — 音訊導演（DOM-free、可測試）＋ WebAudio 引擎（只喺瀏覽器）。
   - Director：由行為日誌（behavior.journal）、事件、需求、時段決定「播咩 cue」；全部規則（最短間隔／冷卻／事件優先／touch 輪流／連點唔播 touch…）喺呢度，Node 可測。
   - Engine：WebAudio。BGM 按時段 crossfade（喺小節線開始，3.5294s／小節，用秒排程；目標 loop 由 (b+1) mod 小節數 開始，和弦對齊）；
     loop 用 BufferSource.loop（sample-accurate）；SFX 解碼後即播；需先有使用者手勢先解鎖 AudioContext。
   - 音檔來自遊音 audio/（原檔不改）；cue 表在 data.js AUDIO。原創代碼。 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory(require('./data.js'), require('./sim.js'));
  else { root.Glimmer = root.Glimmer || {}; root.Glimmer.audio = factory(root.Glimmer.data, root.Glimmer.sim); }
})(typeof self !== 'undefined' ? self : this, function (D, SIM) {
  'use strict';
  const A = D.PARAMS.audio, AU = D.AUDIO, CUES = AU.cues;
  const minNeed = (s) => Math.min(s.needs.hunger, s.needs.mood, s.needs.clean, s.needs.energy);

  // ═════════ Director（純邏輯）═════════
  function createDirector(seed) {
    return {
      rng: SIM.makeRng(((seed >>> 0) ^ 0xa0d10) || 1), t: 0, jn: 0, queue: [], lastPet: -99, cdUntil: {}, touchAlt: 0,
      warnAt: { hungry: -999, sleepy: -999, unc: -999 }, evId: null, evBlockUntil: -1, combo: 0,
      loops: { sleep_breath: false, sunbathe: false }, bgm: null, stats: { cues: 0, skipped: 0 }, alt: {}, lastAB: {},
    };
  }
  const SFX_AB = { sneeze: 1, scratch: 1, step_hop: 1, step_drag: 1, step_plod: 1, bug_pat: 1, nuzzle_purr: 1, reunion_happy: 1 };   // 第三段加 nuzzle_purr／reunion_happy
  function rateFor(d, c) { if (c.fixedRate) return c.fixedRate; return c.rate ? A.petRate[0] + (A.petRate[1] - A.petRate[0]) * d.rng() : 1; }
  // 嘗試出一個 cue（遵守冷卻／間隔／事件優先）；after＝延遲秒
  function emit(d, out, name, after, opts) {
    const c = CUES[name]; if (!c) throw new Error('unknown cue ' + name);
    opts = opts || {};
    const at = d.t + (after || 0);
    if (after > 0 && !opts.now) { d.queue.push({ at, name, opts: Object.assign({}, opts, { now: true }) }); return false; }
    const pet = c.bus === 'pet';
    if (pet && d.t < d.evBlockUntil && !opts.force) { d.stats.skipped++; return false; }                 // 事件優先
    const ck = c.cdKey || name;
    if (c.cd && d.t < (d.cdUntil[ck] || -1)) { d.stats.skipped++; return false; }
    if (c.gap && d.t - d.lastPet < A.petMinGap && !opts.force) { d.stats.skipped++; return false; }     // 寵物聲最短間隔
    if (c.cd) d.cdUntil[ck] = d.t + c.cd;
    if (pet && !c.noLast && !/touch|turn/.test(name)) d.lastPet = d.t;   // 腳步聲（noLast）唔佔寵物聲間隔
    let rate = opts.rate != null ? opts.rate : rateFor(d, c);
    out.push({ name, rate, gain: opts.gain != null ? opts.gain : 1, t: +d.t.toFixed(3) });
    d.stats.cues++; return true;
  }
  function comboRate(n) { let r = 1; for (const [k, v] of A.comboRates) if (n >= k) r = v; return r; }

  /* UI／sim 行動通知（回傳 void；cue 入 queue，下次 update 流出）。
     kind: tap confirm cancel error fed played rinsed poop sleep wake hatch evolve mg-start mg-result mg-catch mg-big mg-stone reward */
  function notify(d, kind, info, s) {
    info = info || {};
    const q = (name, after, opts) => d.queue.push({ at: d.t + (after || 0), name, opts: Object.assign({ now: true }, opts || {}) });
    const good = s && minNeed(s) > 60;
    switch (kind) {
      case 'tap': case 'confirm': case 'cancel': case 'error': q(kind); break;
      case 'fed': q(info.kind === 'snack' ? 'feed_snack' : 'feed_meal'); q('pet_content', A.contentAfterFeedMs / 1000); break;
      case 'played': q('play_tease'); if (good) q('pet_happy', A.happyAfterPlayMs / 1000); break;
      case 'rinsed': q('clean_wash'); if (good) q('pet_happy', 1.1); break;
      case 'poop': q('clean_poop'); break;
      case 'sleep': if (info.on) q('sleep_on'); else q('pet_content'); break;
      case 'hatch': q('hatch'); d.evBlockUntil = Math.max(d.evBlockUntil, d.t + 3.5); break;
      case 'evolve': q('evolve'); d.evBlockUntil = Math.max(d.evBlockUntil, d.t + 3.5); break;
      case 'mg-start': q('mg_start'); d.combo = 0; break;
      case 'mg-catch': case 'mg-big': d.combo++; q('mg_catch', 0, { rate: comboRate(d.combo) }); break;
      case 'mg-stone': d.combo = 0; q('mg_miss'); break;
      case 'mg-result': if (info.win) q('mg_win'); q('reward_orb', info.win ? 1.4 : 0.3); break;
      case 'reward': q('reward_orb'); break;
      default: break;
    }
  }

  /* 每幀：w = { beh（behavior state）, s, period, ev（{id,t,dur}|null）, mode, dt }。
     回傳 { cues:[{name,rate,gain,t}], loops:{sleep_breath,sunbathe}, bgm:'morning|noon|evening|night' } */
  function update(d, dt, w) {
    d.t += dt;
    const out = [], s = w.s, b = w.beh, mg = w.mode === 'minigame', egg = !s || s.stage === 'egg';
    // 延遲／即時 queue
    if (d.queue.length) { const keep = []; for (const e of d.queue) { if (e.at <= d.t + 1e-9) emit(d, out, e.name, 0, e.opts); else keep.push(e); } d.queue = keep; }
    if (!mg && b && !egg) {
      // 行為日誌 → cue
      const J = b.journal;
      for (let i = 0; i < J.length; i++) {
        const e = J[i]; if (e.n <= d.jn) continue; d.jn = e.n;
        if (e.ev === 'variant' && e.name === 'yawn') emit(d, out, 'pet_yawn');
        else if (e.ev === 'turn') { if (b.state !== 'grumpy' && emit(d, out, d.rng() < 0.5 ? 'pet_turn_huh_a' : 'pet_turn_huh_b')) d.turnN = e.n; }   // D2 回頭「咦？」
        else if (e.ev === 'tap') {
          if (e.name === 'pet') { if (d.turnN === e.n - 1) d.turnN = -1; else if (!(+e.ph >= 4) && b.state !== 'grumpy') emit(d, out, d.touchAlt++ % 2 ? 'pet_touch_b' : 'pet_touch_a'); }
          else emit(d, out, 'pet_curious');
        } else if (e.ev === 'state') {
          if (e.name === 'grumpy') emit(d, out, 'pet_grumpy');
          else if (e.name === 'wake') emit(d, out, 'pet_content');
          else if (e.name === 'nap') emit(d, out, 'pet_sleepy');
          else if (e.name === 'unwell' && d.t - d.warnAt.unc >= A.needWarnEvery) { if (emit(d, out, 'pet_uncomfortable')) d.warnAt.unc = d.t; }
        } else if (e.ev === 'impact') emit(d, out, 'env_pot_bump');
        else if (e.ev === 'sfx' && SFX_AB[e.name]) {        // 生命感第二段：sneeze／scratch／step_hop／step_drag／bug_pat → a/b 交替（唔連續同一個）
          const k = e.name, nm = 'pet_' + k + '_' + (d.lastAB[k] === 'a' ? 'b' : 'a');
          if (emit(d, out, nm)) d.lastAB[k] = nm.slice(-1);
        }
      }
      // 事件
      if (w.ev && w.ev.id !== d.evId) {
        d.evId = w.ev.id; const cn = AU.eventCue[w.ev.id];
        if (cn && emit(d, out, cn)) d.evBlockUntil = d.t + Math.max(w.ev.dur || 0, 2) + A.eventBlockPet;
      } else if (!w.ev) d.evId = null;
      // 需求警告（唔喺瞓覺／事件／迷你遊戲）
      if (!s.sleeping && !w.ev && d.t > 3) {
        const n = s.needs, mn = minNeed(s);
        if (mn < D.PARAMS.sickThreshold) { if (d.t - d.warnAt.unc >= A.needWarnEvery && emit(d, out, 'pet_uncomfortable')) d.warnAt.unc = d.t; }   // 不適時只出 uncomfortable，唔疊 hungry
        else if (n.hunger < 30 && d.t - d.warnAt.hungry >= A.needWarnEvery) { if (emit(d, out, 'pet_hungry')) d.warnAt.hungry = d.t; }
        else if (n.energy < 30 && d.t - d.warnAt.sleepy >= A.needWarnEvery) { if (emit(d, out, 'pet_sleepy')) d.warnAt.sleepy = d.t; }
      }
      d.loops.sleep_breath = !!(s.sleeping || (b.phase === 'loop' && (b.state === 'nap' || b.state === 'simsleep' || b.state === 'event')));
      d.loops.sunbathe = b.state === 'sunbathe' && b.phase === 'lie';
    } else { d.loops.sleep_breath = false; d.loops.sunbathe = false; if (b) d.jn = b.jn; }
    d.bgm = (s && s.sleeping) ? 'night' : (w.period || 'noon');
    d.rain = !!(w.rain && w.mode !== 'minigame');                       // H3 雨層細雨環境聲（rain＝HD-2D 現款 H3rain）
    return { cues: out, loops: d.loops, bgm: d.bgm, rain: d.rain };
  }

  // ═════════ Engine（WebAudio；只喺瀏覽器）═════════
  const Engine = {
    ctx: null, enabled: true, volume: 'high', unlocked: false, log: [], dir: null, raw: {}, buf: {}, loopNodes: {}, bgm: { cur: null, want: null, busy: 0, prev: null },
    status() { return { unlocked: this.unlocked, ctx: this.ctx ? this.ctx.state : 'none', enabled: this.enabled, bgm: this.bgm.cur ? this.bgm.cur.key : null, want: this.bgm.want, loops: Object.keys(this.loopNodes).filter(k => this.loopNodes[k] && !this.loopNodes[k].stopping), sfxLoaded: Object.keys(this.buf).filter(k => !/^bgm_/.test(k)).length, played: this.log.filter(e => e.played).length, requested: this.log.length }; },
    init(G) {
      this.G = G; this.dir = createDirector(G.seed); this.base = A.base;
      const s = G.state.settings; this.enabled = s.sound !== false && A.enabled; this.volume = s.volume || 'high';
      this.prefetch();
      const unlock = () => this.unlock();
      ['pointerdown', 'keydown', 'touchend'].forEach(ev => window.addEventListener(ev, unlock, { capture: true, passive: true }));
      document.addEventListener('visibilitychange', () => { if (!this.ctx) return; if (document.hidden) this.ctx.suspend(); else this.ctx.resume(); });
    },
    url(file) { return this.base + (/^bgm_/.test(file) ? 'bgm/' : /^amb_/.test(file) ? 'amb/' : 'sfx/') + file + '.ogg'; },
    fetchRaw(file) { if (!this.raw[file]) this.raw[file] = fetch(this.url(file)).then(r => { if (!r.ok) throw new Error(r.status + ' ' + file); return r.arrayBuffer(); }).catch(e => { this.err = String(e); return null; }); return this.raw[file]; },
    prefetch() {
      const files = Object.values(CUES).map(c => c.file).concat(Object.values(AU.loops).map(l => l.file));
      new Set(files).forEach(f => this.fetchRaw(f));
      setTimeout(() => Object.values(AU.bgm).forEach(f => this.fetchRaw(f)), 1500);
      if (AU.amb) setTimeout(() => { const R = AU.amb.rain; this.fetchRaw(R.short); this.fetchRaw(R.loop); }, 2000);
    },
    decode(file) {
      if (this.buf[file]) return Promise.resolve(this.buf[file]);
      if (!this.ctx) return Promise.resolve(null);
      const key = '_d_' + file; if (this[key]) return this[key];
      return this[key] = this.fetchRaw(file).then(ab => ab ? new Promise((res, rej) => this.ctx.decodeAudioData(ab.slice(0), res, rej)) : null).then(b => { this.buf[file] = b; this[key] = null; return b; }).catch(e => { this.err = String(e); this[key] = null; return null; });
    },
    unlock() {
      if (this.unlocked) { if (this.ctx && this.ctx.state === 'suspended' && !document.hidden) this.ctx.resume(); return; }
      const AC = window.AudioContext || window.webkitAudioContext; if (!AC) { this.unlocked = true; this.noAC = true; return; }
      this.unlocked = true;
      const ctx = this.ctx = new AC({ latencyHint: 'interactive' });
      this.master = ctx.createGain(); this.master.connect(ctx.destination); this.buses = {};
      for (const k in A.bus) { const g = ctx.createGain(); g.gain.value = A.bus[k]; g.connect(this.master); this.buses[k] = g; }
      this.applyVolume(); ctx.resume();
      const files = Object.values(CUES).map(c => c.file).concat(Object.values(AU.loops).map(l => l.file));
      let p = Promise.resolve(); new Set(files).forEach(f => { p = p.then(() => this.decode(f)); });
      this.ready = p;
    },
    applyVolume() { if (!this.master) return; this.master.gain.value = this.enabled ? A.master * (A.volumeSteps[this.volume] || 1) : 0; },
    setEnabled(on) { this.enabled = !!on; this.applyVolume(); },
    setVolume(v) { this.volume = v; this.applyVolume(); },
    play(c) {   // c: { name, rate, gain, t }
      const def = CUES[c.name]; const rec = { t: c.t, name: c.name, rate: +c.rate.toFixed(3), played: false };
      this.log.push(rec); if (this.log.length > 400) this.log.shift();
      if (!this.ctx || !this.enabled || this.ctx.state !== 'running') { rec.why = !this.ctx ? 'locked' : !this.enabled ? 'muted' : 'suspended'; return; }
      const buf = this.buf[def.file]; if (!buf) { rec.why = 'notReady'; return; }
      const src = this.ctx.createBufferSource(), g = this.ctx.createGain();
      src.buffer = buf; src.playbackRate.value = c.rate; g.gain.value = def.gain * (c.gain == null ? 1 : c.gain);
      src.connect(g); g.connect(this.buses[def.bus]); src.start(); rec.played = true;
    },
    loop(name, on) {
      if (!this.ctx) return; const L = AU.loops[name], cur = this.loopNodes[name], now = this.ctx.currentTime, f = A.loopFadeSec;
      if (on && (!cur || cur.stopping)) {
        const buf = this.buf[L.file]; if (!buf) return;
        const src = this.ctx.createBufferSource(), g = this.ctx.createGain();
        src.buffer = buf; src.loop = true; src.loopStart = 0; src.loopEnd = buf.duration;
        g.gain.setValueAtTime(0, now); g.gain.linearRampToValueAtTime(L.gain, now + f);
        src.connect(g); g.connect(this.buses[L.bus]); src.start(now);
        this.loopNodes[name] = { src, g, stopping: false }; this.log.push({ t: this.dir.t, name: 'loop:' + name + ':on', played: true });
      } else if (!on && cur && !cur.stopping) {
        cur.stopping = true; const gp = cur.g.gain; gp.cancelScheduledValues(now); gp.setValueAtTime(gp.value, now); gp.linearRampToValueAtTime(0, now + f);
        cur.src.stop(now + f + 0.05); this.log.push({ t: this.dir.t, name: 'loop:' + name + ':off', played: true });
        setTimeout(() => { if (this.loopNodes[name] === cur) this.loopNodes[name] = null; }, (f + 0.2) * 1000);
      }
    },
    // ── BGM：按時段 crossfade（小節線對齊）──
    bgmPos(cur, now) { return ((cur.off + Math.max(0, now - cur.t0)) % cur.dur + cur.dur) % cur.dur; },
    bgmApply(key) {
      const B = this.bgm; B.want = key;
      if (!this.ctx || this.ctx.state !== 'running' || (B.cur && B.cur.key === key) || B.loading) return;
      if (B.cur && this.ctx.currentTime < B.busy) return;      // 上一次切換未完成
      const file = AU.bgm[key]; B.loading = true;
      this.decode(file).then(buf => { B.loading = false; if (buf && B.want === key) this.bgmSwitch(key, buf); });
    },
    curve(up, n) { const a = new Float32Array(n); for (let i = 0; i < n; i++) { const u = i / (n - 1); a[i] = up ? Math.sin(u * Math.PI / 2) : Math.cos(u * Math.PI / 2); } return a; },
    bgmSwitch(key, buf) {
      const ctx = this.ctx, B = this.bgm, now = ctx.currentTime, bar = AU.barSec, gain = 1, nb = AU.bgmBars[key];
      const g = ctx.createGain(), src = ctx.createBufferSource(); src.buffer = buf; src.loop = true; src.loopStart = 0; src.loopEnd = buf.duration;
      src.connect(g); g.connect(this.buses.bgm);
      let t0, off, fade, entry;
      if (!B.cur) {
        t0 = now + 0.05; off = 0; fade = A.firstFadeSec;
        g.gain.setValueAtTime(0, now); g.gain.setValueCurveAtTime(this.curve(true, 64), t0, fade);
      } else {
        const o = B.cur, pos = this.bgmPos(o, now), bi = Math.floor(pos / bar + 1e-9);
        let wait = (bi + 1) * bar - pos, k = bi + 1;
        if (wait < A.switchLookahead) { wait += bar; k++; }
        t0 = now + wait; off = (k % nb) * bar; fade = A.xfadeSec;
        g.gain.setValueAtTime(0, now); g.gain.setValueCurveAtTime(this.curve(true, 64), t0, fade);
        o.g.gain.cancelScheduledValues(now); o.g.gain.setValueAtTime(1, now); o.g.gain.setValueCurveAtTime(this.curve(false, 64), t0, fade);
        o.src.stop(t0 + fade + 0.1); B.prev = o;
        this.log.push({ t: this.dir.t, name: 'bgm:xfade:' + o.key + '>' + key, bar: k, offset: +off.toFixed(4), at: +(t0 - now).toFixed(3), played: true });
      }
      src.start(t0, off);
      entry = { key, src, g, t0, off, dur: buf.duration, bars: nb }; B.cur = entry; B.busy = t0 + fade;
      if (!B.prev) this.log.push({ t: this.dir.t, name: 'bgm:start:' + key, played: true });
      // 解碼緩存：只留目前＋上一條
      setTimeout(() => { const keep = new Set([AU.bgm[key], B.prev && AU.bgm[B.prev.key]]); for (const f of Object.values(AU.bgm)) if (!keep.has(f)) this.buf[f] = null; }, (fade + 1) * 1000 + 800);
    },
    // ── H3 雨層細雨環境聲：short → 1.5s 後等功率 crossfade 入 loop（BufferSource.loop＝true）；停雨 loop 淡出 ──
    rain(on) {
      const R = AU.amb && AU.amb.rain; if (!R || !this.ctx) return;
      const st = this.amb || (this.amb = { want: false, on: false, short: null, loop: null, g: null, busy: false, hist: [] });
      st.want = !!on;
      if (on && !st.on && !st.busy) {
        if (this.ctx.state !== 'running') return;
        st.busy = true;
        Promise.all([this.decode(R.short), this.decode(R.loop)]).then(([bs, bl]) => { st.busy = false; if (st.want && !st.on && bs && bl) this.rainStart(bs, bl); });
      } else if (!on && st.on) this.rainStop();
    },
    rainStart(bs, bl) {
      const R = AU.amb.rain, ctx = this.ctx, now = ctx.currentTime, st = this.amb, bus = this.buses[R.bus] || this.master;
      const t0 = now + 0.02, tx = t0 + R.xfadeAt, fx = R.xfadeSec;
      const gs = ctx.createGain(), ss = ctx.createBufferSource(); ss.buffer = bs; ss.connect(gs); gs.connect(bus);
      gs.gain.setValueAtTime(R.gain, now); gs.gain.setValueCurveAtTime(this.curve(false, 64).map(v => v * R.gain), tx, fx);   // short 自己有淡入；交叉時等功率淡走
      ss.start(t0); ss.stop(tx + fx + 0.05);
      const gl = ctx.createGain(), ls = ctx.createBufferSource(); ls.buffer = bl; ls.loop = true; ls.loopStart = 0; ls.loopEnd = bl.duration;   // sample-accurate 無縫
      ls.connect(gl); gl.connect(bus);
      gl.gain.setValueAtTime(0, now); gl.gain.setValueCurveAtTime(this.curve(true, 64).map(v => v * R.gain), tx, fx);
      ls.start(tx, 0);
      st.on = true; st.short = { src: ss, g: gs, t0, end: tx + fx }; st.loop = { src: ls, g: gl, t0: tx }; st.startedAt = now;
      const e = { t: this.dir.t, name: 'amb:rain:start', played: true, xfadeAt: +(tx - t0).toFixed(3), xfadeSec: fx, loop: ls.loop, loopEnd: +ls.loopEnd.toFixed(4), shortDur: +bs.duration.toFixed(3), loopDur: +bl.duration.toFixed(3) };
      this.log.push(e); st.hist.push(e);
    },
    rainStatus() {
      const st = this.amb; if (!st) return { on: false, want: false, hist: [] };
      const L = st.loop && st.loop.src, Sh = st.short && st.short.src, now = this.ctx ? this.ctx.currentTime : 0;
      return { on: st.on, want: st.want, busy: st.busy, now: +now.toFixed(3), startedAt: st.startedAt, stoppedAt: st.stoppedAt, hist: st.hist.slice(),
        loop: L ? { node: L.constructor.name, loop: L.loop, loopStart: L.loopStart, loopEnd: +L.loopEnd.toFixed(4), bufDur: +L.buffer.duration.toFixed(4), t0: +st.loop.t0.toFixed(3), gain: +st.loop.g.gain.value.toFixed(3) } : null,
        short: Sh ? { node: Sh.constructor.name, loop: Sh.loop, bufDur: +Sh.buffer.duration.toFixed(3), t0: +st.short.t0.toFixed(3), end: +st.short.end.toFixed(3), gain: +st.short.g.gain.value.toFixed(3) } : null,
        fading: st.fading ? { loopGain: st.fading.loop ? +st.fading.loop.g.gain.value.toFixed(3) : null } : null, audioEls: document.querySelectorAll('audio').length };
    },
    rainStop() {
      const R = AU.amb.rain, ctx = this.ctx, now = ctx.currentTime, st = this.amb, f = R.fadeOutSec;
      for (const n of [st.loop, st.short]) { if (!n) continue; const gp = n.g.gain; gp.cancelScheduledValues(now); gp.setValueAtTime(gp.value, now); gp.linearRampToValueAtTime(0, now + f); try { n.src.stop(now + f + 0.05); } catch (e) { } }
      const e = { t: this.dir.t, name: 'amb:rain:stop', played: true, fadeOutSec: f };
      this.log.push(e); st.hist.push(e); st.on = false; st.stoppedAt = now;
      const old = { short: st.short, loop: st.loop }; st.short = null; st.loop = null; st.fading = old;
      setTimeout(() => { if (st.fading === old) st.fading = null; }, (f + 0.3) * 1000);
    },
    // ── 對外 ──
    notify(kind, info) { if (this.dir) notify(this.dir, kind, info, this.G.state); },
    update(dt, w) {
      if (!this.dir) return;
      const r = update(this.dir, dt, w);
      for (const c of r.cues) this.play(c);
      if (this.ctx) { this.loop('sleep_breath', r.loops.sleep_breath); this.loop('sunbathe', r.loops.sunbathe); this.rain(r.rain); }
      this.bgmApply(r.bgm);
    },
  };

  return { createDirector, update, notify, emit, comboRate, Engine, AU };
});
