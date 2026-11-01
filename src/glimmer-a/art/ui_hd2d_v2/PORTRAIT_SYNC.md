# 頭像同步（B ×2 面部近鏡 → A 頂旗頭像槽）— 遊美 → 遊程

> 2026-11-02。資料：`portrait/portrait_rects.json`（version 2）；示範：`portrait/portrait_cases_3x.png`；出數程式：`ui_hd2d_v2_kit.py` 嘅 `portrait_rects()`。

## 1. 基本裁位
- 合成 canvas＝寵物 frame 四邊加 PAD 8（`pad`＝8）。所有座標用呢個 canvas 嘅 sprite px。
- 裁一個 **22×22** 正方（`n`＝22），**×2 nearest → 44×44**，放入 `portrait_frame`（52×52、斜角 5、邊 4px、窗 44×44 @4,4）。
- 中心＝兩眼中點：`rect = [round(ex − 11), round(ey − 11), 22]`（`eyefrac`＝0.5，眼喺窗正中）。
- 底層：`portrait_bg_<心情>`（normal／happy／hungry／sleepy／sick／sleep），再疊寵物，再用 `portrait_mask` 裁斜角，最後疊框；心情 ≠ normal 時右下加 `mood_badge_<心情>`。
- 用嗰格 frame：idle 第 1 格（呼吸動畫要跟住郁就每格用同一 rect；rect 唔跟 frame 郁，寵物喺框入面輕微上落係預期效果）。

## 2. 戴飾品：shift → pop → badge
每個 form × 每件飾品已預計好 `acc.<key>` = `{shift, pop, cut, vis, h, badge}`：
1. **need**＝飾品最頂一行高出裁位頂幾多行（只計裁位闊度內嘅飾品 px；用「有飾品 − 冇飾品」差異搵，唔係搵第一粒唔透明 px）。
2. **shift**＝min(need, 4)：裁位向上移，`y0 −= shift`（眼由 50% 跌到最多 68%，仍然係面部近鏡）。
3. **pop**＝min(need − shift, 3)：框頂外面**多畫 pop 行**（×2 ＝ 最多 6 device-art px），穿過框頂邊。**pop 區只畫飾品 px**（用冇飾品 canvas 做 diff），身體 px 唔畫出框，所以闊身形態唔會遮住成條框頂。
4. **cut**＝剩低仲出界嘅行數（就咁裁走）。
5. **badge**＝`need > 0` 而且可見部分 `vis < max(3, h × 0.5)`：飾品大部分睇唔到 → 頭像右上角加 `med13_paper` 細章＋`acc_thumb_<key>`（11px 飾品縮圖，由飾品原圖多數色縮）。
6. 頸飾（領巾、鈴、葉領）喺框底以下：唔處理（`note` 有寫）。

runtime 偽碼：
```
r = rects.forms[form]; x0,y0,n = r.rect; a = r.acc.get(key)
if a: y0 -= a.shift
draw bg, crop(pet_with_acc, x0, y0, n) ×2, mask, frame
if a and a.pop: draw rows [y0-a.pop, y0) of (pet_with_acc − pet_bare) ×2 above frame top
if a and a.badge: draw med13_paper + acc_thumb_<key> at frame top-right
```

## 3. 飾品 key
- 舊線（團絨 old line，25 form）：14 件 — acorn beanie bell bow cherry crown glasses halo leafcollar nightcap sakura scarf starclip straw；用 `compose_accessory_runtime` 即場合成（idle 全部格取最大範圍）。
- from_ref 48 線（新蛋線 A1–H3，24 form）：`wear_hat`、`wear_glasses`。
- 5b 工作帽：`hat_chef`、`hat_garden`、`hat_post`、`hat_watch` — 用 `sprites/series2_long/5b/long_5b.json` 嘅 t1 idle 行，**按 pivot 對齊**（帽 row.pivot 對寵物 pivot），喺加高 40px 嘅 canvas 量頂，所以高帽都量得準。
- series2 細佬（10 form）：冇飾品，只有 rect。

## 4. Alias（細佬 S3／S5／S6）
S3X → X1、S5X → X2、S6X → X3（X＝A…H，共 24 個）：細佬長大用返 from_ref 1／2／3 階 sprite，所以直接用嗰個 form 嘅裁位同飾品值。S5／S6 會有工作帽 → 查 `hat_*`。

## 5. 統計（今次出數）
- 59 form（old 25 + from_ref 24 + series2 10）＋ 24 alias；498 個飾品值；hidden 0。
- 需要 shift：382；需要 pop：319；仍有 cut：238（多數係高帽頂少少，badge 冇觸發即係睇得出）。
- badge 89：halo 23、hat_watch 15、hat_chef 13、hat_garden 11、hat_post 8、nightcap 5、beanie 3、crown 3、wear_hat 3、acorn 2、straw 2、starclip 1。
- 光環（halo）係浮喺頭頂上面，大形態多數要 badge，係預期。

## 6. 已知取捨
- 大形態（光光、軟軟等 radiant 系）喺 n＝22 會好近鏡（只見塊面），跟 B 版設計接受。
- 如果將來想少啲 badge：可以將 `maxPop` 由 3 加到 4（框頂再出 2px），validator 限制要一齊改。

## 7. 示範
`portrait/portrait_cases_3x.png`：8 個 case：冇飾品、蝴蝶結、皇冠（shift 3）、睡帽（shift 4＋pop）、新線帽 wear_hat（A2）、守夜帽 pivot 對齊（A3）、光環 → 細章（radiant）、細佬 alias S5B＋廚師帽。每格頂有 `s<shift> p<pop>（章）` 標示。
