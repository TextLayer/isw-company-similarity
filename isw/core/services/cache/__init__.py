from .decorator import cache_result
from .redis import RedisCacheService

CacheService = RedisCacheService

__all__ = ["CacheService", "cache_result"]
