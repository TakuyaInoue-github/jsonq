import unittest

from jsonq.core.missing import MISSING, MissingMode
from jsonq.core.value import JsonValue
from jsonq.operators import access, missing, pipe, sequence


class OperatorModuleTests(unittest.TestCase):
    def _json(self, value):
        return JsonValue(value, mode=MissingMode.DROP)

    def test_access_getitem_operator(self) -> None:
        op = access.getitem("a")
        result = op(self._json({"a": 10}))
        self.assertEqual(result.value, 10)

    def test_access_path_operator(self) -> None:
        data = [{"a": 1}, {"b": 2}]
        op = access.path("a")
        keep = op(JsonValue(data, mode=MissingMode.KEEP)).value
        drop = op(JsonValue(data, mode=MissingMode.DROP)).value
        self.assertEqual(keep, [1, MISSING])
        self.assertEqual(drop, [1])

    def test_seq_map_and_flat_compose(self) -> None:
        combined = pipe(sequence.map_items(lambda x: [x, x]), sequence.flat())
        out = combined(self._json([1, 2, 3]))
        self.assertEqual(out.value, [1, 1, 2, 2, 3, 3])

    def test_missing_ops(self) -> None:
        value = JsonValue(MISSING, mode=MissingMode.DROP)
        filled = missing.fill(0)(value)
        kept = missing.keep()(value)
        self.assertEqual(filled.value, 0)
        self.assertIs(kept.mode, MissingMode.KEEP)
