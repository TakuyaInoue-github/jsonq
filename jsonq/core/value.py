from __future__ import annotations
from typing import Any, List

from .missing import MISSING, MissingMode, is_missing


class JsonValue:
    """Immutable holder for a JSON-ish value plus missing policy."""

    __slots__ = ("_v", "_mode", "_strict")

    def __init__(self, v: Any, *, mode: MissingMode, strict: bool):
        self._v = v
        self._mode = mode
        self._strict = strict

    def unwrap(self) -> Any:
        return self._v

    def with_mode(self, mode: MissingMode) -> JsonValue:
        return JsonValue(self._v, mode=mode, strict=self._strict)

    @staticmethod
    def is_missing(x: Any) -> bool:
        return is_missing(x)

    def get(self, default: Any = None) -> Any:
        return self._v if not is_missing(self._v) else default

    def as_list(self) -> List[Any]:
        if is_missing(self._v):
            return []
        if isinstance(self._v, list):
            return self._v
        return [self._v]

    def getitem(self, key: Any) -> JsonValue:
        from .access import get_item

        value = get_item(self, key)
        return JsonValue(value, mode=self._mode, strict=self._strict)

    def assert_present(self) -> None:
        if is_missing(self._v):
            raise ValueError("Missing value present")

    def fill_missing(self, value: Any) -> JsonValue:
        replacement = value if is_missing(self._v) else self._v
        return JsonValue(replacement, mode=self._mode, strict=self._strict)
