# 6c 夢境草稿（第三輪，未選定）

對 `long6c.js` @ `4f66a834`。QA 建議，冇推進 code branch。

第三輪有四組全部達標，未揀：

- 20% 再 1 片，修1＋修2a
- 20% 再 1 片，修1＋修2b
- 30% 再 1 片，修1＋修2a
- 30% 再 1 片，修1＋修2b

40% 四條勤力線中位 72–73，低過 75。修1 單獨時疏玩卡喺玩具房。呢五組唔寫進改法。

四組共用下面 A／B／C、修1、片數。玩具房只差修2a 定修2b。

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

`st()` 第 52 行加 `bank`、`bankNight`。一晚完都冇入先加銀行，上限 1。補做成功先減。當夜只用最後一個 ≥19:00 的上線入一次。

`weights` 第 73 行，湖：

```diff
   function weights(F) {
-    const w = { forest: Math.min(CFG.wMax, F.meal), lake: Math.min(CFG.wMax, F.rinse), toy: F.play >= CFG.playMany ? Math.min(CFG.wMax, F.play) : 0, star: 1 };
+    const lake = (F.feed ? 1 : 0) + (F.rinse ? 1 : 0) + (F.poop ? 1 : 0) + (F.mg ? 1 : 0);
+    const w = { forest: Math.min(CFG.wMax, F.meal), lake: Math.min(CFG.wMax, lake), toy: toyWeight(F), star: 1 };
     for (const k of THEMES) if (!(w[k] > 0)) delete w[k]; return w;
   }
```

`nightFacts`（第 70 行已經把 `play` 同 `mg` 加進 `F.play`）要再交 `feed／poop／mg`。

## 修2a（玩具房門檻）

門檻而家係第 20 行 `playMany: 2`，第 73 行 `F.play >= CFG.playMany`。`F.play` 已經包含小遊戲，所以「玩或小遊戲 ≥1」就係 `>= 1`。

```diff
-    toy: F.play >= CFG.playMany ? Math.min(CFG.wMax, F.play) : 0,
+    toy: F.play >= 1 ? Math.min(CFG.wMax, F.play) : 0,
```

## 修2b（玩具房最低權重 1）

同樣改第 73 行，唔再睇第 20 行 `playMany`：

```diff
-    toy: F.play >= CFG.playMany ? Math.min(CFG.wMax, F.play) : 0,
+    toy: Math.max(1, Math.min(CFG.wMax, F.play)),
```

## 修1 同每晚片數

`plan` 第 89 行而家派 `CFG.frags`（6）片，每個未排除的主題至少 1。改成先 1 片，再按 p 加 1 片；每片之前剔走已齊 5 張的主題。四主題都齊就唔出片。

20% 同 30% 都達標，p 未鎖定。

```diff
+  function fragCount(rng, p2) { return 1 + (rng() < p2 ? 1 : 0); }
+  function openWeights(s, F) {
+    const w = weights(F);
+    for (const k of THEMES) if (themeCards(s, k).length >= CFG.cardsPerTheme) delete w[k];
+    return w;
+  }
+  function drawTheme(w, rng) {
+    const ks = THEMES.filter(k => w[k] > 0); let tot = 0; for (const k of ks) tot += w[k]; let u = rng() * tot;
+    for (const k of ks) { u -= w[k]; if (u <= 0) return k; } return ks[ks.length - 1];
+  }
+  function nightFrags(s, F, rng, p2, now) {
+    if (!Object.keys(openWeights(s, F)).length) return [];
+    const n = fragCount(rng, p2), out = [];
+    for (let i = 0; i < n; i++) {
+      const w = openWeights(s, F); if (!Object.keys(w).length) break;
+      const th = drawTheme(w, rng); out.push(th);
+      pick(s, th, now); // 必須先入卡，下一片先剔得走剛齊的主題
+    }
+    return out;
+  }
```

`pick` 唔入錢包。`SHARD_DAILY_TOTAL_CAP` 維持 47。
