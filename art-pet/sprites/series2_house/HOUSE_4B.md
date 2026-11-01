# 4b 屋仔 — 交俾遊程

一切數據喺 `house.json`（slots／furniture／walk／duo／ui），動作喺 `actions/actions_house.json`。純 Pillow/numpy 程序生成，冇 AI 圖。
重跑：`cd art-pet && python3 tools/build_house_4b_actions.py && python3 tools/build_house_4b.py && python3 tools/build_house_4b_ui.py && python3 tools/build_house_4b_preview.py && python3 tools/validate_house_4b.py`

## 1. 房間（HD-2D 場景格式，同 scenes/hd2d/FORMAT.md）
- `room/day/`、`room/night/`：sky／far／mid／fore（223×446，art＋(14,12)）＋ raw/、lightmap、light_add、emissive、emissive_blur、vignette(195×422)、grade.json、palette.json。
- 窗洞喺 far 層透明（art (30,98)–(76,150)），窗外景喺 sky 層；日夜同花園一樣 19:00／06:00 crossfade。
- 視差建議：sky 0.5、far/mid 1.0（牆同地板唔好錯開）、fore 1.3。
- 上面 0–52 留俾 HUD，下面 322 以下留俾 UI。

## 2. 擺位（6 個 slot，art 座標）
| slot | anchor | 層 | sprite pivot |
|---|---|---|---|
| window 窗 | (53,124) 窗洞中心 | wall | 窗洞中心 |
| wall 牆 | (140,104) | wall | 中心 |
| lamp 燈 | (26,254) | ysort | 底中 |
| bed 床 | (138,264) | ysort | 底中；`_front.png`（被）另一層 |
| table 檯 | (44,308) | ysort | 底中 |
| rug 地氈 | (100,290) | floor | 中心 |

畫法：sprite 左上＝anchor − pivot。家具同寵物一樣唔過 LUT，× ambientTint（寵物再 × petTint）。燈夜晚用 `_glow.png` lighter 疊（中心＝glowCenter，glow 係唯一 8-bit alpha）；`_emissive.png` 入 bloom。bed／table／lamp 有地面影（`shadow` 橢圓 w,h，#3c2428 α70）。

畫序：sky → far → window/wall → mid → rug → 影 → ysort（燈、床 back、檯、寵物按 sortY）→ 床 front（sortY＝床 y＋0.1）→ fore → lightmap → light_add → bloom → 燈 glow → fog → vignette → UI。

初始全部空位；每件第一次擺心情 +1；換擺唔使碎。

## 3. 家具 12 件（價錢係美術建議，遊策可改）
| id | slot | 名 | 價／來源 |
|---|---|---|---|
| bed_leaf | 床 | 葉仔床 | 35 碎 |
| bed_cloud | 床 | 雲朵床 | 40 碎 |
| table_stump | 檯 | 樹樁檯 | 20 碎 |
| table_round | 檯 | 格仔布圓檯 | 25 碎 |
| wall_shelf | 牆 | 小盆栽層架 | 18 碎 |
| wall_frame | 牆 | 團絨相框 | 委託獎 |
| rug_round | 地氈 | 粉粉圓地氈 | 22 碎 |
| rug_leaf | 地氈 | 葉仔地氈 | 15 碎 |
| win_curtain | 窗 | 蕾絲窗簾 | 25 碎 |
| win_star | 窗 | 星星窗 | 委託獎 |
| lamp_mushroom | 燈 | 蘑菇燈 | 蘑菇婆婆友誼 5 |
| lamp_firefly | 燈 | 螢火瓶燈 | 螢火小販友誼 5 |

商店 8 件共 200 碎。預覽組合：A 森林組、B 夢幻組（`house.json sets`）。

## 4. 寵物喺屋入面
- 行走區 pivot（腳底）x 22–174、y 262–318，減去有擺嘅 bed／table／lamp blocker。1x 唔縮放，向左 flipX，10px/s，每 4–9 秒閒逛。
- 動作 `actions/<form>_{sit,prank_do,prank_got}.png`：細佬 34 階段＋團絨 25 形態全部有（177 條 strip）。
  - sit 6×150ms，0–1 坐落、2–5 loop。
  - prank_do／prank_got 8×120ms，第 4 格一齊「哇」；strip 有 padding（左右 4、頂 14），用 json 入面每條嘅 pivot。
- 行／idle／瞓：細佬用 4a `series2/actions`，團絨用現有 evo clip。撳寵物＝3a 觸摸反應。

## 5. 雙人（house.json duo）
- **sit_together**：地氈 anchor ±18、+2，面對面坐，每 2.4 秒中間出心心。
- **sleep_same_bed**：床 anchor＋sleepSpots (−20,−12)／(+20,−12)；順序 床 back → 團絨 → 細佬 → 床 front（被遮下半身）＋ fx_zzz。21:00–03:00。冇床就 fallback 4a sleep_together（地氈位＋ov_blanket）。
- **prank**：整蠱人企喺 victim 後面 30px，0–2 格每格 +2px，第 4 格兩條 strip 同時彈；完咗 victim 轉身，兩隻 sit 一輪再散。每日最多 3 次，唔加親密。

## 6. UI（只做 HD-2D；Kurt 揀咗 HD-2D，B2 版冇整）
- `ui/layout.json`（＝house.json `ui`）有全部位置。零件 `ui/*@3x.png`：icon 12 個、花園入口掣（正常／上鎖）、6 slot tab（idle／sel）、pin（＋／已擺 × idle／sel）、sheet 底板、卡 5 種狀態示範（擺緊／擁有／買／上鎖／收起）、完成、佈置、返回。
- 花園入口：委託掣下面 (178,104)，未做家人＝灰＋鎖。
- 屋仔平時：左上返回、標題「屋仔」、右下「佈置」。
- 佈置模式：房間上移 36、底部 sheet（y 280–418）：6 tab → 每 slot 2 件＋收起卡 → 完成；房入面每 slot 一個 pin，撳 pin 跳 tab。買嘢用現有 HD popup 確認。卡入面家具縮圖用 nearest 整數倍。

## 7. 預覽
`preview/room_setA_3x.png`、`room_setB_3x.png`（日＋夜）、`room_empty_day_3x.png`、`living_two_pets_3x.png`（行／坐埋／同床瞓）、`decorate_ui_HD2D_3x.png`（5 個畫面）、`ui_parts_HD2D_3x.png`、`house_two_pets.gif`（行 → 坐埋 → 整蠱）。

## 8. 待確認
- 價錢、邊個訪客／委託送邊件係美術建議，要遊策／遊測確認。
- 初始空房（冇預設家具），要唔要送一張床？
