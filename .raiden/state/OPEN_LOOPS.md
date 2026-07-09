# Open Loops

## LOOP-0020 — OPERATING_RULES.md baseline discrepancy (CLOSED)

Investigated 2026-06-07 during WSL→macOS migration audit.
Baseline hash discrepancy was NOT present in this repo — hashes match exactly.
No corrective action needed. Loop closed.

## OL-002 — Deployment blocker: CONFIG_PATH and render.py SyntaxError (CLOSED)

Resolved in v0.2.0 commit `fix: resolve deployment blockers and settings XSS; bump to v0.2.0`.

- `CONFIG_PATH` default moved to `/opt/audiobookshelf-now-playing/config.json` (writable under systemd `ReadWritePaths`)
- f-string backslash SyntaxError in `render.py` fixed; compatible with Python 3.11+
- Stored XSS in settings JS template fixed with `json.dumps(config.label)`

No further agent action required.

## OL-003 — Cloudflare Access gating /settings and /api/config (OPEN)

- Status: OPEN
- Gate: operator

The settings and config API endpoints must be protected before the service is exposed on
`card.starlightdaemon.dev`. This is an operator action:

1. Create a Cloudflare Access application scoping `card.starlightdaemon.dev/settings` and
   `card.starlightdaemon.dev/api/*` to authenticated users only.
2. The `/card` and `/health` endpoints remain public.

No agent action available until the LXC is provisioned and the tunnel is live.

## OL-004 — Post-deployment backlog (OPEN, not blocking)

- Status: OPEN
- Gate: none

Not blocking live deployment. Track individually as separate loops if prioritised:

- Session recency filter: filter out sessions older than a configurable threshold so stale
  "last played" entries don't appear as "currently reading."
- Dependency pinning: `requirements.txt` is currently unpinned; pin to exact versions after
  a successful integration test run.
- Test expansion:
  - 3 missing layout smoke tests (portrait-bookmark, portrait-dogear, portrait-spine-wide)
  - XML-parse assertions on rendered SVG output
  - Mocked httpx integration tests for `abs.py`
  - TestClient integration tests for `/card`, `/settings`, `/api/config`
  - Cache and config round-trip tests
- CI Python 3.11 matrix: add `python-version: ["3.11", "3.12"]` to GitHub Actions workflow
  to verify the f-string fix is exercised in CI.
- doc/CHANGELOG drift cleanup: README still references v0.1.0 feature set; update to v0.2.0.
- Dead code removal: audit for any render helpers or theme paths no longer reachable from
  `main.py` after the multi-layout refactor.
