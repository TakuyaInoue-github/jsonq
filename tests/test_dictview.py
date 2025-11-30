from __future__ import annotations

from jsonq.core.dictview import DictView
from jsonq.core.missing import MissingMode
from jsonq.core.value import JsonValue


def test_dictview_keys_handles_non_dict() -> None:
    view = DictView(JsonValue({"a": 1}, mode=MissingMode.DROP))
    assert set(view.keys()) == {"a"}

    non_dict = DictView(JsonValue([1, 2], mode=MissingMode.DROP))
    assert non_dict.keys() == []
