#!/usr/bin/env python3
"""M1d feet fix: plant visitor pivots, clamp firefly sniff dip, shift walk_happy mid-stride.
Run from the repo root (or pass --root). Does not commit."""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()

SNAIL_PIVOT = [22, 40]
FIREFLY_PIVOT = [24, 36]
WALK_SHIFTS = {  # 1-based frame index → pixels to move DOWN (feet toward pivot 61)
    2: 3, 3: 5, 5: 3, 6: 5,
}


def load_json(p: Path):
    return json.loads(p.read_text())


def dump_json(p: Path, d):
    p.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n")


def vis_bot(crop: np.ndarray):
    a = crop[..., 3] > 0
    if not a.any():
        return None
    return int(np.where(a.any(1))[0][-1])


def shift_cell(arr: np.ndarray, x, y, w, h, dy: int, extrude=1):
    """Shift pixels inside a frame cell down (dy>0) or up (dy<0). Refresh extrude ring."""
    if dy == 0:
        return 0
    cell = arr[y:y + h, x:x + w].copy()
    out = np.zeros_like(cell)
    if dy > 0:
        out[dy:] = cell[:-dy]
    else:
        out[:dy] = cell[-dy:]
    arr[y:y + h, x:x + w] = out
    # refresh 1px extrude in the padding around the frame, if present
    if extrude and y >= extrude and x >= extrude and y + h + extrude <= arr.shape[0] and x + w + extrude <= arr.shape[1]:
        # copy edge into the ring
        ring_y0, ring_x0 = y - extrude, x - extrude
        ring_y1, ring_x1 = y + h + extrude, x + w + extrude
        # top
        arr[ring_y0:y, x:x + w] = out[0:1]
        # bot
        arr[y + h:ring_y1, x:x + w] = out[-1:]
        # left / right including corners
        arr[ring_y0:ring_y1, ring_x0:x] = arr[ring_y0:ring_y1, x:x + 1]
        arr[ring_y0:ring_y1, x + w:ring_x1] = arr[ring_y0:ring_y1, x + w - 1:x + w]
    return dy


def shift_anchor_dict(anc: dict, dy: int):
    out = dict(anc)
    for k, v in anc.items():
        if isinstance(v, list) and len(v) == 2 and all(isinstance(n, (int, float)) for n in v):
            out[k] = [v[0], v[1] + dy]
    return out


def set_pivot_in_atlas(doc: dict, pivot: list):
    doc["pivotPx"] = list(pivot)
    if isinstance(doc.get("meta"), dict):
        doc["meta"]["pivotPx"] = list(pivot)
    note = doc.get("note")
    if isinstance(note, str):
        # keep the sentence, replace old pivot tuple/list
        for old in ("[24, 44]", "[22, 45]", "(24, 44)", "(22, 45)", "[24, 36]", "[22, 40]"):
            note = note.replace(old, f"[{pivot[0]}, {pivot[1]}]")
        doc["note"] = note
    for name, rec in doc.get("frames", {}).items():
        if not isinstance(rec, dict):
            continue
        pv = rec.get("pivotPx")
        if isinstance(pv, dict):
            rec["pivotPx"] = {"x": pivot[0], "y": pivot[1]}
        elif isinstance(pv, list):
            rec["pivotPx"] = list(pivot)
        # normalized pivot if present
        fr = rec.get("frame") or {}
        h = int(fr.get("h") or doc.get("frameSize") or 48)
        if "pivot" in rec and isinstance(rec["pivot"], dict) and h:
            rec["pivot"] = {"x": rec["pivot"].get("x", pivot[0] / max(fr.get("w") or h, 1)),
                            "y": round(pivot[1] / (h if h else 1), 4)}
    return doc


def fix_visitor_atlases():
    d = ROOT / "art-pet/sprites/visitors/m2"
    changed = []
    # snail: pivot only
    for clip in ("scratch", "sneeze", "sniff"):
        jp = d / f"atlas_snail_postman_{clip}.json"
        doc = load_json(jp)
        set_pivot_in_atlas(doc, SNAIL_PIVOT)
        dump_json(jp, doc)
        changed.append(str(jp.relative_to(ROOT)))
    # firefly scratch/sneeze: pivot only
    for clip in ("scratch", "sneeze"):
        jp = d / f"atlas_firefly_vendor_{clip}.json"
        doc = load_json(jp)
        set_pivot_in_atlas(doc, FIREFLY_PIVOT)
        dump_json(jp, doc)
        changed.append(str(jp.relative_to(ROOT)))
    # firefly sniff: pivot + clamp downward frames so vis_bot <= pivot+1
    jp = d / "atlas_firefly_vendor_sniff.json"
    doc = load_json(jp)
    set_pivot_in_atlas(doc, FIREFLY_PIVOT)
    png = d / doc["meta"]["image"]
    im = Image.open(png).convert("RGBA")
    arr = np.array(im)
    py = FIREFLY_PIVOT[1]
    sniff_shifts = {}
    for name, rec in doc["frames"].items():
        fr = rec["frame"]
        x, y, w, h = fr["x"], fr["y"], fr["w"], fr["h"]
        crop = arr[y:y + h, x:x + w]
        vb = vis_bot(crop)
        # allow 1px dip (nose on dirt); anything more, shift up
        target = py + 1
        if vb is not None and vb > target:
            dy = target - vb  # negative = up
            shift_cell(arr, x, y, w, h, dy)
            if rec.get("anchors"):
                rec["anchors"] = shift_anchor_dict(rec["anchors"], dy)
            sniff_shifts[name] = dy
    if sniff_shifts:
        Image.fromarray(arr).save(png)
        dump_json(jp, doc)
    changed.append(str(jp.relative_to(ROOT)))
    changed.append(str(png.relative_to(ROOT)))
    # liveliness_clips.json
    idxp = d / "liveliness_clips.json"
    idx = load_json(idxp)
    for item in idx.get("items", []):
        if item.get("id") == "snail_postman":
            item["pivotPx"] = list(SNAIL_PIVOT)
        elif item.get("id") == "firefly_vendor":
            item["pivotPx"] = list(FIREFLY_PIVOT)
    note = idx.get("note", "")
    idx["note"] = note + " 腳錨改為實際 vis_bot：蝸牛 (22,40)、螢火 (24,36)，同招牌動作舊標註唔再跟。"
    dump_json(idxp, idx)
    changed.append(str(idxp.relative_to(ROOT)))
    return changed, sniff_shifts


def fix_actor_anim():
    p = ROOT / "data/actor_anim.json"
    d = load_json(p)
    actors = d.get("actors", {})
    if "snail_postman" in actors:
        actors["snail_postman"]["pivot"] = list(SNAIL_PIVOT)
    if "firefly_vendor" in actors:
        actors["firefly_vendor"]["pivot"] = list(FIREFLY_PIVOT)
    # default visitor is snail; plant y, keep existing x
    if "visitor" in actors:
        pv = list(actors["visitor"].get("pivot") or [24, 45])
        pv[1] = SNAIL_PIVOT[1]
        actors["visitor"]["pivot"] = pv
    dump_json(p, d)
    return [str(p.relative_to(ROOT))]


def fix_walk_happy():
    jp = ROOT / "art/liveliness/atlas_radiant_live.json"
    doc = load_json(jp)
    png = ROOT / "art/liveliness" / doc["meta"]["image"]
    im = Image.open(png).convert("RGBA")
    arr = np.array(im)
    applied = {}
    for stem in ("walk_happy", "walk_happy_noface"):
        for i, dy in WALK_SHIFTS.items():
            name = f"{stem}_{i:02d}"
            rec = doc["frames"][name]
            fr = rec["frame"]
            x, y, w, h = fr["x"], fr["y"], fr["w"], fr["h"]
            shift_cell(arr, x, y, w, h, dy)
            applied[name] = dy
    Image.fromarray(arr).save(png)
    # atlas json itself does not store face anchors; CLIPS.json does
    # no structural change to atlas json
    clips_p = ROOT / "art/liveliness/CLIPS.json"
    clips = load_json(clips_p)
    clip = next(c for c in clips["clips"] if c["name"] == "walk_happy")
    radiant = clip["anchors"]["radiant"]
    for i, dy in WALK_SHIFTS.items():
        radiant[i - 1] = shift_anchor_dict(radiant[i - 1], dy)
    dump_json(clips_p, clips)
    return [str(png.relative_to(ROOT)), str(clips_p.relative_to(ROOT))], applied


def patch_source():
    """Fix art_fix1_liveliness.py so a rebuild plants feet on the official pivot."""
    p = ROOT / "art-pet/tools/art_fix1_liveliness.py"
    t = p.read_text()
    t = t.replace(
        '    """Draw snail on 48x48, visual foot ~40, pivot (22,45) like the deliver clip."""',
        '    """Draw snail on 48x48, visual foot ~40, pivot (22,40) = vis_bot."""',
    )
    t = t.replace(
        "    dict(id='snail_postman', zh='蝸牛郵差', pivot=(22, 45)),",
        "    dict(id='snail_postman', zh='蝸牛郵差', pivot=(22, 40)),",
    )
    t = t.replace(
        "    dict(id='firefly_vendor', zh='螢火小販', pivot=(24, 44)),",
        "    dict(id='firefly_vendor', zh='螢火小販', pivot=(24, 36)),",
    )
    # firefly pin_foot block: always pin to official pivot for stand clips;
    # sniff uses a smaller hover and a shared pin so mid frames don't bury.
    old = '''        LAST_ANCHORS = face_anchors(im, (14, 16, 34, 36))
        im = outline_sel(im, OL)
        a = im[..., 3] > 0
        target = 37
        if a.any():
            foot = int(np.where(a.any(1))[0][-1])
            target = min(40, max(36, foot)) if clip != 'sniff' else min(43, max(37, foot))
        im, dx, dy = pin_foot(im, target, 24, with_delta=True)
        LAST_ANCHORS = shift_anc(LAST_ANCHORS, dx, dy)
        return im'''
    new = '''        LAST_ANCHORS = face_anchors(im, (14, 16, 34, 36))
        im = outline_sel(im, OL)
        # 官方 pivot.y=36（實際 vis_bot）。嗅地只准 1px 入土，唔好跟住 vis_bot 改變 target。
        target = 36
        im, dx, dy = pin_foot(im, target, 24, with_delta=True)
        LAST_ANCHORS = shift_anc(LAST_ANCHORS, dx, dy)
        return im'''
    if old not in t:
        raise SystemExit("source pin_foot block not found")
    t = t.replace(old, new)
    # reduce sniff hover so pin_foot(36) doesn't flatten a 8px dive through the ground
    t = t.replace(
        "            hover = [hover0 + 3, hover0 + 8, hover0 + 9, hover0][i]",
        "            hover = [hover0, hover0 + 1, hover0 + 1, hover0][i]",
    )
    p.write_text(t)
    return [str(p.relative_to(ROOT))]


def main():
    ch = []
    vis, sniff_shifts = fix_visitor_atlases()
    ch += vis
    ch += fix_actor_anim()
    walk, walk_applied = fix_walk_happy()
    ch += walk
    ch += patch_source()
    print("CHANGED", len(set(ch)))
    for p in sorted(set(ch)):
        print(" ", p)
    print("SNIFF_SHIFTS", sniff_shifts)
    print("WALK_SHIFTS", walk_applied)


if __name__ == "__main__":
    main()
