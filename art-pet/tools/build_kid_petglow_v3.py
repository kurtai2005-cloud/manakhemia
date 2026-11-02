#!/usr/bin/env python3
"""《微光小圃》第 5 批：細佬 series2 有光源形態 petglow v3（同第 3 批團絨 petglow 同一 schema）。
來源：sprites/series2/actions/<k>_<clip>.png（48×48 strip，pivot (24,45)）；燈泡錨點＝from_ref/tuned_48/bulb_anchors_48.json＋sprites/series2/forms/tuned.json。
逐幀 anchor：喺每幀搵 idle 第 1 幀燈泡像素色（±9px 搜尋），眼光（glow／glow_angry／star 眼）、熔岩紋（veinPx）跟燈泡位移。
瞓覺關光（Kurt：「除左佢訓就會關」）：sleep clip＝0（入瞓 600ms easeInQuad 淡出；醒返 400ms easeOutQuad＋pulse）。
輸出 sprites/series2/petglow_v3/{<k>.json, <k>_glow@3x.{png,json}, index.json}。用法：python3 build_kid_petglow_v3.py"""
import os, sys, json, math
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import build_petglow_v3 as PG
G = PG.G; B = G.B; hx = B.hx; S = 3
ART = G.ART; S2 = f'{ART}/sprites/series2'; OUT = f'{S2}/petglow_v3'; T48 = f'{ART}/sprites/tuanrong/species_concept/from_ref/tuned_48'
ACT = json.load(open(f'{S2}/actions/actions.json')); TS = json.load(open(f'{S2}/forms/tuned.json'))['creatures']
TR = json.load(open(f'{T48}/tuned.json'))['creatures']; BA = json.load(open(f'{T48}/bulb_anchors_48.json'))['creatures']
PV = tuple(ACT['pivot']); FS = ACT['frameSize']; CLIPS = ['idle'] + [c for c in ACT['clips'] if c != 'idle']
SER = {   # 系列光風格（particle 用第 3 批 PIX／PSEQ）
 'A': dict(part='drop', flicker=dict(type='shimmer', hz=1.5, amp=.10), note='水系：水光閃＋水珠'),
 'B': dict(part='mote', flicker=dict(type='breathe', hz=.35, amp=.12), note='燈系：燈光呼吸＋光塵'),
 'C': dict(part='ember', flicker=dict(type='flame', hz=9, amp=.16), note='火系：火光亂閃＋火星'),
 'D': dict(part='ember', flicker=dict(type='flame', hz=5, amp=.12), note='熔石系：熔岩紋＋暗紅火光'),
 'E': dict(part='ember', flicker=dict(type='flame', hz=7, amp=.14), note='火糰系：暖火光＋火星'),
 'F': dict(part='star', flicker=dict(type='twinkle', hz=1.2, amp=.18), note='星系：星光閃'),
 'G': dict(part='star', flicker=dict(type='breathe', hz=.25, amp=.10), note='夜系：柔星光'),
 'H': dict(part='star', flicker=dict(type='breathe', hz=.2, amp=.08), note='月系：月白柔光＋星點'),
 'S': dict(part='mote', flicker=dict(type='breathe', hz=.35, amp=.10), note='BB：頭頂細光（未定色）')}
EYE_GLOW = {'glow', 'glow_angry', 'star'}
CLIP_GLOW = {c: dict(state='awake', value=1.0) for c in CLIPS}
CLIP_GLOW['sleep'] = dict(state='sleep', value=0.0, fadeOut=dict(ms=600, ease='easeInQuad', at='enter（sleep 第 1 幀前）'),
                          fadeIn=dict(ms=400, ease='easeOutQuad', at='exit（離開 sleep）', pulse=dict(ms=150, scale=[1, 1.15, 1])))
def hexs(c): return '#%02x%02x%02x' % tuple(int(v) for v in np.clip(np.round(np.asarray(c) * 255), 0, 255))
def meta(k):
    if k in TR:
        t = TR[k]; b = BA[k]; return dict(name=t['name'], series=k[0], type=b['type'], bulb=tuple(b['anchor']), tint=b['glowTint'], eyes=t['eyes'], veins=t.get('veinPx', []), stage=ACT['forms'][k]['stage'])
    t = TS[k]; ser = t.get('series', 'S')
    if t['bulbType'] == 'none': return dict(name=t['name'], type='none')
    if 'glowTint' in t: tint = t['glowTint']
    else: tint = hexs(np.mean([hx(BA[f'{ser}{i}']['glowTint']) for i in (1, 2, 3)], 0))
    return dict(name=t['name'], series=ser if k != 'S2' else 'S', type=t['bulbType'], bulb=tuple(t['bulbXY']), tint=tint, eyes=t['eyes'], veins=t.get('veinPx', []), stage=ACT['forms'][k]['stage'])
def tints(t):
    c = hx(t); core = G.mix(c, np.ones(3), .65); outer = np.clip(c * np.array([.92, .82, .78]) ** 1.3, 0, 1)
    if c[2] > c[0]: outer = np.clip(c * np.array([.75, .85, 1.0]), 0, 1)
    return [hexs(core), t, hexs(outer)]
def strip(k, clip):
    a = np.asarray(Image.open(f"{S2}/{ACT['forms'][k][clip]}").convert('RGBA')).astype(float) / 255
    return [a[:, i * FS:(i + 1) * FS] for i in range(a.shape[1] // FS)]
def bulb_cols(fr, bx, by, r=3):
    p = fr[max(0, by - r):by + r + 1, max(0, bx - r):bx + r + 1]; m = p[..., 3] > .5
    if not m.any(): return set()
    c = p[m][:, :3]; l = c @ np.array([.3, .55, .15]); th = max(.62, np.percentile(l, 60))
    return {tuple(np.round(x * 255).astype(int)) for x in c[l >= th]}
def find_bulb(fr, cols, ex, ey, rad=9):
    if not cols: return None
    a8 = np.round(fr[..., :3] * 255).astype(int); m = np.zeros(fr.shape[:2], bool)
    for c in cols: m |= (a8 == np.array(c)).all(-1)
    m &= fr[..., 3] > .5; yy, xx = np.mgrid[0:FS, 0:FS]; m &= (abs(xx - ex) <= rad) & (abs(yy - ey) <= rad)
    if m.sum() < 2: return None
    from scipy import ndimage
    lab, n = ndimage.label(m); best = None
    for i in range(1, n + 1):
        yy_, xx_ = np.nonzero(lab == i); c = (xx_.mean(), yy_.mean()); d = math.hypot(c[0] - ex, c[1] - ey); s = len(xx_)
        sc = s - d * .8
        if best is None or sc > best[0]: best = (sc, c, s)
    return best[1], best[2]
R_TYPE = {'bulb': 3.2, 'own': 5.5, 'star': 3.6}
def build(k):
    m = meta(k); ser = m['series']; st = SER[ser]; cols = tints(m['tint']); part = st['part']
    fr_ = {'halo_s': PG.radial(36, cols, (.25, .6)), 'halo_m': PG.radial(60, cols, (.2, .55)), 'halo_l': PG.radial(96, cols, (.16, .5), p=1.2),
           'core_12': PG.radial(12, [cols[0], cols[0], cols[1]], (.5, .9), p=.7)}
    for i, n in enumerate(PG.PSEQ[part]): fr_[f'{part}_{i + 1:02d}'] = PG.pix(n, cols)
    G.pack(fr_, f'{OUT}/{k}_glow@3x', f'{k} 細佬光源 sprite @3x：halo_* 光暈＋core_12（真 alpha，已上色，lighter）；{part}_01..04 光點粒子（alpha 0/255）')
    idle0 = strip(k, 'idle')[0]; bx, by = m['bulb']; bc = bulb_cols(idle0, bx, by, 2 if m['type'] != 'own' else 3)
    base = find_bulb(idle0, bc, bx, by) or ((bx, by), 9)
    frames, seen, miss = {}, {}, 0
    for clip in CLIPS:
        for i, fr in enumerate(strip(k, clip)):
            fn = f'{clip}_{i + 1:02d}'; hit = find_bulb(fr, bc, base[0][0], base[0][1])
            if hit is None: (cx, cy), e = base[0], .6; miss += clip != 'sleep'
            else: (cx, cy), e = hit[0], round(min(1.2, max(.5, hit[1] / max(1, base[1]))), 2)
            dx, dy = cx - base[0][0], cy - base[0][1]; r = R_TYPE[m['type']]
            an = [[round((cx + .5 - PV[0]) * S), round((cy + .5 - PV[1]) * S), round((r * 2.2 + 3) * S), .9 if m['type'] == 'own' else .8]]
            if clip != 'sleep':
                for ey in m['eyes']:
                    if ey['kind'] in EYE_GLOW: an.append([round((ey['x'] + dx + .5 - PV[0]) * S), round((ey['y'] + dy + .5 - PV[1]) * S), 18, .4])
            if m['veins']:
                v = np.array(m['veins'], float).reshape(-1, 2); 
                for grp in np.array_split(v[np.argsort(v[:, 1])], min(3, len(v))):
                    gx, gy = grp.mean(0); an.append([round((gx + dx + .5 - PV[0]) * S), round((gy + dy + .5 - PV[1]) * S), 24, .35])
            key = json.dumps([an, e])
            if key in seen: frames[fn] = dict(same=seen[key]); continue
            seen[key] = fn; frames[fn] = dict(e=e, a=an[:8])
    J = dict(form=k, name=m['name'], kind='series2_kid', series=ser, stage=m['stage'], lightType=m['type'], frameSize=FS, scale=S, pivotPx=list(PV),
             note=st['note'], sheet=f'{k}_glow@3x.json', tints=dict(core=cols[0], mid=cols[1], outer=cols[2]), sourceTint=m['tint'],
             anchorRule='同第 3 批：a = [dx3, dy3, r3, w] 相對 pivot (24,45) 嘅 @3x 偏移（細佬腳底 ＋ (dx3,dy3)×facing）；r3→halo_s≤24／halo_m≤40／halo_l；e＝該幀發光量。幀名＝<clip>_<nn>（actions.json clip strip）。',
             draw=json.load(open(f'{PG.OUT}/evo_still_lumi.json'))['draw'],
             flicker=st['flicker'], sceneScale=dict(PG.SCENE_SCALE, house=dict(day=.5, night=1.0)),
             pool=dict(sprite='scenes/hd2d_v3/fx/fx_glow_v3@3x.json#pet_pool', size3x=[160, 64], offset3x=[0, 4], tint=cols[1], mixWithScene=.5, note='細佬細隻：光池 2/3 size；intensity＝scene petLight.intensity × .7 × sceneScale'),
             emitter=dict(PG.EMIT[part], type=part, frames=[f'{part}_{i:02d}' for i in range(1, 5)], glow='halo_s', glowAlpha=.3, max=max(2, PG.EMIT[part]['max'] // 2)),
             petGlow=dict(source='ui/kit_hd2d_v3/layout_hd2d_v3.json#petGlow', multiplies=['pool', 'halo', 'core', 'particles'], spriteUnchanged=True,
                          rule='Kurt：「除左佢訓就會關」— 細佬 sleep clip＝0（入瞓 600ms easeInQuad 淡出，醒返 400ms easeOutQuad＋150ms pulse 1→1.15→1）；dreamEnter／dreaming＝0；場景燈唔受影響'),
             clipGlow=CLIP_GLOW, frames=frames, trackMiss=miss)
    PG.jdump(J, f'{OUT}/{k}.json', compact=True)
    return J
def main():
    os.makedirs(OUT, exist_ok=True); L = []; skip = {}
    for k in ACT['forms']:
        m = meta(k)
        if m['type'] == 'none': skip[k] = '冇光源（蛋殼仔）→ 只用場景通用 petLight 光池'; continue
        J = build(k); L.append(dict(form=k, name=J['name'], series=J['series'], stage=J['stage'], lightType=J['lightType'], file=f'{k}.json', sheet=J['sheet'], tints=J['tints'],
                                    frames=len(J['frames']), uniqueFrames=sum('same' not in f for f in J['frames'].values()), trackMiss=J['trackMiss']))
        print(k, J['lightType'], len(J['frames']), 'miss', J['trackMiss'])
    PG.jdump(dict(note='第 5 批：細佬 series2 有光源形態 petglow v3（schema 同 sprites/tuanrong/petglow_v3）。', clips=CLIPS, clipGlow=CLIP_GLOW, forms=L, notLight=skip), f'{OUT}/index.json')
if __name__ == '__main__': main()
