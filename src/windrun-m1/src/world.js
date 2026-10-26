/* world.js — Tiled 直讀渲染＋移動（town-lab／walk 共用；Canvas2D）。
   - 直接載入 Tiled JSON（內嵌或外部 .tsj tileset；多 tileset；collision firstgid 由 tilesets[name=='collision'] 讀，唔寫死）。
   - 圖層：ground／deco 烘焙成一張底圖；occlusion 依 ASSET_SPEC_TOWN §C 逐格 sort_y（向下掃到首個 collision=1）同實體一齊 Y 排序，
     掃唔到＝永遠喺實體之上；同 sort_y：玩家 > NPC > 貓 > 圖塊（tile key＝sortY＋0.001 → 圖塊壓住同 y 嘅實體）。
   - tsj `animation`（水 600／草 450／旗 150ms）；日夜 `swap_day_to_lit`（map property lit_swap）；light events → 光圖（multiply）。
   - 玩家 32px（pivot 16,31；12×8 碰撞盒）；NPC／野靈用 narrowcat town48 或玩家精靈染色（占位）；A* 點擊尋路＋浮動搖桿＋鍵盤。
   依賴：WR.Tiled、WR.TownMap（astar／smoothPath／nearestWalkable／moveBox）、WR.SceneEvents。 */
(function (g) {
  'use strict';
  const req = (n, k) => (typeof require !== 'undefined' && typeof module !== 'undefined') ? require(n) : g.WR[k];
  const Tiled = req('./tiled.js', 'Tiled'), TM = req('./town-map.js', 'TownMap'), SE = req('./scene-events.js', 'SceneEvents');
  const TILE = 16, SPEED = 72, SLOW = 0.6, HW = 6, HH = 4;
  const EXTRUDED = { 'tileset_morningmoss.png': 'tileset_morningmoss_extruded.png', 'tileset_morningmoss_b2.png': 'tileset_morningmoss_b2_extruded.png' };
  const AMB = { morning: null, day: null, dusk: [205, 150, 165], night: [44, 56, 108] }, LSTR = { dusk: 0.8, night: 0.85 };
  const DIRV = { u: [0, -1], d: [0, 1], l: [-1, 0], r: [1, 0] };

  // ---------- 載入 ----------
  const dirOf = p => { const i = p.lastIndexOf('/'); return i < 0 ? '' : p.slice(0, i + 1); };
  function join(base, p) { if (/^(https?:|data:|\/)/.test(p)) return p; const parts = (base + p).split('/'), o = []; for (const s of parts) { if (s === '..') o.pop(); else if (s !== '.' && s !== '') o.push(s); } return (base.startsWith('/') ? '/' : '') + o.join('/'); }
  const loadImg = src => new Promise((res, rej) => { const im = new Image(); im.onload = () => res(im); im.onerror = () => rej(new Error('img ' + src)); im.src = src; });
  const getJson = async u => { const r = await fetch(u); if (!r.ok) throw new Error(u + ' ' + r.status); return r.json(); };
  /** 載入場景（地圖＋tileset 圖＋日夜表）。opts.extrude（預設 true）：有 extruded 版本就用（tile id／firstgid 不變）。 */
  async function loadScene(url, opts) {
    opts = opts || {}; const t0 = performance.now(), map = await getJson(url), mdir = dirOf(url), loaded = {};
    for (const t of map.tilesets) if (t.source) loaded[t.source] = await getJson(join(mdir, t.source));
    const sets = Tiled.resolve(map, loaded);
    for (const ts of sets) {
      if (ts.name === 'collision' && !ts.imageSkip) { ts.img = null; continue; }
      let idir = ts.source ? join(mdir, ts.imgBase) : mdir; if (idir && !idir.endsWith('/')) idir += '/'; let file = ts.image, ex = ts.extruded;
      if (opts.extrude !== false && !ex && EXTRUDED[file.split('/').pop()]) { file = file.replace(/[^\/]*$/, EXTRUDED[file.split('/').pop()]); ts.margin = 1; ts.spacing = 2; ts.extruded = true; ex = true; }
      ts.img = await loadImg(join(idir, file));
    }
    let swap = null; const ls = Tiled.props(map).lit_swap;
    if (ls) { try { const j = await getJson(join(mdir, ls.split('#')[0])); swap = j[ls.split('#')[1]] || null; } catch (e) { swap = null; } }
    let phNames = null; const ph = sets.find(s => s.name === 'placeholder');
    if (ph) { try { const j = await getJson(join(mdir, (ph.imgBase || '') + 'tileset_placeholder_names.json')); phNames = j.names; } catch (e) { phNames = null; } }
    const dec = Tiled.decode(map, sets);
    return { url, map, sets, dec, swap, phNames, loadMs: performance.now() - t0 };
  }
  async function loadAssets(base, npcIds) {
    base = base || 'art/sprites/'; const npcs = {};
    await Promise.all((npcIds || []).map(async id => { try { const [img, atlas] = await Promise.all([loadImg(base + 'npc/' + id + '/atlas_' + id + '.png'), getJson(base + 'npc/' + id + '/atlas_' + id + '.json')]); npcs[id] = { img, atlas }; } catch (e) { /* 缺素材→占位 */ } }));
    const [pimg, patlas, cimg, catlas] = await Promise.all([loadImg(base + 'player/player_sheet.png'), getJson(base + 'player/player_atlas.json'), loadImg(base + 'narrowcat/town48/spirit_narrowcat_town48_sheet.png'), getJson(base + 'narrowcat/town48/spirit_narrowcat_town48_atlas.json')]);
    return { pimg, patlas, cimg, catlas, npcs };
  }
  const cv = (w, h) => { const c = document.createElement('canvas'); c.width = Math.max(1, w | 0); c.height = Math.max(1, h | 0); return c; };
  function tint(img, color, a) { const c = cv(img.width, img.height), x = c.getContext('2d'); x.drawImage(img, 0, 0); x.globalCompositeOperation = 'source-atop'; x.globalAlpha = a; x.fillStyle = color; x.fillRect(0, 0, c.width, c.height); return c; }

  // ---------- 世界 ----------
  function create(canvas, A, opt) {
    opt = opt || {};
    const ctx = canvas.getContext('2d', { alpha: false });
    const S = { dpr: opt.dpr || 1, zoom: 2, s: 2, W: 0, H: 0, vw: 0, vh: 0, cx: 0, cy: 0, t: 0, tod: opt.tod || null, fps: 0, labels: opt.labels !== false, debug: !!opt.debug, scene: null };
    const keys = {}, joy = { on: false, dx: 0, dy: 0, ox: 0, oy: 0 };
    const P = { x: 0, y: 0, dir: 'd', moving: false, path: null, pi: 0, force: false, lastTile: [0, 0], speedMul: 1 };
    const cat = { x: 0, y: 0, dir: 'r', moving: false, on: false, hist: [] };
    const hooks = { touch: null, interactable: null, cond: () => true, sceneReady: null }; let sc = null, inputLocked = false, pendingTarget = null, nearT = null, inside = new Set(), marker = null;
    const tinted = {}, stats = { bakeMs: 0, tilesDrawn: 0 };
    const pFrame = n => A.patlas.frames[n], cFrame = n => A.catlas.frames[n];

    function resize(cssW, cssH, dpr) {
      S.dpr = dpr || S.dpr; S.cssW = cssW; S.cssH = cssH; S.W = Math.round(cssW * S.dpr); S.H = Math.round(cssH * S.dpr); canvas.width = S.W; canvas.height = S.H; canvas.style.width = cssW + 'px'; canvas.style.height = cssH + 'px';
      S.zoom = opt.zoom || Math.max(1, Math.round(S.dpr * cssW / 288) / S.dpr * (opt.zoom ? 1 : 1)); S.s = opt.zoom ? opt.zoom * S.dpr : Math.max(1, Math.round(S.dpr * cssW / 288)); S.vw = S.W / S.s; S.vh = S.H / S.s; light = null;
    }
    // ---------- 場景 ----------
    let light = null;
    const isLit = () => S.tod === 'dusk' || S.tod === 'night';
    function drawGid(c, gid, dx, dy, time) {
      const ts = Tiled.tilesetFor(sc.sets, gid); if (!ts || !ts.img) return false; let id = gid - ts.firstgid; const an = ts.anim[id];
      if (an) { let tot = 0; for (const f of an) tot += f.duration; let t = time % tot; for (const f of an) { if (t < f.duration) { id = f.tileid; break; } t -= f.duration; } }
      const r = Tiled.srcRect(ts, id); c.drawImage(ts.img, r.sx, r.sy, ts.tilewidth, ts.tileheight, dx, dy, ts.tilewidth, ts.tileheight); stats.tilesDrawn++; return true;
    }
    const roleOf = (n, L) => (L.role === 'below_entities' || n === 'ground' || n === 'deco' || n === 'decor') ? 'below' : (L.role === 'above_entities' || n === 'occlusion') ? 'above' : null;
    function bake() {
      const t0 = performance.now(), d = sc.dec, W = d.w, H = d.h, lit = isLit() && sc.swap; const sw = lit ? sc.swap : null; const G = g0 => sw && sw[g0] ? sw[g0] : g0;
      sc.bg = cv(W * TILE, H * TILE); sc.bgx = sc.bg.getContext('2d'); sc.bgx.imageSmoothingEnabled = false; sc.occ = cv(W * TILE, H * TILE); const ox = sc.occ.getContext('2d'); ox.imageSmoothingEnabled = false;
      sc.animBelow = []; sc.animOcc = []; sc.occTiles = []; const below = d.order.filter(n => roleOf(n, d.layers[n]) === 'below'), above = d.order.filter(n => roleOf(n, d.layers[n]) === 'above'); sc.below = below;
      sc.occSort = new Float32Array(W * H).fill(Infinity);
      const anyOcc = new Uint8Array(W * H); for (const n of above) for (let i = 0; i < W * H; i++) if (d.layers[n].gids[i]) anyOcc[i] = 1;
      sc.occSort = Tiled.occlusionSort(W, H, anyOcc, sc.col, TILE);
      for (let i = 0; i < W * H; i++) {
        const x = i % W, y = (i / W) | 0;
        for (const n of below) { const gid = G(d.layers[n].gids[i]); if (!gid) continue; const ts = Tiled.tilesetFor(sc.sets, gid); if (ts && ts.anim[gid - ts.firstgid]) sc.animBelow.push(i); drawGid(sc.bgx, gid, x * TILE, y * TILE, 0); }
        for (const n of above) { const gid = G(d.layers[n].gids[i]); if (!gid) continue; const ts = Tiled.tilesetFor(sc.sets, gid), an = ts && ts.anim[gid - ts.firstgid] ? 1 : 0, key = sc.occSort[i];
          if (key === Infinity) { if (an) sc.animOcc.push({ gid, x: x * TILE, y: y * TILE }); else drawGid(ox, gid, x * TILE, y * TILE, 0); } else sc.occTiles.push({ gid, x: x * TILE, y: y * TILE, key: key + 0.001, tile: true }); }
      }
      sc.animBelow = Array.from(new Set(sc.animBelow)); sc.animLast = new Map(); sc.litBaked = !!lit; stats.bakeMs = performance.now() - t0; light = null;
    }
    function updAnim(time) {
      const d = sc.dec, W = d.w; const sw = sc.litBaked ? sc.swap : null; const G = g0 => sw && sw[g0] ? sw[g0] : g0;
      for (const i of sc.animBelow) {
        let sig = ''; for (const n of sc.below) { const gid = G(d.layers[n].gids[i]); if (!gid) continue; const ts = Tiled.tilesetFor(sc.sets, gid); const an = ts && ts.anim[gid - ts.firstgid]; if (an) { let tot = 0; for (const f of an) tot += f.duration; let t = time % tot, k = 0; for (const f of an) { if (t < f.duration) break; t -= f.duration; k++; } sig += k; } }
        if (sc.animLast.get(i) === sig) continue; sc.animLast.set(i, sig); const x = i % W, y = (i / W) | 0; sc.bgx.clearRect(x * TILE, y * TILE, TILE, TILE);
        for (const n of sc.below) { const gid = G(d.layers[n].gids[i]); if (gid) drawGid(sc.bgx, gid, x * TILE, y * TILE, time); }
      }
    }
    function buildLight() {
      const a = AMB[S.tod]; if (!a || !sc) { light = false; return; } const k = 0.5, c = cv(sc.dec.w * TILE * k, sc.dec.h * TILE * k), x = c.getContext('2d');
      x.fillStyle = `rgb(${a})`; x.fillRect(0, 0, c.width, c.height); x.globalCompositeOperation = 'lighter'; x.globalAlpha = LSTR[S.tod] || 0.8;
      for (const l of sc.lights) { const r = l.r * k, col = parseInt(l.color.slice(1), 16), rgb = [col >> 16 & 255, col >> 8 & 255, col & 255]; const gr = x.createRadialGradient(l.x * k, l.y * k, 0, l.x * k, l.y * k, r); gr.addColorStop(0, `rgba(${rgb},0.9)`); gr.addColorStop(0.4, `rgba(${rgb.map(v => v * 0.5 | 0)},0.5)`); gr.addColorStop(1, 'rgba(0,0,0,0)'); x.fillStyle = gr; x.fillRect(l.x * k - r, l.y * k - r, r * 2, r * 2); }
      light = c;
    }
    /** 進入場景。at：{spawn:name}｜{x,y（px）,dir}｜{tx,ty,dir}。 */
    function enter(scene, at, ctxO) {
      sc = S.scene = scene; at = at || {}; const d = scene.dec;
      sc.col = Uint8Array.from(d.collision);
      const norm = SE.normalize(d, Object.assign({ sceneIds: ctxO && ctxO.sceneIds, npcSprites: A.npcs ? Object.keys(A.npcs) : [], dialogIds: ctxO && ctxO.dialogIds, nodeIndex: ctxO && ctxO.nodeIndex, overlay: ctxO && ctxO.overlay }, {}));
      sc.norm = norm; sc.events = norm.events; sc.lights = norm.lights; sc.spawns = norm.spawns; sc.fx = norm.fx; sc.dyn = new Set(); sc.slowTiles = 0;
      const W = d.w, H = d.h;
      sc.grid = { w: W, h: H, isBlocked(x, y) { if (x < 0 || y < 0 || x >= W || y >= H) return true; const i = y * W + x, v = sc.col[i]; return v === 1 || v === 2 || sc.dyn.has(i); }, slow(x, y) { return x >= 0 && y >= 0 && x < W && y < H && sc.col[y * W + x] === 4; } };
      S.tod = S.tod || Tiled.props(scene.map).tod_default || 'day';
      sc.npcs = norm.npcs.map(n => { const m = (n.sprite || '').match(/^human:(#[0-9a-fA-F]{6})$/); const am = (n.sprite || '').match(/^npc:(\w+)$/), at = am && A.npcs && A.npcs[am[1]]; return { atlasId: at ? am[1] : null, ev: n, name: n.name, display: n.display, x: (n.tx + 0.5) * TILE, y: (n.ty + 1) * TILE - 2, dir: n.facing, kind: at ? 'atlas' : m ? 'human' : 'cat', color: m ? m[1] : '#8a8f9a', visible: true, interactCell: n.interactCell, radius: n.radius }; });
      for (const n of sc.npcs) sc.dyn.add(Math.floor((n.y - 1) / TILE) * W + Math.floor(n.x / TILE));
      bake(); light = null; inside = new Set(); P.path = null; pendingTarget = null; nearT = null; P.force = false;
      let sp = null; if (at.spawn) sp = sc.spawns[at.spawn]; else if (at.x != null) sp = { x: at.x, y: at.y, dir: at.dir || 'd' }; else if (at.tx != null) sp = { x: (at.tx + 0.5) * TILE, y: (at.ty + 0.5) * TILE, dir: at.dir || 'd' };
      if (!sp) sp = sc.spawns[Object.keys(sc.spawns)[0]] || { x: W * 8, y: H * 8, dir: 'd' };
      const nw = TM.nearestWalkable(sc.grid, Math.floor(sp.x / TILE), Math.floor(sp.y / TILE), 4) || [Math.floor(sp.x / TILE), Math.floor(sp.y / TILE)];
      const exact = !sc.grid.isBlocked(Math.floor(sp.x / TILE), Math.floor(sp.y / TILE));
      P.x = exact ? sp.x : (nw[0] + 0.5) * TILE; P.y = (exact ? sp.y : (nw[1] + 0.5) * TILE) + 6; P.dir = sp.dir || 'd'; P.moving = false;   // 腳底 pivot：格心下移 6px（碰撞盒中心＝格心附近）
      cat.on = !!(norm.companion || at.cat); cat.x = P.x - 16; cat.y = P.y; cat.hist = []; P.lastTile = [Math.floor(P.x / TILE), Math.floor((P.y - HH) / TILE)];
      camSnap(); if (hooks.sceneReady) hooks.sceneReady(sc); fireTouches(true); return true;
    }
    function setTod(t) { if (S.tod === t) return; const wasLit = isLit(); S.tod = t; light = null; if (sc && wasLit !== isLit() && sc.swap) bake(); }
    function setBlocker(name, open) {
      const e = sc.events.find(x => x.kind === 'blocker' && x.name === name); if (!e) return false; const W = sc.dec.w;
      const ph = sc.sets.find(s => s.name === 'placeholder'), nm = open ? e.tileOpen : e.tileClosed, gid = ph && sc.phNames && nm in sc.phNames ? ph.firstgid + sc.phNames[nm] : 0;
      for (let j = 0; j < e.th; j++) for (let i = 0; i < e.tw; i++) {
        const idx = (e.ty + j) * W + e.tx + i; sc.col[idx] = open ? 0 : 1;
        if (gid) { sc.dec.layers.deco.gids[idx] = gid; const x = (e.tx + i) * TILE, y = (e.ty + j) * TILE; sc.bgx.clearRect(x, y, TILE, TILE); for (const n of sc.below) drawGid(sc.bgx, sc.dec.layers[n].gids[idx], x, y, 0); }
      }
      e.open = !!open; return true;
    }
    // ---------- 相機 ----------
    const snap = v => Math.round(v * S.s) / S.s;
    function camTarget() { const mw = sc.dec.w * TILE, mh = sc.dec.h * TILE; let cx = P.x - S.vw / 2, cy = P.y - 12 - S.vh / 2; cx = mw <= S.vw ? (mw - S.vw) / 2 : Math.max(0, Math.min(mw - S.vw, cx)); cy = mh <= S.vh ? (mh - S.vh) / 2 : Math.max(0, Math.min(mh - S.vh, cy)); return [cx, cy]; }
    function camSnap() { const t = camTarget(); S.cx = t[0]; S.cy = t[1]; }
    // ---------- 觸發／互動 ----------
    const cellOf = () => [Math.floor(P.x / TILE), Math.floor((P.y - HH) / TILE)];
    function inRect(e, tx, ty) { return tx >= e.tx && tx < e.tx + e.tw && ty >= e.ty && ty < e.ty + e.th; }
    function fireTouches(force) {
      const c = cellOf(), now = new Set();
      for (const e of sc.events) { if (e.kind !== 'touch' && e.kind !== 'auto') continue; if (inRect(e, c[0], c[1])) { now.add(e.name); if (force || !inside.has(e.name)) { if (hooks.touch) hooks.touch(e, { from: P.lastTile, cell: c }); } } }
      inside = now; P.lastTile = c;
    }
    function interactables() {
      const out = [];
      for (const n of sc.npcs) { if (!n.visible) continue; const pts = [[n.x, n.y - 8]]; if (n.interactCell) pts.push([(n.interactCell[0] + 0.5) * TILE, (n.interactCell[1] + 0.5) * TILE]); let d = 1e9; for (const p of pts) d = Math.min(d, Math.hypot(p[0] - P.x, p[1] - (P.y - 4))); out.push({ kind: 'npc', ref: n, name: n.name, d, range: n.radius * TILE }); }
      for (const e of sc.events) { if (e.kind !== 'interact') continue; if (e.visibleCond && !hooks.cond(e.visibleCond)) continue; if (e.cond && !hooks.cond(e.cond)) continue; const px = Math.max(e.tx * TILE, Math.min((e.tx + e.tw) * TILE, P.x)), py = Math.max(e.ty * TILE, Math.min((e.ty + e.th) * TILE, P.y - 4)); out.push({ kind: 'interact', ref: e, name: e.name, d: Math.hypot(px - P.x, py - (P.y - 4)), range: e.radius * TILE }); }
      return out;
    }
    function nearest() { let b = null; for (const t of interactables()) if (t.d <= t.range && (!b || t.d < b.d)) b = t; return b; }
    function refreshNear() { const n = nearest(); const k = n ? n.name : null; if ((nearT && nearT.name) !== k) { nearT = n; if (hooks.interactable) hooks.interactable(n); } else nearT = n; }
    // ---------- 路徑／輸入 ----------
    const tileOf = v => Math.floor(v / TILE);
    function pathTo(tx, ty) { const t0 = performance.now(); const sx = tileOf(P.x), sy = tileOf(P.y - HH); let p = TM.astar(sc.grid, sx, sy, tx, ty); if (p) p = TM.smoothPath(sc.grid, p); S.lastAstar = performance.now() - t0; return p; }
    function goTile(tx, ty, tgt) { const n = TM.nearestWalkable(sc.grid, tx, ty, 3); if (!n) return false; const p = pathTo(n[0], n[1]); if (!p) { S.lastTap = 'nopath'; return false; } P.path = p; P.pi = p.length > 1 ? 1 : 0; P.force = false; pendingTarget = tgt || null; marker = { x: n[0] * TILE + 8, y: n[1] * TILE + 8, t: S.t }; S.lastTap = 'path ' + p.length; return true; }
    function tapWorld(wx, wy) {
      if (inputLocked) return false;
      for (const n of sc.npcs) if (n.visible && Math.hypot(n.x - wx, n.y - 10 - wy) < 14) { const c = n.interactCell || [tileOf(n.x), tileOf(n.y - 1) + 1]; return goTile(c[0], c[1], { kind: 'npc', ref: n, name: n.name }) || (nearest() && nearest().name === n.name && (pendingTarget = null, true)); }
      for (const e of sc.events) if (e.kind === 'interact' && wx >= e.tx * TILE - 4 && wx < (e.tx + e.tw) * TILE + 4 && wy >= e.ty * TILE - 4 && wy < (e.ty + e.th) * TILE + 4) return goTile(e.tx, e.ty + e.th, { kind: 'interact', ref: e, name: e.name });
      return goTile(tileOf(wx), tileOf(wy));
    }
    function scriptMove(path) { P.path = path; P.pi = 0; P.force = true; }
    /** 被「推返」：dir＝'u|d|l|r'｜'auto'（由事件矩形中心指向玩家上一格）；tiles 格。 */
    function pushAway(ev, tiles, dir) {
      let v; if (dir && dir !== 'auto') v = DIRV[dir]; else { const cx = (ev.tx + ev.tw / 2) * TILE, cy = (ev.ty + ev.th / 2) * TILE, dx = (P.lastTile ? P.lastTile[0] : 0) , dy = 0; void dx; void dy; const fx = (ev._from ? ev._from[0] + 0.5 : cx / TILE) * TILE - cx, fy = (ev._from ? ev._from[1] + 0.5 : cy / TILE) * TILE - cy; v = Math.abs(fx) >= Math.abs(fy) ? [Math.sign(fx) || 1, 0] : [0, Math.sign(fy) || 1]; }
      const c = cellOf(); let tx = c[0], ty = c[1]; for (let i = 0; i < (tiles || 2); i++) { if (sc.grid.isBlocked(tx + v[0], ty + v[1])) break; tx += v[0]; ty += v[1]; }
      if (tx === c[0] && ty === c[1]) return false; scriptMove([[c[0], c[1]], [tx, ty]]); P.dir = v[0] ? (v[0] < 0 ? 'r' : 'l') : (v[1] < 0 ? 'd' : 'u'); return true;   // 面向事件（背向移動方向）
    }
    function move(dt) {
      let vx = 0, vy = 0, moving = false;
      if (!P.force && !inputLocked) { if (keys.ArrowLeft || keys.a || keys.A) vx -= 1; if (keys.ArrowRight || keys.d || keys.D) vx += 1; if (keys.ArrowUp || keys.w || keys.W) vy -= 1; if (keys.ArrowDown || keys.s || keys.S) vy += 1; if (joy.on) { vx += joy.dx; vy += joy.dy; } if (Math.hypot(vx, vy) > 0.15) { P.path = null; pendingTarget = null; } else { vx = vy = 0; } }
      if (P.path) { if (inputLocked && !P.force) { P.path = null; } else {
        const wp = P.path[P.pi]; if (!wp) { P.path = null; P.force = false; if (pendingTarget) { const t = pendingTarget; pendingTarget = null; const n = nearest(); if (n && n.name === t.name && hooks.interact) hooks.interact(n); } }
        else { const tx = (wp[0] + 0.5) * TILE, ty = (wp[1] + 0.5) * TILE + 6 - HH + HH, dx = tx - P.x, dy = ty - P.y, d = Math.hypot(dx, dy); if (d < 1.5) P.pi++; else { vx = dx / d; vy = dy / d; } }
      } }
      if (vx || vy) {
        const l = Math.hypot(vx, vy); if (l > 1) { vx /= l; vy /= l; } const c = cellOf(), sp = SPEED * (sc.grid.slow(c[0], c[1]) ? SLOW : 1) * P.speedMul * dt;
        const r = TM.moveBox(sc.grid, P.x, P.y - HH, vx * sp, vy * sp, HW, HH); const mx = r[0] - P.x, my = r[1] - (P.y - HH); P.x = r[0]; P.y = r[1] + HH; moving = Math.abs(mx) + Math.abs(my) > 0.01;
        if (!P.force || true) { if (Math.abs(vx) > Math.abs(vy)) P.dir = vx < 0 ? 'l' : 'r'; else P.dir = vy < 0 ? 'u' : 'd'; }
        if (!moving && P.path) { P.pi++; }   // 卡住：跳下一點
      }
      P.moving = moving;
      if (moving) { cat.hist.push([P.x, P.y]); if (cat.hist.length > 40) cat.hist.shift(); }
      if (cat.on) { const tgt = cat.hist.length > 7 ? cat.hist[cat.hist.length - 7] : null, dd = Math.hypot(cat.x - P.x, cat.y - P.y); if (tgt && dd > 22) { const dx = tgt[0] - cat.x, dy = tgt[1] - cat.y, d = Math.hypot(dx, dy) || 1, sp = SPEED * 0.93 * dt; cat.x += dx / d * Math.min(sp, d); cat.y += dy / d * Math.min(sp, d); cat.moving = true; if (Math.abs(dx) > 0.2) cat.dir = dx < 0 ? 'l' : 'r'; } else cat.moving = false; }
    }
    function update(dt) {
      if (!sc) return; S.t += dt; for (const n of sc.npcs) n.visible = !n.ev.visibleCond || hooks.cond(n.ev.visibleCond);
      move(dt); const c = cellOf(); if (c[0] !== P.lastTile[0] || c[1] !== P.lastTile[1] || true) fireTouches(false); refreshNear();
      const t = camTarget(); const k = 1 - Math.pow(0.001, dt); S.cx += (t[0] - S.cx) * k; S.cy += (t[1] - S.cy) * k; if (Math.abs(t[0] - S.cx) < 0.05) S.cx = t[0]; if (Math.abs(t[1] - S.cy) < 0.05) S.cy = t[1];
    }
    // ---------- 渲染 ----------
    function drawFrame(c, img, fr, x, y, flip) { c.drawImage(img, fr.x, fr.y, fr.w, fr.h, Math.round(x - fr.pivot[0]), Math.round(y - fr.pivot[1] + 1), fr.w, fr.h); }
    function playerFr() { const dn = { d: 'down', u: 'up', l: 'left', r: 'right' }[P.dir]; if (P.moving) return pFrame('player_' + dn + '_walk_' + (Math.floor(S.t * 8) % 4)); return pFrame('player_' + dn + '_idle'); }
    function catFr(dir, moving) { const side = dir === 'l' ? 'left' : 'right', a = moving ? 'walk' : 'idle', n = moving ? 4 : 2, i = Math.floor(S.t * (moving ? 8 : 2)) % n; return cFrame('spirit_narrowcat_town48_' + a + '_' + side + '_0' + i); }
    function npcImg(n) { if (n.kind === 'cat') { const k = 'cat' + n.color; return tinted[k] || (tinted[k] = tint(A.cimg, n.color, 0.35)); } const k = 'h' + n.color; return tinted[k] || (tinted[k] = tint(A.pimg, n.color, 0.45)); }
    // NPC 圖集（遊美 ASSET_SPEC_TOWN §N：32px、pivot(16,31)、idle 2@2fps／職員 stamp／flip once；完整幀繪製，唔裁頂部（蕨生髮頂 y=1））
    function drawNpcAtlas(c, n) {
      const a = A.npcs[n.atlasId], fr = a.atlas.frames, an = a.atlas.animations; let name, f;
      if (an.stamp) { const T = 4 + (n.atlasId.length % 3), ph = (S.t + n.x * 0.01) % (T + 1.2), k = Math.floor(S.t / (T + 1.2)); const which = k % 2 ? 'flip' : 'stamp'; if (ph < 4 / 6) name = an[which][Math.min(3, Math.floor(ph * 6))]; else name = an.idle_down[Math.floor(S.t * 2) % 2]; }
      else { const dn = { d: 'down', u: 'up', l: 'left', r: 'right' }[n.dir] || 'down'; const list = an['idle_' + dn]; name = list[Math.floor(S.t * 2) % list.length]; }
      f = fr[name]; c.drawImage(a.img, f.x, f.y, f.w, f.h, Math.round(n.x - f.pivot[0]), Math.round(n.y - f.pivot[1] + 1), f.w, f.h); S.npcDraw = S.npcDraw || {}; S.npcDraw[n.name] = { frame: name, h: f.h, top: Math.round(n.y - f.pivot[1] + 1) };
    }
    function render() {
      if (!sc) return; const s = S.s, t = S.t * 1000; updAnim(t);
      ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.fillStyle = '#0b0e22'; ctx.fillRect(0, 0, S.W, S.H); ctx.imageSmoothingEnabled = false;
      const cx = snap(S.cx), cy = snap(S.cy); ctx.setTransform(s, 0, 0, s, -cx * s, -cy * s);
      ctx.drawImage(sc.bg, 0, 0);
      const items = []; const x0 = cx - 24, x1 = cx + S.vw + 24, y0 = cy - 24, y1 = cy + S.vh + 24;
      for (const o of sc.occTiles) if (o.x > x0 - 16 && o.x < x1 && o.y > y0 - 16 && o.y < y1) items.push(o);
      const ent = (key, draw) => items.push({ key, draw });
      for (const n of sc.npcs) if (n.visible) ent(n.y + 0.0001, c => { if (n.kind === 'atlas') drawNpcAtlas(c, n); else if (n.kind === 'cat') drawFrame(c, npcImg(n), catFr(n.dir === 'l' ? 'l' : 'r', false), n.x, n.y); else { const dn = { d: 'down', u: 'up', l: 'left', r: 'right' }[n.dir]; drawFrame(c, npcImg(n), pFrame('player_' + dn + '_idle'), n.x, n.y); } });
      if (cat.on) ent(cat.y, c => drawFrame(c, A.cimg, catFr(cat.dir, cat.moving), cat.x, cat.y));
      ent(P.y + 0.0002, c => drawFrame(c, A.pimg, playerFr(), P.x, P.y));
      items.sort((a, b) => a.key - b.key);
      for (const it of items) if (it.tile) drawGid(ctx, it.gid, it.x, it.y, t); else it.draw(ctx);
      ctx.drawImage(sc.occ, 0, 0); for (const o of sc.animOcc) drawGid(ctx, o.gid, o.x, o.y, t);
      if (marker && S.t - marker.t < 0.6) { ctx.strokeStyle = 'rgba(255,233,138,' + (1 - (S.t - marker.t) / 0.6) + ')'; ctx.lineWidth = 1; ctx.strokeRect(marker.x - 5, marker.y - 5, 10, 10); }
      if (S.debug) { ctx.fillStyle = 'rgba(255,0,0,.28)'; for (let y = 0; y < sc.dec.h; y++) for (let x = 0; x < sc.dec.w; x++) { const v = sc.col[y * sc.dec.w + x]; if (v) { ctx.fillStyle = v === 1 ? 'rgba(255,0,0,.3)' : v === 2 ? 'rgba(0,120,255,.35)' : 'rgba(255,255,0,.3)'; ctx.fillRect(x * TILE, y * TILE, TILE, TILE); } } ctx.strokeStyle = '#0f0'; for (const e of sc.events) if (e.kind !== 'blocker') ctx.strokeRect(e.tx * TILE + .5, e.ty * TILE + .5, e.tw * TILE - 1, e.th * TILE - 1); }
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      if (AMB[S.tod]) { if (light === null) buildLight(); if (light) { ctx.globalCompositeOperation = 'multiply'; ctx.drawImage(light, cx * 0.5, cy * 0.5, S.vw * 0.5, S.vh * 0.5, 0, 0, S.W, S.H); ctx.globalCompositeOperation = 'source-over'; } }
      if (S.labels) { ctx.font = Math.round(10 * S.dpr) + 'px system-ui,"Noto Sans TC",sans-serif'; ctx.textAlign = 'center'; for (const n of sc.npcs) if (n.visible && n.display) { const sx = (n.x - cx) * s, sy = (n.y - 34 - cy) * s; ctx.fillStyle = 'rgba(10,14,40,.7)'; const w = ctx.measureText(n.display).width + 8 * S.dpr; ctx.fillRect(sx - w / 2, sy - 11 * S.dpr, w, 14 * S.dpr); ctx.fillStyle = '#ffe98a'; ctx.fillText(n.display, sx, sy); } }
    }
    // ---------- 輸入事件 ----------
    const toWorld = ev => { const r = canvas.getBoundingClientRect(); return [(ev.clientX - r.left) * (S.W / r.width) / S.s + snap(S.cx), (ev.clientY - r.top) * (S.H / r.height) / S.s + snap(S.cy)]; };
    const joyEl = opt.joyEl, knobEl = opt.knobEl; let down = null; const joyShow = on => { if (joyEl) joyEl.style.display = on ? 'block' : 'none'; if (knobEl) knobEl.style.display = on ? 'block' : 'none'; };
    canvas.addEventListener('pointerdown', ev => { ev.preventDefault(); canvas.setPointerCapture && canvas.setPointerCapture(ev.pointerId); down = { id: ev.pointerId, x: ev.clientX, y: ev.clientY, t: performance.now() }; });
    canvas.addEventListener('pointermove', ev => {
      if (!down || ev.pointerId !== down.id) return; const dx = ev.clientX - down.x, dy = ev.clientY - down.y;
      if (!joy.on && Math.hypot(dx, dy) > 12) { joy.on = true; joy.ox = down.x; joy.oy = down.y; if (joyEl) { joyEl.style.left = joy.ox + 'px'; joyEl.style.top = joy.oy + 'px'; } joyShow(true); }
      if (joy.on) { const R = 48, l = Math.hypot(ev.clientX - joy.ox, ev.clientY - joy.oy), k = l > R ? R / l : 1, vx = (ev.clientX - joy.ox) * k, vy = (ev.clientY - joy.oy) * k; joy.dx = vx / R; joy.dy = vy / R; if (knobEl) { knobEl.style.left = (joy.ox + vx) + 'px'; knobEl.style.top = (joy.oy + vy) + 'px'; } }
    });
    const up = ev => { if (!down || ev.pointerId !== down.id) return; if (!joy.on && performance.now() - down.t < 450) { const w = toWorld(ev); tapWorld(w[0], w[1]); } joy.on = false; joy.dx = joy.dy = 0; joyShow(false); down = null; };
    canvas.addEventListener('pointerup', up); canvas.addEventListener('pointercancel', up);
    g.addEventListener('keydown', e => { keys[e.key] = true; if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', ' '].indexOf(e.key) >= 0 && !e.target.closest) e.preventDefault(); });
    g.addEventListener('keyup', e => { keys[e.key] = false; });
    // ---------- 迴圈 ----------
    let raf = 0, last = 0, acc = [];
    function loop(ts) { raf = requestAnimationFrame(loop); const dt = Math.max(0, Math.min(0.05, (ts - last) / 1000 || 0.016)); last = ts; update(dt); render(); acc.push(dt); if (acc.length > 30) acc.shift(); S.fps = 1 / (acc.reduce((a, b) => a + b, 0) / acc.length); }
    const start = () => { if (!raf) { last = performance.now(); raf = requestAnimationFrame(loop); } }, stop = () => { cancelAnimationFrame(raf); raf = 0; };
    /** headless 量幀（唔係真機）：固定 dt＝1/30，每幀 getImageData flush。 */
    function bench(o) {
      o = o || {}; const N = o.frames || 240, warm = o.warm || 30, dt = 1 / 30, times = []; stop(); const route = o.route || [[20, 24], [20, 18], [14, 16], [30, 16], [20, 12], [20, 4], [6, 10], [20, 22]]; let ri = 0; P.path = null;
      const go = () => { const r = route[ri++ % route.length], p = pathTo(r[0], r[1]); if (p) { P.path = p; P.pi = p.length > 1 ? 1 : 0; P.force = true; } };
      for (let i = 0; i < N + warm; i++) { if (!P.path) go(); const t0 = performance.now(); update(dt); render(); ctx.getImageData(0, 0, 1, 1); if (i >= warm) times.push(performance.now() - t0); }
      times.sort((a, b) => a - b); const avg = times.reduce((a, b) => a + b, 0) / times.length; return { avg, p50: times[times.length >> 1], p95: times[Math.floor(times.length * 0.95)], max: times[times.length - 1], n: times.length };
    }
    const api = { S, P, cat, keys, hooks, enter, setTod, setBlocker, resize, update, render, start, stop, bench, tapWorld, goTile, scriptMove, pushAway, nearest, interactables, pathTo, cellOf,
      lock(v) { inputLocked = !!v; if (v && !P.force) { P.path = null; pendingTarget = null; } }, get locked() { return inputLocked; }, get scene() { return sc; }, get nearT() { return nearT; },
      faceNpc(name, dir) { const n = sc.npcs.find(x => x.name === name); if (n) n.dir = dir; return !!n; }, facePlayerTo(x, y) { const dx = x - P.x, dy = y - P.y; P.dir = Math.abs(dx) > Math.abs(dy) ? (dx < 0 ? 'l' : 'r') : (dy < 0 ? 'u' : 'd'); },
      state() { const c = cellOf(); return { map: sc && sc.url, x: P.x, y: P.y, tx: c[0], ty: c[1], dir: P.dir, moving: P.moving, path: P.path ? P.path.length - P.pi : 0, tod: S.tod, lit: sc && sc.litBaked }; } };
    return api;
  }
  const api = { create, loadScene, loadAssets, AMB, TILE, SPEED, HW, HH, join, EXTRUDED };
  g.WR = g.WR || {}; g.WR.World = api; if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
