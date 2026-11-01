# 《微光小圃》HD-2D kit mockups — 全部只用 atlas JSON 砌（證明 kit 可用），純 Pillow，無 AI。
import sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw, ImageFilter
import ui_hd2d_kit as K
from ui_kit_hd2d_render import Kit
ROOT = K.ROOT; OUT = f'{ROOT}/ui/kit_hd2d'; os.makedirs(f'{OUT}/mockups', exist_ok=True)
kit = Kit(3); S = 3
CREAM = (255, 245, 220); INK = (58, 40, 64)

# ---------------- layout (art px, 195x422) — also exported for 遊程 ----------------
L = dict(
    top=dict(h=38, note='頂部 UI 帶 0–38（名牌 h20＋需要值 h10＋光暈）'),
    bottom=dict(y=348, h=74, note='底部 UI 帶 348–422（動作掣 d28＋字牌＋dock h34）'),
    garden=dict(y=38, h=310, pct=round(310 / 422 * 100, 1)),
    nameplate=dict(x=3, y=3, w=92, h=20, portrait=dict(cx=13, cy=13, frame='med19_paper', head=15), name=dict(x=25.5, y=9.2, size=9, font='serif'),
                   stage=dict(x=62, y=4.4, w=24, h=10), exp=dict(x=25, y=15.2, w=66, h=5, gems=[.33, .66])),
    chips=[dict(x=99, y=5, w=44, h=16, icon='light', val=140), dict(x=151, y=5, w=38, h=16, icon='star', val=10)],
    needs=[dict(x=3 + i * 47.5, y=26, w=45.5, h=10, icon=ic, fill=fk) for i, (ic, fk) in enumerate([('feed', 'feed'), ('heart_bunny', 'mood'), ('clean', 'clean'), ('sleep', 'energy')])],
    rail=[dict(id='quest', cx=180, cy=52, d=22, icon='gift', label='委託', labelY=65.5), dict(id='mail', cx=180, cy=81, d=20, icon='mail', note='P0-1 通知佇列；冇字'),
          dict(id='house', cx=178, cy=104, d=24, icon='house', label='屋仔', labelY=120.5, note='4b layout.json gardenEntry 原位')],
    acts=[dict(cx=round(26 + i * 47.7, 1), cy=362, d=28, fill=f, icon=ic, label=lb, plate=dict(w=28, h=10, y=372)) for i, (ic, f, lb) in
          enumerate([('feed', 'pri', '餵食'), ('play_cat', 'rose', '玩耍'), ('clean', 'sec', '清潔'), ('sleep', 'violet', '瞓覺')])],
    dock=dict(x=3, y=386, w=189, h=34, tabs=['照顧', '玩', '小圃', '手帳', '設定'], icons=['heart_bunny', 'play_cat', 'sprout', 'book_bear', 'gear_chick'],
              idle=dict(d=18, cy=398, frame='med18_navy_in', icon=14, labelY=414), active=dict(d=24, cy=393, frame='med24_pri', icon=19, labelY=414, pillar='dock_pillar')),
    toast=dict(x=31.5, y=44, w=132, h=18), bubble=dict(x=56, y=236, w=60, h=20),
    popup=dict(x=19, y=104, w=157, h=148, title_y=95, close=dict(dx=-11, dy=11), row=dict(x=9, y=18, w=139, h=27, gap=30), btn=dict(w=84, h=20, dy=-28)),
)
json.dump(L, open(f'{OUT}/layout_hd2d.json', 'w'), ensure_ascii=False, indent=1)

LAY = K.scene_layers('A1')
SC = K.scene_ss(LAY).reduce(2)                  # 585x1266
PET = K.k.load(f'{ROOT}/sprites/tuanrong/species_concept/from_ref/tuned_48/sprites/A1_48.png')
def head():
    bb = PET.getbbox(); return PET.crop((bb[0], bb[1] + 3, bb[2], bb[1] + 3 + (bb[2] - bb[0])))

def hud(bd, active=0, acts=True):
    n = L['nameplate']; kit.draw(bd, 'nameplate', n['x'], n['y'], n['w'], n['h'])
    kit.drawc(bd, 'med19_paper', 13, 13)
    hh = head().resize((15 * S, 15 * S), Image.NEAREST); bd.alpha_composite(hh, (round(5.5 * S), round(5.6 * S)))
    kit.text(bd, '滴滴', 25.5, 9.4, 8.6, CREAM, 'serif', 0.9, anchor='lm')
    kit.draw(bd, 'stage_tag', 62, 4.4, 24, 10); kit.text(bd, '幼崽', 74, 9.2, 7.0, (255, 255, 255), 'sans', 0.7, (46, 26, 82))
    e = n['exp']; kit.draw(bd, 'exp_trough', e['x'], e['y'], e['w'], 5); kit.draw(bd, 'exp_fill', e['x'] + 1, e['y'] + 1, (e['w'] - 2) * .62, 3)
    for t in e['gems']: kit.drawc(bd, 'exp_gem_on' if t < .62 else 'exp_gem_off', e['x'] + e['w'] * t, e['y'] + 2.5)
    for c in L['chips']:
        kit.draw(bd, 'chip', c['x'], c['y'], c['w'], 16); kit.icon(bd, c['icon'], c['x'] + 3, c['y'] + 8, 17)
        kit.btext(bd, 'gold', str(c['val']), c['x'] + c['w'] / 2 + 5, c['y'] + 12.3, 'm', 0.8)
        kit.drawc(bd, 'chip_plus', c['x'] + c['w'] - 0.5, c['y'] + 8)
    for i, nd in enumerate(L['needs']):
        v = [.62, .48, .55, .15][i]
        kit.draw(bd, 'need_trough', nd['x'], nd['y'], nd['w'], 10)
        fx0 = nd['x'] + 10.2; fw = (nd['w'] - 13.6) * v
        kit.draw(bd, 'need_fill_' + ('low' if v < .2 else nd['fill']), fx0, nd['y'] + 3, max(4.4, fw), 4)
        kit.drawc(bd, 'bar_tip', fx0 + max(4.4, fw) - 1, nd['y'] + 5, alpha=.8)
        kit.drawc(bd, 'med11_navy', nd['x'] + 4.4, nd['y'] + 5); kit.icon(bd, nd['icon'], nd['x'] + 4.4, nd['y'] + 5, 11.5)
    for r in L['rail']:
        kit.drawc(bd, f"med{r['d']}_navy" if r['d'] != 20 else 'med19_navy', r['cx'], r['cy']) if r['d'] != 24 else kit.drawc(bd, 'med24_navy', r['cx'], r['cy'])
        kit.icon(bd, r['icon'], r['cx'], r['cy'], r['d'] * .8)
        if r.get('label'): kit.text(bd, r['label'], r['cx'], r['labelY'], 7.0, CREAM, 'sans', 0.8)
    kit.drawc(bd, 'red_dot_num', 188, 44); kit.btext(bd, 'round', '3', 188, 46.3, 'm')
    kit.drawc(bd, 'red_dot', 187.5, 74)
    for a in (L['acts'] if acts else []):
        kit.drawc(bd, f"med28_{a['fill']}", a['cx'], a['cy']); kit.icon(bd, a['icon'], a['cx'], a['cy'], 21)
        kit.draw(bd, 'label_plate', a['cx'] - 14, 372, 28, 10); kit.lbl(bd, 'act_' + a['label'], a['cx'], 377)
    dk = L['dock']; kit.draw(bd, 'dock_bar', dk['x'], dk['y'], dk['w'], dk['h'])
    for i in range(5):
        cx = dk['x'] + dk['w'] / 5 * (i + .5)
        if i: kit.draw(bd, 'dock_div', dk['x'] + dk['w'] / 5 * i, dk['y'] + 7)
        if i == active:
            kit.drawc(bd, 'dock_pillar', cx, dk['y'] + 14); kit.drawc(bd, 'med24_pri', cx, 393); kit.icon(bd, dk['icons'][i], cx, 393, 19)
            kit.lbl(bd, 'tab_on_' + dk['tabs'][i], cx, 413.6)
        else:
            kit.drawc(bd, 'med18_navy_in', cx, 398); kit.icon(bd, dk['icons'][i], cx, 398, 14.5); kit.lbl(bd, 'tab_' + dk['tabs'][i], cx, 413.8)
    cx3 = dk['x'] + dk['w'] / 5 * 3.5
    if active != 3: kit.drawc(bd, 'red_dot', cx3 + 7.5, 391)

def home(toast=True, bubble=True):
    bd = SC.copy(); hud(bd)
    if toast:
        t = L['toast']; kit.drawc(bd, 'toast_wing_l', t['x'] + t['w'] * .2 - 13, t['y'] + 9, alpha=.9); kit.drawc(bd, 'toast_wing_r', t['x'] + t['w'] * .8 + 13, t['y'] + 9, alpha=.9)
        kit.draw(bd, 'toast', t['x'], t['y'], t['w'], 18); kit.drawc(bd, 'med19_pri', t['x'] + 4, t['y'] + 9); kit.icon(bd, 'star', t['x'] + 4, t['y'] + 9, 15)
        kit.text(bd, '收到小禮物', t['x'] + 56, t['y'] + 8.6, 8.0, CREAM, 'sans', 0.9); kit.btext(bd, 'gold', '+5', t['x'] + 98, t['y'] + 12.6, 'm', .8)
    if bubble:
        b = L['bubble']; kit.draw(bd, 'bubble', b['x'], b['y'], b['w'], b['h']); kit.draw(bd, 'bubble_tail', b['x'] + 9, b['y'] + b['h'] - 1)
        kit.icon(bd, 'feed', b['x'] + 9, b['y'] + 10, 12); kit.text(bd, '肚仔餓…', b['x'] + 35, b['y'] + 9.6, 8.0, INK, 'sans', 0)
    return bd

def dimbg(bd):
    small = bd.reduce(3).filter(ImageFilter.GaussianBlur(1.6)).resize(bd.size, Image.BICUBIC)
    out = Image.blend(bd, small, 1.0); out.alpha_composite(Image.new('RGBA', out.size, (20, 26, 54, 110))); return out

def popup_window(bd, x, y, w, h, title, plaque='plaque'):
    kit.draw(bd, 'panel_glass', x, y, w, h)
    pw = max(64, len(title) * 10 + 26)
    kit.draw(bd, 'plaque_tail_l', x + w / 2 - pw / 2 - 9, y - 4.5); kit.draw(bd, 'plaque_tail_r', x + w / 2 + pw / 2 - 4, y - 4.5)
    kit.draw(bd, plaque, x + w / 2 - pw / 2, y - 8.5, pw, 17); kit.drawc(bd, 'plaque_gem', x + w / 2, y - 9.5)
    kit.lbl(bd, 'title_' + title, x + w / 2, y + 0.3)
    kit.drawc(bd, 'close', x + w - 11, y + 11)

def popup():
    bd = dimbg(home(toast=False, bubble=False)); p = L['popup']; x, y, w, h = p['x'], p['y'], p['w'], p['h']
    popup_window(bd, x, y, w, h, '今日委託')
    rows = [('play_cat', '陪佢玩 2 次', .5, '1/2'), ('feed', '餵佢食嘢', 1.0, None), ('clean', '幫佢沖涼', 0, '0/1'), ('mg_stardust', '接星屑 1 局', 0, '0/1')]
    for i, (ic, lb, v, pr) in enumerate(rows[:3]):
        rx, ry = x + 9, y + 20 + i * 30
        kit.draw(bd, 'panel_inset_sel' if v >= 1 else 'panel_inset', rx, ry, w - 18, 27)
        kit.drawc(bd, 'med19_paper', rx + 12, ry + 13.5); kit.icon(bd, ic, rx + 12, ry + 13.5, 15.5)
        kit.text(bd, lb, rx + 25, ry + 8.6, 7.6, CREAM, 'sans', 0.8, anchor='lm')
        kit.draw(bd, 'prog_trough', rx + 25, ry + 15, 56, 6)
        if v > 0: kit.draw(bd, 'prog_fill_gold' if v >= 1 else 'prog_fill_teal', rx + 26, ry + 16, 54 * v, 4)
        if pr: kit.btext(bd, 'px7_ol', pr, rx + 84, ry + 21.5, 'l')
        kit.icon(bd, 'star', rx + w - 47, ry + 13.5, 13); kit.btext(bd, 'gold', '+4', rx + w - 33, ry + 17.6, 'm', .72)
        if v >= 1:
            kit.drawc(bd, 'stamp_done', rx + w - 21, ry + 2.5, .8); kit.icon(bd, 'check', rx + w - 21, ry + 2.5, 10)
            kit.text(bd, '完成', rx + 84 + 7, ry + 18.4, 7.0, (200, 255, 214), 'sans', 0.8, (16, 60, 36))
    kit.draw(bd, 'btn_pri', x + (w - 84) / 2, y + h - 28, 84, 20); kit.lbl(bd, 'btn_pri_全部領取', x + w / 2, y + h - 18.3)
    kit.drawc(bd, 'fx_spark', x + w / 2 + 40, y + h - 26, .9); kit.drawc(bd, 'fx_mote', x + 20, y + h - 10)
    return bd

def settings():
    bd = dimbg(home(toast=False, bubble=False)); x, y, w, h = 8, 58, 179, 304
    popup_window(bd, x, y, w, h, '設定')
    def row(i, ic, lab):
        ry = y + 16 + i * 31; kit.draw(bd, 'panel_inset', x + 7, ry, w - 20, 27); kit.drawc(bd, 'med19_navy', x + 18, ry + 13.5); kit.icon(bd, ic, x + 18, ry + 13.5, 15)
        kit.text(bd, lab, x + 30, ry + 13.5, 7.8, CREAM, 'sans', 0.8, anchor='lm'); return ry
    def seg(rx, ry, opts, on, ww):
        kit.draw(bd, 'seg_bg', rx, ry, ww, 16); sw = (ww - 4) / len(opts)
        for j, o in enumerate(opts):
            if j == on: kit.draw(bd, 'seg_on', rx + 2 + j * sw, ry + 2, sw, 12)
            elif j and j != on + 1: kit.draw(bd, 'seg_div', rx + 2 + j * sw, ry + 4)
            kit.text(bd, o, rx + 2 + (j + .5) * sw, ry + 7.8, 7.4, (255, 255, 255) if j == on else (232, 226, 210), 'sans', 0.8, (122, 58, 16) if j == on else (20, 24, 52))
    ry = row(0, 'quality', '畫質'); seg(x + 66, ry + 5.5, ['低', '中', '高', '自動'], 2, 98)
    ry = row(1, 'sound', '聲音'); kit.draw(bd, 'toggle_track_on', x + 138, ry + 7); kit.drawc(bd, 'toggle_knob_on', x + 138 + 19.5, ry + 13.5)
    ry = row(2, 'sound', '音量'); seg(x + 84, ry + 5.5, ['細', '中', '大'], 1, 80)
    ry = row(3, 'hint', '提示'); kit.draw(bd, 'toggle_track_off', x + 138, ry + 7); kit.drawc(bd, 'toggle_knob_off', x + 138 + 6.5, ry + 13.5)
    ry = row(4, 'surprise', '懸浮小驚喜'); kit.draw(bd, 'toggle_track_on', x + 138, ry + 7); kit.drawc(bd, 'toggle_knob_on', x + 138 + 19.5, ry + 13.5)
    ry = row(5, 'water', '飲水間隔'); seg(x + 84, ry + 5.5, ['30', '60', '90'], 1, 80)
    ry = row(6, 'bedtime', '早瞓時間'); seg(x + 74, ry + 5.5, ['21', '22', '23', '0', '關'], 1, 90)
    kit.draw(bd, 'scroll_track', x + w - 6, y + 18, 4, 214); kit.draw(bd, 'scroll_thumb', x + w - 6, y + 22, 4, 60)
    kit.draw(bd, 'divider', x + 14, y + h - 58, w - 28, 4); kit.drawc(bd, 'dock_gem', x + w / 2, y + h - 56)
    kit.draw(bd, 'btn_rose', x + 14, y + h - 40, 70, 20); kit.lbl(bd, 'btn_rose_重設', x + 49, y + h - 30.3)
    kit.draw(bd, 'btn_dis', x + w - 84, y + h - 40, 70, 20); kit.lbl(bd, 'btn_dis_未解鎖', x + w - 49, y + h - 30.3)
    kit.text(bd, '細字示範：正文 sans 7.4 art、數字用像素字', x + w / 2, y + h - 10, 7.0, (220, 214, 196), 'sans', 0.7)
    return bd

def journal():
    bd = SC.copy(); bd = dimbg(bd); hud(bd, active=3, acts=False)
    x, y, w, h = 6, 50, 183, 300
    popup_window(bd, x, y, w, h, '手帳')
    subs = ['委託', '日記', '親密', '徽章', '圖鑑']
    for i, s in enumerate(subs):
        sx = x + 8 + i * 33.6
        kit.draw(bd, 'subtab_on' if i == 4 else 'subtab', sx, y + 14, 32, 15)
        kit.text(bd, s, sx + 16, y + 21.2, 7.4, (255, 255, 255) if i == 4 else (236, 230, 214), 'sans', 0.8, (122, 58, 16) if i == 4 else (20, 24, 52))
    kit.drawc(bd, 'red_dot', x + 8 + 1 * 33.6 + 30, y + 15)
    kit.text(bd, '圖鑑', x + 12, y + 40, 8.2, CREAM, 'sans', 0.8, anchor='lm'); kit.btext(bd, 'px7_ol', '4/9', x + 34, y + 44, 'l')
    kit.draw(bd, 'prog_trough', x + 56, y + 37, 100, 6); kit.draw(bd, 'prog_fill_teal', x + 57, y + 38, 98 * 4 / 9, 4)
    kit.drawc(bd, 'med16_navy', x + w - 15, y + 40); kit.icon(bd, 'info', x + w - 15, y + 40, 12)
    items = [('d_cloud', '雲朵咪', 0), ('play_cat', '貓仔', 0), ('heart_bunny', '兔兔', 1), ('book_bear', '熊熊', 0), (None, '未發現', 2), (None, '未發現', 2),
             ('mg_firefly', '螢火仔', 0), (None, '未發現', 2), (None, '未發現', 2)]
    for i, (ic, lb, st) in enumerate(items):
        cx0 = x + 12 + (i % 3) * 54; cy0 = y + 52 + (i // 3) * 64
        kit.draw(bd, ['card', 'card_sel', 'card_locked'][st], cx0, cy0, 50, 58)
        if st < 2: kit.drawc(bd, 'card_spot', cx0 + 25, cy0 + 22, alpha=.8); kit.icon(bd, ic, cx0 + 25, cy0 + 22, 24)
        else: kit.drawc(bd, 'card_qmark', cx0 + 25, cy0 + 22); kit.icon(bd, 'lock', cx0 + 42, cy0 + 8, 10)
        kit.text(bd, lb, cx0 + 25, cy0 + 47, 7.4, (244, 245, 252) if st == 2 else CREAM, 'sans', 0.8, (20, 24, 52))
        if st == 1: kit.drawc(bd, 'red_dot', cx0 + 47, cy0 + 3)
    return bd

def stubs():
    W = 585; bd = Image.new('RGBA', (W * 2 + 30, 1266), (16, 18, 36, 255))
    # --- 4b decorate re-skin (room art read-only from 4b preview) ---
    room = f'{ROOT}/sprites/series2_house/preview/room_setA_3x.png'
    a = Image.open(room).convert('RGBA') if os.path.exists(room) else SC.copy()
    if a.width >= 1000: a = a.crop((0, 0, a.width // 2, a.height))
    a = a.resize((585, round(a.height * 585 / a.width)), Image.LANCZOS)
    a = a.crop((0, 36 * 3, 585, 1266)); A = Image.new('RGBA', (585, 1266), (20, 22, 40, 255)); A.paste(a, (0, 0))
    ui4b = f'{ROOT}/sprites/series2_house/ui'
    def ic4b(bd_, n, cx, cy, size):
        p = f'{ui4b}/icon_{n}@3x.png'
        if os.path.exists(p):
            im = Image.open(p).convert('RGBA'); sc = size / 24; im = im.resize((round(im.width * sc), round(im.height * sc)), Image.LANCZOS)
            bd_.alpha_composite(im, (round(cx * 3 - im.width / 2), round(cy * 3 - im.height / 2)))
    kit.drawc(A, 'med22_navy', 16, 18); ic4b(A, 'back', 16, 18, 16)
    kit.draw(A, 'plaque_tail_l', 97.5 - 42 - 9, 12.5); kit.draw(A, 'plaque_tail_r', 97.5 + 42 - 4, 12.5)
    kit.draw(A, 'plaque', 97.5 - 42, 8, 84, 17); kit.lbl(A, 'title_屋仔佈置', 97.5, 16.8)
    for (px, py, st) in ((60, 150, 'pri'), (130, 210, 'navy')):
        d = 20 if st == 'pri' else 16; kit.drawc(A, f'med{d}_{st}', px, py); kit.icon(A, 'furniture' if st == 'navy' else 'decorate', px, py, d * .7)
    kit.draw(A, 'panel_glass_plain', 4, 280, 187, 138); kit.drawc(A, 'sheet_handle', 97.5, 284)
    for i, n in enumerate(['bed', 'table', 'wall', 'rug', 'window', 'lamp']):
        cx = 19.58 + i * 31.17
        if i == 0: kit.drawc(A, 'med25_pri', cx, 297)
        else: kit.drawc(A, 'med22_navy', cx, 297)
        ic4b(A, n, cx, 297, 17 if i == 0 else 15)
    for j, (st, lab, pill) in enumerate((('card_sel', '葉仔床', 'sec'), ('card', '雲朵床', 'pri'), ('card_locked', '星星床', 'dis'))):
        cx0 = [8.5, 70.5, 132.5][j]; kit.draw(A, st, cx0, 322, 54, 66)
        if st != 'card_locked': kit.drawc(A, 'card_spot', cx0 + 27, 342, alpha=.6); kit.icon(A, 'furniture', cx0 + 27, 342, 24)
        else: kit.drawc(A, 'card_qmark', cx0 + 27, 342); kit.icon(A, 'lock', cx0 + 46, 330, 10)
        kit.text(A, lab, cx0 + 27, 367, 7.6, (244, 245, 252), 'sans', 0.8, (20, 24, 52))
        kit.draw(A, f'pill_{pill}', cx0 + 4, 374, 46, 11)
        if pill == 'sec': kit.lbl(A, 'btn_sec_擺緊', cx0 + 27, 379.6)
        elif pill == 'pri': kit.icon(A, 'star', cx0 + 14, 379.5, 10); kit.btext(A, 'gold', '40', cx0 + 30, 383.2, 'm', .62)
        else: kit.text(A, '委託獎', cx0 + 27, 379.4, 7.2, (38, 42, 72), 'sans', 0)
    kit.draw(A, 'btn16_pri', 62, 396, 71, 16); kit.lbl(A, 'btn_pri_完成', 97.5, 404)
    kit.text(A, '4b 佈置（kit 重砌示範；房間圖只讀 4b preview）', 97.5, 272, 6.6, (255, 236, 190), 'sans', 0.8)
    bd.alpha_composite(A, (0, 0))
    # --- 5a family tree ---
    B = dimbg(SC.copy())
    popup_window(B, 8, 40, 179, 330, '家族樹')
    kit.drawc(B, 'family_crest', 97.5, 76); kit.btext(B, 'gold', '3', 97.5, 81.5, 'm', .9)
    kit.text(B, '家族等級', 97.5, 101, 7.6, (255, 236, 190), 'sans', 0.8)
    kit.draw(B, 'exp_trough', 47, 108, 101, 5); kit.draw(B, 'exp_fill', 48, 109, 99 * .45, 3); kit.btext(B, 'px7_ol', '45/100', 97.5, 123, 'm')
    nodes = [(97.5, 150, '滴滴', 1), (60, 215, '細佬', 0), (135, 215, '???', 2), (60, 285, '???', 2)]
    kit.draw(B, 'tree_line_v', 96.5, 163, 2, 26); kit.draw(B, 'tree_line_h', 60, 189, 76, 2); kit.draw(B, 'tree_line_v', 59, 189, 2, 13); kit.draw(B, 'tree_line_v', 134, 189, 2, 13)
    kit.drawc(B, 'tree_joint', 97.5, 190); kit.draw(B, 'tree_line_v', 59, 228, 2, 44)
    for (cx, cy, nm, st) in nodes:
        kit.drawc(B, 'tree_node_sel' if st == 1 else 'tree_node', cx, cy, alpha=1 if st < 2 else .55)
        if st < 2: hh = head().resize((19 * 3, 19 * 3), Image.NEAREST); B.alpha_composite(hh, (round(cx * 3 - 28), round(cy * 3 - 30)))
        else: kit.drawc(B, 'card_qmark', cx, cy, .8)
        kit.draw(B, 'label_plate', cx - 15, cy + 13, 30, 10); kit.text(B, nm, cx, cy + 17.8, 7.2, CREAM, 'sans', 0.8)
    kit.text(B, '5a 家族（stub）', 97.5, 352, 7.0, (255, 236, 190), 'sans', 0.8)
    bd.alpha_composite(B, (W + 30, 0))
    return bd

def overview():
    A = kit.A['frames']; groups = {}
    for n, f in A.items(): groups.setdefault(f['group'], []).append(n)
    BW = 1800; bd = Image.new('RGBA', (BW, 4200), (22, 26, 52, 255)); x = y = 30; rowh = 0
    def head_(t):
        nonlocal x, y, rowh
        x = 30; y += rowh + 40; rowh = 0
        kit.text(bd, t, x / 3, (y) / 3, 9, (255, 226, 154), 'serif', 0.9, anchor='lm'); y += 30
    kit.text(bd, '《微光小圃》HD-2D UI kit 總覽 @3x（全部由 atlas JSON 砌出）— 頂 UI 0–38／花園 38–348（73%）／底 UI 348–422', 10, 10, 9, (255, 246, 207), 'serif', 1, anchor='lm')
    y = 40
    for g in ['panel', 'card', 'button', 'medallion', 'hud', 'dock', 'badge', 'toast', 'bubble', 'title', 'control', 'fx', 'stub_5a']:
        head_({'stub_5a': '5a 家族 stub', 'panel': '面板 panel（9-slice）', 'card': '卡 card', 'button': '掣 button／pill／subtab', 'medallion': '圓章 medallion',
               'hud': 'HUD（名牌／chip／需要值／進度）', 'dock': 'dock', 'badge': '紅點', 'toast': 'toast', 'bubble': '泡泡', 'title': '標題緞帶', 'control': '控件', 'fx': 'FX'}[g])
        for n in groups.get(g, []):
            im, f = kit.spr(n)
            if f['group'] == 'medallion' and im.width > 120: pass
            cw = max(im.width, len(n) * 13) + 24
            if x + cw > BW - 20: x = 30; y += rowh + 14; rowh = 0
            bd.alpha_composite(im, (x, y)); kit.text(bd, n, (x) / 3, (y + im.height + 10) / 3, 4.6, (200, 206, 232), 'sans', 0, anchor='lm')
            x += cw; rowh = max(rowh, im.height + 24)
    head_('icons（24 art；小動物有表情）')
    for n, f in kit.I['icons'].items():
        if x + 120 > BW - 20: x = 30; y += rowh + 10; rowh = 0
        kit.icon(bd, n, (x + 50) / 3, (y + 40) / 3, 24); kit.text(bd, n, (x + 50) / 3, (y + 95) / 3, 4.6, (200, 206, 232), 'sans', 0)
        x += 130; rowh = max(rowh, 110)
    head_('字體：gold（Cinzel）／round（Fredoka）／px7 像素（1x 整數倍）／標題 serif、正文 sans')
    kit.btext(bd, 'gold', '0123456789 +-×/%:', x / 3, (y + 45) / 3); kit.btext(bd, 'round', '0123456789+×!', 330, (y + 45) / 3)
    y += 70; kit.btext(bd, 'px7_ol', '0123456789 +-/%: LV.3 x3 22:30 1/2 ABCDEFGHIJKLMNOPQRSTUVWXYZ', 10, (y + 30) / 3)
    y += 50; kit.btext(bd, 'px7', '0123456789 LV.3 22:30', 10, (y + 30) / 3)
    y += 40; x = 30; rowh = 0
    for n, f in A.items():
        if f['group'] != 'label': continue
        im, _ = kit.spr(n)
        if x + im.width + 16 > BW - 20: x = 30; y += rowh + 8; rowh = 0
        bg = Image.new('RGBA', (im.width, im.height), (60, 66, 110, 255)) if not n.startswith('lbl_btn') else None
        bd.alpha_composite(im, (x, y)); x += im.width + 16; rowh = max(rowh, im.height)
    y += rowh + 30
    bd = bd.crop((0, 0, BW, y + 20))
    # thumbnails of mockups on the right? keep separate files
    return bd

home().save(f'{OUT}/mockups/home_3x.png')
popup().save(f'{OUT}/mockups/popup_3x.png')
settings().save(f'{OUT}/mockups/settings_3x.png')
journal().save(f'{OUT}/mockups/journal_dex_3x.png')
stubs().save(f'{OUT}/mockups/stubs_4b_5a_3x.png')
overview().save(f'{OUT}/overview_3x.png')
# 1x readability check: home + popup scaled to a small phone (360 px wide = 1.846 art px)
for n in ('home_3x', 'popup_3x', 'settings_3x'):
    im = Image.open(f'{OUT}/mockups/{n}.png'); im.resize((360, 779), Image.LANCZOS).save(f'{OUT}/mockups/{n.replace("_3x", "")}_smallphone_360w.png')
print('mockups ok')
