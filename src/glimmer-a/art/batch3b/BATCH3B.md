# Batch 3b 美術：③ 朋友訪客 ＋ ④ 進化大場面（俾遊程）

**生成日期**：2026-11-01（HKT）
**製作方法**：純 Pillow/numpy 程序生成，冇用 AI 圖。
**重跑**：`cd art-pet && python3 tools/build_batch3b.py && python3 tools/preview_batch3b.py && python3 tools/validate_batch3b.py`
**跟住嘅規格**：`docs-gdd/batch3-fun-spec.md`、`make-it-fun-v1.md`（v1.1）。

**所有數據都喺 `batch3b.json`**（version `batch3b-1`），呢份文件只係導讀。
`visit_pet_clips.json` 係團絨嘅 3a 格式 clip，可以直接 merge 入 3a 反應系統。

## 通用規則
- **座標**：全部用 art 1x 座標（195×422），時間單位係 ms。
  - 寵物 pivot 喺 art (97,292)。
  - 場景層係 223×446，offset (14,12)。
- **像素規格**：alpha 只有 0/255；每條 strip 最多 12 色（漫畫格豁免，見下面）。
  - 光暈全部由引擎畫（radial）。
  - `*_emissive.png` 係發光 mask：白色＝發光像素，可以做 additive 或者夜間唔受 lightmap 影響。
- **Strip 格式**：橫排，frameW × frames。
- **方向**：訪客面向右。行去左嗰陣引擎做 flipX，pivot.x 要鏡像（= W−1−x）。
- **Pivot 定義**：
  - 非懸空訪客：腳底最低實像素行 = pivot.y + 1。
  - 螢火小販懸空：pivot 係地影位置，地影由引擎畫。

## ③ 朋友訪客 `visitors/<id>/`

| id | 名 | frame | pivot | clips（每條 6 幀） | 錨點 head / bag | 專屬擺設 |
|---|---|---|---|---|---|---|
| snail_postman（先做） | 蝸牛郵差 | 44×37 | 22,34 | idle 180ms 循環／walk 120ms／happy 100ms×1 | 33,8 / 28,21 | deco_mailbox 郵筒仔 18×27 |
| mushroom_granny | 蘑菇婆婆 | 38×45 | 19,42 | 同上 | 19,4 / 19,31 | deco_mushroom_lamp 蘑菇夜燈 18×23（有 emissive） |
| firefly_vendor | 螢火小販 | 42×43 | 21,40（hover） | 同上，每條都有 `_emissive` | 25,6 / 8,22 | deco_firefly_jar 螢火瓶燈 14×22（有 emissive） |

**每位訪客嘅額外資產**：
- `_portrait.png`（26×26 圓形頭像，用喺 UI 或日記）
- `_badge.png`（18×18，友好度滿 5 嘅徽章）

**hitbox**：JSON `hitbox.rel`，相對 pivot。玩家拖禮物落去呢個框＝送禮。

**道具 `props/`**：
- `prop_letter` 13×10：信由 bag 錨點彈上頭頂，撳一下開一句日記。
- `prop_seed` 10×12。
- `friend_heart` 9×8×2：幀 0 係空心，幀 1 係實心；5 粒排一行，間距 10px。

**流程**：喺 `visitRules` 入面，包括出現條件、小販時段 17:00–07:00、入場位置、帶路 loop（8s、followGap 30）、送禮、友好度 5 → 擺設＋徽章、離場。

**團絨嘅 3a clip**（喺 `petClips3aFormat`，同 `visit_pet_clips.json` 一樣）：
- `visit_lead_start`
- `visit_lead_strut`（循環，引擎沿 path 郁）
- `visit_gift_cheer`（用 3a fx_heart）

新蛋 24 隻用 3a rig。舊 evo 形態行路就用 atlas 嘅 `walk_happy` 幀，配 smug 面。

## ④ 進化大場面 `evo/` ＋ `cards/`

**時間軸**：喺 `evolution.timeline`，全長 8000ms，2000ms 之後可以 skip。
- 撳 skip 會直接跳去 5600 現身，再過 300ms 出名卡。
- 如果有小遊戲或者拖動進行緊，先排隊，做完先播。
- 參考實現：`tools/preview_batch3b.py` 入面嘅 `evo_render(t, old, new, scene)`。逐條 track 照抄就得。

| ms | 發生乜 | 資產 |
|---|---|---|
| 0–600 | 畫面變暗 #1E1630 α0→0.7，HUD 收起 | 引擎 |
| 300–1500 | 寵物震＋surprised 面 | 3a |
| 400–2200 | 14 粒光點螺旋吸入 | evo_mote 7×7×3 |
| 900–1500 | 剪影同原色交替閃 | 引擎 source-in |
| 1500–2700 | 光繭成形 | evo_cocoon_form 64×72×6，pivot 32,68 放喺寵物 pivot |
| 2700–3900 | 光繭心跳（越跳越快） | evo_cocoon_pulse ×4 ＋ body sx/sy |
| 3900–4400 | 爆裂 | evo_cocoon_crack ×4 |
| 4400– | 碎片 ×8、光環、光芒 | evo_shard 6×6×3、evo_ring 96×96×5、evo_rays 112×112×6（z=back） |
| 4400–5600 | 新舊剪影互換 15 次，越換越快 | 引擎剪影，**要加 1px 描邊 #967EDC**，唔係會同 rays 溶埋 |
| 5600 | 白閃，新形態現身，squash 彈，smug 面，跟住 celebrate | — |
| 5600–7400 | 彩紙 28 片 | evo_confetti 7×7×8（4 款，每款 2 幀） |
| 6000–7700 | 名卡彈出，中心 (97,352)，用 MOTION.md sticker pop | cards/card_<route>.png 168×64 |
| 2000– | skip 提示（右下角腳印） | evo_skip_hint 15×15×2 |

**名卡**：
- 文字由引擎畫：名字框 `textBoxes.name` [66,9,158,25]，白字；介紹框 `line` [66,31,158,55]，打字效果每字 30ms。
- 頭像位：圓心 (33,32)，半徑 25。新形態 idle 幀 0 嘅 pivot 對準 petPivot (33,54)，可以凸出圓框，係故意嘅。
- `formToCard` 列明每個形態用邊張卡：dot/sprout/hop 用 `card_base`；guard_* 同 still_* 用自己路線嘅卡。`formName` 讀 atlas `meta.name`。

**進化前兆**（`evolution.omens`，達門檻前最後 24h 隨機一款）：
- `flicker`：冇新圖，引擎疊剪影色。
- `appetite`：冇新圖，食量 ×1.5，配 line 事件。
- `dream`：瞓覺時每 20s 喺 headTop 出 `omen_dream_bubble` 34×34×3，夢中心 (19,13)。入面放 `omen_dream_icons` 12×10×6 其中一個：四方太陽／戴帽魚／飛鞋／行路茶杯／倒轉月／蛋糕山。

## 四格漫畫 `comics/`
- **格仔尺寸**：每格 92×84（內框 86×78 加 sticker 邊）。日記頁 2×2 排位、字幕框位置見 `comics.layout`。
- **數量**：5 個進化節點 × 4 格 = 20 款設計。跟路線變嘅格會 9 條路線各出一張，總共 60 張 PNG：
  - `n4_p4_<route>`
  - `n5_p1..p4_<route>`
- **字幕**：由引擎畫。`captionDraft` 係我寫嘅粵語草稿，**要遊策改**；`{route}` 會換做 `routeZh`。
- **色數豁免**：漫畫背景係由 HD-2D 場景裁出嚟，所以超過 12 色。呢點已經喺驗證入面註明豁免。

## 我自己決定嘅詮釋（規格冇講清楚嘅地方）
1. 每位訪客 1 件專屬擺設，總共 3 件。螢火小販賣嘅擺設規格冇列，所以冇畫。
2. 「9 張名卡」理解為 9 條路線各一張，另外加多張中性 `card_base` 俾 dot/sprout/hop 用。
3. 漫畫 20 款設計，跟路線變嘅格逐條路線預先 bake 好（60 張）。
4. 徽章、友好心、頭像係額外加嘅小圖。

## 已知問題
- n3_p2（撻低）只係用舊 atlas 嘅 droop 幀，冇專門畫撻低動作。
- 光繭 pulse 嘅織紋喺 1x 可能有啲密，唔啱可以減 stripes。
- 進化期間寵物用 1x 原大，冇做鏡頭 zoom；想再誇張啲可以由引擎 scale 1.5（pixel 會變粗）。
- `visit_lead_strut` 只係用喺新 24 隻；舊形態用 atlas walk_happy。

## 預覽
`batch3b_overview_4x.png`、`comics_overview_2x.png`、`comics_route_variants_2x.png`，加上 `preview/` 入面：
- `visit_*_3x.gif`
- `visitors_idle_walk_happy_4x.gif`
- `evolution_hop_to_guard_ember_2x.gif`
- `evolution_guard_moon_to_still_moon_2x.gif`
- `evolution_keyframes_2x.png`
- `omen_dream_4x.gif`
- `diary_page_n1_2x.png`

**驗證**：`tools/validate_batch3b.py`，結果寫入 `check/validation.json`。
