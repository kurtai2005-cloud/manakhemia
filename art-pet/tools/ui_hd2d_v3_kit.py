# 《微光小圃》UI kit v3 — atlas／icon／字型子集／portrait_rects／v2→v3 對照 — 遊美 2026-11-02
# 重跑：python3 art-pet/tools/ui_hd2d_v3_kit.py（之後先跑 build_ui_hd2d_v3_mockups.py）
import os, sys, json, shutil, hashlib
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import ui_hd2d_v3_lib as L
import ui_hd2d_v3_icons as I
KIT = L.KIT; V2 = I.V2
def pack(items, maxw=1024, pad=2):
    """shelf pack；items: [(name, img)] → (atlas, frames)"""
    items = sorted(items, key=lambda t: (-t[1].height, t[0])); x = y = sh = 0; pos = {}
    for n, im in items:
        if x + im.width + pad > maxw: x = 0; y += sh + pad; sh = 0
        pos[n] = (x, y); x += im.width + pad; sh = max(sh, im.height)
    A = Image.new('RGBA', (maxw, y + sh)); fr = {}
    for n, im in items:
        A.alpha_composite(im, pos[n]); fr[n] = dict(x=pos[n][0], y=pos[n][1], w=im.width, h=im.height)
    return A, fr
def v2_map(v2names, v3parts, v3icons):
    cm = {'pri': 'amber', 'sec': 'sky', 'green': 'mint', 'rose': 'rose', 'violet': 'violet', 'gold': 'gold'}
    out = {}
    for n in sorted(v2names):
        t = None; why = ''
        if n in v3parts: t = n
        elif n.startswith('acc_thumb_'): t = 'icon:' + n
        elif n.startswith('bar_fill_'):
            _, _, c, h = n.split('_'); t = f"bar_fill_{cm[c]}_{ {'h5': 'h5', 'h6': 'h6', 'h7': 'h8'}[h]}"
        elif n.startswith('bar_tip_'): t = 'bar_tip_amber'; why = '每色一粒光點'
        elif n.startswith('bar_trough_'): t = 'bar_track_' + {'h5': 'h5', 'h6': 'h6', 'h7': 'h8'}[n.split('_')[-1]]
        elif n.startswith('btn16_'): t = 'btn_s_' + n[6:]
        elif n.startswith('med'):
            d = int(''.join(ch for ch in n[3:].split('_')[0])); c = n.split('_')[1]; dd = 36 if d <= 17 else (48 if d <= 22 else 60)
            c3 = {'navy': 'navy', 'paper': 'gold', 'dis': 'navy', 'green': 'sec'}.get(c, c); t = f'med{dd}_{c3}'; why = '按下＝runtime 縮 0.94' if n.endswith('_p') else ''
        elif n.startswith('gem_'): t = 'exp_gem_on'
        elif n.startswith('sparkle_'): t = {'3': 'flare_12', '5': 'flare_20', '7': 'flare_34'}[n.split('_')[1]]
        elif n.startswith('ribbon_') or n.startswith('plaque'): t = 'title_rule'; why = 'v3 唔用絲帶／牌匾，改金線＋菱形'
        elif n.startswith('toggle_knob'): t = 'toggle_knob'
        else:
            t = {'banner_top': 'scrim_top', 'dock_bar': 'dock', 'dock_pillar': 'dock_on', 'panel_navy': 'panel', 'panel_navy_flat': 'panel_flat', 'pill_navy': 'pill_navy',
                 'fx_veil_tile': 'veil', 'fx_veil25_tile': 'veil_light', 'rivet': 'diamond'}.get(n)
        ok = t is not None and (t in v3parts or (t.startswith('icon:') and t[5:] in v3icons))
        out[n] = dict(v3=t, ok=ok, note=why)
    return out
def main():
    for d in ('atlas', 'icons', 'icons/glow', 'portrait', 'fonts', 'mockups'): os.makedirs(f'{KIT}/{d}', exist_ok=True)
    # ---- UI parts atlas
    imgs = {n: d['fn'](*d['size']) for n, d in L.PARTS.items()}
    for n, im in imgs.items(): L.PARTS[n]['size'] = im.size   # 實際尺寸（部份零件有外光邊）
    A3, F3 = pack(list(imgs.items()), 1024)
    meta = {n: dict(slice=L.PARTS[n]['slice'], nine=L.PARTS[n]['nine'], group=L.PARTS[n]['group'], note=L.PARTS[n]['note'], backdrop=L.PARTS[n]['backdrop']) for n in imgs}
    for n in F3: F3[n].update(meta[n]); F3[n]['w'], F3[n]['h'] = imgs[n].size
    A3.save(f'{KIT}/atlas/ui_hd2d_v3@3x.png', optimize=True)
    json.dump(dict(image='ui_hd2d_v3@3x.png', scale=3, size=list(A3.size), mode='9-slice stretch（nine＝[l,t,r,b] @3x px）；backdrop:true＝先畫預烘模糊場景再疊', frames=F3), open(f'{KIT}/atlas/ui_hd2d_v3@3x.json', 'w'), ensure_ascii=False, indent=1)
    im2 = {n: im.resize((max(1, round(im.width * 2 / 3)), max(1, round(im.height * 2 / 3))), Image.LANCZOS) for n, im in imgs.items()}
    A2, F2 = pack(list(im2.items()), 768)
    for n in F2:
        F2[n].update(meta[n]); F2[n]['nine'] = None if meta[n]['nine'] is None else [round(v * 2 / 3) for v in meta[n]['nine']]
    A2.save(f'{KIT}/atlas/ui_hd2d_v3@2x.png', optimize=True)
    json.dump(dict(image='ui_hd2d_v3@2x.png', scale=2, size=list(A2.size), frames=F2), open(f'{KIT}/atlas/ui_hd2d_v3@2x.json', 'w'), ensure_ascii=False, indent=1)
    # ---- icons
    S = I.sources(); v2ui = json.load(open(f'{V2}/atlas/ui_hd2d_v2@1x.json'))['frames']; Av2 = Image.open(f'{V2}/atlas/ui_hd2d_v2@1x.png').convert('RGBA')
    for n, f in v2ui.items():
        if n.startswith('acc_thumb_'): S[n] = Av2.crop((f['x'], f['y'], f['x'] + f['w'], f['y'] + f['h']))
    ic, gl, imeta = {}, {}, {}
    for n, src in S.items():
        sp, g, m = I.enhance(src); ic[n] = sp; gl[n] = g; m['src'] = list(src.size); m['size'] = list(sp.size); imeta[n] = m
        sp.save(f'{KIT}/icons/{n}@3x.png'); g.save(f'{KIT}/icons/glow/{n}_glow@3x.png')
    IA, IF = pack(list(ic.items()), 512)
    for n in IF: IF[n].update(imeta[n])
    IA.save(f'{KIT}/atlas/icons_hd2d_v3@3x.png'); json.dump(dict(image='icons_hd2d_v3@3x.png', scale=3, note='v3 像素 icon，@3x 原生 1:1（16px→32px；mini 11→22；friend_badge 32→64）；alpha 0/255；只可整數倍放大', frames=IF), open(f'{KIT}/atlas/icons_hd2d_v3@3x.json', 'w'), ensure_ascii=False, indent=1)
    I6 = {n: im.resize((im.width * 2, im.height * 2), Image.NEAREST) for n, im in ic.items()}
    IA6, IF6 = pack(list(I6.items()), 1024); IA6.save(f'{KIT}/atlas/icons_hd2d_v3@6x.png'); json.dump(dict(image='icons_hd2d_v3@6x.png', scale=6, note='×2 nearest（大圖示：升級獎勵、分享卡）', frames=IF6), open(f'{KIT}/atlas/icons_hd2d_v3@6x.json', 'w'), ensure_ascii=False, indent=1)
    GA, GF = pack(list(gl.items()), 1024); GA.save(f'{KIT}/atlas/icons_glow_hd2d_v3@3x.png')
    for n in GF: GF[n]['pad'] = imeta[n]['pad']; GF[n]['tint'] = imeta[n]['glow']
    json.dump(dict(image='icons_glow_hd2d_v3@3x.png', scale=3, blend='lighter／screen，alpha 0.0–1.0 動態；sprite 中心對中心', frames=GF), open(f'{KIT}/atlas/icons_glow_hd2d_v3@3x.json', 'w'), ensure_ascii=False, indent=1)
    # ---- portrait_rects（同 v2 一樣；v3 以 k=5 整數倍顯示）
    pr = json.load(open(f'{V2}/portrait/portrait_rects.json')); pr['v3'] = dict(window=L.PORT_D, k=5, rule='window = n·k（n=22 → k=5 → 110px @3x）；飾品 pop 位喺框之上畫；放大一律 nearest 整數倍', frame='portrait_frame（窗口 @6,6）')
    json.dump(pr, open(f'{KIT}/portrait/portrait_rects.json', 'w'), ensure_ascii=False, indent=1)
    if os.path.exists(f'{V2}/PORTRAIT_SYNC.md'): shutil.copy(f'{V2}/PORTRAIT_SYNC.md', f'{KIT}/portrait/PORTRAIT_SYNC.md')
    # ---- v2→v3 對照
    mp = v2_map(list(v2ui), set(L.PARTS), set(ic)); json.dump(dict(note='v2 每個 UI 零件 → v3 名（icon: 前綴＝喺 icons atlas）', map=mp), open(f'{KIT}/atlas/v2_to_v3_map.json', 'w'), ensure_ascii=False, indent=1)
    print('parts', len(imgs), A3.size, 'icons', len(ic), 'v2 map ok', sum(v['ok'] for v in mp.values()), '/', len(mp))
if __name__ == '__main__' and '--fonts' not in sys.argv: main()

# ---------------------------------------------------------------- 字型子集（Noto Sans／Serif CJK TC；OFL 1.1）
def charset():
    import glob
    s = ''
    for p in sorted(glob.glob(f'{L.ROOT}/src/glimmer-a/src/*.js')) + [f'{L.ROOT}/src/glimmer-a/index.html']:
        if os.path.exists(p): s += open(p, encoding='utf-8').read()
    game = set(ch for ch in s if ord(ch) > 0x2e7f)
    tj = f'{KIT}/mockups/texts.json'; mock = set(''.join(t['text'] for t in json.load(open(tj))['texts'])) if os.path.exists(tj) else set()
    base = set(map(chr, range(32, 127))) | set('，。、；：？！「」『』（）《》〈〉…—～・／％＋－×÷→←↑↓★☆♪○●◆◇　０１２３４５６７８９')
    allc = sorted((game | mock | base) - {'\n', '\r', '\t'})
    return ''.join(allc), len(game), len(mock)
def fonts():
    from fontTools import subset
    from fontTools.ttLib import TTCollection
    cs, ng, nm = charset(); os.makedirs(f'{KIT}/fonts', exist_ok=True); open(f'{KIT}/fonts/charset_v3.txt', 'w', encoding='utf-8').write(cs)
    out = {}
    for role, (src, nm_) in {'sans': (L.FONT_SRC['sans'], 'NotoSansCJKtc-Regular.subset.otf'), 'sansb': (L.FONT_SRC['sansb'], 'NotoSansCJKtc-Bold.subset.otf'), 'serif': (L.FONT_SRC['serif'], 'NotoSerifCJKtc-Bold.subset.otf')}.items():
        dst = f'{KIT}/fonts/{nm_}'
        opt = subset.Options(); opt.font_number = L.FONT_TTC_INDEX; opt.layout_features = ['*']; opt.name_IDs = ['*']; opt.name_languages = ['*']; opt.notdef_outline = True; opt.hinting = False
        f = subset.load_font(src, opt); ss = subset.Subsetter(opt); ss.populate(text=cs); ss.subset(f); subset.save_font(f, dst, opt)
        out[role] = dict(file=nm_, bytes=os.path.getsize(dst), source=os.path.basename(src), ttcIndex=L.FONT_TTC_INDEX)
    lic = open('/usr/share/doc/fonts-noto-cjk/copyright', encoding='utf-8').read(); lic = lic[lic.index(' SIL OPEN FONT LICENSE'):]; lic = lic[:lic.index('\nLicense:')] if '\nLicense:' in lic else lic
    lic = '\n'.join(l[1:] if l.startswith(' ') else l for l in lic.splitlines()).replace('\n.\n', '\n\n')
    open(f'{KIT}/fonts/OFL_noto-cjk.txt', 'w', encoding='utf-8').write('Noto Sans CJK / Noto Serif CJK\nhttps://github.com/notofonts/noto-cjk\nCopyright 2014-2021 Adobe (http://www.adobe.com/), with Reserved Font Name \'Source\'.\n（Debian 包：Copyright 2010-2012, Google Corporation）\n\nThis Font Software is licensed under the SIL Open Font License, Version 1.1.\n\n' + lic.strip() + '\n')
    json.dump(dict(note='v3 字：Noto Sans CJK TC Regular／Bold＋Noto Serif CJK TC Bold（只標題）。子集＝遊戲 src 字＋mockup 字＋ASCII＋常用標點。冇 brotli → 出 .otf；上線建議轉 woff2（見 UI_KIT_V3.md）',
                   type={k: dict(font=v[0], px3x=v[1]) for k, v in L.TYPE.items()}, minPx3x=L.MIN_PX, charset=dict(file='charset_v3.txt', count=len(cs), fromGame=ng, fromMockups=nm), fonts=out),
              open(f'{KIT}/fonts/fonts_v3.json', 'w'), ensure_ascii=False, indent=1)
    print('fonts', {k: v['bytes'] for k, v in out.items()}, 'charset', len(cs))
if __name__ == '__main__' and '--fonts' in sys.argv: fonts()
