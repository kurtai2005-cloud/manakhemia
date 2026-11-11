#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""驗證 art-pet/anim_timing.json。

檢查：clip 數同 atlas 一致；fps／幀數／loop 同 atlas 一致；
frameMs 加總 = durationMs，而且同 fps 換算一致；
每個 event 必有 sfx_hook、t_ms、accent；
sfx_hook 須存在於 art-pet/sfx_hooks.json（或 --sfx-readme 覆蓋）或為 null；
t_ms 喺 clip 長度內，而且等於 sum(frameMs[:frameIndex])；
accent 只可以係 land／peak／release。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# 同生成器共用
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_anim_timing as B  # noqa: E402

ACCENTS = B.ACCENTS


def err(errors: list[str], msg: str) -> None:
    errors.append(msg)


def discover_clip_ids(m1: Path, m2: Path) -> dict[str, dict]:
    """由 atlas／index 收集全部應有 clip，同埋基準時機。"""
    found: dict[str, dict] = {}

    def add(cid, fps, n, loop, src):
        if cid in found:
            prev = found[cid]
            if (prev['fps'], prev['frameCount'], prev['loop']) != (fps, n, loop):
                raise SystemExit(f'發現重複 clip {cid} 時機唔一致（{src}）')
        found[cid] = {'fps': fps, 'frameCount': n, 'loop': loop, 'src': src}

    hunt = m1 / 'art-pet/sprites/tuanrong/motion/hunt/clips.json'
    CI = json.loads(hunt.read_text(encoding='utf-8'))
    folder = hunt.parent
    for name, meta in CI['clips'].items():
        for sz, fn in CI['atlases'].items():
            J = json.loads((folder / fn[name]).read_text(encoding='utf-8'))
            add(name, J['fps'], J['frameCount'], J['loop'], f'hunt/{sz}')
            if J['frameCount'] != meta['frames'] or J['fps'] != meta['fps'] or J['loop'] != meta['loop']:
                raise SystemExit(f'{name} {sz} atlas 同 clips.json 唔一致')

    crit_dir = m1 / 'art-pet/sprites/hunt/critters'
    for p in sorted(crit_dir.glob('*.json')):
        if p.name == 'critters.json':
            continue
        J = json.loads(p.read_text(encoding='utf-8'))
        for anim, am in J['animations'].items():
            add(f"{J['id']}_{anim}", am['fps'], len(am['frames']), am['loop'], p.name)

    m2idx = m2 / 'art-pet/sprites/tuanrong/motion/m2/clips.json'
    CI = json.loads(m2idx.read_text(encoding='utf-8'))
    folder = m2idx.parent
    for name, meta in CI['clips'].items():
        for sz, fn in CI['atlases'].items():
            J = json.loads((folder / fn[name]).read_text(encoding='utf-8'))
            add(name, J['fps'], J['frameCount'], J['loop'], f'm2/{sz}')
            if J['frameCount'] != meta['frames'] or J['fps'] != meta['fps'] or J['loop'] != meta['loop']:
                raise SystemExit(f'{name} {sz} atlas 同 clips.json 唔一致')

    vpath = m2 / 'art-pet/sprites/visitors/m2/visitors.json'
    V = json.loads(vpath.read_text(encoding='utf-8'))
    vfolder = vpath.parent
    for it in V['items']:
        J = json.loads((vfolder / it['atlas']).read_text(encoding='utf-8'))
        add(f"{it['id']}_{it['clip']}", J['fps'], J['frameCount'], J['loop'], it['atlas'])
    return found


def validate(timing_path: Path, *, m1: Path | None, m2: Path | None,
             root: Path, sfx_readme: Path | None,
             report_path: Path | None = None,
             refresh_hooks: bool = False) -> int:
    errors: list[str] = []
    warnings: list[str] = []
    doc = json.loads(timing_path.read_text(encoding='utf-8'))

    if doc.get('format') != 'anim_timing/1':
        err(errors, f'format 應為 anim_timing/1，實際 {doc.get("format")!r}')
    if doc.get('toleranceFrames') != 1:
        err(errors, f'toleranceFrames 應為 1，實際 {doc.get("toleranceFrames")!r}')

    args_ns = argparse.Namespace(root=str(root), m1=str(m1) if m1 else None,
                                 m2=str(m2) if m2 else None, sfx_readme=str(sfx_readme) if sfx_readme else None)
    m1r, m2r = B.resolve_roots(args_ns)
    found = discover_clip_ids(m1r, m2r)

    clips = doc.get('clips') or []
    ids = [c.get('id') for c in clips]
    if len(ids) != len(set(ids)):
        err(errors, f'clip id 有重複：{[i for i in ids if ids.count(i) > 1]}')

    timing_ids = set(ids)
    atlas_ids = set(found)
    if timing_ids != atlas_ids:
        missing = sorted(atlas_ids - timing_ids)
        extra = sorted(timing_ids - atlas_ids)
        if missing:
            err(errors, f'atlas 有但 timing 冇：{missing}')
        if extra:
            err(errors, f'timing 有但 atlas 冇：{extra}')

    # hook 表：預設 art-pet/sfx_hooks.json；--sfx-readme 先覆蓋。唔會讀本 repo 舊 audio/README.md。
    try:
        hook_list, hook_meta = B.resolve_hooks(root, sfx_readme, refresh=refresh_hooks)
        hooks = set(hook_list)
    except SystemExit as e:
        err(errors, f'讀 hook 表失敗：{e}')
        hooks = set()
    baked = set((doc.get('sfxHooks') or {}).get('names') or [])
    if hooks and baked and baked != hooks:
        warnings.append(
            f'anim_timing.json 內烘焙 hook 表同 {hook_meta.get("via")} 唔一致 '
            f'(baked={len(baked)} current={len(hooks)} '
            f'only_baked={sorted(baked-hooks)[:8]} only_current={sorted(hooks-baked)[:8]})'
        )
    if not hooks:
        err(errors, '冇任何允許嘅 sfx_hook 名單（請確認 art-pet/sfx_hooks.json 存在，或用 --sfx-readme --refresh-hooks）')

    ev_total = 0
    ev_null = 0
    ev_hooked = 0
    null_list = []

    for c in clips:
        cid = c.get('id')
        base = found.get(cid)
        n = c.get('frameCount')
        fps = c.get('fps')
        fms = c.get('frameMs')
        dur = c.get('durationMs')
        if base:
            if c.get('fps') != base['fps']:
                err(errors, f'{cid}: fps {c.get("fps")} ≠ atlas {base["fps"]}')
            if c.get('frameCount') != base['frameCount']:
                err(errors, f'{cid}: frameCount {c.get("frameCount")} ≠ atlas {base["frameCount"]}')
            if c.get('loop') != base['loop']:
                err(errors, f'{cid}: loop {c.get("loop")} ≠ atlas {base["loop"]}')
        if not isinstance(fms, list) or (n is not None and len(fms) != n):
            err(errors, f'{cid}: frameMs 長度 {0 if not isinstance(fms, list) else len(fms)} ≠ frameCount {n}')
            continue
        if any(not isinstance(x, int) or x < 0 for x in fms):
            err(errors, f'{cid}: frameMs 要係非負整數')
        expect = B.frame_ms_list(n, fps) if (n and fps) else None
        if expect is not None and fms != expect:
            err(errors, f'{cid}: frameMs {fms} ≠ 由 fps 換算 {expect}')
        if dur != sum(fms):
            err(errors, f'{cid}: durationMs {dur} ≠ sum(frameMs) {sum(fms)}')
        if fps and n and dur != B.duration_ms(n, fps):
            err(errors, f'{cid}: durationMs {dur} ≠ round(n*1000/fps) {B.duration_ms(n, fps)}')

        events = c.get('events')
        if not isinstance(events, list):
            err(errors, f'{cid}: events 要係陣列')
            continue
        for i, ev in enumerate(events):
            ev_total += 1
            prefix = f'{cid}.events[{i}]'
            for key in ('sfx_hook', 't_ms', 'accent'):
                if key not in ev:
                    err(errors, f'{prefix}: 欠欄 {key}')
            hook = ev.get('sfx_hook', '__missing__')
            t = ev.get('t_ms')
            accent = ev.get('accent')
            fi = ev.get('frameIndex')
            if hook is None:
                ev_null += 1
                null_list.append({
                    'clip': cid,
                    'id': ev.get('id'),
                    'zh': ev.get('zh'),
                    'frameIndex': fi,
                    't_ms': t,
                    'accent': accent,
                    'note': ev.get('note'),
                })
            elif hook == '__missing__':
                pass
            else:
                ev_hooked += 1
                if hook not in hooks:
                    err(errors, f'{prefix}: sfx_hook {hook!r} 唔喺遊音 hook 表，亦唔係 null')
            if accent is not None and accent not in ACCENTS:
                err(errors, f'{prefix}: accent {accent!r} 唔係 land/peak/release')
            if not isinstance(t, int):
                err(errors, f'{prefix}: t_ms 要係整數，實際 {t!r}')
            else:
                if dur is not None and not (0 <= t <= dur):
                    err(errors, f'{prefix}: t_ms {t} 超出 clip 長度 0..{dur}')
                if isinstance(fi, int) and 0 <= fi <= len(fms):
                    expect_t = sum(fms[:fi])
                    if t != expect_t:
                        err(errors, f'{prefix}: t_ms {t} ≠ sum(frameMs[:{fi}]) {expect_t}')
                elif fi is None:
                    err(errors, f'{prefix}: 欠 frameIndex')
                else:
                    err(errors, f'{prefix}: frameIndex {fi} 超出 0..{len(fms)-1}')

        # 寵物 S/M/L 齊
        if c.get('kind') == 'pet':
            if c.get('sizes') != ['S', 'M', 'L']:
                err(errors, f'{cid}: 寵物 clip 應有 sizes S/M/L，實際 {c.get("sizes")}')

    counts = doc.get('counts') or {}
    if counts.get('clips') != len(clips):
        err(errors, f'counts.clips {counts.get("clips")} ≠ 實際 {len(clips)}')
    if counts.get('events') != ev_total:
        err(errors, f'counts.events {counts.get("events")} ≠ 實際 {ev_total}')
    if counts.get('eventsHookNull') != ev_null:
        err(errors, f'counts.eventsHookNull {counts.get("eventsHookNull")} ≠ 實際 {ev_null}')
    if counts.get('eventsWithHook') != ev_hooked:
        err(errors, f'counts.eventsWithHook {counts.get("eventsWithHook")} ≠ 實際 {ev_hooked}')

    report = {
        'ok': not errors,
        'errors': errors,
        'warnings': warnings,
        'clips': len(clips),
        'atlasClips': len(found),
        'events': ev_total,
        'eventsWithHook': ev_hooked,
        'eventsHookNull': ev_null,
        'nullHooks': null_list,
        'hookTableSize': len(hooks),
    }
    if report_path:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(f'wrote {report_path}')

    if errors:
        print(f'FAIL  {len(errors)} error(s), {len(warnings)} warning(s)')
        for e in errors:
            print('  -', e)
        return 1
    print(f'OK  clips={len(clips)} (atlas={len(found)})  events={ev_total}  '
          f'hooked={ev_hooked}  null={ev_null}  warnings={len(warnings)}')
    for w in warnings:
        print('  warn:', w)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description='驗證 art-pet/anim_timing.json')
    ap.add_argument('--root', default='.')
    ap.add_argument('--m1', default=None)
    ap.add_argument('--m2', default=None)
    ap.add_argument('--sfx-readme', default=None,
                    help='遊音最新 audio/README.md（覆蓋快照；配合 --refresh-hooks 重寫 art-pet/sfx_hooks.json）')
    ap.add_argument('--refresh-hooks', action='store_true',
                    help='用 --sfx-readme 抽出嘅名單重寫 art-pet/sfx_hooks.json（必須同時提供 --sfx-readme）')
    ap.add_argument('--timing', default=None, help='anim_timing.json（預設 <root>/art-pet/anim_timing.json）')
    ap.add_argument('--write-report', default=None, help='寫 validation JSON')
    args = ap.parse_args()
    timing = Path(args.timing) if args.timing else Path(args.root) / 'art-pet' / 'anim_timing.json'
    if not timing.is_file():
        print(f'搵唔到 {timing}', file=sys.stderr)
        return 2
    return validate(
        timing,
        m1=Path(args.m1) if args.m1 else None,
        m2=Path(args.m2) if args.m2 else None,
        root=Path(args.root),
        sfx_readme=Path(args.sfx_readme) if args.sfx_readme else None,
        report_path=Path(args.write_report) if args.write_report else None,
        refresh_hooks=bool(args.refresh_hooks),
    )


if __name__ == '__main__':
    raise SystemExit(main())
