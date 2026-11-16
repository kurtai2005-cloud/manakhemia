# SOURCE_MAP（art r1）

說明：重用檔係**原像素拷貝**（真實 32×32；檔名 @3x 唔代表 96px）。新畫只補語意缺口同低干擾 chrome，唔大量重畫。r1.1 撤下糖果，第4掣改為新手掌「摸」。淋水素材仍保留，mapping pending。kit_hd2d_v3 **整體 UI 版面已取消**，只借個別圖形，唔搬舊版面。

## 重用（原檔拷貝）

| 本包檔 | 語意 | 來源（真實 32×32） | SHA-256 |
|---|---|---|---|
| `assets/icons/icon_care_feed_32.png` | 餵 | `kit_hd2d_v3/icons/feed@3x.png` | `fa2ed8cb02ddd043…8568ab54` |
| `assets/icons/icon_care_water_32.png` | 淋水 | `kit_hd2d_v3/icons/water@3x.png` | `7ba8dc579b5241a6…5dd7e965` |
| `assets/icons/icon_need_eat_32.png` | 想食 | `m1_icons/icons/need_eat@3x.png` | `ed4d0f24add4ff7d…bdea023e` |
| `assets/icons/icon_need_play_32.png` | 想玩 | `m1_icons/icons/need_play@3x.png` | `bfac3674a931265a…309be865` |
| `assets/icons/icon_need_sleep_32.png` | 想瞓 | `m1_icons/icons/need_sleep@3x.png` | `5e755eacaf116699…9b0c6e72` |
| `assets/icons/icon_need_pet_32.png` | 想摸 | `m1_icons/icons/need_pet@3x.png` | `903d49e5f598986d…a888281e` |

完整哈希見 `tools/_src_map.tsv` 同 `MANIFEST.txt`。

## 新畫（最小必要）

| 本包檔 | 點解要新畫 | 尺寸 |
|---|---|---|
| `icon_care_pat_32.png` | r1.1：摸（張開手掌）。現成 pal／球唔合適當操作掣：`need_pet` 係想摸氣泡；`d_paw` 係掌印不是手掌；`ev_play` 係事件球，且玩無玩家入口。故最小新畫 32px，kit 風格描邊。SHA-256 `d5c5a9c12b93c9ea738c806a41b3930ae6f10eff8a2cbe7a54c3427e96f32831` | 32×32 |
| `icon_care_poop_32.png` | 執屎無正確原 icon（見下「不用」） | 32×32 |
| `icon_admire_32.png` | 找不到欣賞／觀察眼睛圖示 | 32×32 |
| `frames/btn_plate_40_{normal,pressed,disabled}.png` | 舊整體 UI 已取消，要低干擾可淡出底板 | 40×40 |
| `frames/bubble_need_quiet_48.png` | 今輪唔搬 64×56 V3-A 框；可選安靜框，優先仍係 32px M1 icon | 48×48 |
| `frames/panel_9slice_24.png` 及 `assets/svg/*` | 可選九宮格／SVG 參考，唔當像素正本 | 24×24 / SVG |
| `buttons/btn_*_{normal,pressed,disabled}.png`（第4掣檔名 `btn_care_pat_*`，已無 `btn_care_play_*`） | 底板＋圖示合成，方便接入 | 40×40 |
| `bubbles/bubble_need_{eat,play,sleep,pet}.png` | 安靜框＋原 32px need icon（光學置中，無拉伸） | 48×48 |

新圖風格：沿用 kit 紫褐描邊 `(36,23,44)`、暗暖底板、暗金褐邊，避免同夜景暖燈搶光。

## 不用（語意不對或今輪明確唔搬）

| 檔 | 真實像素 | 原因 |
|---|---|---|
| kit `play@3x.png`（粉紅糖果／蛋糕） | 32×32 | **r1 曾誤用為玩／摸，已撤。** 一眼只會讀成食物，唔再硬映射 |
| M1 `ev_play`（藍球） | 32×32 | 事件「玩」球形；本掣改為手掌「摸」（玩無明確玩家入口），故不用 |
| kit `d_paw` | 32×32 | 掌印，唔係手掌 |
| kit `clean@3x.png` | 32×32 | 水滴，會同「淋水」衝突，**唔係**執屎 |
| M1 `ev_rain` | 32×32 | 事件「雨」，唔係淋水操作 |
| M1 `need_*` 當照顧掣 | 32×32 | 係「想要」表徵，唔自動當操作 icon（本包只用於泡泡）。`need_pet` 手掌＋心係想摸，**唔當**摸操作掣 |
| `art/m1-icons/bubble_need*.png`、`m1_icons/bubbles/need_*@3x.png`、`bubble_need@3x.png` | **64×56** | 舊 V3-A 金紺框；主線世界泡泡即呢款，**今輪唔搬** |
| `bubble_dream@3x.png` | 96×72 | 夢泡泡／後輪，唔等同 need |
| kit／M1 `photo`、`mg_hide` 等 | 32×32 | 唔係欣賞；欣賞已另畫安靜眼睛 |
| kit_hd2d_v3 整體版面／多畫面零件 | — | 已取消，唔直接搬舊 UI |

## 仍缺（刻意唔畫）

長按執屎手勢圈、退出觀察專用圖、總結卡／郵局／廚房／圖鑑／狩獵／M2、照顧數值。找不到嘅正確操作 icon 已只補執屎同欣賞兩枚。
