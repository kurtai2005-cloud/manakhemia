#!/usr/bin/env bash
# Root import map for frozen 675 bytes.
# Symlinks only. Does not copy or edit godot_hd2d_v6.
# The nested project.godot makes Godot ignore that folder, so res:// load()
# of those files cannot resolve. This stage lives outside that folder.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STAGE="$ROOT/hd2d_stage"
mkdir -p "$STAGE/pet/r4" "$STAGE/meshes"
shopt -s nullglob
linked=0
for src in "$ROOT/godot_hd2d_v6/art/pet/r4/"*.png; do
  name="$(basename "$src")"
  ln -sfn "../../../godot_hd2d_v6/art/pet/r4/$name" "$STAGE/pet/r4/$name"
  linked=$((linked + 1))
done
ln -sfn "../../godot_hd2d_v6/art/meshes/cottage.glb" "$STAGE/meshes/cottage.glb"
if [[ "$linked" -lt 1 ]]; then
  echo "stage_hd2d_assets: no r4 pngs found" >&2
  exit 1
fi
echo "stage_hd2d_assets: $linked r4 pngs + cottage.glb"
