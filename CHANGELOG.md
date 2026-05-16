# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
