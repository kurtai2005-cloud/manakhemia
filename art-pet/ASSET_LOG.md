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

## 2026-10-31 13:11 — 螢絨 lumi std23 補齊（+9 clip／42 幀）
- 新 clip（pose＝radiant 同名 clip，只換外觀層）：sway 4、yawn 4、emo_wantplay 2、emo_cuddly 2、emo_surprised 2、cheer_jump 6、catch_reach 6、sunbathe 8、pot_bump 8；grumpy：radiant 冇呢個 clip（只係 face preset）→ 冇出
- 合共 24 clip／102 幀（std23 23 clip＋picked_up）；每幀 emissive、_noface/_faceov、錨點；冇幀掂 64px 邊（只 play_04 自動收 shear，同上一版）
- sunbathe：新 `sun_lumi` ramp（lumi_fur0/1/2＋cream4 亮部暖光）
- 改檔：sprites/tuanrong/atlas_lumi.png/.json、atlas_lumi_emissive.png（重 pack，仍 1024×1024 單頁，290 塊；舊幀 rect 位置有變，名同像素不變）、lumi/face_anchors_lumi.json、lumi/contact_lumi_4x.png、lumi/_stats.json、motion/CLIPS.json（forms.lumi＋9 clip anchors.lumi）、motion/CLIPS.md、tools/build_lumi.py、tools/build_lumi_concept.py（sun_lumi ramp）、tools/validate_lumi.py（24/102、掂邊檢查）、lumi_concept/NOTES.md
- 新檔：lumi/{frames,layers,emissive}/ 9 clip 嘅幀、preview/<clip>_8x.gif、preview/strips/<clip>_strip_8x.png
- 備份：/workspace/game-design/_backups/pre_lumi_std23_20261031/
- 驗證：validate_lumi.py → ALL PASS；validate_liveliness.py（含 lumi）→ ALL PASS（FAIL 0）
- Pillow／numpy 程式繪製、lumi 31 色、alpha 0/255、無 AA、無 AI

## 2026-10-31 15:43 — 團絨 evo6 batch A 動畫（光卵 24／絨點 28／絨芽 32／絨跳 38，v3 lumi feel）
- 新腳本：tools/build_evo6_anim.py（import tuanrong／motion／liveliness／evo6_concept 做 module；姿勢＝現有同名 clip，只換外觀層）、tools/validate_evo6_anim.py
- 光卵 evo_egg：5 clip／20 幀（idle 4、glow 2、tap 4、hatch 6 hold last、picked_up 4 pivot＝grab），冇 face rig
- 絨點 evo_dot／絨芽 evo_sprout／絨跳 evo_hop：各 39 clip／171 幀（std23 ＋ 生命感 s1 含 picked_up ＋ s2 smug_pose/act_cool/lookup_tip/getup/sniff_itch）；face kit 重出（絨點/絨芽 S 4×4、絨跳 L 4×5）；bulb 只限絨跳
- 新檔：sprites/tuanrong/evo6/（<form>/{frames,layers,emissive,kit}、face_anchors_<form>.json、atlas_<form>.png/.json/_emissive.png、palette_base.json、_stats.json）、sprites/tuanrong/preview/evo6/（<form>_contact_4x.png、evo6_batchA_contact_4x.png、gif/）
- 改檔（只加）：motion/CLIPS.json（forms.evo_*、clips[].anchors.evo_*、clips[].evo_*、evo6 段）、motion/CLIPS.md（EVO6A 段）
- 冇改：舊 sprout／radiant／soft／lumi 任何幀、atlas
- 備份：art-pet/_backups/pre_evo6_animA_20261031/（同 /workspace/game-design/_backups/pre_evo6_animA_20261031/）
- 驗證：validate_evo6_anim.py → ALL PASS；validate_liveliness／validate_lumi／validate_motion／validate_hd2d_scenes 照樣 PASS
- 注意：build_tuanrong_liveliness_docs.py 由 _backup_v1 重砌 CLIPS.json → 之後要再跑 build_lumi.py 同 build_evo6_anim.py
- Pillow／numpy 程式繪製、31 色、alpha 0/255、無 AA、無 AI

<!-- LIVE-S3-LOG-START -->
## 2026-10-31 — 團絨生命感第三段（s3）
- nuzzle_purr 4幀/6fps 循環、reunion_happy 5幀/8fps；sprout／radiant／soft 各 9 幀（noface＋faceov＋full＋anchors）。
- `sprites/tuanrong/motion/liveliness/atlas_<form>_live_s3.png/json`；預覽 `preview/<form>/<clip>_strip_8x.png`、`live_s3_contact_4x.png`。
- 工具 `tools/build_tuanrong_live_s3.py`（Pillow/numpy 程式繪製，無 AI）；驗證 `tools/validate_liveliness.py`（加 s3 檢查）。
- 微塵（dust）現有尺寸冇身體美術 → 未出 live atlas（見 LIVE_S3_NOTES.md 建議）。
<!-- LIVE-S3-LOG-END -->

<!-- EVO6BC-LOG-START -->
## 2026-10-31 — 團絨 evo6 動畫 batch B（守夜者 44 ×4）＋ batch C（靜光 48 ×4 MVP）
- 守夜者・螢絨 `evo_guard_lumi`：39 clip／171 幀（noface＋faceov＋full＋emissive＋anchors），atlas 1024×1024／426 塊。
- 守夜者・燦光 `evo_guard_radiant`：39 clip／171 幀（noface＋faceov＋full＋emissive＋anchors），atlas 1024×1024／426 塊。
- 守夜者・柔光 `evo_guard_soft`：39 clip／171 幀（noface＋faceov＋full＋emissive＋anchors），atlas 1024×1024／426 塊。
- 守夜者・微塵 `evo_guard_dust`：41 clip／180 幀（noface＋faceov＋full＋emissive＋anchors），atlas 1024×1024／444 塊。
- 靜光・螢絨 `evo_still_lumi`：7 clip／28 幀（noface＋faceov＋full＋emissive＋anchors），atlas 1024×256／140 塊。
- 靜光・燦光 `evo_still_radiant`：7 clip／28 幀（noface＋faceov＋full＋emissive＋anchors），atlas 1024×256／140 塊。
- 靜光・柔光 `evo_still_soft`：7 clip／28 幀（noface＋faceov＋full＋emissive＋anchors），atlas 1024×256／140 塊。
- 靜光・微塵 `evo_still_dust`：7 clip／28 幀（noface＋faceov＋full＋emissive＋anchors），atlas 1024×256／140 塊。
- 守夜者：std23＋生命感 s1/s2（含 picked_up）；微塵另加 s3 nuzzle_purr／reunion_happy。靜光 MVP：idle、blink、emo_happy、fall_asleep、sleep_loop、wake、picked_up。
- `sprites/tuanrong/evo6/atlas_<form>(.png/_emissive.png/.json)`、`evo6/<form>/`；色盤 `evo6/palette_{base,lumi,dust}.json`；預覽 `preview/evo6/<form>_contact_4x.png`、`gif/`、`evo6_batchB_contact_4x.png`、`evo6_batchC_contact_4x.png`。
- 工具 `tools/build_evo6_animBC.py`（Pillow/numpy 程式繪製，無 AI）；驗證 `tools/validate_evo6_anim.py`（擴展到 B/C：分支色盤、emissive、bulb/bulb2/tail、MVP、s3）。CLIPS.json 只新增（forms＋clips[].<form>＋anchors.<form>＋evo6B／evo6C 段）；備份 `_backups/pre_evo6_animBC_20261031/`。
<!-- EVO6BC-LOG-END -->

<!-- EVO6D-LOG-START -->
## 2026-10-31 — 團絨 evo6 動畫 batch D（靜光 48 ×4 升級全套＋微塵燈跟手＋靜光瞓覺 aura 調暗）
- 靜光・螢絨／燦光／柔光／微塵 `evo_still_<branch>`：各 41 clip／180 幀（std23＋生命感 s1/s2 含 picked_up＋s3 nuzzle_purr／reunion_happy），atlas 1024×1024／444 塊；batch C 嗰 7 個 MVP clip 幀不變，只係 fall_asleep／sleep_loop（aura 調暗）同靜光・微塵（燈跟手）有改。
- 守夜者・微塵 `evo_guard_dust`：41 clip／180 幀重出——手燈跟右手（垂手提燈短柄、舉手高舉、橫伸喺手前、冇右手放身右下），`bulb` 錨點＝燈中心同步；其餘守夜者 3 形態冇郁。
- 靜光 aura：fall_asleep 0.8→0.2 漸暗、sleep_loop 0.2（暗色、只內圈疏點、冇閃星／飄花）。
- 預覽 `sprites/tuanrong/preview/evo6/evo6_batchD_contact_4x.png`、`evo6_dust_lamp_before_after_4x.png`；統計 `evo6/_stats_batchD.json`。
- 工具 `tools/build_evo6_animBC.py D`（Pillow/numpy 程式繪製，無 AI）；`tools/validate_evo6_anim.py` 加：靜光冇 mvp key 就用全套規則（要 s3）、微塵 bulb 錨點要落喺燈上。CLIPS.json 只新增／更新自己 key（forms.<still/guard_dust>、clips[].<form>、anchors.<form>、evo6D 段、evo6C.supersededBy）；CLIPS.md 加 EVO6D 段；備份 `_backups/pre_evo6_animD_20261031/`。
<!-- EVO6D-LOG-END -->

<!-- EVO6E-LOG-START -->
## 2026-10-31 — 團絨 evo6 動畫 batch E（靜光・燦光 halo 瞓覺調暗）
- `evo_still_radiant` 大 halo 弧：fall_asleep 跟 aura 0.8→0.2 漸暗（glow→egg_shade→egg_dark；emissive glow_core/glow_mid 點越疏）、sleep_loop 0.2、wake 0.2→1 返光（wake_04 原樣）。改 11 幀（fall_asleep 4、sleep_loop 4、wake 3）＋對應 layers／emissive／atlas；其餘 clip 同形態不變。
- 預覽 `sprites/tuanrong/preview/evo6/evo6_radiant_halo_sleep_before_after_4x.png`；工具 `tools/build_evo6_animBC.py E`（Pillow/numpy，無 AI）；CLIPS.json 只更新 forms.evo_still_radiant＋clips[].evo_still_radiant／anchors＋新增 evo6E；CLIPS.md 加 EVO6E 段；備份 `_backups/pre_evo6_animE_20261031/`。
<!-- EVO6E-LOG-END -->

<!-- EVO6F1-LOG-START -->
## 2026-10-31 — 團絨 evo6 動畫 batch F1（新支線・水珠 tide）
- 守夜者 44＋靜光 48 全套 41 clip：`evo_guard_tide` 180 幀、`evo_still_tide` 180 幀；frames／layers／emissive／kit／face_anchors（bulb＝燈中心）／atlas＋emissive。色盤 `sprites/tuanrong/evo6/palette_tide.json`。
- 分支動態：浮浮下：idle 身浮 1px、水珠燈逐幀上下、泡泡上升、肚波紋流、鰭耳／魚尾擺。靜光瞓覺 aura 漸暗同靜光 ×4。
- 預覽 `sprites/tuanrong/preview/evo6/evo6_batchF1_contact_4x.png`；工具 `tools/build_evo6_animF.py F1`（Pillow/numpy 程式繪製，無 AI）；CLIPS.json 只新增自己 key（forms.<form>、clips[].<form>、anchors.<form>、evo6F.batches.F1）；CLIPS.md EVO6F 段；備份 `_backups/pre_evo6_branches5_anim_20261031/`。
<!-- EVO6F1-LOG-END -->

<!-- EVO6F2-LOG-START -->
## 2026-10-31 — 團絨 evo6 動畫 batch F2（新支線・菇傘 shroom）
- 守夜者 44＋靜光 48 全套 41 clip：`evo_guard_shroom` 180 幀、`evo_still_shroom` 180 幀；frames／layers／emissive／kit／face_anchors（bulb＝燈中心）／atlas＋emissive。色盤 `sprites/tuanrong/evo6/palette_shroom.json`。
- 分支動態：菇帽搖：菇帽逐幀左右擺＋斜（帽邊一高一低）、細菇燈跟住晃、孢子飄。靜光瞓覺 aura 漸暗同靜光 ×4。
- 預覽 `sprites/tuanrong/preview/evo6/evo6_batchF2_contact_4x.png`；工具 `tools/build_evo6_animF.py F2`（Pillow/numpy 程式繪製，無 AI）；CLIPS.json 只新增自己 key（forms.<form>、clips[].<form>、anchors.<form>、evo6F.batches.F2）；CLIPS.md EVO6F 段；備份 `_backups/pre_evo6_branches5_anim_20261031/`。
<!-- EVO6F2-LOG-END -->

<!-- EVO6F3-LOG-START -->
## 2026-10-31 — 團絨 evo6 動畫 batch F3（新支線・晶角 crystal）
- 守夜者 44＋靜光 48 全套 41 clip：`evo_guard_crystal` 180 幀、`evo_still_crystal` 180 幀；frames／layers／emissive／kit／face_anchors（bulb＝燈中心）／atlas＋emissive。色盤 `sprites/tuanrong/evo6/palette_crystal.json`。
- 分支動態：晶光閃：晶耳／晶燈／身上晶粉閃點逐幀輪住閃（glint）。靜光瞓覺 aura 漸暗同靜光 ×4。
- 預覽 `sprites/tuanrong/preview/evo6/evo6_batchF3_contact_4x.png`；工具 `tools/build_evo6_animF.py F3`（Pillow/numpy 程式繪製，無 AI）；CLIPS.json 只新增自己 key（forms.<form>、clips[].<form>、anchors.<form>、evo6F.batches.F3）；CLIPS.md EVO6F 段；備份 `_backups/pre_evo6_branches5_anim_20261031/`。
<!-- EVO6F3-LOG-END -->

<!-- EVO6F4-LOG-START -->
## 2026-10-31 — 團絨 evo6 動畫 batch F4（新支線・月眠 moon）
- 守夜者 44＋靜光 48 全套 41 clip：`evo_guard_moon` 180 幀、`evo_still_moon` 180 幀；frames／layers／emissive／kit／face_anchors（bulb＝燈中心）／atlas＋emissive。色盤 `sprites/tuanrong/evo6/palette_moon.json`。
- 分支動態：渴瞓：idle／生命感 clip 間中半瞇眼、睡帽尖跟住點頭；fall_asleep 月牙燈漸暗、sleep_loop 暗、wake 返光。靜光瞓覺 aura 漸暗同靜光 ×4。
- 預覽 `sprites/tuanrong/preview/evo6/evo6_batchF4_contact_4x.png`；工具 `tools/build_evo6_animF.py F4`（Pillow/numpy 程式繪製，無 AI）；CLIPS.json 只新增自己 key（forms.<form>、clips[].<form>、anchors.<form>、evo6F.batches.F4）；CLIPS.md EVO6F 段；備份 `_backups/pre_evo6_branches5_anim_20261031/`。
<!-- EVO6F4-LOG-END -->

<!-- EVO6F5-LOG-START -->
## 2026-10-31 — 團絨 evo6 動畫 batch F5（新支線・火苗 ember）
- 守夜者 44＋靜光 48 全套 41 clip：`evo_guard_ember` 180 幀、`evo_still_ember` 180 幀；frames／layers／emissive／kit／face_anchors（bulb＝燈中心）／atlas＋emissive。色盤 `sprites/tuanrong/evo6/palette_ember.json`。
- 分支動態：火苗閃：頭頂火苗燈／尾尖火／耳尖逐幀高低擺、火星點閃。靜光瞓覺 aura 漸暗同靜光 ×4。
- 預覽 `sprites/tuanrong/preview/evo6/evo6_batchF5_contact_4x.png`；工具 `tools/build_evo6_animF.py F5`（Pillow/numpy 程式繪製，無 AI）；CLIPS.json 只新增自己 key（forms.<form>、clips[].<form>、anchors.<form>、evo6F.batches.F5）；CLIPS.md EVO6F 段；備份 `_backups/pre_evo6_branches5_anim_20261031/`。
<!-- EVO6F5-LOG-END -->

<!-- EVO6G-LOG-START -->
## 2026-11-01 — 團絨 evo6 batch G（§7 路線清晰化）
- 絨跳燈色 8 路（螢絨唔顯示）：`sprites/tuanrong/evo6/route_clarity/palette_route_bulbs.json`＋`palette_evo_hop_<id>.json` ×8＋`atlas_evo_hop_bulbmask.png`＋`atlas_evo_hop_bulb_<id>.png` ×8；現有 evo_hop 散檔像素冇改。
- 預告 tell_<id> ×9（絨跳）：56 幀；atlas_evo_hop 重排（1024×1024，540 塊）。
- 圖鑑剪影 ×9：`route_clarity/silhouette/sil_<id>_48.png`＋`collection_route.json`。
- 預覽 `sprites/tuanrong/preview/evo6/evo6_batchG_route_clarity_4x.png`；工具 `tools/build_evo6_routeG.py`；驗證 `tools/validate_route_clarity.py`；備份 `_backups/pre_evo6_route_clarity_20261101/`。Pillow/numpy 程式繪製，無 AI。
<!-- EVO6G-LOG-END -->

<!-- SYS12B1-LOG-START -->
## 2026-11-01 — systems12 第 1 批素材
- 團絨天氣 clip：leaf_umbrella（撐葉 6 幀）＋ shiver（打冷震 4 幀）× 25 形態（sprout／radiant／soft／lumi＋evo6 21）＝ 250 幀；新 atlas `atlas_<form>_live_wx` ×3，atlas_lumi＋evo6 atlas 重排（evo_hop 連 route_clarity 重出）；舊幀像素冇改（載入對拍）。
- UI（`ui/systems12/`）：委託面板 9-slice＋行底＋checkbox ×2、委託 icon ×3（餵／淋水／陪玩）、星星碎 16／32、心聲泡框＋尾、日記頁框（普通／特別）、日記貼紙 ×6、提醒 icon ×2；`atlas_systems12_ui`。
- 天氣：`scenes/hd2d/H3/{overcast,fog}/`＋`grade_{overcast,fog}.json`＋`weather/{overcast_clouds,fog_bank}.png`＋`weather.json`（雨沿用 rain/）。
- 季節：`scenes/hd2d/seasons/<spring|summer|autumn|winter>/H1–H4/`（LUT＋預烘層＋lightmap＋grade）＋`seasons.json`（香港月份）。
- 預覽 `sprites/tuanrong/preview/systems12/`；工具 `tools/build_systems12_b1.py`＋`tools/build_systems12_b1_ui.py`；驗證 `tools/validate_systems12_b1.py`；備份 `_backups/pre_systems12_b1_20261101/`。Pillow/numpy 程式繪製，無 AI。
<!-- SYS12B1-LOG-END -->

<!-- SYS12S2-LOG-START -->
## 2026-11-01 — 季節 v2（四季一眼分得出）
- Kurt 02:12「4季唔夠明顯分別」→ 4 季 × H1–H4 全部重做場景內容（唔止 LUT）：春櫻花／粉遠樹／花瓣；夏深綠／積雲／向日葵／蟬；秋紅橙金葉／落葉堆／南瓜；冬禿枝積雪／雪地／屋頂欄杆積雪／冰柱。
- 新：`seasons/<season>/<H#>/raw/*.png`＋`palette.json`；`seasons/<season>/particles/{sheet.png,particles.json}`（花瓣／螢火蟲＋熱浪光點／落葉／雪）；`seasons.json` v2（particleOverlay、lightTint）。層格式唔變。
- 色彩：季節色喺 H1 日光空間定，經 H1→H# 仿射（最小二乘）帶入時段光；H4 夜晚同保色相縮暗各半，免淺色變飽和藍。
- 預覽：`sprites/tuanrong/preview/systems12/seasons_v1_vs_v2_compare.png`、`seasons_4x4_1x.png`、`seasons_particles_6x.png`。工具 `tools/build_seasons_v2.py`（`build_systems12_b1.py seasons`）；驗證 `tools/validate_systems12_b1.py`；備份 `_backups/pre_seasons2_20261101/`。Pillow/numpy 程式繪製，無 AI。
<!-- SYS12S2-LOG-END -->

<!-- ACC1-LOG-START -->
## 2026-11-01 — 飾品完整版 ACC1（框架＋收藏品 12＋草帽／蝴蝶結／頸巾）
- Kurt 03:14 揀咗「做完整版」，分 5 批做（`sprites/tuanrong/accessories/ACC_PLAN.md`）。今批交框架、收藏品同頭 3 件飾品。
- 框架：`tools/build_accessories.py` 逐幀由 face anchors＋剪影推導 fit（axis／top／hw／ang／hs），飾品每幀用參數重新畫，所以會跟傾側、壓扁同拉長。燈泡同莖穿過帽，洞口補描邊；bulb／bulb2 一律挖空。頸巾順住剪影畫，尾巴有慣性。月眠同菇傘用帽針版。逐形態手調集中喺 `FIT`／`HIDE`／`NECK_LIM` 表。
- 輸出：`accessories/ACCESSORIES.json`（slots／drawOrder／sizeClasses S·M·L／13 件總表／每形態 atlas＋hiddenClips）、`items/<item>/atlas_<item>_<form>.png/json` 共 75 套、`fit_<item>.json`、`ref/acc_<item>_{S,M,L}.png`。
- 數量：草帽 4524 幀（1030/1055 clip）、蝴蝶結 4674 幀（1055/1055）、頸巾 4674 幀（1055/1055）。
- 收藏品：`ui/collectibles/col_<key>_{16,32}.png`＋`_sil` 剪影、`atlas_collectibles.png/json`、`collectibles.json`（名、季節、稀有度、攞法建議）。
- 預覽：`sprites/tuanrong/preview/accessories/acc1_*.png`。驗證：`tools/validate_accessories.py`。備份：`_backups/pre_acc1_20261101/`。全部 Pillow／numpy，冇 AI，v3 色盤，alpha 0/255。
<!-- ACC1-LOG-END -->

<!-- ACC2-LOG-START -->
## 2026-11-01 — 飾品完整版 ACC2（毛冷帽／橡果帽／小皇冠＋草帽 polish）
- 依 `sprites/tuanrong/accessories/ACC_PLAN.md` 第 2 批。三件 head slot × 25 形態 × 全 clip：毛冷帽 4524 幀、橡果帽 4524 幀、小皇冠 4524 幀（各 1030/1055 clip；leaf_umbrella 收起）。
- `tools/build_accessories.py`：草帽畫法抽成通用 head drawer（`HEAD` 參數表＋`make_head_draw`）。
  - 毛冷帽：直坑針織紋、白色反邊、pompom 偏左（燈泡位喺正中），沉落頭頂多啲但唔遮眼。
  - 橡果帽：鱗片交叉紋、深啡帽邊、帽蒂（有燈泡嘅形態俾燈挖走）。
  - 小皇冠：細（0.68×頭闊），S／M 3 支尖、闊啲 5 支；64px 形態加大紅寶石、帶底刻紋同尖頂小珠。
  - 月眠／菇傘 4 個形態逐件出帽針版。
- 頭飾穩定化（`stabilise_head`，所有 head 飾品共用）：頭頂點橫向對返頭頂中點（±2px），相對身體 bbox 做 3-tap 平滑；ws 用 median-3，夾 0.85–1.12；傾角每幀變化 ≤8°，clip 第一幀相對 idle 計。
  - 草帽 lookup_tip_04 最大傾角跳由 13.2° 降到 8.0°，闊度跳由 6 降到 2 px；turn_back_02 闊度跳由 14 降到 8 px，位移由 6.4 降到 4.2 px；getup_01 傾角跳由 9.9° 降到 8.0°，闊度跳由 10 降到 4 px。
- 草帽其他 polish：月眠守護帽針 sc 1.45→1.8；lumi 系 3 個形態只挖葉（綠）同葉描邊，莖同淺紫毛唔挖，帽身唔再有碎洞；guard／still_lumi 草帽唔加織紋。
- validator：head slot 通用化，加咗傾角跳 ≤8° 同 ws 0.85–1.12 檢查。
- 預覽：`sprites/tuanrong/preview/accessories/acc2_*.png`，包括草帽 before／after 兩張。備份：`_backups/pre_acc2_20261101/`。全部 Pillow／numpy，冇 AI，v3 色盤，alpha 0/255。
<!-- ACC2-LOG-END -->

<!-- ACC3-LOG-START -->
## 2026-11-01 — 飾品完整版 ACC3（星星髮夾／櫻花髮飾／圓框眼鏡）
- 依 `sprites/tuanrong/accessories/ACC_PLAN.md` 第 3 批，三件 × 25 形態 × 全 clip：
  - 星星髮夾 4674 幀（1055/1055 clip）
  - 櫻花髮飾 4674 幀（1055/1055 clip）
  - 圓框眼鏡 4353 幀（979/1055 clip）
- side_l：`head_l` 用兩眼中垂線鏡像 head_r（側面眼距 <0.75×idle 就用 fit 中軸），月眠新月形態唔會再跌落月牙底。細尺寸星星（7×8／9×10）同櫻花（7×7／9×9）用手繪模板，避免糊成一舊。
- 眼鏡：
  - 鏡片中心跟 eyeL／eyeR＋眼 blob 偏移，半軸由眼 blob 半寬／半高＋1.5，傾角跟兩眼連線。
  - L 級（64px）框粗 2＋內圈 orange_d，其餘 1；框色 orange_dd；r≥3.5 加白色反光點。
  - ¾ 圓框：近口內下角開口，唔會撞腮紅／口；evo_dot 太細，用上半框。
  - 每個 clip 逐級試候選（收窄／壓扁／上移／向外，再試逐幀跟眼），全部幀過晒先用；眨眼／閉眼／sleep clip 鏡片大細固定（用 clip 同 idle 最大眼 blob）。
  - 收起 clip 統計（形態數）：turn_back×24、lookup_tip×19、swat×18、emo_sleepy×1、walk_drag×1、reunion_happy×1、walk×1、play×1、pot_bump×1、eat×1、walk_happy×1、sniff×1、nuzzle×1、rush×1、smug_pose×1、shiver×1、lookup×1、scratch×1。
- validator：加 side_l（bbox 中心近 head_l）同 face（faceVisible、鏡片中點 ≤2.5px、傾角 ≤12°、L 級框粗 2、框唔壓眼 blob）檢查。
- 預覽：`sprites/tuanrong/preview/accessories/acc3_*.png`（包括 `acc3_glasses_face_a／b_6x` 臉部特寫）。備份：`_backups/pre_acc3_20261101/`。全部 Pillow／numpy，冇 AI，v3 色盤，alpha 0/255。
<!-- ACC3-LOG-END -->

<!-- ACC4-LOG-START -->
## 2026-11-01 — 飾品完整版 ACC4（葉仔領／燈泡小鈴／燈泡光環／睡帽）
- 依 `sprites/tuanrong/accessories/ACC_PLAN.md` 第 4 批，四件 × 25 形態 × 全 clip：
  - 葉仔領 4,674 幀（1,055/1,055 clip）
  - 燈泡小鈴 4,674 幀（1,055/1,055 clip）
  - 燈泡光環 4,674 幀（1,055/1,055 clip）
  - 睡帽 4,524 幀（1,030/1,055 clip）
- 燈泡錨點：evo 形態用非 v3 色，靠色量燈泡會漏落個頭，所以改用手調嘅玻璃半徑表 `BR`。
  - evo_dot／evo_sprout 冇燈泡：鈴吊喺頭頂芽右邊，光環放頭頂。
  - lumi 系（觸角）、dust（尾燈）、moon（新月）嘅 bulb 唔喺頭頂：光環放頭頂最高點上面，保持水平；鈴照吊喺佢哋嘅 bulb。
- 光環：橢圓環，後半 GOLDD、前半 GOLD，L 級有白反光。環洞用暫時 label 填住先 render，所以唔會描內邊，洞係透明。高跳幀會貼住 PAD 8 頂。
- 小鈴：suzu 手繪模板（5／7／9），金身、中間坑、下開口，頂有紅繩結。阻尼擺動夾 ±25°，每幀最多轉 14°。loop clip 跑兩轉取第二轉，所以頭尾接得順。
- 葉仔領：頸位同頸巾一樣。尖頭葉兩隻綠交替（有分界），前右有粉紅細花＋金芯。
- 睡帽：
  - zzz 紫圓錐，白斜紋，白帽邊，L 級有金星。燈泡由帽頂個洞穿出嚟（head_cut）。
  - 長尾由帽尖垂落，有白波波。尾擺用阻尼彈簧（vx＋vy），夾 ±30°，每幀 ≤14°。
  - 尾撞五官或者出 padding，就先向外擺（dphi），再唔得就縮短（tailK）。統計：dphi0/tailK1.0 4466、dphi-15/tailK1.0 44、dphi-30/tailK1.0 14。
  - shroom／moon 用細 hatpin 版。收起 clip：leaf_umbrella×25。
- ACC1–3 輸出 byte-identical（md5 對過 `_backups/pre_acc4_20261101/`）。
- validator 加咗以下檢查：
  - 葉仔領頂行 = ny
  - 鈴中心跟 fit，喺燈泡下面，擺幅 ≤25°，每幀 ≤14°
  - 光環中心 ±1.6，喺燈泡或者頭頂上面
  - 睡帽位跟 fit，傾角每幀 ≤8°，尾擺 ≤30°，每幀 ≤14°，尾端有波波
- 預覽：`sprites/tuanrong/preview/accessories/acc4_*.png`。備份：`_backups/pre_acc4_20261101/`。全部 Pillow／numpy 做，冇用 AI，v3 色盤，alpha 0/255。
<!-- ACC4-LOG-END -->

<!-- ACC5-LOG-START -->
## 2026-11-01 — 飾品完整版 ACC5（收尾：同戴衝突、contact sheet、總覆核、定稿）
- 同戴衝突（`sprites/tuanrong/accessories/COMBOS.json`）：
  - 每 slot ≤1、最多 5 件；讓位次序 halo > bell > starclip > sakura > bow > leafcollar > scarf > glasses > straw > beanie > acorn > crown > nightcap（排先嗰件讓）。
  - 衝突＝halo 任何重疊，或者被遮嗰件被蓋 >30%（鈴對 50%）。讓位件逐 clip 試細整數位移（成段 clip 全部幀都要過、唔遮五官／燈泡、唔出畫布、除光環外仲要貼住身體或者對方），唔得就成段收起。
  - 1,625 對（item 對 × 形態），344 對有規則；4,473 個 clip 位移、426 個 clip 收起；驗咗 294,654 幀，有衝突 12,895 幀。
  - 多啲：straw+halo（位移 500／收起 1）、halo+nightcap（位移 447／收起 5）、acorn+sakura（位移 372／收起 4）、beanie+halo（位移 354／收起 1）、acorn+halo（位移 315／收起 0）、straw+sakura（位移 298／收起 4）、beanie+sakura（位移 289／收起 1）、crown+halo（位移 284／收起 0）。
  - 594 個合法同戴組合 × 25 形態全部再驗：兩兩套規則後仲有 391 幀殘留（鈴位移後撞蝴蝶結等），所以加 `outfitOverrides`：279 個（組合 × clip）收起 {'halo': 37, 'bell': 242}；再驗 0 殘留。
- 背面鏡像：turn_back_01（24 形態 faceVisible=false）蝴蝶結 side_r 改去左邊、髮夾／髮飾 side_l 改去右邊（模板左右翻）。帽針頭飾跟返形態本身頂帽，冇鏡像。
- 月眠帽針睡帽：改用直身細圓錐 pincap（白間、白帽邊、W≥11 有金點），尾垂向右下，唔再似羽毛；guard_moon／still_moon 42/43 clip（leaf_umbrella 收起）。
- dust 小鈴：尾燈太近地面（鈴底離地 < max(6, 25%S)）→ guard_dust／still_dust 改吊頭頂（base `top_low`），43/43 clip。
- evo_dot 眼鏡：ACC3 半框似眉毛 → 改做「推上額頭」全圓框（細鏡片、兩片一齊沿眼線法線升到框底喺眼頂上 ≥1px、≥50% 貼頭），40/41 clip（只係 turn_back 收起）。
- 可見度總覆核：撐葉傘：葉蓋住頭頂，頭飾收起 ×125、鏡框會壓到眼 ×36、faceVisible=false ×24、會遮五官 ×3、眼距 ×2。
- emissive：飾品冇自己嘅 emissive；引擎 emissive 畫喺飾品之後但用飾品 alpha 聯集遮走（發光唔透過帽），燈泡 ±1 一直挖空。平均遮咗：sakura 12.7%、nightcap 10.0%、beanie 9.0%、starclip 8.0%、acorn 7.4%、straw 7.2%、bow 5.8%、leafcollar 4.5%、scarf 4.5%、bell 3.7%、crown 3.3%、halo 2.0%、glasses 0.7%。sprout／radiant／soft 冇 emissive。
- 改動範圍：bow／starclip／sakura 嘅 turn_back（24 形態）、moon 睡帽（2）、dust 鈴（2）、dot 眼鏡（1）；其他 atlas byte-identical（md5 對過 `_backups/pre_acc5_20261101/`）。
- 同場：route 提示字跟遊策新版更新（`build_evo6_routeG.py --hints`、`validate_route_clarity.py` 檢查新字＋舊字唔可以再出現）。
- 預覽：`sprites/tuanrong/preview/accessories/acc5_*.png`（25×13 contact sheet idle／walk_03、同戴示範、背面、moon 睡帽、dust 鈴、dot 眼鏡）。全部 Pillow／numpy，冇用 AI，v3 色盤，alpha 0/255。
<!-- ACC5-LOG-END -->
