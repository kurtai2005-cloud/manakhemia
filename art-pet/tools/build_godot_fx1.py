#!/usr/bin/env python3
"""build_godot_fx1.py — Godot 4 強化第一批：景深＋7 套調色 LUT、粒子圖＋GPUParticles 參數。
用法：PYTHONDONTWRITEBYTECODE=1 python3 art-pet/tools/build_godot_fx1.py [--root DIR]
預設 root＝本檔 art-pet 上一層（staging 根）。只寫 art-pet/fx/（同工具已存在就跳過覆寫工具本身）。
"""
import os, sys, json, math
import numpy as np
from PIL import Image, ImageDraw
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fx1_common as C

def root_of():
    r = os.path.abspath(os.path.join(HERE, '../..'))
    if '--root' in sys.argv:
        r = os.path.abspath(sys.argv[sys.argv.index('--root') + 1])
    return r

def dump(p, obj):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
        f.write('\n')

def put(p, arr):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    C.save_png(p, arr)


# ---------------- Environment / CameraAttributes ----------------
def environments():
    dof = dict(C.DEFAULT_DOF)
    # Godot 屬性名（CameraAttributesPractical / Environment），遊程轉 .tres
    cam_attr = {
        'resource': 'CameraAttributesPractical',
        'exposure_multiplier': 1.0,
        'auto_exposure_enabled': False,
        **{k: v for k, v in dof.items()},
        'note': '對齊 H1 鏡頭 pitch 30°、dist 580、target [0,30,-72]、1 unit＝1 art px。焦段約 510–720（寵物／中景）；近景高草／畫面下方約 400 開始朦；遠山／天約 720 起朦，1100 全朦。amount 0.16＝八方式輕朦，像素唔好過糊。若 import_scale=0.01，所有距離 ×0.01（amount 唔改）。',
    }
    def env(fog_color, fog_begin, fog_end, fog_energy, glow, exposure, bright, contrast, sat, lut, extra=None):
        e = {
            'background_mode': 'keep_or_sky',
            'background_note': '場景已有 backdrop mesh／sky 板；唔好用會蓋過美術天空嘅 Clear Color。',
            'tonemap_mode': 'Linear',
            'tonemap_exposure': exposure,
            'tonemap_white': 1.0,
            'tonemap_note': 'LUT 按 Linear（預覽 clip 0–1）編。若改 ACES／AgX／Filmic 要再校 LUT。',
            'glow_enabled': glow['enabled'],
            'glow_intensity': glow['intensity'],
            'glow_strength': glow['strength'],
            'glow_bloom': glow['bloom'],
            'glow_hdr_threshold': glow['hdr_threshold'],
            'glow_hdr_scale': glow.get('hdr_scale', 2.0),
            'glow_blend_mode': glow.get('blend_mode', 'softlight' if glow['intensity'] < 0.5 else 'screen'),
            'glow_normalized': False,
            'fog_enabled': True,
            'fog_mode': 'depth',  # Environment.FOG_MODE_DEPTH
            'fog_light_color': fog_color,
            'fog_light_energy': fog_energy,
            'fog_sun_scatter': 0.08,
            'fog_density': 0.0,  # depth 模式唔靠 exponential density
            'fog_aerial_perspective': 0.15,
            'fog_sky_affect': 0.4,
            'fog_depth_begin': fog_begin,
            'fog_depth_end': fog_end,
            'fog_depth_curve': 1.0,
            'ssr_enabled': False,
            'ssao_enabled': False,
            'ssil_enabled': False,
            'sdfgi_enabled': False,
            'volumetric_fog_enabled': False,
            'adjustment_enabled': True,
            'adjustment_brightness': bright,
            'adjustment_contrast': contrast,
            'adjustment_saturation': sat,
            'adjustment_color_correction': lut,
        }
        if extra:
            e.update(extra)
        return e

    glow_day = dict(enabled=True, intensity=0.22, strength=1.0, bloom=0.0, hdr_threshold=1.0, blend_mode='softlight')
    glow_dusk = dict(enabled=True, intensity=0.45, strength=1.05, bloom=0.02, hdr_threshold=0.85, blend_mode='screen')
    glow_night = dict(enabled=True, intensity=0.75, strength=1.1, bloom=0.04, hdr_threshold=0.62, blend_mode='screen')

    presets = [
        dict(id='day', zh='日', lut='art-pet/fx/luts/lut_day.png',
             environment=env('#ffe8c8', 420, 1400, 1.0, glow_day, 1.0, 1.0, 1.0, 1.0, 'art-pet/fx/luts/lut_day.png'),
             lighting_hint='沿用 H1／草原 lights.json 日值（sun 1.0、fill 0.38、ambient #cfe0f0 0.55、燈 intensity 0）。'),
        dict(id='dusk', zh='黃昏', lut='art-pet/fx/luts/lut_dusk.png',
             environment=env('#e8a070', 380, 1200, 0.95, glow_dusk, 0.92, 1.0, 1.02, 1.0, 'art-pet/fx/luts/lut_dusk.png'),
             lighting_hint='建議 sun.intensity 0.55、fill 0.18、ambient #c88868 0.4；可開少量燈 intensityNight×0.35。'),
        dict(id='night', zh='夜', lut='art-pet/fx/luts/lut_night.png',
             environment=env('#161a28', 360, 1100, 0.85, glow_night, 0.88, 1.0, 1.04, 0.96, 'art-pet/fx/luts/lut_night.png',
                             extra=dict(night_ground_target_luma=26, night_sky_target_luma=55,
                                        engine_issue='遊程報 game 夜地 lum 約 55（過亮），認可 GIF 約 26；夜空約 55。請同時用本 Environment（曝光 0.88、霧 #161a28）＋ lut_night。只換 LUT 時，LUT 會把暖綠中灰（約 55）壓到約 26，藍色／中性天空保持約 55，暖色燈高光保留。')),
             lighting_hint='H1 night：sun 0.12、ambient #4a5a90 0.35、燈用 intensityNight。若地上仍然偏亮，再略降 ambient 或靠 LUT。window 用 window 燈、側窗請改綁 window_side。'),
        dict(id='spring', zh='春', lut='art-pet/fx/luts/lut_spring.png',
             environment=env('#ffe6dc', 420, 1400, 1.0, glow_day, 1.02, 1.02, 1.0, 1.0, 'art-pet/fx/luts/lut_spring.png'),
             lighting_hint='日間季節；太陽／fill 用日值。花瓣粒子可開。'),
        dict(id='summer', zh='夏', lut='art-pet/fx/luts/lut_summer.png',
             environment=env('#ffe8c8', 440, 1500, 1.0, dict(enabled=True, intensity=0.28, strength=1.0, bloom=0.01, hdr_threshold=0.95, blend_mode='softlight'), 1.04, 1.0, 1.02, 1.0, 'art-pet/fx/luts/lut_summer.png'),
             lighting_hint='日間季節；可稍提高 sun 至 1.05。'),
        dict(id='autumn', zh='秋', lut='art-pet/fx/luts/lut_autumn.png',
             environment=env('#efc8a0', 400, 1300, 1.0, glow_day, 0.98, 1.0, 1.02, 1.0, 'art-pet/fx/luts/lut_autumn.png'),
             lighting_hint='日間季節；落葉粒子用 autumn 幀組。'),
        dict(id='winter', zh='冬', lut='art-pet/fx/luts/lut_winter.png',
             environment=env('#d0dce8', 380, 1200, 1.0, glow_day, 0.98, 1.0, 1.0, 0.94, 'art-pet/fx/luts/lut_winter.png'),
             lighting_hint='日間季節；開雪粒子。sun 可降到 0.85、ambient 偏藍。'),
    ]
    return {
        'format': 'godot_fx1.environment/1',
        'engine': 'Godot 4',
        'units': {
            'art': '1 unit = 1 art px, Y up, +Z toward camera',
            'recommended_import_scale': 1.0,
            'metric_alternative_scale': 0.01,
            'metric_note': 'scale 0.01 時，Environment 嘅 fog_depth_* 同 CameraAttributes 嘅 dof_*_distance／transition 全部 ×0.01；amount／glow／tonemap／LUT 唔改。',
        },
        'camera': {
            'align': 'scenes/garden3d/H1/camera.json 同 hunt3d/prairie/camera.json',
            'pitchDeg': 30, 'dist': 580, 'fovDeg': 40, 'target': [0, 30, -72],
        },
        'camera_attributes': cam_attr,
        'lut': {
            'size': [C.LUT_W, C.LUT_H],
            'cube': C.LUT_SIZE,
            'layout': 'Godot 4 official 33×33×33 horizontal strip（同 docs environment_adjustments_3d_lut_template）：寬 33×33＝1089，高 33。由左到右 33 格＝B 0→1；格內 X＝R 0→1，Y 上→下＝G 0→1。',
            'import': 'Import As Texture3D；Horizontal slices=33，Vertical slices=1；Filter Linear；唔做 mipmap；壓縮用 Lossless／VRAM Uncompressed（避免 LUT 區塊）。指派到 Environment.adjustment_color_correction。LUT 喺 tonemap 之後生效。',
        },
        'presets': presets,
        'quality': {
            'baseline': 'low',
            'zh': '低畫質係開發基準：同一個 3D 場景，只熄影／glow／DoF／fog（可降解像度），唔可以退返平面層。LUT／調色低檔都開（成本低）。粒子用 amount_low。中／高只喺開發者模式開效果。舊 HTML5／three.js 已凍結，今批只對 Godot 4。',
            'tiers': {
                'low': {
                    'shadow_enabled': False,
                    'glow_enabled': False,
                    'dof_enabled': False,
                    'fog_enabled': False,
                    'adjustment_enabled': True,
                    'lut': True,
                    'particles': 'amount_low',
                },
                'mid': {
                    'shadow_enabled': True,
                    'glow_enabled': True,
                    'dof_enabled': True,
                    'fog_enabled': True,
                    'adjustment_enabled': True,
                    'lut': True,
                    'particles': 'amount_mid',
                },
                'high': {
                    'shadow_enabled': True,
                    'glow_enabled': True,
                    'dof_enabled': True,
                    'fog_enabled': True,
                    'adjustment_enabled': True,
                    'lut': True,
                    'particles': 'amount_high',
                    'glow_note': '用各 preset 嘅 glow_*；高檔可把 glow_intensity 再 ×1.15，DoF 距離／amount 同 mid。',
                },
            },
            # 逐項：low＝關效果；mid／high＝開。LUT 三檔都開。下面 presets／camera_attributes 寫嘅係 mid／high 嘅「開」值。
            'field_tiers': {
                'dof_blur_near_enabled': {'low': False, 'mid': True, 'high': True},
                'dof_blur_far_enabled': {'low': False, 'mid': True, 'high': True},
                'dof_blur_amount': {'low': 0.0, 'mid': 0.16, 'high': 0.16},
                'dof_blur_near_distance': {'low': None, 'mid': 400.0, 'high': 400.0, 'note': 'low 熄 DoF 時唔使用'},
                'dof_blur_near_transition': {'low': None, 'mid': 110.0, 'high': 110.0},
                'dof_blur_far_distance': {'low': None, 'mid': 720.0, 'high': 720.0},
                'dof_blur_far_transition': {'low': None, 'mid': 380.0, 'high': 380.0},
                'glow_enabled': {'low': False, 'mid': True, 'high': True},
                'fog_enabled': {'low': False, 'mid': True, 'high': True},
                'shadow_enabled': {'low': False, 'mid': True, 'high': True, 'note': 'DirectionalLight3D.shadow_enabled；H1 sun.shadowIntensity 0.3 只 mid／high'},
                'adjustment_enabled': {'low': True, 'mid': True, 'high': True},
                'adjustment_color_correction': {'low': True, 'mid': True, 'high': True, 'note': 'LUT 便宜，低檔都開'},
                'tonemap_mode': {'low': 'Linear', 'mid': 'Linear', 'high': 'Linear'},
                'ssr_enabled': {'low': False, 'mid': False, 'high': False},
                'ssao_enabled': {'low': False, 'mid': False, 'high': False},
                'ssil_enabled': {'low': False, 'mid': False, 'high': False},
                'sdfgi_enabled': {'low': False, 'mid': False, 'high': False},
                'volumetric_fog_enabled': {'low': False, 'mid': False, 'high': False},
            },
        },
        'mobile_note': '目標只係 Godot 4（舊 HTML5／three.js 已凍結）。建議 Mobile 或 Forward+。Compatibility 嘅 Glow 參數較少、DoF 請遊程確認。SSR／SSAO／SSIL／SDFGI／Volumetric Fog 三檔都關。低檔再開效能：降解像度，唔好改平面場景。粒子數量見 amount_low／amount_mid／amount_high。',
    }


def godot_import():
    return {
        'format': 'godot_fx1.godot_import/1',
        'engine': 'Godot 4',
        'lut': {
            'files': 'art-pet/fx/luts/lut_*.png',
            'import_as': 'Texture3D',
            'slices_horizontal': C.LUT_SIZE,
            'slices_vertical': 1,
            'filter': 'Linear',
            'mipmaps': False,
            'compress': 'Lossless or VRAM Uncompressed',
            'srgb': False,
            'assign': 'Environment.adjustment_color_correction（調整／Adjustments → Color Correction）',
            'verify': '先用 lut_identity.png：畫面應同冇 LUT 一樣。若色偏／切片感，多半係 slices 或 Y 向設錯。',
        },
        'particle_sprites': {
            'filter': 'Nearest',
            'mipmaps': False,
            'srgb': True,
            'transparency': 'AlphaScissor 0.5（雨／雪／葉／花瓣／碎屑）；螢火蟲建議 blend_mode=add，RGB=0 即唔加。',
            'billboard': 'PARTICLE_BILLBOARD / Billboard Mode = Particle Billboard',
            'particles_anim': '用 StandardMaterial3D particles_anim_h_frames／v_frames／loop，配合 ParticleProcessMaterial anim_speed',
        },
        'environment_tres': '將 environments.json 各 preset 轉 WorldEnvironment.environment 同 Camera3D.attributes（CameraAttributesPractical）。LUT 路徑按專案 res:// 改。',
    }


# ---------------- particles ----------------
def px(img, x, y, rgba):
    h, w = img.shape[:2]
    if 0 <= x < w and 0 <= y < h:
        img[y, x] = rgba


def disk(img, cx, cy, r, rgba, even=False):
    for y in range(int(cy - r - 1), int(cy + r + 2)):
        for x in range(int(cx - r - 1), int(cx + r + 2)):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r + (0.2 if not even else 0):
                px(img, x, y, rgba)


def blit(dst, src, x, y):
    """貼硬 alpha sprite。"""
    h, w = src.shape[:2]
    x0, y0 = int(x), int(y)
    for j in range(h):
        for i in range(w):
            if src[j, i, 3] >= 128:
                px(dst, x0 + i, y0 + j, src[j, i])


def rot_frames(base, n=8, size=None):
    im = Image.fromarray(base)
    S = size or base.shape[0]
    frames = []
    for i in range(n):
        r = im.rotate(-i * (360 / n), resample=Image.Resampling.NEAREST, expand=False, fillcolor=(0, 0, 0, 0))
        arr = C.hard_rgba(np.array(r.convert('RGBA')))
        if arr.shape[0] != S or arr.shape[1] != S:
            canv = np.zeros((S, S, 4), np.uint8)
            # center paste
            offy = (S - arr.shape[0]) // 2
            offx = (S - arr.shape[1]) // 2
            canv[offy:offy + arr.shape[0], offx:offx + arr.shape[1]] = arr
            arr = C.hard_rgba(canv)
        frames.append(arr)
    return frames


def sheet_of(rows, cell, pad_to_pot=True):
    """rows: list[list[HxWx4]]；每格 cell×cell。"""
    n_r = len(rows)
    n_c = max(len(r) for r in rows)
    W, H = n_c * cell, n_r * cell
    if pad_to_pot:
        def up(n):
            p = 1
            while p < n:
                p *= 2
            return p
        W, H = up(W), up(H)
    out = np.zeros((H, W, 4), np.uint8)
    frames = {}
    for j, row in enumerate(rows):
        for i, fr in enumerate(row):
            y, x = j * cell, i * cell
            h, w = fr.shape[:2]
            oy, ox = y + (cell - h) // 2, x + (cell - w) // 2
            out[oy:oy + h, ox:ox + w] = fr
            frames[f'r{j}c{i}'] = dict(frame=dict(x=x, y=y, w=cell, h=cell))
    return C.hard_rgba(out), frames, (W, H)


# ---- draw sprites ----
def _firefly_frame(phase, size=8):
    im = np.zeros((size, size, 4), np.uint8)
    cx = cy = size // 2 - 0.5
    # brightness pulse
    t = 0.45 + 0.55 * (0.5 + 0.5 * math.sin(phase))
    core = np.array([255, 255, int(200 + 40 * t), 255], np.uint8)
    mid = np.array([210, 255, int(140 + 40 * t), 255], np.uint8)
    rim = np.array([160, 230, 90, 255], np.uint8)
    # hard diamond glow (no soft alpha)
    coords = {
        0: [(0, 0, core)],
        1: [(-1, 0, mid), (1, 0, mid), (0, -1, mid), (0, 1, mid)],
        2: [(-1, -1, rim), (1, -1, rim), (-1, 1, rim), (1, 1, rim)],
    }
    if t > 0.7:
        coords[3] = [(-2, 0, rim), (2, 0, rim), (0, -2, rim), (0, 2, rim)]
    for _, pts in coords.items():
        for dx, dy, col in pts:
            px(im, int(cx + dx + 0.5), int(cy + dy + 0.5), col)
    # tiny wings on mid phases
    if 0.3 < (phase % (2 * math.pi)) < 2.2:
        wcol = np.array([200, 255, 180, 255], np.uint8)
        px(im, int(cx - 2), int(cy), wcol)
        px(im, int(cx + 2), int(cy), wcol)
    return C.hard_rgba(im)


def make_fireflies():
    cell = 8
    frames = [_firefly_frame(i * math.pi / 4) for i in range(8)]
    # second row: slightly larger pulse / offset body for variation
    frames2 = [_firefly_frame(i * math.pi / 4 + 0.8) for i in range(8)]
    sheet, fmap, hw = sheet_of([frames, frames2], cell)
    return sheet, dict(
        id='fireflies', zh='螢火蟲', cell=cell, image='particles/fireflies.png',
        frames_h=8, frames_v=2, pivot=[4, 4],
        colors={'core': '#ffffc8', 'glow': '#c8ffb0', 'align': 'H1 jar #c8ffb0／預覽螢火 #fff696'},
        animations={'pulse': dict(frames=[f'r0c{i}' for i in range(8)], fps=8, loop=True)},
        atlas_frames=fmap,
        material=dict(shading_mode='unshaded', blend_mode='add', billboard='particle',
                      particles_anim_h_frames=8, particles_anim_v_frames=2, particles_anim_loop=True,
                      texture_filter='Nearest', vertex_color_use_as_albedo=True, emissive=True),
        process_material=dict(
            emission_shape='box',
            emission_box_extents=[140, 40, 90],
            emission_offset_hint='H1 花園：中心約 [−40, 35, −20]（燈柱／螢火瓶／舞台一帶）；狩獵草原：中心 [0, 40, 10]，只喺黃昏／夜開。',
            direction=[0, 1, 0], spread=180, flatness=0.0,
            initial_velocity_min=4, initial_velocity_max=12,
            gravity=[0, 0.4, 0],
            damping_min=0.5, damping_max=1.2,
            angular_velocity_min=-4, angular_velocity_max=4,
            orbit_velocity_min=-0.05, orbit_velocity_max=0.05,
            scale_min=0.85, scale_max=1.35,
            color='#e8ffc0',
            color_ramp=[{'offset': 0.0, 'color': '#ffffff00'},
                        {'offset': 0.12, 'color': '#ffffe8ff'},
                        {'offset': 0.7, 'color': '#d8ffb0ff'},
                        {'offset': 1.0, 'color': '#ffffe800'}],
            hue_variation_min=-0.04, hue_variation_max=0.06,
            anim_speed_min=0.6, anim_speed_max=1.2,
            turbulence_enabled=True, turbulence_noise_strength=0.8,
            turbulence_noise_scale=1.5, turbulence_noise_speed=[0.2, 0.15, 0.2],
        ),
        gpu_particles=dict(amount=26, amount_high=26, amount_mid=16, amount_low=8, amount_mobile=16, lifetime=6.0, preprocess=3.0,
                           explosiveness=0.0, randomness=0.4, speed_scale=1.0, local_coords=False,
                           visibility_aabb=[-200, 0, -160, 400, 120, 320]),
    )


def _leaf_shape(kind, rgb, size=16):
    im = np.zeros((size, size, 4), np.uint8)
    cx = cy = size // 2
    col = np.array([*rgb, 255], np.uint8)
    dark = np.array([max(0, rgb[0] - 35), max(0, rgb[1] - 30), max(0, rgb[2] - 25), 255], np.uint8)
    lite = np.array([min(255, rgb[0] + 40), min(255, rgb[1] + 35), min(255, rgb[2] + 20), 255], np.uint8)
    vein = np.array([max(0, rgb[0] - 50), max(0, rgb[1] - 45), max(0, rgb[2] - 30), 255], np.uint8)
    # kind 0 oval, 1 notched maple-ish, 2 long willow
    if kind == 0:
        for y in range(size):
            for x in range(size):
                dx, dy = (x - cx) / 4.2, (y - cy) / 6.0
                if dx * dx + dy * dy <= 1:
                    px(im, x, y, col)
        # stem
        px(im, cx, size - 3, dark); px(im, cx, size - 2, dark)
        # vein
        for y in range(cy - 4, cy + 5):
            px(im, cx, y, vein)
        px(im, cx + 1, cy - 2, lite); px(im, cx - 1, cy, lite)
        # notch tip
        px(im, cx, 2, 0)
    elif kind == 1:
        body = [(0, -6), (2, -4), (4, -2), (5, 0), (3, 2), (1, 4), (0, 6),
                (-1, 4), (-3, 2), (-5, 0), (-4, -2), (-2, -4)]
        for dx, dy in body:
            disk(im, cx + dx, cy + dy, 1.2, col)
        disk(im, cx, cy, 3.2, col)
        px(im, cx, size - 2, dark)
        for y in range(cy - 3, cy + 5):
            px(im, cx, y, vein)
        px(im, cx + 2, cy - 1, lite)
    else:
        for y in range(2, size - 2):
            t = (y - 2) / (size - 4)
            w = 1 + int(2.2 * math.sin(math.pi * t))
            for x in range(cx - w, cx + w + 1):
                px(im, x, y, col if x != cx else vein)
        px(im, cx + 1, cy, lite)
        px(im, cx, size - 2, dark)
    return C.hard_rgba(im)


LEAF_PAL = {
    'spring': [(126, 196, 90), (170, 214, 110), (90, 168, 96)],
    'summer': [(58, 148, 62), (90, 168, 48), (40, 120, 55)],
    'autumn': [(212, 132, 42), (196, 64, 36), (148, 86, 36)],
    'winter': [(120, 96, 64), (96, 84, 64), (140, 120, 96)],
}


def make_leaves():
    cell = 16
    seasons = ['spring', 'summer', 'autumn', 'winter']
    rows = []
    groups = {}
    for si, season in enumerate(seasons):
        for ki, rgb in enumerate(LEAF_PAL[season]):
            base = _leaf_shape(ki, rgb, cell)
            frs = rot_frames(base, 8, cell)
            rows.append(frs)
            groups[f'{season}_{ki}'] = [f'r{len(rows)-1}c{i}' for i in range(8)]
    sheet, fmap, hw = sheet_of(rows, cell)
    return sheet, dict(
        id='leaves', zh='落葉（四季顏色）', cell=cell, image='particles/leaves.png',
        frames_h=8, frames_v=12,  # 4 seasons × 3 shapes（圖高 pad 到 256）
        pivot=[8, 8],
        groups=groups,
        season_rows={'spring': [0, 1, 2], 'summer': [3, 4, 5], 'autumn': [6, 7, 8], 'winter': [9, 10, 11]},
        atlas_frames=fmap,
        material=dict(shading_mode='unshaded', blend_mode='mix', transparency='alpha_scissor',
                      alpha_scissor_threshold=0.5, billboard='particle',
                      particles_anim_h_frames=8, particles_anim_v_frames=12, particles_anim_loop=True,
                      texture_filter='Nearest', vertex_color_use_as_albedo=True),
        process_material=dict(
            emission_shape='box',
            emission_box_extents=[180, 10, 80],
            emission_offset_hint='樹冠／畫面上方：H1 大樹約 [−110, 140, −44]；草原上空 [0, 160, −40]。',
            direction=[0.25, -1, 0.05], spread=18,
            initial_velocity_min=18, initial_velocity_max=42,
            gravity=[0, -28, 0],
            damping_min=0.4, damping_max=1.0,
            angular_velocity_min=-12, angular_velocity_max=12,
            orbit_velocity_min=-0.15, orbit_velocity_max=0.15,
            tangential_accel_min=-4, tangential_accel_max=4,
            scale_min=0.7, scale_max=1.35,
            color='#ffffff',
            color_ramp=[{'offset': 0.0, 'color': '#ffffffff'},
                        {'offset': 0.85, 'color': '#ffffffee'},
                        {'offset': 1.0, 'color': '#ffffff00'}],
            anim_speed_min=0.4, anim_speed_max=1.0,
            turbulence_enabled=True, turbulence_noise_strength=1.1,
            turbulence_noise_scale=2.0, turbulence_noise_speed=[0.4, 0.0, 0.15],
        ),
        gpu_particles=dict(amount=28, amount_high=28, amount_mid=16, amount_low=6, amount_mobile=16, amount_autumn=40, amount_autumn_mid=24, amount_autumn_low=8,
                           lifetime=5.0, preprocess=3.0, explosiveness=0.0, randomness=0.5,
                           speed_scale=1.0, local_coords=False,
                           visibility_aabb=[-260, -20, -200, 520, 280, 400],
                           season_note='春天用 spring_* 幀、夏天 summer_*、秋天 autumn_* 並用較多 amount、冬天 winter_* 減少量。anim_offset 隨機揀行。'),
    )


def _petal(kind, rgb, size=8):
    im = np.zeros((size, size, 4), np.uint8)
    cx = cy = size // 2
    col = np.array([*rgb, 255], np.uint8)
    lite = np.array([min(255, rgb[0] + 40), min(255, rgb[1] + 35), min(255, rgb[2] + 30), 255], np.uint8)
    if kind == 0:  # teardrop
        for y in range(1, size - 1):
            t = (y - 1) / (size - 2)
            w = 1 if t < 0.25 or t > 0.85 else 2
            for x in range(cx - w, cx + w + (1 if t > 0.3 else 0)):
                px(im, x, y, lite if x == cx and y < cy else col)
    elif kind == 1:  # round
        disk(im, cx, cy, 2.3, col)
        px(im, cx, cy, lite)
        px(im, cx, cy + 3, col)
    else:  # notched heart-ish
        px(im, cx - 1, cy - 1, col); px(im, cx + 1, cy - 1, col)
        disk(im, cx, cy, 2.1, col)
        px(im, cx, cy, lite)
        px(im, cx, cy + 3, col)
    return C.hard_rgba(im)


def make_petals():
    cell = 8
    pal = [(255, 170, 186), (255, 226, 232), (255, 214, 170)]  # 粉、白、淺金
    rows = []
    groups = {}
    names = ['pink', 'white', 'gold']
    for i, (nm, rgb) in enumerate(zip(names, pal)):
        # two shapes per color
        a = rot_frames(_petal(i % 3, rgb, cell), 8, cell)
        rows.append(a)
        groups[nm] = [f'r{i}c{k}' for k in range(8)]
    sheet, fmap, hw = sheet_of(rows, cell)
    return sheet, dict(
        id='petals', zh='花瓣', cell=cell, image='particles/petals.png',
        frames_h=8, frames_v=4, pivot=[4, 4], groups=groups, atlas_frames=fmap,
        material=dict(shading_mode='unshaded', blend_mode='mix', transparency='alpha_scissor',
                      alpha_scissor_threshold=0.5, billboard='particle',
                      particles_anim_h_frames=8, particles_anim_v_frames=4, particles_anim_loop=True,
                      texture_filter='Nearest', vertex_color_use_as_albedo=True),
        process_material=dict(
            emission_shape='box', emission_box_extents=[120, 8, 60],
            emission_offset_hint='花圃／盆花上方：H1 pot／bed 一帶；草原花叢上方。春夏為主。',
            direction=[0.15, -1, 0], spread=22,
            initial_velocity_min=8, initial_velocity_max=20,
            gravity=[0, -10, 0],
            damping_min=0.6, damping_max=1.4,
            angular_velocity_min=-8, angular_velocity_max=8,
            orbit_velocity_min=-0.2, orbit_velocity_max=0.2,
            scale_min=0.8, scale_max=1.4,
            color='#ffffff',
            color_ramp=[{'offset': 0, 'color': '#ffffffff'}, {'offset': 0.8, 'color': '#ffffffcc'}, {'offset': 1, 'color': '#ffffff00'}],
            anim_speed_min=0.3, anim_speed_max=0.8,
            turbulence_enabled=True, turbulence_noise_strength=1.3, turbulence_noise_scale=2.4,
            turbulence_noise_speed=[0.35, 0.05, 0.2],
        ),
        gpu_particles=dict(amount=22, amount_high=22, amount_mid=12, amount_low=6, amount_mobile=12, lifetime=6.5, preprocess=4.0,
                           explosiveness=0.0, randomness=0.5, local_coords=False,
                           visibility_aabb=[-200, -10, -160, 400, 200, 320]),
    )


def make_rain():
    cell = 16
    frames = []
    # 4 streak lengths, slight head highlight
    for L in (6, 8, 11, 14):
        im = np.zeros((cell, cell, 4), np.uint8)
        x = cell // 2
        y0 = (cell - L) // 2
        body = np.array([176, 200, 230, 255], np.uint8)
        head = np.array([230, 240, 255, 255], np.uint8)
        for i in range(L):
            px(im, x, y0 + i, head if i == 0 else body)
            if L >= 11 and i > 1:
                px(im, x, y0 + i, body)
        frames.append(C.hard_rgba(im))
    # 4 splash frames (small plus → ring dots)
    spl = []
    for k in range(4):
        im = np.zeros((cell, cell, 4), np.uint8)
        c = np.array([200, 220, 240, 255], np.uint8)
        cx = cy = cell // 2
        if k == 0:
            px(im, cx, cy, c)
        elif k == 1:
            for d in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                px(im, cx + d[0], cy + d[1], c)
        elif k == 2:
            for d in [(-2, 0), (2, 0), (0, -2), (0, 1), (-1, 1), (1, 1)]:
                px(im, cx + d[0], cy + d[1], c)
        else:
            for d in [(-2, 1), (2, 1), (0, 2), (-1, 2), (1, 2)]:
                px(im, cx + d[0], cy + d[1], np.array([180, 200, 220, 255], np.uint8))
        spl.append(C.hard_rgba(im))
    sheet, fmap, hw = sheet_of([frames, spl], cell)
    return sheet, dict(
        id='rain', zh='雨', cell=cell, image='particles/rain.png',
        frames_h=4, frames_v=2, pivot=[8, 8],
        groups={'streak': [f'r0c{i}' for i in range(4)], 'splash': [f'r1c{i}' for i in range(4)]},
        atlas_frames=fmap,
        material=dict(shading_mode='unshaded', blend_mode='mix', transparency='alpha_scissor',
                      alpha_scissor_threshold=0.5, billboard='particle',
                      particles_anim_h_frames=4, particles_anim_v_frames=2, particles_anim_loop=False,
                      texture_filter='Nearest', vertex_color_use_as_albedo=True,
                      particle_flag_align_y_hint='streak 建議 ParticleProcessMaterial particle_flag_align_y=true，令長條對準速度方向。'),
        process_material=dict(
            emission_shape='box', emission_box_extents=[220, 8, 140],
            emission_offset_hint='畫面頂上方 y≈220，覆蓋中景。',
            direction=[0.08, -1, 0], spread=3,
            initial_velocity_min=260, initial_velocity_max=380,
            gravity=[0, -60, 0],
            scale_min=0.8, scale_max=1.3,
            color='#d0e4ffff',
            color_ramp=[{'offset': 0, 'color': '#d0e4ffff'}, {'offset': 1, 'color': '#d0e4ffcc'}],
            anim_speed_min=0.0, anim_speed_max=0.0,  # 靜態長條；splash 用另一系統
            particle_flag_align_y=True,
        ),
        gpu_particles=dict(amount=120, amount_high=120, amount_mid=70, amount_low=24, amount_mobile=70, lifetime=0.85, preprocess=0.8,
                           explosiveness=0.0, randomness=0.25, local_coords=False,
                           visibility_aabb=[-300, -40, -220, 600, 320, 440],
                           splash_note='落地水花可用第二個 one_shot GPUParticles3D，用 splash 幀、amount 每擊 1、lifetime 0.25、gravity 0，喺地面碰撞或定高 y=0 觸發。M1 可先淨係用 streak。'),
    )


def _flake(kind, size=8):
    im = np.zeros((size, size, 4), np.uint8)
    w = np.array([245, 250, 255, 255], np.uint8)
    b = np.array([210, 226, 245, 255], np.uint8)
    cx = cy = size // 2
    if kind == 0:  # 2x2
        px(im, cx, cy, w); px(im, cx + 1, cy, w)
        px(im, cx, cy + 1, b); px(im, cx + 1, cy + 1, w)
    elif kind == 1:  # plus
        for d in [(-1, 0), (1, 0), (0, -1), (0, 1), (0, 0)]:
            px(im, cx + d[0], cy + d[1], w if d == (0, 0) else b)
    elif kind == 2:  # small asterisk
        for d in [(-1, 0), (1, 0), (0, -1), (0, 1), (0, 0), (-1, -1), (1, 1), (-1, 1), (1, -1)]:
            px(im, cx + d[0], cy + d[1], w if abs(d[0]) + abs(d[1]) <= 1 else b)
    else:  # tiny crystal
        disk(im, cx, cy, 1.2, w)
        px(im, cx, cy - 2, b); px(im, cx, cy + 2, b)
        px(im, cx - 2, cy, b); px(im, cx + 2, cy, b)
    return C.hard_rgba(im)


def make_snow():
    cell = 8
    rows = []
    groups = {}
    names = ['dot', 'plus', 'asterisk', 'crystal']
    for i, nm in enumerate(names):
        base = _flake(i, cell)
        # 4 twinkle: original, dimmer, original, slightly bigger via draw
        frs = [base]
        dim = base.copy()
        dim[dim[..., 3] > 0, :3] = (dim[dim[..., 3] > 0, :3] * 0.7).astype(np.uint8)
        frs.append(C.hard_rgba(dim))
        frs.append(base)
        frs.append(base)  # hold
        # pad to 8 with rotations of asterisk/crystal only
        extra = rot_frames(base, 4, cell)
        frs = (frs + extra)[:8]
        rows.append(frs)
        groups[nm] = [f'r{i}c{k}' for k in range(8)]
    sheet, fmap, hw = sheet_of(rows, cell)
    return sheet, dict(
        id='snow', zh='雪', cell=cell, image='particles/snow.png',
        frames_h=8, frames_v=4, pivot=[4, 4], groups=groups, atlas_frames=fmap,
        material=dict(shading_mode='unshaded', blend_mode='mix', transparency='alpha_scissor',
                      alpha_scissor_threshold=0.5, billboard='particle',
                      particles_anim_h_frames=8, particles_anim_v_frames=4, particles_anim_loop=True,
                      texture_filter='Nearest', vertex_color_use_as_albedo=True),
        process_material=dict(
            emission_shape='box', emission_box_extents=[220, 8, 140],
            emission_offset_hint='畫面頂上方 y≈200。',
            direction=[0.1, -1, 0], spread=12,
            initial_velocity_min=12, initial_velocity_max=28,
            gravity=[0, -8, 0],
            damping_min=0.2, damping_max=0.6,
            angular_velocity_min=-6, angular_velocity_max=6,
            orbit_velocity_min=-0.12, orbit_velocity_max=0.12,
            scale_min=0.6, scale_max=1.5,
            color='#f5f8ffff',
            color_ramp=[{'offset': 0, 'color': '#ffffffff'}, {'offset': 0.9, 'color': '#f0f6ffee'}, {'offset': 1, 'color': '#ffffff00'}],
            anim_speed_min=0.4, anim_speed_max=1.0,
            turbulence_enabled=True, turbulence_noise_strength=1.4, turbulence_noise_scale=2.8,
            turbulence_noise_speed=[0.25, 0.0, 0.2],
        ),
        gpu_particles=dict(amount=64, amount_high=64, amount_mid=36, amount_low=16, amount_mobile=36, lifetime=6.5, preprocess=4.0,
                           explosiveness=0.0, randomness=0.55, local_coords=False,
                           visibility_aabb=[-300, -20, -220, 600, 280, 440]),
    )


def make_grass_debris():
    cell = 8
    bits = []
    greens = [(70, 140, 55), (110, 168, 60), (50, 110, 48), (168, 150, 62), (96, 80, 48)]
    # grass blade fragments (vertical / diagonal)
    for i, rgb in enumerate(greens):
        im = np.zeros((cell, cell, 4), np.uint8)
        col = np.array([*rgb, 255], np.uint8)
        if i < 3:
            # short blade
            L = 3 + i
            x, y = 4, 2
            for k in range(L):
                px(im, x + (k // 3), y + k, col)
        else:
            # dirt / seed
            disk(im, 4, 4, 1.1 if i == 3 else 0.7, col)
            if i == 3:
                px(im, 4, 2, col)
        bits.append(C.hard_rgba(im))
    # extra angled blades
    extra = []
    for rgb in greens[:3]:
        extra += rot_frames(_leaf_shape(2, rgb, 8) if False else bits[0], 4, cell)[:4]
    # build 2 rows of 8
    row0 = bits + bits[:3]
    row0 = row0[:8]
    # diagonal variants
    row1 = []
    for i, b in enumerate(bits):
        row1.append(rot_frames(b, 8, cell)[1])  # 45°
    while len(row1) < 8:
        row1.append(row1[-1])
    sheet, fmap, hw = sheet_of([row0, row1[:8]], cell)
    return sheet, dict(
        id='grass_debris', zh='撥草碎屑', cell=cell, image='particles/grass_debris.png',
        frames_h=8, frames_v=2, pivot=[4, 6],
        atlas_frames=fmap,
        use='寵物播 part_grass 嗰下喺腳底／草叢位 one-shot 爆發；H1 菜畦／花盆互動同狩獵撥草共用。',
        material=dict(shading_mode='unshaded', blend_mode='mix', transparency='alpha_scissor',
                      alpha_scissor_threshold=0.5, billboard='particle',
                      particles_anim_h_frames=8, particles_anim_v_frames=2, particles_anim_loop=False,
                      texture_filter='Nearest', vertex_color_use_as_albedo=True),
        process_material=dict(
            emission_shape='sphere', emission_sphere_radius=6,
            emission_offset_hint='跟寵物 pivot 地面 (x, 4, z)；part_grass 第 2–3 幀觸發。',
            direction=[0, 1, 0], spread=75,
            initial_velocity_min=36, initial_velocity_max=88,
            gravity=[0, -90, 0],
            damping_min=2.0, damping_max=4.0,
            angular_velocity_min=-18, angular_velocity_max=18,
            scale_min=0.7, scale_max=1.4,
            color='#ffffff',
            color_ramp=[{'offset': 0, 'color': '#ffffffff'},
                        {'offset': 0.65, 'color': '#ffffffdd'},
                        {'offset': 1, 'color': '#ffffff00'}],
            anim_speed_min=0.0, anim_speed_max=0.0,
            hue_variation_min=-0.04, hue_variation_max=0.05,
        ),
        gpu_particles=dict(amount=14, amount_high=14, amount_mid=10, amount_low=6, amount_mobile=10, lifetime=0.55, preprocess=0.0,
                           explosiveness=1.0, randomness=0.6, one_shot=True, local_coords=False,
                           visibility_aabb=[-40, 0, -40, 80, 60, 80],
                           trigger='part_grass 開始後約 80–120ms 發射一次。'),
    )


def particles_index(items):
    return {
        'format': 'godot_fx1.particles/1',
        'engine': 'Godot 4',
        'units': '速度／重力／AABB 用 art unit（1 unit＝1 art px）。import_scale=0.01 時全部 ×0.01，scale_min/max 同 amount 唔改。',
        'alpha': '所有 sprite alpha 只有 0/255，透明 RGB=0；Filter Nearest，關 mipmap。',
        'nodes': '每款一個 GPUParticles3D＋ParticleProcessMaterial＋StandardMaterial3D（或 ShaderMaterial）。螢火 add＋emissive；其他 Alpha Scissor 0.5。',
        'quality': {
            'low': 'amount_low（開發基準；效果粒子仍喺同一 3D 場景播，只係數量少）',
            'mid': 'amount_mid（＝舊 amount_mobile）',
            'high': 'amount_high（＝amount）；落葉秋天用 amount_autumn',
        },
        'items': items,
    }


def main():
    root = root_of()
    fx = os.path.join(root, 'art-pet', 'fx')
    lutd = os.path.join(fx, 'luts')
    pard = os.path.join(fx, 'particles')
    os.makedirs(lutd, exist_ok=True)
    os.makedirs(pard, exist_ok=True)

    luts_meta = {'format': 'godot_fx1.lut/1', 'width': C.LUT_W, 'height': C.LUT_H, 'cube': C.LUT_SIZE,
                 'layout': 'horizontal strip, Godot official 33³ (Y-down G increases)', 'items': []}
    for name, fn in C.LUT_FNS.items():
        arr = C.build_lut(fn)
        path = os.path.join(lutd, f'lut_{name}.png')
        put(path, arr)
        luts_meta['items'].append(dict(id=name, zh=C.LUT_ZH[name], file=f'luts/lut_{name}.png',
                                       size=[C.LUT_W, C.LUT_H]))
    dump(os.path.join(lutd, 'luts.json'), luts_meta)

    env = environments()
    dump(os.path.join(fx, 'environments', 'environments.json'), env)
    dump(os.path.join(fx, 'godot_import.json'), godot_import())

    makers = [make_fireflies, make_leaves, make_petals, make_rain, make_snow, make_grass_debris]
    items = []
    for mk in makers:
        sheet, meta = mk()
        put(os.path.join(pard, os.path.basename(meta['image'])), sheet)
        # don't embed full atlas pixel map twice? keep frames for validator
        dump(os.path.join(pard, meta['id'] + '.json'), meta)
        items.append({k: meta[k] for k in meta if k != 'atlas_frames'})
        items[-1]['spec'] = f'particles/{meta["id"]}.json'
    dump(os.path.join(pard, 'particles.json'), particles_index(items))
    print('ok', fx)


if __name__ == '__main__':
    main()
