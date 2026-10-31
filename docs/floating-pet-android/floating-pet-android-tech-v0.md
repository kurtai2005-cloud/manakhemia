# 浮動團絨（Android）技術評估 v0 — 遊程

狀態：Kurt 2026-10-31 批准（經善哥），排生命感三段＋開發者模式版之後。未開工。iOS 唔做。
設計稿：docs-gdd/floating-pet-android-v0.md（遊策）。

## 1. 技術路線
- Capacitor 包現有 web build 成 APK；自寫 Kotlin plugin：前景 Service（foregroundServiceType=specialUse）＋常駐通知＋WindowManager TYPE_APPLICATION_OVERLAY（SYSTEM_ALERT_WINDOW）。
- overlay 用原生 Canvas 自訂 View 畫 atlas，**唔用 WebView**（WebView 常駐 50–100MB、耗電、透明窗觸控穿透麻煩）。≤15fps，熄螢幕停。
- 視窗只係寵物大細（48dp＋邊界），行動用 updateViewLayout 搬窗，其餘位置觸控穿透。
- 面部合成唔喺 Kotlin 重寫：工具 script 將精簡集 clip＋眼／口預烘成 overlay 專用 atlas＋JSON。
- 必要 clip：行、邊行邊望、回頭、待機、瞓覺、抓癢、噴嚏、開心、grumpy_tap、被拎起（新，遊美）。

## 2. 同 app 狀態同步
- game 係唯一模擬者。存檔時經 Capacitor Preferences（SharedPreferences）寫快照 JSON：form、mood、needs×4、personality、timeSlot、eventFlag、version、ts。
- Service 聽 OnSharedPreferenceChangeListener 轉表情；需求 <30 出小圖示；事件／閃光日頭頂 ✨ 泡泡，點開 app，唔彈窗。
- overlay 互動只 append 入 queue key（有上限）；app resume 經 plugin 取走清空，走現有離線重播結算：每次互動心情 +1，每日上限 +5，唔改需求／CQ／進化，唔派獎、唔出事件。一 key 一個寫者。
- 模式設定（範圍矩形、定點位置、模式）存 Preferences。

## 3. 活動模式（4）
1. 沿邊行（預設）
2. 自訂範圍：設定頁拖角調大細、拖中間移位，最細 120×120dp
3. 全畫面自由行：避開狀態列／導航列／鍵盤（鍵盤用 1px 高全寬隱形 overlay 讀 IME insets；廠商唔準時退回「避開下半屏」）
4. 定點：拖放停定
切換：設定頁＋通知快捷掣＋長按選單。點＝回頭、長按拖、拖去×關、雙擊開 app。

## 4. 人日（覆核後約 13，範圍 11–15）
| 項 | 人日 |
|---|---|
| Capacitor＋APK＋簽名 | 1.5 |
| 前景 Service＋通知＋權限引導 | 2 |
| overlay 渲染＋預烘 atlas＋表情 | 2.5 |
| 行動：沿邊／自由行／自訂範圍／定點／拖×關／雙擊 | 2.5 |
| 模式切換：設定頁＋通知快捷掣＋長按選單＋鍵盤避讓 | 1 |
| 同步橋＋queue＋心情上限 | 1.5 |
| Play 政策聲明＋電量優化 | 0.5 |
| 實機＋小米／OPPO／vivo／三星兼容 | 1.5 |

## 5. 排期
生命感第三段之後（用最終 clip，免重烘）。Capacitor＋APK 1.5 日可插第二段後空檔，唔阻三段同開發者模式版。

## 6. 風險
- Play 審核 SYSTEM_ALERT_WINDOW＋前景服務用途（最大）。
- 小米／OPPO／vivo 殺背景、額外「懸浮窗」權限。
- Android 14+ 前景服務類型規則。
- 耗電投訴；自由行遮其他 app 按鈕（預設沿邊，自由行做開關＋一撳停定）。
- 鍵盤偵測各廠商唔一致。
