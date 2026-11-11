#!/usr/bin/env python3
"""build_art_fix1.py — Kurt 批核嘅三項美術修正：文靜坐低、細佬／訪客 M 生命感、夜景染色數值。"""
import os, sys, json, shutil
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import art_fix1_sit as SIT
import art_fix1_liveliness as LIVE

NIGHT_TINT = {
    "format": "godot_fx1.night_tint/1",
    "engine": "Godot 4 Compatibility（低檔：熄影／glow／DoF／fog，LUT 仍開）",
    "units": "albedo_color 係乘上 albedo_texture 嘅 modulate（1,1,1＝唔染色）",
    "why": "G0.1 地面同遠山係 unshaded，環境光／太陽減暗影響唔到佢哋；只開 lut_night 之後中綠草地同米色遠山仍然偏光。要喺 LUT 之前（或一齊）對 unshaded 材質乘暗色。已用 Godot 4.7.2 + Xvfb + llvmpipe 低檔驗證。",
    "applies_to": {
        "ground": "花園 H1 同草原 prairie 嘅 unshaded 地面／草 tile（StandardMaterial3D.shading_mode = unshaded）",
        "hills": "遠山 backdrop（unshaded billboard／mesh）",
        "sky_card": "天卡（G0.1 夜景已有近似染色，可一齊用下面嘅值對齊）",
        "shaded_meshes": "小屋、樹、受光物件唔使乘呢個色（太陽／環境光／LUT 已經會暗）"
    },
    "lut": {
        "night": "art-pet/fx/luts/lut_night.png",
        "dusk": "art-pet/fx/luts/lut_dusk.png",
        "use_with": "environments.json 嘅 night／dusk preset；低檔都要 adjustment_enabled = true"
    },
    "times": {
        "night": {
            "zh": "夜",
            "albedo_multiply": {
                "ground": {"rgb": [0.35, 0.40, 0.62], "hex": "#59709E", "note": "壓綠、偏藍紫，LUT 之後先讀成夜草"},
                "hills":  {"rgb": [0.28, 0.28, 0.42], "hex": "#47476B", "note": "比地面再暗少少，遠山先唔會仲係日間米色"},
                "sky_card": {"rgb": [0.35, 0.40, 0.70], "hex": "#5966B3", "note": "可選；G0.1 夜空卡已有類似染色"}
            },
            "emission": {
                "ground": 0.0,
                "hills": 0.0,
                "sky_card": 0.0,
                "lamps_windows": {
                    "emission_energy_multiplier": 1.2,
                    "note": "燈柱／燈籠／窗／側窗／螢火瓶跟 lights.json intensityNight，唔好剪暗"
                }
            },
            "fog": {
                "enabled_low_quality": False,
                "enabled_mid_high": True,
                "fog_light_color": "#161a28",
                "fog_light_energy": 0.85,
                "fog_depth_begin": 360,
                "fog_depth_end": 1100,
                "fog_aerial_perspective": 0.15,
                "fog_sky_affect": 0.4,
                "note": "低檔熄霧，所以遠山主要靠 hills albedo_multiply；中／高檔再開 environments.json 夜霧加強遠山壓暗。"
            },
            "lighting_hint": "sun.energy 0.12、sun 色 (0.55,0.65,1.0)、fill 0、ambient (0.29,0.35,0.56)×0.35；開 intensityNight 點光。"
        },
        "dusk": {
            "zh": "黃昏",
            "albedo_multiply": {
                "ground": {"rgb": [0.78, 0.62, 0.50], "hex": "#C79E80", "note": "輕微暖暗，草地偏暮橙，唔好同夜一樣咁暗"},
                "hills":  {"rgb": [0.70, 0.55, 0.48], "hex": "#B38C7A", "note": "遠山略深、偏暖"},
                "sky_card": {"rgb": [0.85, 0.65, 0.55], "hex": "#D9A68C", "note": "可選"}
            },
            "emission": {
                "ground": 0.0,
                "hills": 0.0,
                "sky_card": 0.0,
                "lamps_windows": {
                    "emission_energy_multiplier": 0.4,
                    "note": "黃昏可開 intensityNight×0.35（environments.json lighting_hint）"
                }
            },
            "fog": {
                "enabled_low_quality": False,
                "enabled_mid_high": True,
                "fog_light_color": "#e8a070",
                "fog_light_energy": 0.95,
                "fog_depth_begin": 380,
                "fog_depth_end": 1200,
                "note": "同 environments.json dusk preset。"
            },
            "lighting_hint": "sun.energy 0.55、fill 0.18、ambient #c88868 0.4。"
        },
        "day": {
            "zh": "日",
            "albedo_multiply": {
                "ground": {"rgb": [1.0, 1.0, 1.0], "hex": "#FFFFFF"},
                "hills":  {"rgb": [1.0, 1.0, 1.0], "hex": "#FFFFFF"},
                "sky_card": {"rgb": [1.0, 1.0, 1.0], "hex": "#FFFFFF"}
            },
            "emission": {"ground": 0.0, "hills": 0.0, "sky_card": 0.0, "lamps_windows": {"emission_energy_multiplier": 0.0}},
            "note": "日間唔染色。"
        }
    },
    "godot_example": {
        "language": "GDScript",
        "snippet": "mat.albedo_color = Color(0.35, 0.40, 0.62)  # unshaded ground, night\\nmat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED\\nenv.adjustment_enabled = true\\nenv.adjustment_color_correction = lut_night"
    },
    "verified": {
        "renderer": "Godot 4.7.2 Compatibility + Xvfb + llvmpipe（OpenGL 3.3，唔用 --headless）",
        "quality": "低檔：影／glow／DoF／fog 關，lut_night 開",
        "preview": "/workspace/game-design/art_fix1/night_before_after.png"
    }
}

NIGHT_DOC = """# 夜景地面／遠山染色（給遊程，G0.1）

問題：夜 LUT 單獨唔夠暗。G0.1 地面同遠山係 **unshaded**，太陽／環境光減暗影響唔到草地，遠山亦未乘色，夜景仍然偏日間綠／米色。

## 用法

對 unshaded 地面同遠山嘅 `StandardMaterial3D.albedo_color` 乘下面嘅 RGB（texture 保持原樣，當 modulate）。**低檔都要開** `lut_night`（`adjustment_enabled = true`）。燈同窗嘅 emission **唔好剪**。

機器可讀：`art-pet/fx/night_tint.json`。霧參數同 `art-pet/fx/environments/environments.json` 嘅 night／dusk preset 一致。

## 夜（已用真 Godot 低檔驗證）

| 材質 | albedo multiply | hex | emission |
|---|---|---|---|
| 地面／草 tile | 0.35, 0.40, 0.62 | `#59709E` | 0 |
| 遠山 | 0.28, 0.28, 0.42 | `#47476B` | 0 |
| 天卡（可選） | 0.35, 0.40, 0.70 | `#5966B3` | 0 |
| 燈／窗／螢火瓶 | （唔乘暗色） | — | multiplier **1.2**，跟 `lights.json` intensityNight |

中／高檔再開夜霧：`fog_light_color #161a28`、energy 0.85、depth 360→1100。低檔熄霧，遠山靠上面嘅 hills 染色。

## 黃昏（附加，低檔同樣乘色＋`lut_dusk`）

| 材質 | albedo multiply | hex |
|---|---|---|
| 地面 | 0.78, 0.62, 0.50 | `#C79E80` |
| 遠山 | 0.70, 0.55, 0.48 | `#B38C7A` |
| 天卡（可選） | 0.85, 0.65, 0.55 | `#D9A68C` |

燈 multiplier 約 0.4（或 intensityNight×0.35）。霧跟 dusk preset：`#e8a070`、380→1200。

日間全部乘 `(1,1,1)`，燈 emission 0。

## 驗證

Godot 4.7.2 Compatibility、Xvfb、llvmpipe，低檔。對照圖：`/workspace/game-design/art_fix1/night_before_after.png`（左：只開夜 LUT；右：LUT＋呢組染色）。
"""


def write_night_tint(out_root):
    """G0.1 @ 86769723 已修好夜地／遠山，唔再寫 plug-in 值，以免重複乘暗。"""
    print('  night tint: already OK（遊程 G0.1 @ 86769723；唔寫 night_tint.json）', flush=True)
    return []


def patch_m2_clips_tool(out_root):
    """令 build_m2_clips.py 以後再生產都用坐低稿。"""
    src = os.path.join(HERE, 'build_m2_clips.py')
    # prefer existing m2 tool if we copied it
    cand = [
        os.path.join(out_root, 'art-pet/tools/build_m2_clips.py'),
        '/workspace/m2-actions-src/art-pet/tools/build_m2_clips.py',
        src,
    ]
    origin = next((p for p in cand if os.path.exists(p) and 'art_fix1' not in open(p).read()[:500] or (os.path.exists(p) and 'pose_idle_quiet' in open(p).read())), None)
    # Always copy from m2-actions-src if present
    origin = '/workspace/m2-actions-src/art-pet/tools/build_m2_clips.py'
    if not os.path.exists(origin):
        return []
    txt = open(origin).read()
    old = '''def pose_idle_quiet(i):
    """文靜：坐低喺度，輕輕呼吸、偶爾眨眼。"""
    blink = i in (2, 3)
    base = fr('blink_03' if blink else ('idle_03' if i % 2 else 'idle_01'))
    # 坐：下半壓扁、放低、稍闊
    breath = 0.70 + 0.03 * math.sin(i * math.pi / 3)
    sit = _squash(base, 56, breath, 1.18)
    sit = shift(sit, dy=6)
    im = rgba(64)
    blit(im, sit, 0, 0)
    # 坐墊／腿團（一眼睇到係坐住）
    fill_ellipse(im, 32, 58, 14 + (i % 2), 6, PAL['cream1'])
    fill_ellipse(im, 32, 57, 11, 4, PAL['cream2'])
    pset(im, 24, 56, PAL['cream3']); pset(im, 40, 56, PAL['cream3'])
    return finish_spr(im)
'''
    new = '''def pose_idle_quiet(i):
    """文靜：坐低收腳（Kurt 批坐低草稿，2026-11-11），輕輕呼吸、偶爾眨眼。"""
    from art_fix1_sit import pose_idle_quiet as _sit
    return _sit(i)
'''
    dest_dir = os.path.join(out_root, 'art-pet/tools')
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, 'build_m2_clips.py')
    if old in txt:
        txt = txt.replace(old, new)
        open(dest, 'w').write(txt)
        print('  patched build_m2_clips.py pose_idle_quiet', flush=True)
    else:
        if origin != dest:
            shutil.copy2(origin, dest)
        print('  warn: pose_idle_quiet block not patched (pattern mismatch); copied original', flush=True)
    # copy sit module next to it
    for fn in ('art_fix1_sit.py', 'art_fix1_liveliness.py', 'm1_common.py'):
        s = os.path.join(HERE, fn)
        d = os.path.join(dest_dir, fn)
        if os.path.abspath(s) != os.path.abspath(d) and os.path.exists(s):
            shutil.copy2(s, d)
    return [dest]


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else '/workspace/art-fix1-src'
    print('build art-fix1 →', root, flush=True)
    written = []
    written += SIT.build_idle_quiet(root)['written']
    written += LIVE.build_kid(root)
    written += LIVE.build_visitors(root)
    written += write_night_tint(root)
    written += patch_m2_clips_tool(root)
    # also copy this orchestrator
    dest_dir = os.path.join(root, 'art-pet/tools')
    os.makedirs(dest_dir, exist_ok=True)
    me = os.path.abspath(__file__)
    if os.path.abspath(os.path.join(dest_dir, 'build_art_fix1.py')) != me:
        shutil.copy2(me, os.path.join(dest_dir, 'build_art_fix1.py'))
        written.append(os.path.join(dest_dir, 'build_art_fix1.py'))
    print('done', len(written), 'paths', flush=True)


if __name__ == '__main__':
    main()
