#!/usr/bin/env python3
"""preview_godot_fx1.py — 將 H1 花園／狩獵套 LUT＋DoF 出對比 sheet，並出粒子 GIF（<3MB）。
預覽唔包入 staging zip。用法：
  PYTHONDONTWRITEBYTECODE=1 python3 art-pet/tools/preview_godot_fx1.py \\
    [--root DIR] [--out /workspace/game-design/godot_fx1] \\
    [--garden-src DIR] [--hunt-root DIR]
"""
import os, sys, json, math, argparse
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fx1_common as C

CROP = (0, 190, 600, 590)  # 同 H1／狩獵穩陣 GIF 600×400
OUT = '/workspace/game-design/godot_fx1'
FONT_PATH = None

def font(sz=16):
    global FONT_PATH
    if FONT_PATH is None:
        import glob
        cands = [
            '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
            '/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc',
        ] + glob.glob('/usr/share/fonts/**/*CJK*Regular*.ttc', recursive=True)
        FONT_PATH = next((p for p in cands if os.path.isfile(p)), None)
    if FONT_PATH:
        try:
            return ImageFont.truetype(FONT_PATH, sz, index=0)
        except Exception:
            try:
                return ImageFont.truetype(FONT_PATH, sz)
            except Exception:
                pass
    return ImageFont.load_default()

def label(d, xy, s, sz=16, fill=(255, 255, 255), bg=(20, 22, 34, 200)):
    f = font(sz)
    b = d.textbbox(xy, s, font=f)
    d.rectangle((b[0] - 3, b[1] - 2, b[2] + 3, b[3] + 2), fill=bg if len(bg) == 3 else bg)
    d.text(xy, s, font=f, fill=fill)

def lum_region(arr, box):
    x0, y0, x1, y1 = box
    sl = arr[y0:y1, x0:x1]
    return float(C.luma(sl.astype(np.float64)).mean())

def crop600(im, depth=None):
    x0, y0, x1, y1 = CROP
    if isinstance(im, np.ndarray):
        rgb = im[y0:y1, x0:x1]
        dep = None if depth is None else depth[y0:y1, x0:x1]
        return rgb, dep
    return np.array(im.crop(CROP)), None

def to_pil(a):
    return Image.fromarray(a)


# ---------- render sources ----------
def _ensure_lib():
    """preview_garden3d 要 ui_hd2d_v3_lib；工作區可能冇，從 branch 抽到 /tmp。"""
    p = '/tmp/h1docs'
    os.makedirs(p, exist_ok=True)
    lib = os.path.join(p, 'ui_hd2d_v3_lib.py')
    if not os.path.isfile(lib):
        for repo in ('/workspace/glimmer-3d-h1', '/workspace/live-s2'):
            if os.path.isdir(os.path.join(repo, '.git')) or os.path.isfile(os.path.join(repo, '.git')):
                import subprocess
                r = subprocess.run(['git', '-C', repo, 'show', 'art/garden3d-h1-mesh:art-pet/tools/ui_hd2d_v3_lib.py'],
                                   capture_output=True)
                if r.returncode == 0 and r.stdout:
                    open(lib, 'wb').write(r.stdout)
                    break
    return p

def render_garden(src, night=False):
    libp = _ensure_lib()
    sys.path.insert(0, libp)
    tools = os.path.join(os.path.dirname(src), '..', '..', 'tools')
    # prefer tools next to scene's art-pet
    art = os.path.abspath(os.path.join(src, '..', '..', '..'))  # .../art-pet
    tdir = os.path.join(art, 'tools')
    if os.path.isdir(tdir):
        sys.path.insert(0, tdir)
    import preview_garden3d as G
    G.ART = art
    G.load(src, out=OUT)
    try:
        fr = G.pet_dir4('front_idle_01')
        pet = dict(x=G.J['pet']['x'], z=G.J['pet']['z'], frame=fr, flip=False, glow=1.0)
    except Exception:
        pet = 'default'
    im, cam = G.render(0, night=night, W=600, H=844, want_depth=True, pet=pet)
    rgb, dep = crop600(im, cam['depth'])
    return rgb, dep, G

def render_hunt(hunt_root):
    tdir = os.path.join(hunt_root, 'art-pet', 'tools')
    sys.path.insert(0, tdir)
    import preview_hunt3d as H
    H.load(hunt_root, out=OUT)
    # patch want_depth
    import inspect
    src = inspect.getsource(H.render)
    if 'want_depth' not in src.split('(')[1].split(')')[0]:
        src = src.replace(
            "def render(yaw, W=600, H=844, cam=None, pet='default', show_critters=True, show_fruits=True):",
            "def render(yaw, W=600, H=844, cam=None, pet='default', show_critters=True, show_fruits=True, want_depth=False):",
        )
        src = src.replace(
            "return (np.clip(col, 0, 1) * 255 + .5).astype(np.uint8)",
            "out = (np.clip(col, 0, 1) * 255 + .5).astype(np.uint8)\n    return (out, depth) if want_depth else out",
        )
        ns = dict(vars(H))
        exec(compile(src, '<hunt_render_patch>', 'exec'), ns)
        render = ns['render']
    else:
        render = H.render
    im, depth = render(0, W=600, H=844, want_depth=True)
    rgb, dep = crop600(im, depth)
    return rgb, dep, H


def simulate_engine_night(rgb):
    """把正確夜地（約 22–26）提到約 55，天空／燈少動，模擬遊程報嘅過亮 game 夜。"""
    img = rgb.astype(np.float64)
    L = C.luma(img)
    r, g, b = img[..., 0], img[..., 1], img[..., 2]
    ground = C.sat((g - b) / 255.0 * 2.4 + (g - r) / 255.0 * 0.6)
    ground *= (1 - C.smoothstep(140, 200, L))
    chroma = img.max(-1) - img.min(-1)
    sky = (1 - C.smoothstep(12, 36, chroma)) * C.smoothstep(30, 46, L) * (1 - C.smoothstep(80, 130, L))
    # mid lift toward 55
    target = 55.0
    scale = np.ones_like(L)
    mid = (L > 12) & (L < 80)
    scale[mid] = np.clip(target / np.maximum(L[mid], 8), 1.0, 2.8)
    scale *= 0.15 + 0.85 * ground  # mainly lift ground
    scale = np.clip(scale, 1.0, 2.8)
    # don't lift sky or lamps
    scale = np.where(sky > 0.4, 1.0, scale)
    scale = np.where(L >= 140, 1.0, scale)
    out = np.clip(img * scale[..., None], 0, 255)
    return out.astype(np.uint8)


def panel(rgb, title, extra=None, w=300):
    h = int(round(rgb.shape[0] * w / rgb.shape[1]))
    im = Image.fromarray(rgb).resize((w, h), Image.Resampling.NEAREST)
    d = ImageDraw.Draw(im, 'RGBA')
    label(d, (6, 4), title, 14)
    if extra:
        label(d, (6, h - 22), extra, 13, fill=(255, 240, 180))
    return im


def sheet_row(cells, title, pad=8, bg=(24, 26, 38)):
    w = sum(c.width for c in cells) + pad * (len(cells) + 1)
    h = max(c.height for c in cells) + 40 + pad
    sh = Image.new('RGB', (w, h), bg)
    d = ImageDraw.Draw(sh)
    label(d, (pad, 8), title, 18)
    x = pad
    for c in cells:
        sh.paste(c, (x, 36))
        x += c.width + pad
    return sh


def vstack(imgs, bg=(24, 26, 38), pad=10):
    w = max(i.width for i in imgs) + pad * 2
    h = sum(i.height for i in imgs) + pad * (len(imgs) + 1)
    sh = Image.new('RGB', (w, h), bg)
    y = pad
    for i in imgs:
        sh.paste(i, (pad, y))
        y += i.height + pad
    return sh


def process(rgb, depth, lut=None, dof=True):
    out = rgb
    if dof and depth is not None:
        out = C.apply_dof(out, depth)
    if lut is not None:
        out = C.apply_lut(out, lut)
    return out


def load_luts(fx):
    d = {}
    for n in C.LUT_FNS:
        d[n] = np.array(Image.open(os.path.join(fx, 'luts', f'lut_{n}.png')).convert('RGB'))
    return d


# ---------- particle GIFs ----------
def load_sheet(fx, name):
    spec = json.load(open(os.path.join(fx, 'particles', f'{name}.json')))
    img = np.array(Image.open(os.path.join(fx, 'particles', os.path.basename(spec['image']))).convert('RGBA'))
    cell = spec['cell']
    return spec, img, cell

def frame_at(img, cell, r, c):
    return img[r * cell:(r + 1) * cell, c * cell:(c + 1) * cell]


def blit_add(dst, spr, x, y, tint=None, add=False):
    h, w = spr.shape[:2]
    H, W = dst.shape[:2]
    x, y = int(round(x)), int(round(y))
    for j in range(h):
        yy = y + j
        if yy < 0 or yy >= H:
            continue
        for i in range(w):
            xx = x + i
            if xx < 0 or xx >= W:
                continue
            if spr[j, i, 3] < 128:
                continue
            col = spr[j, i, :3].astype(np.float64)
            if tint is not None:
                col = np.clip(col * tint, 0, 255)
            if add:
                dst[yy, xx] = np.clip(dst[yy, xx].astype(np.float64) + col * (spr[j, i, 3] / 255.0), 0, 255)
            else:
                dst[yy, xx] = col


def save_gif(path, frames, ms=90, colors=64):
    pil = [Image.fromarray(f.astype(np.uint8) if f.dtype != np.uint8 else f).convert('RGB') for f in frames]
    # shared palette
    big = Image.new('RGB', (pil[0].width, pil[0].height * min(len(pil), 8)))
    for i, f in enumerate(pil[::max(1, len(pil)//8)][:8]):
        big.paste(f, (0, i * f.height))
    pal = big.quantize(colors, method=Image.Quantize.MEDIANCUT)
    q = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in pil]
    q[0].save(path, save_all=True, append_images=q[1:], duration=ms, loop=0, optimize=True)
    sz = os.path.getsize(path)
    if sz >= 3 * 1024 * 1024:
        raise SystemExit(f'GIF too big {path} {sz}')
    return sz


def gif_fireflies(bg, spec, sheet, cell, path):
    rng = np.random.default_rng(7)
    n = 22
    W, H = bg.shape[1], bg.shape[0]
    pos = np.stack([rng.uniform(20, W - 20, n), rng.uniform(20, H * 0.7, n), rng.uniform(0, 2 * math.pi, n)], 1)
    vel = rng.uniform(-8, 8, (n, 2))
    frames = []
    N = 24
    dt = 0.1
    for k in range(N):
        im = bg.copy().astype(np.float64)
        t = k * dt
        for i in range(n):
            pos[i, 0] += vel[i, 0] * dt + 9 * math.sin(t * 1.3 + pos[i, 2]) * dt
            pos[i, 1] += vel[i, 1] * dt + 5 * math.sin(t * 1.9 + pos[i, 2] * 1.7) * dt
            blink = 0.5 + 0.5 * math.sin(t * 5 + pos[i, 2] * 3)
            if blink < 0.2:
                continue
            fr = (k + i) % 8
            spr = frame_at(sheet, cell, i % 2, fr)
            blit_add(im, spr, pos[i, 0] - 4, pos[i, 1] - 4, add=True)
        frames.append(np.clip(im, 0, 255).astype(np.uint8))
    return save_gif(path, frames, 90)


def gif_leaves(bgs, spec, sheet, cell, path):
    # 2×2 四季，每個 300×200 若不足就 resize bg
    seasons = ['spring', 'summer', 'autumn', 'winter']
    rows_of = spec['season_rows']
    rng = np.random.default_rng(3)
    N = 24
    dt = 0.1
    cells_f = []
    for si, season in enumerate(seasons):
        bg = Image.fromarray(bgs[si]).resize((300, 200), Image.Resampling.NEAREST)
        bg = np.array(bg.convert('RGB'))
        n = 14 if season != 'autumn' else 20
        row_choices = rows_of[season]
        parts = []
        for i in range(n):
            parts.append(dict(
                x=float(rng.uniform(-10, 310)), y=float(rng.uniform(-40, 80)),
                vx=float(rng.uniform(8, 28)), vy=float(rng.uniform(18, 42)),
                row=int(row_choices[i % len(row_choices)]),
                fr=int(rng.integers(0, 8)),
                phase=float(rng.uniform(0, 6)),
            ))
        seq = []
        for k in range(N):
            im = bg.copy()
            for p in parts:
                p['x'] += (p['vx'] + 10 * math.sin(k * dt * 2 + p['phase'])) * dt
                p['y'] += p['vy'] * dt
                if p['y'] > 210:
                    p['y'] = -16; p['x'] = float(rng.uniform(-10, 310))
                if p['x'] > 320:
                    p['x'] = -16
                fr = (p['fr'] + k // 2) % 8
                spr = frame_at(sheet, cell, p['row'], fr)
                blit_add(im, spr, p['x'], p['y'])
            seq.append(im)
        cells_f.append(seq)
    frames = []
    titles = ['春', '夏', '秋', '冬']
    for k in range(N):
        canv = Image.new('RGB', (600, 400), (24, 26, 38))
        for i, title in enumerate(titles):
            x, y = (i % 2) * 300, (i // 2) * 200
            canv.paste(Image.fromarray(cells_f[i][k]), (x, y))
            d = ImageDraw.Draw(canv)
            label(d, (x + 6, y + 4), f'落葉 {title}', 14)
        frames.append(np.array(canv))
    return save_gif(path, frames, 90)


def gif_petals(bg, spec, sheet, cell, path):
    bg = np.array(Image.fromarray(bg).resize((320, 200), Image.Resampling.NEAREST).convert('RGB'))
    rng = np.random.default_rng(5)
    n = 18
    parts = [dict(x=float(rng.uniform(-8, 320)), y=float(rng.uniform(-30, 160)),
                  vx=float(rng.uniform(4, 16)), vy=float(rng.uniform(8, 18)),
                  row=int(i % 3), fr=int(rng.integers(0, 8)), phase=float(rng.uniform(0, 6)))
             for i in range(n)]
    frames = []
    N, dt = 24, 0.1
    for k in range(N):
        im = bg.copy()
        for p in parts:
            p['x'] += (p['vx'] + 14 * math.sin(k * dt * 1.4 + p['phase'])) * dt
            p['y'] += p['vy'] * dt
            if p['y'] > 210:
                p['y'] = -8; p['x'] = float(rng.uniform(0, 320))
            spr = frame_at(sheet, cell, p['row'], (p['fr'] + k // 2) % 8)
            blit_add(im, spr, p['x'], p['y'])
        d = ImageDraw.Draw(Image.fromarray(im))
        # label after? draw on array via pil
        pil = Image.fromarray(im)
        label(ImageDraw.Draw(pil), (6, 4), '花瓣', 14)
        frames.append(np.array(pil))
    return save_gif(path, frames, 90)


def gif_rain(bg, spec, sheet, cell, path):
    bg = np.array(Image.fromarray(bg).resize((320, 200), Image.Resampling.NEAREST).convert('RGB'))
    rng = np.random.default_rng(9)
    n = 70
    parts = [dict(x=float(rng.uniform(0, 320)), y=float(rng.uniform(-40, 200)),
                  v=float(rng.uniform(280, 380)), col=int(rng.integers(0, 4)))
             for _ in range(n)]
    frames = []
    N, dt = 20, 0.08
    for k in range(N):
        im = bg.copy().astype(np.float64)
        # slight darken for rain mood
        im = im * 0.92
        for p in parts:
            p['y'] += p['v'] * dt
            if p['y'] > 210:
                p['y'] = float(rng.uniform(-40, -8)); p['x'] = float(rng.uniform(0, 320))
            spr = frame_at(sheet, cell, 0, p['col'])
            blit_add(im, spr, p['x'] - 8, p['y'] - 8)
        pil = Image.fromarray(np.clip(im, 0, 255).astype(np.uint8))
        label(ImageDraw.Draw(pil), (6, 4), '雨', 14)
        frames.append(np.array(pil))
    return save_gif(path, frames, 80)


def gif_snow(bg, spec, sheet, cell, path):
    bg = np.array(Image.fromarray(bg).resize((320, 200), Image.Resampling.NEAREST).convert('RGB'))
    rng = np.random.default_rng(11)
    n = 50
    parts = [dict(x=float(rng.uniform(0, 320)), y=float(rng.uniform(-40, 200)),
                  vx=float(rng.uniform(-8, 8)), vy=float(rng.uniform(12, 26)),
                  row=int(rng.integers(0, 4)), fr=int(rng.integers(0, 8)), phase=float(rng.uniform(0, 6)))
             for _ in range(n)]
    frames = []
    N, dt = 24, 0.1
    for k in range(N):
        im = bg.copy()
        for p in parts:
            p['x'] += (p['vx'] + 16 * math.sin(k * dt * 1.1 + p['phase'])) * dt
            p['y'] += p['vy'] * dt
            if p['y'] > 210:
                p['y'] = -8; p['x'] = float(rng.uniform(0, 320))
            spr = frame_at(sheet, cell, p['row'], (p['fr'] + k // 3) % 8)
            blit_add(im, spr, p['x'] - 4, p['y'] - 4)
        pil = Image.fromarray(im)
        label(ImageDraw.Draw(pil), (6, 4), '雪', 14)
        frames.append(np.array(pil))
    return save_gif(path, frames, 90)


def gif_debris(bg, spec, sheet, cell, path, origin=(180, 150)):
    bg = np.array(Image.fromarray(bg).resize((320, 200), Image.Resampling.NEAREST).convert('RGB'))
    rng = np.random.default_rng(13)
    N, dt = 16, 0.07
    n = 14
    parts0 = [dict(x=origin[0] + float(rng.uniform(-4, 4)), y=origin[1] + float(rng.uniform(-2, 2)),
                   vx=float(rng.uniform(-50, 50)), vy=float(rng.uniform(-90, -30)),
                   row=int(rng.integers(0, 2)), col=int(rng.integers(0, 8)))
              for _ in range(n)]
    frames = []
    for k in range(N):
        im = bg.copy()
        # burst once at start, then fall
        fade = 1.0 if k < 10 else max(0, 1 - (k - 10) / 6)
        if fade > 0:
            for p in parts0:
                x = p['x'] + p['vx'] * k * dt
                y = p['y'] + p['vy'] * k * dt + 0.5 * 90 * (k * dt) ** 2
                spr = frame_at(sheet, cell, p['row'], p['col'])
                if fade < 1:
                    tmp = spr.copy()
                    # hard fade: skip some
                    if fade < 0.5 and (p['col'] + k) % 2 == 0:
                        continue
                blit_add(im, spr, x - 4, y - 6)
        pil = Image.fromarray(im)
        label(ImageDraw.Draw(pil), (6, 4), '撥草碎屑', 14)
        frames.append(np.array(pil))
    return save_gif(path, frames, 80)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default=os.path.abspath(os.path.join(HERE, '../..')))
    ap.add_argument('--out', default=OUT)
    ap.add_argument('--garden-src', default='/workspace/glimmer-3d-h1/art-pet/scenes/garden3d/H1')
    ap.add_argument('--hunt-root', default='/workspace/m1-icons-hunt-src')
    a = ap.parse_args()
    root, out = os.path.abspath(a.root), os.path.abspath(a.out)
    os.makedirs(out, exist_ok=True)
    fx = os.path.join(root, 'art-pet', 'fx')
    luts = load_luts(fx)

    print('render garden…')
    gday, gday_z, _ = render_garden(a.garden_src, night=False)
    gnight, gnight_z, _ = render_garden(a.garden_src, night=True)
    print('render hunt…')
    hday, hday_z, _ = render_hunt(a.hunt_root)

    # save raw
    to_pil(gday).save(os.path.join(out, 'src_garden_day.png'))
    to_pil(gnight).save(os.path.join(out, 'src_garden_night.png'))
    to_pil(hday).save(os.path.join(out, 'src_hunt_day.png'))

    def extras(rgb, which='day'):
        # sky top band, ground bottom band
        sk = lum_region(rgb, (40, 8, 220, 48))
        gd = lum_region(rgb, (40, 320, 560, 390))
        return f'空L{sk:.0f} 地L{gd:.0f}'

    # Garden day: 原 | DoF | 日 | 春 | 夏 | 秋 | 冬
    def row_for(rgb, depth, keys, title):
        cells = []
        cells.append(panel(rgb, '原圖', extras(rgb)))
        cells.append(panel(process(rgb, depth, None, True), '+DoF', extras(process(rgb, depth, None, True))))
        for k in keys:
            out = process(rgb, depth, luts[k], True)
            cells.append(panel(out, C.LUT_ZH[k], extras(out)))
        return sheet_row(cells, title)

    s1 = row_for(gday, gday_z, ['day', 'spring', 'summer', 'autumn', 'winter'], '花園 H1 日間＋景深＋調色（600×400 裁切，同穩陣 GIF）')
    s1.save(os.path.join(out, 'lut_dof_garden_day.png'))
    s2 = row_for(hday, hday_z, ['day', 'spring', 'summer', 'autumn', 'winter'], '狩獵草原日間＋景深＋調色')
    s2.save(os.path.join(out, 'lut_dof_hunt_day.png'))

    # dusk from day
    dusk = process(gday, gday_z, luts['dusk'], True)
    hdusk = process(hday, hday_z, luts['dusk'], True)
    s3 = sheet_row([
        panel(gday, '花園原日', extras(gday)),
        panel(dusk, '黃昏＋DoF', extras(dusk)),
        panel(hday, '草原原日', extras(hday)),
        panel(hdusk, '草原黃昏＋DoF', extras(hdusk)),
    ], '黃昏調色（由日間底圖套 lut_dusk）')
    s3.save(os.path.join(out, 'lut_dof_dusk.png'))

    # night comparison
    eng = simulate_engine_night(gnight)
    fixed = process(eng, gnight_z, luts['night'], True)
    already = process(gnight, gnight_z, luts['night'], True)
    # reference gif frame if present
    cells_n = [
        panel(gnight, '預覽夜（認可級）', extras(gnight)),
        panel(eng, '模擬引擎夜（地≈55）', extras(eng)),
        panel(fixed, '引擎夜＋lut_night＋DoF', extras(fixed)),
        panel(already, '認可夜再套 LUT（應仍暗）', extras(already)),
    ]
    ref = '/workspace/game-design/pilot3d_h1_mesh/night_lamps.gif'
    if os.path.isfile(ref):
        rf = Image.open(ref)
        rf.seek(0)
        rf = rf.convert('RGB').resize((300, int(300 * rf.size[1] / rf.size[0])), Image.Resampling.NEAREST)
        d = ImageDraw.Draw(rf)
        # measure
        arr = np.array(Image.open(ref).convert('RGB'))
        label(d, (6, 4), '認可 night_lamps.gif', 13)
        cells_n.append(rf)
    s4 = sheet_row(cells_n, '夜景地面：引擎過亮（約 55）→ LUT 目標約 26；夜空約 55。右欄係 Kurt 認可 GIF 參考（構圖唔完全相同）。')
    s4.save(os.path.join(out, 'lut_dof_garden_night.png'))

    # combined big sheet
    vstack([s1, s2, s3, s4]).save(os.path.join(out, 'compare_sheet.png'))

    # LUT strips preview (tiny)
    strip = Image.new('RGB', (1089, 33 * 8 + 8 * 16), (20, 22, 34))
    d = ImageDraw.Draw(strip)
    for i, n in enumerate(['identity', 'day', 'dusk', 'night', 'spring', 'summer', 'autumn', 'winter']):
        y = i * (33 + 16)
        label(d, (4, y), C.LUT_ZH[n], 13)
        strip.paste(Image.fromarray(luts[n]), (0, y + 14))
    strip.save(os.path.join(out, 'luts_strip.png'))

    print('particle gifs…')
    # backgrounds for particles
    night_bg = process(gnight, gnight_z, luts['night'], True)
    spring_bg = process(gday, gday_z, luts['spring'], True)
    summer_bg = process(gday, gday_z, luts['summer'], True)
    autumn_bg = process(gday, gday_z, luts['autumn'], True)
    winter_bg = process(hday, hday_z, luts['winter'], True)
    hunt_dof = process(hday, hday_z, luts['day'], True)

    sizes = {}
    sp, sh, cell = load_sheet(fx, 'fireflies')
    sizes['fireflies.gif'] = gif_fireflies(night_bg, sp, sh, cell, os.path.join(out, 'fireflies.gif'))
    sp, sh, cell = load_sheet(fx, 'leaves')
    sizes['leaves.gif'] = gif_leaves([spring_bg, summer_bg, autumn_bg, winter_bg], sp, sh, cell, os.path.join(out, 'leaves.gif'))
    sp, sh, cell = load_sheet(fx, 'petals')
    sizes['petals.gif'] = gif_petals(spring_bg, sp, sh, cell, os.path.join(out, 'petals.gif'))
    sp, sh, cell = load_sheet(fx, 'rain')
    sizes['rain.gif'] = gif_rain(gday, sp, sh, cell, os.path.join(out, 'rain.gif'))
    sp, sh, cell = load_sheet(fx, 'snow')
    sizes['snow.gif'] = gif_snow(winter_bg, sp, sh, cell, os.path.join(out, 'snow.gif'))
    sp, sh, cell = load_sheet(fx, 'grass_debris')
    sizes['grass_debris.gif'] = gif_debris(hunt_dof, sp, sh, cell, os.path.join(out, 'grass_debris.gif'), origin=(200, 155))

    # particle sheet contact
    imgs = []
    for n, zh in [('fireflies', '螢火蟲'), ('leaves', '落葉'), ('petals', '花瓣'),
                   ('rain', '雨'), ('snow', '雪'), ('grass_debris', '撥草碎屑')]:
        im = Image.open(os.path.join(fx, 'particles', f'{n}.png')).convert('RGBA')
        # scale up nearest for readability, cap width
        sc = 4 if im.size[0] <= 64 else (2 if im.size[0] <= 128 else 1)
        im = im.resize((im.size[0] * sc, im.size[1] * sc), Image.Resampling.NEAREST)
        bg = Image.new('RGB', (im.size[0] + 16, im.size[1] + 32), (32, 30, 40))
        # checker
        ch = np.zeros((im.size[1], im.size[0], 3), np.uint8)
        ch[:] = 40
        yy, xx = np.mgrid[0:im.size[1], 0:im.size[0]]
        ch[((yy // 8) + (xx // 8)) % 2 == 0] = (60, 58, 70)
        bg.paste(Image.fromarray(ch), (8, 24))
        bg.paste(im, (8, 24), im)
        label(ImageDraw.Draw(bg), (8, 4), zh, 14)
        imgs.append(bg)
    # stack
    pw = max(i.width for i in imgs)
    ph = sum(i.height for i in imgs) + 8 * len(imgs)
    contact = Image.new('RGB', (pw + 16, ph + 16), (24, 26, 38))
    y = 8
    for i in imgs:
        contact.paste(i, (8, y))
        y += i.height + 8
    contact.save(os.path.join(out, 'particles_sheet.png'))

    meta = dict(crop=list(CROP), gifs=sizes, notes='預覽用現有 numpy 渲染器＋後製 DoF／LUT，非 Godot 引擎畫面。')
    json.dump(meta, open(os.path.join(out, 'preview_meta.json'), 'w'), ensure_ascii=False, indent=1)
    print('ok', out, sizes)


if __name__ == '__main__':
    main()
