#!/usr/bin/env python3
"""V3 美術接入：由 art branch（預設 art/workscenes-v3）用 git archive 抽 runtime 要用嘅檔去 art/v3/。
唔 checkout 成個 art repo；跳過 preview／raw／mockups／1x 層。原創代碼。
用法：python3 tools/import_v3.py [ref]"""
import io, os, re, subprocess, sys, tarfile
REF = sys.argv[1] if len(sys.argv) > 1 else 'art/workscenes-v3'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], cwd=ROOT, text=True).strip()
MAP = [  # (src prefix, dest, include regex（相對 src）)
    ('art-pet/scenes/hd2d_v3/', 'art/v3/garden/', r'^(fx/.*|seasons/fx/.*|seasons/seasons_v3\.json|(seasons/[a-z]+/)?H\d/(grade\.json|x3/.*)|H3/grade_[a-z]+\.json|H3/[a-z]+/x3/.*)$'),
    ('art-pet/ui/kit_hd2d_v3/', 'art/v3/ui/', r'^(atlas/(ui_hd2d_v3@3x|icons_hd2d_v3@3x|icons_hd2d_v3@6x|icons_glow_hd2d_v3@3x)\.(png|json)|atlas/v2_to_v3_map\.json|fonts/.*\.(otf|txt|json)|layout_hd2d_v3\.json|portrait/portrait_rects\.json)$'),
    ('art-pet/sprites/tuanrong/petglow_v3/', 'art/v3/petglow/tuanrong/', r'^[a-z_0-9]+(_glow@3x)?\.(json|png)$'),
    ('art-pet/sprites/series2/petglow_v3/', 'art/v3/petglow/kid/', r'^[A-Za-z_0-9]+(_glow@3x)?\.(json|png)$'),
    ('art-pet/sprites/series2_house/v3/', 'art/v3/house/', r'^(house_v3\.json|furniture_v3\.json|souvenir_v3\.json|light/.*|furniture/.*|souvenir/.*|rooms/room\d/(day|night)/(grade\.json|x3/.*))$'),
    ('art/breakthrough/6b/v3/', 'art/v3/walk/', r'^(walk6b_v3\.json|deco/.*|walk_bg/stone_glow@3x\.png|walk_bg/(day|dusk|night)/(grade\.json|x3/.*))$'),
]
DOCS = ['art-pet/ui/style_ref/hd2d_v3/V3.md', 'art-pet/ui/kit_hd2d_v3/UI_KIT_V3.md', 'art-pet/scenes/hd2d_v3/FORMAT_V3.md', 'art-pet/scenes/hd2d_v3/seasons/SEASONS_V3.md',
        'art-pet/sprites/tuanrong/petglow_v3/PETGLOW_V3.md', 'art-pet/sprites/series2/petglow_v3/PETGLOW_KID_V3.md', 'art-pet/sprites/series2_house/v3/HOUSE_V3.md', 'art/breakthrough/6b/v3/WALK_6B_V3.md']
n = 0; tot = 0
for src, dst, rx in MAP:
    data = subprocess.check_output(['git', 'archive', '--format=tar', REF, src], cwd=REPO)
    with tarfile.open(fileobj=io.BytesIO(data)) as t:
        for m in t.getmembers():
            if not m.isfile(): continue
            rel = m.name[len(src):]
            if '/preview/' in '/' + rel or '/raw/' in '/' + rel or not re.match(rx, rel): continue
            out = os.path.join(ROOT, dst, rel); os.makedirs(os.path.dirname(out), exist_ok=True)
            b = t.extractfile(m).read(); open(out, 'wb').write(b); n += 1; tot += len(b)
os.makedirs(os.path.join(ROOT, 'docs/art_v3'), exist_ok=True)
for d in DOCS:
    open(os.path.join(ROOT, 'docs/art_v3', os.path.basename(d)), 'wb').write(subprocess.check_output(['git', 'show', REF + ':' + d], cwd=REPO))
rev = subprocess.check_output(['git', 'rev-parse', REF], cwd=REPO, text=True).strip()
open(os.path.join(ROOT, 'art/v3/SOURCE.txt'), 'w').write('V3 美術來源：%s @ %s（tools/import_v3.py）\n' % (REF, rev))
print('imported %d files, %.1f MB from %s @ %s' % (n, tot / 1e6, REF, rev[:8]))
