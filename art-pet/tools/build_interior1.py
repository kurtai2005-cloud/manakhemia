#!/usr/bin/env python3
"""build_interior1.py — 微光小圃 H1 室內美術（程序化 Pillow／numpy，冇 AI 圖）。

V3-A HD-2D，色盤同 texel 跟 garden3d/H1 小屋（cottage.png 21 色）。
假設房間（等遊程 GIF 先鎖定）：闊 160 × 深 128 × 天花 120 units
（1 unit＝1 art px＝1 世界單位）。貼圖可平鋪，之後可以換尺寸。
"""
from __future__ import annotations
import json, math, os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
# 預設寫入 staging 室內目錄
ROOT = os.environ.get(
    "INTERIOR1_OUT",
    os.path.abspath(os.path.join(HERE, "..", "..", "art", "garden3d", "H1", "interior")),
)
if not os.path.isdir(os.path.dirname(ROOT)):
    ROOT = "/workspace/interior1-staging/art/garden3d/H1/interior"

# ----- 假設房間（可換）-----
ROOM_W, ROOM_D, ROOM_H = 160, 128, 120
WALL_T = 3
DOOR_W, DOOR_H = 56, 96          # 唔跟屋外均勻 ×2 嘅 32×96；加闊到 56 先過到 L 寵物（可見闊 44）
WIN_W, WIN_H = 48, 48
WIN_SILL = 52                    # 窗台離地
TILE = 64
TEXEL = 1                        # 1 px / unit（同 H1 1x 美術）
# L 可見高 54 u 當 0.80 m → 1 u = 0.014815 m
M_PER_U = 0.80 / 54.0

# ----- H1 小屋實色（cottage.png 21 色，已 graded）-----
PAL = {
    "WALL":  ["#955b30", "#d38540", "#f4ae5d", "#deb474", "#fcfae4"],
    "WOOD":  ["#371a14", "#583120", "#694435", "#955b30", "#b59475", "#deb474"],
    "WIN":   ["#241d2b", "#5c4845", "#a1c5cc", "#fcfae4"],
    "STONE": ["#371a14", "#5c4845", "#694435", "#b59475"],
    "IVY":   ["#24391a", "#6c9536", "#aec04c"],
    "FLOWER":["#591d1b", "#b55d5a", "#d45b39", "#fcfae4"],
    "GLASS_E": ["#d45b39", "#ffc870", "#ffe9a0", "#fcfae4"],
}
# 額外：#ffc870 / #ffe9a0 係 H1 窗／燈籠發光色，唔喺 albedo 小屋圖，只用喺 emissive
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], float) / 16.0


def hx(c: str) -> np.ndarray:
    c = c.lstrip("#")
    return np.array([int(c[i:i + 2], 16) for i in (0, 2, 4)], np.uint8)


def up3(a: np.ndarray) -> np.ndarray:
    return np.repeat(np.repeat(a, 3, 0), 3, 1)


def save(a: np.ndarray, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    Image.fromarray(a).save(path, optimize=True)


def shade(h: int, w: int, colors: list[str], f, dither: float = 0.3, alpha=None) -> np.ndarray:
    ramp = np.stack([hx(c) for c in colors], 0)
    n = len(colors)
    Y, X = np.mgrid[0:h, 0:w]
    bay = BAYER[Y % 4, X % 4]
    if not isinstance(f, np.ndarray):
        f = np.full((h, w), float(f))
    q = np.clip(np.floor(f * n + (bay - 0.5) * dither * 2), 0, n - 1).astype(int)
    out = np.zeros((h, w, 4), np.uint8)
    out[..., :3] = ramp[q]
    if alpha is None:
        out[..., 3] = 255
    else:
        a = (alpha > 0.5) if alpha.dtype != bool else alpha
        out[..., 3] = np.where(a, 255, 0)
        out[~a, :3] = 0
    return out


def put(dst: np.ndarray, mask: np.ndarray, colors: list[str], f, dither: float = 0.3) -> None:
    h, w = dst.shape[:2]
    tmp = shade(h, w, colors, f, dither)
    m = mask.astype(bool) if mask.dtype != bool else mask
    dst[m] = tmp[m]


def floor_tile(n: int = TILE, seed: int = 7) -> np.ndarray:
    """可平鋪木地板：沿 z（圖向下）走嘅木板，闊 8 px。"""
    rng = np.random.default_rng(seed)
    h = w = n
    Y, X = np.mgrid[0:h, 0:w]
    pitch = 8
    band = (X % (n)) // pitch  # wraps because n % 8 == 0
    # 每條板一個色調；用 X 週期，令左右接得上
    nband = n // pitch
    tone = rng.random(nband) * 0.18 - 0.08
    # 木紋：沿板方向（Y）短線，X 週期
    grain = rng.random((h, nband)) < 0.04
    gx = X // pitch
    gy = Y
    g = grain[gy, gx % nband]
    seam = (X % pitch) == (pitch - 1)
    f = 0.55 + tone[gx % nband] - 0.45 * seam - 0.12 * ((X % pitch) == (pitch - 2))
    f = f - 0.10 * g * (~seam)
    # 節疤（稀疏，避開接縫）
    knots = rng.random((h, w)) < 0.003
    f = np.clip(f - 0.2 * knots * (~seam), 0, 1)
    return shade(h, w, PAL["WOOD"], f, 0.28)


def wall_tile(n: int = TILE, seed: int = 1, pitch: int = 8) -> np.ndarray:
    """可平鋪橫木板牆（同小屋 planks，Y 同 X 都週期）。"""
    rng = np.random.default_rng(seed)
    h = w = n
    Y, X = np.mgrid[0:h, 0:w]
    ya = (h - 1 - Y) % h
    nband = n // pitch
    tone = rng.random(nband) * 0.16 - 0.08
    band = (ya // pitch) % nband
    grain = rng.random((nband, w)) < 0.012
    g = grain[band, X]
    f = 0.72 + tone[band] - 0.55 * ((ya % pitch) == pitch - 1) - 0.1 * g
    f = f - 0.12 * ((ya % pitch) == pitch - 2)
    return shade(h, w, PAL["WALL"], np.clip(f, 0, 1), 0.3)


def wall_unique(h: int, w: int, seed: int, hole=None, baseboard: bool = True) -> np.ndarray:
    """獨幅牆（可開洞）。用 tile 舖，再加踢腳石同邊木。"""
    tile = wall_tile(TILE, seed)
    yy, xx = np.mgrid[0:h, 0:w]
    out = tile[yy % TILE, xx % TILE].copy()
    if hole:
        x0, x1, y0, y1 = hole  # y 由地起
        r0, r1 = h - y1, h - y0
        out[r0:r1, x0:x1] = 0
    if baseboard:
        # 近地 3 px 石基，同小屋 foundation
        k = np.zeros((h, w), bool)
        k[h - 3:h, :] = out[h - 3:h, :, 3] > 0
        rng = np.random.default_rng(3 + seed)
        f = 0.5 + 0.25 * rng.random((h, w)) - 0.3 * (((xx + 3 * ((yy - h) % 2)) % 7) == 0)
        f = f - 0.2 * (yy == h - 3)
        put(out, k, PAL["STONE"], np.clip(f, 0, 1), 0.3)
        # 左右封邊木
        edge = np.zeros((h, w), bool)
        edge[:, :2] = out[:, :2, 3] > 0
        edge[:, w - 2:] = out[:, w - 2:, 3] > 0
        put(out, edge, PAL["WOOD"], 0.3, 0)
    return out


def window_tex(fw: int = 64, fh: int = 64) -> tuple[np.ndarray, np.ndarray]:
    """窗框＋玻璃（獨幅）。開孔 48×48，外框 8。"""
    a = np.zeros((fh, fw, 4), np.uint8)
    # 置中
    x0, y0 = (fw - WIN_W) // 2, (fh - WIN_H) // 2
    x1, y1 = x0 + WIN_W, y0 + WIN_H
    # 外框 4 px
    frame = np.zeros((fh, fw), bool)
    frame[y0 - 4:y1 + 4, x0 - 4:x1 + 4] = True
    put(a, frame, PAL["WOOD"], 0.72, 0)
    put(a, np.zeros((fh, fw), bool) | _rect(fh, fw, x0 - 4, x1 + 4, y0 - 4, y0 - 2), PAL["WOOD"], 0.9, 0)
    # 窗台
    put(a, _rect(fh, fw, x0 - 5, x1 + 5, y1 + 1, y1 + 4), PAL["WOOD"], 0.5, 0)
    # 玻璃
    Y, X = np.mgrid[0:fh, 0:fw]
    gl = _rect(fh, fw, x0, x1, y0, y1)
    gf = np.clip(0.25 + 0.75 * (((X - x0) + (Y - y0)) > WIN_W * 0.9) + 0.2 * (((X - x0) - (Y - y0)) % 9 == 0), 0, 1)
    put(a, gl, PAL["WIN"], gf, 0)
    # 窗櫺十字
    put(a, _rect(fh, fw, (x0 + x1) // 2, (x0 + x1) // 2 + 1, y0, y1), PAL["WOOD"], 0.45, 0)
    put(a, _rect(fh, fw, x0, x1, (y0 + y1) // 2, (y0 + y1) // 2 + 1), PAL["WOOD"], 0.45, 0)
    # emissive＝玻璃（夜間暖黃）
    em = np.zeros_like(a)
    # 窗櫺唔發光
    mull = _rect(fh, fw, (x0 + x1) // 2, (x0 + x1) // 2 + 1, y0, y1) | _rect(fh, fw, x0, x1, (y0 + y1) // 2, (y0 + y1) // 2 + 1)
    glass = gl & ~mull
    em[glass, :3] = hx("#ffc870")
    # 高光一角更亮
    hi = glass & ((((X - x0) + (Y - y0)) > WIN_W * 0.9))
    em[hi, :3] = hx("#ffe9a0")
    em[glass, 3] = 255
    return a, em


def _rect(h, w, x0, x1, y0, y1):
    k = np.zeros((h, w), bool)
    k[max(int(y0), 0):max(int(y1), 0), max(int(x0), 0):max(int(x1), 0)] = True
    return k


def door_tex(fw: int = 128, fh: int = 128) -> np.ndarray:
    """室內見到嘅門（入屋門嘅內面）：直木板門扇＋框＋門栓。門洞 56×96。"""
    a = np.zeros((fh, fw, 4), np.uint8)
    # 門扇置底中（腳落地）
    x0 = (fw - DOOR_W) // 2
    y1 = fh - 0
    y0 = y1 - DOOR_H
    x1 = x0 + DOOR_W
    # 外框（四周 5 px，底貼地）
    fr = _rect(fh, fw, x0 - 5, x1 + 5, y0 - 5, y1)
    put(a, fr, PAL["WOOD"], 0.28, 0)
    put(a, _rect(fh, fw, x0 - 5, x1 + 5, y0 - 5, y0 - 2), PAL["WOOD"], 0.15, 0)
    # 門扇直板
    leaf = _rect(fh, fw, x0, x1, y0, y1)
    Y, X = np.mgrid[0:fh, 0:fw]
    pitch = 8
    band = ((X - x0) // pitch)
    rng = np.random.default_rng(11)
    tone = rng.random(16) * 0.18 - 0.06
    f = np.full((fh, fw), 0.55)
    f = 0.55 + tone[np.clip(band, 0, 15)] - 0.4 * (((X - x0) % pitch) == pitch - 1)
    f = f - 0.08 * ((Y % 11) == 0)
    put(a, leaf, PAL["WOOD"], np.clip(f, 0, 1), 0.25)
    # 橫檔兩條
    put(a, _rect(fh, fw, x0 + 2, x1 - 2, y0 + 18, y0 + 22), PAL["WOOD"], 0.25, 0)
    put(a, _rect(fh, fw, x0 + 2, x1 - 2, y0 + 58, y0 + 62), PAL["WOOD"], 0.25, 0)
    # 門栓（右，室內）
    hx0, hy0 = x1 - 10, y0 + 44
    put(a, _rect(fh, fw, hx0, hx0 + 7, hy0, hy0 + 4), PAL["STONE"], 0.7, 0)
    put(a, _rect(fh, fw, hx0 + 5, hx0 + 8, hy0 - 1, hy0 + 5), PAL["STONE"], 0.45, 0)
    return a


def pad_pow2(a: np.ndarray) -> tuple[np.ndarray, list[int]]:
    h, w = a.shape[:2]
    ph = 1 << int(math.ceil(math.log2(max(h, 1))))
    pw = 1 << int(math.ceil(math.log2(max(w, 1))))
    if ph == h and pw == w:
        return a, [w, h]
    out = np.zeros((ph, pw, 4), np.uint8)
    out[:h, :w] = a
    return out, [pw, ph]


# ----- mesh 幾何 -----
def _flat(arr):
    out = []
    for v in arr:
        out.extend([float(round(x, 4)) for x in v])
    return out


def mesh_plane(axis: str, w: float, h: float, origin, normal, uv_scale=TILE):
    """矩形一行。origin＝左下角世界座標；w 沿第一橫軸，h 沿第二。
    axis: 'xz' floor (w=+X, h=+Z), 'xy' wall facing +Z (w=+X, h=+Y),
          'zy' wall facing +X (w=+Z, h=+Y), 'zy-' facing -X.
    UV：1 tile = uv_scale units，V-up。
    """
    o = np.array(origin, float)
    if axis == "xz":
        uax, vax = np.array([w, 0, 0.]), np.array([0, 0, h])
    elif axis == "xy":
        uax, vax = np.array([w, 0, 0.]), np.array([0, h, 0.])
    elif axis == "zy":
        uax, vax = np.array([0, 0, w]), np.array([0, h, 0.])
    elif axis == "zy-":
        uax, vax = np.array([0, 0, -w]), np.array([0, h, 0.])
        w = w  # width along -Z for left wall from back to front? we'll place carefully
    else:
        raise ValueError(axis)
    p0 = o
    p1 = o + uax
    p2 = o + uax + vax
    p3 = o + vax
    n = np.array(normal, float)
    n = n / (np.linalg.norm(n) + 1e-9)
    uw, vh = abs(w) / uv_scale, abs(h) / uv_scale if axis == "xz" else abs(h) / uv_scale
    # for walls h is height
    if axis == "xz":
        uvs = [(0, 1), (uw, 1), (uw, 1 - vh), (0, 1 - vh)]  # V-up, v=1 at -Z? origin is -X-Z corner, +Z is forward
        # floor: u along +X, v along +Z (v increases toward camera). V-up means v=0 at "top" of image = -Z if we want
        # Use u=+X, v=+Z with V-up so v=0 is far (-Z) if we flip: v_img = 1 at origin z, 0 at +z? Keep simple: u=x, v=z, V-up flip in engine.
        uvs = [(0, 0), (abs(w) / uv_scale, 0), (abs(w) / uv_scale, abs(h) / uv_scale), (0, abs(h) / uv_scale)]
    else:
        uvs = [(0, 0), (abs(w) / uv_scale, 0), (abs(w) / uv_scale, abs(h) / uv_scale), (0, abs(h) / uv_scale)]
    pos = [p0, p1, p2, p3]
    nrm = [n, n, n, n]
    # CCW from normal side
    idx = [0, 1, 2, 0, 2, 3]
    return pos, nrm, uvs, idx


def append_quad(bufs, pos, nrm, uvs, indices, both_sides=True):
    base = len(bufs["pos"])
    bufs["pos"].extend(pos)
    bufs["nrm"].extend(nrm)
    bufs["uv"].extend(uvs)
    bufs["idx"].extend([base + i for i in indices])
    if both_sides:
        # 反向背面三角（同 garden3d 卡片），CULL_BACK 都睇到
        back = []
        for i in range(0, len(indices), 3):
            back.extend([indices[i], indices[i+2], indices[i+1]])
        bufs["idx"].extend([base + i for i in back])


def write_mesh(oid, zh, bufs, texture, tex_size, footprint, extra=None, emissive=None):
    pos = np.array(bufs["pos"], float)
    bounds = {"min": [float(round(x, 3)) for x in pos.min(0)], "max": [float(round(x, 3)) for x in pos.max(0)]}
    doc = {
        "format": "garden3d.mesh/2",
        "id": oid,
        "zh": zh,
        "units": "1 unit＝1x art px；Y 上；原點＝物件底中（局部座標）；+Z 向鏡頭。放置用 objects.json 嘅 x／z／y＋yawDeg",
        "texture": f"meshes/{os.path.basename(texture)}",
        "texture3x": f"meshes/{os.path.basename(texture).replace('.png', '@3x.png')}",
        "textureSize": tex_size,
        "alphaTest": 0.5,
        "doubleSided": False,
        "material": {
            "filter": "nearest",
            "mipmap": False,
            "lit": True,
            "sRGB": True,
            "bakedLight": False,
        },
        "positions": _flat(bufs["pos"]),
        "normals": _flat(bufs["nrm"]),
        "uvs": _flat(bufs["uv"]),
        "indices": [int(i) for i in bufs["idx"]],
        "bounds": bounds,
        "footprint": footprint,
        "castShadow": True,
        "receiveShadow": True,
        "vertexCount": len(bufs["pos"]),
        "triangleCount": len(bufs["idx"]) // 3,
    }
    if emissive:
        doc["emissive"] = f"meshes/{os.path.basename(emissive)}"
        doc["emissive3x"] = f"meshes/{os.path.basename(emissive).replace('.png', '@3x.png')}"
    if extra:
        doc.update(extra)
    path = os.path.join(ROOT, "meshes", f"{oid}.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump(doc, open(path, "w"), ensure_ascii=False, indent=1)
    return doc


def build():
    os.makedirs(os.path.join(ROOT, "meshes"), exist_ok=True)
    os.makedirs(os.path.join(ROOT, "tiles"), exist_ok=True)

    ft = floor_tile()
    save(ft, os.path.join(ROOT, "tiles", "floor_tile.png"))
    save(up3(ft), os.path.join(ROOT, "tiles", "floor_tile@3x.png"))
    wt = wall_tile()
    save(wt, os.path.join(ROOT, "tiles", "wall_tile.png"))
    save(up3(wt), os.path.join(ROOT, "tiles", "wall_tile@3x.png"))

    # --- 後牆：160×120，開窗洞 ---
    # 窗喺後牆中央偏上：sill 52，高 48 → y 52–100。牆座標 x 0..160（由左）
    win_x0 = (ROOM_W - WIN_W) // 2
    back = wall_unique(ROOM_H, ROOM_W, seed=2, hole=(win_x0, win_x0 + WIN_W, WIN_SILL, WIN_SILL + WIN_H))
    # 窗洞加一圈內框木（洞邊 2 px 已經係洞，框畫喺洞外）
    back_p, back_sz = pad_pow2(back)
    save(back_p, os.path.join(ROOT, "meshes", "wall_back.png"))
    save(up3(back_p), os.path.join(ROOT, "meshes", "wall_back@3x.png"))

    # 側牆：深 128 × 高 120，冇洞
    side = wall_unique(ROOM_H, ROOM_D, seed=4, hole=None)
    side_p, side_sz = pad_pow2(side)
    save(side_p, os.path.join(ROOT, "meshes", "wall_side.png"))
    save(up3(side_p), os.path.join(ROOT, "meshes", "wall_side@3x.png"))

    # 地板獨幅（用 tile 舖 160×128，方便預覽；引擎亦可改用 tiles/ 重複）
    fy, fx = np.mgrid[0:ROOM_D, 0:ROOM_W]
    floor_img = ft[fy % TILE, fx % TILE].copy()
    floor_p, floor_sz = pad_pow2(floor_img)
    save(floor_p, os.path.join(ROOT, "meshes", "floor.png"))
    save(up3(floor_p), os.path.join(ROOT, "meshes", "floor@3x.png"))

    win, win_e = window_tex(64, 64)
    save(win, os.path.join(ROOT, "meshes", "window.png"))
    save(up3(win), os.path.join(ROOT, "meshes", "window@3x.png"))
    save(win_e, os.path.join(ROOT, "meshes", "window_emissive.png"))
    save(up3(win_e), os.path.join(ROOT, "meshes", "window_emissive@3x.png"))

    door = door_tex(128, 128)
    door_p, door_sz = pad_pow2(door)
    save(door_p, os.path.join(ROOT, "meshes", "door.png"))
    save(up3(door_p), os.path.join(ROOT, "meshes", "door@3x.png"))

    # ----- 局部原點＝房間底中 (0,0,0)；+Z 向鏡頭／門口 -----
    hw, hd = ROOM_W * 0.5, ROOM_D * 0.5
    # 地板
    buf = {"pos": [], "nrm": [], "uv": [], "idx": []}
    pos, nrm, uvs, idx = mesh_plane("xz", ROOM_W, ROOM_D, origin=(-hw, 0, -hd), normal=(0, 1, 0), uv_scale=TILE)
    # UV 用獨幅 floor.png（pad 後 256×128? 160x128 → 256x128)
    # 改：u = x_local / tex_w, 但獨幅實際內容 160×128 放喺 atlas 左上。
    # V-up：圖頂＝遠（-Z）。內容在 atlas [0:128, 0:160] if pad to 256x128? pad_pow2: h=128,w=160 → 128,256.
    tw, th = floor_sz
    # remap uv to content
    uvs = [(0, 1 - 0), (ROOM_W / tw, 1 - 0), (ROOM_W / tw, 1 - ROOM_D / th), (0, 1 - ROOM_D / th)]
    # wait V-up: v=1 is top of image = far = -Z = first row of floor_img which is z=-hd.
    # p0 = (-hw,0,-hd) should be u=0, v=1 (top-left of content)
    # p1 = (hw,0,-hd) u=ROOM_W/tw, v=1
    # p2 = (hw,0,hd) u=ROOM_W/tw, v=1-ROOM_D/th
    # p3 = (-hw,0,hd) u=0, v=1-ROOM_D/th
    uvs = [
        (0, 1.0),
        (ROOM_W / tw, 1.0),
        (ROOM_W / tw, 1.0 - ROOM_D / th),
        (0, 1.0 - ROOM_D / th),
    ]
    append_quad(buf, pos, nrm, uvs, idx)
    write_mesh(
        "floor", "室內地板（可平鋪；獨幅由 64 木板 tile 舖）",
        buf, "floor.png", floor_sz,
        {"rect": {"x": [-hw, hw], "z": [-hd, hd]}, "pad": 0},
    )

    # 後牆：z = -hd，面向 +Z，x -hw..hw, y 0..H
    buf = {"pos": [], "nrm": [], "uv": [], "idx": []}
    tw, th = back_sz  # pad of 160x120
    # 後牆用 5 塊圍住窗洞，避免同窗 z-fight
    xL, xR = -hw, hw
    # 窗洞 local x
    wx0 = -hw + win_x0
    wx1 = wx0 + WIN_W
    wy0, wy1 = WIN_SILL, WIN_SILL + WIN_H
    # quads: left of window (full height), right of window, above, below
    def wall_quad(x0, x1, y0, y1, z, tex_w, tex_h, room_h, x_off=-hw):
        # UV from unique wall image: u=(x-(-hw))/tex_w, v_up: image row 0 is top (y=room_h)
        # v = y / tex_h in V-up? Image y=0 is top = room_h. V-up v=1 at image top? Format says V-up, origin bottom-left of image so v=0 at image bottom = y=0.
        # u = (x - x_off) / tex_w
        # v = y / tex_h   (V-up, 0 at floor)
        p = [
            (x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z),
        ]
        n = [(0, 0, 1)] * 4
        # 圖內容由上而下：row 0＝牆頂（y=room_h）。V-up：v=1 喺圖頂。
        # v(y) = 1 - (room_h - y)/tex_h
        def vv(y):
            return 1.0 - (room_h - y) / tex_h
        uvs = [
            ((x0 - x_off) / tex_w, vv(y0)),
            ((x1 - x_off) / tex_w, vv(y0)),
            ((x1 - x_off) / tex_w, vv(y1)),
            ((x0 - x_off) / tex_w, vv(y1)),
        ]
        return p, n, uvs, [0, 1, 2, 0, 2, 3]

    z_back = -hd
    for (x0, x1, y0, y1) in [
        (xL, wx0, 0, ROOM_H),
        (wx1, xR, 0, ROOM_H),
        (wx0, wx1, 0, wy0),
        (wx0, wx1, wy1, ROOM_H),
    ]:
        p, n, u, i = wall_quad(x0, x1, y0, y1, z_back, tw, th, ROOM_H)
        append_quad(buf, p, n, u, i)
    write_mesh(
        "wall_back", "後牆（橫木板，開窗洞）",
        buf, "wall_back.png", back_sz,
        {"rect": {"x": [-hw, hw], "z": [-hd - 1, -hd + 1]}, "pad": 0},
    )

    # 左側牆 x=-hw, 面向 +X, z -hd..hd（w along +Z）
    buf = {"pos": [], "nrm": [], "uv": [], "idx": []}
    tw, th = side_sz
    z0, z1 = -hd, hd
    p = [(-hw, 0, z0), (-hw, 0, z1), (-hw, ROOM_H, z1), (-hw, ROOM_H, z0)]
    n = [(1, 0, 0)] * 4
    # 貼圖：u along z from back to front, v up
    v0 = 1.0 - ROOM_H / th   # 牆底（圖 row=ROOM_H）
    v1 = 1.0                 # 牆頂（圖 row 0）
    uvs = [
        (0, v0),
        (ROOM_D / tw, v0),
        (ROOM_D / tw, v1),
        (0, v1),
    ]
    append_quad(buf, p, n, uvs, [0, 1, 2, 0, 2, 3])
    write_mesh(
        "wall_L", "左牆（橫木板，可平鋪）",
        buf, "wall_side.png", side_sz,
        {"rect": {"x": [-hw - 1, -hw + 1], "z": [-hd, hd]}, "pad": 0},
    )

    # 右側牆 x=+hw, 面向 -X, z -hd..hd；為令正面（從房內睇）CCW：從 +Z 去 -Z
    buf = {"pos": [], "nrm": [], "uv": [], "idx": []}
    p = [(hw, 0, z1), (hw, 0, z0), (hw, ROOM_H, z0), (hw, ROOM_H, z1)]
    n = [(-1, 0, 0)] * 4
    uvs = [
        (0, v0),
        (ROOM_D / tw, v0),
        (ROOM_D / tw, v1),
        (0, v1),
    ]
    append_quad(buf, p, n, uvs, [0, 1, 2, 0, 2, 3])
    write_mesh(
        "wall_R", "右牆（橫木板，可平鋪）",
        buf, "wall_side.png", side_sz,
        {"rect": {"x": [hw - 1, hw + 1], "z": [-hd, hd]}, "pad": 0},
    )

    # 窗：插喺後牆洞，略移入房（+Z 0.4），用 64×64 圖；幾何就窗框咁大（64，內容置中）
    buf = {"pos": [], "nrm": [], "uv": [], "idx": []}
    # 圖 64×64，窗洞 48，框伸出 8；幾何用 64 闊 × 64 高，底喺 sill-8
    ww, wh = 64, 64
    z_win = -hd + 0.4
    cx = (wx0 + wx1) / 2
    yb = wy0 - 8
    p = [
        (cx - ww / 2, yb, z_win),
        (cx + ww / 2, yb, z_win),
        (cx + ww / 2, yb + wh, z_win),
        (cx - ww / 2, yb + wh, z_win),
    ]
    n = [(0, 0, 1)] * 4
    uvs = [(0, 0), (1, 0), (1, 1), (0, 1)]
    append_quad(buf, p, n, uvs, [0, 1, 2, 0, 2, 3])
    write_mesh(
        "window", "後窗（室內面；玻璃有 emissive）",
        buf, "window.png", [64, 64],
        {"rect": {"x": [cx - ww / 2, cx + ww / 2], "z": [-hd, -hd + 2]}, "pad": 0},
        emissive="window_emissive.png",
    )

    # 門：放喺前緣 z=+hd，面向 -Z（由屋內望出去見到門內面）
    buf = {"pos": [], "nrm": [], "uv": [], "idx": []}
    tw, th = door_sz  # 128×128
    # 門圖：門扇 56×96 置底中，框伸出 5，底貼圖底
    dw, dh = 128, 128
    z_door = hd - 0.2
    # 門略偏右，呼應屋外門偏右；但室內要留行位，置中偏右 8
    door_cx = 8
    p = [
        (door_cx + dw / 2, 0, z_door),
        (door_cx - dw / 2, 0, z_door),
        (door_cx - dw / 2, dh, z_door),
        (door_cx + dw / 2, dh, z_door),
    ]
    n = [(0, 0, -1)] * 4  # 面向屋內（-Z? wait +Z is toward camera/door, so inside looking at door looks toward +Z, normal should be -Z)
    # Camera is at +Z looking toward -Z (into the room, toward back wall).
    # Door is on the near wall (z=+hd), we see it from inside which is from smaller z, looking +Z.
    # So the interior face normal is -Z (facing into the room, toward back).
    # Yes normal (0,0,-1). CCW when viewed from inside (from -Z side, looking +Z? From inside we look toward +Z at the door, so we look in +Z direction, the face normal should point toward the viewer, i.e. -Z. Good.
    # Vertices: when viewed from -Z (looking +Z), CCW... actually viewed from the interior (position z < z_door, looking +Z). In that view, +X is right. Bottom-left should be door_cx-dw/2. I have p0 = (cx+dw/2) which is bottom-right if looking +Z? 
    # Looking +Z: +X is right. Bottom-left = (cx-dw/2, 0), bottom-right=(cx+dw/2,0).
    # I listed p0=(cx+dw/2) first then p1=(cx-dw/2) — that's right then left, with normal -Z.
    # Standard: CCW when normal toward you. Normal is -Z, so "toward you" if you look along -Z (from +Z, looking toward origin). That's from OUTSIDE.
    # I got this confused.
    # Godot / format: CCW = front, normal should match.
    # We want the front of the door visible from INSIDE (camera is at +Z looking -Z... wait).
    # Room: back wall z=-64, door z=+64, camera typically at z=+200 looking at origin, look direction is -Z.
    # Camera SEES the back wall (faces +Z, normal +Z, camera looks -Z, so it sees the +Z face of the back wall). Good.
    # Camera also needs to SEE the interior face of the door. The door is NEAR the camera, at z=+64, camera is at z>64? If camera is at z=+200, the door is between camera and room. The camera would see the OUTSIDE of the door (the +Z face) unless the front wall is open and we look past the door frame.
    # For a 3-wall room with door on the near edge, typically the door is at the near wall but we view from a slightly lower angle seeing the interior, OR the door is on a SIDE wall.
    # Octopath often has the door on the side or back. "Inside view of the door" — put the door on the LEFT or RIGHT wall so the camera looking into the room sees the door clearly on a side wall.
    # Better: put the door on the right wall (x=+hw), so we see it from inside, facing -X (into the room). That's a classic 3-wall set with door on the right.
    # 遊程 said 撑入屋先轉室內近鏡 — you enter and the camera is inside looking at the back wall. The door you came through would be behind/near the camera (front open). So the "inside view of the door" is the back of the entrance, on the near side, maybe slightly in frame at the bottom or side.
    # I'll put the door on the RIGHT wall so it's clearly visible in the preview (inside face). That's more useful for art review.
    buf = {"pos": [], "nrm": [], "uv": [], "idx": []}
    # Right wall inner face at x=hw, door standing on floor, leaf 56 wide along Z, 96 tall.
    # Center door along Z slightly toward back? Or center. Let's center at z=0, door leaf along Z (width 56 is horizontal).
    # Image is 128×128 with door at bottom center. Place so bottom of image is y=0, and the 128 width goes along -Z (so looking from inside, left of texture is toward +Z/camera? )
    # Inside viewer looks at right wall (looking +X). +Z is to the left? If we look +X, +Z is left, -Z is right, +Y up.
    # Texture left should be +Z (left). p0 bottom-left = (hw, 0, +dw/2), p1 bottom-right = (hw, 0, -dw/2).
    # 門扇＋框實際 66×101（56+5×2，96+5），UV 只取呢塊，1 px＝1 unit。
    u0, u1 = 31 / 128.0, 97 / 128.0
    dh = 101
    v1 = dh / 128.0
    half = 33.0  # 66/2
    p = [
        (hw - 0.4, 0, half),
        (hw - 0.4, 0, -half),
        (hw - 0.4, dh, -half),
        (hw - 0.4, dh, half),
    ]
    n = [(-1, 0, 0)] * 4
    uvs = [(u0, 0), (u1, 0), (u1, v1), (u0, v1)]
    append_quad(buf, p, n, uvs, [0, 1, 2, 0, 2, 3])
    write_mesh(
        "door", "入屋門之內面（掛喺右牆；腳落地）",
        buf, "door.png", door_sz,
        {"rect": {"x": [hw - 2, hw], "z": [-33.0, 33.0]}, "pad": 0},
    )

    # objects / lights / camera / room.json
    objects = {
        "format": "garden3d.interior/1",
        "id": "H1_interior",
        "zh": "小屋室內（三牆盒：地板、後牆、左右牆、窗、門）",
        "assumedRoom": {
            "units": "1 unit = 1 art px = 1 world unit",
            "width": ROOM_W,
            "depth": ROOM_D,
            "ceiling": ROOM_H,
            "wallThickness": WALL_T,
            "metres": {
                "note": "L 寵物可見身高 54 u 當 0.80 m（Q 版小伴）；遊程 GIF 出咗可以改",
                "mPerUnit": round(M_PER_U, 6),
                "width_m": round(ROOM_W * M_PER_U, 3),
                "depth_m": round(ROOM_D * M_PER_U, 3),
                "ceiling_m": round(ROOM_H * M_PER_U, 3),
            },
            "tileable": True,
            "tileSize": TILE,
            "origin": "floor center; +X right, +Y up, +Z toward camera / near edge",
            "openFront": True,
        },
        "objects": [
            {"id": "floor", "type": "mesh", "zh": "地板", "mesh": "meshes/floor.json", "x": 0, "y": 0, "z": 0, "yawDeg": 0, "castShadow": True, "receiveShadow": True, "layer": "near"},
            {"id": "wall_back", "type": "mesh", "zh": "後牆", "mesh": "meshes/wall_back.json", "x": 0, "y": 0, "z": 0, "yawDeg": 0, "castShadow": True, "receiveShadow": True, "layer": "mid"},
            {"id": "wall_L", "type": "mesh", "zh": "左牆", "mesh": "meshes/wall_L.json", "x": 0, "y": 0, "z": 0, "yawDeg": 0, "castShadow": True, "receiveShadow": True, "layer": "mid"},
            {"id": "wall_R", "type": "mesh", "zh": "右牆", "mesh": "meshes/wall_R.json", "x": 0, "y": 0, "z": 0, "yawDeg": 0, "castShadow": True, "receiveShadow": True, "layer": "mid"},
            {"id": "window", "type": "mesh", "zh": "後窗", "mesh": "meshes/window.json", "x": 0, "y": 0, "z": 0, "yawDeg": 0, "castShadow": False, "receiveShadow": True, "layer": "mid", "emissiveLight": "window"},
            {"id": "door", "type": "mesh", "zh": "門（內面）", "mesh": "meshes/door.json", "x": 0, "y": 0, "z": 0, "yawDeg": 0, "castShadow": True, "receiveShadow": True, "layer": "near"},
        ],
    }
    json.dump(objects, open(os.path.join(ROOT, "objects.json"), "w"), ensure_ascii=False, indent=1)

    lights = {
        "variant": "H1_interior",
        "name": "室內晨光（窗光為主）",
        "assumedRoom": {"width": ROOM_W, "depth": ROOM_D, "ceiling": ROOM_H},
        "lights": [
            {
                "id": "window",
                "zh": "後窗日光／夜燈",
                "x": 0,
                "y": WIN_SILL + WIN_H * 0.5,
                "z": -hd + 2,
                "color": "#ffc870",
                "radius": 90,
                "intensity": 0.0,
                "intensityNight": 0.9,
                "flicker": 0.02,
            }
        ],
        "sun": {
            "dir": [0.35, -0.55, -0.76],
            "color": "#ffe6b8",
            "intensity": 0.55,
            "ambient": {"color": "#e8d8c0", "intensity": 0.70},
            "shadowIntensity": 0.25,
            "note": "由窗方向略斜照入；唔烘入貼圖",
        },
        "fill": {
            "dir": [0.15, -0.2, -0.97],
            "color": "#ffe2c4",
            "intensity": 0.50,
            "intensityNight": 0.0,
            "note": "鏡頭方向補光，日 0.50，夜 0",
        },
        "night": {
            "sun": 0.06,
            "ambient": "#5a4a70",
            "ambientIntensity": 0.40,
        },
        "fog": {"color": "#ffe8c8", "near": 420, "far": 1400, "enabled": False},
        "tiers": {
            "high": {
                "sun_color": "#ffe6b8",
                "sun_energy": 0.55,
                "fill_color": "#ffe2c4",
                "fill_energy": 0.50,
                "ambient_color": "#e8d8c0",
                "ambient_energy": 0.70,
                "window_color": "#ffc870",
                "window_day": 0.0,
                "window_night": 0.9,
                "shadow_opacity": 0.25,
                "shaded": True,
            },
            "mid": {
                "sun_color": "#ffe6b8",
                "sun_energy": 0.40,
                "fill_color": "#ffe2c4",
                "fill_energy": 0.35,
                "ambient_color": "#e8d8c0",
                "ambient_energy": 0.75,
                "window_color": "#ffc870",
                "window_day": 0.0,
                "window_night": 0.75,
                "shadow_opacity": 0.15,
                "shaded": True,
            },
            "low": {
                "sun_color": "#ffe6b8",
                "sun_energy": 0.0,
                "fill_color": "#ffe2c4",
                "fill_energy": 0.0,
                "ambient_color": "#f0e0c8",
                "ambient_energy": 1.0,
                "window_color": "#ffc870",
                "window_day": 0.0,
                "window_night": 0.6,
                "shadow_opacity": 0.0,
                "shaded": False,
                "albedo_mul_day": "#fff6e8",
                "albedo_mul_night": "#6a6088",
            },
        },
    }
    json.dump(lights, open(os.path.join(ROOT, "lights.json"), "w"), ensure_ascii=False, indent=1)

    # 室內近鏡：pitch 30，望房中央略後，距離睇到三牆同寵物
    camera = {
        "target": [0, 36, -8],
        "pitchDeg": 30,
        "dist": 260,
        "fovDeg": 40,
        "yawDeg": 0,
        "orbitMinDeg": -12,
        "orbitMaxDeg": 12,
        "near": 4,
        "far": 2000,
        "note": "Octopath 固定 pitch 30°；近鏡，遊程 GIF 可以改 dist／target",
    }
    json.dump(camera, open(os.path.join(ROOT, "camera.json"), "w"), ensure_ascii=False, indent=1)

    room = {
        "id": "H1_interior",
        "assumed": True,
        "waitingFor": "遊程室內 GIF（最終房間尺寸）",
        "units": "1 unit = 1 art px = 1 world unit",
        "size": {"width": ROOM_W, "depth": ROOM_D, "ceiling": ROOM_H, "wallThickness": WALL_T},
        "metres": {
            "basis": "L pet visible height 54 u = 0.80 m",
            "mPerUnit": round(M_PER_U, 6),
            "width_m": round(ROOM_W * M_PER_U, 3),
            "depth_m": round(ROOM_D * M_PER_U, 3),
            "ceiling_m": round(ROOM_H * M_PER_U, 3),
        },
        "door": {"width": DOOR_W, "height": DOOR_H, "wall": "right", "note": "1.78× L 可見高 54；闊 56 ＞ L 可見闊 44"},
        "window": {"width": WIN_W, "height": WIN_H, "sill": WIN_SILL, "wall": "back"},
        "texelDensity": "1 px/unit（1x）；@3x 最近鄰 ×3",
        "palette": "H1 cottage.png 21 色＋窗發光 #ffc870／#ffe9a0",
        "tileable": {"floor_tile": 64, "wall_tile": 64},
        "furnitureHint": {
            "pixel_size": 1.0,
            "keep": ["flowerpots", "lamp_posts", "fence", "trees", "mushrooms", "can", "jar", "lanterns", "veg_bed"],
            "moveInside": ["bed", "table", "rug", "lamp", "wall", "window"],
        },
    }
    json.dump(room, open(os.path.join(ROOT, "room.json"), "w"), ensure_ascii=False, indent=1)
    print("interior1 written to", ROOT)


if __name__ == "__main__":
    build()
