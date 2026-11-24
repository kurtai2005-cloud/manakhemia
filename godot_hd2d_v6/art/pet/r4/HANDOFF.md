# r4 parent handoff

結果：側向六幀已重畫成短腳前後交替，兩次plant +6/+6；可作parent親看後的工程實景候選，未接入／未驗收。

- 包：`/workspace/pet_walk_art_r4/`
- keep鏡像：`/home/box/keep/godot/hd2d-pilot-v6/pet_walk_art_r4/`
- 接入用圖唯一位置：`frames/r4/`（21張64×64）；不要拿evidence或聯絡表當圖。
- 規格／限制／完整兩腳表：`SPEC.md`；機讀：`CLIP.json`、`MEASUREMENTS.json`、`QA.json`。
- parent先看：`previews/contact_side_walk_r4_8x.png`、`evidence/side_feet_16x.png`、`evidence/side_identity_visible_16x.png`、`evidence/side_complete_world_trajectory.png`、`evidence/side_travel_grid_2wu_6x.png`及20/48節奏GIF。
- 只改side腳與肚底rows58..62；0..57身體/臉/球像素一致，12色；front/back所有檔byte不變，front idle仍認可原圖。
- side_idle＝新contact01；loop6、stride12wu，fps=6*實際速度/12；20→10fps，48→24fps，速度沒改。
- 誠實限制：0只係side純X採樣鎖定，含跨圈；幀間連續root量化微滑<2wu。48每秒8步可能太急；遠腳02被遮到只剩1足底像素，低倍率可讀性未驗；front/back只投影，斜向／3D相機投影未驗。停步硬回contact會有相位snap風險。
- `(32,61)`是舊layout anchor，不是足底；接觸底邊63，仍比anchor低2px；不要求改rig。SPEC解釋像素中心+0.5慣例。
- 沒改任何repo、工程、PC、export、場景、引擎或鏡頭。未傳訊、未花錢、未做APK。r1–r3未動；只追加GAPS自段。
- 沒叫遊程接入。由parent親看再決定是否交遊程實景驗證；不把此包當發布完成。
- 來源已定位，權利未獨立核證；沒有法律／商用保證。
