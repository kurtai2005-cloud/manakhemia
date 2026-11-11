#!/usr/bin/env python3
"""Lowest opaque row vs pivot.y. Tolerance ±1px. Airborne clips (name-matched) reported separately."""
from __future__ import annotations
import json, re, sys
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
from PIL import Image

AIR = re.compile(r'(pounce|jump|cheer|hop|picked_up|carry|part_grass|rush|fall)', re.I)
KIT = ('eyes_', 'mouth_', 'bulb_')


def vis_bot(crop):
    a = crop[..., 3] > 0
    if not a.any():
        return None
    return int(np.where(a.any(1))[0][-1])


def pivot_y(rec, sheet_pv, h):
    pv = rec.get('pivotPx')
    if isinstance(pv, dict):
        return int(pv['y'])
    if isinstance(pv, (list, tuple)) and len(pv) >= 2:
        return int(pv[1])
    if sheet_pv is not None:
        return int(sheet_pv[1] if isinstance(sheet_pv, (list, tuple)) else sheet_pv.get('y'))
    return None


def scan(root: Path, tol=1):
    rows = []
    for jf in sorted(root.glob('art*/**/atlas_*.json')):
        doc = json.loads(jf.read_text())
        img = (doc.get('meta') or {}).get('image') or (jf.stem + '.png')
        png = jf.parent / img
        if not png.exists():
            continue
        arr = np.array(Image.open(png).convert('RGBA'))
        sp = doc.get('pivotPx')
        for name, rec in doc.get('frames', {}).items():
            if name.startswith(KIT):
                continue
            fr = rec.get('frame') or rec
            if not (isinstance(fr, dict) and 'w' in fr):
                continue
            x, y, w, h = fr['x'], fr['y'], fr['w'], fr['h']
            vb = vis_bot(arr[y:y + h, x:x + w])
            py = pivot_y(rec, sp, h)
            err = None if vb is None or py is None else vb - py
            rows.append((str(jf.relative_to(root)), name, vb, py, err, bool(AIR.search(name))))
    return rows


def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else '.').resolve()
    tol = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    rows = scan(root, tol)
    off = [r for r in rows if r[4] is not None and abs(r[4]) > tol and not r[5]]
    air = [r for r in rows if r[4] is not None and abs(r[4]) > tol and r[5]]
    print(f'scanned {len(rows)} body frames  grounded_off={len(off)}  air_off={len(air)}  tol=±{tol}')
    by = defaultdict(list)
    for r in off:
        by[r[0]].append(r)
    for atlas, rs in by.items():
        c = Counter((re.sub(r'_\d+$', '', r[1]), r[4]) for r in rs)
        print(f'OFF {atlas}: {dict(c)}')
        for r in rs[:8]:
            print(f'  {r[1]} vis={r[2]} piv={r[3]} err={r[4]:+d}')
    if not off:
        print('PASS')
        sys.exit(0)
    sys.exit(1)


if __name__ == '__main__':
    main()
