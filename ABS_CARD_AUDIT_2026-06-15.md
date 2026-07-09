# Audiobookshelf Now Playing — Pre-Deployment Audit
**Audit date:** 2026-06-15
**Version audited:** v0.1.0 (HEAD `41cdbc0`, 57 commits ahead of tag `v0.1.0`)
**Type:** Pre-deployment readiness audit

## Deployment Readiness Verdict

**NOT READY.**

The application **cannot start on its own deployment target**. `app/render.py:190` uses a backslash inside an f-string expression part, which is a hard `SyntaxError` on every Python below 3.12 (PEP 701). The deploy stack provisions Debian 12 (`var_version=12`), whose system `python3` — used verbatim to build the venv — is **Python 3.11.2**. On import, `app.render` raises `SyntaxError`, `uvicorn app.main:app` never binds, and the hardened unit's `Restart=on-failure` loops forever. This was invisible in development because the dev machine runs Python 3.12 (confirmed: the file compiles under 3.12 and fails under 3.9/3.11). A secondary blocker compounds it: the settings UI's config persistence writes to `/etc`, which the systemd sandbox (`ProtectSystem=strict`) and the non-root `abs-card` user both forbid, so a shipped feature is dead on arrival. Both defects are **agent-fixable before** any infrastructure is provisioned — the operator should not provision the LXC until they are corrected.

---

## Findings by Domain

### 1. Code Correctness & Quality

#### CRITICAL — f-string syntax breaks the build on the target runtime — `app/render.py:190`
```python
f'{" opacity=\"0.45\" font-style=\"italic\"" if muted else ""}>'
```
Backslashes inside the expression part of an f-string are only legal from Python 3.12 (PEP 701). Verified:
- `/usr/bin/python3` (3.9.6): `SyntaxError: f-string expression part cannot include a backslash`
- `python3.12`: compiles cleanly.

The deploy targets Debian 12 → Python 3.11.2; `deploy/install/...-install.sh:80` builds the venv from that interpreter. Result: `from .render import ...` in `app/main.py:12` fails at import → service never starts. `app/render.py` is the **only** module that fails to compile under <3.12; all others compile under 3.9. The README badge claims `python-3.11+` (`README.md:5`), which this directly contradicts.
**Fix:** hoist the conditional out of the f-string, e.g. `muted_attr = ' opacity="0.45" font-style="italic"' if muted else ''` then interpolate `{muted_attr}`. (low complexity, **blocking**)

#### MEDIUM — "most recent session" is presented as "currently playing" — `app/abs.py:26-39`, `app/main.py:79-81`
`get_current_session()` returns `book_sessions[0]` from `/api/me/listening-sessions` with **no recency/active filter**. A book finished weeks ago still renders under the "Currently Reading" label indefinitely, and the "No listening history yet" state (`render.py:243`) effectively never appears once any session has ever existed. `CURRENT_STATE.md` acknowledges the position is last-sync (not live) but not this staleness-of-book issue, and the README/labels imply live status.
**Fix:** filter on session `updatedAt`/`isActive` within a window, or relabel honestly. (medium, post-deployment polish)

#### LOW — empty `libraryItemId` produces an error card — `app/main.py:82`
`item_id = session.get("libraryItemId", "")` → `get_item("")` hits `/api/items/` → non-2xx → `raise_for_status()` → error card. Defensive `if not item_id: return None` would degrade gracefully. (low, polish)

#### LOW — dead/confusing legacy code — `app/render.py:8-27`
A fully commented-out earlier `_progress_bar` block sits directly above the active one (`render.py:88`). Two "progress bar" definitions in one file invites the wrong one being edited. Delete the block. (low, polish)

#### INFO — cache thread-safety is fine for the shipped config only — `app/cache.py`
`TTLCache` is a plain dict with no lock. Correct under the single-process, single-worker uvicorn invocation in the unit (`deploy/...service:11-13`, no `--workers`). If anyone adds `--workers N`, each worker gets an independent cache **and** an independent view of saved config. Document the single-worker assumption. The `set("session", False)` sentinel logic (`main.py:73-80`) is correct.

#### INFO — `config.py` load path is robust; save path is not (see Deployment §4)
`load_config()` correctly handles `FileNotFoundError` → defaults and validates every field (`config.py:31-52`). The defect is the *write* path, covered under Deployment.

### 2. Test Coverage

#### MEDIUM — coverage is a startup smoke check, not a test suite — `tests/smoke.py`
- Exercises **8 of 11** layouts × 4 themes = 32 assertions, **demo variants only**. Missing from `RENDERERS` (`smoke.py:27-36`): `render_landscape_minimal_demo`, `render_portrait_spine_demo`, `render_portrait_spine_wide_demo`.
- Never calls the real `render_*` (with live `CardData`), nor the `_nothing`/`_error`/standalone variants.
- Assertions are `startswith("<svg")` / `endswith("</svg>")` only — no XML well-formedness/parse check, so malformed-but-bracketed SVG passes.
- **Zero** tests for `abs.py`, `cache.py` (TTL expiry), `config.py` (load/save round-trip + validation), `fujin_tokens.py`, or any `main.py` endpoint.
- Crucially, the suite runs under dev Python (3.12) and so **would not have caught the CRITICAL** — only a run on the target Python would.

**Positives:** the smoke test **is** runnable without a live ABS (pure demo data, no network — `smoke.py:91-94`) and is dual-mode (standalone + pytest via injected globals).

#### LOW — pytest not configured; `_check()` is dead code
No `conftest.py`, `pytest.ini`, `pyproject.toml`, or `setup.cfg` (verified absent). `python -m pytest tests/smoke.py` works only via the runtime-injected `test_*` globals (`smoke.py:78-81`). `_check()` (`smoke.py:39-53`) is never called and contains a no-op `result = renderer_name`. pytest is not in `requirements.txt` (acceptable as dev-only).

**Appropriate target for a deployed service:** TestClient integration tests for `/health`, `/status`, `/card`, `/api/config` (incl. 400 paths); `abs.py` with mocked `httpx`; `cache.py` TTL-expiry; `config.py` round-trip; XML-parse assertion on every renderer; and **CI on a Python 3.11 matrix** (which alone would have caught the CRITICAL).

### 3. Security

#### MEDIUM — unauthenticated, publicly-exposed config mutation + stored XSS — `app/main.py:414-446`, `app/settings_ui.py:427`
`/settings` (GET) and `/api/config` (GET/POST) have **no authentication** and are intended to sit behind the public Cloudflare Tunnel (`card.starlightdaemon.dev`). Two consequences:
- **Defacement:** anyone on the internet can `POST /api/config` to change the global card layout/theme/label shown on the operator's README. `layout`/`theme`/`corners` are allowlist-validated (safe), but the mutation itself is unauthenticated.
- **Stored XSS:** `label` is persisted (validated only as non-empty `str`, `main.py:441-443`) then interpolated **unescaped** into a `<script>` string literal: `let currentLabel = "{config.label}";` (`settings_ui.py:427`). A label such as `</script><script>…` breaks out and executes in `/settings`. In SVG output `label` is escaped via `_x()`, but the HTML/JS context here is not — a gap the 2026-05-18 security audit (SVG-only) did not cover.

Currently *latent* only because finding §4 prevents persistence. **If §4 is fixed without adding auth, this goes live.**
**Fix:** put Cloudflare Access (or basic auth) in front of `/settings` + `/api/config`; JSON/HTML-escape `label` before interpolation. (medium, **fix before exposing settings**)

#### INFO — token handling is clean (PASS)
`ABS_TOKEN` is read from the environment only (`abs.py:20`), sent as a `Bearer` header, **never logged or echoed**; the lifespan warning names the env vars but not their values (`main.py:51-55`); `is_configured()` rejects the placeholder (`abs.py:7-14`). No credential appears in any response. `/status` and `/health` expose only intended public data (title/author/series; `demo_mode` boolean).

#### INFO — CORS absence is correct, not a gap
No CORS middleware is configured, and none is needed: cards are consumed via `<img>` (not subject to CORS) and the settings page calls `/api/config` same-origin. No action required.

#### INFO — no hardcoded secrets
Only project-identity constants are hardcoded (`StarlightDaemon` org, `card.starlightdaemon.dev`); the `.env.example` token is the documented placeholder. PASS.

### 4. Deployment Readiness

#### HIGH — saved config cannot be written in production (settings feature dead on arrival) — `app/config.py:8-9,55-61`; `deploy/...service:18-20`
`_CONFIG_PATH` defaults to `/etc/audiobookshelf-now-playing-config.json`. The unit runs as non-root `abs-card` with `ProtectSystem=strict` + `ReadWritePaths=/opt/audiobookshelf-now-playing` only — so `/etc` is **read-only**, and even without the sandbox `abs-card` cannot write `/etc`. `save_config()` (`config.py:57`) raises and **re-raises**, so `POST /api/config` returns 500 and the UI shows "Failed to save". The install script never creates/chowns the config file, and `CONFIG_PATH` is documented nowhere (`.env.example`/README/deploy — verified absent). Because the file never exists, `/card` (`main.py:449-455`) silently serves hardcoded defaults forever.
**Fix:** point `CONFIG_PATH` at a writable location (e.g. `/opt/audiobookshelf-now-playing/config.json`, already in `ReadWritePaths`), or add a writable dir to the unit + create/chown it in install; document the variable. (low–medium, **blocking for the settings feature**)

#### MEDIUM — `.env.example` is inconsistent with code and README
`.env.example` correctly documents the **real** variables `SESSION_TTL` and `CARD_TTL` (`main.py:33-35`) — but the README/CHANGELOG document a **non-existent** `CACHE_TTL` (see §Docs). It omits `CONFIG_PATH`, `FUJIN_TOKENS`. `HOST`/`PORT` are present and required by the unit's `ExecStart=${HOST}/${PORT}` substitution (`...service:12-13`); a hand-edited env file omitting them would yield empty uvicorn args. (low, polish)

#### INFO — deploy scripts are otherwise sound
The `ct/` host script (community-scripts style, whiptail wizard, credential capture, `pct` create/start) and the `install/` script (FUNCTIONS_FILE_PATH dual-mode, venv via `python3-venv`/ensurepip to avoid the gcc toolchain, dedicated `abs-card` user, env file `chmod 640 root:abs-card`, MOTD + update symlinks) are coherent and reference consistent paths/service names. The systemd unit references correct user/group/WorkingDirectory/EnvironmentFile and is well-hardened.

#### INFO — health check exists but the deploy script never probes it — `app/main.py:373-375`
`/health` returns `{"status":"ok","demo_mode":…}` and is used by `motd.sh` via `/status`, but neither the `ct/` nor `install/` script waits on `/health`/`/status` after `systemctl start` before declaring success (`ct/...sh:320-322`). Add a readiness poll so a crash-looping service (e.g. the CRITICAL) is reported at install time instead of appearing "live."

#### INFO — startup when ABS is unreachable is handled gracefully
`is_configured()` gates client creation; missing creds → demo mode with a clear warning (`main.py:50-55`). With creds set but ABS down, `_fetch_card_data` raises → caught in `_serve_card` (`main.py:163-165`) → "Unable to reach Audiobookshelf" card. Startup never blocks on ABS. PASS.

### 5. Governance State

- **Edict version: v1.0.0 — current, NOT behind CTRL.** Confirmed in `instance/metadata.json`, `instance/baseline.json`, `writ/README.md`, and the latest commit. Matches CTRL's v1.0.0.
- **No stale operational WSL/`/mnt` paths.** The only `wsl`/`/mnt` hits are *historical notes describing the completed 2026-06-07 migration* inside `CURRENT_STATE.md:28-31` and `OPEN_LOOPS.md:5`. Migration is genuinely complete.
- **`CURRENT_STATE.md` is inaccurate.** "What exists → app/ (main.py, abs.py, cache.py, render.py, themes.py)" omits `config.py`, `settings_ui.py`, `fujin_tokens.py`, `fujin-tokens-resolved.json`, `tests/`, `deploy/motd.sh`, `deploy/update.sh`. It frames "v0.1.0 shipped … Tagged v0.1.0" as the current state, but **HEAD is 57 commits ahead of tag `v0.1.0`** (tag = `40605bb`, 2026-05-15) with major unreleased features (settings UI, 4 themes, 11 layouts, corners, Fujin tokens) and **no new CHANGELOG/VERSION entry**.
- **`OPEN_LOOPS.md` is inaccurate.** It asserts only operator actions remain ("No agent action available"). The CRITICAL and HIGH above are agent-fixable and **must precede** deployment — there is substantial agent work outstanding.
- **`GOALS.md` "README & Docs: Done" overstates** given the doc drift below.
- **`DECISIONS.md` D-001/D-002 are accurate and respected:** `render.py`/`themes.py` carry no Fujin values; `settings_ui.py` uses CSS-var alignment only. ✓

### 6. Dependencies

- **All imports satisfied by the three pinned deps.** `fastapi` (+ bundled `starlette`), `uvicorn[standard]` (runtime server), `httpx` (`abs.py`). Everything else is stdlib (`base64`, `json`, `os`, `logging`, `time`, `pathlib`, `dataclasses`, `contextlib`, `typing`). **No missing dependency.** ✓
- **MEDIUM — versions are floor-pinned only** (`fastapi>=0.115.0`, `uvicorn[standard]>=0.30.0`, `httpx>=0.27.0`). The update path (`deploy/update.sh:14`, `ct/...sh:108`) runs `pip install -r requirements.txt` on **every** git pull, so a future breaking upstream release can break a previously-working container with no code change. For a deployed service, pin exact versions or add a lockfile (uv/pip-tools) and an upper-bound policy.

#### LOW — `fujin_tokens` silently drops missing mapped tokens — `app/fujin_tokens.py:73-74`
`if fujin in dark: result[local] = …` omits any mapped token absent from the source, which would later `KeyError` in `settings_ui.py`'s `t['--surface2']`-style f-strings. Safe with the committed `fujin-tokens-resolved.json` (all keys present, valid, `dark`+`tokens`+computed `--accent-dim`). **What is it / is it used / correct?** It themes the `/settings` HTML page only (per D-001/D-002), is genuinely imported by `settings_ui.build_settings_page`, and is correct — but it couples the repo to an external "Fujin" checkout for a single utility page and is not mentioned in the CHANGELOG/spec.

#### MEDIUM (cross-cutting) — Documentation drift between README/CHANGELOG and code
- `CACHE_TTL` documented (`README.md:80,114`; `CHANGELOG.md:25`) **does not exist**; real vars are `SESSION_TTL`/`CARD_TTL`.
- README "Themes: dark · light" and CHANGELOG "Dark and light themes" — actually **4** themes (`light`, `github-dark`, `parchment`, `kraft`), default `github-dark`.
- CHANGELOG "495×128 px" card — actual landscape is **600×160**.
- README endpoint table omits `/card` (the canonical embed per the settings UI), `/settings`, `/api/config`, and all **9** non-default layout routes; `/health` body understated.
- README fallback text "Not currently playing" — code renders "No listening history yet".
- README deployment steps skip from "### 2" to "### 4" (no step 3); embed examples use `/cardlandscape` while the settings UI promotes `/card` — the canonical URL story is inconsistent.

---

## Agent Work Identified

Prioritized; complexity and blocking status noted.

1. **[BLOCKING · low] Fix `render.py:190` f-string backslash.** Extract the conditional to a variable so the file parses on Python 3.11. The single highest-priority item — nothing deploys until this lands.
2. **[BLOCKING · low–medium] Make config writable in production.** Default `CONFIG_PATH` to a path inside `ReadWritePaths` (e.g. `/opt/audiobookshelf-now-playing/config.json`), or add+create+chown a writable dir in the install script; document the variable. Removes the 500 on Save and makes `/card` honor saved config.
3. **[BLOCKING-for-exposure · medium] Gate `/settings` + `/api/config`** (Cloudflare Access / basic auth) **and HTML/JS-escape `label`** at `settings_ui.py:427`. Required before the settings UI is reachable from the public tunnel.
4. **[post-deploy · low] Add a target-Python CI check** (compile + smoke on a 3.11 matrix) so a §1-class regression can never ship again.
5. **[post-deploy · medium] Reconcile docs with code:** fix `CACHE_TTL`→`SESSION_TTL`/`CARD_TTL`, theme count, card dimensions, endpoint table, fallback strings, step numbering, and the `/card` vs `/cardlandscape` canonical-URL story.
6. **[post-deploy · low] Pin dependency versions / add a lockfile.**
7. **[post-deploy · medium] Expand tests:** add the 3 missing layouts to `smoke.py`, an XML-parse assertion, and TestClient/abs-mock/cache-TTL/config round-trip tests.
8. **[post-deploy · low] Session recency filter** so "Currently Reading" reflects an active session, not the all-time-latest.
9. **[post-deploy · low] Cleanup:** delete dead `_progress_bar` comment block (`render.py:8-27`) and dead `_check()` (`smoke.py:39-53`).
10. **[governance · low] Update `CURRENT_STATE.md`/`OPEN_LOOPS.md`** to list all modules, record HEAD-vs-tag drift, and capture the blocking code defects as open loops; cut a real tag/CHANGELOG entry (e.g. v0.2.0) for the 57 post-tag commits.

## Operator Actions Required

These cannot be done by an agent. **Do not perform #1–#3 until Agent items 1–2 land**, or the LXC will deploy a crash-looping service.

1. **Provision the Proxmox LXC** (`deploy/ct/audiobookshelf-now-playing.sh`).
2. **Set `ABS_HOST` and `ABS_TOKEN`** in `/etc/audiobookshelf-now-playing.env` on the LXC.
3. **Configure the Cloudflare Tunnel:** `card.starlightdaemon.dev` → `LXC:8000`.
4. **Decide settings-UI exposure:** enable Cloudflare Access for `/settings` + `/api/config` (pairs with Agent item 3), or keep them off the public hostname.
5. **Choose the config storage location** (`CONFIG_PATH`) so it matches the writable path chosen in Agent item 2.

## Governance Notes

- **Edict:** v1.0.0 — current, parity with CTRL; not behind.
- **Migration:** WSL→macOS remediation is genuinely complete; remaining `wsl`/`/mnt` strings are historical notes only, not live paths.
- **State accuracy:** `CURRENT_STATE.md` and `OPEN_LOOPS.md` are **out of date** — they predate the settings UI / multi-layout / Fujin work (added after the `v0.1.0` tag), omit several shipped modules, and incorrectly assert that only operator actions remain. The repo presents as "v0.1.0 shipped" while HEAD carries 57 unreleased commits with no corresponding tag/CHANGELOG/VERSION bump. `DECISIONS.md` (D-001/D-002) is accurate and the code honors it.
