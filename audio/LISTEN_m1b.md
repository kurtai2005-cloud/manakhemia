# 聽感表 — M1b 功能音＋狩獵 BGM（v1，2026-11-11）

郵局／廚房／圖鑑／家具／狩獵 SFX，同 `bgm_hunt_loop`。SFX 全部原創程式合成；BGM 用 VCSL CC0 豎琴／鐘琴／直笛做樂器（樂句同合成層係原創）。**未有人聽過**，只做過數值檢查。

重音喺 0 ms（hook 觸發即播）。a/b 交替或隨機，唔好連續兩次同一個。欣賞模式唔靜音呢批聲（只有 `sfx_need_warning` 受 §0.5 限）。

| 檔 | 應該聽落係 | Kurt：好／要改 | 備註 |
|---|---|---|---|
| `sfx_post_letter_send` | 信紙甩入郵筒：短氣流＋木篤，唔似 letter_drop 嘅短放低 |  | -14 LUFS20。派工去郵局即播。 |
| `sfx_post_letter_receive` | 信落到枱＋細蠟印，略上行，唔似 ui8_confirm 落章 |  | 郵局 READY／門光亮時播。 |
| `sfx_kitchen_cook_start` | 暖鍋沿一記＋薄蒸汽，唔似 feed_meal 咀嚼 |  | 派工去廚房。 |
| `sfx_kitchen_stir_loop` | 短木匙攪拌，0.500 s 可循環；唔刺耳 |  | -18。檔名已含 `_loop`，自動循環。 |
| `sfx_kitchen_cook_done` | 鍋蓋中音叮，唔用 C7 鋼片琴簇 |  | 廚房 READY；建議同時停攪拌 loop。 |
| `sfx_codex_page_flip_a`／`_b` | 翻一頁紙（摩擦＋氣流），長過 letter 聲，冇鈴 |  | 開圖鑑；a/b 交替。建議代替 popup_open，以免兩聲疊。 |
| `sfx_codex_new_entry` | 紙上一記＋上行五度暖鈴，唔似 confirm／btn_sparkle |  | 新解鎖；一次多個只播一次；開局 unlock 唔好播。 |
| `sfx_furn_pickup` | 提起偏重木器，重過 sfx_pet_pickup |  | M1b 未有拖曳 UX，檔先做低。 |
| `sfx_furn_place_a`／`_b` | 實木放下，a 偏低、b 稍亮 |  | place／一鍵擺；連續多件最多 3 下、間隔 ≥120 ms。 |
| `sfx_furn_buy` | 短購買鐘（G4 為主），唔係 toast 用嘅 ui8_coin 跳 |  | 成功 t=0；隨即 place 建議遲 120–160 ms。 |
| `sfx_hunt_pounce_a`／`_b` | 撲出體勢氣流＋軟墊，唔代替 clip 嘅 jump／land |  | 連住現有 sfx_pet_jump／step_hop。 |
| `sfx_hunt_enter` | 入草原：草沙＋兩粒暖撥弦，短過 treasure_hunt，唔似光幕 |  | PHASE_HUNT；同時 crossfade `bgm_hunt_loop`。 |
| `bgm_hunt_loop` | 輕冒險但仍然暖：豎琴分解和弦、直笛短句、疏落鐘琴、軟低音同輕打擊 |  | -16 LUFS，108 BPM、16 小節無縫。離開草原 crossfade 返照顧 BGM。 |

狩獵撲中用現有 `sfx_mg_catch` → `sfx_critter_transform` → `sfx_critter_roll`；撲唔中（code 未有分支）用 `sfx_critter_startle`＋`sfx_critter_shake`，**唔用** `sfx_mg_miss`。完整對照見 `audio/m1b_sfx_map.json` 同 README §7.14。
