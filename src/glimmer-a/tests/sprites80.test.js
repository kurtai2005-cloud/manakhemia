/* 遊美 80px 正式版寵物 smoke（Node 無依賴）：node tests/sprites80.test.js —— pets_idle_80 atlas 尺寸／幀／pivot／時長、bulb_anchors_80、PARAMS.sprites80 對應、腳底 (97,292) 數學。 */
const fs = require('fs'), path = require('path'), zlib = require('zlib');
const D = require('../src/data.js');
const C = D.PARAMS.sprites80, root = path.join(__dirname, '..');
let pass = 0, fail = 0;
function ok(c, name, info) { if (c) { pass++; console.log('  ✓ ' + name); } else { fail++; console.log('  ✗ ' + name + (info !== undefined ? '  → ' + JSON.stringify(info) : '')); } }
const KEYS = []; for (const l of 'ABCDEFGH') for (const t of [1, 2, 3]) KEYS.push(l + t);

console.log('# config');
ok(C && C.enabled === true, 'PARAMS.sprites80 存在、預設開');
ok(C.frame === 80 && C.pivot[0] === 40 && C.pivot[1] === 77, 'frame 80、pivot (40,77)', C.pivot);
ok(JSON.stringify(C.idleMs) === '[260,180,260,140]', 'idle 260/180/260/140ms', C.idleMs);
ok(C.clips.idle === 'idle' && C.clips.blink === 3, 'idle／blink 有 80px；其餘 clip fallback');
ok(Object.keys(D.CLIPS).filter(k => C.clips[k] != null).join() === 'idle,blink', '只有 idle＋blink 用 80px', Object.keys(C.clips));
for (const [f, l] of Object.entries(C.lines)) ok(/^[A-H]$/.test(l) && (D.BRANCHES.includes(f) || f === 'radiant'), 'line ' + f + '→' + l);
for (const [st, tr] of Object.entries(C.tiers)) ok(D.STAGES.includes(st) && tr >= 1 && tr <= 3, 'tier ' + st + '→' + tr);
ok(!C.tiers.egg, 'egg 唔用 80px');

console.log('# atlas');
const pngPath = path.join(root, C.base, C.atlas + '.png'), buf = fs.readFileSync(pngPath);
ok(buf.slice(1, 4).toString() === 'PNG', 'pets_idle_80.png 係 PNG');
const W = buf.readUInt32BE(16), H = buf.readUInt32BE(20);
ok(W === 320 && H === 1920, 'atlas 320×1920', [W, H]);
const J = JSON.parse(fs.readFileSync(path.join(root, C.base, C.atlas + '.json'), 'utf8'));
ok(J.meta.size.w === 320 && J.meta.size.h === 1920 && J.meta.frameSize === 80 && J.meta.filter === 'nearest', 'meta 320×1920／80／nearest');
ok(Object.keys(J.frames).length === 96, '96 幀（24 隻 × 4）', Object.keys(J.frames).length);
let bad = [];
KEYS.forEach((k, row) => { for (let f = 0; f < 4; f++) { const F = J.frames[k + '_idle_' + f];
  if (!F || F.frame.x !== f * 80 || F.frame.y !== row * 80 || F.frame.w !== 80 || F.frame.h !== 80 || F.pivot.x !== 40 || F.pivot.y !== 77 || F.durationMs !== C.idleMs[f]) bad.push(k + f); } });
ok(!bad.length, '每行一隻 A1→H3、4 欄、pivot (40,77)、durationMs 對 idleMs', bad);

console.log('# 解 PNG（alpha 量化 0/60/110/170/255、腳底有實體）');
{ // 最簡 PNG 解碼（8-bit RGBA，非 interlace）
  let p = 8, idat = [], ct, bd, il;
  while (p < buf.length) { const len = buf.readUInt32BE(p), ty = buf.slice(p + 4, p + 8).toString(); if (ty === 'IHDR') { bd = buf[p + 16]; ct = buf[p + 17]; il = buf[p + 20]; } if (ty === 'IDAT') idat.push(buf.slice(p + 8, p + 8 + len)); p += 12 + len; }
  ok(bd === 8 && ct === 6 && il === 0, 'RGBA8 非 interlace', [bd, ct, il]);
  const raw = zlib.inflateSync(Buffer.concat(idat)), bpp = 4, stride = W * bpp, px = Buffer.alloc(W * H * 4);
  for (let y = 0; y < H; y++) { const ft = raw[y * (stride + 1)], o = y * (stride + 1) + 1;
    for (let i = 0; i < stride; i++) { const a = i >= bpp ? px[y * stride + i - bpp] : 0, b = y ? px[(y - 1) * stride + i] : 0, c = (y && i >= bpp) ? px[(y - 1) * stride + i - bpp] : 0; let v = raw[o + i];
      if (ft === 1) v += a; else if (ft === 2) v += b; else if (ft === 3) v += (a + b) >> 1; else if (ft === 4) { const pp = a + b - c, pa = Math.abs(pp - a), pb = Math.abs(pp - b), pc = Math.abs(pp - c); v += (pa <= pb && pa <= pc) ? a : pb <= pc ? b : c; }
      px[y * stride + i] = v & 255; } }
  const A = (x, y) => px[(y * W + x) * 4 + 3];
  const al = new Set(); for (let i = 3; i < px.length; i += 4) al.add(px[i]);
  ok([...al].every(v => [0, 60, 110, 170, 255].includes(v)), 'alpha 只用 0/60/110/170/255', [...al]);
  const noFoot = []; KEYS.forEach((k, row) => { let hit = false; for (let y = 72; y <= 77; y++) for (let x = 20; x < 60; x++) if (A(x, row * 80 + y) >= 170) hit = true; if (!hit) noFoot.push(k); });
  ok(!noFoot.length, '每隻幀 0 腳底（y 72–77）近 pivot 有實體', noFoot);
  const BA = JSON.parse(fs.readFileSync(path.join(root, C.base, C.anchors), 'utf8'));
  const offArt = []; KEYS.forEach((k, row) => { const a = BA.creatures[k].anchor; let m = 0; for (let dy = -2; dy <= 2; dy++) for (let dx = -2; dx <= 2; dx++) m = Math.max(m, A(a[0] + dx, row * 80 + a[1] + dy)); if (m < 170) offArt.push(k); });
  ok(!offArt.length, 'bulb anchor 落喺實體像素（±2px）', offArt);
}

console.log('# bulb_anchors_80');
const BA = JSON.parse(fs.readFileSync(path.join(root, C.base, C.anchors), 'utf8'));
ok(BA.size === 80 && BA.pivot[0] === 40 && BA.pivot[1] === 77 && BA.glowRadiusPx === C.glowR, 'size 80／pivot／glowRadius 14 = PARAMS.glowR');
ok(KEYS.every(k => BA.creatures[k]), '24 隻齊', KEYS.filter(k => !BA.creatures[k]));
bad = [];
for (const k of KEYS) { const c = BA.creatures[k], a = c.anchor;
  if (!(a[0] >= 0 && a[0] < 80 && a[1] >= 0 && a[1] < 80) || c.perFrame.length !== 4 || c.fromFoot[0] !== a[0] - 40 || c.fromFoot[1] !== a[1] - 77 || !/^#[0-9a-f]{6}$/i.test(c.glowTint) || !['bulb', 'star', 'own'].includes(c.type)) bad.push(k);
  const d1 = c.perFrame[1][1] - c.perFrame[0][1]; if (d1 < 0 || d1 > 1 || c.perFrame[0][0] !== a[0] || c.perFrame[2][1] !== a[1]) bad.push(k + ':pf'); }
ok(!bad.length, 'anchor 喺框內、perFrame×4（幀 1 bob 0–1px 低）、fromFoot＝anchor−pivot、glowTint、type', bad);
ok(BA.creatures.B1.type === 'own' && BA.creatures.H3.type === 'own' && BA.creatures.F1.type === 'star' && BA.creatures.G1.type === 'star', 'B1/H3 own、F1/G1 star');

console.log('# 腳底落 art (97,292)');
{ const R = { CX: 97, GY: 292 }; const dx = R.CX - C.pivot[0], dy = R.GY - C.pivot[1];
  ok(dx === 57 && dy === 215, 'drawX 97−40=57、drawY 292−77=215', [dx, dy]);
  const c2 = BA.creatures.C2; ok(dx + c2.anchor[0] === 99 && dy + c2.anchor[1] === 240, 'C2 燈泡 art (99,240)'); }

console.log('# idle 節奏（同 render.spr80Frame 一樣公式）');
{ const fr = (t) => { const ms = C.idleMs, tot = 840; let u = ((t * 1000) % tot + tot) % tot; for (let i = 0; i < 4; i++) { if (u < ms[i]) return i; u -= ms[i]; } return 0; };
  ok(fr(0) === 0 && fr(0.259) === 0 && fr(0.26) === 1 && fr(0.44) === 2 && fr(0.7) === 3 && fr(0.84) === 0, '0→1→2→3 @ 0/260/440/700ms、840ms 循環'); }

console.log('# 打包（build-single 內嵌 art/**）');
ok(fs.readFileSync(path.join(root, 'tools', 'build-single.py'), 'utf8').includes("'art'"), 'art/sprites80 會被 build-single 內嵌');
ok(fs.readFileSync(path.join(root, 'src', 'main.js'), 'utf8').includes("qs.get('spr') === 'old'"), '?spr=old 開關存在');

console.log(`結果：${pass} 通過，${fail} 失敗`);
process.exit(fail ? 1 : 0);
