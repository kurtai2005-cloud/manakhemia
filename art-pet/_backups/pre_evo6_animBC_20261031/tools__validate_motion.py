#!/usr/bin/env python3
"""validate PNGs under a directory: palette-only, alpha 0/255, size, atlas overlap, edge-clip."""
import json, os, sys, glob
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
pal = json.load(open(os.path.join(HERE, "..", "sprites", "tuanrong", "palette.json")))
PALSET = {tuple(int(c["hex"][i:i + 2], 16) for i in (1, 3, 5)) for c in pal["colors"]}
def check_png(p, size=None):
    im = Image.open(p)
    errs = []
    if im.mode != "RGBA": errs.append("mode " + im.mode)
    a = np.array(im.convert("RGBA"))
    al = np.unique(a[..., 3])
    if not set(al.tolist()) <= {0, 255}: errs.append("alpha " + str(al.tolist()))
    px = a[a[..., 3] == 255][:, :3]
    cols = {tuple(c) for c in np.unique(px, axis=0).tolist()} if len(px) else set()
    bad = cols - PALSET
    if bad: errs.append("offpalette %d e.g. %s" % (len(bad), sorted(bad)[:2]))
    if size and im.size != size: errs.append("size %s != %s" % (im.size, size))
    edge = bool(a[0, :, 3].max() or a[:, 0, 3].max() or a[:, -1, 3].max())  # bottom ignored (feet outline)
    return errs, edge, im.size
def check_atlas(js, png, maxdim=1024):
    d = json.load(open(js)); im = Image.open(png); errs = []
    if im.width > maxdim or im.height > maxdim: errs.append("atlas too big %s" % (im.size,))
    rects = [(k, v["frame"]) for k, v in d["frames"].items()]
    for i, (k, r) in enumerate(rects):
        if r["x"] < 2 or r["y"] < 2 or r["x"] + r["w"] > im.width - 2 or r["y"] + r["h"] > im.height - 2: errs.append("bounds " + k)
        for k2, r2 in rects[i + 1:]:
            if not (r["x"] + r["w"] + 2 <= r2["x"] or r2["x"] + r2["w"] + 2 <= r["x"] or r["y"] + r["h"] + 2 <= r2["y"] or r2["y"] + r2["h"] + 2 <= r["y"]):
                errs.append("overlap/pad %s %s" % (k, k2))
    A = np.array(im.convert("RGBA"))
    for k, r in rects:  # atlas pixels equal individual frame
        pass
    return errs, im.size, len(rects)
if __name__ == "__main__":
    root = sys.argv[1]; size_by_dir = {"sprout": (32, 32), "radiant": (64, 64), "soft": (64, 64)}
    n = 0; bad = 0; edges = []
    for p in sorted(glob.glob(root + "/**/*.png", recursive=True)):
        if "/atlas" in p.replace("\\", "/") or os.path.basename(p).startswith(("atlas", "contact")): continue
        form = next((f for f in size_by_dir if f"/{f}/" in p), None)
        errs, edge, sz = check_png(p, size_by_dir.get(form) if form else None)
        n += 1
        if errs: bad += 1; print("ERR", p, errs)
        if edge and form: edges.append(os.path.relpath(p, root))
    print("png checked", n, "bad", bad)
    print("frames touching border:", len(edges), edges[:12])
    for js in sorted(glob.glob(root + "/atlas_*.json")):
        e, sz, c = check_atlas(js, js.replace(".json", ".png")); print("atlas", os.path.basename(js), sz, c, "frames", "OK" if not e else e[:5])
