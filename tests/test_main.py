"""
TestClient integration tests for the FastAPI app: /card, /settings,
/api/config, /health, /status.

ABS_HOST/ABS_TOKEN are intentionally left unset so the app runs in demo mode
(no real network calls) unless a test explicitly sets them.
CONFIG_PATH is redirected to a per-test tmp file so tests never touch the
real on-disk config.
"""

import xml.etree.ElementTree as ET

import pytest
from fastapi.testclient import TestClient

import app.config as config_module


@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.delenv("ABS_HOST", raising=False)
    monkeypatch.delenv("ABS_TOKEN", raising=False)
    monkeypatch.setattr(config_module, "_CONFIG_PATH", str(tmp_path / "config.json"))

    from app.main import app
    with TestClient(app) as c:
        yield c


# ── /health ───────────────────────────────────────────────────────────────────

def test_health_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["demo_mode"] is True


# ── /status ───────────────────────────────────────────────────────────────────

def test_status_demo_mode(client):
    resp = client.get("/status")
    assert resp.status_code == 200
    assert resp.json() == {"playing": False, "demo_mode": True}


# ── /card ─────────────────────────────────────────────────────────────────────

def test_card_default_returns_demo_svg(client):
    resp = client.get("/card")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("image/svg+xml")
    assert resp.text.startswith("<svg")
    ET.fromstring(resp.text)  # well-formed


def test_card_landscape_demo_endpoint(client):
    resp = client.get("/cardlandscapedemo")
    assert resp.status_code == 200
    ET.fromstring(resp.text)


def test_card_portrait_demo_endpoint(client):
    resp = client.get("/cardportraitdemo")
    assert resp.status_code == 200
    ET.fromstring(resp.text)


def test_card_respects_theme_query_param(client):
    resp = client.get("/cardlandscapedemo?theme=light")
    assert resp.status_code == 200
    ET.fromstring(resp.text)


# ── /settings ─────────────────────────────────────────────────────────────────

def test_settings_page_renders(client):
    resp = client.get("/settings")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "<select" in resp.text
    assert "Audiobookshelf Now Playing" in resp.text


# ── /api/config ───────────────────────────────────────────────────────────────

def test_get_config_returns_defaults(client):
    resp = client.get("/api/config")
    assert resp.status_code == 200
    body = resp.json()
    assert body["layout"] == "landscape-classic"
    assert body["theme"] == "github-dark"
    assert body["label"] == "Currently Reading"
    assert body["corners"] == "rounded"


def test_post_config_saves_and_persists(client):
    resp = client.post("/api/config", json={
        "layout": "portrait-dogear", "theme": "parchment",
        "label": "Now Listening", "corners": "square",
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["saved"] is True
    assert body["layout"] == "portrait-dogear"

    # Round trip: a subsequent GET reflects the saved config
    resp2 = client.get("/api/config")
    assert resp2.json()["layout"] == "portrait-dogear"
    assert resp2.json()["theme"] == "parchment"


def test_post_config_rejects_invalid_layout(client):
    resp = client.post("/api/config", json={
        "layout": "not-a-layout", "theme": "light",
        "label": "Reading", "corners": "rounded",
    })
    assert resp.status_code == 400
    assert "error" in resp.json()


def test_post_config_rejects_invalid_theme(client):
    resp = client.post("/api/config", json={
        "layout": "landscape-classic", "theme": "not-a-theme",
        "label": "Reading", "corners": "rounded",
    })
    assert resp.status_code == 400


def test_post_config_rejects_invalid_corners(client):
    resp = client.post("/api/config", json={
        "layout": "landscape-classic", "theme": "light",
        "label": "Reading", "corners": "hexagonal",
    })
    assert resp.status_code == 400


def test_post_config_falls_back_on_blank_label(client):
    resp = client.post("/api/config", json={
        "layout": "landscape-classic", "theme": "light",
        "label": "   ", "corners": "rounded",
    })
    assert resp.status_code == 200
    assert resp.json()["label"] == "Currently Reading"


def test_card_uses_saved_config(client):
    client.post("/api/config", json={
        "layout": "portrait-spine-wide", "theme": "kraft",
        "label": "Listening To", "corners": "square",
    })
    resp = client.get("/card")
    assert resp.status_code == 200
    ET.fromstring(resp.text)
