#!/usr/bin/env python3
"""build_m2_previews.py — 總覽 sheet、每 clip strip＋GIF、訪客、道具、6 秒 H1 花園穩陣 GIF。"""
import os, sys, json, math, types
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from m1_common import V3, rgba, blit, save_png, load_png, SIZES

def font(sz=14):
    import glob
    cands = [
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc',
    ] + glob.glob('/usr/share/fonts/**/*CJK*Regular*.ttc', recursive=True)
    for p in cands:
        if os.path.isfile(p):
            try:
                return ImageFont.truetype(p, sz, index=0)
            except Exception:
                try:
                    return ImageFont.truetype(p, sz)
                except Exception:
                    pass
    return ImageFont.load_default()

def label(img, text, x, y, fill=V3['cream'], sz=13, shadow=True):
    im = Image.fromarray(img) if isinstance(img, np.ndarray) else img
    arr_in = isinstance(img, np.ndarray)
    d = ImageDraw.Draw(im)
    f = font(sz)
    if shadow:
        d.text((x + 1, y + 1), text, font=f, fill=(20, 16, 28, 200))
    col = fill + ((255,) if len(fill) == 3 else ())
    d.text((x, y), text, font=f, fill=col)
    return np.array(im) if arr_in else im

def _load_clip(root, cid, sz):
    hd = f'{root}/art-pet/sprites/tuanrong/motion/m2'
    idx = json.load(open(f'{hd}/clips.json'))
    stem = os.path.splitext(os.path.basename(idx['atlases'][sz][cid]))[0]
    J = json.load(open(f'{hd}/{stem}.json'))
    atl = load_png(f'{hd}/{stem}.png')
    nrm = load_png(f'{hd}/{stem}_n.png')
    em = load_png(f'{hd}/{stem}_emissive.png')
    frs, ns, es = [], [], []
    cm = idx['clips'][cid]
    for i in range(cm['frames']):
        nm = f'{cid}_{i+1:02d}'
        fr = J['frames'][nm]['frame']
        sl = (slice(fr['y'], fr['y'] + fr['h']), slice(fr['x'], fr['x'] + fr['w']))
        frs.append(atl[sl])
        ns.append(nrm[sl])
        es.append(em[sl])
    pv = tuple(J['pivotPx'])
    return frs, ns, es, pv, cm, J

def overview(root, out):
    hd = f'{root}/art-pet/sprites/tuanrong/motion/m2'
    idx = json.load(open(f'{hd}/clips.json'))
    clips = list(idx['clips'].items())
    cols, cell, pad, header = 6, 96, 12, 44
    rows = (len(clips) + cols - 1) // cols
    # visitor + props row
    vis = json.load(open(f'{root}/art-pet/sprites/visitors/m2/visitors.json'))
    props = json.load(open(f'{root}/art-pet/sprites/props/m2/props.json'))
    extra_h = 160
    W = pad + cols * cell + pad
    H = header + pad + rows * (cell + 22) + extra_h + 80
    im = rgba(H, W)
    im[..., :3] = V3['navy']; im[..., 3] = 255
    im = label(im, 'M2 動作總覽  招牌 idle×6 ＋ 小動作×4 ＋ 投信／指相框（L）＋ 訪客＋道具', 12, 10, V3['goldhi'], 16)
    for i, (cid, cm) in enumerate(clips):
        r, c = divmod(i, cols)
        x, y = pad + c * cell, header + pad + r * (cell + 22)
        bg = rgba(80, 80); bg[..., :3] = V3['navy2']; bg[..., 3] = 255
        blit(im, bg, x, y)
        frs, *_ = _load_clip(root, cid, 'L')
        mid = frs[min(2, len(frs) - 1)]
        blit(im, mid, x + (80 - 64) // 2, y + (80 - 64) // 2)
        im = label(im, cm['zh'], x, y + 80, V3['mute'], 11)
    # visitors
    y0 = header + pad + rows * (cell + 22) + 8
    im = label(im, '訪客招牌（每位 1）', pad, y0, V3['gold'], 14)
    vx = pad
    for it in vis['items']:
        J = json.load(open(f"{root}/art-pet/sprites/visitors/m2/{it['atlas']}"))
        atl = load_png(f"{root}/art-pet/sprites/visitors/m2/{J['meta']['image']}")
        fr = J['frames'][f"{it['clip']}_03"]['frame']
        spr = atl[fr['y']:fr['y'] + fr['h'], fr['x']:fr['x'] + fr['w']]
        blit(im, spr, vx, y0 + 22)
        im = label(im, it['zh'] + '・' + it['clip_zh'], vx, y0 + 22 + 50, V3['mute'], 11)
        vx += 130
    # props
    y1 = y0 + 90
    im = label(im, '道具', pad, y1, V3['gold'], 14)
    px = pad
    for it in props['items']:
        spr = load_png(f"{root}/art-pet/sprites/props/m2/{it['file']}")
        blit(im, np.repeat(np.repeat(spr, 2 if spr.shape[1] <= 32 else 1, 0), 2 if spr.shape[1] <= 32 else 1, 1), px, y1 + 20)
        im = label(im, it['zh'], px, y1 + 20 + 68, V3['mute'], 11)
        px += 90
    save_png(f'{out}/overview_sheet.png', im)
    return f'{out}/overview_sheet.png'

def clip_previews(root, out):
    hd = f'{root}/art-pet/sprites/tuanrong/motion/m2'
    idx = json.load(open(f'{hd}/clips.json'))
    for cid, cm in idx['clips'].items():
        row_imgs = {}
        for sz, szm in SIZES.items():
            frs, *_ = _load_clip(root, cid, sz)
            row_imgs[sz] = frs
        scale, pad, gap, left = 3, 8, 6, 48
        fw = 64 * scale
        W = left + cm['frames'] * (fw + gap) + pad
        H = pad + 3 * (64 * scale + 24) + 28
        sheet = rgba(H, W)
        sheet[..., :3] = (24, 22, 36); sheet[..., 3] = 255
        sheet = label(sheet, f"{cm['zh']}  {cid}  {cm['frames']}f  {cm['fps']}fps  loop={cm['loop']}  radiant ×S/M/L", 8, 4, V3['goldhi'], 14)
        for ri, (sz, szm) in enumerate(SIZES.items()):
            y = 26 + ri * (64 * scale + 24)
            sheet = label(sheet, sz, 8, y + 64 * scale // 2 - 8, V3['cream'], 16)
            for i, fr in enumerate(row_imgs[sz]):
                sc = (64 * scale) // szm['size']
                big = np.repeat(np.repeat(fr, sc, 0), sc, 1)
                blit(sheet, big, left + i * (fw + gap), y)
        save_png(f'{out}/{cid}_strip.png', sheet)
        # GIF
        gw = 16 + 3 * (64 * 2 + 12)
        gh = 64 * 2 + 28
        gif_f = []
        for i in range(cm['frames']):
            arr = rgba(gh, gw)
            arr[..., :3] = (24, 22, 36); arr[..., 3] = 255
            arr = label(arr, f"{cm['zh']}  S / M / L", 8, 4, V3['goldhi'], 13)
            x = 8
            for sz, szm in SIZES.items():
                big = np.repeat(np.repeat(row_imgs[sz][i], 2, 0), 2, 1)
                yy = gh - 8 - big.shape[0]
                blit(arr, big, x, yy)
                x += big.shape[1] + 10
            gif_f.append(Image.fromarray(arr).convert('P', palette=Image.ADAPTIVE, colors=128))
        dur = int(1000 / cm['fps'])
        gif_f[0].save(f'{out}/{cid}.gif', save_all=True, append_images=gif_f[1:],
                      duration=dur, loop=0, optimize=True, disposal=2)
        if os.path.getsize(f'{out}/{cid}.gif') >= 3 * 1024 * 1024:
            raise SystemExit(f'GIF 太大 {cid}')
        print('  preview', cid, flush=True)

def visitor_previews(root, out):
    vis = json.load(open(f'{root}/art-pet/sprites/visitors/m2/visitors.json'))
    for it in vis['items']:
        J = json.load(open(f"{root}/art-pet/sprites/visitors/m2/{it['atlas']}"))
        atl = load_png(f"{root}/art-pet/sprites/visitors/m2/{J['meta']['image']}")
        frs = []
        for i in range(J['frameCount']):
            fr = J['frames'][f"{it['clip']}_{i+1:02d}"]['frame']
            frs.append(atl[fr['y']:fr['y'] + fr['h'], fr['x']:fr['x'] + fr['w']])
        sc, gap, pad = 3, 8, 10
        fw = 48 * sc
        W = pad + J['frameCount'] * (fw + gap) + pad
        H = 48 * sc + 48
        sheet = rgba(H, W)
        sheet[..., :3] = (24, 22, 36); sheet[..., 3] = 255
        sheet = label(sheet, f"{it['zh']}  {it['clip_zh']}  {it['clip']}  6f  {it['fps']}fps  loop", 8, 4, V3['goldhi'], 14)
        for i, fr in enumerate(frs):
            blit(sheet, np.repeat(np.repeat(fr, sc, 0), sc, 1), pad + i * (fw + gap), 28)
        save_png(f'{out}/{it["id"]}_strip.png', sheet)
        gif_f = []
        for fr in frs:
            arr = rgba(48 * 3 + 28, 48 * 3 + 16)
            arr[..., :3] = (24, 22, 36); arr[..., 3] = 255
            arr = label(arr, it['clip_zh'], 8, 4, V3['goldhi'], 13)
            blit(arr, np.repeat(np.repeat(fr, 3, 0), 3, 1), 8, 22)
            gif_f.append(Image.fromarray(arr).convert('P', palette=Image.ADAPTIVE, colors=64))
        gif_f[0].save(f'{out}/{it["id"]}.gif', save_all=True, append_images=gif_f[1:],
                      duration=int(1000 / it['fps']), loop=0, optimize=True, disposal=2)
        print('  visitor preview', it['id'], flush=True)

def _inject_font_lib():
    if 'ui_hd2d_v3_lib' in sys.modules:
        return
    mod = types.ModuleType('ui_hd2d_v3_lib')
    def F(name, sz):
        return font(sz)
    mod.F = F
    sys.modules['ui_hd2d_v3_lib'] = mod

def garden_idle_steady(root, out, fn='garden_idle_steady.gif'):
    """6 秒 H1 穩陣鏡頭，示範性格 idle 同小動作。"""
    _inject_font_lib()
    gtools = '/workspace/glimmer-3d-h1/art-pet/tools'
    sys.path.insert(0, gtools)
    import preview_garden3d as PG
    src = '/workspace/glimmer-3d-h1/art-pet/scenes/garden3d/H1'
    PG.load(src, out=out)
    CJ = PG.CJ
    A = CJ.get('swayAmplitudeDeg', 5); dmp = CJ.get('followDamping', 2.)
    wx, wz = CJ.get('followWeight', [.25, .3])
    ox, oz = CJ.get('followOffset', [-20, 0]); gx, gz = CJ.get('followOrigin', [-110, -40])
    # 寵物喺花園舞台原點附近（H1 pet 喺 0,0；followOrigin 係園內參考點）
    pet_xz = (0.0, 0.0)
    dt, N, W = 0.1, 60, 600
    crop = (0, 190, 600, 590)
    # 時間軸（秒）：活潑 → 叉腰 → 文靜 → 抓頭 → 懶散 → 望天
    seq_def = [
        (0.0, 1.0, 'idle_lively', '招牌·活潑'),
        (1.0, 2.0, 'proud_hips', '叉腰得意'),
        (2.0, 3.2, 'idle_quiet', '招牌·文靜'),
        (3.2, 4.2, 'scratch_head', '抓頭'),
        (4.2, 5.2, 'idle_lazy', '招牌·懶散'),
        (5.2, 6.0, 'look_sky', '望天'),
    ]
    # cache L frames as float 0-1
    cache = {}
    def pet_frame(cid, fi):
        k = (cid, fi)
        if k not in cache:
            frs, ns, es, pv, cm, J = _load_clip(root, cid, 'L')
            i = max(0, min(len(frs) - 1, fi))
            c = frs[i].astype(float) / 255.0
            n = ns[i].astype(float) / 255.0
            e = es[i].astype(float) / 255.0
            cache[k] = (c, n, e, (pv[0] / c.shape[1], pv[1] / c.shape[0]), cm)
        return cache[k]

    tg0 = np.array(CJ['target'], float)
    cx = cz = None
    frames = []
    for f_ in range(N):
        t = f_ * dt
        cid, zh, fi, cm = 'idle_lively', '招牌·活潑', 0, None
        for a, b, cname, zhn in seq_def:
            if a <= t < b or (t >= 5.2 and cname == 'look_sky'):
                cid, zh = cname, zhn
                local = t - a
                # fps from clip
                frs0, ns0, es0, pv0, cm, J = _load_clip(root, cid, 'L')
                if cm['loop']:
                    fi = int(local * cm['fps']) % cm['frames']
                else:
                    fi = min(cm['frames'] - 1, int(local * cm['fps']))
                break
        c, nn, e, pv, cm = pet_frame(cid, fi)
        yw = -A * math.cos(math.pi * f_ / (N - 1))
        x, z = pet_xz
        dx_, dz_ = ox + wx * (x - gx), oz + wz * (z - gz)
        if cx is None:
            cx, cz = dx_, dz_
        else:
            al = 1 - math.exp(-dmp * dt)
            cx += (dx_ - cx) * al; cz += (dz_ - cz) * al
        im = PG.render(yw, W=W, H=844, cam=dict(target=[tg0[0] + cx, tg0[1], tg0[2] + cz]),
                       pet=dict(x=x, z=z, frame=(c, nn, e, pv), flip=False))
        pil = Image.fromarray(im).crop(crop)
        dd = ImageDraw.Draw(pil)
        # use garden's label if available, else ours
        try:
            PG.label(dd, (8, 8), f'日間 穩定鏡 {yw:+.1f}°  {zh}', 18)
        except Exception:
            fnt = font(18)
            bb = dd.textbbox((8, 8), f'日間 穩定鏡 {yw:+.1f}°  {zh}', font=fnt)
            dd.rectangle((bb[0] - 4, bb[1] - 3, bb[2] + 4, bb[3] + 3), fill=(20, 22, 34))
            dd.text((8, 8), f'日間 穩定鏡 {yw:+.1f}°  {zh}', font=fnt, fill=(255, 255, 255))
        frames.append(pil)
        print(f'  garden gif {f_+1}/{N} {zh}', flush=True)
    colors = 96
    big = Image.new('RGB', (frames[0].width, frames[0].height * len(frames[::4])))
    for i_, f in enumerate(frames[::4]):
        big.paste(f, (0, i_ * f.height))
    palimg = big.quantize(colors, method=Image.Quantize.MEDIANCUT)
    pal = [f.quantize(palette=palimg, dither=Image.Dither.NONE) for f in frames]
    path = f'{out}/{fn}'
    pal[0].save(path, save_all=True, append_images=pal[1:], duration=int(dt * 1000), loop=0, optimize=True)
    sz = os.path.getsize(path)
    if sz >= 3 * 1024 * 1024:
        palimg = big.quantize(80, method=Image.Quantize.MEDIANCUT)
        pal = [f.quantize(palette=palimg, dither=Image.Dither.NONE) for f in frames]
        pal[0].save(path, save_all=True, append_images=pal[1:], duration=int(dt * 1000), loop=0, optimize=True)
        sz = os.path.getsize(path)
    if sz >= 3 * 1024 * 1024:
        raise SystemExit(f'garden GIF 太大 {sz}')
    return dict(file=path, frames=N, secs=6.0, bytes=sz, size=frames[0].size)

def build(root, out):
    os.makedirs(out, exist_ok=True)
    overview(root, out)
    clip_previews(root, out)
    visitor_previews(root, out)
    info = garden_idle_steady(root, out)
    print('previews →', out, 'garden', info)
    return info

if __name__ == '__main__':
    root = sys.argv[1] if len(sys.argv) > 1 else '/workspace/m2-actions-src'
    out = sys.argv[2] if len(sys.argv) > 2 else '/workspace/game-design/m2_actions'
    build(root, out)
