# 6c 夢境 A+B(1)+C 草稿

對 `long6c.js` @ `4f66a834`。呢份只係 QA 建議，冇推進 code branch。

模擬（`QA/qa-econ-6c-dream.md`）：存 2 晚同存 1 晚，夜貓中位都係 25、P10 24，低過目標 60／45。草稿用存 1 晚。日數目標仍然未達（勤力等中位約 25，目標 75–110）。每晚 4 片、湖每晚最多 1 片、19:00 改 18:00 三個單改都未入帶。未選定。

`canEnter` 而家喺第 57 行：要瞓緊，而且鐘數要喺 21:00–03:00。

```diff
   const inHours = (h) => h >= CFG.hours[0] || h < CFG.hours[1];
+  const AFTER = 19; // A：19:00 後最後一次上線都當入夢
+  const inLate = (h) => h >= AFTER || h < CFG.hours[1];
+  const BANK_CAP = 1; // B：錯過存起。存 2 晚模擬過，夜貓唔再慢，改 1
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

銀行要喺「一晚完咗都冇入」時 +1，上限 `BANK_CAP`，補做成功 −1。`st()` 而家第 52 行只留 `night／frag／cards／furn／log／n`，要加 `bank`、`bankNight`，否則 sanitize 會刪走。UI 用當夜最後一個 ≥19:00 的上線叫 `enter`，唔好每個上線都入（每晚 1 夢）。

`weights` 而家喺第 73 行，湖只計淋水。

```diff
   function weights(F) {
-    const w = { forest: Math.min(CFG.wMax, F.meal), lake: Math.min(CFG.wMax, F.rinse), toy: F.play >= CFG.playMany ? Math.min(CFG.wMax, F.play) : 0, star: 1 };
+    // C：餵食、淋水、執屎、小遊戲，每樣當日最多 +1。總片數仍然 CFG.frags（6），分配公式唔改。
+    const lake = (F.feed ? 1 : 0) + (F.rinse ? 1 : 0) + (F.poop ? 1 : 0) + (F.mg ? 1 : 0);
+    const w = { forest: Math.min(CFG.wMax, F.meal), lake: Math.min(CFG.wMax, lake), toy: F.play >= CFG.playMany ? Math.min(CFG.wMax, F.play) : 0, star: 1 };
     for (const k of THEMES) if (!(w[k] > 0)) delete w[k]; return w;
   }
```

`nightFacts`（第 65 行）要多交 `feed／poop／mg` 旗，先至餵到上面個權重。而家只得 `meal／rinse／play`。`pick` 唔好加錢包；`SHARD_DAILY_TOTAL_CAP` 維持 47。
