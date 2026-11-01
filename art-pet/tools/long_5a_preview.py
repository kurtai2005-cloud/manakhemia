# 《微光小圃》5a 預覽：3 間擴房（日／夜，擺家具＋寵物）、互動 GIF（兩隻打招呼）、互動 strip 總覽
import json, os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import long_5abc_lib as LB
import long_5abc_ui as U
import long_5a_ui as UI
O5 = os.path.join(LB.OUTL, "5a"); PV = os.path.join(O5, "preview")

def x3(a): return Image.fromarray(a).resize((a.shape[1] * 3, a.shape[0] * 3), Image.NEAREST)
def rooms_sheet():
    ims, tl = [], []
    for room, items in (("room2", UI.SET_A), ("room3", UI.SET_B), ("room4", UI.SET_A)):
        for var in ("day", "night"):
            pets = UI.pets_in(UI.DEMO_PETS[room], 3)
            ims.append(x3(U.room_arr(room, var, items, pets))); tl.append(f"{UI.ROOMS[room]}・{'日' if var == 'day' else '夜'}")
    ims.insert(0, x3(U.room_arr("room1", "day", UI.SET_A))); tl.insert(0, "（對照）4b 屋仔")
    U.strip_sheet(ims, tl, os.path.join(PV, "rooms_5a_3x.png"))
    for room in ("room2", "room3", "room4"):   # 空房（新開時）
        x3(U.room_arr(room, "day", {})).save(os.path.join(PV, f"{room}_empty_day_3x.png"))

def interact_gif():
    import numpy as np
    def bw(k):
        a = U.strip_frame(k, "sit", 0)[0][..., 3]; xs = np.nonzero(a.any(0))[0]; return xs.max() - xs.min() + 1
    gap = max(22, (bw("A3") + bw("evo_still_moon")) // 2 - 4); xa, xb = 97 - gap // 2, 97 + (gap - gap // 2)
    frames = []
    for loop in range(2):
        for i in range(8):
            fa, pa, _ = U.strip_frame("A3", "interact", i, False); fb, pb, _ = U.strip_frame("evo_still_moon", "interact", i, True)
            arr = U.room_arr("room2", "day", UI.SET_A, [(fa, pa, xa, 300, 300), (fb, pb, xb, 300, 300)])
            frames.append(x3(arr).crop((0, 600, 585, 1050)))
        for j in range(4):
            fa, pa, _ = U.strip_frame("A3", "sit", j, False); fb, pb, _ = U.strip_frame("evo_still_moon", "sit", j, True)
            arr = U.room_arr("room2", "day", UI.SET_A, [(fa, pa, xa, 300, 300), (fb, pb, xb, 300, 300)])
            frames.append(x3(arr).crop((0, 600, 585, 1050)))
    LB.save_gif(frames, os.path.join(PV, "interact_duo_room2.gif"), 120)
    # 細佬＋團絨幼崽都得
    frames = []
    for i in range(8):
        row = [U.strip_frame(k, "interact", i)[0] for k in ("S2", "S4F", "C2", "sprout", "evo_hop", "evo_guard_ember")]
        h = max(r.shape[0] for r in row); w = sum(r.shape[1] for r in row); o = np.zeros((h, w, 4), np.uint8); x = 0
        for r in row: o[h - r.shape[0]:, x:x + r.shape[1]] = r; x += r.shape[1]
        im = Image.new("RGBA", (w * 3, h * 3), (64, 52, 74, 255)); im.alpha_composite(x3(o)); frames.append(im)
    LB.save_gif(frames, os.path.join(PV, "interact_forms.gif"), 120)

def strips_sheet():
    ks = LB.ALL59; cols = 3; rows = []
    for k in ks:
        a = np.asarray(Image.open(os.path.join(O5, "actions", f"{k}_interact.png")).convert("RGBA")); rows.append((k, a))
    W = max(a.shape[1] for _, a in rows); Hs = [a.shape[0] for _, a in rows]
    per = (len(rows) + cols - 1) // cols; colw = W * 3 + 20
    colh = [sum(Hs[c * per:(c + 1) * per]) * 3 + 24 * per for c in range(cols)]
    sh = Image.new("RGBA", (colw * cols, max(colh)), (40, 28, 36, 255))
    from PIL import ImageDraw
    d = ImageDraw.Draw(sh)
    for c in range(cols):
        y = 0
        for k, a in rows[c * per:(c + 1) * per]:
            d.text((c * colw + 6, y + 2), k, font=LB.font(16), fill=(255, 240, 220)); y += 22
            bg = Image.new("RGBA", (a.shape[1] * 3, a.shape[0] * 3), (64, 52, 74, 255)); bg.alpha_composite(x3(a)); sh.alpha_composite(bg, (c * colw, y)); y += a.shape[0] * 3 + 2
    sh.convert("RGB").save(os.path.join(PV, "interact_all59_3x.png"))

if __name__ == "__main__":
    os.makedirs(PV, exist_ok=True); rooms_sheet(); interact_gif(); strips_sheet(); print("preview 5a ok")
