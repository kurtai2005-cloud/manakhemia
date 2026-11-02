"""build_petglow_v3 — 第 3 批：寵物逐形態逐幀光源 v3 ＋ H2 寵物光池加強 ＋ H3 天氣 V3。
只用 Pillow／numpy（＋scipy.ndimage 做連通區）。無 AI 圖。
輸出：
  sprites/tuanrong/petglow_v3/<form>.json      逐幀 anchor（@3x，相對 pivotPx）＋ clipGlow（瞓覺關光）＋ 光池／粒子
  sprites/tuanrong/petglow_v3/<form>_glow@3x.png/.json  光暈（真 alpha）＋ 光點粒子（alpha 0/255）
  scenes/hd2d_v3/H3/{rain,overcast,fog}/…＋ H3/grade_{rain,overcast,fog}.json
用法：python3 build_petglow_v3.py [forms weather garden preview]
"""
import os, sys, json, math, copy, glob
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import build_garden_hd2d_v3 as G
B = G.B
ART = G.ART; EVO = f'{ART}/sprites/tuanrong/evo6'; OUT = f'{ART}/sprites/tuanrong/petglow_v3'
SC = f'{ART}/scenes/hd2d_v3'; S = 3
hx = B.hx
def to8(a): return (np.clip(a, 0, 1) * 255 + .5).astype(np.uint8)
def save(a, p): os.makedirs(os.path.dirname(p), exist_ok=True); Image.fromarray(to8(a), 'RGBA' if a.shape[-1] == 4 else 'RGB').save(p, optimize=True)
def up3(a): return np.repeat(np.repeat(a, S, 0), S, 1)
def jdump(o, p, compact=False):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w') as f:
        if compact: json.dump(o, f, ensure_ascii=False, separators=(',', ':'))
        else: json.dump(o, f, ensure_ascii=False, indent=1)

# ================================================================ ① 邊啲形態有光源
# evo6 有 emissive 嘅形態：守夜者 9 款＋靜光 9 款（emissiveColors）＋光卵（成隻發光）＋絨跳（第一粒燈芽）。
# 絨點（1px 眼高光）同絨芽（0px）唔算光源。
LIGHT_FORMS = ['evo_egg', 'evo_hop'] + [f'evo_{s}_{b}' for s in ('guard', 'still') for b in ('radiant', 'soft', 'dust', 'ember', 'lumi', 'moon', 'crystal', 'shroom', 'tide')]
NOT_LIGHT = {'evo_dot': '只有 1px 眼高光，唔係光源', 'evo_sprout': '冇 emissive'}
# 每個分支：顏色名（palette）、粒子形、閃爍
STYLE = {
 'base':    dict(core='glow_core', mid='glow_mid', outer='glow', part='mote', flicker=dict(type='breathe', hz=.35, amp=.10), note='暖金柔光'),
 'radiant': dict(core='glow_core', mid='glow_mid', outer='glow', part='mote', flicker=dict(type='breathe', hz=.4, amp=.12), note='燦光：金色大光暈＋光塵'),
 'soft':    dict(core='glow_core', mid='glow_mid', outer='glow_warm', part='mote', flicker=dict(type='breathe', hz=.25, amp=.08), note='柔光：細、暖、慢呼吸'),
 'dust':    dict(core='glow_core', mid='glow_mid', outer='glow', part='mote', flicker=dict(type='twinkle', hz=1.2, amp=.18), note='微塵：細光點閃'),
 'ember':   dict(core='flame_gc', mid='flame_gm', outer='flame_g', part='ember', flicker=dict(type='flame', hz=9, amp=.16), note='火苗：火光亂閃＋火星上升'),
 'lumi':    dict(core='fly_core', mid='fly', outer='fly_d', part='fly', flicker=dict(type='blink', hz=.7, amp=.35), note='螢絨：螢光一明一暗＋螢火'),
 'moon':    dict(core='moon_gc', mid='moon_gm', outer='moon_g', part='star', flicker=dict(type='breathe', hz=.2, amp=.08), note='月眠：月白柔光＋星點閃'),
 'crystal': dict(core='prism_gc', mid='prism_gm', outer='prism_g', part='prism', flicker=dict(type='glint', hz=.5, amp=.25), note='晶角：稜光＋星芒閃（加 fx flare）'),
 'shroom':  dict(core='myco_gc', mid='myco_gm', outer='myco_g', part='spore', flicker=dict(type='breathe', hz=.3, amp=.12), note='菇傘：菌光＋孢子慢飄'),
 'tide':    dict(core='drop_gc', mid='drop_gm', outer='drop_g', part='drop', flicker=dict(type='shimmer', hz=1.5, amp=.10), note='水珠：水光閃＋水珠反光'),
}
EMIT = {   # 粒子 emitter（@3x；由 anchor 加權抽位生）
 'mote':  dict(rate=1.2, max=6, life=[1.6, 2.6], vx3=[-6, 6], vy3=[-14, -6], spread3=18),
 'ember': dict(rate=2.5, max=8, life=[.7, 1.3], vx3=[-6, 6], vy3=[-40, -22], spread3=9),
 'fly':   dict(rate=.6, max=4, life=[3, 5], vx3=[-12, 12], vy3=[-9, 6], spread3=30, blink=True),
 'star':  dict(rate=.8, max=5, life=[1.2, 2.0], vx3=[0, 0], vy3=[-3, 0], spread3=30),
 'prism': dict(rate=.7, max=4, life=[.8, 1.4], vx3=[0, 0], vy3=[0, 0], spread3=21, flare='fx_glow_v3@3x#flare_s_01..06'),
 'spore': dict(rate=1.0, max=7, life=[2.5, 4.0], vx3=[-5, 5], vy3=[-10, -4], spread3=24),
 'drop':  dict(rate=.6, max=3, life=[.8, 1.2], vx3=[0, 0], vy3=[6, 14], spread3=12),
}
SCENE_SCALE = {'H1': .55, 'H3': .45, 'H2': .9, 'H4': 1.0}    # 光暈／粒子喺唔同時段嘅可見度（日頭淡、夜晚全開）
CLIP_GLOW = {   # Kurt：「除左佢訓就會關」— 跟 layout_hd2d_v3.json petGlow
 'fall_asleep': dict(state='sleepClip', fadeOut=dict(ms=600, ease='easeInQuad', at='frame1'), value=0.0),
 'sleep_loop': dict(state='sleep', value=0.0),
 'wake': dict(state='sleep', value=0.0, fadeIn=dict(ms=400, ease='easeOutQuad', at='lastFrame', pulse=dict(ms=150, scale=[1, 1.15, 1]))),
 'yawn': dict(state='sleepy', value=.6), 'emo_sleepy': dict(state='sleepy', value=.6),
}

def palette(meta):
    d = json.load(open(f"{EVO}/{meta.get('palette', 'palette_base.json')}")); c = {x['name']: x['hex'] for x in d['colors']}
    base = {x['name']: x['hex'] for x in json.load(open(f'{EVO}/palette_base.json'))['colors']}
    return lambda n: c.get(n) or base.get(n) or '#FFF4C0'
def branch(meta): return meta.get('branch') or 'base'

# ================================================================ ② 每形態 sprite（@3x）
def radial(sz, cols, stops, p=1.0):
    yy, xx = np.mgrid[0:sz, 0:sz]; r = np.hypot(xx - sz / 2 + .5, yy - sz / 2 + .5) / (sz / 2)
    o = np.zeros((sz, sz, 4)); C = [hx(c) for c in cols]
    w0 = np.clip(1 - r / stops[0], 0, 1); w1 = np.clip(1 - r / stops[1], 0, 1)
    rgb = C[2][None, None] * (1 - w1[..., None]) + C[1] * w1[..., None]; rgb = rgb * (1 - w0[..., None]) + C[0] * w0[..., None]
    a = np.clip(1 - r, 0, 1) ** (1.6 * p) * .85 + np.exp(-(r / .18) ** 2) * .4
    o[..., :3] = rgb; o[..., 3] = np.clip(a, 0, 1); return o
PIX = {   # 1x 7×7 像素圖（c=core, m=mid, o=outer）
 'mote':  ["...", ".c.", "..."], 'mote2': [".m.", "mcm", ".m."], 'mote3': ["..m..", ".mcm.", "mcccm", ".mcm.", "..m.."],
 'star1': [".c.", "ccc", ".c."], 'star2': ["..c..", "..c..", "ccccc", "..c..", "..c.."], 'star3': ["...m...", "...c...", "..mcm..", "mcccccm", "..mcm..", "...c...", "...m..."],
 'ember1': ["c", "m"], 'ember2': [".c.", ".c.", "mmm", ".o."], 'ember3': ["c", "m", "o"],
 'fly1': ["cm", "m."], 'fly2': [".m.", "mcm", ".m."], 'fly3': ["o."],
 'prism1': [".c.", "cmc", ".c."], 'prism2': ["..c..", ".cmc.", "cmomc", ".cmc.", "..c.."],
 'spore1': [".m.", "mcm", ".m."], 'spore2': ["mm", "mm"], 'spore3': ["m"],
 'drop1': [".c.", "cmc", "mmm", ".m."], 'drop2': ["c", "m"],
}
PSEQ = {'mote': ['mote', 'mote2', 'mote3', 'mote2'], 'star': ['star1', 'star2', 'star3', 'star2'], 'ember': ['ember2', 'ember1', 'ember3', 'ember1'],
        'fly': ['fly2', 'fly1', 'fly2', 'fly3'], 'prism': ['prism1', 'prism2', 'prism1', 'mote'], 'spore': ['spore1', 'spore2', 'spore1', 'spore3'], 'drop': ['drop1', 'drop2', 'drop1', 'mote']}
def pix(name, cols):
    rows = PIX[name]; h, w = len(rows), len(rows[0]); a = np.zeros((7, 7, 4)); oy, ox = (7 - h) // 2, (7 - w) // 2
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch != '.': a[oy + y, ox + x, :3] = hx(cols[{'c': 0, 'm': 1, 'o': 2}[ch]]); a[oy + y, ox + x, 3] = 1
    return up3(a)
def form_sheet(form, cols, part):
    fr = {'halo_s': radial(36, cols, (.25, .6)), 'halo_m': radial(60, cols, (.2, .55)), 'halo_l': radial(96, cols, (.16, .5), p=1.2),
          'core_12': radial(12, [cols[0], cols[0], cols[1]], (.5, .9), p=.7)}
    for i, n in enumerate(PSEQ[part]): fr[f'{part}_{i + 1:02d}'] = pix(n, cols)
    return G.pack(fr, f'{OUT}/{form}_glow@3x', f'{form} 光源 sprite @3x：halo_* 光暈＋core_12（真 alpha，已上色，lighter）；{part}_01..04 光點粒子（alpha 0/255，source-over＋可 lighter 疊 halo_s）')

# ================================================================ ③ 逐幀 anchor
def frame_anchors(E, f, pv):
    x, y, w, h = f['x'], f['y'], f['w'], f['h']; m = E[y:y + h, x:x + w, 3] > 0
    if not m.any(): return 0, []
    lab, n = ndimage.label(ndimage.binary_dilation(m, iterations=1), structure=np.ones((3, 3)))
    out = []
    for i in range(1, n + 1):
        mk = (lab == i) & m; c = int(mk.sum())
        if not c: continue
        yy, xx = np.nonzero(mk); cx, cy = xx.mean() + .5, yy.mean() + .5
        r = math.sqrt(c / math.pi)
        out.append([round((cx - pv[0]) * S), round((cy - pv[1]) * S), round(max(6, (r * 2.2 + 3) * S)), c])
    out.sort(key=lambda a: -a[3])
    if len(out) > 8:   # 細點合併入最近大點
        for a in out[8:]:
            j = min(range(8), key=lambda k: (out[k][0] - a[0]) ** 2 + (out[k][1] - a[1]) ** 2); out[j][3] += a[3]
        out = out[:8]
    return int(m.sum()), out
def build_form(form):
    d = json.load(open(f'{EVO}/atlas_{form}.json')); meta = d['meta']; E = np.asarray(Image.open(f"{EVO}/{meta['emissive']}").convert('RGBA'))
    br = branch(meta); st = STYLE[br]; P = palette(meta); cols = [P(st['core']), P(st['mid']), P(st['outer'])]
    part = st['part']; pos = form_sheet(form, cols, part)
    anim_frames = []
    for c, a in d['animations'].items():
        for fn in a['frames']:
            if fn not in anim_frames: anim_frames.append(fn)
    raw = {}
    for fn in anim_frames:
        fi = d['frames'][fn]; pv = (fi['pivotPx']['x'], fi['pivotPx']['y']) if 'pivotPx' in fi else tuple(meta['pivotPx'])
        raw[fn] = frame_anchors(E, fi['frame'], pv)
    awake = [raw[f][0] for c, a in d['animations'].items() if c.split('_noface')[0] in ('idle', 'blink', 'walk') for f in a['frames']] or [1]
    ref = max(1, float(np.median(awake)))
    frames, seen = {}, {}
    for fn, (tot, an) in raw.items():
        a3 = [[x, y, r, round(min(1.0, .35 + .05 * math.sqrt(c)), 2)] for x, y, r, c in an]
        key = json.dumps(a3)
        e = round(min(1.25, tot / ref), 2)
        if key in seen and frames[seen[key]]['e'] == e: frames[fn] = dict(same=seen[key]); continue
        seen.setdefault(key, fn); frames[fn] = dict(e=e, a=a3)
    fs = meta['frameSize']; k = fs / 48
    clip_glow = {}
    for c in d['animations']:
        b = c.replace('_noface', '')
        clip_glow[c] = CLIP_GLOW.get(b, dict(state='awake', value=1.0))
    J = dict(form=form, name=meta.get('name'), branch=br, stage=meta.get('stage'), frameSize=fs, scale=S,
             note=st['note'], sheet=f'{form}_glow@3x.json',
             tints=dict(core=cols[0], mid=cols[1], outer=cols[2]),
             anchorRule='a = [dx3, dy3, r3, w]：相對該幀 pivotPx 嘅 @3x 偏移（寵物腳底 ＋ (dx3,dy3)×facing）；r3＝光暈半徑 @3x → halo_s≤24／halo_m≤40／halo_l；w＝強度 0–1。e＝該幀發光量（相對 awake 中位數）。same＝同另一幀一樣。鏡像：dx3 × scaleX。',
             draw=['pool（腳底光池，scene petLight 之後，lightmap 之前，lighter）', 'sprite＋飾品（不變）', 'emissive（sprite 自帶，lighter ×.33 × petGlow）', 'halo（每個 anchor：halo_* tint 已上色，globalAlpha＝w×e×flicker×sceneScale×petGlow，lighter）', 'core_12（最大 anchor，×petGlow）', 'particles（emitter，×petGlow）'],
             flicker=st['flicker'], sceneScale=SCENE_SCALE,
             pool=dict(sprite='scenes/hd2d_v3/fx/fx_glow_v3@3x.json#pet_pool', size3x=[round(240 * (.6 + .4 * k)), round(96 * (.6 + .4 * k))], offset3x=[0, 6],
                       tint=cols[1], mixWithScene=.5, note='同 scene grade.v3.petLight 疊：tint＝form mid 同 scene tint 50/50；intensity＝scene petLight.intensity × sceneScale'),
             emitter=dict(EMIT[part], type=part, frames=[f'{part}_{i:02d}' for i in range(1, 5)], glow='halo_s', glowAlpha=.35),
             petGlow=dict(source='ui/kit_hd2d_v3/layout_hd2d_v3.json#petGlow', multiplies=['pool', 'halo', 'core', 'particles', 'emissive'], spriteUnchanged=True,
                          rule='Kurt：「除左佢訓就會關」— sleep／sleepClip／dreamEnter／dreaming＝0；sleepy .6；fadeOut 600ms easeInQuad；fadeIn 400ms easeOutQuad＋150ms pulse 1→1.15→1；場景燈唔受影響'),
             clipGlow=clip_glow, frames=frames)
    jdump(J, f'{OUT}/{form}.json', compact=True)
    return J, cols, pos

# ================================================================ ④ 花園 grade：petLight 接 form ＋ H2 加強
H2_POOL = dict(intensity=1.0, size3x=[320, 120], postLightmap=.5, bounce=dict(tint='#ffb070', alpha=.24, note='黃昏：寵物身底暖反光（rim 下半 lighter）'))
def patch_garden():
    for key in ('H1', 'H3', 'H2', 'H4'):
        p = f'{SC}/{key}/grade.json'; g = json.load(open(p)); pl = g['v3']['petLight']
        pl['formLight'] = 'sprites/tuanrong/petglow_v3/<form>.json（有光源形態先有；冇就用呢個通用光池）'
        pl['tintMode'] = 'mix(scene tint, form pool.tint, form pool.mixWithScene)'
        pl['rule'] = 'layout_hd2d_v3.json → petGlow：瞓覺／sleepClip／入夢前＝0；淡出 600ms easeInQuad、醒返淡入 400ms＋pulse。場景燈唔受影響。逐形態光暈／光點 anchor 見 petglow_v3（第 3 批）。'
        if key == 'H2': pl.update(intensity=H2_POOL['intensity'], size3x=H2_POOL['size3x'], bounce=H2_POOL['bounce'], postLightmap=H2_POOL['postLightmap'], postLightmapNote='光池嘅一半（×postLightmap）喺 lightmap 之後再 lighter 疊一次，唔俾黃昏暗地食走')
        jdump(g, p)

# ================================================================ ⑤ H3 天氣 V3（rain／overcast／fog）
WX = {
 'rain':     dict(sat=.70, con=.92, tint='#c4d6e4', split=dict(shadow='#3a5a8a', highlight='#dfeaf4', amount=.06), bloom=dict(threshold=.92, intensity=.12), vignette=.22, fogc='#c8d6e0', fogd=.10,
                  lm=.85, add=.25, farFade=.18, haze=(.20, .12), petLight=.3, extra='rain'),
 'overcast': dict(sat=.80, con=.95, tint='#d6dee6', split=dict(shadow='#4a5a7a', highlight='#f0f2f4', amount=.05), bloom=dict(threshold=.94, intensity=.08), vignette=.16, fogc='#d4dce2', fogd=.06,
                  lm=.75, add=.15, farFade=.12, haze=(.18, .08), petLight=.3, extra='overcast'),
 'fog':      dict(sat=.66, con=.88, tint='#e0e8ee', split=dict(shadow='#6a7a90', highlight='#f4f6f6', amount=.04), bloom=dict(threshold=.95, intensity=.06), vignette=.12, fogc='#e2e8ea', fogd=.16,
                  lm=.5, add=.1, farFade=.5, haze=(.42, .26), petLight=.35, extra='fog'),
}
def weather(wx):
    c = WX[wx]; d = f'{SC}/H3'; wd = f'{d}/{wx}'; os.makedirs(f'{wd}/x3', exist_ok=True)
    g0 = json.load(open(f'{d}/grade.json')); v2 = json.load(open(f'{G.SRC}/H3/grade_{wx}.json'))
    g = {k: copy.deepcopy(v) for k, v in g0.items() if k != 'v3'}
    g.update(baseVariant='H3', ambientTint=v2['ambientTint'], petTint=v2['petTint'], rim=v2['rim'], dof=v2['dof'],
             saturation=round(g0['saturation'] * c['sat'], 3), contrast=round(g0['contrast'] * c['con'], 3), bloom=c['bloom'], vignette=c['vignette'],
             fog=dict(color=c['fogc'], density=c['fogd']), splitTone=c['split'])
    g['particles'] = dict(v2['particles'])
    lut = G.make_lut3(g); tint = hx(c['tint'])
    raws = {n: np.asarray(Image.open(f'{d}/raw/{n}.png').convert('RGBA')).astype(float) / 255 for n in ('sky', 'far', 'mid', 'fore')}
    fc = hx(c['fogc'])
    def wxize(n, a):
        a = a.copy(); a[..., :3] = a[..., :3] * tint
        if n == 'far': a[..., :3] = a[..., :3] * (1 - c['farFade']) + fc * c['farFade']
        if n == 'sky':
            l = (a[..., :3] @ np.array([.3, .55, .15]))[..., None]; a[..., :3] = a[..., :3] * .55 + (l * .5 + fc * .5) * .45   # 天空灰白化
        return a
    W = {n: wxize(n, r) for n, r in raws.items()}
    for n, r in W.items(): G.save(B.bake(r, g, n, lut), f'{wd}/{n}.png')
    G.save(lut, f'{wd}/lut_{wx}.png')
    L3 = G.bake3x(W, g, lut)
    for n, a in L3.items(): G.save(a, f'{wd}/x3/{n}@3x.png')
    lm3 = np.asarray(Image.open(f'{d}/x3/lightmap@3x.png').convert('RGB')).astype(float) / 255
    lm3 = 1 - (1 - lm3) * c['lm']; G.save(lm3, f'{wd}/x3/lightmap@3x.png')
    add3 = np.asarray(Image.open(f'{d}/x3/light_add@3x.png').convert('RGB')).astype(float) / 255 * c['add']; G.save(add3, f'{wd}/x3/light_add@3x.png')
    yy = np.mgrid[0:G.H3, 0:G.W3][0].astype(float) / S - G.MY
    far = np.exp(-((yy - 232) / (34 if wx == 'fog' else 22)) ** 2) * c['haze'][0] + (np.clip((300 - yy) / 120, 0, 1) * .18 if wx == 'fog' else 0)
    rnd = np.random.RandomState(31); nn = np.asarray(Image.fromarray(to8(rnd.rand(10, 30))).resize((G.W3, G.H3), Image.BICUBIC)).astype(float) / 255
    mist = np.exp(-((yy - 305) / (26 if wx == 'fog' else 16)) ** 2) * c['haze'][1] * (.6 + .8 * nn)
    def rgba(col, a): o = np.zeros((G.H3, G.W3, 4)); o[..., :3] = col; o[..., 3] = np.clip(a, 0, 1); return o
    G.save(rgba(fc, far), f'{wd}/x3/haze_far@3x.png'); G.save(rgba(G.mix(fc, hx('#ffffff'), .3), mist), f'{wd}/x3/mist@3x.png')
    # bloom：只有高光（冇 emissive 喺日頭）
    comp = L3['sky'][..., :3]
    for n in ('far', 'mid'): comp = comp * (1 - L3[n][..., 3:]) + L3[n][..., :3] * L3[n][..., 3:]
    G.save(G.bloom3(np.zeros((G.H3, G.W3, 4)), np.clip(comp * lm3 + add3, 0, 1), g), f'{wd}/x3/bloom@3x.png')
    G.save(G.vignette3('H3', g), f'{wd}/x3/vignette@3x.png')
    stack = []
    for s in G.STACK:
        s = dict(s)
        if s.get('file'):
            s['file'] = f'{wx}/' + s['file']
            if s.get('fallback1x') in ('sky.png', 'far.png', 'mid.png', 'fore.png'): s['fallback1x'] = f'{wx}/' + s['fallback1x']
        if s['layer'] == 'emissive_flicker': continue
        stack.append(s)
        if s['layer'] == 'far' and wx == 'overcast':
            stack.append(dict(layer='overcast_clouds', file='scenes/hd2d/weather/overcast_clouds.png', scale3x='nearest ×3', blend='source-over', parallax=.15, realtime=True, alpha=.85, drift3x=6, note='沿用 v2 陰天雲層（×3）'))
        if s['layer'] == 'far' and wx == 'fog':
            stack.append(dict(layer='fog_bank_far', file='scenes/hd2d/weather/fog_bank.png#far', scale3x='nearest ×3', blend='source-over', parallax=.35, realtime=True, alpha=.7, drift3x=9))
        if s['layer'] == 'fore' and wx == 'fog':
            stack.insert(len(stack) - 1, dict(layer='fog_bank_near', file='scenes/hd2d/weather/fog_bank.png#near', scale3x='nearest ×3', blend='source-over', parallax=1.0, realtime=True, alpha=.45, drift3x=-18))
        if s['layer'] == 'bloom' and wx == 'rain':
            stack.append(dict(layer='rain', file='scenes/hd2d/rain/rain_tile.png', scale3x='nearest ×3', blend='source-over', realtime=True, alpha=.55, fps=12, note='沿用 v2 雨絲（×3 平鋪）＋ ripple.png 地面水花'))
    flares = [] if wx != 'overcast' else []
    emit = {'rain': [dict(type='ripple', sprite='scenes/hd2d/rain/ripple.json', rect=[10, 300, 185, 380], rate=6, max=10)],
            'overcast': [dict(type='pollen', glow='glow_12', tint='#f0f0e0', rect=[0, 220, 195, 340], rate=.3, life=[5, 7], vy=[-2, 0], sway=3, max=4, add=.2)],
            'fog': []}[wx]
    pl = dict(g0['v3']['petLight']); pl['intensity'] = c['petLight']; pl['tint'] = '#fff4dc'
    g['v3'] = dict(g0['v3'], note=f'H3 {wx} V3：@3x 層喺 H3/{wx}/x3/；lightmap 已按天氣減弱（×{c["lm"]}）；體積光 ×{c["add"]}。晴天轉天氣 crossfade 3s（同 v2）。',
                   stack=stack, flares=flares, emitters=emit, petLight=pl, bloom3x=dict(intensity=c['bloom']['intensity']))
    g['note'] = f'H3 {wx}（V3）最終值；層用 H3/{wx}/*'
    jdump(g, f'{d}/grade_{wx}.json')
    return g

# ================================================================ ⑥ 預覽
def compose_scene(key, wx=None, pet=None, glow=1.0, seed=5, part_seed=3):
    d = f'{SC}/{key}'; base = f'{d}/{wx}' if wx else d
    g = json.load(open(f'{d}/grade_{wx}.json' if wx else f'{d}/grade.json'))
    ld = G.ld; L = {n: ld(f'{base}/x3/{n}@3x.png') for n in ('sky', 'far', 'haze_far', 'mid', 'mist', 'fore')}
    img = L['sky'][..., :3].copy()
    for n in ('far', 'haze_far', 'mid', 'mist'): img = img * (1 - L[n][..., 3:]) + L[n][..., :3] * L[n][..., 3:]
    F = G.fx(); post = []
    if pet:
        img, post = draw_pet(img, key, g, pet, glow, part_seed)
    img = img * (1 - L['fore'][..., 3:]) + L['fore'][..., :3] * L['fore'][..., 3:]
    img = img * ld(f'{base}/x3/lightmap@3x.png')[..., :3] + ld(f'{base}/x3/light_add@3x.png')[..., :3] + ld(f'{base}/x3/bloom@3x.png')[..., :3] * g['bloom']['intensity']
    for fn in post: fn(img)
    rnd = np.random.RandomState(seed)
    for f in g['v3']['flares']:
        sp = F[f"flare_{f['size']}_{1 + int(rnd.randint(0, 6)):02d}"]; G.addsp(img, sp, (f['pos'][0] + G.MX) * S, (f['pos'][1] + G.MY) * S, f['tint'], f['intensity'])
    for e in g['v3']['emitters']:
        if e['type'] == 'ripple' or e['type'] not in ('dust', 'pollen', 'petal', 'gold', 'firefly', 'bokeh'): continue
        for i in range(e['max'] // 2 + 2):
            x, y = (rnd.uniform(e['rect'][0], e['rect'][2]) + G.MX) * S, (rnd.uniform(e['rect'][1], e['rect'][3]) + G.MY) * S
            if pet and abs(x / S - G.MX - 97) < 26 and 240 < y / S - G.MY < 296: continue
            if 'sprite' in e: G.addsp(img, F[e['sprite']], x, y, e['tint'], e['alpha'] * 2.2); continue
            if 'glow' in e: G.addsp(img, F[e['glow']], x, y, e['tint'], e['add'] * .8)
            G.oversp(img, F[f"{e['type']}_{1 + i % 6:02d}"], int(x - 12), int(y - 12))
    if wx == 'rain': img = rain_fx(img)
    if wx == 'fog': img = fogbank_fx(img)
    if wx == 'overcast': img = clouds_fx(img)
    fc = hx(g['fog']['color']); img = img * (1 - g['fog']['density']) + fc * g['fog']['density']
    img = np.clip(img, 0, 1)[G.MY * S:G.MY * S + G.SH3, G.MX * S:G.MX * S + G.SW3]
    vg = ld(f'{base}/x3/vignette@3x.png'); img = img * (1 - vg[..., 3:]) + vg[..., :3] * vg[..., 3:]
    return Image.fromarray(to8(img), 'RGB')
def _tile_over(img, t, alpha, y0=0, x0=0):
    H, W = img.shape[:2]; th, tw = t.shape[:2]
    T = np.tile(t, ((H - y0) // th + 2, W // tw + 2, 1))[:H - y0, x0:x0 + W]; a = T[..., 3:] * alpha
    img[y0:] = img[y0:] * (1 - a) + T[..., :3] * a; return img
def rain_fx(img):
    J = json.load(open(f'{G.SRC}/rain/rain_tile.json')); sh = G.ld(f'{G.SRC}/rain/rain_tile.png'); f = J['frames']['rain_01']['frame']
    t = up3(sh[f['y']:f['y'] + f['h'], f['x']:f['x'] + f['w']]); return _tile_over(img, t, .5)
def fogbank_fx(img):
    sh = G.ld(f'{G.SRC}/weather/fog_bank.png'); h = sh.shape[0] // 2
    for (part, y, a) in ((sh[:h], 200, .7), (sh[h:], 300, .45)):
        t = up3(part); y0 = (y + G.MY) * S; hh = min(t.shape[0], img.shape[0] - y0)
        T = np.tile(t[:hh], (1, img.shape[1] // t.shape[1] + 2, 1))[:, :img.shape[1]]; aa = T[..., 3:] * a
        img[y0:y0 + hh] = img[y0:y0 + hh] * (1 - aa) + T[..., :3] * aa
    return img
def clouds_fx(img):
    t = up3(G.ld(f'{G.SRC}/weather/overcast_clouds.png')); hh = min(t.shape[0], img.shape[0] - 18)
    T = np.tile(t[:hh], (1, img.shape[1] // t.shape[1] + 2, 1))[:, :img.shape[1]]; a = T[..., 3:] * .85
    img[18:18 + hh] = img[18:18 + hh] * (1 - a) + T[..., :3] * a; return img

_AT = {}
def atlas(form):
    if form not in _AT:
        d = json.load(open(f'{EVO}/atlas_{form}.json')); m = d['meta']
        _AT[form] = (d, np.asarray(Image.open(f'{EVO}/{m["image"]}').convert('RGBA')).astype(float) / 255, np.asarray(Image.open(f'{EVO}/{m["emissive"]}').convert('RGBA')).astype(float) / 255)
    return _AT[form]
_PG = {}
def pg(form):
    if form not in _PG:
        J = json.load(open(f'{OUT}/{form}.json')); sj = json.load(open(f'{OUT}/{J["sheet"]}')); sh = G.ld(f'{OUT}/{sj["image"]}')
        _PG[form] = (J, {k: sh[f['y']:f['y'] + f['h'], f['x']:f['x'] + f['w']] for k, f in sj['frames'].items()})
    return _PG[form]
def addc(img, sp, cx, cy, a):   # 已上色 sprite lighter
    h, w = sp.shape[:2]; x0, y0 = int(round(cx - w / 2)), int(round(cy - h / 2))
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(img.shape[1], x0 + w), min(img.shape[0], y0 + h)
    if xa < xb and ya < yb: s = sp[ya - y0:yb - y0, xa - x0:xb - x0]; img[ya:yb, xa:xb] += s[..., :3] * s[..., 3:] * a
def draw_pet(img, key, g, pet, glow, seed):
    form, fn = pet; d, AT, EM = atlas(form); fi = d['frames'][fn]; f = fi['frame']
    pv = (fi['pivotPx']['x'], fi['pivotPx']['y']) if 'pivotPx' in fi else tuple(d['meta']['pivotPx'])
    sp = AT[f['y']:f['y'] + f['h'], f['x']:f['x'] + f['w']].copy(); em = EM[f['y']:f['y'] + f['h'], f['x']:f['x'] + f['w']].copy()
    orig = sp.copy(); tint = hx(g['petTint']) * hx(g['ambientTint']); sp[..., :3] *= tint
    inner, nx, ny = B.rim_from_alpha(sp[..., 3]); dv = np.array(g['rim']['dir'], float); dv /= np.linalg.norm(dv)
    w = np.clip(nx * dv[0] + ny * dv[1], 0, 1) * inner * min(1, g['rim']['intensity'] * 1.15); sp[..., :3] = sp[..., :3] * (1 - w[..., None]) + hx(g['rim']['color']) * w[..., None]
    emk = (em[..., 3] > 0)[..., None] & (orig[..., 3:] > 0)
    if glow > 0: sp[..., :3] = np.where(emk, orig[..., :3] * glow + sp[..., :3] * (1 - glow), sp[..., :3])   # 發光像素醒時唔食 tint；瞓時同身體一樣
    sp3 = up3(sp); emc = up3(np.where(emk, orig[..., :3], 0))
    J, FR = pg(form); ss = J['sceneScale'][key]; cx, cy = (97 + G.MX) * S, (292 + G.MY) * S
    yy, xx = np.mgrid[0:G.H3, 0:G.W3]
    shd = np.exp(-(((xx - cx) / (sp3.shape[1] * .30)) ** 2 + ((yy - cy - 2) / 9) ** 2) ** 2) * .34; img *= 1 - shd[..., None]
    pl = g['v3']['petLight']; pool = G.fx()['pet_pool']
    if tuple(pl.get('size3x', (240, 96))) != (240, 96):
        pool = np.asarray(Image.fromarray(to8(pool)).resize(tuple(pl['size3x']), Image.BICUBIC)).astype(float) / 255
    ptint = G.mix(hx(pl['tint']), hx(J['pool']['tint']), J['pool']['mixWithScene'])
    addc_t = pool.copy(); addc_t[..., :3] = ptint
    addc(img, addc_t, cx, cy + 6, pl['intensity'] * .5 * glow * (1 + ss * .4))
    if key == 'H2' and pl.get('bounce') and glow > 0:   # 黃昏身底暖反光
        b = pl['bounce']; lowm = np.clip((np.arange(sp3.shape[0])[:, None] / sp3.shape[0] - .55) / .45, 0, 1) * up3(inner)
        sp3[..., :3] = np.clip(sp3[..., :3] + hx(b['tint']) * (lowm * b['alpha'] * 2 * glow)[..., None], 0, 1)
    x0, y0 = int(cx - pv[0] * S), int(cy - pv[1] * S); G.oversp(img, sp3, x0, y0)
    def post(I):
        if glow <= 0: return
        if pl.get('postLightmap'): addc(I, addc_t, cx, cy + 6, pl['intensity'] * .5 * glow * pl['postLightmap'])
        h, w = emc.shape[:2]; I[y0:y0 + h, x0:x0 + w] += emc * .33 * glow * (.6 + .4 * ss)
        fd = J['frames'][fn]; fd = J['frames'][fd['same']] if 'same' in fd else fd
        an = fd.get('a', [])
        for i, (dx, dy, r, wt) in enumerate(an):
            hn = 'halo_s' if r <= 24 else 'halo_m' if r <= 40 else 'halo_l'
            addc(I, FR[hn], cx + dx, cy + dy, wt * fd['e'] * ss * glow * .75)
        if an: addc(I, FR['core_12'], cx + an[0][0], cy + an[0][1], .6 * glow * ss)
        em_ = J['emitter']; rnd = np.random.RandomState(seed)
        if an:
            wts = np.array([a[3] for a in an]); wts = wts / wts.sum()
            for k in range(em_['max']):
                a = an[rnd.choice(len(an), p=wts)]; t = rnd.rand()
                px = cx + a[0] + rnd.uniform(-1, 1) * em_['spread3'] + rnd.uniform(*em_['vx3']) * t * 2
                py = cy + a[1] + rnd.uniform(-1, 1) * em_['spread3'] * .6 + rnd.uniform(*em_['vy3']) * t * 2
                addc(I, FR['halo_s'], px, py, em_['glowAlpha'] * ss * glow)
                p = FR[em_['frames'][k % 4]]; h2, w2 = p.shape[:2]; xa, ya = int(px - w2 / 2), int(py - h2 / 2)
                if 0 <= xa and 0 <= ya and xa + w2 < I.shape[1] and ya + h2 < I.shape[0]:
                    m = p[..., 3:] > 0; I[ya:ya + h2, xa:xa + w2] = np.where(m, I[ya:ya + h2, xa:xa + w2] * .3 + p[..., :3] * (.7 + .3 * ss), I[ya:ya + h2, xa:xa + w2])
            if J['branch'] == 'crystal':
                F = G.fx(); addsp_ = G.addsp
                for k in range(2): a = an[k % len(an)]; addsp_(I, F[f'flare_s_0{3 + k}'], cx + a[0] + (k * 2 - 1) * 9, cy + a[1] - 6, J['tints']['mid'], .8 * ss * glow)
    return img, [post]

PREV_FORMS = ['evo_still_ember', 'evo_still_lumi', 'evo_still_moon', 'evo_still_crystal', 'evo_still_radiant', 'evo_still_shroom', 'evo_guard_tide', 'evo_hop']
def font(sz, b=True):
    import ui_hd2d_v3_lib as UL
    return ImageFont.truetype(UL.FONT_SRC['sansb' if b else 'sans'], sz, index=UL.FONT_TTC_INDEX)
def crop_pet(im): return im.crop((97 * S - 150, 292 * S - 225, 97 * S + 150, 292 * S + 75))   # 300×300 @3x
def previews():
    P = f'{OUT}/preview'; os.makedirs(P, exist_ok=True); fb, fs = font(24), font(17, False)
    cols = [('H3', None, 'idle_01', 1.0, 'H3 日・醒'), ('H3', None, 'sleep_loop_01', 0.0, 'H3 日・瞓'), ('H2', None, 'idle_01', 1.0, 'H2 黃昏・醒'),
            ('H4', None, 'idle_01', 1.0, 'H4 夜・醒'), ('H4', None, 'sleep_loop_01', 0.0, 'H4 夜・瞓')]
    cw = 300; sheet = Image.new('RGB', (200 + len(cols) * (cw + 10), 80 + len(PREV_FORMS) * (cw + 10)), (14, 16, 30)); dr = ImageDraw.Draw(sheet)
    dr.text((20, 14), '《微光小圃》寵物光源 v3 — 日／黃昏／夜 × 醒／瞓（瞓覺 petGlow＝0：光暈、光點、光池、自發光全關；場景燈照舊）', font=fb, fill=(255, 236, 184))
    for j, c in enumerate(cols): dr.text((200 + j * (cw + 10), 52), c[4], font=fs, fill=(240, 230, 200))
    for i, form in enumerate(PREV_FORMS):
        J, _ = pg(form); dr.text((16, 80 + i * (cw + 10) + 120), J['name'], font=fs, fill=(240, 230, 200)); dr.text((16, 80 + i * (cw + 10) + 146), form.replace('evo_', ''), font=fs, fill=(170, 170, 190))
        for j, (key, wx, fn, gl, _) in enumerate(cols):
            im = compose_scene(key, wx, (form, fn), gl, part_seed=i * 7 + j)
            sheet.paste(crop_pet(im), (200 + j * (cw + 10), 80 + i * (cw + 10)))
    sheet.save(f'{P}/petglow_grid.png', optimize=True)
    # 全畫面：火苗／螢絨 H4 醒 vs 瞓；H2 黃昏光池前後
    full = []
    for form in ('evo_still_lumi', 'evo_still_ember'):
        a = compose_scene('H4', None, (form, 'idle_01'), 1.0); b = compose_scene('H4', None, (form, 'sleep_loop_01'), 0.0)
        sh = Image.new('RGB', (G.SW3 * 2 + 60, G.SH3 + 80), (14, 16, 30)); d2 = ImageDraw.Draw(sh)
        sh.paste(a, (20, 70)); sh.paste(b, (G.SW3 + 40, 70)); d2.text((20, 14), f'{pg(form)[0]["name"]} H4 夜燈 — 醒（petGlow 1）｜瞓（petGlow 0，場景燈照舊）', font=fb, fill=(255, 236, 184))
        sh.save(f'{P}/H4_{form}_awake_vs_sleep.png', optimize=True); full.append(sh)
    # H2 光池前後
    g = json.load(open(f'{SC}/H2/grade.json')); pl = g['v3']['petLight']; keep = dict(pl)
    old = dict(pl); old.update(intensity=.55, size3x=[240, 96]); old.pop('bounce', None); old.pop('postLightmap', None)
    g['v3']['petLight'] = old; json.dump(g, open(f'{SC}/H2/grade.json', 'w'), ensure_ascii=False, indent=1)
    a = compose_scene('H2', None, ('evo_still_radiant', 'idle_01'), 1.0)
    g['v3']['petLight'] = keep; jdump(g, f'{SC}/H2/grade.json')
    b = compose_scene('H2', None, ('evo_still_radiant', 'idle_01'), 1.0)
    sh = Image.new('RGB', (620 * 2 + 40, 620 + 80), (14, 16, 30)); d2 = ImageDraw.Draw(sh)
    for k, im in enumerate((a, b)): sh.paste(crop_pet(im).resize((600, 600), Image.NEAREST), (20 + k * 630, 70))
    d2.text((20, 14), 'H2 黃昏寵物光池：前（.55，240×96）｜後（1.0，320×120，一半疊喺 lightmap 後＋身底暖反光）', font=fb, fill=(255, 236, 184)); sh.save(f'{P}/H2_pool_before_after.png', optimize=True)
def weather_previews():
    P = f'{SC}/preview'; fb, fs = font(24), font(18, False)
    ims = [('晴（V3）', compose_scene('H3', None, ('evo_still_tide', 'idle_01'), 1.0))]
    for wx, nm in (('rain', '雨'), ('overcast', '陰'), ('fog', '霧')): ims.append((nm, compose_scene('H3', wx, ('evo_still_tide', 'idle_01'), 1.0)))
    sh = Image.new('RGB', (len(ims) * (G.SW3 + 20) + 20, G.SH3 + 100), (14, 16, 30)); dr = ImageDraw.Draw(sh)
    dr.text((20, 12), '《微光小圃》H3 天氣 V3 — 晴｜雨｜陰｜霧', font=fb, fill=(255, 236, 184))
    for i, (nm, im) in enumerate(ims): sh.paste(im, (20 + i * (G.SW3 + 20), 80)); dr.text((20 + i * (G.SW3 + 20), 52), nm, font=fs, fill=(240, 230, 200))
    sh.save(f'{P}/H3_weather_v3.png', optimize=True)
    # 前後（v2 mockup ×3 vs v3）
    sh2 = Image.new('RGB', (3 * (G.SW3 + 20) + 20, 2 * (G.SH3 + 60) + 60), (14, 16, 30)); dr = ImageDraw.Draw(sh2)
    dr.text((20, 12), 'H3 天氣 前（v2 ×3）／後（V3）', font=fb, fill=(255, 236, 184))
    for i, wx in enumerate(('rain', 'overcast', 'fog')):
        p = f'{G.SRC}/H3/{wx}/mockup_{wx}_radiant.png'
        o = Image.open(p).convert('RGB').resize((G.SW3, G.SH3), Image.NEAREST) if os.path.exists(p) else Image.new('RGB', (G.SW3, G.SH3))
        sh2.paste(o, (20 + i * (G.SW3 + 20), 50)); sh2.paste(ims[i + 1][1], (20 + i * (G.SW3 + 20), 50 + G.SH3 + 60))
    sh2.resize((sh2.width // 2, sh2.height // 2), Image.LANCZOS).save(f'{P}/H3_weather_compare.png', optimize=True)

def main():
    what = sys.argv[1:] or ['forms', 'garden', 'weather', 'preview']
    if 'forms' in what:
        idx = []
        for f in LIGHT_FORMS:
            J, cols, pos = build_form(f); n = len(J['frames']); nd = sum(1 for v in J['frames'].values() if 'same' not in v)
            idx.append(dict(form=f, name=J['name'], branch=J['branch'], file=f'{f}.json', sheet=J['sheet'], tints=J['tints'], frames=n, uniqueFrames=nd)); print(f, n, nd)
        jdump(dict(note='第 3 批 寵物光源 v3：有光源／特效嘅形態一覽。冇喺呢度嘅形態（絨點、絨芽）只用花園通用 petLight 光池。', forms=idx, notLight=NOT_LIGHT,
                   sceneScale=SCENE_SCALE, clipGlowDefault=CLIP_GLOW), f'{OUT}/index.json')
    if 'garden' in what: patch_garden(); print('garden petLight patched')
    if 'weather' in what:
        for wx in WX: weather(wx); print('weather', wx)
    if 'preview' in what: previews(); weather_previews(); print('preview ok')
if __name__ == '__main__': main()
