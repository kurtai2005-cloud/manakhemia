# 聽感表 — 寵物／訪客／小動物動作音（v1，2026-11-11）

試聽合輯（**唔入遊戲**）：`sfx/_preview_pet_anim.ogg`（26.102 s，42 段，中間 0.4 s 靜音）。次序同下表。全部原創程式合成；**未有人聽過**，只做過數值檢查。

規則備忘：`foley`＝所有角色共用，執行時按體型 `playbackRate` S 1.12／M 1.00／L 0.88。`voice`＝每角色一檔；而家只有團絨，細佬／訪客 fallback＝團絨檔＋體型音高。新檔 accent 喺 0 ms（約 10–20 ms 到能量峰）。

| 檔（合輯次序） | 應該聽落係 | Kurt：好／要改 | 備註 |
|---|---|---|---|
| `sfx_pet_step_walk_a` | 普通行路：軟肉墊踏地一下，輕、短 |  | foley，-22。要同 hop（彈）／drag（擦）／plod（重）分開。
| `sfx_pet_step_walk_b` | 同上，略低略鈍嘅另一步 |  | 同 a 交替（carry_fruit 0／300 ms）。
| `sfx_pet_jump_a` | 起跳蹬地：短「噗」＋輕輕向上 |  | foley。唔係落地。
| `sfx_pet_jump_b` | 同上，略低 |  | pounce／cheer 共用。
| `sfx_pet_step_hop_a` | （現有）蹦跳落地，軟彈「噗」 |  | 已有 hook，未改檔。
| `sfx_pet_step_hop_b` | （現有）同上，略高 |  | 
| `sfx_pet_grass_rustle_a` | 肉墊撥入草叢，開頭最密嘅葉沙 |  | foley。手機喇叭要聽得到低少少嘅「入草」。
| `sfx_pet_grass_rustle_b` | 同上，略厚 |  | 
| `sfx_pet_letter_drop_a` | 信封滑入信箱：紙沙＋細「篤」 |  | foley。
| `sfx_pet_letter_drop_b` | 同上，略低 |  | 
| `sfx_pet_clap_a` | 軟肉墊拍一下，悶、短，唔似人拍手 |  | foley。
| `sfx_pet_clap_b` | 兩下軟拍 |  | 
| `sfx_pet_pickup_a` | 執起一片葉：細提＋葉沙 |  | 循環 idle 750 ms，要夠細聲先唔煩。
| `sfx_pet_pickup_b` | 同上，略低 |  | 
| `sfx_pet_place_a` | 放低葉子，軟落地一下 |  | 同上，循環。
| `sfx_pet_place_b` | 同上，略低 |  | 
| `sfx_pet_reach_a` | 身體前傾伸爪，毛皮輕 sweep，冇口型聲 |  | 循環 750 ms。有「咦？」就變 voice。
| `sfx_pet_reach_b` | 同上，略低 |  | 
| `sfx_pet_stretch_a` | 拉到最高再放鬆嘅身體聲（唔係呵欠、冇「啊～」） |  | foley，-20。MOTION 註明唔借用 yawn。
| `sfx_pet_stretch_b` | 同上，略低 |  | 
| `sfx_pet_proud_a` | 挺胸叉腰：胸腔輕「噗」＋爪就位 |  | 唔好變歡呼。
| `sfx_pet_proud_b` | 同上，略低 |  | 
| `sfx_pet_point_a` | 伸臂指向：短 sweep＋一粒細叮 |  | 
| `sfx_pet_point_b` | 同上，略低 |  | 
| `sfx_pet_scratch_a` | （現有）抓癢沙沙，快、約 6 下 |  | 已有 hook；accent＝起音。
| `sfx_pet_scratch_b` | （現有）同上，慢、厚、約 5 下 |  | 
| `sfx_pet_happy` | （現有）三音上行「啾啾啾～」 |  | voice，團絨。cheer 跳到最高。細佬／訪客尚未做。
| `sfx_pet_yawn` | （現有）吸氣 → 呵欠 → 嘆氣 |  | voice，團絨。要 preroll 600 ms 先對到峰。
| `sfx_critter_startle_a` | 小動物身體一縮，短、軟（唔係叫聲） |  | 四種共用。只喺進入 scared 播一次。
| `sfx_critter_startle_b` | 同上，略低 |  | 
| `sfx_critter_shake_a` | 左右抖兩三次，細、密 |  | 變成果前。
| `sfx_critter_shake_b` | 同上，略慢 |  | 
| `sfx_critter_transform_a` | 成果瞬間：柔和短铃＋暖身，唔好似 UI 鈴 |  | -20。四種共用。
| `sfx_critter_transform_b` | 同上，略低 |  | 
| `sfx_critter_roll_a` | 果實碌走，幾下愈嚟愈細嘅軟「篤」 |  | 
| `sfx_critter_roll_b` | 同上，略低 |  | 
| `sfx_visitor_offer_letter` | 鞠躬遞信：紙沙＋身低 |  | 蝸牛郵差。loop，建議唔每圈都響。
| `sfx_visitor_offer_seed` | 奉上種子：細有機「篤」 |  | 蘑菇婆婆。同遞信分開。
| `sfx_visitor_nod_a` | 點頭最低：軟「篤」 |  | 
| `sfx_visitor_nod_b` | 同上，略低 |  | 
| `sfx_visitor_rattle_a` | 螢火瓶輕搖：瓶身＋裏面幾粒 |  | 一圈兩下（250／500），交替 a/b。
| `sfx_visitor_rattle_b` | 同上，另一邊、略少幾粒 |  | 

建議靜音、合輯冇收：`idle_lively`／`hop_peak`（落地已有 step_hop）。
