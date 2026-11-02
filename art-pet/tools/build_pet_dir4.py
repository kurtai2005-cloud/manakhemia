#!/usr/bin/env python3
"""build_pet_dir4.py — 團絨 radiant 4 方向（3D 花園試點用）：正面／背面 idle×4＋walk×6（新出），側面沿用現有 walk（右）＋鏡像（左）。
程序化逐像素改（唔用 AI）：色圖、_n 法線、_emissive 三張圖套同一個變換，尺寸 64×64、pivotPx (32,61) 同現有一致，alpha 0/255。
  正面 idle：現有 idle_01…04（本身係正面）原樣抄過嚟改名；正面 walk：由 idle_01 拆左右腳逐步抬腳＋身體上下 1px。
  背面：去五官／腮紅（用身體色補）、左右鏡像令光暗方向同正面相反 → 似睇緊背脊，加背毛紋、腳只見腳踭；_n 鏡像時 R 反轉。
用法：PYTHONDONTWRITEBYTECODE=1 python3 tools/build_pet_dir4.py
"""
import os, sys, json
import numpy as np
from PIL import Image
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__)); ART = os.path.abspath(f'{HERE}/..')
SRC = f'{ART}/sprites/tuanrong/motion/atlas_radiant'; OUTD = f'{ART}/sprites/tuanrong/motion/dir4'; FS = 64; PIV = (32, 61)
E = (59, 42, 62); H = (255, 239, 196); I_ = (246, 221, 176); J_ = (233, 190, 132); K = (242, 139, 155); G = (255, 248, 224)
F = (224, 127, 69); Lc = (242, 166, 90)

def load():
    A = json.load(open(f'{SRC}.json')); ims = [np.array(Image.open(f'{SRC}{s}.png').convert('RGBA')) for s in ('', '_n', '_emissive')]
    def fr(n):
        r = A['frames'][n]['frame']; return [im[r['y']:r['y']+FS, r['x']:r['x']+FS].copy() for im in ims]
    return A, fr
def eq(c, col): return (c[..., 0] == col[0]) & (c[..., 1] == col[1]) & (c[..., 2] == col[2]) & (c[..., 3] > 0)

FOOTROW = 57          # 呢行以下＝腳（58…62）
FEET = ((19, 28), (36, 45))
def walk(trip, dyL, dyR, dyB):
    """trip＝[色, 法線, 發光]；身體（含光芽）上下 dyB，左右腳各自抬 dyL/dyR（負＝向上）。"""
    out = []
    for k, a in enumerate(trip):
        bg = np.zeros_like(a)
        if k == 1: bg[..., :3] = (128, 128, 255)
        res = bg.copy(); body = a.copy(); body[FOOTROW+1:] = bg[FOOTROW+1:]
        feet = []
        for (x0, x1), dy in zip(FEET, (dyL, dyR)):
            f = bg.copy(); f[FOOTROW+1:, x0:x1] = a[FOOTROW+1:, x0:x1]; feet.append((f, dy))
        # 腳之間嘅底線（row 60 E）屬身體：保留
        mid = bg.copy(); mid[FOOTROW+1:, FEET[0][1]:FEET[1][0]] = a[FOOTROW+1:, FEET[0][1]:FEET[1][0]]
        def paste(dst, src, dy):
            s = np.roll(src, dy, 0)
            if dy < 0: s[dy:] = bg[dy:]
            if dy > 0: s[:dy] = bg[:dy]
            m = s[..., 3] > 0; dst[m] = s[m]
        paste(res, mid, dyB); paste(res, body, dyB)
        for f, dy in feet: paste(res, f, dy)
        out.append(res)
    return out
def back(trip, seed=0):
    c, n, e = [t.copy() for t in trip]; al = c[..., 3] > 0
    # 五官＝身體輪廓以內嘅 E／K／眼高光（行 40…53）
    inner = np.zeros(al.shape, bool); inner[40:54, 14:50] = True
    from scipy import ndimage as nd
    edge = al & ~nd.binary_erosion(al, np.ones((3, 3)))
    face = inner & (eq(c, E) & ~edge | eq(c, K) | (eq(c, G) & nd.binary_dilation(eq(c, E) & inner & ~edge, iterations=1)))
    c[face, :3] = H
    # 腮紅位／五官附近身體色重整：行內左右取樣避免一片平
    c = c[:, ::-1].copy(); n = n[:, ::-1].copy(); e = e[:, ::-1].copy()
    n[..., 0] = np.where(n[..., 3] > 0, 255 - n[..., 0], n[..., 0])
    al = c[..., 3] > 0
    # 背毛紋：中間幾條短弧（I／J），似毛球背脊
    for (y, x0, x1, col) in ((42, 27, 31, I_), (43, 31, 35, I_), (46, 24, 28, I_), (47, 28, 31, I_), (46, 36, 40, I_),
                             (50, 30, 34, J_), (51, 34, 37, J_), (52, 26, 29, J_)):
        k = np.zeros(al.shape, bool); k[y, x0:x1] = True; k &= al & ~edge[:, ::-1]; c[k, :3] = col
    # 腳：背面只見腳踭（腳面 F → 深一級，腳頂 L → J）
    c[eq(c, F), :3] = (196, 104, 58); c[eq(c, Lc), :3] = J_
    return [c, n, e]

def main():
    A, fr = load(); os.makedirs(OUTD, exist_ok=True)
    WALK = [(0, 0, 0), (-2, 0, -1), (-1, 0, 0), (0, 0, 0), (0, -2, -1), (0, -1, 0)]   # (左腳, 右腳, 身體)
    frames = {}
    for i in range(1, 5): frames[f'front_idle_0{i}'] = fr(f'idle_0{i}')
    base = fr('idle_01')
    for i, (l, r, b) in enumerate(WALK): frames[f'front_walk_0{i+1}'] = walk(base, l, r, b)
    for i in range(1, 5): frames[f'back_idle_0{i}'] = back(fr(f'idle_0{i}'))
    bb = back(base)
    for i, (l, r, b) in enumerate(WALK): frames[f'back_walk_0{i+1}'] = walk(bb, r, l, b)    # 背面左右對調
    for i in range(1, 7): frames[f'side_walk_0{i}'] = fr(f'walk_0{i}')
    for i in range(1, 5): frames[f'side_idle_0{i}'] = fr(f'idle_0{i}')
    names = list(frames); cols = 8; P = 2; cell = FS + 2*P
    Wd = 1024; Hd = 1 << int(np.ceil(np.log2(cell*((len(names)+cols-1)//cols))))
    ims = [np.zeros((Hd, Wd, 4), np.uint8) for _ in range(3)]; ims[1][..., :3] = (128, 128, 255)
    J = {'frames': {}, 'meta': {'image': 'atlas_radiant_dir4.png', 'normal': 'atlas_radiant_dir4_n.png', 'emissive': 'atlas_radiant_dir4_emissive.png',
         'size': {'w': Wd, 'h': Hd}, 'format': 'RGBA8888', 'padding': P, 'form': 'radiant', 'frameSize': FS, 'pivotPx': list(PIV),
         'pivotRule': 'bottom-center (w/2, h-3)，同 atlas_radiant 一致',
         'directions': {'front': '向鏡頭（+Z）', 'back': '背向鏡頭（−Z）', 'side': '向右（+X）；向左＝scaleX −1（法線 R 反轉：R→255−R）'},
         'clips': {'front_idle': 4, 'front_walk': 6, 'back_idle': 4, 'back_walk': 6, 'side_idle': 4, 'side_walk': 6},
         'fps': {'idle': 4, 'walk': 10}, 'note': 'side_* 同 front_idle 係現有 atlas_radiant 幀原樣抄（方便引擎一張 atlas 搞掂）；front_walk／back_* 係新出'}}
    for k, nm in enumerate(names):
        x, y = (k % cols)*cell + P, (k//cols)*cell + P
        for t in range(3): ims[t][y:y+FS, x:x+FS] = frames[nm][t]
        J['frames'][nm] = {'frame': {'x': x, 'y': y, 'w': FS, 'h': FS}, 'pivotPx': {'x': PIV[0], 'y': PIV[1]}, 'pivot': {'x': .5, 'y': round(PIV[1]/FS, 4)}}
    for t in range(3):
        a = ims[t]; m = a[..., 3] > 0; a[..., 3] = np.where(m, 255, 0); 
        if t != 1: a[~m, :3] = 0
    for t, s in enumerate(('', '_n', '_emissive')): Image.fromarray(ims[t]).save(f'{OUTD}/atlas_radiant_dir4{s}.png', optimize=True)
    json.dump(J, open(f'{OUTD}/atlas_radiant_dir4.json', 'w'), ensure_ascii=False, indent=1)
    print('ok', len(names))   # 檢查圖改由 preview_garden3d.py --only dir4 出（pet_dir4_sheet.png）
if __name__ == '__main__': main()
