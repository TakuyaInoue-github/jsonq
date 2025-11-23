from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final, TypeVar, cast

from .access import get_item as _core_get_item
from .coerce import coerce_json_element
from .missing import MissingMode, MissingType, is_missing

_DefaultT = TypeVar("_DefaultT")
_SAME_SENTINEL: Final = object()

if TYPE_CHECKING:
    from .core_types import JsonElement


def coerce_json_value(json_elem: JsonElement) -> JsonValue:
    """Wrap a JSON element with JsonValue, ensuring nested items are valid JSON."""
    if isinstance(json_elem, JsonValue):
        return json_elem
    coerced = coerce_json_element(json_elem)
    return JsonValue(coerced, mode=MissingMode.DROP, strict=False)


@dataclass(frozen=True, slots=True)
class JsonValue:
    """Serializable DTO that couples a JSON value with missing policy."""

    value: JsonElement
    mode: MissingMode
    strict: bool = False

    _SAME: Final = _SAME_SENTINEL

    def unwrap(self) -> JsonElement:
        return self.value

    def with_mode(self, mode: MissingMode) -> JsonValue:
        return self.replace(mode=mode)

    def replace(
        self,
        *,
        value: JsonElement | MissingType | object = _SAME,
        mode: MissingMode | object = _SAME,
        strict: bool | object = _SAME,
    ) -> JsonValue:
        new_value = self.value if value is JsonValue._SAME else cast("JsonElement", value)
        new_mode = self.mode if mode is JsonValue._SAME else cast("MissingMode", mode)
        new_strict = self.strict if strict is JsonValue._SAME else cast("bool", strict)
        if new_value is self.value and new_mode is self.mode and new_strict is self.strict:
            return self
        return JsonValue(new_value, mode=new_mode, strict=new_strict)

    @staticmethod
    def is_missing(x: object) -> bool:
        return is_missing(x)

    def __get_item(self, key: str | int | slice) -> JsonElement:
        return _core_get_item(self, key)

    def get(self, default: JsonElement | _DefaultT | None = None) -> JsonElement | _DefaultT | None:
        return self.value if not is_missing(self.value) else default

    def as_list(self) -> list[JsonElement]:
        value = self.value
        if isinstance(value, list):
            items = [coerce_json_element(v) for v in list(value)]
        elif is_missing(value):
            items = [] if self.mode is MissingMode.DROP else [coerce_json_element(value)]
        else:
            items = [coerce_json_element(value)]
        if self.mode is MissingMode.DROP:
            items = [coerce_json_element(item) for item in items if not is_missing(item)]
        return items

    def getitem(self, key: str | int | slice) -> JsonValue:
        value = self.__get_item(key)
        return self.replace(value=value)

    def assert_present(self) -> None:
        if is_missing(self.value):
            raise ValueError("Missing value present")

    def fill_missing(self, value: JsonElement | MissingType) -> JsonValue:
        replacement = value if is_missing(self.value) else self.value
        return self.replace(value=replacement)
