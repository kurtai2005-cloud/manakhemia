/* town-lab 功能＋截圖：BASE=http://localhost:8131/ node tests/town-e2e.js
   390×844 觸控（hasTouch）＋桌面 1280×720；headless 桌面 Chrome，非真機。 */
const { chromium } = require('playwright-core'); const path = require('path');
(async () => {
  const base = process.env.BASE || 'http://localhost:8131/', out = path.join(__dirname, '../screens') + '/';
  const browser = await chromium.launch({ executablePath: '/usr/bin/google-chrome', args: ['--no-sandbox'] });
  const errs = [], log = []; let fails = 0; const T = (c, m) => { log.push((c ? 'PASS ' : 'FAIL ') + m); if (!c) fails++; };
  const open = async (ctx, qs) => { const p = await ctx.newPage(); p.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') errs.push(m.text()); }); p.on('pageerror', e => errs.push('pageerror ' + e.message)); await p.goto(base + 'town-lab-gen.html?' + qs); await p.waitForFunction(() => window.__townReady || window.__townErr, null, { timeout: 30000 }); T(!(await p.evaluate(() => window.__townErr)), 'load ' + qs); return p; };
  const st = p => p.evaluate(() => window.__town.state());
  // ---- 手機觸控 390×844 ----
  const mob = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, hasTouch: true, isMobile: true });
  let p = await open(mob, 'q=high&tod=night&hud=0');
  await p.evaluate(() => { window.__town.stop(); });
  await p.screenshot({ path: out + 'town-390-spawn-night-high.png' });
  // 點擊尋路：用世界座標→螢幕座標（touch tap）
  const toScr = (x, y) => p.evaluate(([x, y]) => { const T = window.__town, r = document.getElementById('c').getBoundingClientRect(); return [r.left + (x - Math.round(T.S.cx * T.S.s) / T.S.s) * T.S.zoom, r.top + (y - Math.round(T.S.cy * T.S.s) / T.S.s) * T.S.zoom]; }, [x, y]);
  const tapW = async (x, y) => { const [sx, sy] = await toScr(x, y); await p.touchscreen.tap(sx, sy); };
  await p.evaluate(() => window.__town.start());
  await tapW(20 * 16 + 8, 18 * 16 + 8); await p.waitForTimeout(150);
  let s = await st(p); T(s.path > 0, '點擊後有路徑 len=' + s.path);
  await p.waitForFunction(() => window.__town.state().path === 0, null, { timeout: 15000 }); s = await st(p);
  T(s.tx === 20 && s.ty === 18, '到達目標格 (20,18) 實際 (' + s.tx + ',' + s.ty + ')');
  // 點擊障礙（房屋牆）→ 容錯到鄰近可行格，唔卡死
  await p.evaluate(() => { window.__town.teleportTo(8, 13); window.__town.step(40); }); await tapW(5 * 16 + 8, 8 * 16 + 8); await p.waitForTimeout(100); s = await st(p); T(s.path > 0, '點擊房屋牆 → 容錯尋路到鄰近格');
  await p.waitForFunction(() => window.__town.state().path === 0, null, { timeout: 25000 });
  // 浮動搖桿：拖動
  await p.evaluate(() => window.__town.teleportTo(20, 22));
  const cdp = await mob.newCDPSession(p);
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x: 200, y: 600 }] });
  for (let i = 1; i <= 6; i++) await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x: 200, y: 600 - i * 10 }] });
  await p.waitForTimeout(600); const joyVis = await p.evaluate(() => getComputedStyle(document.getElementById('joy')).display);
  await p.screenshot({ path: out + 'town-390-joystick.png' });
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] }); s = await st(p);
  T(joyVis === 'block', '搖桿出現（浮動，按下位置）'); T(s.ty < 22, '搖桿向上移動 ty=' + s.ty);
  // 遮擋：玩家行入樹後被遮（樹 (23,5) 兩格闊，base row 5；玩家喺 row 4 即樹後）
  await p.evaluate(() => { const T = window.__town; T.stop(); T.teleportTo(23, 4); T.step(2); });
  await p.screenshot({ path: out + 'town-390-occlusion-behind-tree.png', clip: { x: 100, y: 40, width: 290, height: 280 } });
  await p.evaluate(() => { const T = window.__town; T.teleportTo(24, 7); T.step(2); });
  await p.screenshot({ path: out + 'town-390-occlusion-front-of-tree.png', clip: { x: 100, y: 40, width: 290, height: 280 } });
  // 碰撞：向左穿牆（玩家喺 (4,12)，向房屋行）
  await p.evaluate(() => { window.__town.teleportTo(6, 12); });
  const col = await p.evaluate(() => { const T = window.__town; T.P.path = null; const keys = {}; let y0 = T.P.y; for (let i = 0; i < 90; i++) { T.P.y -= 1.2; /* 直接用 moveBox 路徑：模擬鍵盤上行 */ } return 0; });
  // 傳送：行入北門
  await p.evaluate(() => { window.__town.teleportTo(20, 3); window.__town.start(); });
  await tapW(20 * 16 + 8, 0 * 16 + 8); await p.waitForFunction(() => window.__town.state().map === 'route_fernshade', null, { timeout: 20000 });
  s = await st(p); T(s.map === 'route_fernshade', '北門傳送 → 蕨影小徑；出生 (' + s.tx + ',' + s.ty + ')');
  await p.waitForTimeout(500); await p.screenshot({ path: out + 'town-390-route.png' });
  // 傳送回城
  await p.evaluate(() => { window.__town.teleportTo(2, 7); });
  await tapW(0 * 16 + 8, 7 * 16 + 8); await p.waitForFunction(() => window.__town.state().map === 'town_morningmoss', null, { timeout: 20000 }); s = await st(p);
  T(s.map === 'town_morningmoss' && s.ty <= 3, '傳送返城，出生喺北門內 (' + s.tx + ',' + s.ty + ')');
  // NPC 對話
  await p.evaluate(() => { window.__town.teleportTo(22, 23); });
  await p.waitForTimeout(500);
  await p.evaluate(() => { const T = window.__town; const n = T.M.npcs.find(n => n.name === 'npc_elder'); T.tapWorld(n.x, n.y - 8); });
  await p.waitForFunction(() => window.__town.state().path === 0, null, { timeout: 15000 }); await p.waitForTimeout(200); s = await st(p); T(s.dlg === 'block', '點 NPC 後走近並顯示對話');
  await p.screenshot({ path: out + 'town-390-dialog.png' });
  // 畫質層截圖
  for (const q of ['off', 'low', 'mid']) { const pq = await open(mob, 'q=' + q + '&tod=night&hud=0'); await pq.evaluate(() => { window.__town.stop(); window.__town.teleportTo(20, 14); window.__town.step(40); }); await pq.screenshot({ path: out + 'town-390-' + q + '.png' }); await pq.close(); }
  const pd = await open(mob, 'q=high&tod=day&hud=0'); await pd.evaluate(() => { window.__town.stop(); window.__town.teleportTo(20, 14); window.__town.step(40); }); await pd.screenshot({ path: out + 'town-390-day-high.png' }); await pd.close();
  // ---- 桌面 ----
  const desk = await browser.newContext({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1 });
  const pk = await open(desk, 'q=high&tod=night&hud=1'); await pk.evaluate(() => { window.__town.teleportTo(20, 14); }); await pk.keyboard.down('ArrowRight'); await pk.waitForTimeout(500); await pk.keyboard.up('ArrowRight');
  s = await st(pk); T(s.tx > 20, '桌面鍵盤向右行 tx=' + s.tx); await pk.screenshot({ path: out + 'town-desktop-1280x720.png' });
  // 鍵盤撞牆：由 (6,12) 向上（房屋 house_a 於 x3–7、base row 9）
  await pk.evaluate(() => window.__town.teleportTo(5, 12)); await pk.keyboard.down('ArrowUp'); await pk.waitForTimeout(1500); await pk.keyboard.up('ArrowUp'); s = await st(pk);
  T(s.ty === 10, '撞房屋牆停喺 row 10（牆腳印 row 7–9 碰撞）ty=' + s.ty);
  console.log(log.join('\n')); console.log(errs.length ? 'CONSOLE ISSUES:\n' + errs.join('\n') : 'NO CONSOLE ERRORS / WARNINGS'); console.log(fails ? fails + ' FAIL' : 'ALL PASS');
  await browser.close(); process.exit(fails ? 1 : 0);
})();
