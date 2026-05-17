#!/usr/bin/env bash
IP=$(hostname -I 2>/dev/null | awk '{print $1}')
BL='\033[36m'; GN='\033[32m'; YW='\033[33m'; RD='\033[01;31m'; CL='\033[m'

printf "\n"
printf "${BL}  Audiobookshelf Now Playing${CL}\n"
printf "  ----------------------------------------\n"
printf "  Card URL : http://${IP}:8000/card\n"

if ! systemctl is-active --quiet audiobookshelf-now-playing; then
  if systemctl is-enabled --quiet audiobookshelf-now-playing 2>/dev/null; then
    printf "  ${YW}Service  : starting up...${CL}\n"
  else
    printf "  ${RD}Service  : not running  (systemctl start audiobookshelf-now-playing)${CL}\n"
  fi
  printf "\n  Commands : update  (pull latest code and restart)\n\n"
  return 0 2>/dev/null || exit 0
fi

STATUS=$(python3 -c "
import urllib.request, json, sys
try:
    r = urllib.request.urlopen('http://localhost:8000/status', timeout=2)
    print(r.read().decode())
except Exception:
    pass
" 2>/dev/null)

if [ -z "$STATUS" ]; then
  printf "  ${YW}Service  : starting up...${CL}\n"
else
  DEMO=$(printf '%s' "$STATUS" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('demo_mode',False))" 2>/dev/null)
  PLAYING=$(printf '%s' "$STATUS" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('playing',False))" 2>/dev/null)
  if [ "$DEMO" = "True" ]; then
    printf "  ${YW}Status   : Demo mode - configure ABS credentials${CL}\n"
  elif [ "$PLAYING" = "True" ]; then
    TITLE=$(printf '%s' "$STATUS" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('title',''))" 2>/dev/null)
    AUTHOR=$(printf '%s' "$STATUS" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('author',''))" 2>/dev/null)
    printf "  ${GN}Currently Reading:${CL}\n"
    printf "    Title  : %s\n" "$TITLE"
    printf "    Author : %s\n" "$AUTHOR"
  else
    printf "  ${YW}Status   : Live - no listening history yet${CL}\n"
  fi
fi

printf "\n  Commands : update  (pull latest code and restart)\n\n"
