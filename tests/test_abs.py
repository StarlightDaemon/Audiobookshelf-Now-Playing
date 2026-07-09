"""
Mocked httpx integration tests for app.abs.AbsClient.

No real network calls are made — AbsClient's internal httpx.AsyncClient.get is
monkeypatched per-test with a canned response.
"""

import asyncio
import time

import pytest

from app.abs import AbsClient, is_configured


@pytest.fixture
def abs_env(monkeypatch):
    monkeypatch.setenv("ABS_HOST", "http://abs.local:13378")
    monkeypatch.setenv("ABS_TOKEN", "test-token")


class _FakeResponse:
    def __init__(self, json_data=None, status_code=200, content=b"", headers=None):
        self._json_data = json_data
        self.status_code = status_code
        self.content = content
        self.headers = headers or {}

    def json(self):
        return self._json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


def _session(item_id="item-1", media_type="book", updated_at=None):
    return {
        "libraryItemId": item_id,
        "mediaType": media_type,
        "currentTime": 120,
        "duration": 3600,
        "updatedAt": updated_at,
    }


# ── is_configured() ────────────────────────────────────────────────────────

def test_is_configured_false_when_missing(monkeypatch):
    monkeypatch.delenv("ABS_HOST", raising=False)
    monkeypatch.delenv("ABS_TOKEN", raising=False)
    assert is_configured() is False


def test_is_configured_false_for_placeholder_token(monkeypatch):
    monkeypatch.setenv("ABS_HOST", "http://abs.local:13378")
    monkeypatch.setenv("ABS_TOKEN", "your-abs-api-token-here")
    assert is_configured() is False


def test_is_configured_true(abs_env):
    assert is_configured() is True


# ── get_current_session() ────────────────────────────────────────────────────

def test_get_current_session_returns_latest_book_session(abs_env):
    client = AbsClient()
    fake = _FakeResponse(json_data={"sessions": [
        _session("item-1", "book"),
        _session("item-2", "podcast"),
    ]})

    async def fake_get(*args, **kwargs):
        return fake

    client._client.get = fake_get
    result = asyncio.run(client.get_current_session())
    assert result["libraryItemId"] == "item-1"


def test_get_current_session_filters_podcasts(abs_env):
    client = AbsClient()
    fake = _FakeResponse(json_data={"sessions": [_session("item-2", "podcast")]})

    async def fake_get(*args, **kwargs):
        return fake

    client._client.get = fake_get
    result = asyncio.run(client.get_current_session())
    assert result is None


def test_get_current_session_none_when_no_sessions(abs_env):
    client = AbsClient()
    fake = _FakeResponse(json_data={"sessions": []})

    async def fake_get(*args, **kwargs):
        return fake

    client._client.get = fake_get
    result = asyncio.run(client.get_current_session())
    assert result is None


def test_get_current_session_filters_stale_session(abs_env):
    client = AbsClient()
    two_hours_ago_ms = (time.time() - 7200) * 1000
    fake = _FakeResponse(json_data={"sessions": [
        _session("item-1", "book", updated_at=two_hours_ago_ms),
    ]})

    async def fake_get(*args, **kwargs):
        return fake

    client._client.get = fake_get
    result = asyncio.run(client.get_current_session(max_age_seconds=3600))
    assert result is None


def test_get_current_session_keeps_recent_session(abs_env):
    client = AbsClient()
    one_minute_ago_ms = (time.time() - 60) * 1000
    fake = _FakeResponse(json_data={"sessions": [
        _session("item-1", "book", updated_at=one_minute_ago_ms),
    ]})

    async def fake_get(*args, **kwargs):
        return fake

    client._client.get = fake_get
    result = asyncio.run(client.get_current_session(max_age_seconds=3600))
    assert result is not None
    assert result["libraryItemId"] == "item-1"


def test_get_current_session_no_filter_when_max_age_disabled(abs_env):
    client = AbsClient()
    a_week_ago_ms = (time.time() - 7 * 86400) * 1000
    fake = _FakeResponse(json_data={"sessions": [
        _session("item-1", "book", updated_at=a_week_ago_ms),
    ]})

    async def fake_get(*args, **kwargs):
        return fake

    client._client.get = fake_get
    result = asyncio.run(client.get_current_session(max_age_seconds=0))
    assert result is not None


def test_get_current_session_no_filter_when_updated_at_missing(abs_env):
    client = AbsClient()
    fake = _FakeResponse(json_data={"sessions": [
        _session("item-1", "book", updated_at=None),
    ]})

    async def fake_get(*args, **kwargs):
        return fake

    client._client.get = fake_get
    result = asyncio.run(client.get_current_session(max_age_seconds=3600))
    assert result is not None


def test_get_current_session_raises_on_http_error(abs_env):
    client = AbsClient()
    fake = _FakeResponse(status_code=500)

    async def fake_get(*args, **kwargs):
        return fake

    client._client.get = fake_get
    with pytest.raises(RuntimeError):
        asyncio.run(client.get_current_session())


# ── get_item() ────────────────────────────────────────────────────────────────

def test_get_item_returns_json(abs_env):
    client = AbsClient()
    fake = _FakeResponse(json_data={"media": {"metadata": {"title": "Test Book"}}})

    async def fake_get(*args, **kwargs):
        return fake

    client._client.get = fake_get
    result = asyncio.run(client.get_item("item-1"))
    assert result["media"]["metadata"]["title"] == "Test Book"


# ── get_cover_b64() ───────────────────────────────────────────────────────────

def test_get_cover_b64_returns_data_uri(abs_env):
    client = AbsClient()
    fake = _FakeResponse(
        status_code=200,
        content=b"fake-image-bytes",
        headers={"content-type": "image/jpeg"},
    )

    async def fake_get(*args, **kwargs):
        return fake

    client._client.get = fake_get
    result = asyncio.run(client.get_cover_b64("item-1"))
    assert result.startswith("data:image/jpeg;base64,")


def test_get_cover_b64_none_on_non_200(abs_env):
    client = AbsClient()
    fake = _FakeResponse(status_code=404)

    async def fake_get(*args, **kwargs):
        return fake

    client._client.get = fake_get
    result = asyncio.run(client.get_cover_b64("item-1"))
    assert result is None
