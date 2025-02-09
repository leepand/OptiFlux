from diskcache import Cache
from typing import Any, Optional

class ModelCache:
    def __init__(self, cache_dir: str, size_limit: int = 10**9, **kwargs):
        self.cache = Cache(cache_dir, size_limit=size_limit, **kwargs)

    def get(self, key: str) -> Optional[Any]:
        return self.cache.get(key)

    def set(self, key: str, value: Any, expire: int = 3600):
        self.cache.set(key, value, expire=expire)

    def clear(self):
        self.cache.clear()