// node tests/tiled-compat.test.js —— Tiled JSON 相容性：corner／batch2 town／遊策生成圖。collision firstgid 一律讀 tilemap 內 tilesets，唔寫死。
const assert = require('assert'), fs = require('fs'), path = require('path');
const T = require('../src/tiled.js'), TM = require('../src/town-map.js'); const ROOT = path.join(__dirname, '..');
let n = 0; const ok = (c, m) => { assert(c, m); n++; }; const log = [];
const rj = p => JSON.parse(fs.readFileSync(path.join(ROOT, p), 'utf8'));
const pngSize = p => { const b = fs.readFileSync(path.join(ROOT, p)); return [b.readUInt32BE(16), b.readUInt32BE(20)]; };
function load(mp) {
  const map = rj(mp), dir = path.dirname(mp), loaded = {};
  for (const t of map.tilesets) if (t.source) loaded[t.source] = rj(path.join(dir, t.source));
  const sets = T.resolve(map, loaded), dec = T.decode(map, sets);
  const res = T.check(map, { loaded, mapPath: mp, files: p => fs.existsSync(path.join(ROOT, dir, p)) || fs.existsSync(path.join(ROOT, p)), imageSize: p => { try { return pngSize(path.join(dir, p)); } catch (e) { return null; } } });
  return { map, sets, dec, res, dir };
}
const cases = [['corner（舊 firstgid 193）', 'art/tiles/morningmoss/tilemap_corner.json', 193, 'corner'], ['batch2 town（40×30，firstgid 545）', 'art/tiles/morningmoss/tilemap_town.json', 545, 'town'],
  ['遊策生成 town', 'art/adventure/town_morningmoss.json', 193, 'adv'], ['遊策生成 arena', 'art/adventure/arena_windrun.json', 193, 'adv'], ['遊策生成 trail', 'art/adventure/trail_fernshadow.json', 193, 'adv']];
for (const [label, mp, fg, kind] of cases) {
  const c = load(mp), colSet = c.sets.find(t => t.name === 'collision');
  ok(colSet, label + ' 有 collision tileset'); ok(colSet.firstgid === fg, label + ' collision firstgid 由 tilemap 讀出＝' + colSet.firstgid + '（預期 ' + fg + '）');
  ok(c.res.errors.length === 0, label + ' check 無 error：' + c.res.errors.map(e => e.code + ' ' + e.msg).join(' | '));
  const vals = new Set(c.dec.collision); for (const v of vals) ok(v >= 0 && v <= 4, label + ' collision 解碼值 0..4（' + [...vals] + '）');
  ok(c.dec.collision.length === c.map.width * c.map.height, label + ' collision 尺寸');
  // 同一份 collision 數據用「錯誤」firstgid 解碼會唔同＝證明讀 tilemap 而唔係寫死
  if (fg !== 193) { const wrong = c.dec.layers.collision.gids.reduce((a, g) => a + (g && g - 192 > 4 ? 1 : 0), 0); ok(wrong > 0, label + ' 若寫死 193 會有 ' + wrong + ' 格越界值'); }
  // 所有 gid 落喺某 tileset（flip bits 先剝除）
  for (const [ln, L] of Object.entries(c.dec.layers)) { if (ln === 'collision') continue; for (const g of L.gids) if (g) ok(T.tilesetFor(c.sets, g), label + ' ' + ln + ' gid ' + g + ' 屬於某 tileset'); }
  log.push(label + '：W×H ' + c.map.width + '×' + c.map.height + '；tilesets ' + c.sets.map(t => t.name + '@' + t.firstgid).join(', ') + '；error ' + c.res.errors.length + '／warning ' + c.res.warnings.length + (c.res.warnings.length ? '（' + [...new Set(c.res.warnings.map(w => w.code))].join(',') + '）' : ''));
}
// batch2 專項
{
  const c = load('art/tiles/morningmoss/tilemap_town.json'), d = c.dec, W = d.w, H = d.h, col = d.collision;
  ok(W === 40 && H === 30, '40×30'); ok(c.map.tilesets.length >= 3, 'tilesets ≥3（b2＋landmarks＋collision）');
  const cnt = [0, 0, 0, 0, 0]; for (const v of col) cnt[v]++; ok(cnt[1] > 0 && cnt[2] > 0 && cnt[4] >= 0, '有 block／water 格'); log.push('batch2 collision 值分佈 walk/block/water/trigger/slow＝' + cnt.join('/'));
  // 屋頂喺 occlusion 層、sort_y 有限（有實體基座）或 Infinity（無）：統計
  const occ = d.layers.occlusion; ok(occ, '有 occlusion 層'); const sy = T.occlusionSort(W, H, occ.gids, col, 16); let fin = 0, inf = 0; for (let i = 0; i < W * H; i++) if (occ.gids[i]) { if (isFinite(sy[i])) fin++; else inf++; } ok(fin + inf > 0, 'occlusion 有 tile'); log.push('batch2 occlusion tiles ' + (fin + inf) + '：sort_y 有限 ' + fin + '／Infinity ' + inf);
  // 溝＋木橋
  const grid = { w: W, h: H, isBlocked: (x, y) => x < 0 || y < 0 || x >= W || y >= H || col[y * W + x] === 1 || col[y * W + x] === 2 };
  const bridge = [[19, 27], [20, 27], [21, 27]]; for (const b of bridge) ok(!grid.isBlocked(b[0], b[1]), '木橋格 ' + b + ' 可行走'); 
  const water = []; for (let x = 0; x < W; x++) if (col[27 * W + x] === 2) water.push(x); ok(water.length > 0, '溝（row27）有 water 格 ' + water); for (const x of water) ok(grid.isBlocked(x, 27), '溝格 (' + x + ',27) 阻擋');
  const sp = d.events.filter(e => e.type === 'spawn'); ok(sp.length >= 1, '有 spawn'); const s0 = sp.find(e => e.name === 'spawn_start') || sp[0], st = [s0.tx, s0.ty];
  ok(!grid.isBlocked(st[0], st[1]), 'spawn 可行'); const dy = []; for (let y = 0; y < H; y++) if (col[y * W + 20] === 2) dy.push(y);
  // 全 events 可達（warp／npc／interact：本格或四鄰格）
  let un = [], tot = 0; for (const e of d.events) { if (!['warp', 'npc_spawn', 'interact', 'trigger'].includes(e.type)) continue; tot++; let r = false; for (let j = -1; j <= e.th && !r; j++) for (let i = -1; i <= e.tw && !r; i++) { const x = e.tx + i, y = e.ty + j; if (!grid.isBlocked(x, y) && TM.astar(grid, st[0], st[1], x, y)) r = true; } if (!r) un.push(e.name); }
  ok(un.length === 0, 'spawn 可達全部 ' + tot + ' 個 warp／npc／interact／trigger（不可達：' + un + '）'); log.push('batch2 events ' + d.events.length + '（可達性檢查對象 ' + tot + '，不可達 ' + un.length + '）');
  // 封橋後繞路
  const blocked = Object.assign({}, grid, { isBlocked: (x, y) => grid.isBlocked(x, y) || (y === 27 && x >= 19 && x <= 21) }); const south = d.events.find(e => e.type === 'warp' && e.ty >= 25) || null;
  const pOpen = TM.astar(grid, st[0], st[1], 20, 28), pShut = TM.astar(blocked, st[0], st[1], 20, 28); ok(pOpen, '開橋可達溝南 (20,28)'); log.push('封橋後溝南 (20,28) ' + (pShut ? '仍可繞路（路徑 ' + pShut.length + ' 格，通橋 ' + pOpen.length + ' 格）' : '不可達＝木橋係唯一過溝路徑') + (south ? '' : ''));
  // 動畫 tile／lit 對
  const lm = c.sets.find(t => /landmark/i.test(t.name || t.source || '')); ok(lm, '有 landmarks tileset');
  const anim = c.sets.reduce((a, t) => a + Object.keys(t.anim).length, 0); ok(anim > 0, '有動畫 tile ' + anim);
  const ex = T.props(c.map); log.push('batch2 map 屬性：' + JSON.stringify(ex).slice(0, 200) + '；動畫 tile ' + anim);
  // 門／NPC
  const dr = d.events.find(e => e.name === 'door_registry'); ok(dr && /arena_windrun/.test(JSON.stringify(dr.props)), 'door_registry → arena_windrun：' + JSON.stringify(dr && dr.props).slice(0, 120));
  const nr = d.events.find(e => e.name === 'npc_registry'); ok(nr && nr.tx === 32 && nr.ty === 9, 'npc_registry 在 (32,9)'); ok(!grid.isBlocked(32, 9), 'npc_registry 站位格本身 collision=0'); 
  const ne = d.events.find(e => e.name === 'npc_elder'); ok(ne && /老鐘/.test(JSON.stringify(ne.props)), 'npc_elder 正名老鐘');
}
console.log(log.join('\n')); console.log('tiled-compat: ' + n + ' assertions OK');
