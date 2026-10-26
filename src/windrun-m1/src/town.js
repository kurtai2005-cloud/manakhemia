/* town.js — 城鎮實驗渲染／互動（town-lab.html 用）。Canvas2D；地圖資料＝Tiled JSON 子集（src/town-map.js 生成）。
   功能：chunk 預渲染（可開關）、Y 排序遮擋（道具／NPC／玩家）＋遮擋圖塊層、光圖（baked／live）、tilt-shift 景深、
   A* 點擊尋路＋浮動虛擬搖桿＋鍵盤、格子碰撞、傳送點（淡入淡出）、NPC 巡邏。
   量度：__town.bench()（headless 量幀時；標明唔係真機）。 */
(function (g) {
  'use strict';
  const TM = g.WR.TownMap, TILE = 16, CHUNK = 16;
  const QUAL = {
    off: { light: 'none', dof: 0, glow: 0, vig: 0, lres: 4 },
    low: { light: 'baked', dof: 0, glow: 0, vig: 0, lres: 2 },
    mid: { light: 'live', dof: 0, glow: 0, vig: 1, lres: 4 },
    high: { light: 'live', dof: 1, glow: 1, vig: 1, lres: 2 }
  };
  const AMB = { day: [255, 248, 232], dusk: [205, 150, 165], night: [44, 56, 108] };
  const LSTR = { day: 0, dusk: 0.8, night: 0.85 };
  const LCOL = { lamp: [255, 190, 110], window: [255, 214, 140], banner: [255, 150, 160], lantern: [255, 200, 120], portal: [110, 230, 215], player: [255, 214, 150], firefly: [255, 233, 138] };
  const SPEED = 72, NPC_SPEED = 30, HW = 5, HH = 3;

  function loadImg(src) { return new Promise((res, rej) => { const im = new Image(); im.onload = () => res(im); im.onerror = () => rej(new Error('img ' + src)); im.src = src; }); }
  async function load(base, mode) {
    const t0 = performance.now(); base = base || 'art/town/';
    const names = TM.PROP_NAMES, chars = ['player', 'elder', 'fern', 'clerk'];
    const [tiles, ...rest] = await Promise.all([loadImg(base + 'town_tiles.png')].concat(names.map(n => loadImg(base + 'props/' + n + '.png')), chars.map(n => loadImg(base + 'char_' + n + '.png'))));
    const props = {}, ch = {}; names.forEach((n, i) => { props[n] = rest[i]; }); chars.forEach((n, i) => { ch['char_' + n] = rest[names.length + i]; });
    let maps, from = 'json';
    if (mode !== 'gen') { try { maps = {}; for (const id of ['town_morningmoss', 'route_fernshade']) { const r = await fetch(base + id + '.json'); if (!r.ok) throw new Error(r.status); maps[id] = await r.json(); } } catch (e) { maps = null; } }
    if (!maps) { maps = TM.buildMaps('night'); from = 'generated'; }
    return { tiles, props, chars: ch, maps, loadMs: performance.now() - t0, from };
  }
  const prop = (o, k, d) => { const p = (o.properties || []).find(q => q.name === k); return p ? p.value : d; };
  function cv(w, h) { const c = document.createElement('canvas'); c.width = Math.max(1, w | 0); c.height = Math.max(1, h | 0); return c; }

  function create(canvas, A, opt) {
    opt = opt || {};
    const ctx = canvas.getContext('2d', { alpha: false, willReadFrequently: !!opt.willRead });
    const S = { q: opt.q || 'high', chunk: opt.chunk !== 0, tod: opt.tod || 'night', dpr: opt.dpr || 1, zoom: opt.zoom || 2, W: 0, H: 0, light: null, dof: null, mapId: null, fade: 0, t: 0, perf: { fps: 0 }, lastAstar: 0 };
    const keys = {}, joy = { on: false, id: -1, ox: 0, oy: 0, dx: 0, dy: 0 };
    let M = null, pending = null, fadeTo = null, dlgT = 0, toast = '';
    const P = { x: 0, y: 0, dir: 'd', walk: 0, path: null, pi: 0 };
    const stats = { astarMs: [], chunkMs: 0, chunkPx: 0, tilesDrawn: 0 };

    function setQ(q, o) { S.q = q; o = o || {}; if (o.chunk !== undefined) S.chunk = !!o.chunk; if (o.light) S.lightMode = o.light; else S.lightMode = null; if (o.dof !== undefined) S.dofOv = o.dof; else S.dofOv = null; if (o.glow !== undefined) S.glowOv = o.glow; else S.glowOv = null; }
    const cfg = () => { const c = Object.assign({}, QUAL[S.q]); if (S.lightMode) c.light = S.lightMode; if (S.dofOv != null) c.dof = S.dofOv; if (S.glowOv != null) c.glow = S.glowOv; return c; };

    function resize(cssW, cssH, dpr) {
      S.dpr = dpr || S.dpr; S.cssW = cssW; S.cssH = cssH; S.W = Math.round(cssW * S.dpr); S.H = Math.round(cssH * S.dpr);
      canvas.width = S.W; canvas.height = S.H; canvas.style.width = cssW + 'px'; canvas.style.height = cssH + 'px';
      S.zoom = opt.zoom || (cssW < 600 ? 2 : 3); S.s = S.zoom * S.dpr; S.vw = S.W / S.s; S.vh = S.H / S.s; light = null; dofBufs = null; vig = null;
    }
    // ---------- 地圖 ----------
    function enter(id, spawnName) {
      const t0 = performance.now(), m = A.maps[id]; if (!m) return false;
      const L = n => TM.layerOf(m, n), G = n => (L(n).objects || []);
      M = { id, m, w: m.width, h: m.height, grid: TM.buildGrid(m), ground: L('ground').data, decor: L('decor').data, occ: L('occlusion').data, props: [], npcs: [], lights: [], portals: [], spawns: {}, events: G('events'), anim: [], chunks: [], occChunks: [] };
      for (const o of G('props')) M.props.push({ img: A.props[TM.PROP_NAMES[o.gid - TM.PROP_FIRSTGID]], x: o.x, y: o.y - o.height, w: o.width, h: o.height, key: o.y, name: o.name });
      M.props.sort((a, b) => a.key - b.key);
      for (const o of G('npcs')) { const pt = String(prop(o, 'patrol', '')).split(';').filter(Boolean).map(s => s.split(',').map(Number)); M.npcs.push({ name: o.name, display: prop(o, 'display', ''), img: A.chars[prop(o, 'sprite', 'char_elder')], x: o.x + 8, y: o.y + 8, dir: prop(o, 'dir', 'd'), dialog: prop(o, 'dialog', ''), patrol: pt, pi: 0, path: null, wait: Math.random() * 2, walk: 0 }); }
      for (const o of G('lights')) M.lights.push({ x: o.x, y: o.y, r: prop(o, 'radius', 60), kind: prop(o, 'kind', 'lamp'), ph: Math.random() * 6.28 });
      for (const o of G('portals')) M.portals.push({ name: o.name, x: o.x, y: o.y, w: o.width, h: o.height, target: prop(o, 'target', ''), spawn: prop(o, 'spawn', ''), glow: prop(o, 'glow', 'cool') });
      for (const o of G('spawns')) M.spawns[o.name] = { x: o.x, y: o.y, dir: prop(o, 'dir', 'd') };
      for (let i = 0; i < M.w * M.h; i++) { const gg = M.ground[i]; if (gg === TM.T.water || gg === TM.T.water_b) M.anim.push(i); }
      // chunk 預渲染（原生 1× 解像度；放大用 nearest）
      const tc0 = performance.now(); stats.chunkPx = 0;
      for (let cy = 0; cy * CHUNK < M.h; cy++) for (let cx = 0; cx * CHUNK < M.w; cx++) {
        const tw = Math.min(CHUNK, M.w - cx * CHUNK), th = Math.min(CHUNK, M.h - cy * CHUNK);
        const c = cv(tw * TILE, th * TILE), cx2 = c.getContext('2d'); cx2.imageSmoothingEnabled = false; drawTiles(cx2, ['ground', 'decor'], cx * CHUNK, cy * CHUNK, tw, th, -cx * CHUNK * TILE, -cy * CHUNK * TILE);
        M.chunks[cy * 99 + cx] = c; stats.chunkPx += c.width * c.height;
        let any = false; for (let j = 0; j < th && !any; j++) for (let i = 0; i < tw; i++) if (M.occ[(cy * CHUNK + j) * M.w + cx * CHUNK + i]) { any = true; break; }
        if (any) { const o = cv(tw * TILE, th * TILE), ox = o.getContext('2d'); drawTiles(ox, ['occlusion'], cx * CHUNK, cy * CHUNK, tw, th, -cx * CHUNK * TILE, -cy * CHUNK * TILE); M.occChunks[cy * 99 + cx] = o; stats.chunkPx += o.width * o.height; }
      }
      stats.chunkMs = performance.now() - tc0;
      bakeLight();
      const sp = M.spawns[spawnName] || M.spawns.start || Object.values(M.spawns)[0]; P.x = sp.x; P.y = sp.y; P.dir = sp.dir; P.path = null; S.mapId = id; S.mapLoadMs = performance.now() - t0; camSnap(); return true;
    }
    function tileSrc(gid) { const i = gid - 1; return [(i % 16) * TILE, ((i / 16) | 0) * TILE]; }
    function drawTiles(c, layers, x0, y0, tw, th, ox, oy) {
      for (const ln of layers) { const d = ln === 'ground' ? M.ground : ln === 'decor' ? M.decor : M.occ;
        for (let j = 0; j < th; j++) for (let i = 0; i < tw; i++) { const gid = d[(y0 + j) * M.w + x0 + i]; if (!gid) continue; const s = tileSrc(gid); c.drawImage(A.tiles, s[0], s[1], TILE, TILE, ox + (x0 + i) * TILE, oy + (y0 + j) * TILE, TILE, TILE); stats.tilesDrawn++; } }
    }
    // 靜態烘焙光圖（整張圖 1/2 解像度；夜／黃昏）
    const lightSprites = {};
    function lightSprite(kind, r) {
      const k = kind + '_' + r; if (lightSprites[k]) return lightSprites[k]; const c = cv(r * 2, r * 2), x = c.getContext('2d'), col = LCOL[kind] || LCOL.lamp;
      const gr = x.createRadialGradient(r, r, 0, r, r, r); gr.addColorStop(0, `rgba(${col},1)`); gr.addColorStop(0.35, `rgba(${col.map(v => v * 0.55 | 0)},1)`); gr.addColorStop(1, 'rgba(0,0,0,1)');
      x.fillStyle = gr; x.fillRect(0, 0, r * 2, r * 2); return (lightSprites[k] = c);
    }
    function ambFill(x, w, h) { const a = AMB[S.tod] || AMB.night; x.globalCompositeOperation = 'source-over'; x.fillStyle = `rgb(${a})`; x.fillRect(0, 0, w, h); }
    function bakeLight() {
      const sc = 0.5, b = cv(M.w * TILE * sc, M.h * TILE * sc), x = b.getContext('2d'); ambFill(x, b.width, b.height);
      if (LSTR[S.tod] > 0) { x.globalCompositeOperation = 'lighter'; x.globalAlpha = LSTR[S.tod]; for (const l of M.lights) { const sp = lightSprite(l.kind, l.r); x.drawImage(sp, (l.x - l.r) * sc, (l.y - l.r) * sc, l.r * 2 * sc, l.r * 2 * sc); } x.globalAlpha = 1; }
      M.baked = b; stats.chunkPx += 0;
    }
    // ---------- 路徑／互動 ----------
    const tileOf = v => Math.floor(v / TILE);
    function pathTo(sx, sy, tx, ty, smooth) { const t0 = performance.now(); let p = TM.astar(M.grid, sx, sy, tx, ty); if (p && smooth !== false) p = TM.smoothPath(M.grid, p); const dt = performance.now() - t0; stats.astarMs.push(dt); if (stats.astarMs.length > 400) stats.astarMs.shift(); S.lastAstar = dt; return p; }
    function tapWorld(wx, wy) {
      const npc = M.npcs.find(n => Math.hypot(n.x - wx, n.y - 8 - wy) < 14);   // 點中 NPC → 走到旁邊再對話
      let tx = tileOf(wx), ty = tileOf(wy); pending = null;
      if (npc) { pending = { npc }; tx = tileOf(npc.x); ty = tileOf(npc.y) + 1; }
      const sg = (() => { const sn = M.events.find(e => e.type === 'sign' && tileOf(wx) === e.x / TILE && tileOf(wy) === e.y / TILE); return sn; })();
      if (sg) { pending = { sign: sg }; }
      const n = TM.nearestWalkable(M.grid, tx, ty, 3); if (!n) return false;
      const p = pathTo(tileOf(P.x), tileOf(P.y), n[0], n[1]); if (!p) { S.lastTap = 'nopath'; return false; }
      P.path = p; P.pi = p.length > 1 ? 1 : 0; S.lastTap = 'path ' + p.length; S.marker = { x: n[0] * TILE + 8, y: n[1] * TILE + 8, t: S.t }; return true;
    }
    function say(name, text) { const d = document.getElementById('dlg'); if (!d) return; d.innerHTML = '<b></b><span></span>'; d.firstChild.textContent = name; d.lastChild.textContent = text; d.style.display = 'block'; dlgT = 3; }
    const LINES = { 'dlg.elder.intro': '歡迎返嚟，今晚風好大。去蕨影小徑睇下啦。', 'dlg.fern.rival1': '喂！等你熱完身，我哋賽道上見。', 'dlg.clerk.register': '報名處今日開放，東門通往迴風場。', 'sign.square': '晨苔廣場（示範告示）', 'sign.hall': '報名處 ↑', 'dlg.route.wild': '（野靈對你眨眨眼）' };
    function interact(n) { say(n.display || n.name, LINES[n.dialog] || n.dialog); }
    function doToast(t) { toast = t; S.toastT = 2; say('傳送點', t); }
    function teleport(p) {
      if (S.fade > 0) return; const dest = A.maps[p.target];
      if (!dest) { doToast('目標場景「' + p.target + '」未接入（M1 先接賽跑場景）'); P.path = null; P.x -= (P.x > p.x ? -1 : 1) * 14; return; }
      fadeTo = { id: p.target, spawn: p.spawn }; S.fade = 0.0001; S.fadeDir = 1;
    }
    // ---------- 更新 ----------
    function inputVec() {
      let dx = (keys.ArrowRight || keys.d || keys.D ? 1 : 0) - (keys.ArrowLeft || keys.a || keys.A ? 1 : 0), dy = (keys.ArrowDown || keys.s || keys.S ? 1 : 0) - (keys.ArrowUp || keys.w || keys.W ? 1 : 0);
      if (joy.on) { dx += joy.dx; dy += joy.dy; } const l = Math.hypot(dx, dy); if (l > 1) { dx /= l; dy /= l; } return [dx, dy, l];
    }
    function npcBlock(x, y) { for (const n of M.npcs) if (Math.abs(n.x - x) < 9 && Math.abs(n.y - y) < 7) return true; return false; }
    function stepMove(e, dx, dy, hw, hh, block) { let [nx, ny] = TM.moveBox(M.grid, e.x, e.y, dx, 0, hw, hh); [nx, ny] = TM.moveBox(M.grid, nx, e.y, 0, dy, hw, hh); if (block && npcBlock(nx, ny) && !npcBlock(e.x, e.y)) return false; const mv = nx !== e.x || ny !== e.y; e.x = nx; e.y = ny; return mv; }
    function faceOf(e, dx, dy) { e.dir = Math.abs(dx) > Math.abs(dy) ? (dx < 0 ? 'l' : 'r') : (dy < 0 ? 'u' : 'd'); }
    function update(dt) {
      S.t += dt; if (dlgT > 0) { dlgT -= dt; if (dlgT <= 0) { const d = document.getElementById('dlg'); if (d) d.style.display = 'none'; } }
      if (S.fade > 0) { S.fade += dt * 4 * S.fadeDir; if (S.fadeDir > 0 && S.fade >= 1) { enter(fadeTo.id, fadeTo.spawn); S.fadeDir = -1; S.fade = 1; } else if (S.fadeDir < 0 && S.fade <= 0) { S.fade = 0; fadeTo = null; } return; }
      const [ix, iy, il] = inputVec(); let moving = false;
      if (il > 0.12) { P.path = null; pending = null; moving = stepMove(P, ix * SPEED * dt, iy * SPEED * dt, HW, HH, true); faceOf(P, ix, iy); }
      else if (P.path) {
        const w = P.path[P.pi]; if (!w) { P.path = null; } else {
          const tx = w[0] * TILE + 8, ty = w[1] * TILE + 8, dx = tx - P.x, dy = ty - P.y, d = Math.hypot(dx, dy), step = SPEED * dt;
          if (d <= step + 0.5) { P.x = tx; P.y = ty; P.pi++; if (P.pi >= P.path.length) { P.path = null; if (pending && pending.npc) { faceOf(P, pending.npc.x - P.x, pending.npc.y - P.y); interact(pending.npc); } else if (pending && pending.sign) { say('告示', LINES[prop(pending.sign, 'text', '')] || '…'); } pending = null; } moving = true; }
          else { const mv = stepMove(P, dx / d * step, dy / d * step, HW, HH, true); moving = mv; if (!mv) { P.path = null; } faceOf(P, dx, dy); }
        }
      }
      P.walk = moving ? P.walk + dt * 8 : 0;
      for (const n of M.npcs) { // 巡邏
        if (!n.patrol.length) continue; if (n.wait > 0) { n.wait -= dt; n.walk = 0; continue; }
        if (!n.path) { const nx = n.patrol[(n.pi = (n.pi + 1) % n.patrol.length)]; n.path = TM.astar(M.grid, tileOf(n.x), tileOf(n.y), nx[0], nx[1]); n.k = 1; if (!n.path) n.wait = 1; }
        else { const w = n.path[n.k]; if (!w) { n.path = null; n.wait = 1.5 + Math.random() * 2; continue; } const tx = w[0] * TILE + 8, ty = w[1] * TILE + 8, dx = tx - n.x, dy = ty - n.y, d = Math.hypot(dx, dy), st = NPC_SPEED * dt; if (d <= st) { n.x = tx; n.y = ty; n.k++; } else { n.x += dx / d * st; n.y += dy / d * st; faceOf(n, dx, dy); } n.walk += dt * 6; }
      }
      for (const p of M.portals) if (P.x >= p.x && P.x < p.x + p.w && P.y >= p.y && P.y < p.y + p.h) { teleport(p); break; }
      // 鏡頭
      const tx = P.x - S.vw / 2, ty = P.y - 8 - S.vh / 2; S.cx += (clampCam(tx, 'x') - S.cx) * Math.min(1, dt * 8); S.cy += (clampCam(ty, 'y') - S.cy) * Math.min(1, dt * 8);
    }
    function clampCam(v, ax) { const mw = (ax === 'x' ? M.w : M.h) * TILE, vv = ax === 'x' ? S.vw : S.vh; return mw <= vv ? (mw - vv) / 2 : Math.max(0, Math.min(mw - vv, v)); }
    function camSnap() { S.cx = clampCam(P.x - S.vw / 2, 'x'); S.cy = clampCam(P.y - 8 - S.vh / 2, 'y'); }
    // ---------- 渲染 ----------
    let light = null, dofBufs = null, vig = null;
    const snap = v => Math.round(v * S.s) / S.s;
    function drawActor(e, img) { const fr = e.walk ? (Math.floor(e.walk) % 4) : 0, row = 'dlru'.indexOf(e.dir); const x = Math.round(e.x - 8), y = Math.round(e.y - 21);
      ctx.drawImage(img, fr * 16, row * 24, 16, 24, x, y, 16, 24); }
    function render() {
      const c = cfg(), s = S.s, W = S.W, H = S.H;
      ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalCompositeOperation = 'source-over'; ctx.globalAlpha = 1; ctx.imageSmoothingEnabled = false;
      ctx.fillStyle = '#10163a'; ctx.fillRect(0, 0, W, H);
      const cx = snap(S.cx), cy = snap(S.cy); ctx.setTransform(s, 0, 0, s, -cx * s, -cy * s);
      const tx0 = Math.max(0, Math.floor(cx / TILE)), ty0 = Math.max(0, Math.floor(cy / TILE)), tx1 = Math.min(M.w - 1, Math.floor((cx + S.vw) / TILE)), ty1 = Math.min(M.h - 1, Math.floor((cy + S.vh) / TILE));
      stats.tilesDrawn = 0;
      if (S.chunk) { for (let j = Math.floor(ty0 / CHUNK); j <= Math.floor(ty1 / CHUNK); j++) for (let i = Math.floor(tx0 / CHUNK); i <= Math.floor(tx1 / CHUNK); i++) { const k = M.chunks[j * 99 + i]; if (k) { ctx.drawImage(k, i * CHUNK * TILE, j * CHUNK * TILE); stats.tilesDrawn++; } } }
      else drawTiles(ctx, ['ground', 'decor'], tx0, ty0, tx1 - tx0 + 1, ty1 - ty0 + 1, 0, 0);
      // 水面動畫（逐格覆蓋；chunk 內存靜態圖）
      const wf = Math.floor(S.t * 1.6) % 2; for (const i of M.anim) { const x = i % M.w, y = (i / M.w) | 0; if (x < tx0 || x > tx1 || y < ty0 || y > ty1) continue; const gs = tileSrc(((x + y + wf) % 2) ? TM.T.water : TM.T.water_b); ctx.drawImage(A.tiles, gs[0], gs[1], TILE, TILE, x * TILE, y * TILE, TILE, TILE); }
      // 傳送點光環
      for (const p of M.portals) { const f = Math.floor(S.t * 3) % 2, gs = tileSrc(f ? TM.T.portal_b : TM.T.portal_a); for (let j = 0; j < p.h / TILE; j++) for (let i = 0; i < p.w / TILE; i++) ctx.drawImage(A.tiles, gs[0], gs[1], TILE, TILE, p.x + i * TILE, p.y + j * TILE, TILE, TILE); }
      if (S.marker && S.t - S.marker.t < 1.2) { ctx.globalAlpha = 1 - (S.t - S.marker.t) / 1.2; ctx.strokeStyle = '#ffe98a'; ctx.lineWidth = 1; ctx.beginPath(); ctx.arc(S.marker.x, S.marker.y, 3 + (S.t - S.marker.t) * 6, 0, 6.3); ctx.stroke(); ctx.globalAlpha = 1; }
      // Y 排序：道具＋NPC＋玩家
      const ents = []; for (const p of M.props) { if (p.x > cx + S.vw || p.x + p.w < cx || p.y > cy + S.vh || p.y + p.h < cy) continue; ents.push({ k: p.key, p }); }
      for (const n of M.npcs) ents.push({ k: n.y + 3, n }); ents.push({ k: P.y + 3, pl: 1 }); ents.sort((a, b) => a.k - b.k);
      for (const e of ents) { if (e.p) ctx.drawImage(e.p.img, e.p.x, e.p.y); else { const a = e.n || P; ctx.fillStyle = 'rgba(30,20,50,.35)'; ctx.beginPath(); ctx.ellipse(a.x, a.y + 2, 6, 2.5, 0, 0, 6.3); ctx.fill(); drawActor(a, e.n ? e.n.img : A.chars.char_player); } }
      // 遮擋圖塊層（拱門等）
      if (S.chunk) { for (let j = Math.floor(ty0 / CHUNK); j <= Math.floor(ty1 / CHUNK); j++) for (let i = Math.floor(tx0 / CHUNK); i <= Math.floor(tx1 / CHUNK); i++) { const k = M.occChunks[j * 99 + i]; if (k) ctx.drawImage(k, i * CHUNK * TILE, j * CHUNK * TILE); } }
      else drawTiles(ctx, ['occlusion'], tx0, ty0, tx1 - tx0 + 1, ty1 - ty0 + 1, 0, 0);
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      // 光
      const ls = LSTR[S.tod]; if (c.light === 'baked') {
        ctx.globalCompositeOperation = 'multiply'; ctx.imageSmoothingEnabled = true; ctx.drawImage(M.baked, cx * 0.5, cy * 0.5, S.vw * 0.5, S.vh * 0.5, 0, 0, W, H); ctx.globalCompositeOperation = 'source-over';
      } else if (c.light === 'live') {
        const lw = Math.max(8, Math.round(W / (c.lres * S.dpr))), lh = Math.max(8, Math.round(H / (c.lres * S.dpr)));
        if (!light || light.width !== lw || light.height !== lh) { light = cv(lw, lh); }
        const lx = light.getContext('2d'); ambFill(lx, lw, lh); const k = lw / S.vw;
        if (ls > 0) {
          lx.globalCompositeOperation = 'lighter'; lx.globalAlpha = ls;
          for (const l of M.lights) { const r = l.r * (1 + 0.05 * Math.sin(S.t * 7 + l.ph) + 0.03 * Math.sin(S.t * 13 + l.ph * 2)); if (l.x + r < cx || l.x - r > cx + S.vw || l.y + r < cy || l.y - r > cy + S.vh) continue; const sp = lightSprite(l.kind, l.r); lx.drawImage(sp, (l.x - r - cx) * k, (l.y - r - cy) * k, r * 2 * k, r * 2 * k); }
          const pr = 58; lx.drawImage(lightSprite('player', pr), (P.x - pr - cx) * k, (P.y - 8 - pr - cy) * k, pr * 2 * k, pr * 2 * k); lx.globalAlpha = 1;
        }
        ctx.globalCompositeOperation = 'multiply'; ctx.imageSmoothingEnabled = true; ctx.drawImage(light, 0, 0, W, H);
        if (c.glow && ls > 0) { ctx.globalCompositeOperation = 'lighter'; ctx.globalAlpha = 0.22 * ls; ctx.drawImage(light, 0, 0, W, H); ctx.globalAlpha = 1; }
        ctx.globalCompositeOperation = 'source-over';
      }
      // 景深（遠＝上、近＝下；tilt-shift 帶）
      if (c.dof) dof(0.26, 0.2);
      if (c.vig) { if (!vig || vig.width !== W) { vig = cv(W, H); const vx = vig.getContext('2d'), gr = vx.createRadialGradient(W / 2, H / 2, Math.min(W, H) * 0.3, W / 2, H / 2, Math.max(W, H) * 0.75); gr.addColorStop(0, 'rgba(10,12,40,0)'); gr.addColorStop(1, 'rgba(10,12,40,.5)'); vx.fillStyle = gr; vx.fillRect(0, 0, W, H); } ctx.drawImage(vig, 0, 0); }
      if (S.fade > 0) { ctx.fillStyle = `rgba(8,10,30,${Math.min(1, S.fade)})`; ctx.fillRect(0, 0, W, H); }
    }
    function dof(topF, botF) {
      const W = S.W, H = S.H, bands = [[0, Math.round(H * topF), true], [H - Math.round(H * botF), Math.round(H * botF), false]];
      if (!dofBufs || dofBufs.W !== W) { dofBufs = { W, a: [], b: [] }; bands.forEach(() => { dofBufs.a.push(cv(W / 4, H / 4)); dofBufs.b.push(cv(W / 8, H / 8)); }); }
      ctx.imageSmoothingEnabled = true; ctx.globalCompositeOperation = 'source-over';
      bands.forEach((bd, i) => {
        const [y, h, top] = bd, a = dofBufs.a[i], b = dofBufs.b[i], ax = a.getContext('2d'), bx = b.getContext('2d'), w4 = W / 4 | 0, h4 = Math.max(1, h / 4 | 0), w8 = W / 8 | 0, h8 = Math.max(1, h / 8 | 0);
        ax.globalCompositeOperation = 'copy'; ax.drawImage(canvas, 0, y, W, h, 0, 0, w4, h4); bx.globalCompositeOperation = 'copy'; bx.drawImage(a, 0, 0, w4, h4, 0, 0, w8, h8);
        ax.globalCompositeOperation = 'copy'; ax.drawImage(b, 0, 0, w8, h8, 0, 0, w4, h4);
        ax.globalCompositeOperation = 'destination-in'; const gr = ax.createLinearGradient(0, 0, 0, h4); if (top) { gr.addColorStop(0, 'rgba(0,0,0,1)'); gr.addColorStop(1, 'rgba(0,0,0,0)'); } else { gr.addColorStop(0, 'rgba(0,0,0,0)'); gr.addColorStop(1, 'rgba(0,0,0,1)'); }
        ax.fillStyle = gr; ax.fillRect(0, 0, w4, h4); ctx.drawImage(a, 0, 0, w4, h4, 0, y, W, h);
      });
    }
    function flush() { ctx.getImageData(0, 0, 1, 1); }
    // ---------- 輸入 ----------
    function toWorld(ev) { const r = canvas.getBoundingClientRect(); return [(ev.clientX - r.left) / S.zoom + snap(S.cx), (ev.clientY - r.top) / S.zoom + snap(S.cy)]; }
    const joyEl = opt.joyEl, knobEl = opt.knobEl; let down = null;
    function joyShow(on) { if (joyEl) joyEl.style.display = on ? 'block' : 'none'; if (knobEl) knobEl.style.display = on ? 'block' : 'none'; }
    canvas.addEventListener('pointerdown', ev => { ev.preventDefault(); canvas.setPointerCapture && canvas.setPointerCapture(ev.pointerId); down = { id: ev.pointerId, x: ev.clientX, y: ev.clientY, t: performance.now(), moved: false, ev }; });
    canvas.addEventListener('pointermove', ev => {
      if (!down || ev.pointerId !== down.id) return; const dx = ev.clientX - down.x, dy = ev.clientY - down.y;
      if (!joy.on && (Math.hypot(dx, dy) > 12)) { joy.on = true; joy.ox = down.x; joy.oy = down.y; if (joyEl) { joyEl.style.left = joy.ox + 'px'; joyEl.style.top = joy.oy + 'px'; } joyShow(true); }   // 浮動：以按下位置為中心
      if (joy.on) { const R = 48, l = Math.hypot(ev.clientX - joy.ox, ev.clientY - joy.oy), k = l > R ? R / l : 1, vx = (ev.clientX - joy.ox) * k, vy = (ev.clientY - joy.oy) * k; joy.dx = vx / R; joy.dy = vy / R; if (knobEl) { knobEl.style.left = (joy.ox + vx) + 'px'; knobEl.style.top = (joy.oy + vy) + 'px'; } }
    });
    const up = ev => { if (!down || ev.pointerId !== down.id) return; if (!joy.on && performance.now() - down.t < 400) { const w = toWorld(ev); tapWorld(w[0], w[1]); } joy.on = false; joy.dx = joy.dy = 0; joyShow(false); down = null; };
    canvas.addEventListener('pointerup', up); canvas.addEventListener('pointercancel', up);
    g.addEventListener('keydown', e => { keys[e.key] = true; if ((e.key === 'e' || e.key === 'E' || e.key === ' ') && M) { const n = M.npcs.find(n => Math.hypot(n.x - P.x, n.y - P.y) < 26); if (n) interact(n); } });
    g.addEventListener('keyup', e => { keys[e.key] = false; });
    // ---------- 迴圈／量度 ----------
    let raf = 0, last = 0, acc = [];
    function loop(ts) { raf = requestAnimationFrame(loop); const dt = Math.min(0.05, (ts - last) / 1000 || 0.016); last = ts; update(dt); render(); acc.push(dt); if (acc.length > 30) acc.shift(); S.perf.fps = 1 / (acc.reduce((a, b) => a + b, 0) / acc.length); }
    function start() { if (!raf) { last = performance.now(); raf = requestAnimationFrame(loop); } }
    function stop() { cancelAnimationFrame(raf); raf = 0; }
    // headless 量幀時：唔受 vsync 限制，每幀 getImageData flush；玩家沿腳本路線行（含遮擋、傳送唔觸發）
    function bench(o) {
      o = o || {}; const N = o.frames || 240, warm = o.warm || 30, dt = 1 / 30; stop(); const times = [];
      const route = o.route || [[20, 24], [20, 18], [14, 16], [30, 16], [20, 12], [20, 4], [6, 10], [20, 22]]; let ri = 0;
      P.path = null; const go = () => { const r = route[ri++ % route.length]; const p = pathTo(tileOf(P.x), tileOf(P.y), r[0], r[1]); if (p) { P.path = p; P.pi = p.length > 1 ? 1 : 0; } };
      go();
      for (let i = 0; i < N + warm; i++) { if (!P.path) go(); const t0 = performance.now(); update(dt); render(); flush(); if (i >= warm) times.push(performance.now() - t0); }
      times.sort((a, b) => a - b); const avg = times.reduce((a, b) => a + b, 0) / times.length;
      return { avg, p50: times[times.length >> 1], p95: times[Math.floor(times.length * 0.95)], max: times[times.length - 1], n: times.length };
    }
    function astarBench(n) {
      const g2 = M.grid, free = []; for (let y = 0; y < g2.h; y++) for (let x = 0; x < g2.w; x++) if (!g2.isBlocked(x, y)) free.push([x, y]);
      let seed = 12345; const rnd = () => (seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0) / 4294967296; const ts = [], ls = [], ex = [];
      for (let i = 0; i < n; i++) { const a = free[rnd() * free.length | 0], b = free[rnd() * free.length | 0]; const t0 = performance.now(); const p = TM.astar(g2, a[0], a[1], b[0], b[1]); const t1 = performance.now(); if (p) { TM.smoothPath(g2, p); ts.push(t1 - t0); ls.push(p.length); ex.push(p.expanded || 0); } }
      ts.sort((a, b) => a - b); const m = a => a.reduce((x, y) => x + y, 0) / a.length; return { n: ts.length, avgMs: m(ts), p95Ms: ts[Math.floor(ts.length * 0.95)], maxMs: ts[ts.length - 1], avgLen: m(ls), avgExpanded: m(ex), freeTiles: free.length };
    }
    const api = { S, P, QUAL, setQ, cfg, resize, enter, start, stop, update, render, flush, bench, astarBench, tapWorld, say, stats, get M() { return M; }, state() { return { map: S.mapId, x: P.x, y: P.y, tx: tileOf(P.x), ty: tileOf(P.y), dir: P.dir, path: P.path ? P.path.length : 0, fade: S.fade, q: S.q, chunk: S.chunk, cam: [S.cx, S.cy], dlg: (document.getElementById('dlg') || {}).style ? document.getElementById('dlg').style.display : '' }; }, step(n, dt) { for (let i = 0; i < n; i++) update(dt || 1 / 30); render(); }, pathTo, tileOf, teleportTo(x, y) { P.x = x * TILE + 8; P.y = y * TILE + 8; P.path = null; camSnap(); } };
    return api;
  }
  g.WR.Town = { load, create, QUAL, AMB };
})(typeof globalThis !== 'undefined' ? globalThis : this);
