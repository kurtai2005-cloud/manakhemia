"""batch3b 預覽：4x 總表、漫畫總表、GIF（訪客、蝸牛探訪、進化大場面 ×2、怪夢預兆）。
進化 render(t) 即係 timeline 嘅參考實作（遊程可以照抄）。"""
import os, sys, json, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_batch3b as BB
import batch3b_paint as B
import reactions_lib as L
from batch3b_paint import paste, canvas

OUT = BB.OUT; PV = os.path.join(OUT, "preview")
J = json.load(open(os.path.join(OUT, "batch3b.json")))
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
def font(sz): return ImageFont.truetype(FONT, sz, index=3)
def load(rel): return np.array(Image.open(os.path.join(OUT, rel)).convert("RGBA"))
def frames(rel, w):
    a = load(rel); return [a[:, i:i + w] for i in range(0, a.shape[1], w)]
ease = {"oCubic": lambda t: 1 - (1 - t) ** 3, "iCubic": lambda t: t ** 3, "ioSine": lambda t: -(math.cos(math.pi * t) - 1) / 2,
        "iBack": lambda t, s=1.70158: t * t * ((s + 1) * t - s)}
def keys(t, ts, vs, e=ease["ioSine"]):
    if t <= ts[0]: return vs[0]
    for i in range(len(ts) - 1):
        if t <= ts[i + 1]: u = (t - ts[i]) / (ts[i + 1] - ts[i]); return vs[i] + (vs[i + 1] - vs[i]) * e(u)
    return vs[-1]
def clamp(x, a=0, b=1): return max(a, min(b, x))

def xform(a, sx=1, sy=1, rot=0, piv=None):
    """最近鄰縮放／旋轉，返 (img, 新 pivot)"""
    piv = piv or (a.shape[1] // 2, a.shape[0] - 1); im = Image.fromarray(a)
    W, H = max(1, round(a.shape[1] * sx)), max(1, round(a.shape[0] * sy))
    im = im.resize((W, H), Image.NEAREST); p = (piv[0] * sx, piv[1] * sy)
    if rot:
        big = Image.new("RGBA", (W * 3, H * 3)); big.paste(im, (W, H)); big = big.rotate(-rot, Image.NEAREST, center=(W + p[0], H + p[1]))
        return np.array(big), (W + p[0], H + p[1])
    return np.array(im), p
def blit(dst, a, piv, x, y, alpha=1.0):
    a = a.copy()
    if alpha < 1:
        src = canvas(dst.shape[1], dst.shape[0]); paste(src, a, round(x - piv[0]), round(y - piv[1]))
        m = src[..., 3] == 255; dst[m, :3] = (dst[m, :3] * (1 - alpha) + src[m, :3] * alpha).astype(np.uint8); return
    paste(dst, a, round(x - piv[0]), round(y - piv[1]))
def fill(dst, col, alpha):
    c = np.array(col, float); dst[..., :3] = (dst[..., :3] * (1 - alpha) + c * alpha).astype(np.uint8)
def hexrgb(h): return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))

# ═════════ 進化 render(t) ═════════
EA = J["evolution"]["assets"]
def fr_of(k): e = EA[k]; return frames(e["file"], e["frameW"]), e["pivot"]
EVF = {k: fr_of(k) for k in EA if not k.startswith("_")}
CARDS = J["evolution"]["cards"]

def evo_render(t, old, new, scene, rng_seed=7):
    PX, PY = 97, 292
    img = BB.scene_art(scene); fore = BB.fore_art(scene)
    oa, opv = BB.pet_frame(old, "idle_01") if old != "evo_egg" else BB.pet_frame(old, "idle_01")
    na, npv = BB.pet_frame(new, "idle_01")
    # dim
    if t < 600: d = .7 * ease["ioSine"](t / 600)
    elif t < 5600: d = .7
    elif t < 6000: d = .7 - .25 * (t - 5600) / 400
    elif t < 7700: d = .45
    else: d = .45 * (1 - (t - 7700) / 300)
    over_pet = []
    layer = img.copy()
    paste_fore = True
    fill(layer, hexrgb("#1E1630"), d)
    rng = np.random.default_rng(rng_seed)
    ch = oa.shape[0]; cx, cy = PX, PY - (na.shape[0] if t > 5600 else oa.shape[0]) // 2
    # rays（後）
    if 4400 <= t < 7000:
        rf, rp = EVF["evo_rays"]; i = int((t - 4400) // 90) % len(rf)
        if not (t > 6500 and int(t // 80) % 2): blit(layer, rf[i], rp, cx, cy)
    # 寵物
    if t < 1500:
        k = clamp((t - 300) / 1200) * 1.5 if t >= 300 else 0
        dx = round(math.sin(t * .09) * k)
        a = oa
        if 900 <= t < 1500:
            iv = 120 if t < 1200 else 60
            if int((t - 900) // iv) % 2 == 0: a = BB.sil(oa)
        blit(layer, a, opv, PX + dx, PY)
    elif t < 5600:
        if t < 4400: cur = B.add_outline(np.pad(BB.sil(oa), ((1, 1), (1, 1), (0, 0))), BB.F.LAV_D); cpv = (opv[0] + 1, opv[1] + 1)
        else:
            sw = J["evolution"]["timeline"]["tracks"]; sw = [x for x in sw if x["id"] == "silhouette_swap"][0]["swapsAt"]
            n = sum(1 for s in sw if s <= t); last = max([s for s in sw if s <= t] or [4400])
            isnew = n % 2 == 1 or n == len(sw)
            cur, cpv = (BB.sil(na), npv) if isnew else (BB.sil(oa), opv)
            cur = B.add_outline(np.pad(cur, ((1, 1), (1, 1), (0, 0))), BB.F.LAV_D); cpv = (cpv[0] + 1, cpv[1] + 1)
            u = clamp((t - last) / 90); sx = 1.15 + (1 - 1.15) * u; sy = .88 + (1 - .88) * u
            cur, cpv = xform(cur, sx, sy, 0, cpv)
        if t >= 4400 or t < 1500 + 0: blit(layer, cur, cpv, PX, PY)
        elif t < 2700:  # 繭包緊：剪影仲睇到少少
            blit(layer, cur, cpv, PX, PY)
    else:
        u = t - 5600
        sx = keys(u, [0, 120, 260, 380, 500], [1.3, .9, 1.06, .98, 1]); sy = keys(u, [0, 120, 260, 380, 500], [.7, 1.12, .96, 1.01, 1])
        try:
            r = L.rig(new); face = L.face_image(r, "smug")[1] if u > 300 else None
        except Exception: face = None
        a = na.copy()
        if face is not None and face.shape == a.shape: m = face[..., 3] == 255; a[m] = face[m]
        cur, cpv = xform(a, sx, sy, 0, npv); blit(layer, cur, cpv, PX, PY)
    # 光繭
    if 1500 <= t < 4400:
        if t < 2700: f, p = EVF["evo_cocoon_form"]; i = min(5, int((t - 1500) // 200)); a = f[i]; sx = sy = 1
        elif t < 3900:
            f, p = EVF["evo_cocoon_pulse"]; u = t - 2700; ms = 150 - 60 * u / 1200; i = int(u // ms) % 4; a = f[i]
            sx = keys(u, [0, 300, 600, 900, 1200], [1, 1.04, .98, 1.06, 1]); sy = keys(u, [0, 300, 600, 900, 1200], [1, .97, 1.03, .95, 1])
        else: f, p = EVF["evo_cocoon_crack"]; i = min(3, int((t - 3900) // 125)); a = f[i]; sx = sy = 1
        a2, p2 = xform(a, sx, sy, 0, p); blit(layer, a2, p2, PX, PY)
    # 光點
    if 400 <= t < 2200:
        mf, mp = EVF["evo_mote"]
        for k in range(14):
            st = 400 + k * 600 / 14; u = (t - st) / 1100
            if not 0 <= u < 1: continue
            th0 = k * 2.4; r = 90 * (1 - ease["oCubic"](u)); th = th0 + 2.5 * math.pi * u
            blit(layer, mf[int(t // 80 + k) % 3], mp, PX + r * math.cos(th), PY - oa.shape[0] / 2 + r * math.sin(th) * .8)
    # 碎＋光圈
    if 4400 <= t < 4900:
        sf, sp = EVF["evo_shard"]; u = (t - 4400) / 500
        for k in range(8):
            th = k * math.pi / 4 + .3; dd = 40 * ease["oCubic"](u)
            if u > .8 and int(t // 50) % 2: continue
            blit(layer, sf[k % 3], sp, PX + dd * math.cos(th), PY - 30 + dd * math.sin(th) + 30 * (u * .5) ** 2 * 4)
    if 4400 <= t < 4750:
        rf, rp = EVF["evo_ring"]; blit(layer, rf[min(4, int((t - 4400) // 70))], rp, PX, PY - 28)
    # 彩紙
    if 5600 <= t < 7400:
        cf, cp = EVF["evo_confetti"]; rr = np.random.default_rng(3)
        for k in range(28):
            vx = rr.uniform(-60, 60); vy = rr.uniform(-140, -90); s = (t - 5600) / 1000; kind = k % 4
            x = PX + vx * s; y = PY - 24 + vy * s + 80 * s * s
            if y > 430: continue
            blit(layer, cf[kind * 2 + int(t // rr.integers(120, 181)) % 2], cp, x, y)
    if paste_fore:
        a = fore[..., 3:4].astype(float) / 255; layer[..., :3] = (layer[..., :3] * (1 - a) + fore[..., :3] * a).astype(np.uint8)
    # flash
    if 5600 <= t < 5900: fill(layer, (255, 255, 255), .85 * (1 - ease["oCubic"]((t - 5600) / 300)))
    # skip hint
    if 2000 <= t < 5600:
        hf, hp = EVF["evo_skip_hint"]; blit(layer, hf[int(t // 450) % 2], hp, 180, 400)
    # 名卡
    card_state = None
    if 6000 <= t < 7700:
        route = CARDS["formToCard"][new]; ca = load(CARDS["files"][route.replace("card_", "")]["file"])
        u = clamp((t - 6000) / 500)
        sc = keys(u, [0, .45, .7, .85, 1], [0.01, 1.1, .96, 1.02, 1], ease["oCubic"]); rot = keys(u, [0, .45, .7, .85, 1], [-8, 4, -2, 1, 0])
        al = 1
        if t >= 7500: v = clamp((t - 7500) / 200); sc *= 1 - .4 * ease["iBack"](v); al = 1 - v
        c2 = ca.copy(); pp = CARDS["portrait"]["petPivot"]; paste(c2, na, pp[0] - npv[0], pp[1] - npv[1])
        if sc > .05:
            a2, p2 = xform(c2, sc, sc, rot, (c2.shape[1] / 2, c2.shape[0] / 2))
            if al > .5: blit(layer, a2, p2, 97, 352)
            card_state = (sc, rot, al, u)
    return layer, card_state

def evo_gif(old, new, scene, path, step=80):
    fs = []; fnt = font(18); fnt2 = font(11)
    name = BB.form_name(new); route = CARDS["formToCard"][new]
    for t in range(0, 8000, step):
        a, cs = evo_render(t, old, new, scene)
        im = Image.fromarray(a[..., :3]).resize((390, 844), Image.NEAREST)
        if cs and cs[0] > .9 and cs[2] > .5:
            d = ImageDraw.Draw(im); tb = CARDS["textBoxes"]; ox = 97 * 2 - 168; oy = 352 * 2 - 64
            n = name[:max(0, int((t - 6400) / 30) + 1)] if t > 6400 else ""
            d.text((ox + tb["name"][0] * 2 + 8, oy + tb["name"][1] * 2 + 3), n, font=fnt, fill=(255, 255, 255), stroke_width=2, stroke_fill=(107, 86, 131))
            line = "（介紹文案：遊策寫）"
            d.text((ox + tb["line"][0] * 2 + 4, oy + tb["line"][1] * 2 + 6), line[:max(0, int((t - 6600) / 30))] if t > 6600 else "", font=fnt2, fill=(107, 86, 131))
        fs.append(im.convert("P", palette=Image.ADAPTIVE, colors=255))
    fs[0].save(path, save_all=True, append_images=fs[1:], duration=step, loop=0, optimize=True)

# ═════════ 訪客 GIF ═════════
def vis_frames(vid):
    v = J["visitors"][vid]; w = v["frameW"]; return {c: frames(v["clips"][c]["file"], w) for c in v["clips"]}, v

def visitors_gif(path):
    W, H = 3 * 70, 3 * 56; fs = []
    allv = {vid: vis_frames(vid) for vid in J["visitors"]}
    for t in range(0, 3600, 60):
        a = canvas(W, H); a[...] = (150, 196, 130, 255); a[:, :, :3][::2, ::2] = (142, 188, 124)
        for col, c in enumerate(("idle", "walk", "happy")):
            for row, vid in enumerate(allv):
                fr, v = allv[vid]; ms = v["clips"][c]["ms"]; i = int(t // ms) % 6
                if c == "happy" and t // (ms * 6) % 2: i = 0
                piv = v["pivot"]; blit(a, fr[c][i], piv, col * 70 + 35, row * 56 + 50)
        fs.append(Image.fromarray(a[..., :3]).resize((W * 4, H * 4), Image.NEAREST))
    fs[0].save(path, save_all=True, append_images=fs[1:], duration=60, loop=0, optimize=True)

def path_pt(pts, s):
    seg = [math.dist(a, b) for a, b in zip(pts, pts[1:])]; tot = sum(seg); s %= tot
    for (a, b), l in zip(zip(pts, pts[1:]), seg):
        if s <= l: u = s / l; return (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u), (b[0] - a[0])
        s -= l
    return pts[-1], 1

def visit_gif(vid, path, form="evo_hop"):
    fr, v = vis_frames(vid); piv = v["pivot"]; lp = J["visitRules"]["lead"]; pts = lp["loop"]
    hearts = BB.fx3a("fx_heart", 1)
    seq = []; Y0 = 200
    scene = BB.scene_art("H1" if vid != "firefly_vendor" else "H4"); fore = BB.fore_art("H1" if vid != "firefly_vendor" else "H4")
    letter = load(J["visitorProps"]["letter"]["file"]); seed = load(J["visitorProps"]["seed"]["file"])
    gift = (BB.L.token("leaf") if True else None)
    for t in range(0, 12000, 100):
        a = scene.copy(); items = []
        # 入場 0–3000
        if t < 3000:
            vx = 230 - (230 - 143) * (t / 3000); vy = 292; vflip = True; clip = "walk"; px_, py_ = 97, 292; pf = BB.pet_frame(form, "idle_01" if t < 2000 else "lookup_01"); pflip = False
        elif t < 3900:
            vx, vy, vflip, clip = 143, 292, True, "idle"; px_, py_ = 97, 292; pf = BB.pet_frame(form, f"smug_pose_0{1 + int((t - 3000) // 225) % 4}"); pflip = False
        elif t < 9500:
            s = (t - 3900) / 1000 * 26
            (px_, py_), dirx = path_pt(pts, s + 0.01); pflip = dirx < 0
            (vx, vy), vd = path_pt(pts, max(0, s - 30) + 0.01) if s > 30 else ((143 - (143 - pts[0][0]) * 0, 292), -1)
            vflip = vd < 0; clip = "walk"
            pf = BB.pet_frame(form, f"walk_happy_0{1 + int(t // 110) % 6}")
            if s <= 30: vx, vy = 143 - s * 0, 292; clip = "idle"
        else:
            px_, py_, pflip = 97, 292, False; vx, vy, vflip = 143, 292, True
            u = t - 9500; clip = "happy" if u >= 300 and u < 900 else "idle"
            pf = BB.pet_frame(form, "cheer_jump_0%d" % (1 + int(u // 120) % 6) if 300 <= u < 1020 else "idle_01")
        ms = v["clips"][clip]["ms"]; i = int(t // ms) % 6
        if clip == "happy": i = min(5, int((t - 9800) // ms))
        vf = fr[clip][i]; vp = list(piv)
        if vflip: vf = B.flipx(vf); vp = [vf.shape[1] - 1 - piv[0], piv[1]]
        pa, pp = pf
        if pflip: pa = B.flipx(pa); pp = (pa.shape[1] - 1 - pp[0], pp[1])
        for (yy, img_, p_, x_) in sorted([(vy, vf, vp, vx), (py_, pa, pp, px_)], key=lambda z: z[0]):
            blit(a, img_, p_, x_, yy)
        if t >= 9500:
            u = t - 9500
            if u < 300: blit(a, seed, (5, 11), 160 - u / 300 * 17, 230 + u / 300 * 30)
            sg = -1 if vflip else 1
            anc = lambda nm: (vx + sg * (v["anchors"][nm][0] - piv[0]), vy + (v["anchors"][nm][1] - piv[1]))
            if 300 <= u < 1200: hh, hp = hearts; hx, hy = anc("head"); blit(a, hh, hp, hx, hy - 3 - (u - 300) / 100)
            if vid == "snail_postman" and u >= 1200:
                k = clamp((u - 1200) / 400); bx, by = anc("bag"); hx, hy = anc("head"); blit(a, letter, (6, 9), bx + (hx - bx) * k, by + (hy - 8 - by) * ease["oCubic"](k))
        f = fore[..., 3:4].astype(float) / 255; a[..., :3] = (a[..., :3] * (1 - f) + fore[..., :3] * f).astype(np.uint8)
        seq.append(Image.fromarray(a[Y0:Y0 + 130, :, :3]).resize((195 * 3, 130 * 3), Image.NEAREST))
    seq[0].save(path, save_all=True, append_images=seq[1:], duration=100, loop=0, optimize=True)

def omen_gif(path, form="evo_guard_moon"):
    db, dp = EVF["omen_dream_bubble"]; ic, ip = EVF["omen_dream_icons"]; ctr = EA["_dreamCenter"]
    r = L.rig(form); ht = r.anchors["headTop"]; seq = []; scene = BB.scene_art("H4")
    for t in range(0, 6000, 80):
        a = scene.copy(); pa, pp = BB.pet_frame(form, f"sleep_loop_0{1 + int(t // 400) % 4}")
        blit(a, pa, pp, 97, 292)
        ax, ay = 97 - pp[0] + ht[0] + 4, 292 - pp[1] + ht[1] - 2
        cyc = t % 3000
        if cyc < 2640:
            i = 0 if cyc < 220 else 1 if cyc < 440 else 2
            blit(a, db[i], dp, ax, ay)
            if i == 2:
                k = (t // 3000) % 6; bob = int(cyc // 400) % 2
                blit(a, ic[k], ip, ax - dp[0] + ctr[0], ay - dp[1] + ctr[1] - bob)
        elif cyc < 2900:
            pf, pfp = BB.fx3a("fx_puff", min(2, int((cyc - 2640) // 90))) if "fx_puff" in BB.FX3A else (None, None)
            if pf is not None: blit(a, pf, pfp, ax + 12, ay - 14)
        seq.append(Image.fromarray(a[200:310, 30:165, :3]).resize((135 * 4, 110 * 4), Image.NEAREST))
    seq[0].save(path, save_all=True, append_images=seq[1:], duration=80, loop=0, optimize=True)

# ═════════ 總表 ═════════
def sheet():
    items = []   # (label, img)
    for vid, v in J["visitors"].items():
        for c in ("idle", "walk", "happy"): items.append((f"{v['name']} {c}", load(v["clips"][c]["file"])))
        items.append((f"{v['name']} 頭像／徽章／擺設", np.concatenate([np.pad(load(v["portrait"]["file"]), ((0, max(0, 30 - 26)), (0, 4), (0, 0))),
                                                                     np.pad(load(v["badge"]["file"]), ((0, 30 - 18), (0, 4), (0, 0))),
                                                                     np.pad(load(v["decor"]["file"]), ((0, 30 - load(v["decor"]["file"]).shape[0]), (0, 4), (0, 0)))], 1)))
    pr = J["visitorProps"]
    items.append(("小道具：信／種子／友好心", np.concatenate([np.pad(load(pr[k]["file"]), ((0, 12 - load(pr[k]["file"]).shape[0]), (0, 4), (0, 0))) for k in ("letter", "seed", "friend_heart")], 1)))
    for k, e in EA.items():
        if k.startswith("_"): continue
        items.append((k, load(e["file"])))
    rows = []; f = font(22); k = 4
    for lab, img in items:
        im = Image.fromarray(img).resize((img.shape[1] * k, img.shape[0] * k), Image.NEAREST)
        W = max(im.width, 600) + 20; H = im.height + 40
        r = Image.new("RGB", (W, H), (88, 76, 120)); r.paste(im, (10, 34), im); ImageDraw.Draw(r).text((10, 4), lab, font=f, fill=(255, 255, 255)); rows.append(r)
    cards = [load(c["file"]) for c in CARDS["files"].values()]
    cr = Image.new("RGB", (2 * (168 * 3 + 10) + 10, 5 * (64 * 3 + 40) + 40), (88, 76, 120)); d = ImageDraw.Draw(cr); d.text((10, 4), "名卡 9 路線＋base（頭像窗 = 引擎畫新形態，字 = 引擎）", font=f, fill=(255, 255, 255))
    for i, (r_, c) in enumerate(zip(CARDS["files"], cards)):
        x = 10 + (i % 2) * (168 * 3 + 10); y = 40 + (i // 2) * (64 * 3 + 40)
        cc = c.copy()
        sample = {"base": "evo_hop"}.get(r_, f"evo_still_{r_}")
        pa, pp = BB.pet_frame(sample, "idle_01"); P_ = CARDS["portrait"]["petPivot"]; paste(cc, pa, P_[0] - pp[0], P_[1] - pp[1])
        im = Image.fromarray(cc).resize((168 * 3, 64 * 3), Image.NEAREST); cr.paste(im, (x, y + 24), im); d.text((x, y), f"card_{r_}（示範：{BB.form_name(sample)}）", font=font(18), fill=(255, 255, 255))
    rows.append(cr)
    W = max(r.width for r in rows); H = sum(r.height for r in rows)
    out = Image.new("RGB", (W, H), (88, 76, 120)); y = 0
    for r in rows: out.paste(r, (0, y)); y += r.height
    out.save(os.path.join(OUT, "batch3b_overview_4x.png"))

def comics_sheet():
    f = font(14); k = 2; route = "ember"
    rows = []
    for n, node in J["comics"]["nodes"].items():
        ims = [load(f"comics/{p.replace('{route}', route)}.png") for p in node["panels"]]
        caps = J["comics"]["captionDraft"][n]
        W = 4 * (92 * k + 8) + 8; H = 84 * k + 70
        r = Image.new("RGB", (W, H), (250, 244, 236)); d = ImageDraw.Draw(r)
        d.text((8, 4), f"{n}：{BB.form_name(node['from'].format(r=route))} → {BB.form_name(node['to'].format(r=route))}", font=f, fill=(107, 86, 131))
        for i, (im, c) in enumerate(zip(ims, caps)):
            x = 8 + i * (92 * k + 8); I = Image.fromarray(im).resize((92 * k, 84 * k), Image.NEAREST); r.paste(I, (x, 24), I)
            d.text((x + 2, 24 + 84 * k + 4), c.replace("{route}", BB.ROUTE_ZH[route]), font=font(12), fill=(90, 70, 110))
        rows.append(r)
    W = rows[0].width; out = Image.new("RGB", (W, sum(r.height for r in rows)), (250, 244, 236)); y = 0
    for r in rows: out.paste(r, (0, y)); y += r.height
    out.save(os.path.join(OUT, "comics_overview_2x.png"))
    # 路線換圖（第 4／5 節點尾格 ×9）
    keys = [f"n4_p4_{r}" for r in BB.F.ROUTES] + [f"n5_p4_{r}" for r in BB.F.ROUTES]
    ims = [load(f"comics/{k_}.png") for k_ in keys]
    g = np.concatenate([np.concatenate(ims[i:i + 9], 1) for i in (0, 9)], 0)
    Image.fromarray(g).resize((g.shape[1] * 2, g.shape[0] * 2), Image.NEAREST).save(os.path.join(OUT, "comics_route_variants_2x.png"))
    # 日記頁 mock（art 195×422，n1）
    page = np.zeros((422, 195, 4), np.uint8); page[...] = (255, 249, 238, 255)
    for i, p in enumerate(J["comics"]["nodes"]["n1"]["panels"]):
        x, y = J["comics"]["layout"]["pos"][i]; paste(page, load(f"comics/{p}.png"), x, y)
    im = Image.fromarray(page).resize((390, 844), Image.NEAREST); d = ImageDraw.Draw(im)
    for i, c in enumerate(J["comics"]["captionDraft"]["n1"]):
        x, y = J["comics"]["layout"]["pos"][i]; d.text((x * 2 + 4, (y + 86) * 2), c, font=font(14), fill=(107, 86, 131))
    d.text((20, 70), "團絨日記・第 1 話（mock）", font=font(22), fill=(107, 86, 131))
    im.save(os.path.join(PV, "diary_page_n1_2x.png"))

def main():
    os.makedirs(PV, exist_ok=True)
    sheet(); comics_sheet()
    visitors_gif(os.path.join(PV, "visitors_idle_walk_happy_4x.gif"))
    visit_gif("snail_postman", os.path.join(PV, "visit_snail_postman_3x.gif"))
    visit_gif("mushroom_granny", os.path.join(PV, "visit_mushroom_granny_3x.gif"), "evo_guard_soft")
    visit_gif("firefly_vendor", os.path.join(PV, "visit_firefly_vendor_3x.gif"), "evo_still_lumi")
    evo_gif("evo_hop", "evo_guard_ember", "H4", os.path.join(PV, "evolution_hop_to_guard_ember_2x.gif"))
    evo_gif("evo_guard_moon", "evo_still_moon", "H2", os.path.join(PV, "evolution_guard_moon_to_still_moon_2x.gif"))
    omen_gif(os.path.join(PV, "omen_dream_4x.gif"))
    # 關鍵幀靜圖（俾冇 GIF 嘅地方睇）
    ts = [300, 1200, 2000, 3200, 4200, 4700, 5300, 5700, 6600]
    ims = [Image.fromarray(evo_render(t, "evo_hop", "evo_guard_ember", "H4")[0][150:390, :, :3]) for t in ts]
    W = len(ims) * 197; out = Image.new("RGB", (W, 240 + 20), (30, 24, 44)); d = ImageDraw.Draw(out)
    for i, (t, im) in enumerate(zip(ts, ims)): out.paste(im, (i * 197, 20)); d.text((i * 197 + 4, 2), f"{t}ms", font=font(13), fill=(255, 255, 255))
    out.resize((W * 2, 260 * 2), Image.NEAREST).save(os.path.join(PV, "evolution_keyframes_2x.png"))
    print("previews ok")

if __name__ == "__main__":
    main()
