#!/usr/bin/env python3
"""build_bubble_fix1.py — M1 需要泡泡（單格）V3-A 金幼線＋深藍磨砂玻璃。

原因：M1a（tree 5f4ccc27／遊程 8da4d168）只把 32px icon 用 Sprite3D pixel_size=0.35
掛喺頭頂，overview 大約 15px，冇泡泡框，喺日間草地同招牌頭頂光球旁邊睇唔清。
bubble_dream@3x 係兩格事件框，仲有真 alpha，唔適合 Sprite3D ALPHA_CUT_DISCARD。

呢份產出：單格需要泡泡，風格唔改（金幼線、深藍霜玻璃），對比同外框加強；
sprite alpha 只有 0/255（透明 RGB=0），可以直接做世界空間 Sprite3D。
Pillow／numpy 程序化，冇 AI 圖。

用法：python3 build_bubble_fix1.py [out_root]
預設 out_root = /workspace/game-design
"""
from __future__ import annotations
import os, sys, json, hashlib
import numpy as np
from PIL import Image

V3 = dict(
    ink=(36, 34, 52), cream=(250, 244, 230), mute=(206, 212, 230),
    gold=(232, 200, 128), goldhi=(255, 236, 184), golddk=(66, 40, 4),
    navy=(18, 24, 48), navy2=(30, 40, 74), navy3=(44, 58, 104),
    amber=(246, 176, 72),
)
# 外框加深一檔，日間草地先托得住金線
INK = (48, 28, 56)

W, H = 64, 56  # 單格需要泡泡
ICON = 32
# icon 置中於泡泡主體（唔計尾）
BODY = (2, 2, 62, 44)  # x0,y0,x1,y1 exclusive-ish inclusive draw


def rgba(h, w=None):
    if w is None:
        w = h
    return np.zeros((h, w, 4), np.uint8)


def pset(im, x, y, col, a=255):
    h, w = im.shape[:2]
    if 0 <= x < w and 0 <= y < h:
        im[y, x] = (col[0], col[1], col[2], a if len(col) == 3 else col[3])


def fill_rect(im, x0, y0, x1, y1, col, a=255):
    h, w = im.shape[:2]
    xa, xb = max(0, min(x0, x1)), min(w, max(x0, x1))
    ya, yb = max(0, min(y0, y1)), min(h, max(y0, y1))
    c = col if len(col) == 4 else (col[0], col[1], col[2], a)
    im[ya:yb, xa:xb] = c


def disc(im, cx, cy, r, col, a=255):
    h, w = im.shape[:2]
    c = col if len(col) == 4 else (col[0], col[1], col[2], a)
    yy, xx = np.ogrid[:h, :w]
    m = (xx - cx) ** 2 + (yy - cy) ** 2 <= (r + 0.25) ** 2
    im[m] = c


def rrect(dst, x0, y0, x1, y1, r, col, a=255):
    """Filled rounded rect, x1/y1 exclusive."""
    fill_rect(dst, x0 + r, y0, x1 - r, y1, col, a)
    fill_rect(dst, x0, y0 + r, x1, y1 - r, col, a)
    disc(dst, x0 + r, y0 + r, r, col, a)
    disc(dst, x1 - r - 1, y0 + r, r, col, a)
    disc(dst, x0 + r, y1 - r - 1, r, col, a)
    disc(dst, x1 - r - 1, y1 - r - 1, r, col, a)


def line(im, x0, y0, x1, y1, col, a=255):
    x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
    dx, dy = abs(x1 - x0), abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx - dy
    while True:
        pset(im, x0, y0, col, a)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy


def harden_alpha(im):
    out = im.copy()
    m = out[..., 3] > 127
    out[..., 3] = np.where(m, 255, 0)
    out[~m, :3] = 0
    return out


def blit(dst, src, x, y):
    s = src
    h, w = s.shape[:2]
    H, W_ = dst.shape[:2]
    x0, y0 = int(x), int(y)
    sx0 = 0 if x0 >= 0 else -x0
    sy0 = 0 if y0 >= 0 else -y0
    sx1 = w if x0 + w <= W_ else W_ - x0
    sy1 = h if y0 + h <= H else H - y0
    if sx1 <= sx0 or sy1 <= sy0:
        return dst
    patch = s[sy0:sy1, sx0:sx1]
    m = patch[..., 3] > 127
    region = dst[y0 + sy0:y0 + sy1, x0 + sx0:x0 + sx1]
    region[m] = patch[m]
    dst[y0 + sy0:y0 + sy1, x0 + sx0:x0 + sx1] = region
    return dst


def load_rgba(path):
    im = Image.open(path).convert("RGBA")
    return np.array(im)


def save_png(path, im):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    Image.fromarray(harden_alpha(im), "RGBA").save(path, "PNG")


def ring_mask(base_mask, shrink=1):
    """Pixels in mask that are within `shrink` of the outside."""
    a = base_mask
    P = np.pad(a, 1)
    inner = P[1:-1, 1:-1] & P[:-2, 1:-1] & P[2:, 1:-1] & P[1:-1, :-2] & P[1:-1, 2:]
    if shrink <= 1:
        return a & ~inner
    # iteratively erode
    cur = a
    for _ in range(shrink):
        P = np.pad(cur, 1)
        cur = cur & P[:-2, 1:-1] & P[2:, 1:-1] & P[1:-1, :-2] & P[1:-1, 2:]
    return a & ~cur


def bubble_plate():
    """單格思想泡泡：不透明深藍霜玻璃＋金幼線＋深色外框。0/255。"""
    im = rgba(H, W)
    # 1) 外影／深外框（ink）— 比原 bubble_dream 更實，托住日間草地
    rrect(im, 1, 1, 63, 45, 11, INK, 255)
    # 2) 主體霜玻璃：navy 外圈、navy2 填、上部 navy3 高光帶（焗成實色，唔用半透明）
    rrect(im, 2, 2, 62, 44, 10, V3["navy"], 255)
    rrect(im, 4, 4, 60, 42, 8, V3["navy2"], 255)
    # 上部玻璃高光（實色，稍亮）
    fill_rect(im, 12, 5, 52, 9, V3["navy3"], 255)
    fill_rect(im, 16, 5, 48, 6, V3["goldhi"] and V3["navy3"], 255)
    # 一條更亮嘅頂線（玻璃反光，仍然 0/255）
    fill_rect(im, 18, 5, 46, 6, (58, 72, 120), 255)
    # 3) 金幼線：喺 ink 同 navy 之間描一圈
    body = rgba(H, W)
    rrect(body, 2, 2, 62, 44, 10, V3["gold"], 255)
    inner = rgba(H, W)
    rrect(inner, 4, 4, 60, 42, 8, (255, 255, 255), 255)
    gold_edge = (body[..., 3] > 0) & (inner[..., 3] == 0)
    im[gold_edge, :3] = V3["gold"]
    im[gold_edge, 3] = 255
    # 金線外側再加 1px golddk，令金線喺亮草地同夜地都有厚度
    # （只改貼住金線、原本已經不透明嘅像素，避免脹出 canvas）
    goldm = np.zeros((H, W), bool)
    goldm[gold_edge] = True
    P = np.pad(goldm, 1)
    neigh = P[:-2, 1:-1] | P[2:, 1:-1] | P[1:-1, :-2] | P[1:-1, 2:]
    # 外圈：唔係金線、係 ink 外框嗰層
    is_ink = (im[..., 0] == INK[0]) & (im[..., 1] == INK[1]) & (im[..., 2] == INK[2]) & (im[..., 3] == 255)
    dk = neigh & is_ink & ~goldm
    im[dk, :3] = V3["golddk"]
    im[dk, 3] = 255
    # 4) 尾（朝下，對準寵物頭頂）
    # 底邊約 y=43，尾尖 y=54，偏中
    tip_x, tip_y = 32, 54
    left, right, top = 24, 40, 43
    for y in range(top, tip_y + 1):
        t = (y - top) / float(tip_y - top)
        x0 = int(round(left + (tip_x - left) * t))
        x1 = int(round(right + (tip_x - right) * t))
        for x in range(x0, x1 + 1):
            # 邊：ink + gold；內：navy2
            if x == x0 or x == x1 or y == tip_y:
                pset(im, x, y, INK, 255)
            else:
                pset(im, x, y, V3["navy2"], 255)
    # 尾金邊（內側一像素）
    line(im, left + 1, top, tip_x, tip_y - 1, V3["gold"], 255)
    line(im, right - 1, top, tip_x, tip_y - 1, V3["gold"], 255)
    # 尖端金點
    pset(im, tip_x, tip_y - 1, V3["gold"], 255)
    pset(im, tip_x, tip_y, INK, 255)
    # 5) 兩粒金光（同 dream 泡泡裝飾語言，唔加第二格）
    pset(im, 8, 8, V3["goldhi"], 255)
    pset(im, 55, 10, V3["gold"], 255)
    return harden_alpha(im)


def composite_need(plate, icon):
    out = plate.copy()
    # icon 置中於主體：body inner 4..60 x 4..42 → center (32, 23)
    ix = 32 - ICON // 2
    iy = 23 - ICON // 2
    blit(out, icon, ix, iy)
    return harden_alpha(out)


def find_icon(name, search_roots):
    candidates = [
        f"art/m1-icons/{name}.png",
        f"art-pet/ui/m1_icons/icons/{name}@3x.png",
        f"src/glimmer-a/art/v3/ui/m1_icons/icons/{name}@3x.png",
    ]
    for root in search_roots:
        for rel in candidates:
            p = os.path.join(root, rel)
            if os.path.isfile(p):
                return p
    # absolute fallbacks
    for p in (
        f"/workspace/glimmer-godot/art/m1-icons/{name}.png",
        f"/workspace/art-fix1-wt/art-pet/ui/m1_icons/icons/{name}@3x.png",
        f"/workspace/game-design/art-pet/ui/m1_icons/icons/{name}@3x.png",
    ):
        if os.path.isfile(p):
            return p
    raise FileNotFoundError(name)


def sha1(path):
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def contrast_ratio(c1, c2):
    def lum(c):
        def f(v):
            v = v / 255.0
            return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
        r, g, b = f(c[0]), f(c[1]), f(c[2])
        return 0.2126 * r + 0.7152 * g + 0.0722 * b
    L1, L2 = lum(c1), lum(c2)
    hi, lo = max(L1, L2), min(L1, L2)
    return (hi + 0.05) / (lo + 0.05)


def build(out_root):
    bubbles_dir = os.path.join(out_root, "art-pet/ui/m1_icons/bubbles")
    godot_dir = os.path.join(out_root, "art/m1-icons")
    os.makedirs(bubbles_dir, exist_ok=True)
    os.makedirs(godot_dir, exist_ok=True)

    plate = bubble_plate()
    assert set(np.unique(plate[..., 3]).tolist()) <= {0, 255}
    # transparent RGB=0
    assert np.all(plate[plate[..., 3] == 0, :3] == 0)

    search = [out_root, "/workspace/game-design", "/workspace/art-fix1-wt", "/workspace/glimmer-godot"]
    needs = ["need_eat", "need_play", "need_sleep", "need_pet"]
    files = {}
    plate_path = os.path.join(bubbles_dir, "bubble_need@3x.png")
    save_png(plate_path, plate)
    files["bubble_need@3x.png"] = plate_path
    # godot drop-in (no @3x suffix)
    save_png(os.path.join(godot_dir, "bubble_need.png"), plate)
    files["godot/bubble_need.png"] = os.path.join(godot_dir, "bubble_need.png")

    sources = {}
    for n in needs:
        src = find_icon(n, search)
        sources[n] = src
        icon = load_rgba(src)
        assert icon.shape == (32, 32, 4), (n, icon.shape)
        assert set(np.unique(icon[..., 3]).tolist()) <= {0, 255}, n
        comp = composite_need(plate, icon)
        assert set(np.unique(comp[..., 3]).tolist()) <= {0, 255}
        p1 = os.path.join(bubbles_dir, f"{n}@3x.png")
        p2 = os.path.join(godot_dir, f"bubble_{n}.png")
        save_png(p1, comp)
        save_png(p2, comp)
        files[f"{n}@3x.png"] = p1
        files[f"godot/bubble_{n}.png"] = p2

    # contrast notes
    day_grass = (161, 195, 56)
    night_grass = (28, 46, 36)
    notes = {
        "navy2_vs_day_grass": round(contrast_ratio(V3["navy2"], day_grass), 2),
        "navy2_vs_night_grass": round(contrast_ratio(V3["navy2"], night_grass), 2),
        "gold_vs_day_grass": round(contrast_ratio(V3["gold"], day_grass), 2),
        "gold_vs_night_grass": round(contrast_ratio(V3["gold"], night_grass), 2),
        "need_eat_cream_vs_day_grass": round(contrast_ratio((250, 244, 230), day_grass), 2),
        "need_play_leaf_vs_day_grass": round(contrast_ratio((107, 191, 106), day_grass), 2),
    }

    spec = dict(
        format="m1.need_bubble/1",
        style="V3-A 金光深藍、金幼線、深藍霜玻璃（焗成 0/255，Sprite3D 用）",
        size=[W, H],
        scale="@3x（1:1 顯示，同 kit_hd2d_v3）",
        alpha="sprite 0/255；透明 RGB=0",
        pivotPx=[32, 54],
        iconSlot={"x": 16, "y": 7, "w": 32, "h": 32},
        plate="bubble_need@3x.png",
        items=[{"id": n, "file": f"{n}@3x.png", "godot": f"art/m1-icons/bubble_{n}.png"} for n in needs],
        engine=dict(
            path="res://art/m1-icons/bubble_need_eat.png  （依 icon_id 換 bubble_{id}.png）",
            do_not_replace="art/m1-icons/need_*.png — HUD 一鍵掣共用呢批 32px 純 icon",
            do_not_use="bubble_dream@3x.png（兩格事件框、真 alpha）",
            sprite3d={
                "shaded": False,
                "alpha_cut": "ALPHA_CUT_DISCARD",
                "alpha_scissor_threshold": 0.5,
                "texture_filter": "TEXTURE_FILTER_NEAREST",
                "modulate": "Color(1, 1, 1, 1)",
                "pixel_size": 0.62,
                "billboard": "BILLBOARD_ENABLED",
                "double_sided": True,
                "render_priority": 2,
                "no_depth_test": True,
                "cast_shadow": "SHADOW_CASTING_SETTING_OFF",
                "pixel_size_note": "64×56 × 0.62 ≈ 40×35 世界單位；overview 寵物框 64u、畫面高佔 10% 時泡泡約 52px 高。唔好再用 0.35 掛裸 32px icon（約 15px）。",
            },
            lut="Sprite3D 會食環境 LUT／tonemap。夜間 exposure 0.88。因為框已係實色深藍＋金線，LUT 之後仍然對得上草地。唔使 modulate>1。Godot 4 唔可以單獨豁免一粒 Sprite3D 唔食 LUT；若要完全豁免，改 CanvasLayer 投影。",
            position="用 walker.visible_world_top() + 泡泡高度一半 + 6，避開招牌頭頂光球（atlas_radiant 光球大約喺框頂以下 7px）。",
        ),
        contrast=notes,
        sources=sources,
        note="風格同已通過嘅 V3-A 一緻：金幼線、深藍霜玻璃。加強嘅係外框對比同焗實 alpha，唔改造型語言。",
    )
    spec_path = os.path.join(bubbles_dir, "bubbles.json")
    with open(spec_path, "w") as f:
        json.dump(spec, f, ensure_ascii=False, indent=1)
    files["bubbles.json"] = spec_path
    return spec, files


if __name__ == "__main__":
    root = sys.argv[1] if len(sys.argv) > 1 else "/workspace/game-design"
    spec, files = build(root)
    print("bubble_fix1 ok", json.dumps({k: os.path.getsize(v) for k, v in files.items()}, ensure_ascii=False, indent=1))
    print("contrast", spec["contrast"])
