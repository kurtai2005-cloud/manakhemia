/* scene-events.js — 把 Tiled events 物件層（遊美 §D／§K 詞彙 ＋ 遊策 §5 詞彙）正規化成引擎事件（DOM-free，Node 可測）。
   WR.SceneEvents.normalize(dec, {overlay, sceneIds, dialogIds}) → { events, npcs, lights, spawns, fx, companion, warnings, missing }
   missing＝遊美／遊策資料缺嘅欄位清單（報告用）；warnings＝可疑但已處理。 */
(function (g) {
  'use strict';
  const DIR = { down: 'd', up: 'u', left: 'l', right: 'r', d: 'd', u: 'u', l: 'l', r: 'r' };
  const dirOf = (v, d) => DIR[String(v || '').toLowerCase()] || d || 'd';
  const dropWarp = () => null;

  function normalize(dec, ctx) {
    ctx = ctx || {}; const ov = ctx.overlay || {}, sceneIds = ctx.sceneIds || null, dialogIds = ctx.dialogIds || null, nodeIndex = ctx.nodeIndex || {}, npcSprites = ctx.npcSprites || [];
    const out = { events: [], npcs: [], lights: [], spawns: {}, fx: [], companion: null, warnings: [], missing: [] };
    const miss = m => { if (out.missing.indexOf(m) < 0) out.missing.push(m); }, warn = m => { if (out.warnings.indexOf(m) < 0) out.warnings.push(m); };
    const hasDialog = id => !dialogIds || dialogIds.indexOf(id) >= 0;
    const alias = id => id;   // 遊策 11:25：d_elder_intro／d_elder_hub 唔做別名，overlay 無 dialog_alias
    const onceOf = v => v === true || v === 'true' ? 'save' : (v === 'save' || v === 'match' ? v : null);
    const base = (e, kind) => ({ name: e.name, kind, tx: e.tx, ty: e.ty, tw: e.tw, th: e.th, cond: e.cond || null, once: null, actions: [], dialogs: null, display: '', sprite: '', facing: 'd', radius: 1.5, interactCell: null, visibleCond: e.visibleCond || null, openCond: e.openCond || null, hint: e.props.hint || '', src: 'game', props: e.props });
    const condMentions = (c, f) => JSON.stringify(c || '').indexOf('"' + f + '"') >= 0;
    for (const e of dec.events) {
      const p = e.props, t = e.type;
      if (t === 'spawn') {
        if (p.spirit) { out.companion = { name: e.name, spirit: p.spirit, sprite: p.sprite || '', tx: e.tx, ty: e.ty }; continue; }
        out.spawns[e.name] = { x: e.tx * dec.tw + dec.tw / 2, y: e.ty * dec.th + dec.th / 2, tx: e.tx, ty: e.ty, dir: dirOf(p.facing, 'd') }; continue;
      }
      if (t === 'light') { out.lights.push({ name: e.name, x: (e.tx + 0.5) * dec.tw, y: (e.ty + 0.5) * dec.th, kind: p.kind || 'lantern', color: p.color || '#FFB060', r: (+p.radius || 4) * dec.tw, litDefault: p.lit_default === true }); continue; }
      if (t === 'blocker') { const b = base(e, 'blocker'); b.tileClosed = p.tile_closed || ''; b.tileOpen = p.tile_open || ''; out.events.push(b); continue; }
      if (t === 'warp') {   // ---- 遊美 warp → touch ＋ teleport ----
        const target = (ov.scene_alias && ov.scene_alias[p.target]) || p.target, known = !sceneIds || sceneIds.indexOf(target) >= 0;
        const ev = base(e, 'touch'); ev.hint = p.hint || '';
        if (p.locked === true || p.locked === 'true') { ev.actions = [{ do: 'bubble', text: (ov.warp_text && ov.warp_text[e.name]) || p.hint || '鎖咗門' }]; out.events.push(ev); continue; }
        if (!known) { miss('warp「' + e.name + '」target「' + p.target + '」唔係遊策場景（無對應地圖）→ 以提示文字代替'); ev.actions = [{ do: 'bubble', text: (ov.warp_text && ov.warp_text[e.name]) || (p.hint ? p.hint + '（未開放）' : '未開放') }]; out.events.push(ev); continue; }
        const entry = (ov.entry_alias && ov.entry_alias[target + ':' + (p.entry || '')]) || p.entry || '';
        ev.actions = []; if (ov.last_door_events && ov.last_door_events.indexOf(e.name) >= 0) ev.actions.push({ do: 'set_var', var: 'last_town_door', value: e.name }); ev.actions.push({ do: 'teleport', scene: target, entry }); if (p.autosave === true) ev.actions.push({ do: 'autosave' });
        out.events.push(ev);
        if (ev.cond) { const b = base(e, 'touch'); b.name = e.name + '_blocked'; b.cond = { not: ev.cond }; b.actions = [{ do: 'bubble', text: condMentions(ev.cond, 'prologue_done') ? (ov.cond_fail_default || '未開放') : (p.hint || '未開放') }, { do: 'push', dir: 'auto', tiles: 2 }]; out.events.push(b); }
        continue;
      }
      if (t === 'npc_spawn' || t === 'npc') {
        const n = base(e, 'npc'), o = (ov.npcs && ov.npcs[e.name]) || {};
        n.display = o.display || p.display || p.npc_id || e.name; n.sprite = o.sprite || p.sprite || '';
        if (!n.sprite && npcSprites.indexOf(p.npc_id) >= 0) n.sprite = 'npc:' + p.npc_id;
        n.portrait = npcSprites.indexOf(p.npc_id) >= 0 ? p.npc_id : '';
        if (!n.sprite) { miss('npc「' + e.name + '」無 sprite 欄（遊美 npc_spawn 只有 npc_id／facing／dialog_node／radius）→ 用占位精靈'); n.sprite = 'human:#9aa0b0'; }
        n.facing = dirOf(p.facing, 'd'); n.radius = +p.radius || 1.5; n.interactCell = p.interact_cell ? String(p.interact_cell).split(',').map(Number) : null; n.npcId = p.npc_id || e.name;
        n.dialogs = o.dialogs || e.dialogs || (p.dialog_node ? [nodeIndex[alias(p.dialog_node)] && !hasDialog(alias(p.dialog_node)) ? { id: nodeIndex[alias(p.dialog_node)], node: alias(p.dialog_node) } : { id: alias(p.dialog_node) }] : null);
        if (!n.dialogs) miss('npc「' + e.name + '」無對話清單'); else for (const d of n.dialogs) if (!hasDialog(d.id)) miss('npc「' + e.name + '」對話 id「' + d.id + '」唔存在');
        if (p.radius && +p.radius < 1.5) warn('npc「' + e.name + '」radius=' + p.radius + ' 細過 interact_range 1.5 → 取較大者');
        n.radius = Math.max(n.radius, 1.5); out.npcs.push(n); out.events.push(n); continue;
      }
      if (t === 'trigger') {
        const eff = p.effect;
        if (eff === 'mist') { out.fx.push({ name: e.name, effect: 'mist', strength: +p.strength || 0.3, tx: e.tx, ty: e.ty, tw: e.tw, th: e.th }); continue; }
        if (eff === 'push_back') { const ev = base(e, 'touch'); ev.actions = [{ do: 'bubble', text: p.hint || '' }, { do: 'push', dir: 'auto', tiles: +p.push_tiles || 2 }]; out.events.push(ev); continue; }
        if (eff === 'auto_dialog') { const ev = base(e, 'auto'); ev.once = onceOf(p.once); const id = alias(p.dialog_node || ''); if (!hasDialog(id)) miss('trigger「' + e.name + '」dialog_node「' + id + '」唔存在'); ev.actions = (ov.auto_extra && ov.auto_extra[e.name] || []).concat([{ do: 'dialog', id }]); out.events.push(ev); continue; }
        miss('trigger「' + e.name + '」effect「' + eff + '」未知'); continue;
      }
      if (t === 'interact') {
        const ev = base(e, 'interact'); ev.radius = +p.radius || 1.5; const id = p.dialog ? alias(p.dialog) : '';
        if (id && hasDialog(id)) ev.actions = [{ do: 'dialog', id }];
        else if (id && nodeIndex[id]) ev.actions = [{ do: 'dialog', id: nodeIndex[id], node: id }];   // 遊策 §4：節點喺 d_objects_town 內
        else if (id && ov.texts && ov.texts[id]) { ev.actions = [{ do: 'say', speaker: 'narrator', text: ov.texts[id] }]; miss('interact「' + e.name + '」dialog「' + id + '」喺遊策對話資料不存在 → 遊程占位文字'); }
        else if (e.actions) ev.actions = e.actions;
        else { ev.actions = [{ do: 'say', speaker: 'narrator', text: p.hint || '…' }]; miss('interact「' + e.name + '」dialog「' + id + '」不存在、無占位文字 → 用 hint'); }
        out.events.push(ev); continue;
      }
      if (t === 'touch' || t === 'auto' || t === 'interact') { /* 遊策詞彙：下面處理 */ }
      if (t === 'touch' || t === 'auto') { const ev = base(e, t); ev.once = onceOf(p.once); ev.actions = e.actions || []; out.events.push(ev); continue; }
      warn('未處理 event type：' + t + '（' + e.name + '）');
    }
    // 遊策詞彙 interact（見上：t==='interact' 已統一處理，遊策版 actions 優先）
    for (const ev of out.events) if (ev.kind === 'interact' && ev.props && ev.props.actions) { try { const a = typeof ev.props.actions === 'string' ? JSON.parse(ev.props.actions) : ev.props.actions; if (Array.isArray(a)) ev.actions = a; } catch (_) { /* keep */ } }
    out.events.forEach(ev => { if (ev.props && ev.props.interact_cell && ev.kind === 'npc') ev.interactCell = String(ev.props.interact_cell).split(',').map(Number); });
    if (!Object.keys(out.spawns).length) miss('地圖無 spawn 事件');
    return out;
  }
  const api = { normalize, dirOf };
  g.WR = g.WR || {}; g.WR.SceneEvents = api; if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
