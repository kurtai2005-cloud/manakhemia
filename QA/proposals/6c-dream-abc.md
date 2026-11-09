# 6c 夢境 A+B(1)+C 草稿（第二輪片數）

對 `long6c.js` @ `4f66a834`。QA 建議，冇推進 code branch。

第二輪（`QA/qa-econ-6c-dream.md`）：每晚 1 片，30% 同 40% 再加 1 片。兩個都未達標（疏玩 0／200；勤力等中位 124–159，目標 75–110）。**唔鎖定百分比。**

`canEnter` 第 57 行：

```diff
   const inHours = (h) => h >= CFG.hours[0] || h < CFG.hours[1];
+  const AFTER = 19;
+  const inLate = (h) => h >= AFTER || h < CFG.hours[1];
+  const BANK_CAP = 1;
   function canEnter(s, now, h) {
     if (h == null) h = hourOf(now);
     if (!s || s.stage === 'egg') return { ok: false, why: 'egg' }; if (kidMain(s)) return { ok: false, why: 'km' };
     if (!s.sleeping) return { ok: false, why: 'awake' };
-    if (!inHours(h)) return { ok: false, why: 'hours' };
+    const o = st(s);
+    if (!inHours(h) && !inLate(h)) {
+      if ((o.bank | 0) > 0) return { ok: true, why: 'bank', night: o.bankNight || nightKey(now, h) };
+      return { ok: false, why: 'hours' };
+    }
     if (st(s).night === nightKey(now, h)) return { ok: false, why: 'done' };
     return { ok: true, why: 'ok', night: nightKey(now, h) };
   }
```

`st()` 第 52 行要加 `bank`、`bankNight`。一晚完都冇入先 `bank = min(BANK_CAP, bank+1)`。補做成功先減。當夜只可以用最後一個 ≥19:00 的上線入一次。

`weights` 第 73 行：

```diff
   function weights(F) {
-    const w = { forest: Math.min(CFG.wMax, F.meal), lake: Math.min(CFG.wMax, F.rinse), toy: F.play >= CFG.playMany ? Math.min(CFG.wMax, F.play) : 0, star: 1 };
+    const lake = (F.feed ? 1 : 0) + (F.rinse ? 1 : 0) + (F.poop ? 1 : 0) + (F.mg ? 1 : 0);
+    const w = { forest: Math.min(CFG.wMax, F.meal), lake: Math.min(CFG.wMax, lake), toy: F.play >= CFG.playMany ? Math.min(CFG.wMax, F.play) : 0, star: 1 };
     for (const k of THEMES) if (!(w[k] > 0)) delete w[k]; return w;
   }
```

`nightFacts` 要多交 `feed／poop／mg`。

每晚片數唔再係 `CFG.frags`（6）。抽主題，湖只係權重其中一項：

```diff
+  // 30% 同 40% 模擬都未達標，P2 未鎖定。
+  function fragCount(rng, p2) { return 1 + (rng() < p2 ? 1 : 0); }
+  function drawTheme(w, rng) {
+    const ks = THEMES.filter(k => w[k] > 0); let tot = 0; for (const k of ks) tot += w[k]; let u = rng() * tot;
+    for (const k of ks) { u -= w[k]; if (u <= 0) return k; } return ks[ks.length - 1];
+  }
+  function nightFrags(F, rng, p2) {
+    const w = weights(F), n = fragCount(rng, p2), out = [];
+    for (let i = 0; i < n; i++) out.push(drawTheme(w, rng));
+    return out; // 唔好喺呢度再加湖片
+  }
```

`pick` 唔入錢包。`SHARD_DAILY_TOTAL_CAP` 維持 47。
