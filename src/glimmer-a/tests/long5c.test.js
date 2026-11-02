/* 第 5 批 5c（docs-gdd/series2-4a4b-spec.md v1.1 §5c＋5a–5c 定案）：承傳 s.fam.c5 — 美術對數／揀上一代（成年、主養、遠足中都得；冇成年跳過）／
   花紋（系／路線 → 8 款）＋色（tint_pair 對比）／家傳招式（團絨＝示範最多，打和最近，冇示範隨機；細佬＝自己系 → 學最多 → 自己系）／runtime 示範記錄／
   未揀就孵 → 自動揀／家族 Lv3 細佬頭 2 階快 20%（團絨蛋唔計）／屋仔家具圖鑑等級工作照留／§7 分支比例唔變（±0.3pt，包括第二代團絨蛋）。 */
const D = require('../src/data.js'), SIM = require('../src/sim.js'), S2 = require('../src/series2.js'), HS = require('../src/house.js'), F = require('../src/long5a.js'), B = require('../src/long5b.js'), C = require('../src/long5c.js');
const fs = require('fs'), path = require('path'), ART = path.join(__dirname, '../art/series2_long');
const J = (f) => JSON.parse(fs.readFileSync(path.join(ART, f), 'utf8')), L = J('5c/long_5c.json'), LAY = J('5c/ui/layout.json');
let pass = 0, fail = 0; const ok = (c, m, x) => { if (c) { pass++; console.log('  ✓ ' + m); } else { fail++; console.log('  ✗ ' + m + (x !== undefined ? '  → ' + JSON.stringify(x) : '')); } };
const at = (d, h, m) => new Date(2026, 10, 1 + d, h, m || 0, 0).getTime();
const NOW = at(0, 12), env = { rebirth: SIM.rebirth, trFk: 'evo_still_tide' }, ctx = { art: L, trFk: 'evo_still_tide', kidFk: 'A3' };
function fam(o) { const s = SIM.newState(at(-30, 12), 7); s.stage = 'elder'; s.form = 'tide'; s.dex = ['tide']; S2.noteElder(s, at(-25, 12)); S2.deliver(s, at(-24, 12)); const p = S2.st(s);
  p.dreams = [{ day: p.d0, line: 'A' }, { day: p.d0 + 1, line: 'B' }, { day: p.d0 + 2, line: null }]; S2.hatch(s, at(-20, 12)); Object.assign(p, { intim: 90, rel: 'family', line: 'A' }, o || {}); HS.ensure(s, at(-5, 12)); return s; }
const routeSnap = (s) => JSON.stringify({ evo: s.evo, evs: s.evs, form: s.form, cq: s.cq, seed: s.seed, gen: s.gen, stage: s.stage, growthSec: s.growthSec });
const adultKid = (s) => { S2.st(s).hatchDay = S2.dayNum(NOW) - 20; };

console.log('⓪ 美術／資料對數');
{ ok(JSON.stringify(C.PATTERNS.map(p => p.id + p.zh)) === JSON.stringify(L.patterns.map(p => p.id + p.zh)), '8 款花紋 id／名對 long_5c.json');
  ok(JSON.stringify(C.BY_SERIES) === JSON.stringify(L.patternBySeries) && JSON.stringify(C.BY_ROUTE) === JSON.stringify(L.patternByRoute), '系 → 花紋、路線 → 花紋對數');
  ok(Object.keys(L.tricks).every(k => C.TRICK[k] === L.tricks[k].title) && Object.keys(C.TRICK).length === 8, '8 個家傳招式名對數');
  ok(L.rules.fastGrow.fromFamilyLv === C.FAST.fromLv && L.rules.fastGrow.stages === C.FAST.stages && L.rules.fastGrow.speedup === C.FAST.speedup && L.rules.fastGrow.excludeEgg === C.FAST.excludeEgg && C.FAST.factor === 1 - C.FAST.speedup, '加速：Lv3、頭 2 階、20%、團絨蛋唔計');
  ok(F.UNLOCKS[3].some(u => u.id === 'inherit_fast'), '家族 Lv3 解鎖 inherit_fast');
  ok(Object.keys(L.parents).length === 25 && Object.keys(L.parents).every(k => { const P = L.parents[k]; return C.patternOf(/^evo_/.test(k) ? { kind: 'tr', fk: k } : { kind: 'kid', fk: k, line: k[0] }, null) === P.pattern; }), '25 隻成年（團絨靜光 9＋細佬 S5/S6 16）花紋＝系／路線規則', null);
  const miss = []; const chk = (f) => { if (!fs.existsSync(path.join(ART, '5c', f))) miss.push(f); };
  for (const k in L.overlay.forms) chk(L.overlay.forms[k].png); for (const k in L.overlay.eggs) chk(L.overlay.eggs[k].png);
  const ui = fs.readdirSync(path.join(ART, '5c/ui')); ok(!miss.length && Object.keys(L.overlay.forms).length === 59 && ui.length >= 25, '59 形態＋3 蛋花紋 PNG、UI 零件喺 repo', miss.slice(0, 3));
  ok(Object.values(L.overlay.forms).every(f => C.PATTERNS.every(p => f.rows.some(r => r.pattern === p.id))), '每形態 8 款花紋都有 row');
  ok(LAY.parentPick && LAY.inheritResult, 'layout：揀上一代＋遺傳結果');
}
console.log('① 新蛋 → 揀上一代（細佬蛋）');
{ const s = fam(); adultKid(s); F.scan(s, NOW, { kidFk: 'A3' }); const p = S2.st(s);
  for (let i = 0; i < 3; i++) S2.st(s).lessons.push({ line: i < 2 ? 'C' : 'A', day: 0, at: at(-19, 9 + i), stage: 'S1' });
  F.st(s).offer = { due: S2.dayNum(NOW), at: 1 }; const hb = JSON.stringify(HS.st(s)), lv0 = F.st(s).lv, xp0 = F.st(s).xp;
  const r = F.pick(s, 'kid', NOW, env); ok(r.ok && S2.st(s).phase === 'egg', '5a 揀細佬蛋');
  const kid = S2.st(s).fid, ev = C.scan(s, NOW, ctx); ok(ev.some(e => e.k === 'pend' && e.child === kid), '新蛋排隊揀上一代', ev);
  const cs = C.candidates(s, NOW, ctx, kid); ok(cs.length === 2 && cs[0].id === 'tr1' && cs[0].main && cs[1].kind === 'kid', '候選：主養團絨（第一）＋搬咗入屋嘅成年細佬', cs.map(c => c.id));
  ok(cs[0].pattern === 'wave' && cs[1].pattern === 'wave', '花紋：潮汐團絨＝波紋、A 系細佬＝波紋', cs.map(c => c.pattern));
  ok(cs[1].trick === 'A' && cs[1].tsrc === 'own', '細佬上一代：有學過自己系（A）→ 招式 A（json）', cs[1]);
  ok(cs[0].trick === 'C' && cs[0].tsrc === 'demo', '團絨上一代：示範最多（C ×2）→ C', [cs[0].trick, cs[0].tsrc, C.demoOf(s, 'tr1')]);
  const c = C.choose(s, kid, cs[1].id, NOW + 10, ctx); ok(c.ok && c.inh.parent === cs[1].id && c.inh.pattern === 'wave' && c.inh.trick === 'A' && !C.pendOf(s).length, '揀細佬做上一代');
  const c2 = C.choose(s, kid, 'tr1', NOW + 20, ctx); ok(c2.ok && C.inhOf(s, kid).parent === 'tr1', '孵之前可以改');
  ok(!C.choose(s, kid, 'nobody', NOW, ctx).ok, '唔係候選：揀唔到');
  ok(JSON.stringify(HS.st(s)) === hb && F.st(s).lv === lv0 && F.st(s).xp === xp0, '屋仔／家具／家族等級照留');
}
console.log('② 未揀就孵 → 自動揀；冇成年 → 跳過');
{ const s = fam(); adultKid(s); F.scan(s, NOW, { kidFk: 'A3' }); F.st(s).offer = { due: S2.dayNum(NOW), at: 1 }; F.pick(s, 'kid', NOW, env); const kid = S2.st(s).fid;
  C.scan(s, NOW, ctx); S2.hatch(s, NOW + 1000); const ev = C.scan(s, NOW + 2000, ctx);
  ok(ev.some(e => e.k === 'auto' && e.parent === 'tr1') && C.inhOf(s, kid).auto, '孵咗未揀 → 自動揀第一隻（主養）', ev);
  ok(ev.some(e => e.k === 'hatched' && e.child === kid), '孵化事件（彈遺傳結果）');
  ok(!C.scan(s, NOW + 3000, ctx).some(e => e.k === 'hatched'), '只出一次');
  const s0 = SIM.newState(NOW, 1); s0.stage = 'egg'; const e0 = C.scan(s0, NOW, ctx); ok(e0.some(e => e.k === 'skip') && !C.pendOf(s0).length, '第一隻光卵（屋企冇成年）→ 跳過（冇遺傳）', e0);
  const s1 = SIM.newState(NOW, 1); s1.stage = 'elder'; S2.noteElder(s1, NOW); S2.deliver(s1, NOW); const e1 = C.scan(s1, NOW, ctx), k1 = S2.st(s1).fid;
  ok(e1.some(e => e.k === 'pend' && e.child === k1) && C.candidates(s1, NOW, ctx, k1).map(c => c.id).join() === 'tr1', '4a 第一隻細佬蛋：上一代＝主養團絨（得 1 隻）');
  ok(C.candidates(s1, NOW, ctx, k1)[0].tsrc === 'random' && S2.LINES.includes(C.candidates(s1, NOW, ctx, k1)[0].trick), '從未示範過 → 隨機 1 課');
  const t1 = C.candidates(s1, NOW, ctx, k1)[0].trick; ok(C.candidates(s1, NOW + 9999, ctx, k1)[0].trick === t1, '隨機有種子（穩定）');
}
console.log('③ 團絨示範記錄（runtime）：最多 → 打和最近 → 隨機');
{ const s = fam(); const p = S2.st(s); p.lessons.length = 0; p.hatchDay = S2.dayNum(at(0, 0)); p.hatchAt = at(0, 1); p.stageSeen = 'S1';
  const L1 = (line, t) => { const r = S2.lesson(s, line, t); return r.ok; };
  ok(L1('B', at(0, 9)) && L1('D', at(0, 10)), '教 2 堂（B、D）'); C.syncDemo(s);
  const d = C.demoOf(s, 'tr1'); ok(d.B && d.B.n === 1 && d.D && d.D.n === 1, '每堂記落 demo[tr1]', d);
  ok(C.trickOf(s, { kind: 'tr', id: 'tr1' }).L === 'D', '打和 → 揀最近（D）');
  L1('B', at(1, 9)); C.syncDemo(s); ok(C.trickOf(s, { kind: 'tr', id: 'tr1' }).L === 'B', 'B ×2 → B');
  C.syncDemo(s); ok(C.demoOf(s, 'tr1').B.n === 2, '重複 sync 唔重計');
  const r = { id: 'kidR', kind: 'kid', fk: 'C3', line: 'C', name: 'R', bro: 'tr1', room: 'room1', at: 1, snap: { lessons: [{ line: 'H', at: 5 }, { line: 'H', at: 6 }, { line: 'H', at: 7 }] } }; F.st(s).res.push(r);
  C.syncDemo(s); ok(C.demoOf(s, 'tr1').H.n === 3 && C.trickOf(s, { kind: 'tr', id: 'tr1' }).L === 'H', '住客細佬以前學嘅（大佬 tr1）都計', C.demoOf(s, 'tr1'));
  ok(C.trickOf(s, { kind: 'kid', id: 'kidR', fk: 'C3', line: 'C', lessons: r.snap.lessons }, L).L === 'H' && C.trickOf(s, { kind: 'kid', id: 'kidR', fk: 'C3', line: 'C', lessons: r.snap.lessons }, L).src === 'most', '細佬冇學過自己系 → 學得最多（H）');
  ok(C.trickOf(s, { kind: 'kid', id: 'x', fk: 'G3', line: 'G', lessons: [] }, L).L === 'G', '細佬乜都冇學過 → 自己系（G）');
}
console.log('④ 團絨蛋（第二代）＋遠足中都揀得');
{ const s = fam(); adultKid(s); F.scan(s, NOW, { kidFk: 'A3' }); F.st(s).offer = { due: S2.dayNum(NOW), at: 1 };
  const r = F.pick(s, 'tr', NOW, env); ok(r.ok && s.stage === 'egg' && s.gen === 2, '5a 揀團絨蛋（第 2 代）');
  B.st(s).away.tr1 = { at: NOW, dk: 0, sv: F.SOUV[0].id };
  const ev = C.scan(s, NOW, ctx); ok(ev.some(e => e.k === 'pend' && e.child === 'tr2'), '團絨蛋排隊');
  const cs = C.candidates(s, NOW, ctx, 'tr2'); ok(cs.some(c => c.id === 'tr1' && c.away) && cs.some(c => c.kind === 'kid'), '候選：舊主養（遠足中）＋花園成年細佬', cs.map(c => c.id + (c.away ? '*' : '')));
  ok(C.fastState(s, 'tr') === 'tr', '團絨蛋：加速唔計');
  const c = C.choose(s, 'tr2', 'tr1', NOW, ctx); ok(c.ok && c.inh.kind === 'tr' && c.inh.pattern === 'wave', '揀咗（遠足中嗰隻）');
  s.stage = 'newborn'; const e2 = C.scan(s, NOW + 1, ctx); ok(e2.some(e => e.k === 'hatched' && e.child === 'tr2' && !e.fast), '團絨孵化：冇加速');
}
console.log('⑤ 家族 Lv3：細佬頭 2 階快 20%');
{ const mk = (lv) => { const s = fam(); adultKid(s); F.scan(s, NOW, { kidFk: 'A3' }); const o = F.st(s); const need = F.THRESH[lv - 1]; if (o.xp < need) F.addXp(s, 'dev', need - o.xp, NOW); o.offer = { due: S2.dayNum(NOW), at: 1 }; F.pick(s, 'kid', NOW, env); C.scan(s, NOW, ctx); return s; };
  const s2 = mk(2), s3 = mk(3); ok(C.fastState(s2, 'kid') === 'locked' && C.fastState(s3, 'kid') === 'on', 'Lv2 鎖、Lv3 開');
  const H0 = at(1, 8); S2.hatch(s2, H0); S2.hatch(s3, H0); C.scan(s2, H0 + 1, ctx); C.scan(s3, H0 + 1, ctx);
  ok(!S2.st(s2).fast && S2.st(s3).fast === 0.8 && C.inhOf(s3, S2.st(s3).fid).fast, '孵化鎖定：Lv3 pet2.fast＝0.8');
  const first = (s, k) => { for (let t = H0; t < H0 + 30 * 864e5; t += 600e3) if (S2.stageOf(s, t) === k) return t; return null; };
  const n1 = first(s2, 'S2') - H0, f1 = first(s3, 'S2') - H0, n3 = first(s2, 'S3') - H0, f3 = first(s3, 'S3') - H0;
  ok(Math.abs(f1 / n1 - 0.8) < 0.02, 'S1 時長 ×0.8', [n1 / 36e5, f1 / 36e5]);
  ok(Math.abs((f3 - f1) / (n3 - n1) - 0.8) < 0.01, 'S2 時長 ×0.8', [(n3 - n1) / 36e5, (f3 - f1) / 36e5]);
  const n4 = first(s2, 'S4') - H0, f4 = first(s3, 'S4') - H0; ok(Math.abs((f4 - f3) - (n4 - n3)) <= 600e3, 'S3 之後照舊長度（只係提早）', [(n4 - n3) / 36e5, (f4 - f3) / 36e5]);
  let mono = true, last = 0; for (let t = H0; t < H0 + 20 * 864e5; t += 900e3) { const i = S2.stageIdx(S2.stageOf(s3, t)); if (i < last) mono = false; last = i; } ok(mono && S2.stageOf(s3, H0 + 20 * 864e5) === 'S6', '階段只會向前（S1→S6）');
  const s4 = fam(); S2.st(s4).fast = 0.8; S2.st(s4).hatchDay = S2.dayNum(NOW) - 1; ok(S2.stageOf(s4, NOW) === 'S2', 'DEV 撥 hatchDay 照計得（S2）');
  const sv = JSON.parse(JSON.stringify(S2.st(s3))); sv.fast = 7; const s5 = fam(); s5.pet2 = sv; S2.st(s5); ok(!('fast' in S2.st(s5)), 'sanitize：fast 唔合理 → 刪');
}
console.log('⑥ §7 分支比例唔變（±0.3pt；包括第二代團絨蛋）');
{ const N = 240, cnt = (o, k) => { o[k] = (o[k] || 0) + 1; }, A = {}, Bx = {}; let same = 0, drift = 0;
  let HOUR = 12; SIM.setHourFn && SIM.setHourFn(() => HOUR);
  const run = (s, seed) => { let r = seed >>> 0; const rnd = () => ((r = (Math.imul(r, 1664525) + 1013904223) >>> 0) / 4294967296);
    const w = [rnd(), rnd(), rnd(), rnd()], care = 0.2 + rnd() * 0.8, low = rnd() * 70, h0 = (rnd() * 24) | 0;
    for (let h = 0; h < 120 && s.stage !== 'adult' && s.stage !== 'elder'; h++) { HOUR = (h0 + h * (1 + (seed % 5))) % 24; for (const k of D.NEED_KEYS) s.needs[k] = low + rnd() * (100 - low);
      try { if (s.stage !== 'egg' && rnd() < care) { const a = rnd() * (w[0] + w[1] + w[2] + w[3]); if (a < w[0]) SIM.feed(s, D.FOODS[(rnd() * D.FOODS.length) | 0].id); else if (a < w[0] + w[1]) SIM.play(s); else if (a < w[0] + w[1] + w[2]) SIM.rinse(s); else if (s.poops) SIM.clearPoop(s); } } catch (e) { }
      SIM.advance(s, 3600, {}, 600); } return s.form || s.stage; };
  for (let i = 1; i <= N; i++) {
    const mk = () => { const s = fam(); adultKid(s); s.seed = (i * 2654435761) >>> 0; F.scan(s, NOW, { kidFk: 'A3' }); F.st(s).offer = { due: S2.dayNum(NOW), at: 1 }; F.pick(s, 'tr', NOW, env); return s; };
    const a = mk(), b = mk(); C.scan(b, NOW, ctx); const cs = C.candidates(b, NOW, ctx, 'tr2'); C.choose(b, 'tr2', cs[i % cs.length].id, NOW, ctx);
    if (routeSnap(a) === routeSnap(b)) same++;
    const fa = run(a, i), fb = run(b, i); C.scan(b, NOW + 1, ctx); cnt(A, fa); cnt(Bx, fb); if (fa !== fb) drift++;
  }
  ok(same === N, '承傳之後 §7 欄位（evo／cq／seed／gen）一模一樣', same);
  const keys = [...new Set([...Object.keys(A), ...Object.keys(Bx)])], dpt = Math.max(...keys.map(k => Math.abs(((A[k] || 0) - (Bx[k] || 0)) / N * 100)));
  ok(dpt <= 0.3, '第二代團絨蛋分支比例差 ≤0.3pt（' + dpt.toFixed(2) + 'pt）', { A, B: Bx });
  ok(keys.length >= 2, '分支有分佈（唔係全部一樣）', A);
}
console.log('⑦ 色：上一代主色＋對比規則（tint_pair）');
{ const h = { pfk: 'A3' }, t1 = C.tintPair(L, h, 'B1'); ok(t1.hi === L.parents.A3.tint.hi && t1.lo === L.parents.A3.tint.lo && !t1.near, '色差夠 → 用上一代 hi／lo', t1);
  const t2 = C.tintPair(L, h, 'A3'); ok(t2.near && t2.hi !== L.parents.A3.tint.hi && C.hx(t2.hi).every((v, i) => v >= C.hx(L.parents.A3.tint.hi)[i]) && C.hx(t2.lo).every((v, i) => v <= C.hx(L.parents.A3.tint.lo)[i]), '同細佬主色太近（<90）→ hi 推白、lo 壓深', t2);
  const t3 = C.tintPair(L, { pfk: 'tide' }, 'S1'); ok(/^#[0-9a-f]{6}$/.test(t3.hi) && /^#[0-9a-f]{6}$/.test(t3.lo), '舊形態（冇 parents 色）→ 由主色推');
}
console.log('⑧ sanitize／reset');
{ const s = fam(); F.st(s).c5 = { demo: { tr1: { A: { n: 'x' }, Z: 1 } }, inh: { k9: { parent: 1 } }, pend: { a: 5 }, seen: { q: 'zzz' } }; const o = C.st(s);
  ok(o.demo.tr1.A.n === 0 && !o.demo.tr1.Z && !o.inh.k9 && !o.pend.a && !o.seen.q, '壞資料清走');
  S2.st(s).fast = 0.8; C.reset(s); ok(!F.st(s).c5.inh.k1 && !S2.st(s).fast, 'reset 清 c5＋fast');
}
console.log(`\n${pass} 通過，${fail} 失敗`); process.exit(fail ? 1 : 0);
