import unittest

from jsonq.api import Q
from jsonq.core.missing import MISSING, MissingMode


class QOperatorTests(unittest.TestCase):
    def test_map_preserves_drop_policy(self) -> None:
        q = Q([1, MISSING, 2], mode=MissingMode.DROP)

        result = q.map(lambda x: x * 10 if x != MISSING else x).list()

        self.assertEqual(result, [10, 20])

    def test_path_respects_missing_policy(self) -> None:
        data = [{"a": 1}, {"b": 2}]

        keep = Q(data, mode=MissingMode.KEEP).path("a").list()
        drop = Q(data, mode=MissingMode.DROP).path("a").list()

        self.assertEqual(keep, [1, MISSING])
        self.assertEqual(drop, [1])
