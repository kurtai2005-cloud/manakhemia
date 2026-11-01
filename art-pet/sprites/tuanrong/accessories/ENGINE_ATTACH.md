# ENGINE_ATTACH — 團絨飾品「畫一次、即場套落所有形態／clip」引擎規格（俾遊程）

> 參考實作：`tools/compose_accessory_runtime.py`（Python/numpy，逐 px 同引擎要做嘅一樣）。
> 生成器：`tools/build_accessory_runtime.py`（attach 表、item source、對照、預覽）。驗證：`tools/validate_accessory_runtime.py`。
> 目標平台：canvas2D、冇 shader。**舊 baked atlas（`accessories/atlas/…`）照留**：runtime 未做好之前可以繼續用 baked；兩者畫面 99.7% 幀合格（見 `RUNTIME_COMPARE.md`）。

## 0. 點解要 runtime
baked＝13 件 × 25 形態 × 1055 clip 預先砌好嘅 atlas；加一件新飾品就要重 bake 全部。runtime＝每件飾品只畫 **3 個 view（front/side/back）× S/M/L**，引擎每幀用 attach 表（身體錨點）即場放大縮細、轉角、擺動、避五官。新飾品（例：櫻桃髮夾 `cherry`）只要加 `source/<id>/` 一個資料夾。

## 1. 檔案

| 路徑 | 內容 |
|---|---|
| `accessories/attach/ATTACH.json` | index：每個形態嘅 attach 檔、frameSize、clip 數；欄位說明（`fields`） |
| `accessories/attach/<form>.json` | 一個形態：`frameSize`、`sizeClass`(S/M/L)、`overlayPad`(=8)、`ref`、`slots`、`emissiveDir`、`clips` |
| `accessories/source/<item>/item.json` | 一件飾品：slot、materials（label→ramp）、views、parts、size／place 規則、swing、yield、formOverrides、hideClips… |
| `accessories/source/<item>/lab_*.png` | **label map**（每種物料一隻 key 色，alpha 0/255）——引擎用呢啲 |
| `accessories/source/<item>/<view>_<S|M|L>.png` | 已 render 好嘅預覽（設計睇／引擎唔使） |
| `accessories/source/glasses/lab_lens_sheet.png` | 眼鏡鏡片 ladder（1168 格，左鏡片；右鏡片＝水平鏡像） |

### 1.1 attach `<form>.json`
```
clips.<clip> = { frameDir, fps, loop, n, hidden:{slot: 原因}, f:{ <field>: [第1幀, 第2幀, …] } }
```
`hidden.<slot>` 有值＝成個 clip 嗰個 slot 唔畫（例：`leaf_umbrella` 頭飾收起；背面 clip 冇 face）。
每幀欄位（座標＝身體 frame 像素，**未加 pad**；角度＝度，正＝順時針，y 向下）：

| field | 值 |
|---|---|
| `facing` | `F` 正面／`S` 側面／`B` 背面 → 揀 item 嘅 front／side／back view |
| `dir` | +1 向右／-1 向左 |
| `head` | `[x, y, ux, uy, ang, ws, hs]`：頭頂點、向上單位向量、傾角、闊／高比例（對 idle） |
| `pin` | `[x, y, ang, ws]`（head.mode=pin 嘅形態先有：髮夾式戴法） |
| `side_r` / `side_l` | `[x, y, ang, ws, mirror]`：耳邊位；`mirror=1` → view 水平反轉 |
| `face` | `[lx, ly, rx, ry, bx, by, plx, ply, prx, pry, pbx, pby, eyeTopL, eyeTopR]`：眼心（idle 參考）、眼半闊高、逐幀眼 blob 中心、眼頂 y |
| `eyes` | `[[x,y,x,y…], […]]`：左右眼 blob 像素（鏡框唔准壓） |
| `neck` | `[ny, cx, ang, xl, xr, rows]`：頸線 y、中心、傾角、左右邊；`rows[i]`＝第 `ny-4+i` 行可畫 `[x0,x1]` 或 null |
| `bulb` | `[hx, hy, fx, fy, fang, fw, ux, uy]`：燈泡掛點、浮點（光環中心）、光環角、光環闊、向上向量 |
| `facePts` | `[[x,y]…]` eyeL／eyeR／mouth；±1px 係保護區 |
| `glow` | `[[x,y]…]` 燈／光點：飾品喺 ±1px 挖空 |
| `bulbPt` | `[x,y]` 燈泡（唔准遮） |
| `stem` | `[[y, x0, x1]…]` 帽要挖空嘅芽／莖 run（一行可以多段） |

`slots`：`head.mode` hat／pin、`head.pinSide`、各 slot `sc`（形態級縮放）、`face.mode` eyes／forehead、`neck.thRef`（頸帶厚）、`bulb.topBulb`。
`ref.hw`＝idle 頭闊（size 規則嘅基準）。

### 1.2 item.json（重點欄位）
- `slot`：head／side_r／side_l／neck／bulb／face。
- `materials`：`{ "#key色": {base, hi, shade, hole?, bodyOnly?} }`，順序＝label 1,2,3…。
- `views.<front|side|back>.<S|M|L>`：`{lab, w, h, pivot:[px,py], anchors:{名:[x,y]}, parts:[{id, at, angK, sizeClass?, scale?, replace?}]}`。
- `parts.<id>.<S|M|L>`：`{lab, pivot}`（例：cherry 嘅 `dangle`、sakura 嘅 `bud`（只 L 級））。
- `size`：`{mode:"rel", k, minW, odd, ws:[lo,hi], hr?, hs?}` → 目標闊 `W = odd(ref.hw · k · sc · clamp(ws))`。
- `place`：`sink`（帽陷入頭幾多 × hw）、`rot`（耳邊件額外角度，mirror 時反號）、`faceGuard {step:[dx,dy], max, mirrorFlipX}`。
- `swing`：`{src, kx, ky, decay, lim, maxd, apply:"item"|<partId>, gain}`。
- `partFallback`：`[{rot, scale}…]` 擺件撞五官／出界時逐個試。
- `yield`：`{priority, steps:[[dx,dy]…], coverMax, floatOk, anyOverlap}`（多件衝突）。
- `formOverrides.<form>`：`dx, dy, sc, th, r, hide:{clip: 原因}`；`hideClips.<"*"|form>.<clip>`。
- `retry`（眼鏡）、`lens`、`glasses`；`neck`（頸飾）；`cutStem`、`faceClear`、`slotScaleFrom`。

## 2. 每幀流程（單件）
1. **clip 級**：`hideClips`／`formOverrides.hide`／`attach.hidden[slot]` 有 → 成個 clip 唔畫。計 swing（§4）。
2. **揀 view**：`facing` F/S/B → front/side/back（冇就 front）。背面（B）嘅耳邊件：鏡像與否完全由 attach `side_*.mirror` 決定（build 時已計好背面要反）；item 嘅 `mirrorOnBack:true` 只係標記，引擎唔使再反多次。
3. **揀 size**：S/M/L 入面「最細一個 w ≥ W」，冇就最大。`sx = W / w`（帽：`sy = H / h`）。
4. **變形（label map，nearest）**：縮放 → 鏡像 → 轉整數度。全部 nearest、snap 到 px（見 §3）。
5. **落點**：`X = org(pos.x, pivot.x)`、`Y = org(pos.y, pivot.y)`；pos：
   - 帽：`head.xy − u·sink + (dx,dy)`；角度＝`head.ang`。
   - 耳邊：`side.xy + (dx·sg, dy)`，角度＝`side.ang + place.rot·sg`（sg＝mirror?-1:1）。
   - parts：錨點跟主件變形（`xpt`），角度＝swing·gain＋fallback.rot＋angK·主件角。
6. **render（label → RGBA，一次）**：每個 label 填 base；上／左邊同其他 label 交界 → hi；下／右邊 → shade（下右優先）；外圍 4 鄰 1px 描邊 `#3B2A3E`（59,42,62）；`hole` 物料清走。**render 要喺組合晒所有 label 之後先做一次**（主件＋parts 同一張 label canvas），咁 parts 同主件之間唔會有多餘描邊。
7. **後處理**（按次序）：
   1. 眼鏡：`bodyOnly` 物料喺身體外清走；任何 `eyes` 像素被蓋 → 換下一個 retry；額頭模式喺身體上嘅比例 < `onBodyMin` → 換。
   2. `faceGuard`：蓋到 `facePts ±1` → 每次移 `step`（mirror 時 x 反號），最多 `max` 次。
   3. `faceClear`（頸飾）：facePts ±1 直接清走。
   4. 有 `partFallback`：仲撞五官或者出界 → 試下一組 rot/scale。
   5. `cutStem`（帽）：`stem` run 清走，洞邊碎粒（≥3 邊空）清 2 輪，洞邊補描邊。
   6. `glow ±1` 挖空；挖完剩 < 65% → 成個 clip 收起。
   7. 仍然蓋五官 ±1 → 收起；蓋 `bulbPt` ±1（而燈泡喺身體上）→ 收起。
8. 任何一幀失敗 ⇒ **成個 clip** 嗰件唔畫（唔好逐幀閃）。

## 3. 像素規則（一定要跟，否則同 baked 差 1px）
- **org(p, piv) = roundHalfEven(p − piv − 1) + 1**。Python `round` 係 banker's rounding；JS **唔好用 `Math.round`**：
  ```js
  function rhe(x){ const f=Math.floor(x), d=x-f; if(d>0.5) return f+1; if(d<0.5) return f; return (f%2===0)?f:f+1; }
  const org=(p,piv)=>rhe(p-piv-1)+1;
  ```
  （眼鏡鏡片同光環以外：主件、parts 都用 org；眼鏡鏡片落點用普通 rhe(c−piv)。）
- **nearest 縮放**：`W2=round(w·sx)`；來源 index `xi = floor((i+.5)·w/W2)`；新 pivot＝`(p+.5)·W2/w − .5`。
- **鏡像**：`m[:, ::-1]`，`px = w−1−px`。
- **旋轉**（整數度 a）：輸出格 (dx,dy) 相對 pivot → 來源 `sx = cos·dx + sin·dy + px`、`sy = −sin·dx + cos·dy + py`，四捨五入取樣（反向映射，所以唔會穿窿）；之後 crop 到非空 bbox，pivot 跟住移。
- 所有變形喺 **label map** 做，唔好喺 RGBA 做（否則描邊／高光會斷）。
- canvas2D：用 `ImageData`／`Uint8Array` 自己做以上運算，**唔好用 `ctx.rotate/drawImage` 縮放**（會 smoothing、半格偏移）。結果可以 cache：key＝(item, view, size, sx, sy, ang, mirror)。

## 4. 擺動（swing）
```
s=0; 對 loop clip 行兩轉、攞第二轉；第 k 幀：v = pt[k]−pt[k−1]（loop 第 0 幀用最後一幀）
t = clamp(decay·s + kx·vx + ky·vy, ±lim);  s += clamp(t−s, ±maxd)
```
`src`＝取點：head／bulb（bulbPt）／side_r…。`apply:"item"` → 成件轉；`apply:"<part>"` → 只轉個 part（例：cherry 兩粒櫻桃 `dangle`，gain 1）。
頸飾尾 `lag`：每幀 `clamp(−Δcx, ±2)`，沿尾長線性 shear。

## 5. 眼鏡（face slot）
- **lens ladder**：`lens.index["{ax}_{ay}_t{th}_{n|o}_{fx}_{fy}"] = [x, y, w, h, pivx, pivy]`（sheet 座標）。ax 1–6、ay .5–5.5（.5 一級）；th＝S≥64 ? 2 : 1；`n`＝正常（有鼻位缺口）／`o`＝額頭模式全圈（細碼先有）；fx/fy＝鏡心小數位 0/.5。
- 逐 clip 試 `retry` 每組 `(drx, dry, lift, out, pf)`，成個 clip 同一組，第一組成功就用：
  - 鏡心：pf ? 逐幀 blob 中心 (plx,ply)/(prx,pry) : idle 眼心；沿眼線法向 lift、向外 out。
  - `ax = bx + 1.5 + r + drx`、`ay = by + 1.5 + r + dry`（r＝formOverrides.r）；`ax ≤ (dist+2out)/2 − th/2`；`ax < bx+.45+out` → 失敗（「眼距太窄」）。
  - 額頭模式（`slots.face.mode=forehead`）：`ay = 1.5+dry`、`ax = min(2.5+drx, lim)`，成副上移到眼頂上 2.5px。
  - ax/ay floor 到 .5；左鏡片＝cell、右鏡片＝cell 水平鏡像；兩片都轉 `atan2(眼線)`。
- 引擎自己畫：**鼻橋**（兩片內側、`bridgeY·ay` 高度，一條 1px 線，用 `frameKey` 物料）；**反光**（`(ax+ay)/2 ≥ glintMinR` → 每片 `c − glintK·(ax−1, ay−1)` 一點 `glintKey`，只畫喺空位）。之後照 §2.6 一次 render。

## 6. 頸飾（neck slot）
- `stripe`（圍巾／鈴）：tile 逐列砌，第 x 列 y 偏移 `round(−tan(ang)·(x−cx))`，每點用 `rows` 收邊；尾巴（`tail.sizes[th]`）貼右邊，加 lag shear。
- `leaves`（葉頸圈）：A/B 葉片交替，只頂行收邊；細花貼 `flowerAt`。

## 7. 光環（bulb slot，float）
`rx_t = fw/2·sc` → 揀 `halo.rx` 最近（同距揀細）嘅 size；中心 `(fx,fy) + u·(ry+dy)`；角度 fang；Y 出咗頂 → 貼 padding 頂；X 出界 → 收起。落點 org()。

## 8. 多件（combos，即場解）
1. 先各自用 §2 計好每件嘅 clip 層；收起嘅記低原因。
2. **同一個 slot 只戴一件**：priority 大嗰件留低。
3. 按 priority 細→大逐對檢查衝突（覆蓋 > `coverMax`（預設 30%，以下層嗰件計）；`anyOverlap` 件一重疊就算）。priority 細嗰件（讓位件）照 `steps` 試位移（成個 clip 同一個 dx,dy），條件：唔撞所有其他件、唔遮五官／燈泡、要貼住身體或者對方（`floatOk` 例外）。試晒都唔得 → 收起。
4. 最後仲有殘留衝突 → 收起 priority 細嗰件。
5. 畫序（下→上）：`neck → head → side_r → side_l → face → bulb`。
結果只係每件一個 (dx,dy) 或者收起 ⇒ 可以每個 (outfit, form, clip) cache。

## 9. emissive（夜光）
有 `<emissiveDir>/<clip>_<kk>_emissive.png`（attach 頂層 `emissiveDir`；冇就唔做）：疊喺身體＋飾品之上，但**被所有飾品 alpha 遮走**；混合＝`rgb += emissive.rgb/3`（canvas2D：`globalCompositeOperation='lighter'`、`globalAlpha≈.33`，先用飾品 mask `destination-out` 清走 emissive 層）。

## 10. 新飾品點加（例：cherry 櫻桃髮夾）
1. 畫 `lab_front/side/back_{S,M,L}.png`（key 色、alpha 0/255），需要擺嘅部分拆做 `lab_part_<id>_{S,M,L}.png`。
2. 寫 item.json（slot、materials、size、place、swing、yield、partFallback）。
3. 跑 `python3 tools/build_accessory_runtime.py`（或者只 `src_<id>()`）→ 預覽；`validate_accessory_runtime.py` 會用全部 25 形態試 render。
cherry：slot side_r、S9/M13/L17、rot +8、兩粒櫻桃 `dangle` 跟 side_r 擺（kx6 ky3 decay.55 lim28）、faceGuard [1,−1]×6、priority 3.5。

## 11. 遊程要實作嘅清單
- [ ] 讀 ATTACH.json／<form>.json／item.json；載入 lab PNG → Uint8 label map（key 色→index）。
- [ ] nearest 縮放／鏡像／整數度旋轉（§3），roundHalfEven 嘅 org()。
- [ ] label canvas 組合（主件＋parts，`replace` 限制）、一次 render（hi/shade/描邊/hole）。
- [ ] 後處理：bodyOnly、faceGuard、faceClear、partFallback、cutStem、glow 挖空、五官／燈泡檢查、clip 級收起。
- [ ] swing（item／part）、頸飾 lag。
- [ ] 眼鏡 lens ladder＋retry＋鼻橋＋反光；頸飾 stripe／leaves；光環。
- [ ] combos：同 slot、yield steps、殘留收起、畫序。
- [ ] emissive 疊加。
- [ ] cache：clip 層（item,form,clip）、outfit 解（outfit,form,clip）。
- [ ] 驗收：用 `compose_accessory_runtime.py <form> <clip> <a+b+c> out.png` 出參考圖逐 px 對（應該 100% 一樣）。

## 12. 新形態／新種族（data-only）
attach 表係「形態 × clip × 幀」嘅錨點表；**飾品 source 同 compositor 唔認形態名**（只係 `formOverrides` 可選微調）。所以加新形態（例：`species_concept/species.json` 嘅新種族）只要加 anchor data：
1. 準備身體幀 `<frameDir>/<clip>_<kk>.png`（同現有命名一樣）。
2. 每幀 anchors：`eyeL`、`eyeR`、`mouth`、`head_r`、（可選）`bulb`／`bulb2`、`faceVisible`——同 motion 嘅 `face_anchors_*.json` 一樣格式 `{"anchors": {clip: [每幀]}}`。
3. 喺 `attach/FORMS_EXTRA.json` 加一項（格式見 `attach/FORMS_EXTRA.example.json`）：`frameDir`、`anchors`，可選 `animations`、`emissiveDir`、`bulbR`、`glassesForehead`、`pinSide`（頭頂有大物件 → 頭飾改帽針）、`headSc`／`sideSc`、`axisFromEyes`（燈唔喺頭頂）。
4. `python3 tools/build_accessory_runtime.py attach` → 出 `attach/<form>.json`，ATTACH.json 標 `extra:true`。引擎唔使改。
5. 要微調先喺個別 item.json `formOverrides.<form>` 加 dx/dy/sc。
示範（dry-run，寫去 /tmp，唔掂 species_concept）：`python3 build_accessory_runtime.py species` → species.json 16 個有眼錨點嘅 route×stage 全部生成 attach，用 cherry／straw／glasses／scarf／bow／halo render 晒（`preview/accessories/runtime/species_extra_demo_3x.png`）。lumi 兩個 stage 喺 species.json 冇 anchors → 要補先加得。概念圖得 idle 一幀，冇做逐形態微調（例：shroom 大菇傘應該設 `pinSide`）。
