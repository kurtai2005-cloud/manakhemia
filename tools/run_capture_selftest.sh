#!/usr/bin/env bash
# Linux selftest on the current DISPLAY. Not a GPU or phone pass.
# --headless has no viewport image, so this script does not pass --headless.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
GODOT="${GODOT:-/tmp/godot-bin/Godot_v4.7.2-stable_linux.x86_64}"
OUT="${CAPTURE_SELFTEST_OUT:-/tmp/vc27_capture_selftest_$$}"
CFG="$ROOT/override.cfg"
if [[ -e "$CFG" ]]; then
  echo "FAIL override.cfg already exists" >&2
  exit 2
fi
rm -rf "$HOME/.local/share/vc27_errand_capture" "$HOME/.local/share/vc27_progress_capture"
mkdir -p "$OUT/errand" "$OUT/progress" "$OUT/logs"
cleanup() { rm -f "$CFG"; }
trap cleanup EXIT
run_stage() {
  local name="$1" profile="$2" stage="$3" dest="$4"
  cat > "$CFG" << EOF
[application]
config/use_custom_user_dir=true
config/custom_user_dir_name="$profile"
EOF
  set +e
  CAPTURE_STAGE="$stage" CAPTURE_OUT="$dest" CAPTURE_PROJECT="$ROOT" CAPTURE_MAX_MS=220000 \
    "$GODOT" --rendering-method mobile --path "$ROOT" \
    --script res://tests/hd2d_capture_harness.gd \
    > "$OUT/logs/${stage}_stdout.txt" 2> "$OUT/logs/${stage}_stderr.txt"
  local ec=$?
  echo "$ec" > "$OUT/logs/${stage}.exit"
  echo "$stage EXIT:$ec"
  return "$ec"
}
if [[ -z "${DISPLAY:-}" ]]; then
  echo "FAIL no DISPLAY. Headless mode saved no viewport image." >&2
  exit 2
fi
echo "selftest out=$OUT"
echo "DISPLAY=$DISPLAY. Not an RTX or phone pass."
set +e
run_stage errand vc27_errand_capture errand_out "$OUT/errand"
ec1=$?
run_stage errand vc27_errand_capture errand_resume "$OUT/errand"
ec2=$?
run_stage progress vc27_progress_capture progress "$OUT/progress"
ec3=$?
set -e
python3 - "$OUT" << 'PY'
import json, pathlib, sys
out = pathlib.Path(sys.argv[1])
rows = []
for path in sorted(out.rglob("trace_*.jsonl")):
    for line in path.read_text().splitlines():
        if line.strip():
            rows.append(json.loads(line))
exits = {}
for path in sorted((out / "logs").glob("*.exit")):
    exits[path.stem] = int(path.read_text().strip() or "1")
frames = []
for row in rows:
    png = row.get("png") or ""
    stage = str(row.get("stage") or "")
    folder = {"errand_out": "errand", "errand_resume": "errand", "progress": "progress", "layers": "layers"}.get(stage, stage)
    file_path = None
    size = 0
    if png:
        candidate = out / folder / png
        if candidate.is_file():
            file_path = str(candidate.relative_to(out))
            size = candidate.stat().st_size
    frames.append({
        "stage": row.get("stage"),
        "shot": row.get("shot"),
        "driver": row.get("driver"),
        "png": png,
        "png_path": file_path,
        "png_bytes": size,
        "phase": row.get("phase"),
        "fruit_count": row.get("fruit_count"),
        "paid_through": row.get("paid_through"),
        "coat_facing": row.get("coat_facing"),
        "care_id": row.get("care_id"),
        "wall_clock": row.get("wall_clock"),
        "wall_unix_ms": row.get("wall_unix_ms"),
        "growth_sec": row.get("growth_sec"),
        "in_interior": row.get("in_interior"),
        "note": row.get("note"),
    })
manifest = {
    "display_note": "Linux DISPLAY selftest. llvmpipe/OpenGL fallback is not a GPU or phone pass.",
    "exits": exits,
    "frames": frames,
}
(out / "manifest.json").write_text(json.dumps(manifest, indent=2))
print("manifest frames", len(frames), "pngs", sum(1 for f in frames if f["png_bytes"] > 0))
PY
echo "SELFTEST_DONE $OUT exits=$ec1,$ec2,$ec3"
exit $(( ec1 || ec2 || ec3 ))
