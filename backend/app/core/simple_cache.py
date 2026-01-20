import time
from typing import Any, Dict, Tuple

_CACHE: Dict[str, Tuple[float, Any]] = {}

def get(key: str):
    item = _CACHE.get(key)
    if not item:
        return None
    expires_at, value = item
    if time.time() > expires_at:
        _CACHE.pop(key, None)
        return None
    return value

def set(key: str, value: Any, ttl_seconds: int):
    _CACHE[key] = (time.time() + ttl_seconds, value)
