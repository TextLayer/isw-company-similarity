import inspect
import threading
from functools import wraps
from typing import Any

from .redis import RedisCacheService

_shared_cache = None
_cache_lock = threading.Lock()


def _get_shared_cache(**kwargs):
    """
    Get a shared cache instance for using decorators outside of commands.
    Currently, this only supports Redis.

    Args:
        **kwargs: Keyword arguments to pass to the RedisCacheService constructor

    Returns:
        RedisCacheService: The shared cache instance for use in decorators
    """
    global _shared_cache
    if _shared_cache is None:
        with _cache_lock:
            if _shared_cache is None:
                _shared_cache = RedisCacheService(**kwargs)

    return _shared_cache


def cache_result(ttl: int = 3600):
    """
    Decorator to cache the result of any function.
    Supports background caching of generator functions.

    Args:
        ttl: Time to live in seconds. Defaults to 3600 seconds.

    Returns:
        Decorator function
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            """Wrapper function that interacts with the cache in a thread-safe manner."""
            cache = _get_shared_cache()
            cache_key = ""

            def _handle_cached_result(cache_result: dict) -> Any:
                """Convert cached results back into generators"""
                cached_result = cache_result.get("result")
                cached_result_behavior = cache_result.get("result_behavior")

                if cached_result_behavior == "generator":
                    return iter(cached_result)
                else:
                    return cached_result

            def _push_to_cache(result: Any, result_behavior: str = "plain"):
                """Store the value in the cache"""
                data = {
                    "result": result,
                    "result_behavior": result_behavior,
                }
                cache.set(cache_key, value=data, ttl=ttl)

            def _run() -> Any:
                """Cache safely but let natural errors bubble up"""
                try:
                    _set_cache_key()
                    if cache_result := cache.get(cache_key):
                        return _handle_cached_result(cache_result)
                except Exception:
                    pass

                result = func(*args, **kwargs)

                try:
                    if inspect.isgenerator(result):
                        return _spy_on_generator(result)
                    else:
                        _push_to_cache(result)
                        return result
                except RuntimeError:
                    return result
                except Exception:
                    return result

            def _set_cache_key():
                """Serialize all args and kwargs to a string for uniqueness"""
                nonlocal cache_key
                cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"

            def _spy_on_generator(generator: Any):
                """Consume generator and update cache result w/ rolling values"""
                memoized_result = []
                for item in generator:
                    memoized_result.append(item)
                    _push_to_cache(memoized_result, "generator")
                    yield item

            return _run()

        return wrapper

    return decorator
