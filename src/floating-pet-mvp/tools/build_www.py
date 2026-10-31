#!/usr/bin/env python3
"""www/index.html = glimmer-combo.html + fpet bridge（inject 喺最後 </body> 前）。"""
import sys, os
here = os.path.dirname(os.path.abspath(__file__)); root = os.path.dirname(here)
src = sys.argv[1] if len(sys.argv) > 1 else '/workspace/bundles/glimmer-combo.html'
s = open(src, encoding='utf-8').read(); b = open(os.path.join(here, 'fpet-bridge.js'), encoding='utf-8').read()
i = s.rfind('</body>'); tag = '<script id="fpet-bridge">\n' + b + '\n</script>\n'
s = s[:i] + tag + s[i:] if i >= 0 else s + tag
os.makedirs(os.path.join(root, 'www'), exist_ok=True)
open(os.path.join(root, 'www', 'index.html'), 'w', encoding='utf-8').write(s); print('www/index.html', len(s))
