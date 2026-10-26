// node tests/town-map.test.js —— 地圖結構／碰撞／A*／傳送可達性
const assert = require('assert'), fs = require('fs'), path = require('path');
const TM = require('../src/town-map.js');
let n = 0; const ok = (c, m) => { assert(c, m); n++; };
const maps = TM.buildMaps('night');
for (const id of Object.keys(maps)) {
  const m = maps[id], grid = TM.buildGrid(m), L = nm => m.layers.find(l => l.name === nm), O = nm => L(nm).objects;
  ok(m.tilewidth === 16 && m.orientation === 'orthogonal', id + ' 格式');
  for (const nm of ['ground', 'decor', 'occlusion', 'collision']) ok(L(nm).type === 'tilelayer' && L(nm).data.length === m.width * m.height, id + ' ' + nm + ' 尺寸');
  for (const nm of ['props', 'npcs', 'portals', 'lights', 'spawns', 'events']) ok(L(nm).type === 'objectgroup', id + ' ' + nm);
  // gid 範圍
  const maxT = TM.TILE_NAMES.length; for (const nm of ['ground', 'decor', 'occlusion']) for (const g of L(nm).data) ok(g >= 0 && g <= maxT, id + ' gid');
  for (const o of O('props')) ok(o.gid >= TM.PROP_FIRSTGID && o.gid < TM.PROP_FIRSTGID + TM.PROP_NAMES.length, 'prop gid');
  // 全圖地面層不可有空格（地面一定鋪滿）
  ok(L('ground').data.every(g => g > 0), id + ' ground 鋪滿');
  // 出生點可行；入口連通
  const sp = O('spawns'); ok(sp.length >= 1, id + ' 有出生點');
  const tile = o => [Math.floor(o.x / 16), Math.floor(o.y / 16)];
  sp.forEach(s => { const t = tile(s); ok(!grid.isBlocked(t[0], t[1]), id + ' 出生點 ' + s.name + ' 可行'); });
  const start = tile(sp[0]);
  // 所有傳送點、NPC 旁、門口都可從出生點抵達
  for (const p of O('portals')) { let found = false; for (let j = 0; j < p.height / 16 && !found; j++) for (let i = 0; i < p.width / 16; i++) { const t = [p.x / 16 + i, p.y / 16 + j]; if (!grid.isBlocked(t[0], t[1]) && TM.astar(grid, start[0], start[1], t[0], t[1])) { found = true; break; } } ok(found, id + ' 傳送點 ' + p.name + ' 可達'); }
  for (const e of O('events').filter(e => e.type === 'door')) { const t = tile(e); ok(!grid.isBlocked(t[0], t[1]), id + ' 門口可行'); ok(TM.astar(grid, start[0], start[1], t[0], t[1]), id + ' 門口可達'); }
  for (const np of O('npcs')) { const t = tile(np); ok(!grid.isBlocked(t[0], t[1]), id + ' NPC ' + np.name + ' 站位可行'); ok(TM.astar(grid, start[0], start[1], t[0], t[1]), id + ' NPC 可達'); }
  // 傳送目標存在（除 arena 外，標記為待接入）
  for (const p of O('portals')) { const tg = p.properties.find(q => q.name === 'target').value, sn = p.properties.find(q => q.name === 'spawn').value; if (maps[tg]) ok(maps[tg].layers.find(l => l.name === 'spawns').objects.some(s => s.name === sn), '目標出生點存在'); else ok(tg === 'arena_windback', '未知目標 ' + tg); }
  // A*：隨機對測——最短路徑長度對比 4 向 BFS（8 向路徑成本 ≤ 4 向）、路徑每步可行、無切角
  let seed = 7; const rnd = () => (seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0) / 4294967296; const free = []; for (let y = 0; y < grid.h; y++) for (let x = 0; x < grid.w; x++) if (!grid.isBlocked(x, y)) free.push([x, y]);
  let tested = 0, reach = 0;
  for (let i = 0; i < 300; i++) {
    const a = free[rnd() * free.length | 0], b = free[rnd() * free.length | 0]; const p8 = TM.astar(grid, a[0], a[1], b[0], b[1]), p4 = TM.astar(grid, a[0], a[1], b[0], b[1], { diag: false });
    ok((p8 === null) === (p4 === null), '可達性一致'); if (!p8) continue; reach++;
    const cost = p => { let c = 0; for (let k = 1; k < p.length; k++) c += Math.hypot(p[k][0] - p[k - 1][0], p[k][1] - p[k - 1][1]); return c; };
    ok(cost(p8) <= cost(p4) + 1e-6, '8 向不長於 4 向');
    for (let k = 0; k < p8.length; k++) { ok(!grid.isBlocked(p8[k][0], p8[k][1]), '路徑格可行'); if (k) { const dx = p8[k][0] - p8[k - 1][0], dy = p8[k][1] - p8[k - 1][1]; ok(Math.abs(dx) <= 1 && Math.abs(dy) <= 1, '步長'); if (dx && dy) ok(!grid.isBlocked(p8[k - 1][0] + dx, p8[k - 1][1]) && !grid.isBlocked(p8[k - 1][0], p8[k - 1][1] + dy), '唔切角'); } }
    const sm = TM.smoothPath(grid, p8); ok(sm[0][0] === a[0] && sm[sm.length - 1][0] === b[0] && sm.length <= p8.length, '拉直保持端點'); tested++;
    // 拉直後每段取樣不穿牆
    for (let k = 1; k < sm.length; k++) ok(TM.lineClear(grid, sm[k - 1][0], sm[k - 1][1], sm[k][0], sm[k][1]), '拉直段可行');
  }
  ok(reach > 250, id + ' 大部分隨機對可達（' + reach + '）');
  // 障礙 → null；容錯
  const blk = (() => { for (let y = 0; y < grid.h; y++) for (let x = 0; x < grid.w; x++) if (grid.isBlocked(x, y) && x > 0 && y > 0 && x < grid.w - 1) return [x, y]; })();
  ok(TM.astar(grid, start[0], start[1], blk[0], blk[1]) === null, '目標為障礙→null');
  const nw = TM.nearestWalkable(grid, blk[0], blk[1], 3); ok(nw === null || !grid.isBlocked(nw[0], nw[1]), '最近可行格');
  // moveBox：牆前停住、斜走滑行
  const s = start, cx = s[0] * 16 + 8, cy = s[1] * 16 + 8; let x = cx, y = cy; for (let i = 0; i < 4000; i++) { [x, y] = TM.moveBox(grid, x, y, 1, 0, 5, 3); } ok(x < grid.w * 16, '碰撞盒唔出界'); ok(!grid.isBlocked(Math.floor((x + 4) / 16), Math.floor(y / 16)), '碰撞盒停喺牆前');
  // JSON 檔同生成一致
  const f = path.join(__dirname, '../art/town/' + id + '.json'); if (fs.existsSync(f)) ok(JSON.stringify(JSON.parse(fs.readFileSync(f, 'utf8'))) === JSON.stringify(m), id + '.json 同生成器一致（重跑 tools/gen-town-json.js）');
  console.log(id, '通過；隨機尋路對', tested, '；可行格', free.length);
}
// 決定論：同一輸入同一輸出
ok(JSON.stringify(TM.buildMaps('night')) === JSON.stringify(TM.buildMaps('night')), '生成器決定論');

// ---- batch2（遊美 40×30）：以 tilemap 實際資料為準；collision firstgid 由 tilesets 讀出 ----
{
  const T = require('../src/tiled.js'), rj = f => JSON.parse(fs.readFileSync(path.join(__dirname, '..', f), 'utf8'));
  const mp = 'art/tiles/morningmoss/tilemap_town.json', map = rj(mp), loaded = {}; for (const t of map.tilesets) if (t.source) loaded[t.source] = rj('art/tiles/morningmoss/' + t.source);
  const sets = T.resolve(map, loaded), d = T.decode(map, sets), W = d.w, H = d.h, col = d.collision, cs = sets.find(t => t.name === 'collision');
  ok(cs.firstgid === 545, 'batch2 collision firstgid 讀自 tilemap＝' + cs.firstgid);
  const grid = { w: W, h: H, isBlocked: (x, y) => x < 0 || y < 0 || x >= W || y >= H || col[y * W + x] === 1 || col[y * W + x] === 2 };
  const ov = rj('data/overlay/town_morningmoss.json');
  for (const k of Object.keys(ov.arrive_by_var.map)) { const a = ov.arrive_by_var.map[k]; ok(!grid.isBlocked(a[0], a[1]), 'overlay 返鎮落點 ' + k + ' (' + a[0] + ',' + a[1] + ') 可行走'); }
  { const a = ov.arrive.trail_fernshadow; ok(!grid.isBlocked(a[0], a[1]), 'trail 返鎮落點 (' + a + ') 可行走'); }
  const sp = d.events.find(e => e.name === 'spawn_start') || d.events.find(e => e.type === 'spawn'); ok(sp, 'batch2 有 spawn');
  for (const nm of ['door_registry', 'door_arena', 'door_town', 'obj_well']) { const e = d.events.find(x => x.name === nm); if (!e) continue; let r = false; for (let j = -1; j <= e.th && !r; j++) for (let i = -1; i <= e.tw && !r; i++) if (!grid.isBlocked(e.tx + i, e.ty + j) && TM.astar(grid, sp.tx, sp.ty, e.tx + i, e.ty + j)) r = true; ok(r, nm + ' 可達'); }
  const nr = d.events.find(e => e.name === 'npc_registry'); ok(nr && [[0, 1], [-1, 0], [1, 0], [0, -1]].some(([a, b]) => !grid.isBlocked(nr.tx + a, nr.ty + b) && TM.astar(grid, sp.tx, sp.ty, nr.tx + a, nr.ty + b)), 'npc_registry 周邊有可達互動格');
  for (const x of [19, 20, 21]) ok(col[27 * W + x] === 0, '木橋 (' + x + ',27) collision=0'); ok(col[27 * W + 10] === 2 && col[27 * W + 22] === 2, '溝 collision=2');
  const occ = d.layers.occlusion, sy = T.occlusionSort(W, H, occ.gids, col, 16); let fin = 0; for (let i = 0; i < W * H; i++) if (occ.gids[i] && isFinite(sy[i])) fin++; ok(fin > 0, 'occlusion（屋頂／樹冠）sort_y 有限 ' + fin);
  const lm = sets.find(t => /landmark/.test(t.name)), ids = Object.keys(lm.byId).length; ok(Object.keys(lm.anim).length >= 4, 'landmarks 動畫 tile ≥4（旗／風標）');
  const nmj = rj('art/tiles/morningmoss/tileset_morningmoss_b2_names.json'); ok(!!nmj, 'b2 names 表存在');
  ok(fs.existsSync(path.join(__dirname, '..', 'art/tiles/morningmoss/tileset_morningmoss_b2_extruded.png')), 'b2 extruded 圖存在（引擎改用 extruded）');
}
console.log('town-map 測試通過，斷言', n);
