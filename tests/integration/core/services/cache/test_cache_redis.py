import time

import pytest

from tests import BaseTest
from isw.core.services.cache import cache_result


class TestCacheRedisIntegration(BaseTest):
    @pytest.mark.integration
    def test_cache_generator(self):
        func_calls = 0

        @cache_result()
        def test_cache_generator():
            nonlocal func_calls
            func_calls += 1
            yield 1
            yield 2
            yield 3

        result = list(test_cache_generator())
        assert result == [1, 2, 3]

        time.sleep(1)
        result = list(test_cache_generator())
        assert result == [1, 2, 3]

        # should skip second invocation
        assert func_calls == 1

    @pytest.mark.integration
    def test_cache_regular_function(self):
        func_calls = 0

        @cache_result()
        def test_cache_regular_function():
            nonlocal func_calls
            func_calls += 1
            return 1

        result = test_cache_regular_function()
        assert result == 1

        time.sleep(1)
        result = test_cache_regular_function()
        assert result == 1

        # should skip second invocation
        assert func_calls == 1

    @pytest.mark.integration
    def test_cache_regular_function_with_error(self):
        func_calls = 0

        @cache_result()
        def test_cache_regular_function_with_error():
            nonlocal func_calls
            func_calls += 1
            raise Exception("test error")

        with pytest.raises(Exception, match="test error"):
            test_cache_regular_function_with_error()
