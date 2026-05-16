# Goals

## Primary Goal

Build a self-hosted, README-embeddable "Now Listening" widget for Audiobookshelf — a single image URL that renders a styled SVG card showing the current or most recent audiobook listening session, embeddable in any GitHub profile README.

## Milestones

| # | Milestone | Status |
|---|---|---|
| 1 | RAIDEN Orientation | Done |
| 2 | LXC Provisioning | Pending — operator action required |
| 3 | ABS Client | Done |
| 4 | SVG Renderer | Done |
| 5 | FastAPI Service | Done |
| 6 | Caching | Done |
| 7 | Tunnel Config | Pending — operator action required |
| 8 | Theming | Done |
| 9 | Fallback States | Done |
| 10 | README & Docs | Done |

## Deployment Target

LXC container on Proxmox. FastAPI via uvicorn, managed by systemd. Public endpoint via Cloudflare Tunnel at `card.starlightdaemon.dev`.

## Out of Scope (v1)

- Docker deployment
- Multi-user support
- OAuth flow
- Podcast sessions
