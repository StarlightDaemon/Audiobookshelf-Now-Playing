# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added

- `SESSION_MAX_AGE` env var (default 3600s): sessions older than this are
  treated as stale and no longer shown as "currently reading"
- Test suite: smoke tests now cover all 11 layouts (was 8) with XML
  well-formedness checks; mocked `httpx` tests for `abs.py`; `TestClient`
  integration tests for `/card`, `/settings`, `/api/config`; cache and
  config round-trip tests — 88 tests total
- CI: GitHub Actions workflow running the full suite on a Python
  3.11 / 3.12 matrix

### Changed

- `requirements.txt` pinned to exact versions (`fastapi==0.139.0`,
  `uvicorn[standard]==0.51.0`, `httpx==0.28.1`), verified against the full
  test suite on both supported Python versions
- README updated to reflect v0.2.0 (multi-layout, settings UI, current env
  vars and endpoints — previously still described the v0.1.0 feature set)

### Removed

- Dead code in `render.py`: a stale commented-out `_progress_bar()` block
  describing a design superseded by the live implementation, an unused
  local variable, and an unused test helper in `tests/smoke.py`

---

## [0.2.0] — 2026-06-16

### Added

- Settings UI (`/settings`) with live card preview, layout/theme/corners/label selectors, and save-to-disk via `/api/config`
- Multi-layout support: 11 card layouts across landscape and portrait families
- Fujin token integration — settings UI theming driven by design token JSON
- `app/config.py` — persistent config read/write with validation
- `app/settings_ui.py` — HTML settings page builder with Fujin-token CSS vars
- `app/fujin_tokens.py` — Fujin token loader with fallback defaults
- `fujin-tokens-resolved.json` — resolved design token file
- `tests/smoke.py` — basic smoke tests
- `deploy/motd.sh` — MOTD script for LXC container
- `deploy/update.sh` — in-place update script for LXC container

### Fixed

- Python 3.11 compatibility: removed backslash inside f-string expression in `render.py` (SyntaxError on Python < 3.12); replaced inline conditional with hoisted `_muted_attrs` variable
- Deployment: `CONFIG_PATH` default moved from `/etc/audiobookshelf-now-playing-config.json` (read-only under systemd `ProtectSystem`) to `/opt/audiobookshelf-now-playing/config.json` (covered by `ReadWritePaths`)
- Security: `config.label` is now serialized with `json.dumps()` before interpolation into the settings JS template, preventing stored XSS via a crafted label value

---

## [0.1.0] — 2026-05-15

### Added

- FastAPI service with `/card` and `/health` endpoints
- Audiobookshelf API client — session fetch, item metadata, cover art (base64 inline)
- TTL-based in-memory cache (default 60 s) to protect ABS instance
- SVG card renderer — 495×128 px, Fira Code font stack, rounded corners, inline cover art
- Dark theme (default) and light theme, selectable via `?theme=` query param
- Progress bar showing current playback position
- Series metadata displayed when present (name · Book N)
- Fallback states: nothing playing, ABS unreachable, cover art unavailable
- `deploy/ct/audiobookshelf-now-playing.sh` — Proxmox host script; creates and configures LXC container automatically, styled after [community-scripts](https://community-scripts.org/) conventions
- `deploy/install/audiobookshelf-now-playing-install.sh` — container install script; installs Python, app, systemd service; follows community-scripts `msg_info`/`msg_ok`/`$STD` conventions
- Hardened systemd unit (`NoNewPrivileges`, `ProtectSystem`, dedicated `abs-card` service user)
- Environment-variable configuration (`ABS_HOST`, `ABS_TOKEN`, `CACHE_TTL`, `HOST`, `PORT`)
- `.env.example` template
- MIT license

[0.1.0]: https://github.com/StarlightDaemon/audiobookshelf-now-playing/releases/tag/v0.1.0
