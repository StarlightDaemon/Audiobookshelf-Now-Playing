# Audiobookshelf Now Playing

[![Version](https://img.shields.io/badge/version-0.2.0-blue?style=flat-square)](CHANGELOG.md)
[![License: MIT](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue?style=flat-square)](https://www.python.org/)

A self-hosted, README-embeddable "Now Listening" widget for [Audiobookshelf](https://www.audiobookshelf.org/). Drop-in equivalent of the Spotify Now Playing badge, for your audiobook shelf.

```md
![Now Listening](https://card.starlightdaemon.dev/card)
```

`/card` renders using whichever layout, theme, corner style, and label were
last saved via the [settings UI](#settings-ui) — no query params needed.
Individual layout endpoints (see [Endpoints](#endpoints)) are also available
directly and accept `?theme=` on their own.

---

## Card preview

```
┌─────────────────────────────────────────┐
│  [COVER]  Now Listening                 │
│           Book Title                    │
│           Author Name                   │
│           Series Name · Book N          │
│           ████████████░░░░  64%         │
└─────────────────────────────────────────┘
```

11 layouts across landscape and portrait families — classic, compact,
editorial, minimal, cover, frosted, typeset, bookmark, dog-ear, spine, and
spine-wide — each in 4 themes: `light` · `github-dark` (default) ·
`parchment` · `kraft`. Pick a combination and preview it live at `/settings`.

---

## Settings UI

`/settings` gives you a live-preview picker for layout, theme, corner style,
and card label, an embeddable URL, and a "Save & apply" button that persists
your choice as the default served by `/card`. Saved config is written to
`CONFIG_PATH` (see [Environment variables](#environment-variables)).

`/settings` and `/api/config` write configuration, so they can be gated behind
[Cloudflare Access](#cloudflare-access-for-settings--apiconfig). When
`CF_ACCESS_TEAM_DOMAIN` and `CF_ACCESS_AUD` are set the app verifies Cloudflare's
signed `Cf-Access-Jwt-Assertion` header on those two paths and rejects
unauthenticated requests; `/card` and `/health` always stay public. With the
vars unset (local/dev) they remain open and the app logs a startup warning.

---

## Architecture

```
GitHub README  →  Cloudflare Tunnel  →  FastAPI (LXC on Proxmox)  →  Audiobookshelf
```

The service calls your ABS instance directly over the internal Proxmox network. ABS never needs additional public exposure.

---

## Deployment

### Prerequisites

- Proxmox with an existing Audiobookshelf instance on the internal network
- A Cloudflare Tunnel already configured (add one new public hostname)
- An ABS API token — generate one in **ABS → Settings → Users → (your user) → API Token**

### 1. Run the ct/ script on the Proxmox host

This creates and configures the LXC container automatically (Debian 12, 1 core, 512 MB, 4 GB):

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/StarlightDaemon/audiobookshelf-now-playing/main/deploy/ct/audiobookshelf-now-playing.sh)
```

The script will:
- Download a Debian 12 template if not already present
- Create and start an unprivileged LXC container
- Run the install script inside it (Python, venv, app, systemd service)
- Print the container's IP and next steps

Resource defaults can be overridden before running:

```bash
var_ram=1024 var_disk=8 bash <(curl -fsSL ...)
```

### 2. Configure environment variables

Edit `/etc/audiobookshelf-now-playing.env` on the LXC:

```env
ABS_HOST=http://192.168.1.100:13378
ABS_TOKEN=your-abs-api-token
SESSION_TTL=10
CARD_TTL=300
SESSION_MAX_AGE=3600
HOST=0.0.0.0
PORT=8000
```

Then restart the service:

```bash
systemctl restart audiobookshelf-now-playing
```

### 3. Configure the Cloudflare Tunnel

Add a new public hostname in your Cloudflare Tunnel configuration:

| Field | Value |
|---|---|
| Public hostname | `card.starlightdaemon.dev` |
| Service | `http://<LXC-IP>:8000` |

### 4. Embed in your README

```md
![Now Listening](https://card.starlightdaemon.dev/card)
```

---

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `ABS_HOST` | *(required)* | Internal URL of your ABS instance, e.g. `http://192.168.1.100:13378` |
| `ABS_TOKEN` | *(required)* | API token from ABS user settings |
| `SESSION_TTL` | `300` | Seconds between polls of ABS for the current session (book changes) |
| `CARD_TTL` | `300` | Seconds to cache cover art + metadata per book; only re-fetched on book change or expiry |
| `SESSION_MAX_AGE` | `3600` | Seconds a listening session may age before it's treated as stale and no longer shown as "currently reading". `0` disables the filter |
| `HOST` | `0.0.0.0` | uvicorn bind address |
| `PORT` | `8000` | uvicorn listen port |
| `CONFIG_PATH` | `/opt/audiobookshelf-now-playing/config.json` | Where saved settings (layout, theme, label, corners) are persisted |
| `FUJIN_TOKENS` | *(unset — falls back to built-in defaults)* | Path to a resolved Fujin design-token JSON file used to theme `/settings` |
| `CF_ACCESS_TEAM_DOMAIN` | *(unset — enforcement off)* | Cloudflare Access team domain (bare name, `*.cloudflareaccess.com` host, or full URL). With `CF_ACCESS_AUD`, gates `/settings` + `/api/config` |
| `CF_ACCESS_AUD` | *(unset — enforcement off)* | Application Audience (AUD) tag of the Access application covering `/settings` and `/api/*` |

---

## Cloudflare Access for `/settings` + `/api/config`

`/card` and `/health` are safe to expose publicly, but `/settings` and
`/api/config` read and write configuration and should be restricted once the
service is on the public internet. The app enforces this itself as defence in
depth: when `CF_ACCESS_TEAM_DOMAIN` and `CF_ACCESS_AUD` are both set, every
request to those two paths must carry a valid `Cf-Access-Jwt-Assertion` header
(the signed token Cloudflare Access injects). The app validates the token's
signature against your team's published signing keys — fetched from
`https://<team-domain>/cdn-cgi/access/certs` and cached — along with its
audience, issuer, and expiry, and returns `401` (missing) or `403` (invalid)
otherwise. With the vars unset, enforcement is off and a startup warning is
logged so local/dev use keeps working.

### Operator: create the Access application in the Cloudflare dashboard

App-side enforcement only takes effect once a matching Access application exists.
In the [Cloudflare Zero Trust dashboard](https://one.dash.cloudflare.com/):

1. **Access → Applications → Add an application → Self-hosted.**
2. Add two **Application domains** on `card.starlightdaemon.dev`, both
   restricted to `/settings` and `/api/*` — leave the bare hostname and `/card`
   **out** so the card stays public:
   - `card.starlightdaemon.dev` path `/settings`
   - `card.starlightdaemon.dev` path `/api/*`
3. Attach a **policy** allowing only the intended identities (e.g. an Allow rule
   scoped to your email or your Access group).
4. Save, then open the application's **Overview** and copy its **Application
   Audience (AUD) tag**.
5. On the LXC, set both vars in `/etc/audiobookshelf-now-playing.env`:
   ```env
   CF_ACCESS_TEAM_DOMAIN=<your-team>.cloudflareaccess.com
   CF_ACCESS_AUD=<the-AUD-tag-from-step-4>
   ```
   then `systemctl restart audiobookshelf-now-playing`.

After the restart, unauthenticated hits to `/settings` or `/api/config` are
rejected both at Cloudflare's edge and by the app itself, while `/card` stays
open.

---

## Endpoints

| Endpoint | Description |
|---|---|
| `GET /card` | Primary embed endpoint — layout, theme, label, and corners come from saved config (`/settings`) |
| `GET /settings` | Settings UI — live preview, layout/theme/corners/label pickers, save-to-disk |
| `GET /api/config` | Current saved config as JSON |
| `POST /api/config` | Save layout/theme/label/corners (JSON body); `400` on an unknown layout, theme, or corner style |
| `GET /cardlandscape` | Landscape Classic SVG card (600×160) — add `?theme=` |
| `GET /cardportrait` | Portrait Cover SVG card (240×360) — add `?theme=` |
| `GET /cardlandscape{c,d,e}` · `/cardportrait{c,e,f,g,h,i}` | Remaining layout variants (compact, editorial, minimal, frosted, typeset, bookmark, dog-ear, spine, spine-wide) |
| `GET /card...demo` | Demo counterpart of each layout endpoint — sample data, ignores ABS, accepts `?theme=&label=&corners=` |
| `GET /health` | Health check — returns `{"status": "ok", "demo_mode": bool}` |
| `GET /status` | JSON playing status (title/author/series when playing) |

---

## Local development

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt

export ABS_HOST=http://192.168.1.100:13378
export ABS_TOKEN=your-token

uvicorn app.main:app --reload
# → http://localhost:8000/card
```

### Running tests

```bash
pytest -v
```

The suite includes SVG-renderer smoke tests (all 11 layouts × 4 themes, with
XML well-formedness checks), mocked `httpx` tests for the ABS client,
cache/config round-trip tests, and `TestClient` integration tests for
`/card`, `/settings`, and `/api/config`. CI runs the full suite on Python
3.11 and 3.12.

---

## Fallback states

| Condition | Card shows |
|---|---|
| No recent session | "Not currently playing" |
| ABS unreachable | "Unable to reach Audiobookshelf" |
| Cover art unavailable | Book icon placeholder |

---

## Scope (v1)

- Audiobooks only — podcast sessions are filtered out
- Single-user — one ABS token, one user's sessions
- In-memory cache — restarts reset the cache; `SESSION_TTL`/`CARD_TTL` default to 300 s
- Stale sessions (older than `SESSION_MAX_AGE`, default 1 hour) are treated as "not playing" rather than shown indefinitely

---

## Versioning

This project uses [Semantic Versioning](https://semver.org/). See [CHANGELOG.md](CHANGELOG.md) for release history.

---

## License

[MIT](LICENSE) © 2026 StarlightDaemon
