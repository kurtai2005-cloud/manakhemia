#!/usr/bin/env node
/* b7278cf：霧天照顧計菇傘 +0.5。唔改 code branch。
 * 設定寫法係 route.fog = { to:'shroom', w:0.5 }，唔係字面 "fog: 0.5"。
 * 用法：SIM=/tmp/glimmer-s12/src/glimmer-a/src/sim.js node QA/sys12/fog-shroom.test.js
 */
'use strict';
const path = require('path');
const simPath = process.env.SIM || '/tmp/glimmer-s12/src/glimmer-a/src/sim.js';
const S = require(path.resolve(simPath));
const D = require(path.resolve(path.dirname(simPath), 'data.js'));
const C = D.PARAMS.evo6.branch;
let pass = 0, fail = 0;
function ok(c, n, info) { if (c) { pass++; console.log('  ✓ ' + n); } else { fail++; console.log('  ✗ ' + n + (info !== undefined ? '  → ' + JSON.stringify(info) : '')); } }
function near(a, b, n) { ok(Math.abs(a - b) < 1e-6, n, { got: a, expect: b }); }
function pet(wx) {
  const s = S.newState(new Date(2026, 10, 2, 13, 0).getTime(), 7);
  s.stage = 'sprout'; s.growthSec = 0; s.needs.hunger = 40;
  S.setHourFn(() => 13); S.setWeatherFn(() => wx); S.setNowFn(() => new Date(2026, 10, 2, 13, 0).getTime());
  return s;
}
function sh(s) { const b = s.evo && s.evo.b5 && s.evo.b5.sprout; return b ? +b.shroom || 0 : 0; }

console.log('# config：霧唔係 "fog: 0.5" 字面，而係 route.fog.w');
ok(C.weather.route.fog && C.weather.route.fog.to === 'shroom' && C.weather.route.fog.w === 0.5, 'route.fog = { to:shroom, w:0.5 }', C.weather.route.fog);
ok(C.weather.route.overcast.w === 0.5 && C.weather.route.rain.w === 1 && C.kinds.feed.w === 0, '陰 0.5、雨 1、餵食本身 0');

console.log('# 13:00（唔喺晨露／月眠窗）');
{
  const play = pet('fog'); S.noteCare(play, 13, 'play');
  near(sh(play), 0.5, '霧天玩：菇傘 +0.5');
  near(play.evo.b5.sprout.ember, 1, '霧天玩：火苗仍然 +1');
  const feed = pet('fog'); S.feed(feed, 'meal');
  near(sh(feed), 0.5, '霧天餵：本身 0，天氣 +0.5');
  const twice = pet('fog'); S.noteCare(twice, 13, 'play'); S.noteCare(twice, 13, 'rinse');
  near(sh(twice), 1, '霧天兩次照顧：菇傘 +1.0');
  const clear = pet('clear'); S.feed(clear, 'meal');
  near(sh(clear), 0, '晴天餵：菇傘 0');
  const ov = pet('overcast'); S.noteCare(ov, 13, 'play');
  near(sh(ov), 0.5, '陰天玩：菇傘 +0.5（同霧）');
  const rain = pet('rain'); S.noteCare(rain, 13, 'play');
  near(sh(rain), 1, '雨天玩：菇傘 +1');
}
console.log('# 08:00 晨露窗：時段優先，霧唔再加菇傘');
{
  const s = pet('fog'); S.setHourFn(() => 8); S.noteCare(s, 8, 'play');
  near(sh(s), 0, '霧＋晨露：菇傘 0');
  near(s.evo.b5.sprout.tide, 1, '霧＋晨露：水珠 +1');
}
S.setHourFn(null); S.setWeatherFn(null); S.setNowFn(null);
console.log(`結果：${pass} 通過，${fail} 失敗`);
process.exit(fail ? 1 : 0);
