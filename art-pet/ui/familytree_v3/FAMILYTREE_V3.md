# 族譜 V3-A（第 7 批）

依 `docs-gdd/family-work-scenes-v1.md` §1（族譜）同 §2.1 族譜美術清單；規格 V3-A（Kurt 已批）：金光深藍磨砂＋1.5px 金幼線、Noto CJK TC（最細 18@3x）、對比 ≥4.5、@3x 烘焙光影＋粒子。
全部 Pillow／numpy 程序化，冇 AI 圖；唔用 Fusion Pixel。sprite（皇冠、蛋、頭像、粒子）alpha 0/255；UI／光影層真 alpha。

- 入口：`familytree_v3.json`（parts／backgrounds／fx／stamps／relations／nodeRules／petGlow／achievements／rewards／layout／hits／mockups）
- demo：`family_demo.json`（GDD §1.6 欄位＋`derived` 關係）
- 生成：`tools/build_familytree_v3.py`；驗證：`tools/validate_familytree_v3.py` → `validation.json`；預覽：`tools/preview_familytree_v3.py`
- 畫布 585×1266 @3x；bands 0→126→1044→1266（split 0→42→348→422 ×3）：頂＝返回／標題／「全家｜只睇直系」；中＝族譜；底＝成就列＋掣

## §2.1 清單對照
| GDD | 檔 |
|---|---|
| 節點框 ×2 | `node_round_{live,gray,sel}`（團絨圓框）、`node_leaf_{live,gray,sel}`（細佬葉框：TL／BR 尖＋葉柄）、`node_*_mask`（頭像窗 96） |
| 關係章 ×3 | `stamp_chuan` 傳（朱）、`stamp_zu` 祖（銅）、`stamp_wu` 屋（藍＋屋角） |
| 線 ×4 | `line_gen_{h,v}`＋`line_arrow`＋`line_joint`（金實線、向下箭咀）、`line_sib_{h,v}`（銀虛線）、`line_house_{h,v}`＋`icon_house`（淺藍點線）、`line_anc_{h,v}`（淡金＋細星） |
| 成就 ×6 | `ach_<id>`／`ach_<id>_locked`：first_home、three_gen（「三代」）、brothers、nine_light、eight_series、move_heir |
| 獎勵 | `reward_gold_frame`（9-slice 40）、`reward_sibling_frame`、`reward_halo_top`（光層）、`reward_leaf_border`（tile，右邊 flipX）、`reward_ancestral_tag`「祖傳」 |
| 暖色背景 ×1 | `bg/bg_warm@3x`（三代同堂解鎖）；另 `bg/bg_normal@3x`；各配 `_light_add`（lighter，sway 6px／9s） |
| 其他 | `node_crown`（主寵）、`sib_dot_*`（同上一代同色）、`inherit_arrow`（遺傳自）、`egg_unhatched`、`node_aura`（白，runtime tint）、`fx/particles@3x`＋`fx/emitters.json` |

## 節點
- 疊層：aura（光層）→ 框 → 窗底（心情漸層）→ 頭像 sprite（現有寵物 sprite，跟實際形態＋狀態；瞓覺用 sleep 幀；k=4）→ 皇冠／章／圓點 → 名（label 18）。
- 亮＝仲喺屋企；灰＝退休或未孵（框灰、窗去飽和）；sel＝撳中（金光外圈）。
- 撳節點：佢嘅關係線同節點保持，其他節點 alpha .55／rgb×.38，線 alpha .22。
- 「只睇直系」：主寵＋上一代鏈＋下一代，全部置中一條直線（唔畫祖輩線，只保留「祖」章）。
- 同屋：由主寵視角推（同時住、唔同上一代、冇直系）。

## 寵物光（petGlow）
跟 `ui/kit_hd2d_v3/layout_hd2d_v3.json#petGlow`（Kurt：「除左佢訓就會關」）：
- `node_aura`、`node_aura_mote` = petglow outer tint（`sprites/*/petglow_v3/<form>.json`）× petGlow(state)：awake 1、sleepy .6、sleep／sleepClip／dreamEnter／dreaming 0。
- fadeOut 600ms easeInQuad；fadeIn 400ms easeOutQuad＋150ms pulse 1→1.15→1。
- 退休／未孵蛋 = 0；`notLight` 形態（例如 S1）冇 aura。
- 背景光柱、bokeh、線光、成就光環屬場景光，唔受影響。
- demo：豆豆（S2）瞓緊 → aura 0（醒時有）。

## Mockup（`mockups/*_3x.png`，疊 UI v3）
ft_full（暖色＋金框）、ft_direct、ft_focus（撳團絨）、ft_card（遺傳自＋箭咀、祖傳、4 行故事、睇佢一生 6 剪影、叫佢出嚟／玩招式）、ft_achievements、ft_full_all（6 成就全開）、ft_normal（普通背景）、ft_egg_pick（未孵蛋揀上一代）。文字記錄：`mockups/texts.json`。

## 已知限制
- 磨砂喺 mockup 即場 blur；引擎用預烘模糊圖。
- 同屋只示範主寵視角一條線；多條同屋線嘅避讓要引擎排版。
- 「睇佢一生」中間剪影用 A 系階段 sprite（S1→S2→S4A→A1）示範；實際用該隻寵物嘅歷史形態。
- 工作場景（GDD §2 其餘）未做，等下一批。
