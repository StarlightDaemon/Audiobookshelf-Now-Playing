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
- `app/cf_access.py` — Cloudflare Access JWT verifier; FastAPI dependency gating `/settings` + `/api/config` (validates `Cf-Access-Jwt-Assertion` against the team JWKS; fail-closed when `CF_ACCESS_TEAM_DOMAIN` + `CF_ACCESS_AUD` are set, no-op with a startup warning when unset)
- `app/settings_ui.py` — Settings page HTML builder with Fujin-token CSS vars and XSS-safe label interpolation
- `app/themes.py` — Theme definitions
- `app/fujin_tokens.py` — Fujin design token loader with fallback defaults
- `fujin-tokens-resolved.json` — Resolved design token file
- `tests/smoke.py` — SVG renderer smoke tests, all 11 layouts × 4 themes, with XML well-formedness checks
- `tests/test_abs.py` — Mocked `httpx` tests for the ABS client
- `tests/test_cache.py`, `tests/test_config.py` — Cache TTL and config round-trip tests
- `tests/test_main.py` — `TestClient` integration tests for `/card`, `/settings`, `/api/config`
- `tests/test_cf_access.py` — Cloudflare Access enforcement tests (real RSA-signed JWTs, stubbed JWKS): allow, deny missing/invalid/expired/wrong-aud/wrong-issuer, unset-env passthrough
- `pytest.ini`, `requirements-dev.txt` — Test config and dev/test dependency set
- `.github/workflows/ci.yml` — CI, Python 3.11/3.12 matrix
- `deploy/ct/audiobookshelf-now-playing.sh` — Proxmox host LXC creation script
- `deploy/install/audiobookshelf-now-playing-install.sh` — Container install script
- `deploy/motd.sh` — MOTD script for LXC container
- `deploy/update.sh` — In-place update script for LXC container
- `deploy/audiobookshelf-now-playing.service` — systemd unit
- `requirements.txt`, `.env.example`, `README.md`, `LICENSE`, `VERSION`, `CHANGELOG.md`, `.gitignore`
- `ABS_CARD_AUDIT_2026-06-15.md` — Pre-deployment audit report
- Remote: https://github.com/StarlightDaemon/Audiobookshelf-Now-Playing

## Deployment blockers resolved (as of v0.2.0)

- `CONFIG_PATH` default was `/etc/...` (blocked by `ProtectSystem=strict`); now `/opt/audiobookshelf-now-playing/config.json`
- f-string backslash SyntaxError on Python < 3.12 in `render.py`; fixed
- Stored XSS via `config.label` in settings JS template; fixed with `json.dumps()`

## Pending operator actions

1. Provision LXC container on Proxmox (see `deploy/ct/audiobookshelf-now-playing.sh`)
2. Set `ABS_HOST` and `ABS_TOKEN` in `/etc/audiobookshelf-now-playing.env` on the LXC
3. Configure Cloudflare Tunnel: `card.starlightdaemon.dev` → LXC:8000
4. Create the Cloudflare Access application over `/settings` + `/api/*`, then set
   `CF_ACCESS_TEAM_DOMAIN` + `CF_ACCESS_AUD` on the LXC (app-side enforcement is
   done; the dashboard policy is the remaining operator step — see OL-003)

## Post-deployment backlog

See OL-004.

## ABS API note

The session endpoint returns `currentTime` and `duration` from the last sync — not a live position. This is acceptable for v1.
