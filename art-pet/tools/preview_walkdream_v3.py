#!/usr/bin/env python3
"""第 6 批預覽：6b 散步／6c 夢遊 原檔 vs V3-A（前後）＋疊 UI v3（s_walk／s_dream monkeypatch 換 V3 素材）＋夢遊寵物光規則。
輸出：env GD_WALKDREAM_V3 或 <repo>/walkdream_v3；重點圖再 copy 去 art/breakthrough/6b|6c/v3/preview/。"""
import os, sys, json, shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import build_walkdream_v3 as W
REPO = os.path.normpath(os.path.join(HERE, '..', '..')); GD = os.environ.get('GD_WALKDREAM_V3') or os.path.join(REPO, 'walkdream_v3')
BT, O6B, O6C = W.BT, W.O6B, W.O6C; BG = (22, 18, 40)
def font(sz, b=True):
    import ui_hd2d_v3_lib as UL
    return ImageFont.truetype(UL.FONT_SRC['sansb' if b else 'sans'], sz, index=UL.FONT_TTC_INDEX)
def sheet(cells, cols, title, pad=16, lab=34, cell_bg=None):
    """cells：[(label, PIL)]"""
    cw = max(c[1].width for c in cells); ch = max(c[1].height for c in cells); rows = (len(cells) + cols - 1) // cols
    im = Image.new('RGB', (cols * (cw + pad) + pad, 70 + rows * (ch + lab + pad) + pad), BG); d = ImageDraw.Draw(im); d.text((pad, 18), title, font=font(30), fill=(255, 236, 190))
    for i, (t, c) in enumerate(cells):
        x, y = pad + (i % cols) * (cw + pad), 70 + (i // cols) * (ch + lab + pad)
        d.text((x, y), t, font=font(20, False), fill=(220, 214, 255))
        if c.mode == 'RGBA':
            b = Image.new('RGBA', c.size, cell_bg or (40, 32, 78, 255)); b.alpha_composite(c); c = b
        im.paste(c.convert('RGB'), (x, y + lab))
    return im
def up(im, k): return im.resize((im.width * k, im.height * k), Image.NEAREST)
def walk_before(): return Image.open(f'{BT}/6b/walk_bg@3x.png').convert('RGB')
def p_walk():
    cells = [('原檔 walk_bg@3x（6b@a1a6e9a2）', walk_before())]
    for v in W.WV: cells.append((f'V3 {W.WV[v]["zh"]}（{v}）＋A3＋楓葉', W.compose_walk(v, deco=[('deco_maple_leaf', (220, 330))])))
    sheet(cells, 4, '6b 散步 walk_bg：原檔 vs V3-A（300×360 @3x，同尺寸頂替）').save(f'{GD}/walk_before_after.png', optimize=True)
    cells = [(f'{v}', up(Image.open(f'{BT}/6b/walk_bg.png').convert('RGB'), 3) if v == '原 1x×3' else Image.open(f'{O6B}/walk_bg/{v}/lightmap.png').resize((300, 360), Image.NEAREST)) for v in ['原 1x×3']]
    d = f'{O6B}/walk_bg/dusk'
    for n in ('sky', 'far', 'mid', 'fore', 'lightmap', 'light_add', 'bloom', 'emissive', 'haze_far', 'mist', 'vignette'):
        cells.append((f'dusk x3/{n}', Image.open(f'{d}/x3/{n}@3x.png').convert('RGBA')))
    sheet(cells, 6, '6b 散步 V3 層拆解（黃昏）').save(f'{GD}/walk_layers_dusk.png', optimize=True)
    J = json.load(open(f'{O6B}/walk6b_v3.json'))['deco']; cells = []
    for k, v in J.items():
        n = k.split(':')[1]; cells.append((f'{n} 原', up(Image.open(f'{BT}/6b/{n.replace("deco_", "deco/deco_")}@3x.png').convert('RGBA'), 2)))
        g = Image.open(f'{O6B}/{v["glow"]}').convert('RGBA'); b = Image.new('RGBA', (96, 96), (40, 32, 78, 255)); gg = np.asarray(g).astype(float) / 255
        bb = np.asarray(b).astype(float) / 255; bb[12:84, 12:84, :3] += gg[..., :3] * gg[..., 3:] * .6; b = Image.fromarray(W.to8(np.clip(bb, 0, 1)), 'RGBA')
        s = up(Image.open(f'{O6B}/{v["v3"]}').convert('RGBA'), 2); b.alpha_composite(s, (0, 0)); cells.append((f'{n} V3＋glow', b))
    sheet(cells, 8, '6b deco：原 vs V3（rim 烘入、glow 光暈；×2）').save(f'{GD}/deco_before_after.png', optimize=True)
def p_dream():
    a = Image.open(f'{BT}/6c/fx/dream_bg@3x.png').convert('RGB'); b = Image.open(f'{O6C}/dream_bg/dream_bg_v3@3x.png').convert('RGB'); m = W.compose_dream_map(seed=1)
    old = a.copy(); oa = np.asarray(old).astype(float) / 255   # 原檔地圖（原 tile＋原 fog）
    rev = {(0, 0), (1, 0), (1, 1), (2, 1), (1, 2), (0, 3)}; th = ['forest', 'lake', 'toy', 'star']; rnd = np.random.RandomState(1)
    T = {t: W.ld(f'{BT}/6c/tiles/tile_{t}@3x.png') for t in th}; fog = W.ld(f'{BT}/6c/tiles/fog@3x.png')
    for r in range(5):
        for c in range(3):
            x, y = (11 + c * 58) * 3, (64 + r * 58) * 3
            if (c, r) in rev: v = rnd.randint(4); W.over(oa, T[th[(r + c) % 4]][:, v * 168:(v + 1) * 168], x, y)
            else: W.over(oa, fog, x, y)
    old = Image.fromarray(W.to8(oa), 'RGB')
    cells = [('原 dream_bg@3x', a), ('V3 dream_bg（baked）', b), ('原 地圖（tile＋fog）', old), ('V3 地圖（tile glow＋流霧＋寵物冇光）', m)]
    sheet([(t, i.resize((390, 844), Image.LANCZOS)) for t, i in cells], 4, '6c 夢遊 dream_bg／地圖：原檔 vs V3-A（縮細 2/3）').save(f'{GD}/dream_before_after.png', optimize=True)
    m.crop((0, 120, 585, 900)).save(f'{GD}/dream_map_v3_crop.png', optimize=True)
    cells = []
    for t in th:
        cells.append((f'tile_{t} 原', Image.open(f'{BT}/6c/tiles/tile_{t}@3x.png').convert('RGBA')))
        v3 = W.ld(f'{O6C}/tiles/tile_{t}_v3@3x.png'); gl = W.ld(f'{O6C}/tiles/tile_{t}_glow@3x.png'); o = np.zeros_like(v3); o[..., :3] = W.hx('#28204e'); o[..., 3] = 1
        W.over(o, v3, 0, 0); o[..., :3] += gl[..., :3] * gl[..., 3:] * .85
        if t == 'lake': ca = W.ld(f'{O6C}/tiles/tile_lake_caustic@3x.png')[:168]; o[..., :3] += ca[..., :3] * ca[..., 3:]
        cells.append((f'tile_{t} V3＋glow' + ('＋caustic' if t == 'lake' else ''), Image.fromarray(W.to8(np.clip(o, 0, 1)), 'RGBA')))
    sheet(cells, 2, '6c 四套 tileset：原 vs V3（key light、AO、rim、發光細節）').save(f'{GD}/dream_tiles_before_after.png', optimize=True)
    bgc = np.asarray(b).astype(float)[300:468, 200:368] / 255; cells = []
    f0 = W.ld(f'{BT}/6c/tiles/fog@3x.png'); o = bgc.copy(); W.over(o, f0, 0, 0); cells.append(('fog 原', Image.fromarray(W.to8(o), 'RGB')))
    for nm, lab in (('fog_v3', 'fog V3 流動'), ('fog_reveal', '揭開')):
        s = W.ld(f'{O6C}/tiles/{nm}@3x.png')
        for i in range(0, 8, 2 if nm == 'fog_v3' else 1):
            o = bgc.copy(); W.over(o, s[:, i * 168:(i + 1) * 168], 0, 0); cells.append((f'{lab} {i}', Image.fromarray(W.to8(np.clip(o, 0, 1)), 'RGB')))
    sheet(cells, 7, '6c fog：原（75% 棋盤）vs V3 流霧 8 幀＋揭開溶解 8 幀（疊 V3 bg）').save(f'{GD}/dream_fog.png', optimize=True)
    scene = W.compose_walk('night'); sc = scene.resize((1055, 1266), Image.LANCZOS).crop((235, 0, 820, 1266)); cells = []   # 散步夜晚 cover 成全螢幕做底
    for i in (0, 3, 6, 9):
        o = sc.convert('RGBA'); o.alpha_composite(Image.open(f'{BT}/6c/fx/transition_in@3x.png').convert('RGBA').crop((i * 585, 0, (i + 1) * 585, 1266))); cells.append((f'原 幀{i}', o.convert('RGB').resize((293, 633))))
    for i in (0, 3, 6, 9):
        o = sc.convert('RGBA'); o.alpha_composite(Image.open(f'{O6C}/transition/transition_in_v3_{i:02d}@3x.png').convert('RGBA')); cells.append((f'V3 幀{i}', o.convert('RGB').resize((293, 633))))
    sheet(cells, 4, '6c 入夢過場：原（硬邊）vs V3（羽化＋淡紫光邊）').save(f'{GD}/dream_transition.png', optimize=True)
    J = json.load(open(f'{BT}/6c/dream6c.json'))['keys']; ks = [k for k in J if k.startswith('6c:card_')]; cells = []
    for k in ks:
        n = k.split(':')[1]; o = Image.new('RGBA', (180, 132), (30, 24, 60, 255)); o.alpha_composite(Image.open(f'{BT}/6c/cards/{n}@3x.png').convert('RGBA'), (4, 20))
        th_ = J[k].get('theme') or 'back'; g = W.ld(f'{O6C}/cards/card_glow_{th_}@3x.png'); oa = np.asarray(o).astype(float) / 255
        oa[0:132, 66:180, :3] += g[18:150, 0:114, :3] * g[18:150, 0:114, 3:] * .7; o = Image.fromarray(W.to8(np.clip(oa, 0, 1)), 'RGBA')
        o.alpha_composite(Image.open(f'{O6C}/cards/{n}_v3@3x.png'), (92, 12)); cells.append((f'{n} 原 → V3', o))
    sh = W.ld(f'{O6C}/cards/card_shine@3x.png'); c0 = W.ld(f'{O6C}/cards/card_s3_v3@3x.png'); st = np.zeros((108, 84 * 8 + 70, 3)); st[:] = W.hx('#1e183c')
    for i in range(8): o = st[:, i * 94:i * 94 + 84]; W.over(o, c0, 0, 0); o += sh[:, i * 84:(i + 1) * 84, :3] * sh[:, i * 84:(i + 1) * 84, 3:]
    im = sheet(cells, 7, '6c 夢卡 21 張：原 vs V3（金框 spec、窗光 AO、主題光暈）'); s2 = Image.fromarray(W.to8(np.clip(st, 0, 1)), 'RGB')
    o = Image.new('RGB', (im.width, im.height + 160), BG); o.paste(im, (0, 0)); ImageDraw.Draw(o).text((16, im.height + 4), 'card_shine 8 幀（翻卡掃光）', font=font(20, False), fill=(220, 214, 255)); o.paste(s2, (16, im.height + 40))
    o.save(f'{GD}/dream_cards_before_after.png', optimize=True)
def p_ui():
    import build_ui_hd2d_v3_mockups as M3, ui_hd2d_v3_lib as UL
    CN = M3.CN; og, os_, ob, ov = CN.grade, CN.screen, CN.bloom, CN.vignette; OPEN = Image.open
    M3.garden('normal')   # 先 cache 花園（避免 patch 影響佢）
    walk = W.compose_walk('day', fi=2).convert('RGBA'); blank = None
    def fake_open(p, *a, **k):
        p = str(p)
        if p.endswith('6b/walk_bg@3x.png'): return walk.copy()
        if p.endswith('6b/per_pet/A3/walk@3x.png'): im = OPEN(p, *a, **k); return Image.new('RGBA', im.size, (0, 0, 0, 0))   # 寵物已喺 V3 合成入面（含光池）
        if '/6b/deco/deco_' in p: n = os.path.basename(p).replace('@3x.png', ''); return OPEN(f'{O6B}/deco/{n}_v3@3x.png')
        if p.endswith('6c/fx/dream_bg@3x.png'): return OPEN(f'{O6C}/dream_bg/dream_bg_v3@3x.png')
        if p.endswith('6c/cards/card_f3.png'): return OPEN(f'{O6C}/cards/card_f3_v3@3x.png').convert('RGBA').resize((28, 36), Image.BOX)
        return OPEN(p, *a, **k)
    def keep(shape): return lambda f: (lambda a, *x, **k: a if a.shape[:2] in shape else f(a, *x, **k))
    S_ = [(360, 300), (1266, 585)]
    class _Img: pass
    try:
        M3.Image = type('I', (), {k: getattr(Image, k) for k in dir(Image) if not k.startswith('__')}); M3.Image.open = staticmethod(fake_open)
        CN.grade, CN.screen, CN.vignette = keep(S_)(og), keep(S_)(os_), keep(S_)(ov)
        UL.SCREEN[0] = '6b_walk_v3'; a = M3.s_walk(); UL.SCREEN[0] = '6c_dream_v3'; b = M3.s_dream()
    finally:
        M3.Image = Image; CN.grade, CN.screen, CN.bloom, CN.vignette = og, os_, ob, ov
    KM = f'{W.ART}/ui/kit_hd2d_v3/mockups'
    for n, im, lab in (('6b_walk', a, '散步'), ('6c_dream', b, '夢遊')):
        o0 = Image.open(f'{KM}/{n}_3x.png').convert('RGB')
        sheet([('UI v3 原（原 6b/6c 素材）', o0), ('UI v3 ＋ 第 6 批 V3 素材', im.convert('RGB'))], 2, f'{lab}畫面：疊 UI v3（@3x 585×1266）').save(f'{GD}/ui_{n}_v3.png', optimize=True)
        im.convert('RGB').save(f'{GD}/ui_{n}_v3_3x.png', optimize=True)
def p_rule():
    lay = W.LAY; wk = W.compose_walk('night', fi=0); dm = W.compose_dream_map(seed=1).crop((180, 400, 480, 760))
    im = sheet([('散步（醒 petGlow 1）：光池＋形態光', wk), ('夢遊（dreaming petGlow 0）：寵物光熄、月光 rim 照開', dm)], 2,
               f"寵物光規則：awake {lay['states']['awake']}／sleepy {lay['states']['sleepy']}／sleep・dreamEnter・dreaming 0；fadeOut {lay['fadeOut']['ms']}ms、fadeIn {lay['fadeIn']['ms']}ms＋pulse")
    im.save(f'{GD}/petglow_rule_walk_vs_dream.png', optimize=True)
def main():
    os.makedirs(GD, exist_ok=True); p_walk(); print('walk'); p_dream(); print('dream'); p_rule(); print('rule'); p_ui(); print('ui')
    for dst, names in ((f'{O6B}/preview', ('walk_before_after', 'deco_before_after', 'ui_6b_walk_v3')),
                       (f'{O6C}/preview', ('dream_before_after', 'dream_tiles_before_after', 'dream_cards_before_after', 'dream_transition', 'ui_6c_dream_v3'))):
        os.makedirs(dst, exist_ok=True)
        for n in names: shutil.copy(f'{GD}/{n}.png', f'{dst}/{n}.png')
    print('->', GD, sorted(os.listdir(GD)))
if __name__ == '__main__': main()
