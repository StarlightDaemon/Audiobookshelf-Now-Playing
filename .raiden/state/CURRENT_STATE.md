# Current State

## Status

Initial implementation complete. All application code written, not yet deployed.

## What exists

- `app/` — FastAPI application (main.py, abs.py, cache.py, render.py, themes.py)
- `deploy/` — systemd unit file and LXC install script
- `requirements.txt`, `.env.example`, `README.md`

## Pending operator actions

1. Provision LXC container on Proxmox (see deploy/install.sh)
2. Set environment variables in `/etc/audiobookshelf-now-playing.env` on the LXC
3. Add `card.starlightdaemon.dev` Cloudflare Tunnel hostname pointing to LXC:8000

## ABS API note

The session endpoint returns `currentTime` and `duration` from the last sync — not a live position. This is acceptable for v1.
