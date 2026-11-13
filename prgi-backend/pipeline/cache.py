"""
Caching layer — in-memory TTLCache with optional Redis backend.
Falls back gracefully if Redis is unavailable.
"""
from __future__ import annotations
import hashlib
import json
from typing import Any, Optional

from cachetools import TTLCache

_mem_cache: TTLCache = TTLCache(maxsize=5_000, ttl=3600)
CACHE_TTL = 3600

try:
    import redis as _redis_lib
    _rc = _redis_lib.Redis(host="localhost", port=6379, db=0, socket_connect_timeout=1)
    _rc.ping()
    REDIS_AVAILABLE = True
    print("[INFO] Redis cache connected")
except Exception:
    REDIS_AVAILABLE = False
    _rc = None


def _key(title: str, periodicity: str, language: str, state: str) -> str:
    raw = f"{title.lower().strip()}|{periodicity}|{language}|{state}"
    return "prgi:" + hashlib.md5(raw.encode()).hexdigest()


def get_cached(title: str, periodicity: str, language: str, state: str = "") -> Optional[dict]:
    k = _key(title, periodicity, language, state)
    if REDIS_AVAILABLE:
        try:
            val = _rc.get(k)
            if val:
                return json.loads(val)
        except Exception:
            pass
    return _mem_cache.get(k)


def set_cached(title: str, periodicity: str, language: str, state: str, result: dict) -> None:
    k = _key(title, periodicity, language, state)
    if REDIS_AVAILABLE:
        try:
            _rc.setex(k, CACHE_TTL, json.dumps(result))
            return
        except Exception:
            pass
    _mem_cache[k] = result


def cache_stats() -> dict:
    return {
        "backend": "redis" if REDIS_AVAILABLE else "memory",
        "entries": len(_mem_cache),
        "maxsize": _mem_cache.maxsize,
        "ttl_seconds": CACHE_TTL,
    }
