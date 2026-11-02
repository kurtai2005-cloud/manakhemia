#!/usr/bin/env python3
"""《微光小圃》第 5 批：H3 四季 16 款（4 季 × H1–H4）轉 V3-A。
做法：季節內容（build_seasons_v2 嘅 spring/summer/autumn/winter 筆觸）重新畫喺 V3 花園 raw（scenes/hd2d_v3/H#/raw，含 V3 新材質）之上，
再用 V3 花園烘焙（build_garden_hd2d_v3：LUT＋split-tone、@3x DoF、葉隙光斑、體積光、bloom、高度霧、vignette）。
季節光：lightmap ＝ V3 H# lightmap × (季節 v2 lightmap ÷ v2 H# lightmap)；體積光 × 季節 lightTint。
輸出 scenes/hd2d_v3/seasons/<season>/<H#>/（同 V3 H# 同一格式）＋ seasons/fx/particles_seasons_v3@3x.{png,json}＋ seasons/seasons_v3.json
用法：python3 build_seasons_v3.py [fx] [spring summer autumn winter | all] [json]"""
import os, sys, json, copy
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import build_garden_hd2d_v3 as G
import build_seasons_v2 as SV
B = G.B; S = 3; LW, LH, MX, MY = G.LW, G.LH, G.MX, G.MY
V3 = G.OUT; V2 = G.SRC; OUTS = f'{V3}/seasons'
SEASONS = ('spring', 'summer', 'autumn', 'winter'); HS = ('H1', 'H2', 'H3', 'H4')
SJ = json.load(open(f'{V2}/seasons/seasons.json'))
hx, to8, save, up3, smooth3 = B.hx, G.to8, G.save, G.up3, G.smooth3
def ld(p): return np.asarray(Image.open(p).convert('RGBA')).astype(float) / 255

# ---------------------------------------------------------------- ① 將 build_seasons_v2 嘅 Ctx 指去 V3 raw／index／色盤
for nm_, ix_ in B.IDX.items():
    if nm_ not in SV.MI: SV.MI[nm_] = list(ix_)
    for i in ix_: SV.NM.setdefault(i, nm_)
def pal3(H): return {c['index']: SV.hx(c['hex']) for c in json.load(open(f'{V3}/{H}/palette.json'))['colors']}
SV.pal = pal3; SV.P1 = pal3('H1')
def idx3(H, nm): return np.asarray(Image.open(f'{V3}/{H}/raw/{nm}_index.png')).astype(int)
def raw3(H, nm): return ld(f'{V3}/{H}/raw/{nm}.png')
_OK1 = {}
def H1OK3():
    if not _OK1:
        ref = np.zeros((256, 3)); [ref.__setitem__(i, c) for i, c in SV.P1.items()]
        for nm in ('sky', 'far', 'mid', 'fore'):
            r, m = raw3('H1', nm), idx3('H1', nm); _OK1[nm] = (np.abs(r[..., :3] - ref[m]).max(-1) < .6 / 255) & (r[..., 3] > .5) & (m > 0)
        _OK1['sky'][:] = False
    return _OK1
SV.H1OK = H1OK3; SV.LUMR = {H: SV._lumr(H) for H in HS}
class Ctx3(SV.Ctx):
    def __init__(s, H):
        s.H = H; s.M, s.P = SV.fit(H); s.L = {}; s.mat = {}; s.off = {}
        ref = np.zeros((256, 3)); [ref.__setitem__(i, c) for i, c in s.P.items()]
        for nm in ('sky', 'far', 'mid', 'fore'):
            raw, m = raw3(H, nm), idx3(H, nm)
            ok = (np.abs(raw[..., :3] - ref[m]).max(-1) < .6 / 255) & (raw[..., 3] > .5) & (m > 0)
            s.off[nm] = np.zeros((LH, LW, 3))
            if H != 'H1':
                xo = ~ok & (raw[..., 3] > .5) & (m > 0) & H1OK3()[nm]; s.off[nm][xo] = raw[xo, :3] - ref[m][xo]; ok |= xo
            s.mat[nm] = np.where(ok, m, 0); s.L[nm] = raw.copy()
# V3 新材質嘅季節處理（v2 季節筆觸冇覆蓋）
def extra(sk, c):
    lv = SV.levels
    if sk == 'autumn':
        for nm in ('mid', 'fore'): lv(c, nm, 'IVY', ['#8a3e1c', '#d2722c'])
    if sk == 'winter':
        for nm in ('mid', 'fore'):
            iv = c.mask(nm, 'IVY'); lv(c, nm, 'IVY', ['#5a5048', '#7c7064'])
            c.put(nm, iv & SV.top_edge(iv, ~iv), '#f4f8ff')
        for nm in ('mid', 'fore'):     # V3 新花：冬天收埋（換成雪點），燈泡／螢火瓶保留
            fl = c.mask(nm, 'FLOWER_B', 'FLOWER_W'); c.put(nm, fl, '#d8e2f0')
    if sk == 'summer':
        for nm in ('mid', 'fore'): lv(c, nm, 'IVY', ['#2f6a2c', '#4fb04a'])
def season_raws(sk, H):
    c = Ctx3(H); SV.SEASON_FN[sk](c); extra(sk, c); out = {}
    for nm in ('sky', 'far', 'mid', 'fore'):
        L = c.L[nm]; a = L[..., 3] > .5; L[..., 3] = a.astype(float); L[~a, :3] = 0; L[..., :3] = SV.q8(L[..., :3]); out[nm] = L
    return out

# ---------------------------------------------------------------- ② 調色：V3 H# grade × 季節（v2 季節 grade 相對 v2 H# grade）
def grade_s(sk, H):
    g = G.grade_v3(H); sg = json.load(open(f'{V2}/seasons/{sk}/{H}/grade.json')); vg = G.VAR[H]['grade']
    for k in ('ambientTint', 'petTint', 'fog', 'rim', 'bulbGlowTint', 'particles'):
        if k in sg: g[k] = copy.deepcopy(sg[k])
    g['saturation'] = round(g['saturation'] * sg['saturation'] / vg['saturation'], 3); g['contrast'] = round(g['contrast'] * sg['contrast'] / vg['contrast'], 3)
    p = SJ['seasons'][sk]['params']; g['seasonParams'] = p
    st = dict(g['splitTone']); st['highlight'] = '#%02x%02x%02x' % tuple(int(v) for v in to8(B.mix(hx(st['highlight']), hx(p['lightTint']), .5)))
    st['shadow'] = '#%02x%02x%02x' % tuple(int(v) for v in to8(B.mix(hx(st['shadow']), hx(p['shadow']) * .55, .3))); g['splitTone'] = st
    if sk == 'winter': g['bloom'] = dict(g['bloom'], threshold=round(min(.92, g['bloom']['threshold'] + .08), 3))   # 雪地唔好爆白
    if (sk, H) in WASH: w = WASH[sk, H]; g['bloom'] = dict(g['bloom'], threshold=round(min(.95, g['bloom']['threshold'] + w['bloomT']), 3), intensity=round(g['bloom']['intensity'] * w['bloomI'], 3))
    return g
def season_ratio(sk, H):
    """季節 v2 lightmap ÷ v2 H# lightmap（平滑、夾 .6–1.6）＝季節光嘅相對變化"""
    a = ld(f'{V2}/seasons/{sk}/{H}/lightmap.png')[..., :3]; b = ld(f'{V2}/{H}/lightmap.png')[..., :3]
    r = np.clip((a + .02) / (b + .02), .6, 1.6); return G.gblur(r, 2)
WASH = {('winter', 'H1'): dict(vol=.55, haze=.55, mist=1.0, bloomT=.06, bloomI=.7)}   # 冬朝雪地＋晨光太白 → 減體積光／霧／bloom
VOLK = {'spring': .9, 'summer': 1.0, 'autumn': .78, 'winter': .7}
DAPK = {'spring': 1.0, 'summer': 1.15, 'autumn': .85, 'winter': .35}   # 冬天禿樹 → 葉隙光斑少

# ---------------------------------------------------------------- ③ 季節粒子 sheet @3x（v2 8px 粒子 ×3 nearest，alpha 0/255）
PGLOW = {'firefly': ('glow_24', '#d8ff90', .9), 'sunmote': ('glow_12', '#fff4c0', .5), 'snow': ('glow_12', '#eef4ff', .25)}
def build_fx():
    d = f'{OUTS}/fx'; os.makedirs(d, exist_ok=True); frames = {}; types = {}; tiles = []
    for sk in SEASONS:
        pj = json.load(open(f'{V2}/seasons/{sk}/particles/particles.json')); sh = Image.open(f'{V2}/seasons/{sk}/particles/sheet.png').convert('RGBA')
        for k, f in pj['frames'].items(): tiles.append((f'{sk}_{k}', sh.crop((f['x'], f['y'], f['x'] + f['w'], f['y'] + f['h'])).resize((f['w'] * S, f['h'] * S), Image.NEAREST)))
        for t in pj['types']:
            t = copy.deepcopy(t); t['anims'] = {v: [f'{sk}_{x}' for x in pj['anims'][v]] for v in t['variants']}
            if t['name'] in PGLOW: g_, c_, a_ = PGLOW[t['name']]; t['glow'] = dict(sprite=f'../../fx/fx_glow_v3@3x.json#{g_}', tint=c_, add=a_, blend='lighter', multiplyBy='scene（唔跟 petGlow）')
            types.setdefault(sk, []).append(t)
    cols = 12; cw = 24; sheet = Image.new('RGBA', (cols * cw, ((len(tiles) + cols - 1) // cols) * cw), (0, 0, 0, 0))
    for i, (k, im) in enumerate(tiles):
        x, y = (i % cols) * cw, (i // cols) * cw; sheet.paste(im, (x, y)); frames[k] = dict(x=x, y=y, w=cw, h=cw)
    a = np.asarray(sheet).copy(); a[..., 3] = np.where(a[..., 3] > 127, 255, 0); a[a[..., 3] == 0] = 0; Image.fromarray(a, 'RGBA').save(f'{d}/particles_seasons_v3@3x.png', optimize=True)
    json.dump(dict(image='particles_seasons_v3@3x.png', cell=cw, pivot=[11.5, 11.5], scale=3, note='季節粒子 V3：v2 季節粒子（8px）×3 nearest；核心 alpha 0/255 source-over，firefly／sunmote／snow 另加 fx_glow_v3 光暈（lighter）。畫喺 fore 之上、vignette 之下；H4 × 0.75。',
                   frames=frames, types=types), open(f'{d}/particles_seasons_v3@3x.json', 'w'), ensure_ascii=False, indent=1)
    print('fx ok', len(frames))
_PF = {}
def pfx():
    if not _PF:
        sh = ld(f'{OUTS}/fx/particles_seasons_v3@3x.png'); js = json.load(open(f'{OUTS}/fx/particles_seasons_v3@3x.json'))
        for k, f in js['frames'].items(): _PF[k] = sh[f['y']:f['y'] + f['h'], f['x']:f['x'] + f['w']]
        _PF['_types'] = js['types']
    return _PF

# ---------------------------------------------------------------- ④ 每款烘焙
def h_emitters(sk, H):
    """V3 花園 H# 嘅即時粒子，按季節取捨（花瓣／花粉淨春天；冬天冇螢火蟲）"""
    out = []
    for e in G.EMIT[H]:
        e = copy.deepcopy(e)
        if e['type'] in ('petal', 'pollen') and sk != 'spring': continue
        if e['type'] == 'firefly' and sk == 'winter': continue
        if e['type'] == 'firefly' and sk == 'autumn': e['max'] = max(4, e['max'] // 2); e['rate'] = round(e['rate'] * .5, 2)
        if sk == 'winter' and e['type'] in ('dust', 'gold'): e['tint'] = '#eef4ff'
        out.append(e)
    return out
def build(sk, H):
    d = f'{OUTS}/{sk}/{H}'; os.makedirs(f'{d}/x3', exist_ok=True); os.makedirs(f'{d}/raw', exist_ok=True)
    raws = season_raws(sk, H); g = grade_s(sk, H); lut = G.make_lut3(g)
    for n, r in raws.items(): save(r, f'{d}/raw/{n}.png')
    L1 = G.bake1x(raws, g, lut)
    for n, a in L1.items(): save(a, f'{d}/{n}.png')
    rat = season_ratio(sk, H); lm = np.clip(ld(f'{V3}/{H}/lightmap.png')[..., :3] * rat, 0, 1)
    add = ld(f'{V3}/{H}/light_add.png')[..., :3] * hx(SJ['seasons'][sk]['params']['lightTint'])
    save(lm, f'{d}/lightmap.png'); save(add, f'{d}/light_add.png')
    # emissive：V3 H# 嘅發光 mask，季節改過色（例如積雪蓋住）嘅格熄
    em = ld(f'{V3}/{H}/emissive.png'); same = np.ones((LH, LW), bool)
    for n in ('sky', 'far', 'mid', 'fore'):
        r0 = raw3(H, n); same &= ~((np.abs(r0 - raws[n]).max(-1) > 1 / 255) & ((r0[..., 3] > .5) | (raws[n][..., 3] > .5)))
    em[~same] = 0; save(em, f'{d}/emissive.png')
    eb = ld(f'{V3}/{H}/emissive_blur.png'); eb[..., :3] *= G.gblur(same.astype(float)[..., None], 2) if em[..., 3].any() else 0; eb[..., 3] = np.clip(eb[..., :3].max(-1) * 0 + eb[..., 3], 0, 1); save(eb, f'{d}/emissive_blur.png')
    yy, xx = np.mgrid[0:G.AH, 0:G.AW].astype(float); dd = ((xx / G.AW - .5) / .5) ** 2 + ((yy / G.AH - .48) / .5) ** 2
    vg = np.zeros((G.AH, G.AW, 4)); vg[..., :3] = hx(G.VAR[H]['vig']); vg[..., 3] = np.clip(np.clip((dd - .35) / .9, 0, 1) ** 1.5 * g['vignette'] * 1.6, 0, 1); save(vg, f'{d}/vignette.png')
    save(lut, f'{d}/lut.png')
    L3_ = G.bake3x(raws, g, lut)
    for n, a in L3_.items(): save(a, f'{d}/x3/{n}@3x.png')
    base3 = smooth3(lm); dap = G.dapple3(H, base3); k = DAPK[sk]; lm3 = np.clip(base3 + (dap - base3) * k, 0, 1); save(lm3, f'{d}/x3/lightmap@3x.png')
    vol = G.volumetric(H) * hx(SJ['seasons'][sk]['params']['lightTint']) * VOLK[sk] * WASH.get((sk, H), {}).get('vol', 1)
    add3 = np.clip(smooth3(add) + vol, 0, 1); save(add3, f'{d}/x3/light_add@3x.png')
    em3 = up3(em); em3o = em3.copy(); em3o[..., 3] = em3[..., 3] > 0; save(em3o, f'{d}/x3/emissive@3x.png')
    comp = L3_['sky'][..., :3]
    for n in ('far', 'mid'): comp = comp * (1 - L3_[n][..., 3:]) + L3_[n][..., :3] * L3_[n][..., 3:]
    comp = np.clip(comp * lm3 + add3, 0, 1); save(G.bloom3(em3, comp, g), f'{d}/x3/bloom@3x.png')
    hz, ms = G.haze3(H, g)
    if sk == 'winter': ms[..., 3] = np.clip(ms[..., 3] * 1.4 * WASH.get((sk, H), {}).get('mist', 1), 0, 1)
    if (sk, H) in WASH: hz[..., 3] *= WASH[sk, H]['haze']
    save(hz, f'{d}/x3/haze_far@3x.png'); save(ms, f'{d}/x3/mist@3x.png'); save(G.vignette3(H, g), f'{d}/x3/vignette@3x.png')
    v3g = json.load(open(f'{V3}/{H}/grade.json'))['v3']
    gj = dict(variant=H, season=sk, name=f"{SJ['seasons'][sk]['name']}・{G.VAR[H]['name']}（V3-A）", hours=G.VAR[H]['hours'], baseVariant=H); gj.update(g)
    pl = copy.deepcopy(v3g['petLight']); pl['tint'] = g['bulbGlowTint']
    gj['v3'] = dict(note=f"V3-A 季節：{SJ['seasons'][sk]['note']}。同 scenes/hd2d_v3/{H} 一樣嘅 @3x 疊層（x3/），季節內容已畫入 raw；天氣規則同 v2（落雨／陰／霧優先，季節只影響 ambientTint／petTint／粒子）。",
                    layerSize3x=v3g['layerSize3x'], screenSize3x=v3g['screenSize3x'], layerOffset3x=v3g['layerOffset3x'], pivot=v3g['pivot'], stack=G.STACK,
                    bloom3x=dict(intensity=g['bloom']['intensity']), flares=G.flare_list(H) if em[..., 3].any() else [], emitters=h_emitters(sk, H),
                    seasonParticles=dict(sheet='../../fx/particles_seasons_v3@3x.json', types=[dict(t, rateScale=t['emitter']['perVariant'][H] * (.75 if H == 'H4' else 1)) for t in pfx()['_types'][sk]],
                                         layer='fore 之上、vignette 之下；唔乘 lightmap（H4 × 0.75）'),
                    petLight=pl, petPop=v3g['petPop'],
                    seasonLight=dict(lightmapRatio='scenes/hd2d/seasons/<s>/<H>/lightmap ÷ scenes/hd2d/<H>/lightmap（已烘入）', lightTint=SJ['seasons'][sk]['params']['lightTint'], volumetricK=round(VOLK[sk] * WASH.get((sk, H), {}).get('vol', 1), 3), dappleK=DAPK[sk]))
    json.dump(gj, open(f'{d}/grade.json', 'w'), ensure_ascii=False, indent=1)
    cols = set()
    for n, L in raws.items():
        a = L[..., 3] > .5; cols |= {tuple(int(x) for x in v) for v in np.unique(to8(L[a][:, :3]), axis=0)}
    json.dump(dict(season=sk, variant=H, usedColors=len(cols), colors=['#%02x%02x%02x' % c for c in sorted(cols)]), open(f'{d}/palette.json', 'w'), indent=0)
    print(sk, H, 'ok colors', len(cols))
def build_json():
    o = dict(version=3, by='第 5 批（V3-A）', base='scenes/hd2d_v3/H#', spec=SJ['spec'], months={k: SJ['seasons'][k]['months'] for k in SEASONS},
             seasons={k: dict(name=SJ['seasons'][k]['name'], dir=f'seasons/{k}/', note=SJ['seasons'][k]['note'], params=SJ['seasons'][k]['params']) for k in SEASONS},
             variants=list(HS), files='seasons/<season>/<H#>/{sky,far,mid,fore,lightmap,light_add,emissive,emissive_blur,vignette,lut}.png＋grade.json＋palette.json＋raw/；x3/{sky,far,haze_far,mid,mist,fore,lightmap,light_add,bloom,emissive,vignette}@3x.png',
             particles='seasons/fx/particles_seasons_v3@3x.{png,json}', weatherRule=SJ['weatherRule'], crossfade=SJ['crossfade'],
             petGlow=dict(source='ui/kit_hd2d_v3/layout_hd2d_v3.json#petGlow', rule='寵物光 × petGlow（瞓覺＝0）；季節燈／螢火蟲／雪光係場景光，唔熄'))
    json.dump(o, open(f'{OUTS}/seasons_v3.json', 'w'), ensure_ascii=False, indent=1)
def main():
    a = sys.argv[1:] or ['fx', 'all', 'json']
    if 'fx' in a: build_fx()
    for sk in SEASONS:
        if sk in a or 'all' in a:
            for H in HS: build(sk, H)
    if 'json' in a: build_json()
if __name__ == '__main__': main()
