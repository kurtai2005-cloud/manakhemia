# art-pet ASSET_LOG（遊美）
> 記錄 art-pet 下新出／改動嘅資產。全部 Python（Pillow／numpy）程式逐像素繪製，無 AI 生成，全原創。時間 HKT。

## 2026-10-31 10:50 — 《微光小圃》HD-2D 場景 H1–H4（定稿格式：canvas2D 預烘）
- 腳本：tools/build_hd2d_scenes.py（`python3 build_hd2d_scenes.py [layers|H1|H3|H4|H2|rain|particles|crossfade|all]`）、tools/validate_hd2d_scenes.py（`--strict`）、tools/build_tuanrong_rim.py
- scenes/hd2d/index/、layout.json、layout_preview_2x.png — 共用 4 層 index map（64 材質）＋佈局（寵物範圍、地面線、盆、燈、UI 安全區）
- scenes/hd2d/H1｜H2｜H3｜H4/ — sky/far/mid/fore（預烘 LUT＋DoF，223×446）、raw/（≤64 色：61／61／61／63／62）、lightmap、light_add、emissive、emissive_blur、vignette、lut.png（256×16）、grade.json、palette.json、mockup_×3 形態＋2x
- scenes/hd2d/H3/grade_rain.json、H3/rain/（預烘落雨層＋lut_rain.png＋mockup_rain）；scenes/hd2d/rain/rain_tile（64×64×4）、ripple（16×8×4）
- scenes/hd2d/particles/particles.png/.json — mote／gold／petal／firefly 各 6 幀 8×8
- sprites/tuanrong/rim/ — rim_{sprout,radiant,soft}.png/.json（同 motion atlas 尺寸／rect／幀名，各 96 幀）＋單幀＋預覽
- scenes/hd2d/crossfade/ — H1→H3→H2→H4→H1 GIF（1x、2x）＋key strip
- 文件：scenes/hd2d/FORMAT.md、PROGRESS.md
- 冇改：團絨 sprite／atlas／31 色色盤、motion/liveliness/、glimmer-live repo、任何現有檔案（全部新檔）
- 驗證：validate_hd2d_scenes.py --strict → PASS 419 / FAIL 0

## 2026-10-31 11:50 — 團絨 picked_up（D6 被拎起，浮動團絨）
- 腳本：tools/build_tuanrong_liveliness.py（新增 picked_up、鐘擺 shear `pend_shear`、腿仔 `ex_legs`、`grab` 錨點、clip pivot override、`pickup_preview`）、tools/build_tuanrong_liveliness_docs.py（CLIPS.json `pivot`/`faceOnEnter`、FACE_RIG 新章節）、tools/validate_liveliness.py（驗 grab／pivot override）
- 3 form（sprout 32／radiant 64／soft 64，尺寸不變）各 6 幀、8fps、loop、朝右：身體吊住微拉長、以頭頂 grab 為軸鐘擺擺、雙腳交替輕踢
- 新檔：layers/<form>/picked_up_0[1-6]_{noface,faceov}.png、frames/<form>/picked_up_0[1-6].png、preview/<form>/picked_up_{8x.gif,grab_8x.gif,strip_8x.png}
- 改檔：atlas_{sprout,radiant,soft}_live.png/json（重 pack，仍 1 頁：1024×256／1024×1024／1024×1024；舊幀 rect 位置有變，名同像素不變）、face_anchors.json（+grab、+pivotOverride）、CLIPS.json／CLIPS.md、FACE_RIG.md、MILESTONE1.md、contact_*_liveliness.png
- 舊 33 個 clip 嘅 layers／frames／kit／GIF 逐檔 md5 不變
- 備份：/workspace/game-design/_backups/pre_pickup_20261031/
- 驗證：validate_liveliness.py → ALL PASS（FAIL 0；錨點 459 幀、pivot override 36 塊）
- Pillow／numpy 程式繪製、31 色盤、alpha 0/255、無 AA，無 AI

## 2026-10-31 13:10 — 螢絨 lumi 動畫（隱藏稀有成年形態，round_s）
- 概念改：翼由頭頂移去背後（中／下背，身後；左邊露出輪廓外一截）→ 重出 lumi_concept/lumi_idle_64.png、lumi_idle_emissive_64.png、lumi_concept_8x.png；tools/build_lumi_concept.py 改成 parametric `render_lumi(p)`（同 render_pet 參數語義）
- 新腳本：tools/build_lumi.py（import motion／liveliness 做 module，唔跑佢哋 main；pose 參數＝radiant 同名 clip，只換外觀層）、tools/validate_lumi.py
- 15 clip／60 幀（MVP 12／46：idle 4、blink 4、walk 6、play 6、eat 4、sleep_loop 4、emo_happy 2、emo_hungry 2、emo_sleepy 2、celebrate 4、droop 6、sick 2；加 picked_up 6（pivot＝grab）、fall_asleep 4、wake 4）
- 發光：尾燈脈衝（bud 基準＋幀相位 0/1/2 級）、8 粒身上光點逐幀閃、觸角燈頭隨 sway/droop；每幀 emissive 遮罩（白＝fly／fly_core）
- 新檔：sprites/tuanrong/atlas_lumi.png/.json（1024×1024，206 塊，padding 2、extrude 1，pivotPx 逐塊）、atlas_lumi_emissive.png（同 layout）；sprites/tuanrong/lumi/{frames,layers(_noface/_faceov),emissive,kit,preview}/、face_anchors_lumi.json（eyeL/eyeR/mouth/head_r/bulb/bulb2/tail/faceVisible/face/grab）、palette_lumi.json、contact_lumi_4x.png、compare_radiant_vs_lumi_4x.png、_stats.json
- 改檔：motion/CLIPS.json（forms.lumi、clips[].anchors.lumi、clips[].lumi）、motion/CLIPS.md（lumi 段）、tools/validate_liveliness.py（結尾調用 validate_lumi）、lumi_concept/NOTES.md
- 冇改：radiant／soft／sprout 任何幀、atlas、liveliness 檔；31 色共用色盤
- 備份：/workspace/game-design/_backups/pre_lumi_anim_20261031/
- 驗證：validate_lumi.py → ALL PASS；validate_liveliness.py（含 lumi）→ ALL PASS（FAIL 0）
- 注意：build_tuanrong_liveliness_docs.py 會由 _backup_v1 重砌 CLIPS.json → 重跑後要再跑 build_lumi.py 補返 lumi 段
- Pillow／numpy 程式繪製、alpha 0/255、無 AA、無 AI
