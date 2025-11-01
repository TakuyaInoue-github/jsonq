from __future__ import annotations

from typing import Any

from ...core.missing import MissingMode
from ...core.value import JsonValue
from ..base import JsonOperator


def keep() -> JsonOperator:
    def op(value: JsonValue) -> JsonValue:
        return value.with_mode(MissingMode.KEEP)

    return op


def drop() -> JsonOperator:
    def op(value: JsonValue) -> JsonValue:
        return value.with_mode(MissingMode.DROP)

    return op


def fill(value_to_use: Any) -> JsonOperator:
    def op(value: JsonValue) -> JsonValue:
        return value.fill_missing(value_to_use)

    return op
