#!/usr/bin/env node
/* gen-adventure-maps.js — 由遊策 maps-and-events.md 嘅 ASCII 草圖＋事件表，產生三張 Tiled JSON（遊美 tileset 優先、缺嘅用 placeholder）。
   輸出：art/adventure/{town_morningmoss,arena_windrun,trail_fernshadow}.json ＋ art/adventure/MISSING_ASSETS.json
   用法：node tools/gen-adventure-maps.js        （確定性：同輸入同輸出；唔用隨機數）
   圖層（對齊 ASSET_SPEC_TOWN §C）：ground｜deco｜collision（gid 193＝1…）｜occlusion｜events（objectgroup）。
   遊策 §5 嘅 objects／occlude／lights 層：objects 併入 deco（碰撞入 collision）、occlude＝occlusion、lights 本版未生成。 */
'use strict';
const fs = require('fs'), path = require('path');
const ROOT = path.join(__dirname, '..'), OUT = path.join(ROOT, 'art/adventure');
const names = JSON.parse(fs.readFileSync(path.join(ROOT, 'art/tiles/morningmoss/tileset_morningmoss_names.json'), 'utf8')).names;
const phNames = JSON.parse(fs.readFileSync(path.join(OUT, 'tileset_placeholder_names.json'), 'utf8')).names;
const FG_ART = 1, FG_COL = 193, FG_PH = 197;
const missing = new Set();
const G = n => { if (names[n]) return names[n]; throw new Error('no art tile ' + n); };
const P = n => { if (phNames[n] === undefined) throw new Error('no ph tile ' + n); return FG_PH + phNames[n]; };
const h2 = (x, y, k) => { let h = (Math.imul(x + 374761393, 668265263) ^ Math.imul(y + 1274126177, 2246822519) ^ Math.imul(k + 97, 3266489917)) >>> 0; h = Math.imul(h ^ (h >>> 13), 1274126177) >>> 0; return ((h ^ (h >>> 16)) >>> 0) / 4294967296; };

// ---------- 解析 ASCII ----------
function parseAscii(md, sec) {
  const i = md.indexOf(sec); if (i < 0) throw new Error('section ' + sec);
  const a = md.indexOf('```', i), b = md.indexOf('```', a + 3), lines = md.slice(a + 3, b).split('\n').filter(l => /^ ?\d{1,2}  [^\d\s]/.test(l));
  return lines.map(l => l.replace(/^ ?\d{1,2}  /, ''));
}
const md = fs.readFileSync(path.join(ROOT, 'design/adventure-slice/maps-and-events.md'), 'utf8');
const ASC = { town_morningmoss: parseAscii(md, '## 2. 場景一'), arena_windrun: parseAscii(md, '## 3. 場景二'), trail_fernshadow: parseAscii(md, '## 4. 場景三') };
const DIM = { town_morningmoss: [40, 30], arena_windrun: [40, 15], trail_fernshadow: [60, 16] };
for (const k in ASC) { if (ASC[k].length !== DIM[k][1] || ASC[k].some(r => r.length !== DIM[k][0])) throw new Error('ascii dim ' + k + ' ' + ASC[k].length + 'x' + ASC[k][0].length); }

const SOLID = new Set('#YBMW~Cb G x s n i'.replace(/ /g, '').split(''));   // 靜態碰撞（G 另有條件開放）
const PLAZA = { x0: 17, x1: 23, y0: 12, y1: 16 };

function build(id) {
  const asc = ASC[id], [W, H] = DIM[id], ch = (x, y) => (x < 0 || y < 0 || x >= W || y >= H) ? null : asc[y][x];
  const L = { ground: new Array(W * H).fill(0), deco: new Array(W * H).fill(0), occlusion: new Array(W * H).fill(0), collision: new Array(W * H).fill(0) };
  const set = (l, x, y, g) => { if (x >= 0 && y >= 0 && x < W && y < H) L[l][y * W + x] = g; };
  const get = (l, x, y) => (x < 0 || y < 0 || x >= W || y >= H) ? 0 : L[l][y * W + x];
  const arena = id === 'arena_windrun', town = id === 'town_morningmoss';
  const inPlaza = (x, y) => town && x >= PLAZA.x0 && x <= PLAZA.x1 && y >= PLAZA.y0 && y <= PLAZA.y1;
  const hall = (x, y) => arena && x >= 1 && x <= 12 && y >= 2 && y <= 13;
  const tunnel = (x, y) => arena && x >= 14 && x <= 20 && y >= 7 && y <= 9;
  const isPathLike = (x, y) => { const c = ch(x, y); if (c === null) return true; if (inPlaza(x, y)) return true; return c === '=' || c === 'E' || c === 'P' || c === 'D'; };
  const isCobble = (x, y) => { const c = ch(x, y); if (c === null) return true; return inPlaza(x, y) || tunnel(x, y) || ((c === '=') && false); };
  const mask = (f, x, y) => (f(x, y - 1) ? 1 : 0) | (f(x + 1, y) ? 2 : 0) | (f(x, y + 1) ? 4 : 0) | (f(x - 1, y) ? 8 : 0);
  const mk = (p, m) => p + '_' + (m < 10 ? '0' : '') + m;

  // ---- ground ----
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
    const c = ch(x, y); let g;
    const grass = () => { const r = h2(x, y, 1); return G(r < 0.04 ? 'grass_dew' : r < 0.07 ? ['grass_flower_pink', 'grass_flower_yellow', 'grass_flower_violet'][(h2(x, y, 2) * 3) | 0] : ['grass_a', 'grass_b', 'grass_c', 'grass_d'][(h2(x, y, 3) * 4) | 0]); };
    if (c === '#') g = arena ? P('ph_wall_stone') : P('ph_rock');
    else if (hall(x, y)) g = P((x + y) % 2 ? 'ph_floor_b' : 'ph_floor_a');
    else if (tunnel(x, y) || inPlaza(x, y)) { const m = mask(isCobble, x, y); g = m === 15 ? G(['cobble_a', 'cobble_b', 'cobble_c', 'cobble_d'][(h2(x, y, 4) * 4) | 0]) : G(mk('cobble_edge', m)); }
    else if (c === '~') { const m = mask((a, b) => ch(a, b) === '~' || ch(a, b) === null, x, y); g = m === 15 ? G(h2(x, y, 5) < 0.5 ? 'water_a1' : 'water_b1') : G(mk('pond', m)); }
    else if (arena && x >= 21 && x <= 38 && y >= 2 && y <= 13) g = G(['dirt_a', 'dirt_b', 'dirt_c', 'dirt_d'][(h2(x, y, 6) * 4) | 0]);
    else if (!arena && (c === '=' || c === 'E' || c === 'P')) g = G(mk('path', mask(isPathLike, x, y)));
    else if (arena && c === 'D') g = P('ph_floor_a');
    else g = grass();
    set('ground', x, y, g);
  }
  // ---- 建築（B 連通塊）----
  const seen = new Uint8Array(W * H), blds = [];
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) if (ch(x, y) === 'B' && !seen[y * W + x]) {
    let x1 = x, y1 = y; while (ch(x1 + 1, y) === 'B') x1++; while (ch(x, y1 + 1) === 'B') y1++;
    for (let j = y; j <= y1; j++) for (let i = x; i <= x1; i++) seen[j * W + i] = 1; blds.push({ x0: x, y0: y, x1, y1 });
  }
  const doors = [];
  for (const b of blds) {
    const w = b.x1 - b.x0 + 1, h = b.y1 - b.y0 + 1, bottom = b.y1; if (h < 5) throw new Error('building too short ' + JSON.stringify(b));
    let dcol = -1; for (let i = b.x0; i <= b.x1; i++) if (ch(i, bottom) === 'D') dcol = i;
    const dx = dcol >= 0 ? (dcol + 1 <= b.x1 ? dcol : dcol - 1) : -1;     // 門 2 格闊：ASCII 只標 1 格 D → 向右擴張（右邊貼牆時向左）
    const side = (i) => i === b.x0 ? 'l' : i === b.x1 ? 'r' : 'm';
    for (let i = b.x0; i <= b.x1; i++) {
      const s = side(i), y = b.y0;
      set('deco', i, y, G('roof_top_' + s));
      for (let j = 0; j < h - 4; j++) { let n = 'roof_mid_' + s; if (s === 'm' && h2(i, y + j, 7) < 0.18) n = h2(i, y + j, 8) < 0.5 ? 'roof_mid_moss_a' : 'roof_mid_moss_b'; set('deco', i, y + 1 + j, G(n)); }
      set('deco', i, bottom - 2, G('roof_eave_' + s));
      const isDoor = dx >= 0 && (i === dx || i === dx + 1), win = !isDoor && s === 'm' && ((i - b.x0) % 2 === 1);
      set('deco', i, bottom - 1, isDoor ? G(i === dx ? 'door_00' : 'door_01') : win ? G(h2(i, bottom, 9) < 0.5 ? 'window_a_day' : 'window_b_day') : G(s === 'l' ? 'wall_upper_l' : s === 'r' ? 'wall_upper_r' : 'wall_upper'));
      set('deco', i, bottom, isDoor ? G(i === dx ? 'door_10' : 'door_11') : G(s === 'l' ? 'wall_lower_l' : s === 'r' ? 'wall_lower_r' : 'wall_lower'));
      for (let j = b.y0; j <= bottom; j++) set('collision', i, j, isDoor && j === bottom ? 0 : FG_COL);
    }
    if (dx >= 0) doors.push({ x: dx, y: bottom, w: 2, bld: b });
    if (w >= 6 && h >= 6) { const cx = b.x1 - 1; set('deco', cx, b.y0 + 1, G('chimney_base')); set('occlusion', cx, b.y0 - 1 < 0 ? 0 : b.y0 - 1, b.y0 - 1 < 0 ? 0 : G('chimney_top')); }
  }
  // ---- 樹（Y）----
  const Y = (x, y) => ch(x, y) === 'Y', treeCells = new Set();
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) if (Y(x, y)) {
    const par = x & 1 ? '1' : '0', below = Y(x, y + 1), above = Y(x, y - 1);
    const isolated = !Y(x - 1, y) && !Y(x + 1, y) && !below && !above;
    if (isolated && ch(x + 1, y) && ch(x + 1, y) !== '#' && ch(x + 1, y) !== 'B') {       // 單格樹：畫成 2 格闊（art 樹本身 2 格闊），右鄰格亦設碰撞
      set('deco', x, y, G('tree_small_20')); set('deco', x + 1, y, G('tree_small_21')); set('collision', x + 1, y, FG_COL); set('occlusion', x, y - 1, G('tree_small_10')); set('occlusion', x + 1, y - 1, G('tree_small_11')); set('occlusion', x, y - 2, G('tree_small_00')); set('occlusion', x + 1, y - 2, G('tree_small_01')); continue;
    }
    if (!below) { set('deco', x, y, G('tree_small_2' + par)); let k = 1; while (Y(x, y - k) && k <= 2) k++; const room = k - 1;
      if (room >= 1) set('deco', x, y - 1, G('tree_small_1' + par)); if (room >= 2) set('deco', x, y - 2, G('tree_small_0' + par));
      if (!above) { set('occlusion', x, y - 1, G('tree_small_1' + par)); if (y >= 2 && ch(x, y - 2) !== '#') set('occlusion', x, y - 2, G('tree_small_0' + par)); } }
    else if (!above) set('deco', x, y, G('tree_small_0' + par));
    else if (get('deco', x, y) === 0) set('deco', x, y, G('tree_small_1' + par));
  }
  // 垂直樹牆內部格：統一用 canopy 中段
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) if (Y(x, y) && get('deco', x, y) === 0) set('deco', x, y, G('tree_small_1' + (x & 1)));
  // ---- 其他物件／標記 ----
  const cellHas = (x, y) => get('deco', x, y) !== 0;
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
    const c = ch(x, y);
    if (c === 'M' && ch(x - 1, y) !== 'M' && ch(x, y - 1) !== 'M') { set('deco', x, y, P('ph_mill_00')); set('deco', x + 1, y, P('ph_mill_01')); set('deco', x, y + 1, P('ph_mill_10')); set('deco', x + 1, y + 1, P('ph_mill_11')); missing.add('windmill 2×2（含槳葉動畫）'); }
    if (c === 'W' && ch(x - 1, y) !== 'W' && ch(x, y - 1) !== 'W') { set('deco', x, y, P('ph_well_00')); set('deco', x + 1, y, P('ph_well_01')); set('deco', x, y + 1, P('ph_well_10')); set('deco', x + 1, y + 1, P('ph_well_11')); missing.add('水井 2×2'); }
    if (c === 'x' && ch(x - 1, y) !== 'x' && ch(x, y - 1) !== 'x') { set('deco', x, y, P('ph_log_00')); set('deco', x + 1, y, P('ph_log_01')); set('deco', x, y + 1, P('ph_log_10')); set('deco', x + 1, y + 1, P('ph_log_11')); missing.add('倒塌樹幹路障 2×2'); }
    if (c === 's') { set('deco', x, y, P('ph_sign')); missing.add('告示牌（單格）'); }
    if (c === 'n') { set('deco', x, y, P('ph_notice')); missing.add('告示板（單格；art 有 board_* 2×2 可替換）'); }
    if (c === 'i') { set('deco', x, y, P('ph_scout')); missing.add('情報位（M3 佔位）'); }
    if (c === 'C') { const l = ch(x - 1, y) === 'C', r = ch(x + 1, y) === 'C'; set('deco', x, y, P(!l ? 'ph_counter_l' : !r ? 'ph_counter_r' : 'ph_counter_m')); missing.add('報名櫃台'); }
    if (c === 'b') { const l = ch(x - 1, y) === 'b', r = ch(x + 1, y) === 'b'; set('deco', x, y, P(!l ? 'ph_bench_l' : !r ? 'ph_bench_r' : 'ph_bench_m')); missing.add('長凳／看台座位'); }
    if (c === 'G') { set('deco', x, y, P('ph_gate_closed')); missing.add('入場閘口（關／開兩態）'); }
    if (c === 'S') { set('deco', x, y, P('ph_startline')); missing.add('起跑線貼花'); }
    if (c === 'F') { set('deco', x, y, P('ph_formation')); missing.add('佈陣點貼花'); }
    if (c === 'r') { set('deco', x, y, P('ph_regmark')); missing.add('報名互動格貼花'); }
    if (c === 'E') { set('deco', x, y, P('ph_exit')); missing.add('場景出口標記'); }
    if (c === 'D' && arena) { set('deco', x, y, P('ph_door_plain')); missing.add('迴風場大廳外門（室內牆圖塊）'); }
    if (c === ',') { set('occlusion', x, y, G('tuft')); }
    if (SOLID.has(c) && !(c === 'B') && !(c === 'Y') && get('collision', x, y) === 0) set('collision', x, y, c === '~' ? FG_COL + 1 : FG_COL);
    if (c === 'Y' || c === '#') set('collision', x, y, FG_COL);
  }
  // 廣場路燈（遊美示範圖有 3 盞路燈）：只加 deco／occlusion，碰撞只喺底座
  if (town) for (const [lx, ly] of [[16, 12], [24, 12], [16, 16], [24, 16]]) { set('deco', lx, ly, G('lantern_base')); set('collision', lx, ly, FG_COL); set('deco', lx, ly - 1, G('lantern_mid')); set('occlusion', lx, ly - 2, G('lantern_top')); }
  // 地面小裝飾（只放喺草地、唔阻擋嘅格）
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
    if (cellHas(x, y) || get('collision', x, y) || ch(x, y) !== '.' || arena) continue;
    const r = h2(x, y, 11); if (r < 0.035) set('deco', x, y, G(['flowers_pink', 'flowers_yellow', 'flowers_violet'][(h2(x, y, 12) * 3) | 0])); else if (r < 0.06) set('deco', x, y, G(h2(x, y, 13) < 0.5 ? 'moss_patch_a' : 'moss_patch_b')); else if (r < 0.075) set('deco', x, y, G('puddle'));
  }
  // 門前 warp 格 collision=0 已於建築處理；水面 collision=2
  return { W, H, L, doors, ch };
}

// ---------- 事件 ----------
const J = o => JSON.stringify(o);
let oid = 0;
function ev(name, type, x, y, w, h, props) { const p = []; for (const k in props || {}) { const v = props[k]; if (v === undefined || v === null) continue; p.push(typeof v === 'number' ? { name: k, type: Number.isInteger(v) ? 'int' : 'float', value: v } : typeof v === 'boolean' ? { name: k, type: 'bool', value: v } : { name: k, type: 'string', value: typeof v === 'object' ? J(v) : String(v) }); } return { id: ++oid, name, type, x: x * 16, y: y * 16, width: w * 16, height: h * 16, rotation: 0, visible: true, properties: p }; }
const dlg = id => [{ do: 'dialog', id }];
const bub = t => ({ do: 'bubble', text: t });
const say = t => ({ do: 'say', speaker: 'narrator', text: t });
const tp = (scene, x, y, dir, save) => [{ do: 'teleport', scene, x, y, dir }].concat(save ? [{ do: 'autosave' }] : []);
const reg = { has_value: 'registered_match' };
const EVENTS = {
  town_morningmoss: d => [
    ev('spawn_start', 'spawn', 20, 26, 1, 1, { facing: 'u', note: '新遊戲' }),
    ev('ev_town_south', 'touch', 19, 29, 3, 1, { actions: [bub('來時路，唔回頭'), { do: 'push', dir: 'u', tiles: 2 }] }),
    ev('ev_elder_intro', 'auto', 17, 12, 7, 5, { once: 'save', cond: { not: { flag: 'prologue_done' } }, actions: dlg('d_elder_hub') }),
    ev('npc_elder', 'npc', 21, 14, 1, 1, { npc_id: 'elder', display: '老鐘', sprite: 'human:#c9a35a', facing: 'l', dialogs: [{ id: 'd_elder_hub' }] }),
    ev('ev_fern_first', 'auto', 17, 9, 7, 3, { once: 'save', cond: { all: [{ flag: 'prologue_done' }, { not: { flag: 'met_fern' } }] }, actions: [{ do: 'npc_face', npc: 'npc_fern', dir: 'd' }].concat(dlg('d_fern_first')) }),
    ev('npc_fern', 'npc', 21, 10, 1, 1, { npc_id: 'fern', display: '蕨生', sprite: 'human:#d46a5a', facing: 'd', dialogs: [{ cond: { flag: 'c1r1_won' }, id: 'd_fern_after_r1' }, { cond: { flag: 'met_fern' }, id: 'd_fern_idle' }, { id: 'd_fern_first' }] }),
    ev('door_arena', 'touch', d.doors.find(o => o.bld.x0 === 14).x, 8, 2, 1, { cond: { flag: 'prologue_done' }, actions: tp('arena_windrun', 6, 13, 'u') }),
    ev('door_arena_locked', 'touch', d.doors.find(o => o.bld.x0 === 14).x, 8, 2, 1, { cond: { not: { flag: 'prologue_done' } }, actions: [bub('先同老鐘傾下偈')] }),
    ev('door_elder', 'touch', 6, 8, 2, 1, { actions: [bub('鎖咗門')] }), ev('door_store', 'touch', 30, 8, 2, 1, { actions: [bub('鎖咗門')] }),
    ev('door_fernhome', 'touch', 6, 22, 2, 1, { actions: [bub('鎖咗門')] }), ev('door_house', 'touch', 32, 22, 2, 1, { actions: [bub('鎖咗門')] }),
    
    ev('obj_well', 'interact', 19, 13, 2, 2, { radius: 1.5, actions: [say('老井裡傳來水滴聲，風吹過井口，帶一點涼意。')] }),
    ev('obj_notice_board', 'interact', 8, 12, 1, 1, { radius: 1.5, actions: [say('告示：喚風祭・初葉盃報名中。')] }),
    ev('obj_sign_east', 'interact', 36, 12, 1, 1, { radius: 1.5, actions: [say('東：蕨影小徑 → 石磯港')] }),
    ev('ev_town_east', 'touch', 39, 13, 1, 2, { cond: { flag: 'prologue_done' }, actions: [{ do: 'teleport', scene: 'trail_fernshadow', entry: 'west' }, { do: 'autosave' }] }),
    ev('ev_town_east_locked', 'touch', 39, 13, 1, 2, { cond: { not: { flag: 'prologue_done' } }, actions: [bub('先同老鐘傾下偈'), { do: 'push', dir: 'l', tiles: 2 }] })
  ],
  arena_windrun: d => [
    ev('spawn_from_town', 'spawn', 6, 13, 1, 1, { facing: 'u' }),
    ev('door_town', 'touch', 6, 14, 1, 1, { actions: tp('town_morningmoss', 20, 9, 'd', true) }),
    ev('npc_sang', 'npc', 6, 3, 1, 1, { npc_id: 'sang', display: '桑姨', sprite: 'human:#7fb0a0', facing: 'd', interact_cell: '6,5', dialogs: [{ id: 'd_sang_hub' }] }),
    ev('obj_board_daily', 'interact', 11, 5, 1, 1, { radius: 1.5, actions: [say('每日賽事：暫未開放')] }),
    ev('obj_scout_hall', 'interact', 3, 5, 1, 1, { radius: 1.5, actions: [say('情報位暫未開放')] }), ev('obj_scout_stand', 'interact', 22, 6, 1, 1, { radius: 1.5, actions: [say('情報位暫未開放')] }),
    ev('ev_gate_entry', 'touch', 13, 7, 1, 3, { cond: reg, actions: [{ do: 'play_cue', id: 'cue_entry_tunnel' }, { do: 'open_gate' }] }),
    ev('ev_gate_closed', 'touch', 13, 7, 1, 3, { cond: { not: reg }, actions: [bub('未報名，去搵桑姨')] }),
    ev('gate', 'blocker', 13, 7, 1, 3, { open_cond: reg, tile_closed: 'ph_gate_closed', tile_open: 'ph_gate_open' }),
    ev('ev_stand_intro', 'auto', 21, 2, 7, 12, { once: 'match', cond: reg, actions: [{ do: 'play_cue', id: 'cue_team_intro' }] }),
    ev('ev_formation', 'interact', 24, 8, 1, 1, { radius: 1.5, cond: reg, actions: [{ do: 'open_ui', name: 'formation' }] }),
    ev('npc_fern_arena', 'npc', 30, 11, 1, 1, { npc_id: 'fern', display: '蕨生', sprite: 'human:#d46a5a', facing: 'l', visible_cond: reg, dialogs: [{ cond: { flag: 'c1r1_won' }, id: 'd_fern_after_r1' }, { cond: { flag: 'c1r1_lost_last' }, id: 'd_fern_after_r1' }, { id: 'd_fern_prematch' }] }),
    ev('npc_opponent', 'npc', 36, 7, 1, 1, { npc_id: 'opponent', display: '見習跑手', sprite: 'human:#8a8cc0', facing: 'l', visible_cond: reg, dialogs: [{ id: 'd_opponent_misc' }] }),
    ev('ev_fern_prematch', 'auto', 28, 9, 5, 5, { once: 'save', cond: { all: [{ has_value: 'registered_match' }, { not: { flag: 'seen_fern_prematch' } }] }, actions: dlg('d_fern_prematch') }),
    ev('ev_start_line', 'touch', 34, 5, 1, 6, { cond: { all: [reg, { flag: 'formation_done' }] }, actions: [{ do: 'play_cue', id: 'cue_countdown' }, { do: 'start_match', match: 'c1_r1' }] }),
    ev('ev_start_line_warn', 'touch', 34, 5, 1, 6, { cond: { all: [reg, { not: { flag: 'formation_done' } }] }, actions: [bub('未佈陣：去看台佈陣點 F'), { do: 'push', dir: 'l', tiles: 2 }] })
  ],
  trail_fernshadow: d => [
    ev('west', 'spawn', 1, 7, 1, 1, { facing: 'r' }),
    ev('ev_trail_west', 'touch', 0, 7, 1, 2, { actions: tp('town_morningmoss', 38, 13, 'l', true) }),
    ev('obj_sign_hint', 'interact', 3, 6, 1, 1, { radius: 1.5, actions: [say('前方空地有野靈，走近點一下可結緣。')] }),
    ev('npc_wild_badger', 'npc', 38, 3, 1, 1, { npc_id: 'wild_badger', display: '野生碎石獾', sprite: 'cat', radius: 2, facing: 'l', visible_cond: { not: { flag: 'captured_badger' } }, dialogs: [{ id: 'd_capture_intro' }] }),
    ev('obj_sign_east', 'interact', 56, 6, 1, 1, { radius: 1.5, actions: [say('前往石磯港（風停咗，路暫時未通）')] }),
    ev('ev_trail_block', 'interact', 58, 7, 2, 2, { radius: 1.5, actions: [bub('倒塌嘅樹幹擋住路')] })
  ]
};
const TS = [
  { firstgid: FG_ART, source: '../tiles/morningmoss/tileset_morningmoss_extruded.tsj' },
  { columns: 4, firstgid: FG_COL, image: '../tiles/morningmoss/tileset_collision.png', imageheight: 16, imagewidth: 64, margin: 0, name: 'collision', spacing: 0, tilecount: 4, tilewidth: 16, tileheight: 16 },
  { firstgid: FG_PH, source: 'tileset_placeholder.tsj' }
];
const pr = (name, v, type) => ({ name, type: type || 'string', value: v });
const SCENE = { town_morningmoss: '晨苔鎮', arena_windrun: '迴風場', trail_fernshadow: '蕨影小徑' };
for (const id of Object.keys(ASC)) {
  oid = 0; const b = build(id), d = b;
  const layers = [], role = r => [pr('role', r)];
  let lid = 0;
  const tl = (name, data, r, vis) => ({ id: ++lid, name, type: 'tilelayer', x: 0, y: 0, width: b.W, height: b.H, opacity: 1, visible: vis !== false, data, properties: role(r) });
  layers.push(tl('ground', b.L.ground, 'below_entities'), tl('deco', b.L.deco, 'below_entities'), Object.assign(tl('collision', b.L.collision, 'logic', false), { properties: [pr('role', 'logic'), pr('legend', '1=block 2=water(blocks walkers) 3=trigger 4=slow（gid−193+1）')] }), tl('occlusion', b.L.occlusion, 'above_entities'));
  layers.push({ id: ++lid, name: 'events', type: 'objectgroup', x: 0, y: 0, opacity: 1, visible: true, draworder: 'topdown', objects: EVENTS[id](d) });
  const map = { compressionlevel: -1, height: b.H, width: b.W, infinite: false, nextlayerid: lid + 1, nextobjectid: oid + 1, orientation: 'orthogonal', renderorder: 'right-down', tiledversion: '1.10.2', tileheight: 16, tilewidth: 16, type: 'map', version: '1.10',
    properties: [pr('scene', id), pr('name', SCENE[id]), pr('tod_default', 'morning'), pr('y_sort_entities', true, 'bool'), pr('note', '由 tools/gen-adventure-maps.js 自 design/adventure-slice/maps-and-events.md 產生；佔位圖塊見 MISSING_ASSETS.json')], layers, tilesets: TS };
  fs.writeFileSync(path.join(OUT, id + '.json'), JSON.stringify(map, null, 1));
  console.log(id, b.W + 'x' + b.H, 'events', layers[4].objects.length, 'doors', b.doors.map(o => o.x + ',' + o.y).join(' '));
}
fs.writeFileSync(path.join(OUT, 'MISSING_ASSETS.json'), JSON.stringify({ note: '遊美 tileset 未覆蓋、以 tileset_placeholder 佔位者；另缺 NPC 精靈／頭像／野靈（碎石獾）town 版', tilesPlaceholder: [...missing].sort(),
  characters: ['老鐘／蕨生／桑姨／見習跑手：暫用 player 32px 精靈＋色調（無獨立 NPC 圖集）', '野生碎石獾：暫用窄樑貓 town48', '對話頭像 4 表情 × 3 位（頭像未交付：UI 用色塊＋名字）'],
  mapFeatures: ['lights 層（窗／路燈光點）未生成', '門前兩格闊（art 門 2 格；ASCII 1 格 D）', '蕨叢 `,` 上半入遮擋層：用 tuft 單 tile 暫代（art 無專用蕨叢）', '內部場景 interior_* 未做'] }, null, 1));
