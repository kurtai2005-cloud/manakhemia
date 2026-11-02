/* 《微光小圃》 e2e-uikit2 — 4b.1 HD-2D UI kit v2（art/ui_hd2d_v2；UI_KIT_V2.md／PORTRAIT_SYNC.md）：預設 v2、?ui=1 → v1、🛠「UI v2」即時切換＋逐個彈窗、
   字型（Fusion Pixel）、9-slice tile／pixelated、layout 排位（×2）、頭像即場裁（心情／rect）、屋仔／細佬卡／設定／開發者面板換皮、功能照舊、冇 console error。
   截圖 → SHOTS（uikit2-*.png）。node tests/e2e-uikit2.js（BASE 預設 http://localhost:8240/index.html） */
const path = require('path');
let chromium;
for (const p of [process.env.PW, 'playwright-core', '/workspace/qa-live-s1/node_modules/playwright-core']) { try { if (p) { chromium = require(p).chromium; break; } } catch (e) { } }
if (!chromium) { console.error('找不到 playwright-core'); process.exit(2); }
const BASE = process.env.BASE || 'http://localhost:8240/index.html';
const SHOTS = process.env.SHOTS || process.env.OUT || path.join(__dirname, '..', '..', '..', 'screens') + '/';
require('fs').mkdirSync(SHOTS, { recursive: true });
let pass = 0, fail = 0;
const ok = (c, n, info) => { if (c) { pass++; console.log('  ✓ ' + n); } else { fail++; console.log('  ✗ ' + n + (info !== undefined ? ' → ' + JSON.stringify(info) : '')); } };
const T0 = new Date(2026, 10, 2, 13, 0).getTime();
const near = (a, b, d) => Math.abs(a - b) <= (d || 2);

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROME || '/usr/bin/google-chrome', args: ['--no-sandbox', '--autoplay-policy=no-user-gesture-required'] });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2 });
  const page = await ctx.newPage();
  const errs = [];
  page.on('console', m => { if (m.type() === 'error') errs.push(m.type() + ': ' + m.text()); });
  page.on('pageerror', e => errs.push('pageerror: ' + e.message));
  const E = (fn, arg) => page.evaluate(fn, arg);
  const W = (ms) => page.waitForTimeout(ms);
  const shot = (n) => page.screenshot({ path: SHOTS + 'uikit2-' + n + '.png' });
  const u = () => E(() => __qa.uiv2.st());
  const setT = (t) => E((t) => { __glimmer.clock.fake = true; __glimmer.clock.t = t; }, t);
  const prep = () => E(() => { window.__noSaveOnHide = true; const s = __glimmer.state; s.stage = 'adult'; s.form = 'dust'; s.sleeping = false; Object.assign(s.needs, { mood: 50, energy: 100, hunger: 60, clean: 100 }); s.poops = 0; });
  const load = async (qs, clear) => {
    qs += '&ui63=0';   // 6b.3：呢個 suite 驗 6b.2 原尺寸 layout；縮細層由 e2e-6b3 驗
    if (clear !== false) { await page.goto(BASE + '?' + qs); await E(() => { window.__noSaveOnHide = true; localStorage.clear(); }); }
    await page.goto(BASE + '?' + qs); await page.waitForFunction(() => window.__glimmer && __glimmer.liveLoad).catch(() => { }); await E(() => __glimmer.liveLoad);
    await E(() => __glimmer.s2Load); await E(() => __glimmer.houseLoad);
    await page.waitForFunction(() => window.__qa && __qa.uiv2 && __qa.uiv2.st().ready, null, { timeout: 15000 }).catch(() => { });
    await setT(T0); if (clear !== false) await prep(); await W(500);
  };
  const closeModals = async () => { for (let i = 0; i < 10; i++) { const open = await E(() => Glimmer.ui.isModalOpen()); if (!open) break; await E(() => { const b = [...document.querySelectorAll('#mbox .btn')].pop(); if (b) b.click(); }); await W(150); } await E(() => { if (__glimmer.s12close) __glimmer.s12close(); if (Glimmer.ui.closePop) Glimmer.ui.closePop(); if (__qa.house && __qa.house.st().open) __qa.house.close(); }); await W(300); };
  const openDev = async () => { await closeModals(); await E(() => __qa.devmode.setShown(true)); await W(100); await page.locator('[data-testid=dev-btn]').click(); await W(400); };
  const dev = async (k) => { await openDev(); await page.locator('[data-testid=dev-uiv2-' + k + ']').click(); await W(700); };
  const box = (sel) => E((sel) => { const e = document.querySelector(sel); if (!e) return null; const r = e.getBoundingClientRect(), u = document.getElementById('ui').getBoundingClientRect(); return { x: r.x - u.x, y: r.y - u.y, w: r.width, h: r.height }; }, sel);
  const cs = (sel, props) => E(([sel, props]) => { const e = document.querySelector(sel); if (!e) return null; const c = getComputedStyle(e); const o = {}; props.forEach(p => o[p] = c.getPropertyValue(p)); return o; }, [sel, props]);
  const toKid = async () => { await E(() => { const G = __glimmer, SR = Glimmer.series2, s = G.state, now = G.now(); s.stage = 'elder'; SR.noteElder(s, now - 6 * 86400e3); const o = SR.st(s); o.dueDay = SR.dayNum(now) - 6; SR.deliver(s, now - 5 * 86400e3);
    o.dreams = [{ day: 1, line: 'A', at: 0, live: true }, { day: 2, line: 'A', at: 0, live: true }, { day: 3, line: 'E', at: 0, live: true }]; SR.hatch(s, now - 1 * 86400e3); o.relQ.length = 0; G.save(); }); await W(400); };

  console.log('# ① 預設 v2：載入、字型、零件');
  await load('q=high&hour=13&seed=21&ev=0');
  let S = await u();
  ok(S.ready && S.on, '預設開 UI v2', S);
  ok(!S.errors.length && !S.missing.length, 'kit 零件／icons 冇缺、冇錯', { e: S.errors, m: S.missing });
  ok(S.fonts.GlimmerFP12 && !S.fonts.GlimmerFP8 && !S.fonts.GlimmerFP10, 'Fusion Pixel 12 載入（5a.2：FP8／FP10 唔再載）', S.fonts);
  ok(await E(() => document.getElementById('ui').classList.contains('v2') && document.body.classList.contains('uiv2')), '#ui.v2＋body.uiv2');
  ok(await E(() => document.fonts.check('24px GlimmerFP12') && ![...document.fonts].some(f => /GlimmerFP(8|10)/.test(f.family))), 'document.fonts 有 GlimmerFP12、冇 FP8／FP10');
  { const c = await cs('#stagename', ['font-family', 'font-size']); ok(c && /GlimmerFP12/.test(c['font-family']) && c['font-size'] === '24px', '名牌用 FP12 24px（×2）', c); }
  { const c = await cs('#hdBan2', ['border-image-repeat', 'image-rendering', 'border-image-source']); ok(c && /repeat/.test(c['border-image-repeat']) && !/stretch/.test(c['border-image-repeat']) && c['image-rendering'] === 'pixelated' && /^url\(/.test(c['border-image-source']), '9-slice：border-image repeat（tile）＋pixelated', c && { r: c['border-image-repeat'], i: c['image-rendering'] }); }
  ok(await E(() => [...document.styleSheets].every(s => { try { return ![...s.cssRules].some(r => /border-image[^;]*stretch/.test(r.cssText) && /#ui\.hd\.v2/.test(r.cssText)); } catch (e) { return true; } })), 'v2 CSS 冇 border-image stretch');
  ok(await E(() => { const e = __qa.uiv2.part('card_sel'); return e && e.w > 0 && e.h > 0; }), 'part(card_sel) 有尺寸');

  console.log('# ② layout 排位（layout_hd2d_v2 ×2）');
  const L = await E(() => __qa.uiv2.layout());
  { const b = await box('#hdBan2'); ok(b && near(b.x, L.banner.x * 2) && near(b.y, L.banner.y * 2) && near(b.w, L.banner.w * 2) && near(b.h, L.banner.h * 2), 'banner ' + JSON.stringify(L.banner && [L.banner.x, L.banner.y, L.banner.w, L.banner.h]) + ' ×2', b); }
  { const b = await box('.hdFace2'); ok(b && near(b.x, L.portrait.x * 2) && near(b.y, L.portrait.y * 2) && near(b.w, L.portrait.w * 2), '頭像 ' + L.portrait.w + '×' + L.portrait.h + ' ×2', b); }
  { const b = await box('#diary > i.m'), h = await box('#diary'), R = S.rail.mail, dy = await E(() => document.getElementById('ui').classList.contains('u62') ? -10 : 0); ok(b && near(b.x + b.w / 2, R.x, 3) && near(b.y + b.h / 2, R.y + dy, 3) && near(b.w, 48) && h.w >= 64, 'rail 信件 card_sel 24×24×2 喺 layout 位（撳位 ≥64）', { b, h, R }); }
  { const b = await box('#s12chip .q'), R = S.rail.gift; ok(b && near(b.x + b.w / 2, R.x, 3) && near(b.y + b.h / 2, R.y, 3), 'rail 委託（gift）喺 layout 位', { b, R }); }
  { const b = await box('#dex'), R = S.rail.dex; ok(b && near(b.x + b.w / 2, R.x, 3) && near(b.y + b.h / 2, R.y, 3), 'rail 圖鑑', { b, R }); }
  ok(await E(() => { const l = document.querySelector('#s12chip .hd2gl'); return l && l.textContent === '委託' && getComputedStyle(l).display !== 'none'; }), '委託字牌（ribbon）');
  await shot('01-home');

  console.log('# ③ 頭像（PORTRAIT_SYNC）');
  let F = await E(() => __qa.uiv2.face());
  ok(F && F.fk && Array.isArray(F.rect) && F.rect[2] === 22, '頭像即場裁 22×22（' + (F && F.fk) + '）', F);
  ok(F && F.hit, 'form 喺 portrait_rects 搵到', F);
  ok(await E(() => { const c = document.querySelector('.hdFace2 canvas'); const d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data; let n = 0; for (let i = 3; i < d.length; i += 4) if (d[i] > 0) n++; return n > c.width * c.height * 0.5; }), '頭像 canvas 有畫嘢');
  for (const m of ['happy', 'hungry', 'sleepy', 'sick', 'sleep', 'normal']) { const f = await E((m) => __qa.uiv2.mood(m), m); ok(f && f.mood === m, '心情 ' + m + ' → bg_' + m, f && f.mood); }
  await E(() => __qa.uiv2.mood(null)); await E(() => { __glimmer.state.needs.hunger = 10; }); await W(1300);
  F = await E(() => __qa.uiv2.face()); ok(F && F.mood === 'hungry', '狀態肚餓 → 頭像 hungry', F && F.mood); await E(() => { __glimmer.state.needs.hunger = 60; });
  { const a = await E(() => { const R = __qa.uiv2.face(); const k = R && R.accKeys && R.accKeys[0]; return k ? __qa.uiv2.acc(k) : { skip: true }; }); ok(a && (a.skip || a.acc), '配件 shift／badge（QA）', a); await E(() => __qa.uiv2.acc(null)); }

  console.log('# ④ 🛠 開發者「UI v2」');
  const secs = await E(() => __qa.devmode.sections());
  const sec = secs.find(x => x.id === 'uiv2');
  const KEYS = ['toggle', 'settings', 'dex', 'journal', 'garden', 'feed', 'popup', 'toast', 'kid', 'house', 'deco', 'mood', 'sysf', 'reset'];
  ok(sec && JSON.stringify(sec.items) === JSON.stringify(KEYS), '「UI v2」組 14 個掣（5a.1 加「清晰字型（系統字）」）', sec);
  ok(secs.some(x => x.id === 's2') && secs.some(x => x.id === 'house'), '4a／4b 組照舊');
  await openDev(); ok(await page.locator('[data-testid=dev-sec-uiv2]').isVisible(), '開發者面板有「UI v2」'); ok((await page.locator('[data-testid=dev-version]').innerText()).match(/版本 (5[abc]|6[ab])/), '版本 5a');
  ok(!(await E(() => !!document.querySelector('#mbox [data-testid=dev-sec-uiv2]') && document.getElementById('mbox').dataset.kind === 's2Settings')), '唔喺設定');
  await shot('02-devpanel');
  await dev('toggle'); S = await u(); ok(!S.on && !(await E(() => document.getElementById('ui').classList.contains('v2'))), '撳切換 → v1（即時）', S.on);
  ok(await E(() => localStorage.getItem('glimmer.ui') === '1'), '記低 glimmer.ui=1'); await shot('03-toggled-v1');
  ok(await E(() => getComputedStyle(document.getElementById('hdBan2')).display === 'none'), 'v1 冇 v2 banner');
  await dev('toggle'); S = await u(); ok(S.on && await E(() => localStorage.getItem('glimmer.ui') === '2'), '再撳 → v2', S.on);
  const pops = [
    ['settings', () => Glimmer.ui.isModalOpen(), '設定'],
    ['dex', () => Glimmer.ui.isModalOpen() || !!document.querySelector('#dexp.on, .dexOpen, #ui.hdPage'), '圖鑑'],
    ['journal', () => !!document.querySelector('#s12p.on, #s12p.open') || (__glimmer.s12 && __glimmer.s12.open), '手帳'],
    ['garden', () => (__glimmer.s12 && __glimmer.s12.open) || Glimmer.ui.isModalOpen(), '小圃'],
    ['feed', () => !!document.querySelector('#pop.on, #pop.show, #pop:not([hidden])') && getComputedStyle(document.getElementById('pop')).display !== 'none', '餵食選單'],
    ['popup', () => document.getElementById('mbox').dataset.kind === 'uiv2Sample', '示範彈窗'],
    ['toast', () => /收到小禮物/.test((window.__toasts || []).join('|') + (document.getElementById('toast') || {}).textContent), 'toast'],
  ];
  for (const [k, fn, nm] of pops) { await dev(k); const r = await E(fn); ok(!!r, '「' + nm + '」掣開到', k); await shot('10-' + k); await closeModals(); }
  { await dev('popup'); const p = await box('#mbox'); const c = await cs('#mbox', ['border-image-source', 'font-family']); ok(p && near(p.w, L.popup.w * 2, 4), '彈窗寬 ' + L.popup.w + '×2', p); ok(c && (/^url/.test(c['border-image-source']) || await E(() => document.getElementById('ui').classList.contains('u62') && getComputedStyle(document.getElementById('mbox')).borderTopLeftRadius === '14px')), '彈窗 panel 9-slice（6b.2：CSS 金邊面板取代）', c && c['border-image-source'].slice(0, 20)); await closeModals(); }
  { await dev('settings'); ok(await page.locator('[data-testid=uiv2-font-credit]').isVisible(), '設定有「字型：Fusion Pixel（OFL 1.1）」'); ok((await page.locator('[data-testid=s2-version]').innerText()).match(/版本 (5[abc]|6[ab])/), '設定版本行'); await closeModals(); }
  await dev('mood'); ok((await u()).moodOv, '「頭像心情」輪住睇'); await dev('reset'); ok(!(await u()).moodOv, '「頭像還原」');

  console.log('# ⑤ 細佬卡／屋仔換皮（功能照舊）');
  await toKid(); await E(() => __qa.s2.test('family')); await W(800);
  { const b = await box('[data-testid=s2-rail-house]'), R = S.rail.house, dy = await E(() => document.getElementById('ui').classList.contains('u62') ? 6 : 0); ok(b && near(b.x + b.w / 2, R.x, 3) && near(b.y + b.h / 2, R.y + dy, 3) && near(b.w, 48), 'rail 屋仔喺 layout 位', { b, R }); }
  { const b = await box('[data-testid=s2-rail-kid]'), R = S.rail.kid; ok(b && near(b.x + b.w / 2, R.x, 3) && near(b.y + b.h / 2, R.y, 3), 'rail 細佬', { b, R }); }
  await dev('kid'); ok(await E(() => document.getElementById('mbox').dataset.kind === 's2Card'), '「睇細佬卡」→ 細佬卡'); await shot('20-kidcard');
  { const c = await cs('#mbox', ['border-image-source']); ok(c && (/^url/.test(c['border-image-source']) || await E(() => document.getElementById('ui').classList.contains('u62') && getComputedStyle(document.getElementById('mbox')).borderTopLeftRadius === '14px')), '細佬卡用 v2 panel（6b.2：CSS 金邊面板）'); } await closeModals();
  await dev('house'); ok(await E(() => __qa.house.st().open), '「睇屋仔」→ 屋仔'); await W(800); await shot('21-house');
  { const b = await box('[data-testid=house-back]'), H = L.house4b; ok(b && near(b.x + b.w / 2, H.back[0] * 2, 2) && near(b.y + b.h / 2, H.back[1] * 2, 2) && near(b.w, Math.max(48, H.back[2] * 2)) && b.h >= 48, '屋仔返回掣喺 house4b.back（5a.2 熱區 ≥48）', { b, back: H.back }); }
  { const c = await cs('[data-testid=house-title]', ['font-family', 'border-image-source']); ok(c && /GlimmerFP/.test(c['font-family']), '屋仔標題用 Fusion Pixel', c && c['font-family']); }
  await E(() => { Glimmer.sys12.st(__glimmer.state).wallet.total += 200; }); await dev('deco'); await W(600);
  ok(await E(() => __qa.house.st().deco), '「睇佈置」→ 佈置'); await shot('22-decorate');
  { const b = await box('[data-testid=house-sheet]'), H = L.house4b; ok(b && near(b.y, H.sheet[1] * 2, 6) && near(b.w, H.sheet[2] * 2, 6), '佈置 sheet 喺 house4b.sheet', { b, s: H.sheet }); }
  { const n = await page.locator('#s2houseV .card').count(); ok(n >= 2, '家具卡 ' + n); }
  { const before = await E(() => JSON.stringify([__qa.house.st().save, __qa.house.st().wallet])); await page.locator('[data-testid=house-tab-bed]').click().catch(() => { }); await W(300);
    const c = page.locator('#s2houseV .card[data-state=owned], #s2houseV .card[data-state=buy]').first(); if (await c.count()) { await c.click(); await W(500); }
    const after = await E(() => JSON.stringify([__qa.house.st().save, __qa.house.st().wallet])); ok(after !== before || await E(() => !!document.querySelector('#s2houseV .card[data-state=equipped]')), '撳卡（買／擺）照行', { before, after }); }
  for (let i = 0; i < 5 && await E(() => Glimmer.ui.isModalOpen()); i++) { await E(() => { const b = [...document.querySelectorAll('#mbox .btn')].pop(); if (b) b.click(); }); await W(200); }
  await shot('23-after-card'); await page.locator('[data-testid=house-done]').click({ timeout: 3000 }).catch((e) => console.log('done click', e.message.slice(0, 200))); await W(500); ok(!(await E(() => __qa.house.st().deco)), '「完成」收起佈置');
  await closeModals();

  console.log('# ⑥ 功能照舊（v2）');
  { const h0 = await E(() => __glimmer.state.needs.hunger); await page.locator('[data-testid=feed]').click(); await W(500); const it = page.locator('#pop .it, #pop [data-testid^=food-], #pop .row').first(); if (await it.count()) { await it.click(); await W(1500); } const h1 = await E(() => __glimmer.state.needs.hunger); ok(h1 >= h0, '餵食照行（肚餓 ' + h0 + ' → ' + h1 + '）'); await closeModals(); }
  ok(await E(() => !!(Glimmer.uisfx && typeof Glimmer.uisfx === 'object')), 'ui8 v3 音效模組照喺度');
  ok(await E(() => !!document.querySelector('#hdDock .hdTab')), 'dock 5 格照舊');

  console.log('# ⑦ ?ui=1 → v1；?ui=2 → v2');
  await load('q=high&hour=13&seed=21&ev=0&ui=1'); S = await u();
  ok(S.ready && !S.on && !(await E(() => document.getElementById('ui').classList.contains('v2'))), '?ui=1 → v1', S.on);
  ok(await E(() => document.getElementById('ui').classList.contains('hd')), 'v1 HD-2D 照用');
  ok(await E(() => getComputedStyle(document.getElementById('hdBan2')).display === 'none'), 'v1 唔見 v2 banner');
  await shot('30-v1');
  await load('q=high&hour=13&seed=21&ev=0', true); await E(() => localStorage.setItem('glimmer.ui', '1')); await load('q=high&hour=13&seed=21&ev=0', false); ok(!(await u()).on, 'localStorage=1 → v1');
  await load('q=high&hour=13&seed=21&ev=0&ui=2', false); ok((await u()).on, '?ui=2 蓋過 → v2');
  await load('q=high&hour=13&seed=21&ev=0&hdui=0'); ok(await E(() => !document.getElementById('ui').classList.contains('v2')), '?hdui=0 → 冇 HD-2D（v2 都唔開）');

  const bad = errs.filter(e => !/favicon|ERR_FILE_NOT_FOUND|net::/.test(e)); ok(!bad.length, '冇 console error', bad);
  console.log('\n' + pass + ' 過／' + fail + ' 唔過'); await browser.close(); process.exit(fail ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
