#!/usr/bin/env bash
# Install or remove the macOS launchd job that runs nightly-analysis.sh every day.
set -euo pipefail

LABEL="com.chesscoach.nightly-analysis"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
HOUR="${HOUR:-20}"

uninstall() {
  launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
  rm -f "$PLIST"
}

install() {
  uninstall
  mkdir -p "$REPO/data/logs" "$(dirname "$PLIST")"
  cat >"$PLIST" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/caffeinate</string><string>-i</string>
    <string>/bin/bash</string><string>$REPO/scripts/nightly-analysis.sh</string>
  </array>
  <key>StartCalendarInterval</key>
  <dict><key>Hour</key><integer>$HOUR</integer><key>Minute</key><integer>0</integer></dict>
  <key>StandardOutPath</key><string>$REPO/data/logs/nightly.log</string>
  <key>StandardErrorPath</key><string>$REPO/data/logs/nightly.log</string>
</dict>
</plist>
PLIST
  launchctl bootstrap "gui/$(id -u)" "$PLIST"
  echo "Scheduled daily at $HOUR:00 -> $PLIST (log: data/logs/nightly.log)"
}

case "${1:-install}" in
  install) install ;;
  uninstall) uninstall && echo "Removed $LABEL" ;;
  *) echo "usage: $0 [install|uninstall]" >&2; exit 2 ;;
esac
