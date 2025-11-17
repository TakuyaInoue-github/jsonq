from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

from .core_types import JsonElement
from .missing import MISSING, MissingMode, is_missing

if TYPE_CHECKING:
    from .value import JsonValue


def _flatten_once(seq: list[JsonElement], *, drop_missing: bool) -> list[JsonElement]:
    out: list[JsonElement] = []
    for item in seq:
        if isinstance(item, list):
            out.extend(item)
        elif drop_missing and is_missing(item):
            continue
        else:
            out.append(item)
    return out


def _handle_missing(mode: MissingMode, *, exc: Exception | None = None) -> JsonElement:
    if mode is MissingMode.RAISE:
        if exc is not None:
            raise exc
        raise KeyError("missing")
    return MISSING


def get_item(v: JsonValue, key: str | int | slice) -> JsonElement:
    """Vectorized safe item access based on current MissingMode."""
    effective_mode = MissingMode.RAISE if v.strict else v.mode
    drop_missing = v.mode is MissingMode.DROP
    return _get_item_from_element(v.value, key, mode=effective_mode, drop_missing=drop_missing)


def apply_path(v: JsonValue, tokens: tuple[str | int, ...]) -> JsonElement:
    """Apply a tokenized path expression to a JsonValue."""
    effective_mode = MissingMode.RAISE if v.strict else v.mode
    drop_missing = v.mode is MissingMode.DROP
    current: JsonElement = v.value
    for token in tokens:
        current = _get_item_from_element(current, token, mode=effective_mode, drop_missing=drop_missing)
        if is_missing(current):
            break
    return current


def _get_item_from_element(
    value: JsonElement,
    key: str | int | slice,
    *,
    mode: MissingMode,
    drop_missing: bool,
) -> JsonElement:
    if is_missing(value):
        return _handle_missing(mode)
    if isinstance(key, str):
        return _get_by_key(value, key, mode=mode, drop_missing=drop_missing)
    if isinstance(key, slice):
        return _get_by_slice(value, key, mode=mode, drop_missing=drop_missing)
    return _get_by_index(value, key, mode=mode)


def _get_by_key(value: JsonElement, key: str, *, mode: MissingMode, drop_missing: bool) -> JsonElement:
    if isinstance(value, dict):
        if key in value:
            return value[key]
        return _handle_missing(mode, exc=KeyError(key))
    if isinstance(value, list):
        return _vectorized_from_list(value, key, mode=mode, drop_missing=drop_missing)
    return _handle_missing(mode, exc=KeyError(key))


def _get_by_index(value: JsonElement, key: int, *, mode: MissingMode) -> JsonElement:
    if not isinstance(value, list):
        return _handle_missing(mode, exc=IndexError(key))
    if not value:
        return _handle_missing(mode, exc=IndexError(key))
    try:
        return value[key]
    except IndexError:
        return _handle_missing(mode, exc=IndexError(key))


def _get_by_slice(
    value: JsonElement,
    key: slice,
    *,
    mode: MissingMode,
    drop_missing: bool,
) -> JsonElement:
    if not isinstance(value, list):
        return _handle_missing(mode, exc=TypeError("slice access requires a list"))
    try:
        sliced = value[key]
    except ValueError as exc:
        return _handle_missing(mode, exc=exc)
    return _drop_missing(sliced, drop_missing)


def _vectorized_from_list(
    seq: Iterable[JsonElement],
    key: str | int | slice,
    *,
    mode: MissingMode,
    drop_missing: bool,
) -> JsonElement:
    items = [_get_item_from_element(item, key, mode=mode, drop_missing=drop_missing) for item in seq]
    return _flatten_once(items, drop_missing=drop_missing)


def _drop_missing(seq: list[JsonElement], drop_missing: bool) -> list[JsonElement]:
    if not drop_missing:
        return list(seq)
    return [item for item in seq if not is_missing(item)]
