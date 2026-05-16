#!/usr/bin/env bash
set -euo pipefail
APP_DIR=/opt/audiobookshelf-now-playing
GN='\033[32m'; YW='\033[33m'; CL='\033[m'
git config --global --add safe.directory "$APP_DIR"
BEFORE=$(git -C "$APP_DIR" rev-parse HEAD)
git -C "$APP_DIR" fetch --depth 1 origin -q
git -C "$APP_DIR" reset --hard origin/HEAD -q
AFTER=$(git -C "$APP_DIR" rev-parse HEAD)
if [[ "$BEFORE" == "$AFTER" ]]; then
  printf "${YW}  [ok] Already up to date${CL}\n"
else
  printf "${GN}  [ok] Updated to $(git -C "$APP_DIR" log -1 --format='%h %s')${CL}\n"
  "$APP_DIR/venv/bin/pip" install -q -r "$APP_DIR/requirements.txt"
  systemctl restart audiobookshelf-now-playing
  printf "${GN}  [ok] Service restarted${CL}\n"
fi
