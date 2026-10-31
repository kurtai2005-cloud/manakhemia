# EVENT_ICONS（事件 icon／小 FX 對照表）

32x32、置中 pivot (16,16)、PNG-24 RGBA、無抗鋸齒、alpha 0/255、只用團絨色盤（`sprites/tuanrong/palette.json` 31 色，已驗證）。全程式化（`tools/build_event_icons.py`），可重跑。

- `icon_<id>.png`：靜態單幀 icon（＝動畫第 1 幀）。`<id>_NN.png`：動畫幀。`atlas_events.png/json`：全部幀（padding 2、extrude 1、1024 寬，`animations` 內有 fps／loop）。`<id>_8x.gif` 預覽、`contact_events.png` 總覽。

| id | 中文名 | 事件 | 幀數 | fps | loop | 設計 | 靜態檔 | 動畫幀 |
|---|---|---|---|---|---|---|---|---|
| `gift_return` | 帶禮物回來 | 事件 1 | 3 | 4 | 是 | 禮物盒＋紅絲帶蝴蝶結，盒口飄出光粒（回歸禮物＝光粒） | `icon_gift_return.png` | `gift_return_01`–`gift_return_03` |
| `butterfly` | 蝴蝶訪客 | 事件 2 | 4 | 8 | 是 | 紫身粉翼蝴蝶，4 幀拍翼 | `icon_butterfly.png` | `butterfly_01`–`butterfly_04` |
| `meteor_night` | 流星夜 | 事件 3 | 4 | 6 | 是 | 金色流星帶漸隱尾巴斜落，夜空小星閃爍 | `icon_meteor_night.png` | `meteor_night_01`–`meteor_night_04` |
| `rainbow` | 雨後彩虹 | 事件 4 | 3 | 4 | 是 | 六色彩虹拱＋兩朵雲＋雨滴，高光沿彩虹游走 | `icon_rainbow.png` | `rainbow_01`–`rainbow_03` |
| `sleep_talk` | 夢話 | 事件 5 | 3 | 3 | 是 | 對話氣泡內有月牙同閃星，底部「…」逐點亮起 | `icon_sleep_talk.png` | `sleep_talk_01`–`sleep_talk_03` |
| `tantrum` | 鬧脾氣 | 事件 6 | 3 | 6 | 是 | 漫畫式紅色怒筋（四瓣）＋四角冒煙，脈衝放大 | `icon_tantrum.png` | `tantrum_01`–`tantrum_03` |
| `treasure` | 尋寶 | 事件 7 | 3 | 4 | 是 | 寶箱，蓋逐幀掀起，箱內光芒同青色寶石升起 | `icon_treasure.png` | `treasure_01`–`treasure_03` |
| `shiny_day` | 閃光日 | 事件 8（3%） | 4 | 6 | 是 | 大四芒星＋四粒衛星閃爍，帶虛線光暈 | `icon_shiny_day.png` | `shiny_day_01`–`shiny_day_04` |
| `firefly_walk` | 螢火散步 | 傍晚事件（新增） | 4 | 5 | 是 | 螢火蟲：發光腹部（脈衝光暈）＋半透明翅＋四周漂浮光點 | `icon_firefly_walk.png` | `firefly_walk_01`–`firefly_walk_04` |

用法：事件彈出時引擎放 icon 於觸發點／寵物頭頂，播 `animations[id]`；整數倍放大、Nearest。icon 不烙陰影，bloom 由引擎對 glow 色做（threshold 0.7）。
