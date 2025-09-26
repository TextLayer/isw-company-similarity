import unittest

from isw.core.utils.keyword import Keyword


class TestKeyword(unittest.TestCase):
    def test_sanitization(self):
        kf = Keyword('Hello, "world"! How are you?')
        assert kf.clean() == "Hello world How are you"

    def test_singular_phrase_extraction(self):
        kf = Keyword('Hello, "world"! How are you?')
        assert kf.split_into_phrases() == ["world"]

    def test_multiple_phrases_extraction(self):
        kf = Keyword('Hello, "world"! How are "you "?')
        assert kf.split_into_phrases() == ["world", "you"]
