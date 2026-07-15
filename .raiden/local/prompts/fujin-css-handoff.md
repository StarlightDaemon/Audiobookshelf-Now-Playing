You are the ABS Now Playing Instance agent, operating inside E:\Citadel/audiobookshelf-now-playing.

Read first:
- AGENTS.md
- .raiden/state/CURRENT_STATE.md
- .raiden/state/DECISIONS.md
- .raiden/state/OPEN_LOOPS.md

---

## What this project is

A FastAPI Python service that serves SVG "now playing" cards for Audiobookshelf. The primary
output is a single image URL embeddable in GitHub READMEs. The web page is the `/settings`
route — a single server-rendered HTML page built in `app/settings_ui.py` as a Python f-string.
There is no JS build toolchain, no npm, no React. It is `pip install` and done.

Core files:
- `app/settings_ui.py`  — the only web page; HTML + embedded CSS returned from `/settings`
- `app/render.py`       — all SVG card renderers (landscape, portrait A–G)
- `app/themes.py`       — card Theme dataclass and the 6 card theme definitions
- `app/main.py`         — FastAPI routes
- `app/abs.py`          — Audiobookshelf API client
- `app/cache.py`        — TTL cache

---

## Fujin relationship

Fujin (`E:\Citadel/Fujin`) is a Mantine v7 React component library. This project consumes its
**visual language only** — not its components. There is no npm dependency and no React.

### Hard boundary — never cross this

**Fujin scopes to the settings page (`settings_ui.py`) only.**

The SVG cards in `render.py` and the card theme engine in `themes.py` are entirely out of
scope for Fujin. They have their own internal theme system (`Theme` dataclass, 6 named themes)
that is independent of and must not be touched by any Fujin-related work. The cards are the
product; the settings page is a utility screen.

If a task description says "apply Fujin theming," it means `settings_ui.py` only.

---

## What changed on 2026-05-17

The settings page CSS was rewritten to use Fujin's design token values. Approach chosen was
**CSS alignment (Option A)** — not a React integration. The decision record is in DECISIONS.md.

### Changes made to `app/settings_ui.py`

Seven edits to the embedded CSS inside `build_settings_page()`:

1. `:root` custom properties — all color values replaced with Fujin dark Slate palette.
   `--radius: 8px` removed entirely; accent changed from GitHub blue to Fujin violet.
   Font stacks updated: Verdana-first UI stack, JetBrains Mono-first mono stack.

2. `.dot` — `border-radius: 50%` removed. Status dot is now a sharp square.

3. `.label-select, .label-input` — `border-radius: var(--radius)` → `border-radius: 0`

4. `.preview-card` — `border-radius: 10px` removed; box-shadow updated to Fujin shadow-lg.
   Transition duration aligned to Fujin base (150ms).

5. `.embed-url` — `border-radius: var(--radius)` → `border-radius: 0`

6. `.btn` — `border-radius: var(--radius)` → `border-radius: 0`

7. `.toast` — `border-radius: var(--radius)` → `border-radius: 0`

### Token loading — live connection to Fujin

CSS vars are no longer hardcoded. `settings_ui.py` calls `load_dark_tokens()` from
`app/fujin_tokens.py` on each page request. The module loads `app/fujin-tokens-resolved.json`
(a committed copy of Fujin's export) and maps `--fujin-*` vars to local CSS var names.

**Update process when Fujin tokens change:**
1. In `E:\Citadel/Fujin`: `npm run export-tokens` → writes `dist/tokens-resolved.json`
2. Copy that file to `app/fujin-tokens-resolved.json` in this repo
3. Commit and restart (no code change needed — the JSON is read at request time)

**Load order** (`app/fujin_tokens.py`):
1. `FUJIN_TOKENS` env var (override)
2. `app/fujin-tokens-resolved.json` (local copy — used in production/LXC)
3. `../../Fujin/dist/tokens-resolved.json` (dev machine sibling path)
4. Hardcoded fallback (identical to last committed copy — service never hard-fails)

**Var mapping** (`--fujin-*` → local CSS var):
| Local CSS var   | Fujin token                    |
|-----------------|-------------------------------|
| `--bg`          | `--fujin-bg-base`             |
| `--surface`     | `--fujin-bg-surface`          |
| `--surface2`    | `--fujin-bg-elevated`         |
| `--border`      | `--fujin-border-default`      |
| `--accent`      | `--fujin-interactive-default` |
| `--text`        | `--fujin-text-primary`        |
| `--text-dim`    | `--fujin-text-muted`          |
| `--success`     | `--fujin-status-success`      |
| `--accent-dim`  | derived: accent hex + 0.15 opacity |
| `--font`        | `tokens.fontFamily`           |
| `--font-mono`   | `tokens.fontFamilyMono`       |

---

## What "further" means for this project

### Settings page — what to follow if extending

Any new UI element added to `settings_ui.py` must use the existing CSS vars (`--bg`,
`--surface`, `--border`, `--accent`, `--text`, `--text-dim`) and must not introduce
`border-radius` with a non-zero value. Follow the same control patterns: flat bordered
inputs, flat bordered buttons, no decorative curves.

If Fujin's Slate palette or accent changes, the token mapping table above is the update
target in `settings_ui.py`. The card themes in `themes.py` are independent — do not
conflate them.

### Project — pending operator actions

These are blocked on the operator, not agent tasks:
- LXC container provisioning on Proxmox (see `deploy/ct/`)
- `/etc/audiobookshelf-now-playing.env` configured with ABS_HOST and ABS_TOKEN
- Cloudflare Tunnel hostname `card.starlightdaemon.dev` → LXC:8000

Until those are done, the service runs in demo mode (serves static demo cards).

### Potential future agent tasks

- If the settings page grows new controls (e.g. polling interval, ABS connection test),
  wire them to the same CSS vars and ensure no new border-radius is introduced.
- If a `/api/status` display is added to the settings page (e.g. showing live connection
  state), use `--success` / `--text-dim` with a square status indicator, not a dot.
- If Fujin releases a standalone CSS distribution (no React), revisit whether a real
  import becomes viable — check `.raiden/state/DECISIONS.md` first.

---

## Constraints

- Do not modify `app/render.py` or `app/themes.py` for any Fujin-related reason.
- Do not introduce a `package.json`, `node_modules`, or Vite config. This project has
  no JS build step and must not gain one without explicit operator decision.
- Do not add `border-radius` with a non-zero value to the settings page CSS.
- Commit attribution: operator identity only. No Co-Authored-By trailers.
  The commit-msg hook enforces this.
