# 《微光小圃》HD-2D UI 動態規格（production）

- 來源：概念 `ui/style_ref/hd2d/motion_popup_HD2D.gif`（約 2.0s）、`motion_screen_transition_HD2D.gif`（約 1.9s）。量產版收短到 1/2–2/3，避免玩家等。
- 單位：時間 ms；位移 art（×3＝@3x px）。全部 Canvas2D：`translate/scale/globalAlpha` ＋ 已 bake 嘅光暈 sprite，冇 shader。
- Easing（t∈[0,1]）：
  - `oCubic`＝1−(1−t)³；`iCubic`＝t³；`ioSine`＝−(cos(πt)−1)/2
  - `oBack`＝1+2.2(t−1)³+1.2(t−1)²（overshoot ≈5%）
  - `keys(ts,vs)`＝分段線性插值再套 oCubic
- 減少動態（設定「畫質：低」或系統 reduce-motion）：全部改 150ms 淡入淡出，冇 parallax、冇 veil、冇微塵。
- SFX 只用遊音現有 `sfx_ui8_*`（`/workspace/遊音-staging/audio/README.md` §7.11）；改名只係建議（§8），冇改佢哋檔案。

## 1. Tab switch（dock 5 tab）— 240ms
| t | 物件 | 動作 | easing |
|---|---|---|---|
| 0 | 撳中 tab | `med18_navy_in` 按下縮 0.92（60ms）；出 `fx_ripple` r 4→16 α .9→0（220ms） | oCubic |
| 0–200 | 舊 active | `med24_pri`→`med18_navy_in`：scale 24/18→1、cy 393→398；`dock_pillar` α 1→0 | iCubic |
| 40–240 | 新 active | `med18_navy_in`→`med24_pri`：scale 0.75→1.08→1（keys [0,.7,1]）、cy 398→393；`dock_pillar` α 0→1、高 0.6→1 | oBack |
| 40–240 | 字 | `lbl_tab_*` crossfade → `lbl_tab_on_*` | linear |
| 0–240 | 內容頁 | 同層頁：舊頁 α→0、dx 0→∓8；新頁 dx ±8→0、α 0→1（方向跟 tab index） | oCubic |
- SFX：t=0 `sfx_ui8_tab_switch_a`／下一次 `sfx_ui8_tab_switch_b`（交替）。大頁（手帳／小圃）改用 §6 轉場。

## 2. Popup open／close
**Open — 420ms**
| t | 物件 | 動作 | easing |
|---|---|---|---|
| 0–200 | 觸發掣 | `fx_ripple` r 4→20，α .9→0 | oCubic |
| 0–260 | 背景 | DoF：blur 0→2 art（可略）＋ `#141A36` α 0→110/255 | ioSine |
| 40–360 | `panel_glass` | scale keys [0,.55,.8,1]→[.78,1.05,.985,1]；α 前 35% 0→1；dy +10→0 | oCubic |
| 120–300 | `plaque` | dy −6→0，α 0→1 | oBack |
| 200–420 | 金框 | 外光脈衝：`panel_glass` 第二層 additive α 0→.6→0 | sin |
| 220＋60·i | 列 i | dx −10→0，α 0→1，200ms | oCubic |
| 300–620 | 主掣 | scale [.5,1.12,.96,1]（keys [0,.5,.8,1]）；之後 `fx_sweep` 掃一次（320ms） | oCubic |
| 全程 | `fx_mote` ×8 | 向上飄 6 art／s、閃爍（高畫質先開） | linear |
- SFX：t=0 `sfx_ui8_popup_open`。

**Close — 200ms**
| t | 物件 | 動作 | easing |
|---|---|---|---|
| 0–60 | `close`→`close_p` | 按下 | — |
| 0–180 | `panel_glass`＋內容 | scale 1→.9，α 1→0，dy 0→+6 | iCubic |
| 40–200 | 背景 | DoF 還原 | ioSine |
- SFX：t=0 `sfx_ui8_popup_close`（✕／背景撳）；「取消」掣用 `sfx_ui8_cancel`。

## 3. Button press — down 60ms／up 120ms
| 階段 | 動作 | easing |
|---|---|---|
| pointerdown（0–60） | 換 `_p` frame（已 bake 下沉 1.1 art、光減半、冇 sheen）；內容（字／icon）dy +1.1；scale .97 | oCubic |
| pointerup（0–120） | 換回常態 frame；scale .97→1.03→1 | oBack |
| 主掣確認後 | `fx_spark` ×3 喺右上 pop（200ms）＋`fx_sweep` | oCubic |
| 停用掣撳 | `btn_dis` 左右震 ±1.5 art ×2（160ms），冇 `_p` | sin |
- SFX：down `sfx_ui8_btn_press_a`／`sfx_ui8_btn_press_b`（隨機）；圓章 `sfx_ui8_tap_a`／`sfx_ui8_tap_b`；主掣確認 `sfx_ui8_confirm`＋`sfx_ui8_btn_sparkle`；停用 `sfx_ui8_error`。

## 4. Toast — in 220ms／停 1800ms／out 180ms
| t | 物件 | 動作 | easing |
|---|---|---|---|
| 0–220 | `toast` | dy −10→0（由頂 HUD 下面滑出，y44），scale x .6→1.04→1，α 0→1 | oBack |
| 80–260 | `toast_wing_l`/`_r` | dx ∓6→0，α 0→1 | oCubic |
| 120–300 | icon 圓章 | scale 0→1.15→1 | oBack |
| 140–260 | 數字（`px7_ol`/`gold`） | +N 由 0 數上去 | linear |
| 2020–2200 | 全部 | dy 0→−6，α→0 | iCubic |
- 一次一個（P0-1 隊列）；同類 1.5s 內合併「+5 ⭐、徽章 ×1」並重新計停留時間。
- SFX：t=0 `sfx_ui8_toast_in`；貨幣類加 `sfx_ui8_coin`（t=140）。

## 5. Red dot
| 事件 | 動作 | easing |
|---|---|---|
| 出現 | `red_dot`／`red_dot_num` scale 0→1.25→1（240ms） | oBack |
| 提醒 wiggle | 每 6s（畫面靜止時）：rotate 0→−12°→10°→−6°→0（360ms）；scale 1→1.1→1 | ioSine |
| 數字變 | 舊數 dy 0→−3 α→0；新數 dy +3→0（160ms） | oCubic |
| 消失（已讀） | scale 1→1.2→0，α→0（160ms）＋`fx_spark` ×1 | iCubic |
- SFX：wiggle `sfx_ui8_badge_wiggle`（冷卻 ≥5s，一個畫面只響一次）；出現冇聲。

## 6. Screen transition（主頁 ⇄ 手帳／小圃／屋仔）— 900ms
| t | 物件 | 動作 | easing |
|---|---|---|---|
| 0–200 | 撳中 tab／掣 | `fx_ripple` | oCubic |
| 0–600 | 場景 parallax | sky −1.5／far −4,−1／mid −8,−2／fore −14,+5 art（前快遠慢） | ioSine |
| 40–280 | 頂 HUD／行動掣 | HUD dy 0→−10、行動掣 dy 0→+12，α→0（dock 留低） | iCubic |
| 80–280 | dock | active 交棒（同 §1） | oBack |
| 160–700 | `fx_veil` | 由 tab 中心擴散，scale 0.9→9（R 30→290 art），α keys [0,.35,.65,1]→[0,.88,.88,0]；入面 `fx_mote` ×12 | ioSine |
| 200–540 | 場景 | DoF：blur 0→2.3 art＋壓暗 | ioSine |
| 420–700 | 新頁 | scale 1.06→.99→1，α 前 40% 0→1，dy +4→0 | oCubic |
| 520＋40·i | 卡／列 i | pop [.5,1.1,.97,1]，240ms | oCubic |
| 700–900 | 頁框 | `fx_sweep` 掃一次 | linear |
- 返回：倒播（場景 parallax 回 0，HUD／行動掣 dy 回 0，α 0→1，oCubic），600ms，冇卡 pop。
- SFX（遊音 README v3 已改名）：t=0 `sfx_ui8_transition_veil_close`（光幕收埋舊畫面），t=420 `sfx_ui8_transition_veil_open`（新頁出現）；返回只播 `sfx_ui8_transition_veil_open`。

## 7. 其他小動態
| 元素 | 動態 | SFX |
|---|---|---|
| toggle | knob dx 13 art，120ms oBack；track crossfade | `sfx_ui8_toggle_on`／`sfx_ui8_toggle_off` |
| seg 分段 | `seg_on` 滑去新格 140ms oCubic | `sfx_ui8_tap_a` |
| 需要條 | 數值變：fill 寬 300ms oCubic；補滿：`fx_sweep` 掃一次；<20%：換 `need_fill_low`，icon 每 2s 輕跳 1 art | — |
| 委託完成 | `stamp_done` scale 1.6→.9（0–100ms）→1（100–160ms）＋`fx_spark` | `sfx_ui8_confirm` |
| hint | `hint_arrow` dy 0→2→0 1s loop | — |

## 8. SFX 對照＋建議改名（只係建議，遊音話事；冇改佢哋檔案）
> 檔案長度以遊音 README §7.11 為準（下表長度係 v1 舊數，只供參考）。卡 pop 聲只播頭 3 張；pointerup 唔加聲。

| 用喺 | 而家名（README §7.11） | 長度 | 建議名 | 原因 |
|---|---|---|---|---|
| §6 轉場收 | `sfx_ui8_transition_veil_close` | 0.570s | ✅ 遊音 v3 已採用 | 舊 heart_close 停用 |
| §6 轉場開 | `sfx_ui8_transition_veil_open` | 0.570s | ✅ 遊音 v3 已採用 | 舊 heart_open 停用 |
| §1 tab | `sfx_ui8_tab_switch_a`/`sfx_ui8_tab_switch_b` | 0.129s | 唔使改 | |
| §3 掣 | `sfx_ui8_btn_press_a`/`sfx_ui8_btn_press_b`、`sfx_ui8_btn_sparkle` | 0.099／0.277s | 唔使改 | |
| §2 popup | `sfx_ui8_popup_open`/`sfx_ui8_popup_close` | 0.273／0.179s | 唔使改 | 長度啱 420／200ms |
| §4 toast | `sfx_ui8_toast_in` | 0.209s | 唔使改 | |
| §5 紅點 | `sfx_ui8_badge_wiggle` | 0.224s | → reddot_wiggle（可選） | 對應 `red_dot` 名 |
| 確認／取消／錯 | `sfx_ui8_confirm`/`sfx_ui8_cancel`/`sfx_ui8_error` | .309／.169／.210s | 唔使改 | |
| toggle | `sfx_ui8_toggle_on`/`sfx_ui8_toggle_off` | 0.079s | 唔使改 | |
| 舊 sfx_tap／confirm／cancel／error／hit | 保留做 fallback | | | |

## 10. Part 2 新增動態
### 10.1 升級 popup（mockups/levelup_3x.png）
| t (ms) | 元素 | 動作 |
|---|---|---|
| 0 | 背景 dim | α 0→.55 200ms；`sfx_ui8_popup_open` |
| 0–320 | 窗 `panel_glass`＋`plaque_pri`「升級啦」 | scale .86→1.04→1 easeOutBack；`toast_wing_l`/`toast_wing_r` 由內向外滑 6 art |
| 200–600 | 寵物圓章 `med34_pri`＋`fx_veil` | 圓章 pop .6→1.08→1；veil α 0→.9→.6 breathe 2s loop |
| 360 | 3 粒 `star_on` | 左→中→右 每粒 +80ms pop .4→1.2→1；每粒 `sfx_ui8_btn_sparkle` |
| 600 | 金字「✦ LV.4 ✦」 | 數字 3→4 翻牌（y −4→0, α），兩邊 ✦ 旋 0→90° 一下；`sfx_ui8_confirm` |
| 760–1000 | 獎勵行（`panel_inset`） | 每行由下 +6 art 淡入，間隔 90ms；「✦+20」數字由 0 滾到 20（400ms），每跳 4 一下 `sfx_ui8_coin` |
| 1000 | 解鎖行（`panel_inset_sel`＋`red_dot_num`） | 紅點 `badge_wiggle`（MOTION §7）；`sfx_ui8_badge_wiggle` |
| loop | `fx_spark`／`fx_mote` | spark 1.2s 閃，mote 慢飄 dy −8 art/3s |
| 撳「好呀」 | `btn_pri` | 掣 §3 press；`sfx_ui8_btn_press_a`；窗 scale 1→.92 α→0 180ms；`sfx_ui8_popup_close` |
- 細機（360w／`smallphone`）：同一 art 座標，窗高 240 art 以內，唔使改排位。
- Reduced motion：跳過 scale/滾數，只做 α 淡入 150ms。

### 10.2 長 list 邊緣（`scroll_fade_top`／`scroll_fade_bot`／`scroll_glow_top`／`scroll_glow_bot`）
- 靜態：list 上／下仲有內容就顯示 fade（α 1；scrollTop=0 時 top fade α 0，到底時 bot fade α 0；變化 120ms）。
- Overscroll：拉過頂／底時顯示 glow，α = min(1, pull/24 art)，放手 200ms 淡走；唔播聲（避免手指拖嘅時候連聲）。
- fade 用 3h slice，闊度跟 list；glow 疊喺 fade 上面。
