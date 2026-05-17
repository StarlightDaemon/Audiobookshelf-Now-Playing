# Open Loops

## OL-002 — Deployment: pending operator actions (ongoing)

The following are blocked on operator, not agent tasks:

1. Provision LXC container on Proxmox (see `deploy/ct/audiobookshelf-now-playing.sh`)
2. Set `ABS_HOST` and `ABS_TOKEN` in `/etc/audiobookshelf-now-playing.env` on the LXC
3. Configure Cloudflare Tunnel: `card.starlightdaemon.dev` → LXC:8000

Until these are done, the service operates in demo mode. No agent action available.
