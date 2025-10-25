from __future__ import annotations
from dataclasses import dataclass
from typing import Any, List

from .missing import MISSING, MissingMode, is_missing


@dataclass(frozen=True, slots=True)
class JsonValue:
    """Serializable DTO that couples a JSON value with missing policy."""

    value: Any
    mode: MissingMode
    strict: bool = False

    _SAME = object()

    def unwrap(self) -> Any:
        return self.value

    def with_mode(self, mode: MissingMode) -> JsonValue:
        return self.replace(mode=mode)

    def replace(
        self,
        *,
        value: Any | object = _SAME,
        mode: MissingMode | object = _SAME,
        strict: bool | object = _SAME,
    ) -> JsonValue:
        new_value = self.value if value is JsonValue._SAME else value
        new_mode = self.mode if mode is JsonValue._SAME else mode
        new_strict = self.strict if strict is JsonValue._SAME else strict
        if new_value is self.value and new_mode is self.mode and new_strict is self.strict:
            return self
        return JsonValue(new_value, mode=new_mode, strict=new_strict)  # type: ignore[arg-type]

    @staticmethod
    def is_missing(x: Any) -> bool:
        return is_missing(x)

    def get(self, default: Any = None) -> Any:
        return self.value if not is_missing(self.value) else default

    def as_list(self) -> List[Any]:
        if is_missing(self.value):
            return []
        if isinstance(self.value, list):
            return self.value
        return [self.value]

    def getitem(self, key: Any) -> JsonValue:
        from .access import get_item

        value = get_item(self, key)
        return self.replace(value=value)

    def assert_present(self) -> None:
        if is_missing(self.value):
            raise ValueError("Missing value present")

    def fill_missing(self, value: Any) -> JsonValue:
        replacement = value if is_missing(self.value) else self.value
        return self.replace(value=replacement)
