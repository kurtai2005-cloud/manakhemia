#!/usr/bin/env python3
# 《微光小圃》furn-fix1 — 散步鞋架 wall_shoes
# 補 M1c 缺咗嘅牆槽家具圖。純 Pillow/numpy，冇 AI 生圖。
# 風格同 house_4b_furniture.py：V3-A、alpha 0/255、≤12 色、OL 外框、光由左上。
import os, sys
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import house_4b_furniture as F
from series2_lib import ncolors, save, paste

# 50×36：闊度同 wall_shelf（50），兩層鞋各留約 11px 高度。
W, H = 50, 36
PIVOT = (W // 2, H // 2)  # (25, 18)  2D 屋仔牆槽 pivot＝中心


def _flip_h(a):
    return a[:, ::-1].copy()


def _fill_if_body(img, x, y, c):
    if 0 <= y < img.shape[0] and 0 <= x < img.shape[1]:
        if img[y, x, 3] == 255 and tuple(img[y, x, :3]) != F.OL:
            F.put(img, x, y, c)


def _shoe(kind, col):
    """向右嘅一隻鞋。開口用填色而唔係挖洞，避免外框變成『角』。"""
    sw, sh = 16, 12
    img = F.canvas(sw, sh)
    if kind == "mary":
        # 後踭較高、圓頭較低嘅娃娃鞋
        heel = F.m_rr(sw, sh, (1, 1, 7, 9), 2)
        body = heel | F.m_poly(sw, sh, [
            (3, 3), (9, 3), (13, 5), (15, 7),
            (14, 9), (2, 9), (1, 6),
        ]) | F.m_ell(sw, sh, (8, 3, 15, 10))
        F.part(img, body, col, spec=False)
        # 開口（後上）＋襪
        for x, y, c in [
            (3, 2, F.CREAM[2]), (4, 2, F.CREAM[1]), (5, 2, F.CREAM[2]),
            (3, 3, F.CREAM[1]), (4, 3, F.CREAM[0]), (5, 3, F.CREAM[1]),
        ]:
            _fill_if_body(img, x, y, c)
        # 橫帶＋白扣
        for x in range(3, 9):
            _fill_if_body(img, x, 5, col[2])
        _fill_if_body(img, 6, 5, (255, 255, 255))
        # 連續鞋底（貼底，唔留空行）
        for x in range(1, 15):
            _fill_if_body(img, x, 9, F.BARK[2])
        for x in range(2, 15):
            _fill_if_body(img, x, 10, F.BARK[3] if x > 5 else F.BARK[2])
        _fill_if_body(img, 12, 5, (255, 255, 255))
    else:
        # 散步波鞋：略長頭、鞋舌
        body = (
            F.m_rr(sw, sh, (1, 1, 10, 9), 2)
            | F.m_poly(sw, sh, [(7, 2), (14, 5), (15, 8), (14, 10), (2, 10), (1, 6), (2, 2)])
            | F.m_ell(sw, sh, (9, 3, 15, 10))
        )
        F.part(img, body, col, spec=False)
        for x, y, c in [
            (3, 2, F.CREAM[2]), (4, 2, F.CREAM[1]), (5, 2, F.CREAM[2]),
            (3, 3, F.CREAM[1]), (4, 3, F.CREAM[0]), (5, 3, F.CREAM[1]),
        ]:
            _fill_if_body(img, x, y, c)
        _fill_if_body(img, 5, 4, (255, 255, 255))
        _fill_if_body(img, 7, 5, (255, 255, 255))
        for y in range(4, 9):
            _fill_if_body(img, 9, y, col[2])
        for x in range(1, 15):
            _fill_if_body(img, x, 9, F.BARK[2])
        for x in range(2, 15):
            _fill_if_body(img, x, 10, F.BARK[3] if x > 6 else F.BARK[2])
        _fill_if_body(img, 12, 5, (255, 255, 255))
    return img


def _opaque_bottom(shoe):
    rows = [y for y in range(shoe.shape[0]) if (shoe[y, :, 3] == 255).any()]
    return rows[-1] if rows else shoe.shape[0] - 1


def _place_shoe(dst, shoe, left, sole_y, face=1):
    if face < 0:
        shoe = _flip_h(shoe)
    top = sole_y - _opaque_bottom(shoe)
    paste(dst, shoe, left, top)


def wall_shoes():
    img = F.canvas(W, H)
    # 兩層木架＋左右撐＋底托（同 wall_shelf 木材語彙）
    F.part(img, F.m_rr(W, H, (1, 15, 48, 19), 1), F.WOOD)   # 上板
    F.part(img, F.m_rr(W, H, (1, 27, 48, 31), 1), F.WOOD)   # 下板
    F.part(img, F.m_rect(W, H, (2, 15, 6, 31)), F.WOOD)
    F.part(img, F.m_rect(W, H, (43, 15, 47, 31)), F.WOOD)
    for x in (7, 39):
        F.part(img, F.m_poly(W, H, [(x, 31), (x + 4, 31), (x + 4, 35)]), F.WOOD)

    pink = _shoe("mary", F.PINK)
    _place_shoe(img, pink, 7, 14, face=-1)
    _place_shoe(img, pink, 27, 14, face=1)

    blue = _shoe("sneaker", F.BLUE)
    _place_shoe(img, blue, 7, 26, face=-1)
    _place_shoe(img, blue, 27, 26, face=1)
    return F.fin(img)


def _save_debug_shoes():
    draft_dir = "/workspace/game-design/furn_fix1/drafts"
    os.makedirs(draft_dir, exist_ok=True)
    for kind, col, name in (("mary", F.PINK, "shoe_mary"), ("sneaker", F.BLUE, "shoe_sneaker")):
        im = F.fin(_shoe(kind, col))
        pil = Image.fromarray(im)
        bg = Image.new("RGBA", (im.shape[1] * 8 + 16, im.shape[0] * 8 + 16), (186, 168, 150, 255))
        big = pil.resize((im.shape[1] * 8, im.shape[0] * 8), Image.NEAREST)
        bg.paste(big, (8, 8), big)
        bg.save(os.path.join(draft_dir, f"{name}_8x.png"))


def main():
    _save_debug_shoes()
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "sprites/series2_house/furniture")
    img = wall_shoes()
    path = os.path.join(out_dir, "wall_shoes.png")
    save(img, path)
    mid = int(np.sum((img[..., 3] > 0) & (img[..., 3] < 255)))
    print("wrote", path, "size", img.shape[1], img.shape[0],
          "colors", ncolors(img), "mid_alpha", mid,
          "pivot", PIVOT, "bytes", os.path.getsize(path))
    pil = Image.fromarray(img)
    print("palette:")
    for n, c in sorted(((n, c) for n, c in pil.getcolors(200000) if c[3] == 255), key=lambda t: -t[0]):
        print(f"  {c} x{n}")
    draft = "/workspace/game-design/furn_fix1/drafts/wall_shoes_8x.png"
    bg = Image.new("RGBA", (W * 8 + 16, H * 8 + 16), (186, 168, 150, 255))
    big = pil.resize((W * 8, H * 8), Image.NEAREST)
    bg.paste(big, (8, 8), big)
    bg.save(draft)
    print("draft", draft)


if __name__ == "__main__":
    main()
