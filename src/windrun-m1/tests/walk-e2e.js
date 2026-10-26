/* walk e2e（走路→傾偈→報名）：BASE=http://localhost:8131/ node tests/walk-e2e.js
   headless 桌面 Chrome（390×844 觸控模擬），非真機。涵蓋：序章→老鐘→取得苔團＋命名→互動旁白→報名處門（interior_registry 別名）→桑姨（隊伍不足被拒）→
   last_town_door 返鎮落點→小徑結緣（占位面板）→報名（葉 −20、registered_match）→閘口開→溝／木橋行走→存檔還原。 */
const { chromium } = require('playwright-core'); const path = require('path');
(async () => {
  const base = process.env.BASE || 'http://localhost:8131/', out = path.join(__dirname, '../screens') + '/', VERBOSE = process.env.VERBOSE === '1';
  const browser = await chromium.launch({ executablePath: '/usr/bin/google-chrome', args: ['--no-sandbox'] });
  const errs = [], log = []; let fails = 0; const T = (c, m) => { log.push((c ? 'PASS ' : 'FAIL ') + m); console.log((c ? 'PASS ' : 'FAIL ') + m); if (!c) fails++; };
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, hasTouch: true, isMobile: true });
  const p = await ctx.newPage(); p.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') errs.push(m.text()); }); p.on('pageerror', e => errs.push('pageerror ' + e.message));
  const slot = 'e2e' + Date.now(), url = q => base + 'walk.html?slot=' + slot + '&cps=9999&' + (q || '');
  await p.goto(url('new=1')); await p.waitForFunction(() => window.__walkReady || window.__walkErr, null, { timeout: 30000 }); T(!(await p.evaluate(() => window.__walkErr)), '載入 walk.html（batch2 town）');
  const st = () => p.evaluate(() => window.__adv.state());
  { const s0 = await st(); T(s0.minTeam === 2 && s0.devRelax === false, '預設（正式流程）：r1_min_team=2、唔放寬（實 ' + s0.minTeam + ',' + s0.devRelax + '）'); T(await p.evaluate(() => window.__world.scene.norm.missing.length === 0 && !JSON.stringify(window.__adv.warnings).match(/alias|別名/)), 'overlay 無 dialog_alias：ev_elder_intro（dialog_node=d_elder_intro）直接解析，scene missing=0'); const wn = await p.evaluate(() => window.__adv.warnings.concat(window.__adv.G.warns)); T(!wn.some(w => /party_size|別名|alias/.test(w)), '引擎唔再警告 party_size／alias（warnings=' + wn.length + '）'); }
  const say = [], por = new Set(); 
  const talk = async (pick, note) => {
    for (let i = 0; i < 120; i++) {
      const s = await st();
      if (await p.isVisible('#wr-prompt')) { await p.fill('#wr-prompt input', '小苔'); await p.click('#wr-prompt .ok'); say.push('[naming]'); continue; }
      if (await p.isVisible('#panel')) { const t = await p.textContent('#panel'); say.push('[panel] ' + t); const want = (note && note.panel) || 'first'; const idx = want === 'lose' ? 1 : 0; await p.click('#panel button >> nth=' + idx); continue; }
      if (!s.dialog.open) { if (s.busy === 0) return; await p.waitForTimeout(80); continue; }
      const d = s.dialog; por.add(d.speaker + '/' + d.portrait); say.push(d.speaker + ': ' + d.text + (d.choices.length ? ' ⟨' + d.choices.join(' | ') + '⟩' : ''));
      if (d.choices.length) { const idx = pick ? pick(d.choices) : 0; await p.click('#wr-dlg .ch button:not([disabled]) >> nth=' + Math.max(0, idx)); } else await p.click('#wr-dlg .box', { position: { x: 20, y: 14 } });
      await p.waitForTimeout(20);
    }
    T(false, 'talk 迴圈保護');
  };
  const go = async (tx, ty, ms) => { await p.evaluate(([x, y]) => window.__world.goTile(x, y), [tx, ty]); await p.waitForFunction(() => { const s = window.__adv.state(); return s.path === 0 && !s.moving || s.busy > 0; }, null, { timeout: ms || 40000 }); await p.waitForTimeout(60); };
  const idle = () => p.waitForFunction(() => window.__adv.state().busy === 0 && !window.__adv.state().dialog.open, null, { timeout: 30000 }).catch(async e => { console.log('IDLE TIMEOUT state', JSON.stringify(await p.evaluate(() => { const s = window.__adv.state(); return { scene: s.scene, busy: s.busy, dlg: s.dialog, panel: (document.querySelector('#panel') || {}).innerText, cell: [s.tx, s.ty] }; })).slice(0, 600)); throw e; });
  const flag = f => p.evaluate(f => window.__adv.G.getFlag(f), f), vr = v => p.evaluate(v => window.__adv.G.getVar(v), v);
  const cell = async () => { const s = await st(); return [s.tx, s.ty]; };
  // ---- 1 序章 ----
  await talk(); T(await flag('intro_p1_done'), '序章 P0/P1 播完 → intro_p1_done');
  const nodes0 = say.length;
  // ---- 2 走去廣場：真觸控點擊尋路 ----
  const toScr = (x, y) => p.evaluate(([x, y]) => { const A = window.__adv, S = A.W.S, r = document.getElementById('c').getBoundingClientRect(); return [r.left + (x - Math.round(S.cx * S.s) / S.s) * S.zoom, r.top + (y - Math.round(S.cy * S.s) / S.s) * S.zoom]; }, [x, y]);
  { const [sx, sy] = await toScr(20 * 16 + 8, 24 * 16 + 8); await p.touchscreen.tap(sx, sy); await p.waitForTimeout(150); const s = await st(); T(s.path > 0, '點擊地面 → 有路徑'); await p.waitForFunction(() => window.__adv.state().path === 0, null, { timeout: 15000 }); const c = await cell(); T(c[0] === 20 && c[1] === 24, '點擊到達 (20,24) 實際 (' + c + ')'); }
  await go(20, 16); await talk(c => { const i = c.findIndex(t => /照顧/.test(t)); return i; });
  T(await flag('got_mochi') && await flag('prologue_done'), '老鐘 → got_mochi＋prologue_done');
  let s = await st(); T(s.party.join() === 'mochi', '隊伍＝苔團'); T(await p.evaluate(() => window.__adv.G.save.party[0].nick) === '小苔', '命名＝小苔（open_ui naming）'); T(s.objective === 'c1_start', '目標 c1_start');
  T(await p.evaluate(() => window.__world.cat.on), 'spirit_follow：got_mochi 後生成跟隨野靈');
  await p.screenshot({ path: out + 'walk-390-after-elder.png' });
  T(por.has('elder/npc_elder:neutral') && [...por].some(x => /^elder\/npc_elder:(happy|worried|surprised)$/.test(x)), '對話頭像：老鐘 neutral＋非 neutral 表情（emote→expression）：' + [...por].filter(x => /npc_/.test(x)).join(','));
  T([...por].some(x => /^player\/$/.test(x)) || [...por].every(x => !/^player\/npc/.test(x)), '玩家／旁白無頭像');
  { const r = await p.evaluate(async () => { const W = window.__world, A = window.__adv, nd = W.S.npcDraw || {}, sc = W.scene; const out = { npc: Object.keys(nd), atlas: sc.npcs.map(n => n.name + ':' + n.kind) }; const n = sc.npcs.find(x => x.name === 'npc_fern'); const a = A.W && n && sc && null; return out; });
    T(r.atlas.every(x => /:atlas$/.test(x)) && r.atlas.length === 3, '鎮內 3 個 NPC 全用遊美圖集（' + r.atlas + '）'); }
  { const r = await p.evaluate(() => { const nd = window.__world.S.npcDraw, sc = window.__world.scene; const f = sc.npcs.find(n => n.name === 'npc_fern'); return { h: nd.npc_fern.h, top: nd.npc_fern.top, y: f.y, rg: sc.npcs.map(n => n.name + '@' + Math.round(n.x) + ',' + Math.round(n.y)).join(' ') }; });
    T(r.h === 32 && r.top === r.y - 30, '蕨生以完整 32px 幀繪製、唔裁頂部（top=' + r.top + '＝腳底 y−30）'); }
  { const top = await p.evaluate(async () => { const j = await (await fetch('art/sprites/npc/npc_fern/atlas_npc_fern.json')).json(); const f = j.frames.npc_fern_down_walk_0; return new Promise(res => { const im = new Image(); im.onload = () => { const c = document.createElement('canvas'); c.width = im.width; c.height = im.height; const x = c.getContext('2d'); x.drawImage(im, 0, 0); const d = x.getImageData(f.x, f.y + 1, 32, 1).data; let n = 0; for (let i = 3; i < d.length; i += 4) if (d[i] > 0) n++; res(n); }; im.src = 'art/sprites/npc/npc_fern/atlas_npc_fern.png'; }); });
    T(top > 0, '蕨生 down_walk_0 頂列 (y=1 外框) 有像素 ' + top + ' px → 渲染必須保留頂部'); }
  // ---- 3 互動旁白（d_objects_town）----
  await go(19, 15); s = await st(); { const nr = await p.evaluate(() => { const n = window.__world.nearest(); return n && n.name; }); T(nr === 'obj_well', '井旁 nearest=obj_well（實 ' + nr + '）'); }
  say.length = 0; await p.click('#act'); await talk(); T(say.length === 2 && /井水清得見底/.test(say[0]) && /風在下面打了個轉/.test(say[1]), 'obj_well_01 兩句旁白（遊策 §4）：' + say.join(' / '));
  // 報名處職員 npc_registry (32,9)：dialog_node＝registry_counter_01（d_objects_town）
  await go(32, 10); { const nr = await p.evaluate(() => { const n = window.__world.nearest(); return n && n.name; }); T(nr === 'npc_registry', '報名處職員 nearest（實 ' + nr + '）'); }
  say.length = 0; await p.click('#act'); await talk(); T(say.length === 1 && /櫃台後有位職員低頭整理名冊/.test(say[0]) && /想報名，就入迴風場/.test(say[0]), 'npc_registry（背景職員）interact＝registry_counter_01，旁白「櫃台後有位職員低頭整理名冊，…」：' + say.join(' / '));
  // ---- 4 報名處門 → arena（interior_registry 別名）----
  await go(30, 9); await p.evaluate(() => window.__world.goTile(30, 8)); await p.waitForFunction(() => window.__adv.state().scene === 'arena_windrun', null, { timeout: 20000 }); await idle();
  s = await st(); T(s.scene === 'arena_windrun', 'door_registry → arena_windrun（interior_registry 別名）'); T(await vr('last_town_door') === 'door_registry', 'last_town_door＝door_registry');
  { const c = await cell(); T(c[0] === 6 && c[1] >= 12 && c[1] <= 13, '落點＝spawn_from_town (6,13) 附近（實 ' + c + '）'); }
  // ---- 5 桑姨（隊伍不足：只得 1 隻）----
  await go(6, 5); { const nr = await p.evaluate(() => { const n = window.__world.nearest(); return n && n.name; }); T(nr === 'npc_sang', '桑姨可行走到互動格 (6,5) 且 nearest=npc_sang（實 ' + nr + '）'); }
  say.length = 0; await p.click('#act'); { let n = 0; await talk(c => { n++; const i = c.findIndex(t => /報名/.test(t)); return n === 1 && i >= 0 ? i : c.length - 1; }); }
  await p.screenshot({ path: out + 'walk-390-sang-refuse.png' });
  T(!(await vr('registered_match')), '只得 1 隻野靈 → 報名被拒（registered_match 仍空）；對白：' + say.slice(0, 4).join(' / ').slice(0, 160));
  // ---- 6 last_town_door 返鎮 (30,9) ----
  await go(6, 14); await p.waitForFunction(() => window.__adv.state().scene === 'town_morningmoss', null, { timeout: 20000 }); await idle(); { const c = await cell(); T(c[0] === 30 && c[1] === 9, 'door_town 返鎮：door_registry → (30,9)（實 ' + c + '）'); }
  // ---- 7 溝／木橋 ----
  await p.evaluate(() => window.__adv.W.stop && 0);
  { const w = await p.evaluate(() => { const sc = window.__world.scene, W = sc.dec.w; return { w: sc.col[27 * W + 19], water: sc.col[27 * W + 12], n: [10, 11, 12, 18, 22, 23].map(x => sc.col[27 * W + x]) }; }); T(w.w === 0, '木橋格 (19,27) 可走（collision=' + w.w + '）'); T(w.n.some(v => v === 2), '溝水格存在（collision=2）row27 x[10,11,12,18,22,23]=' + w.n); }
  // ---- 8 出鎮東行 → 小徑 ----
  await go(37, 13); await p.evaluate(() => window.__world.goTile(39, 13)); await p.waitForFunction(() => window.__adv.state().scene === 'trail_fernshadow', null, { timeout: 40000 }); await idle(); s = await st(); T(s.scene === 'trail_fernshadow', 'ev_town_east → trail（entry west）'); { const c = await cell(); T(c[0] <= 2 && c[1] >= 6 && c[1] <= 8, '落點＝west (1,7) 附近（實 ' + c + '）'); }
  // ---- 9 結緣戰（占位面板：勝）----
  await go(37, 4); { const nr = await p.evaluate(() => { const n = window.__world.nearest(); return n && n.name; }); T(nr === 'npc_wild_badger', '碎石獾 nearest（實 ' + nr + '）'); }
  say.length = 0; await p.click('#act'); await talk(c => 0, { panel: 'first' }); await talk(); s = await st();
  T(s.party.length === 2 && s.party.indexOf('gravelbadger') >= 0 || s.party.length === 2, '結緣勝 → 隊伍 2 隻（' + s.party + '）'); T(await flag('got_second_spirit') || s.party.length === 2, 'party_size=2');
  console.log('  結緣流程對白：', say.join(' / ').slice(0, 400));
  // ---- 10 返鎮 → door_arena → 報名 ----
  await go(2, 7); await p.evaluate(() => window.__world.goTile(0, 7)); await p.waitForFunction(() => window.__adv.state().scene === 'town_morningmoss', null, { timeout: 40000 }); await idle(); { const c = await cell(); T(c[0] >= 37 && c[1] >= 12 && c[1] <= 14, 'ev_trail_west 返鎮 (38,13) 附近（實 ' + c + '）'); }
  await go(20, 10); await p.waitForTimeout(300); say.length = 0; await talk(); T(await flag('met_fern') && /蕨生/.test(say.join('')) && por.has('fern/npc_fern:happy'), '途經蕨生觸發格 → ev_fern_first 自動對白（met_fern，頭像 npc_fern:happy）'); await p.evaluate(() => window.__world.goTile(19, 8)); await p.waitForFunction(() => window.__adv.state().scene === 'arena_windrun', null, { timeout: 30000 }); await idle(); T(await vr('last_town_door') === 'door_arena', 'last_town_door＝door_arena');
  await go(6, 5); say.length = 0; await p.click('#act'); { let n = 0; await talk(c => { n++; const i = c.findIndex(t => /報名/.test(t)); return n === 1 && i >= 0 ? i : c.length - 1; }); }
  const reg = await vr('registered_match'); s = await st(); T(reg === 'c1_r1', '報名成功 registered_match=c1_r1（實 ' + reg + '）'); T(s.leaf === 30, '報名費 20 → 葉 50→30（實 ' + s.leaf + '）'); T(s.objective === 'c1_enter', '目標 c1_enter（實 ' + s.objective + '）');
  console.log('  桑姨對白：', say.join(' / ').slice(0, 600));
  await p.screenshot({ path: out + 'walk-390-registered.png' });
  // ---- 11 閘口 ----
  await go(12, 8); await p.waitForTimeout(200); { const o = await p.evaluate(() => { const sc = window.__world.scene, W = sc.dec.w; return [7, 8, 9].map(y => sc.col[y * W + 13]); }); T(o.every(v => v === 0), '閘口開啟（collision (13,7–9)＝' + o + '）'); }
  // ---- 12 存檔還原 ----
  await p.evaluate(() => { window.__adv.savePos(); window.__adv.G.autosave(); }); await p.goto(url('')); await p.waitForFunction(() => window.__walkReady || window.__walkErr, null, { timeout: 30000 }); s = await st();
  T(s.scene === 'arena_windrun' && s.registered === 'c1_r1' && s.party.length === 2, '重新載入還原：場景／報名／隊伍（' + s.scene + ',' + s.registered + ',' + s.party + '）');
  // ---- 13 dev 放寬模式（?dev=1／⚙ 面板）：只得 1 隻亦可報名；預設模式已於 §5 驗證被拒 ----
  await p.goto(base + 'walk.html?slot=' + slot + 'dev&cps=9999&new=1&dev=1'); await p.waitForFunction(() => window.__walkReady || window.__walkErr, null, { timeout: 30000 });
  { const s1 = await st(); T(s1.minTeam === 1 && s1.devRelax === true, '?dev=1 → r1_min_team 放寬到 1（實 ' + s1.minTeam + '）'); T(await p.evaluate(() => getComputedStyle(document.getElementById('dev')).display) === 'block', '?dev=1 自動打開 ⚙ 面板'); }
  await p.evaluate(() => { document.getElementById('dev').style.display = 'none'; }); await talk();   // 新遊戲序章 P0/P1 自動播（先收面板免遮住對話）
  { await p.click('#devbtn'); T(await p.evaluate(() => getComputedStyle(document.getElementById('dev')).display) === 'block', '⚙ 按鈕打開面板');
    const tg = () => p.evaluate(() => [...document.querySelectorAll('#dev button')].find(b => /放寬/.test(b.textContent)).click());
    let s1; await tg(); s1 = await st(); T(s1.minTeam === 2 && !s1.devRelax, '⚙ 面板切換：關 → 2'); await tg(); s1 = await st(); T(s1.minTeam === 1 && s1.devRelax, '⚙ 面板切換：開 → 1'); await p.click('#devbtn'); }
  await p.evaluate(() => { const G = window.__adv.G; G.setFlag('prologue_done', true); G.setFlag('got_mochi', true); G.giveSpirit('mochi', 3); G.setFlag('met_sang', true); G.runAll([{ do: 'teleport', scene: 'arena_windrun', entry: 'spawn_from_town' }]); });
  await p.waitForFunction(() => window.__adv.state().scene === 'arena_windrun', null, { timeout: 20000 }); await idle();
  { const s1 = await st(); T(s1.party.length === 1, 'dev 模式：只得 1 隻（' + s1.party + '）'); }
  await go(6, 5); say.length = 0; await p.click('#act'); { let n = 0; await talk(c => { n++; const i = c.findIndex(t => /報名/.test(t)); return n === 1 && i >= 0 ? i : c.length - 1; }); }
  { const r2 = await vr('registered_match'), s2 = await st(); T(r2 === 'c1_r1' && s2.party.length === 1 && s2.leaf === 30, 'dev 放寬：1 隻亦可報名（registered_match=' + r2 + '，葉 ' + s2.leaf + '）；對白：' + say.join(' / ').slice(0, 120)); }
  const real = errs.filter(e => !/favicon/.test(e)); T(real.length === 0, '無 console error/warning' + (real.length ? '：' + real.slice(0, 3).join(' | ') : ''));
  console.log(fails ? '\nFAILED ' + fails : '\nwalk-e2e 全部通過', log.filter(l => l.startsWith('PASS')).length + ' PASS'); await browser.close(); process.exit(fails ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
