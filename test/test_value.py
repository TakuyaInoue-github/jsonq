import unittest

from jsonq.core.value import JsonValue
from jsonq.core.missing import MissingMode


class JsonValueReplaceTests(unittest.TestCase):
    def test_no_changes_returns_same_instance(self) -> None:
        original = JsonValue({"a": 1}, mode=MissingMode.DROP, strict=True)

        self.assertIs(original.replace(), original)
        self.assertIs(original.with_mode(MissingMode.DROP), original)

    def test_updates_selected_fields(self) -> None:
        original = JsonValue({"a": 1}, mode=MissingMode.DROP, strict=False)

        swapped_value = original.replace(value={"a": 99})
        self.assertEqual(swapped_value.value, {"a": 99})
        self.assertIs(swapped_value.mode, MissingMode.DROP)
        self.assertFalse(swapped_value.strict)

        toggled_mode = original.replace(mode=MissingMode.KEEP)
        self.assertIs(toggled_mode.mode, MissingMode.KEEP)
        self.assertEqual(toggled_mode.value, {"a": 1})
        self.assertFalse(toggled_mode.strict)
