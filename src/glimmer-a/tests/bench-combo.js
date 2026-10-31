/* 低端機 bench：before（原版 :8139）vs after（合併版 :8138：cache 開／?hdcache=0／?hd2d=0）
   CDP CPU throttle（4× 中端、6× 低端），G.bench(quality, n) 量 renderer.frame（含 HD-2D 合成＋放大）ms/幀 */
const { chromium } = require(process.env.PW || 'playwright-core');
const BEFORE = process.env.BEFORE || 'http://localhost:8139/index.html', AFTER = process.env.AFTER || 'http://localhost:8138/index.html';
(async () => {
  const browser = await chromium.launch({ executablePath: '/usr/bin/google-chrome', args: ['--no-sandbox'] });
  const out = [];
  const cfgs = [
    ['before 原版（無 HD-2D）', BEFORE, ''],
    ['after HD-2D cache 開', AFTER, ''],
    ['after HD-2D cache 關（?hdcache=0）', AFTER, '&hdcache=0'],
    ['after ?hd2d=0 fallback', AFTER, '&hd2d=0'],
    ['after H3rain cache 開', AFTER, '&scene=H3rain'],
    ['after H3rain cache 關', AFTER, '&scene=H3rain&hdcache=0'],
  ];
  for (const [rate, tier, q] of [[4, '中端（4× throttle）', 'mid'], [6, '低端（6× throttle）', 'low']]) {
    for (const [name, base, extra] of cfgs) {
      const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2 });
      const page = await ctx.newPage(); const cdp = await ctx.newCDPSession(page);
      await page.goto(base + '?debug=1&hour=13&seed=11&ev=0&q=' + q + (extra.includes('scene') ? extra : '&scene=H2' + extra));
      await page.waitForFunction(() => window.__glimmer && __glimmer.renderer && __glimmer.state, null, { timeout: 20000 });
      await page.evaluate(() => { const s = __glimmer.state; s.stage = 'adult'; s.form = 'soft'; s.growthSec = 3600; Object.assign(s.needs, { hunger: 100, mood: 100, clean: 100, energy: 100 }); s.poops = 0; });
      await page.waitForTimeout(1500);
      await cdp.send('Emulation.setCPUThrottlingRate', { rate });
      const runs = []; for (let i = 0; i < 3; i++) runs.push(await page.evaluate((q) => __glimmer.bench(q, 120), q));
      const med = runs.map(r => r.avgMs).sort((a, b) => a - b)[1];
      const st = await page.evaluate(() => window.__qa && __qa.hd2d && __qa.hd2d.cache ? __qa.hd2d.cache() : null).catch(() => null);
      const line = tier + ' q=' + q + ' | ' + name + ' | ' + JSON.stringify({ med, runs: runs.map(r => r.avgMs), maxMs: Math.max(...runs.map(r => r.maxMs)), cache: st && { on: st.on, builds: st.builds, hits: st.hits } });
      console.log(line); out.push(line); await ctx.close();
    }
  }
  require('fs').writeFileSync(require('path').join(__dirname, 'last-run-bench-combo.txt'), out.join('\n') + '\n');
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
