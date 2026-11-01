/* 《微光小圃》 reactclip.js — 第 3 批 3a：遊美 團絨反應 clip 播放器（純函數，冇 DOM）。原創代碼。
   讀 art/reactions/reactions.json（遊美 batch3a-1，REACTIONS.md「引擎模型」）：
   body keyframes {t,sx,sy,rot(度,順時針),x,y,flip,e}（缺欄沿用；段內 easing 用下一格 e）、face 軌、wear 軌、fx 清單、events。
   render.js 用 evalClip() 嘅結果畫：base(idle 幀 0) → face patch → wear patch → body transform → fx（z back／front）。 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else { root.Glimmer = root.Glimmer || {}; root.Glimmer.reactclip = factory(); }
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';
  const EASE = {
    linear: (t) => t,
    in: (t) => t * t,
    out: (t) => 1 - (1 - t) * (1 - t),
    inout: (t) => (t < 0.5 ? 2 * t * t : 1 - 2 * (1 - t) * (1 - t)),
    outBack: (t) => 1 + 2.70158 * Math.pow(t - 1, 3) + 1.70158 * Math.pow(t - 1, 2),
    step: (t) => (t >= 1 ? 1 : 0),
  };
  const KEYS = ['sx', 'sy', 'rot', 'x', 'y', 'flip'], DEF = { sx: 1, sy: 1, rot: 0, x: 0, y: 0, flip: 0 };
  /* 缺欄沿用：先將每格填滿 */
  function filled(body) {
    if (body._filled) return body._filled;
    let cur = Object.assign({}, DEF); const out = [];
    for (const k of body) { cur = Object.assign({}, cur); for (const n of KEYS) if (k[n] != null) cur[n] = k[n]; out.push(Object.assign({ t: k.t, e: k.e || 'linear' }, cur)); }
    Object.defineProperty(body, '_filled', { value: out, enumerable: false }); return out;
  }
  function bodyAt(clip, ms) {
    const B = clip.body && clip.body.length ? filled(clip.body) : [Object.assign({ t: 0, e: 'linear' }, DEF)];
    if (ms <= B[0].t) return pick(B[0]);
    for (let i = 1; i < B.length; i++) {
      const b = B[i]; if (ms > b.t) continue;
      const a = B[i - 1], span = Math.max(1e-6, b.t - a.t), u = (EASE[b.e] || EASE.linear)(Math.max(0, Math.min(1, (ms - a.t) / span)));
      const r = {}; for (const n of KEYS) r[n] = n === 'flip' ? (u >= 1 ? b.flip : a.flip) : a[n] + (b[n] - a[n]) * u;
      return snap(clip, r);
    }
    return snap(clip, pick(B[B.length - 1]));
  }
  const pick = (k) => { const r = {}; for (const n of KEYS) r[n] = k[n]; return r; };
  function snap(clip, r, rotStep) { const st = rotStep != null ? rotStep : clip.rotStep; if (st) r.rot = Math.round(r.rot / st) * st; return r; }
  /* 軌：[{t, f(字串／陣列／null／數字), ms}] → 而家嘅值 */
  function trackAt(tr, ms) {
    if (!tr || !tr.length) return null; let cur = null;
    for (const k of tr) { if (k.t <= ms) cur = k; else break; }
    if (!cur) return null; const f = cur.f;
    if (Array.isArray(f)) { const step = cur.ms || 100; return f[Math.floor((ms - cur.t) / step) % f.length]; }
    return f;
  }
  function moveAt(mv, e) {
    if (!mv || !mv.length) return [0, 0]; if (e <= mv[0][0]) return [mv[0][1], mv[0][2]];
    for (let i = 1; i < mv.length; i++) { const a = mv[i - 1], b = mv[i]; if (e <= b[0]) { const u = (e - a[0]) / Math.max(1e-6, b[0] - a[0]); return [a[1] + (b[1] - a[1]) * u, a[2] + (b[2] - a[2]) * u]; } }
    const l = mv[mv.length - 1]; return [l[1], l[2]];
  }
  /* fx 一格：frameCount＝該 fx 圖幀數；defMs＝fx.json／series.json 嘅 ms */
  function fxFrame(f, e, frameCount, defMs) {
    const ms = f.ms || defMs || 100, loop = f.loop !== false, n = Math.floor(e / ms);
    if (f.frames && f.frames.length) return f.frames[loop ? n % f.frames.length : Math.min(n, f.frames.length - 1)];
    const fc = frameCount || 1; return loop ? n % fc : Math.min(n, fc - 1);
  }
  /* clip 喺 ms（相對開始）嘅狀態。opt: { rotStep, frameInfo(id)→{frames,ms} } */
  function evalClip(clip, ms, opt) {
    opt = opt || {}; const dur = clip.dur || 0, loop = !!clip.loop, t = loop && dur ? ((ms % dur) + dur) % dur : Math.min(ms, dur);
    const body = bodyAt(clip, t); if (opt.rotStep != null && clip.rotStep) snap(clip, body, opt.rotStep);
    const face = trackAt(clip.face, t);
    const wear = (clip.wear || []).filter(w => t >= (w.t0 || 0) && t <= (w.t1 == null ? dur : w.t1)).map(w => ({ id: w.id, f: +(trackAt(w.frames, t - (w.t0 || 0)) || 0) }));
    const fx = [];
    for (const f of clip.fx || []) {
      const t0 = f.t0 || 0, t1 = f.t1 == null ? dur : f.t1; if (t < t0 || t > t1) continue;
      const e = t - t0, info = opt.frameInfo ? opt.frameInfo(f.id) : null, mv = moveAt(f.move, e);
      fx.push({ id: f.id, anchor: f.anchor || 'pivot', dx: (f.dx || 0) + mv[0], dy: (f.dy || 0) + mv[1], frame: fxFrame(f, e, info && info.frames, info && info.ms), follow: f.follow !== false, atGround: !!f.atGround, mirrorX: !!f.mirrorX, z: f.z || 'front' });
    }
    return { t, dur, loop, done: !loop && ms >= dur, body, face: face == null ? null : face, wear, fx, origin: clip.origin || 'pivot', groundLock: !!clip.groundLock };
  }
  /* (prevMs, ms] 之間觸發嘅 events（loop clip 用 repeatEvery） */
  function eventsBetween(clip, prevMs, ms) {
    const out = [];
    for (const ev of clip.events || []) {
      if (ev.repeatEvery) { for (let k = Math.max(0, Math.ceil((prevMs - ev.t) / ev.repeatEvery)); ; k++) { const tt = ev.t + k * ev.repeatEvery; if (tt > ms) break; if (tt > prevMs) out.push({ id: ev.id, t: tt }); } }
      else if (ev.t > prevMs && ev.t <= ms) out.push({ id: ev.id, t: ev.t });
    }
    return out;
  }
  /* body 變形（以 pivot 做原點，art 座標，y 向下）：rotate（順時針度）→ scale → 平移；origin 唔係 pivot 時補償位移 */
  function xform(body, o) {
    const a = body.rot * Math.PI / 180, c = Math.cos(a), s = Math.sin(a), sx = body.sx * (body.flip ? -1 : 1), sy = body.sy;
    const M = (p) => [sx * (c * p[0] - s * p[1]), sy * (s * p[0] + c * p[1])];
    const oo = o || [0, 0], mo = M(oo), tx = body.x + oo[0] - mo[0], ty = body.y + oo[1] - mo[1];
    return { map: (p) => { const m = M(p); return [m[0] + tx, m[1] + ty]; }, tx, ty, sx, sy, rad: a };
  }
  return { EASE, bodyAt, trackAt, moveAt, fxFrame, evalClip, eventsBetween, xform };
});
