# Audiobookshelf Now Playing

A self-hosted "Now Listening" SVG card for Audiobookshelf, embeddable in a README like the Spotify Now Playing badge. A small FastAPI service (v0.2.0) with 11 layouts × 4 themes, a settings page with live preview, and optional Cloudflare Access gating of the settings endpoints. It is a public GitHub repository (StarlightDaemon/Audiobookshelf-Now-Playing).

## Run and test

Python 3.11+ (CI tests 3.11 and 3.12).

- Install: `pip install -r requirements-dev.txt`
- Test: `python -m pytest -v` (config in `pytest.ini`; collects `tests/test_*.py` and `tests/smoke.py`)
- Run locally: `uvicorn app.main:app --reload` (needs `ABS_HOST` and `ABS_TOKEN`; see `.env.example` and the README's environment table)

CI (`.github/workflows/ci.yml`) runs the test suite on every push and pull request.

## Layout

- `app/main.py`: FastAPI routes (`/card`, `/settings`, `/api/config`, `/health`, layout endpoints)
- `app/abs.py` (Audiobookshelf client), `app/cache.py`, `app/config.py` (persistent card config), `app/render.py` (SVG layouts), `app/themes.py`, `app/settings_ui.py`, `app/cf_access.py` (Cloudflare Access JWT check), `app/fujin_tokens.py` + `app/fujin-tokens-resolved.json` (Fujin design tokens for the settings page)
- `tests/`: unit, integration and smoke tests
- `deploy/`: Proxmox LXC creation and install scripts, systemd unit, update and MOTD scripts
- `mockups/`: local design mockups (gitignored, so only in the main checkout)
- `.raiden/state/`: the project records (see below)

## Key rules

- Main branch is `main`. Agent work goes on `<agent>/<task>` branches in their own worktrees.
- No `Co-Authored-By` or other agent attribution lines in commits; the `commit-msg` hook enforces this. Never bypass it.
- Ask the owner before pushing, tagging or releasing.
- Never commit secrets: real values belong in the server's environment file, never in the repo. Only `.env.example` (variable names, no values) is tracked.
- `/card` and `/health` stay public; `/settings` and `/api/config` write configuration and must stay behind the Cloudflare Access check when it's configured.
- Fujin only supplies CSS tokens for the settings page; it never touches the SVG cards (D-001, D-002).
- Local audit reports in `.audits/` are untracked and not yet gitignored: don't commit them. `audit-reports/` and `.raiden/state/AUDIT_LOG.md` are gitignored.
- Don't edit `.raiden/writ/` or `.raiden/instance/`. They're historical RAIDEN v2 text kept for the old tooling. Where they, `.raiden/README.md` or `.raiden/local/` disagree with this file, this file wins.

## Project records

This file and `.raiden/state/` are authoritative for this repo. Read in this order and stop when you have what you need:
1. `.raiden/state/CURRENT_STATE.md`: version, what exists, pending owner steps.
2. The `## Active` section at the top of `.raiden/state/OPEN_LOOPS.md`: open, deferred and held items (statuses: `open`, `deferred`, `held: <who>`, `no-action`, `accepted`, `closed`).
3. Only when needed: `DECISIONS.md` (IDs `D-0xx`), `WORK_LOG.md`, `GOALS.md` and `ABS_CARD_AUDIT_2026-06-15.md` (history and evidence).

Current picture: nothing open for agents. One item is held for the owner: OL-003, the Cloudflare Access application in the Cloudflare dashboard (the app-side check is done). Deployment to the owner's server is also an owner step (`CURRENT_STATE.md`, "Pending operator actions").

Update `CURRENT_STATE.md` and `OPEN_LOOPS.md` when you finish or pause work. Keep one home per fact and link evidence; don't paste it in. Never renumber or reuse a loop or decision ID. Medium+ audit findings become loops.

## Working in parallel

One agent per worktree. Before starting, read the Claims section of `../../HANDOFF.md` (the workspace folder two levels above the repo or worktree root, outside Git, so every worktree sees the same file) and `git worktree list`, then add your claim line there; mark it done when you finish. Separate tasks may run in parallel only when both claims are listed there and they don't touch the same files. The owner (or the agent they assign) merges branches and updates `.raiden/state/`. Releases, deployments, the hook and Git config are one-at-a-time work.

This repository is public: don't commit personal names, absolute local paths or details of the owner's private tooling.
