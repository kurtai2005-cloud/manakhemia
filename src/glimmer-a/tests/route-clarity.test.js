/* §7 路線清晰化 Node 無依賴測試：node tests/route-clarity.test.js
   覆蓋：① config（顏色／時間／預告動作）② 領先路線（螢絨隱藏）③ 跳跳期燈泡路線色（慢慢轉）④ 判定前 12h 預告（一次）⑤ 圖鑑（解鎖／剪影／一句提示）
   全部數值讀 PARAMS.evo6.route／branch；改 config 唔使改測試。 */
const fs = require('fs'), path = require('path');
const S = require('../src/sim.js');
const D = require('../src/data.js');
const BEH = require('../src/behavior.js');
const P = D.PARAMS, EV6 = P.evo6, C = EV6.branch, R = EV6.route;
let pass = 0, fail = 0;
function ok(cond, name, info) { if (cond) { pass++; console.log('  ✓ ' + name); } else { fail++; console.log('  ✗ ' + name + (info !== undefined ? '  → ' + info : '')); } }
const inW = (w, h) => w.from <= w.to ? h >= w.from && h < w.to : h >= w.from || h < w.to;
const DAY = [12, 13, 14, 15, 16, 10, 11, 17, 18, 19, 20].find(h => !C.windows.some(w => inW(w, h)));
let HOUR = DAY; S.setHourFn(() => HOUR); S.setRainFn(() => false);
const JUV = P.stageSec.juvenile, OPEN = ['tide', 'shroom', 'crystal', 'moon', 'ember', 'bright', 'soft', 'dust'];
function juv(counts, cq, prog) {
  const s = S.newState(1e12, 7); s.stage = 'sprout'; Object.assign(s.needs, { hunger: 90, mood: 90, clean: 100, energy: 90 });
  for (const k in counts) for (let i = 0; i < counts[k]; i++) S.noteCare(s, null, k, k === 'feed' ? true : undefined);   // v8：feed＝落雨餵（菇傘 +1；晴天餵本身 0）
  if (counts.poop) Object.assign(s.evo.b5.sprout, { loginPoop: counts.poop, quickLogin: counts.poop });   // v7：poop＝每次上線即清（晶角＝比率×k×總數）
  s.evo.cl = { sprout: { sum: 100 * 1e6, sec: 1e6 } }; s.stage = 'juvenile'; s.cq = cq; s.growthSec = JUV * (prog == null ? 0.5 : prog); return s;
}
const hiCQ = Math.max(C.brightCQ, C.b5CQ) + 10;
const hx = (h) => [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16));

console.log('# ① config（PARAMS.evo6.route）');
ok(OPEN.every(f => /^#[0-9A-Fa-f]{6}$/.test(R.colors[f])) && !('lumi' in R.colors), '8 條可見路線各有一個色；螢絨冇色（唔顯示）', JSON.stringify(R.colors));
ok(new Set(OPEN.map(f => R.colors[f].toLowerCase())).size === OPEN.length, '每條路一個唔同色');
ok(R.foreshadowLeadSec === 12 * 3600 && R.foreshadowLeadSec < JUV, '預告＝判定前 12h（config）', R.foreshadowLeadSec);
ok(R.bulbStage === 'juvenile' && R.bulbMaxMix > 0 && R.bulbMaxMix <= 1 && R.bulbRampProgress >= 0 && R.bulbRampProgress <= 1 && R.bulbFadeSec > 0 && R.leadRecalcSec > 0, '燈泡：跳跳期、mix／漸變時間喺 config');
{ const valid = (a) => a && ((a.beh && (BEH.VARIANTS.includes(a.beh) || BEH.MICRO_FORCE.includes(a.beh) || (a.beh.startsWith('now_') && BEH.NOW.includes(a.beh.slice(4))))) || (a.act && a.dur > 0));
  ok(OPEN.every(f => valid(R.foreshadow[f])) && !R.foreshadow.lumi, '每條可見路線一個預告動作（只用現有 clip／動作；螢絨冇）', JSON.stringify(R.foreshadow));
  ok(R.foreshadow.moon.beh === 'yawn' && R.foreshadow.ember.act === 'celebrate', '月眠＝打喊路（yawn）、火苗＝原地跳（celebrate）— 文件例子'); }
ok(D.BRANCHES.every(f => typeof D.ROUTE_HINT[f] === 'string' && D.ROUTE_HINT[f].length) && D.ROUTE_HINT.lumi === '？？？', '圖鑑一句提示：9 條（螢絨＝？？？）');
{ const doc = fs.readFileSync(path.join(__dirname, '../../../docs-gdd/pet-template-v1.md'), 'utf8'), sec = doc.slice(doc.indexOf('§7 路線清晰化'));
  ok(D.BRANCHES.filter(f => f !== 'lumi').every(f => sec.includes('「' + D.ROUTE_HINT[f] + '」')), '提示文字同文件 §7 路線清晰化原文一樣'); }
ok(/^#[0-9A-Fa-f]{6}$/.test(R.silhouette), '剪影色喺 config');
{ const fs = require('fs'), path = require('path'); ok(R.silArt && D.BRANCHES.every(id => fs.existsSync(path.join(__dirname, '../art', R.silArt + (id === 'bright' ? 'radiant' : id) + '_48.png'))), '遊美 batch G 剪影圖 ×9 喺 art/（bright→radiant）'); }

console.log('# ② 領先路線（routeLead）＝ 判定邏輯但螢絨隱藏');
{
  const cases = [[{ feed: 10, play: 2 }, hiCQ, 'shroom'], [{ play: 10, feed: 1 }, hiCQ, 'ember'], [{ rinse: 10, play: 1 }, hiCQ, 'tide'], [{ poop: 10, play: 1 }, hiCQ, 'crystal'],
    [{ feed: 3, play: 3, rinse: 3 }, C.brightCQ, 'bright'], [{ feed: 3, play: 3, rinse: 3 }, C.softCQ, C.softCQ >= C.brightCQ ? 'bright' : 'soft'], [{ feed: 3, play: 3, rinse: 3 }, C.softCQ - 1, 'dust']];
  for (const [c, cq, f] of cases) { const s = juv(c, cq); ok(S.routeLead(s).form === f && S.decideBranch(s).form === f, `${JSON.stringify(c)} CQ ${cq} → 領先 ${D.FORM_NAME[f]}（同判定一致）`, S.routeLead(s).form); }
  { HOUR = C.windows.find(w => w.id === 'moon').from; const s = juv({ feed: 6 }, hiCQ); HOUR = DAY; ok(S.routeLead(s).form === 'moon', '夜晚照顧 → 領先月眠'); }
  { const s = juv({ feed: 10, play: 2 }, Math.max(EV6.branch.lumi.minCQ, hiCQ)); s.evo.evIn.juvenile = { [EV6.lumiEvent]: 1 }; s.evo.care.juvenile = { all: 10, night: 10 };
    S.setBranchRoll(() => 0); const dl = S.decideBranch(s).form; S.setBranchRoll(null);
    ok(dl === 'lumi' && S.routeLead(s).form === 'shroom', '符合螢絨 → 判定係螢絨，但領先路線唔顯示螢絨（顯示菇傘）', S.routeLead(s).form); }
  { const s = juv({ feed: 10 }, hiCQ); s.evo.force = 'ember'; ok(S.routeLead(s).form === 'shroom', 'DEV 強制唔影響領先路線顯示'); }
}

console.log('# ③ 跳跳期燈泡：慢慢轉做領先路線色');
{
  const s0 = juv({ feed: 10 }, hiCQ, 0), b0 = S.routeBulb(s0); ok(b0 && b0.form === 'shroom' && b0.color === R.colors.shroom && b0.mix === 0, '跳跳期頭：路線色 mix 0（未轉）', JSON.stringify(b0));
  const prog = [0, 0.1, 0.25, 0.4, 0.6, 0.9].map(p => S.routeBulb(juv({ feed: 10 }, hiCQ, p)).mix);
  ok(prog.every((m, i) => i === 0 || m >= prog[i - 1]) && prog[prog.length - 1] === R.bulbMaxMix, '隨跳跳期進度慢慢升到 bulbMaxMix', prog.join());
  ok(Math.abs(S.routeBulb(juv({ feed: 10 }, hiCQ, R.bulbRampProgress / 2)).mix - R.bulbMaxMix / 2) < 1e-3, `進度 ${R.bulbRampProgress / 2} → 一半`);
  for (const st of ['newborn', 'sprout', 'adult', 'elder']) { const s = juv({ feed: 10 }, hiCQ); s.stage = st; ok(S.routeBulb(s) === null, `${D.STAGE_NAME[st]} → 唔轉色`); }
  { const s = juv({ feed: 10, play: 2 }, hiCQ); s.evo.evIn.juvenile = { [EV6.lumiEvent]: 1 }; s.evo.care.juvenile = { all: 10, night: 10 }; ok(S.routeBulb(s).form !== 'lumi' && S.routeBulb(s).color !== undefined, '螢絨唔顯示（燈泡用下一條路色）'); }
  const rsrc = fs.readFileSync(path.join(__dirname, '../src/render.js'), 'utf8');
  ok(/routeBulbOf\(s, t\)/.test(rsrc) && /RC\.bulbFadeSec/.test(rsrc) && /RC\.leadRecalcSec/.test(rsrc) && /fst\.bulb = \{[^}]*route:/.test(rsrc), 'render：燈泡 tint 混入路線色（bulbFadeSec 漸變、leadRecalcSec 重算、faceStat 記 route）');
}

console.log('# ④ 判定前 12h 預告（每隻一次）');
{
  const run = (counts, cq) => { const s = juv(counts, cq, 0); s.growthSec = JUV - R.foreshadowLeadSec - 30; const evs = [];
    for (let i = 0; i < 2; i++) { S.step(s, 10, {}); evs.push(...s.ev.splice(0)); } return { s, evs }; };
  let { s, evs } = run({ feed: 10 }, hiCQ); ok(!evs.some(e => e.type === 'foreshadow') && !s.evo.fore, '判定前 >12h：未預告');
  for (let i = 0; i < 3; i++) { S.step(s, 10, {}); evs.push(...s.ev.splice(0)); }
  let fs1 = evs.filter(e => e.type === 'foreshadow'); ok(fs1.length === 1 && fs1[0].form === 'shroom' && fs1[0].act === R.foreshadow.shroom && s.evo.fore.form === 'shroom', '跨過判定前 12h → 預告一次（領先路線＋config 動作）', JSON.stringify(fs1));
  ok(Math.abs(s.evo.fore.at - (JUV - R.foreshadowLeadSec)) <= 20, '預告時間 ≈ 判定前 12h', s.evo.fore.at);
  for (let i = 0; i < 20; i++) { S.step(s, 600, {}); evs.push(...s.ev.splice(0)); }
  ok(evs.filter(e => e.type === 'foreshadow').length === 1, '之後唔再預告');
  ok(S.deserialize(S.serialize(s), 1e12).evo.fore.form === 'shroom', '預告紀錄跟存檔（重開唔會再做）');
  for (const [c, f] of [[{ play: 10 }, 'ember'], [{ rinse: 10 }, 'tide'], [{ feed: 3, play: 3, rinse: 3 }, 'bright']]) {
    const r = run(c, hiCQ); for (let i = 0; i < 3; i++) { S.step(r.s, 10, {}); r.evs.push(...r.s.ev.splice(0)); }
    const e = r.evs.find(x => x.type === 'foreshadow'); ok(e && e.form === f && e.act === R.foreshadow[f], `${D.FORM_NAME[f]} 路線 → 預告 ${JSON.stringify(R.foreshadow[f])}`, e && e.form);
  }
  { const s2 = juv({ feed: 10, play: 2 }, Math.max(EV6.branch.lumi.minCQ, hiCQ), 0); s2.evo.evIn.juvenile = { [EV6.lumiEvent]: 1 }; s2.evo.care.juvenile = { all: 10, night: 10 }; s2.growthSec = JUV - R.foreshadowLeadSec + 1; S.step(s2, 1, {});
    const e = s2.ev.find(x => x.type === 'foreshadow'); ok(e && e.form !== 'lumi', '螢絨隱藏：預告做下一條路，唔洩露', e && e.form); }
  { const s3 = juv({ feed: 10 }, hiCQ, 0); s3.stage = 'sprout'; s3.growthSec = P.stageSec.sprout - 1; S.step(s3, 5, {}); ok(!s3.ev.some(e => e.type === 'foreshadow'), '芽崽 → 跳跳期一刻唔預告'); }
  { const s4 = juv({ feed: 10 }, hiCQ, 0); s4.growthSec = JUV - R.foreshadowLeadSec - 1; S.step(s4, 5, {}); s4.ev.length = 0; s4.growthSec = JUV - 1; S.step(s4, 5, {});
    ok(s4.stage === 'adult' && s4.form === 'shroom', '預告後照常判定（菇傘）', s4.form); }
  const usrc = fs.readFileSync(path.join(__dirname, '../src/ui.js'), 'utf8');
  ok(/e\.type === 'foreshadow'/.test(usrc) && /UI\.pendingFore && !s\.sleeping && !modalOpen/.test(usrc) && /BEH\.force\(G\.beh, a\.beh/.test(usrc) && /rd\.act\(a\.act/.test(usrc), 'ui：預告等醒咗／冇彈窗先做（behavior.force 或 renderer.act）');
}

console.log('# ⑤ 圖鑑');
{
  const s = S.newState(1e12, 3); let L = S.dexList(s);
  ok(L.length === 9 && L.map(d => d.id).join() === D.BRANCHES.join() && L.every(d => !d.unlocked && d.name === '？？？' && d.hint === D.ROUTE_HINT[d.id]), '新存檔：9 格全部未解鎖（剪影＋一句提示）');
  const t = juv({ feed: 10 }, hiCQ, 0); t.growthSec = JUV - 1; S.step(t, 5, {}); L = S.dexList(t);
  ok(t.form === 'shroom' && L.find(d => d.id === 'shroom').unlocked && L.find(d => d.id === 'shroom').name === '菇傘' && L.filter(d => d.unlocked).length === 1, '成為守夜者 → 解鎖嗰格（顯示名）');
  t.stage = 'elder'; t.fadeReady = true; S.fade(t, 1e12); ok(S.dexList(t).find(d => d.id === 'shroom').unlocked && t.stage === 'egg', '化光重養：圖鑑保留');
  const u = S.deserialize(S.serialize(t), 1e12); ok(u.dex.join() === 'shroom', '存檔來回保留圖鑑');
  const old = S.newState(1e12, 4); delete old.dex; old.memorial = [{ gen: 1, form: 'moon' }]; old.stage = 'adult'; old.form = 'ember';
  const o2 = S.deserialize(S.serialize(old), 1e12); ok(o2.dex.sort().join() === 'ember,moon', '舊存檔：由紀念＋而家形態補返圖鑑', o2.dex.join());
  ok(S.unlockDex(o2, 'nope') === false && S.unlockDex(o2, 'moon') === false && S.unlockDex(o2, 'lumi') === true, 'unlockDex：亂嘢／重複唔加');
  const usrc = fs.readFileSync(path.join(__dirname, '../src/ui.js'), 'utf8'), html = fs.readFileSync(path.join(__dirname, '../index.html'), 'utf8');
  ok(/rd\.atlasSrc\(A\.atlas, 'idle', 0\)/.test(usrc) && /source-in/.test(usrc) && /route\.silhouette/.test(usrc), 'ui：剪影由現有守夜者 idle 圖生（source-in 填剪影色）');
  ok(/id="dex"[^>]*data-testid="dex"/.test(html) && /\$\('#dex'\)/.test(usrc), 'HUD 有圖鑑掣（#dex）');
  ok(D.BRANCHES.every(f => fs.existsSync(path.join(__dirname, '../art/evo6/atlas_' + D.evoForm('adult', f) + '.png'))), '9 格都有現有守夜者圖（剪影來源）');
}

console.log(`結果：${pass} 通過，${fail} 失敗`);
process.exit(fail ? 1 : 0);
