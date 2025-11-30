from __future__ import annotations

import pytest

from jsonq.core.coerce import coerce_json_element
from jsonq.core.missing import MISSING, MissingMode
from jsonq.core.value import JsonValue


def test_coerce_json_element_handles_wrappers_and_rejects_unsupported() -> None:
    wrapped = JsonValue(coerce_json_element({"a": MISSING}), mode=MissingMode.KEEP)
    assert coerce_json_element(wrapped) == {"a": MISSING}

    with pytest.raises(TypeError, match="JSON object keys must be str"):
        coerce_json_element({1: "x"})
    with pytest.raises(TypeError, match="Unsupported JSON element type"):
        coerce_json_element({"x": {1, 2}})


def test_as_list_respects_keep_drop_and_fill_missing() -> None:
    kept = JsonValue(coerce_json_element([1, MISSING, 2]), mode=MissingMode.KEEP).as_list()
    assert kept[1] is MISSING

    dropped = JsonValue(coerce_json_element([1, MISSING, 2]), mode=MissingMode.DROP).as_list()
    assert dropped == [1, 2]

    filled = JsonValue(coerce_json_element(MISSING), mode=MissingMode.KEEP).fill_missing("x")
    assert filled.as_list() == ["x"]
