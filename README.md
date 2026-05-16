# Audiobookshelf Now Playing

A self-hosted, README-embeddable "Now Listening" widget for [Audiobookshelf](https://www.audiobookshelf.org/). Drop-in equivalent of the Spotify Now Playing badge, for your audiobook shelf.

```md
![Now Listening](https://card.starlightdaemon.dev/card)
```

```md
![Now Listening](https://card.starlightdaemon.dev/card?theme=light)
```

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

Themes: `dark` (default) · `light`

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
CACHE_TTL=60
HOST=0.0.0.0
PORT=8000
```

Then restart the service:

```bash
systemctl restart audiobookshelf-now-playing
```

### 4. Configure the Cloudflare Tunnel

Add a new public hostname in your Cloudflare Tunnel configuration:

| Field | Value |
|---|---|
| Public hostname | `card.starlightdaemon.dev` |
| Service | `http://<LXC-IP>:8000` |

### 5. Embed in your README

```md
![Now Listening](https://card.starlightdaemon.dev/card)
```

---

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `ABS_HOST` | *(required)* | Internal URL of your ABS instance, e.g. `http://192.168.1.100:13378` |
| `ABS_TOKEN` | *(required)* | API token from ABS user settings |
| `CACHE_TTL` | `60` | Seconds to cache ABS responses before re-fetching |
| `HOST` | `0.0.0.0` | uvicorn bind address |
| `PORT` | `8000` | uvicorn listen port |

---

## Endpoints

| Endpoint | Description |
|---|---|
| `GET /card` | SVG card — add `?theme=light` for light theme |
| `GET /health` | Health check — returns `{"status": "ok"}` |

---

## Local development

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

export ABS_HOST=http://192.168.1.100:13378
export ABS_TOKEN=your-token

uvicorn app.main:app --reload
# → http://localhost:8000/card
```

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
- In-memory cache — restarts reset the cache; TTL defaults to 60 s
