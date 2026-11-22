#!/usr/bin/env bash
# Portable entry point. The copy is done in Python so Windows Git checkouts
# do not need core.symlinks, Developer Mode, or junction privileges.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if command -v python3 >/dev/null 2>&1; then
  exec python3 "$ROOT/tools/stage_hd2d_assets.py"
fi
if command -v py >/dev/null 2>&1; then
  exec py -3 "$ROOT/tools/stage_hd2d_assets.py"
fi
echo "stage_hd2d_assets: python3 is required" >&2
exit 1
