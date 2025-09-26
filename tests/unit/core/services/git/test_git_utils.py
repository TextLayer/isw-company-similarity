import os
import unittest

from isw.core.utils.git import determine_working_dir

fixture = determine_working_dir(os.path.join(os.path.dirname(__file__), "fixtures"))


class TestGitUtils(unittest.TestCase):
    def test_determine_working_dir_without_indicators(self):
        assert fixture == determine_working_dir(fixture)

    def test_determine_working_dir_with_empty_indicators(self):
        assert fixture == determine_working_dir(fixture, [])

    def test_determine_working_dir_with_single_indicator(self):
        dir = determine_working_dir(fixture, [{"is_folder": False, "name": "mark-sub.txt"}])

        assert dir == os.path.join(fixture, "fixture-sub/fixture-mark")

    def test_determine_working_dir_with_multiple_indicators(self):
        dir = determine_working_dir(
            fixture,
            [
                {"is_folder": True, "name": "fixture-mark"},
                {"is_folder": False, "name": "mark.txt"},
            ],
        )

        assert dir == os.path.join(fixture, "fixture-sub")
