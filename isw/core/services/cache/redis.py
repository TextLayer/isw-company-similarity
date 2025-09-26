import json
import time
from typing import Any, Optional

import redis

from ....shared.config import config
from ....shared.logging.logger import logger


class RedisCacheService:
    def __del__(self):
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()

    def __init__(self, redis_url: Optional[str] = None):
        url = redis_url or config().redis_url

        if not url:
            try:
                import fakeredis

                self.client = fakeredis.FakeRedis(decode_responses=True)
            except ImportError as e:
                raise ImportError("Do not use use_memory=True if you don't have fakeredis installed for testing") from e
        else:
            self.client = redis.from_url(url, decode_responses=True)
            self.client.ping()

    def get(self, key: str, default: Any = None) -> dict | None:
        """
        Get a value from the cache.

        Args:
            key: The cache key
            default: Default value if key doesn't exist

        Returns:
            The cached value or default
        """
        try:
            if value := self.client.get(key):
                return json.loads(value)

            return default
        except Exception as e:
            logger.error(f"Couldn't retrieve {key} from cache: {e}")
            return default

    def set(
        self,
        key: str,
        value: dict,
        ttl: Optional[int] = 3600,
    ) -> bool:
        """
        Set a key-value pair in the cache.

        Args:
            key: The cache key
            value: A dictionary value to cache
            ttl: Time to live in seconds

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.client.set(key, json.dumps(value), ex=int(time.time()) + ttl)
            return True
        except Exception as e:
            logger.error(f"Couldn't set {key} in cache: {e}")
            return False
