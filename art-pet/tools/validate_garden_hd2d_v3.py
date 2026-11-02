"""validate_garden_hd2d_v3 — 花園 H1–H4 V3-A 光影（第 2 批）驗證。只用 Pillow/numpy。"""
import json, os, sys
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..'))
V3 = os.path.join(ROOT, 'scenes/hd2d_v3'); V2 = os.path.join(ROOT, 'scenes/hd2d')
HS = ('H1', 'H2', 'H3', 'H4')
L1 = ('sky', 'far', 'mid', 'fore', 'lightmap', 'light_add', 'emissive', 'emissive_blur')
L3 = ('sky', 'far', 'mid', 'fore', 'lightmap', 'light_add', 'emissive', 'bloom', 'haze_far', 'mist')
R = []
def chk(name, ok, info=''):
    R.append(dict(check=name, ok=bool(ok), info=str(info))); print(('PASS ' if ok else 'FAIL ') + name + ('' if ok else '  ' + str(info)))
def im(p): return Image.open(os.path.join(V3, p))
def bin_alpha(a): return set(np.unique(np.asarray(a))) <= {0, 255}

miss = [f'{h}/{n}' for h in HS for n in [l + '.png' for l in L1] + ['vignette.png', 'lut.png', 'grade.json', 'palette.json', 'raw/sky.png', 'raw/mid_index.png']
        + [f'x3/{l}@3x.png' for l in L3] + ['x3/vignette@3x.png'] if not os.path.exists(os.path.join(V3, h, n))]
chk('files_exist_H1-H4', not miss, miss[:5])
bad = []
for h in HS:
    for l in L1:
        if im(f'{h}/{l}.png').size != (223, 446): bad.append(f'{h}/{l}')
    if im(f'{h}/vignette.png').size != (195, 422): bad.append(f'{h}/vignette')
    for l in L3:
        if im(f'{h}/x3/{l}@3x.png').size != (669, 1338): bad.append(f'{h}/x3/{l}')
    if im(f'{h}/x3/vignette@3x.png').size != (585, 1266): bad.append(f'{h}/x3/vignette')
chk('sizes_1x_223x446_3x_669x1338_vignette', not bad, bad[:5])
# 層名兼容：v2 每個 1x png 喺 v3 都有
bad = [f'{h}/{f}' for h in HS for f in os.listdir(os.path.join(V2, h)) if f.endswith('.png') and f in [l + '.png' for l in L1] + ['vignette.png', 'lut.png'] and not os.path.exists(os.path.join(V3, h, f))]
chk('layer_names_compat_v2', not bad, bad)
# raw sprite alpha 0/255
bad = []
for h in HS:
    for f in os.listdir(os.path.join(V3, h, 'raw')):
        if f.endswith('.png') and 'index' not in f:
            i = im(f'{h}/raw/{f}')
            if i.mode == 'RGBA' and not bin_alpha(i.getchannel('A')): bad.append(f'{h}/raw/{f}')
chk('raw_sprite_alpha_0_255', not bad, bad)
# raw colours ≤ 96（v3 加咗 11 種新材質）
cnt = {}
for h in HS:
    g = json.load(open(os.path.join(V3, h, 'grade.json'))); cnt[h] = g['v3']['rawColors']
chk('raw_colors_le_96', all(v <= 96 for v in cnt.values()), cnt)
# grade keys
bad = []
for h in HS:
    g2 = json.load(open(os.path.join(V2, h, 'grade.json'))); g = json.load(open(os.path.join(V3, h, 'grade.json')))
    m = [k for k in g2 if k not in g]
    if m: bad.append((h, m))
    v = g.get('v3', {})
    for k in ('stack', 'flares', 'emitters', 'petLight', 'pivot'):
        if k not in v: bad.append((h, k))
chk('grade_keys_v2_plus_v3', not bad, bad)
bad = []
for h in HS:
    v = json.load(open(os.path.join(V3, h, 'grade.json')))['v3']
    for s in v['stack']:
        if 'file' in s and not os.path.exists(os.path.join(V3, h, s['file'])): bad.append((h, s['file']))
        if 'baked' not in s and 'realtime' not in s: bad.append((h, s.get('layer'), 'no baked/realtime flag'))
    if not any(s.get('realtime') for s in v['stack']) or not any(s.get('baked') for s in v['stack']): bad.append((h, 'baked/realtime 未分開'))
chk('stack_files_and_baked_vs_realtime', not bad, bad[:5])
bad = []
for h in HS:
    p = json.load(open(os.path.join(V3, h, 'grade.json')))['v3']['petLight']
    if p.get('multiplyBy') != 'petGlow' or p.get('anchor') != 'foot': bad.append(h)
lay = json.load(open(os.path.join(ROOT, 'ui/kit_hd2d_v3/layout_hd2d_v3.json')))
chk('petLight_multiplyBy_petGlow', not bad and 'petGlow' in json.dumps(lay), bad)
# LUT：raw sky 經 LUT ≈ 1x sky（DoF 前，sky 冇 DoF）
def apply_lut(rgb, lut):
    L = np.asarray(lut.convert('RGB')).astype(np.float32) / 255; n = 16
    c = rgb.astype(np.float32) / 255 * (n - 1); r, g, b = [np.round(c[..., i]).astype(int) for i in range(3)]
    return (L[g, b * n + r] * 255)
err = {}
for h in HS:
    raw = np.asarray(im(f'{h}/raw/sky.png').convert('RGB')); out = np.asarray(im(f'{h}/sky.png').convert('RGB')).astype(np.float32)
    lut = im(f'{h}/lut.png')
    if lut.size == (256, 16):
        e = np.abs(apply_lut(raw, lut) - out).mean(); err[h] = round(float(e), 2)
    else: err[h] = 'lut size ' + str(lut.size)
chk('lut_256x16_matches_sky', all(isinstance(e, float) and e < 12 for e in err.values()), err)
# clearBox 唔好塞新細節：比較 v2 / v3 mid index 喺 clearBox 入面嘅差異
bad = {}
cb = [30, 210, 165, 300]
for h in HS:
    a = np.asarray(Image.open(os.path.join(V2, h, 'raw', 'mid.png')).convert('RGBA'))
    b = np.asarray(im(f'{h}/raw/mid.png').convert('RGBA'))
    sl = (slice(12 + cb[1], 12 + cb[3]), slice(14 + cb[0], 14 + cb[2]))
    d = float((a[sl] != b[sl]).any(-1).mean())
    bad[h] = round(d, 3)
chk('clearBox_new_detail_le_8pct', all(v <= .08 for v in bad.values()), bad)
# fx
bad = []
for n in ('fx_glow_v3@3x', 'particles_v3@3x'):
    d = json.load(open(os.path.join(V3, 'fx', n + '.json'))); I = im('fx/' + n + '.png'); W, H = I.size
    for k, f in d['frames'].items():
        if f['x'] < 0 or f['y'] < 0 or f['x'] + f['w'] > W or f['y'] + f['h'] > H: bad.append(n + ':' + k)
    if n.startswith('particles') and not bin_alpha(I.getchannel('A')): bad.append(n + ' alpha not 0/255')
chk('fx_frames_in_bounds_particles_alpha', not bad, bad[:5])
glow = json.load(open(os.path.join(V3, 'fx', 'fx_glow_v3@3x.json')))['frames']; pt = json.load(open(os.path.join(V3, 'fx', 'particles_v3@3x.json')))['frames']
bad = []
for h in HS:
    v = json.load(open(os.path.join(V3, h, 'grade.json')))['v3']
    for e in v['emitters']:
        if e.get('glow') and e['glow'] not in glow: bad.append((h, e['glow']))
    for f in v['flares']:
        if f'flare_{f["size"]}_06' not in glow: bad.append((h, f['size']))
    if v['petLight']['sprite'].split('#')[1] not in glow: bad.append((h, 'pet_pool'))
chk('fx_refs_resolve', not bad, bad[:5])
need = [f'preview/{h}_v3_3x.png' for h in HS] + [f'preview/{h}_v3_ui_3x.png' for h in HS] + [f'preview/compare_{h}.png' for h in HS] + ['preview/overview.png', 'FORMAT_V3.md']
m = [p for p in need if not os.path.exists(os.path.join(V3, p))]
chk('previews_and_doc_exist', not m, m)
junk = [os.path.join(dp, d) for dp, ds, fs in os.walk(V3) for d in ds if d in ('_backups', '__pycache__')]
junk += [os.path.join(HERE, '__pycache__')] if os.path.isdir(os.path.join(HERE, '__pycache__')) else []
chk('no_backups_pycache', not junk, junk)
ok = all(r['ok'] for r in R)
json.dump(dict(ok=ok, passed=sum(r['ok'] for r in R), total=len(R), checks=R), open(os.path.join(V3, 'validation.json'), 'w'), ensure_ascii=False, indent=1)
print(f'{sum(r["ok"] for r in R)}/{len(R)}', 'OK' if ok else 'FAIL'); sys.exit(0 if ok else 1)
