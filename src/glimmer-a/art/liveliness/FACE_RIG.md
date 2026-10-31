# FACE_RIG — 團絨五官疊層（生命感 v1）

> 3 form：sprout 32px pivot(16,29)；radiant／soft 64px pivot(32,61)。全部朝右畫，朝左＝整個合成容器 scaleX −1（pivot 喺水平中心）。

## 檔案
- `atlas_<form>_live.png/json`（1024 寬、padding 2、extrude 1）：
  - `<clip>_noface_NN`：33 個 clip 嘅無臉身體（舊 23 個＋新 10 個），animation `<clip>_noface`
  - `<clip>_NN`：新 10 個 clip 嘅完整幀（已疊預設表情），animation `<clip>`
  - `eyes_<style>_<gaze>_<l|r>`、`mouth_<style>`、`bulb_base`、`bulb_glow`：五官套／燈泡（每塊有 `pivotPx`）
- `layers/<form>/<clip>_NN_noface.png`、`_faceov.png`（faceov＝原幀五官像素；noface＋faceov＝原幀）
- `frames/<form>/<new clip>_NN.png`（新 clip 完整幀）；`kit/<form>/*.png`（散件）
- `face_anchors.json`（＝CLIPS.json 入面 `anchors` 嘅鏡像）

## 錨點格式
`CLIPS.json → clips[i].anchors[form][frameIndex]`（face_anchors.json 同結構：`anchors[form][clip][frameIndex]`）：
```json
{"eyeL":[x,y],"eyeR":[x,y],"mouth":[x,y],"head_r":[x,y],"bulb":[x,y],"faceVisible":true,
 "face":{"eyes":"neutral","gaze":"C","mouth":"neutral"}}
```
- 座標＝**幀內 px，原點幀左上角，y 向下**。要相對 pivot：`(x − pivotX, y − pivotY)`。
- 已計埋幀內 dx／lift／擠壓／shear（斜傾按錨點嗰行嘅位移）。
- `faceVisible:false`（turn_back 第 1 幀背面）＝唔好疊眼／口。
- `face`＝呢幀預設表情；引擎想自由換表情就無視佢。

## 疊法（每幀）
```
draw(body = atlas["<clip>_noface_NN"], at = petPos − pivotPx)
if anchors.faceVisible:
   eyeL = kit["eyes_<style>_<gazeL>_l"] ; draw at petPos − pivotPx + anchors.eyeL − eyeL.pivotPx
   eyeR = kit["eyes_<styleR>_<gazeR>_r"]; draw at ... + anchors.eyeR − eyeR.pivotPx
   mouth = kit["mouth_<style>"]         ; draw at ... + anchors.mouth − mouth.pivotPx
if bulbOverlay && clip != sick:
   draw bulb_base at anchors.bulb ; draw bulb_glow at anchors.bulb with tint=mood.tint, alpha/brightness=mood.intensity
head_r 圖示（zzz／heart…）用 anchors.head_r（取代舊固定 headRightAnchor）
```
- 閉眼款（happy／sleepy／wink）只有 `_C_`；會郁嘅款（neutral／surprised／squint／angry／sad）有 L、CL、C、CR、R、U、D。
- gaze 偏移已畫喺 piece 入面（CL/CR 1px、L/R 2px、U/D 1px），同款唔同 gaze 嘅 canvas／pivotPx 一樣，可以逐幀換。
- wink：eyeL 用 `eyes_neutral_*_l`，eyeR 用 `eyes_wink_C_r`（或反轉）。
- 左右眼 piece 分 `_l`／`_r`：angry／sad 眉同眼瞼係鏡像；高光固定左上（光源一致）。
- 朝左：成個合成（身體＋五官＋燈泡）放入同一容器再 scaleX −1；**唔好**逐件 flip，否則 l/r 會掉轉。

## A1／D1 gaze 建議
- walk／walk_happy／walk_drag：預設 gaze R（望行進方向）；每 1.5–3s 隨機望 C（鏡頭）0.6s、或望最近花盆／手指。
- 手指喺寵物左／右 → L／R；距離近（<24px）→ CL／CR；喺頭上 → U；喺腳邊 → D。
- 每次 gaze 轉換最少停 0.25s，避免抖。

## 表情 preset
見 CLIPS.json `faceKit.presets`：neutral、happy、sleepy、surprised、hungry、cuddly、grumpy、curious（＋wink）。

## 已知限制
- shear 幀（walk、play 等斜傾）五官用直身 piece，相對原幀會有 ≤1px 錯位（原幀眼形會跟 shear 拆行）；用 faceov 重現原表情則完全一樣。
- eat 嘅士多啤梨畫喺身體層，口 piece 疊上去會蓋過一部分莓；餵食期間建議用原 eat 幀或 mouth 用 happy。
- 燈泡 piece 固定大細，光芽縮細（bud<0.8）嘅幀會大少少。
