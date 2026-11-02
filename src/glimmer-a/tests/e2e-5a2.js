/* 5a.2 e2e：遊測 QA（qa-report-cec1e9b P2）
   ① 熱區 ≥48（#ui 版面 px）：屋仔返回／佈置返回、彈窗掣、設定分段＋開關、開發者面板掣、🛠 入口 —— 用 elementFromPoint 喺 48×48 四角＋四邊探
   ② 淺字對彩底 ≥4.5（字色本身，唔計描邊）：路線小牌、餵食／玩耍／清潔／關燈絲帶、副標、彈窗關閉、委託 tab／標題、開關、重設
   ③ 單檔唔再打包 reskin_4b／FP8／FP10；v2 唔再 FontFace 載 FP8／FP10
   node tests/e2e-5a2.js（要 localhost:8240） */
const path = require('path'), fs = require('fs'), os = require('os'), cp = require('child_process'); let chromium;
for (const p of [process.env.PW, 'playwright-core', '/workspace/qa-live-s1/node_modules/playwright-core']) { try { if (p) { chromium = require(p).chromium; break; } } catch (e) { } }
const { cr } = require('./readaudit.js');
const BASE = process.env.BASE || 'http://localhost:8240/index.html', ROOT = path.join(__dirname, '..');
const T0 = new Date(2026, 10, 2, 13, 0).getTime();
let pass = 0, fail = 0; const ok = (c, m) => { if (c) { pass++; console.log('  ✓ ' + m); } else { fail++; console.log('  ✗ ' + m); } };
(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROME || '/usr/bin/google-chrome', args: ['--no-sandbox', '--autoplay-policy=no-user-gesture-required'] });
  for (const [vw, vh] of [[360, 780], [390, 800]]) {
    console.log(`# ${vw}×${vh}`);
    const ctx = await browser.newContext({ viewport: { width: vw, height: vh }, deviceScaleFactor: 3, hasTouch: true }); const page = await ctx.newPage();
    const errs = []; page.on('pageerror', e => errs.push(e.message));
    const E = (fn, a) => page.evaluate(fn, a), W = (ms) => page.waitForTimeout(ms);
    await page.goto(BASE + '?q=high&hour=13&seed=21&ev=0'); await E(() => { window.__noSaveOnHide = true; localStorage.clear(); });
    await page.goto(BASE + '?q=high&hour=13&seed=21&ev=0'); await page.waitForFunction(() => window.__glimmer && __glimmer.liveLoad); await E(() => __glimmer.liveLoad); await E(() => __glimmer.s2Load); await E(() => __glimmer.houseLoad);
    await page.waitForFunction(() => window.__qa && __qa.uiv2 && __qa.uiv2.st().ready && __qa.uiv2.st().on, null, { timeout: 15000 });
    await E((t) => { __glimmer.clock.fake = true; __glimmer.clock.t = t; const s = __glimmer.state; s.stage = 'adult'; s.form = 'dust'; s.sleeping = false; Object.assign(s.needs, { mood: 70, energy: 100, hunger: 80, clean: 100 }); s.poops = 0; }, T0);
    const closeAll = async () => { for (let i = 0; i < 8; i++) { const o = await E(() => Glimmer.ui.isModalOpen()); if (!o) break; await E(() => { const b = [...document.querySelectorAll('#mbox .btn')].pop(); if (b) b.click(); }); await W(150); }
      await E(() => { if (__glimmer.s12close) __glimmer.s12close(); if (window.__qa.house && __qa.house.st().open) __glimmer.house5 && __glimmer.house5.close(); if (__qa.l5) __qa.l5.close(); }); await W(300); };
    const openDev = async () => { await closeAll(); await E(() => __qa.devmode.setShown(true)); await W(100); await page.locator('[data-testid=dev-btn]').click(); await W(500); };
    const run = async (sec, k) => { await openDev(); await page.locator('[data-testid=dev-' + sec + '-' + k + ']').click(); await W(1800); };
    // ① 熱區：48×48（#ui 版面）中心對齊元素中心，四角＋四邊中點都要打中自己（或者子元素）
    const hit = (sel) => E((sel) => { const ui = document.getElementById('ui'), k = ui.getBoundingClientRect().width / ui.offsetWidth;
      return [...document.querySelectorAll(sel)].filter(e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden'; }).map(e => {
        e.scrollIntoView({ block: 'center', inline: 'nearest' }); const r = e.getBoundingClientRect(), cx = r.left + r.width / 2, cy = r.top + r.height / 2, h = 24 * k - 0.75; let n = 0, miss = [];
        for (const [dx, dy] of [[-1, -1], [1, -1], [-1, 1], [1, 1], [0, -1], [0, 1], [-1, 0], [1, 0]]) { const t = document.elementFromPoint(cx + dx * h, cy + dy * h); if (t && (t === e || e.contains(t))) n++; else miss.push(dx + ',' + dy + '→' + (t ? (t.dataset.testid || t.id || t.className || t.tagName) : '-')); }
        return { id: e.dataset.testid || e.id, n, miss: miss.slice(0, 2), lay: [Math.round(r.width / k), Math.round(r.height / k)] }; }); }, sel);
    const hitOk = async (label, sel, min) => { const L = await hit(sel); ok(L.length >= (min || 1), label + '：搵到 ' + L.length + ' 個');
      const bad = L.filter(x => x.n < 8); ok(bad.length === 0, label + '：熱區 ≥48' + (bad.length ? ' ← ' + JSON.stringify(bad.slice(0, 3)) : '（' + L.slice(0, 3).map(x => x.id + ' ' + x.lay.join('×')).join('，') + '）')); };
    // ② 對比：字色 vs 字底主色（文字透明截圖、字框入面最多嘅色）
    const contrast = async (label, sel) => {
      const items = await E((sel) => [...document.querySelectorAll(sel)].filter(e => { const r = e.getBoundingClientRect(); return r.width > 2 && r.height > 2 && (e.textContent || '').trim(); }).map(e => {
        const tns = [], tw = document.createTreeWalker(e, NodeFilter.SHOW_TEXT); let tn; while ((tn = tw.nextNode())) if (tn.nodeValue.trim()) tns.push(tn);   // #83：只量文字節點（6b.3 u63hit 透明熱區會撐大 range → 漸變掣底俾面板色搶咗眾數）
        const rs = tns.map(n => { const rg = document.createRange(); rg.selectNodeContents(n); return rg.getBoundingClientRect(); }).filter(r => r.width > 0), L0 = Math.min(...rs.map(r => r.left)), T0 = Math.min(...rs.map(r => r.top)), rr = { left: L0, top: T0, width: Math.max(...rs.map(r => r.right)) - L0, height: Math.max(...rs.map(r => r.bottom)) - T0 }, m = getComputedStyle(e).color.match(/[\d.]+/g).map(Number);
        return { id: e.dataset.testid || e.id || e.className, t: e.textContent.trim().slice(0, 10), col: m.slice(0, 3), r: [rr.left, rr.top, rr.width, rr.height] }; }).filter(Boolean), sel);
      ok(items.length > 0, label + '：有字 ' + items.length);
      if (!items.length) return;
      await E(() => document.querySelectorAll('#ui *').forEach(e => { e.dataset.chide = e.getAttribute('style') || ''; e.style.setProperty('color', 'transparent', 'important'); e.style.setProperty('text-shadow', 'none', 'important'); })); await W(60);
      const buf = await page.screenshot({ type: 'png' }); await E(() => document.querySelectorAll('#ui [data-chide]').forEach(e => { if (e.dataset.chide) e.setAttribute('style', e.dataset.chide); else e.removeAttribute('style'); delete e.dataset.chide; }));
      const bgs = await E(async ([b64, items]) => { const im = new Image(); await new Promise(r => { im.onload = r; im.src = 'data:image/png;base64,' + b64; }); const c = document.createElement('canvas'); c.width = im.width; c.height = im.height; const g = c.getContext('2d'); g.drawImage(im, 0, 0); const d = devicePixelRatio;
        return items.map(it => { const [x, y, w, h] = it.r, X = Math.max(0, Math.round(x * d)), Y = Math.max(0, Math.round(y * d)), Wd = Math.max(1, Math.min(c.width - X, Math.round(w * d))), Hd = Math.max(1, Math.min(c.height - Y, Math.round(h * d))), px = g.getImageData(X, Y, Wd, Hd).data, m = {}; let best = 0, col = null;
          for (let i = 0; i < px.length; i += 4) { const k = (px[i] >> 3) + ',' + (px[i + 1] >> 3) + ',' + (px[i + 2] >> 3); m[k] = (m[k] || 0) + 1; if (m[k] > best) { best = m[k]; col = [px[i], px[i + 1], px[i + 2]]; } } return col; }); }, [buf.toString('base64'), items]);
      const res = items.map((it, i) => ({ id: it.id, t: it.t, cr: +cr(it.col, bgs[i]).toFixed(2), bg: bgs[i] })), bad = res.filter(x => x.cr < 4.5);
      ok(bad.length === 0, label + '：字色對底 ≥4.5（最低 ' + Math.min(...res.map(x => x.cr)) + '）' + (bad.length ? ' ← ' + JSON.stringify(bad.slice(0, 3)) : ''));
      return res; };
    await run('house', 'prep'); await closeAll();
    await contrast('主畫面絲帶（餵食／玩耍／清潔／關燈）', '#ui .abtn:not(.dis) .hdl');
    await contrast('副標', '#substage');
    await E(() => __qa.devmode.setShown(true)); await W(200); await hitOk('🛠 開發者入口', '[data-testid=dev-btn]');
    await openDev(); await hitOk('開發者面板掣', '#mbox[data-kind="devmode"] [data-testid^="dev-sec-"] .btn', 5); await hitOk('開發者開合', '[data-testid="dev-toggle-btn"]', 0);
    await run('uiv2', 'settings'); await hitOk('設定：彈窗掣', '#mbox > .btn, #mbox .row > .btn:not(.hdTg)', 1); await hitOk('設定：分段', '#mbox .seg .btn', 4); await hitOk('設定：開關', '#mbox .hdTg', 2);
    await contrast('設定：開關／重設／關閉', '#mbox .hdTg, #mbox [data-testid="reset-save"], #mbox > .btn');
    await run('uiv2', 'popup'); await hitOk('示範彈窗掣', '#mbox .btn', 1); await contrast('示範彈窗：標題／掣', '#mbox > h2, #mbox .btn');
    await run('uiv2', 'journal'); await contrast('手帳：委託標題／tab／路線牌', '#s12box > h3, .s12tabs b.on, .rt');
    await run('uiv2', 'house'); await hitOk('屋仔返回', '[data-testid="house-back"]');
    await run('uiv2', 'deco'); await hitOk('佈置返回', '[data-testid="house-deco-back"]');
    const back = await E(() => { const e = document.querySelector('[data-testid="house-deco-back"]'); if (!e) return { w: 0, h: 0, bs: '' };
      return { w: e.offsetWidth, h: e.offsetHeight, bs: getComputedStyle(e).backgroundSize, v3: document.getElementById('ui').classList.contains('v3') }; });   // V3 圓章 contain（唔拉）
    ok(back.w >= 48 && back.h >= 48 && (/^44px 44px/.test(back.bs) || (back.v3 && back.bs === 'contain')), '返回掣 ' + back.w + '×' + back.h + '、med22 圓章冇拉（' + back.bs + '）');
    const fonts = await E(() => ({ f: Object.keys(__qa.uiv2.st().fonts || {}), set: [...document.fonts].map(f => f.family) }));
    ok(!fonts.set.some(f => /GlimmerFP(8|10)/.test(f)) && fonts.set.some(f => /GlimmerFP12/.test(f)), 'document.fonts 只得 FP12（冇 FP8／FP10）' + JSON.stringify(fonts.set.filter(f => /Glimmer/.test(f))));
    ok(errs.length === 0, '冇 pageerror' + (errs.length ? ' ← ' + errs.slice(0, 2).join(' | ') : ''));
    await ctx.close();
  }
  await browser.close();
  console.log('# 單檔');
  const out = path.join(os.tmpdir(), 'e2e5a2-single.html'), log = cp.execFileSync('python3', [path.join(ROOT, 'tools', 'build-single.py'), out], { encoding: 'utf8' });
  const html = fs.readFileSync(out, 'utf8'), keys = Object.keys(JSON.parse(html.match(/__GLIMMER_ASSETS = (\{.*?\});/s)[1]));
  ok(!keys.some(k => /\/reskin_4b\//.test(k)), '單檔冇 reskin_4b（' + keys.length + ' 個資產）');
  ok(!keys.some(k => /fp(8|10)-subset\.ttf$/.test(k)) && keys.some(k => /fp12-subset\.ttf$/.test(k)), '單檔冇 FP8／FP10，有 FP12');
  ok(keys.includes('art/ui_hd2d/ui_hd2d@3x.png'), 'v1 atlas 照留');
  { const B5 = 'art/series2_long/5b/ui/', mock = ['diary_page_example', 'job_card_example', 'job_card_capped', 'toast_return', 'icon_job_lv'].concat(...['expedition', 'job', 'rest'].map(a => ['on', 'off', 'locked'].map(b => 'seg_' + a + '_' + b))).map(n => B5 + n + '@3x.png').concat(B5 + 'layout.json');
    const left = mock.filter(k => keys.includes(k)); ok(mock.length === 15 && !left.length, '5b.1 單檔冇 5b 示意圖（' + mock.length + ' 個）', left);
    ok(mock.every(k => fs.existsSync(path.join(ROOT, k))), '5b 示意圖仍然留喺 repo');
    ok(['icon_expedition', 'icon_shards', 'icon_rest', 'icon_job_post', 'badge_job_lv1', 'badge_job_lv6'].every(n => keys.includes(B5 + n + '@3x.png')), '5b 用緊嘅 UI 照打包');
    const src = fs.readdirSync(path.join(ROOT, 'src')).filter(f => f.endsWith('.js')).map(f => fs.readFileSync(path.join(ROOT, 'src', f), 'utf8')).join('\n');
    ok(!/diary_page_example|job_card_example|job_card_capped|toast_return|icon_job_lv['@]|seg_(expedition|job|rest)_|5b\/ui\/layout/.test(src), 'src 冇載入 5b 示意圖'); }
  { const C5 = 'art/series2_long/5c/ui/', mock = ['parent_card_A3', 'parent_card_evo_still_moon', 'inherit_preview_bar', 'icon_trick', 'icon_pattern', 'pill_fast_on', 'pill_fast_tr', 'pill_fast_locked'].map(n => C5 + n + '@3x.png').concat(C5 + 'layout.json');
    const left = mock.filter(k => keys.includes(k)), sz = mock.reduce((a, k) => a + fs.statSync(path.join(ROOT, k)).size, 0); ok(mock.length === 9 && !left.length, '5c.1 單檔冇 5c 未用 UI（' + mock.length + ' 個，' + Math.round(sz / 1024) + 'KB）', left);
    ok(mock.every(k => fs.existsSync(path.join(ROOT, k))), '5c 未用 UI 仍然留喺 repo');
    ok(['icon_fast', 'icon_inherit', 'chip_trick_A', 'chip_trick_H', 'swatch_wave_A3', 'swatch_crescent_H3'].every(n => keys.includes(C5 + n + '@3x.png')), '5c 用緊嘅 UI 照打包');
    const src = fs.readdirSync(path.join(ROOT, 'src')).filter(f => f.endsWith('.js')).map(f => fs.readFileSync(path.join(ROOT, 'src', f), 'utf8')).join('\n');
    ok(!/parent_card_|inherit_preview_bar|icon_trick|icon_pattern|pill_fast_|5c\/ui\/layout/.test(src), 'src 冇載入 5c 未用 UI'); }
  ok(/skipped \d+ files/.test(log), 'build log 報跳過 ' + (log.match(/skipped \d+ files \d+ raw bytes/) || [''])[0]);
  ok(fs.existsSync(path.join(ROOT, 'art/ui_hd2d_v2/fonts/fp8-subset.ttf')), 'FP8／FP10 檔仍然留喺 repo');
  fs.unlinkSync(out);
  console.log(`\n結果：${pass} 通過，${fail} 失敗`); process.exit(fail ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
