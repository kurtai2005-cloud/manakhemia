#!/usr/bin/env python3
"""6c：V3 字（源雲明體 GenWanMin2 TC v2.100，OFL 1.1，https://github.com/ButTaiwan/genwan-font）子集。
   python3 tools/font_v3_subset.py DIR   # DIR 有 GenWanMin2TC-R.otf／-SB.otf（release GenWanMin2TC-otf.zip）→ 重出 art/v3/ui/fonts/*.subset.otf＋charset_v3.txt
   python3 tools/font_v3_subset.py --check   # 淨係驗：遊戲全部 CJK／全形字都喺子集（emoji／符號容許系統字補）
   字表＝舊 charset_v3.txt ∪ src/**/*.js、index.html、art/**/*.json 全部非 ASCII 字 ∪ ASCII。改咗遊戲字之後再跑一次。"""
import glob, os, subprocess, sys, unicodedata
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(ROOT)
FD = 'art/v3/ui/fonts/'; CS = FD + 'charset_v3.txt'
def chars():
    S = set(open(CS, encoding='utf8').read()) if os.path.exists(CS) else set()
    for f in glob.glob('src/**/*.js', recursive=True) + ['index.html'] + glob.glob('art/**/*.json', recursive=True):
        S |= {c for c in open(f, encoding='utf8', errors='ignore').read() if ord(c) > 127}
    return (S | {chr(i) for i in range(32, 127)}) - {'\n', '\r', '\t'}
def cjk(c): o = ord(c); return unicodedata.category(c).startswith('L') or 0x3000 <= o < 0x3100 or 0xff00 <= o < 0xffef or 0x2e80 <= o < 0xa000
def check(S):
    from fontTools.ttLib import TTFont
    bad = 0
    for w in ('R', 'SB'):
        cm = TTFont(FD + 'GenWanMin2TC-%s.subset.otf' % w, lazy=True).getBestCmap(); miss = sorted(c for c in S if ord(c) not in cm)
        m = [c for c in miss if cjk(c)]; bad += len(m)
        print(w, len(cm), 'glyphs; 缺 CJK／全形', len(m), ''.join(m), '| 系統字補（emoji／符號）', len(miss) - len(m))
    return bad
S = chars()
if sys.argv[1:] and sys.argv[1] != '--check':
    src = sys.argv[1]; open(CS, 'w', encoding='utf8').write(''.join(sorted(S)))
    for w in ('R', 'SB'):
        subprocess.check_call(['pyftsubset', os.path.join(src, 'GenWanMin2TC-%s.otf' % w), '--text-file=' + CS, '--output-file=' + FD + 'GenWanMin2TC-%s.subset.otf' % w, '--layout-features=*', '--no-hinting', '--name-IDs=*', '--name-languages=*'])
sys.exit(1 if check(S) else 0)
