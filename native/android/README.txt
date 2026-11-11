M1a Android 浮動團絨（PetOverlayService）來源，喺每次 export 由 tools/export_android.sh 注入 Godot gradle 工程。

包含：PetOverlayService 同依賴（PetView／PetAtlas／PetPrefs／PetStatus／PetForm／FxView／PetSys12／Sys12Views）、Settings／PowerGuide、舊 assets/pet、GlimmerOverlay Godot 插件（取代 Capacitor FloatingPetPlugin）。

GlimmerApp 改為 object + install()，唔再當 Application。

今輪未做／缺口：
- 6b RealWorldPlugin（計步／天氣）未移植，權限已留
- 6d Share6dPlugin 未移植
- JS／Capacitor 橋改為 Godot singleton GlimmerOverlay；遊戲內未做齊同舊 app 一樣嘅狀態同步（PetPrefs 仍用 CapacitorStorage 名，Godot SaveSystem 未自動對寫）
- 訪客行路圖仍未有（遊戲內 walk 用 A1）
