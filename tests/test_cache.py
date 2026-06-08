"""Tests for caching functionality."""

import time
from pathlib import Path
from tempfile import TemporaryDirectory

from motdd.cache import Cache


def test_cache_basic_operations() -> None:
    """Test basic cache operations."""
    with TemporaryDirectory() as tmpdir:
        cache = Cache(cache_dir=Path(tmpdir), ttl_seconds=300)

        # Test set and get
        cache.set("github", "notifications", {"data": [1, 2, 3]})
        result = cache.get("github", "notifications")

        assert result is not None
        assert result["data"] == [1, 2, 3]


def test_cache_with_params() -> None:
    """Test cache with parameters."""
    with TemporaryDirectory() as tmpdir:
        cache = Cache(cache_dir=Path(tmpdir), ttl_seconds=300)

        # Set with params
        cache.set("github", "prs", {"count": 5}, params={"user": "alice"})
        cache.set("github", "prs", {"count": 10}, params={"user": "bob"})

        # Get with different params
        alice_result = cache.get("github", "prs", params={"user": "alice"})
        bob_result = cache.get("github", "prs", params={"user": "bob"})

        assert alice_result["count"] == 5
        assert bob_result["count"] == 10


def test_cache_expiration() -> None:
    """Test cache TTL expiration."""
    with TemporaryDirectory() as tmpdir:
        cache = Cache(cache_dir=Path(tmpdir), ttl_seconds=1)  # 1 second TTL

        cache.set("github", "test", {"data": "fresh"})

        # Should be available immediately
        result = cache.get("github", "test")
        assert result is not None
        assert result["data"] == "fresh"

        # Wait for expiration
        time.sleep(1.1)

        # Should be expired
        result = cache.get("github", "test")
        assert result is None


def test_cache_clear() -> None:
    """Test cache clearing."""
    with TemporaryDirectory() as tmpdir:
        cache = Cache(cache_dir=Path(tmpdir), ttl_seconds=300)

        cache.set("github", "test1", {"data": 1})
        cache.set("gitlab", "test2", {"data": 2})

        # Clear specific provider
        cache.clear("github")

        assert cache.get("github", "test1") is None
        assert cache.get("gitlab", "test2") is not None

        # Clear all
        cache.clear()
        assert cache.get("gitlab", "test2") is None


def test_cache_stats() -> None:
    """Test cache statistics."""
    with TemporaryDirectory() as tmpdir:
        cache = Cache(cache_dir=Path(tmpdir), ttl_seconds=300)

        cache.set("github", "test1", {"data": 1})
        cache.set("github", "test2", {"data": 2})
        cache.set("gitlab", "test3", {"data": 3})

        stats = cache.get_stats()
        assert stats["total_entries"] == 3
        assert stats["valid_entries"] >= 0
        assert stats["cache_dir"] == str(tmpdir)


def test_cache_missing_file() -> None:
    """Test cache behavior with missing files."""
    with TemporaryDirectory() as tmpdir:
        cache = Cache(cache_dir=Path(tmpdir), ttl_seconds=300)

        # Try to get non-existent cache
        result = cache.get("github", "nonexistent")
        assert result is None


def test_cache_persistent_metadata() -> None:
    """Test that metadata persists across cache instances."""
    with TemporaryDirectory() as tmpdir:
        # Create cache and add entry
        cache1 = Cache(cache_dir=Path(tmpdir), ttl_seconds=300)
        cache1.set("github", "test", {"data": "value"})

        # Create new cache instance with same directory
        cache2 = Cache(cache_dir=Path(tmpdir), ttl_seconds=300)

        # Should still have the entry
        result = cache2.get("github", "test")
        assert result is not None
        assert result["data"] == "value"
