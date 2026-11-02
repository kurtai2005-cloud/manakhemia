/* 《微光小圃》 e2e-6b2 — 6b.2「UI 打磨」（Kurt 親口反饋）：
   ① 講嘢句（G.say：心聲／記憶句／招呼）按字數計時淡出、撳一下即閂；狀態氣泡 #bubble 出 dur 秒淡出、撳一下即閂；
   ② 字級分層（標題 FP12 24、內文系統字 18、輔助 16；對比 ≥4.5、有效字號 ≥14）；③ 面板換膚（半透明＋模糊＋金邊＋圓角＋淡入上移）；
   ④ 360×640／390×844／412×915 逐頁（主畫面、工作、屋仔、今日安排、散步、信件、圖鑑、設定、細佬、小提示）量可見 UI 框兩兩重疊 ＝ 0；
   ⑤ 左上頭像跟寵物而家嗰幀；⑦ rail 字標籤、面板用途說明、第一次小提示（可閂、🛠 重置）；⑧「工作」主畫面；v1 唔受影響；?ui62=0 全停。
   截圖 → SHOTS（6b2-*.png）。node tests/e2e-6b2.js */
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

  // ───────── A. 講嘢句計時＋撳閂 ─────────
  console.log('A. 講嘢句（G.say）計時淡出＋撳一下閂');
  { const { ctx, page, E, W } = await boot([390, 844]); await adult(E); await W(800);
    const ss = await E(() => [__qa.ui62.speechSec('好開心'), __qa.ui62.speechSec('一二三四五六七八九十'), __qa.ui62.speechSec('團絨今日喺花園見到一隻好大嘅蝴蝶追咗佢成個下晝'), __qa.ui62.speechSec('長'.repeat(200))]);
    ok(ss[0] === 3.5 && ss[1] === 3.5 && ss[2] > 3.5 && ss[2] < 9 && ss[3] === 9, '字數計時：短句 3.5 秒、長句按字數加、最長 9 秒', ss);
    const L = '團絨記得你上次陪佢喺花園睇咗好耐好耐嘅星星';
    await E((L) => { __glimmer.nq.clear(); __glimmer.say({ line: L, src: 'mem6', sec: 6, urgent: true }); }, L); await W(300);
    const c0 = await E(() => ({ op: +document.getElementById('s12voice').style.opacity, sec: __glimmer.nq.cur && __glimmer.nq.cur.sec, src: __glimmer.nq.cur && __glimmer.nq.cur.src }));
    const want = await E((L) => __qa.ui62.speechSec(L), L);
    ok(c0.op === 1 && c0.sec === want && c0.src === 'mem6', '記憶句（mem6 原本 6 秒）改按字數 ' + want + ' 秒', c0);
    await W(want * 1000 + 900); const op1 = await E(() => +document.getElementById('s12voice').style.opacity);
    ok(op1 === 0, '時間到自動淡出（' + want + ' 秒）', op1);
    await E(() => __glimmer.say({ line: '撳我就閂', src: 'voice', urgent: true })); await W(300);
    const pe = await E(() => getComputedStyle(document.getElementById('s12voice')).pointerEvents);
    ok(pe === 'auto', '出緊嘅泡泡撳得到（pointer-events:auto）', pe);
    await page.click('#s12voice'); await W(400);
    const c2 = await E(() => ({ op: +document.getElementById('s12voice').style.opacity, cur: !!__glimmer.nq.cur, pe: getComputedStyle(document.getElementById('s12voice')).pointerEvents, n: __qa.ui62.st().stat.voiceClose }));
    ok(c2.op === 0 && !c2.cur && c2.pe === 'none' && c2.n >= 1, '撳一下即閂（閂咗唔再擋住撳寵物）', c2);
    // 狀態氣泡
    await E(() => { __glimmer.nq.clear(); const s = __glimmer.state; s.needs.hunger = 10; }); await W(1200);
    const b0 = await E(() => { const b = document.getElementById('bubble'); return { t: b.textContent, d: b.style.display, gone: b.classList.contains('u62gone'), op: getComputedStyle(b).opacity }; });
    ok(b0.t && b0.d === 'block' && !b0.gone, '狀態氣泡出「' + b0.t + '」', b0);
    await W(3800); const b1 = await E(() => { const b = document.getElementById('bubble'); return { d: b.style.display, gone: b.classList.contains('u62gone'), op: +getComputedStyle(b).opacity }; });
    ok(b1.d === 'block' && b1.gone && b1.op < 0.05, '狀態仍然成立，但氣泡 ~3.5 秒後淡出（唔再一直企喺中間）', b1);
    await E(() => { const s = __glimmer.state; s.sleeping = true; }); await W(1000);
    const b2 = await E(() => { const b = document.getElementById('bubble'); return { t: b.textContent, gone: b.classList.contains('u62gone'), pe: getComputedStyle(b).pointerEvents }; });
    ok(b2.t !== b0.t && !b2.gone && b2.pe === 'auto', '換咗新狀態句（' + b2.t + '）即刻再出（撳得）', b2);
    await page.click('#bubble'); await W(500);
    const b3 = await E(() => { const b = document.getElementById('bubble'); return { gone: b.classList.contains('u62gone'), op: +getComputedStyle(b).opacity, n: __qa.ui62.st().stat.bubbleTap }; });
    ok(b3.gone && b3.op < 0.05 && b3.n === 1, '撳一下氣泡即閂', b3);
    await page.screenshot({ path: SHOTS + '6b2-01-bubble-gone.png' });
    await ctx.close(); }

  // ───────── B. 字級＋面板換膚＋說明＋rail 字 ─────────
  console.log('B. 字級分層、面板換膚、用途說明、rail 字');
  { const { ctx, page, E, W } = await boot([360, 780], null, 2); await adult(E); await family(E); await W(1500);
    const rl = await E(() => [...document.querySelectorAll('#ui .ibtn')].filter(e => e.offsetWidth && getComputedStyle(e).display !== 'none' && !e.closest('#hdDock')).map(e => { const ls = [...e.querySelectorAll('i.l, .l, span')].filter(x => /[\u3400-\u9fff]/.test(x.textContent) && x.offsetWidth > 0); const r = e.getBoundingClientRect(); return { id: e.id, l: ls.map(x => x.textContent).join('|'), w: r.width, h: r.height }; }));
    ok(rl.length >= 6 && rl.every(r => r.l.length >= 2), 'rail 每個掣都有文字標籤（' + rl.map(r => r.l).join('、') + '）', rl.filter(r => !r.l));
    ok(rl.every(r => r.w * 390 / 360 >= 47.5 && r.h * 390 / 360 >= 47.5), 'rail 熱區 ≥48', rl.map(r => [r.id, Math.round(r.w), Math.round(r.h)]));
    ok(rl.some(r => r.id === 'u62workbtn' && r.l === '工作'), '主 rail 有「工作」入口', rl.map(r => r.id));
    await page.click('#diary'); await W(900);
    const m = await E(() => { const b = document.getElementById('mbox'), cs = getComputedStyle(b), h2 = getComputedStyle(b.querySelector('h2')), sub = b.querySelector('.u62sub'), p = b.querySelector('p:not(.u62sub)[data-r62]');
      return { bi: cs.borderImageSource, bd: cs.borderTopColor, rad: cs.borderTopLeftRadius, blur: cs.backdropFilter, bg: cs.backgroundImage.slice(0, 40), anim: cs.animationName, h2f: h2.fontFamily.slice(0, 14), h2s: h2.fontSize, h2ls: h2.letterSpacing, sub: sub && sub.textContent, subs: sub && getComputedStyle(sub).fontSize, pf: p && getComputedStyle(p).fontFamily.slice(0, 12), ps: p && getComputedStyle(p).fontSize, pr: p && p.dataset.r62, pad: cs.paddingLeft }; });
    ok(m.bi === 'none' && /rgba\(232, 194, 122/.test(m.bd) && m.rad === '14px' && /blur/.test(m.blur) && m.anim === 'u62in', '面板：半透明深底＋模糊＋細金邊＋圓角 14＋淡入上移', m);
    ok(/GlimmerFP12/.test(m.h2f) && m.h2s === '24px' && m.h2ls === '2px', '標題 FP12 24px、字距 2px', m);
    ok(m.sub && m.subs === '16px', '面板頂有一句用途說明（輔助字 16px）：' + m.sub, m);
    ok(/Noto Sans/.test(m.pf) && m.ps === (m.pr === 'b' ? '18px' : '16px'), '內文細一級：系統中文字（內文 18／輔助 16）→ ' + m.pr + ' ' + m.ps, m);
    ok(m.pad === '16px', '面板內邊距跟間距尺（16）', m.pad);
    { const a = await audit(page, '#mbox'); ok(a.items.length > 0 && a.bad.length === 0, '信件面板字 ' + a.items.length + ' 段：有效字號 ≥14、對比 ≥4.5', a.bad.slice(0, 3).map(b => [b.t, b.eff, b.cr, b.fam])); }
    await page.screenshot({ path: SHOTS + '6b2-02-panel-diary.png' });
    await page.click('[data-testid=modal-btn-0]'); await W(500);
    await page.click('#l6bbtn'); await W(900);
    const l6 = await E(() => { const s = document.querySelector('#l6bov .u62sub'), p = document.querySelector('[data-testid=l6b-panel]'); const bs = p ? [...p.querySelectorAll('[data-r62="b"]')].map(e => getComputedStyle(e).fontSize) : []; return { s: s && s.textContent, pan: p && p.classList.contains('u62pan'), bi: p && getComputedStyle(p).borderImageSource, bs }; });
    ok(l6.bs.length > 0 && l6.bs.every(x => x === '18px'), '面板內文 18px（' + l6.bs.length + ' 段）', l6.bs);
    ok(l6.s && l6.pan && l6.bi === 'none', '散步路面板：換膚＋用途說明「' + l6.s + '」', l6);
    { const a = await audit(page, '[data-testid=l6b-panel]'); ok(a.items.length > 0 && a.bad.length === 0, '散步路面板字 ' + a.items.length + ' 段合格', a.bad.slice(0, 3).map(b => [b.t, b.eff, b.cr, b.fam])); }
    await E(() => document.querySelector('[data-testid=l6b-close]').click()); await W(400);
    await E(() => __qa.l5b.plan()); await W(900);
    const pl = await E(() => { const s = document.querySelector('#l5bov .u62sub'); const r = s && s.getBoundingClientRect(); return { s: s && s.textContent, y: r && r.top, pans: document.querySelectorAll('#l5bov .u62pan').length }; });
    ok(pl.s && pl.pans >= 1, '今日安排：換膚＋用途說明「' + pl.s + '」', pl);
    await page.screenshot({ path: SHOTS + '6b2-03-panel-plan.png' });
    await ctx.close(); }

  // ───────── C. 第一次小提示 ─────────
  console.log('C. 第一次小提示（可閂、只出一次、🛠 重置）');
  { const { ctx, page, E, W } = await boot([390, 844], QS + '&tips62=1'); await adult(E); await family(E); await W(1200);
    await page.click('#diary'); await W(700);
    const t0 = await E(() => { const t = document.getElementById('u62tip'); if (!t) return null; const k = t.querySelector('.k').getBoundingClientRect(); return { k: t.dataset.k, txt: t.textContent, kw: k.width, kh: k.height, b: getComputedStyle(t.querySelector('.b')).fontSize }; });
    ok(t0 && t0.k === 'diary' && /小提示/.test(t0.txt) && t0.kw >= 48 && t0.kh >= 48 && t0.b === '18px', '第一次開信件 → 出小提示（「知道喇」≥48）', t0);
    { const a = await audit(page, '#u62tip'); ok(a.items.length > 0 && a.bad.length === 0, '小提示字合格', a.bad.slice(0, 3).map(b => [b.t, b.eff, b.cr])); }
    await page.screenshot({ path: SHOTS + '6b2-04-first-tip.png' });
    await page.click('[data-testid=u62-tip-ok]'); await W(300);
    ok(await E(() => !document.getElementById('u62tip')), '撳「知道喇」閂');
    await page.click('[data-testid=modal-btn-0]'); await W(400); await page.click('#diary'); await W(700);
    ok(await E(() => !document.getElementById('u62tip')), '第二次開唔再出');
    await page.click('[data-testid=modal-btn-0]'); await W(400);
    await page.click('#u62workbtn'); await W(800);
    const tw = await E(() => { const t = document.getElementById('u62tip'); return t && t.dataset.k; });
    ok(tw === 'work', '第一次開工作主畫面 → 工作小提示', tw);
    await page.screenshot({ path: SHOTS + '6b2-05-work-first-tip.png' });
    await E(() => { document.querySelector('[data-testid=u62-tip-ok]').click(); __qa.work62.close(); });
    const r = await E(() => __qa.ui62.dev().items.find(i => i.k === 'tips').run()); await W(300);
    ok(r.ok && Object.keys(await E(() => __qa.ui62.st().seen)).length === 0, '🛠「6b.2」重置小提示', r);
    await page.click('#diary'); await W(700);
    ok(await E(() => { const t = document.getElementById('u62tip'); return !!t && t.dataset.k === 'diary'; }), '重置後再開 → 再出');
    const dv = await E(() => { const d = __qa.ui62.dev(); return { id: d.id, t: d.title, n: d.items.length, st: d.status() }; });
    ok(dv.id === 'ui62' && dv.n >= 5 && /提示/.test(dv.st), '🛠 開發者模式有「6b.2」區', dv);
    await ctx.close(); }

  // ───────── D. 工作主畫面 ─────────
  console.log('D. 「工作」主畫面');
  { const { ctx, page, E, W } = await boot([360, 780], null, 3); await adult(E); await family(E); await W(1200);
    await page.click('#u62workbtn'); await W(1500);
    const w = await E(() => { const rows = __qa.l5b.rows().filter(r => r.a === 'job'); const st = __qa.work62.st(); const el = document.getElementById('u62work'); const r = el.getBoundingClientRect();
      return { rows: rows.length, cards: st.cards.length, full: r.width >= 359 && r.height >= 779, names: rows.map(r => r.name), txt: el.innerText, ph: el.querySelectorAll('[data-ph^="6b2:work_bg_"]').length, jobs: st.cards.map(c => c.job), shift: st.cards.map(c => [c.shift, c.pct]) }; });
    ok(w.full && w.rows >= 3 && w.cards === w.rows, '全畫面工作場景：每隻返工嘅寵物一個工作站（' + w.cards + '）', w);
    ok(w.names.every(n => w.txt.indexOf(n) >= 0) && /Lv\d/.test(w.txt) && /今日已賺|今晚出糧/.test(w.txt) && /收工|開工/.test(w.txt) && /全家今日 \d+／12/.test(w.txt), '每隻有名、工作名＋Lv、今日已賺／日薪、幾時收工；頂有全家 n／12', w.txt.slice(0, 200));
    ok(w.ph === w.cards, '工作地點背景＝洋紅 placeholder（data-ph 6b2:work_bg_*）', w.ph);
    ok(w.shift.every(([s, p]) => (s === 'on' && p > 0 && p < 1) || s === 'before' || s === 'done'), '進度條跟更份（13:00 日更做緊、守夜未開工）', w.shift);
    const bars = await E(() => [...document.querySelectorAll('#u62work .pb i')].map(i => i.style.width));
    ok(bars.length === w.cards && bars.some(b => parseFloat(b) > 0), '有進度條', bars);
    const clips = new Set(); let px = 0;
    for (let i = 0; i < 12; i++) { const s = await E(() => { const c = document.querySelectorAll('#u62work canvas'); let n = 0; for (const cv of c) { const d = cv.getContext('2d').getImageData(0, 0, 96, 96).data; for (let k = 3; k < d.length; k += 16) if (d[k] > 20) n++; } return { clips: __qa.work62.st().cards.map(c => c.clip), n }; }); s.clips.forEach(c => clips.add(c)); px = Math.max(px, s.n); await W(450); }
    ok(px > 100 && clips.has('walk') && clips.has('idle'), '寵物用現有 walk／idle clip 做工作動畫（' + [...clips].join('/') + '）', { px, clips: [...clips] });
    { const a = await audit(page, '#u62work'); ok(a.items.length > 5 && a.bad.length === 0, '工作畫面字 ' + a.items.length + ' 段合格', a.bad.slice(0, 3).map(b => [b.t, b.eff, b.cr, b.fam])); }
    const tg = await E(() => ['u62w-back', 'u62w-plan'].map(t => { const r = document.querySelector('[data-testid=' + t + ']').getBoundingClientRect(); return [t, r.width * 390 / 360, r.height * 390 / 360]; }));
    ok(tg.every(t => t[1] >= 48 && t[2] >= 48), '返回／安排工作 熱區 ≥48', tg);
    await page.screenshot({ path: SHOTS + '6b2-06-work-screen.png' });
    await page.click('[data-testid=u62w-back]'); await W(400);
    ok(await E(() => !document.getElementById('u62work') && !__qa.work62.isOpen()), '撳「返回」返主畫面');
    await page.click('#u62workbtn'); await W(500); await page.click('[data-testid=u62w-plan]'); await W(700);
    ok(await E(() => !document.getElementById('u62work') && __qa.l5b.st().ov === 'plan'), '「安排工作」→ 開今日安排');
    await E(() => __qa.l5b.close());
    const sh = await E(() => [G = __glimmer, __qa.work62.shift('post', 8.5).state, __qa.work62.shift('post', 12).pct, __qa.work62.shift('watch', 23).state, __qa.work62.shift('watch', 4).state, __qa.work62.shift('watch', 6).state].slice(1));
    ok(sh[0] === 'before' && sh[1] === 0.375 && sh[2] === 'on' && sh[3] === 'on' && sh[4] === 'before', '更份：日更 09–17、守夜 21–05（06:00 顯示今晚 21:00 開工）', sh);
    await ctx.close(); }

  // ───────── E. 頭像即時 ─────────
  console.log('E. 左上頭像跟寵物而家嗰幀');
  { const { ctx, page, E, W } = await boot([390, 844]); await adult(E); await W(1200);
    const fr = new Set(); let same = 0, live = 0, n = 0;
    for (let i = 0; i < 16; i++) { const f = await E(() => { const u = __qa.uiv2.st().face, pb = __glimmer.renderer.petBlit; return { live: u && u.live, frame: u && u.frame, pb: pb ? (pb.clip || '') + ':' + pb.fi + (pb.scx < 0 ? 'm' : '') : null }; });
      n++; if (f.live) live++; if (f.frame) fr.add(f.frame); if (f.frame && f.frame === f.pb) same++; if (i === 5) await E(() => __glimmer.renderer.act('happy', 2)); await W(200); }
    ok(live === n, '頭像用緊即時幀（live）', { live, n });
    ok(fr.size >= 2, '頭像跟住寵物郁（' + fr.size + ' 款幀）', [...fr]);
    ok(same >= n * 0.6, '頭像幀＝寵物而家畫緊嗰幀（' + same + '/' + n + '）', { same, n });
    const h = [];
    for (let i = 0; i < 3; i++) { h.push(await E(() => { const c = document.querySelector('[data-testid=uiv2-portrait] canvas') || document.querySelector('[data-testid=uiv2-portrait]'); const cv = c.tagName === 'CANVAS' ? c : c.querySelector('canvas'); const d = cv.getContext('2d').getImageData(0, 0, cv.width, cv.height).data; let s = 0; for (let k = 0; k < d.length; k += 7) s = (s * 31 + d[k]) >>> 0; return s; })); await W(450); }
    ok(new Set(h).size >= 2, '頭像 canvas 內容會變（唔再死企 idle 第 0 幀）', h);
    await ctx.close(); }

  // ───────── F. 重疊檢查 3 個尺寸 × 每頁 ─────────
  console.log('F. UI 重疊（360×640、390×844、412×915）');
  for (const vp of [[360, 640], [390, 844], [412, 915]]) {
    const { ctx, page, E, W } = await boot(vp); await adult(E); await family(E); await W(1500);
    const tag = vp.join('x'); let tot = 0; const bad = [];
    for (const pg of ['main', 'work', 'house', 'plan', 'walk', 'diary', 'dex', 'settings', 'kid', 'tip', 'voice']) {
      await E(() => { try { __qa.work62.close(); } catch (e) { } try { __qa.l5b.close(); } catch (e) { } try { __qa.house.close(); } catch (e) { } const t = document.getElementById('u62tip'); if (t) t.remove(); const c = document.querySelector('[data-testid=l6b-close]'); if (c) c.click(); const b = document.querySelector('#modal[style*="flex"] [data-testid=modal-btn-0]'); if (b) b.click(); __glimmer.nq.clear(); }); await W(400);
      if (pg === 'settings') await E(() => { const tab = document.querySelector('[data-testid=hd-tab-home]'); if (tab) tab.click(); }).then(() => W(300));
      await E((pg) => { const c = (s) => { const e = document.querySelector(s); if (e) e.click(); };
        if (pg === 'work') __qa.work62.open(); else if (pg === 'house') c('#s2house'); else if (pg === 'plan') __qa.l5b.plan(); else if (pg === 'walk') c('#l6bbtn'); else if (pg === 'diary') c('#diary'); else if (pg === 'dex') c('#dex');
        else if (pg === 'settings') c('#gear'); else if (pg === 'kid') c('#s2kid'); else if (pg === 'tip') { __qa.ui62.dev().items.find(i => i.k === 'tipdemo').run(); } else if (pg === 'voice') __glimmer.say({ line: '今日天氣好好，我哋出去行下好唔好？', src: 'voice', urgent: true }); }, pg);
      await W(pg === 'house' ? 1800 : 900);
      const o = await E(() => __qa.ui62.overlap()); tot += o.hits.length; if (o.hits.length) bad.push([pg, o.hits.slice(0, 4)]);
      if (['main', 'work', 'house', 'plan', 'tip'].includes(pg)) await page.screenshot({ path: SHOTS + '6b2-ov-' + tag + '-' + pg + '.png' });
      if (pg === 'settings') await E(() => { const tab = document.querySelector('[data-testid=hd-tab-home]'); if (tab) tab.click(); });
    }
    ok(tot === 0, tag + '：11 頁可見 UI 框兩兩冇重疊', bad);
    await ctx.close();
  }

  // ───────── G. v1 唔受影響、?ui62=0 ─────────
  console.log('G. v1 舊 UI 停更（唔受影響）、?ui62=0');
  { const { ctx, page, E, W } = await boot([390, 844], QS + '&ui=1'); await adult(E); await W(800);
    await E(() => { __glimmer.nq.clear(); __glimmer.say({ line: 'v1 心聲測試一句長長嘅句子睇下有冇改到秒數', sec: 6, urgent: true }); }); await W(200);
    const v = await E(() => ({ v2: document.getElementById('ui').classList.contains('v2'), sec: __glimmer.nq.cur && __glimmer.nq.cur.sec, pe: getComputedStyle(document.getElementById('s12voice')).pointerEvents, tf: getComputedStyle(document.getElementById('toast')).top, live: !!(__glimmer.ui2 && __glimmer.ui2.on) }));
    ok(!v.v2 && v.sec === 6 && v.pe === 'none' && !v.live, 'v1：心聲秒數、撳穿、toast 位全部照舊', v);
    await ctx.close(); }
  { const { ctx, page, E, W } = await boot([390, 844], QS + '&ui62=0'); await adult(E); await family(E); await W(1500);
    const v = await E(() => ({ css: !!document.getElementById('ui62css'), btn: !!document.getElementById('u62workbtn'), qa: !!(window.__qa && __qa.ui62), live: !!(__glimmer.ui2 && __glimmer.ui2.live62), u: document.getElementById('ui').classList.contains('u62') }));
    ok(!v.css && !v.btn && !v.qa && !v.live && !v.u, '?ui62=0：6b.2 全停（返 6b.1 樣）', v);
    await ctx.close(); }

  ok(errs.length === 0, '冇 console error／pageerror', errs.slice(0, 5));
  await browser.close();
  console.log(`\n6b2 e2e：${pass} pass / ${fail} fail`);
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
