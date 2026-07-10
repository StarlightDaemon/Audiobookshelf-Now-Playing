"""
Tests for Cloudflare Access enforcement on /settings and /api/config.

Signature verification is exercised for real against an in-test RSA keypair:
the JWKS client is stubbed to return the matching public key, and tokens are
signed with PyJWT, so allow/deny outcomes come from genuine `jwt.decode`
validation (signature, exp, aud, iss) rather than a mocked verifier.
"""

import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

import app.cf_access as cf_access
import app.config as config_module

TEAM = "testteam"
ISSUER = "https://testteam.cloudflareaccess.com"
AUD = "test-aud-tag"
HEADER = cf_access.ACCESS_JWT_HEADER


# ── helpers ────────────────────────────────────────────────────────────────────

def _make_token(private_key, *, aud=AUD, iss=ISSUER, exp_offset=3600, kid="test-kid"):
    now = int(time.time())
    payload = {
        "aud": aud,
        "iss": iss,
        "iat": now,
        "exp": now + exp_offset,
        "email": "operator@example.com",
        "sub": "user-123",
    }
    return jwt.encode(payload, private_key, algorithm="RS256", headers={"kid": kid})


class _StubSigningKey:
    def __init__(self, key):
        self.key = key


class _StubJWKClient:
    """Returns a fixed public key for any token (real signature check still runs)."""

    def __init__(self, public_key):
        self._public_key = public_key

    def get_signing_key_from_jwt(self, token):
        return _StubSigningKey(self._public_key)


@pytest.fixture
def rsa_key():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture
def enforced_client(monkeypatch, tmp_path, rsa_key):
    """App with Access enforcement ON and the JWKS client stubbed to rsa_key."""
    monkeypatch.delenv("ABS_HOST", raising=False)
    monkeypatch.delenv("ABS_TOKEN", raising=False)
    monkeypatch.setenv("CF_ACCESS_TEAM_DOMAIN", TEAM)
    monkeypatch.setenv("CF_ACCESS_AUD", AUD)
    monkeypatch.setattr(config_module, "_CONFIG_PATH", str(tmp_path / "config.json"))
    public_key = rsa_key.public_key()
    monkeypatch.setattr(cf_access, "_get_jwk_client", lambda certs_url: _StubJWKClient(public_key))

    from app.main import app
    with TestClient(app) as c:
        yield c


@pytest.fixture
def unset_client(monkeypatch, tmp_path):
    """App with Access enforcement OFF (env vars unset) — passthrough."""
    monkeypatch.delenv("ABS_HOST", raising=False)
    monkeypatch.delenv("ABS_TOKEN", raising=False)
    monkeypatch.delenv("CF_ACCESS_TEAM_DOMAIN", raising=False)
    monkeypatch.delenv("CF_ACCESS_AUD", raising=False)
    monkeypatch.setattr(config_module, "_CONFIG_PATH", str(tmp_path / "config.json"))

    from app.main import app
    with TestClient(app) as c:
        yield c


# ── unit: helpers ──────────────────────────────────────────────────────────────

@pytest.mark.parametrize("raw,expected", [
    ("testteam", "testteam.cloudflareaccess.com"),
    ("testteam.cloudflareaccess.com", "testteam.cloudflareaccess.com"),
    ("https://testteam.cloudflareaccess.com", "testteam.cloudflareaccess.com"),
    ("https://testteam.cloudflareaccess.com/", "testteam.cloudflareaccess.com"),
    ("  testteam  ", "testteam.cloudflareaccess.com"),
    ("", ""),
])
def test_normalize_team_domain(raw, expected):
    assert cf_access._normalize_team_domain(raw) == expected


def test_is_access_enforced_requires_both(monkeypatch):
    monkeypatch.delenv("CF_ACCESS_TEAM_DOMAIN", raising=False)
    monkeypatch.delenv("CF_ACCESS_AUD", raising=False)
    assert cf_access.is_access_enforced() is False
    monkeypatch.setenv("CF_ACCESS_TEAM_DOMAIN", TEAM)
    assert cf_access.is_access_enforced() is False  # AUD still missing
    monkeypatch.setenv("CF_ACCESS_AUD", AUD)
    assert cf_access.is_access_enforced() is True


# ── allow ───────────────────────────────────────────────────────────────────────

def test_settings_allowed_with_valid_token(enforced_client, rsa_key):
    token = _make_token(rsa_key)
    resp = enforced_client.get("/settings", headers={HEADER: token})
    assert resp.status_code == 200
    assert "<select" in resp.text


def test_get_config_allowed_with_valid_token(enforced_client, rsa_key):
    token = _make_token(rsa_key)
    resp = enforced_client.get("/api/config", headers={HEADER: token})
    assert resp.status_code == 200
    assert resp.json()["layout"] == "landscape-classic"


def test_post_config_allowed_with_valid_token(enforced_client, rsa_key):
    token = _make_token(rsa_key)
    resp = enforced_client.post(
        "/api/config",
        headers={HEADER: token},
        json={"layout": "portrait-dogear", "theme": "parchment",
              "label": "Now Listening", "corners": "square"},
    )
    assert resp.status_code == 200
    assert resp.json()["saved"] is True


# ── deny ────────────────────────────────────────────────────────────────────────

def test_missing_token_rejected_401(enforced_client):
    for method, path in [("get", "/settings"), ("get", "/api/config")]:
        resp = getattr(enforced_client, method)(path)
        assert resp.status_code == 401, path
    resp = enforced_client.post("/api/config", json={})
    assert resp.status_code == 401


def test_invalid_signature_rejected_403(enforced_client):
    # Signed by a different key than the one the JWKS stub returns.
    other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    token = _make_token(other_key)
    resp = enforced_client.get("/api/config", headers={HEADER: token})
    assert resp.status_code == 403


def test_expired_token_rejected_403(enforced_client, rsa_key):
    token = _make_token(rsa_key, exp_offset=-3600)
    resp = enforced_client.get("/settings", headers={HEADER: token})
    assert resp.status_code == 403


def test_wrong_aud_rejected_403(enforced_client, rsa_key):
    token = _make_token(rsa_key, aud="some-other-application")
    resp = enforced_client.get("/api/config", headers={HEADER: token})
    assert resp.status_code == 403


def test_wrong_issuer_rejected_403(enforced_client, rsa_key):
    token = _make_token(rsa_key, iss="https://evil.cloudflareaccess.com")
    resp = enforced_client.get("/api/config", headers={HEADER: token})
    assert resp.status_code == 403


def test_malformed_token_rejected_403(enforced_client):
    resp = enforced_client.get("/api/config", headers={HEADER: "not-a-jwt"})
    assert resp.status_code == 403


# ── unset-env passthrough ───────────────────────────────────────────────────────

def test_settings_open_when_unset(unset_client):
    resp = unset_client.get("/settings")
    assert resp.status_code == 200


def test_config_api_open_when_unset(unset_client):
    assert unset_client.get("/api/config").status_code == 200
    resp = unset_client.post("/api/config", json={
        "layout": "landscape-classic", "theme": "light",
        "label": "Reading", "corners": "rounded"})
    assert resp.status_code == 200


# ── public endpoints stay open even when enforcement is ON ──────────────────────

def test_public_card_not_gated_under_enforcement(enforced_client):
    assert enforced_client.get("/card").status_code == 200
    assert enforced_client.get("/health").status_code == 200
