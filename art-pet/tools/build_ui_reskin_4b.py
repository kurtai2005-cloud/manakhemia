# 《微光小圃》4b 屋仔 UI → HD-2D kit 重砌包（UI_KIT.md §6 建議落實）。
# 只讀 sprites/series2_house/（ui/*.png 量尺寸、furniture/*.png 做縮圖、ui/icon_<類別> 做 tab icon），一個 byte 都唔寫返去。
# 輸出：ui/kit_hd2d/reskin_4b/<同名>@3x.png（同 canvas 尺寸、同中心）＋ reskin_map.json ＋ preview_before_after_3x.png
import os, json, hashlib
from PIL import Image, ImageDraw, ImageFont
import ui_hd2d_kit as K
from ui_kit_hd2d_render import Kit
ROOT = K.ROOT; H4 = f'{ROOT}/sprites/series2_house'; U4 = f'{H4}/ui'; OUT = f'{ROOT}/ui/kit_hd2d/reskin_4b'
os.makedirs(OUT, exist_ok=True); kit = Kit(3); S = 3
CREAM = (244, 245, 252); NAMEST = (20, 24, 52)
def sha(p): return hashlib.sha1(open(p, 'rb').read()).hexdigest()
before = {f: sha(f'{U4}/{f}') for f in sorted(os.listdir(U4))}
def size4b(n): return Image.open(f'{U4}/{n}@3x.png').size
def canvas(n): return Image.new('RGBA', size4b(n), (0, 0, 0, 0))
def ic4b(bd, n, cx, cy, size, alpha=1.0):
    im = Image.open(f'{U4}/icon_{n}@3x.png').convert('RGBA'); sc = size / 24
    im = im.resize((round(im.width * sc), round(im.height * sc)), Image.LANCZOS)
    if alpha < 1: im.putalpha(im.getchannel('A').point(lambda v: int(v * alpha)))
    bd.alpha_composite(im, (round(cx * S - im.width / 2), round(cy * S - im.height / 2)))
def thumb(bd, name, cx, cy, maxw=46, maxh=30, sil=False):
    im = Image.open(f'{H4}/furniture/{name}.png').convert('RGBA'); w, h = im.size
    k = min(maxw / w, maxh / h); tw, th = round(w * k * S), round(h * k * S)
    im = im.resize((tw, th), Image.LANCZOS)
    if sil:
        a = im.getchannel('A').point(lambda v: int(v * .82)); im = Image.new('RGBA', im.size, (30, 34, 66, 255)); im.putalpha(a)
    bd.alpha_composite(im, (round(cx * S - tw / 2), round(cy * S - th / 2)))
M = []; OUTS = {}
def save(n, im, parts, why, anchor, optional=False):
    assert im.size == size4b(n), n
    p = f'{OUT}/{n}@3x.png'; im.save(p, optimize=True); OUTS[n] = im
    M.append(dict(id=n, orig=f'sprites/series2_house/ui/{n}@3x.png', reskin=f'ui/kit_hd2d/reskin_4b/{n}@3x.png',
                  size=list(im.size), anchor=anchor, kitParts=parts, change=why, optional=optional))

# ---- 圓章類（中心＝canvas 中心）----
for n, d, base, ic, isz in (('btn_back', 22, 'med22_navy', 'back', 15), ('btn_house', 24, 'med24_navy', 'house', 17)):
    bd = canvas(n); c = bd.width / 6; kit.drawc(bd, base, c, c); kit.icon(bd, ic, c, c, isz)
    save(n, bd, [base, f'ic:{ic}'], f'd{d} 金框海軍藍圓章＋kit icon（同 HUD 其他圓章一致）', 'center')
bd = canvas('btn_house_locked'); c = bd.width / 6
kit.drawc(bd, 'med24_dis', c, c); kit.icon(bd, 'house', c, c, 17, alpha=.55); kit.icon(bd, 'lock', c + 6.5, c + 6.5, 10)
save('btn_house_locked', bd, ['med24_dis', 'ic:house α.55', 'ic:lock'], 'part 2 新 med24_dis 停用圓章；屋 icon α.55＋右下鎖', 'center')
bd = canvas('btn_decorate'); cx = bd.width / 6; cy = 17.0
kit.drawc(bd, 'med30_pri', cx, cy); kit.icon(bd, 'decorate', cx, cy, 21)
kit.draw(bd, 'label_plate', cx - 15, cy + 14, 30, 10); kit.lbl(bd, 'act_佈置', cx, cy + 19)
save('btn_decorate', bd, ['med30_pri', 'ic:decorate', 'label_plate', 'lbl_act_佈置'], 'd30 橙金圓章＋kit 字牌（同 HUD 動作掣一致）；label 中心＝圓心下 19 art（= layout labelY）', 'center x；圓心 y=17 art（51px）')
for st, d, base in (('idle', 16, 'med16_navy'), ('sel', 20, 'med20_pri')):
    bd = canvas(f'pin_plus_{st}'); c = bd.width / 6
    if st == 'sel': kit.drawc(bd, 'fx_ripple', c, c, .9, .75)
    kit.drawc(bd, base, c, c); kit.icon(bd, 'plus', c, c, d * .62)
    save(f'pin_plus_{st}', bd, [base, 'ic:plus'] + (['fx_ripple'] if st == 'sel' else []), f'd{d} kit 圓章＋part 2 新 ic:plus', 'center')
    bd = canvas(f'pin_filled_{st}'); c = bd.width / 6
    if st == 'sel': kit.drawc(bd, 'fx_ripple', c, c, .9, .75)
    kit.drawc(bd, base, c, c)
    save(f'pin_filled_{st}', bd, [base] + (['fx_ripple'] if st == 'sel' else []), f'd{d} kit 圓章底（engine 照舊疊 slot icon）', 'center')
for t in ('bed', 'table', 'wall', 'rug', 'window', 'lamp'):
    for st, base, isz in (('idle', 'med22_navy', 15), ('sel', 'med25_pri', 17)):
        n = f'tab_{t}_{st}'; bd = canvas(n); c = bd.width / 6
        kit.drawc(bd, base, c, c); ic4b(bd, t, c, c, isz)
        save(n, bd, [base, f'4b icon_{t}（只讀）'], 'kit 圓章底（idle 海軍藍 d22／sel 橙金 d25）；家具類別 icon 沿用 4b', 'center')
# ---- 完成掣 / sheet ----
bd = canvas('btn_done'); cx, cy = bd.width / 6, bd.height / 6
kit.draw(bd, 'btn16_pri', cx - 35.5, cy - 8, 71, 16); kit.lbl(bd, 'btn_pri_完成', cx, cy)
save('btn_done', bd, ['btn16_pri', 'lbl_btn_pri_完成'], '16 art 細身主掣（同 popup 掣一致）', 'center（box 71×16）')
bd = canvas('sheet_panel'); cx, cy = bd.width / 6, bd.height / 6
kit.draw(bd, 'panel_glass_plain', cx - 93.5, cy - 69, 187, 138); kit.drawc(bd, 'sheet_handle', cx, cy - 65)
save('sheet_panel', bd, ['panel_glass_plain', 'sheet_handle'], '海軍藍玻璃 panel＋金邊＋拉柄（同 popup 一致）', 'center（box 187×138）')
# ---- 卡 ----
def card(n, frame, furn, name, pill, lbl=None, why='', extra=()):
    bd = canvas(n); x0, y0 = bd.width / 6 - 27, bd.height / 6 - 33; parts = [frame]
    kit.draw(bd, frame, x0, y0, 54, 66)
    if furn == 'clear': kit.drawc(bd, 'card_spot', x0 + 27, y0 + 20, alpha=.45); kit.icon(bd, 'clear', x0 + 27, y0 + 20, 20); parts += ['card_spot', 'ic:clear']
    elif 'locked' in frame: thumb(bd, furn, x0 + 27, y0 + 20, sil=True); kit.icon(bd, 'lock', x0 + 27, y0 + 21, 14); parts += [f'furniture/{furn}（剪影）', 'ic:lock']
    else: kit.drawc(bd, 'card_spot', x0 + 27, y0 + 20, alpha=.6); thumb(bd, furn, x0 + 27, y0 + 20); parts += ['card_spot', f'furniture/{furn}']
    kit.text(bd, name, x0 + 27, y0 + 44, 7.6, CREAM, 'sans', 0.8, NAMEST)
    kit.draw(bd, f'pill_{pill}', x0 + 4, y0 + 51, 46, 11); parts.append(f'pill_{pill}')
    if lbl: kit.lbl(bd, lbl, x0 + 27, y0 + 56.5); parts.append('lbl_' + lbl)
    else: kit.icon(bd, 'star', x0 + 14, y0 + 56.5, 10); kit.btext(bd, 'gold', '40', x0 + 30, y0 + 60.2, 'm', .62); parts += ['ic:star', 'font gold']
    if 'gem' in extra: kit.drawc(bd, 'dock_gem', x0 + 49, y0 + 5); parts.append('dock_gem')
    save(n, bd, parts, why, 'center（box 54×66；縮圖 cy +20、名 +44、pill +51 h11 inset 4＝layout.cards）')
card('card_equipped_example', 'card_sel', 'bed_leaf', '葉仔床', 'sec', 'pill_sec_擺緊', '揀中卡金光框＋右上寶石＋藍綠 pill', ('gem',))
card('card_owned_example', 'card', 'lamp_mushroom', '蘑菇燈', 'pri', 'pill_pri_擺上去', 'kit 卡＋橙 pill')
card('card_buy_example', 'card', 'bed_cloud', '雲朵床', 'pri', None, 'kit 卡＋橙 pill（星星碎 icon＋金字價錢）；唔夠碎 → 換 pill_dis')
card('card_locked_example', 'card_locked', 'win_star', '星星窗', 'dis', 'pill_dis_委託獎', '灰卡＋暗剪影＋鎖＋來源 pill（訪客禮＝lbl_pill_dis_訪客禮）')
card('card_clear_example', 'card', 'clear', '收起', 'navy', 'pill_navy_清空', 'kit 卡＋part 2 新 ic:clear＋新 pill_navy')
# ---- 單 icon（4b icon canvas 90×90，icon 24 art 置中）----
for t in ('back', 'plus', 'clear', 'lock', 'house', 'decorate'):
    n = f'icon_{t}'; bd = canvas(n); c = bd.width / 6; kit.icon(bd, t, c, c, 24)
    save(n, bd, [f'ic:{t}'], '可選：kit icon 同名替換（有樣仔面＋暖色描邊）；4b 原 icon 都夾，遊程/4b 話事', 'center', optional=True)
KEEP = [f'icon_{t}' for t in ('bed', 'table', 'wall', 'rug', 'window', 'lamp')] + ['layout.json']
after = {f: sha(f'{U4}/{f}') for f in sorted(os.listdir(U4))}
assert before == after, '4b 檔被改咗！'
json.dump(dict(version='reskin_4b-1.0', note='遊美 HD-2D kit 重砌 4b 屋仔 UI。全部同 4b 原檔同名、同 canvas 尺寸、同中心 → 遊程 只要將 asset 路徑由 orig 換做 reskin（或者將 reskin_4b/*.png 覆蓋落 sprites/series2_house/ui/，由 4b 負責人決定），layout.json 數字唔使改。4b 檔冇改（建包時 sha1 前後對過）。',
               swap='drop-in：同名、同尺寸、同 anchor', layoutChanges='無', keptFrom4b=KEEP, untouched4bSha1=after, items=M),
          open(f'{OUT}/reskin_map.json', 'w'), ensure_ascii=False, indent=1)
# ---- before/after preview ----
order = [m['id'] for m in M]; cell = 240; cols = 6; rows = -(-len(order) // cols)
pv = Image.new('RGBA', (cols * cell * 2 + 40, rows * (cell + 30) + 60), (18, 20, 40, 255)); d = ImageDraw.Draw(pv)
f = ImageFont.truetype(K.CJK_SANS, 20, index=4)
d.text((20, 18), '4b 原版（左）→ kit 重砌（右）  reskin_4b/', font=f, fill=(255, 236, 190))
for i, n in enumerate(order):
    r, cI = divmod(i, cols); X = 20 + cI * cell * 2; Y = 60 + r * (cell + 30)
    for j, im in enumerate((Image.open(f'{U4}/{n}@3x.png').convert('RGBA'), OUTS[n])):
        sc = min(1, (cell - 16) / max(im.size)); t = im.resize((round(im.width * sc), round(im.height * sc)), Image.LANCZOS)
        bx = X + j * cell; d.rectangle((bx + 4, Y, bx + cell - 4, Y + cell - 4), fill=(34, 38, 66, 255) if j == 0 else (44, 40, 70, 255))
        pv.alpha_composite(t, (bx + (cell - t.width) // 2, Y + (cell - 4 - t.height) // 2))
    d.text((X + 8, Y + cell - 2), n, font=f, fill=(220, 225, 245))
pv.convert('RGB').save(f'{OUT}/preview_before_after_3x.png', optimize=True)
print('reskin', len(M), 'items; 4b untouched')
