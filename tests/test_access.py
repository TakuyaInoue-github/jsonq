from __future__ import annotations

from typing import cast

import pytest

from jsonq.core.access import apply_path, get_item
from jsonq.core.core_types import JsonElement
from jsonq.core.missing import MISSING, MissingMode
from jsonq.core.value import JsonValue


def test_dict_lookup() -> None:
    value = JsonValue({"name": "alice"}, mode=MissingMode.DROP)
    assert get_item(value, "name") == "alice"


def test_missing_key_respects_mode() -> None:
    dropped = JsonValue({"name": "alice"}, mode=MissingMode.DROP)
    assert JsonValue.is_missing(get_item(dropped, "age"))

    kept = JsonValue({"name": "alice"}, mode=MissingMode.KEEP)
    assert get_item(kept, "age") is MISSING


def test_vectorized_lookup_drops_missing() -> None:
    value = JsonValue(
        [{"name": "alice"}, {"name": "bob"}, {"age": 30}],
        mode=MissingMode.DROP,
    )
    assert get_item(value, "name") == ["alice", "bob"]


def test_vectorized_lookup_keeps_missing_when_requested() -> None:
    value = JsonValue(
        [{"name": "alice"}, {"age": 30}],
        mode=MissingMode.KEEP,
    )
    result = get_item(value, "name")
    assert isinstance(result, list)
    assert result[0] == "alice"
    assert JsonValue.is_missing(result[1])


def test_index_and_slice() -> None:
    numbers = JsonValue([1, 2, 3, 4], mode=MissingMode.DROP)
    assert get_item(numbers, 1) == 2
    assert get_item(numbers, -1) == 4
    assert get_item(numbers, slice(1, 3)) == [2, 3]


def test_apply_path_vectorizes() -> None:
    data = JsonValue(
        {"users": [{"profile": {"email": "a"}}, {"profile": {"email": "b"}}]},
        mode=MissingMode.DROP,
    )
    result = apply_path(data, ("users", "profile", "email"))
    assert result == ["a", "b"]


def test_apply_path_handles_missing() -> None:
    data = JsonValue({"users": []}, mode=MissingMode.DROP)
    result = apply_path(data, ("users", 0, "profile"))
    assert JsonValue.is_missing(result)


def test_strict_mode_raises_on_missing() -> None:
    value = JsonValue({"name": "alice"}, mode=MissingMode.DROP, strict=True)
    with pytest.raises(KeyError):
        get_item(value, "age")


def test_scalar_to_list() -> None:
    value = JsonValue(10, mode=MissingMode.DROP)
    assert value.as_list() == [10]


def test_missing_to_list() -> None:
    dropped = JsonValue(MISSING, mode=MissingMode.DROP)
    assert dropped.as_list() == []

    kept = JsonValue(MISSING, mode=MissingMode.KEEP)
    assert kept.as_list() == [MISSING]


def test_drop_missing_inside_list() -> None:
    value = JsonValue(cast(JsonElement, [1, MISSING, 2]), mode=MissingMode.DROP)
    assert value.as_list() == [1, 2]
