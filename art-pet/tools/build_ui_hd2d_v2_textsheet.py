# 《微光小圃》HD-2D v2 kit — Fusion Pixel 字體樣板（8／10／12 + 常用色 + charset 全表）— 遊美 2026-11-02
# 用 build_ui_hd2d_v2_mockups 嘅 text() 引擎（tint→描邊→影），1x 畫完 ×3 nearest。純 Pillow／numpy。
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import build_ui_hd2d_v2_mockups as M
from hd2d_v2_px import P, new, up, put
W = 300
G = M.FJ['fp8']['glyphs']; chars = ''.join(sorted(c for c in G if c.strip()))
per = 34; rows = [chars[i:i + per] for i in range(0, len(chars), per)]
H = 196 + len(rows) * 10 + 14
bd = new(W, H, P['nv3'])
put(bd, M.nine('panel_navy', W - 8, 186), 4, 4)
M.text(bd, 'Fusion Pixel 字體（OFL 1.1）· kit_hd2d_v2', 12, 16, 12, col='white', col2='g_hi')
y = 32
for sz in (12, 10, 8):
    M.text(bd, f'fp{sz}：團絨今日好開心！Lv5 +120 ×2 18:00', 12, y + sz // 2, sz); y += sz + 8
y += 2
M.text(bd, '8px 面板正文（唔描邊）：夜晚會喺窗邊發出淡淡月光，最鍾意聽故事。', 12, y, 8, col='paper1'); y += 12
put(bd, M.nine('bubble', 200, 16), 12, y); M.text(bd, '泡泡字 ink 無描邊：肚仔餓…', 18, y + 8, 10, col='ink', ol=False, shadow=False); y += 22
cx = 12
for f, t in (('pri', '確認'), ('sec', '存檔'), ('rose', '重置'), ('violet', '通知'), ('dis', '未開')):
    b = M.button(t, 50, f); put(bd, b, cx, y); cx += 54
y += 26; cx = 12
for f in ('pri', 'sec', 'rose', 'violet', 'navy'):
    p = M.pill('Lv3→4', f, M.tw('Lv3→4', 8) + 16); put(bd, p, cx, y); cx += p.width + 6
y += 18
M.text(bd, '金字 col2：升級喇！', 12, y + 6, 12, col='white', col2='g_hi', outline='g_dk'); M.text(bd, '細字 paper2：省電 標準 靚', 150, y + 6, 8, col='paper2')
y = 196
M.text(bd, f'charset（fp8，{len(G)} 字；由 kit md／series2／5x json／builder 原始碼收集）', 8, y - 4, 8, col='g_hi')
for r in rows:
    M.text(bd, r, 8, y + 6, 8, col='cream'); y += 10
out = f'{M.KIT}/fonts/text_sheet_3x.png'; up(bd, 3).save(out); print(out, bd.size, 'missing', ''.join(sorted(M.MISSING)) or 'none')
