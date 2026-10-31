# 生命感第二段（s2）— 遊美 2026-10-31 HKT

個性：「蠢蠢地但覺得自己好醒」。3 form（sprout 32×32 pivot (16,29)／radiant、soft 64×64 pivot (32,61)），朝右，31 色、alpha 0/255、無 AA，Pillow+numpy 程式繪製。

| clip | 幀／fps | 備註 |
|---|---|---|
| smug_pose | 4／6，最後幀 holdLast_s 0.8 | 撲空落地 → 企直 → 挺胸仰頭合眼 ω 口、雙手叉腰；第 4 幀頭頂閃一下（烙入）。preset `smug` = eyes sleepy + mouth squint(ω) |
| act_cool | 4／5 | 別過頭側眼（ft）→ 輕咳（咳氣烙入，向左）→ 拍拍肚（塵烙入）×2 |
| lookup_tip | 4／6 | 接 lookup 第 3 幀姿勢，以後腳為軸向後轉 5°/10°/16° → 一屁股坐低（12°）；next getup |
| getup | 4／6 | 坐低（同 lookup_tip_04）→ 後手撐地 angry 用力臉 → 彈起 → 企定；next act_cool |
| sniff_itch | 2／6 | 鼻貼地抽（鼻癢線烙入）→ 抬頭瞇眼；next sneeze |
| fx_bug | 3 幀 8×8／10fps | `fx/atlas_fx_live.*`，anim 01→02→03→02，pivot (4,4)，朝右 |

- atlas：第二段另出 `atlas_<form>_live_s2.png/json`（sprout 1024×128、radiant/soft 1024×256，各 36 塊）；第一段 `atlas_<form>_live.*` 逐 byte 不變；五官 kit 仍喺 `atlas_<form>_live`。
- 錨點：CLIPS.json `clips[].anchors[form]`／`face_anchors.json`（lookup_tip／getup 錨點已跟 rot 轉）。
- 預覽：`preview/<form>/<clip>_strip_8x.png`（行 1 完整幀；行 2 noface＋錨點點：藍＝眼、粉＝口、綠＝head_r、紅＝bulb）、`<clip>_8x.gif`、`preview/fx_bug_16x.png`、`live_s2_contact_4x.png`。

## walk 腳步幀（量度 frames/<form>/walk_*.png）
- walk_happy：**落地＝索引 0、3**（唔係 2、5）。索引 0/3 雙腳著地（radiant 腳底 y61、sprout y30）＋壓扁（頂 y11）；索引 1/4 升起（腳 y57）；索引 2/5 係**半空最高點**（腳 y55，離地 6px；sprout 3px）。即係 2→3、5→0 落地，音效／塵喺 3 同 0 出。
- walk_drag：**落腳（腳放返落地）＝索引 2、5**；索引 1 左腳拖起 1px、索引 4 右腳拖起 1px，塵烙喺 1、4（「第 2／5 幀起塵」＝索引 1、4）。step_drag 擦地聲建議跟塵出 1、4；如要「落腳」實聲用 2、5。身體高度 6 幀一樣（腳以外冇上下）。
