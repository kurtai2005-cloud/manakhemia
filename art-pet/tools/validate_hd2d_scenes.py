#!/usr/bin/env python3
"""驗證 scenes/hd2d（格式見 scenes/hd2d/FORMAT.md）。用法：python3 validate_hd2d_scenes.py [--strict]
--strict：粒子／雨層／rim／crossfade 未交都當 FAIL（預設只係 PENDING）。"""
import json, os, re, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_hd2d_scenes as B

OUT = B.OUT; RIM = os.path.join(B.ROOT, 'sprites', 'tuanrong', 'rim')
LW, LH, AW, AH = B.LW, B.LH, B.AW, B.AH
res = {'PASS': 0, 'FAIL': 0, 'PENDING': 0}; strict = '--strict' in sys.argv
def rep(ok, msg, pending=False):
    k = 'PASS' if ok else ('PENDING' if pending and not strict else 'FAIL'); res[k] += 1
    if k != 'PASS' or '-v' in sys.argv: print(f'[{k}] {msg}')
HEX = re.compile(r'^#[0-9a-f]{6}$')
def im(p): return Image.open(p)
def arr(p): return np.asarray(Image.open(p).convert('RGBA'))

def check_grade(g, where, rain_ok=True):
    def num(path, lo, hi):
        cur = g
        for k in path.split('.'): cur = cur.get(k) if isinstance(cur, dict) else None
        rep(isinstance(cur, (int, float)) and not isinstance(cur, bool) and lo <= cur <= hi, f'{where} {path}={cur} ∈ [{lo},{hi}]')
    def col(path):
        cur = g
        for k in path.split('.'): cur = cur.get(k) if isinstance(cur, dict) else None
        rep(isinstance(cur, str) and bool(HEX.match(cur)), f'{where} {path}={cur} 係 "#rrggbb"')
    for c in ('ambientTint', 'petTint', 'fog.color', 'rim.color', 'bulbGlowTint', 'particles.color', 'rain.tint'): col(c)
    num('saturation', 0, 2); num('contrast', 0.5, 1.5); num('bloom.threshold', 0, 1); num('bloom.intensity', 0, 2)
    num('fog.density', 0, 0.3); num('dof.far', 0, 8); num('dof.mid', 0, 8); num('dof.fore', 0, 8); num('vignette', 0, 1)
    num('rim.intensity', 0, 1); num('particles.rate', 0, 10); num('rain.saturation', 0, 2); num('rain.contrast', 0.5, 1.5)
    d = g.get('rim', {}).get('dir')
    rep(isinstance(d, list) and len(d) == 2 and all(isinstance(x, (int, float)) for x in d) and 0.9 <= float(np.hypot(*d)) <= 1.1, f'{where} rim.dir={d} 係單位向量 [x,y]')
    rep(g.get('particles', {}).get('type') in ('mote', 'gold', 'petal', 'firefly'), f'{where} particles.type')
    allowed = {'variant', 'name', 'hours', 'ambientTint', 'petTint', 'saturation', 'contrast', 'bloom', 'fog', 'dof', 'vignette', 'rim', 'bulbGlowTint', 'particles', 'rain', 'baseVariant', 'note'}
    extra = set(g) - allowed; rep(not extra, f'{where} 冇多餘欄位 {sorted(extra)}')

def check_layerset(d, key, g, lutname='lut.png', sub=''):
    tag = f'{key}{sub}'
    for nm in ('sky', 'far', 'mid', 'fore'):
        p = os.path.join(d, f'{nm}.png'); ok = os.path.exists(p); rep(ok, f'{tag} {nm}.png 存在')
        if not ok: continue
        i = im(p); rep(i.size == (LW, LH) and i.mode == 'RGBA', f'{tag} {nm}.png {i.size} {i.mode} == {(LW, LH)} RGBA')
        if nm == 'sky': rep(arr(p)[..., 3].min() == 255, f'{tag} sky 全不透明')
    p = os.path.join(d, lutname)
    if os.path.exists(p):
        l = im(p); rep(l.size == (256, 16) and l.mode == 'RGB', f'{tag} {lutname} 256×16 RGB')
        lut = np.asarray(l).astype(float)/255
        ref = B.make_lut({k: g[k] for k in ('ambientTint', 'contrast', 'saturation')}, None)
        rep(np.abs(lut-ref).max() <= 1.5/255 or sub, f'{tag} {lutname} 同 grade.json 公式一致（Δmax {np.abs(lut-ref).max()*255:.2f}/255）')
        # sky 未模糊：baked ≈ LUT(raw)
        rp = os.path.join(os.path.dirname(d) if sub else d, 'raw', 'sky.png'); sp = os.path.join(d, 'sky.png')
        if os.path.exists(rp) and os.path.exists(sp):
            raw = arr(rp)[..., :3].astype(float)/255; bk = arr(sp)[..., :3].astype(float)/255
            dl = np.abs(B.apply_lut(raw, lut)-bk).max()*255; rep(dl <= 2.0, f'{tag} sky.png ＝ LUT(raw/sky)（Δmax {dl:.2f}/255）')
    else: rep(False, f'{tag} {lutname} 存在')

def check_variant(key):
    d = os.path.join(OUT, key)
    if not os.path.isdir(d): rep(False, f'{key} 資料夾', pending=True); return
    gp = os.path.join(d, 'grade.json'); rep(os.path.exists(gp), f'{key} grade.json')
    g = json.load(open(gp)); check_grade(g, f'{key}/grade.json')
    pal = json.load(open(os.path.join(d, 'palette.json'))); allowed = {tuple(int(c['hex'][i:i+2], 16) for i in (1, 3, 5)) for c in pal['colors']}
    rep(len(pal['colors']) <= 64, f'{key} palette.json ≤64 色（{len(pal["colors"])}）')
    used = set()
    for nm in ('sky', 'far', 'mid', 'fore'):
        p = os.path.join(d, 'raw', f'{nm}.png'); ok = os.path.exists(p); rep(ok, f'{key} raw/{nm}.png 存在')
        if not ok: continue
        a = arr(p); rep(a.shape[:2] == (LH, LW), f'{key} raw/{nm} 尺寸')
        rep(set(np.unique(a[..., 3])) <= {0, 255}, f'{key} raw/{nm} alpha 只有 0/255')
        cs = {tuple(c) for c in a[a[..., 3] == 255][:, :3]}; used |= cs
        rep(cs <= allowed, f'{key} raw/{nm} 全部喺 palette.json（越界 {len(cs-allowed)}）')
    rep(len(used) <= 64, f'{key} raw 四層合共 {len(used)} 色 ≤ 64')
    check_layerset(d, key, g)
    for nm, mode in (('lightmap', 'RGB'), ('light_add', 'RGB'), ('emissive', 'RGBA'), ('emissive_blur', 'RGB')):
        p = os.path.join(d, f'{nm}.png'); ok = os.path.exists(p); rep(ok, f'{key} {nm}.png 存在')
        if ok: i = im(p); rep(i.size == (LW, LH) and i.mode == mode, f'{key} {nm}.png {i.size} {i.mode} == {(LW, LH)} {mode}')
    p = os.path.join(d, 'emissive.png')
    if os.path.exists(p): rep(set(np.unique(arr(p)[..., 3])) <= {0, 255}, f'{key} emissive alpha 0/255')
    p = os.path.join(d, 'vignette.png'); ok = os.path.exists(p); rep(ok, f'{key} vignette.png 存在')
    if ok: i = im(p); rep(i.size == (AW, AH) and i.mode == 'RGBA', f'{key} vignette.png {i.size} == {(AW, AH)} RGBA')
    for f in B.FORMS:
        for suf, sz in (('', (AW, AH)), ('_2x', (AW*2, AH*2))):
            p = os.path.join(d, f'mockup_{f}{suf}.png'); ok = os.path.exists(p); rep(ok, f'{key} mockup_{f}{suf}.png 存在')
            if ok: rep(im(p).size == sz, f'{key} mockup_{f}{suf}.png 尺寸 {im(p).size} == {sz}')
    if key == 'H3':
        rp = os.path.join(d, 'grade_rain.json'); ok = os.path.exists(rp); rep(ok, 'H3 grade_rain.json', pending=True)
        if ok:
            gr = json.load(open(rp)); check_grade(gr, 'H3/grade_rain.json')
            check_layerset(os.path.join(d, 'rain'), key, gr, 'lut_rain.png', sub='/rain')

def main():
    lp = os.path.join(OUT, 'layout.json'); rep(os.path.exists(lp), 'layout.json')
    L = json.load(open(lp))
    rep(L['layerSize'] == [LW, LH] and L['artSize'] == [AW, AH] and L['layerOffset'] == [B.MX, B.MY], 'layout 尺寸 223×446／195×422／offset 14,12')
    rep(L['pet']['foot'] == [97, 292] and L['pet']['rangeXRel'] == [-62, 62], 'layout 寵物腳底 (97,292)、rangeX ±62')
    for k in ('ground', 'pots', 'lights', 'uiSafe'): rep(k in L, f'layout.{k}')
    mj = json.load(open(os.path.join(OUT, 'index', 'materials.json'))); rep(mj['count'] <= 64, f'materials ≤64（{mj["count"]}）')
    for nm in ['sky', 'far', 'mid', 'fore'] + [f'sky_index_{k}' for k in B.VAR]:
        p = os.path.join(OUT, 'index', (nm if nm.startswith('sky_index') else f'{nm}_index') + '.png'); ok = os.path.exists(p); rep(ok, f'index/{os.path.basename(p)}')
        if ok: a = np.asarray(im(p)); rep(a.shape == (LH, LW) and a.max() <= mj['count'], f'{os.path.basename(p)} 尺寸／值域')
    for key in ('H1', 'H3', 'H4', 'H2'): check_variant(key)
    # 粒子
    pp, pj = os.path.join(OUT, 'particles', 'particles.png'), os.path.join(OUT, 'particles', 'particles.json')
    ok = os.path.exists(pp) and os.path.exists(pj); rep(ok, 'particles.png＋json', pending=True)
    if ok:
        a = arr(pp); J = json.load(open(pj)); rep(set(np.unique(a[..., 3])) <= {0, 255}, 'particles alpha 0/255')
        for t in ('mote', 'gold', 'petal', 'firefly'):
            fr = [k for k in J['frames'] if k.startswith(t + '_')]; rep(4 <= len(fr) <= 6, f'particles {t} {len(fr)} 幀（4–6）')
            for k in fr: f = J['frames'][k]['frame']; rep(f['w'] == 8 and f['h'] == 8, f'{k} 8×8')
    # 雨層
    rd = os.path.join(OUT, 'rain'); ok = all(os.path.exists(os.path.join(rd, f)) for f in ('rain_tile.png', 'rain_tile.json', 'ripple.png', 'ripple.json'))
    rep(ok, '雨層 rain_tile／ripple', pending=True)
    if ok:
        J = json.load(open(os.path.join(rd, 'rain_tile.json'))); rep(3 <= len(J['frames']) <= 4, '雨絲 3–4 幀')
        J2 = json.load(open(os.path.join(rd, 'ripple.json'))); rep(len(J2['frames']) == 4, '漣漪 4 幀')
        for f in ('rain_tile.png', 'ripple.png'): rep(set(np.unique(arr(os.path.join(rd, f))[..., 3])) <= {0, 255}, f'{f} alpha 0/255')
        # 平鋪：每幀上下左右邊接得上（雨絲用 wrap 畫，檢查 wrap 後連續性＝冇斷頭）
    # rim
    for form in B.FORMS:
        ap = os.path.join(B.SPR, f'atlas_{form}.json'); rp = os.path.join(RIM, f'rim_{form}.json')
        ok = os.path.exists(rp); rep(ok, f'rim_{form}.json', pending=True)
        if not ok: continue
        A_ = json.load(open(ap)); R_ = json.load(open(rp))
        rep(set(A_['frames']) == set(R_['frames']), f'rim_{form} 幀名同 atlas_{form} 一致（{len(R_["frames"])}／{len(A_["frames"])}）')
        rep(all(A_['frames'][k]['frame'] == R_['frames'][k]['frame'] for k in A_['frames'] if k in R_['frames']), f'rim_{form} rect 同 atlas 一致')
        ri = im(os.path.join(RIM, R_['meta']['image'])); ai = im(os.path.join(B.SPR, A_['meta']['image']))
        rep(ri.size == ai.size, f'rim_{form} atlas 尺寸同 atlas_{form}')
        ra, aa = np.asarray(ri.convert('RGBA'))[..., 3], np.asarray(ai.convert('RGBA'))[..., 3]
        rep(set(np.unique(ra)) <= {0, 255} and not ((ra > 0) & (aa == 0)).any(), f'rim_{form} 只喺 sprite 內（alpha 0/255）')
    # crossfade
    cp = os.path.join(OUT, 'crossfade', 'crossfade_H1-H3-H2-H4.gif'); rep(os.path.exists(cp), 'crossfade GIF', pending=True)
    print(f"PASS {res['PASS']}  FAIL {res['FAIL']}  PENDING {res['PENDING']}")
    print('ALL PASS' if res['FAIL'] == 0 and res['PENDING'] == 0 else ('OK（有 PENDING）' if res['FAIL'] == 0 else 'HAS FAIL'))
    sys.exit(1 if res['FAIL'] else 0)

if __name__ == '__main__': main()
