# Work Log

## 2026-05-17 — Fujin CSS alignment: settings page theming

- Reviewed `/settings` page structure in `app/settings_ui.py`
- Evaluated two integration approaches: CSS alignment vs. full React SPA
- Decision: CSS alignment only (D-001). Rationale and options in DECISIONS.md.
- Replaced all 8 `:root` CSS custom property values with Fujin dark Slate palette
  equivalents from `createFujinTheme.ts` / `tokens.json`
- Accent changed from GitHub blue (#4d8ef0) to Fujin violet[6] (#7950f2)
- Removed `--radius: 8px`; all 4 usage sites set to literal `0`
- `.dot` — `border-radius: 50%` removed; sharp square
- `.preview-card` — `border-radius: 10px` removed; box-shadow → Fujin shadow-lg
- Font stacks updated: Verdana-first UI, JetBrains Mono-first mono
- Transition durations aligned to Fujin base (150ms)
- Card boundary decision recorded (D-002): render.py and themes.py never touched by Fujin
- Session handoff written to `.raiden/local/prompts/fujin-css-handoff.md`

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
