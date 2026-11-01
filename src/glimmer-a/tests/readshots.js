/* 5a.1 字清晰度：360×780 DPR3 截 7 個畫面（設定、圖鑑、手帳、開發者面板、細佬卡、屋仔、主畫面）＋審查（字號／字型／對比）
   node tests/readshots.js <前綴> [qs]   → SHOTS/<前綴>-<畫面>.png ＋ <前綴>-audit.json */
const path = require('path'), fs = require('fs'); let chromium;
for (const p of [process.env.PW, 'playwright-core', '/workspace/qa-live-s1/node_modules/playwright-core']) { try { if (p) { chromium = require(p).chromium; break; } } catch (e) { } }
const { audit } = require('./readaudit.js');
const BASE = process.env.BASE || 'http://localhost:8240/index.html', TAG = process.argv[2] || 'read', QS = process.argv[3] || '';
const SHOTS = process.env.SHOTS || path.join(__dirname, '..', '..', '..', 'screens') + '/'; fs.mkdirSync(SHOTS, { recursive: true });
const T0 = new Date(2026, 10, 2, 13, 0).getTime();
(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROME || '/usr/bin/google-chrome', args: ['--no-sandbox', '--autoplay-policy=no-user-gesture-required'] });
  const ctx = await browser.newContext({ viewport: { width: 360, height: 780 }, deviceScaleFactor: 3 }); const page = await ctx.newPage();
  const errs = []; page.on('pageerror', e => errs.push(e.message));
  const E = (fn, a) => page.evaluate(fn, a), W = (ms) => page.waitForTimeout(ms);
  await page.goto(BASE + '?q=high&hour=13&seed=21&ev=0' + QS); await E(() => { window.__noSaveOnHide = true; localStorage.clear(); });
  await page.goto(BASE + '?q=high&hour=13&seed=21&ev=0' + QS); await page.waitForFunction(() => window.__glimmer && __glimmer.liveLoad); await E(() => __glimmer.liveLoad); await E(() => __glimmer.s2Load); await E(() => __glimmer.houseLoad);
  await page.waitForFunction(() => window.__qa && __qa.uiv2 && __qa.uiv2.st().ready, null, { timeout: 15000 }).catch(() => { });
  await E((t) => { __glimmer.clock.fake = true; __glimmer.clock.t = t; const s = __glimmer.state; s.stage = 'adult'; s.form = 'dust'; s.sleeping = false; Object.assign(s.needs, { mood: 70, energy: 100, hunger: 80, clean: 100 }); s.poops = 0; }, T0);
  if (process.env.SYSF) await E(() => __qa.uiv2.sysFont && __qa.uiv2.sysFont(true));
  // 細佬家人（屋仔／細佬卡要）

  const closeAll = async () => { for (let i = 0; i < 8; i++) { const o = await E(() => Glimmer.ui.isModalOpen()); if (!o) break; await E(() => { const b = [...document.querySelectorAll('#mbox .btn')].pop(); if (b) b.click(); }); await W(150); }
    await E(() => { if (__glimmer.s12close) __glimmer.s12close(); if (window.__qa.house && __qa.house.st().open) __glimmer.house5 && __glimmer.house5.close(); if (__qa.l5) __qa.l5.close(); }); await W(300); };
  const openDev = async () => { await closeAll(); await E(() => __qa.devmode.setShown(true)); await W(100); await page.locator('[data-testid=dev-btn]').click(); await W(500); };
  const run = async (sec, k) => { await openDev(); await page.locator('[data-testid=dev-' + sec + '-' + k + ']').click(); await W(2000); };
  await run('house', 'prep'); await closeAll();
  const res = {};
  const one = async (name, open, root) => { await open(); const a = await audit(page, root); await page.screenshot({ path: SHOTS + TAG + '-' + name + '.png' }); res[name] = { n: a.items.length, bad: a.bad.length, minEff: Math.min(...a.items.map(i => i.eff)), minCr: Math.min(...a.items.map(i => i.cr)), fams: [...new Set(a.items.map(i => i.fam + '@' + i.fs))], worst: a.bad.slice(0, 12).map(i => ({ t: i.t, tid: i.tid, fs: i.fs, eff: i.eff, fam: i.fam, cr: i.cr })) };
    console.log(name.padEnd(9), 'texts', a.items.length, 'bad', a.bad.length, 'minEff', res[name].minEff, 'minCr', res[name].minCr); };
  await one('settings', () => run('uiv2', 'settings'), '#mbox');
  await one('dex', () => run('uiv2', 'dex'), null);
  await one('journal', () => run('uiv2', 'journal'), null);
  await one('dev', openDev, '#mbox');
  await one('kidcard', () => run('uiv2', 'kid'), '#mbox');
  await one('house', () => run('uiv2', 'house'), null);
  await one('garden', closeAll, null);
  fs.writeFileSync(SHOTS + TAG + '-audit.json', JSON.stringify(res, null, 1)); if (errs.length) console.log('errors', errs.slice(0, 3));
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
