#!/usr/bin/env bash
# Sync new games, then analyze a batch of each time class. Scheduled by scripts/schedule-nightly.sh.
set -euo pipefail
cd "$(dirname "$0")/.."

# launchd starts jobs with a minimal PATH; Docker Desktop keeps its CLI helpers here.
export PATH="/Applications/Docker.app/Contents/Resources/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"

GAMES_PER_CLASS="${GAMES_PER_CLASS:-100}"
DEPTH="${DEPTH:-12}"
THREADS="${THREADS:-6}"
TIME_CLASSES="${TIME_CLASSES:-rapid blitz}"

echo "=== $(date '+%Y-%m-%d %H:%M:%S') nightly analysis ==="

if ! docker info >/dev/null 2>&1; then
  open -ga Docker
  for _ in $(seq 60); do docker info >/dev/null 2>&1 && break; sleep 5; done
fi

coach() { docker compose run --rm -T -e ENGINE__THREADS="$THREADS" coach "$@"; }

docker compose build -q coach
coach sync
for time_class in $TIME_CLASSES; do
  coach analyze --time-class "$time_class" --last "$GAMES_PER_CLASS" --depth "$DEPTH"
done
echo "=== $(date '+%Y-%m-%d %H:%M:%S') done ==="
