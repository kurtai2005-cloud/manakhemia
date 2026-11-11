#!/usr/bin/env node
/* b7278cf 頁面：?weather=fog 之後照顧，菇傘 +0.5。唔改 code branch。 */
'use strict';
const path = require('path');
let chromium;
for (const p of [process.env.PW, 'playwright-core']) {
  try { if (p) { chromium = require(p).chromium; break; } } catch (e) { /* next */ }
}
if (!chromium) { console.error('找不到 playwright-core'); process.exit(2); }
const BASE = process.env.BASE || 'http://127.0.0.1:8241/index.html';
let pass = 0, fail = 0;
const ok = (c, n, info) => { if (c) { pass++; console.log('  ✓ ' + n); } else { fail++; console.log('  ✗ ' + n + (info !== undefined ? '  → ' + JSON.stringify(info) : '')); } };

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROME || '/usr/bin/google-chrome', args: ['--no-sandbox'] });
  const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
  const q = '?q=high&hour=13&seed=7&ev=0&dev=1&weather=fog';
  await page.goto(BASE + q);
  await page.evaluate(() => { window.__noSaveOnHide = true; localStorage.clear(); });
  await page.goto(BASE + q);
  await page.waitForFunction(() => window.__glimmer && window.Glimmer && Glimmer.sim);
  await page.waitForTimeout(400);
  const r = await page.evaluate(() => {
    const G = window.__glimmer, S = Glimmer.sim, s = G.state;
    s.stage = 'sprout'; s.growthSec = 0; s.needs.hunger = 40; s.sleeping = false;
    s.evo.b5 = {};
    const wx = S.weatherNow();
    S.noteCare(s, 13, 'play');
    const afterPlay = s.evo.b5.sprout.shroom;
    s.evo.b5 = {};
    Glimmer.sim.feed(s, 'meal');
    const afterFeed = s.evo.b5.sprout.shroom;
    S.setWeatherFn(() => 'clear'); s.evo.b5 = {}; S.noteCare(s, 13, 'feed');
    const clearFeed = s.evo.b5.sprout ? s.evo.b5.sprout.shroom || 0 : 0;
    const route = Glimmer.data.PARAMS.evo6.branch.weather.route.fog;
    return { wx, afterPlay, afterFeed, clearFeed, route };
  });
  ok(r.wx === 'fog', '?weather=fog → weatherNow 係 fog', r.wx);
  ok(r.route && r.route.to === 'shroom' && r.route.w === 0.5, '頁面 config route.fog.w＝0.5', r.route);
  ok(Math.abs(r.afterPlay - 0.5) < 1e-6, '霧天玩：菇傘 +0.5', r.afterPlay);
  ok(Math.abs(r.afterFeed - 0.5) < 1e-6, '霧天餵：菇傘 +0.5', r.afterFeed);
  ok(Math.abs(r.clearFeed) < 1e-6, '晴天餵：菇傘 0', r.clearFeed);
  await browser.close();
  console.log(`結果：${pass} 通過，${fail} 失敗`);
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
