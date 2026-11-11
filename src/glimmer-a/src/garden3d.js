/* 《微光小圃》 garden3d.js — #89 3D 花園 H1／H1.2（八方旅人式 HD-2D；遊美 art/garden3d-h1-mesh @ 620509fc）。原創代碼。
   純邏輯（Node 可 require，唔使 three.js）：座標、鏡頭 sway／follow、可見區構圖、碰撞、4 方向、日夜光、畫質自動。
   瀏覽器 Scene：Three.js 載 17 件 mesh＋地面＋背景板＋寵物 billboard（radiant 用 dir4；其他形態用 2D sprite 後備）。
   Kurt：三級畫質＋自動偵測＋fps／耗電面板（開發者模式）；?3d=0 返 2D；低畫質／低端機＝2D 後備；
   鏡頭自動擺／跟拍（開發者模式有開關，預設開）。H1.1：寵物 flipY 修正；XZ 走位＋碰撞接入 moveTo；地面網格。
   H1.2：直版可見區構圖（樹／籬笆／燈柱／屋唔被 UI 遮）＋跟拍保建立鏡頭；日影／夜空對齊參考；網格預設關；3D 行速 20 u/s。
   H1.3：寵物自主四圍行（唔使撳）；2D 地面物件全部做 billboard（寫 depth、被擋、影子、坐 XZ、跟光）；細佬自主 nav；遊測 P2／P3（mid 縮影圖、high 減 shadow 更新、LICENSE 入包）。
   H1.4：遊測 H1.3 QA — 屎盒優先命中、半透明 actor alphaTest 0.1、mid 影圖 256、high 關 soft shadow、雨點加大加深。
   H1.5：遊測 H1.4 P2 效能 — 尺寸／dpr 冇變就唔好每幀 setSize；high／mid dpr 上限 1.5／1.25；3D 開時 renderer.frame 唔再畫 L0／L1。
   H1.6：遊測 H1.5 P2 — high dpr 1.5→1；WebGL 緩衝整數倍對齊顯示（關平滑上採）；3D 開時唔畫 2D 寵物。 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else { root.Glimmer = root.Glimmer || {}; root.Glimmer.garden3d = factory(); }
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';
  const W = 195, H = 422, CX = 97, GROUND_Y = 292, ZSCALE = 1.6;
  const KEY_Q = 'glimmer.g3d.quality', KEY_Q_MANUAL = 'glimmer.g3d.qManual', KEY_SWAY = 'glimmer.g3d.sway', KEY_FOLLOW = 'glimmer.g3d.follow', KEY_GRID = 'glimmer.g3d.grid';
  /* 可見花園區：layout_hd2d_v2.json bands.garden 42–348，向下讓過頂欄／頭像／開發者掣，向右讓過 rail，向上讓過 action。 */
  const VIS = { x: 2, y: 64, w: 152, h: 278 };
  const VIS_HFOV_DEG = 29;           /* 參考 day_cam_steady crop 有效橫向 FOV ≈29°；landmark 方位跨度 ≈25° */
  const WALK_SPEED_2D = 15, WALK_SPEED_3D = 20;  /* data.js beh.walkSpeed 維持 15；3D 只喺 g3dWalk 放大 */
  const NIGHT_SRGB = [0.22, 0.26, 0.42];         /* preview_garden3d.py 夜景 unlit 乘色 */
  const FOG_NIGHT = [0.16, 0.2, 0.36];
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const lerp = (a, b, t) => a + (b - a) * t;
  const hex = (c) => { const n = parseInt(String(c || '#ffffff').replace('#', ''), 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255]; };
  const TAU = Math.PI * 2;

  /* ── 座標：3D 原點＝寵物預設腳底 art (97,292)；x＝art x−97；前排 z＝(art y−292)×1.6 ── */
  function artToWorld(ax, ay) { return { x: ax - CX, z: (ay - GROUND_Y) * ZSCALE }; }
  function worldToArtFlat(x, z) { return { x: x + CX, y: GROUND_Y + z / ZSCALE }; }
  function petWorld(beh) {
    const x = beh && beh.x != null ? +beh.x : 0;
    const z = beh && beh.z != null ? +beh.z : (beh && beh.depth ? (+beh.depth) * ZSCALE : 0);
    return { x: x, z: z };
  }

  /* ── 日夜：跟現有 HD-2D 時段（06–16 日、16–19 黃昏、19–06 夜）── */
  function nightMix(hour) {
    const h = ((hour % 24) + 24) % 24;
    if (h >= 6 && h < 16) return 0;
    if (h >= 16 && h < 19) return (h - 16) / 3;
    return 1;
  }
  function mixLights(L, night) {
    night = clamp(night, 0, 1);
    const sun = L.sun || {}, fill = L.fill || {}, N = L.night || {};
    const ambD = hex((sun.ambient && sun.ambient.color) || '#cfe0f0'), ambN = hex(N.ambient || '#4a5a90');
    const points = (L.lights || []).map(function (l) {
      return { id: l.id, x: l.x, y: l.y, z: l.z, color: l.color, radius: l.radius,
        intensity: lerp(l.intensity || 0, l.intensityNight || 0, night), flicker: l.flicker || 0 };
    });
    const byId = {}; points.forEach(function (p) { byId[p.id] = p.intensity; });
    return {
      night: night,
      sun: lerp(sun.intensity == null ? 1 : sun.intensity, N.sun == null ? 0.12 : N.sun, night),
      sunColor: sun.color || '#ffe6b8',
      sunDir: sun.dir || [0.42, -0.72, 0.55],
      shadowIntensity: sun.shadowIntensity == null ? 0.3 : sun.shadowIntensity,
      ambColor: [lerp(ambD[0], ambN[0], night), lerp(ambD[1], ambN[1], night), lerp(ambD[2], ambN[2], night)],
      ambIntensity: lerp((sun.ambient && sun.ambient.intensity) || 0.55, N.ambientIntensity == null ? 0.35 : N.ambientIntensity, night),
      fill: lerp(fill.intensity == null ? 0.38 : fill.intensity, fill.intensityNight == null ? 0 : fill.intensityNight, night),
      fillColor: fill.color || '#ffe2c4',
      fillDir: fill.dir || [0.2, -0.12, -0.97],
      points: points, byId: byId,
      fog: L.fog || { color: '#ffe8c8', near: 420, far: 1400 }
    };
  }

  /* ── 鏡頭：preview_garden3d.py 同行；yaw＝−A·cos(π·t/T) 單程緩入緩出 pingpong；跟拍指數阻尼 ── */
  function swayYaw(t, cam) {
    const A = cam.swayAmplitudeDeg == null ? 5 : cam.swayAmplitudeDeg;
    const T = cam.swayHalfPeriodSec == null ? 6 : cam.swayHalfPeriodSec;
    if (!(T > 0) || A === 0) return cam.yawDeg || 0;
    return -A * Math.cos(Math.PI * t / T);
  }
  function followOriginOf(cam) {
    const w = cam.followWeight || [0.25, 0.3];
    const o = cam.followOffset || [-20, 0];
    const home = cam.followHome || [0, 0];
    /* H1.2 預設：寵物喺家（原點）時 look＝camera.json target，建立鏡頭見齊樹／屋。舊 origin 用 followEstablish:false 還原。 */
    if (cam.followEstablish === false) return cam.followOrigin || [-110, -40];
    const wx = w[0] || 0.25, wz = w[1] || 0.3;
    return [home[0] + (o[0] || 0) / wx, (home[1] || 0) + (o[1] || 0) / wz];
  }
  function followDesired(cam, pet) {
    const tg = cam.target || [0, 30, -72];
    const w = cam.followWeight || [0.25, 0.3];
    const o = cam.followOffset || [-20, 0];
    const or = followOriginOf(cam);
    const px = pet && pet.x != null ? pet.x : 0, pz = pet && pet.z != null ? pet.z : 0;
    const des = [tg[0] + o[0] + w[0] * (px - or[0]), tg[1], tg[2] + (o[1] || 0) + w[1] * (pz - or[1])];
    return followClamp(des, cam);
  }
  function followClamp(des, cam) {
    const tg = cam.target || [0, 30, -72];
    if (cam.followClamp === false) return des;
    const mx = cam.followClampX == null ? 18 : cam.followClampX;
    const mz = cam.followClampZ == null ? 12 : cam.followClampZ;
    return [clamp(des[0], tg[0] - mx, tg[0] + mx), des[1], clamp(des[2], tg[2] - mz, tg[2] + mz)];
  }
  function followStep(cur, desired, dt, damping) {
    const k = 1 - Math.exp(-(damping == null ? 2 : damping) * Math.max(0, dt));
    return [cur[0] + (desired[0] - cur[0]) * k, cur[1] + (desired[1] - cur[1]) * k, cur[2] + (desired[2] - cur[2]) * k];
  }
  function camPos(target, yawDeg, cam) {
    const p = (cam.pitchDeg == null ? 30 : cam.pitchDeg) * Math.PI / 180;
    const yw = yawDeg * Math.PI / 180;
    const d = cam.dist == null ? 580 : cam.dist;
    return [target[0] + d * Math.sin(yw) * Math.cos(p), target[1] + d * Math.sin(p), target[2] + d * Math.cos(yw) * Math.cos(p)];
  }
  function clampYaw(yaw, cam, user) {
    const mn = cam.orbitMinDeg == null ? -10 : cam.orbitMinDeg;
    const mx = cam.orbitMaxDeg == null ? 10 : cam.orbitMaxDeg;
    return clamp((yaw || 0) + (user || 0), mn, mx);
  }
  /* ── 直版可見區：讓 VIS 矩形（唔計 HUD／rail／底欄）擁有參考 GIF 嘅橫向 FOV ── */
  function visibleRect(cam) {
    const v = (cam && cam.vis) || VIS;
    return { x: v.x, y: v.y, w: v.w, h: v.h };
  }
  function visFov(vis, cam) {
    vis = vis || visibleRect(cam);
    const hf = (cam && cam.visHfovDeg != null) ? cam.visHfovDeg : VIS_HFOV_DEG;
    const vf = 2 * Math.atan(Math.tan(hf * Math.PI / 360) * vis.h / vis.w) * 180 / Math.PI;
    return { hfovDeg: hf, vfovDeg: vf, vis: vis };
  }
  function viewOffset(vis, width, height) {
    vis = vis || VIS;
    width = width == null ? W : width; height = height == null ? H : height;
    return { fullWidth: vis.w, fullHeight: vis.h, x: -vis.x, y: -vis.y, width: width, height: height };
  }
  function srgbToLinear(k) {
    k = clamp(k, 0, 1);
    return k <= 0.04045 ? k / 12.92 : Math.pow((k + 0.055) / 1.055, 2.4);
  }
  function nightBackdropFactor(night) {
    night = clamp(night, 0, 1);
    return NIGHT_SRGB.map(function (k) { return srgbToLinear(lerp(1, k, night)); });
  }
  function shadowIntensityLin(si) {
    /* preview 喺 sRGB 用 sh*=(1−SI)；three.js shadow.intensity 喺 linear mix。轉成等效濃度。 */
    si = si == null ? 0.3 : si;
    return 1 - srgbToLinear(1 - clamp(si, 0, 1));
  }
  function walkStep3d(st) {
    return (st || 0) * (WALK_SPEED_3D / WALK_SPEED_2D);
  }
  function emissiveScale(id) {
    if (!id) return 1;
    if (id === 'jar') return 0.7;
    if (id === 'lamp') return 1.7;
    if (id.indexOf('lantern') === 0) return 1.65;
    if (id.indexOf('window') === 0) return 1.3;
    return 1;
  }
  function pointScale(id) {
    return id === 'jar' ? 1.05 : 2.2;
  }

  /* ── 4 方向：|dx|≥|dz| → side（dx<0 鏡像）；dz>0 front；dz<0 back。fps idle 4／walk 10 ── */
  function dirOf(dx, dz, moving) {
    const clip = moving ? 'walk' : 'idle';
    if (Math.abs(dx) >= Math.abs(dz)) return { dir: 'side', flip: dx < 0, clip: clip };
    return { dir: dz < 0 ? 'back' : 'front', flip: false, clip: clip };
  }
  function frameName(info, t) {
    const n = info.clip === 'walk' ? 6 : 4, fps = info.clip === 'walk' ? 10 : 4;
    const i = ((Math.floor(Math.max(0, t) * fps) % n) + n) % n + 1;
    return info.dir + '_' + info.clip + '_' + (i < 10 ? '0' : '') + i;
  }

  /* ── 碰撞：寵物半徑唔可以入 footprint 外擴 pad＋radius（串燈／補位件冇 footprint）── */
  function distRect(x, z, r) {
    const dx = x < r.x[0] ? r.x[0] - x : x > r.x[1] ? x - r.x[1] : 0;
    const dz = z < r.z[0] ? r.z[0] - z : z > r.z[1] ? z - r.z[1] : 0;
    return Math.hypot(dx, dz);
  }
  function distPoly(x, z, pts) {
    let inside = false, min = Infinity, n = pts.length;
    for (let i = 0, j = n - 1; i < n; j = i++) {
      const xi = pts[i][0], zi = pts[i][1], xj = pts[j][0], zj = pts[j][1];
      const den = Math.hypot(xj - xi, zj - zi) || 1e-9;
      const t = clamp(((x - xi) * (xj - xi) + (z - zi) * (zj - zi)) / (den * den), 0, 1);
      min = Math.min(min, Math.hypot(x - (xi + t * (xj - xi)), z - (zi + t * (zj - zi))));
      const hit = ((zi > z) !== (zj > z)) && (x < (xj - xi) * (z - zi) / ((zj - zi) || 1e-9) + xi);
      if (hit) inside = !inside;
    }
    return inside ? 0 : min;
  }
  function fpDist(fp, x, z) {
    if (!fp) return Infinity;
    if (fp.type === 'poly' && fp.points) return distPoly(x, z, fp.points);
    if (fp.type === 'rect' && fp.x && fp.z) return distRect(x, z, fp);
    if (fp.rect) return distRect(x, z, fp.rect);
    if (fp.poly) return distPoly(x, z, fp.poly);
    return Infinity;
  }
  function blocked(objects, x, z, radius) {
    radius = radius == null ? 10 : radius;
    const hit = [];
    (objects || []).forEach(function (o) {
      const fp = o.footprint; if (!fp || o.backfill) return;
      const d = fpDist(fp, x, z), pad = (fp.pad == null ? 0 : fp.pad);
      if (d < pad + radius) hit.push(o.id);
    });
    return hit;
  }

  /* ── XZ 走位：喺地面真正前後左右行；撞到 footprint 就沿邊滑／繞。?3d=0 唔用。── */
  const RANGE3 = { x: [-140, 140], z: [-125, 100] };
  const WALK_LANDMARKS = [
    { x: 82, z: -110, tag: 'behind_cottage' },
    { x: -88, z: -80, tag: 'behind_tree' },
    { x: -110, z: -70, tag: 'tree_side' },
    { x: -81, z: 40, tag: 'behind_pot_L' },
    { x: 0, z: 60, tag: 'front' },
    { x: 40, z: 50, tag: 'front_R' },
    { x: 90, z: 0, tag: 'right' },
    { x: -90, z: 0, tag: 'left' },
    { x: 20, z: -70, tag: 'yard_back' },
    { x: 0, z: 20, tag: 'front_near' },
    { x: 49, z: 5, tag: 'near_pot_S' }
  ];
  function inRange3(x, z, range) {
    range = range || RANGE3;
    const rx = range.x || range, rz = range.z || range;
    return x >= rx[0] && x <= rx[1] && z >= rz[0] && z <= rz[1];
  }
  const NEAR_FREE_R = 12;          /* 小屋中心距可企格 >4 格（32u），用 12 格（96u） */
  const ARRIVE_DIST = 2;           /* 到達距離下限（同 step 取大） */
  const STALL_STEPS = 16;          /* 冇進展 N 步＝卡住，停止喺圍欄／花盆前打轉 */
  function snapDest(objects, tx, tz, radius, rangeX, rangeZ) {
    radius = radius == null ? 10 : radius;
    const rx = rangeX || RANGE3.x, rz = rangeZ || RANGE3.z;
    tx = clamp(tx == null ? 0 : tx, rx[0], rx[1]);
    tz = clamp(tz == null ? 0 : tz, rz[0], rz[1]);
    if (!blocked(objects, tx, tz, radius).length) return { x: tx, z: tz, snapped: false };
    const cell = 8, x0 = rx[0], z0 = rz[0];
    const nx = Math.round((rx[1] - rx[0]) / cell), nz = Math.round((rz[1] - rz[0]) / cell);
    const toW = function (ix, iz) { return { x: x0 + ix * cell, z: z0 + iz * cell }; };
    const toC = function (wx, wz) {
      return [Math.max(0, Math.min(nx, Math.round((wx - x0) / cell))), Math.max(0, Math.min(nz, Math.round((wz - z0) / cell)))];
    };
    const walkable = function (ix, iz) {
      if (ix < 0 || iz < 0 || ix > nx || iz > nz) return false;
      const w = toW(ix, iz);
      return !blocked(objects, w.x, w.z, radius).length;
    };
    const c = toC(tx, tz);
    if (walkable(c[0], c[1])) return { x: tx, z: tz, snapped: false };
    for (let r = 1; r <= NEAR_FREE_R; r++) {
      for (let dx = -r; dx <= r; dx++) for (let dz = -r; dz <= r; dz++) {
        if (Math.max(Math.abs(dx), Math.abs(dz)) !== r) continue;
        if (walkable(c[0] + dx, c[1] + dz)) {
          const w = toW(c[0] + dx, c[1] + dz);
          return { x: w.x, z: w.z, snapped: true };
        }
      }
    }
    return { x: tx, z: tz, snapped: false };
  }
  function stepXZ(objects, x, z, tx, tz, step, radius, rangeX, rangeZ) {
    step = Math.max(0, step || 0);
    radius = radius == null ? 10 : radius;
    const rx = rangeX || RANGE3.x, rz = rangeZ || RANGE3.z;
    const free = function (nx, nz) {
      if (nx < rx[0] || nx > rx[1] || nz < rz[0] || nz > rz[1]) return false;
      return !blocked(objects, nx, nz, radius).length;
    };
    if (!free(tx, tz)) {
      const sn = snapDest(objects, tx, tz, radius, rx, rz);
      tx = sn.x; tz = sn.z;
    }
    const dist = Math.hypot(tx - x, tz - z);
    const eps = Math.max(step, ARRIVE_DIST);
    if (dist <= eps) {
      if (free(tx, tz)) return { x: tx, z: tz, arrived: true, dx: tx - x, dz: tz - z };
      return { x: x, z: z, arrived: false, dx: 0, dz: 0, stuck: true };
    }
    const ang = Math.atan2(tz - z, tx - x);
    const tryA = [0, 1, -1, 2, -2, 3, -3, 4];
    for (let i = 0; i < tryA.length; i++) {
      const a = ang + tryA[i] * Math.PI / 4;
      const nx = x + Math.cos(a) * step, nz = z + Math.sin(a) * step;
      if (free(nx, nz)) return { x: nx, z: nz, arrived: false, dx: nx - x, dz: nz - z };
    }
    return { x: x, z: z, arrived: false, dx: 0, dz: 0, stuck: true };
  }
  /* 粗格 A*（8 向，8 unit 一格）：去物件後面要繞圍欄／小屋，單靠貪心會卡牆 */
  function buildPath(objects, x, z, tx, tz, radius, rangeX, rangeZ) {
    radius = radius == null ? 10 : radius;
    const rx = rangeX || RANGE3.x, rz = rangeZ || RANGE3.z;
    const cell = 8;
    const x0 = rx[0], z0 = rz[0];
    const nx = Math.round((rx[1] - rx[0]) / cell), nz = Math.round((rz[1] - rz[0]) / cell);
    const toW = function (ix, iz) { return { x: x0 + ix * cell, z: z0 + iz * cell }; };
    const toC = function (wx, wz) {
      return [Math.max(0, Math.min(nx, Math.round((wx - x0) / cell))), Math.max(0, Math.min(nz, Math.round((wz - z0) / cell)))];
    };
    const walkable = function (ix, iz) {
      if (ix < 0 || iz < 0 || ix > nx || iz > nz) return false;
      const w = toW(ix, iz);
      return !blocked(objects, w.x, w.z, radius).length;
    };
    const nearFree = function (ix, iz) {
      if (walkable(ix, iz)) return [ix, iz];
      for (let r = 1; r <= NEAR_FREE_R; r++) {
        for (let dx = -r; dx <= r; dx++) for (let dz = -r; dz <= r; dz++) {
          if (Math.max(Math.abs(dx), Math.abs(dz)) !== r) continue;
          if (walkable(ix + dx, iz + dz)) return [ix + dx, iz + dz];
        }
      }
      return null;
    };
    const snapped = snapDest(objects, tx, tz, radius, rx, rz);
    tx = snapped.x; tz = snapped.z;
    let sc = nearFree.apply(null, toC(x, z)), gc = nearFree.apply(null, toC(tx, tz));
    if (!sc || !gc) return [{ x: tx, z: tz }];
    const sk = sc[0] + ',' + sc[1], gk = gc[0] + ',' + gc[1];
    if (sk === gk) return [{ x: tx, z: tz }];
    const open = [{ ix: sc[0], iz: sc[1], g: 0, f: Math.hypot(gc[0] - sc[0], gc[1] - sc[1]), from: null }];
    const seen = {}; seen[sk] = 0;
    const dirs = [[1, 0], [-1, 0], [0, 1], [0, -1], [1, 1], [1, -1], [-1, 1], [-1, -1]];
    let found = null, guard = 0;
    while (open.length && guard++ < 4000) {
      let bi = 0; for (let i = 1; i < open.length; i++) if (open[i].f < open[bi].f) bi = i;
      const cur = open.splice(bi, 1)[0];
      if (cur.ix === gc[0] && cur.iz === gc[1]) { found = cur; break; }
      for (let d = 0; d < dirs.length; d++) {
        const ix = cur.ix + dirs[d][0], iz = cur.iz + dirs[d][1];
        if (!walkable(ix, iz)) continue;
        const g = cur.g + Math.hypot(dirs[d][0], dirs[d][1]);
        const k = ix + ',' + iz;
        if (seen[k] != null && seen[k] <= g + 1e-9) continue;
        seen[k] = g;
        open.push({ ix: ix, iz: iz, g: g, f: g + Math.hypot(gc[0] - ix, gc[1] - iz), from: cur });
      }
    }
    if (!found) return [{ x: tx, z: tz }];
    const cells = [];
    for (let n = found; n; n = n.from) cells.push(n);
    cells.reverse();
    const path = cells.map(function (c) { return toW(c.ix, c.iz); });
    if (!blocked(objects, tx, tz, radius).length) path.push({ x: tx, z: tz });
    return path;
  }
  function followPath(objects, x, z, path, dest, step, radius, rangeX, rangeZ, pi, stall) {
    pi = pi || 0;
    stall = stall || 0;
    const goal = dest || (path && path.length ? path[path.length - 1] : null);
    const g = goal ? snapDest(objects, goal.x, goal.z, radius, rangeX, rangeZ) : null;
    if (!path || !path.length) {
      const r0 = stepXZ(objects, x, z, g ? g.x : dest.x, g ? g.z : dest.z, step, radius, rangeX, rangeZ);
      return { step: r0, pi: 0, stall: stall };
    }
    while (pi < path.length && Math.hypot(path[pi].x - x, path[pi].z - z) <= Math.max(step, 4)) pi++;
    const wp = pi >= path.length ? (g || path[path.length - 1]) : path[pi];
    const r = stepXZ(objects, x, z, wp.x, wp.z, step, radius, rangeX, rangeZ);
    const eps = Math.max(step, ARRIVE_DIST);
    const atGoal = g && Math.hypot(g.x - r.x, g.z - r.z) <= eps && !blocked(objects, r.x, r.z, radius).length;
    if (atGoal) r.arrived = true;
    const moved = Math.hypot(r.dx || 0, r.dz || 0);
    if (r.stuck || moved < Math.max(0.05, step * 0.1)) stall++; else stall = 0;
    if (r.stuck || stall >= STALL_STEPS) { r.stuck = true; r.arrived = true; }
    return { step: r, pi: pi, stall: stall };
  }
  function pickWalk(objects, rng, from, radius, range) {
    range = range || RANGE3;
    radius = radius == null ? 10 : radius;
    const r = (typeof rng === 'function') ? rng : Math.random;
    const fx = from && from.x != null ? from.x : 0, fz = from && from.z != null ? from.z : 0;
    const far = function (x, z) { return Math.hypot(x - fx, z - fz) > 16; };
    const okp = function (x, z) { return inRange3(x, z, range) && !blocked(objects, x, z, radius).length && far(x, z); };
    if (r() < 0.4) {
      const L = WALK_LANDMARKS.slice();
      for (let i = L.length - 1; i > 0; i--) { const j = Math.floor(r() * (i + 1)); const tmp = L[i]; L[i] = L[j]; L[j] = tmp; }
      for (let i = 0; i < L.length; i++) { if (okp(L[i].x, L[i].z)) return { x: L[i].x, z: L[i].z, tag: L[i].tag }; }
    }
    for (let i = 0; i < 24; i++) {
      const x = range.x[0] + r() * (range.x[1] - range.x[0]);
      const z = range.z[0] + r() * (range.z[1] - range.z[0]);
      if (okp(x, z)) return { x: x, z: z, tag: 'rand' };
    }
    return { x: 0, z: 20, tag: 'front_near' };
  }

  /* ── H1.3：2D 花園地面／世界物件清單（會喺地面或花園空間出現嘅嘢）── */
  const POOP_SLOTS = [[50, 304], [146, 302], [118, 318]];  /* 同 render.js 一致 */
  function poopWorld(i) {
    const p = POOP_SLOTS[i];
    return p ? artToWorld(p[0], p[1]) : null;
  }
  const WORLD_ITEMS = [
    { id: 'pet', zh: '寵物', how: '既有 billboard（dir4／2D 後備）', inGarden: true, wantArt: '其他形態 dir4' },
    { id: 'kid', zh: '細佬', how: 'billboard＋自主 XZ nav', inGarden: true, wantArt: '細佬 dir4＋法線' },
    { id: 'kidEgg', zh: '細佬蛋', how: 'billboard', inGarden: true, wantArt: null },
    { id: 'dreamBubble', zh: '孵夢／怪夢泡泡', how: 'billboard（浮喺寵物或蛋上）', inGarden: true, wantArt: null },
    { id: 'poop', zh: '便便', how: 'billboard＋raycast 清理', inGarden: true, wantArt: '便便 3D／法線' },
    { id: 'pot', zh: '花盆', how: '已有 3D mesh（pot_L／R／S）', inGarden: true, wantArt: null },
    { id: 'potProp', zh: '撞盆掉落小物', how: 'billboard', inGarden: true, wantArt: null },
    { id: 'ball', zh: '玩具波', how: 'billboard', inGarden: true, wantArt: '3D 小球' },
    { id: 'food', zh: '食物', how: '餵食時暫時 billboard', inGarden: true, wantArt: '常駐食碗（遊戲而家冇）' },
    { id: 'foodBowl', zh: '食物碗', how: '2D 花園冇常駐食碗（只列）', inGarden: false, wantArt: '常駐食碗美術' },
    { id: 'wash', zh: '沖洗水泡', how: 'billboard 粒子', inGarden: true, wantArt: null },
    { id: 'fx', zh: 'FX（心心／火花／汗／蒸氣／塵／字／zzz）', how: 'billboard', inGarden: true, wantArt: null },
    { id: 'event', zh: '事件特效（蝴蝶／禮物／寶藏／icon；流星／彩虹 overlay）', how: '地面件 billboard；天空件 overlay', inGarden: true, wantArt: null },
    { id: 'visitor', zh: '訪客', how: 'billboard（跟 2D 行位 artic 轉 XZ）', inGarden: true, wantArt: '訪客 dir4' },
    { id: 'visitProp', zh: '訪客信／種子／心心', how: 'billboard', inGarden: true, wantArt: null },
    { id: 'decor', zh: '友誼擺設（郵筒／蘑菇燈／螢火瓶）', how: 'billboard（場景已有 jar／mushroom mesh 就唔再疊）', inGarden: true, wantArt: '郵筒 3D mesh' },
    { id: 'shadow', zh: '6d 朋友影子', how: 'billboard＋XZ 行', inGarden: true, wantArt: '影子 3D 造型' },
    { id: 'weather', zh: '天氣粒子（雨）', how: '3D 雨點', inGarden: true, wantArt: '季節／霧疊 3D' },
    { id: 'omen', zh: '3b 預兆閃剪影／怪夢', how: 'billboard', inGarden: true, wantArt: null },
    { id: 'souvenir', zh: '手信 souvenir', how: '入屋仔家具庫，花園唔落地', inGarden: false, wantArt: '花園手信位（若 Kurt 要擺出嚟）' },
    { id: 'sunPatch', zh: '日光斑', how: '地面 decal／略過（地面已有光）', inGarden: true, wantArt: null }
  ];
  function worldItem(id) { return WORLD_ITEMS.filter(function (x) { return x.id === id; })[0] || null; }
  function worldInGarden() { return WORLD_ITEMS.filter(function (x) { return x.inGarden; }); }
  function worldWantArt() { return WORLD_ITEMS.filter(function (x) { return !!x.wantArt; }); }

  /* 自主行：3D 企咗超過 idleSec 就強制行（唔打斷 variant／瞓／事件） */
  const G3D_IDLE_WALK_SEC = 3.2;
  const G3D_WALK_MUL = 2.6;
  const G3D_STAY_MUL = 0.4;
  const G3D_DECIDE_EVERY = [1.8, 3.6];
  function shouldForceWalk(b, t, idleSec) {
    if (!b || b.variant || (b.hushUntil > t)) return false;
    if (b.state && b.state !== 'stay') return false;
    const last = b.lastWalkAt || 0;
    return (t - last) >= (idleSec == null ? G3D_IDLE_WALK_SEC : idleSec) && (b.stateT || 0) >= 1.15;
  }
  function wanderWeights(w) {
    const o = {};
    for (const k in w) o[k] = w[k];
    if (o.walk != null) o.walk *= G3D_WALK_MUL;
    if (o.stay != null) o.stay *= G3D_STAY_MUL;
    return o;
  }

  /* ── 畫質：high／mid＝3D；low＝2D 後備。?3d=0 永遠 2D；低端機自動 low。── */
  const QSET = {
    high: { dpr: 1, shadow: 1024, tex3x: true, shadows: true, shadowEvery: 3, softShadow: false },    /* H1.6：dpr 上限 1（整數倍 195×422→390×844，關平滑） */
    mid: { dpr: 1, shadow: 256, tex3x: false, shadows: true, shadowEvery: 2, softShadow: false },     /* H1.6：after 量度後 mid 亦 dpr 1（整數倍），影圖 256、每 2 幀 */
    low: { dpr: 1, shadow: 0, tex3x: false, shadows: false, shadowEvery: 0, softShadow: false }
  };
  /* k＝2D 顯示倍數；dprCap＝3D 幀緩衝上限。回傳 WebGL 實際像素。 */
  function viewScale(k, dprCap) {
    k = k || 2;
    const gk = Math.min(k, dprCap == null ? k : dprCap);
    const w = Math.max(1, Math.round(W * gk)), h = Math.max(1, Math.round(H * gk));
    const dw = W * k, dh = H * k;
    const integer = (w === dw && h === dh) || (dw % w === 0 && dh % h === 0);
    return { gk: gk, w: w, h: h, dw: dw, dh: dh, integer: integer };
  }
  const ACTOR_ALPHA_SOFT = 0.1;  /* 低過 6d 影子 alpha 0.45，半透明片元唔好被切走 */
  const RAIN = { n: 200, size: 6, color: 0x4a6a96, opacity: 0.9, sizeAttenuation: false };
  function detectQuality(o) {
    o = o || {};
    const qs = o.qs || {};
    const v = qs['3d'];
    if (o.force === 'off' || v === '0') return { want: false, quality: 'low', reason: 'off' };
    if (o.webgl === false) return { want: false, quality: 'low', reason: 'nowebgl' };
    if (v === 'high' || v === 'mid' || v === 'low') return { want: v !== 'low', quality: v, reason: 'qs' };
    /* H1.6：自動偵測唔可高過 low；mid／high 只喺開發者模式（或 ?3d=mid／high）先揀 */
    if (v === '1') return { want: false, quality: 'low', reason: 'auto' };
    const lowEnd = (o.hardwareConcurrency != null && o.hardwareConcurrency <= (o.lowEndCores || 4))
      || (o.deviceMemory != null && o.deviceMemory <= (o.lowEndMemGB || 4));
    if (lowEnd) return { want: false, quality: 'low', reason: 'lowend' };
    return { want: false, quality: 'low', reason: 'auto' };
  }
  function hasWebGL() {
    if (typeof document === 'undefined') return false;
    try {
      const c = document.createElement('canvas');
      return !!(c.getContext('webgl2') || c.getContext('webgl') || c.getContext('experimental-webgl'));
    } catch (e) { return false; }
  }
  function lsGet(k, d) { try { const v = localStorage.getItem(k); return v == null ? d : v; } catch (e) { return d; } }
  function lsSet(k, v) { try { localStorage.setItem(k, v); } catch (e) { } }

  // ───────── 瀏覽器 Scene ─────────
  function Scene(opts) {
    opts = opts || {};
    this.base = opts.base || 'art/garden3d/H1/';
    this.dir4base = opts.dir4base || 'art/garden3d/dir4/';
    this.enabled = opts.enabled !== false;
    this.quality = opts.quality || 'low';
    this.swayOn = opts.swayOn !== false;
    this.followOn = opts.followOn !== false;
    this.gridOn = !!opts.gridOn;
    this.ready = false; this.error = null; this.loaded = false;
    this.t = 0; this.userYaw = 0; this.look = null; this.yaw = 0;
    this.pet = { x: 0, z: 0, dx: 0, dz: 0, moving: false, glow: 1, form: 'radiant', facing: { dir: 'front', flip: false, clip: 'idle' } };
    this.stat = { draws: 0, meshes: 0, frames: 0, ms: 0, fps: 0, lastMs: 0 };
    this.perf = { n: 0, sum: 0, max: 0, last: 0, fps: 0, acc: 0, fn: 0 };
    this.objects = []; this.lightsJ = null; this.camJ = null; this.objJ = null;
    this._drag = null; this._fbSprite = null; this._night = 0;
    this.lost = false;
  }
  Scene.prototype.on = function () { return !!(this.enabled && this.ready && this.quality !== 'low' && !this.lost); };
  Scene.prototype.ownsPet = function () { return this.on(); };
  Scene.prototype.qs = function () { return QSET[this.quality] || QSET.high; };

  Scene.prototype.load = function () {
    const self = this, B = this.base, D4 = this.dir4base;
    const THREE = (typeof window !== 'undefined' && window.THREE) || (typeof globalThis !== 'undefined' && globalThis.THREE);
    if (!THREE) { this.error = 'no THREE'; return Promise.resolve(false); }
    const img = (u) => new Promise(function (res, rej) { const im = new Image(); im.onload = function () { res(im); }; im.onerror = function () { rej(new Error(u)); }; im.src = u; });
    const js = (u) => fetch(u).then(function (r) { if (!r.ok) throw new Error(u + ' ' + r.status); return r.json(); });
    return Promise.all([js(B + 'objects.json'), js(B + 'lights.json'), js(B + 'camera.json'),
      js(D4 + 'atlas_radiant_dir4.json'), img(D4 + 'atlas_radiant_dir4.png'), img(D4 + 'atlas_radiant_dir4_n.png'), img(D4 + 'atlas_radiant_dir4_emissive.png')
    ]).then(function (pack) {
      const oj = pack[0], lj = pack[1], cj = pack[2];
      self.objJ = oj; self.lightsJ = lj; self.camJ = cj;
      self.dir4 = { json: pack[3], img: pack[4], n: pack[5], e: pack[6] };
      self.objects = oj.objects || [];
      const jobs = [];
      const g = oj.ground;
      jobs.push(Promise.all([img(B + g.file), img(B + g.file3x), img(B + g.ao), img(B + g.ao3x), img(B + g.outerTile.file), img(B + g.outerTile.file3x)]).then(function (im) {
        self.groundIm = { c1: im[0], c3: im[1], ao1: im[2], ao3: im[3], t1: im[4], t3: im[5] };
      }));
      self.meshJ = {}; self.meshIm = {};
      self.objects.forEach(function (o) {
        if (o.type === 'mesh') {
          jobs.push(js(B + o.mesh).then(function (m) {
            self.meshJ[o.id] = m;
            const te = [];
            te.push(img(B + m.texture), img(B + m.texture3x));
            if (m.emissive) te.push(img(B + m.emissive), img(B + m.emissive3x));
            return Promise.all(te).then(function (ims) { self.meshIm[o.id] = { c1: ims[0], c3: ims[1], e1: ims[2], e3: ims[3] }; });
          }));
        } else if (o.type === 'backdrop') {
          jobs.push(Promise.all([img(B + o.file), img(B + o.file3x)]).then(function (ims) { self.meshIm[o.id] = { c1: ims[0], c3: ims[1] }; }));
        }
      });
      return Promise.all(jobs);
    }).then(function () {
      self._build(THREE);
      self.ready = true; self.loaded = true; self.stat.meshes = (self.objects.filter(function (o) { return o.type === 'mesh'; }).length);
      return true;
    }).catch(function (e) { self.error = String(e && e.message || e); self.ready = false; return false; });
  };

  Scene.prototype._tex = function (THREE, im, opts) {
    opts = opts || {};
    const t = new THREE.Texture(im);
    t.magFilter = t.minFilter = THREE.NearestFilter;
    t.generateMipmaps = false;
    t.wrapS = t.wrapT = opts.repeat ? THREE.RepeatWrapping : THREE.ClampToEdgeWrapping;
    if (opts.repeat) { t.repeat.set(opts.repeat[0], opts.repeat[1]); }
    if (opts.srgb && THREE.SRGBColorSpace) t.colorSpace = THREE.SRGBColorSpace;
    t.needsUpdate = true;
    t.flipY = opts.flipY !== false; // images default flipY true（同 three 慣例；mesh uv 已經 V 上）
    if (opts.flipY === false) t.flipY = false;
    return t;
  };
  Scene.prototype._aoAlbedo = function (color, ao) {
    const c = document.createElement('canvas'); c.width = color.width; c.height = color.height;
    const x = c.getContext('2d', { willReadFrequently: true }); x.imageSmoothingEnabled = false; x.drawImage(color, 0, 0);
    const ac = document.createElement('canvas'); ac.width = c.width; ac.height = c.height;
    const ax = ac.getContext('2d', { willReadFrequently: true }); ax.imageSmoothingEnabled = false; ax.drawImage(ao, 0, 0, c.width, c.height);
    const cd = x.getImageData(0, 0, c.width, c.height), ad = ax.getImageData(0, 0, c.width, c.height);
    const d = cd.data, a = ad.data;
    for (let i = 0; i < d.length; i += 4) { const m = a[i] / 255; d[i] *= m; d[i + 1] *= m; d[i + 2] *= m; }
    x.putImageData(cd, 0, 0);
    return c;
  };
  Scene.prototype._flipUVV = function (geo) {
    const uv = geo.attributes.uv; for (let i = 0; i < uv.count; i++) uv.setY(i, 1 - uv.getY(i)); uv.needsUpdate = true;
  };

  Scene.prototype._build = function (THREE) {
    const self = this, Q = this.qs();
    if (this.renderer) { try { this.renderer.dispose(); } catch (e) { } }
    const canvas = document.createElement('canvas');
    canvas.width = W * 2; canvas.height = H * 2;
    const renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: false, alpha: false, preserveDrawingBuffer: true, powerPreference: this.quality === 'high' ? 'high-performance' : 'low-power' });
    renderer.outputColorSpace = THREE.SRGBColorSpace || renderer.outputColorSpace;
    if ('useLegacyLights' in renderer) renderer.useLegacyLights = true;
    renderer.shadowMap.enabled = !!Q.shadows;
    renderer.shadowMap.type = (Q.softShadow === false) ? THREE.PCFShadowMap : THREE.PCFSoftShadowMap;
    renderer.setPixelRatio(1);
    renderer.setSize(W * 2, H * 2, false);
    renderer.setClearColor(0xffe8c8, 1);
    this.canvas = canvas; this.renderer = renderer;
    this._fb = null;  /* 新 renderer 要再 setSize 去 dpr 上限 */
    this.lost = false;
    const selfLost = this;
    canvas.addEventListener('webglcontextlost', function (e) {
      try { e.preventDefault(); } catch (err) { }
      selfLost.lost = true;
    });
    canvas.addEventListener('webglcontextrestored', function () {
      selfLost.lost = false;
      try { selfLost._build(window.THREE); selfLost.ready = true; } catch (err) { selfLost.error = String(err && err.message || err); selfLost.ready = false; }
    });
    const scene = new THREE.Scene();
    this.scene = scene;
    const cam = new THREE.PerspectiveCamera(40, W / H, 10, 4000);
    this.camera = cam;
    this.look = followDesired(this.camJ, this.pet);

    // fog
    const fog = this.lightsJ.fog || { color: '#ffe8c8', near: 420, far: 1400 };
    scene.fog = new THREE.Fog(fog.color, fog.near, fog.far);

    // lights
    this.ambL = new THREE.AmbientLight(0xcfe0f0, 0.55); scene.add(this.ambL);
    this.sunL = new THREE.DirectionalLight(0xffe6b8, 1); this.sunL.castShadow = !!Q.shadows;
    this.sunL.shadow.intensity = shadowIntensityLin((this.lightsJ.sun && this.lightsJ.sun.shadowIntensity) || 0.3);
    this.sunL.shadow.mapSize.set(Q.shadow || 1024, Q.shadow || 1024);
    const sc = this.sunL.shadow.camera; sc.left = -280; sc.right = 280; sc.top = 280; sc.bottom = -160; sc.near = 10; sc.far = 1800;
    this.sunL.shadow.bias = -0.0008;
    scene.add(this.sunL); scene.add(this.sunL.target);
    this.fillL = new THREE.DirectionalLight(0xffe2c4, 0.38); this.fillL.castShadow = false; scene.add(this.fillL);
    this.hemiL = new THREE.HemisphereLight(0xcfe0f0, 0x3a2818, 0.22); scene.add(this.hemiL);
    this.pointL = [];
    (this.lightsJ.lights || []).forEach(function (l) {
      const pl = new THREE.PointLight(l.color, 0, l.radius || 40, 2);
      pl.position.set(l.x, l.y, l.z); pl.userData.id = l.id; pl.castShadow = false;
      scene.add(pl); self.pointL.push({ light: pl, src: l });
    });

    // ground + outer tile
    const use3 = Q.tex3x;
    const tileIm = use3 ? this.groundIm.t3 : this.groundIm.t1;
    // 外圍 tile：以 (−128,−128) 對齊每 64 units；平面 x±640、z −480…+320（中心 z −80）
    const tile = this._tex(THREE, tileIm, { srgb: true, repeat: [1280 / 64, 800 / 64], flipY: true });
    tile.offset.set(-8, -5.5);
    const tileMat = new THREE.MeshLambertMaterial({ map: tile });
    const tileGeo = new THREE.PlaneGeometry(1280, 800);
    this._flipUVV(tileGeo);
    const tileMesh = new THREE.Mesh(tileGeo, tileMat);
    tileMesh.rotation.x = -Math.PI / 2; tileMesh.position.set(0, -0.2, -80); tileMesh.receiveShadow = !!Q.shadows;
    scene.add(tileMesh); this.tileMesh = tileMesh;

    const gIm = use3 ? this.groundIm.c3 : this.groundIm.c1, aoIm = use3 ? this.groundIm.ao3 : this.groundIm.ao1;
    const gCanvas = this._aoAlbedo(gIm, aoIm);
    const gTex = this._tex(THREE, gCanvas, { srgb: true, flipY: true });
    const gMat = new THREE.MeshLambertMaterial({ map: gTex });
    const gGeo = new THREE.PlaneGeometry(256, 256);
    this._flipUVV(gGeo);   // rotX −90 之後世界 z＝−localY；翻 v 令 v=(z+128)/256（圖頂 z −128）
    const gMesh = new THREE.Mesh(gGeo, gMat);
    gMesh.rotation.x = -Math.PI / 2; gMesh.position.set(0, 0, 0); gMesh.receiveShadow = !!Q.shadows;
    scene.add(gMesh); this.groundMesh = gMesh;

    // 地面網格：令地面讀成有深度嘅平面（每 16／64 units 一條線），唔好似貼平 backdrop
    const gridC = document.createElement('canvas'); gridC.width = 256; gridC.height = 256;
    const gx = gridC.getContext('2d'); gx.clearRect(0, 0, 256, 256);
    gx.fillStyle = 'rgba(48, 30, 18, 0.20)';
    for (let i = 0; i <= 256; i += 16) { gx.fillRect(i, 0, 1, 256); gx.fillRect(0, i, 256, 1); }
    gx.fillStyle = 'rgba(48, 30, 18, 0.38)';
    for (let i = 0; i <= 256; i += 64) { gx.fillRect(i, 0, 1, 256); gx.fillRect(0, i, 256, 1); }
    const gridTex = this._tex(THREE, gridC, { srgb: false, flipY: true });
    const gridMat = new THREE.MeshBasicMaterial({ map: gridTex, transparent: true, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -1, polygonOffsetUnits: -1 });
    const gridGeo = new THREE.PlaneGeometry(256, 256);
    this._flipUVV(gridGeo);
    const gridMesh = new THREE.Mesh(gridGeo, gridMat);
    gridMesh.rotation.x = -Math.PI / 2; gridMesh.position.set(0, 0.08, 0); gridMesh.renderOrder = 1;
    gridMesh.receiveShadow = false; gridMesh.castShadow = false;
    scene.add(gridMesh); this.gridMesh = gridMesh;
    // 外圍 64-unit 疏格，透視延伸到花園外
    const ogC = document.createElement('canvas'); ogC.width = 64; ogC.height = 64;
    const ogx = ogC.getContext('2d'); ogx.clearRect(0, 0, 64, 64);
    ogx.fillStyle = 'rgba(48, 30, 18, 0.16)';
    ogx.fillRect(0, 0, 1, 64); ogx.fillRect(0, 0, 64, 1);
    const ogTex = this._tex(THREE, ogC, { srgb: false, repeat: [1280 / 64, 800 / 64], flipY: true });
    ogTex.offset.set(-8, -5.5);
    const ogMat = new THREE.MeshBasicMaterial({ map: ogTex, transparent: true, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -1, polygonOffsetUnits: -1 });
    const ogGeo = new THREE.PlaneGeometry(1280, 800);
    this._flipUVV(ogGeo);
    const ogMesh = new THREE.Mesh(ogGeo, ogMat);
    ogMesh.rotation.x = -Math.PI / 2; ogMesh.position.set(0, 0.06, -80); ogMesh.renderOrder = 0;
    scene.add(ogMesh); this.outerGridMesh = ogMesh;
    this._syncGrid();

    // meshes + backdrops
    this.meshObj = {}; this.emissiveMat = []; this.backdropMat = [];
    this.objects.forEach(function (o) {
      if (o.type === 'mesh') {
        const m = self.meshJ[o.id], ims = self.meshIm[o.id];
        const geo = new THREE.BufferGeometry();
        geo.setAttribute('position', new THREE.Float32BufferAttribute(m.positions, 3));
        geo.setAttribute('normal', new THREE.Float32BufferAttribute(m.normals, 3));
        geo.setAttribute('uv', new THREE.Float32BufferAttribute(m.uvs, 2));
        geo.setIndex(m.indices);
        // mesh UV 係 V 上、原點左下（three.js 慣例）→ flipY 保持預設 true
        const cmap = self._tex(THREE, use3 ? ims.c3 : ims.c1, { srgb: true });
        const mat = new THREE.MeshLambertMaterial({
          map: cmap, alphaTest: m.alphaTest == null ? 0.5 : m.alphaTest, transparent: false,
          side: THREE.FrontSide
        });
        if (m.emissive && (ims.e1 || ims.e3)) {
          mat.emissive = new THREE.Color(0xffffff);
          mat.emissiveMap = self._tex(THREE, use3 ? ims.e3 : ims.e1, { srgb: true });
          mat.emissiveIntensity = 0;
          self.emissiveMat.push({ mat: mat, light: o.emissiveLight });
        }
        const mesh = new THREE.Mesh(geo, mat);
        mesh.position.set(o.x, o.y || 0, o.z);
        mesh.rotation.y = (o.yawDeg || 0) * Math.PI / 180;
        mesh.castShadow = !!(Q.shadows && o.castShadow);
        mesh.receiveShadow = !!(Q.shadows && o.receiveShadow);
        mesh.userData.id = o.id;
        scene.add(mesh); self.meshObj[o.id] = mesh;
      } else if (o.type === 'backdrop') {
        const ims = self.meshIm[o.id];
        const tex = self._tex(THREE, use3 ? ims.c3 : ims.c1, { srgb: true, flipY: true });
        const mat = new THREE.MeshBasicMaterial({ map: tex, transparent: true, alphaTest: 0.05, depthWrite: false, fog: false });
        const plane = new THREE.Mesh(new THREE.PlaneGeometry(o.w, o.h), mat);
        // pivot [0.5, 1]＝底中；原點喺 (x, 0, z)，板向上
        const pv = o.pivot || [0.5, 1];
        plane.position.set(o.x + (0.5 - pv[0]) * o.w, o.h * (1 - pv[1]) + o.h / 2, o.z);
        plane.rotation.y = (o.yawDeg || 0) * Math.PI / 180;
        plane.frustumCulled = false;
        plane.renderOrder = -10;
        scene.add(plane); self.meshObj[o.id] = plane;
        self.backdropMat = self.backdropMat || [];
        self.backdropMat.push(mat);
      }
    });

    // pet billboard（圓柱面向）＋軟影
    const petGeo = new THREE.PlaneGeometry(64, 64);
    this.petCanvas = document.createElement('canvas'); this.petCanvas.width = 64; this.petCanvas.height = 64;
    this.petTex = this._tex(THREE, this.petCanvas, { srgb: true, flipY: true });
    this.petEmTex = this._tex(THREE, this.petCanvas, { srgb: true, flipY: true }); // replaced per frame
    this.petMat = new THREE.MeshLambertMaterial({ map: this.petTex, alphaTest: 0.5, transparent: false, side: THREE.DoubleSide });
    this.petMat.emissive = new THREE.Color(0xffffff);
    this.petMesh = new THREE.Mesh(petGeo, this.petMat);
    this.petMesh.castShadow = false; this.petMesh.receiveShadow = false;
    this.petMesh.userData.id = 'pet';
    // pivot (32,61)＝距圖頂 61px，即距圖底 3px。Three.js 預設 flipY true：圖底 → v=0 → Plane 底（局部 y=−32）。
    // 腳底喺局部 y = −32+3 = −29，所以 position.y = 29 令腳底喺世界 y=0。（H1 誤用 flipY false 會令頭腳倒轉。）
    this.petYOffset = 64 / 2 - (64 - 61); // 29
    this.petMesh.position.set(0, this.petYOffset, 0);
    scene.add(this.petMesh);

    // blob shadow
    const shC = document.createElement('canvas'); shC.width = 64; shC.height = 64;
    const sx = shC.getContext('2d'); const grd = sx.createRadialGradient(32, 32, 0, 32, 32, 30);
    grd.addColorStop(0, 'rgba(10,20,20,0.45)'); grd.addColorStop(1, 'rgba(10,20,20,0)');
    sx.fillStyle = grd; sx.fillRect(0, 0, 64, 64);
    const shTex = this._tex(THREE, shC, { srgb: false, flipY: true });
    const shMat = new THREE.MeshBasicMaterial({ map: shTex, transparent: true, depthWrite: false });
    this.shadowMesh = new THREE.Mesh(new THREE.PlaneGeometry(28, 18), shMat);
    this.shadowMesh.rotation.x = -Math.PI / 2; this.shadowMesh.position.set(0, 0.15, 0);
    scene.add(this.shadowMesh);

    // H1.3：世界 billboard 池（細佬／屎／訪客／影子／道具…）
    this._actorMap = {}; this._actors = []; this._actorGroup = new THREE.Group(); scene.add(this._actorGroup);

    // H1.4：雨點加大／加深（sizeAttenuation 關，用螢幕像素）等截圖睇到
    const nRain = RAIN.n, rpos = new Float32Array(nRain * 3);
    for (let i = 0; i < nRain; i++) { rpos[i * 3] = (Math.random() - 0.5) * 360; rpos[i * 3 + 1] = Math.random() * 220 + 10; rpos[i * 3 + 2] = (Math.random() - 0.5) * 280; }
    const rainGeo = new THREE.BufferGeometry(); rainGeo.setAttribute('position', new THREE.BufferAttribute(rpos, 3));
    const rainMat = new THREE.PointsMaterial({ color: RAIN.color, size: RAIN.size, sizeAttenuation: RAIN.sizeAttenuation, transparent: true, opacity: RAIN.opacity, depthWrite: false });
    this.rainMesh = new THREE.Points(rainGeo, rainMat); this.rainMesh.visible = false; this.rainMesh.frustumCulled = false;
    scene.add(this.rainMesh); this._rainPos = rpos; this._weather = 'clear';

    this._applyLights(0, 0);
    this._placeCamera(0);
  };

  Scene.prototype._applyLights = function (night, t) {
    if (!this.lightsJ || !this.ambL) return;
    const M = mixLights(this.lightsJ, night);
    this._night = night;
    const ac = M.ambColor;
    this.ambL.color.setRGB(ac[0] / 255, ac[1] / 255, ac[2] / 255);
    this.ambL.intensity = M.ambIntensity;
    this.sunL.color.set(M.sunColor);
    this.sunL.intensity = M.sun;
    const sd = M.sunDir;
    this.sunL.position.set(-sd[0], -sd[1], -sd[2]).multiplyScalar(900);
    this.sunL.target.position.set(0, 40, -20);
    this.sunL.shadow.intensity = shadowIntensityLin(M.shadowIntensity);
    this.fillL.color.set(M.fillColor);
    this.fillL.intensity = M.fill;
    const fd = M.fillDir;
    this.fillL.position.set(-fd[0], -fd[1], -fd[2]).multiplyScalar(700);
    if (this.hemiL) this.hemiL.intensity = lerp(0.22, 0.06, night);
    const self = this;
    this.pointL.forEach(function (p) {
      const src = M.points.filter(function (q) { return q.id === p.src.id; })[0];
      let I = src ? src.intensity : 0;
      if (src && src.flicker && t != null) I *= 1 + src.flicker * Math.sin(t * 8 + (p.src.x || 0));
      p.light.intensity = I * pointScale(p.src && p.src.id);
    });
    this.emissiveMat.forEach(function (e) {
      // glb emissiveFactor＝1，呢度乘返 emissiveLight 強度。小屋側窗改跟 window_side（同 window 一張 emissive 圖就用較大嗰個）。
      let ids = (e.lights || (e.light ? [e.light] : [])).slice();
      if (e.light === 'window' && ids.indexOf('window_side') < 0) ids.push('window_side');
      let I = 0, sid = e.light;
      ids.forEach(function (id) { if (M.byId[id] != null && M.byId[id] >= I) { I = M.byId[id]; sid = id; } });
      e.mat.emissiveIntensity = I * emissiveScale(sid);
    });
    function mixHex(dayHex, nightSrgb, t, into) {
      const THREE = window.THREE;
      if (!self._colA) { self._colA = new THREE.Color(); self._colB = new THREE.Color(); }
      const c = (into || self._colA).set(dayHex);
      self._colB.setRGB(srgbToLinear(nightSrgb[0]), srgbToLinear(nightSrgb[1]), srgbToLinear(nightSrgb[2]));
      return c.lerp(self._colB, clamp(t, 0, 1));
    }
    if (this.scene && this.scene.fog && M.fog) {
      this.scene.fog.color.copy(mixHex(M.fog.color || '#ffe8c8', FOG_NIGHT, night, self._colA));
    }
    if (this.renderer) {
      if (!self._colClear) self._colClear = new (window.THREE).Color();
      this.renderer.setClearColor(mixHex(0xffe8c8, NIGHT_SRGB, night, self._colClear), 1);
    }
    // 背景板未有夜景圖：sRGB 正確乘法（preview 用 [.22,.26,.42]），linear 寫入 color
    if (this.backdropMat) {
      const f = nightBackdropFactor(night);
      this.backdropMat.forEach(function (m) { m.color.setRGB(f[0], f[1], f[2]); });
    }
    this._lit = M;
  };

  Scene.prototype._placeCamera = function (dt) {
    const cam = this.camJ; if (!cam || !this.camera) return;
    const des = followDesired(cam, this.pet);
    if (!this.look) this.look = des.slice();
    if (this.followOn) this.look = followStep(this.look, des, dt || 0, cam.followDamping);
    else this.look = (cam.target || [0, 30, -72]).slice();
    const auto = this.swayOn ? swayYaw(this.t, cam) : 0;
    this.yaw = clampYaw(auto, cam, this.userYaw);
    const P = camPos(this.look, this.yaw, cam);
    this.camera.position.set(P[0], P[1], P[2]);
    this.camera.lookAt(this.look[0], this.look[1], this.look[2]);
    this._applyView();
    this.camera.updateMatrixWorld();
  };
  Scene.prototype._applyView = function () {
    if (!this.camera) return;
    const cam = this.camJ || {};
    const vis = visibleRect(cam);
    const vf = visFov(vis, cam);
    const vo = viewOffset(vis, W, H);
    const near = cam.near || 10, far = cam.far || 4000;
    const prev = this._vo;
    if (prev && prev.fov === vf.vfovDeg && prev.near === near && prev.far === far
      && prev.fw === vo.fullWidth && prev.fh === vo.fullHeight && prev.x === vo.x && prev.y === vo.y
      && prev.w === vo.width && prev.h === vo.height && prev.aspect === W / H) return;
    this.camera.fov = vf.vfovDeg;
    this.camera.near = near;
    this.camera.far = far;
    this.camera.aspect = W / H;
    this.camera.setViewOffset(vo.fullWidth, vo.fullHeight, vo.x, vo.y, vo.width, vo.height);
    this._vo = { fov: vf.vfovDeg, near: near, far: far, fw: vo.fullWidth, fh: vo.fullHeight, x: vo.x, y: vo.y, w: vo.width, h: vo.height, aspect: W / H };
  };
  Scene.prototype._syncGrid = function () {
    const on = !!this.gridOn;
    if (this.gridMesh) this.gridMesh.visible = on;
    if (this.outerGridMesh) this.outerGridMesh.visible = on;
  };
  Scene.prototype.setGrid = function (on) {
    this.gridOn = !!on;
    lsSet(KEY_GRID, this.gridOn ? '1' : '0');
    this._syncGrid();
    return this.gridOn;
  };

  Scene.prototype._dir4Frame = function (name, flip) {
    const J = this.dir4 && this.dir4.json, fr = J && J.frames[name]; if (!fr) return null;
    const f = fr.frame, c = this.petCanvas, x = c.getContext('2d');
    x.imageSmoothingEnabled = false; x.clearRect(0, 0, 64, 64);
    if (flip) { x.save(); x.translate(64, 0); x.scale(-1, 1); }
    x.drawImage(this.dir4.img, f.x, f.y, f.w, f.h, 0, 0, 64, 64);
    if (flip) x.restore();
    this.petTex.needsUpdate = true;
    // emissive
    if (!this.petEmCanvas) { this.petEmCanvas = document.createElement('canvas'); this.petEmCanvas.width = 64; this.petEmCanvas.height = 64; }
    const e = this.petEmCanvas.getContext('2d'); e.imageSmoothingEnabled = false; e.clearRect(0, 0, 64, 64);
    if (flip) { e.save(); e.translate(64, 0); e.scale(-1, 1); }
    e.drawImage(this.dir4.e, f.x, f.y, f.w, f.h, 0, 0, 64, 64);
    if (flip) e.restore();
    if (!this.petEmTex2) {
      const THREE = window.THREE;
      this.petEmTex2 = this._tex(THREE, this.petEmCanvas, { srgb: true, flipY: true });
      this.petMat.emissiveMap = this.petEmTex2;
    } else this.petEmTex2.needsUpdate = true;
    // normal map：左方向鏡像之後要反 R channel（R → 255−R）
    if (this.dir4.n) {
      if (!this.petNCanvas) { this.petNCanvas = document.createElement('canvas'); this.petNCanvas.width = 64; this.petNCanvas.height = 64; }
      const nctx = this.petNCanvas.getContext('2d', { willReadFrequently: true });
      nctx.imageSmoothingEnabled = false; nctx.clearRect(0, 0, 64, 64);
      if (flip) { nctx.save(); nctx.translate(64, 0); nctx.scale(-1, 1); }
      nctx.drawImage(this.dir4.n, f.x, f.y, f.w, f.h, 0, 0, 64, 64);
      if (flip) nctx.restore();
      if (flip) {
        const id = nctx.getImageData(0, 0, 64, 64), d = id.data;
        for (let i = 0; i < d.length; i += 4) d[i] = 255 - d[i];
        nctx.putImageData(id, 0, 0);
      }
      if (!this.petNTex) {
        const THREE = window.THREE;
        this.petNTex = this._tex(THREE, this.petNCanvas, { srgb: false, flipY: true });
        this.petMat.normalMap = this.petNTex;
      } else this.petNTex.needsUpdate = true;
    }
    return fr;
  };

  Scene.prototype.setPetSprite = function (src, o) {
    o = o || {}; this._fbSprite = src ? { src: src, mir: o.mir || 1, px: src.px, py: src.py } : null;
  };

  Scene.prototype._fallbackFrame = function () {
    const fb = this._fbSprite, src = fb && fb.src; if (!src || !src.img) return false;
    const c = this.petCanvas, x = c.getContext('2d');
    x.imageSmoothingEnabled = false; x.clearRect(0, 0, 64, 64);
    const mir = fb.mir < 0;
    const dx = 32 - src.px, dy = 61 - src.py;
    if (mir) { x.save(); x.translate(64, 0); x.scale(-1, 1); }
    x.drawImage(src.img, src.sx, src.sy, src.sw, src.sh, mir ? (64 - (dx + src.sw)) : dx, dy, src.sw, src.sh);
    if (mir) x.restore();
    this.petTex.needsUpdate = true;
    return true;
  };

  Scene.prototype._updatePet = function () {
    if (!this.petMesh) return;
    const p = this.pet;
    this.petMesh.position.set(p.x, this.petYOffset, p.z);
    this.shadowMesh.position.set(p.x, 0.15, p.z);
    // cylindrical face camera
    const cx = this.camera.position.x - p.x, cz = this.camera.position.z - p.z;
    this.petMesh.rotation.set(0, Math.atan2(cx, cz), 0);
    const useDir4 = this.dir4 && (!p.form || p.form === 'radiant' || p.form === 'bright' || p.fk === 'radiant' || p.fk === 'evo_still_radiant' || p.useDir4);
    // 試點得 radiant 一隻 dir4；其他形態用 2D sprite 後備
    const isRadiant = !p.form || p.form === 'radiant' || p.fk === 'radiant' || p.useDir4 === true;
    if (isRadiant && this.dir4) {
      const info = p.facing || dirOf(p.dx || 0, p.dz || 0, !!p.moving);
      const name = frameName(info, this.t);
      this._dir4Frame(name, !!info.flip);
      this._lastFrame = name;
      this.petMat.emissiveIntensity = (p.glow == null ? 1 : p.glow);
    } else {
      this._fallbackFrame();
      this.petMat.emissiveIntensity = (p.glow == null ? 1 : p.glow) * 0.2;
      this._lastFrame = 'fallback';
    }
    this.petMesh.visible = !p.hidden;
    this.shadowMesh.visible = !p.hidden;
  };

  Scene.prototype.update = function (dt, ctx) {
    dt = Math.max(0, Math.min(dt || 0, 0.1)); this.t += dt;
    ctx = ctx || {};
    if (ctx.pet) {
      this.pet.x = ctx.pet.x != null ? ctx.pet.x : this.pet.x;
      this.pet.z = ctx.pet.z != null ? ctx.pet.z : this.pet.z;
      this.pet.dx = ctx.pet.dx != null ? ctx.pet.dx : this.pet.dx;
      this.pet.dz = ctx.pet.dz != null ? ctx.pet.dz : this.pet.dz;
      this.pet.moving = !!ctx.pet.moving;
      this.pet.glow = ctx.pet.glow != null ? ctx.pet.glow : this.pet.glow;
      this.pet.form = ctx.pet.form || this.pet.form;
      this.pet.fk = ctx.pet.fk;
      this.pet.hidden = !!ctx.pet.hidden;
      const fac = (this.pet.dx || this.pet.dz) ? dirOf(this.pet.dx, this.pet.dz, this.pet.moving) : (this.pet.facing || dirOf(0, 1, false));
      if (ctx.pet.facing) this.pet.facing = ctx.pet.facing;
      else if (this.pet.moving) this.pet.facing = fac;
      else if (this.pet.facing) this.pet.facing.clip = 'idle';
    }
    if (this._forcePet) {
      if (this._forcePet.x != null) this.pet.x = this._forcePet.x;
      if (this._forcePet.z != null) this.pet.z = this._forcePet.z;
      if (this._forcePet.hidden != null) this.pet.hidden = !!this._forcePet.hidden;
      if (this._forcePet.dx != null) this.pet.dx = this._forcePet.dx;
      if (this._forcePet.dz != null) this.pet.dz = this._forcePet.dz;
      if (this._forcePet.moving != null) this.pet.moving = !!this._forcePet.moving;
      if (this._forcePet.facing) this.pet.facing = this._forcePet.facing;
    }
    const hour = ctx.hour != null ? ctx.hour : 8;
    const forced = ctx.night; // 0/1 override
    const night = forced == null ? nightMix(hour) : +forced;
    this._applyLights(night, this.t);
    this._placeCamera(dt);
    this._updatePet();
    this._updateRain(dt, this._forceWeather || ctx.weather);
    this._faceActors();
    return this;
  };

  Scene.prototype.resize = function (k) {
    k = k || 2; if (!this.renderer) return this;
    const vs = viewScale(k, this.qs().dpr);
    if (!this._fb || this._fb.w !== vs.w || this._fb.h !== vs.h) {
      this.renderer.setSize(vs.w, vs.h, false);
      this._setSizeN = (this._setSizeN || 0) + 1;
      this._fb = { w: vs.w, h: vs.h };
      this._applyView();
    }
    this.k = k; this.gk = vs.gk;
    return this;
  };

  Scene.prototype.draw = function (ctx, k, _opt) {
    if (!this.on() || !this.renderer) return false;
    const t0 = (typeof performance !== 'undefined' && performance.now) ? performance.now() : 0;
    k = k || this.k || 2;
    this.resize(k);
    const ev = (this.qs() && this.qs().shadowEvery) || 1;
    if (this.renderer.shadowMap && this.renderer.shadowMap.enabled && ev > 1) {
      this.renderer.shadowMap.autoUpdate = false;
      this._shN = (this._shN || 0) + 1;
      this.renderer.shadowMap.needsUpdate = (this._shN % ev === 1);
    } else if (this.renderer.shadowMap) {
      this.renderer.shadowMap.autoUpdate = true;
    }
    this.renderer.render(this.scene, this.camera);
    const vs = viewScale(k, this.qs().dpr);
    ctx.imageSmoothingEnabled = !vs.integer;  /* 整數倍（1×／2×）關平滑，唔好每幀雙線性放大 293×633 */
    ctx.drawImage(this.canvas, 0, 0, vs.dw, vs.dh);
    const ms = ((typeof performance !== 'undefined' && performance.now) ? performance.now() : 0) - t0;
    this.stat.draws++; this.stat.lastMs = ms; this.stat.ms += ms;
    this.perf.n++; this.perf.sum += ms; this.perf.max = Math.max(this.perf.max, ms); this.perf.last = ms;
    this.perf.acc += ms; this.perf.fn++;
    if (this.perf.fn >= 30) { this.perf.drawMs = this.perf.acc / this.perf.fn; this.perf.acc = 0; this.perf.fn = 0; }
    return true;
  };

  Scene.prototype.project = function (x, y, z) {
    if (!this.camera) return worldToArtFlat(x, z);
    const THREE = window.THREE;
    const v = new THREE.Vector3(x, y, z).project(this.camera);
    return { x: (v.x * 0.5 + 0.5) * W, y: (-v.y * 0.5 + 0.5) * H, ndc: [v.x, v.y, v.z] };
  };
  Scene.prototype.petDraw = function () {
    const p = this.pet, foot = this.project(p.x, 0, p.z), head = this.project(p.x, 64, p.z);
    const y0 = Math.min(foot.y, head.y), y1 = Math.max(foot.y, head.y);
    const w = 40, h = Math.max(24, y1 - y0);
    return { x: foot.x - w / 2, y: y0, w: w, h: h, bud: { x: foot.x, y: y0 + 8 }, footY: foot.y, g3d: true };
  };
  Scene.prototype.petHit = function (ax, ay) {
    const box = this.petDraw();
    return ax >= box.x && ax <= box.x + box.w && ay >= box.y && ay <= box.y + box.h;
  };
  Scene.prototype.occluded = function (x, z, y) {
    if (!this.camera || !window.THREE) return false;
    const ys = y != null ? [y] : [8, 16, 24];  /* 花盆 pot_S 高 19：單用 y=20 永遠穿過盆頂 */
    for (let i = 0; i < ys.length; i++) if (this._occludedAt(x, ys[i], z)) return true;
    return false;
  };
  Scene.prototype._occludedAt = function (x, y, z) {
    const THREE = window.THREE;
    const origin = this.camera.position.clone();
    const target = new THREE.Vector3(x, y, z);
    const dir = target.clone().sub(origin);
    const dist = dir.length();
    if (dist < 1e-6) return false;
    dir.multiplyScalar(1 / dist);
    const ray = new THREE.Raycaster(origin, dir);
    const meshes = [];
    this.scene.traverse(function (o) { if (o.isMesh && o.userData && o.userData.id && o.userData.id !== 'pet' && o.userData.kind !== 'actor') meshes.push(o); });
    const hits = ray.intersectObjects(meshes, false);
    if (!hits.length) return false;
    return hits[0].distance + 1 < dist;
  };
  Scene.prototype.artToGround = function (ax, ay) {
    if (!this.camera || typeof window === 'undefined' || !window.THREE) return artToWorld(ax, ay);
    const THREE = window.THREE;
    const origin = this.camera.position.clone();
    const ndcX = (ax / W) * 2 - 1, ndcY = -(ay / H) * 2 + 1;
    const aim = new THREE.Vector3(ndcX, ndcY, 0.5).unproject(this.camera);
    const dir = aim.sub(origin);
    if (Math.abs(dir.y) < 1e-6) return artToWorld(ax, ay);
    const t = -origin.y / dir.y;
    if (t < 0) return artToWorld(ax, ay);
    return {
      x: clamp(origin.x + dir.x * t, RANGE3.x[0], RANGE3.x[1]),
      z: clamp(origin.z + dir.z * t, RANGE3.z[0], RANGE3.z[1])
    };
  };
  Scene.prototype._updateRain = function (dt, weather) {
    weather = weather || 'clear';
    this._weather = weather;
    if (!this.rainMesh || !this._rainPos) return;
    const on = weather === 'rain';
    this.rainMesh.visible = on;
    if (!on) return;
    const pos = this._rainPos, n = pos.length / 3, fall = 180 * Math.max(0, dt);
    for (let i = 0; i < n; i++) {
      pos[i * 3 + 1] -= fall * (0.7 + (i % 5) * 0.12);
      if (pos[i * 3 + 1] < 0) { pos[i * 3] = (Math.random() - 0.5) * 360; pos[i * 3 + 1] = 160 + Math.random() * 80; pos[i * 3 + 2] = (Math.random() - 0.5) * 280; }
    }
    this.rainMesh.geometry.attributes.position.needsUpdate = true;
  };
  function actorMatOpts(a) {
    const soft = !!(a && a.alpha != null && a.alpha < 1);
    const at = (a && a.alphaTest != null) ? a.alphaTest : (soft ? ACTOR_ALPHA_SOFT : 0.5);
    return { alphaTest: at, transparent: soft, depthWrite: !soft };
  }
  function applyActorMat(rec, a) {
    if (!rec || !rec.mat) return;
    const opt = actorMatOpts(a);
    if (rec.mat.alphaTest !== opt.alphaTest || rec.mat.transparent !== opt.transparent || rec.mat.depthWrite !== opt.depthWrite) {
      rec.mat.alphaTest = opt.alphaTest;
      rec.mat.transparent = opt.transparent;
      rec.mat.depthWrite = opt.depthWrite;
      rec.mat.needsUpdate = true;
    }
  }
  Scene.prototype._actorSize = function (src) {
    const sw = (src && (src.sw || (src.img && src.img.width))) || 16;
    const sh = (src && (src.sh || (src.img && src.img.height))) || 16;
    return (sw > 64 || sh > 64) ? 128 : 64;
  };
  Scene.prototype._paintActor = function (rec, a) {
    const src = a.src, C = rec.canvas.width, x = rec.canvas.getContext('2d');
    x.imageSmoothingEnabled = false; x.clearRect(0, 0, C, C);
    if (!src || !src.img) return;
    const sw = src.sw != null ? src.sw : src.img.width, sh = src.sh != null ? src.sh : src.img.height;
    const sx = src.sx || 0, sy = src.sy || 0;
    const px = src.px != null ? src.px : sw / 2, py = src.py != null ? src.py : sh;
    const ox = C / 2 - px, oy = (C - 3) - py, flip = !!a.flip;
    if (flip) { x.save(); x.translate(C, 0); x.scale(-1, 1); x.drawImage(src.img, sx, sy, sw, sh, C - (ox + sw), oy, sw, sh); x.restore(); }
    else x.drawImage(src.img, sx, sy, sw, sh, ox, oy, sw, sh);
    if (a.alpha != null && a.alpha < 1) {
      x.globalCompositeOperation = 'destination-in';
      x.fillStyle = 'rgba(0,0,0,' + clamp(a.alpha, 0, 1) + ')';
      x.fillRect(0, 0, C, C);
      x.globalCompositeOperation = 'source-over';
    }
    rec.tex.needsUpdate = true;
  };
  Scene.prototype._makeActor = function (a) {
    const THREE = window.THREE, C = this._actorSize(a.src);
    const canvas = document.createElement('canvas'); canvas.width = C; canvas.height = C;
    const tex = this._tex(THREE, canvas, { srgb: true, flipY: true });
    const opt = actorMatOpts(a);
    const mat = new THREE.MeshLambertMaterial({ map: tex, alphaTest: opt.alphaTest, transparent: opt.transparent, depthWrite: opt.depthWrite, side: THREE.DoubleSide });
    const mesh = new THREE.Mesh(new THREE.PlaneGeometry(C, C), mat);
    const yOff = C / 2 - 3;
    mesh.userData.id = 'actor:' + a.id; mesh.userData.kind = 'actor'; mesh.userData.actorId = a.id;
    mesh.castShadow = false; mesh.receiveShadow = false;
    const rec = { id: a.id, canvas: canvas, tex: tex, mat: mat, mesh: mesh, yOff: yOff, size: C, key: '', shadow: null };
    if (a.shadow !== false) {
      const sh = this.shadowMesh ? this.shadowMesh.clone() : null;
      if (sh) { sh.material = this.shadowMesh.material; rec.shadow = sh; this._actorGroup.add(sh); }
    }
    this._actorGroup.add(mesh);
    this._actorMap[a.id] = rec;
    return rec;
  };
  Scene.prototype._disposeActor = function (rec) {
    if (!rec) return;
    if (rec.mesh && rec.mesh.parent) rec.mesh.parent.remove(rec.mesh);
    if (rec.shadow && rec.shadow.parent) rec.shadow.parent.remove(rec.shadow);
    try { if (rec.tex && rec.tex.dispose) rec.tex.dispose(); if (rec.mat && rec.mat.dispose) rec.mat.dispose(); } catch (e) { }
  };
  Scene.prototype.syncActors = function (list) {
    list = list || [];
    this._actors = list;
    if (!this.scene || typeof window === 'undefined' || !window.THREE || !this._actorGroup) return list;
    const self = this, seen = {};
    list.forEach(function (a) {
      if (!a || !a.id) return;
      seen[a.id] = true;
      let rec = self._actorMap[a.id];
      const sz = self._actorSize(a.src);
      if (rec && rec.size !== sz) { self._disposeActor(rec); delete self._actorMap[a.id]; rec = null; }
      if (!rec) rec = self._makeActor(a);
      rec.idle = 0;
      applyActorMat(rec, a);
      const key = [a.kind, a.src && (a.src.name || a.src.sx), a.src && a.src.sy, a.src && a.src.sw, !!a.flip, a.alpha, a.src && a.src.frame].join('|');
      if (key !== rec.key) { self._paintActor(rec, a); rec.key = key; }
      const yLift = a.yLift || 0;
      rec.mesh.position.set(a.x, rec.yOff + yLift, a.z);
      rec.mesh.visible = a.hidden ? false : true;
      rec.mesh.renderOrder = a.order || 2;
      if (a.lit === false) rec.mat.emissive = rec.mat.emissive || rec.mat.color;
      if (rec.shadow) { rec.shadow.position.set(a.x, 0.16, a.z); rec.shadow.visible = !a.hidden && a.shadow !== false; const sc = a.shadowScale || 1; rec.shadow.scale.set(sc, sc, sc); }
      rec.a = a;
    });
    Object.keys(this._actorMap).forEach(function (id) {
      if (seen[id]) return;
      const rec = self._actorMap[id];
      rec.mesh.visible = false; if (rec.shadow) rec.shadow.visible = false;
      rec.idle = (rec.idle || 0) + 1;
      if (rec.idle > 120) { self._disposeActor(rec); delete self._actorMap[id]; }
    });
    this._faceActors();
    return list;
  };
  Scene.prototype._faceActors = function () {
    if (!this.camera || !this._actorMap) return;
    const cx = this.camera.position.x, cz = this.camera.position.z;
    const map = this._actorMap;
    Object.keys(map).forEach(function (id) {
      const rec = map[id]; if (!rec.mesh || !rec.mesh.visible) return;
      const p = rec.mesh.position;
      rec.mesh.rotation.set(0, Math.atan2(cx - p.x, cz - p.z), 0);
    });
  };
  Scene.prototype.actors = function () { return (this._actors || []).slice(); };
  Scene.prototype.actorBox = function (a) {
    if (!a) return null;
    const h = a.h != null ? a.h : (a.src && a.src.sh) || 24;
    const w = a.w != null ? a.w : Math.max(14, ((a.src && a.src.sw) || 16) * 0.65);
    const foot = this.project(a.x, a.yLift || 0, a.z);
    const head = this.project(a.x, (a.yLift || 0) + h, a.z);
    const y0 = Math.min(foot.y, head.y), y1 = Math.max(foot.y, head.y);
    return { x: foot.x - w / 2, y: y0, w: w, h: Math.max(10, y1 - y0 + 4), foot: foot, id: a.id, kind: a.kind };
  };
  Scene.prototype.hitActor = function (ax, ay) {
    const list = this._actors || [];
    let best = null, bestZ = 2, poop = null, poopZ = 2;
    for (let i = 0; i < list.length; i++) {
      const a = list[i]; if (!a || a.hit === false || a.hidden) continue;
      const box = this.actorBox(a); if (!box) continue;
      if (ax >= box.x && ax <= box.x + box.w && ay >= box.y && ay <= box.y + box.h) {
        const z = box.foot.ndc ? box.foot.ndc[2] : 1;
        if (a.kind === 'poop' && z < poopZ) { poopZ = z; poop = a; }
        if (z < bestZ) { bestZ = z; best = a; }
      }
    }
    return poop || best;  /* 撳中點喺屎盒入面就優先回屎（細佬／訪客高盒唔好搶） */
  };

  Scene.prototype.setQuality = function (q, o) {
    if (q !== 'high' && q !== 'mid' && q !== 'low') return this.quality;
    const prev = this.quality; this.quality = q; lsSet(KEY_Q, q);
    if (o && o.manual) lsSet(KEY_Q_MANUAL, q === 'low' ? '0' : '1');
    if (this.loaded && prev !== q && q !== 'low') {
      try { this._build(window.THREE); } catch (e) { this.error = String(e && e.message || e); }
    }
    return this.quality;
  };
  Scene.prototype.setSway = function (on) { this.swayOn = !!on; lsSet(KEY_SWAY, on ? '1' : '0'); return this.swayOn; };
  Scene.prototype.setFollow = function (on) { this.followOn = !!on; lsSet(KEY_FOLLOW, on ? '1' : '0'); return this.followOn; };
  Scene.prototype.orbit = function (deg) {
    const cam = this.camJ || { orbitMinDeg: -10, orbitMaxDeg: 10 };
    this.userYaw = clamp(deg, cam.orbitMinDeg, cam.orbitMaxDeg);
    this._placeCamera(0); return this.userYaw;
  };
  Scene.prototype.autoDrop = function (avgMs, slowMs) {
    if (this.quality === 'low') return this.quality;
    if (avgMs > (slowMs || 28)) {
      const nq = this.quality === 'high' ? 'mid' : 'low';
      this.setQuality(nq); return nq;
    }
    return this.quality;
  };

  /* ── 開發者模式：畫質／擺鏡／跟拍／fps 面板 ── */
  function mountPerf(G, S) {
    if (typeof document === 'undefined') return;
    let el = document.getElementById('g3dPerf');
    if (!el) {
      el = document.createElement('div'); el.id = 'g3dPerf'; el.dataset.testid = 'g3d-perf';
      el.style.cssText = 'display:none;position:absolute;right:8px;top:112px;z-index:7;padding:4px 8px;border-radius:8px;font:700 11px/16px sans-serif;color:#fff3d6;background:rgba(14,16,34,.82);border:1px solid rgba(255,214,110,.55);pointer-events:none;white-space:pre';
      const ui = document.getElementById('ui'); if (ui) ui.appendChild(el); else document.body.appendChild(el);
    }
    S.perfEl = el;
    S.showPerf = S.showPerf || lsGet('glimmer.g3d.perf', '0') === '1';
    el.style.display = S.showPerf ? 'block' : 'none';
  }
  function tickPerf(S) {
    if (!S.perfEl || !S.showPerf) return;
    const fps = S.stat.fps ? S.stat.fps.toFixed(0) : '—';
    const ms = (S.stat.lastFrameMs != null) ? S.stat.lastFrameMs.toFixed(1) : (S.perf.last ? S.perf.last.toFixed(1) : '—');
    const on = S.on() ? ('3D ' + S.quality) : '2D 後備';
    S.perfEl.textContent = on + '  ' + fps + ' fps  ' + ms + ' ms/幀\n耗電：' + (S.quality === 'high' ? '高（影圖＋@3x）' : S.quality === 'mid' ? '中（1x＋較細影）' : '低（2D）');
  }

  function install(G, NS) {
    const D = NS.data, P = D.PARAMS, qs = new URLSearchParams(location.search);
    const savedQ = lsGet(KEY_Q, '');
    const det = detectQuality({
      qs: { '3d': qs.get('3d') },
      webgl: hasWebGL(),
      hardwareConcurrency: navigator.hardwareConcurrency,
      deviceMemory: navigator.deviceMemory,
      lowEndCores: (P.quality && P.quality.lowEndCores) || 4,
      lowEndMemGB: (P.quality && P.quality.lowEndMemGB) || 4
    });
    let quality = det.quality;
    const manual = lsGet(KEY_Q_MANUAL, '') === '1';
    /* 手動（開發者模式）先可以沿用 mid／high；自動／舊自動偵測存檔一律 cap 喺 low */
    if (savedQ && !qs.get('3d') && savedQ === 'low') quality = 'low';
    else if (savedQ && !qs.get('3d') && (savedQ === 'high' || savedQ === 'mid') && manual) quality = savedQ;
    else if (!qs.get('3d')) quality = 'low';
    const S = new Scene({
      base: (P.art && P.art.base || 'art/') + 'garden3d/H1/',
      dir4base: (P.art && P.art.base || 'art/') + 'garden3d/dir4/',
      enabled: det.want || quality !== 'low',
      quality: quality,
      swayOn: lsGet(KEY_SWAY, '1') !== '0',
      followOn: lsGet(KEY_FOLLOW, '1') !== '0',
      gridOn: lsGet(KEY_GRID, '0') === '1'
    });
    if (qs.get('3d') === '0') { S.enabled = false; S.quality = 'low'; }
    G.g3d = S; if (G.renderer) G.renderer.g3d = S;
    const loadP = (S.enabled && S.quality !== 'low') ? S.load() : Promise.resolve(false);
    G.g3dLoad = loadP;
    loadP.then(function (ok) {
      if (!ok && S.quality !== 'low' && qs.get('3d') !== '0') { S.quality = 'low'; }
      if (G.renderer) G.renderer.g3d = S;
    });
    mountPerf(G, S);

    // 自動降畫質（自己嘅窗口，唔改現有 2D quality auto）
    const qm = { sum: 0, n: 0, slow: 0, grace: 90 };
    S.noteFrame = function (frameMs) {
      // 用整幀 wall-clock（render.js frame()）計 fps，唔好用 WebGL 單獨耗時
      S.stat.lastFrameMs = frameMs;
      S.perf.fAcc = (S.perf.fAcc || 0) + frameMs; S.perf.fN = (S.perf.fN || 0) + 1;
      if (S.perf.fN >= 30) { S.stat.fps = S.perf.fAcc > 0 ? 1000 / (S.perf.fAcc / S.perf.fN) : 0; S.perf.fAcc = 0; S.perf.fN = 0; }
      tickPerf(S);
      if (S.quality === 'low' || !S.on()) return;
      if (qm.grace > 0) { qm.grace--; return; }
      qm.sum += frameMs; qm.n++;
      if (qm.n >= 120) {
        const avg = qm.sum / qm.n; qm.sum = 0; qm.n = 0;
        if (avg > 28) qm.slow++; else qm.slow = 0;
        if (qm.slow >= 2) {
          const nq = S.autoDrop(99, 1);
          qm.slow = 0; qm.grace = 90;
          if (NS.ui && NS.ui.toast) NS.ui.toast(nq === 'low' ? '效能較低，已轉返 2D 花園' : '效能較低，已降低 3D 畫質');
        }
      }
    };

    // 拖鏡（空地水平拖）
    if (typeof document !== 'undefined') {
      const cv = G.renderer && G.renderer.canvas;
      if (cv) {
        cv.addEventListener('pointerdown', function (e) {
          if (!S.on() || (G.ui && G.ui.isModalOpen && G.ui.isModalOpen())) return;
          const art = G.renderer.screenToArt(e.clientX, e.clientY);
          if (S.petHit(art.x, art.y)) return;
          if (art.y < 38 || art.y > 360) return;
          S._drag = { x0: e.clientX, y0: e.clientY, yaw0: S.userYaw, moved: false, id: e.pointerId };
        });
        cv.addEventListener('pointermove', function (e) {
          const d = S._drag; if (!d || d.id !== e.pointerId) return;
          const dx = e.clientX - d.x0;
          if (!d.moved && Math.abs(dx) < 16) return;
          d.moved = true;
          try { cv.setPointerCapture(e.pointerId); } catch (err) { }
          S.orbit(d.yaw0 - dx * 0.05);
        });
        const up = function (e) { if (S._drag && S._drag.id === e.pointerId) S._drag = null; };
        cv.addEventListener('pointerup', up); cv.addEventListener('pointercancel', up);
      }
    }

    window.__qa = window.__qa || {};
    window.__qa.g3d = {
      on: function () { return S.on(); },
      ready: function () { return !!S.ready; },
      quality: function () { return S.quality; },
      setQuality: function (q) { return S.setQuality(q); },
      meshes: function () { return S.stat.meshes; },
      error: function () { return S.error; },
      night: function () { return S._night; },
      yaw: function () { return S.yaw; },
      look: function () { return S.look && S.look.slice(); },
      pet: function () { return { x: S.pet.x, z: S.pet.z, frame: S._lastFrame, facing: S.pet.facing }; },
      forcePet: function (p) { S._forcePet = p || null; return S._forcePet; },
      project: function (x, y, z) { return S.project(x, y, z); },
      petDraw: function () { return S.petDraw(); },
      petHit: function (x, y) { return S.petHit(x, y); },
      occluded: function (x, z, y) { return S.occluded(x == null ? S.pet.x : x, z == null ? S.pet.z : z, y); },
      artToGround: function (ax, ay) { return S.artToGround(ax, ay); },
      lost: function () { return !!S.lost; },
      hooksOnBeh: function () { return !!(S && window.Glimmer && Glimmer.data && Glimmer.data.PARAMS && Glimmer.data.PARAMS.beh && typeof Glimmer.data.PARAMS.beh.g3dWalk === 'function'); },
      actors: function () { return S.actors(); },
      syncActors: function (list) { return S.syncActors(list); },
      hitActor: function (ax, ay) { return S.hitActor(ax, ay); },
      actorBox: function (a) { return S.actorBox(a); },
      poopWorld: poopWorld,
      poopSlots: function () { return POOP_SLOTS.map(function (p) { return p.slice(); }); },
      worldItems: function () { return WORLD_ITEMS.slice(); },
      weather: function () { return S._weather; },
      setWeather: function (w) { S._forceWeather = w || null; if (S._updateRain) S._updateRain(0, w || 'clear'); return S._weather; },
      shadowEvery: function () { return (S.qs() && S.qs().shadowEvery) || 0; },
      shadowSize: function () { return (S.qs() && S.qs().shadow) || 0; },
      shadowSoft: function () { return !!(S.qs() && S.qs().softShadow); },
      setSizeN: function () { return S._setSizeN || 0; },
      gk: function () { return S.gk; },
      viewSize: function () { return S.canvas ? { w: S.canvas.width, h: S.canvas.height, k: S.k, gk: S.gk, dpr: S.qs() && S.qs().dpr } : null; },
      actorMat: function (id) {
        const rec = S._actorMap && S._actorMap[id]; if (!rec || !rec.mat) return null;
        let maxA = 0, n = 0;
        try { const g = rec.canvas && rec.canvas.getContext('2d'); if (g) { const d = g.getImageData(0, 0, rec.canvas.width, rec.canvas.height).data; for (let i = 3; i < d.length; i += 4) { if (d[i] > 0) { n++; if (d[i] > maxA) maxA = d[i]; } } } } catch (e) { }
        return { alphaTest: rec.mat.alphaTest, transparent: !!rec.mat.transparent, depthWrite: !!rec.mat.depthWrite, maxA: maxA / 255, typed: n };
      },
      rainInfo: function () { return { visible: !!(S.rainMesh && S.rainMesh.visible), n: S._rainPos ? S._rainPos.length / 3 : 0, size: (S.rainMesh && S.rainMesh.material && S.rainMesh.material.size) || 0, atten: !!(S.rainMesh && S.rainMesh.material && S.rainMesh.material.sizeAttenuation), color: S.rainMesh && S.rainMesh.material && S.rainMesh.material.color && S.rainMesh.material.color.getHex() }; },
      orbit: function (d) { return S.orbit(d); },
      setSway: function (v) { return S.setSway(v); },
      setFollow: function (v) { return S.setFollow(v); },
      setGrid: function (v) { return S.setGrid(v); },
      swayOn: function () { return S.swayOn; },
      followOn: function () { return S.followOn; },
      gridOn: function () { return !!S.gridOn; },
      vis: function () { return visibleRect(S.camJ); },
      visFov: function () { return visFov(null, S.camJ); },
      lookTarget: function () { return followDesired(S.camJ || {}, S.pet); },
      walkStep3d: walkStep3d,
      shadowIntensityLin: shadowIntensityLin,
      fps: function () { return S.stat.fps; },
      lastMs: function () { return S.stat.lastMs; },
      lastFrameMs: function () { return S.stat.lastFrameMs; },
      lit: function () { return S._lit && { sun: S._lit.sun, fill: S._lit.fill, night: S._lit.night, byId: S._lit.byId }; },
      blocked: function (x, z) { return blocked(S.objects, x, z, (S.objJ && S.objJ.pet && S.objJ.pet.radius) || 10); },
      petFlipY: function () { return !!(S.petTex && S.petTex.flipY); },
      range3: function () { return { x: RANGE3.x.slice(), z: RANGE3.z.slice() }; },
      stepXZ: function (x, z, tx, tz, step) { return stepXZ(S.objects, x, z, tx, tz, step, (S.objJ && S.objJ.pet && S.objJ.pet.radius) || 10, RANGE3.x, RANGE3.z); },
      showPerf: function (v) { S.showPerf = v !== false; lsSet('glimmer.g3d.perf', S.showPerf ? '1' : '0'); if (S.perfEl) S.perfEl.style.display = S.showPerf ? 'block' : 'none'; return S.showPerf; },
      reload: function () { return S.load(); }
    };

    const DEV = {
      id: 'g3d', title: '3D 花園 H1.6', order: 13,
      status: function () { return (S.on() ? ('3D ' + S.quality) : (qs.get('3d') === '0' ? '?3d=0 2D' : '2D 後備')) + '・擺鏡 ' + (S.swayOn ? '開' : '關') + '・跟拍 ' + (S.followOn ? '開' : '關') + '・網格 ' + (S.gridOn ? '開' : '關'); },
      items: [
        { k: 'high', label: '畫質：高（3D）', run: function () { S.setQuality('high', { manual: true }); if (!S.ready) S.load(); return { ok: true, msg: '3D 畫質 → 高' }; } },
        { k: 'mid', label: '畫質：中（3D）', run: function () { S.setQuality('mid', { manual: true }); if (!S.ready) S.load(); return { ok: true, msg: '3D 畫質 → 中' }; } },
        { k: 'low', label: '畫質：低（2D 後備）', run: function () { S.setQuality('low', { manual: true }); return { ok: true, msg: '已轉返 2D 花園' }; } },
        { k: 'sway', label: '鏡頭自動擺（預設開）', run: function () { const v = S.setSway(!S.swayOn); return { ok: true, msg: v ? '自動擺鏡開' : '自動擺鏡關' }; } },
        { k: 'follow', label: '鏡頭跟拍（預設開）', run: function () { const v = S.setFollow(!S.followOn); return { ok: true, msg: v ? '跟拍開' : '跟拍關' }; } },
        { k: 'grid', label: '地面網格（預設關）', run: function () { const v = S.setGrid(!S.gridOn); return { ok: true, msg: v ? '地面網格開' : '地面網格關' }; } },
        { k: 'perf', label: 'fps／耗電面板', run: function () { const v = !S.showPerf; window.__qa.g3d.showPerf(v); return { ok: true, msg: v ? '面板開' : '面板關' }; } },
        { k: 'off', label: '轉返 2D（?3d=0）', run: function () { const q = new URLSearchParams(location.search); q.set('3d', '0'); setTimeout(function () { location.search = q.toString(); }, 50); return { ok: true, msg: '重新載入 2D…' }; } }
      ]
    };
    if (NS) { if (NS.devmode) NS.devmode.register(DEV); else (NS.devSections = NS.devSections || []).push(DEV); }

    // H1.1／H1.2：3D 開時行為用 XZ 走位＋碰撞。hook 要掛喺 PARAMS.beh（behavior.js 讀 D.PARAMS.beh），唔好掛親 PARAMS。
    bindBehHooks(P.beh, S);
    return S;
  }

  function bindBehHooks(beh, S) {
    if (!beh) return null;
    const radOf = function () { return (S.objJ && S.objJ.pet && S.objJ.pet.radius) || 10; };
    beh.g3dOn = function () { return S.on(); };
    beh.g3dWalk = function (b, tx, st) {
      if (!S.on() || !S.objects || !S.objects.length) return null;
      if (b.z == null) b.z = 0;
      const rawZ = b.tz != null ? b.tz : b.z;
      const dest = snapDest(S.objects, tx, rawZ, radOf(), RANGE3.x, RANGE3.z);
      if (!b._g3dPath || b._g3dTx !== dest.x || b._g3dTz !== dest.z) {
        b._g3dPath = buildPath(S.objects, b.x, b.z, dest.x, dest.z, radOf(), RANGE3.x, RANGE3.z);
        b._g3dTx = dest.x; b._g3dTz = dest.z; b._g3dPi = 0; b._g3dStall = 0; b._g3dBest = null;
      }
      const fol = followPath(S.objects, b.x, b.z, b._g3dPath, { x: dest.x, z: dest.z }, walkStep3d(st), radOf(), RANGE3.x, RANGE3.z, b._g3dPi || 0, b._g3dStall || 0);
      b._g3dPi = fol.pi;
      const r = fol.step;
      const dist = Math.hypot(dest.x - r.x, dest.z - r.z);
      if (b._g3dBest == null || dist < b._g3dBest - 0.05) { b._g3dBest = dist; b._g3dStall = 0; }
      else b._g3dStall = (fol.stall != null ? fol.stall : (b._g3dStall || 0) + 1);
      if (r.stuck || b._g3dStall >= STALL_STEPS) { r.stuck = true; r.arrived = true; }
      return r;
    };
    beh.g3dPickWalk = function (b) {
      if (!S.on() || !S.objects || !S.objects.length) return null;
      return pickWalk(S.objects, b && b.rng, { x: b && b.x || 0, z: (b && b.z) || 0 }, radOf(), RANGE3);
    };
    beh.g3dSpot = function (kind) {
      if (!S.on()) return null;
      if (kind === 'sun') return { x: 20, z: 36 };
      if (kind === 'bump') return { x: 49, z: 5 };
      return null;
    };
    beh.g3dClampX = function (x) {
      if (!S.on()) {
        const rx = beh.rangeX || RANGE3.x;
        return clamp(x, rx[0], rx[1]);
      }
      return clamp(x, RANGE3.x[0], RANGE3.x[1]);
    };
    return beh;
  }

  return {
    W: W, H: H, CX: CX, GROUND_Y: GROUND_Y, ZSCALE: ZSCALE, QSET: QSET, ACTOR_ALPHA_SOFT: ACTOR_ALPHA_SOFT, RAIN: RAIN, actorMatOpts: actorMatOpts, viewScale: viewScale,
    VIS: VIS, VIS_HFOV_DEG: VIS_HFOV_DEG, WALK_SPEED_2D: WALK_SPEED_2D, WALK_SPEED_3D: WALK_SPEED_3D,
    POOP_SLOTS: POOP_SLOTS, poopWorld: poopWorld, WORLD_ITEMS: WORLD_ITEMS, worldItem: worldItem, worldInGarden: worldInGarden, worldWantArt: worldWantArt,
    G3D_IDLE_WALK_SEC: G3D_IDLE_WALK_SEC, G3D_WALK_MUL: G3D_WALK_MUL, G3D_STAY_MUL: G3D_STAY_MUL, G3D_DECIDE_EVERY: G3D_DECIDE_EVERY,
    shouldForceWalk: shouldForceWalk, wanderWeights: wanderWeights,
    NIGHT_SRGB: NIGHT_SRGB, FOG_NIGHT: FOG_NIGHT,
    artToWorld: artToWorld, worldToArtFlat: worldToArtFlat, petWorld: petWorld,
    nightMix: nightMix, mixLights: mixLights,
    swayYaw: swayYaw, followDesired: followDesired, followOriginOf: followOriginOf, followClamp: followClamp, followStep: followStep, camPos: camPos, clampYaw: clampYaw,
    visibleRect: visibleRect, visFov: visFov, viewOffset: viewOffset,
    srgbToLinear: srgbToLinear, nightBackdropFactor: nightBackdropFactor, shadowIntensityLin: shadowIntensityLin,
    walkStep3d: walkStep3d, emissiveScale: emissiveScale, pointScale: pointScale,
    dirOf: dirOf, frameName: frameName,
    fpDist: fpDist, blocked: blocked, stepXZ: stepXZ, buildPath: buildPath, followPath: followPath, pickWalk: pickWalk, RANGE3: RANGE3,
    snapDest: snapDest, NEAR_FREE_R: NEAR_FREE_R, ARRIVE_DIST: ARRIVE_DIST, STALL_STEPS: STALL_STEPS, bindBehHooks: bindBehHooks,
    detectQuality: detectQuality, hasWebGL: hasWebGL,
    Scene: Scene, install: install
  };
});
