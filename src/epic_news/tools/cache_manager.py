"""
Cache manager for API results to reduce rate limits and improve performance.

This module provides a simple file-based caching system for financial data API calls
to avoid repeated requests and respect rate limits.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

from loguru import logger


class CacheManager:
    """Simple file-based cache manager for API results."""

    def __init__(self, cache_dir: str = "cache", default_ttl: int = 3600):
        """
        Initialize the cache manager.

        Args:
            cache_dir: Directory to store cache files
            default_ttl: Default time-to-live in seconds (1 hour default)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.default_ttl = default_ttl

    def _get_cache_path(self, key: str) -> Path:
        """Get the cache file path for a given key."""
        # Create a safe filename from the key
        safe_key = "".join(c for c in key if c.isalnum() or c in ("-", "_", ".")).rstrip()
        return self.cache_dir / f"{safe_key}.json"

    def get(self, key: str, ttl: Optional[int] = None) -> Optional[Any]:
        """
        Get a value from cache if it exists and hasn't expired.

        Args:
            key: Cache key
            ttl: Time-to-live in seconds (uses default if None)

        Returns:
            Cached value if found and valid, None otherwise
        """
        cache_path = self._get_cache_path(key)

        if not cache_path.exists():
            return None

        try:
            with open(cache_path) as f:
                cache_data = json.load(f)

            # Check if cache has expired
            cached_time = datetime.fromisoformat(cache_data["timestamp"])
            ttl_seconds = ttl or self.default_ttl

            if datetime.now() - cached_time > timedelta(seconds=ttl_seconds):
                # Cache expired, remove file
                cache_path.unlink()
                return None

            return cache_data["data"]

        except (json.JSONDecodeError, KeyError, ValueError):
            # Invalid cache file, remove it
            cache_path.unlink()
            return None

    def set(self, key: str, value: Any) -> None:
        """
        Store a value in cache.

        Args:
            key: Cache key
            value: Value to cache
        """
        cache_path = self._get_cache_path(key)

        cache_data = {"timestamp": datetime.now().isoformat(), "data": value}

        try:
            with open(cache_path, "w") as f:
                json.dump(cache_data, f, indent=2)
        except Exception as e:
            # If caching fails, just continue without caching
            logger.warning(f"Failed to cache data for key {key}: {e}")

    def clear(self) -> None:
        """Clear all cached data."""
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()

    def clear_expired(self, ttl: Optional[int] = None) -> int:
        """
        Clear expired cache entries.

        Args:
            ttl: Time-to-live in seconds (uses default if None)

        Returns:
            Number of expired entries removed
        """
        ttl_seconds = ttl or self.default_ttl
        removed_count = 0

        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file) as f:
                    cache_data = json.load(f)

                cached_time = datetime.fromisoformat(cache_data["timestamp"])

                if datetime.now() - cached_time > timedelta(seconds=ttl_seconds):
                    cache_file.unlink()
                    removed_count += 1

            except (json.JSONDecodeError, KeyError, ValueError):
                # Invalid cache file, remove it
                cache_file.unlink()
                removed_count += 1

        return removed_count


# Global cache instance
_cache_manager = None


def get_cache_manager() -> CacheManager:
    """Get the global cache manager instance."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


def cache_api_call(key: str, ttl: int = 3600):
    """
    Decorator to cache API call results.

    Args:
        key: Base cache key (will be combined with function args)
        ttl: Time-to-live in seconds
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            cache = get_cache_manager()

            # Create a unique cache key based on function name and arguments
            cache_key = f"{key}_{func.__name__}_{hash(str(args) + str(sorted(kwargs.items())))}"

            # Try to get from cache first
            cached_result = cache.get(cache_key, ttl)
            if cached_result is not None:
                return cached_result

            # Call the function and cache the result
            result = func(*args, **kwargs)
            cache.set(cache_key, result)

            return result

        return wrapper

    return decorator
