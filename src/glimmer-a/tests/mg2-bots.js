// 小遊戲 v2 測試用 bot（skill 0..1）：unit test＋經濟模擬共用。原創代碼。
'use strict';
function botStep(g, sk, rng, st) {
  st = st || {};
  if (g.kind === 'bounce') {
    const p = g.pet;
    if (g.phase === 'ready') { st.cw = (st.cw || 0) + 1 / 60; if (st.cw > 0.25 + (1 - sk) * 0.6) { st.cw = 0; st.goal = 0.45 + rng() * 0.5; g.press(p.x, p.y); } }
    else if (g.phase === 'charge') { if (g.power >= st.goal) g.release(); }
    else if (g.phase === 'air') {
      let tx;
      if (p.vy < 0 || p.y < 150) { let best = null, bd = 1e9; for (const d of g.dots) { const dd = Math.abs(d.x - p.x) + Math.max(0, p.y - d.y) * 0.2; if (d.y < p.y && dd < bd) { bd = dd; best = d; } } tx = best ? best.x : p.x; }
      else tx = g.M.leaf.x;
      if (rng() < 0.15 + sk * 0.8) g.move(tx + (rng() - 0.5) * (1 - sk) * 140, 0);
    }
  } else if (g.kind === 'ghide') {
    if (g.phase !== 'seek') { st.seen = -1; st.round = -1; return st; }
    const cs = g.covers;
    if (st.round !== g.round) { st.round = g.round; st.seen = -1; }
    // 睇住：露尾＝一定係；自己搖（唔係撳）＝可能係（風會有假線索）
    if (g.peeking) st.seen = g.at; else { const sh = cs.findIndex((c, i) => c.shake > 0.2 && c.shake < 0.26 && !c.tried); if (sh >= 0 && st.seen !== g.at) st.seen = sh; }
    st.w = (st.w || 0) + 1 / 60; if (st.w < 0.8 + (1 - sk) * 1.6) return st; st.w = 0;
    const free = cs.map((c, i) => i).filter(i => !cs[i].tried);
    const use = st.seen >= 0 && !cs[st.seen].tried && rng() < sk;
    g.pick(use ? st.seen : free[Math.floor(rng() * free.length)]); st.seen = -1;
  } else if (g.kind === 'firefly') {
    if (g.stun > 0 || g.path.length) return st;
    st.w = (st.w || 0) + 1 / 60; if (st.w < 0.2 + (1 - sk) * 0.8) return st; st.w = 0;
    let best = null, bd = 1e9; for (const f of g.flies) { const d = Math.hypot(f.x - g.pet.x, f.y - g.pet.y); if (d < bd) { bd = d; best = f; } }
    if (!best) return st; const p = g.pet, n = 8, ox = (rng() - 0.5) * (1 - sk) * 60, oy = (rng() - 0.5) * (1 - sk) * 60;
    // skill 高嘅 bot 會繞過樹枝（中途點偏開）
    let mx = (p.x + best.x) / 2, my = (p.y + best.y) / 2;
    if (sk > 0.5) for (const b of g.branches) if (g.constructor && require('../src/minigames2.js').segDist(mx, my, b) < 18) { mx += 26; }
    g.press(p.x, p.y); for (let i = 1; i <= n; i++) { const u = i / n, ax = i <= n / 2 ? p.x + (mx - p.x) * u * 2 : mx + (best.x + ox - mx) * (u * 2 - 1), ay = i <= n / 2 ? p.y + (my - p.y) * u * 2 : my + (best.y + oy + 8 - my) * (u * 2 - 1); g.move(ax, ay); } g.release();
  }
  return st;
}
function playBot(M, kind, seed, sk, rng, opt) { const g = M.create(kind, seed, opt); let st = {}, n = 0; while (!g.over && n < 4000) { st = botStep(g, sk, rng, st); g.update(1 / 60); n++; } return g; }
module.exports = { botStep, playBot };
