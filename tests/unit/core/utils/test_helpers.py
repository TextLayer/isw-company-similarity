import unittest

from isw.core.utils.helpers import decode, flatten


class TestHelpers(unittest.TestCase):
    def test_flatten_with_nested_lists(self):
        assert flatten([[1, 2], [3, 4]]) == [1, 2, 3, 4]

    def test_flatten_with_empty_lists(self):
        assert flatten([[], [1, 2], []]) == [1, 2]

    def test_flatten_with_single_list(self):
        assert flatten([[1, 2]]) == [1, 2]

    def test_flatten_with_single_item(self):
        assert flatten([1]) == [1]

    def test_decode_with_list(self):
        assert decode(["a%20b", "c%20d"]) == ["a b", "c d"]

    def test_decode_with_single_item(self):
        assert decode("a%20b") == "a b"

    def test_decode_with_empty_string(self):
        assert decode("") == ""

    def test_decode_with_none(self):
        assert decode(None) == ""

    def test_decode_with_empty_list(self):
        assert decode([]) == []
