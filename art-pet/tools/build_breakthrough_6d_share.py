#!/usr/bin/env python3
"""breakthrough 6d 社交（分享碼／QR／影子探訪／蛋碼）— 美術 builder（遊美 2026-11-02）
跟 HD-2D UI kit v2（art-pet/ui/kit_hd2d_v2）：金邊海軍藍、頂 plaque、9-slice 一律 tile 唔拉伸、alpha 0／255、FP12 起字（描邊＋影）。
輸出 art/breakthrough/6d/：新零件（qr_frame／code_field／share_card_bg／shadow_mask）、icon ×7、朋友牌 32px、4 個 3x mockup、share6d.json、preview_6d_3x.png。
純 Pillow／numpy 程序化像素；QR 喺 mockup 係「示意」圖樣（真 QR 由 code 用 lib 生 module，整數 px 畫入 qr_frame 白位）。"""
import os, sys, json, hashlib
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import hd2d_v2_px as X
from hd2d_v2_px import P, FILLS
import ui_hd2d_v2_icons as UI
import build_ui_hd2d_v2_mockups as M
from bt6_px import Spr, render, save, ncol, over, LINE, hx

ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "art/breakthrough/6d")
SW, SH = 195, 422
TEXTLOG = []          # 每次落字：size、前景、描邊、底 → validator 驗 FP12／對比

def arr(im): return np.array(im.convert("RGBA"))
def pim(a): return Image.fromarray(np.ascontiguousarray(a), "RGBA")
def save2(a, rel):
    p = os.path.join(OUT, rel); os.makedirs(os.path.dirname(p), exist_ok=True)
    save(a, p); save(a, p.replace(".png", "@3x.png"), 3)
    return {"1x": rel, "3x": rel.replace(".png", "@3x.png"), "size": [int(a.shape[1]), int(a.shape[0])], "colors": ncol(a)}
def c3(k): return tuple(int(v) for v in P[k][:3])

# ------------------------------------------------------------------ 字（FP12 TTF，關 AA；kit 規則：描邊＋1px 影）
def T(bd, t, x, y, col='white', col2='g_hi', anchor='l', bg='nv3', screen=None):
    im = X.text_img(t, 12, col=col, col2=col2)
    if anchor == 'm': x -= im.width / 2
    elif anchor == 'r': x -= im.width
    X.put(bd, im, x - 1, y - im.height / 2)
    TEXTLOG.append({"screen": screen, "text": t, "size": 12, "fg": c3(col), "fg2": c3(col2 or col), "outline": c3('line'), "bg": c3(bg) if isinstance(bg, str) else bg})
    return im.width

# ------------------------------------------------------------------ 新零件（9-slice，mode＝tile）
def qr_frame_src():
    """20×20，nine [6,6,6,6]：外描＋金 2px（左上亮右下暗）＋內描＋白 quiet zone；四角金角括號"""
    n = 20; a = np.zeros((n, n, 4), np.uint8); yy, xx = np.mgrid[0:n, 0:n]
    a[:] = P['g_mid']; a[(xx <= 2) | (yy <= 2)] = P['g_hi']; a[(xx >= n - 3) | (yy >= n - 3)] = P['g_lo']
    a[((xx <= 2) & (yy >= n - 3)) | ((yy <= 2) & (xx >= n - 3))] = P['g_mid']
    a[(xx == 0) | (yy == 0) | (xx == n - 1) | (yy == n - 1)] = P['line']
    a[3:n - 3, 3:n - 3] = P['line']; a[4:n - 4, 4:n - 4] = P['white']
    for cx, cy in ((1, 1), (n - 2, 1), (1, n - 2), (n - 2, n - 2)): a[cy, cx] = P['g_br']
    for (x0, y0) in ((0, 0), (n - 1, 0), (0, n - 1), (n - 1, n - 1)): a[y0, x0] = 0
    return a
def code_field_src(on=False):
    """24×20 3h nine [6,0,6,0]：凹入嘅深藍輸入格（內陰影喺左上），on＝金邊亮（focus）"""
    w, h = 24, 20; a = np.zeros((h, w, 4), np.uint8); yy, xx = np.mgrid[0:h, 0:w]
    rim_hi, rim_lo = (P['g_hi'], P['g_mid']) if on else (P['g_mid'], P['g_lo'])
    a[:] = rim_hi; a[(yy >= h - 2)] = rim_hi; a[(yy <= 1)] = rim_lo
    a[(xx == 0) | (yy == 0) | (xx == w - 1) | (yy == h - 1)] = P['line']
    a[2:h - 2, 2:w - 2] = P['line']; a[3:h - 3, 3:w - 3] = P['nv3']; a[3, 3:w - 3] = P['nv4'] if 'nv4' in P else P['line']; a[3:h - 3, 3] = a[3, 3]
    a[h - 4, 4:w - 3] = P['nv2']
    for (x0, y0) in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)): a[y0, x0] = 0
    return a
def tile9(src, nine, w, h, sl='9'):
    l, t, r, b = nine
    cm = M._map(int(w), l, r, src.shape[1]); rm = M._map(int(h), t, b, src.shape[0]) if sl == '9' else np.arange(src.shape[0])
    return src[rm][:, cm]
def shadow_mask():
    """4×4 1-bit：影子形態用棋盤 50% 抽走像素（取代半透明），code：pet 像素 ∧ mask＝畫"""
    a = np.zeros((4, 4, 4), np.uint8); yy, xx = np.mgrid[0:4, 0:4]; a[(xx + yy) % 2 == 0] = (255, 255, 255, 255); return a

def ghost(petrgba, tint='vi1'):
    """影子示意：剪影 → 兩色（vi1／vi2）＋棋盤抽像素；冇半透明"""
    a = petrgba.copy(); m = a[..., 3] == 255; yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]]
    lum = a[..., :3] @ np.array([.299, .587, .114]); o = np.zeros_like(a)
    o[m & (lum >= 120)] = P['vi0']; o[m & (lum < 120)] = P['vi1']; o[m & (lum < 60)] = P['vi2']
    o[(xx + yy) % 2 == 1] = 0; return o

# ------------------------------------------------------------------ icon（16×16，同 kit ic_*）
def icons():
    out = {}
    def ic_share(i): i.R(1, 6, 10, 14, 'c', cut=1); i.R(3, 8, 8, 12, 'C'); i.PG([(5.5, 10), (11.5, 4), (9, 1.5), (14.2, 1.5), (14.2, 6.8), (12.2, 4.8), (7.5, 11.5)], 'y')
    def ic_copy(i): i.R(5, 1, 14, 11, 's', cut=1); i.R(1, 4, 10, 14, 'c', cut=1); i.P([(3, 7), (4, 7), (5, 7), (6, 7), (7, 7), (3, 9), (4, 9), (5, 9), (6, 9), (3, 11), (4, 11), (5, 11), (6, 11), (7, 11)], 'S')
    def ic_paste(i): i.R(2, 3, 13, 14, 'n', cut=1); i.R(4, 5, 11, 12, 'c'); i.R(5, 1, 10, 4, 's', cut=1); i.P([(5, 7), (6, 7), (7, 7), (8, 7), (9, 7), (5, 9), (6, 9), (7, 9), (8, 9), (5, 11), (6, 11), (7, 11)], 'S')
    def ic_photo(i): i.R(1, 3, 14, 13, 'c', cut=1); i.R(3, 5, 12, 11, 'b'); i.PG([(3, 11), (6.5, 6.5), (9, 9.5), (10.5, 8), (12.9, 11.9), (3, 11.9)], 'g'); i.C(10.5, 6.5, 1.4, 'y')
    def ic_qr(i):
        i.R(1, 1, 14, 14, 'c', cut=1)
        for (x, y) in ((2, 2), (9, 2), (2, 9)): i.R(x, y, x + 4, y + 4, 'u'); i.R(x + 1, y + 1, x + 3, y + 3, 'c'); i.P([(x + 2, y + 2)], 'U')
        i.P([(10, 10), (12, 10), (11, 11), (10, 12), (12, 12), (13, 13), (9, 13), (13, 9)], 'U')
    def ic_friend(i):
        i.C(5, 10, 4.4, 'c'); i.C(11, 10, 4.4, 'p'); i.C(3, 6, 1.5, 'c'); i.C(13, 6, 1.5, 'p')
        i.face(5, 10, 2, 'dot', blush=False); i.face(11, 10, 2, 'dot', blush=False)
        i.A(6, 1, ['_r_r_', 'rrrrr', '_rrr_', '__r__'])
    def ic_egg_code(i):
        i.E(7.5, 8.5, 5.6, 6.6, 'c'); i.A(5, 6, ['_v_v_', 'vvvvv', '_v_v_', 'vvvvv', '_v_v_'])
    for n, fn in (('ic_share', ic_share), ('ic_copy', ic_copy), ('ic_paste', ic_paste), ('ic_photo', ic_photo), ('ic_qr', ic_qr), ('ic_friend', ic_friend), ('ic_egg_code', ic_egg_code)):
        ic = UI.Ic(); fn(ic); out[n] = np.array(UI.render(ic))
    return out

def friend_badge():
    """32×32 朋友牌：金圓勳章＋深藍窗＋兩隻團絨（奶白／粉）＋心＋粉絲帶尾；≤12 色"""
    s = Spr(32, 32)
    s.PG([(9, 22), (6, 30.4), (11, 27.5), (14, 30.4), (14, 23)], 'p'); s.PG([(23, 22), (26, 30.4), (21, 27.5), (18, 30.4), (18, 23)], 'p')
    s.C(16, 14.5, 13.2, 'e'); s.C(16, 14.5, 10, 'U')
    s.C(11.5, 15.5, 4.8, 'c'); s.C(20.5, 15.5, 4.8, 'p'); s.C(9, 11, 1.6, 'c'); s.C(23, 11, 1.6, 'p')
    s.face(11, 15, 2, 'dot', blush=False); s.face(20, 15, 2, 'dot', blush=False)
    s.A(13, 6, ['_p_p_', 'ppppp', '_ppp_', '__p__'])
    return render(s, UI.MAT, special={'k': '#24172C'})

# ------------------------------------------------------------------ 示意 QR（finder＋timing＋hash 雜點；唔係真 QR）
def fake_qr(text, n=41):
    h = hashlib.sha256(text.encode()).digest(); rng = np.random.RandomState(int.from_bytes(h[:4], 'big'))
    m = rng.rand(n, n) < .5
    for (x, y) in ((0, 0), (n - 7, 0), (0, n - 7)):
        m[y:y + 7, x:x + 7] = True; m[y + 1:y + 6, x + 1:x + 6] = False; m[y + 2:y + 5, x + 2:x + 5] = True
        m[max(0, y - 1):y + 8, max(0, x - 1):x + 8][:, :] &= np.pad(np.ones((7, 7), bool), 1)[(1 if y == 0 else 0):(9 if y == 0 else 8), (1 if x == 0 else 0):(9 if x == 0 else 8)][:min(9, n - max(0, y - 1)), :min(9, n - max(0, x - 1))] | (False)
    m[6, 8:n - 8] = (np.arange(8, n - 8) % 2 == 0); m[8:n - 8, 6] = (np.arange(8, n - 8) % 2 == 0)
    a = np.zeros((n, n, 4), np.uint8); a[:] = P['white']; a[m] = P['line']; return a

# ------------------------------------------------------------------ share card（分享圖：可以存相／傳俾朋友，揀相解碼）
CW, CHH = 165, 252
def share_card_bg():
    bd = X.new(CW, CHH)
    X.put(bd, M.panel('panel_navy', CW, CHH - 8), 0, 8)
    pw = 96; pl = M.h3('plaque', pw); X.put(bd, M.UI('plaque_tail_l'), CW / 2 - pw / 2 - 6, 2); X.put(bd, M.UI('plaque_tail_r'), CW / 2 + pw / 2 - 2, 2); X.put(bd, pl, CW / 2 - pw / 2, 0)
    X.put(bd, M.panel('panel_inset', 145, 58), 10, 92)                        # 3 段回憶
    for i in range(3): X.put(bd, M.UI('gem_pri_5'), 15, 99 + i * 18)
    X.put(bd, M.h3('divider', 125), 20, 154)
    X.put(bd, pim(tile9(qr_frame_src(), (6, 6, 6, 6), 66, 66)), (CW - 66) // 2, 160)
    return bd
SLOTS = {"title": {"x": 82.5, "y": 8.5, "anchor": "m", "font": "fp12", "w": 96},
         "portrait": {"x": 10, "y": 24, "w": 54, "h": 56, "note": "kit portrait()（52 框＋pop）"},
         "name": {"x": 70, "y": 34, "font": "fp12", "maxW": 85},
         "family": {"x": 70, "y": 52, "font": "fp12", "note": "家族 Lv＋kit ic_family_level mini"},
         "form": {"x": 70, "y": 70, "font": "fp12", "note": "形態名"},
         "memories": [{"x": 24, "y": 101 + i * 18, "font": "fp12", "maxW": 126} for i in range(3)],
         "qr": {"x": 49, "y": 160, "w": 66, "h": 66, "inner": [53, 164, 58, 58], "note": "白 quiet zone 58×58；QR module 用整數 art px（v3 29 module ×2、或 ≤v10 57 module ×1）；四邊留 ≥4 module 白"},
         "code": {"x": 82.5, "y": 236, "anchor": "m", "font": "fp12", "note": "顯示碼頭 8 位＋…＋checksum 4 位"}}

def fill_card(bd, name='波波', form='A3', fam='家族 Lv4', mems=('第一次見到螢火蟲', '雨天一齊踩水氹', '識咗新朋友松鼠'), code='GLM1-7Q3K…9F2A', screen=None):
    T(bd, '朋友名片', SLOTS['title']['x'], SLOTS['title']['y'], anchor='m', bg='g_mid', screen=screen)
    pt, po = M.portrait(form, 'happy'); X.put(bd, pt, SLOTS['portrait']['x'], SLOTS['portrait']['y'] - po)
    T(bd, name, 70, 34, screen=screen); X.put(bd, M.icm('star'), 70, 46); T(bd, fam, 83, 52, col='g_hi', col2='g_br', screen=screen)
    T(bd, '形態：' + {'A3': '泡泡', 'evo_still_tide': '靜光'}.get(form, form), 70, 70, col='cream', col2='cream', screen=screen)
    for i, t in enumerate(mems): T(bd, t, 24, 101 + i * 18, col='cream', col2='cream', bg='nv2', screen=screen)
    q = fake_qr(code); qx, qy = 53 + (58 - 41) // 2, 164 + (58 - 41) // 2
    over_arr = np.array(bd); over(over_arr, q, qx, qy); bd = pim(over_arr)
    T(bd, code, CW / 2, 236, anchor='m', col='cream', col2='cream', bg='nv3', screen=screen)
    return bd

# ------------------------------------------------------------------ mockups（195×422 → 3x）
def btn12(t, w, fill='pri', icon=None):
    b = M.h3(f'btn_{fill}', w); tx = w / 2 + (6 if icon else 0)
    if icon: X.putc(b, icon if isinstance(icon, Image.Image) else M.icm(icon), tx - X.text_img(t, 12).width / 2 - 5, 10)
    T(b, t, tx, 9.5, anchor='m', col='white', col2='g_hi' if fill == 'pri' else 'cream', bg={'pri': 'g_mid', 'sec': 'tl1', 'rose': 'red', 'violet': 'vi1', 'dis': 'nv2'}.get(fill, 'nv2')); return b
def icon_im(a): return pim(a)
def tag12(t, fill='sec', icon=None, screen=None):
    """FP12 細牌（kit btn16_* 3h tile，高 16）— 取代 kit 8px pill，守 FP12 下限"""
    tw_ = X.text_img(t, 12).width - 4; w = tw_ + 14 + (12 if icon else 0); b = M.h3(f'btn16_{fill}', w)
    if icon: X.putc(b, M.icm(icon), 8, 8)
    T(b, t, w / 2 + (6 if icon else 0), 7.5, anchor='m', col='white', col2='cream', bg={'pri': 'g_mid', 'sec': 'tl1', 'violet': 'vi1', 'rose': 'red'}[fill], screen=screen); return b
def plaque12(bd, t, cx, y, screen=None):
    w = X.text_img(t, 12).width + 16; p = M.h3('plaque', w)
    X.put(bd, M.UI('plaque_tail_l'), cx - w / 2 - 6, y + 2); X.put(bd, M.UI('plaque_tail_r'), cx + w / 2 - 2, y + 2); X.put(bd, p, cx - w / 2, y)
    T(bd, t, cx, y + 8.5, anchor='m', bg='g_mid', screen=screen)
def field(t, w, on=False, screen=None):
    f = pim(tile9(code_field_src(on), (6, 0, 6, 0), w, 20, '3h')); T(f, t, 8, 9.5, col='cream', col2='cream', bg='nv3', screen=screen); return f

def m_share(IC):
    bd = M.room('night' if False else 'day', pets=(('A3', 'normal', 96, 300),)) if True else None
    M.veil(bd); T_ = 'share'
    card = fill_card(share_card_bg(), screen=T_); X.put(bd, card, (SW - CW) // 2, 50)
    M.close_btn(bd, (SW + CW) // 2 - 19, 62)
    X.put(bd, btn12('複製碼', 78, 'sec', icon_im(IC['ic_copy'])), 15, 314); X.put(bd, btn12('存圖', 78, 'pri', icon_im(IC['ic_photo'])), 102, 314)
    p = M.h3('panel_navy_flat', 171) if False else None
    T(bd, '朋友掃描或貼上就可以探你', SW / 2, 350, anchor='m', col='white', col2='cream', bg='nv3', screen=T_)
    return bd
def m_enter(IC):
    bd = M.room('day', pets=(('evo_still_tide', 'normal', 96, 300),)); M.veil(bd)
    x, y, w = 12, 70, 171; X.put(bd, M.panel('panel_navy', w, 268), x, y); plaque12(bd, '加朋友', SW / 2, y - 7, 'enter'); M.close_btn(bd, x + w - 19, y + 4)
    T(bd, '貼上朋友嘅碼', x + 12, y + 26, screen='enter')
    X.put(bd, field('GLM1-7Q3K…9F2A', w - 24, True, 'enter'), x + 12, y + 36)
    X.put(bd, btn12('貼上', 70, 'sec', icon_im(IC['ic_paste'])), x + 12, y + 62); X.put(bd, btn12('揀相', 70, 'sec', icon_im(IC['ic_photo'])), x + w - 82, y + 62)
    X.put(bd, M.h3('divider', w - 30), x + 15, y + 92)
    T(bd, '讀到：', x + 12, y + 108, col='g_hi', col2='g_br', screen='enter')
    X.put(bd, M.panel('panel_inset', w - 24, 92), x + 12, y + 118)
    pt, po = M.portrait('A3', 'happy'); X.put(bd, pt, x + 18, y + 124 - po)
    T(bd, '波波', x + 78, y + 132, screen='enter', bg='nv2'); T(bd, '家族 Lv4', x + 78, y + 150, col='g_hi', col2='g_br', screen='enter', bg='nv2')
    X.put(bd, tag12('校驗 OK', 'sec', 'check', 'enter'), x + 78, y + 160)
    T(bd, '第一次見到螢火蟲', x + 22, y + 196, col='cream', col2='cream', screen='enter', bg='nv2')
    X.put(bd, btn12('請佢嚟玩', 110, 'pri', icon_im(IC['ic_friend'])), (SW - 110) // 2, y + 228)
    return bd
def m_visit(IC, badge):
    bd = M.home('normal' if False else 'hungry')
    g, info = X.compose_pet('A3', 'happy'); ga = ghost(arr(g)); a = np.array(bd); over(a, ga, 152 - ga.shape[1] // 2, 312 - ga.shape[0] + 8); bd = pim(a)
    X.putc(bd, pim(badge), 152, 312 - ga.shape[0] + 10)
    t = M.h3('toast', 150); X.put(t, icon_im(IC['ic_friend']), 4, 2) if t.height >= 18 else None
    X.put(bd, M.panel('panel_navy_flat', 171, 40), 12, 150 - 104)
    X.put(bd, icon_im(IC['ic_friend']), 20, 54); T(bd, '波波嚟探你！', 40, 61, screen='visit', bg='nv2')
    T(bd, '仲有 23 粒鐘', 40, 76, col='g_hi', col2='g_br', screen='visit', bg='nv2')
    X.put(bd, tag12('影子', 'violet', None, 'visit'), 140, 53)
    return bd
def m_egg(IC):
    bd = M.room('day', pets=()); M.veil(bd)
    x, y, w = 12, 80, 171; X.put(bd, M.panel('panel_navy', w, 236), x, y); plaque12(bd, '交換蛋碼', SW / 2, y - 7, 'egg'); M.close_btn(bd, x + w - 19, y + 4)
    X.put(bd, tag12('家族 Lv4 解鎖', 'pri', 'star', 'egg'), x + 12, y + 20)
    X.put(bd, M.panel('egg_card', 64, 72), x + 12, y + 42); X.putc(bd, X.up(M.ic('egg_kid'), 2), x + 44, y + 78)
    T(bd, '團絨線・A 系', x + 84, y + 56, screen='egg', bg='nv3'); T(bd, '花紋：泡泡', x + 84, y + 74, col='cream', col2='cream', screen='egg', bg='nv3')
    T(bd, '我嘅蛋碼', x + 12, y + 130, col='g_hi', col2='g_br', screen='egg')
    X.put(bd, field('EGG4-M2TA…C81D', w - 24, False, 'egg'), x + 12, y + 140)
    X.put(bd, btn12('複製', 70, 'sec', icon_im(IC['ic_copy'])), x + 12, y + 168); X.put(bd, btn12('貼上', 70, 'sec', icon_im(IC['ic_paste'])), x + w - 82, y + 168)
    X.put(bd, btn12('交換', 100, 'pri', icon_im(IC['ic_egg_code'])), (SW - 100) // 2, y + 202)
    return bd

def main():
    os.makedirs(OUT, exist_ok=True); TEXTLOG.clear()
    J = {"version": 1, "batch": "breakthrough 6d 社交（分享碼／QR／影子探訪／蛋碼）", "spec": "docs-gdd/breakthrough-6a6d-spec.md §6d", "screen": [SW, SH],
         "kit": "art-pet/ui/kit_hd2d_v2（零件 key 直接用 kit atlas 名；以下只列 6d 新嘢）", "keys": {}, "mockups": {}}
    K = J["keys"]
    K["6d:qr_frame"] = dict(save2(qr_frame_src(), "parts/qr_frame.png"), slice="9", nine=[6, 6, 6, 6], mode="tile", inner="白 quiet zone＝(w−8)×(h−8) @ (4,4)")
    K["6d:code_field"] = dict(save2(code_field_src(False), "parts/code_field.png"), slice="3h", nine=[6, 0, 6, 0], mode="tile", text="FP12 cream，x＋8，垂直置中")
    K["6d:code_field_on"] = dict(save2(code_field_src(True), "parts/code_field_on.png"), slice="3h", nine=[6, 0, 6, 0], mode="tile", note="focus／已貼上")
    K["6d:shadow_mask"] = dict(save2(shadow_mask(), "parts/shadow_mask.png"), note="影子形態：pet 像素 ∧ 呢個 4×4 棋盤（白＝畫）＝50% 抽像素，取代半透明；色用 kit vi0／vi1／vi2 剪影")
    scb = arr(share_card_bg()); K["6d:share_card_bg"] = dict(save2(scb, "parts/share_card_bg.png"), slots=SLOTS,
                                                              note="分享圖底（kit panel_navy／plaque／panel_inset／divider tile 砌＋qr_frame）；字同頭像由 code 落；存相＝@3x 495×756")
    IC = icons()
    for n, a in IC.items(): K["icon_" + n[3:]] = dict(save2(a, f"icons/{n}@1x.png".replace("@1x", "")), note="16×16，同 kit ic_* 同規格")
    fb = friend_badge(); K["6d:friend_badge"] = dict(save2(fb, "icons/friend_badge.png"), note="朋友牌（32×32）：探訪中影子頭頂／朋友列表；細版＝icon_friend 16×16")
    reuse = {"icon_visitor": "ic_visitor", "icon_family_level": "ic_family_level", "icon_egg_tr": "ic_egg_tr", "icon_gift": "ic_gift（影子留低嘅手信）", "icon_badge": "ic_badge"}
    J["reuseKit"] = reuse
    sample = fill_card(pim(scb.copy()), screen='card_sample'); save2(arr(sample), "mockups/share_card_sample.png")
    J["mockups"]["share_card_sample"] = "mockups/share_card_sample.png"
    for nm, fn in (("share", lambda: m_share(IC)), ("enter_code", lambda: m_enter(IC)), ("visit_shadow", lambda: m_visit(IC, fb)), ("egg_code", lambda: m_egg(IC))):
        bd = fn(); a = arr(bd); assert a.shape[:2] == (SH, SW)
        Image.fromarray(np.repeat(np.repeat(a, 3, 0), 3, 1)).save(os.path.join(OUT, f"mockups/{nm}_3x.png"), optimize=True)
        J["mockups"][nm] = f"mockups/{nm}_3x.png"
    J["text"] = TEXTLOG
    json.dump(J, open(os.path.join(OUT, "share6d.json"), "w"), ensure_ascii=False, indent=1)
    preview(J, IC, fb)
    print("ok", len(K), "keys", len(TEXTLOG), "text runs")

def preview(J, IC, fb):
    ms = [np.array(Image.open(os.path.join(OUT, J["mockups"][k]))) for k in ("share", "enter_code", "visit_shadow", "egg_code")]
    row = np.concatenate([np.pad(m, ((0, 0), (0, 18), (0, 0))) for m in ms], 1)
    pad = lambda a, p=3: np.pad(a, ((p, p), (p, p), (0, 0)))
    parts = [pad(a) for a in IC.values()] + [pad(fb)[:, :, :]]
    hmax = max(p.shape[0] for p in parts); parts = [np.pad(p, ((0, hmax - p.shape[0]), (0, 0), (0, 0))) for p in parts]
    strip = np.concatenate(parts + [pad(tile9(qr_frame_src(), (6, 6, 6, 6), 40, 32)), pad(tile9(code_field_src(), (6, 0, 6, 0), 60, 20, '3h')), pad(tile9(code_field_src(True), (6, 0, 6, 0), 60, 20, '3h'))], 1) if False else np.concatenate(parts, 1)
    s3 = np.repeat(np.repeat(strip, 6, 0), 6, 1)
    pz = np.concatenate([pad(tile9(qr_frame_src(), (6, 6, 6, 6), 40, 34)), pad(np.pad(tile9(code_field_src(), (6, 0, 6, 0), 60, 20, '3h'), ((0, 14), (0, 0), (0, 0)))), pad(np.pad(tile9(code_field_src(True), (6, 0, 6, 0), 60, 20, '3h'), ((0, 14), (0, 0), (0, 0))))], 1)
    p3 = np.repeat(np.repeat(pz, 6, 0), 6, 1)
    Wd = row.shape[1]; out = np.zeros((row.shape[0] + 24 + s3.shape[0] + 24 + p3.shape[0], Wd, 4), np.uint8); out[:] = (40, 36, 64, 255)
    out[:row.shape[0]] = np.where(row[..., 3:] == 255, row, out[:row.shape[0]])
    over(out, s3, 0, row.shape[0] + 24); over(out, p3, 0, row.shape[0] + 48 + s3.shape[0])
    Image.fromarray(out).save(os.path.join(OUT, "preview_6d_3x.png"), optimize=True)

if __name__ == "__main__":
    main()
