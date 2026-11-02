/* 《微光小圃》 e2e-6b3 — 6b.3「UI 縮細＋收埋」（Kurt 19:54）：
   ① ui62 全部 UI 縮細一級：字 24／18／16 → 有效 20／16／14；按鈕、rail、面板、HUD、頭像同比例縮（CSS scale 0.8333）；對比 ≥4.5；撳位 ≥48（透明 hit area）；
   ② 「收埋 UI」掣（細、半透明、左下角）：撳一下淡出全部 UI 淨低寵物同場景；再撳／撳空位即返；狀態記住（reload 後照舊）；對白／彈出照出；
   ③ 360×640／390×844／412×915 逐頁量可見 UI 框兩兩重疊 ＝ 0（加「收埋」狀態）；④ 🛠「6b.3」喺開發者模式、唔喺設定；⑤ ?ui63=0 返 6b.2、v1 唔郁。
   截圖 → SHOTS（6b3-*.png）。node tests/e2e-6b3.js */
const path = require('path');
let chromium;
for (const p of [process.env.PW, 'playwright-core', '/workspace/qa-live-s1/node_modules/playwright-core']) { try { if (p) { chromium = require(p).chromium; break; } } catch (e) { } }
if (!chromium) { console.error('找不到 playwright-core'); process.exit(2); }
const { audit } = require('./readaudit');
const BASE = process.env.BASE || 'http://localhost:8240/index.html';
const SHOTS = process.env.SHOTS || process.env.OUT || path.join(__dirname, '..', '..', '..', 'screens') + '/';
require('fs').mkdirSync(SHOTS, { recursive: true });
let pass = 0, fail = 0;
const ok = (c, n, info) => { if (c) { pass++; console.log('  ✓ ' + n); } else { fail++; console.log('  ✗ ' + n + (info !== undefined ? ' → ' + JSON.stringify(info) : '')); } };
const QS = 'q=high&seed=21&ev=0&hour=13';

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROME || '/usr/bin/google-chrome', args: ['--no-sandbox', '--autoplay-policy=no-user-gesture-required'] });
  const errs = [];
  async function boot(vp, qs, dpr) {
    const ctx = await browser.newContext({ viewport: { width: vp[0], height: vp[1] }, deviceScaleFactor: dpr || 1 }); const page = await ctx.newPage();
    page.on('pageerror', e => errs.push('pageerror: ' + e.message)); page.on('console', m => { if (m.type() === 'error' && !/open-meteo|ERR_FAILED|net::/.test(m.text())) errs.push(m.text()); });
    const q = qs == null ? QS : qs;
    await page.goto(BASE + '?' + q); await page.evaluate(() => { window.__noSaveOnHide = true; localStorage.clear(); }); await page.goto(BASE + '?' + q);
    await page.waitForFunction(() => window.__glimmer && __glimmer.liveLoad); await page.evaluate(() => __glimmer.liveLoad); await page.evaluate(() => __glimmer.houseLoad).catch(() => { }); await page.evaluate(() => __glimmer.s2Load).catch(() => { });
    return { ctx, page, E: (f, a) => page.evaluate(f, a), W: (ms) => page.waitForTimeout(ms) };
  }
  const adult = (E) => E(() => { const s = __glimmer.state; s.stage = 'adult'; s.form = 'dust'; s.sleeping = false; Object.assign(s.needs, { mood: 80, energy: 100, hunger: 100, clean: 100 }); s.poops = 0; });
  const family = (E) => E(() => { const it = __qa.l5b.dev().items; it.find(i => i.k === 'prep').run(); it.find(i => i.k === 'hats').run(); __qa.house.close(); });


  // 有效字號（設計 px：除返成個 #ui 嘅適配倍數）
  const effOf = (E, sel) => E((sel) => { const ui = document.getElementById('ui'), k = ui.getBoundingClientRect().width / ui.offsetWidth; return [...document.querySelectorAll(sel)].filter(e => e.offsetWidth && e.textContent.trim()).map(e => { const r = e.getBoundingClientRect(); return +(parseFloat(getComputedStyle(e).fontSize) * r.width / e.offsetWidth / k).toFixed(2); }); }, sel);
  // 撳位：元素本身＋透明 hit area 嘅聯集（設計 px），再用 elementFromPoint 驗四邊真係撳到
  const hits = (E, sel) => E((sel) => { const ui = document.getElementById('ui'), k = ui.getBoundingClientRect().width / ui.offsetWidth;
    return [...document.querySelectorAll(sel)].filter(e => e.offsetWidth && getComputedStyle(e).display !== 'none' && getComputedStyle(e).visibility !== 'hidden').map(e => { const rs = [e.getBoundingClientRect(), ...[...e.querySelectorAll(':scope > i.u63hit')].map(h => h.getBoundingClientRect())];
      const L = Math.min(...rs.map(r => r.left)), T = Math.min(...rs.map(r => r.top)), R = Math.max(...rs.map(r => r.right)), B = Math.max(...rs.map(r => r.bottom)), cx = (L + R) / 2, cy = (T + B) / 2;
      const pts = [[L + 2, cy], [R - 2, cy], [cx, T + 2], [cx, B - 2]].filter(([x, y]) => x >= 0 && y >= 0 && x < innerWidth && y < innerHeight);
      const okp = pts.filter(([x, y]) => { const t = document.elementFromPoint(x, y); return t && (t === e || e.contains(t)); }).length;
      const tc = document.elementFromPoint(cx, cy); return { top: tc && !(tc === e || e.contains(tc)) ? (tc.id || tc.dataset.testid || String(tc.className)) : undefined, id: e.dataset.testid || e.id || e.className, w: +((R - L) / k).toFixed(1), h: +((B - T) / k).toFixed(1), okp, np: pts.length }; }); }, sel);
  const hitOk = (list) => list.every(h => h.w >= 47.5 && h.h >= 47.5 && h.okp === h.np);
  const closeAll = (E) => E(() => { try { __qa.work62.close(); } catch (e) { } try { __qa.l5b.close(); } catch (e) { } try { __qa.house.close(); } catch (e) { } const t = document.getElementById('u62tip'); if (t) t.remove(); const c = document.querySelector('[data-testid=l6b-close]'); if (c) c.click(); const b = document.querySelector('#modal[style*="flex"] [data-testid=modal-btn-0]'); if (b) b.click(); });

  // ───────── A. 縮細一級：字 20／16／14、同比例縮 ─────────
  console.log('A. 縮細一級（字 20／16／14、按鈕／rail／面板／HUD／頭像同比例縮）');
  { const { ctx, page, E, W } = await boot([390, 844]); await adult(E); await family(E); await W(1500);
    const st = await E(() => ({ u: document.getElementById('ui').classList.contains('u63'), S: __glimmer.ui2.u63, q: __qa.ui63.st() }));
    ok(st.u && Math.abs(st.S - 20 / 24) < 1e-6, '預設開 ui63（倍數 20/24）', st);
    const sc = await E(() => ['#hdBan2', '#chip', '#needs', '#top-r', '#s12chip', '#hdRail', '#bar', '#hdDock'].map(s => { const e = document.querySelector(s); return [s, e ? getComputedStyle(e).scale : null]; }));
    ok(sc.every(([, v]) => v && Math.abs(parseFloat(v) - 0.8333) < 0.001), 'HUD／頭像／rail／動作掣／底 dock 全部 ×0.8333', sc);
    const pr = await E(() => { const p = document.querySelector('[data-testid=uiv2-portrait]') || document.querySelector('#chip canvas'); const r = p.getBoundingClientRect(); return [r.width, p.offsetWidth]; });
    ok(Math.abs(pr[0] / pr[1] - 0.8333) < 0.01, '頭像同比例縮（' + pr.map(Math.round).join('／') + '）', pr);
    const rl = await E(() => [...document.querySelectorAll('#hdRail .ibtn')].filter(e => e.offsetWidth).map(e => +(e.getBoundingClientRect().width / e.offsetWidth).toFixed(3)));
    ok(rl.length >= 5 && rl.every(v => Math.abs(v - 0.833) < 0.005), 'rail 掣 ×0.833（' + rl.length + ' 個）', rl);
    // 標題 FP12 有效 20
    const ab = await effOf(E, '#bar .abtn .hdl');
    ok(ab.length >= 4 && ab.every(v => Math.abs(v - 20) < 0.3), '動作掣字（FP12）有效 20', ab);
    await page.click('#diary'); await W(900);
    const h2 = await effOf(E, '#mbox h2'), sub = await effOf(E, '#mbox .u62sub'), bd = await effOf(E, '#mbox [data-r62="b"]');
    ok(h2.length && h2.every(v => Math.abs(v - 20) < 0.3), '面板標題有效 20（FP12 24 CSS × 0.833）', h2);
    ok(sub.length && sub.every(v => Math.abs(v - 14) < 0.3), '面板用途句（輔助）有效 14', sub);
    ok(bd.length === 0 || bd.every(v => Math.abs(v - 16) < 0.3), '面板內文有效 16', bd);
    const fp = await E(() => getComputedStyle(document.querySelector('#mbox h2')).fontSize);
    ok(fp === '24px', '點陣字 FP12 保持 24 CSS（12 倍數唔糊）', fp);
    { const a = await audit(page, '#mbox'); ok(a.items.length > 0 && a.bad.length === 0, '信件面板字 ' + a.items.length + ' 段合格（有效 ≥14、對比 ≥4.5）', a.bad.slice(0, 3).map(b => [b.t, b.eff, b.cr, b.fam])); }
    { const h = await hits(E, '#mbox [data-testid^=modal-btn]'); ok(h.length && hitOk(h), '面板掣撳位 ≥48', h); }
    await page.screenshot({ path: SHOTS + '6b3-01-panel-diary.png' });
    await page.click('[data-testid=modal-btn-0]'); await W(500);
    await page.click('#l6bbtn'); await W(900);
    const lb = await effOf(E, '[data-testid=l6b-panel] [data-r62="b"]'), la = await effOf(E, '[data-testid=l6b-panel] [data-r62="a"], #l6bov .u62sub');
    ok(lb.length > 0 && lb.every(v => Math.abs(v - 16) < 0.3), '散步路面板內文有效 16（' + lb.length + ' 段）', lb);
    ok(la.length > 0 && la.every(v => Math.abs(v - 14) < 0.3), '散步路面板輔助字有效 14（' + la.length + ' 段）', la);
    { const a = await audit(page, '[data-testid=l6b-panel]'); ok(a.items.length > 0 && a.bad.length === 0, '散步路面板字 ' + a.items.length + ' 段合格', a.bad.slice(0, 3).map(b => [b.t, b.eff, b.cr, b.fam])); }
    { const h = await hits(E, '[data-testid=l6b-close]'); ok(h.length && hitOk(h), '散步路「閂」撳位 ≥48', h); }
    await page.screenshot({ path: SHOTS + '6b3-02-panel-walk.png' });
    await closeAll(E); await W(400);
    await E(() => __qa.work62.open()); await W(1000);
    const wt = await effOf(E, '#u62work .ttl'), wb = await effOf(E, '#u62work .nm, #u62work .er');
    ok(wt.length && wt.every(v => Math.abs(v - 20) < 0.3), '工作畫面標題有效 20', wt);
    ok(wb.length && wb.every(v => Math.abs(v - 16) < 0.3), '工作卡內文有效 16', wb);
    const clip = await E(() => [...document.querySelectorAll('#u62work .st')].map(s => [s.offsetHeight, s.scrollHeight]).filter(([a, b]) => b > a + 1));
    ok(clip.length === 0, '工作卡字冇被裁（長句換行，唔縮字）', clip);
    { const a = await audit(page, '#u62work'); ok(a.items.length > 5 && a.bad.length === 0, '工作畫面字 ' + a.items.length + ' 段合格', a.bad.slice(0, 3).map(b => [b.t, b.eff, b.cr, b.fam])); }
    { const h = await hits(E, '[data-testid=u62w-back], [data-testid=u62w-plan]'); ok(h.length === 2 && hitOk(h), '返回／安排工作 撳位 ≥48', h); }
    await page.screenshot({ path: SHOTS + '6b3-03-panel-work.png' });
    await closeAll(E); await W(500);
    { const a = await audit(page, '#hud, #top-r, #s12chip, #bar, #hdRail, #hdDock'); ok(a.items.length >= 5 && a.bad.length === 0, '主畫面 HUD／rail／掣字 ' + a.items.length + ' 段合格', a.bad.slice(0, 3).map(b => [b.t, b.eff, b.cr, b.fam])); }
    await page.screenshot({ path: SHOTS + '6b3-04-main.png' });
    await ctx.close(); }

  // ───────── B. 撳位 ≥48（360 細機都夠） ─────────
  console.log('B. 撳位 ≥48（透明 hit area）');
  for (const vp of [[360, 640], [390, 844]]) {
    const { ctx, page, E, W } = await boot(vp, QS + '&tips62=1'); await adult(E); await family(E); await W(1500);
    const tag = vp.join('x');
    { let h; for (let i = 0; i < 8; i++) { h = await hits(E, '#hdRail .ibtn'); if (h.length >= 5 && hitOk(h)) break; await W(500); }   // 等 rail 排位定咗（新掣入場會郁）
      ok(h.length >= 5 && hitOk(h), tag + '：rail 掣（' + h.length + '）撳位 ≥48', h.filter(x => !(x.w >= 47.5 && x.h >= 47.5 && x.okp === x.np))); }
    { const h = await hits(E, '#bar .abtn'); ok(h.length >= 4 && hitOk(h), tag + '：動作掣撳位 ≥48', h.filter(x => !(x.w >= 47.5 && x.h >= 47.5 && x.okp === x.np))); }
    { const h = await hits(E, '#hdDock .hdTab, #hdDock .ibtn, #hdDock [data-testid^=hd-tab]'); ok(h.length >= 4 && hitOk(h), tag + '：底 dock 撳位 ≥48', h.filter(x => !(x.w >= 47.5 && x.h >= 47.5 && x.okp === x.np))); }
    { const h = await hits(E, '#u63hide'); ok(h.length === 1 && hitOk(h), tag + '：「收埋」掣撳位 ≥48', h); }
    { const ca = await audit(page, '#u63hide'); ok(ca.items.length >= 1 && ca.bad.length === 0, tag + '：「收埋」字有效 ≥14、對比 ≥4.5', ca.bad.map(b => [b.t, b.eff, b.cr])); }
    await page.click('#diary'); await W(800);
    { const h = await hits(E, '#u62tip .k'); ok(h.length === 1 && hitOk(h), tag + '：小提示「知道喇」撳位 ≥48', h); }
    { const v = await E(() => getComputedStyle(document.getElementById('u63hide')).display); ok(v === 'none', tag + '：小提示出緊 →「收埋」掣讓位', v); }
    await ctx.close();
  }

  // ───────── C. 收埋 UI ─────────
  console.log('C. 「收埋 UI」掣');
  { const { ctx, page, E, W } = await boot([390, 844]); await adult(E); await family(E); await W(1500);
    const b0 = await E(() => { const b = document.getElementById('u63hide'), r = b.getBoundingClientRect(), cs = getComputedStyle(b); return { r: [r.left, r.top, r.width, r.height].map(Math.round), op: +cs.opacity, txt: b.textContent.trim(), tid: b.dataset.testid }; });
    ok(b0.tid === 'u63-hide' && b0.r[0] < 40 && b0.r[2] <= 56 && b0.op > 0.3 && b0.op < 0.8 && /收埋/.test(b0.txt), '細、半透明、左邊角落有「收埋」掣', b0);
    const vis = () => E(() => ['#hud', '#bar', '#s12chip', '#hdRail', '#hdDock'].map(s => { const e = document.querySelector(s), cs = getComputedStyle(e); return [s, +cs.opacity, cs.pointerEvents]; }));
    const v0 = await vis();
    await page.click('#u63hide'); await page.waitForFunction(() => +getComputedStyle(document.getElementById('hud')).opacity === 0, null, { timeout: 3000 }).catch(() => { }); await W(200);
    let v = await vis(); const s1 = await E(() => ({ h: __qa.ui63.st().hidden, ls: localStorage.getItem('glimmer.u63hide'), txt: document.getElementById('u63hide').textContent.trim(), body: document.body.classList.contains('u63hid') }));
    ok(v.every(([, o, p]) => o === 0 && p === 'none'), '撳一下 → HUD／動作掣／委託／rail／dock 淡出、撳唔到', v);
    ok(s1.h && s1.body && s1.ls === '1' && /顯示/.test(s1.txt), '狀態記低（localStorage）＋掣變「顯示」', s1);
    const rc = await E(() => { const r = document.getElementById('diary').getBoundingClientRect(), t = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2); return t && (t.id || t.className); });
    ok(rc !== 'diary' && !String(rc).includes('ibtn'), '收埋時撳 rail 位置唔會開信件', rc);
    const pet = await E(() => { const c = document.querySelector('canvas'); return !!c && c.offsetWidth > 300; });
    ok(pet, '寵物同場景仍然喺度', pet);
    await page.screenshot({ path: SHOTS + '6b3-05-hidden.png' });
    // 對白／彈出仍可出
    await E(() => __glimmer.say({ line: '收埋咗都聽到我講嘢㗎！', src: 'voice', urgent: true })); await W(600);
    const vc = await E(() => { const e = document.getElementById('s12voice'), cs = getComputedStyle(e); return { op: +cs.opacity, d: cs.display, t: e.textContent }; });
    ok(vc.op > 0.5 && vc.d !== 'none' && /聽到/.test(vc.t), '收埋時心聲對白照出', vc);
    await page.screenshot({ path: SHOTS + '6b3-06-hidden-voice.png' });
    await E(() => Glimmer.ui.modal({ title: '測試彈出', lines: ['收埋咗都會彈出。'], buttons: [{ text: '知道', primary: true }] }));
    await W(500);
    const md = await E(() => { const m = document.getElementById('modal'); return { d: getComputedStyle(m).display, op: +getComputedStyle(m).opacity, t: document.getElementById('mbox').textContent }; });
    ok(md.d !== 'none' && md.op > 0.5 && /收埋咗都會彈出/.test(md.t), '收埋時彈出窗照出', md);
    await page.screenshot({ path: SHOTS + '6b3-07-hidden-modal.png' });
    await page.click('[data-testid=modal-btn-0]'); await W(400);
    ok(await E(() => __qa.ui63.st().hidden), '閂彈出窗後仍然收埋');
    // reload 後記住
    await page.reload(); await page.waitForFunction(() => window.__glimmer && __glimmer.liveLoad); await page.evaluate(() => __glimmer.liveLoad); await W(1500);
    v = await vis(); const s2 = await E(() => ({ h: __qa.ui63.st().hidden, body: document.body.classList.contains('u63hid') }));
    ok(s2.h && s2.body && v.every(([, o]) => o === 0), '重開遊戲 → 仍然收埋（狀態記住）', { s2, v });
    // 再撳掣 → 返
    await page.click('#u63hide'); await W(500); v = await vis();
    ok(v.every(([, o, p], i) => o > 0.9 && p === v0[i][2]) && !(await E(() => __qa.ui63.st().hidden)), '再撳掣 → UI 返嚟（撳得返）', { v, v0 });
    // 撳空位 → 返（嗰下唔當摸寵物）
    await page.click('#u63hide'); await W(500);
    const pat0 = await E(() => __glimmer.state.stats ? JSON.stringify(__glimmer.state.stats) : '');
    await page.mouse.click(300, 560); await W(500); v = await vis();
    const s3 = await E(() => ({ h: __qa.ui63.st().hidden, ls: localStorage.getItem('glimmer.u63hide'), show: __qa.ui63.st().stat.show }));
    ok(!s3.h && s3.ls === '0' && v.every(([, o]) => o > 0.9), '收埋時撳空位 → UI 返嚟', { s3, v });
    const pat1 = await E(() => __glimmer.state.stats ? JSON.stringify(__glimmer.state.stats) : '');
    ok(pat0 === pat1, '嗰一下唔會當撳寵物', { pat0: pat0.slice(0, 80), pat1: pat1.slice(0, 80) });
    await ctx.close(); }

  // ───────── D. 重疊 3 尺寸 × 每頁（＋收埋狀態） ─────────
  console.log('D. UI 重疊（360×640、390×844、412×915）');
  for (const vp of [[360, 640], [390, 844], [412, 915]]) {
    const { ctx, page, E, W } = await boot(vp); await adult(E); await family(E); await W(1500);
    const tag = vp.join('x'); let tot = 0; const bad = [];
    for (const pg of ['main', 'work', 'house', 'plan', 'walk', 'diary', 'dex', 'settings', 'kid', 'tip', 'voice', 'hidden']) {
      await closeAll(E); await E(() => { __glimmer.nq && __glimmer.nq.clear && __glimmer.nq.clear(); __qa.ui63.setHidden(false); }); await W(400);
      await E((pg) => { const c = (s) => { const e = document.querySelector(s); if (e) e.click(); };
        if (pg === 'work') __qa.work62.open(); else if (pg === 'house') c('#s2house'); else if (pg === 'plan') __qa.l5b.plan(); else if (pg === 'walk') c('#l6bbtn'); else if (pg === 'diary') c('#diary'); else if (pg === 'dex') c('#dex');
        else if (pg === 'settings') c('#gear'); else if (pg === 'kid') c('#s2kid'); else if (pg === 'tip') { __qa.ui62.dev().items.find(i => i.k === 'tipdemo').run(); } else if (pg === 'voice') __glimmer.say({ line: '今日天氣好好，我哋出去行下好唔好？', src: 'voice', urgent: true });
        else if (pg === 'hidden') { __qa.ui63.setHidden(true); __glimmer.say({ line: '收埋咗都會講嘢', src: 'voice', urgent: true }); } }, pg);
      await W(pg === 'house' ? 1800 : 900);
      const o = await E(() => __qa.ui62.overlap()); tot += o.hits.length; if (o.hits.length) bad.push([pg, o.hits.slice(0, 4)]);
      if (['main', 'work', 'house', 'plan', 'tip', 'hidden'].includes(pg)) await page.screenshot({ path: SHOTS + '6b3-ov-' + tag + '-' + pg + '.png' });
      if (pg === 'settings') await E(() => { const tab = document.querySelector('[data-testid=hd-tab-home]'); if (tab) tab.click(); });
    }
    ok(tot === 0, tag + '：12 頁（含收埋）可見 UI 框兩兩冇重疊', bad);
    await ctx.close();
  }

  // ───────── E. 🛠 開發者模式、?ui63=0、v1 ─────────
  console.log('E. 🛠「6b.3」、?ui63=0、v1');
  { const { ctx, page, E, W } = await boot([390, 844]); await adult(E); await W(1200);
    await E(() => __qa.devmode.setShown(true)); await W(100); await page.locator('[data-testid=dev-btn]').click(); await W(500);
    ok(await page.locator('[data-testid=dev-sec-ui63]').isVisible(), '分組「6b.3」喺開發者模式');
    ok(!(await E(() => [...document.querySelectorAll('[data-testid^=s2-set],[data-testid^=toggle-]')].some(e => /6b\.3|收埋/.test(e.textContent)))), '試玩掣唔喺設定');
    await page.locator('[data-testid=dev-ui63-hide]').scrollIntoViewIfNeeded(); await page.locator('[data-testid=dev-ui63-hide]').click(); await W(300);
    ok(await E(() => __qa.ui63.st().hidden), '🛠「收埋 UI」有效');
    await E(() => { const b = document.querySelector('[data-testid=dev-ui63-show]'); if (b) b.click(); else __qa.ui63.dev().items.find(i => i.k === 'show').run(); }); await W(300);
    ok(!(await E(() => __qa.ui63.st().hidden)), '🛠「顯示 UI」有效');
    await ctx.close(); }
  { const { ctx, page, E, W } = await boot([390, 844], QS + '&ui63=0'); await adult(E); await W(1200);
    const v = await E(() => ({ u: document.getElementById('ui').classList.contains('u63'), btn: !!document.getElementById('u63hide'), sc: document.querySelectorAll('#ui .u63s').length, qa: !!(window.__qa && __qa.ui63), u62: document.getElementById('ui').classList.contains('u62') }));
    ok(!v.u && !v.btn && !v.sc && !v.qa && v.u62, '?ui63=0：返 6b.2（冇縮、冇掣）', v);
    await ctx.close(); }
  { const { ctx, page, E, W } = await boot([390, 844], QS + '&ui=1'); await adult(E); await W(1000);
    const v = await E(() => ({ v2: document.getElementById('ui').classList.contains('v2'), u: document.getElementById('ui').classList.contains('u63'), btn: (() => { const b = document.getElementById('u63hide'); return !!b && getComputedStyle(b).display !== 'none'; })(), sc: [...document.querySelectorAll('.u63s')].filter(e => getComputedStyle(e).scale !== 'none').length }));
    ok(!v.v2 && !v.u && !v.btn && !v.sc, 'v1 舊 UI 唔郁', v);
    await ctx.close(); }

  ok(errs.length === 0, '冇 console error／pageerror', errs.slice(0, 5));
  await browser.close();
  console.log(`\n6b3 e2e：${pass} pass / ${fail} fail`);
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
