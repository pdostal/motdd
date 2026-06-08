"""Caching functionality for MOTDD."""

import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


class Cache:
    """Disk-based cache with TTL support."""

    def __init__(self, cache_dir: Path | None = None, ttl_seconds: int = 300):
        """
        Initialize cache.

        Args:
            cache_dir: Cache directory path (defaults to ~/.cache/motdd)
            ttl_seconds: Time-to-live for cache entries in seconds (default 5 minutes)
        """
        if cache_dir is None:
            cache_dir = Path.home() / ".cache" / "motdd"

        self.cache_dir = cache_dir
        self.ttl_seconds = ttl_seconds
        self.metadata_file = cache_dir / "metadata.json"

        # Create cache directory if it doesn't exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Load or initialize metadata
        self._metadata = self._load_metadata()

    def _load_metadata(self) -> dict:
        """Load cache metadata."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file) as f:
                    return json.load(f)
            except (OSError, json.JSONDecodeError):
                return {}
        return {}

    def _save_metadata(self) -> None:
        """Save cache metadata."""
        try:
            with open(self.metadata_file, "w") as f:
                json.dump(self._metadata, f, indent=2)
        except OSError:
            pass  # Fail silently on write errors

    def _get_cache_key(self, provider: str, endpoint: str, params: dict | None = None) -> str:
        """
        Generate cache key.

        Args:
            provider: Provider name
            endpoint: Endpoint name
            params: Optional parameters dict

        Returns:
            Cache key string
        """
        # Create a stable string representation
        key_parts = [provider, endpoint]

        if params:
            # Sort params for consistent keys
            param_str = json.dumps(params, sort_keys=True)
            key_parts.append(param_str)

        key_string = ":".join(key_parts)

        # Use hash to keep filename reasonable length
        return hashlib.sha256(key_string.encode()).hexdigest()[:16]

    def _get_cache_path(self, provider: str, cache_key: str) -> Path:
        """
        Get cache file path.

        Args:
            provider: Provider name
            cache_key: Cache key

        Returns:
            Path to cache file
        """
        provider_dir = self.cache_dir / provider
        provider_dir.mkdir(exist_ok=True)
        return provider_dir / f"{cache_key}.json"

    def get(self, provider: str, endpoint: str, params: dict | None = None) -> Any | None:
        """
        Get value from cache.

        Args:
            provider: Provider name
            endpoint: Endpoint name
            params: Optional parameters

        Returns:
            Cached value or None if not found or expired
        """
        cache_key = self._get_cache_key(provider, endpoint, params)
        cache_path = self._get_cache_path(provider, cache_key)

        if not cache_path.exists():
            return None

        # Check if cache entry is expired
        metadata_key = f"{provider}:{cache_key}"
        if metadata_key in self._metadata:
            timestamp_str = self._metadata[metadata_key].get("timestamp")
            if timestamp_str:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str)
                    age = datetime.now() - timestamp

                    if age.total_seconds() > self.ttl_seconds:
                        # Expired - remove it
                        self._remove_cache_file(cache_path, metadata_key)
                        return None
                except (ValueError, KeyError):
                    pass

        # Load and return cached data
        try:
            with open(cache_path) as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            # Invalid cache file - remove it
            self._remove_cache_file(cache_path, metadata_key)
            return None

    def set(self, provider: str, endpoint: str, value: Any, params: dict | None = None) -> None:
        """
        Set value in cache.

        Args:
            provider: Provider name
            endpoint: Endpoint name
            value: Value to cache
            params: Optional parameters
        """
        cache_key = self._get_cache_key(provider, endpoint, params)
        cache_path = self._get_cache_path(provider, cache_key)

        # Save data
        try:
            with open(cache_path, "w") as f:
                json.dump(value, f, indent=2)

            # Update metadata
            metadata_key = f"{provider}:{cache_key}"
            self._metadata[metadata_key] = {
                "timestamp": datetime.now().isoformat(),
                "endpoint": endpoint,
                "provider": provider,
            }
            self._save_metadata()
        except OSError:
            pass  # Fail silently on write errors

    def _remove_cache_file(self, cache_path: Path, metadata_key: str) -> None:
        """Remove a cache file and its metadata."""
        try:
            cache_path.unlink()
        except OSError:
            pass

        if metadata_key in self._metadata:
            del self._metadata[metadata_key]
            self._save_metadata()

    def clear(self, provider: str | None = None) -> None:
        """
        Clear cache.

        Args:
            provider: Optional provider name to clear only that provider's cache
        """
        if provider:
            # Clear specific provider
            provider_dir = self.cache_dir / provider
            if provider_dir.exists():
                shutil.rmtree(provider_dir)

            # Remove metadata for this provider
            keys_to_remove = [k for k in self._metadata if k.startswith(f"{provider}:")]
            for key in keys_to_remove:
                del self._metadata[key]
            self._save_metadata()
        else:
            # Clear all cache
            if self.cache_dir.exists():
                shutil.rmtree(self.cache_dir)
                self.cache_dir.mkdir(parents=True, exist_ok=True)
            self._metadata = {}
            self._save_metadata()

    def get_stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        total_entries = len(self._metadata)
        expired_count = 0
        total_size = 0

        now = datetime.now()

        for metadata_key, entry in self._metadata.items():
            # Check expiration
            try:
                timestamp = datetime.fromisoformat(entry["timestamp"])
                age = now - timestamp
                if age.total_seconds() > self.ttl_seconds:
                    expired_count += 1
            except (ValueError, KeyError):
                pass

        # Calculate total cache size
        for provider_dir in self.cache_dir.iterdir():
            if provider_dir.is_dir():
                for cache_file in provider_dir.glob("*.json"):
                    try:
                        total_size += cache_file.stat().st_size
                    except OSError:
                        pass

        return {
            "total_entries": total_entries,
            "expired_entries": expired_count,
            "valid_entries": total_entries - expired_count,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "cache_dir": str(self.cache_dir),
            "ttl_seconds": self.ttl_seconds,
        }
