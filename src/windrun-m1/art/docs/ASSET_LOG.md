# ASSET_LOG（來源記錄）— 風野競走 M1 垂直切片
| 日期（HKT） | 資產 | 來源 | 腳本／工具 | 修整 | 相似度檢查 |
|---|---|---|---|---|---|
| 2026-10-26 | 色盤（野靈 32、苔坡環境、地形、技能、適性） | 自訂 HEX（對齊 art-pet/HD2D_STYLE.md 色系，另擴充） | `tools/wind_palette.py`、`build_palettes.py` | — | n/a |
| 2026-10-26 | 野靈「窄樑貓」20 幀、圖集、預覽、contact sheet | **全程式化自製**（Pillow／numpy；橢圓／膠囊／多邊形遮罩＋cel 偏移上色＋2 骨 IK 步態）；名稱／造型原創（v2 一頁設計名單之野靈；石板藍貓＋青色風巾＋條紋） | `tools/build_narrowcat.py` | 迭代 3 次（腿長／身高、尾巴分段、光環範圍） | 待做：contact_sheet.png 以圖搜圖（TinEye／Bing／Lens），結果補入此表 |
| 2026-10-26 | 苔坡 sky_far×3、mid、track、fore、emissive、lightmap×4、草屑 4 幀、lowfx、vignette | **全程式化自製**（Pillow／numpy；三倍寬畫布取中段保證無縫；固定亂數種子 20261026） | `tools/build_mossy_slope.py` | 迭代 2 次（bloom 過曝、野靈縮放 4x→6x） | 場景為通用森林／苔地元素，無特定來源；風格板上線前一併做風格比對 |
| 2026-10-26 | 風格板 style_board_mossy_slope*.png | 程式化合成（景深／bloom／tilt-shift／光圖／vignette 模擬） | `build_mossy_slope.py`（build_board） | — | n/a |
**AI 生成圖：0**（GenerateImage 未用）。第三方／光碟素材：0。

## 相似度檢查：窄樑貓（2026-10-26）
- TinEye：拼圖與第一幀皆 0 matches。
- Google Lens（第一幀）：無 exact match；視覺相似只係一般藍灰像素貓（LKG wiki、Warrior Cats 同人、Unity 像素動物包等），無官方 IP 撞款。
- Bing Visual Search：上傳失敗，未有結果。
- 判斷：撞款風險 低。截圖：similarity/。
- 待辦：其餘 7 隻野靈各做一次；Bing 改日再試。

## 晨苔鎮補充批次（2026-10-26，遊美）
| 日期（HKT） | 資產 | 來源 | 腳本／工具 | 修整 | 相似度檢查 |
|---|---|---|---|---|---|
| 2026-10-26 | 晨苔鎮環境色盤 32 色＋四時段參數 | 自訂 HEX（沿用野靈／苔坡色系延伸：苔綠、泥棕、苔石、青瓦、水、燈光） | `tools/town_palette.py`、`build_town_palette.py` | — | n/a |
| 2026-10-26 | `tiles/morningmoss/` tileset（158 tile）、extruded／emissive／collision 衍生、`tilemap_corner.json`（20x15）、預覽 | **全程式化自製**（Pillow／numpy；坐標 hash 變體、4-bit autotile；固定種子） | `tools/build_town_tiles.py`、`town_art.py`、`pixkit_town.py` | 迭代 2 次（草地雜訊降噪、石板對比降低、屋頂苔斑改塊狀、水窪移上泥路） | 場景為通用歐式鄉村石屋／泥路元素，無特定來源 |
| 2026-10-26 | `sprites/player/` 32px 玩家（4 向×(走 4＋idle 1)＝20 幀）＋ sheet／atlas／GIF／8x 預覽／contact sheet | **全程式化自製**（橢圓／膠囊／多邊形遮罩＋cel 偏移上色）；造型原創：寬簷橙帽＋黃羽＋青綠披風＋奶色上衣 | `tools/build_player.py`、`charkit.py` | 迭代 3 次（比例：帽簷縮、腿加長；側面臉部／頭髮分離；眼睛位移離外框） | **待做**：`player_contact_sheet.png` 以圖搜圖（TinEye／Lens／Bing），結果補入此表；暫憑造型判斷：無鴨舌帽、無紅白、無頭巾，撞款風險預估低 |
| 2026-10-26 | `sprites/narrowcat/town48/` 48px 窄樑貓 town 跟隨（idle 2、walk 4、左右鏡像＝12 幀） | 沿用 `build_narrowcat.py` 之 `render()` 與野靈色盤；以**幾何縮放 monkeypatch**（K=0.64，capsule 半徑×1.22，眼睛改細）重繪，非位圖縮小 | `tools/build_narrowcat_town48.py` | 迭代 2 次（K 0.60→0.64、腿／風巾加粗） | 同 64px 版（已有結果，見上）；48px 僅縮放重繪，無新造型 |
| 2026-10-26 | `style_board_morningmoss_corner*.png`、`scale_reference.png` | 程式化合成（剪切投影／光軸／晨霧／光圖／bloom／tilt-shift／vignette 模擬） | `tools/build_town_board.py` | 迭代 3 次（光源 rgb 比例錯致過曝、光軸／霧強度與形狀、夜間亮度） | n/a |
**本批 AI 生成圖：0**（GenerateImage 未用）。第三方／光碟素材：0。

## 相似度檢查：玩家角色（player，32px，橙闊邊帽＋青綠披風）— 2026-10-26
- TinEye（整張 sheet＋正面裁圖）：0 matches。
- Google Lens（裁圖）：無 exact match；僅泛 chibi／農夫像素角色（AI Overview 提及 My Time at Portia 嘅 Alice，屬風格／配色推測，視覺上只係闊邊帽＋青綠）。
- 無撞 Pokémon／Link／Stardew／Graal。風險：低（只有「帽＋chibi」通用風格重疊）。
- 截圖：similarity/ 下 run01 舊檔；今次截圖未能存檔，結果以本記錄為準。
- 未做：town 貓 48px、其餘 7 野靈。

## 晨苔鎮 v0.2 擴充（batch2 tile／地標／全鎮示範圖）— 2026-10-26
| 日期 | 資產 | 來源／做法 | 腳本 | 迭代 | AI 圖 |
|---|---|---|---|---|---|
| 2026-10-26 | `tiles/morningmoss/tileset_morningmoss_b2*`（181 新 tile：石板／廣場徽章／車轍／泥↔石轉接／House B 木框屋／House C 店舖／House A 變體／攤檔／井／16 款籬笆／石階堤坡／高草蕨（2 幀）／橋涵／花蘆菇／箱桶告示牌郵箱晾衣繩／燈籠 day↔lit） | **全程式化自製**（Pillow／numpy；固定種子；多邊形遮罩＋32 色盤；wrap-around 繪製保證 seamless；籬笆用 padded canvas 再裁切） | `tools/town_art2.py`、`build_town_tiles_batch2.py` | 車轍由「雙軌」改成斷續淺痕（原版似鐵軌）；蕨頂葉加長 | 0 |
| 2026-10-26 | `landmarks/`（報名處 6x6、迴風場入口 12x7、路標 1x2；day／lit×4 幀；158 tile、atlas、24 幀 PNG） | **全程式化自製**；造型原創（風渦徽章、青瓦、橫條招牌、風向標） | `tools/landmark_art.py`、`build_landmarks.py` | — | 0 |
| 2026-10-26 | `tilemap_town.json`（40x30）＋`tileset_all_gids.json`＋1x／4x／debug 預覽 | ASCII 版面→autotile（泥／石／溝／塘）→建築／地標／物件放置；events 40 個（含 light） | `tools/build_town_map.py` | 4 輪：house_A 牆名 bug；梯台改位（原本石階通落店舖屋頂）；廣場徽章移離邊行；散布花唔蓋石階 | 0 |
| 2026-10-26 | `tracks/town/style_board_morningmoss_town{,_night,_nopost}.png`（2560x1920） | 程式化合成，同 corner board 流程；sprite bloom ×0.70；夜景用 swap_day_to_lit＋light events | `tools/build_town_board_town.py` | morning 1 輪；night 2 輪（arena 口燈光疊加過曝 → 單盞強度 ×0.55、縮半徑、略去重疊燈） | 0 |
| 2026-10-26 | 驗證 | JSON／gid／事件、32 色盤純度、名稱 gid 唯一、seamless、鄰格材質、可達性、舊檔 md5 | `tools/validate_town.py` | — | — |
**本批 AI 生成圖：0**（GenerateImage 未用）。第三方／光碟素材：0。未入 repo、未推 GitHub、零費用。
**偏離**：collision tileset 喺新圖 firstgid=545（舊圖 193）；屋頂放 occlusion；風車位改院子；商店移東南、報名處佔東北（待遊策確認）。
**色盤例外**：預覽／board／debug 疊圖不受 32 色限制；其餘 tileset／地標／frames／atlas 全部純 32 色（已驗證）。

