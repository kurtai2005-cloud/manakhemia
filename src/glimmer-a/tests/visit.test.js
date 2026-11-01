/* 第 3 批 3b（docs-gdd/batch3-fun-spec.md §③④）：朋友訪客排程／送禮／友好度＋徽章／種子／小販、帶路 loop、進化大場面時間軸、四格解鎖、預兆。node tests/visit.test.js */
const D = require('../src/data.js'), SIM = require('../src/sim.js'), V = require('../src/visit.js'), X = require('../src/systems.js'), B = require('../src/systems2.js');
const J = require('../art/batch3b/batch3b.json'), VC = require('../art/batch3b/visit_pet_clips.json');
const fs = require('fs'), path = require('path');
let pass = 0, fail = 0; const ok = (c, m, x) => { if (c) { pass++; console.log('  ✓ ' + m); } else { fail++; console.log('  ✗ ' + m + (x !== undefined ? '  → ' + JSON.stringify(x) : '')); } };
const T0 = new Date(2026, 10, 1, 15, 0, 0).getTime(), H = 3600e3, DAY = 24 * H, C = V.CFG;
const fresh = (age) => { const s = SIM.newState(T0 - (age == null ? 5 : age) * DAY, 7); s.stage = 'juvenile'; return s; };
const seq = (a) => { let i = 0; return () => a[i++ % a.length]; };

console.log('⓪ 資料／圖');
{ ok(V.VISITORS.length === 3 && V.VISITORS.every(k => J.visitors[k]), '3 位訪客都有遊美圖');
  const miss = []; const chk = (f) => { if (!fs.existsSync(path.join(__dirname, '../art/batch3b', f))) miss.push(f); };
  for (const k of V.VISITORS) { const v = J.visitors[k]; ['idle', 'walk', 'happy'].forEach(c => chk(v.clips[c].file)); chk(v.portrait.file); chk(v.decor.file); ok(C.decor[k] === v.decor.id, k + ' 擺設 id 對得上', [C.decor[k], v.decor.id]); }
  for (const k in J.evolution.assets) if (k[0] !== '_') chk(J.evolution.assets[k].file);
  for (const k in J.evolution.cards.files) chk(J.evolution.cards.files[k].file);
  for (const n of V.NODES) for (const r of ['dust', 'tide', 'lumi']) for (const p of V.comicPanels(n, r, J.comics)) chk(p.file);
  ok(!miss.length, '所有引用圖檔存在', miss);
  ok(Object.keys(J.evolution.cards.formToCard).every(f => D.FORMS[f]), '名卡 formToCard 全部係現有 evo 形態');
  ok(Object.keys(D.FORMS).filter(f => /^evo_/.test(f) && f !== 'evo_egg').every(f => J.evolution.cards.formToCard[f] && J.evolution.cards.formName[f] && V.CARD_LINE[f]), '每個進化後 evo 形態（蛋除外）都有名卡＋名＋一句', Object.keys(D.FORMS).filter(f => /^evo_/.test(f) && f !== 'evo_egg' && !V.CARD_LINE[f]));
  ok(VC.clips.visit_lead_start && VC.clips.visit_lead_strut && VC.clips.visit_gift_cheer, '3a 反應 clip（帶路／送禮歡呼）');
  ok(J.comics.caption && V.NODES.every(n => (J.comics.caption[n] || []).length === 4), '四格字幕定稿（每話 4 句）');
  ok(D.PARAMS.b3b && D.PARAMS.b3b.enabled === true, 'PARAMS.b3b 開'); }

console.log('① 存檔 sanitize');
{ const s = fresh(); s.b3b = { day: 'x', vis: { snail_postman: { fr: 99, met: -3 }, ghost: {} }, seeds: 50, comics: { n9: {}, n1: { routes: ['dust', 'zzz'] } } };
  const o = V.st(s); ok(o.vis.snail_postman.fr === C.friendMax && o.vis.snail_postman.met === 0 && !o.vis.ghost, 'fr 夾 0–5、met ≥0、唔識嘅訪客刪', o.vis);
  ok(o.seeds <= 9 && typeof o.day === 'object', '種子 ≤9、day 修返做物件', o.seeds);
  ok(!o.comics.n9, '唔識嘅四格節點刪'); const j = JSON.parse(JSON.stringify(s)); ok(JSON.stringify(V.st(j)) === JSON.stringify(o), '存讀 round-trip 一樣'); }

console.log('② 排程：每日最多 1 位、第 3 日起、蝸牛先嚟、小販夜晚');
{ ok(V.canVisit(fresh(1), T0).reason === 'early', '第 1–2 日唔會有訪客'); const e = fresh(); e.stage = 'egg'; ok(V.canVisit(e, T0).reason === 'egg', '蛋唔會有訪客');
  const s = fresh(); ok(V.canVisit(s, T0).ok, '第 5 日可以');
  ok(V.pickVisitor(s, 13, () => 0.99) === 'snail_postman', '第一位一定係蝸牛郵差');
  V.startVisit(s, 'snail_postman', T0); ok(V.canVisit(s, T0 + H).reason === 'done', '同日已經有人嚟過 → 唔再嚟');
  ok(V.canVisit(s, T0 + DAY).ok, '第二日又得');
  const day = V.VISITORS.map(() => 0); for (let i = 0; i < 300; i++) { const r = V.pickVisitor(s, 13, Math.random); day[V.VISITORS.indexOf(r)]++; } ok(day[2] === 0, '日頭（13 點）小販唔出', day);
  let n = 0; for (let i = 0; i < 300; i++) if (V.pickVisitor(s, 22, Math.random) === 'firefly_vendor') n++; ok(n > 30, '夜晚小販會出', n);
  ok(V.vendorOpen(17) && V.vendorOpen(3) && !V.vendorOpen(7) && !V.vendorOpen(12), '小販 17–07');
  const s2 = fresh(); V.st(s2).vis.mushroom_granny.met = 5; V.st(s2).vis.snail_postman.met = 1; let g = 0; for (let i = 0; i < 400; i++) if (V.pickVisitor(s2, 13, Math.random) === 'mushroom_granny') g++; ok(g < 200, '少見嘅訪客較易嚟（met 加權）', g); }

console.log('③ 送禮／友好度／擺設＋徽章');
{ const s = fresh(); V.startVisit(s, 'snail_postman', T0);
  let r = V.gift(s, 'snail_postman', T0); ok(r.ok && r.fr === 1 && !r.reward, '送禮 → 友好度 +1');
  r = V.gift(s, 'snail_postman', T0 + 60e3); ok(!r.ok && r.reason === 'daily', '每位每日送 1 次');
  for (let d = 1; d <= 3; d++) V.gift(s, 'snail_postman', T0 + d * DAY);
  r = V.gift(s, 'snail_postman', T0 + 4 * DAY); ok(r.ok && r.fr === 5 && r.reward && r.reward.decor === 'deco_mailbox' && r.reward.badge === V.BADGE.snail_postman, '滿 5 → 郵筒仔＋徽章', r);
  ok(V.st(s).decor.deco_mailbox > 0, '擺設寫入存檔');
  r = V.gift(s, 'snail_postman', T0 + 5 * DAY); ok(r.ok && r.fr === 5 && !r.reward, '滿咗再送都得（唔再獎）');
  const bl = D.PARAMS.systems12b.badges.list.filter(b => b.when && b.when.friend); ok(bl.length === 3 && D.PARAMS.systems12b.badges.total === 34, '3 個朋友徽章（共 34）', bl.map(b => b.k));
  s.ev = []; B.badgeCheck(s, T0 + 5 * DAY); const got = B.badges(s); const k = V.BADGE.snail_postman;
  ok(got.list.find(b => b.k === k).got, '徽章檢查：蝸牛郵差好友徽章到手');
  const s3 = fresh(); s3.ev = []; B.badgeCheck(s3, T0); ok(!B.badges(s3).list.find(b => b.k === k).got, '未滿 5 冇徽章'); }

console.log('④ 禮物清單（花瓶花／重覆收集品／路邊小花）');
{ const s = fresh(); let it = V.giftItems(s, {}); ok(it.length === 1 && it[0].kind === 'free', '乜都冇 → 路邊小花（免費）');
  const sb = { garden: { vase: { daisy: 2 } }, walk: { got: { pebble: 3, leaf: 1 } } }; it = V.giftItems(s, sb);
  ok(it.some(i => i.kind === 'vase' && i.k === 'daisy' && i.n === 2) && it.some(i => i.kind === 'walk' && i.k === 'pebble' && i.n === 2) && !it.some(i => i.k === 'leaf') && !it.some(i => i.kind === 'free'), '花瓶花＋重覆（≥2）收集品；唔送最後一件', it);
  ok(V.takeItem(s, sb, { kind: 'vase', k: 'daisy' }) && sb.garden.vase.daisy === 1, '送花 → 花瓶 −1');
  ok(V.takeItem(s, sb, { kind: 'walk', k: 'pebble' }) && sb.walk.got.pebble === 2, '送收集品 → −1');
  ok(!V.takeItem(s, sb, { kind: 'walk', k: 'leaf' }) || sb.walk.got.leaf >= 1, '唔夠就唔扣'); }

console.log('⑤ 信／種子／小販');
{ const s = fresh(), seen = new Set(); for (let i = 0; i < V.LINES.letters.length; i++) seen.add(V.letter(s, T0 + i, Math.random)); ok(seen.size === V.LINES.letters.length, '信唔重覆（輪晒先重嚟）', seen.size);
  ok(V.st(s).letters.length > 0 && V.st(s).letters.length <= 30, '信寫入存檔（有上限）');
  ok(V.seedGift(s) === 1 && V.useSeed(s) && !V.useSeed(s), '婆婆種子：+1、用咗就冇');
  for (let i = 0; i < 20; i++) V.seedGift(s); ok(V.st(s).seeds === 9, '種子最多 9');
  const w = fresh(); X.st(w).wallet.total = 15; let r = V.buy(w, 'deco_mailbox', X.spend, T0); ok(r.ok && X.st(w).wallet.total === 3, '小販：郵筒仔 12 碎', X.st(w).wallet);
  r = V.buy(w, 'deco_mailbox', X.spend, T0); ok(!r.ok && r.reason === 'owned', '有咗唔再賣');
  r = V.buy(w, 'deco_firefly_jar', X.spend, T0); ok(!r.ok && r.reason === 'shards' && X.st(w).wallet.total === 3, '唔夠碎 → 唔扣');
  ok(C.shop.map(i => i.price).join() === '12,16,20', '價錢 10–20 碎範圍'); }

console.log('⑥ 帶路 loop');
{ const a = V.leadAt(0), z = V.leadAt(C.lead.lapMs - 1); ok(Math.abs(a.pet.x - 97) < 1 && Math.abs(z.pet.x - 97) < 2, '一圈由中間出發返中間', [a.pet, z.pet]);
  let maxD = 0; for (let t = 0; t < C.lead.lapMs; t += 50) { const L = V.leadAt(t); ok.silent = 1; maxD = Math.max(maxD, Math.abs(L.pet.y - 292)); if (L.pet.x < 30 || L.pet.x > 165) maxD = 99; } ok(maxD <= 12, '帶路喺花圃範圍（y ±12、x 30–165）', maxD);
  const mid = V.leadAt(3000), r = V.leadAt(3000, true); ok(Math.abs(r.pet.x - (194 - mid.pet.x)) < 1e-6 && r.pet.dir === -mid.pet.dir && r.pet.y === mid.pet.y, '右邊入＝鏡像 loop');
  const g = V.leadAt(4000); ok(Math.hypot(g.pet.x - g.vis.x, g.pet.y - g.vis.y) > 15, '訪客喺後面跟（followGap）'); }

console.log('⑦ 進化大場面時間軸');
{ const TL = V.TL; ok(TL.dur === 8000 && TL.reveal === 5600 && TL.cardIn === 6000, '8s；5.6s 現身；6s 名卡');
  const f = (t) => V.evoFrame(t, 97, 292, 30, 40);
  ok(f(0).dim < 0.1 && f(1500).dim >= 0.6, '暗場 0 → 0.7');
  ok(f(100).pet.show === 'old' && !f(100).pet.sil, '開頭係舊形態');
  ok(f(1500).motes.length > 0, '光點吸入');
  ok(f(2000).cocoon && f(2000).cocoon.id === 'evo_cocoon_form' && f(3000).cocoon.id === 'evo_cocoon_pulse', '光繭包住 → 呼吸');
  ok(f(4500).shards.length > 0 && f(4500).ring, '爆：碎片＋光環');
  const sw = new Set(); for (let t = 4400; t < 5600; t += 20) sw.add(f(t).pet.show); ok(sw.has('old') && sw.has('new'), '剪影新舊閃換');
  ok(f(5700).pet.show === 'new' && !f(5700).pet.sil && f(5700).flash > 0 && f(5700).confetti.length > 0, '現身：白閃＋彩紙');
  ok(!f(5900).card && f(6300).card && f(6300).card.sc > 0.5 && f(7600).card.al < 1 && !f(7800).card, '名卡 6.0 彈入、7.5 收');
  ok(f(6300).card.nameN === 0 && f(6500).card.nameN > 0 && f(6700).card.lineN > 0, '名字／一句逐字打出');
  ok(V.skipTo(1000) === null && V.skipTo(2500) === 5600 && V.skipTo(6200) === 7500 && V.skipTo(7600) === null, '2s 後先可以跳；跳去現身；名卡再撳收');
  ok(f(2100).skip && !f(1900).skip, '2s 後出「撳跳過」');
  ok(JSON.stringify(f(6500).confetti) === JSON.stringify(f(6500).confetti), '彩紙 deterministic（seeded）'); }

console.log('⑧ evo 事件 → 形態對／四格節點');
{ const P = (e) => V.evoPair(e);
  ok(P({ type: 'hatch' }).node === 'n1' && P({ type: 'hatch' }).to === 'evo_dot', '孵化 n1');
  ok(P({ type: 'grow', stage: 'sprout' }).node === 'n2' && P({ type: 'grow', stage: 'juvenile' }).node === 'n3', '成長 n2／n3');
  const e = P({ type: 'evolve', form: 'bright' }); ok(e.node === 'n4' && e.route === D.EVO_BRANCH.bright && D.FORMS[e.to], '進化 n4（bright→radiant）', e);
  const l = P({ type: 'elder', form: 'tide' }); ok(l.node === 'n5' && D.FORMS[l.from] && D.FORMS[l.to], '晚年 n5', l);
  ok(P({ type: 'fed' }) === null, '其他事件唔理');
  const s = fresh(); ok(V.unlockComic(s, 'n4', 'dust', T0) && !V.unlockComic(s, 'n4', 'dust', T0) && V.unlockComic(s, 'n4', 'tide', T0), '四格解鎖（新路線再加）');
  const pn = V.comicPanels('n4', 'tide', J.comics); ok(pn.length === 4 && /n4_p4_tide/.test(pn[3].file) && pn[3].cap.indexOf('潮') >= 0 && pn[3].cap.indexOf('{route}') < 0, '路線版第 4 格＋字幕代入', pn[3]);
  ok(V.comicPanels('n1', null, J.comics)[1].cap === '蛋：「我計劃好晒喇。」', '字幕用定稿 caption'); }

console.log('⑨ 預兆');
{ const s = fresh(); s.stage = 'juvenile'; const sec = D.PARAMS.stageSec.juvenile; s.growthSec = 0; ok(V.omen(s, D.PARAMS.stageSec) === null, '未到最後窗口冇預兆');
  s.growthSec = sec - 3600; const o = V.omen(s, D.PARAMS.stageSec); ok(o && V.OMENS.includes(o.kind), '最後 24h → 一款預兆', o);
  ok(JSON.stringify(V.omen(s, D.PARAMS.stageSec)) === JSON.stringify(o), '同一隻同一階段固定一款');
  s.stage = 'egg'; ok(V.omen(s, D.PARAMS.stageSec) === null, '蛋冇預兆'); s.stage = 'elder'; ok(V.omen(s, D.PARAMS.stageSec) === null, '晚年冇預兆');
  const kinds = new Set(); for (let i = 0; i < 60; i++) { const t = fresh(); t.seed = i; t.stage = 'sprout'; t.growthSec = D.PARAMS.stageSec.sprout - 60; kinds.add(V.omen(t, D.PARAMS.stageSec).kind); } ok(kinds.size === 3, '三款都會出', [...kinds]);
  ok(V.flickerOn(0) && !V.flickerOn(85) && V.flickerOn(185) && !V.flickerOn(400), '閃剪影 2 下 80ms');
  ok(V.dreamAt(0).f === 0 && V.dreamAt(300).f === 1 && V.dreamAt(800).icon && V.dreamAt(2700).puff != null && V.dreamAt(4000) === null, '怪夢泡泡：0→1→2＋夢圖→puff'); }

console.log(`\n結果：${pass} 通過，${fail} 失敗`); process.exit(fail ? 1 : 0);
