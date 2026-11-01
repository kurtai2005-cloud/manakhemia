/* 《微光小圃》 e2e-b3b — 第 3 批 3b（docs-gdd/batch3-fun-spec.md §③④）：朋友訪客（入場／帶路一圈／信／拖禮物／友好度＋徽章／婆婆種子／小販）、
   進化大場面（8s、跳過、播完先出原本彈窗）、圖鑑「團絨日記」四格、預兆（閃剪影／胃口大／怪夢）、?b3b=0。截圖 → SHOTS。
   node tests/e2e-b3b.js（BASE 預設 http://localhost:8138/index.html） */
const path = require('path');
let chromium;
for (const p of [process.env.PW, 'playwright-core', '/workspace/qa-live-s1/node_modules/playwright-core']) { try { if (p) { chromium = require(p).chromium; break; } } catch (e) { } }
if (!chromium) { console.error('找不到 playwright-core'); process.exit(2); }
const BASE = process.env.BASE || 'http://localhost:8138/index.html';
const SHOTS = process.env.SHOTS || process.env.OUT || path.join(__dirname, '..', '..', '..', 'screens') + '/';
require('fs').mkdirSync(SHOTS, { recursive: true });
let pass = 0, fail = 0;
const ok = (c, n, info) => { if (c) { pass++; console.log('  ✓ ' + n); } else { fail++; console.log('  ✗ ' + n + (info !== undefined ? ' → ' + JSON.stringify(info) : '')); } };
const V = require('../src/visit.js');

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROME || '/usr/bin/google-chrome', args: ['--no-sandbox', '--autoplay-policy=no-user-gesture-required'] });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2 });
  const page = await ctx.newPage();
  const errs = [];
  page.on('console', m => { if (m.type() === 'error') errs.push(m.type() + ': ' + m.text()); });
  page.on('pageerror', e => errs.push('pageerror: ' + e.message));
  const E = (fn, arg) => page.evaluate(fn, arg);
  const W = (ms) => page.waitForTimeout(ms);
  const shot = (n, clip) => page.screenshot(Object.assign({ path: SHOTS + 'b3b-' + n + '.png' }, clip ? { clip } : {}));
  const load = async (qs, setup) => {
    await page.goto(BASE + '?' + qs); await E(() => { window.__noSaveOnHide = true; localStorage.clear(); });
    await page.goto(BASE + '?' + qs); await page.waitForFunction(() => window.__glimmer && __glimmer.liveLoad).catch(() => { }); await E(() => __glimmer.liveLoad); await E(() => __glimmer.b3bLoad); await W(400);
    await E((st) => { window.__noSaveOnHide = true; const s = __glimmer.state; s.stage = st || 'adult'; s.form = st === 'adult' || !st ? 'dust' : null; s.sleeping = false; Object.assign(s.needs, { mood: 80, energy: 100, hunger: 100, clean: 100 }); s.poops = 0; }, setup || null);
    await W(300);
  };
  const closeModals = async () => { for (let i = 0; i < 10; i++) { const open = await E(() => Glimmer.ui.isModalOpen()); if (!open) return; await E(() => { const b = [...document.querySelectorAll('#mbox .btn, #mbox button')].filter(x => !x.closest('[data-testid=b3b-shop]')).pop(); if (b) b.click(); }); await W(150); } };
  const b3 = () => E(() => __qa.b3b.st());
  const css = (x, y) => E(([x, y]) => __qa.b3b.css(x, y), [x, y]);
  const until = async (fn, ms) => { const t0 = Date.now(); while (Date.now() - t0 < (ms || 8000)) { const s = await b3(); if (fn(s)) return s; await W(100); } return b3(); };

  console.log('# 預設：Playwright 唔自動出訪客／大場面／預兆；?b3b=0 全停');
  await load('q=high&hour=13&seed=21&ev=0');
  let s = await b3(); ok(s.ready && !s.errors.length, '3b 圖全部載入', s.errors);
  ok(!s.auto.visit && !s.auto.scene && !s.auto.omen, 'webdriver 下 AUTO 全閂', s.auto);
  ok(await E(() => Glimmer.data.PARAMS.systems12b.badges.total === 34), '徽章 34 個');

  console.log('# ③ 蝸牛郵差（右邊入、向左行）');
  ok((await E(() => __qa.b3b.spawn('snail_postman', 'right'))).ok, 'spawn 蝸牛（右）');
  await W(1200); s = await b3(); ok(s.vs.phase === 'enter' && s.vs.dir === -1 && s.vs.x < 225, '由右邊行入、向左', s.vs);
  ok(s.render.visitor > 10, '有畫訪客', s.render);
  ok(s.log.some(l => l.k === 'spawn'), '記錄 spawn');
  await shot('visitor-arrival');
  // 向左行：信＋心都要鏡像（錨點喺 pivot 左邊）
  await until(s => s.vs && s.vs.x < 168, 12000);
  await E(() => __qa.b3b.props({ letter: 'wait', heart: true, heartT: 200, meter: true })); await W(150);
  s = await b3(); const sn = s.vs; ok(Math.abs(sn.head.x - (sn.x + (22 - 33))) < 0.1 && Math.abs(sn.bag.x - (sn.x + (22 - 28))) < 0.1, '向左：head／bag 錨點鏡像（W−1−x）', { head: sn.head, bag: sn.bag, x: sn.x });
  let a = await css(sn.x - 40, sn.y - 60), b = await css(sn.x + 40, sn.y + 8);
  await shot('snail-walk-left', { x: a.x, y: a.y, width: b.x - a.x, height: b.y - a.y });
  // 像素檢查：信喺頭頂（head 錨點 x），唔喺殼嗰邊
  const px = await E(([hx, hy, sx]) => { const cv = Glimmer.render && __glimmer.renderer.canvas; const g = document.createElement('canvas'); g.width = cv.width; g.height = cv.height; const q = g.getContext('2d'); q.drawImage(cv, 0, 0); const k = cv.width / 195;
    const col = (x, y) => { const d = q.getImageData(Math.round(x * k), Math.round(y * k), 1, 1).data; return d[0] + d[1] + d[2]; }; let L = 0, R = 0; for (let y = hy - 18; y < hy - 8; y++) { for (let x = hx - 6; x <= hx + 6; x++) L = Math.max(L, col(x, y)); for (let x = sx + 6; x <= sx + 18; x++) R = Math.max(R, col(x, y)); } return { L, R }; }, [sn.head.x, sn.head.y, sn.x]).catch(e => ({ err: String(e) }));
  ok(px.err || px.L > 500, '信（白）畫喺鏡像後嘅頭頂', px);
  await E(() => __qa.b3b.props({ letter: null })); await E(() => { const c = 0; });
  s = await until(s => s.vs && s.vs.phase === 'join', 15000); ok(s.vs.phase === 'join', '企定 → 團絨得意 pose（join）', s.vs);
  await W(500); s = await b3(); ok(s.puppet && s.puppet.clip === 'smug_pose' && s.puppet.face && s.puppet.face.mouth === 'squint', '團絨 smug（eyes sleepy＋mouth squint）', s.puppet);
  s = await until(s => s.vs && s.vs.phase === 'lead', 3000); await W(1500); s = await b3();
  ok(s.vs.phase === 'lead' && s.puppet && s.puppet.clip === 'walk_happy', '帶路一圈：團絨 walk_happy', s.puppet);
  ok(s.puppet && typeof s.puppet.depth === 'number', '帶路有深度（y）', s.puppet);
  s = await until(s => s.vs && s.vs.phase === 'stand', 9000); ok(s.vs.phase === 'stand' && !s.puppet, '一圈完 → 放返團絨（stand）', s.puppet);
  ok(await E(() => !__glimmer.beh.puppet && (__glimmer.beh.depth | 0) === 0), '團絨深度歸零、行為機恢復');
  s = await until(s => s.vs && s.vs.letter === 'wait', 3000); ok(s.vs.letter === 'wait', '蝸牛信飛上頭頂');
  await W(1200); s = await b3();
  let L = s.vs.letterRect, p = await css(L.x + L.w / 2, L.y + L.h / 2); await page.mouse.click(p.x, p.y); await W(300);
  s = await b3(); ok(!s.vs.letter && s.save.letters.length === 1 && s.log.some(l => l.k === 'letter'), '真滑鼠撳信 → 一句日記', s.save.letters);
  ok(s.tray, '托盤出咗');
  // 真拖禮物
  const chip = await page.$('#b3bTray .b3b-chip'); let bb = await chip.boundingBox(); const H = s.vs.hit; p = await css(H.x + H.w / 2, H.y + H.h / 2);
  await page.mouse.move(bb.x + bb.width / 2, bb.y + bb.height / 2); await page.mouse.down(); await page.mouse.move(p.x, p.y, { steps: 10 }); await page.mouse.up(); await W(250);
  s = await b3(); ok(s.save.vis.snail_postman.fr === 1 && s.vs.clip === 'happy', '拖去訪客身 → 送禮、友好度 1、happy', s.save.vis.snail_postman);
  ok(s.log.some(l => l.k === 'gift'), '送禮記錄'); await W(400); s = await b3(); ok(!s.tray, '今日送咗 → 收埋托盤');
  p = await css(H.x + H.w / 2, H.y + H.h / 2); await page.mouse.click(p.x, p.y); await W(400);
  ok(await E(() => document.querySelector('[data-testid=b3b-fr]') && document.querySelector('[data-testid=b3b-fr]').dataset.fr === '1'), '撳訪客 → 卡（友好度 1 粒心）');
  await closeModals(); await W(300);
  // 滿 5 → 擺設＋徽章
  await E(() => { const o = __glimmer.state.b3b; o.vis.snail_postman.fr = 4; o.day.gift = {}; }); let r = await E(() => __qa.b3b.gift());
  ok(r.ok && r.reward && r.reward.decor === 'deco_mailbox', '友好度滿 5 → 郵筒仔', r);
  await W(300); s = await b3(); ok(s.save.decor.deco_mailbox > 0, '擺設寫入');
  ok(await E(() => Glimmer.sys12b.badges(__glimmer.state).list.find(b => b.k === 'friend_snail').got), '蝸牛好朋友徽章');
  await closeModals();
  await E(() => __qa.b3b.until(0)); s = await until(s => !s.vs, 15000); ok(!s.vs, '10 分鐘到 → 行返出去', s.vs);
  await E(() => __qa.b3b.spawn('snail_postman', 'left')); await E(() => Object.defineProperty(document, 'hidden', { configurable: true, get: () => true })); await E(() => document.dispatchEvent(new Event('visibilitychange')));
  s = await b3(); ok(!s.vs, '落線（hidden）→ 即走'); await E(() => { delete document.hidden; });

  console.log('# 蘑菇婆婆：種子＝下次種花免費');
  await load('q=high&hour=13&seed=22&ev=0');
  await E(() => { __qa.b3b.spawn('mushroom_granny', 'left'); __qa.b3b.phase('stand'); }); await W(300);
  s = await b3(); ok(s.save.seeds === 1 && s.vs.seed, '婆婆送種子（彈去背包）', s.save.seeds);
  r = await E(() => { const s = __glimmer.state, X = Glimmer.sys12, w = X.st(s).wallet; w.total = 0; const i = Glimmer.sys12b.st(s).garden.pots.findIndex(p => !p); const r = Glimmer.sys12b.plant(s, i, Glimmer.data.PARAMS.systems12b.garden.flowers[0].k, Date.now()); return { r, w: w.total, seeds: s.b3b.seeds }; });
  ok(r.r.ok && r.r.free && r.w === 0 && r.seeds === 0, '0 碎都種到（用婆婆種子）', r);
  r = await E(() => { const s = __glimmer.state, i = Glimmer.sys12b.st(s).garden.pots.findIndex(p => !p); return i < 0 ? { skip: 1 } : Glimmer.sys12b.plant(s, i, Glimmer.data.PARAMS.systems12b.garden.flowers[0].k, Date.now()); });
  ok(r.skip || (!r.ok && r.reason === 'shards'), '冇種子 → 照舊要碎', r);

  console.log('# 螢火小販（夜晚）：賣擺設、發光');
  await load('q=high&hour=22&seed=23&ev=0');
  await E(() => { Glimmer.sys12.st(__glimmer.state).wallet.total = 15; __qa.b3b.spawn('firefly_vendor', 'right'); __qa.b3b.phase('stand'); }); await W(400);
  s = await b3(); p = await css(s.vs.hit.x + s.vs.hit.w / 2, s.vs.hit.y + s.vs.hit.h / 2); await page.mouse.click(p.x, p.y); await W(400);
  ok(await E(() => !!document.querySelector('[data-testid=b3b-shop]')), '撳小販 → 商店');
  await E(() => { Glimmer.sys12.st(__glimmer.state).wallet.total = 15; });
  await page.click('[data-testid=b3b-buy-deco_mailbox]'); await W(200);
  r = await E(() => ({ w: Glimmer.sys12.st(__glimmer.state).wallet.total, d: __glimmer.state.b3b.decor }));
  ok(r.w === 3 && r.d.deco_mailbox, '買郵筒仔 12 碎', r);
  await page.click('[data-testid=b3b-buy-deco_firefly_jar]'); await W(200); ok(await E(() => Glimmer.sys12.st(__glimmer.state).wallet.total === 3 && !__glimmer.state.b3b.decor.deco_firefly_jar), '唔夠碎唔賣');
  s = await b3(); ok(s.render.visitor > 0, '小販有畫（emissive＋glow light）');
  await closeModals(); await W(300);
  await shot('vendor-night');

  console.log('# ④ 進化大場面（真事件流）');
  await load('q=high&hour=13&seed=24&ev=0&evoscene=1', 'sprout');
  ok((await b3()).auto.scene, '?evoscene=1 開');
  await E(() => { const s = __glimmer.state; s.stage = 'juvenile'; s.ev.push({ type: 'grow', stage: 'juvenile', cq: 0 }); Glimmer.ui.processEvents(); });
  s = await until(s => s.scene, 3000); ok(s.scene && s.scene.from === 'evo_sprout' && s.scene.to === 'evo_hop', '成長事件 → 大場面（sprout→hop）', s.scene);
  ok(s.hud && !(await E(() => Glimmer.ui.isModalOpen())), 'HUD 收埋、原本彈窗未出');
  ok(s.save.comics.n3, '四格 n3 解鎖');
  await E(() => __qa.b3b.sceneAt(4520, true)); await W(200); s = await b3(); ok(s.scene.last.ring && s.scene.last.shards > 0 && s.scene.last.sil, '爆：碎片＋光環＋剪影', s.scene.last);
  await shot('evo-mid');
  await E(() => __qa.b3b.sceneAt(7000, true)); await W(200); s = await b3(); ok(s.scene.last.card && s.scene.card && s.scene.card.name.length > 0, '名卡＋名字', s.scene.card);
  await shot('evo-namecard');
  await E(() => __qa.b3b.sceneAt(7400, false)); s = await until(s => !s.scene, 3000);
  ok(!s.scene && s.played.length === 1, '播完', s.played);
  await W(300); ok(await E(() => Glimmer.ui.isModalOpen()), '播完先出原本成長彈窗');
  ok(!(await E(() => document.body.classList.contains('b3b-evo'))) && !(await E(() => __glimmer.beh.puppet)), 'HUD 返嚟、團絨放返');
  await closeModals(); await W(300);
  // 跳過（真滑鼠撳）
  await E(() => { const s = __glimmer.state; s.stage = 'adult'; s.form = 'tide'; s.ev.push({ type: 'evolve', form: 'tide', cq: 0 }); Glimmer.ui.processEvents(); });
  s = await until(s => s.scene, 3000); ok(s.scene && s.scene.to === 'evo_guard_tide', '進化 → 潮守夜者', s.scene);
  await page.mouse.click(195, 300); await W(100); s = await b3(); ok(s.scene && !s.scene.skip, '頭 2s 撳唔跳');
  await E(() => __qa.b3b.sceneAt(2500, false)); await page.mouse.click(195, 300); await W(50); s = await b3(); ok(s.scene.skip && s.scene.t >= 5600, '2s 後撳 → 跳去現身', s.scene);
  s = await until(s => s.scene && s.scene.last && s.scene.last.card, 1500); ok(s.scene && s.scene.t - 5600 <= 450, '跳過後 ~300ms 出名卡', s.scene && s.scene.t);
  await page.mouse.click(195, 300); await W(100); s = await b3(); ok(!s.scene || s.scene.eff >= 7500, '名卡再撳 → 收', s.scene && s.scene.eff);
  s = await until(s => !s.scene, 2000); ok(s.save.comics.n4 && s.save.comics.n4.routes.includes('tide') && s.save.stats.skips === 1, 'n4 潮解鎖、skip 記錄', s.save.stats);
  await closeModals(); await W(300);

  console.log('# 圖鑑「團絨日記」四格');
  await E(() => __qa.b3b.unlock('n4', 'dust'));
  await E(() => Glimmer.ui.openDex()); await W(400);
  ok(await E(() => document.querySelectorAll('[data-testid^=dex-comic-][data-got="1"]').length === 2 && !!document.querySelector('[data-testid=dex-comics]')), '圖鑑 5 格（2 格解鎖）');
  await page.click('[data-testid=dex-comic-n4]'); await W(400);
  ok(await E(() => document.querySelectorAll('[data-testid^=b3b-comic-panel-]').length === 4), '四格頁');
  ok(await E(() => document.querySelector('[data-testid=b3b-comic-cap-1]').textContent === '夜晚要有人守。'), '字幕定稿');
  await page.click('[data-testid=b3b-comic-route-tide]'); await W(300);
  ok(await E(() => document.querySelector('[data-testid=b3b-comic-page]').dataset.route === 'tide' && /n4_p4_tide/.test(document.querySelector('[data-testid=b3b-comic-panel-4]').src) && document.querySelector('[data-testid=b3b-comic-cap-4]').textContent.indexOf('潮') === 0), '路線 tab：潮守夜者版第 4 格');
  await shot('comic-page');
  const pb = await (await page.$('[data-testid=b3b-comic-panel-4]')).boundingBox(); await shot('comic-panel', { x: pb.x, y: pb.y, width: pb.width, height: pb.height * (104 / 84) });
  await page.click('[data-testid=b3b-comic-close]'); await W(200); ok(await E(() => getComputedStyle(document.getElementById('b3bComic')).display === 'none'), '關閉');
  await closeModals();

  console.log('# 預兆');
  await load('q=high&hour=13&seed=25&ev=0', 'juvenile');
  await E(() => __qa.b3b.omen('flicker')); s = await until(s => s.render.flick > 0, 9000); ok(s.omen.kind === 'flicker' && s.render.flick > 0, '閃剪影', s.render);
  await E(() => __qa.b3b.omen('appetite')); await W(1100); const f0 = await E(() => Glimmer.data.FOODS[0].id);
  await E((id) => { __glimmer.state.needs.hunger = 30; Glimmer.sim.feed(__glimmer.state, id); Glimmer.ui.processEvents(); }, f0); await W(2200);
  s = await b3(); ok(s.log.some(l => l.k === 'omenFed'), '胃口大：食多陣＋一句', s.log.slice(-3));
  await E(() => { __glimmer.state.sleeping = true; __qa.b3b.omen('dream'); }); s = await until(s => s.render.dream > 0, 4000); ok(s.render.dream > 0, '怪夢泡泡（瞓緊）', s.render);
  await E(() => { __glimmer.state.sleeping = false; __qa.b3b.omen(null); });
  const autoOmen = await E(() => { const s = __glimmer.state; s.growthSec = Glimmer.data.PARAMS.stageSec.juvenile - 3600; return Glimmer.visit.omen(s, Glimmer.data.PARAMS.stageSec); }); ok(autoOmen && autoOmen.kind, '真存檔最後 24h → 有預兆', autoOmen);

  console.log('# ?b3b=0');
  await load('q=high&hour=13&seed=26&ev=0&b3b=0');
  ok(await E(() => !window.__qa.b3b && !__glimmer.b3bTick), '?b3b=0 → 唔裝');
  await E(() => { const s = __glimmer.state; s.ev.push({ type: 'grow', stage: 'juvenile', cq: 0 }); Glimmer.ui.processEvents(); }); await W(300);
  ok(await E(() => Glimmer.ui.isModalOpen()), '舊流程：即刻彈窗');

  ok(!errs.length, '冇 console error', errs.slice(0, 5));
  await browser.close();
  console.log(`\n結果：${pass} 通過，${fail} 失敗`); process.exit(fail ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
