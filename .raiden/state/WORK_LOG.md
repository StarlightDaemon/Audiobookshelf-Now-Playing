# Work Log

## 2026-07-09 — OL-003 Cloudflare Access gating implemented app-side

- Operator approved gating `/settings` and `/api/config`. Implemented app-side
  enforcement as defence in depth (the Cloudflare edge policy is still the
  operator's dashboard step).
- `app/cf_access.py` — new module. `require_cf_access` FastAPI dependency reads
  `CF_ACCESS_TEAM_DOMAIN` + `CF_ACCESS_AUD` at call time; when both set it
  verifies the `Cf-Access-Jwt-Assertion` header via `PyJWT` against the team
  JWKS (`https://<team>/cdn-cgi/access/certs`, cached with `PyJWKClient`),
  checking RS256 signature, audience, issuer, and expiry. Fails closed: 401 on
  a missing header, 403 on any invalid token. When either var is unset the gate
  is a no-op (passthrough) and `main.py`'s lifespan logs a startup warning —
  same optional-env posture as `SESSION_MAX_AGE`, so local/dev use is unchanged.
- `app/main.py` — added `dependencies=[Depends(require_cf_access)]` to the three
  routes (`GET /settings`, `GET /api/config`, `POST /api/config`); `/card`,
  `/health`, `/status`, and all card variants stay public. Added the
  enforcement-off startup warning.
- Dependency: `requirements.txt` gains `PyJWT[crypto]==2.13.0` +
  `cryptography==49.0.0` (pinned); verified with a clean install on 3.12.
- `tests/test_cf_access.py` — 19 tests. Real RSA keypair, tokens signed with
  PyJWT, JWKS client stubbed to the matching public key so `jwt.decode` runs
  genuine verification: allow (all three routes), deny (missing→401;
  invalid-signature / expired / wrong-aud / wrong-issuer / malformed→403),
  unset-env passthrough, public endpoints open under enforcement, plus unit
  coverage of `_normalize_team_domain` and `is_access_enforced`. Suite 88 → 107,
  green.
- Docs: README gains a "Cloudflare Access" section (behaviour + operator
  dashboard steps) and two env-var table rows; the old "unauthenticated" note
  rewritten. `.env.example` documents both vars. CHANGELOG Unreleased entry.
- OL-003 moved from OPEN to "Implemented app-side, pending Cloudflare dashboard
  policy (2026-07-09) — Gate: operator (dashboard)" in `OPEN_LOOPS.md`;
  `CURRENT_STATE.md` snapshot updated (new module, test file, operator action).

## 2026-07-09 — OL-004 post-deployment backlog closed

- All six OL-004 items landed across 11 commits (`2f00e72`..`8e72bc2`), each commit green
  against the suite:
  - Session recency filter: `SESSION_MAX_AGE` env var (default 3600s) in `main.py`, filter
    on session `updatedAt` in `AbsClient.get_current_session()`; documented in
    `.env.example` and README.
  - Test expansion: smoke tests grown from 8 to all 11 layouts with XML well-formedness
    checks; mocked `httpx` tests for `abs.py`; cache TTL and config round-trip tests;
    `TestClient` integration tests for `/card`, `/settings`, `/api/config`. Suite grew
    32 → 88 tests; `pytest.ini` and `requirements-dev.txt` added.
  - CI: `.github/workflows/ci.yml` added, `python-version: ["3.11", "3.12"]` matrix
    (none existed before).
  - Dependency pinning: `requirements.txt` pinned to `fastapi==0.139.0`,
    `uvicorn[standard]==0.51.0`, `httpx==0.28.1` after the full 88-test suite passed
    against them from clean installs on both 3.11.15 and 3.12.13.
  - doc drift: README rewritten from the v0.1.0 feature set to v0.2.0 reality (endpoints,
    env vars, settings UI, testing section); CHANGELOG Unreleased entry added.
  - Dead code: stale commented-out `_progress_bar()` block and unused `txt_w` local
    removed from `render.py`; uncalled `_check()` helper removed from `tests/smoke.py`.
- Chore alongside: `ABS_CARD_AUDIT_2026-06-15.md` committed in place (no docs/audit home;
  `audit-reports/` is gitignored generated output); `.serena/` added to `.gitignore`.
- OL-004 marked Closed (2026-07-09) in `OPEN_LOOPS.md`. OL-003 untouched (operator-gated).

## 2026-07-09 — Edict v2.0.0 + state normalization

- Applied RAIDEN Edict update 1.0.1 → 2.0.0 via `raiden_updater.cli` (plan → apply → re-plan
  confirmed "Already up to date"). Managed-file changes: added `ROUTING_POLICY.md`; removed
  `MODEL_TIERS.md` (present in installed baseline, absent from new package — expected
  `managed_file_removal` warning, accepted); `README.md`, `OPERATING_RULES.md`,
  `WORKSPACE_AUDIT_PROTOCOL.md`, `FORK_REVIEW_PROTOCOL.md`, `AGENTS.md` updated to v2.0.0
  content; `hooks/commit-msg` unchanged.
- Stamped `"state_schema_version": 2` into `.raiden/instance/metadata.json`.
- Routing overlay migrated: removed `.raiden/local/MODEL_MAP.md` (untracked/gitignored tier
  map, never committed) and replaced it with `.raiden/local/ROUTING.md`, a rung-based routing
  ladder (R1–R4 plus an offload pool) reflecting current available models and the
  subscription-first billing posture (Raiden-ops `DECISIONS.md` OPS-D-003).
- State normalization pass (per `.raiden/writ/OPERATING_RULES.md` Fact-Home Rule):
  - Relocated the 2026-06-07 WSL→macOS migration note out of `CURRENT_STATE.md` into this
    log (see entry below) — `CURRENT_STATE.md` had been carrying dated historical narrative,
    which belongs here instead.
  - Removed the duplicate "(Edict v0.6.1)" version citation from `OPEN_LOOPS.md` LOOP-0020;
    that historical detail now lives only in the dated log entry below.
  - Collapsed `CURRENT_STATE.md`'s "Post-deployment backlog" section, which fully restated
    OL-004's content (and mis-cited one item as OL-003), into a bare `OL-004` citation.
  - No hand-written "Last Updated"/"Last Verified" footers were found in `.raiden/state/*.md`.

## 2026-06-07 — WSL→macOS migration remediation (Edict v0.6.1 audit)

- Hook permissions corrected (commit-msg, pre-commit: 666 → 755)
- pre-commit hook updated to use python3.12 explicitly (macOS system python3 = 3.9)
- Path references updated: /mnt/e/ → /Users/dante/Citadel/ (AGENTS.md, fujin-css-handoff.md)
- LOOP-0020 baseline discrepancy investigated — NOT present in this repo, hashes match

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
