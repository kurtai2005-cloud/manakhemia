/* 6b.3 單元測試（Node 無依賴）：node tests/ui63.test.js —— 縮細倍數、字級、縮放錨點（ui63.anchorOf） */
const U = require('../src/ui63.js');
let pass = 0, fail = 0;
function ok(c, name, info) { if (c) { pass++; console.log('  ✓ ' + name); } else { fail++; console.log('  ✗ ' + name + (info !== undefined ? '  → ' + JSON.stringify(info) : '')); } }
ok(Math.abs(U.S - 20 / 24) < 1e-9, '縮細一級：倍數 20/24', U.S);
ok(U.TYPE.title === 20 && U.TYPE.body === 16 && U.TYPE.aux === 14, '字級 24／18／16 → 20／16／14', U.TYPE);
ok(Math.abs(24 * U.S - 20) < 1e-9 && Math.abs(18 * U.S - 15) < 1e-9, '點陣字 FP12 24 CSS × S ＝ 有效 20（保持 12 倍數）');
ok(U.TYPE.lhBody >= U.TYPE.body * 1.4 && U.TYPE.lhAux >= U.TYPE.aux * 1.4, '行距 ≥1.4 倍', U.TYPE);
ok(U.HK === 'glimmer.u63hide', '收埋狀態 localStorage key', U.HK);
const A = U.anchorOf;
ok(JSON.stringify(A(0, 0, 390, 94)) === '[195,0]', '頂 banner：中上錨', A(0, 0, 390, 94));
ok(JSON.stringify(A(2, 770, 386, 74)) === '[195,844]', '底 dock：中下錨', A(2, 770, 386, 74));
ok(JSON.stringify(A(14, 96, 362, 712)) === '[195,0]', '大面板頂近邊：中上錨', A(14, 96, 362, 712));
ok(JSON.stringify(A(8, 214, 374, 590)) === '[195,844]', '面板底近邊：中下錨', A(8, 214, 374, 590));
ok(JSON.stringify(A(330, 300, 48, 48)) === '[390,324]', '右邊細掣：右錨（靠邊唔離位）', A(330, 300, 48, 48));
ok(JSON.stringify(A(10, 300, 60, 40)) === '[0,320]', '左邊細掣：左錨', A(10, 300, 60, 40));
ok(JSON.stringify(A(150, 400, 90, 40)) === '[195,420]', '中間：自己中心', A(150, 400, 90, 40));
{ let inside = true; for (let L = 0; L <= 340; L += 20) for (let T = 0; T <= 800; T += 40) { const [x, y] = A(L, T, 50, 40); const nx = x + (L - x) * U.S, ny = y + (T - y) * U.S; if (nx < -0.01 || ny < -0.01 || nx + 50 * U.S > 390.01 || ny + 40 * U.S > 844.01) inside = false; } ok(inside, '任何位置縮完都仲喺 390×844 入面'); }
console.log('\nui63 單元：' + pass + ' pass / ' + fail + ' fail'); process.exit(fail ? 1 : 0);
