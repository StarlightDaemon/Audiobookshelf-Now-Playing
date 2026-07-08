# Current State

## Status

v0.2.0. All deployment blockers resolved. Service is ready for LXC provisioning.
Operator infrastructure steps remain outstanding.

## What exists

- `app/main.py` — FastAPI application entry point; routes for `/card`, `/settings`, `/api/config`, `/health`, and all demo/variant endpoints
- `app/abs.py` — Audiobookshelf API client (session fetch, item metadata, cover art)
- `app/cache.py` — TTL-based in-memory cache
- `app/render.py` — SVG card renderer; 11 layouts across landscape and portrait families
- `app/config.py` — Persistent config read/write with validation; `CONFIG_PATH` default now `/opt/audiobookshelf-now-playing/config.json`
- `app/settings_ui.py` — Settings page HTML builder with Fujin-token CSS vars and XSS-safe label interpolation
- `app/themes.py` — Theme definitions
- `app/fujin_tokens.py` — Fujin design token loader with fallback defaults
- `fujin-tokens-resolved.json` — Resolved design token file
- `tests/smoke.py` — Basic smoke tests
- `deploy/ct/audiobookshelf-now-playing.sh` — Proxmox host LXC creation script
- `deploy/install/audiobookshelf-now-playing-install.sh` — Container install script
- `deploy/motd.sh` — MOTD script for LXC container
- `deploy/update.sh` — In-place update script for LXC container
- `deploy/audiobookshelf-now-playing.service` — systemd unit
- `requirements.txt`, `.env.example`, `README.md`, `LICENSE`, `VERSION`, `CHANGELOG.md`, `.gitignore`
- Remote: https://github.com/StarlightDaemon/Audiobookshelf-Now-Playing

## Deployment blockers resolved (as of v0.2.0)

- `CONFIG_PATH` default was `/etc/...` (blocked by `ProtectSystem=strict`); now `/opt/audiobookshelf-now-playing/config.json`
- f-string backslash SyntaxError on Python < 3.12 in `render.py`; fixed
- Stored XSS via `config.label` in settings JS template; fixed with `json.dumps()`

## Pending operator actions

1. Provision LXC container on Proxmox (see `deploy/ct/audiobookshelf-now-playing.sh`)
2. Set `ABS_HOST` and `ABS_TOKEN` in `/etc/audiobookshelf-now-playing.env` on the LXC
3. Configure Cloudflare Tunnel: `card.starlightdaemon.dev` → LXC:8000
4. Gate `/settings` and `/api/config` behind Cloudflare Access (operator action; not automated)

## Post-deployment backlog (not blocking)

- Session recency filter (OL-003)
- Dependency pinning (requirements.txt currently unpinned)
- Test expansion: 3 missing layout smoke tests, XML-parse assertions, mocked httpx for `abs.py`, TestClient integration, cache/config round-trip tests
- CI Python 3.11 matrix (verify fix is exercised in CI)
- doc/CHANGELOG drift cleanup
- Dead code removal audit

## ABS API note

The session endpoint returns `currentTime` and `duration` from the last sync — not a live position. This is acceptable for v1.

## Migration note (2026-06-07)

WSL→macOS migration remediation complete (Edict v0.6.1 audit):
- Hook permissions corrected (commit-msg, pre-commit: 666 → 755)
- pre-commit hook updated to use python3.12 explicitly (macOS system python3 = 3.9)
- Path references updated: /mnt/e/ → /Users/dante/Citadel/ (AGENTS.md, fujin-css-handoff.md)
- LOOP-0020 baseline discrepancy investigated — NOT present in this repo, hashes match
