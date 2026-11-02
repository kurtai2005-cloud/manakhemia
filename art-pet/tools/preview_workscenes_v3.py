# -*- coding: utf-8 -*-
"""第 8 批 工作場景預覽：出 contact sheets 去 $GD_WORKSCENES_V3（預設 /workspace/game-design/workscenes_v3/），並抄關鍵張去 scenes/work_v3/preview/。"""
import os, sys, json, math, shutil
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_workscenes_v3 as B
import ws3_sprites as P
import ui_hd2d_v3_lib as L
GD = os.environ.get('GD_WORKSCENES_V3', '/workspace/game-design/workscenes_v3')
REP = {'S': 'S2', 'M': 'S4C', 'L': 'evo_still_tide'}
BG = (28, 32, 54)
def lab(im, xy, s, sz=20, col=(250, 240, 220)):
    d = ImageDraw.Draw(im); d.text(xy, s, font=L.F('sans', sz), fill=col)
def on_bg(arr, bg=BG):
    o = np.ones(arr.shape[:2] + (3,)) * np.array(bg) / 255; o = o * (1 - arr[..., 3:]) + arr[..., :3] * arr[..., 3:]; return Image.fromarray(B.to8(o))
def sheet_scenes():
    ims = [B.compose3x(k) for k in B.SCENE_KEYS]; W, H = 585 // 2, 1266 // 2
    out = Image.new('RGB', (W * 5 + 60, H + 70), BG)
    for i, (k, im) in enumerate(zip(B.SCENE_KEYS, ims)):
        out.paste(im.resize((W, H), Image.LANCZOS), (10 + i * (W + 10), 60)); lab(out, (14 + i * (W + 10), 18), f'{k}・{B.GRADE[k]["name"]}', 24)
    return out, ims
def sheet_tod():
    W, H = 585 // 3, 1266 // 3; ks = ['post', 'garden', 'kitchen']; out = Image.new('RGB', (W * 4 * 3 + 130, H * 1 + 70), BG); x = 10
    for k in ks:
        for t in B.TOD:
            im = B.compose3x(k, tod=t, particles=False).resize((W, H), Image.LANCZOS); out.paste(im, (x, 60)); lab(out, (x + 4, 18), f'{k} {t}', 20); x += W + 10
        x += 10
    return out
def sheet_props():
    J = json.load(open(f'{B.OUT}/workscenes_v3.json'))['props']; rows = []
    for k, e in J.items():
        a = B.ld(f'{B.OUT}/{e["sheet"]}'); im = on_bg(a, (60, 66, 96))
        if 'glow' in e:
            g = B.ld(f'{B.OUT}/{e["glow"]["sheet"]}'); base = np.asarray(im).astype(float) / 255; base = np.clip(base + g[..., :3] * g[..., 3:] * .9, 0, 1)
            base = base * (1 - a[..., 3:]) + a[..., :3] * a[..., 3:]; im = Image.fromarray(B.to8(base))
        rows.append((k, e, im))
    W = max(r[2].width for r in rows) + 260; H = sum(r[2].height + 16 for r in rows) + 20; out = Image.new('RGB', (W, H), BG); y = 10
    for k, e, im in rows: out.paste(im, (250, y)); lab(out, (10, y + 6), k, 22); lab(out, (10, y + 36), f'{e["zh"]}・{e["frames"]} 幀', 20, (220, 200, 160)); y += im.height + 16
    return out
def sheet_deco_hats_icons():
    J = json.load(open(f'{B.OUT}/workscenes_v3.json')); out = Image.new('RGB', (1500, 1010), BG); x = 20
    lab(out, (20, 12), 'Lv3 擺設', 26)
    for j, e in J['decoLv3'].items():
        a = B.ld(f'{B.OUT}/{e["img"]}'); im = on_bg(a, (60, 66, 96)); out.paste(im, (x, 56)); lab(out, (x, 56 + im.height + 6), e['zh'], 20); x += im.width + 60
    lab(out, (20, 230), 'Lv5 職業帽（S/M/L，戴喺代表寵物上）', 26); y = 270
    for j in B.JOBS:
        x = 20; lab(out, (x, y + 70), B.JOB_ZH[j], 22); x += 90
        for sz in ('S', 'M', 'L'):
            a = B.pet_frame(REP[sz], {}, hat_job=j); bb = np.argwhere(a[..., 3] > 0); y0, x0 = bb.min(0); y1, x1 = bb.max(0)
            crop = a[max(0, y0 - 6):y1 + 6, max(0, x0 - 6):x1 + 6]; im = on_bg(crop, (60, 66, 96)); im = im.resize((im.width * 2 // 3, im.height * 2 // 3), Image.NEAREST)
            out.paste(im, (x, y + 150 - im.height)); lab(out, (x, y + 152), f'{sz}・{REP[sz]}', 18); x += im.width + 30
        if j in ('post', 'garden'): pass
        y += 0
        if j == 'garden': y = 270
        if j in ('post',): out_x_shift = 0
    # 4 職排兩欄
    out2 = Image.new('RGB', (1500, 1010), BG); out2.paste(out.crop((0, 0, 1500, 260)), (0, 0)); y = 270
    for i, j in enumerate(B.JOBS):
        cx = 20 + (i % 2) * 740; cy = 270 + (i // 2) * 210; x = cx; lab(out2, (x, cy + 60), B.JOB_ZH[j], 22); x += 90
        for sz in ('S', 'M', 'L'):
            a = B.pet_frame(REP[sz], {}, hat_job=j); bb = np.argwhere(a[..., 3] > 0); y0, x0 = bb.min(0); y1, x1 = bb.max(0)
            crop = a[max(0, y0 - 6):y1 + 6, max(0, x0 - 6):x1 + 6]; im = on_bg(crop, (60, 66, 96))
            if im.height > 170: im = im.resize((im.width * 170 // im.height, 170), Image.NEAREST)
            out2.paste(im, (x, cy + 175 - im.height)); lab(out2, (x, cy + 178), f'{sz}・{REP[sz]}', 18); x += im.width + 24
    lab(out2, (20, 700), '產品 icon 48px（上：基本；下：機率版＋光）', 26); x = 20
    for i, (nm, e) in enumerate(J['icons'].items()):
        a = B.ld(f'{B.OUT}/{e["img"]}'); bgc = np.ones((72, 72, 3)) * np.array((60, 66, 96)) / 255
        if 'glow' in e: g = B.ld(f'{B.OUT}/{e["glow"]["img"]}'); bgc = np.clip(bgc + g[..., :3] * g[..., 3:] * .9, 0, 1)
        bgc[12:60, 12:60] = bgc[12:60, 12:60] * (1 - a[..., 3:]) + a[..., :3] * a[..., 3:]
        im = Image.fromarray(B.to8(bgc)).resize((144, 144), Image.NEAREST); xx = 20 + (i // 2) * 360 + (i % 2) * 170
        out2.paste(im, (xx, 750)); lab(out2, (xx, 900), e['zh'], 20); lab(out2, (xx, 928), '機率版' if e['kind'] == 'probability' else '基本', 18, (220, 200, 160))
    return out2
def clip_strip(job, sz, kind, form, bg=(60, 66, 96)):
    J = json.load(open(f'{B.OUT}/workscenes_v3.json'))['clips'][f'{job}_{sz}_{kind}']; ims = []
    for f in range(J['frames']):
        back, front, glow = B.clip_layers(job, sz, kind, f); pet = B.pet_frame(form, J['petTransform'][f])
        c = np.ones(back.shape[:2] + (3,)) * np.array(bg) / 255
        for l in (back, pet, front): c = c * (1 - l[..., 3:]) + l[..., :3] * l[..., 3:]
        if glow is not None: c = np.clip(c + glow[..., :3] * glow[..., 3:] * .8, 0, 1)
        ims.append(Image.fromarray(B.to8(c)))
    return ims
def sheet_clips(job):
    W, H = P.CW * 3 // 2, P.CH * 3 // 2; out = Image.new('RGB', (W * 8 + 240, (H + 40) * 6 + 30), BG); y = 20
    for sz in ('S', 'M', 'L'):
        for kind in ('loop', 'done'):
            ims = clip_strip(job, sz, kind, REP[sz]); lab(out, (10, y + 40), f'{sz} {kind}', 22); lab(out, (10, y + 70), B.CLIP_ZH[(job, kind)], 20, (220, 200, 160)); lab(out, (10, y + 100), REP[sz], 18, (180, 190, 220))
            for i, im in enumerate(ims): out.paste(im.resize((W, H), Image.NEAREST), (230 + i * W, y))
            y += H + 40
    return out
def gif(job, sz='M'):
    ims = clip_strip(job, sz, 'loop', REP[sz]) * 2 + clip_strip(job, sz, 'done', REP[sz])
    ims = [i.resize((i.width * 2 // 3, i.height * 2 // 3), Image.NEAREST) for i in ims]
    ims[0].save(f'{GD}/clip_{job}_{sz}.gif', save_all=True, append_images=ims[1:], duration=[110] * 16 + [140] * 4, loop=0)
def run():
    os.makedirs(GD, exist_ok=True); PV = f'{B.OUT}/preview'; os.makedirs(PV, exist_ok=True)
    sc, ims = sheet_scenes(); sc.save(f'{GD}/ws_scenes.png', optimize=True)
    sheet_tod().save(f'{GD}/ws_tod.png', optimize=True)
    sheet_props().save(f'{GD}/ws_props.png', optimize=True)
    sheet_deco_hats_icons().save(f'{GD}/ws_deco_hats_icons.png', optimize=True)
    for j in B.JOBS: sheet_clips(j).save(f'{GD}/ws_clips_{j}.png', optimize=True); gif(j)
    for f in ('ws_scenes', 'ws_props', 'ws_deco_hats_icons'): shutil.copy(f'{GD}/{f}.png', f'{PV}/{f}.png')
    if os.path.isdir(f'{B.OUT}/mockups'):
        mk = sorted(x for x in os.listdir(f'{B.OUT}/mockups') if x.endswith('.png')); W, H = 585 // 2, 1266 // 2
        out = Image.new('RGB', ((W + 10) * 4 + 10, (H + 50) * ((len(mk) + 3) // 4) + 10), BG)
        for i, m in enumerate(mk):
            im = Image.open(f'{B.OUT}/mockups/{m}').convert('RGB').resize((W, H), Image.LANCZOS); x = 10 + (i % 4) * (W + 10); y = 10 + (i // 4) * (H + 50)
            out.paste(im, (x, y + 40)); lab(out, (x, y + 6), m[:-4], 22)
        out.save(f'{GD}/ws_mockups.png', optimize=True); shutil.copy(f'{GD}/ws_mockups.png', f'{PV}/ws_mockups.png')
        for m in mk: shutil.copy(f'{B.OUT}/mockups/{m}', f'{GD}/{m}')
    print('preview ->', GD, sorted(os.listdir(GD)))
if __name__ == '__main__': run()
