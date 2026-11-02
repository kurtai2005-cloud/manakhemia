# 6c 夢遊 V3-A 光影（第 6 批）

底：`art/breakthrough/6c`（commit af5b4821）原檔冇郁；`dream6c.json`、key、尺寸照用。V3 喺 `6c/v3/`，入口 `dream6c_v3.json`。
生成：`art-pet/tools/build_walkdream_v3.py dream`；驗證：`validate_walkdream_v3.py`；預覽：`preview_walkdream_v3.py`。

## 夢遊中寵物光＝0
`dream6c_v3.json#pets.<pid>.petLight = 0`、`glow = off`（跟 layout_hd2d_v3.json#petGlow dreamEnter／dreaming 0）。
入夢第 0 幀開始 fadeOut 600ms easeInQuad；出夢最後一幀 fadeIn 400ms easeOutQuad＋150ms pulse 1→1.15→1。
月光 rim（#c8c0ff .5）、星、tile 發光細節、菇燈係**場景光**，照開。dream_walk／nightcap／frag／icon 原樣用。

## dream_bg（585×1266 @3x）
`dream_bg/sky@3x`（全幅）、`light_add@3x`（星雲／銀河帶、月暈、淡月光柱，lighter）、`emissive@3x`（星，0/255，twinkle 清單喺 json）、
`moon@3x`（0/255＋rim，喺 vignette 上面）、`clouds@3x`（前景雲，月光 rim）、`mist@3x`、`lightmap@3x`、`bloom@3x`、`vignette@3x`、`lut.png`；
`dream_bg_v3@3x.png`／`dream_bg_v3.png`（195×422）＝預合成。emitters：dreamMote、shootingStar（程序畫）。

## tiles（四套：forest 夢森林／lake 星湖／toy 玩具屋／star 星空頂）
`tiles/tile_<th>_v3@3x.png`（672×168＝4 款 168，alpha 0/255，外形同原：左上 key light、邊 AO、中心月光池、rim）；
`_glow@3x`（lighter 真 alpha）、`_emissive@3x`（mask）；`tile_lake_caustic@3x.png`（4 幀直條）；`tile_reveal_glow@3x.png`（216×216 已揭格邊光）。flicker 參數喺 json。

## fog
`tiles/fog_v3@3x.png`：8 幀流霧（1344×168，4fps，真 alpha，原外形＋雲紋細節）；`fog_reveal@3x.png`：8 幀揭開溶解＋淡紫光邊（16fps）；`fog_v3.png` 1x。

## transition
`transition/transition_in_v3_00..09@3x.png`（585×1266，8fps，真 alpha）：原 10 幀外形、邊羽化＋淡紫光邊；幀 7–9 加月 flare。enter 0→9、exit 9→0。

## 夢卡（21 張含 card_back）
`cards/card_<id>_v3@3x.png`（84×108，0/255：金框左上 spec＋斜光、窗光 AO）；`card_glow_<forest|lake|toy|star|back>@3x.png`（144×168 光暈）；`card_shine@3x.png`（8 幀掃光）。
