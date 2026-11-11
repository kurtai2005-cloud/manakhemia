#!/usr/bin/env python3
"""build_m1_previews.py — icon 總覽、狩獵場景組合圖、每個 clip 一張 strip＋小 GIF（<3MB）。"""
import os, sys, json, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import garden3d_mesh as GM
from m1_common import V3, PAL, HUNT, rgba, blit, harden_alpha, save_png, load_png, SIZES, CLIPS, CRITTERS, FRUITS

def font(sz=14):
    cands = [
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',
        '/workspace/kitx/art-pet/ui/kit_hd2d/fonts',
    ]
    # search
    import glob
    paths = glob.glob('/usr/share/fonts/**/*CJK*Regular*.ttc', recursive=True) + \
            glob.glob('/usr/share/fonts/**/*CJK*Regular*.otf', recursive=True) + \
            glob.glob('/usr/share/fonts/**/NotoSans*Regular*.ttf', recursive=True)
    for p in cands + paths:
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
    im = Image.fromarray(img)
    d = ImageDraw.Draw(im)
    f = font(sz)
    if shadow:
        d.text((x + 1, y + 1), text, font=f, fill=(20, 16, 28, 200))
    d.text((x, y), text, font=f, fill=fill + ((255,) if len(fill) == 3 else ()))
    return np.array(im)

def icons_sheet(root, out):
    spec = json.load(open(f'{root}/art-pet/ui/m1_icons/icons.json'))
    items = spec['items']
    # 8 列
    cols = 8
    cell, pad, header = 80, 12, 40
    rows = (len(items) + cols - 1) // cols
    W = pad + cols * cell + pad
    H = header + pad + rows * (cell + 22) + pad + 130  # bubble 位
    im = rgba(H, W)
    im[..., :3] = V3['navy']
    im[..., 3] = 255
    im = label(im, 'M1 icon 總覽（需要 4＋表情 10＋事件 20＝34）  @3x 32px', 12, 10, V3['goldhi'], 16)
    for i, it in enumerate(items):
        r, c = divmod(i, cols)
        x, y = pad + c * cell, header + pad + r * (cell + 22)
        fill_bg = rgba(64, 64)
        fill_bg[..., :3] = V3['navy2']
        fill_bg[..., 3] = 255
        blit(im, fill_bg, x, y)
        ic = load_png(f'{root}/art-pet/ui/m1_icons/{it["file"]}')
        blit(im, np.repeat(np.repeat(ic, 2, 0), 2, 1), x, y)
        im = label(im, it['zh'], x, y + 66, V3['mute'], 11)
    # bubble
    bub = load_png(f'{root}/art-pet/ui/m1_icons/bubble_dream@3x.png')
    by = header + pad + rows * (cell + 22) + 4
    blit(im, bub, pad, by)
    im = label(im, '夢泡泡框（兩格事件 icon 撞埋，真 alpha）', pad + 110, by + 4, V3['gold'], 13)
    # badges 放泡泡右側，避開文字
    bx = pad + 110
    im = label(im, '銅證 ×4', bx, by + 24, V3['goldhi'], 13)
    bx = pad + 110
    for meta in CRITTERS:
        b = load_png(f'{root}/art-pet/ui/m1_icons/badges/badge_copper_{meta["id"]}@3x.png')
        blit(im, np.repeat(np.repeat(b, 2, 0), 2, 1), bx, by + 40)
        bx += 70
    save_png(f'{out}/icons_sheet.png', im)
    return f'{out}/icons_sheet.png'

# ----- 簡單透視 rasterizer -----
def look_cam(CJ, yaw_deg=0):
    t = np.array(CJ['target'], float)
    pitch = math.radians(CJ['pitchDeg'])
    yaw = math.radians(yaw_deg)
    # 相機在 target 後方：−forward * dist；forward 由 pitch（下望）同 yaw
    # +Z 向鏡頭，即世界 +Z 係「近」。鏡頭喺 +Z 一側望向 −Z。
    cy, sy = math.cos(yaw), math.sin(yaw)
    cp, sp = math.cos(pitch), math.sin(pitch)
    # forward（相機望向）：yaw 0 時望向 −Z，向下 pitch
    fwd = np.array([sy * cp, -sp, -cy * cp])
    fwd /= np.linalg.norm(fwd)
    eye = t - fwd * CJ['dist']
    up = np.array([0, 1, 0], float)
    right = np.cross(fwd, up); right /= np.linalg.norm(right)
    up = np.cross(right, fwd); up /= np.linalg.norm(up)
    return eye, fwd, right, up, t

def project(p, eye, fwd, right, up, fov, W, H):
    v = p - eye
    x = np.dot(v, right)
    y = np.dot(v, up)
    z = np.dot(v, fwd)  # 前方為正
    if z <= 1e-3:
        return None
    f = 0.5 * H / math.tan(math.radians(fov) / 2)
    sx = W * 0.5 + x * f / z
    sy = H * 0.5 - y * f / z
    return sx, sy, z


def bary(px, py, a, b, c):
    v0, v1, v2 = b - a, c - a, np.array([px, py]) - a
    d00, d01, d11 = np.dot(v0, v0), np.dot(v0, v1), np.dot(v1, v1)
    d20, d21 = np.dot(v2, v0), np.dot(v2, v1)
    den = d00 * d11 - d01 * d01
    if abs(den) < 1e-9: return None
    v = (d11 * d20 - d01 * d21) / den
    w = (d00 * d21 - d01 * d20) / den
    u = 1 - v - w
    if u < -0.01 or v < -0.01 or w < -0.01: return None
    return u, v, w

def fill_tri_vec(color, zbuf, sx, sy, sz, uvs, tex, lit, v_up=True):
    """sx,sy,sz (3,)；uvs (3,2)；v_up=True 時 row=(1-v)*h。"""
    H, W = color.shape[:2]
    minx, maxx = max(0, int(np.floor(sx.min()))), min(W - 1, int(np.ceil(sx.max())))
    miny, maxy = max(0, int(np.floor(sy.min()))), min(H - 1, int(np.ceil(sy.max())))
    if minx >= maxx or miny >= maxy:
        return
    xs = np.arange(minx, maxx + 1) + 0.5
    ys = np.arange(miny, maxy + 1) + 0.5
    X, Y = np.meshgrid(xs, ys)
    a = np.array([sx[0], sy[0]]); b = np.array([sx[1], sy[1]]); c = np.array([sx[2], sy[2]])
    v0, v1 = b - a, c - a
    d00, d01, d11 = np.dot(v0, v0), np.dot(v0, v1), np.dot(v1, v1)
    den = d00 * d11 - d01 * d01
    if abs(den) < 1e-9:
        return
    v2x, v2y = X - a[0], Y - a[1]
    d20 = v2x * v0[0] + v2y * v0[1]
    d21 = v2x * v1[0] + v2y * v1[1]
    vv = (d11 * d20 - d01 * d21) / den
    ww = (d00 * d21 - d01 * d20) / den
    uu = 1 - vv - ww
    mask = (uu >= -0.01) & (vv >= -0.01) & (ww >= -0.01)
    if not mask.any():
        return
    z = uu * sz[0] + vv * sz[1] + ww * sz[2]
    zbuf_v = zbuf[miny:maxy + 1, minx:maxx + 1]
    closer = mask & (z < zbuf_v)
    if not closer.any():
        return
    tu = uu * uvs[0, 0] + vv * uvs[1, 0] + ww * uvs[2, 0]
    tv = uu * uvs[0, 1] + vv * uvs[1, 1] + ww * uvs[2, 1]
    th, tw = tex.shape[:2]
    if v_up:
        tx = np.clip((tu * tw).astype(int), 0, tw - 1)
        ty = np.clip(((1 - tv) * th).astype(int), 0, th - 1)
    else:
        tx = np.clip((tu * tw).astype(int), 0, tw - 1)
        ty = np.clip((tv * th).astype(int), 0, th - 1)
    px = tex[ty, tx]
    vis = closer & (px[..., 3] >= 128)
    if not vis.any():
        return
    rgb = np.clip(px[..., :3].astype(np.float32) * lit, 0, 255).astype(np.uint8)
    dest = color[miny:maxy + 1, minx:maxx + 1]
    dest[vis, :3] = rgb[vis]
    dest[vis, 3] = 255
    zbuf_v[vis] = z[vis]


def raster_mesh(color, zbuf, MJ, tex, pos, eye, fwd, right, up, fov, W, H, sun_dir, shade=True):
    P = np.array(MJ['positions'], float).reshape(-1, 3) + np.array(pos, float)
    N = np.array(MJ['normals'], float).reshape(-1, 3)
    UV = np.array(MJ['uvs'], float).reshape(-1, 2)
    I = np.array(MJ['indices'], int).reshape(-1, 3)
    # project all
    v = P - eye
    x = v @ right; y = v @ up; z = v @ fwd
    ok = z > 1e-3
    f = 0.5 * H / math.tan(math.radians(fov) / 2)
    sx = W * 0.5 + x * f / np.where(ok, z, 1)
    sy = H * 0.5 - y * f / np.where(ok, z, 1)
    for tri in I:
        if not ok[tri].all():
            continue
        n = N[tri[0]]
        ndl = max(0.25, float(np.dot(n, -np.array(sun_dir)))) if shade else 1.0
        lit = min(1.15, ndl * 0.85 + 0.35)
        fill_tri_vec(color, zbuf, sx[tri], sy[tri], z[tri], UV[tri], tex, lit, v_up=True)


def blit_billboard(color, zbuf, sprite, world, pivot, eye, fwd, right, up, fov, W, H, scale=1.0):
    h, w = sprite.shape[:2]
    px, py = pivot
    corners_w = []
    for ox, oy in ((0, 0), (w, 0), (w, h), (0, h)):
        p = world + right * ((ox - px) * scale) + np.array([0.0, 1.0, 0.0]) * ((py - oy) * scale)
        corners_w.append(p)
    P = np.stack(corners_w)
    v = P - eye
    x = v @ right; y = v @ up; z = v @ fwd
    if (z <= 1e-3).any():
        return
    f = 0.5 * H / math.tan(math.radians(fov) / 2)
    sx = W * 0.5 + x * f / z
    sy = H * 0.5 - y * f / z
    # two tris, uv V-down (sprite row 0 at top)
    uvs = [np.array([[0, 0], [w, 0], [w, h]], float),
           np.array([[0, 0], [w, h], [0, h]], float)]
    idx = [(0, 1, 2), (0, 2, 3)]
    # fill using pixel coords as uv (v_up=False, but uv already in px — hack: pass dummy and custom)
    # Use fill with normalized uv and v_up=False, tex samples tv*h
    uvs_n = [np.array([[0, 0], [1, 0], [1, 1]], float),
             np.array([[0, 0], [1, 1], [0, 1]], float)]
    for (ia, ib, ic), uv in zip(idx, uvs_n):
        fill_tri_vec(color, zbuf, sx[[ia, ib, ic]], sy[[ia, ib, ic]], z[[ia, ib, ic]], uv, sprite, 1.0, v_up=False)


def sky_bg(W, H, sky, hills):
    im = rgba(H, W)
    # 垂直漸變
    for y in range(H):
        t = y / max(H - 1, 1)
        # 上天空下地
        if t < 0.55:
            tt = t / 0.55
            col = tuple(int(HUNT['sky_t'][i] * (1 - tt) + HUNT['sky_b'][i] * tt) for i in range(3))
        else:
            tt = (t - 0.55) / 0.45
            col = tuple(int(HUNT['sky_b'][i] * (1 - tt) + HUNT['grass'][i] * tt) for i in range(3))
        im[y, :, :3] = col
        im[y, :, 3] = 255
    # 遠丘貼喺中間偏下
    hh = np.repeat(np.repeat(hills, 3, 0), 3, 1)
    # 置中
    y0 = int(H * 0.42)
    x0 = (W - hh.shape[1]) // 2
    blit(im, hh, x0, y0)
    return im

def render_scene(root, out, W=360, H=640, yaw=0, pet_pos=(0, 40), pet_frame=None, title=True):
    src = f'{root}/art-pet/scenes/hunt3d/prairie'
    OBJ = json.load(open(f'{src}/objects.json'))
    CJ = json.load(open(f'{src}/camera.json'))
    LJ = json.load(open(f'{src}/lights.json'))
    eye, fwd, right, up, t = look_cam(CJ, yaw)
    hills = load_png(f'{src}/backdrop/bg_hills.png')
    sky = load_png(f'{src}/backdrop/bg_sky.png')
    color = sky_bg(W, H, sky, hills)
    zbuf = np.full((H, W), 1e9, np.float32)
    # 地面：大格
    ground = load_png(f'{src}/ground/ground.png')
    ao = load_png(f'{src}/ground/ground_ao.png')
    tile = load_png(f'{src}/ground/ground_tile.png')
    g = ground.astype(np.int16) * ao[..., :1].astype(np.int16) // 255
    ground = np.clip(g, 0, 255).astype(np.uint8)
    # 預覽用大地面：中心 256 用地圖，外圍用 tile（x±384、z −384…+256）
    span = 520
    res = 640
    big = np.zeros((res, res, 4), np.uint8)
    # world x,z from -span..+span → tex
    # row 0 = z = -span (far)
    for i in range(res):
        z = -span + (i + 0.5) * (2 * span) / res
        for j in range(res):
            x = -span + (j + 0.5) * (2 * span) / res
            if -128 <= x < 128 and -128 <= z < 128:
                col = int(x + 128); row = int(z + 128)
                big[i, j] = ground[min(255, max(0, row)), min(255, max(0, col))]
            else:
                tx = int(x - (-128)) % 64  # 同花園：以 (−128,−128) 對齊
                tz = int(z - (-128)) % 64
                big[i, j] = tile[tz, tx]
    Pcorn = [(-span, 0, -span), (span, 0, -span), (span, 0, span), (-span, 0, span)]
    pts = [project(np.array(p, float), eye, fwd, right, up, CJ['fovDeg'], W, H) for p in Pcorn]
    if all(p is not None for p in pts):
        uvs = np.array([[0, 0], [1, 0], [1, 1], [0, 1]], float)
        sx = np.array([p[0] for p in pts]); sy = np.array([p[1] for p in pts]); sz = np.array([p[2] for p in pts])
        fill_tri_vec(color, zbuf, sx[[0, 1, 2]], sy[[0, 1, 2]], sz[[0, 1, 2]], uvs[[0, 1, 2]], big, 1.0, v_up=False)
        fill_tri_vec(color, zbuf, sx[[0, 2, 3]], sy[[0, 2, 3]], sz[[0, 2, 3]], uvs[[0, 2, 3]], big, 1.0, v_up=False)
        # meshes
    cache = {}
    sun = LJ['sun']['dir']
    # 遠→近（粗：按 z 世界）
    objs = sorted(OBJ['objects'], key=lambda o: o['z'])
    for o in objs:
        mid = os.path.basename(o['mesh']).replace('.json', '')
        if mid not in cache:
            MJ = json.load(open(f"{src}/{o['mesh']}"))
            tex = load_png(f"{src}/{MJ['texture']}")
            cache[mid] = (MJ, tex)
        MJ, tex = cache[mid]
        raster_mesh(color, zbuf, MJ, tex, (o['x'], o.get('y', 0), o['z']),
                    eye, fwd, right, up, CJ['fovDeg'], W, H, sun)
    # 寵物
    if pet_frame is not None:
        blit_billboard(color, zbuf, pet_frame, np.array([pet_pos[0], 0, pet_pos[1]], float),
                       (32, 61), eye, fwd, right, up, CJ['fovDeg'], W, H)
    # 小怪
    for sp in OBJ['critters']['spawn']:
        cj = json.load(open(f'{root}/art-pet/sprites/hunt/critters/{sp["id"]}.json'))
        atl = load_png(f'{root}/art-pet/sprites/hunt/critters/{cj["atlas"]["image"]}')
        frn = cj['animations']['idle']['frames'][0]
        fr = cj['atlas']['frames'][frn]['frame']
        spr = atl[fr['y']:fr['y'] + fr['h'], fr['x']:fr['x'] + fr['w']]
        pv = cj['pivotPx']
        blit_billboard(color, zbuf, spr, np.array([sp['x'], 0, sp['z']], float),
                       tuple(pv), eye, fwd, right, up, CJ['fovDeg'], W, H)
    if title:
        color = label(color, '草原 1 區（M1 lite）  yaw %d°' % yaw, 10, 10, V3['cream'], 14)
    return color

def scene_sheet(root, out):
    """改用 H1 光線投射預覽（地面 @3x、影 0.3、600×400 裁切）。"""
    import preview_hunt3d as PH
    PH.load(root, out=out)
    return PH.scene_stills(out)

def clips_preview(root, out):
    hd = f'{root}/art-pet/sprites/tuanrong/motion/hunt'
    idx = json.load(open(f'{hd}/clips.json'))
    for cid, cm in CLIPS.items():
        # strip：S/M/L 三行，每行 6 幀
        rows = []
        giframes = []  # 並排 S M L 合成
        max_h = 0
        row_imgs = {}
        for sz, szm in SIZES.items():
            stem = os.path.splitext(os.path.basename(idx['atlases'][sz][cid]))[0]
            J = json.load(open(f'{hd}/{stem}.json'))
            atl = load_png(f'{hd}/{stem}.png')
            frs = []
            for i in range(cm['frames']):
                nm = f'{cid}_{i+1:02d}'
                fr = J['frames'][nm]['frame']
                frs.append(atl[fr['y']:fr['y'] + fr['h'], fr['x']:fr['x'] + fr['w']])
            row_imgs[sz] = frs
            max_h = max(max_h, szm['size'])
        # strip canvas
        scale = 3
        pad, gap, left = 8, 6, 48
        fw = 64 * scale  # 用 L 格寬統一
        rows_n = 3
        W = left + cm['frames'] * (fw + gap) + pad
        H = pad + rows_n * (64 * scale + 24) + 28
        sheet = rgba(H, W)
        sheet[..., :3] = (24, 22, 36)
        sheet[..., 3] = 255
        sheet = label(sheet, f'{cm["zh"]}  {cid}  {cm["frames"]}f  {cm["fps"]}fps  loop={cm["loop"]}  radiant ×S/M/L', 8, 4, V3['goldhi'], 14)
        # GIF 畫布：三隻並排
        gw = 16 + 3 * (64 * 2 + 12)
        gh = 64 * 2 + 28
        gif_f = []
        for ri, (sz, szm) in enumerate(SIZES.items()):
            y = 26 + ri * (64 * scale + 24)
            sheet = label(sheet, sz, 8, y + 64 * scale // 2 - 8, V3['cream'], 16)
            frs = row_imgs[sz]
            for i, fr in enumerate(frs):
                sc = (64 * scale) // szm['size']
                big = np.repeat(np.repeat(fr, sc, 0), sc, 1)
                x = left + i * (fw + gap)
                blit(sheet, big, x, y)
        save_png(f'{out}/{cid}_strip.png', sheet)
        # GIF
        for i in range(cm['frames']):
            canvas = Image.new('RGBA', (gw, gh), (24, 22, 36, 255))
            arr = np.array(canvas)
            arr = label(arr, f'{cm["zh"]}  S / M / L', 8, 4, V3['goldhi'], 13)
            x = 8
            for sz, szm in SIZES.items():
                fr = row_imgs[sz][i]
                sc = 2 if szm['size'] >= 48 else 4  # S 32×4=128 太大；統一 2：S=64, M=96, L=128 唔齊
                sc = max(1, 128 // szm['size'])  # S=4, M=2 (96), L=2
                # 用 2 倍統一高度唔同
                big = np.repeat(np.repeat(fr, 2, 0), 2, 1)
                # 底對齊
                yy = gh - 8 - big.shape[0]
                blit(arr, big, x, yy)
                x += big.shape[1] + 10
            gif_f.append(Image.fromarray(arr).convert('P', palette=Image.ADAPTIVE, colors=128))
        dur = int(1000 / cm['fps'])
        gif_f[0].save(f'{out}/{cid}.gif', save_all=True, append_images=gif_f[1:],
                      duration=dur, loop=0, optimize=True, disposal=2)
        szb = os.path.getsize(f'{out}/{cid}.gif')
        if szb >= 3 * 1024 * 1024:
            raise SystemExit(f'GIF 太大 {cid} {szb}')
    # 額外：小怪／果 sheet
    cs = rgba(220, 720)
    cs[..., :3] = V3['navy']; cs[..., 3] = 255
    cs = label(cs, '小怪（idle／驚／變果）＋果實', 10, 8, V3['goldhi'], 15)
    x = 12
    for meta in CRITTERS:
        J = json.load(open(f'{root}/art-pet/sprites/hunt/critters/{meta["id"]}.json'))
        atl = load_png(f'{root}/art-pet/sprites/hunt/critters/{J["atlas"]["image"]}')
        cs = label(cs, meta['zh'], x, 28, V3['cream'], 12)
        y = 48
        for ani in ('idle', 'scared', 'tofruit'):
            frn = J['animations'][ani]['frames'][0]
            fr = J['atlas']['frames'][frn]['frame']
            spr = atl[fr['y']:fr['y'] + fr['h'], fr['x']:fr['x'] + fr['w']]
            blit(cs, np.repeat(np.repeat(spr, 2, 0), 2, 1), x, y)
            y += spr.shape[0] * 2 + 6
        x += 80
    x0 = x + 10
    cs = label(cs, '果 ×6', x0, 28, V3['cream'], 12)
    F = json.load(open(f'{root}/art-pet/sprites/hunt/fruits/fruits.json'))
    fatl = load_png(f'{root}/art-pet/sprites/hunt/fruits/atlas_fruits.png')
    y = 48
    for it in F['items']:
        fr = F['atlas']['frames'][it['id']]['frame']
        spr = fatl[fr['y']:fr['y'] + fr['h'], fr['x']:fr['x'] + fr['w']]
        blit(cs, np.repeat(np.repeat(spr, 2, 0), 2, 1), x0, y)
        cs = label(cs, it['zh'], x0 + 70, y + 20, V3['mute'], 12)
        y += 40
    save_png(f'{out}/critters_fruits_sheet.png', cs)

def build(root, out):
    os.makedirs(out, exist_ok=True)
    icons_sheet(root, out)
    scene_sheet(root, out)
    clips_preview(root, out)
    import preview_hunt3d as PH
    if PH.J is None:
        PH.load(root, out=out)
    info = PH.steady_gif(out)
    cmp = PH.compare_before_after(out)
    print('previews →', out, 'gif', info, 'compare', cmp)

if __name__ == '__main__':
    root = sys.argv[1] if len(sys.argv) > 1 else '/workspace/m1-icons-hunt-src'
    out = sys.argv[2] if len(sys.argv) > 2 else '/workspace/game-design/m1_icons_hunt'
    build(root, out)
