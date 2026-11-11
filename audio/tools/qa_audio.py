"""一條指令檢查 SFX：LUFS20、peak、最大樣本跳（click）、>6 kHz 能量、長度、onset／accent 誤差、PASS/FAIL 表。

用法（喺 audio/）：
  PYTHONPATH=tools /workspace/audio-venv/bin/python tools/qa_audio.py
  PYTHONPATH=tools python tools/qa_audio.py --map anim_sfx_map.json [files...]
  PYTHONPATH=tools python tools/qa_audio.py sfx/sfx_pet_jump_a.ogg

預設讀 anim_sfx_map.json 入面用到嘅全部檔（現有＋新）。
PASS 門檻（可用旗標改）：
  - 44.1 kHz 單聲道 ogg
  - sample peak ≤ -1.0 dBFS
  - LUFS20 同目標差 ≤ 0.3 LU（map 冇目標就用檔名規則：plod -24，step／細 foley -22，reunion -18，其他一般 -20；現有檔若冇寫目標則只檢查硬上限）
  - 相鄰樣本最大差 ≤ 0.30
  - >6 kHz 能量 ≤ 2.0 %
  - |accent_ms − expected| ≤ 30 ms（expected＝map 嘅 accent_offset_ms，冇就 0；現有 yawn 用 603）
"""
from __future__ import annotations
import argparse, json, os, sys
from pathlib import Path

import numpy as np
import soundfile as sf

from measure import ebur, probe

ROOT = Path(__file__).resolve().parents[1]
SR_EXPECT = 44100
PEAK_MAX = -1.0
JUMP_MAX = 0.30
HI6_MAX = 2.0
ACCENT_TOL_MS = 30.0
LUFS_TOL = 0.30

# 檔名 → 預設 LUFS20 目標（map 可以覆蓋；現有生命感／寵物聲有自己嘅目標）
DEFAULT_TGT = {}


def guess_tgt(stem: str):
    if stem in DEFAULT_TGT:
        return DEFAULT_TGT[stem]
    if stem.startswith("sfx_ui8_"):
        return None
    if "plod" in stem:
        return -24.0
    if "reunion_happy" in stem:
        return -18.0
    if any(s in stem for s in (
        "step_", "scratch", "bug_pat", "grass_rustle", "jump", "letter_drop",
        "clap", "pickup", "place", "reach", "point", "shake", "roll",
        "offer_", "nod", "rattle",
    )):
        return -22.0
    if stem.startswith("sfx_pet_") or stem.startswith("sfx_critter_") or stem.startswith("sfx_visitor_"):
        # sneeze / huh / purr / startle / transform / stretch / proud / happy(-18? happy is -18 LUFS4s but LUFS20 may differ)
        if stem in ("sfx_pet_happy",) or "happy" in stem:
            return -18.0
        if stem in ("sfx_pet_yawn",):
            return None  # 7.1 用 LUFS4s -18，唔用 LUFS20 做硬目標
        if any(s in stem for s in ("touch", "grumpy")):
            return None
        return -20.0
    return None


def lufs20(path: Path) -> float:
    x, sr = sf.read(str(path))
    tmp = "/tmp/_qa_l20.wav"
    sf.write(tmp, np.tile(x, 20), sr, subtype="FLOAT")
    return ebur(tmp)[0]


def rms_env(x, sr, win_ms=8.0):
    win = max(1, int(win_ms / 1000 * sr))
    return np.sqrt(np.convolve(x ** 2, np.ones(win) / win, "same"))


def analyse(path: Path, expected_accent_ms=0.0, tgt=None, require_tgt=True, measure='peak'):
    codec, sr, ch, dur = probe(str(path))
    x, sr2 = sf.read(str(path))
    if x.ndim > 1:
        x = np.mean(x, axis=1)
    peak = float(np.max(np.abs(x)) + 1e-12)
    peak_db = 20 * np.log10(peak)
    jump = float(np.max(np.abs(np.diff(x)))) if len(x) > 1 else 0.0
    n = len(x)
    spec = np.fft.rfft(x * np.hanning(n))
    freq = np.fft.rfftfreq(n, 1 / sr2)
    pwr = np.abs(spec) ** 2
    psum = float(np.sum(pwr) + 1e-20)
    hi6 = 100.0 * float(np.sum(pwr[freq >= 6000])) / psum
    body = 100.0 * float(np.sum(pwr[(freq >= 150) & (freq <= 1000)])) / psum
    env = rms_env(x, sr2)
    em = float(env.max() + 1e-20)
    onset_ms = 1000.0 * (np.argmax(env >= 0.20 * em) / sr2)
    peak_ms = 1000.0 * (int(np.argmax(env)) / sr2)
    accent_ms = onset_ms if measure == "onset" else peak_ms
    err = accent_ms - expected_accent_ms
    try:
        L = lufs20(path)
    except Exception as ex:
        L = float("nan")
        lufs_err = str(ex)
    else:
        lufs_err = None
    fails = []
    if codec not in ("vorbis", "ogg"):
        fails.append(f"codec={codec}")
    if sr != SR_EXPECT:
        fails.append(f"sr={sr}")
    if ch != 1:
        fails.append(f"ch={ch}")
    if peak_db > PEAK_MAX + 1e-6:
        fails.append(f"peak {peak_db:.2f} > {PEAK_MAX}")
    if jump > JUMP_MAX:
        fails.append(f"jump {jump:.3f} > {JUMP_MAX}")
    if hi6 > HI6_MAX:
        fails.append(f">6kHz {hi6:.2f}% > {HI6_MAX}")
    if abs(err) > ACCENT_TOL_MS:
        fails.append(f"accent err {err:+.1f} ms")
    if tgt is not None and require_tgt and not np.isnan(L):
        if abs(L - tgt) > LUFS_TOL:
            # peak-limited below target is still a fail for new files; report it
            fails.append(f"LUFS20 {L:.1f} vs {tgt:.1f}")
    status = "FAIL" if fails else "PASS"
    return dict(
        file=path.name, path=str(path), codec=codec, sr=sr, ch=ch,
        dur=round(float(dur), 3), LUFS20=None if np.isnan(L) else round(float(L), 1),
        peak=round(peak_db, 2), jump=round(jump, 3), hi6=round(hi6, 3),
        body=round(body, 1), onset_ms=round(onset_ms, 1), accent_ms=round(accent_ms, 1),
        expected_accent_ms=round(expected_accent_ms, 1), err_ms=round(err, 1),
        tgt=tgt, status=status, fails=fails, lufs_err=lufs_err,
    )


def collect_from_map(mp, root: Path):
    """file -> (expected_accent_ms, tgt, require_tgt, measure). measure=peak|onset."""
    info = {}
    for e in mp.get("entries", []):
        exp = float(e.get("accent_offset_ms", 0) or 0)
        measure = e.get("accent_measure") or "peak"
        for fn in e.get("files") or []:
            p = (Path(fn) if fn.startswith("/") else root / "sfx" / Path(fn).name)
            stem = Path(fn).stem
            tgt = guess_tgt(stem)
            require = e.get("source") != "existing" or stem.startswith(
                ("sfx_pet_step_", "sfx_pet_scratch", "sfx_pet_bug", "sfx_pet_sneeze",
                 "sfx_pet_turn", "sfx_pet_nuzzle", "sfx_pet_reunion")
            )
            if e.get("source") == "existing" and stem in ("sfx_pet_happy", "sfx_pet_yawn"):
                require = False
            key = str(p.resolve()) if p.exists() else str(p)
            cur = info.get(key)
            if cur is None or (exp and not cur[0]):
                info[key] = (exp, tgt, require, measure)
    return info


def fmt_row(r):
    tgt = "—" if r["tgt"] is None else f"{r['tgt']:.1f}"
    L = "—" if r["LUFS20"] is None else f"{r['LUFS20']:.1f}"
    why = "" if not r["fails"] else "  (" + "; ".join(r["fails"]) + ")"
    return (
        f"{r['status']:4s} {r['file']:32s} {r['dur']:6.3f}s  LUFS20 {L:>5s} (tgt {tgt:>5s})  "
        f"peak {r['peak']:6.2f}  jump {r['jump']:.3f}  >6k {r['hi6']:5.2f}%  "
        f"body {r['body']:5.1f}%  onset {r['onset_ms']:6.1f}  accent {r['accent_ms']:6.1f}  "
        f"err {r['err_ms']:+6.1f}{why}"
    )


def main():
    ap = argparse.ArgumentParser(description="SFX numeric QA (LUFS20 / peak / clicks / >6 kHz / accent)")
    ap.add_argument("files", nargs="*")
    ap.add_argument("--map", default=str(ROOT / "anim_sfx_map.json"))
    ap.add_argument("--no-map", action="store_true")
    args = ap.parse_args()
    root = ROOT
    expected = {}
    if not args.no_map and Path(args.map).is_file():
        mp = json.loads(Path(args.map).read_text(encoding="utf-8"))
        expected = collect_from_map(mp, root)
    paths = []
    if args.files:
        for f in args.files:
            p = Path(f)
            if p.is_dir():
                paths.extend(sorted(p.glob("*.ogg")))
            else:
                paths.append(p)
    elif expected:
        paths = [Path(p) for p in sorted(expected)]
    else:
        paths = sorted((root / "sfx").glob("sfx_pet_*.ogg"))
    rows = []
    for p in paths:
        default = (0.0, guess_tgt(p.stem), True, "peak")
        rec = expected.get(str(p.resolve())) or expected.get(str(p))
        if rec is None:
            for k, v in expected.items():
                if Path(k).name == p.name:
                    rec = v
                    break
        exp, tgt, req, meas = rec or default
        rows.append(analyse(p, expected_accent_ms=exp, tgt=tgt, require_tgt=req, measure=meas))
    print(f"{'STAT':4s} {'file':32s} {'dur':>7s}  {'LUFS20':^18s}  {'peak':>8s}  {'jump':>5s}  {'>6k':>8s}  {'body':>6s}  {'onset':>6s}  {'accent':>6s}  err")
    for r in rows:
        print(fmt_row(r))
    n_pass = sum(1 for r in rows if r["status"] == "PASS")
    n_fail = sum(1 for r in rows if r["status"] == "FAIL")
    print(f"\n{n_pass} PASS / {n_fail} FAIL / {len(rows)} total")
    # JSON summary on stdout after the table? also write sidecar
    out = {
        "pass": n_pass, "fail": n_fail, "total": len(rows),
        "thresholds": dict(peak_dBFS=PEAK_MAX, jump=JUMP_MAX, hi6_pct=HI6_MAX,
                           accent_tol_ms=ACCENT_TOL_MS, lufs_tol=LUFS_TOL),
        "rows": rows,
    }
    Path("/tmp/qa_audio_last.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    sys.exit(1 if n_fail else 0)


if __name__ == "__main__":
    main()
