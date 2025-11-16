from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, cast

from .missing import is_missing

if TYPE_CHECKING:
    from .core_types import JsonElement


def coerce_json_element(value: object) -> JsonElement:
    """Ensure arbitrary Python objects conform to the JsonElement contract."""
    from .value import JsonValue  # Local import to avoid circular dependency

    if isinstance(value, JsonValue):
        return value.unwrap()
    if is_missing(value):
        return cast("JsonElement", value)
    if value is None or isinstance(value, bool | int | float | str):
        return cast("JsonElement", value)
    if isinstance(value, list | tuple):
        return cast("JsonElement", _coerce_sequence(value))
    if isinstance(value, Mapping):
        return cast("JsonElement", _coerce_mapping(value))
    msg = f"Unsupported JSON element type: {type(value).__name__}"
    raise TypeError(msg)


def _coerce_sequence(seq: Sequence[object]) -> list[JsonElement]:
    """Recursively coerce list/tuple inputs."""
    return [coerce_json_element(item) for item in seq]


def _coerce_mapping(mapping: Mapping[object, object]) -> dict[str, JsonElement]:
    """Recursively coerce dict-like inputs, enforcing str keys."""
    coerced: dict[str, JsonElement] = {}
    for key, item in mapping.items():
        if not isinstance(key, str):
            msg = f"JSON object keys must be str, got {type(key).__name__}"
            raise TypeError(msg)
        coerced[key] = coerce_json_element(item)
    return coerced
