/* 瀏覽器端：玩一場 → 結算 → 重播，確認重播最終雜湊＝原場。BASE=http://localhost:8131/ node tests/e2e-replay.js */
const { chromium } = require('playwright-core');
(async () => {
  const browser = await chromium.launch({ executablePath: '/usr/bin/google-chrome', args: ['--no-sandbox'] });
  const ctx = await browser.newContext({ viewport: { width: 540, height: 960 }, hasTouch: true });
  const page = await ctx.newPage();
  const errs = [];
  page.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') errs.push(m.type() + ': ' + m.text()); });
  page.on('pageerror', e => errs.push('pageerror: ' + e.message));
  await page.goto((process.env.BASE || 'http://localhost:8123/') + 'index.html');
  await page.evaluate(() => localStorage.clear()); await page.reload(); await page.waitForTimeout(500);
  const out = require('path').join(__dirname, '../screens') + '/';
  await page.evaluate(() => { const G = __wr.G; G.stageSel = 1; G.teamPick = ['mochi', 'gravelbadger']; G.startRace(); });
  await page.waitForTimeout(3600);
  await page.mouse.click(270, 640); await page.waitForTimeout(8000);   // 技能
  await page.mouse.click(270, 820);                                      // 換人
  await page.waitForTimeout(500);
  await page.mouse.click(480, 26);                                       // 2x
  await page.waitForFunction(() => __wr.G.race.match.race.over, null, { timeout: 120000 });
  await page.waitForTimeout(300);
  const live = await page.evaluate(() => { const G = __wr.G, m = G.race.match; return { hash: __wr.Api.hex8(__wr.Sim.hashState(m.race)), steps: m.race.stepN, winner: m.race.winner, dec: G.lastReplay.decisions.length, rp: G.lastReplay.result.finalHash }; });
  console.log('live', JSON.stringify(live));
  await page.mouse.click(270, 370); await page.waitForTimeout(300);       // 看結算
  await page.screenshot({ path: out + 'replay-result-btn.png' });
  await page.mouse.click(270, 704); await page.waitForTimeout(1500);      // 重播
  await page.screenshot({ path: out + 'replay-playing.png' });
  await page.mouse.click(480, 26); await page.mouse.click(480, 26);       // 4x
  await page.waitForFunction(() => __wr.G.scene === 'race' && __wr.G.race.isReplay && __wr.G.race.match.race.over, null, { timeout: 120000 });
  const rep = await page.evaluate(() => { const m = __wr.G.race.match; return { hash: __wr.Api.hex8(__wr.Sim.hashState(m.race)), steps: m.race.stepN, winner: m.race.winner, err: m.verifyError }; });
  console.log('replay', JSON.stringify(rep));
  const ok = rep.hash === live.hash && rep.steps === live.steps && rep.winner === live.winner && !rep.err && live.hash === live.rp;
  const racesBefore = await page.evaluate(() => __wr.G.save.races);
  await page.mouse.click(270, 370); await page.waitForTimeout(300);
  const after = await page.evaluate(() => ({ scene: __wr.G.scene, races: __wr.G.save.races }));
  console.log('back to result', JSON.stringify(after), 'races unchanged:', after.races === racesBefore);
  await browser.close();
  console.log(errs.length ? 'CONSOLE:\n' + errs.join('\n') : 'NO CONSOLE ERRORS / WARNINGS');
  console.log(ok && after.scene === 'result' && after.races === racesBefore ? 'E2E REPLAY PASS' : 'E2E REPLAY FAIL');
  process.exit(ok ? 0 : 1);
})();
