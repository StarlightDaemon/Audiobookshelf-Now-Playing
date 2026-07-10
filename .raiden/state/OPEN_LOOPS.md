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

## OL-003 — Cloudflare Access gating /settings and /api/config

- Status: Implemented app-side, pending Cloudflare dashboard policy (2026-07-09)
- Gate: operator (dashboard)

App-side enforcement is done: `/settings` and `/api/config` verify the
`Cf-Access-Jwt-Assertion` header (signature via the team JWKS, plus
audience/issuer/expiry) and fail closed — 401 missing, 403 invalid — when
`CF_ACCESS_TEAM_DOMAIN` and `CF_ACCESS_AUD` are set; unset preserves current
behaviour with a startup warning. `/card` and `/health` stay public. See
`app/cf_access.py` and the WORK_LOG entry.

Remaining (operator, in the Cloudflare dashboard — cannot be automated here):

1. Create a Cloudflare Access (self-hosted) application scoping
   `card.starlightdaemon.dev/settings` and `card.starlightdaemon.dev/api/*` to
   authenticated identities only; leave `/card` public.
2. Copy the application's AUD tag and set `CF_ACCESS_TEAM_DOMAIN` +
   `CF_ACCESS_AUD` in `/etc/audiobookshelf-now-playing.env`, then restart the
   service. Full step-by-step in the README "Cloudflare Access" section.

## OL-004 — Post-deployment backlog (Closed 2026-07-09)

- Status: Closed (2026-07-09) — all six backlog items landed with the full test suite green.

Resolved:

- Session recency filter: `SESSION_MAX_AGE` env var (default 3600s) filters sessions whose
  `updatedAt` exceeds the threshold out of `AbsClient.get_current_session()`.
- Test expansion: smoke tests now cover all 11 layouts (was 8) with XML-parse
  well-formedness checks; mocked `httpx` tests for `abs.py`; `TestClient` integration tests
  for `/card`, `/settings`, `/api/config`; cache and config round-trip tests — 88 tests total.
- CI: `.github/workflows/ci.yml` added with a `python-version: ["3.11", "3.12"]` matrix.
- Dependency pinning: `requirements.txt` pinned to exact versions after the full suite was
  verified green on both 3.11 and 3.12.
- doc/CHANGELOG drift: README rewritten from the v0.1.0 feature set to v0.2.0 reality;
  CHANGELOG got an Unreleased entry for this pass.
- Dead code removal: stale commented-out `_progress_bar()` block and an unused local in
  `render.py`, plus an uncalled test helper in `tests/smoke.py`.
