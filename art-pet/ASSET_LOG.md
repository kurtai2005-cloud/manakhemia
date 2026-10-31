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
{b_}
