# 生命感第三段（s3）— 遊美 2026-10-31 HKT

個性：「蠢蠢地但覺得自己好醒」。3 form（sprout 32×32 pivot (16,29)／radiant、soft 64×64 pivot (32,61)），朝右，31 色、alpha 0/255、無 AA，Pillow+numpy 程式繪製（`tools/build_tuanrong_live_s3.py`，重用 build_tuanrong_liveliness 嘅 renderer／kit／anchors；第一、二段檔案唔郁）。

| clip | 幀／fps | loop | 內容 |
|---|---|---|---|
| nuzzle_purr | 4／6 | 循環（loopRange [0,3]） | nuzzle ≥1.2s 後切入：挨住右邊手指、合眼笑（eyes happy＋mouth squint ω），身體細震（sx/sy 交替、shear 1px 擺），背後呼嚕震線「( (」烙入（1/3 幀近、2/4 幀遠 1px），第 2–4 幀頭頂右細心心升起（第 4 幀大一級）。放手播完當前幀 → idle（或 30% act_cool）。 |
| reunion_happy | 5／8 | 單次 | rush 衝過頭 → act_cool → 呢個：① 扮冷靜側眼回望（ft 向後、squint gaze L）② 破功壓扁、驚喜眼 ③ 彈起舉手＋細心心 ④ 最高點大心心 pop＋閃光 ⑤ 落地得意 ω 臉（sleepy 眼＋squint 口），細心心飄高。播之前按玩家位置設 scaleX（衝過頭＝玩家喺後面 → 鏡像）。 |

- atlas：`atlas_<form>_live_s3.png/json`（sprout 1024×64、radiant/soft 1024×256，各 18 塊：noface＋full；pivotPx＝(w/2,h−3)；pad 2、extrude 1）。五官 kit 仍喺 `atlas_<form>_live`。
- 錨點：CLIPS.json `clips[].anchors[form]`＝`face_anchors.json`（新增 nuzzle_purr／reunion_happy）。面部預設 `anchors[k].face`。
- 心心、呼嚕線、閃光屬身體層（noface 都有），唔係五官 kit；emissive：呢 3 form 生命感一向冇 emissive 層（只 lumi 有），s3 跟返。
- 預覽：`preview/<form>/<clip>_strip_8x.png`（行 1 完整幀；行 2 noface＋錨點點）、`<clip>_8x.gif`、`live_s3_contact_4x.png`。
- 重建：`python3 tools/build_tuanrong_live_s3.py`（冪等；CLIPS.json／CLIPS.md／ASSET_LOG.md 只加 s3 key，重讀即寫、temp+rename）。如果之後跑 build_tuanrong_liveliness_docs.py 重砌 CLIPS.json，要再跑 build_tuanrong_live_s3.py（同 build_lumi.py、build_evo6_anim.py）。驗證：`python3 tools/validate_liveliness.py`（已加 s3 檢查）。

## 微塵（dust）live atlas — 未出（冇現有尺寸身體美術）
- `build_tuanrong.FORMS` 只有 sprout／radiant／soft（＋蛋）；box 入面冇 64px 微塵 sprite／atlas。遊戲 `render.js` 嘅微塵係程序化 canvas 精靈（PAL.dust、DUST_HEAD [13,−26]），唔係美術檔。
- 唯一微塵美術係 evo6 概念（`evo6_concept/evo6_5_adult_dust_44.png`、`evo6_6_elder_dust_48.png`，44／48px，灰色盤 `palette_evo6_dust.json`）——屬新 6 階段，由 evo6 batch B／C 出動畫（守夜者・微塵 44 會包 std23＋s1/s2 liveliness）。
- 建議：(A，推薦) 唔再畫舊 64px 微塵，等 evo6 batch B 守夜者・微塵 44px 出齊（連 s3 兩個 clip 可之後加），game 換 evo6 時一齊上；舊 64px 期間繼續 fallback。(B) 如要即刻有：用 soft 身形＋新增灰 ramp 出 64px 微塵（要加色入 31 色盤或者用 sick/cream 近似色，需 Kurt 批外觀），約 0.5 人日出 s1+s2+s3 live atlas。
