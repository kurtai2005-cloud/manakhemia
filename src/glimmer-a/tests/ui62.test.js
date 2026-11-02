/* 6b.2 單元測試（Node 無依賴）：node tests/ui62.test.js —— 講嘢句按字數計時（ui62.speechSec）、工作更份（work62.shift） */
const U62 = require('../src/ui62.js'), W62 = require('../src/work62.js');
let pass = 0, fail = 0;
function ok(c, name, info) { if (c) { pass++; console.log('  ✓ ' + name); } else { fail++; console.log('  ✗ ' + name + (info !== undefined ? '  → ' + JSON.stringify(info) : '')); } }
const S = U62.speechSec;
ok(S('你好') === 3.5 && S('') === 3.5, '短句 3.5 秒', [S('你好'), S('')]);
ok(S('一二三四五六七八九十') === 3.5, '10 字內唔加時', S('一二三四五六七八九十'));
ok(S('一二三四五六七八九十一二三四五六七八九十') === 4.7, '20 字 → 3.5＋10×0.12＝4.7', S('一二三四五六七八九十一二三四五六七八九十'));
ok(S('一 二 三 四 五 六 七 八 九 十 一') === 3.62, '空白唔計字', S('一 二 三 四 五 六 七 八 九 十 一'));
ok(S('字'.repeat(200)) === 9, '最長 9 秒', S('字'.repeat(200)));
{ let m = 0, mono = true; for (let n = 0; n <= 80; n++) { const v = S('字'.repeat(n)); if (v < m) mono = false; m = v; } ok(mono, '字數越多秒數唔會少'); }
ok(typeof U62.SUB === 'object' && Object.keys(U62.SUB).length >= 5 && Object.values(U62.SUB).every(v => v.length >= 6 && v.length <= 40), '面板用途說明：每句 6–40 字', Object.values(U62.SUB).map(v => v.length));
ok(typeof U62.TIPS === 'object' && Object.keys(U62.TIPS).length >= 5, '第一次小提示 ≥5 個功能', Object.keys(U62.TIPS));
const sh = W62.shift;
ok(sh('post', 8.5).state === 'before' && sh('post', 8.5).label === '09:00 開工', '日更 08:30 未開工', sh('post', 8.5));
ok(sh('post', 12).state === 'on' && sh('post', 12).pct === 0.375 && sh('post', 12).label === '17:00 收工・剩 5 小時', '日更 12:00 做緊 37.5%', sh('post', 12));
ok(sh('garden', 16.75).label === '17:00 收工・剩 15 分鐘', '剩唔夠 1 小時用分鐘', sh('garden', 16.75));
ok(sh('chef', 17).state === 'done' && sh('chef', 23).label === '收咗工（17:00）', '日更 17:00 後收工', sh('chef', 23));
ok(sh('watch', 20).state === 'before' && sh('watch', 23).state === 'on' && sh('watch', 4).state === 'on', '守夜 21:00–05:00（跨日）', [sh('watch', 20).state, sh('watch', 23).state, sh('watch', 4).state]);
ok(Math.abs(sh('watch', 1).pct - 0.5) < 1e-9 && sh('watch', 1).end === '05:00', '守夜 01:00 做咗一半', sh('watch', 1));
ok(sh('watch', 6).state === 'before', '守夜 06:00 → 今晚 21:00 開工', sh('watch', 6));
ok(sh('nope', 12).state === 'on', '唔識嘅工作 → 當日更', sh('nope', 12));
{ let good = true; for (const j of ['post', 'garden', 'chef', 'watch']) for (let h = 0; h < 24; h += 0.25) { const r = sh(j, h); if (!(r.pct >= 0 && r.pct <= 1) || !r.label) good = false; } ok(good, '全日每 15 分鐘 pct ∈ [0,1]、有字'); }
console.log('\nui62 單元：' + pass + ' pass / ' + fail + ' fail'); process.exit(fail ? 1 : 0);
