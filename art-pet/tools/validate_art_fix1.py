#!/usr/bin/env python3
"""validate_art_fix1.py — 文靜坐低 S/M/L、細佬／訪客 M 生命感：alpha、pivot、幀數、錨點、法線。"""
import os, sys, json
import numpy as np
from PIL import Image

R = []

def chk(name, ok, info=None):
    R.append(dict(check=name, ok=bool(ok), info=None if ok else info))
    return bool(ok)

def load(png):
    return np.array(Image.open(png).convert('RGBA'))

def _norm_ok(n, c):
    k = c[..., 3] > 0
    if not k.any():
        return False, 'empty'
    v = n[..., :3].astype(float) / 255 * 2 - 1
    L = np.linalg.norm(v, axis=-1)
    if np.abs(L[k] - 1).max() >= 0.03:
        return False, f'len max {np.abs(L[k]-1).max():.4f}'
    if n[k, 2].min() < 128:
        return False, 'B<128'
    return True, None

def _g_up(sub):
    a = sub[..., 3] > 0
    if not a.any():
        return False
    rows = np.where(a.any(1))[0]
    q = max(1, len(rows) // 4)
    return sub[rows[:q]][a[rows[:q]], 1].mean() > sub[rows[-q:]][a[rows[-q:]], 1].mean()

def check_atlas(png, js, expect):
    chk(f'{js} 存在', os.path.exists(js) and os.path.exists(png), js)
    if not (os.path.exists(js) and os.path.exists(png)):
        return
    J = json.load(open(js))
    chk(f'{expect["stem"]} frameCount/fps/loop/size/pivot',
        J.get('frameCount') == expect['frames'] and J.get('fps') == expect['fps']
        and J.get('loop') is expect['loop'] and J.get('frameSize') == expect['size']
        and tuple(J.get('pivotPx', [])) == tuple(expect['pivot']),
        (J.get('frameCount'), J.get('fps'), J.get('loop'), J.get('frameSize'), J.get('pivotPx')))
    img = load(png)
    nrm = load(png.replace('.png', '_n.png') if not png.endswith('_n.png') else png)
    # meta paths
    npth = os.path.join(os.path.dirname(png), J['meta']['normal'])
    epth = os.path.join(os.path.dirname(png), J['meta']['emissive'])
    nrm = load(npth)
    em = load(epth)
    chk(f'{expect["stem"]} atlas 尺寸同 meta', tuple(img.shape[:2][::-1]) == (J['meta']['size']['w'], J['meta']['size']['h'])
        or (img.shape[1] == J['meta']['size']['w'] and img.shape[0] == J['meta']['size']['h']),
        (img.shape, J['meta']['size']))
    aspects = []
    for name, rec in J['frames'].items():
        f = rec['frame']
        sub = img[f['y']:f['y'] + f['h'], f['x']:f['x'] + f['w']]
        nsub = nrm[f['y']:f['y'] + f['h'], f['x']:f['x'] + f['w']]
        a = sub[..., 3]
        chk(f'{name} alpha 0/255', set(np.unique(a)).issubset({0, 255}), set(map(int, np.unique(a))))
        if (a == 0).any():
            chk(f'{name} 透明 RGB=0', np.all(sub[a == 0, :3] == 0))
        chk(f'{name} 有 pivotPx', rec.get('pivotPx', {}).get('x') == expect['pivot'][0]
            and rec.get('pivotPx', {}).get('y') == expect['pivot'][1], rec.get('pivotPx'))
        anc = rec.get('anchors') or {}
        ok_anc = all(k in anc and isinstance(anc[k], list) and len(anc[k]) == 2 for k in ('eyeL', 'eyeR', 'mouth'))
        chk(f'{name} 有 eye/mouth anchors', ok_anc, anc)
        if ok_anc:
            fs = expect['size']
            inside = all(0 <= anc[k][0] < fs and 0 <= anc[k][1] < fs for k in ('eyeL', 'eyeR', 'mouth'))
            chk(f'{name} anchors 喺幀內', inside, anc)
        ok_n, info = _norm_ok(nsub, sub)
        chk(f'{name} 法線單位／Z+', ok_n, info)
        if expect.get('check_g_up'):
            chk(f'{name} 法線綠＝上', _g_up(nsub))
        if (a > 0).any():
            ys, xs = np.where(a > 0)
            asp = (xs.max() - xs.min() + 1) / (ys.max() - ys.min() + 1)
            aspects.append(asp)
            if expect.get('aspect'):
                lo, hi = expect['aspect']
                chk(f'{name} 寬高比 {lo}–{hi}', lo <= asp <= hi, round(asp, 3))
    return aspects

def main():
    root = sys.argv[1] if len(sys.argv) > 1 else '/workspace/art-fix1-src'
    art = os.path.join(root, 'art-pet')
    # idle_quiet
    for sz, size, pivot in (('S', 32, (16, 29)), ('M', 48, (24, 45)), ('L', 64, (32, 61))):
        stem = f'atlas_radiant_idle_quiet_{sz}'
        d = f'{art}/sprites/tuanrong/motion/m2'
        check_atlas(f'{d}/{stem}.png', f'{d}/{stem}.json', dict(
            stem=stem, frames=6, fps=6, loop=True, size=size, pivot=pivot,
            aspect=(0.8, 1.1), check_g_up=True,
        ))
    # kid
    kid = f'{art}/sprites/series2/liveliness'
    chk('kid clips.json', os.path.exists(f'{kid}/clips.json'))
    for cid, n, fps in (('scratch', 6, 8), ('sneeze', 5, 8), ('sniff', 4, 6)):
        stem = f'atlas_A1_{cid}'
        check_atlas(f'{kid}/{stem}.png', f'{kid}/{stem}.json', dict(
            stem=stem, frames=n, fps=fps, loop=False, size=48, pivot=(24, 45), check_g_up=True,
        ))
    # visitors
    vis = f'{art}/sprites/visitors/m2'
    chk('visitor liveliness_clips.json', os.path.exists(f'{vis}/liveliness_clips.json'))
    for vid, pivot in (('snail_postman', (22, 45)), ('mushroom_granny', (24, 45)), ('firefly_vendor', (24, 44))):
        for cid, n, fps in (('scratch', 6, 8), ('sneeze', 5, 8), ('sniff', 4, 6)):
            stem = f'atlas_{vid}_{cid}'
            check_atlas(f'{vis}/{stem}.png', f'{vis}/{stem}.json', dict(
                stem=stem, frames=n, fps=fps, loop=False, size=48, pivot=pivot, check_g_up=True,
            ))
    # night tint not required
    ok = all(r['ok'] for r in R)
    failed = [r for r in R if not r['ok']]
    print(f'validate_art_fix1: {sum(r["ok"] for r in R)}/{len(R)} pass', 'OK' if ok else 'FAIL')
    for r in failed:
        print('  FAIL', r['check'], r.get('info'))
    out = os.path.join(art, 'validation_art_fix1.json')
    json.dump(dict(ok=ok, total=len(R), passed=sum(r['ok'] for r in R), checks=R),
              open(out, 'w'), ensure_ascii=False, indent=1)
    print('wrote', out)
    return 0 if ok else 1

if __name__ == '__main__':
    sys.exit(main())
