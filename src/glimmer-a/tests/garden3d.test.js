/* garden3d.test — #89 3D 花園 H1 純邏輯（座標、鏡頭、碰撞、方向、日夜、畫質）。node tests/garden3d.test.js */
const G3 = require('../src/garden3d.js');
let pass = 0, fail = 0;
const ok = (c, m, x) => { if (c) { pass++; console.log('  ✓ ' + m); } else { fail++; console.log('  ✗ ' + m + (x !== undefined ? '  → ' + JSON.stringify(x) : '')); } };
const near = (a, b, e) => Math.abs(a - b) <= (e == null ? 1e-6 : e);

console.log('① 座標');
{
  ok(G3.CX === 97 && G3.GROUND_Y === 292 && G3.ZSCALE === 1.6 && G3.W === 195 && G3.H === 422, '美術格 195×422、原點 (97,292)、z 倍率 1.6');
  const w = G3.artToWorld(97, 292); ok(w.x === 0 && w.z === 0, '腳底 → 世界原點', w);
  const w2 = G3.artToWorld(97 + 10, 292 + 10); ok(w2.x === 10 && near(w2.z, 16), 'art +10,+10 → x=10, z=16', w2);
  const a = G3.worldToArtFlat(10, 16); ok(a.x === 107 && near(a.y, 302), '來回轉換', a);
  const p = G3.petWorld({ x: -20, depth: 5 }); ok(p.x === -20 && near(p.z, 8), 'beh.x／depth → 世界', p);
}

console.log('② 日夜光');
{
  ok(G3.nightMix(8) === 0 && G3.nightMix(13) === 0, '朝／午＝日');
  ok(near(G3.nightMix(17.5), 0.5), '17:30 黃昏 0.5', G3.nightMix(17.5));
  ok(G3.nightMix(22) === 1 && G3.nightMix(3) === 1, '夜＝1');
  const L = { sun: { dir: [0, -1, 0], color: '#ffffff', intensity: 1, ambient: { color: '#cfe0f0', intensity: 0.55 }, shadowIntensity: 0.3 },
    fill: { dir: [0, 0, -1], color: '#ffe2c4', intensity: 0.38, intensityNight: 0 },
    night: { sun: 0.12, ambient: '#4a5a90', ambientIntensity: 0.35 },
    lights: [{ id: 'lamp', x: 0, y: 1, z: 0, color: '#ffd890', radius: 70, intensity: 0, intensityNight: 1.2, flicker: 0 },
      { id: 'window_side', x: 114, y: 57, z: -72, color: '#ffc870', radius: 40, intensity: 0, intensityNight: 0.7, flicker: 0 }] };
  const D = G3.mixLights(L, 0), N = G3.mixLights(L, 1);
  ok(D.sun === 1 && N.sun === 0.12 && D.fill === 0.38 && N.fill === 0, '日／夜 sun＋fill', { D: [D.sun, D.fill], N: [N.sun, N.fill] });
  ok(D.byId.lamp === 0 && N.byId.lamp === 1.2 && N.byId.window_side === 0.7 && D.byId.window_side === 0, '燈：日 0、夜 intensityNight（含 window_side）', { D: D.byId, N: N.byId });
  ok(D.shadowIntensity === 0.3, 'shadowIntensity 0.3');
}

console.log('③ 鏡頭 sway／follow');
{
  const cam = { target: [0, 30, -72], pitchDeg: 30, dist: 580, fovDeg: 40, orbitMinDeg: -10, orbitMaxDeg: 10,
    swayAmplitudeDeg: 5, swayHalfPeriodSec: 6, followDamping: 2, followWeight: [0.25, 0.3], followOffset: [-20, 0], followOrigin: [-110, -40] };
  ok(near(G3.swayYaw(0, cam), -5) && near(G3.swayYaw(3, cam), 0) && near(G3.swayYaw(6, cam), 5) && near(G3.swayYaw(12, cam), -5), 'yaw＝−A·cos(πt/T) 0→−5、3s→0、6s→+5、12s→−5', [G3.swayYaw(0, cam), G3.swayYaw(3, cam), G3.swayYaw(6, cam), G3.swayYaw(12, cam)]);
  const des0 = G3.followDesired(cam, { x: 0, z: 0 });
  ok(near(des0[0], 7.5) && des0[1] === 30 && near(des0[2], -60), '原點 desired＝target＋offset＋weight·(0−origin)', des0);
  const step = G3.followStep([0, 30, -72], [10, 30, -60], 0.5, 2);
  const k = 1 - Math.exp(-2 * 0.5);
  ok(near(step[0], 0 + 10 * k) && near(step[2], -72 + 12 * k), '跟拍 cam+=(desired−cam)·(1−exp(−2dt))', step);
  const P0 = G3.camPos([0, 30, -72], 0, cam);
  ok(near(P0[0], 0) && P0[1] > 30 && P0[2] > -72, 'yaw 0：鏡頭喺 target 右上前方（+Y+Z）', P0);
  ok(G3.clampYaw(8, cam, 5) === 10 && G3.clampYaw(-8, cam, -5) === -10, '手拉＋自動擺夾喺 ±10°');
}

console.log('④ dir4 方向');
{
  const s = G3.dirOf(10, 0, true); ok(s.dir === 'side' && s.flip === false && s.clip === 'walk', '向右行＝side', s);
  const l = G3.dirOf(-4, 1, true); ok(l.dir === 'side' && l.flip === true, '向左行＝side 鏡像', l);
  const f = G3.dirOf(0, 5, false); ok(f.dir === 'front' && f.flip === false && f.clip === 'idle', '向鏡頭停＝front idle', f);
  const b = G3.dirOf(1, -8, true); ok(b.dir === 'back' && b.clip === 'walk', '向屋行＝back walk', b);
  ok(G3.frameName({ dir: 'front', clip: 'idle' }, 0) === 'front_idle_01', 't=0 → 01');
  ok(G3.frameName({ dir: 'side', clip: 'walk' }, 0.5) === 'side_walk_06', 'walk 10fps、0.5s → 第 6 幀', G3.frameName({ dir: 'side', clip: 'walk' }, 0.5));
}

console.log('⑤ 碰撞 footprint');
{
  const objs = [
    { id: 'tree', footprint: { type: 'rect', x: [-98, -78], z: [-53, -35], pad: 3 } },
    { id: 'cottage', footprint: { type: 'rect', x: [53, 112], z: [-94, -50], pad: 4 } },
    { id: 'pot_S', footprint: { type: 'poly', points: [[49, 27], [52.54, 25.54], [54, 22], [52.54, 18.46], [49, 17], [45.46, 18.46], [44, 22], [45.46, 25.54]], pad: 2 } },
    { id: 'lanterns', backfill: false },
    { id: 'bush_bR', backfill: true, footprint: { type: 'rect', x: [0, 10], z: [0, 10], pad: 0 } }
  ];
  ok(G3.blocked(objs, 0, 0, 10).length === 0, '原點唔撞', G3.blocked(objs, 0, 0, 10));
  ok(G3.blocked(objs, -88, -44, 10).indexOf('tree') >= 0, '企入樹幹會被擋', G3.blocked(objs, -88, -44, 10));
  ok(G3.blocked(objs, 82.5, -72, 10).indexOf('cottage') >= 0, '企入屋會被擋', G3.blocked(objs, 82.5, -72, 10));
  ok(G3.blocked(objs, 49, 22, 10).indexOf('pot_S') >= 0, '花盆多邊形碰撞', G3.blocked(objs, 49, 22, 10));
  ok(G3.blocked(objs, 5, 5, 10).indexOf('bush_bR') < 0 && G3.blocked(objs, 0, -46, 10).indexOf('lanterns') < 0, '補位件／吊燈冇 footprint');
}

console.log('⑤b XZ 走位／繞障／揀目標');
{
  const oj = require('../art/garden3d/H1/objects.json');
  const objs = oj.objects;
  const RX = G3.RANGE3.x, RZ = G3.RANGE3.z;
  const s0 = G3.stepXZ(objs, 0, 0, 10, 0, 2, 10, RX, RZ);
  ok(s0.x > 0 && Math.abs(s0.z) < 0.01 && !s0.arrived, '沿 +X 行一步', s0);
  const sZ = G3.stepXZ(objs, 0, 0, 0, 20, 2, 10, RX, RZ);
  ok(sZ.z > 0 && Math.abs(sZ.x) < 0.01, '沿 +Z（向鏡頭）行一步', sZ);
  const sB = G3.stepXZ(objs, 0, 10, 0, 0, 2, 10, RX, RZ);
  ok(sB.z < 10 && sB.dz < 0, '沿 −Z（向屋）行', sB);
  // 唔可以踏入樹幹（由樹前方一步步行近）
  const into = G3.stepXZ(objs, -88, -10, -88, -44, 2, 10, RX, RZ);
  ok(G3.blocked(objs, into.x, into.z, 10).indexOf('tree') < 0, '一步唔會踏入樹 footprint', into);
  // 由原點繞去小屋後／樹後（A* 路徑）
  function followTo(tx, tz) {
    const path = G3.buildPath(objs, 0, 0, tx, tz, 10, RX, RZ);
    let x = 0, z = 0, pi = 0, arr = false, hit = false;
    for (let i = 0; i < 2500; i++) {
      const fol = G3.followPath(objs, x, z, path, { x: tx, z: tz }, 2, 10, RX, RZ, pi);
      pi = fol.pi; x = fol.step.x; z = fol.step.z;
      if (G3.blocked(objs, x, z, 10).length) { hit = true; break; }
      if (fol.step.arrived) { arr = true; break; }
    }
    return { x: x, z: z, arr: arr, hit: hit, n: path && path.length };
  }
  const c = followTo(82, -110);
  ok(c.arr && !c.hit && Math.hypot(c.x - 82, c.z + 110) < 3, '繞過圍欄／小屋到達 (82,−110)', c);
  const tr = followTo(-88, -80);
  ok(tr.arr && !tr.hit && Math.hypot(tr.x + 88, tr.z + 80) < 3, '繞到樹後 (−88,−80)', tr);
  const pw = G3.petWorld({ x: 10, z: -40 });
  ok(pw.x === 10 && pw.z === -40, 'petWorld 用 3D z（唔使 depth×1.6）', pw);
  const pw2 = G3.petWorld({ x: 4, depth: 5 });
  ok(pw2.z === 5 * G3.ZSCALE, '冇 z 時仍用 depth×ZSCALE', pw2);
  const rng = (function () { let i = 0; return function () { i = (i * 1103515245 + 12345) & 0x7fffffff; return (i >>> 0) / 0x7fffffff; }; }());
  const pick = G3.pickWalk(objs, rng, { x: 0, z: 0 }, 10, G3.RANGE3);
  ok(pick && G3.blocked(objs, pick.x, pick.z, 10).length === 0, 'pickWalk 落喺可企位', pick);
}

console.log('⑥ 畫質自動');
{
  ok(G3.detectQuality({ qs: { '3d': '0' }, webgl: true }).want === false && G3.detectQuality({ qs: { '3d': '0' } }).reason === 'off', '?3d=0 → 2D');
  ok(G3.detectQuality({ webgl: false }).quality === 'low' && G3.detectQuality({ webgl: false }).reason === 'nowebgl', '冇 WebGL → 2D');
  const lo = G3.detectQuality({ webgl: true, hardwareConcurrency: 4, deviceMemory: 3 });
  ok(lo.want === false && lo.quality === 'low' && lo.reason === 'lowend', '低端機（≤4 核或 ≤4GB）自動 2D', lo);
  const hi = G3.detectQuality({ webgl: true, hardwareConcurrency: 8, deviceMemory: 8 });
  ok(hi.want === true && hi.quality === 'high', '中高階自動 3D high', hi);
  ok(G3.detectQuality({ qs: { '3d': 'mid' }, webgl: true, hardwareConcurrency: 2 }).quality === 'mid', '?3d=mid 覆蓋低端');
  ok(G3.QSET.high.tex3x && !G3.QSET.mid.tex3x && G3.QSET.high.shadow > G3.QSET.mid.shadow, 'high＝@3x＋大影圖、mid＝1x＋細影');
}

console.log('—' + (fail ? ' 失敗 ' + fail : ' 通過') + '／' + (pass + fail) + '—');
process.exit(fail ? 1 : 0);
