"""Unit tests for app.cache.TTLCache."""

from app.cache import TTLCache


def test_set_and_get_roundtrip():
    cache = TTLCache(ttl=60)
    cache.set("key", {"a": 1})
    assert cache.get("key") == {"a": 1}


def test_get_missing_key_returns_none():
    cache = TTLCache(ttl=60)
    assert cache.get("missing") is None


def test_entry_expires_after_ttl(monkeypatch):
    fake_now = [1000.0]
    monkeypatch.setattr("app.cache.time.monotonic", lambda: fake_now[0])

    cache = TTLCache(ttl=10)
    cache.set("key", "value")
    assert cache.get("key") == "value"

    fake_now[0] += 11  # advance past ttl
    assert cache.get("key") is None


def test_entry_valid_until_ttl_boundary(monkeypatch):
    fake_now = [1000.0]
    monkeypatch.setattr("app.cache.time.monotonic", lambda: fake_now[0])

    cache = TTLCache(ttl=10)
    cache.set("key", "value")

    fake_now[0] += 5  # still within ttl
    assert cache.get("key") == "value"


def test_expired_entry_is_evicted_from_store(monkeypatch):
    fake_now = [1000.0]
    monkeypatch.setattr("app.cache.time.monotonic", lambda: fake_now[0])

    cache = TTLCache(ttl=10)
    cache.set("key", "value")
    fake_now[0] += 11
    cache.get("key")  # triggers eviction
    assert "key" not in cache._store


def test_invalidate_removes_key():
    cache = TTLCache(ttl=60)
    cache.set("key", "value")
    cache.invalidate("key")
    assert cache.get("key") is None


def test_invalidate_missing_key_is_noop():
    cache = TTLCache(ttl=60)
    cache.invalidate("missing")  # should not raise


def test_falsy_values_are_cached_correctly():
    """A cached False/0/'' must be distinguishable from a cache miss (None)."""
    cache = TTLCache(ttl=60)
    cache.set("key", False)
    assert cache.get("key") is False
