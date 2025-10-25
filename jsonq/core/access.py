from __future__ import annotations
from typing import Any, Iterable, List, Sequence, Union

from .missing import MISSING, MissingMode, is_missing
from .value import JsonValue


def _flatten_once(seq: Iterable[Any], *, drop_missing: bool) -> List[Any]:
    out: List[Any] = []
    for item in seq:
        if isinstance(item, list):
            out.extend(item)
        elif drop_missing and is_missing(item):
            continue
        else:
            out.append(item)
    return out


def get_item(v: JsonValue, key: Union[str, int, slice]) -> Any:
    """Vectorized safe item access based on current MissingMode."""

    val = v.unwrap()
    mode = v._mode  # internal access is intentional

    def handle_missing(exc: Exception | None = None):
        if mode is MissingMode.RAISE:
            if isinstance(exc, Exception):
                raise exc
            raise KeyError("missing")
        return MISSING

    if isinstance(val, list):
        if isinstance(key, (int, slice)):
            try:
                return val[key]
            except Exception as exc:
                return handle_missing(exc)
        if isinstance(key, str):
            out: List[Any] = []
            missing_seen = False
            for el in val:
                if isinstance(el, dict):
                    result = el.get(key, MISSING)
                else:
                    result = MISSING
                if is_missing(result):
                    missing_seen = True
                out.append(result)
            if missing_seen and mode is MissingMode.RAISE:
                raise KeyError(key)
            drop = mode is MissingMode.DROP
            return _flatten_once(out, drop_missing=drop)
        return handle_missing()

    if isinstance(val, dict):
        if isinstance(key, str):
            if key in val:
                return val[key]
            return handle_missing()
        return handle_missing()

    return handle_missing()


def apply_path(v: JsonValue, tokens: Sequence[Union[str, int]]) -> Any:
    cur: Any = v
    for token in tokens:
        if isinstance(cur, JsonValue):
            cur = get_item(cur, token)
        else:
            cur = get_item(JsonValue(cur, mode=v._mode, strict=v._strict), token)
        if is_missing(cur):
            break
    return cur
