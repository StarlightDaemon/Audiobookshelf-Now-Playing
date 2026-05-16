# Current State

## Status

v0.1.0 shipped. All application code written and pushed to GitHub. Tagged v0.1.0.

## What exists

- `app/` — FastAPI application (main.py, abs.py, cache.py, render.py, themes.py)
- `deploy/ct/` — Proxmox host LXC creation script (community-scripts style)
- `deploy/install/` — container install script (community-scripts style)
- `deploy/audiobookshelf-now-playing.service` — systemd unit
- `requirements.txt`, `.env.example`, `README.md`, `LICENSE`, `VERSION`, `CHANGELOG.md`, `.gitignore`
- Remote: https://github.com/StarlightDaemon/Audiobookshelf-Now-Playing

## Pending operator actions

1. Provision LXC container on Proxmox (see deploy/install.sh)
2. Set environment variables in `/etc/audiobookshelf-now-playing.env` on the LXC
3. Add `card.starlightdaemon.dev` Cloudflare Tunnel hostname pointing to LXC:8000

## ABS API note

The session endpoint returns `currentTime` and `duration` from the last sync — not a live position. This is acceptable for v1.
