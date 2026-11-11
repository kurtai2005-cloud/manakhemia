# 畫面掃描 1111

對象：`code/glimmer-godot` @ `094e91a4`（tree `fb66ee00`），Godot 4.7.2.stable.official.ed1daf0bf。桌面 Xvfb + llvmpipe，`gl_compatibility`。唔係手機。

`glimmer-live-s1.html` 係凍結舊版，檔案喺 `b4a56160` 的 `src/glimmer-a/dist/glimmer-live-s1.html`，唔喺呢條 QA branch 工作樹。今次冇再開機逐格掃。同 Godot 會再撞到嘅類型（遮擋、白邊、比例、浮陷、影、眼口、UI 重疊）只喺 Godot 截圖記一句。

截圖：`QA/shots-visual-1111/`。時鐘用 `TimeService.use_fake` 鎖 11 月 11 日 08:00／13:00／18:00／22:00。天空同屋身色板四個鐘同「無雨」都係同一組數（天空 RGB 252, 230, 199；屋 201, 142, 77）。

## 遊音三項（第 1 項按遊策更正）

抓癢、噴嚏、嗅地係設計，唔列 bug。`Walker.gd` 而家只播 idle／walk（`Walker.gd:132-144`），呢三個動作片段未接。

### 1. 細佬同訪客冇用自己體型嘅 S／M／L 圖集

全庫角色圖得 `art/kid/A1_idle.png`、`art/kid/A1_walk.png`（48×48 一條），同埋冇人引用嘅 `art/sprites/visitor.png`。冇 S／M／L 圖集。

細佬同訪客載入同一條：

- `scripts/Main.gd:293` 細佬
- `scripts/Main.gd:302` 訪客

兩次都係 `_load_strip("res://art/kid/A1_idle.png", 48, 48, 4, "idle", "res://art/kid/A1_walk.png", 6)`，`pixel_size` 1.0，pivot `(24, 46)`。訪客只係 `Main.gd:304` `modulate = Color(0.85, 0.78, 1.15)`。團絨先用自己嘅 dir4：`Main.gd:282` `atlas_radiant_dir4.png`，64×64。

`Main.gd:341-344` 把同一條正面 idle／walk 填入 front、back、side 六個鍵。Walker 會改方向同 `flip_h`，圖仍然係望住鏡頭嗰條。

動作聲未跟做動作嗰隻。`scripts/` 冇 `AudioStreamPlayer`，`art/` 冇 ogg／wav，抓癢、噴嚏、嗅地同行路都冇播放。未做成「統一播團絨聲」，因為根本冇聲軌。成個遊戲冇聲已知，呢度只核實分流：未接。

P1。截圖 `QA/shots-visual-1111/kid-idle-00.png`（兩隻藍水滴同圖，訪客只係偏色）。負責人：遊程程式接圖同聲；遊美美術交出 S／M／L 同訪客自己嘅條。修法：按體型載入各自圖集，訪客唔好再 tint 細佬；每個動作用做緊嗰隻嘅聲。

### 2. 行路 fps 被覆蓋：細佬嗰個 8 冇被蓋返

`atlas_radiant_dir4.json:514-517` 寫 idle 4、walk 10，冇 gd 讀呢兩個數。`Walker.gd:7-8` 預設 idle 4、walk 10。`Main.gd:288-289` 喺 `setup()` 之前把細佬設成 idle 4、walk 8。`setup()`（`Walker.gd:28-55`）唔寫這兩個欄。`Walker.gd:137` 用欄位本身：行路用 `walk_fps`，企定用 `idle_fps`。

細佬行路維持 8。訪客同團絨冇再設，留 10。圖集入面嘅 fps 未接到播放；團絨嘅 10 同 json 一樣，係預設撞中，唔係讀檔。

唔開 P。

### 3. 畫面時段永遠日間：真

HUD 時鐘跟本機。`TimeService.gd:34-37`、`56-60` 用系統鐘或假鐘。`Hud.gd:160-162` 每幀寫 `%02d:%02d`。

光只喺起場景時寫一次。`Main.gd:142-182` 讀 `lights.json` 設太陽、補光、環境色同背景。`Main.gd:462-463` `_process` 只 `_place_cam`。`Main.gd:407`、`423` 只按畫質改能量。`GardenLoader.gd:45` 把發光貼圖能量設 0，註解話夜景再開，全庫冇第二處寫返。`Hud.gd:120-124` 快轉一小時只推 `Sim`，唔改燈。

08:00、13:00、18:00、22:00 同無雨，天空同屋身色板相同。22:00 時鐘顯示 22:00，花園仍然係日間。雨冇場景接口。

P1。截圖 `QA/shots-visual-1111/garden-390-noon.png`（13:00）、`QA/shots-visual-1111/garden-390-night.png`（22:00）。負責人：遊程程式。修法：`_process` 按 `TimeService.hour_of()` 改太陽方向、能量、環境色同背景；夜晚把 `emission_energy_multiplier` 開返。

## 其他

P2。開發者面板蓋住左上狀態。`Hud.gd:24` 狀態列喺 `(16, 16)`，`Hud.gd:89-98` 面板 `offset_top = 16`、靠右。390 寬度下面兩塊都喺 y=16，面板蓋住「飢／心／潔／力」。截圖 `QA/shots-visual-1111/dev-panel.png`。負責人：遊程程式。修法：面板放到狀態列下面，或者打開時收起左上字。

P2。桌面橫向仍然可玩，冇轉直提示。`project.godot:28` `orientation=1` 只係 handheld 提示。`project.godot:27` `stretch/aspect=keep`。視窗設 844×390 之後 framebuffer 係 180×390，直向畫面縮入去，掣仍然喺度。手機匯出未測。截圖 `QA/shots-visual-1111/land-844x390.png`。負責人：遊程程式。修法：寬大於高就出「請轉直向」，擋住操作。

P3。要求嘅四個直向尺寸只得 390×844 係原生。360×640 實拍 295×640，412×915 實拍 412×891，768×1024 實拍 473×1024，都係 keep 收成 390:844。截圖 `garden-360-noon.png`、`garden-768-noon.png`。唔使改畫，要四個構圖先至改 stretch。

今次見到、唔報：觸控高度，隱藏界面同開發者掣實測 144×48，面板掣 120×44 或 134×44。眼同口畫死喺圖上，Walker 冇獨立層。近睇團絨像素邊乾淨，`Walker.gd:38-39` alpha scissor 0.5 今次冇一圈白。角色腳底貼地，blob 影（`Walker.gd:151-167`）冇獨立錯位可報。側向圖集註記話 side 抄正面，當美術 placeholder。

## Top 5（Kurt 最易見到）

1. 時鐘 22:00，花園仍然全日光。`garden-390-night.png`。`Main.gd:142-182`、`462-463`。遊程程式。
2. 細佬同訪客同一條 A1，訪客只係變色，冇 S／M／L。`kid-idle-00.png`。`Main.gd:293`、`302`、`304`。遊程程式／遊美美術。
3. 細佬同訪客背向鏡頭仍然望住鏡頭。同一條正面填入六個方向。`Main.gd:341-344`。遊程程式。
4. 開發者面板蓋住飢飽四項。`dev-panel.png`。`Hud.gd:89-98`。遊程程式。
5. 桌面打橫仍然玩緊縮細嘅直向畫面，冇鎖定。`land-844x390.png`。`project.godot:27-28`。遊程程式。
