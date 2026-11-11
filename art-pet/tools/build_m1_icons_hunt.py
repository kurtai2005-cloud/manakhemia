#!/usr/bin/env python3
"""build_m1_icons_hunt.py — 一鍵生成 M1 icon＋狩獵 lite，可選預覽。
用法：
  PYTHONDONTWRITEBYTECODE=1 python3 art-pet/tools/build_m1_icons_hunt.py [--root DIR] [--preview DIR]
"""
import os, sys, shutil
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

def main():
    root = os.path.abspath(os.path.join(HERE, '../..'))
    preview = '/workspace/game-design/m1_icons_hunt'
    args = sys.argv[1:]
    if '--root' in args:
        root = os.path.abspath(args[args.index('--root') + 1])
    if '--preview' in args:
        preview = os.path.abspath(args[args.index('--preview') + 1])
    print('root', root)
    import build_m1_icons
    build_m1_icons.build(root)
    print('… icons')
    import build_hunt_sprites
    build_hunt_sprites.build(root)
    print('… sprites')
    import build_hunt3d
    build_hunt3d.build(root)
    print('… hunt3d')
    if preview:
        import build_m1_previews
        build_m1_previews.build(root, preview)
        print('… previews', preview)
    print('done')

if __name__ == '__main__':
    main()
