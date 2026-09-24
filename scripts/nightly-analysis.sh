#!/usr/bin/env bash
# Sync new games, then analyze a batch of each time class. Scheduled by scripts/schedule-nightly.sh.
# One-off runs: SINCE=2026-01-01 THREADS=10 HASH_MB=2048 scripts/nightly-analysis.sh
set -euo pipefail
cd "$(dirname "$0")/.."

# launchd starts jobs with a minimal PATH; Docker Desktop keeps its CLI helpers here.
export PATH="/Applications/Docker.app/Contents/Resources/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"

GAMES_PER_CLASS="${GAMES_PER_CLASS:-100}"
DEPTH="${DEPTH:-12}"
THREADS="${THREADS:-2}"
HASH_MB="${HASH_MB:-256}"
TIME_CLASSES="${TIME_CLASSES:-rapid blitz}"
SINCE="${SINCE:-}"

# A second run (e.g. the nightly job during a long one-off run) would fight for CPU and the database.
LOCK_DIR="data/.analysis.lock"
if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  holder="$(cat "$LOCK_DIR/pid" 2>/dev/null || true)"
  if [ -n "$holder" ] && kill -0 "$holder" 2>/dev/null; then
    echo "=== $(date '+%Y-%m-%d %H:%M:%S') skipped: analysis already running (pid $holder) ==="
    exit 0
  fi
  rm -rf "$LOCK_DIR" && mkdir "$LOCK_DIR"
fi
echo $$ > "$LOCK_DIR/pid"
trap 'rm -rf "$LOCK_DIR"' EXIT

echo "=== $(date '+%Y-%m-%d %H:%M:%S') analysis (threads=$THREADS depth=$DEPTH) ==="

if ! docker info >/dev/null 2>&1; then
  open -ga Docker
  for _ in $(seq 60); do docker info >/dev/null 2>&1 && break; sleep 5; done
fi

coach() {
  docker compose run --rm -T -e ENGINE__THREADS="$THREADS" -e ENGINE__HASH_MB="$HASH_MB" coach "$@"
}

docker compose build -q coach
coach sync
if [ -n "$SINCE" ]; then
  coach analyze --since "$SINCE" --last 100000 --depth "$DEPTH"
else
  for time_class in $TIME_CLASSES; do
    coach analyze --time-class "$time_class" --last "$GAMES_PER_CLASS" --depth "$DEPTH"
  done
fi
echo "=== $(date '+%Y-%m-%d %H:%M:%S') done ==="
