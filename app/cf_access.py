"""
Cloudflare Access enforcement for the sensitive endpoints (`/settings`,
`/api/config`).

When the service is exposed publicly via a Cloudflare Tunnel, an Access
application in the Cloudflare dashboard fronts these paths and injects a signed
`Cf-Access-Jwt-Assertion` header on every request it lets through. This module
verifies that JWT *inside the app* as defence in depth: even if the tunnel or a
misconfigured route let an un-vetted request reach the app directly, the token
is validated against Cloudflare's published signing keys before the request is
served.

Behaviour is controlled by two env vars, following the same optional-env pattern
as `SESSION_MAX_AGE`:

- `CF_ACCESS_TEAM_DOMAIN` — your Access team domain, e.g. `myteam`,
  `myteam.cloudflareaccess.com`, or the full `https://…` URL. Any of these forms
  is accepted.
- `CF_ACCESS_AUD` — the Application Audience (AUD) tag of the Access application
  covering `/settings` and `/api/*`.

Enforcement is active only when **both** are set. When either is unset the gate
is a no-op (`require_cf_access` returns immediately), preserving current
behaviour for local/dev use — the app logs a startup warning in that case.

Fail-closed semantics when enforcement is active:
- missing header               → 401
- invalid signature / expired / wrong-aud / wrong-issuer / JWKS unreachable → 403
"""

import logging
import os
from typing import Dict

import jwt
from fastapi import HTTPException, Request

logger = logging.getLogger(__name__)

# The header Cloudflare Access injects on authenticated requests.
ACCESS_JWT_HEADER = "Cf-Access-Jwt-Assertion"


def _normalize_team_domain(raw: str) -> str:
    """Accept a bare team name, a `*.cloudflareaccess.com` host, or a full URL."""
    d = raw.strip()
    for scheme in ("https://", "http://"):
        if d.startswith(scheme):
            d = d[len(scheme):]
            break
    d = d.strip("/")
    if d and "." not in d:
        d = f"{d}.cloudflareaccess.com"
    return d


def _team_domain() -> str:
    return _normalize_team_domain(os.environ.get("CF_ACCESS_TEAM_DOMAIN", ""))


def _aud() -> str:
    return os.environ.get("CF_ACCESS_AUD", "").strip()


def is_access_enforced() -> bool:
    """True only when both env vars are set — otherwise the gate is a no-op."""
    return bool(_team_domain() and _aud())


# One cached JWKS client per certs URL. PyJWKClient fetches the team's public
# signing keys lazily on first use and caches them, so we never fetch per request.
_jwk_clients: Dict[str, "jwt.PyJWKClient"] = {}


def _get_jwk_client(certs_url: str) -> "jwt.PyJWKClient":
    client = _jwk_clients.get(certs_url)
    if client is None:
        client = jwt.PyJWKClient(certs_url)
        _jwk_clients[certs_url] = client
    return client


async def require_cf_access(request: Request) -> None:
    """
    FastAPI dependency: verify the Cloudflare Access JWT.

    No-op when enforcement is not configured. When configured, raises 401 for a
    missing token and 403 for any invalid token.
    """
    domain = _team_domain()
    aud = _aud()
    if not (domain and aud):
        return

    token = request.headers.get(ACCESS_JWT_HEADER)
    if not token:
        raise HTTPException(status_code=401, detail="Cloudflare Access token missing")

    certs_url = f"https://{domain}/cdn-cgi/access/certs"
    issuer = f"https://{domain}"
    try:
        signing_key = _get_jwk_client(certs_url).get_signing_key_from_jwt(token)
        jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=aud,
            issuer=issuer,
        )
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=403, detail="Cloudflare Access token invalid")
    except Exception:
        # JWKS unreachable, malformed key material, etc. — fail closed.
        logger.exception("Cloudflare Access token verification failed")
        raise HTTPException(status_code=403, detail="Cloudflare Access verification unavailable")
