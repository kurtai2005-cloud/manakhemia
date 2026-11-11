#!/usr/bin/env python3
"""build_m2_actions.py — 一鍵生成 M2 動作＋道具＋訪客，可選預覽。"""
import os, sys
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

def main():
    root = os.path.abspath(os.path.join(HERE, '../..'))
    preview = '/workspace/game-design/m2_actions'
    args = sys.argv[1:]
    if '--root' in args:
        root = os.path.abspath(args[args.index('--root') + 1])
    if '--preview' in args:
        preview = os.path.abspath(args[args.index('--preview') + 1])
    print('root', root)
    import build_m2_clips; build_m2_clips.build(root); print('… clips')
    import build_m2_props; build_m2_props.build(root); print('… props')
    import build_m2_visitors; build_m2_visitors.build(root); print('… visitors')
    if preview:
        import build_m2_previews; build_m2_previews.build(root, preview); print('… previews', preview)
    print('done')

if __name__ == '__main__':
    main()
