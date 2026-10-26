const { chromium } = require('playwright-core');
(async () => {
  const browser = await chromium.launch({ executablePath: '/usr/bin/google-chrome', args: ['--no-sandbox'] });
  const ctx = await browser.newContext({ viewport: { width: 540, height: 960 }, hasTouch: true });
  const page = await ctx.newPage();
  const errs = [];
  page.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') errs.push(m.type() + ': ' + m.text()); });
  page.on('pageerror', e => errs.push('pageerror: ' + e.message));
  await page.goto((process.env.BASE || 'http://localhost:8123/') + 'index.html');
  await page.evaluate(() => localStorage.clear());
  await page.reload();
  await page.waitForTimeout(600);
  const out = require('path').join(__dirname, '../screens') + '/';
  const tap = async (x, y, w) => { await page.mouse.click(x, y); await page.waitForTimeout(w || 150); };
  const st = () => page.evaluate(() => { const G = __wr.G; return { scene: G.scene, over: G.race && G.race.sim.over, t: G.race && +G.race.sim.t.toFixed(1), pos: G.race && G.race.sim.sides.map(s => Math.round(s.pos)) }; });
  await page.screenshot({ path: out + '01-menu.png' });
  await tap(270, 400);                       // 開始遊戲
  await tap(100, 810); await tap(100, 810);  // 餵食 x2
  await tap(270, 810); await tap(100, 810);  // 訓練 → 速度
  await page.screenshot({ path: out + '02-train.png' });
  await tap(270, 906);                       // 去組隊
  // 關卡1：揀 苔團 + 碎石獾
  await tap(145, 520); await tap(145 + 260, 520 + 104 * 1 - 104 + 0);
  await page.evaluate(() => { const G = __wr.G; G.teamPick = ['mochi', 'gravelbadger']; });
  await page.screenshot({ path: out + '03-team.png' });
  await tap(335, 906);                       // 出賽
  await page.waitForTimeout(3600);
  await page.screenshot({ path: out + '04-race-start.png' });
  await page.waitForTimeout(25000);
  await page.screenshot({ path: out + '05-race-mid.png' });
  // 技能 + 換人
  await tap(270, 640);
  await page.waitForTimeout(400);
  await tap(270, 820);                       // 後備頭像
  await page.waitForTimeout(700);
  await page.screenshot({ path: out + '06-race-swap-skill.png' });
  await tap(480, 26);                        // 2x
  while (!(await st()).over) await page.waitForTimeout(500);
  await page.waitForTimeout(300);
  await page.screenshot({ path: out + '07-race-finish.png' });
  console.log('race end', JSON.stringify(await st()));
  await tap(270, 370);                       // 看結算
  await page.waitForTimeout(300);
  await page.screenshot({ path: out + '08-result.png' });
  console.log('save', await page.evaluate(() => localStorage.getItem('windrun_save_v1').slice(0, 160)));
  // 其餘關卡截圖：直接進入
  for (const id of [2, 3]) {
    await page.evaluate((id) => { const G = __wr.G; G.save.cleared[1] = true; G.save.cleared[2] = true; G.stageSel = id; G.teamPick = id === 2 ? ['namifin', 'frostdeer', 'mochi'] : ['narrowcat', 'tingyu', 'mistfern']; G.scene = 'team'; }, id);
    await page.waitForTimeout(200);
    if (id === 3) await page.screenshot({ path: out + '09-team-stage3.png' });
    await tap(335, 906);
    await page.waitForTimeout(3600 + 20000);
    if (id === 3) { await page.screenshot({ path: out + '10-race-stage3-mid.png' }); }
    await tap(480, 26);
    let n = 0; while (!(await st()).over && n++ < 120) await page.waitForTimeout(500);
    console.log('stage', id, JSON.stringify(await st()));
    await page.screenshot({ path: out + '11-stage' + id + '-end.png' });
    await tap(270, 370); await page.waitForTimeout(200);
  }
  await tap(270, 880); // 主頁 button at (20..) 
  await page.evaluate(() => { __wr.G.scene = 'howto'; }); await page.waitForTimeout(200);
  await page.screenshot({ path: out + '12-howto.png' });
  await browser.close();
  console.log(errs.length ? 'CONSOLE:\n' + errs.join('\n') : 'NO CONSOLE ERRORS / WARNINGS');
})();
