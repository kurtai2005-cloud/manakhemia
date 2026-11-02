# breakthrough 6d 社交（分享碼／QR／影子探訪／蛋碼）— 美術交付（遊美，2026-11-02）

依據：`docs-gdd/breakthrough-6a6d-spec.md` §6d（spec 優先：「影子效果 code 做半透明（唔使美術）；QR／分享 UI 1 套；朋友牌 icon 1 個」；v1＝貼碼＋揀相解 QR，相機掃 backlog）。
跟 HD-2D UI kit v2：金邊海軍藍、頂 plaque、9-slice 一律 **tile 唔拉伸**、alpha 0／255、字 **FP12 起**（Fusion Pixel 12 TTF，關 AA，描邊＋1px 影）。
repo 未有 6d code → 以下 key 係**美術提案**，等遊程確認。疊喺 6c 上面（共用 `art-pet/tools/bt6_px.py`）。
Builder：`art-pet/tools/build_breakthrough_6d_share.py`；驗證：`python3 art-pet/tools/validate_breakthrough_6d.py` → **20/20 PASS**。機讀：`share6d.json`（連 slot 座標同每段字嘅色／對比記錄）。

## 新 key（1x；@3x 同名加 `@3x`）
| key | 檔 | art 尺寸 | 9-slice | 備註 |
|---|---|---|---|---|
| `6d:qr_frame` | `parts/qr_frame.png` | 20×20 | `9` nine [6,6,6,6] tile | 金框＋白 quiet zone；白位＝(w−8)×(h−8) @(4,4)；QR module 用整數 art px 畫入去 |
| `6d:code_field` | `parts/code_field.png` | 24×20 | `3h` nine [6,0,6,0] tile | 凹入深藍輸入格；字 FP12 cream，x＋8，垂直置中 |
| `6d:code_field_on` | `parts/code_field_on.png` | 24×20 | `3h` 同上 | focus／已貼上（金邊亮） |
| `6d:share_card_bg` | `parts/share_card_bg.png` | 165×252（存相＝@3x 495×756） | — | 分享圖底：kit `panel_navy`／`plaque`／`panel_inset`／`divider` tile 砌＋qr_frame 66×66；slot 見下 |
| `6d:shadow_mask` | `parts/shadow_mask.png` | 4×4 | 成片 tile | 影子：pet 像素 ∧ 棋盤（白＝畫）＋kit vi0／vi1／vi2 剪影，**取代半透明**（見衝突 1） |
| `6d:friend_badge` | `icons/friend_badge.png` | 32×32 | — | 朋友牌（spec 嗰 1 個）：探訪影子頭頂／朋友列表 |
| `icon_friend` | `icons/ic_friend.png` | 16×16 | — | 朋友牌細版（rail／pill 用） |
| `icon_share` `icon_copy` `icon_paste` `icon_photo` `icon_qr` `icon_egg_code` | `icons/ic_<名>.png` | 16×16 | — | 分享／複製碼／貼上／揀相解碼／QR／蛋碼 |
沿用 kit（唔重畫）：`ic_visitor`、`ic_family_level`、`ic_egg_tr`、`ic_gift`（影子留低嘅手信）、`ic_badge`、`egg_card`、`btn_*`／`btn16_*`、`plaque`、`close`、`fx_veil_tile`。
全部靜態，冇幀／fps。

## share_card slot（art 座標，卡左上＝0,0）
title 中 (82.5, 8.5) FP12「朋友名片」；portrait (10,24) 54×56（kit `portrait()`）；name (70,34)；家族 Lv (70,52)＋mini star；形態 (70,70)；回憶 ×3 (24, 101／119／137) maxW 126；QR 框 (49,160) 66×66，白位 (53,164) 58×58；碼 中 (82.5, 236)。
QR：base64url 快照（spec）長度 → 建議 ECC M、≤v10（57 module）×1 px，或 ≤v3（29）×2 px；四邊留 ≥4 module 白（白位 58 已包）。mockup 嘅 QR 係**示意圖樣**（finder＋hash 雜點），唔可以掃。

## Mockup（3x，585×1266）
`mockups/share_3x.png`（分享名片＋複製碼／存圖）、`enter_code_3x.png`（貼碼／揀相 → 讀到朋友＋校驗 OK → 請佢嚟玩）、`visit_shadow_3x.png`（花園影子探訪＋朋友牌＋剩餘時間）、`egg_code_3x.png`（家族 Lv4 解鎖交換蛋碼）、`share_card_sample.png`（@3x 有）。

## 已知問題／要決定
1. **spec 寫影子「code 做半透明」，但 kit 規定全 alpha 0／255** → 我提供 `shadow_mask` 棋盤＋剪影色做法（mockup 用咗）；要遊策／遊程揀：跟 spec 用半透明，定跟 kit 用棋盤。
2. 6d 未有 code，key 名、slot、尺寸都係提案。
3. mockup 底層用 kit `home()`／`room()`，入面 kit 原有 HUD 字（8／10px）係 kit 規格，唔屬 6d；6d 自己落嘅字全部 FP12（json `text` 有記錄）。
4. kit 字形 json 只得 992 字；6d 字（玩家名、回憶）係動態 → 要用 TTF runtime 出字（mockup 已經咁做）。
5. 存相 495×756 係 @3x；如果要 1080 闊分享圖，要遊程決定 ×6（990）或加邊。
