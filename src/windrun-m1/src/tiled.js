/* tiled.js — Tiled JSON（orthogonal，遊美 ASSET_SPEC_TOWN §C／§D 子集）解析、相容性檢查、遮擋 sort_y。DOM-free（Node／瀏覽器共用）。
   只吃 JSON（唔用 Tiled 編輯器／rea／TMX）。external tileset（.tsj）由呼叫方先 fetch，經 resolve() 併入。
   check() 回傳 {errors, warnings, infos}，每項 {code, msg, where}；engine 能吃但同規格／遊策文件有出入者標 warning。 */
(function (g) {
  'use strict';
  const FLIP = { H: 0x80000000, V: 0x40000000, D: 0x20000000, MASK: 0xE0000000 }, FLIP_ALL = 0xF0000000;
  const COLLISION_LEGEND = { 0: 'walk', 1: 'block', 2: 'water', 3: 'trigger', 4: 'slow' };
  const EVENT_TYPES_ART = ['spawn', 'warp', 'interact', 'npc_spawn', 'trigger', 'light'];              // 遊美 §D
  const EVENT_TYPES_GAME = ['spawn', 'touch', 'interact', 'auto', 'npc'];                    // 遊策 maps-and-events §5
  const EVENT_TYPES_ENGINE = ['spawn', 'warp', 'interact', 'npc_spawn', 'trigger', 'touch', 'auto', 'npc', 'blocker', 'light'];

  const props = o => { const r = {}; for (const p of (o && o.properties) || []) r[p.name] = p.value; return r; };
  const json = (s, d) => { if (s == null || s === '') return d; if (typeof s !== 'string') return s; try { return JSON.parse(s); } catch (e) { return d; } };
  /** 遊美 §K 嘅 cond 表達式（`prologue_done and not met_fern`）→ 遊策 cond JSON。支援 and／or／not／括號／識別字（＝flag）。非法回 undefined。 */
  function parseExpr(str) {
    const tk = String(str).match(/\(|\)|[A-Za-z_][A-Za-z0-9_]*/g) || [], rest = String(str).replace(/\(|\)|[A-Za-z_][A-Za-z0-9_]*|\s+/g, ''); if (rest) return undefined; let i = 0, bad = false;
    const peek = () => tk[i], next = () => tk[i++];
    function prim() { const t = next(); if (t === undefined) { bad = true; return null; } if (t === '(') { const e = orE(); if (next() !== ')') bad = true; return e; } if (t === 'not') return { not: prim() }; if (t === 'and' || t === 'or' || t === ')') { bad = true; return null; } return { flag: t }; }
    function andE() { const a = [prim()]; while (peek() === 'and') { next(); a.push(prim()); } return a.length === 1 ? a[0] : { all: a }; }
    function orE() { const a = [andE()]; while (peek() === 'or') { next(); a.push(andE()); } return a.length === 1 ? a[0] : { any: a }; }
    const r = orE(); return (bad || i !== tk.length) ? undefined : r;
  }
  /** cond 屬性：遊策 JSON 字串／遊美表達式字串／已係物件 → cond JSON（空＝null；非法＝undefined）。 */
  function condOf(v) { if (v == null || v === '') return null; if (typeof v === 'object') return v; const t = String(v).trim(); if (t[0] === '{') return json(t, undefined); return parseExpr(t); }
  const gidOf = raw => { const u = raw >>> 0; return { gid: u & ~FLIP_ALL & 0x0FFFFFFF, flipH: !!(u & FLIP.H), flipV: !!(u & FLIP.V), flipD: !!(u & FLIP.D), raw: u }; };

  /** 把 map.tilesets 內 external（source）項用 loaded[source] 取代／補齊，回傳 firstgid 升序嘅 tileset 陣列（含 tiles 屬性 map、anim map、extruded 旗標）。 */
  function resolve(map, loaded) {
    loaded = loaded || {}; const out = [];
    for (const t of map.tilesets || []) {
      const base = t.source ? Object.assign({}, loaded[t.source] || {}, { firstgid: t.firstgid, source: t.source }) : Object.assign({}, t);
      base.tilewidth = base.tilewidth || map.tilewidth; base.tileheight = base.tileheight || map.tileheight;
      base.margin = base.margin | 0; base.spacing = base.spacing | 0; base.columns = base.columns | 0;
      base.tilecount = base.tilecount | 0; base.byId = {}; base.anim = {};
      for (const tl of base.tiles || []) { base.byId[tl.id] = tl; if (tl.animation) base.anim[tl.id] = tl.animation; }
      base.extruded = base.margin === 1 && base.spacing === 2; base.imgBase = t.source ? t.source.replace(/[^\/]*$/, '') : '';
      out.push(base);
    }
    out.sort((a, b) => a.firstgid - b.firstgid); return out;
  }
  function tilesetFor(sets, gid) { let r = null; for (const t of sets) { if (t.firstgid <= gid) r = t; else break; } return r && gid < r.firstgid + Math.max(r.tilecount, 1) ? r : null; }
  /** gid → {ts, id, sx, sy}（來源矩形，已計 margin/spacing） */
  function srcRect(ts, id) { const c = ts.columns || 1, col = id % c, row = (id / c) | 0; return { sx: ts.margin + col * (ts.tilewidth + ts.spacing), sy: ts.margin + row * (ts.tileheight + ts.spacing) }; }

  /** 解碼成 engine 用結構。collisionName：碰撞 tileset 名（預設 'collision'）；值＝gid−firstgid+1。 */
  function decode(map, sets) {
    const W = map.width, H = map.height, L = {}, order = [], events = [];
    const colSet = sets.find(t => t.name === 'collision');
    let objId = 0;
    for (const l of map.layers) {
      if (l.type === 'tilelayer') { const a = new Int32Array(W * H); const d = Array.isArray(l.data) ? l.data : []; for (let i = 0; i < W * H; i++) a[i] = gidOf(d[i] | 0).gid; L[l.name] = { gids: a, raw: d, props: props(l), role: props(l).role || null, visible: l.visible !== false }; order.push(l.name); }
      else if (l.type === 'objectgroup') for (const o of l.objects || []) {
        const p = props(o), type = o.type || o.class || ''; objId++;
        events.push({ id: o.id, name: o.name || ('obj' + o.id), type, x: o.x, y: o.y, w: o.width || 0, h: o.height || 0, tx: Math.floor(o.x / map.tilewidth), ty: Math.floor(o.y / map.tileheight), tw: Math.max(1, Math.round((o.width || 0) / map.tilewidth)), th: Math.max(1, Math.round((o.height || 0) / map.tileheight)),
          props: p, cond: condOf(p.cond), actions: json(p.actions, null), dialogs: json(p.dialogs, null), openCond: condOf(p.open_cond), visibleCond: condOf(p.visible_cond) });
      }
    }
    const col = new Uint8Array(W * H);
    if (L.collision) { const base = colSet ? colSet.firstgid - 1 : 192; for (let i = 0; i < W * H; i++) { const g = L.collision.gids[i]; col[i] = g ? Math.max(0, g - base) : 0; } }
    return { w: W, h: H, tw: map.tilewidth, th: map.tileheight, layers: L, order, events, collision: col, props: props(map), sets };
  }
  /** 遮擋進階（ASSET_SPEC_TOWN §C）：occlusion tile 逐格 sort_y＝同欄向下掃到第一個 collision=1 嘅格，其底邊世界 y（px）；掃唔到＝Infinity（永遠喺實體上面）。 */
  function occlusionSort(W, H, occ, col, th) {
    th = th || 16; const out = new Float32Array(W * H).fill(Infinity);
    for (let x = 0; x < W; x++) for (let y = 0; y < H; y++) { if (!occ[y * W + x]) continue; let k = y; while (k < H && col[k * W + x] !== 1) k++; out[y * W + x] = k < H ? (k + 1) * th : Infinity; }
    return out;
  }

  // ---------- 相容性檢查 ----------
  /** ctx：{ files?:(path)=>bool（相對 map 檔嘅圖片是否存在；external .tsj 嘅 image 已併上 tsj 目錄）, extrudedFor?:string[]（已有 extruded 版本嘅 image 檔名）, imageSize?:(path)=>[w,h], loaded?:{source:tsj}, sceneIds?:string[]（遊策場景 id）, extrudedAvailable?:bool, dialogIds?:string[], mapPath?:string } */
  function check(map, ctx) {
    ctx = ctx || {}; const R = { errors: [], warnings: [], infos: [] };
    const E = (c, m, w) => R.errors.push({ code: c, msg: m, where: w || '' }), Wn = (c, m, w) => R.warnings.push({ code: c, msg: m, where: w || '' }), I = (c, m, w) => R.infos.push({ code: c, msg: m, where: w || '' });
    if (map.type !== 'map') E('E_TYPE', 'type 唔係 "map"');
    if (map.orientation !== 'orthogonal') E('E_ORIENT', 'orientation=' + map.orientation + '（只支援 orthogonal）');
    if (map.infinite) E('E_INFINITE', 'infinite=true（只支援固定尺寸；chunks 唔解析）');
    if (map.tilewidth !== 16 || map.tileheight !== 16) E('E_TILESIZE', 'tilewidth/height 必為 16（遊美／遊策一致）：' + map.tilewidth + 'x' + map.tileheight);
    if (map.renderorder && map.renderorder !== 'right-down') I('I_RENDERORDER', 'renderorder=' + map.renderorder + '（engine 忽略，固定 right-down）');
    if (map.compressionlevel != null && map.compressionlevel !== -1) I('I_COMPRESSION', 'compressionlevel 只影響 base64 資料；本檔 data 為 JSON 陣列');
    const W = map.width, H = map.height, layers = map.layers || [], names = layers.map(l => l.name);
    const sets = resolve(map, ctx.loaded);
    // tilesets
    if (!sets.length) E('E_NO_TILESET', '冇 tileset');
    for (const t of sets) {
      const w = 'tileset ' + (t.name || t.source);
      if (t.source) { I('I_EXTERNAL_TSET', 'external tileset：' + t.source + '（需要先 fetch .tsj；engine 已支援）', w); if (!ctx.loaded || !ctx.loaded[t.source]) E('E_TSET_UNLOADED', 'external tileset 未載入：' + t.source, w); }
      if (!t.image && !(t.tiles || []).some(x => x.image)) E('E_TSET_IMAGE', '冇 image', w);
      const ip = t.image ? (t.imgBase + t.image) : '';
      if (t.image && ctx.files && !ctx.files(ip)) E('E_TSET_FILE', '圖片不存在：' + ip + (t.source ? '（路徑相對 .tsj，唔係相對 map）' : ''), w);
      if (t.image && ctx.imageSize) { const sz = ctx.imageSize(ip); if (sz) { const expW = t.margin * 2 + t.columns * t.tilewidth + (t.columns - 1) * t.spacing, rows = Math.ceil(t.tilecount / Math.max(1, t.columns)), expH = t.margin * 2 + rows * t.tileheight + (rows - 1) * t.spacing; if (sz[0] !== t.imagewidth || sz[1] !== t.imageheight) E('E_TSET_DIM', 'imagewidth/height（' + t.imagewidth + 'x' + t.imageheight + '）同實際 PNG（' + sz.join('x') + '）唔符', w); else if (sz[0] !== expW || sz[1] !== expH) Wn('W_TSET_GRID', 'margin/spacing/columns 推算尺寸 ' + expW + 'x' + expH + ' ≠ PNG ' + sz.join('x'), w); } }
      if (t.margin === 0 && t.spacing === 0 && t.name !== 'collision' && ctx.extrudedFor && ctx.extrudedFor.indexOf(t.image) >= 0) Wn('W_NOT_EXTRUDED', 'map 內 tileset 用非 extruded 圖（margin0/spacing0）；GPU（Pixi/Phaser）縮放取樣會滲色。engine 載入時改用 extruded .tsj 同一 firstgid（tile id 相同）', w);
      else if (t.margin === 0 && t.spacing === 0 && t.name !== 'collision') I('I_NOT_EXTRUDED', 'tileset 非 extruded（整數縮放＋整數鏡頭位置唔會滲色；改非整數縮放／GPU 取樣先需要 extrude）', w);
      for (const tl of t.tiles || []) { if (tl.animation) for (const f of tl.animation) if (f.duration == null || f.tileid == null) E('E_ANIM', 'animation 幀缺 tileid/duration（tile ' + tl.id + '）', w); if (tl.id >= t.tilecount && t.tilecount) E('E_TILE_ID', 'tile id ' + tl.id + ' ≥ tilecount', w); }
      if (t.tilewidth !== map.tilewidth || t.tileheight !== map.tileheight) E('E_TSET_TILESIZE', 'tileset 圖塊尺寸 ≠ map', w);
    }
    for (let i = 1; i < sets.length; i++) { const a = sets[i - 1], b = sets[i]; if (a.firstgid + a.tilecount > b.firstgid) E('E_GID_OVERLAP', 'tileset gid 範圍重疊：' + a.name + ' / ' + b.name); else if (a.firstgid + a.tilecount < b.firstgid) I('I_GID_GAP', a.name + ' 同 ' + b.name + ' 之間有 gid 空隙（正常）'); }
    // layers
    const need = ['ground', 'deco', 'collision', 'occlusion'];
    for (const n of need) if (names.indexOf(n) < 0) (n === 'collision' ? E : Wn)(n === 'collision' ? 'E_NO_COLLISION' : 'W_MISSING_LAYER', '缺圖層 ' + n);
    if (names.indexOf('events') < 0) Wn('W_MISSING_LAYER', '缺 events 物件層');
    for (const alt of [['occlude', 'occlusion'], ['objects', 'deco'], ['lights', null]]) if (names.indexOf(alt[0]) >= 0 && (alt[1] === null || names.indexOf(alt[1]) < 0)) I('I_NAME_ALIAS', '遊策層名 "' + alt[0] + '" ' + (alt[1] ? '→ engine 當作 ' + alt[1] : '→ engine 未實作 lights 層'));
    if (names.indexOf('objects') < 0) I('I_NO_OBJECTS_LAYER', '遊策 §5 有 objects 層（y-sort 建築／樹）；遊美示範圖無此層（建築／樹畫喺 deco，碰撞喺 collision）。engine 以 deco＋collision 處理');
    if (names.indexOf('lights') < 0) I('I_NO_LIGHTS_LAYER', '無 lights 層：窗／路燈光點需由 tile 名（window_*_lit／lantern_*）或 emissive 圖推算');
    const ids = new Set();
    for (const l of layers) {
      const w = 'layer ' + l.name;
      if (ids.has(l.id)) E('E_LAYER_ID', 'layer id 重複 ' + l.id, w); ids.add(l.id);
      if (l.offsetx || l.offsety) Wn('W_LAYER_OFFSET', 'offsetx/y≠0（engine 忽略）', w);
      if (l.parallaxx != null && l.parallaxx !== 1) Wn('W_PARALLAX', 'parallax≠1（engine 忽略）', w);
      if (l.type === 'tilelayer') {
        if (l.chunks) E('E_CHUNKS', 'layer 用 chunks', w);
        if (typeof l.data === 'string' || l.encoding === 'base64') E('E_ENCODING', 'data 為 base64／csv；engine 只吃 JSON 數字陣列', w);
        else if (!Array.isArray(l.data) || l.data.length !== W * H) E('E_DATA_LEN', 'data 長度 ' + (l.data && l.data.length) + ' ≠ ' + (W * H), w);
        else {
          let flips = 0, bad = 0; const seenBad = new Set();
          for (const raw of l.data) { const o = gidOf(raw); if ((raw >>> 0) & FLIP_ALL) flips++; if (o.gid && !tilesetFor(sets, o.gid)) { bad++; seenBad.add(o.gid); } }
          if (flips) Wn('W_FLIP', flips + ' 格有翻轉旗標（engine 已支援 H／V／D 於繪圖；碰撞層唔應有）', w);
          if (bad) E('E_UNRESOLVED_GID', bad + ' 格 gid 唔屬任何 tileset：' + [...seenBad].slice(0, 6).join(','), w);
        }
        if (!props(l).role) Wn('W_NO_ROLE', '無 role 屬性；engine 以層名推斷（ground/deco/occlusion/collision）', w);
        if (l.name === 'collision') {
          const colSet = sets.find(t => t.name === 'collision'); if (!colSet) E('E_COLLISION_TSET', 'collision 層無對應 "collision" tileset，值無法解碼', w);
          else { const base = colSet.firstgid - 1, vals = new Set(); for (const raw of l.data || []) if (raw) vals.add(gidOf(raw).gid - base); const odd = [...vals].filter(v => v < 1 || v > 4); if (odd.length) Wn('W_COLLISION_VALUE', 'collision 值出界：' + odd.join(','), w);
            I('I_COLLISION_ENCODING', 'collision 層存「gid」（' + (colSet.firstgid) + '–' + (colSet.firstgid + 3) + '）而非 0–4 純值；值＝gid−' + base + '（遊美 §C 嘅 0/1/2/3/4 係解碼後值；遊策 §5 寫 0／1 兩值）。實際出現值：' + [...vals].sort().join(','), w);
            if (l.visible !== false) I('I_COLLISION_VISIBLE', 'collision 層 visible=true（Tiled 預覽會畫出）；示範檔為 false', w); }
        }
      } else if (l.type === 'objectgroup') {
        const nm = new Set(), oids = new Set(), vocab = {}, scn = {}, dlgMiss = [];
        for (const o of l.objects || []) {
          const wo = 'object ' + (o.name || o.id), t = o.type || o.class || '';
          if (!t) E('E_OBJ_TYPE', 'object 無 type／class', wo);
          if (o.class && !o.type) I('I_OBJ_CLASS', 'object 用 "class"（Tiled ≥1.9 JSON 亦可為 "type"；engine 兩者都接受）', wo);
          if (oids.has(o.id)) E('E_OBJ_ID', 'object id 重複 ' + o.id, wo); oids.add(o.id);
          if (o.name) { if (nm.has(o.name)) Wn('W_OBJ_NAME_DUP', 'object name 重複：' + o.name, wo); nm.add(o.name); } else Wn('W_OBJ_NO_NAME', 'object 無 name', wo);
          if (o.point || o.ellipse || o.polygon || o.polyline || o.text || o.gid) Wn('W_OBJ_SHAPE', '非矩形物件（point/ellipse/polygon/text/tile object）：engine 只用矩形', wo);
          if (o.x < 0 || o.y < 0 || o.x + o.width > W * 16 || o.y + o.height > H * 16) Wn('W_OBJ_BOUNDS', 'object 超出地圖範圍', wo);
          if (o.x % 16 || o.y % 16 || o.width % 16 || o.height % 16) I('I_OBJ_UNALIGNED', 'object 未對齊 16px 格', wo);
          if (EVENT_TYPES_ENGINE.indexOf(t) < 0) Wn('W_OBJ_UNKNOWN_TYPE', '未知 type：' + t, wo);
          if (t === 'blocker') I('I_EXT_TYPE', 'type=blocker 係 engine 擴充（條件開放嘅碰撞矩形，例：入場閘口）；遊策 §5 未定義「條件碰撞」', wo);
          else if (EVENT_TYPES_GAME.indexOf(t) < 0 && t) (vocab[t] = vocab[t] || []).push(o.name);
          const p = props(o);
          if (t === 'warp') { if (!p.target) E('E_WARP_TARGET', 'warp 無 target', wo); else if (ctx.sceneIds && ctx.sceneIds.indexOf(p.target) < 0) (scn[p.target] = scn[p.target] || []).push(o.name); if (!p.entry) Wn('W_WARP_ENTRY', 'warp 無 entry（落點名）；遊策用座標（scene,x,y,dir）', wo); }
          for (const dk of ['dialog', 'dialog_node']) if (p[dk] && ctx.dialogIds && ctx.dialogIds.indexOf(p[dk]) < 0 && !/^TBD$/i.test(p[dk])) dlgMiss.push(o.name + ':' + p[dk]);
          if (t === 'npc_spawn') { if (/TBD/i.test(String(p.dialog_node || '')) || /_tbd$/.test(String(p.npc_id || ''))) Wn('W_TBD', 'npc_id／dialog_node 為 TBD（遊策 NPC：npc_elder／npc_fern／npc_sang）', wo); }
          if (t === 'spawn' && !p.facing && !p.spirit) Wn('W_SPAWN_FACING', 'spawn 無 facing', wo);
          if (p.cond != null && p.cond !== '') { const cc = condOf(p.cond); if (cc === undefined) E('E_COND_JSON', 'cond 屬性既非 JSON 字串亦非合法表達式：' + p.cond, wo); else if (String(p.cond).trim()[0] !== '{') vocab.cond_expr = (vocab.cond_expr || []).concat(o.name); }
          if (p.actions && typeof p.actions === 'string' && json(p.actions, undefined) === undefined) E('E_ACTIONS_JSON', 'actions 屬性非合法 JSON 字串', wo);
        }
        for (const k of Object.keys(vocab)) { if (k === 'cond_expr') I('I_COND_EXPR', 'cond 用表達式字串（遊美 §K，例 `prologue_done and not met_fern`）而非遊策 JSON；engine 兩種都解析（' + vocab[k].length + ' 個 object）', w); else Wn('W_VOCAB_ART_ONLY', 'type=' + k + '（' + vocab[k].length + ' 個：' + vocab[k].slice(0, 4).join(',') + (vocab[k].length > 4 ? '…' : '') + '）係遊美 §D／§K 詞彙，遊策 §5 無（遊策：spawn／touch／interact／auto／npc）；engine 兩套都接受，建議統一', w); }
        for (const k of Object.keys(scn)) Wn('W_SCENE_ID', 'warp target "' + k + '" 唔係遊策場景 id（' + (ctx.sceneIds || []).join('／') + '）：' + scn[k].join(','), w);
        if (dlgMiss.length) Wn('W_DIALOG_MISSING', dlgMiss.length + ' 個 dialog／dialog_node 喺對話資料不存在：' + dlgMiss.slice(0, 8).join(', ') + (dlgMiss.length > 8 ? '…' : ''), w);
      } else if (l.type !== 'imagelayer' && l.type !== 'group') Wn('W_LAYER_TYPE', '未知圖層類型 ' + l.type, w);
    }
    if (!(layers.some(l => l.type === 'objectgroup' && (l.objects || []).some(o => (o.type || o.class) === 'spawn')))) Wn('W_NO_SPAWN', '無 spawn 物件');
    const sc = props(map).scene; if (ctx.sceneIds && sc && ctx.sceneIds.indexOf(sc) < 0) Wn('W_MAP_SCENE', 'map 屬性 scene="' + sc + '" 唔係遊策場景 id', 'map');
    I('I_TILED_VERSION', 'tiledversion=' + map.tiledversion + ' version=' + map.version + '；nextlayerid/nextobjectid 唔影響執行', 'map');
    const colLayer = layers.find(l => l.name === 'collision'), grp = layers.find(l => l.type === 'objectgroup');
    // tile-level 'solid' 屬性 vs collision 層
    for (const t of sets) for (const tl of t.tiles || []) { const p = props(tl); if (p.solid) { I('I_TILE_SOLID', '部分 tile 帶 solid 屬性（例如 water_*）同 collision 層重複資訊；engine 只信 collision 層', 'tileset ' + t.name); break; } }
    void colLayer; void grp; return R;
  }
  const api = { parseExpr, condOf, FLIP, COLLISION_LEGEND, EVENT_TYPES_ART, EVENT_TYPES_GAME, props, json, gidOf, resolve, tilesetFor, srcRect, decode, occlusionSort, check };
  g.WR = g.WR || {}; g.WR.Tiled = api; if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
