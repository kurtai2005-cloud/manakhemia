/* 《微光小圃》 minigames2.js — 小遊戲 v2 邏輯（docs-gdd/minigames-v2.md；DOM-free，Node 測得）。原創代碼。
   Kurt 揀：彈彈葉（bounce）、花園捉迷藏重做（ghide）、追螢火（firefly，夜晚限定）。數值＝PARAMS.minigames2（遊策定稿）。
   場地＝邏輯 180×320（直向單手）；輸入＝press／move／release（手指座標）；update(dt) 定步長都得（60fps 友好，冇 alloc 熱點）。
   團絨反應：this.clip（現有 clip 名，UI 冇呢個 clip 就畫 idle）＋ this.flip（翻筋斗角度）；反應序列 play([[key, 秒], ...])。
   每局 2 個變化：mods＝[{cat, k, hard, s}]（3 類揀 2 類、每類抽 1 個；最多 1 個難，難強度 s＝20–25%）。獎勵唔喺呢度發 → systems2.gameFinish。 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory(require('./data.js'), require('./sim.js'));
  else { root.Glimmer = root.Glimmer || {}; root.Glimmer.mg2 = factory(root.Glimmer.data, root.Glimmer.sim); }
})(typeof self !== 'undefined' ? self : this, function (D, SIM) {
  'use strict';
  const C = () => D.PARAMS.minigames2;
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const rr = (rng, a) => a[0] + rng() * (a[1] - a[0]);
  function inHours(h, a) { return a[0] <= a[1] ? h >= a[0] && h < a[1] : h >= a[0] || h < a[1]; }
  function fireflyOpen(hour) { return SIM.isNightHour(hour); }   // 同螢絨夜窗共用 PARAMS.evo6.nightFrom／nightTo
  /* 3 類揀 modCats 類、每類抽 1 個；最多 maxHard 個難（多咗 → 換同類嘅易，嗰類冇易就換第 3 類嘅易）；難嘅強度 s∈hardStr。
     fixed＝[{cat,k}] 或 ['wind','gold'] 指定（QA，唔限難數） */
  function pickMods(rng, pool, fixed) {
    const P = C(), cats = Object.keys(pool), mk = (cat, k) => { const d = pool[cat][k]; return { cat, k, hard: !!d.hard, s: d.hard ? rr(rng, P.hardStr) : 0 }; };
    if (fixed) return fixed.map(f => typeof f === 'string' ? { cat: cats.find(c => pool[c][f]) || null, k: f } : f).filter(m => m.cat && pool[m.cat][m.k]).map(m => mk(m.cat, m.k));
    const order = cats.slice(); for (let i = order.length - 1; i > 0; i--) { const j = Math.floor(rng() * (i + 1)); const t = order[i]; order[i] = order[j]; order[j] = t; }
    const pick = order.slice(0, P.modCats), ks = cat => Object.keys(pool[cat]), easy = cat => ks(cat).filter(k => !pool[cat][k].hard);
    let out = pick.map(cat => { const a = ks(cat); return { cat, k: a[Math.floor(rng() * a.length)] }; });
    let hard = out.filter(m => pool[m.cat][m.k].hard);
    while (hard.length > P.maxHard) {
      const keep = hard[Math.floor(rng() * hard.length)], m = hard.find(h => h !== keep && easy(h.cat).length) || hard.find(h => h !== keep);
      const e = easy(m.cat);
      if (e.length) m.k = e[Math.floor(rng() * e.length)];
      else { const alt = cats.filter(c => !out.some(o => o.cat === c) && easy(c).length)[0]; const e2 = easy(alt); m.cat = alt; m.k = e2[Math.floor(rng() * e2.length)]; }
      hard = out.filter(x => pool[x.cat][x.k].hard);
    }
    return out.sort((a, b) => cats.indexOf(a.cat) - cats.indexOf(b.cat)).map(m => mk(m.cat, m.k));
  }
  function stars(kind, v) { const a = C()[kind].starsAt; let n = 0; for (let i = 0; i < a.length; i++) if (v >= a[i]) n = i + 1; return Math.min(3, n); }

  class Base {
    constructor(kind, seed, opt) {
      opt = opt || {}; this.kind = kind; this.M = C()[kind]; this.seed = (seed >>> 0) || 1; this.rng = SIM.makeRng(this.seed);
      this.mods = pickMods(this.rng, this.M.mods, opt.mods); this.t = 0; this.score = 0; this.over = false;
      this.q = []; this.qt = 0; this.clip = 'idle'; this.flip = 0; this.face = 1; this.fx = []; this.snd = []; this.log = [];
    }
    has(k) { return this.mods.some(m => m.k === k); }
    mod(k) { const m = this.mods.find(x => x.k === k); return m ? this.M.mods[m.cat][m.k] : null; }
    eff(type) { const m = this.mods.find(x => { const d = this.M.mods[x.cat][x.k]; return d.hard === type || d.easy === type; }); return m || null; }   // 按效果類型搵 modifier
    get hardS() { const m = this.mods.find(x => x.hard); return m ? m.s : 0; }
    initEasy() { const E = C().easy; this.dur = (this.M.durationSec || this.M.timeLimitSec) + (this.eff('time') ? E.timeAdd : 0); this.goldP = (this.M.goldProb || 0) * (this.eff('gold') ? E.goldMul : 1); }
    /* 反應序列：[[反應 key, 秒], ...]；播完返 baseReact() */
    play(seq) { this.q = seq.slice(); this.qt = 0; this.clip = C().reactions[this.q[0][0]] || this.q[0][0]; this.react = this.q[0][0]; }
    tickReact(dt) {
      if (this.q.length) { this.qt += dt; if (this.qt >= this.q[0][1]) { this.q.shift(); this.qt = 0; } }
      const k = this.q.length ? this.q[0][0] : this.baseReact(); this.react = k; this.clip = C().reactions[k] || k;
    }
    baseReact() { return 'idle'; }
    emit(type, x, y, v) { this.fx.push({ type, x, y, v }); if (this.fx.length > 40) this.fx.shift(); }
    get stars() { return stars(this.kind, this.score); }
    get left() { return Math.max(0, this.dur - this.t); }
  }

  // ── 1 彈彈葉：撳住葉片儲力 → 放手彈起團絨 → 半空左右拖 → 掂光點得分 ──
  class BounceGame extends Base {
    constructor(seed, opt) {
      super('bounce', seed, opt); const M = this.M; this.initEasy();
      const sp = this.eff('speed'), tg = this.eff('target'), dr = this.eff('drift');
      this.spd = sp ? 1 + sp.s : 1; this.tgt = tg ? 1 - tg.s : 1; this.leafW = M.leaf.w;
      this.windAx = dr ? (this.rng() < 0.5 ? -1 : 1) * dr.s * M.steerMax : 0;   // 漂移：恆定橫風速度 ±s×steerMax
      const h = M.vMax * M.vMax / (2 * M.gravity); this.unit = Math.max(1, M.jumpMinFrac * C().fieldH / h);   // 最大跳高 ≥45% 畫面，唔夠就放大單位
      this.cloud = null;
      this.pet = { x: M.leaf.x, y: M.leaf.y, vx: 0, vy: 0, drift: 0, wv: 0 }; this.phase = 'ready'; this.power = 0; this.tx = M.leaf.x;
      this.dots = []; for (let i = 0; i < M.dots; i++) this.dots.push(this.newDot());
      this.jumps = 0; this.lands = 0; this.falls = 0; this.jumpGot = 0; this.best = 0; this.bend = 0; this.flipping = false;
    }
    newDot() {
      const M = this.M, gold = this.rng() < this.goldP; let x, y, k = 0;
      do { x = 14 + this.rng() * 152; y = rr(this.rng, M.dotY); k++; } while (k < 8 && this.dots && this.dots.some(d => Math.hypot(d.x - x, d.y - y) < 24));
      return { x, y, gold, ph: this.rng() * 6.28 };
    }
    onLeaf() { return Math.abs(this.pet.x - this.M.leaf.x) <= this.leafW / 2; }
    press(x, y) { if (this.over) return false; if (this.phase === 'ready') { this.phase = 'charge'; this.power = 0; this.tx = this.pet.x; this.play([['charge', 99]]); return true; } if (this.phase === 'air') { this.tx = x; return true; } return false; }
    move(x, y) { if (this.phase === 'air' || this.phase === 'charge') this.tx = clamp(x, 8, 172); }
    release() {
      if (this.phase !== 'charge') return false; const M = this.M, p = this.pet;
      p.vy = -(M.vMin + this.power * (M.vMax - M.vMin)) * this.spd * this.unit; p.vx = 0; p.wv = 0; p.drift = 0;
      this.flipping = this.power >= M.flipPower; if (this.flipping) this.flips = (this.flips || 0) + 1;   // 翻筋斗：純演出，唔改落點／分
      this.phase = 'air'; this.jumps++; this.jumpGot = 0; this.flip = 0; this.bend = 0; this.power = 0; this.snd.push('jump');
      this.play(this.flipping ? [['proud', 0.6]] : [['jump', 0.4]]); return true;
    }
    baseReact() { return this.phase === 'air' ? 'jump' : this.phase === 'walk' ? 'walk' : this.phase === 'charge' ? 'charge' : 'idle'; }
    update(dt) {
      if (this.over) return; const M = this.M, p = this.pet; this.t += dt;
      for (const d of this.dots) d.ph += dt * 3;
      if (this.phase === 'charge') { this.power = Math.min(1, this.power + dt / M.chargeSec); this.bend = this.power; }
      else if (this.phase === 'air') {
        const sv = clamp((this.tx - p.x) * M.steer, -M.steerMax, M.steerMax); p.wv = this.windAx;
        p.x = clamp(p.x + (sv + p.drift + p.wv) * dt, 8, 172); p.vy += M.gravity * this.unit * this.spd * this.spd * dt; p.y += p.vy * dt;
        if (this.flipping && this.flip < Math.PI * 2) this.flip = Math.min(Math.PI * 2, this.flip + dt * 9 * this.spd);
        if (p.vx !== 0) this.face = p.vx > 0 ? 1 : -1; if (Math.abs(sv) > 10) this.face = sv > 0 ? 1 : -1;
        for (let i = 0; i < this.dots.length; i++) { const d = this.dots[i]; if (Math.hypot(d.x - p.x, d.y - (p.y - 14)) < (M.dotR + 10) * this.tgt) { const v = d.gold ? M.gold : M.dot; this.score += v; this.jumpGot++; this.emit(d.gold ? 'gold' : 'dot', d.x, d.y, v); this.snd.push(d.gold ? 'big' : 'catch'); this.dots[i] = this.newDot(); if (this.jumpGot === 3) this.play([['proud', 0.5]]); } }
        if (p.vy > 0 && p.y >= M.leaf.y) {
          if (this.onLeaf()) { this.wasFlip = this.flipping; p.y = M.leaf.y; this.phase = 'ready'; this.lands++; this.flip = 0; this.flipping = false; this.best = Math.max(this.best, this.jumpGot); this.bend = 0.35; this.play(this.jumpGot >= 2 || this.wasFlip ? [['proud', 1.0]] : [['idle', 0.1]]); }
          else if (p.y >= M.groundY) { p.y = M.groundY; this.phase = 'fallen'; this.falls++; this.flip = 0; this.flipping = false; this.ft = 0; this.emit('thud', p.x, p.y); this.snd.push('stone'); this.play([['fall', 0.7], ['getup', 0.4], ['cool', M.fallSec - 1.1]]); }
        }
      } else if (this.phase === 'fallen') { this.ft += dt; if (this.ft >= M.fallSec) this.phase = 'walk'; }
      else if (this.phase === 'walk') { const dx = M.leaf.x - p.x, st = M.walkSpeed * dt; this.face = dx > 0 ? 1 : -1; if (Math.abs(dx) <= st) { p.x = M.leaf.x; p.y = M.leaf.y; this.phase = 'ready'; } else { p.x += Math.sign(dx) * st; p.y = M.groundY; } }
      if (this.bend > 0 && this.phase !== 'charge') this.bend = Math.max(0, this.bend - dt * 2);
      this.tickReact(dt);
      if (this.t >= this.dur) { this.t = this.dur; this.over = true; this.play([[this.stars >= 2 ? 'win' : this.stars === 0 ? 'sad' : 'cool', 2]]); }
    }
  }

  // ── 3 花園捉迷藏（重做）：真花園、遮擋物每回合唔同；撳＝搖嗰樣嘢；太慢佢會偷偷轉位；搵到扮冇事行出嚟 ──
  class GardenHide extends Base {
    constructor(seed, opt) {
      super('ghide', seed, opt); const M = this.M; this.initEasy();
      this.nCovers = M.covers; const sn = this.eff('sneak'), tg = this.eff('target'), dr = this.eff('drift');
      this.sneakSec = sn ? this.M.mods[sn.cat][sn.k].sneakSec : M.sneakSec;
      this.hitR = M.hitR * (tg ? 1 - tg.s : 1); this.sway = dr ? dr.s * M.area.minDist : 0;   // 目標細；漂移＝遮擋物隨風左右擺 ±s×minDist
      this.tailChance = M.tailChance; this.peekA = 1;
      this.round = 0; this.found = 0; this.firstHits = 0; this.sneaks = 0; this.phase = 'seek'; this.covers = []; this.next();
    }
    next() {
      const M = this.M, A = M.area, n = this.nCovers, cs = []; let k = 0;
      while (cs.length < n && k++ < 400) { const x = rr(this.rng, A.x), y = rr(this.rng, A.y); if (cs.every(c => Math.hypot(c.x - x, c.y - y) >= A.minDist)) cs.push({ x: Math.round(x), y: Math.round(y), type: M.coverTypes[Math.floor(this.rng() * M.coverTypes.length)], shake: 0, wig: 0, dx: 0, ph: this.rng() * 6.28, tried: false, rustle: 0 }); }
      while (cs.length < n) cs.push({ x: 30 + cs.length * 28, y: A.y[1] - (cs.length % 2) * 30, type: 'bush', shake: 0, wig: 0, dx: 0, ph: 0, tried: false, rustle: 0 });
      cs.sort((a, b) => a.y - b.y); this.covers = cs; this.at = Math.floor(this.rng() * n); this.tries = M.triesPerRound; this.tryN = 0;
      this.tail = this.rng() < this.tailChance; this.peekKind = this.rng() < 0.5 ? 'tail' : 'bulb'; this.idle = 0; this.peekT = rr(this.rng, M.peekEvery); this.peek = 0; this.phase = 'seek'; this.play([['idle', 0.1]]);
    }
    coverAt(x, y) { let best = -1, bd = 1e9; this.covers.forEach((c, i) => { const d = Math.hypot(c.x + c.dx - x, c.y - 8 - y); if (d < this.hitR && d < bd) { bd = d; best = i; } }); return best; }
    press(x, y) { const i = this.coverAt(x, y); return i < 0 ? { ok: false } : this.pick(i); }
    move() {} release() {}
    pick(i) {
      if (this.over || this.phase !== 'seek' || i < 0 || i >= this.covers.length) return { ok: false };
      const c = this.covers[i]; c.shake = this.M.tapShake; this.idle = 0; this.snd.push('rustle');
      if (c.tried) return { ok: true, again: true, hit: false };
      c.tried = true; this.tryN++; this.tries--; const hit = i === this.at, M = this.M, pts = hit ? (M.ptsByTry[this.tryN - 1] | 0) : 0;
      const r = { ok: true, hit, at: this.at, tryN: this.tryN, pts, tail: this.tail, round: this.round, roundOver: hit || this.tries <= 0 };
      if (hit) { this.found++; this.score += pts; if (this.tryN === 1) this.firstHits++; this.emit('found', c.x, c.y - 20, pts); this.snd.push('catch'); this.play([['surprised', 0.4], ['cool', M.revealSec - 0.4]]); }
      else if (r.roundOver) { this.emit('miss', c.x, c.y); this.play([['proud', M.revealSec]]); this.snd.push('stone'); }
      else this.emit('miss', c.x, c.y);
      if (r.roundOver) { this.log.push({ hit, tryN: this.tryN, pts, tail: this.tail, sneaks: this.sneaks }); this.phase = 'reveal'; this.rt = 0; this.revealHit = hit; }
      r.score = this.score; return r;
    }
    baseReact() { return this.phase === 'reveal' ? (this.revealHit ? 'cool' : 'proud') : 'idle'; }
    update(dt) {
      if (this.over) return; const M = this.M; this.t += dt;
      for (const c of this.covers) { c.shake = Math.max(0, c.shake - dt); c.wig = Math.max(0, c.wig - dt); c.rustle = Math.max(0, c.rustle - dt); c.dx = this.sway ? Math.sin(this.t * 2.2 + c.ph) * this.sway : 0; }
      if (this.phase === 'seek') {
        this.idle += dt;
        if (this.idle >= this.sneakSec) {   // 你太慢 → 偷偷轉位（揀一個未撳過嘅，冇就隨便）
          const free = this.covers.map((c, i) => i).filter(i => i !== this.at && !this.covers[i].tried), pool = free.length ? free : this.covers.map((c, i) => i).filter(i => i !== this.at);
          if (pool.length) { this.covers[this.at].rustle = 0.4; this.at = pool[Math.floor(this.rng() * pool.length)]; this.covers[this.at].rustle = 0.4; this.sneaks++; this.snd.push('sneak'); }
          this.idle = 0;
        }
        // 探頭每 2.5–4 秒一次、0.6 秒：露尾／燈泡回合＝見到尾巴或燈泡；其餘回合＝匿嗰樣嘢自己郁（c.wig）
        this.peek = Math.max(0, this.peek - dt); this.peekT -= dt;
        if (this.peekT <= 0) { if (this.tail) this.peek = M.peekSec; else this.covers[this.at].wig = M.peekSec; this.peekT = rr(this.rng, M.peekEvery); }
      } else if (this.phase === 'reveal') {
        this.rt += dt; if (this.rt >= M.revealSec) { this.round++; if (this.round >= M.rounds) { this.over = true; this.play([[this.stars >= 2 ? 'win' : this.stars === 0 ? 'proud' : 'cool', 2]]); } else this.next(); }
      }
      this.tickReact(dt);
      if (!this.over && this.t >= this.dur) { this.t = this.dur; this.over = true; this.play([['proud', 2]]); }
    }
    get peeking() { return this.tail && this.peek > 0 && this.phase === 'seek'; }
  }

  // ── 5 追螢火（夜晚限定）：手指畫一條路 → 團絨跟住衝去捉螢火；撞樹枝扮冇痛 ──
  function segDist(px, py, a) { const dx = a.x2 - a.x1, dy = a.y2 - a.y1, L = dx * dx + dy * dy || 1, u = clamp(((px - a.x1) * dx + (py - a.y1) * dy) / L, 0, 1); return Math.hypot(px - (a.x1 + u * dx), py - (a.y1 + u * dy)); }
  class FireflyChase extends Base {
    constructor(seed, opt) {
      super('firefly', seed, opt); const M = this.M, F = M.field;
      this.initEasy(); const sp = this.eff('speed'), tg = this.eff('target'), dr = this.eff('drift');
      this.spd = 1; this.flySpd = sp ? 1 + sp.s : 1; this.tgt = tg ? 1 - tg.s : 1;   // 速度＝螢火飛快 ×(1+s)；目標細＝螢火判定 ×(1−s)
      this.windX = dr ? (this.rng() < 0.5 ? -1 : 1) * dr.s * M.petSpeed : 0;            // 漂移：團絨被微風推 ±s×petSpeed
      this.pet = { x: 90, y: 270 }; this.path = []; this.drawing = false; this.pathLen = 0; this.stun = 0; this.bumps = 0; this.caught = 0;
      this.branches = []; const nb = M.branches; let k = 0;
      while (this.branches.length < nb && k++ < 300) {
        const x = rr(this.rng, F.x), y = rr(this.rng, [F.y[0] + 30, F.y[1] - 60]), a = this.rng() * Math.PI, L = rr(this.rng, M.branchLen) / 2;
        const b = { x1: x - Math.cos(a) * L, y1: y - Math.sin(a) * L, x2: x + Math.cos(a) * L, y2: y + Math.sin(a) * L };
        if (segDist(this.pet.x, this.pet.y, b) > 40 && this.branches.every(o => Math.hypot((o.x1 + o.x2) / 2 - x, (o.y1 + o.y2) / 2 - y) > 34)) this.branches.push(b);
      }
      this.flies = []; for (let i = 0; i < M.flies; i++) this.flies.push(this.newFly());
    }
    newFly() {
      const M = this.M, F = M.field; let x, y, k = 0;
      do { x = rr(this.rng, F.x); y = rr(this.rng, [F.y[0], F.y[1] - 40]); k++; } while (k < 10 && (Math.hypot(x - this.pet.x, y - this.pet.y) < 50 || this.branches.some(b => segDist(x, y, b) < 14)));
      return { x, y, vx: 0, vy: 0, ph: this.rng() * 6.28, gold: this.rng() < this.goldP };
    }
    press(x, y) { if (this.over) return false; this.drawing = true; this.path = [{ x: clamp(x, 6, 174), y: clamp(y, 30, 312) }]; this.pathLen = 0; return true; }
    move(x, y) {
      if (!this.drawing) return; const l = this.path[this.path.length - 1], p = { x: clamp(x, 6, 174), y: clamp(y, 30, 312) };
      const d = l ? Math.hypot(p.x - l.x, p.y - l.y) : 99; if (d < 4) return; if (this.pathLen + d > this.M.maxPath) { this.drawing = false; return; }
      this.pathLen += d; this.path.push(p); if (this.path.length > 160) this.path.shift();
    }
    release() { this.drawing = false; }
    baseReact() { return this.stun > 0 ? 'cool' : this.path.length ? 'run' : 'idle'; }
    update(dt) {
      if (this.over) return; const M = this.M, F = M.field, p = this.pet; this.t += dt;
      for (const f of this.flies) { f.ph += dt * this.flySpd; const a = M.drift * this.flySpd; f.vx += (Math.sin(f.ph * 1.7 + f.y * 0.05) * a - f.vx) * dt * 1.5; f.vy += (Math.cos(f.ph * 1.3 + f.x * 0.05) * a - f.vy) * dt * 1.5; f.x = clamp(f.x + f.vx * dt, F.x[0], F.x[1]); f.y = clamp(f.y + f.vy * dt, F.y[0], F.y[1] - 30); }
      if (this.windX && this.path.length && !this.stun) p.x = clamp(p.x + this.windX * dt, F.x[0], F.x[1]);
      if (this.stun > 0) this.stun = Math.max(0, this.stun - dt);
      else if (this.path.length) {
        let step = M.petSpeed * this.spd * dt;
        while (step > 0 && this.path.length) { const h = this.path[0], dx = h.x - p.x, dy = h.y - p.y, d = Math.hypot(dx, dy); if (d <= step) { p.x = h.x; p.y = h.y; step -= d; this.path.shift(); } else { p.x += dx / d * step; p.y += dy / d * step; if (Math.abs(dx) > 1) this.face = dx > 0 ? 1 : -1; step = 0; } }
        for (const b of this.branches) if (segDist(p.x, p.y - 6, b) < M.petR) {   // 撞樹枝：彈返少少、停低、扮冇痛
          const mx = (b.x1 + b.x2) / 2, my = (b.y1 + b.y2) / 2, dx = p.x - mx, dy = p.y - my, d = Math.hypot(dx, dy) || 1;
          p.x = clamp(p.x + dx / d * 8, F.x[0], F.x[1]); p.y = clamp(p.y + dy / d * 8, F.y[0], F.y[1]); this.path = []; this.drawing = false; this.stun = M.stunSec; this.bumps++;
          this.emit('bump', p.x, p.y - 20); this.snd.push('stone'); this.play([['bump', 0.4], ['cool', M.stunSec]]); break;
        }
      }
      for (let i = 0; i < this.flies.length; i++) { const f = this.flies[i]; if (Math.hypot(f.x - p.x, f.y - (p.y - 8)) < M.flyR * this.tgt + M.petR) { const v = f.gold ? M.gold : M.fly; this.score += v; this.caught++; this.emit(f.gold ? 'gold' : 'fly', f.x, f.y, v); this.snd.push(f.gold ? 'big' : 'catch'); this.flies[i] = this.newFly(); if (this.caught % 3 === 0) this.play([['proud', 0.6]]); else this.play([['happy', 0.3]]); } }
      this.tickReact(dt);
      if (this.t >= this.dur) { this.t = this.dur; this.over = true; this.play([[this.stars >= 2 ? 'win' : this.stars === 0 ? 'sad' : 'cool', 2]]); }
    }
  }
  const KINDS = { bounce: BounceGame, ghide: GardenHide, firefly: FireflyChase };
  function create(kind, seed, opt) { const K = KINDS[kind]; if (!K) throw new Error('mg2: kind ' + kind); return new K(seed, opt); }
  return { create, pickMods, stars, fireflyOpen, inHours, segDist, KINDS, BounceGame, GardenHide, FireflyChase };
});
