#!/usr/bin/env node
/* 6 時間表 × 7 日星星碎。動作每次都做。懸浮星星碎預設開：每日最多 5 粒。 */
'use strict';
const path = require('path');
const root = process.env.ROOT || '/tmp/glimmer-s12/src/glimmer-a/src';
const S = require(path.join(root, 'sim.js'));
const X = require(path.join(root, 'systems.js'));
const SCHED = {
  勤力: { hours: [8, 11, 14, 17, 20], acts: ['feed', 'play', 'rinse', 'poop'] },
  普通: { hours: [8, 13, 19], acts: ['feed', 'play', 'poop'] },
  疏玩: { hours: [20], acts: ['feed', 'play'], everyOtherDay: true },
  夜貓: { hours: [18, 22, 0, 1], acts: ['feed', 'play'] },
  早起: { hours: [6, 7, 8, 12], acts: ['feed', 'rinse', 'play'] },
  餵食狂: { hours: [9, 12, 15, 18], acts: ['feed', 'feed', 'feed', 'play'] },
};
const T0 = new Date(2026, 10, 2, 0, 0, 0).getTime();
function med(a) { const b = a.slice().sort((x, y) => x - y); return b[b.length >> 1]; }
const out = {};
for (const name of Object.keys(SCHED)) {
  const sc = SCHED[name];
  let now = T0 + 8 * 3600e3;
  S.setNowFn(() => now); S.setHourFn(() => new Date(now).getHours()); S.setWeatherFn(() => 'clear');
  const s = S.newState(now, 11);
  s.stage = 'sprout'; s.growthSec = 0; s.needs.hunger = 40; s.ev = [];
  const days = [];
  for (let d = 0; d < 7; d++) {
    const dayStart = T0 + d * 864e5;
    if (!(sc.everyOtherDay && d % 2)) {
      for (const h of sc.hours) {
        now = dayStart + h * 3600e3;
        if (s.sleeping) S.toggleSleep(s);
        s.needs.hunger = Math.min(s.needs.hunger, 50);
        for (const a of sc.acts) {
          if (a === 'feed') S.feed(s, 'meal');
          else if (a === 'play') S.play(s);
          else if (a === 'rinse') S.rinse(s);
          else while (s.poops > 0) S.clearPoop(s);
        }
      }
    }
    now = dayStart + 23 * 3600e3;
    X.questTick(s, now, s.ev);
    const drops = [];
    for (let i = 0; i < 5; i++) drops.push({ k: 'drop', t: dayStart + (8 + i * 3) * 3600e3 });
    X.applyOverlay(s, drops, now, s.ev);
    days.push(X.wallet(s, now).today);
  }
  out[name] = { days, med: med(days) };
}
S.setNowFn(null); S.setHourFn(null); S.setWeatherFn(null);
console.log(JSON.stringify(out, null, 2));
