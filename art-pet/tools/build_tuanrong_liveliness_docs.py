#!/usr/bin/env python3
"""更新 CLIPS.json／CLIPS.md（團絨生命感 add-on），寫 FACE_RIG.md、MILESTONE1.md。
冪等：第一次運行將原 CLIPS.* 備份去 liveliness/_backup_v1/，之後一律由備份重建。"""
import json, os, glob, shutil, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import build_tuanrong_liveliness as L
MOT = L.MOT; OUT = L.OUT; BK = os.path.join(OUT, "_backup_v1")

def backup():
    os.makedirs(BK, exist_ok=True)
    for n in ("CLIPS.json", "CLIPS.md"):
        if not os.path.exists(os.path.join(BK, n)): shutil.copy2(os.path.join(MOT, n), os.path.join(BK, n))

def counts():
    c = {}
    for form in L.FORM_LIST:
        c[form] = dict(noface=len(glob.glob(f"{OUT}/layers/{form}/*_noface.png")), faceov=len(glob.glob(f"{OUT}/layers/{form}/*_faceov.png")),
                       frames=len(glob.glob(f"{OUT}/frames/{form}/*.png")), kit=len(glob.glob(f"{OUT}/kit/{form}/*.png")),
                       atlas=sorted(os.path.basename(p) for p in glob.glob(f"{OUT}/atlas_{form}_live*.png")))
    return c

def kit_info():
    js = json.load(open(glob.glob(f"{OUT}/atlas_radiant_live*.json")[0]))
    info = {}
    for form in L.FORM_LIST:
        for p in glob.glob(f"{OUT}/atlas_{form}_live*.json"):
            fr = json.load(open(p))["frames"]
            for k in ("eyes_neutral_C_l", "mouth_neutral", "bulb_base"):
                if k in fr: info.setdefault(form, {})[k.split("_")[0]] = dict(size=[fr[k]["sourceSize"]["w"], fr[k]["sourceSize"]["h"]], pivotPx=[fr[k]["pivotPx"]["x"], fr[k]["pivotPx"]["y"]])
    return info

def update_clips():
    backup()
    D = json.load(open(os.path.join(BK, "CLIPS.json")))
    FA = json.load(open(os.path.join(OUT, "face_anchors.json")))["anchors"]
    cnt = counts(); ki = kit_info()
    D["version"] = 2
    D["liveliness"] = {
        "status": "團絨生命感 精簡級 v1（10-31，A 風 HD-2D；畫風未定，Kurt 揀咗再調）",
        "dir": "liveliness/", "rig": "liveliness/FACE_RIG.md", "faceAnchors": "liveliness/face_anchors.json（同下面 clips[].anchors 一樣，鏡像）",
        "anchorCoords": "frame-local px，原點＝幀左上角，y 向下；3 form 各自一套 clips[].anchors[form][frameIndex]",
        "anchorKeys": {"grab": "頭頂拎點（只 picked_up 有；亦係該 clip pivot）", "eyeL": "左眼（畫面左）kit piece pivot 對準點", "eyeR": "右眼", "mouth": "口 pivot 對準點", "head_r": "頭右上圖示（zzz／心等，取代固定 headRightAnchor）",
                       "bulb": "光芽燈泡中心（bulb_base／bulb_glow pivot）", "faceVisible": "false＝背面，唔好疊五官", "face": "呢幀預設表情（kit 名；舊 clip 由原幀推斷，src＝原 eyes/mouth 模板）"},
        "atlas": {f: cnt[f]["atlas"] for f in L.FORM_LIST},
        "phase2": {"clips": L.S2_ORDER, "atlas": "atlas_<form>_live_s2.png/json（第二段 clip 另出；第一段 atlas_<form>_live 版面不變；五官 kit 仍喺 atlas_<form>_live）",
                   "personality": "蠢蠢地但覺得自己好醒", "holdLast_s": L.HOLD_LAST_S, "smugPreset": L.PRESETS.get("smug"),
                   "flow": {"swatMiss": "swat（撲空）→ smug_pose（hold 0.8s）→ idle", "lookupFall": "lookup → lookup_tip → getup → act_cool（60%）／idle",
                            "sneeze": "sniff → sniff_itch → sneeze →（40%）act_cool"},
                   "rot": "lookup_tip／getup 用 rot（以後腳為軸向後轉 5–16°，烙入幀；錨點已跟住轉）"},
        "fx": {"bug": {"atlas": "liveliness/fx/atlas_fx_live.png/json", "frames": ["fx_bug_01", "fx_bug_02", "fx_bug_03"], "size": [8, 8], "pivotPx": [4, 4],
                       "animation": "fx_bug（01→02→03→02 循環，10fps）", "facing": "right（向左 scaleX −1）",
                       "use": "A2 蟲仔：engine 飛近 anchors.head_r；swat 第 3 幀（索引 2）判定；撲空 → smug_pose"}},
    }
    for f in L.FORM_LIST:
        D["forms"][f]["liveAtlas"] = cnt[f]["atlas"]
    D["faceKit"] = {
        "eyes": {"styles": L.EYE_STYLES, "moving": L.MOVING, "closedOnlyC": L.CLOSED, "gaze": list(L.GAZE.keys()),
                 "gazeOffsetPx": L.GAZE, "naming": "eyes_<style>_<gaze>_<l|r>（l＝畫面左眼用、r＝右眼用；閉眼款只有 _C_）",
                 "note": "瞳孔偏移已畫入 piece（同一 canvas、同一 pivotPx），引擎只要換 piece 名；L/R 係 sprite 空間（向右＝R），scaleX −1 時跟住整體鏡像。"},
        "mouth": {"styles": L.MOUTH_STYLES, "naming": "mouth_<style>", "note": "wink 口＝伸脷（俏皮／肚餓舐嘴）；squint 口＝ω 貓口"},
        "pieceInfo": ki,
        "presets": L.PRESETS,
        "drawOrder": "body(<clip>_noface) → eyeL → eyeR → mouth → bulb_base → bulb_glow(tint) → head_r 圖示",
    }
    D["bulb"] = {"layers": {"bulb_base": "固定色外圈（glow 色）", "bulb_glow": "白／淺色內芯，引擎 multiply tint＋intensity"},
                 "anchor": "anchors[].bulb", "moods": L.BULB_TINT,
                 "rules": ["sick clip 期間唔疊燈泡（保留原幀病態灰綠光芽）", "sleep_loop／fall_asleep 用 sleepy", "情緒轉換 0.4s 漸變 tint",
                           "燈泡 piece 固定大細；原幀光芽細過 piece 時（bud<0.8）會略大，可接受"]}
    names = [c["name"] for c in D["clips"]]
    for c in D["clips"]:
        n = c["name"]
        c["anchors"] = {f: FA[f][n] for f in L.FORM_LIST}
        lay = c.get("layers", {})
        newlay = {"noface": f"liveliness/layers/<form>/{n}_NN_noface.png", "faceov": f"liveliness/layers/<form>/{n}_NN_faceov.png",
                  "nofaceClip": f"{n}_noface", "atlas": "liveliness/atlas_<form>_live.json"}
        if lay: newlay["noface_v1"] = lay.get("noface"); newlay["overlay_v1"] = lay.get("overlay")
        c["layers"] = newlay
    for n in L.NEW_ORDER:
        fps, loop, lf, pr, intr, cd, nxt, item, trig, note = L.NEW_META[n]
        d = {"name": n, "status": "已交付（liveliness v1）", "category": "生命感", "item": item, "frames": len(FA["radiant"][n]), "fps": fps, "loop": loop,
             "priority": pr, "interruptible": intr, "trigger": trig, "cooldown_s": cd, "next": nxt, "notes": note,
             "attachments": [{"prop": "heart", "anchor": "head_r", "startFrame": 1, "behind": False}] if n == "nuzzle" else [],
             "layers": {"noface": f"liveliness/layers/<form>/{n}_NN_noface.png", "faceov": f"liveliness/layers/<form>/{n}_NN_faceov.png",
                        "full": f"liveliness/frames/<form>/{n}_NN.png", "nofaceClip": f"{n}_noface", "atlas": "liveliness/atlas_<form>_live.json"},
             "anchors": {f: FA[f][n] for f in L.FORM_LIST}}
        if n == "rush": d["loopRange"] = [1, 4]
        if n in L.PIVOT_OVERRIDE:
            d["pivot"] = L.PIVOT_OVERRIDE[n]
            d["pivotNote"] = "pivot override：呢個 clip 唔用腳底 pivot (w/2,h−3)，改用每幀 anchors[form][k].grab（頭頂拎點，幀左上角 px）；atlas 幀 pivotPx 已＝grab。引擎：sprite 位置 = 手指位置 − grab。scaleX −1：容器以 grab 為原點翻轉（grab.x＝S/2，同腳底 pivot 同一條中線），五官照 FACE_RIG 成組翻。"
            d["faceOnEnter"] = L.FACE_ON_ENTER[n]
            d["layers"]["previewGrab"] = f"liveliness/preview/<form>/{n}_grab_8x.gif"
            d["layers"]["previewStrip"] = f"liveliness/preview/<form>/{n}_strip_8x.png"
        if n in ("walk_happy", "walk_drag"): d["variantOf"] = "walk"
        if n in L.S2_ORDER:
            d["status"] = "已交付（liveliness s2）"; d["phase"] = 2
            d["layers"]["atlas"] = "liveliness/atlas_<form>_live_s2.json"
            d["layers"]["kitAtlas"] = "liveliness/atlas_<form>_live.json（eyes_*/mouth_*/bulb_*）"
            d["layers"]["previewStrip"] = f"liveliness/preview/<form>/{n}_strip_8x.png"
        if n in L.HOLD_LAST_S: d["holdLast_s"] = L.HOLD_LAST_S[n]
        if n in names: D["clips"] = [x for x in D["clips"] if x["name"] != n]
        D["clips"].append(d)
    sm = D.setdefault("stateMachine", {})
    sm["liveliness"] = {
        "walkVariant": "walk 播放時：心情≥70→walk_happy；精力<40 或飽腹<40→walk_drag；否則 walk",
        "midWalkStop": "每段 walk 15% 機率停低，sniff／lookup／swat 平均抽（夜晚 lookup ×3），各自冷卻",
        "idleExtras": "idle 變化抽籤加入 scratch（12）／sneeze（8），同一小動作 ≥10 分鐘唔重複",
        "tap": "背向／行緊路被點 → turn_back → 心情≥50 emo_happy，否則 emo_surprised",
        "longPress": "長按 ≥0.4s → nuzzle（循環至鬆手）",
        "returnAfter6h": "rush（loopRange 跑到位）→ cheer_jump",
        "pickUp": "Android 浮動團絨：手指按住拖曳／拎起 → picked_up（loop，pivot＝grab 對準手指；第一循環 faceOnEnter surprised，之後 happy）→ 放手：引擎跌落／彈返地面 → idle（或 emo_surprised）",
        "gaze": "A1/D1：walk 時眼 gaze 跟行進方向（R），每 1.5–3s 望花盆／鏡頭（C）／手指方向（L…R、U、D）；手指喺頭上方用 U",
    }
    json.dump(D, open(os.path.join(MOT, "CLIPS.json"), "w"), ensure_ascii=False, indent=1)
    # ---- CLIPS.md
    md = open(os.path.join(BK, "CLIPS.md"), encoding="utf-8").read()
    md += "\n\n" + clips_md_addon(cnt)
    open(os.path.join(MOT, "CLIPS.md"), "w", encoding="utf-8").write(md)

def clips_md_addon(cnt):
    L_ = []
    L_.append("## 生命感 add-on（v2，10-31，精簡級）\n")
    L_.append("全部喺 `liveliness/`；詳細疊法睇 `liveliness/FACE_RIG.md`。CLIPS.json 每個 clip 新增 `anchors[form][幀]`（frame 左上角 px）同 `layers.noface`；`liveliness/face_anchors.json` 係同一份錨點嘅鏡像。原 CLIPS.* 備份喺 `liveliness/_backup_v1/`。\n")
    L_.append("- 無臉身體：每個 clip 有 `<clip>_noface`（atlas animation）＋ `liveliness/layers/<form>/<clip>_NN_noface.png`；`_faceov.png` 疊返＝原幀（逐像素驗證）。腮紅保留喺身體（舊 `layers/emo_*_noface` 冇腮紅，屬 v1）。")
    L_.append("- 五官套：`eyes_<style>_<gaze>_<l|r>`、`mouth_<style>`；`bulb_base`＋`bulb_glow`。同身體幀一齊入 `atlas_<form>_live.png`。\n")
    L_.append("### 新 clip（每 form 幀數相同，朝右）\n")
    L_.append("| clip | 項目 | 幀數 | fps | loop | 優先級 | 可中斷 | 冷卻(s) | 觸發條件 | 播完接 | 備註 |")
    L_.append("|---|---|---|---|---|---|---|---|---|---|---|")
    FA = json.load(open(os.path.join(OUT, "face_anchors.json")))["anchors"]
    for n in L.NEW_ORDER:
        fps, loop, lf, pr, intr, cd, nxt, item, trig, note = L.NEW_META[n]
        L_.append(f"| `{n}` | {item} | {len(FA['radiant'][n])} | {fps} | {'是' if loop else '否'} | {pr} | {'是' if intr else '否'} | {cd or '—'} | {trig} | {nxt or '—'} | {note} |")
    L_.append("\n名稱對照（策劃稿 → clip）：hop_walk→`walk_happy`、drag_walk→`walk_drag`、look_up→`lookup`、swat_bug→`swat`、dash→`rush`、D2 回頭→`turn_back`。A1／D1 邊行邊望＝gaze（唔使新 clip）。G1＝燈泡 overlay。\n")
    L_.append("### 燈泡心情色（G1）\n")
    L_.append("| mood | tint | intensity | 動態 |\n|---|---|---|---|")
    for k, v in L.BULB_TINT.items(): L_.append(f"| {k} | `{v['tint']}` | {v['intensity']} | {v['pulse']} |")
    L_.append("\n### 表情 preset（kit 組合）\n")
    L_.append("| preset | eyes | gaze | mouth | 附圖示 |\n|---|---|---|---|---|")
    for k, v in L.PRESETS.items():
        L_.append(f"| {k} | {v['eyes']}{('（右眼 ' + v['eyesR'] + '）') if 'eyesR' in v else ''} | {v['gaze']} | {v['mouth']} | {v.get('prop', '—')} |")
    return "\n".join(L_) + "\n"

FACE_RIG = r"""# FACE_RIG — 團絨五官疊層（生命感 v1）

> 3 form：sprout 32px pivot(16,29)；radiant／soft 64px pivot(32,61)。全部朝右畫，朝左＝整個合成容器 scaleX −1（pivot 喺水平中心）。

## 檔案
- `atlas_<form>_live.png/json`（1024 寬、padding 2、extrude 1）：
  - `<clip>_noface_NN`：34 個 clip 嘅無臉身體（舊 23 個＋新 11 個），animation `<clip>_noface`
  - `<clip>_NN`：新 11 個 clip 嘅完整幀（已疊預設表情），animation `<clip>`
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
- `grab`（**只 `picked_up` 有**）＝頭頂拎點（身體頂中、光芽莖底）；見下面「被拎起」。

## 被拎起 picked_up（D6，浮動團絨）
- 3 form 各 6 幀、8 fps、loop；朝右畫。身體吊住微拉長（sy 1.06–1.08），以 grab 為軸鐘擺擺動（腳底位移 sprout ±1–2px、radiant／soft ±1–3px，三角波），兩隻腳交替輕踢，腳仔有短腿連住身。
- **pivot override**：CLIPS.json `"pivot":"grab"`；atlas `picked_up_NN`／`picked_up_noface_NN` 嘅 `pivotPx`＝該幀 `anchors.grab`（唔係 (w/2,h−3)）。
  - 擺位：`spritePos = finger − grab`；五官照舊 `spritePos + anchors.eyeL − piece.pivotPx`。
  - grab：sprout (16,8)；radiant (32,23)／拉長幀 (32,22)；soft (32,19)／拉長幀 (32,18)。逐幀讀，唔好寫死。
  - scaleX −1：grab.x＝S/2 喺中線，容器以 grab 為原點翻轉即可。
- 錨點（eyeL／eyeR／mouth／head_r／bulb）已計埋鐘擺位移（grab 以下每行按 `round(pend·(y−gy)/(S−3−gy))` 平移）。
- 預設表情：每幀 `face`＝happy；`faceOnEnter`＝surprised（gaze D）播第一個循環（≈0.75s）再轉 happy。可隨時換其他 kit 表情（如拎太耐→ sad／angry）。
- 預覽：`preview/<form>/picked_up_grab_8x.gif`（grab 釘死喺畫面同一點，紅點＝grab／手指位，只係預覽標記）、`picked_up_strip_8x.png`（行 1 happy、行 2 surprised、行 3 無臉）。

## 疊法（每幀）
```
draw(body = atlas["<clip>_noface_NN"], at = petPos − pivotPx)   # picked_up: petPos = 手指位置, pivotPx = anchors.grab
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
"""

def write_rig(): open(os.path.join(OUT, "FACE_RIG.md"), "w", encoding="utf-8").write(FACE_RIG)

def write_milestone():
    cnt = counts(); ki = kit_info()
    s = ["# MILESTONE 1 — 團絨五官 rig（俾遊程先接）\n", "日期：2026-10-31（HKT）。根目錄：`art-pet/sprites/tuanrong/motion/liveliness/`\n",
         "## 已交（3 form：sprout／radiant／soft）",
         "- `idle_noface`（4 幀）、`walk_noface`（6 幀）——其實**全部 33 個 clip 嘅 `_noface` 已一齊出**（見下面數量）",
         "- 眼層：8 款 × gaze（L、CL、C、CR、R＋U、D；閉眼款只 C）× 左右眼；口 8 款；燈泡 base＋glow",
         "- 錨點：`CLIPS.json → clips[].anchors[form][幀]`（frame 左上角 px）＋鏡像 `face_anchors.json`",
         "- 疊法：`FACE_RIG.md`\n", "## 檔案數量", "| form | noface 幀 | faceov | 新 clip 完整幀 | kit 散件 | atlas |", "|---|---|---|---|---|---|"]
    for f in L.FORM_LIST:
        c = cnt[f]; s.append(f"| {f} | {c['noface']} | {c['faceov']} | {c['frames']} | {c['kit']} | {', '.join(c['atlas'])} |")
    s.append("\n## piece 尺寸／pivotPx")
    for f, d in ki.items(): s.append(f"- {f}: " + "；".join(f"{k} {v['size'][0]}x{v['size'][1]} pivot {tuple(v['pivotPx'])}" for k, v in d.items()))
    s.append("\n## 路徑\n- `atlas_<form>_live.png/json`\n- `layers/<form>/<clip>_NN_noface.png`／`_faceov.png`\n- `kit/<form>/eyes_*.png`、`mouth_*.png`、`bulb_*.png`\n- `preview/<form>/A1_walk_gaze_8x.gif`（walk＋gaze 示範）\n")
    open(os.path.join(OUT, "MILESTONE1.md"), "w", encoding="utf-8").write("\n".join(s) + "\n")

if __name__ == "__main__":
    update_clips(); write_rig(); write_milestone(); print("docs ok", counts())
