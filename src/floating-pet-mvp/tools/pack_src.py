#!/usr/bin/env python3
"""源碼 zip → /workspace/bundles/floating-pet-mvp-src.zip（唔包 build/、node_modules、.gradle、www／public 大檔（build_www.py 重建）、screens、log）。"""
import os, zipfile
root = '/workspace/floating-pet-mvp'; out = '/workspace/bundles/floating-pet-mvp-src.zip'
SKIP_DIRS = {'node_modules', 'build', '.gradle', 'www', 'screens', 'public', '.idea'}
n = 0
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
        for f in files:
            if f.endswith('.log') or f == 'local.properties' or f.endswith('.apk'): continue
            p = os.path.join(d, f); z.write(p, os.path.relpath(p, '/workspace')); n += 1
print(out, n, 'files', os.path.getsize(out), 'bytes')
