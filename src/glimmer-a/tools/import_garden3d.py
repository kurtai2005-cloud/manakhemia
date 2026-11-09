#!/usr/bin/env python3
"""3D 花園 H1 美術接入：由 art/garden3d-h1-mesh 抽 runtime 檔去 art/garden3d/。
唔 checkout 成個 art repo；跳過 .glb（引擎用 mesh json）同 preview。原創代碼。
用法：python3 tools/import_garden3d.py [ref]
"""
import io, os, shutil, subprocess, sys
REF = sys.argv[1] if len(sys.argv) > 1 else '620509fc268a26b444540b8da5120e69d3935ac4'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], cwd=ROOT, text=True).strip()
SRC = 'art-pet/scenes/garden3d/H1/'
DST = os.path.join(ROOT, 'art/garden3d/H1')
DIR4_SRC = 'art-pet/sprites/tuanrong/motion/dir4/'
DIR4_DST = os.path.join(ROOT, 'art/garden3d/dir4')
SKIP_EXT = {'.glb'}
n = 0; tot = 0

def take(src_prefix, dst_dir):
    global n, tot
    data = subprocess.check_output(['git', 'archive', '--format=tar', REF, src_prefix], cwd=REPO)
    import tarfile
    with tarfile.open(fileobj=io.BytesIO(data)) as t:
        for m in t.getmembers():
            if not m.isfile(): continue
            rel = m.name[len(src_prefix):]
            if not rel or '/preview/' in '/' + rel: continue
            ext = os.path.splitext(rel)[1].lower()
            if ext in SKIP_EXT: continue
            out = os.path.join(dst_dir, rel)
            os.makedirs(os.path.dirname(out), exist_ok=True)
            b = t.extractfile(m).read(); open(out, 'wb').write(b); n += 1; tot += len(b)

take(SRC, DST)
take(DIR4_SRC, DIR4_DST)
docs = os.path.join(ROOT, 'docs/art_garden3d')
os.makedirs(docs, exist_ok=True)
open(os.path.join(docs, 'FORMAT.md'), 'wb').write(subprocess.check_output(['git', 'show', REF + ':art-pet/scenes/garden3d/H1/FORMAT.md'], cwd=REPO))
rev = subprocess.check_output(['git', 'rev-parse', REF], cwd=REPO, text=True).strip()
os.makedirs(os.path.join(ROOT, 'art/garden3d'), exist_ok=True)
open(os.path.join(ROOT, 'art/garden3d/SOURCE.txt'), 'w').write('3D 花園 H1 美術來源：art/garden3d-h1-mesh @ %s（tools/import_garden3d.py；引擎用 json mesh，唔打包 glb）\n' % rev)
print('imported %d files, %.1f KB from %s' % (n, tot / 1e3, rev[:8]))
