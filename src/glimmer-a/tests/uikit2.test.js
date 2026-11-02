/* 4b.1 UI kit v2（art/ui_hd2d_v2）— 純函數＋kit 資料對數：pref（?ui／localStorage）、moodOf、rectOf（PORTRAIT_SYNC）、accAdj、biCss（9-slice tile，唔 stretch）、
   layout／atlas／icons／字型／OFL 齊。node tests/uikit2.test.js */
const fs = require('fs'), path = require('path');
const U = require('../src/hd2dui2.js'), D = require('../src/data.js');
const K = path.join(__dirname, '../art/ui_hd2d_v2'), J = (f) => JSON.parse(fs.readFileSync(path.join(K, f), 'utf8'));
let pass = 0, fail = 0; const ok = (c, m, x) => { if (c) { pass++; console.log('  ✓ ' + m); } else { fail++; console.log('  ✗ ' + m + (x !== undefined ? '  → ' + JSON.stringify(x) : '')); } };

console.log('① pref');
ok(U.pref('1', '2') === 1 && U.pref('2', '1') === 2, '?ui=1／?ui=2 蓋過 localStorage');
ok(U.pref(null, null) === 2 && U.pref(null, '2') === 2 && U.pref(null, '1') === 1 && U.pref('x', null) === 2, '冇 flag → 記低嘅，預設 v2');
ok(U.KEY === 'glimmer.ui', 'localStorage key glimmer.ui');

console.log('② moodOf');
const st = (n, o) => Object.assign({ needs: Object.assign({ hunger: 80, energy: 80, mood: 50, clean: 80 }, n) }, o || {});
ok(U.moodOf(st({}, { sleeping: true })) === 'sleep', '瞓緊 → sleep');
ok(U.moodOf(st({ hunger: 10 }, { sick: true })) === 'sick', '病 → sick（先過肚餓）');
ok(U.moodOf(st({ hunger: 29 })) === 'hungry', '肚餓 <30 → hungry');
ok(U.moodOf(st({ energy: 10 })) === 'sleepy', '體力 <30 → sleepy');
ok(U.moodOf(st({ mood: 70 })) === 'happy' && U.moodOf(st({ mood: 69 })) === 'normal', '心情 ≥70 → happy，否則 normal');
ok(U.moodOf(null) === 'normal', 'null → normal');

console.log('③ rectOf（portrait_rects）');
const R = J('portrait_rects.json');
const forms = Object.keys(R.forms);
ok(forms.length >= 10, 'forms ' + forms.length + ' 個');
let bad = forms.filter(k => { const r = U.rectOf(R, k); return !(r.hit && r.rect.length === 3 && r.rect[2] === 22 && r.rect[0] >= 0 && r.rect[1] >= 0 && r.rect[0] + 22 <= r.frame + 2 * R.pad && r.rect[1] + 22 <= r.frame + 2 * R.pad); });
ok(!bad.length, '每個 form rect 22×22 喺 pad 後 frame 入面', bad);
const al = Object.keys(R.aliases || {});
ok(al.every(a => { const r = U.rectOf(R, a); return r.hit && JSON.stringify(r.rect) === JSON.stringify(R.forms[R.aliases[a]].rect); }), 'aliases → 對應 form（' + al.length + '）');
const fb = U.rectOf(R, '__nope__', 32); ok(!fb.hit && fb.rect[2] === 22 && fb.frame === 32, '冇 form → 中上 fallback', fb);
ok(U.rectOf(R, forms[0]).rect !== R.forms[forms[0]].rect, 'rect 係 copy（唔改原資料）');

console.log('④ accAdj');
const a = U.accAdj([10, 12, 22], { shift: 3, badge: true, pop: 2 }); ok(a.rect[1] === 9 && a.rect[0] === 10 && a.badge && a.pop === 2, 'shift 向上、badge／pop', a);
const a0 = U.accAdj([10, 12, 22]); ok(a0.rect[1] === 12 && !a0.badge && a0.pop === 0, '冇 acc → 原 rect');

console.log('⑤ biCss（9-slice tile）');
const css = U.biCss('X.png', { nine: [3, 4, 5, 6] });
ok(/border-image:url\(X\.png\) 8 10 12 6 fill \/ 8px 10px 12px 6px \/ 0 repeat/.test(css), 'slice／width ×2，順序 t r b l', css);
ok(/repeat/.test(css) && !/stretch/.test(css) && /pixelated/.test(css), 'repeat（tile）＋pixelated，冇 stretch');

console.log('⑥ kit 資料');
const L = J('layout_hd2d_v2.json'), A = J('ui_hd2d_v2@1x.json'), I = J('icons_hd2d_v2@1x.json');
ok(JSON.stringify(L.art) === '[195,422]', 'layout art 195×422（×2 → 390×844）', L.art);
ok(L.banner && L.portrait && L.dock && L.rail && L.house4b, 'layout 有 banner／portrait／dock／rail／house4b');
const AF = A.frames || A, IF = I.frames || I;
const needA = ['card_sel', 'ribbon_navy', 'chip', 'red_dot_num', 'red_dot', 'med13_navy', 'pill_navy'];
ok(needA.every(k => AF[k]), 'atlas 有 hd2dui2 用嘅零件', needA.filter(k => !AF[k]));
ok(Object.values(AF).filter(f => f.nine).every(f => !f.mode || f.mode === 'repeat' || f.mode === 'tile'), '9-slice 零件 mode 係 tile／repeat', Object.entries(AF).filter(([, f]) => f.nine && f.mode && !/repeat|tile/.test(f.mode)).map(([k, f]) => k + ':' + f.mode));
const needI = ['gift', 'mail', 'house', 'dex', 'feed', 'clean', 'sleep', 'mini_star', 'mini_lock', 'check'];
ok(needI.every(k => IF[k]), 'icons 有 rail／動作用嘅', needI.filter(k => !IF[k]));
ok(fs.existsSync(path.join(K, 'ui_hd2d_v2@1x.png')) && fs.existsSync(path.join(K, 'icons_hd2d_v2@1x.png')), 'atlas png 齊');
['fp8-subset.ttf', 'fp10-subset.ttf', 'fp12-subset.ttf', 'OFL_fusion-pixel.txt', 'README.md'].forEach(f => ok(fs.existsSync(path.join(K, 'fonts', f)), '字型 ' + f));
ok(/SIL OPEN FONT LICENSE/i.test(fs.readFileSync(path.join(K, 'fonts/OFL_fusion-pixel.txt'), 'utf8')), 'OFL 1.1 全文');
ok(fs.existsSync(path.join(__dirname, '../art/ui_hd2d/ui_hd2d@3x.json')) && fs.existsSync(path.join(__dirname, '../src/hd2dui.js')), 'v1 kit＋hd2dui.js 保留（?ui=1 fallback）');

console.log('⑦ 版本');
ok(D.PARAMS.series2.version === '5b', '版本 5b', D.PARAMS.series2.version);

console.log('\n' + pass + ' 過／' + fail + ' 唔過'); process.exit(fail ? 1 : 0);
