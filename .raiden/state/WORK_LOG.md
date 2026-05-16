# Work Log

## 2026-05-16 — Deploy scripts refactor + v0.1.0 push

- deploy/install.sh replaced with community-scripts two-file split (ct/ + install/)
- ct/ script sources misc/core.func for styling; creates LXC via pct on Proxmox host
- install/ script follows community-scripts msg_info/msg_ok/$STD conventions
- Added .gitignore, LICENSE (MIT), VERSION (0.1.0), CHANGELOG.md
- README updated with version/license badges and versioning section
- Pushed to https://github.com/StarlightDaemon/Audiobookshelf-Now-Playing
- Tagged v0.1.0

## 2026-05-15 — Initial implementation

- RAIDEN orientation completed; all state files populated
- Full application scaffolded: FastAPI service, ABS client, TTL cache, SVG renderer, theme engine
- Fallback states implemented: nothing playing, ABS unreachable, cover unavailable
- Dark and light themes implemented
- systemd unit and LXC install script written
- README with setup guide and embed snippet written
- Deployment blocked on operator: LXC provisioning and Cloudflare Tunnel config
