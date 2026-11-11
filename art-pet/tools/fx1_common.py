#!/usr/bin/env python3
"""Godot FX1 共用：33³ LUT（Godot 官方 strip 佈局）、DoF、像素硬 alpha。"""
import math
import numpy as np
from PIL import Image

LUT_SIZE = 33  # 官方 Godot 4 中性模板尺寸（奇數，含 0 同 1）
LUT_W, LUT_H = LUT_SIZE * LUT_SIZE, LUT_SIZE  # 1089×33

REC709 = np.array([0.2126, 0.7152, 0.0722], dtype=np.float64)


def luma(rgb):
    """rgb 最後一維係 3，線性權重（0–1 或 0–255 都得，跟輸入尺度）。"""
    return np.tensordot(np.asarray(rgb, dtype=np.float64), REC709, axes=([-1], [0]))


def hard_rgba(arr):
    """alpha 只得 0/255；透明 RGB=0。"""
    a = arr[..., 3]
    out = arr.copy()
    out[..., 3] = np.where(a >= 128, 255, 0).astype(np.uint8)
    out[out[..., 3] == 0] = 0
    return out


def save_png(path, arr, *, nearest=True):
    Image.fromarray(arr).save(path)


def pot(n):
    return n > 0 and (n & (n - 1)) == 0


# ---------- LUT：官方佈局（docs environment_adjustments_3d_lut_template）----------
# strip 1089×33：33 個 33×33 格由左到右＝B 0→1。
# 格內 X 左→右＝R 0→1；Y 上→下＝G 0→1（PNG y=0 係 G=0）。
def lut_coords():
    s = LUT_SIZE
    xs = np.arange(LUT_W)
    ys = np.arange(LUT_H)
    x, y = np.meshgrid(xs, ys)
    sl = x // s
    lx = x % s
    r = lx / (s - 1)
    g = y / (s - 1)
    b = sl / (s - 1)
    return np.stack([r, g, b], axis=-1)


def identity_lut():
    rgb = lut_coords()
    return (np.clip(rgb, 0, 1) * 255 + 0.5).astype(np.uint8)


def build_lut(fn):
    """fn(rgb_f64 HxWx3 in 0–1) → rgb 0–1。回 1089×33 uint8 RGB。"""
    src = lut_coords()
    out = fn(src)
    return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)


def apply_lut(img_rgb_u8, lut_u8, *, linear_interp=True):
    """跟 Godot Texture3D 取樣：R／G 格內，B 跨 slice 線性插。img HxWx3 uint8。"""
    s = LUT_SIZE
    img = np.asarray(img_rgb_u8, dtype=np.float64) / 255.0
    lut = np.asarray(lut_u8, dtype=np.float64) / 255.0
    r, g, b = img[..., 0], img[..., 1], img[..., 2]
    # 索引 0..s-1
    rf, gf, bf = r * (s - 1), g * (s - 1), b * (s - 1)
    r0 = np.clip(np.floor(rf).astype(int), 0, s - 1)
    g0 = np.clip(np.floor(gf).astype(int), 0, s - 1)
    b0 = np.clip(np.floor(bf).astype(int), 0, s - 1)
    r1 = np.clip(r0 + 1, 0, s - 1)
    g1 = np.clip(g0 + 1, 0, s - 1)
    b1 = np.clip(b0 + 1, 0, s - 1)
    wr, wg, wb = rf - r0, gf - g0, bf - b0

    def at(ri, gi, bi):
        return lut[gi, bi * s + ri]

    c000 = at(r0, g0, b0); c100 = at(r1, g0, b0)
    c010 = at(r0, g1, b0); c110 = at(r1, g1, b0)
    c001 = at(r0, g0, b1); c101 = at(r1, g0, b1)
    c011 = at(r0, g1, b1); c111 = at(r1, g1, b1)
    if not linear_interp:
        return (c000 * 255 + 0.5).astype(np.uint8)
    c00 = c000 * (1 - wr)[..., None] + c100 * wr[..., None]
    c01 = c001 * (1 - wr)[..., None] + c101 * wr[..., None]
    c10 = c010 * (1 - wr)[..., None] + c110 * wr[..., None]
    c11 = c011 * (1 - wr)[..., None] + c111 * wr[..., None]
    c0 = c00 * (1 - wg)[..., None] + c10 * wg[..., None]
    c1 = c01 * (1 - wg)[..., None] + c11 * wg[..., None]
    out = c0 * (1 - wb)[..., None] + c1 * wb[..., None]
    return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a + 1e-12), 0, 1)
    return t * t * (3 - 2 * t)


def lerp(a, b, t):
    return a + (b - a) * t


def sat(x):
    return np.clip(x, 0, 1)


def apply_s_curve(L, contrast):
    """contrast>1 加強；中灰 0.5 不動。"""
    x = np.clip(L, 0, 1)
    # 以 0.5 為中心嘅冪對比
    return sat((x - 0.5) * contrast + 0.5)


def grade_color(rgb, *, lift, gamma, gain, sat_mul=1.0, contrast=1.0, tint_sh=None, tint_hi=None):
    """簡單 ASC CDL＋對比＋陰影／高光染色。rgb 0–1。"""
    x = np.clip(rgb, 0, 1)
    lift = np.asarray(lift, dtype=np.float64)
    gamma = np.asarray(gamma, dtype=np.float64)
    gain = np.asarray(gain, dtype=np.float64)
    y = sat(gain * (x + lift * (1 - x)))
    y = sat(y ** (1.0 / np.maximum(gamma, 1e-6)))
    L = luma(y)[..., None]
    if contrast != 1.0:
        y = sat((y - 0.5) * contrast + 0.5)
        L = luma(y)[..., None]
    if sat_mul != 1.0:
        y = sat(L + (y - L) * sat_mul)
        L = luma(y)[..., None]
    if tint_sh is not None:
        w = (1 - smoothstep(0.15, 0.45, L[..., 0]))[..., None]
        y = sat(y * (1 - w) + y * np.asarray(tint_sh) * w)
    if tint_hi is not None:
        w = smoothstep(0.55, 0.9, L[..., 0])[..., None]
        y = sat(y * (1 - w) + y * np.asarray(tint_hi) * w)
    return sat(y)


# ---------- 七套調色 ----------
def _lut_day(rgb):
    # 晨光暖調：接近 H1 穩陣 GIF，只稍為提暖同輕對比
    return grade_color(
        rgb, lift=[0.012, 0.008, 0.0], gamma=[1.0, 1.0, 1.02],
        gain=[1.04, 1.015, 0.96], sat_mul=1.06, contrast=1.06,
        tint_hi=[1.04, 1.01, 0.94],
    )


def _lut_dusk(rgb):
    y = grade_color(
        rgb, lift=[0.02, 0.0, 0.03], gamma=[0.95, 1.0, 1.06],
        gain=[1.08, 0.92, 0.78], sat_mul=1.12, contrast=1.12,
        tint_sh=[0.92, 0.85, 1.12], tint_hi=[1.14, 0.95, 0.72],
    )
    # 整體稍暗（黃昏）
    return sat(y * 0.88 + np.array([0.04, 0.015, 0.01]) * (1 - luma(y)[..., None] * 0.3))


def _lut_night(rgb):
    """色相分流：暖綠／有彩地面中灰（約 55）壓到約 26；近中性或偏藍天空保持約 55；
    燈暖高光保留。已暗地面（約 22）唔再壓。近中性鄰格亦保持，避免 LUT 插值把天空拉暗。"""
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    L = luma(rgb)
    chroma = np.maximum(np.maximum(r, g), b) - np.minimum(np.minimum(r, g), b)
    sky = sat((b - g) * 2.8 + (b - r) * 1.2)
    near_neutral = 1 - smoothstep(0.018, 0.050, chroma)
    mid = smoothstep(0.13, 0.17, L) * (1 - smoothstep(0.32, 0.50, L))
    sky = sat(sky + near_neutral * mid)
    lamp = sat((r - b) * 2.2) * smoothstep(0.38, 0.75, L)
    # 暖綠／草綠（引擎過亮地面 chroma≈0.09、G>B）
    groundish = sat((g - b) * 8.0 + (g - r) * 2.0) * (1 - sky) * (1 - lamp)
    # 其他有彩（木、泥）中度壓；近中性唔壓
    generic = sat(smoothstep(0.05, 0.12, chroma) * (1 - groundish) * (1 - sky) * (1 - lamp))

    def remap(L, ys):
        xp = np.array([0.0, 0.05, 0.088, 0.14, 0.216, 0.30, 0.45, 0.65, 1.0])
        return np.interp(L, xp, np.array(ys, dtype=np.float64))

    Lg = remap(L, [0.0, 0.045, 0.086, 0.098, 0.102, 0.14, 0.24, 0.50, 0.85])  # 55→26
    Ln = remap(L, [0.0, 0.048, 0.086, 0.12, 0.14, 0.18, 0.30, 0.55, 0.90])   # 中度
    ground_col = sat(rgb * (Lg / np.maximum(L, 1e-5))[..., None] * np.array([0.90, 0.97, 1.08]))
    generic_col = sat(rgb * (Ln / np.maximum(L, 1e-5))[..., None] * np.array([0.88, 0.92, 1.06]))
    # 天空／近中性：幾乎原色，L 輕輕拉向 55
    Ls = lerp(L, 0.216, 0.20)
    sky_col = sat(rgb * (Ls / np.maximum(L, 1e-5))[..., None] * np.array([0.97, 0.99, 1.04]))
    lamp_col = sat(rgb * np.array([1.02, 0.99, 0.90]) * 1.02)
    # 其餘（已好暗、或未分類）跟輕微壓
    rest = sat(rgb * (remap(L, [0.0, 0.048, 0.086, 0.11, 0.13, 0.18, 0.32, 0.58, 0.92]) / np.maximum(L, 1e-5))[..., None])

    w_s = sat(sky)
    w_l = sat(lamp)
    w_g = sat(groundish)
    w_n = sat(generic)
    acc = w_s + w_l + w_g + w_n
    w_r = sat(1 - acc)
    s = np.maximum(acc + w_r, 1e-6)
    out = (sky_col * w_s[..., None] + lamp_col * w_l[..., None]
           + ground_col * w_g[..., None] + generic_col * w_n[..., None]
           + rest * w_r[..., None]) / s[..., None]
    return sat(out)

def _lut_spring(rgb):
    y = grade_color(
        rgb, lift=[0.02, 0.012, 0.018], gamma=[1.02, 0.98, 1.02],
        gain=[1.02, 1.05, 0.98], sat_mul=1.08, contrast=1.04,
        tint_hi=[1.06, 1.02, 1.04],
    )
    # 綠偏嫩黃綠，暗位略粉
    r, g, b = y[..., 0], y[..., 1], y[..., 2]
    green = sat((g - b) * 1.6)
    y = y.copy()
    y[..., 0] = sat(r + 0.03 * green)
    y[..., 1] = sat(g + 0.05 * green)
    y[..., 2] = sat(b - 0.03 * green)
    return y


def _lut_summer(rgb):
    return grade_color(
        rgb, lift=[0.0, 0.01, 0.0], gamma=[0.98, 0.96, 1.02],
        gain=[1.06, 1.08, 0.92], sat_mul=1.16, contrast=1.10,
        tint_hi=[1.08, 1.04, 0.88],
    )


def _lut_autumn(rgb):
    y = grade_color(
        rgb, lift=[0.02, 0.0, 0.0], gamma=[0.96, 1.04, 1.08],
        gain=[1.10, 0.92, 0.78], sat_mul=1.10, contrast=1.10,
        tint_sh=[1.02, 0.88, 0.80], tint_hi=[1.16, 0.95, 0.70],
    )
    # 綠轉金琥珀
    r, g, b = y[..., 0], y[..., 1], y[..., 2]
    green = sat((g - b) * 1.8)
    y = y.copy()
    y[..., 0] = sat(r + 0.10 * green)
    y[..., 1] = sat(g - 0.04 * green)
    y[..., 2] = sat(b - 0.10 * green)
    return y


def _lut_winter(rgb):
    y = grade_color(
        rgb, lift=[0.01, 0.02, 0.04], gamma=[1.04, 1.02, 0.96],
        gain=[0.92, 0.96, 1.08], sat_mul=0.78, contrast=1.06,
        tint_sh=[0.85, 0.90, 1.12], tint_hi=[0.96, 1.00, 1.06],
    )
    # 綠去飽和偏灰藍
    L = luma(y)[..., None]
    r, g, b = y[..., 0], y[..., 1], y[..., 2]
    green = sat((g - b) * 1.5)[..., None]
    y = lerp(y, L + (y - L) * 0.45, green)
    return sat(y)


LUT_FNS = {
    'identity': lambda rgb: rgb,
    'day': _lut_day,
    'dusk': _lut_dusk,
    'night': _lut_night,
    'spring': _lut_spring,
    'summer': _lut_summer,
    'autumn': _lut_autumn,
    'winter': _lut_winter,
}

LUT_ZH = {
    'identity': '中性（匯入驗證，畫面應不變）',
    'day': '日／晨光暖調',
    'dusk': '黃昏',
    'night': '夜',
    'spring': '春',
    'summer': '夏',
    'autumn': '秋',
    'winter': '冬',
}


# ---------- DoF（對齊 CameraAttributesPractical）----------
# amount 0–1；near：depth≤near_distance 全朦，到 near+transition 清晰；
# far：depth≤far_distance 清晰，到 far+transition 全朦。
DEFAULT_DOF = dict(
    dof_blur_near_enabled=True,
    dof_blur_near_distance=400.0,
    dof_blur_near_transition=110.0,
    dof_blur_far_enabled=True,
    dof_blur_far_distance=720.0,
    dof_blur_far_transition=380.0,
    dof_blur_amount=0.16,
)


def coc_factor(depth, dof=None):
    d = DEFAULT_DOF if dof is None else dof
    depth = np.asarray(depth, dtype=np.float64)
    near = np.zeros_like(depth)
    far = np.zeros_like(depth)
    if d.get('dof_blur_near_enabled', True):
        nd, nt = float(d['dof_blur_near_distance']), max(float(d['dof_blur_near_transition']), 1e-6)
        near = sat((nd + nt - depth) / nt)
    if d.get('dof_blur_far_enabled', True):
        fd, ft = float(d['dof_blur_far_distance']), max(float(d['dof_blur_far_transition']), 1e-6)
        far = sat((depth - fd) / ft)
    return np.maximum(near, far) * float(d.get('dof_blur_amount', 0.16))


def apply_dof(rgb_u8, depth, dof=None, max_radius=5.0):
    """分層 box blur（像素風、唔好過朦）。depth 同 rgb 同尺寸；inf／nan 當好遠。"""
    img = np.asarray(rgb_u8, dtype=np.float64)
    z = np.asarray(depth, dtype=np.float64)
    z = np.where(np.isfinite(z), z, 1e5)
    coc = coc_factor(z, dof)
    # amount 0.16 → 大約 0–5 px（600×400 預覽）
    rad = coc / max(float((dof or DEFAULT_DOF).get('dof_blur_amount', 0.16)), 1e-6) * max_radius
    out = img.copy()
    # 3 層：r≈1.5、3、5
    layers = [(1.5, (rad > 0.4) & (rad <= 2.2)),
              (3.0, (rad > 2.2) & (rad <= 3.8)),
              (5.0, rad > 3.8)]
    for r, mask in layers:
        if not mask.any():
            continue
        k = int(round(r * 2 + 1))
        blur = _box_blur(img, k)
        out[mask] = blur[mask]
    return np.clip(out + 0.5, 0, 255).astype(np.uint8)


def _box_blur(img, k):
    k = max(int(k), 1)
    if k % 2 == 0:
        k += 1
    pad = k // 2
    x = np.pad(img, ((pad, pad), (pad, pad), (0, 0)), mode='edge')
    c = np.cumsum(np.cumsum(x, axis=0), axis=1)
    # integral inclusive
    c = np.pad(c, ((1, 0), (1, 0), (0, 0)), mode='constant')
    h, w = img.shape[:2]
    s = (c[k:k + h, k:k + w] - c[0:h, k:k + w] - c[k:k + h, 0:w] + c[0:h, 0:w])
    return s / float(k * k)
