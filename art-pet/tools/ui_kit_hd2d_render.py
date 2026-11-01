# 《微光小圃》HD-2D kit 參考渲染器：只讀 atlas JSON 砌畫面（= engine 應有嘅 drawImage／9-slice 行為）。
import json, os
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.join(HERE, '..', 'ui', 'kit_hd2d')
SANS = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
SERIF = '/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc'

class Kit:
    def __init__(self, scale=3):
        self.s = scale
        self.A = json.load(open(f'{KIT}/atlas/ui_hd2d@{scale}x.json')); self.Aim = Image.open(f'{KIT}/atlas/ui_hd2d@{scale}x.png').convert('RGBA')
        self.I = json.load(open(f'{KIT}/atlas/icons_hd2d@{scale}x.json')); self.Iim = Image.open(f'{KIT}/atlas/icons_hd2d@{scale}x.png').convert('RGBA')
        self.F = json.load(open(f'{KIT}/fonts/fonts_hd2d.json'))['fonts']
        self.Fim = {k: Image.open(f'{KIT}/fonts/{v["image"]}').convert('RGBA') for k, v in self.F.items()}
        self._fc = {}
    def spr(self, n):
        f = self.A['frames'][n]; return self.Aim.crop((f['x'], f['y'], f['x'] + f['w'], f['y'] + f['h'])), f
    def draw(self, bd, n, x, y, w=None, h=None, alpha=1.0):
        im, f = self.spr(n); s = self.s
        bx, by, bw, bh = f['box']; aw, ah = f['art']
        w = aw if w is None else w; h = ah if h is None else h
        tw, th = round(w * s), round(h * s)
        if (tw, th) != (bw, bh):
            if 'nine' in f: im = self.nine(im, f, tw - bw, th - bh)
            else:
                fx, fy = tw / bw, th / bh
                im = im.resize((max(1, round(im.width * fx)), max(1, round(im.height * fy))), Image.LANCZOS); bx, by = bx * fx, by * fy
        if alpha < 1: im.putalpha(im.getchannel('A').point(lambda v: int(v * alpha)))
        bd.alpha_composite(im, (round(x * s - bx), round(y * s - by)))
    def nine(self, im, f, dw, dh):
        l, t, r, b = f['nine']; W, H = im.size
        if f['slice'] == '3h': t = b = 0; dh = 0
        if f['slice'] == '3v': l = r = 0; dw = 0
        xs = [0, l, W - r, W]; ys = [0, t, H - b, H]
        nx = [0, l, W - r + dw, W + dw]; ny = [0, t, H - b + dh, H + dh]
        out = Image.new('RGBA', (W + dw, H + dh), (0, 0, 0, 0))
        for i in range(3):
            for j in range(3):
                sw, sh = xs[i + 1] - xs[i], ys[j + 1] - ys[j]; tw, th = nx[i + 1] - nx[i], ny[j + 1] - ny[j]
                if sw <= 0 or sh <= 0 or tw <= 0 or th <= 0: continue
                p = im.crop((xs[i], ys[j], xs[i + 1], ys[j + 1]))
                if (tw, th) != (sw, sh): p = p.resize((tw, th), Image.BILINEAR)
                out.alpha_composite(p, (nx[i], ny[j]))
        return out
    def drawc(self, bd, n, cx, cy, scale=1.0, alpha=1.0):
        im, f = self.spr(n); s = self.s
        if scale != 1: im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
        if alpha < 1: im.putalpha(im.getchannel('A').point(lambda v: int(v * alpha)))
        px, py = f['pivot']
        bd.alpha_composite(im, (round(cx * s - px * scale), round(cy * s - py * scale)))
    def icon(self, bd, kind, cx, cy, size=16, alpha=1.0):
        f = self.I['icons'][kind]; im = self.Iim.crop((f['x'], f['y'], f['x'] + f['w'], f['y'] + f['h']))
        sc = size / 24; im = im.resize((max(1, round(im.width * sc)), max(1, round(im.height * sc))), Image.LANCZOS)
        if alpha < 1: im.putalpha(im.getchannel('A').point(lambda v: int(v * alpha)))
        bx, by, bw, bh = f['box']; s = self.s
        bd.alpha_composite(im, (round(cx * s - (bx + bw / 2) * sc), round(cy * s - (by + bh / 2) * sc)))
    def btext(self, bd, font, txt, x, y, anchor='l', scale=1.0):
        """bitmap font; x,y art (y = baseline). px fonts integer-scaled nearest."""
        F = self.F[font]; G = F['glyphs']; im = self.Fim[font]; s = self.s
        k = (s if F['scale'] == 1 else s / F['scale']) * scale
        if F['scale'] == 1: k = max(1, round(k))
        width = sum(G[c]['adv'] for c in txt if c in G) * k
        px = x * s - (width / 2 if anchor == 'm' else width if anchor == 'r' else 0); py = y * s
        for c in txt:
            g = G.get(c)
            if not g: continue
            if g['w']:
                gi = im.crop((g['x'], g['y'], g['x'] + g['w'], g['y'] + g['h']))
                gi = gi.resize((round(g['w'] * k), round(g['h'] * k)), Image.NEAREST if F['scale'] == 1 else Image.LANCZOS)
                bd.alpha_composite(gi, (round(px + g['xoff'] * k), round(py + g['yoff'] * k)))
            px += g['adv'] * k
    def text(self, bd, txt, x, y, size, fill=(255, 245, 220), kind='sans', stroke=0.9, scol=(26, 18, 48), anchor='mm'):
        s = self.s; key = (kind, round(size * s))
        if key not in self._fc: self._fc[key] = ImageFont.truetype(SANS if kind == 'sans' else SERIF, key[1], index=4)
        ImageDraw.Draw(bd).text((x * s, y * s), txt, font=self._fc[key], fill=fill, anchor=anchor,
                                stroke_width=round(stroke * s) if stroke else 0, stroke_fill=scol)
    def lbl(self, bd, key, cx, cy): self.drawc(bd, 'lbl_' + key, cx, cy)
