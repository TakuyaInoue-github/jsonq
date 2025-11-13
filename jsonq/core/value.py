from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final, TypeVar, cast

from .missing import MissingMode, MissingType, is_missing

_DefaultT = TypeVar("_DefaultT")
_SAME_SENTINEL: Final = object()

if TYPE_CHECKING:
    from typing import Final

    from .core_types import JsonElement


def unwrap(json_elem: JsonElement) -> JsonValue:
    """Wrap a JSON element with a diff patch."""
    raise NotImplementedError


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

    def __get_item(self, key: str | int | slice) -> JsonValue | MissingType:
        raise NotImplementedError

    def get(self, default: JsonElement | _DefaultT | None = None) -> JsonElement | _DefaultT | None:
        return self.value if not is_missing(self.value) else default

    def as_list(self) -> list[JsonElement]:
        raise NotImplementedError

    def getitem(self, key: str | int | slice) -> JsonValue | list[JsonValue]:
        value = self.__get_item(key)
        return [self.replace(value=value)]

    def assert_present(self) -> None:
        if is_missing(self.value):
            raise ValueError("Missing value present")

    def fill_missing(self, value: JsonElement | MissingType) -> JsonValue:
        replacement = value if is_missing(self.value) else self.value
        return self.replace(value=replacement)
