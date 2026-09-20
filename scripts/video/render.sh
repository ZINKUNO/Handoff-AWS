#!/usr/bin/env bash
# Render the film. Uses Playwright's Chromium so nothing else is downloaded.
#   scripts/video/render.sh [out.mp4] [HandoffDemo|HandoffDemo3Min]
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="${1:-$ROOT/video/out/handoff-aws-demo.mp4}"
COMP="${2:-HandoffDemo}"
case "$OUT" in /*) ;; *) OUT="$PWD/$OUT" ;; esac   # absolute, since we cd below
CHROME=$(ls -d "$HOME"/.cache/ms-playwright/chromium-*/chrome-linux/chrome 2>/dev/null | tail -1)
cd "$ROOT/video"
mkdir -p "$(dirname "$OUT")"
npx remotion render src/index.ts "$COMP" "$OUT" --gl=angle --timeout="${FRAME_TIMEOUT:-300000}" --concurrency="${CONCURRENCY:-6}" ${CHROME:+--browser-executable="$CHROME"} --log=warn
echo "rendered $OUT"
