/* town-map.js — 城鎮示範圖（晨苔鎮 40×30、蕨影小徑 48×16）生成＋格子碰撞＋A* 尋路＋碰撞盒移動。DOM-free，Node／瀏覽器共用。
   輸出格式＝Tiled JSON 子集（orthogonal、16px、tilelayer＋objectgroup、gid、tile object）：
   圖層：ground／decor／occlusion／collision（tilelayer）；props／npcs／portals／lights／spawns／encounters（objectgroup）。命名規範見 docs/engine-eval.md Q8。
   圖塊 gid＝art/town/town_tiles.names.txt（firstgid=1）；道具 gid＝101＋PROP_NAMES 索引（image-collection tileset）。
   全部原創、程序生成（唔係 Tiled 手繪）；用 Tiled GUI 開檔屬「待核實」。 */
(function (g) {
  'use strict';
  const TILE = 16;
  const TILE_NAMES = ['grass_a', 'grass_b', 'grass_c', 'dirt', 'cobble', 'plaza', 'water', 'water_b', 'wall_top', 'wall_face', 'hedge', 'wood', 'sand', 'grass_dark', 'dirt_v', 'shadow',
    'flowers_red', 'flowers_blue', 'pebbles', 'tuft', 'sign', 'crate', 'barrel', 'fence_h', 'fence_v', 'bush', 'mushroom', 'stump', 'lantern_g', 'rock', 'bench', 'puddle',
    'arch_l', 'arch_m', 'arch_r', 'hedge_over', 'vine', 'banner', 'portal_a', 'portal_b'];
  const T = {}; TILE_NAMES.forEach((n, i) => { T[n] = i + 1; });          // 名 → gid
  const PROP_NAMES = ['tree_a', 'tree_b', 'house_a', 'house_b', 'hall', 'lamp', 'well'];
  const PROP_FIRSTGID = 101;
  const PROP_DEFS = {   // w,h＝像素；foot＝碰撞腳印 [dx,dy,w,h]（圖塊，相對左下角圖塊；dy 向上為負）；door＝門口圖塊 [dx,dy]（相對左下角，+1＝前面一格）；lights＝[px,py,radius,kind]（相對圖左上角）
    tree_a: { w: 32, h: 48, foot: [0, 0, 2, 1] }, tree_b: { w: 32, h: 40, foot: [0, 0, 2, 1] },
    house_a: { w: 80, h: 72, foot: [0, -2, 5, 3], door: [2, 1], lights: [[14, 48, 34, 'window'], [63, 48, 34, 'window']] },
    house_b: { w: 64, h: 64, foot: [0, -2, 4, 3], door: [1, 1], lights: [[12, 40, 30, 'window'], [51, 40, 30, 'window']] },
    hall: { w: 96, h: 80, foot: [0, -2, 6, 3], door: [2, 1], lights: [[16, 56, 40, 'window'], [79, 56, 40, 'window'], [48, 40, 36, 'banner']] },
    lamp: { w: 16, h: 32, foot: [0, 0, 1, 1], lights: [[8, 7, 76, 'lamp']] },
    well: { w: 32, h: 32, foot: [0, -1, 2, 2] }
  };
  function hash2(x, y, k) { let h = (Math.imul(x + 374761393, 668265263) ^ Math.imul(y + 1274126177, 2246822519) ^ Math.imul(k + 97, 3266489917)) >>> 0; h = Math.imul(h ^ (h >>> 15), 2246822519) >>> 0; h = Math.imul(h ^ (h >>> 13), 3266489917) >>> 0; return ((h ^ (h >>> 16)) >>> 0) / 4294967296; }

  function Builder(w, h, name, tod) {
    const L = n => new Array(w * h).fill(0);
    const b = { w, h, name, ground: L(), decor: L(), occ: L(), coll: L(), props: [], npcs: [], portals: [], lights: [], spawns: [], encounters: [], signs: [], nextId: 1 };
    b.set = (layer, x, y, gid) => { if (x >= 0 && y >= 0 && x < w && y < h) b[layer][y * w + x] = gid; };
    b.get = (layer, x, y) => (x >= 0 && y >= 0 && x < w && y < h ? b[layer][y * w + x] : 0);
    b.block = (x, y, ww, hh) => { for (let j = 0; j < (hh || 1); j++) for (let i = 0; i < (ww || 1); i++) b.set('coll', x + i, y + j, 1); };
    b.fill = (layer, x, y, ww, hh, gid) => { for (let j = 0; j < hh; j++) for (let i = 0; i < ww; i++) b.set(layer, x + i, y + j, gid); };
    b.prop = (name, bx, by) => {   // bx,by＝左下角圖塊；加碰撞腳印
      const d = PROP_DEFS[name]; b.props.push({ name, bx, by });
      b.block(bx + d.foot[0], by + d.foot[1], d.foot[2], d.foot[3]);
      (d.lights || []).forEach(l => b.lights.push({ x: bx * TILE + l[0], y: (by + 1) * TILE - d.h + l[1], r: l[2], kind: l[3] }));
      if (d.door) b.doors = (b.doors || []).concat([{ x: bx + d.door[0], y: by + d.door[1], prop: name }]);
    };
    return b;
  }
  function paintGrass(b) { for (let y = 0; y < b.h; y++) for (let x = 0; x < b.w; x++) { const r = hash2(x, y, 1); b.set('ground', x, y, r < 0.55 ? T.grass_a : r < 0.8 ? T.grass_b : r < 0.92 ? T.grass_c : T.grass_dark); } }
  function scatter(b, density) {
    for (let y = 0; y < b.h; y++) for (let x = 0; x < b.w; x++) {
      if (b.get('coll', x, y) || b.get('decor', x, y)) continue; const gid = b.get('ground', x, y);
      if (gid !== T.grass_a && gid !== T.grass_b && gid !== T.grass_c && gid !== T.grass_dark) continue;
      const r = hash2(x, y, 2); if (r > density) continue; const k = hash2(x, y, 3);
      if (k < 0.3) b.set('decor', x, y, T.tuft); else if (k < 0.5) b.set('decor', x, y, T.flowers_red); else if (k < 0.7) b.set('decor', x, y, T.flowers_blue);
      else if (k < 0.82) b.set('decor', x, y, T.pebbles); else if (k < 0.9) { b.set('decor', x, y, T.bush); b.block(x, y); } else if (k < 0.95) b.set('decor', x, y, T.mushroom); else { b.set('decor', x, y, T.rock); b.block(x, y); }
    }
  }
  function sortProps(b) { b.props.sort((p, q) => p.by - q.by || p.bx - q.bx); }

  function generateTown() {
    const W = 40, H = 30, b = Builder(W, H, 'town_morningmoss');
    paintGrass(b);
    // 後牆（row0 牆頂、row1 牆面）＋北門缺口 x19–20
    for (let x = 0; x < W; x++) { b.set('ground', x, 0, T.wall_top); b.set('ground', x, 1, T.wall_face); b.block(x, 0, 1, 2); }
    // 東西兩側樹籬；東門缺口 y15–16
    for (let y = 2; y < H; y++) { b.set('ground', 0, y, T.hedge); b.block(0, y); if (y < 15 || y > 16) { b.set('ground', 39, y, T.hedge); b.block(39, y); } }
    // 主街（垂直 x19–20）＋橫街（y15–16）＋廣場
    for (let y = 0; y < H; y++) { b.set('ground', 19, y, T.cobble); b.set('ground', 20, y, T.cobble); }
    for (let x = 1; x < W; x++) { b.set('ground', x, 15, T.cobble); b.set('ground', x, 16, T.cobble); }
    b.fill('ground', 16, 12, 8, 6, T.plaza); b.fill('ground', 19, 12, 2, 6, T.cobble); b.fill('ground', 16, 15, 8, 2, T.cobble);
    for (let x = 18; x < 22; x++) b.set('ground', x, 0, T.cobble);
    // 北門：開口 x19–20（row0–1 變路面），拱門遮擋層 row1
    [[19, 0], [20, 0], [19, 1], [20, 1]].forEach(p => { b.set('ground', p[0], p[1], T.cobble); b.set('coll', p[0], p[1], 0); });
    b.set('occ', 18, 1, T.arch_l); b.set('occ', 19, 1, T.arch_m); b.set('occ', 20, 1, T.arch_m); b.set('occ', 21, 1, T.arch_r);
    // 池塘（西南）＋沙邊
    for (let y = 20; y <= 27; y++) for (let x = 3; x <= 11; x++) { const dx = (x - 7) / 4.6, dy = (y - 23.5) / 4.2, d = dx * dx + dy * dy; if (d < 0.62) { b.set('ground', x, y, (x + y) % 2 ? T.water : T.water_b); b.block(x, y); } else if (d < 1.0) b.set('ground', x, y, T.sand); }
    // 小橋（木板）過池
    for (let x = 4; x <= 10; x++) { b.set('ground', x, 23, T.wood); b.set('coll', x, 23, 0); }
    // 建築
    b.prop('house_a', 3, 9); b.prop('house_a', 11, 8); b.prop('hall', 26, 9); b.prop('house_b', 28, 26);
    b.prop('well', 14, 13);
    // 門口路面
    [[5, 10], [13, 9], [28, 10], [29, 10], [29, 27]].forEach(p => b.set('ground', p[0], p[1], T.dirt));
    for (let y = 10; y <= 14; y++) { b.set('ground', 5, y, T.dirt_v); } for (let y = 9; y <= 14; y++) b.set('ground', 13, y, T.dirt_v); for (let y = 10; y <= 14; y++) { b.set('ground', 28, y, T.dirt_v); b.set('ground', 29, y, T.dirt_v); }
    for (let y = 17; y <= 27; y++) b.set('ground', 29, y, T.dirt_v);
    // 路燈：主街兩側
    [4, 9, 13, 19, 24].forEach(y => { b.prop('lamp', 18, y); b.prop('lamp', 21, y); });
    // 樹
    [[1, 5, 'tree_a'], [1, 11, 'tree_b'], [2, 18, 'tree_a'], [1, 26, 'tree_b'], [36, 5, 'tree_a'], [37, 10, 'tree_b'], [35, 21, 'tree_a'], [37, 25, 'tree_b'], [33, 14, 'tree_a'], [23, 5, 'tree_b'], [16, 5, 'tree_a'], [24, 22, 'tree_a'], [12, 26, 'tree_b'], [33, 28, 'tree_a'], [7, 17, 'tree_b'], [25, 27, 'tree_b']].forEach(t => {
      if (!b.get('coll', t[0], t[1]) && !b.get('coll', t[0] + 1, t[1])) b.prop(t[2], t[0], t[1]);
    });
    // 圍欄（南面）、告示牌、雜物
    for (let x = 12; x <= 17; x++) { b.set('decor', x, 28, T.fence_h); b.block(x, 28); }
    for (let x = 22; x <= 27; x++) { b.set('decor', x, 28, T.fence_h); b.block(x, 28); }
    [[17, 19, 'sign'], [22, 11, 'sign'], [27, 11, 'crate'], [31, 11, 'barrel'], [15, 11, 'bench'], [24, 13, 'bench']].forEach(a => { b.set('decor', a[0], a[1], T[a[2]]); b.block(a[0], a[1]); });
    [[17, 14], [22, 14], [17, 17], [22, 17]].forEach(a => { b.set('decor', a[0], a[1], T.lantern_g); b.block(a[0], a[1]); b.lights.push({ x: a[0] * TILE + 8, y: a[1] * TILE + 6, r: 50, kind: 'lantern' }); });
    for (let x = 30; x <= 36; x++) b.set('decor', x, 8, T.flowers_red);
    b.set('decor', 38, 15, T.banner); b.set('decor', 38, 16, T.banner);
    scatter(b, 0.2);
    // 事件物件
    b.spawns.push({ name: 'start', x: 20, y: 22, dir: 'u' }, { name: 'from_route', x: 20, y: 2, dir: 'd' }, { name: 'from_arena', x: 37, y: 15, dir: 'l' });
    b.portals.push({ name: 'to_route', x: 19, y: 0, w: 2, h: 1, target: 'route_fernshade', spawn: 'from_town', glow: 'cool' }, { name: 'to_arena', x: 39, y: 15, w: 1, h: 2, target: 'arena_windback', spawn: 'from_town', glow: 'warm' });
    b.lights.push({ x: 20 * TILE, y: 0.5 * TILE, r: 56, kind: 'portal' }, { x: 39.5 * TILE, y: 16 * TILE, r: 56, kind: 'portal' });
    b.npcs.push({ name: 'npc_elder', display: '村長老鐘', sprite: 'char_elder', x: 22, y: 20, dir: 'l', dialog: 'dlg.elder.intro', patrol: [] },
      { name: 'npc_fern', display: '蕨生', sprite: 'char_fern', x: 13, y: 16, dir: 'r', dialog: 'dlg.fern.rival1', patrol: [[13, 16], [17, 16], [17, 20], [13, 20]] },
      { name: 'npc_clerk', display: '報名處職員', sprite: 'char_clerk', x: 28, y: 11, dir: 'd', dialog: 'dlg.clerk.register', patrol: [] });
    b.signs.push({ name: 'sign_square', x: 17, y: 19, text: 'sign.square' }, { name: 'sign_hall', x: 22, y: 11, text: 'sign.hall' });
    sortProps(b); return b;
  }
  function generateRoute() {
    const W = 48, H = 16, b = Builder(W, H, 'route_fernshade');
    paintGrass(b);
    for (let x = 0; x < W; x++) { b.set('ground', x, 0, T.hedge); b.block(x, 0); b.set('ground', x, 15, T.hedge); b.block(x, 15); }
    for (let x = 0; x < W; x++) { const y = 7 + Math.round(1.5 * Math.sin(x * 0.28)); b.set('ground', x, y, T.dirt); b.set('ground', x, y + 1, T.dirt); }
    for (let x = 4; x < 44; x += 3) for (const k of [0, 1]) { const y = k ? 11 + Math.floor(hash2(x, 5, 9) * 3) : 2 + Math.floor(hash2(x, 6, 9) * 3); if (!b.get('coll', x, y) && !b.get('coll', x + 1, y)) b.prop(hash2(x, y, 4) > 0.5 ? 'tree_a' : 'tree_b', x, y); }
    // 草叢（結緣賽／遭遇區）
    b.fill('ground', 20, 3, 8, 3, T.grass_dark); b.encounters.push({ name: 'bond_patch', x: 20, y: 3, w: 8, h: 3, table: 'route_fernshade.bond' });
    for (let x = 20; x < 28; x++) for (let y = 3; y < 6; y++) { b.set('coll', x, y, 0); b.set('decor', x, y, hash2(x, y, 8) > 0.5 ? T.tuft : T.flowers_blue); }
    scatter(b, 0.14);
    b.spawns.push({ name: 'from_town', x: 1, y: 7, dir: 'r' });
    b.portals.push({ name: 'to_town', x: 0, y: 7, w: 1, h: 3, target: 'town_morningmoss', spawn: 'from_route', glow: 'warm' });
    b.lights.push({ x: 8, y: 8 * TILE, r: 56, kind: 'portal' });
    b.npcs.push({ name: 'npc_wildling', display: '野靈（結緣）', sprite: 'char_fern', x: 24, y: 4, dir: 'd', dialog: 'dlg.route.wild', patrol: [] });
    sortProps(b); return b;
  }

  // ---------- Tiled JSON ----------
  function toTiled(b, tod) {
    let lid = 1, oid = 1;
    const tl = (name, data) => ({ id: lid++, name, type: 'tilelayer', x: 0, y: 0, width: b.w, height: b.h, opacity: 1, visible: true, data: data.slice() });
    const prop = (name, type, value) => ({ name, type, value });
    const og = (name, objs) => ({ id: lid++, name, type: 'objectgroup', draworder: 'topdown', opacity: 1, visible: true, x: 0, y: 0, objects: objs });
    const layers = [tl('ground', b.ground), tl('decor', b.decor), tl('occlusion', b.occ), tl('collision', b.coll)];
    layers.push(og('props', b.props.map(p => ({ id: oid++, name: p.name, type: 'prop', x: p.bx * TILE, y: (p.by + 1) * TILE, width: PROP_DEFS[p.name].w, height: PROP_DEFS[p.name].h, rotation: 0, visible: true, gid: PROP_FIRSTGID + PROP_NAMES.indexOf(p.name) }))));
    layers.push(og('npcs', b.npcs.map(n => ({ id: oid++, name: n.name, type: 'npc', x: n.x * TILE, y: n.y * TILE, width: TILE, height: TILE, rotation: 0, visible: true, properties: [prop('display', 'string', n.display), prop('sprite', 'string', n.sprite), prop('dir', 'string', n.dir), prop('dialog', 'string', n.dialog), prop('patrol', 'string', n.patrol.map(p => p[0] + ',' + p[1]).join(';'))] }))));
    layers.push(og('portals', b.portals.map(p => ({ id: oid++, name: p.name, type: 'portal', x: p.x * TILE, y: p.y * TILE, width: p.w * TILE, height: p.h * TILE, rotation: 0, visible: true, properties: [prop('target', 'string', p.target), prop('spawn', 'string', p.spawn), prop('glow', 'string', p.glow)] }))));
    layers.push(og('lights', b.lights.map(l => ({ id: oid++, name: l.kind, type: 'light', x: l.x, y: l.y, width: 0, height: 0, point: true, rotation: 0, visible: true, properties: [prop('radius', 'int', l.r), prop('kind', 'string', l.kind)] }))));
    layers.push(og('spawns', b.spawns.map(s => ({ id: oid++, name: s.name, type: 'spawn', x: s.x * TILE + 8, y: s.y * TILE + 8, width: 0, height: 0, point: true, rotation: 0, visible: true, properties: [prop('dir', 'string', s.dir)] }))));
    layers.push(og('events', (b.doors || []).map(d => ({ id: oid++, name: 'door_' + d.prop, type: 'door', x: d.x * TILE, y: d.y * TILE, width: TILE, height: TILE, rotation: 0, visible: true, properties: [prop('building', 'string', d.prop)] }))
      .concat(b.signs.map(s => ({ id: oid++, name: s.name, type: 'sign', x: s.x * TILE, y: s.y * TILE, width: TILE, height: TILE, rotation: 0, visible: true, properties: [prop('text', 'string', s.text)] })))
      .concat(b.encounters.map(e => ({ id: oid++, name: e.name, type: 'encounter', x: e.x * TILE, y: e.y * TILE, width: e.w * TILE, height: e.h * TILE, rotation: 0, visible: true, properties: [prop('table', 'string', e.table)] })))));
    return {
      type: 'map', version: '1.10', tiledversion: '1.11.0', orientation: 'orthogonal', renderorder: 'right-down', infinite: false, compressionlevel: -1,
      width: b.w, height: b.h, tilewidth: TILE, tileheight: TILE, nextlayerid: lid, nextobjectid: oid,
      properties: [prop('name', 'string', b.name), prop('tod', 'string', tod || 'night')],
      tilesets: [
        { firstgid: 1, name: 'town_tiles', image: 'town_tiles.png', imagewidth: 256, imageheight: 48, tilewidth: TILE, tileheight: TILE, tilecount: TILE_NAMES.length, columns: 16, margin: 0, spacing: 0 },
        { firstgid: PROP_FIRSTGID, name: 'props', columns: 0, tilewidth: 0, tileheight: 0, tilecount: PROP_NAMES.length, tiles: PROP_NAMES.map((n, i) => ({ id: i, image: 'props/' + n + '.png', imagewidth: PROP_DEFS[n].w, imageheight: PROP_DEFS[n].h })) }
      ],
      layers
    };
  }

  // ---------- 格子碰撞＋尋路（輸入：Tiled map JSON）----------
  function layerOf(map, name) { return map.layers.find(l => l.name === name); }
  function buildGrid(map) {
    const w = map.width, h = map.height, coll = layerOf(map, 'collision').data, blocked = new Uint8Array(w * h);
    for (let i = 0; i < w * h; i++) blocked[i] = coll[i] ? 1 : 0;
    return { w, h, blocked, isBlocked(x, y) { return x < 0 || y < 0 || x >= w || y >= h || blocked[y * w + x] === 1; } };
  }
  class Heap { constructor() { this.a = []; } push(n) { const a = this.a; a.push(n); let i = a.length - 1; while (i > 0) { const p = (i - 1) >> 1; if (a[p].f <= a[i].f) break; [a[p], a[i]] = [a[i], a[p]]; i = p; } } pop() { const a = this.a, t = a[0], l = a.pop(); if (a.length) { a[0] = l; let i = 0; for (;;) { let m = i; const L = 2 * i + 1, R = L + 1; if (L < a.length && a[L].f < a[m].f) m = L; if (R < a.length && a[R].f < a[m].f) m = R; if (m === i) break; [a[m], a[i]] = [a[i], a[m]]; i = m; } } return t; } get size() { return this.a.length; } }
  const SQ2 = Math.SQRT2, DIRS8 = [[1, 0, 1], [-1, 0, 1], [0, 1, 1], [0, -1, 1], [1, 1, SQ2], [1, -1, SQ2], [-1, 1, SQ2], [-1, -1, SQ2]];
  function astar(grid, sx, sy, tx, ty, opt) {   // 8 向、唔准切角、八分距離啟發；回傳 [[x,y]...]（含起點終點）或 null
    opt = opt || {}; const diag = opt.diag !== false, w = grid.w;
    if (grid.isBlocked(tx, ty) || grid.isBlocked(sx, sy)) return null;
    if (sx === tx && sy === ty) return [[sx, sy]];
    const N = w * grid.h, gS = new Float32Array(N).fill(Infinity), from = new Int32Array(N).fill(-1), closed = new Uint8Array(N), open = new Heap();
    const hf = (x, y) => { const dx = Math.abs(x - tx), dy = Math.abs(y - ty); return diag ? (dx + dy) + (SQ2 - 2) * Math.min(dx, dy) : dx + dy; };
    const s = sy * w + sx; gS[s] = 0; open.push({ i: s, f: hf(sx, sy) }); let expanded = 0;
    while (open.size) {
      const cur = open.pop(); if (closed[cur.i]) continue; closed[cur.i] = 1; expanded++;
      const cx = cur.i % w, cy = (cur.i / w) | 0;
      if (cx === tx && cy === ty) { const path = []; for (let i = cur.i; i !== -1; i = from[i]) path.push([i % w, (i / w) | 0]); path.reverse(); path.expanded = expanded; return path; }
      for (let d = 0; d < (diag ? 8 : 4); d++) {
        const dx = DIRS8[d][0], dy = DIRS8[d][1], nx = cx + dx, ny = cy + dy;
        if (grid.isBlocked(nx, ny)) continue; if (dx && dy && (grid.isBlocked(cx + dx, cy) || grid.isBlocked(cx, cy + dy))) continue;
        const ni = ny * w + nx; if (closed[ni]) continue; const ng = gS[cur.i] + DIRS8[d][2];
        if (ng < gS[ni]) { gS[ni] = ng; from[ni] = cur.i; open.push({ i: ni, f: ng + hf(nx, ny) }); }
      }
    }
    return null;
  }
  function lineClear(grid, x0, y0, x1, y1) {   // 兩個圖塊中心之間直線是否穿過障礙（取樣；半徑＝0.35 格，令碰撞盒唔擦牆）
    const dx = x1 - x0, dy = y1 - y0, n = Math.max(1, Math.ceil(Math.hypot(dx, dy) * 4)), r = 0.35;
    for (let i = 0; i <= n; i++) { const x = x0 + dx * i / n + 0.5, y = y0 + dy * i / n + 0.5; for (const o of [[-r, -r], [r, -r], [-r, r], [r, r]]) if (grid.isBlocked(Math.floor(x + o[0]), Math.floor(y + o[1]))) return false; }
    return true;
  }
  function smoothPath(grid, path) {            // 拉直（string pulling）：減少轉折，行路更自然
    if (!path || path.length < 3) return path; const out = [path[0]]; let a = 0;
    while (a < path.length - 1) { let b = path.length - 1; while (b > a + 1 && !lineClear(grid, path[a][0], path[a][1], path[b][0], path[b][1])) b--; out.push(path[b]); a = b; }
    return out;
  }
  function nearestWalkable(grid, tx, ty, maxR) {   // 點擊容錯：點到障礙時，搵最近可行格（半徑 ≤ maxR）
    if (!grid.isBlocked(tx, ty)) return [tx, ty]; let best = null, bd = 1e9;
    for (let r = 1; r <= (maxR || 3); r++) { for (let dy = -r; dy <= r; dy++) for (let dx = -r; dx <= r; dx++) { if (Math.max(Math.abs(dx), Math.abs(dy)) !== r) continue; if (!grid.isBlocked(tx + dx, ty + dy)) { const d = dx * dx + dy * dy; if (d < bd) { bd = d; best = [tx + dx, ty + dy]; } } } if (best) return best; }
    return null;
  }
  // 碰撞盒移動：腳下 box（halfW×halfH，px），逐軸解析，回傳新位置
  function moveBox(grid, x, y, dx, dy, hw, hh) {
    function hit(px, py) { const x0 = Math.floor((px - hw) / TILE), x1 = Math.floor((px + hw - 0.001) / TILE), y0 = Math.floor((py - hh) / TILE), y1 = Math.floor((py + hh - 0.001) / TILE); for (let j = y0; j <= y1; j++) for (let i = x0; i <= x1; i++) if (grid.isBlocked(i, j)) return true; return false; }
    let nx = x, ny = y; if (dx && !hit(x + dx, y)) nx = x + dx; if (dy && !hit(nx, y + dy)) ny = y + dy; return [nx, ny];
  }

  const api = { TILE, TILE_NAMES, T, PROP_NAMES, PROP_FIRSTGID, PROP_DEFS, generateTown, generateRoute, toTiled, buildGrid, astar, smoothPath, nearestWalkable, moveBox, lineClear, layerOf, hash2,
    buildMaps(tod) { return { town_morningmoss: toTiled(generateTown(), tod), route_fernshade: toTiled(generateRoute(), tod) }; } };
  g.WR = g.WR || {}; g.WR.TownMap = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
