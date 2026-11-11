#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""由 M1／M2 atlas JSON 再生成 art-pet/anim_timing.json。

時機（fps、幀數、loop、體型）以 atlas／clips.json 為準。
事件係跟 build 腳本嘅姿勢註解對出來，唔會加姿勢入面冇嘅動作。
每個事件必有 sfx_hook（須係 art-pet/sfx_hooks.json 快照入面嘅 sfx_* 名，對唔上就 null，唔自製；可用 --sfx-readme --refresh-hooks 更新快照）、
t_ms（由 clip 開頭計）、accent（land／peak／release）。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ACCENTS = ('land', 'peak', 'release')
SIZES_PX = {'S': 32, 'M': 48, 'L': 64}
SIZE_OF_PX = {32: 'S', 48: 'M', 64: 'L'}

# 疊本
STACK_BASE = 'art/m2-actions @ 230dab2f'
SOURCE_M1 = 'art/m1-icons-hunt @ 13a00477'
SOURCE_M2 = 'art/m2-actions @ 230dab2f'

# --------------------------------------------------------------------------
# 事件表：只記姿勢入面睇得出、需要配聲嘅時間點。
# frameIndex 0-based；t_ms／sfx_hook 由生成器填。
# sfx_hook 只寫遊音表入面已有、而且同姿勢對得上嘅名；否則 None。
# --------------------------------------------------------------------------
# (id, zh, frameIndex, accent, sfx_hook or None, note)
EVENTS: dict[str, list[tuple]] = {
    # ---- M1 寵物 ----
    'part_grass': [
        # i>=3 草左右分開；i=2 手先伸入草叢（gx 開始移）
        ('grass_rustle', '撥草', 2, 'peak', None,
         '伸手撥入右側草叢（gx 開始移），下一幀草分開。表入面冇撥草／葉沙專屬 hook。'),
    ],
    'pounce': [
        # 蹲→扭→彈→撲→落地；dy=(2,1,-8,-4,1,0)
        ('jump', '起跳', 2, 'release', None,
         '彈起（dy=-8）。表入面冇起跳專屬 hook。'),
        ('land', '落地', 4, 'land', 'sfx_pet_step_hop_a',
         '由空中（dy=-4）落到近地（dy=+1）；§7.9 蹦跳腳步「每次落地播一次」。'),
    ],
    'carry_fruit': [
        # walk_01–06；walk_01／walk_04 雙腳最低（y=62）係踏地拍
        ('footstep', '腳步', 0, 'land', None,
         'walk_01 雙腳踏地。表入面有 hop／drag／plod，冇普通行路步；唔借用。'),
        ('footstep', '腳步', 3, 'land', None,
         'walk_04 雙腳踏地（另一步）。同上，sfx_hook=null。'),
    ],
    'cheer': [
        # dy=(0,-3,-10,-8,-2,0)
        ('jump', '起跳', 1, 'release', None,
         '開始離地（dy=-3）。表入面冇起跳專屬 hook。'),
        ('cheer_peak', '歡呼峰', 2, 'peak', 'sfx_pet_happy',
         '跳到最高（dy=-10）。歡呼對應 §7.1 寵物開心（玩耍完成）。'),
        ('land', '落地', 4, 'land', 'sfx_pet_step_hop_a',
         '快落地（dy=-2）。§7.9 蹦跳腳步每次落地。'),
    ],
    # ---- M1 小動物 scared／tofruit；idle 只有呼吸 bob，冇聲 ----
    'dewlet_scared': [
        ('startle', '嚇驚', 0, 'peak', None,
         '進入受驚姿勢（圓眼、身壓低）。四幀幾乎同一姿勢；只喺循環開頭標一次。表入面冇受驚 hook。'),
    ],
    'loambun_scared': [
        ('startle', '嚇驚', 0, 'peak', None,
         '進入受驚姿勢。表入面冇受驚 hook。'),
    ],
    'mossback_scared': [
        ('startle', '嚇驚', 0, 'peak', None,
         '進入受驚姿勢。表入面冇受驚 hook。'),
    ],
    'seedfluff_scared': [
        ('startle', '嚇驚', 0, 'peak', None,
         '進入受驚姿勢（翼收）。表入面冇受驚 hook。'),
    ],
    'dewlet_tofruit': [
        ('shake', '發抖', 0, 'release', None,
         'tofruit 第 1–2 幀左右抖。表入面冇對應 hook。'),
        ('transform', '變成果', 3, 'peak', None,
         '第 4 幀（index 3）成果。表入面冇變身 hook。'),
        ('roll', '碌走', 4, 'land', None,
         '第 5 幀開始碌（果左右移）。表入面冇碌走 hook。'),
    ],
    'loambun_tofruit': [
        ('shake', '發抖', 0, 'release', None, 'tofruit 第 1–2 幀左右抖。表入面冇對應 hook。'),
        ('transform', '變成果', 3, 'peak', None, '第 4 幀成果。表入面冇變身 hook。'),
        ('roll', '碌走', 4, 'land', None, '第 5 幀開始碌。表入面冇碌走 hook。'),
    ],
    'mossback_tofruit': [
        ('shake', '發抖', 0, 'release', None, 'tofruit 第 1–2 幀左右抖。表入面冇對應 hook。'),
        ('transform', '變成果', 3, 'peak', None, '第 4 幀成果。表入面冇變身 hook。'),
        ('roll', '碌走', 4, 'land', None, '第 5 幀開始碌。表入面冇碌走 hook。'),
    ],
    'seedfluff_tofruit': [
        ('shake', '發抖', 0, 'release', None, 'tofruit 第 1–2 幀左右抖。表入面冇對應 hook。'),
        ('transform', '變成果', 3, 'peak', None, '第 4 幀成果。表入面冇變身 hook。'),
        ('roll', '碌走', 4, 'land', None, '第 5 幀開始碌。表入面冇碌走 hook。'),
    ],
    # ---- M2 寵物 ----
    'mail_post': [
        # walk_01, walk_03, walk_05, idle_02, catch_reach_03, idle_01
        ('footstep', '腳步', 0, 'land', None,
         '用 walk_01（踏地拍）行近。冇普通行路 hook。'),
        ('letter_drop', '投信入箱', 4, 'land', None,
         '伸手塞入（信封去到最前 44,22）；下一幀信封唔見。表入面冇投信／入箱 hook。'),
        ('clap', '拍手', 5, 'release', None,
         '拍完手、兩爪喺胸前。表入面冇拍手 hook。'),
    ],
    'idle_lively': [
        # hop=[0,-2,-9,-6,-1,0]
        ('hop_peak', '蹦跳峰', 2, 'peak', None,
         '跳到最高（hop=-9）。落地先有 step_hop。'),
        ('land', '落地', 4, 'land', 'sfx_pet_step_hop_a',
         '快落地（hop=-1）。§7.9 蹦跳腳步每次落地。'),
    ],
    # idle_quiet：坐低呼吸眨眼，冇需要配聲嘅動作
    'idle_diligent': [
        # 彎→伸手→執到→企起→睇一眼→放低；葉 y：54,48,40,36,38,54
        ('pickup', '執起葉子', 2, 'peak', None,
         '執到（葉離地提到手中）。表入面冇執／放物件 hook。'),
        ('place', '放低葉子', 5, 'land', None,
         '葉放返地下（y=54）。表入面冇執／放物件 hook。'),
    ],
    'idle_lazy': [
        # i==3 中段小小呵欠
        ('yawn', '呵欠', 3, 'peak', 'sfx_pet_yawn',
         '中段打呵欠（用 yawn_02 攤住）。§7.1 sfx_pet_yawn。'),
    ],
    'idle_clingy': [
        # lean 0.14 最大、爪向鏡頭 i>=1
        ('reach', '伸手', 2, 'peak', None,
         '前傾同伸爪最盡。表入面冇伸手／招手 hook。'),
    ],
    # idle_indep：望天搭額，冇明顯配聲動作
    'scratch_head': [
        # 爪提到頭側；i in (2,3,4) 撓。§7.9：「抓癢動畫開始」播一次（0.52s 包幾下）
        ('scratch', '抓頭', 2, 'peak', 'sfx_pet_scratch_a',
         '爪到頭側開始撓（第 3–5 幀繼續晃）。§7.9 抓癢動畫開始；a/b 可由遊音交替。'),
    ],
    'stretch': [
        # sy 峰 1.18、dy=-4 喺 i=2；雙手向上 i=1–4
        ('stretch', '伸懶腰', 2, 'peak', None,
         '踮腳拉到最高。雖然用咗 yawn 底圖，動作係伸懶腰唔係呵欠；唔借用 sfx_pet_yawn。'),
    ],
    # look_sky：仰頭望一阵，冇明顯配聲動作
    'proud_hips': [
        # i>=1 叉腰；puff 峰 1.14 喺 i=2
        ('hands_hips', '叉腰挺胸', 2, 'peak', None,
         '胸膛最挺、兩爪叉腰。表入面冇得意／叉腰 hook。'),
    ],
    'point_frame': [
        # i>=2 伸臂；i in (3,4) 指引短線
        ('point', '指相框', 3, 'peak', None,
         '臂伸到最前、有指引短線。表入面冇指向 hook。'),
    ],
    # ---- M2 訪客 ----
    'snail_postman_snail_deliver': [
        # bob 最低 -2 喺 i=3；信同時伸得最前
        ('offer', '鞠躬遞信', 3, 'peak', None,
         '鞠躬最低、信件伸得最前。表入面冇訪客遞信 hook。'),
    ],
    'mushroom_granny_granny_seed': [
        # nod 最大 i=2；種子 i=2–3 最前
        ('nod', '點頭', 2, 'land', None,
         '點頭最低。表入面冇訪客點頭 hook。'),
        ('offer', '奉上種子', 3, 'peak', None,
         '種子伸得最前。表入面冇訪客奉上 hook。'),
    ],
    'firefly_vendor_vendor_show': [
        # 瓶 jx 最前 i=2；另一邊 i=4
        ('rattle', '搖瓶', 2, 'peak', None,
         '螢火瓶搖到最前。表入面冇搖瓶／貨檔 hook。'),
        ('rattle', '搖瓶', 4, 'peak', None,
         '螢火瓶搖去另一邊。同上。'),
    ],
}


def frame_ms_list(n: int, fps: int) -> list[int]:
    """每幀整數 ms，累加等於 round(n*1000/fps)，唔會漂移。"""
    ts = [round(i * 1000 / fps) for i in range(n + 1)]
    return [ts[i + 1] - ts[i] for i in range(n)]


def duration_ms(n: int, fps: int) -> int:
    return round(n * 1000 / fps)


def parse_sfx_hooks(readme: Path) -> list[str]:
    """由 遊音 README 抽出全部 sfx_* 名（含 a/b 拆開）。"""
    text = readme.read_text(encoding='utf-8')
    names: set[str] = set()
    for m in re.finditer(r'`(sfx_[a-z0-9_]+)`', text):
        names.add(m.group(1))
    for m in re.finditer(r'`(sfx_[a-z0-9_]+)_a/b`', text):
        names.add(m.group(1) + '_a')
        names.add(m.group(1) + '_b')
    for m in re.finditer(
        r'`(sfx_[a-z0-9_]+_a)`\s*/\s*`((?:sfx_)?[a-z0-9_]*_b)`', text
    ):
        names.add(m.group(1))
        b = m.group(2)
        names.add(b if b.startswith('sfx_') else 'sfx_' + b)
    return sorted(names)


HOOKS_JSON_REL = 'art-pet/sfx_hooks.json'
HOOKS_SOURCE_LABEL = (
    '遊音 audio/README.md（最新，§3 + §7.1／7.2／7.5／7.9／7.11；'
    '非本 repo 內舊稿 audio/README.md）'
)


def hooks_json_path(root: Path) -> Path:
    return Path(root) / HOOKS_JSON_REL


def _hkt_date_of(path: Path) -> str:
    from datetime import datetime, timezone, timedelta
    hkt = timezone(timedelta(hours=8), name='HKT')
    return datetime.fromtimestamp(path.stat().st_mtime, hkt).strftime('%Y-%m-%d')


def _hkt_today() -> str:
    from datetime import datetime, timezone, timedelta
    hkt = timezone(timedelta(hours=8), name='HKT')
    return datetime.now(hkt).strftime('%Y-%m-%d')


def load_hooks_json(path: Path) -> list[str]:
    """由 art-pet/sfx_hooks.json 讀快照名單。"""
    J = json.loads(path.read_text(encoding='utf-8'))
    names = J.get('names')
    if not isinstance(names, list) or not names:
        raise SystemExit(f'{path}: names 空或者唔係陣列')
    if any(not isinstance(n, str) or not n.startswith('sfx_') for n in names):
        raise SystemExit(f'{path}: names 要全部係 sfx_* 字串')
    if J.get('count') not in (None, len(names)):
        raise SystemExit(f'{path}: count {J.get("count")} ≠ names {len(names)}')
    return list(names)


def write_hooks_snapshot(path: Path, names: list[str], readme: Path) -> dict:
    """由遊音最新 README 重寫 hook 快照。"""
    doc = {
        'format': 'sfx_hooks/1',
        'source': HOOKS_SOURCE_LABEL,
        'sourcePath': str(readme.resolve()),
        'date': _hkt_date_of(readme),
        'dateZone': 'Asia/Hong_Kong',
        'snapshotTaken': _hkt_today(),
        'count': len(names),
        'note': (
            '允許嘅 hook 名來自 遊音最新 README 全文已列嘅 sfx_*。'
            '本 repo 根目錄 audio/README.md 係舊稿（風野競走時期），冇 §7 hook 表，唔好用佢嚟驗證。'
        ),
        'names': names,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return doc


def resolve_hooks(root: Path, sfx_readme: Path | None, refresh: bool = False
                  ) -> tuple[list[str], dict]:
    """預設讀 art-pet/sfx_hooks.json；--sfx-readme 覆蓋；--refresh-hooks 連快照都重寫。

    唔會自動用本 repo 嘅 audio/README.md（舊表，冇 hook）。
    """
    snap = hooks_json_path(root)
    if sfx_readme:
        readme = Path(sfx_readme)
        if not readme.is_file():
            raise SystemExit(f'搵唔到 --sfx-readme {readme}')
        names = parse_sfx_hooks(readme)
        if not names:
            raise SystemExit(f'--sfx-readme {readme} 抽出 0 個 sfx_*（係咪用咗本 repo 舊 README？）')
        meta = {
            'via': 'sfx-readme',
            'source': str(readme.resolve()),
            'count': len(names),
        }
        if refresh:
            write_hooks_snapshot(snap, names, readme)
            meta['refreshed'] = str(snap)
            print(f'refreshed {snap}  hooks={len(names)}  from {readme}')
        return names, meta
    if refresh:
        raise SystemExit(
            '--refresh-hooks 要同時提供 --sfx-readme <遊音最新 README>；'
            '唔好用本 repo 舊嘅 audio/README.md'
        )
    if snap.is_file():
        names = load_hooks_json(snap)
        return names, {'via': 'sfx_hooks.json', 'source': str(snap), 'count': len(names)}
    raise SystemExit(
        f'搵唔到 {snap}。請用 --sfx-readme <遊音最新 README> --refresh-hooks 生成快照；'
        '唔好用本 repo 舊嘅 audio/README.md'
    )


def _first_existing(*paths: Path) -> Path | None:
    for p in paths:
        if p and p.exists():
            return p
    return None


def resolve_roots(args) -> tuple[Path, Path]:
    root = Path(args.root).resolve() if args.root else Path('.').resolve()
    m1 = Path(args.m1).resolve() if args.m1 else root
    m2 = Path(args.m2).resolve() if args.m2 else root
    # workspace 分開兩份 overlay 時自動兜
    if not (m1 / 'art-pet/sprites/tuanrong/motion/hunt/clips.json').is_file():
        alt = _first_existing(
            m1, root,
            Path('/workspace/m1-icons-hunt-src'),
        )
        if alt and (alt / 'art-pet/sprites/tuanrong/motion/hunt/clips.json').is_file():
            m1 = alt
    if not (m2 / 'art-pet/sprites/tuanrong/motion/m2/clips.json').is_file():
        alt = _first_existing(
            m2, root,
            Path('/workspace/m2-actions-src'),
        )
        if alt and (alt / 'art-pet/sprites/tuanrong/motion/m2/clips.json').is_file():
            m2 = alt
    return m1, m2


def rel(root: Path, p: Path) -> str:
    try:
        return str(p.resolve().relative_to(root.resolve()))
    except ValueError:
        # 跨 overlay：用 art-pet 起嘅尾段
        s = str(p)
        i = s.find('art-pet/')
        return s[i:] if i >= 0 else s


def load_json(p: Path) -> dict:
    return json.loads(p.read_text(encoding='utf-8'))


def make_events(clip_id: str, frame_ms: list[int], hooks: set[str]) -> list[dict]:
    out = []
    for ev in EVENTS.get(clip_id, []):
        eid, zh, fi, accent, hook, note = ev
        if not (0 <= fi < len(frame_ms)):
            raise SystemExit(f'{clip_id}: event {eid} frameIndex {fi} 超出幀數 {len(frame_ms)}')
        if accent not in ACCENTS:
            raise SystemExit(f'{clip_id}: event {eid} accent={accent!r} 唔係 land/peak/release')
        if hook is not None and hook not in hooks:
            # 防呆：寫錯就當 null，唔自製
            hook = None
        t = sum(frame_ms[:fi])
        out.append({
            'id': eid,
            'zh': zh,
            'frameIndex': fi,
            't_ms': t,
            'sfx_hook': hook,
            'accent': accent,
            'note': note,
        })
    return out


def collect_pet(mroot: Path, index_rel: str, source: str, kind: str, repo: Path) -> list[dict]:
    idx_path = mroot / index_rel
    folder = idx_path.parent
    CI = load_json(idx_path)
    clips = []
    sizes = list(CI['atlases'].keys())  # S, M, L
    for name, meta in CI['clips'].items():
        atlases = {}
        fps = loop = count = None
        for sz in sizes:
            fn = CI['atlases'][sz][name]
            J = load_json(folder / fn)
            atlases[sz] = rel(repo, folder / fn)
            if fps is None:
                fps, loop, count = J['fps'], J['loop'], J['frameCount']
            if (J['fps'], J['loop'], J['frameCount']) != (fps, loop, count):
                raise SystemExit(f'{name} {sz} atlas 時機同其他體型唔一致')
            if count != meta['frames'] or fps != meta['fps'] or loop != meta['loop']:
                raise SystemExit(f'{name} {sz} atlas 同 clips.json 唔一致')
        n = count
        fms = frame_ms_list(n, fps)
        rec = {
            'id': name,
            'zh': meta.get('zh', name),
            'source': source,
            'kind': kind,
            'form': 'radiant',
            'sizes': sizes,
            'sizePx': {s: SIZES_PX[s] for s in sizes},
            'frameCount': n,
            'fps': fps,
            'frameMs': fms,
            'durationMs': sum(fms),
            'loop': loop,
            'atlases': atlases,
        }
        if 'kind' in meta:
            rec['clipKind'] = meta['kind']
        if 'personality' in meta:
            rec['personality'] = meta['personality']
        rec['events'] = make_events(name, fms, HOOKS)
        clips.append(rec)
    return clips


def collect_critters(m1: Path, repo: Path) -> list[dict]:
    folder = m1 / 'art-pet/sprites/hunt/critters'
    out = []
    for p in sorted(folder.glob('*.json')):
        if p.name == 'critters.json':
            continue
        J = load_json(p)
        cid = J['id']
        zh = J.get('zh', cid)
        px = J['size']
        size_key = SIZE_OF_PX[px]
        for anim, am in J['animations'].items():
            n = len(am['frames'])
            fps = am['fps']
            loop = am['loop']
            fms = frame_ms_list(n, fps)
            clip_id = f'{cid}_{anim}'
            rec = {
                'id': clip_id,
                'zh': f'{zh}·{anim}',
                'source': 'm1',
                'kind': 'critter',
                'critter': cid,
                'animation': anim,
                'sizes': [size_key],
                'sizePx': {size_key: px},
                'frameCount': n,
                'fps': fps,
                'frameMs': fms,
                'durationMs': sum(fms),
                'loop': loop,
                'atlas': rel(repo, p),
            }
            rec['events'] = make_events(clip_id, fms, HOOKS)
            out.append(rec)
    return out


def collect_visitors(m2: Path, repo: Path) -> list[dict]:
    folder = m2 / 'art-pet/sprites/visitors/m2'
    V = load_json(folder / 'visitors.json')
    out = []
    for it in V['items']:
        atlas = folder / it['atlas']
        J = load_json(atlas)
        n = J['frameCount']
        fps = J['fps']
        loop = J['loop']
        fms = frame_ms_list(n, fps)
        clip_id = f"{it['id']}_{it['clip']}"
        px = it['frameSize']
        size_key = SIZE_OF_PX[px]
        rec = {
            'id': clip_id,
            'zh': f"{it['zh']}·{it['clip_zh']}",
            'source': 'm2',
            'kind': 'visitor',
            'visitor': it['id'],
            'clip': it['clip'],
            'sizes': [size_key],
            'sizePx': {size_key: px},
            'frameCount': n,
            'fps': fps,
            'frameMs': fms,
            'durationMs': sum(fms),
            'loop': loop,
            'atlas': rel(repo, atlas),
        }
        rec['events'] = make_events(clip_id, fms, HOOKS)
        out.append(rec)
    return out


HOOKS: set[str] = set()


def build(args) -> dict:
    global HOOKS
    m1, m2 = resolve_roots(args)
    hook_list, hook_meta = resolve_hooks(
        Path(args.root),
        Path(args.sfx_readme) if args.sfx_readme else None,
        refresh=bool(getattr(args, 'refresh_hooks', False)),
    )
    HOOKS = set(hook_list)

    hunt_idx = 'art-pet/sprites/tuanrong/motion/hunt/clips.json'
    m2_idx = 'art-pet/sprites/tuanrong/motion/m2/clips.json'
    if not (m1 / hunt_idx).is_file():
        raise SystemExit(f'搵唔到 M1 hunt clips.json（--m1 {m1}）')
    if not (m2 / m2_idx).is_file():
        raise SystemExit(f'搵唔到 M2 clips.json（--m2 {m2}）')

    # repo-relative 路徑用 m2（疊喺上面嗰層）；跨 tree 時 rel() 會退回 art-pet/...
    repo = m2
    clips: list[dict] = []
    clips += collect_pet(m1, hunt_idx, 'm1', 'pet', repo)
    clips += collect_critters(m1, repo)
    clips += collect_pet(m2, m2_idx, 'm2', 'pet', repo)
    clips += collect_visitors(m2, repo)

    n_ev = sum(len(c['events']) for c in clips)
    n_null = sum(1 for c in clips for e in c['events'] if e['sfx_hook'] is None)
    n_hooked = n_ev - n_null

    doc = {
        'format': 'anim_timing/1',
        'stack': STACK_BASE,
        'sources': {'m1': SOURCE_M1, 'm2': SOURCE_M2},
        'toleranceFrames': 1,
        'doc': (
            '遊音同遊測共用呢份檔。每個 clip：id、sizes、frameCount、frameMs、'
            'durationMs、loop、events。t_ms 由 clip 開頭計，等於 sum(frameMs[:frameIndex])'
            '（該幀開始）。遊測若同引擎播放相差超過 1 幀（toleranceFrames）就 fail。'
            '事件只來自姿勢／atlas，冇加姿勢入面冇嘅動作。'
            '每個 event 必有 sfx_hook、t_ms、accent（land／peak／release）。'
            'sfx_hook 必須係 art-pet/sfx_hooks.json（遊音最新 README 快照）已列出嘅 sfx_* 名；對唔上就 null，唔自製。'
        ),
        'sfxHooks': {
            'source': HOOKS_JSON_REL,
            'via': hook_meta.get('via'),
            'note': (
                '允許嘅 hook 名以 art-pet/sfx_hooks.json 為準（遊音最新 README 快照）。'
                '唔好讀本 repo 舊稿 audio/README.md。'
                '§7.11 本身係 HD-2D UI hook；寵物／訪客／小動物動作多數喺 §7.1 同 §7.9。'
            ),
            'count': len(hook_list),
            'names': hook_list,
        },
        'counts': {
            'clips': len(clips),
            'events': n_ev,
            'eventsWithHook': n_hooked,
            'eventsHookNull': n_null,
        },
        'clips': clips,
    }
    return doc


def main() -> int:
    ap = argparse.ArgumentParser(description='生成 art-pet/anim_timing.json')
    ap.add_argument('--root', default='.')
    ap.add_argument('--m1', default=None, help='M1  overlay 根（預設 = --root）')
    ap.add_argument('--m2', default=None, help='M2  overlay 根（預設 = --root）')
    ap.add_argument('--sfx-readme', default=None,
                    help='遊音最新 audio/README.md（覆蓋快照；配合 --refresh-hooks 重寫 art-pet/sfx_hooks.json）')
    ap.add_argument('--refresh-hooks', action='store_true',
                    help='用 --sfx-readme 抽出嘅名單重寫 art-pet/sfx_hooks.json（必須同時提供 --sfx-readme）')
    ap.add_argument('--out', default=None, help='輸出路徑（預設 <root>/art-pet/anim_timing.json）')
    ap.add_argument('--validate', action='store_true', help='寫完即跑 validator')
    args = ap.parse_args()
    doc = build(args)
    out = Path(args.out) if args.out else Path(args.root) / 'art-pet' / 'anim_timing.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'wrote {out}  clips={doc["counts"]["clips"]}  events={doc["counts"]["events"]}  '
          f'hooked={doc["counts"]["eventsWithHook"]}  null={doc["counts"]["eventsHookNull"]}')
    if args.validate:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import validate_anim_timing as V
        return V.validate(
            out,
            m1=Path(args.m1) if args.m1 else None,
            m2=Path(args.m2) if args.m2 else None,
            root=Path(args.root),
            sfx_readme=Path(args.sfx_readme) if args.sfx_readme else None,
        )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
