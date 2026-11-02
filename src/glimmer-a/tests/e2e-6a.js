/* 《微光小圃》 e2e-6a — 第 6 批 6a「團絨記得你」（遊策 breakthrough-6a6d-spec §6a）：
   本機 30 日記錄（嚟嘅時間、照顧、食咗乜、小遊戲最好、訪客）、每日第一次開 game 招呼 1 句（真重開 app）、一日只講一次、
   冇嚟 1 日／3 日以上句、返嚟第一下撳特別開心（真撳寵物）、日記自動加 1 句（日記頁）、記憶心聲（每日最多 2）、得意／委屈表情（6a.1 遊美 per_pet patch smug6a／pout6a；冇圖形態 placeholder）、
   30 日記錄 ≤200KB＋存檔來回、字清晰度（FP12 24px、對比 ≥4.5）、熱區 ≥48、🛠「6a」、?l6a=0。
   截圖 360×780 DPR3 → SHOTS（6a-*.png）。node tests/e2e-6a.js */
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
const DAY = 86400e3;

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROME || '/usr/bin/google-chrome', args: ['--no-sandbox', '--autoplay-policy=no-user-gesture-required'] });
  const ctx = await browser.newContext({ viewport: { width: 360, height: 780 }, deviceScaleFactor: 3 });
  const page = await ctx.newPage();
  const errs = [];
  page.on('console', m => { if (m.type() === 'error') errs.push(m.type() + ': ' + m.text() + ' ' + ((m.location() || {}).url || '')); });
  page.on('pageerror', e => errs.push('pageerror: ' + e.message));
  const E = (fn, arg) => page.evaluate(fn, arg);
  const W = (ms) => page.waitForTimeout(ms);
  const shot = (n) => page.screenshot({ path: SHOTS + '6a-' + n + '.png' });
  const Q = () => E(() => __qa.l6a.st());
  const QS = 'q=high&seed=21&l6a=1';
  const prep = () => E(() => { const s = __glimmer.state; s.stage = 'adult'; s.form = 'dust'; s.sleeping = false; Object.assign(s.needs, { mood: 60, energy: 100, hunger: 80, clean: 100 }); s.poops = 0; });
  const ready = async () => { await page.waitForFunction(() => window.__glimmer && __glimmer.liveLoad).catch(() => { }); await E(() => __glimmer.liveLoad); await E(() => __glimmer.s2Load).catch(() => { }); await E(() => __glimmer.houseLoad).catch(() => { }); };
  const fresh = async (qs) => { await page.goto(BASE + '?' + (qs || QS)); await E(() => { window.__noSaveOnHide = true; localStorage.clear(); }); await page.goto(BASE + '?' + (qs || QS)); await ready(); await W(300); };
  const reload = async (qs) => { await page.goto(BASE + '?' + (qs || QS)); await ready(); };
  // 準備「上次嚟」：last＝今日 − (gap+1) 日，嗰日有記錄；今日記錄刪走 → 重開 app 當今日第一次
  const plant = (gap) => E((gap) => { const M = Glimmer.long6a, s = __glimmer.state, m = M.st(s), t = __glimmer.now(), k = M.dayKey(t), pk = M.dayKey(t - (gap + 1) * 864e5);
    __qa.l6a.fillDay(pk); for (let i = 0; i <= gap; i++) delete m.d[M.dayKey(t - i * 864e5)]; m.last = pk; m.prev = null; m.greet = null; m.happy = null; m.said = {};
    const st = s.stage; __glimmer.save(); window.__noSaveOnHide = true; return { pk, st }; }, gap);
  const voice = () => E(() => { const v = document.getElementById('s12voice'); return { src: v.dataset.src || '', txt: v.textContent.trim(), op: +v.style.opacity, fs: getComputedStyle(v).fontSize, ff: getComputedStyle(v).fontFamily }; });
  const waitVoice = async (ms) => { for (let i = 0; i < (ms || 6000) / 200; i++) { const v = await voice(); if (v.src === 'mem6' && v.op > 0) return v; await W(200); } return voice(); };
  // 6a.1：遊美表情（per_pet patch）→ log 有 face（key＝kind6a、唔係 placeholder）＋ renderer 真係蓋咗（faceStat.face6a 有數）
  const faceSeen = (kind, why) => E(([kind, why]) => { const L = __qa.l6a.log().filter(x => x.k === 'face' && !x.ph && /^(smug|pout)6a$/.test(x.key || '') && (!kind || x.kind === kind) && (!why || x.why === why)); return L.length > 0 && (__glimmer.renderer.faceStat.face6a | 0) > 0 && !document.querySelector('#l6aface[data-ph]:not([style*="display: none"])'); }, [kind, why]);
  const readOk = async (name, sel) => { const a = await audit(page, sel); ok(a.items.length > 0 && a.bad.length === 0, name + '：字 ' + a.items.length + ' 段全部合格（FP12 24px、對比 ≥4.5）', a.bad.slice(0, 3).map(b => [b.t, b.eff, b.cr, b.fam])); };
  const petXY = () => E(() => { const r = document.getElementById('gl').getBoundingClientRect(), k = r.width / 195, h = Glimmer.ui.petHitBox(); return { x: r.left + (h.x + h.w / 2) * k, y: r.top + (h.y + h.h / 2) * k }; });
  const hit = (sel) => E((sel) => { const ui = document.getElementById('ui'), k = ui.getBoundingClientRect().width / ui.offsetWidth;
      return [...document.querySelectorAll(sel)].filter(e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden'; }).map(e => {
        e.scrollIntoView({ block: 'center', inline: 'nearest' }); const r = e.getBoundingClientRect(), cx = r.left + r.width / 2, cy = r.top + r.height / 2, h = 24 * k - 0.75; let n = 0;
        for (const [dx, dy] of [[-1, -1], [1, -1], [-1, 1], [1, 1], [0, -1], [0, 1], [-1, 0], [1, 0]]) { const t = document.elementFromPoint(cx + dx * h, cy + dy * h); if (t && (t === e || e.contains(t))) n++; }
        return { id: e.dataset.testid || e.id, n, lay: [Math.round(r.width / k), Math.round(r.height / k)] }; }); }, sel);
  const closeModals = async () => { for (let i = 0; i < 10; i++) { const open = await E(() => Glimmer.ui.isModalOpen()); if (!open) return; await E(() => { const b = document.querySelector('[data-testid=dev-close]') || [...document.querySelectorAll('#mbox .btn')].pop(); if (b) b.click(); }); await W(150); } };

  console.log('# 載入');
  await fresh();
  ok(await E(() => !!(Glimmer.long6a && Glimmer.long6aui && window.__qa && __qa.l6a && __glimmer.l6a)), 'long6a＋long6aui 裝咗');
  ok(await E(() => /^6[abc]$/.test(Glimmer.data.PARAMS.series2.version)), '版本 6a');
  ok(await E(() => Glimmer.long6a.ALL.length === 60 && new Set(Glimmer.long6a.ALL.map(L => L.t)).size === 60), '首批 60 句（冇重複）');
  ok(await E(() => Glimmer.devmode.sections().some(s => s.id === 'l6a' && s.title.includes('6a'))), '🛠 開發者模式有「6a」分組');
  let q = await Q(); ok(q.days === 1 && q.today && q.today.n === 1 && !q.prev, '第一次開：記低今日（第一日唔講招呼）', q);
  await W(3500); q = await Q(); ok(q.n.greet === 0, '第一日：冇招呼（未有上次記錄）', q.n);

  console.log('# 記錄（照顧／食咗乜／小遊戲／訪客）');
  await prep();
  await E(() => { const S = Glimmer.sim, s = __glimmer.state; s.needs.hunger = 20; S.feed(s, 'meal'); __glimmer.sysFed('meal'); S.play(s); });
  await E(() => { const s = __glimmer.state; Glimmer.sys12b.gameFinish(s, 'bounce', 12, __glimmer.now()); Glimmer.sys12b.gameFinish(s, 'bounce', 27, __glimmer.now()); });
  await E(() => Glimmer.visit.startVisit(__glimmer.state, 'snail_postman', __glimmer.now()));
  q = await Q(); const td = q.today;
  ok(td.c.feed >= 1 && td.c.play >= 1, '照顧類型（餵食、玩耍）', td.c);
  ok(td.f.meal >= 1, '食咗乜（暖菇飯）', td.f);
  ok(td.g.bounce && td.g.bounce[0] === 27 && td.g.bounce[1] >= 2 && td.g.bounce[2] === 1, '小遊戲當日最好（彈彈葉 27 分，破紀錄）', td.g);
  ok(td.vi.includes('蝸牛郵差'), '訪客（蝸牛郵差）', td.vi);
  ok(q.ticks >= 2, '細佬大事每秒掃描（ticks ' + q.ticks + '）');

  console.log('# 每日第一次開 game：招呼 1 句（真重開 app）');
  await plant(0); await reload(); await prep(); await W(300);
  let v = await waitVoice(7000); q = await Q();
  ok(v.src === 'mem6' && v.txt.length > 4 && q.n.greet === 1 && q.greet === q.last, '重開 app → 團絨講招呼', { v, n: q.n });
  const gid = (q.log.find(x => x[2] === 'greet') || [])[1];
  ok(gid && !/^a[123]_/.test(gid), '琴日有嚟 → 講琴日嘅事（' + gid + '）', q.log);
  ok(!/\{\w+\}/.test(v.txt), '空位全部填好', v.txt);
  const V3 = await E(() => document.getElementById('ui').classList.contains('v3'));   // #83：V3 換皮 → Noto CJK TC subset（GlimmerV3Sans）代 FP12
  ok(v.fs === '24px' && (V3 ? /GlimmerV3Sans/ : /GlimmerFP12/).test(v.ff), '記憶句泡泡 ' + (V3 ? 'V3 字' : 'FP12') + ' 24px', v);
  // 遊測：淡入（transition .35s）第一格 computed opacity 仲 <0.05 就截圖審查 → flaky；等淡入完（computed ≥0.99，連續 2 格）先審
  const fadeIn = async () => { let n = 0; for (let i = 0; i < 40; i++) { const o = await E(() => +getComputedStyle(document.getElementById('s12voice')).opacity); n = o >= 0.99 ? n + 1 : 0; if (n >= 2) return o; await W(50); } return -1; };
  ok(await fadeIn() >= 0.99, '招呼泡泡淡入完（computed opacity ≥0.99）先審對比');
  await E(() => { document.getElementById('s12voice').style.pointerEvents = 'auto'; }); await readOk('招呼泡泡', '#s12voice'); await E(() => { document.getElementById('s12voice').style.pointerEvents = ''; });
  ok(await faceSeen(null, 'bubble'), '講嘢時團絨換 6a 表情（遊美 per_pet patch，smug6a／pout6a）', await E(() => __qa.l6a.log().filter(x => x.k === 'face').slice(-3)));
  await shot('01-greet');
  await W(6500); await reload(); await W(3500); q = await Q(); ok(q.n.greet === 1, '同一日再開 → 唔再講招呼', q.n);
  ok(q.today.n >= 1, '今日嚟咗 ' + q.today.n + ' 次（20 分鐘內返嚟唔當新一次）');

  console.log('# 冇嚟 1 日 →「你琴日去咗邊？」類；冇懲罰；第一下撳特別開心');
  const bond0 = await E(() => Glimmer.sys12.bond(__glimmer.state, __glimmer.now()).v);
  await plant(1); await reload(); await prep(); v = await waitVoice(7000); q = await Q();
  const a1 = q.log.filter(x => x[2] === 'greet').pop();
  ok(a1 && /^a1_/.test(a1[1]) && v.src === 'mem6', '冇嚟 1 日 → 冇嚟 1 日句：「' + v.txt + '」', q.log);
  ok(await E(() => Glimmer.long6a.LINES.absent1.some(L => L[1] === '你琴日去咗邊？')), 'spec 句「你琴日去咗邊？」喺 1 日句庫');
  ok(q.happy === q.last && q.gap === 1, '記低：冇嚟 1 日、等緊特別開心', { happy: q.happy, gap: q.gap });
  const bond1 = await E(() => Glimmer.sys12.bond(__glimmer.state, __glimmer.now()).v);
  ok(bond1 >= bond0 - 2.0001, '6a 冇加懲罰（親密度只有系統 6 原本嘅冇照顧扣分）', { bond0, bond1 });
  await W(6300);
  await E(() => { const p = document.getElementById('devp'); if (p) p.classList.add('fold'); });
  // 6a.1（遊測 P1）：第一下撳純視覺 → 心情共用額、摸頭委託、mem6 摸頭三個計數唔郁
  const cnt = () => E(() => { const s = __glimmer.state, M = Glimmer.long6a, d = M.st(s).d[M.dayKey(__glimmer.now())] || {}, Q12 = s.sys12 && s.sys12.quests;
    return { press: __glimmer.lastPetPress || null, shared: __qa.touch.st().mood.shared, grants: __qa.touch.st().grants.filter(g => g.ok).length, quest: Q12 ? Q12.list.reduce((a, x) => a + (x.n || 0), 0) : 0, pat: (d.c && d.c.pat) || 0 }; });
  await E(() => { localStorage.removeItem('fpet_daily_v1'); const M = Glimmer.long6a, d = M.st(__glimmer.state).d[M.dayKey(__glimmer.now())]; if (d && d.c) d.c.pat = 0; __glimmer.lastPetPress = null; });
  const k0 = await cnt();
  const c = await petXY(); await page.mouse.click(c.x, c.y); await W(250);
  q = await Q();
  ok(!q.happy && q.n.happy === 1, '返嚟第一下撳 → 特別開心（用咗）', q.n);
  const k1 = await cnt(); ok(k0.shared === 0 && k1.shared === 0 && k1.grants === k0.grants && k1.quest === k0.quest && k1.pat === 0 && !k1.press, '第一下撳純視覺（唔跑 sysPress）：心情共用額 0、摸頭委託冇加、mem6 摸頭 0', { k0, k1 });
  ok(await E(() => document.querySelectorAll('[data-testid=l6a-heart]').length >= 3), '心心飄出嚟');
  ok(await E(() => __qa.touch && __qa.touch.st().act && __qa.touch.st().act.key === 'g_tickle'), '團絨笑到震（g_tickle）', await E(() => __qa.touch && __qa.touch.st().act));
  ok(await faceSeen('smug'), '得意表情 smug6a（' + (await E(() => __qa.l6a.st().faceFk)) + ' per_pet；冇 placeholder）', await E(() => __qa.l6a.log().filter(x => x.k === 'face').slice(-3)));
  await shot('02-happy');
  await W(1800); await E(() => { __glimmer.lastPetPress = null; }); { const c2 = await petXY(); await page.mouse.click(c2.x, c2.y); } await W(250); q = await Q(); ok(q.n.happy === 1, '第二下撳 → 正常（唔再特別開心）', q.n);
  { const k2 = await cnt(); ok(!!k2.press && k2.grants >= k1.grants, '第二下撳 → 照舊行觸摸／sysPress', { k1, k2 }); }

  console.log('# 冇嚟 3 日以上 →「我以為你搬咗屋。」類');
  await plant(4); await reload(); await prep(); v = await waitVoice(7000); q = await Q();
  const a3 = q.log.filter(x => x[2] === 'greet').pop();
  ok(a3 && /^a3_/.test(a3[1]) && q.gap === 4, '冇嚟 4 日 → 3 日以上句：「' + v.txt + '」', { a3, gap: q.gap });
  ok(await E(() => Glimmer.long6a.LINES.absent3.some(L => L[1] === '我以為你搬咗屋。')), 'spec 句「我以為你搬咗屋。」喺 3 日以上句庫');
  ok(await faceSeen('pout'), '委屈表情 pout6a（per_pet；冇 placeholder）', await E(() => __qa.l6a.log().filter(x => x.k === 'face').slice(-3)));
  await W(500); await shot('03-absent3');

  console.log('# 日記每日自動寫 1 句');
  await W(6500);
  let r = await E(() => __qa.l6a.dev().items.find(i => i.k === 'diary').run());
  ok(r.ok, '琴日嗰篇加咗 1 句：' + r.msg, r);
  const dd = await E(() => { const M = Glimmer.long6a, k = M.dayKey(__glimmer.now() - 864e5), e = Glimmer.sys12.diary(__glimmer.state, __glimmer.now()).list.find(x => x.d === k); return e ? { m6: e.m6, n: e.lines.length, mem: e.lines[e.lines.length - 2], close: e.lines[e.lines.length - 1] } : null; });
  ok(dd && M_ok(dd), '記憶句擺喺收尾句前面', dd);
  function M_ok(d) { return d.m6 && d.m6 !== '-' && d.mem && d.close && d.mem !== d.close; }
  const n2 = await E(() => __qa.l6a.annotate()); ok(n2 === 0, '每篇只寫一次', n2);
  ok(await E(() => { const d = Glimmer.sys12.diary(__glimmer.state, __glimmer.now()); return !d.today || !!d.today.m6; }), '今日草稿有預覽句');
  await E(() => { __glimmer.s12.dsrc = 'cur'; __qa.sys12.open('diary'); }); await W(400);
  await E(() => { const k = Glimmer.long6a.dayKey(__glimmer.now() - 864e5); const pages = [...document.querySelectorAll('[data-testid=s12-diary-prev]')]; return pages.length; });
  for (let i = 0; i < 4; i++) { const pg = await E(() => __qa.sys12.diaryPage()); if (pg && pg.txt.includes(dd.mem)) break; await E(() => { const b = document.querySelector('[data-testid=s12-diary-prev]'); if (b) b.click(); }); await W(250); }
  const pg = await E(() => __qa.sys12.diaryPage());
  ok(pg && pg.txt.includes(dd.mem), '日記頁顯示記憶句', pg && pg.txt.slice(0, 80));
  ok(await E((mem) => { const p = document.querySelector('[data-testid=s12-diary-page]'); const el = [...p.querySelectorAll('*')].find(e => e.children.length === 0 && e.textContent.trim() === mem); if (!el) return false; el.dataset.l6amem = '1'; el.scrollIntoView({ block: 'center' }); return true; }, dd.mem), '日記頁：記憶句獨立一行');
  await W(200); await readOk('日記頁記憶句', '[data-l6amem]');
  await shot('04-diary');
  await closeModals(); await E(() => { if (__qa.sys12.close) __qa.sys12.close(); });

  console.log('# 心聲泡泡：記憶句（每日最多 2）');
  await E(() => { const M = Glimmer.long6a, s = __glimmer.state, m = M.st(s), t = __glimmer.now(); m.vn = 0; m.vday = null; M.note(s, 'care', 'rinse', 0, 0, 0, t); M.note(s, 'food', 'soup', 0, 0, 0, t); M.note(s, 'care', 'pat', 0, 0, 0, t); M.note(s, 'care', 'pat', 0, 0, 0, t); });
  const outs = await E(() => { const o = []; for (let i = 0; i < 5; i++) { Glimmer.sys12.bondOf(__glimmer.state).lastVoice = 0; const r = __glimmer.sysVoice({ force: true, src: 'test', mem6: true, rng: () => 0.01 }); o.push(r.src); } return o; });
  ok(outs.filter(x => x === 'mem6').length === 2 && outs.length === 5, '5 次心聲 → 2 次記憶句（每日上限 2），其餘照舊', outs);
  await W(300);
  ok(await E(() => { const h = Glimmer.sys12.bondOf(__glimmer.state).heard, L = new Set(Glimmer.long6a.ALL.map(x => x.t.slice(0, 4))); return !h.some(x => L.has(String(x).slice(0, 4))); }), '心聲收集冇被記憶句佔');

  console.log('# 7 日唔重複（招呼＋日記＋心聲共用）');
  const rep = await E(() => { const M = Glimmer.long6a, s = JSON.parse(JSON.stringify(__glimmer.state)); delete s.mem6; let t = __glimmer.now(); const seen = {}; let bad = 0, n = 0;
    for (let d = 0; d < 40; d++) { const T = t + d * 864e5 + 9 * 36e5; M.visit(s, T); M.note(s, 'care', 'feed', 0, 0, 0, T); M.note(s, 'food', 'cookie', 0, 0, 0, T); if (d % 3 === 0) M.note(s, 'game', 'catch', 10 + d, 2, 0, T);
      const ps = [M.greet(s, T, {}), M.voicePick(s, T + 36e5, { force: true }), M.voicePick(s, T + 2 * 36e5, { force: true })]; const dk = M.dayKey(T - 864e5); const dp = M.rec(s, dk) && M.diaryPick(s, dk, T, {}); if (dp) ps.push(M.commit(s, dp, 'diary', T));
      for (const p of ps) { if (!p) continue; n++; if (seen[p.id] != null && d - seen[p.id] < 7) bad++; seen[p.id] = d; } }
    return { bad, n, used: Object.keys(seen).length }; });
  ok(rep.bad === 0 && rep.n >= 60, '40 日模擬：講 ' + rep.n + ' 句、用 ' + rep.used + ' 款，7 日內冇重複', rep);

  console.log('# 30 日記錄 ≤200KB＋存檔來回');
  r = await E(() => __qa.l6a.dev().items.find(i => i.k === 'fill30').run());
  q = await Q(); ok(q.days === 30 && q.bytes <= 200 * 1024, '30 日 ' + (q.bytes / 1024).toFixed(1) + 'KB ≤ 200KB', r);
  await E(() => { const M = Glimmer.long6a, m = M.st(__glimmer.state); for (const k of Object.keys(m.d)) { const d = m.d[k]; for (let i = 0; i < 8; i++) d.k.push(['lesson', '細佬名字好長好長', '少年']); d.vi = ['蝸牛郵差', '蘑菇婆婆', '螢火小販', '蝸牛郵差2']; for (const g of ['catch', 'hide', 'bounce', 'ghide', 'firefly']) d.g[g] = [99999, 3, 1]; } __glimmer.save(); });
  q = await Q(); ok(q.bytes <= 200 * 1024, '塞滿上限仍然 ' + (q.bytes / 1024).toFixed(1) + 'KB ≤ 200KB');
  await reload(); q = await Q(); ok(q.days === 30, '重開 app：30 日記錄保留', q.days);
  ok(await E(() => { const L = localStorage, k = Glimmer.data.PARAMS.saveKey; return JSON.parse(L.getItem(k)).mem6 != null; }), '存檔入面有 mem6');

  console.log('# 🛠 開發者模式「6a」');
  await closeModals(); await E(() => __qa.devmode.setShown(true)); await W(100); await page.locator('[data-testid=dev-btn]').click(); await W(400);
  ok(await page.locator('[data-testid=dev-sec-l6a]').isVisible(), '分組「6a（團絨記得你）」喺開發者模式');
  const L6 = await hit('[data-testid^=dev-l6a-]'); ok(L6.length >= 10 && L6.every(x => x.n === 8), '6a 掣熱區 ≥48（' + L6.length + ' 個）', L6.filter(x => x.n < 8).slice(0, 3));
  await page.locator('[data-testid=dev-sec-l6a]').scrollIntoViewIfNeeded(); await readOk('開發者「6a」', '[data-testid=dev-sec-l6a]');
  await page.locator('[data-testid=dev-l6a-pout]').click(); await W(300);
  ok(await E(() => __qa.l6a.st().faceKey === 'pout6a' && __qa.l6a.st().faceMode === 'art'), '撳「委屈」→ pout6a 表情');
  ok(!(await E(() => [...document.querySelectorAll('[data-testid^=s2-set],[data-testid^=toggle-]')].some(e => /6a/.test(e.textContent)))), '試玩掣唔喺設定');
  await closeModals();

  console.log('# 浮動團絨唔受影響');
  ok(await E(() => { const o = __glimmer.evo.sys12Overlay ? __glimmer.evo.sys12Overlay() : {}; return !JSON.stringify(o).includes('mem6'); }), '懸浮 snapshot 冇 6a 記憶句');

  console.log('# 6a.1 遊美表情：49 隻形態 per_pet（smug6a／pout6a），疊法同 3a（idle 幀 0 大細、左上對齊）');
  await closeModals();
  const fa = await E(() => __qa.l6a.st().faceArt); ok(fa.json && fa.pets === 49 && !fa.err.length, 'faces6a.json 49 隻形態', fa);
  ok(await E(() => { const r = __glimmer.renderer.rx; return !r || !r.anchors || Object.values(r.anchors).every(a => !a.faces || !a.faces.order.some(k => /6a$/.test(k))); }), '3a reactions 嘅 smug 冇被改（6a 用 smug6a／pout6a key）');
  const strip3 = [];
  for (const [st, fm] of [['elder', 'bright'], ['adult', 'moon'], ['juvenile', 'dust']]) {
    for (const kind of ['smug', 'pout']) {
      await E(([st, fm]) => { const s = __glimmer.state; s.stage = st; s.form = fm; s.sleeping = false; Object.assign(s.needs, { mood: 80, energy: 100, hunger: 80, clean: 100 }); s.poops = 0; }, [st, fm]); await W(300);
      await E(k => __qa.l6a.face(k, 4000, 'e2e'), kind); await W(500); await E(k => __qa.l6a.face(k, 4000, 'e2e'), kind); await W(350);
      const r = await E(() => { const l = __glimmer.renderer.faceStat.last || {}, q = __qa.l6a.st(), F = Glimmer.data.FORMS[l.form]; return { form: l.form, f6: l.face6a || null, clip: l.clip, frame: l.frame, mode: q.faceMode, fsz: F && F.frameSize, dom: !!document.querySelector('#l6aface[data-ph]:not([style*="display: none"])') }; });
      ok(r.f6 === kind + '6a' && r.mode === 'art' && r.clip === 'idle' && r.frame === 0 && !r.dom, st + '／' + fm + ' → ' + r.form + '（' + r.fsz + 'px）蓋 ' + kind + '6a（base＝idle 幀 0）', r);
      if (kind === 'smug') strip3.push(r.form);
      if (st === 'elder' || st === 'adult') await shot('05-face-' + r.form + '-' + kind);
    }
  }
  await E(() => __qa.l6a.hideFace()); await W(300);
  ok(await E(() => !(__glimmer.renderer.faceStat.last || {}).face6a), '表情時間過咗 → 返原本五官');
  await E(() => { const s = __glimmer.state; s.stage = 'egg'; }); await W(200); await E(() => __qa.l6a.face('smug', 1500, 'e2e')); await W(150);
  ok(await E(() => __qa.l6a.st().faceMode === 'ph' && __qa.l6a.st().facePh === '6a:face_smug'), '冇 per_pet 圖嘅形態（蛋）→ 照舊 placeholder 疊層');
  await E(() => { __qa.l6a.hideFace(); const s = __glimmer.state; s.stage = 'adult'; s.form = 'dust'; }); await W(200);

  console.log('# ?l6a=0');
  await fresh('q=high&seed=21&l6a=0'); await W(1500);
  ok(await E(() => !window.__qa.l6a && !__glimmer.l6a && !__glimmer.state.mem6), '?l6a=0：冇裝、冇記錄');
  ok(await E(() => !Glimmer.devmode.sections().some(s => s.id === 'l6a')), '?l6a=0：冇「6a」分組');
  ok(await E(() => { const r = __glimmer.sysVoice({ force: true, src: 'test' }); return !r.ok || r.src !== 'mem6'; }), '?l6a=0：心聲照舊');

  console.log('# webdriver 預設（冇 ?l6a=1）：記錄照做，唔自動講');
  await fresh('q=high&seed=21'); q = await Q(); ok(q.auto === false && q.days === 1, '記錄有、自動講閂', { auto: q.auto, days: q.days });

  ok(errs.length === 0, '冇 console error', errs.slice(0, 5));
  console.log(`\n結果：${pass} 通過，${fail} 失敗`);
  await browser.close(); process.exit(fail ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
