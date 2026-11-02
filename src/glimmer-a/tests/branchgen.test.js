/* 5c.1 QA P1：結局判定唔受「第幾代」影響（sim.branchRoll 唔再混 s.gen；long5a 團絨蛋 gen+1 之後分佈要同第 1 代一樣）。
   ① 第 1 代 branchRoll 同舊公式（tag:seed:gen=1）bit-identical；第 2／3 代同第 1 代一樣
   ② route-sweep 真 code：6 個時間表 × N seed，芽崽開始＋光卵開始，第 2 代 vs 第 1 代 每條路差 ≤0.3pt。node tests/branchgen.test.js [N=150] */
const S = require('../src/sim.js'), D = require('../src/data.js'), R = require('../tools/route-sweep.js');
let pass = 0, fail = 0; const ok = (c, n, i) => { if (c) { pass++; console.log('  ✓ ' + n); } else { fail++; console.log('  ✗ ' + n + (i !== undefined ? ' → ' + JSON.stringify(i) : '')); } };
const N = +process.argv[2] || 150;

console.log('① branchRoll 同代數無關，第 1 代同舊版一樣');
function oldRoll(s, tag) { let h = 2166136261; const k = tag + ':' + (s.seed >>> 0) + ':' + (s.gen || 1); for (let i = 0; i < k.length; i++) h = Math.imul(h ^ k.charCodeAt(i), 16777619); return S.makeRng(h >>> 0)(); }
{ let same1 = 0, same2 = 0, same3 = 0, n = 0;
  for (let seed = 1; seed <= 400; seed++) for (const tag of ['lumi', 'b5draw', 'x']) { const s = S.newState(0, seed * 7919); n++;
    const g1 = S.branchRoll(s, tag); if (g1 === oldRoll(s, tag)) same1++; s.gen = 2; if (S.branchRoll(s, tag) === g1) same2++; s.gen = 3; if (S.branchRoll(s, tag) === g1) same3++; delete s.gen; }
  ok(same1 === n, '第 1 代：' + same1 + '/' + n + ' 同舊公式 bit-identical');
  ok(same2 === n && same3 === n, '第 2／3 代：同第 1 代一樣（' + same2 + '／' + same3 + '）'); }

console.log('② 第 2 代 vs 第 1 代 結局分佈（每表 ' + N + ' 隻 × ' + Object.keys(R.SCHED).length + ' 表）');
function dist(o) { const c = {}; let tot = 0; for (const name of Object.keys(R.SCHED)) for (let i = 1; i <= N; i++) { const r = R.run(name, i, o); c[r.form] = (c[r.form] || 0) + 1; tot++; } const p = {}; for (const f of D.BRANCHES) p[f] = 100 * (c[f] || 0) / tot; return { p, tot, other: tot - D.BRANCHES.reduce((a, f) => a + (c[f] || 0), 0) }; }
for (const [lab, base] of [['芽崽開始', {}], ['光卵開始', { egg: true }]]) {
  const a = dist(Object.assign({ gen: 1 }, base)), b = dist(Object.assign({ gen: 2 }, base));
  const diffs = D.BRANCHES.map(f => [D.FORM_NAME[f], +(b.p[f] - a.p[f]).toFixed(2)]), worst = Math.max(...diffs.map(d => Math.abs(d[1])));
  ok(a.other === 0 && b.other === 0, lab + '：' + a.tot + ' 隻全部去到 9 條路其中一條', { a: a.other, b: b.other });
  ok(worst <= 0.3, lab + '：每條路 |第 2 代 − 第 1 代| ≤0.3pt（最大 ' + worst + 'pt）', diffs);
  console.log('    ' + D.BRANCHES.map(f => D.FORM_NAME[f] + ' ' + a.p[f].toFixed(1) + '%').join('  '));
}
console.log(`\n結果：${pass} 通過，${fail} 失敗`); process.exit(fail ? 1 : 0);
