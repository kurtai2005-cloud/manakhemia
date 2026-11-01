/* 新蛋系列 48px 預覽 smoke（Node 無依賴）：node tests/sprites48.test.js —— pets_idle_48 atlas、bulb_anchors_48、PARAMS.newSeries、主寵 80px path 停用。 */
const fs = require('fs'), path = require('path'), zlib = require('zlib');
const D = require('../src/data.js');
const C = D.PARAMS.newSeries, root = path.join(__dirname, '..');
let pass = 0, fail = 0;
function ok(c, name, info) { if (c) { pass++; console.log('  ✓ ' + name); } else { fail++; console.log('  ✗ ' + name + (info !== undefined ? '  → ' + JSON.stringify(info) : '')); } }
const KEYS = []; for (const l of 'ABCDEFGH') for (const t of [1, 2, 3]) KEYS.push(l + t);

console.log('# config');
ok(C && C.enabled === true && C.activeSeries === 'tuanrong', 'PARAMS.newSeries 開、activeSeries 仍係 tuanrong（主寵唔換）');
ok(D.PARAMS.sprites80 && D.PARAMS.sprites80.enabled === false, '80px 主寵 path 停用（主寵＝evo6 原樣）');
ok(C.frame === 48 && C.pivot[0] === 24 && C.pivot[1] === 45, 'frame 48、pivot (24,45)', C.pivot);
ok(JSON.stringify(C.idleMs) === '[260,180,260,140]', 'idle 260/180/260/140ms');
ok(C.glowR === 9 && C.shadowHalfW === 13, 'glowR 9、shadowHalfW 13（ENGINE_48）');
ok(C.glowA[0] === 0.42 && C.glowA[1] === 0.18, 'glowA 0.42±0.18');
ok(!fs.existsSync(path.join(root, 'art/sprites80')), 'art/sprites80 已移除（唔入 build）');

console.log('# atlas');
const buf = fs.readFileSync(path.join(root, C.base, C.atlas + '.png'));
const W = buf.readUInt32BE(16), H = buf.readUInt32BE(20);
ok(buf.slice(1, 4).toString() === 'PNG' && W === 192 && H === 1152, 'pets_idle_48.png 192×1152', [W, H]);
const J = JSON.parse(fs.readFileSync(path.join(root, C.base, C.atlas + '.json'), 'utf8'));
ok(J.meta.frameSize === 48 && J.meta.filter === 'nearest' && Object.keys(J.frames).length === 96, 'meta 48／nearest／96 幀');
const bad = []; KEYS.forEach((k, row) => { for (let f = 0; f < 4; f++) { const F = J.frames[k + '_idle_' + f];
  if (!F || F.frame.x !== f * 48 || F.frame.y !== row * 48 || F.frame.w !== 48 || F.pivot.x !== 24 || F.pivot.y !== 45 || F.durationMs !== C.idleMs[f]) bad.push(k + f); } });
ok(!bad.length, '每行一隻 A1→H3、4 欄、pivot (24,45)、durationMs', bad);
{ let p = 8, idat = [], ct, bd;
  while (p < buf.length) { const len = buf.readUInt32BE(p), ty = buf.slice(p + 4, p + 8).toString(); if (ty === 'IHDR') { bd = buf[p + 16]; ct = buf[p + 17]; } if (ty === 'IDAT') idat.push(buf.slice(p + 8, p + 8 + len)); p += 12 + len; }
  ok(bd === 8 && ct === 6, 'RGBA8');
  const raw = zlib.inflateSync(Buffer.concat(idat)), bpp = 4, stride = W * bpp, px = Buffer.alloc(W * H * 4);
  for (let y = 0; y < H; y++) { const ft = raw[y * (stride + 1)], o = y * (stride + 1) + 1;
    for (let i = 0; i < stride; i++) { const a = i >= bpp ? px[y * stride + i - bpp] : 0, b = y ? px[(y - 1) * stride + i] : 0, c = (y && i >= bpp) ? px[(y - 1) * stride + i - bpp] : 0; let v = raw[o + i];
      if (ft === 1) v += a; else if (ft === 2) v += b; else if (ft === 3) v += (a + b) >> 1; else if (ft === 4) { const pp = a + b - c, pa = Math.abs(pp - a), pb = Math.abs(pp - b), pc = Math.abs(pp - c); v += (pa <= pb && pa <= pc) ? a : pb <= pc ? b : c; }
      px[y * stride + i] = v & 255; } }
  const A = (x, y) => px[(y * W + x) * 4 + 3], al = new Set(); for (let i = 3; i < px.length; i += 4) al.add(px[i]);
  ok([...al].every(v => v === 0 || v === 255), 'alpha 只有 0/255', [...al]);
  const noFoot = []; KEYS.forEach((k, row) => { let hit = false; for (let y = 42; y <= 46; y++) for (let x = 10; x < 38; x++) if (A(x, row * 48 + y) === 255) hit = true; if (!hit) noFoot.push(k); });
  ok(!noFoot.length, '每隻腳底（y 42–46）有實體', noFoot);
  const clear = []; KEYS.forEach((k, row) => { for (let f = 0; f < 4; f++) for (let x = 0; x < 48; x++) if (A(f * 48 + x, row * 48 + 47) !== 0) { clear.push(k); return; } });
  ok(!clear.length, 'y=47 透明（地線 46）', clear);
  const BA = JSON.parse(fs.readFileSync(path.join(root, C.base, C.anchors), 'utf8'));
  ok(BA.size === 48 && BA.pivot[0] === 24 && BA.pivot[1] === 45 && BA.glowRadiusPx === C.glowR, 'bulb_anchors_48：size／pivot／glowRadius 9');
  ok(KEYS.every(k => BA.creatures[k] && BA.creatures[k].name && Array.isArray(BA.creatures[k].perFrame) && BA.creatures[k].perFrame.length === 4), '24 隻都有 name＋perFrame×4');
  const off = []; KEYS.forEach((k, row) => { BA.creatures[k].perFrame.forEach((a, f) => { if (a[0] < 0 || a[0] > 47 || a[1] < 0 || a[1] > 47) off.push(k + f); }); });
  ok(!off.length, 'anchor 喺 48 框內', off);
}
console.log(`結果：${pass} 通過，${fail} 失敗`); process.exit(fail ? 1 : 0);
