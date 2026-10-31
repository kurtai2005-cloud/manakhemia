# 團絨 飾品完整版 — 分批計劃（ACC_PLAN）
遊美 2026-11-01 03:20 HKT。Kurt 03:14 揀咗「做完整版」：飾品 13 件 × 25 個可穿戴形態 × 全部 clip，逐形態手調，高動作 clip 跟變形，有 L／64px 版，另加收藏品 12 件。
基數：25 個形態（光卵唔戴）、1,055 個 clip、4,674 幀。每批一次 staging（`/workspace/acc<N>-staging(.zip)`），唔 commit，唔 push。
規則：只用 Pillow／numpy 程式畫，冇 AI；飾品像素一律用 v3 色盤；alpha 只得 0／255；改檔前先備份；文件只加唔刪；validator 要過，仲要喺上一個 head 上面做 repo sim。

## 共用框架（ACC1 起，之後每批沿用）
- `tools/build_accessories.py`：逐幀用現有 face anchors 同身體剪影推導 fit，包括 axis、top、hw、ang、hs。飾品每幀照 fit 參數重新 raster，帽／結隨傾角轉，大細跟頭闊同壓扁拉長走。燈泡同發光點一律喺飾品層挖空。可見度以 clip 為單位，邊個 clip 收起、點解收起，都寫入 JSON。
- `sprites/tuanrong/accessories/ACCESSORIES.json`：slot、drawOrder、sizeClasses、items、每形態 atlas 同 hiddenClips。
- `tools/validate_accessories.py`：檢查 schema、幀覆蓋、v3／alpha、唔遮五官同燈泡、overlay 同 fit 一致、數量，仲有收藏品。
- 預覽放 `sprites/tuanrong/preview/accessories/`。

## 分批
| 批 | 內容 | 重點／風險 | 估算 |
|---|---|---|---|
| **ACC1**（今批） | 框架＋data format＋validator；收藏品 12 件（16／32px、剪影、atlas、collectibles.json）；飾品 **草帽 straw／蝴蝶結 bow／頸巾 scarf** × 25 形態 × 全 clip | 頭頂偵測同 axis 要套晒 25 個形態，包括冇燈泡嘅、lumi 系同 64px；月眠／菇傘用帽針版；頸巾順住剪影畫，尾巴有慣性 | 約 2 日（今晚做框架同 3 件） |
| ACC2 | 毛冷帽 beanie、橡果帽 acorn、小皇冠 crown（全部 head slot） | 月眠／菇傘逐件出帽針版；beanie 包住頭頂所以挖空範圍唔同；crown 細，喺 L 級要補細節 | 約 1.5 日 |
| ACC3 | 星星髮夾 starclip、櫻花髮飾 sakura（side_l）；圓框眼鏡 glasses（face） | 眼鏡跟 eyeL／eyeR 間距同傾角走；faceVisible=false 就收起；L 級鏡框加粗；閉眼／眨眼 clip 都要睇 | 約 1.5 日 |
| ACC4 | 葉仔領 leafcollar（neck）；燈泡小鈴 bell、燈泡光環 halo（bulb）；睡帽 nightcap（head，有長尾） | dot／evo_sprout 冇燈泡要另做 fallback；光環會出 frame 頂，用 padding 解決；睡帽尾有擺動物理；sleep_* clip 預設保留睡帽 | 約 2 日 |
| ACC5 | 收尾：多 slot 同時戴嘅衝突測試，每 slot 最多 1 件，最多 5 件；25×13 全表 contact sheet；可見度總覆核；同 emissive 層嘅交疊；文件定稿 | 可能要回頭微調 ACC1–4 嘅 FIT 表 | 約 1 日 |
合計大約 8 日美術，比概念估嘅 12–15 日少，因為每幀用參數重畫，取代逐幀手修。逐形態手調集中喺 `FIT`／`HIDE` 表，每項都有註明。

## 未決（交遊策／遊程）
- 13 件嘅攞法同數值見 `ACCESSORIES.json` 嘅 `items[].obtain`，暫時只係建議值。
- 衣櫃 UI 未畫，建議同第 3 批房間 UI 一齊做。
- 引擎要做嘅嘢：飾品層畫喺 face 之上、emissive 之下；scaleX 鏡像同身體一齊做；spriteSourceSize 可以係負數，即係超出 frame 邊。

<!-- ACC-PROGRESS-START -->
## 進度
- ACC1 ✅ 2026-11-01：框架、收藏品 12 件、草帽／蝴蝶結／頸巾（`/workspace/acc1-staging`）。
- ACC2 ✅ 2026-11-01：毛冷帽／橡果帽／小皇冠，加草帽 polish（`/workspace/acc2-staging`）。
- ACC3 ✅ 2026-11-01：星星髮夾、櫻花髮飾、圓框眼鏡（`/workspace/acc3-staging`）。
- ACC4 ⏳ 葉仔領、燈泡小鈴、燈泡光環、睡帽。
- ACC5 ⏳ 多 slot 衝突、25×13 contact sheet、總覆核、文件定稿。
<!-- ACC-PROGRESS-END -->
