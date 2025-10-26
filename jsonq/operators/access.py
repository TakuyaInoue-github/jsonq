from __future__ import annotations

from typing import Any

from ..core.access import apply_path, get_item
from ..core.path import tokenize_path
from ..core.value import JsonValue
from .base import JsonOperator


def getitem(key: Any) -> JsonOperator:
    def op(value: JsonValue) -> JsonValue:
        return value.replace(value=get_item(value, key))

    return op


def path(expr: str) -> JsonOperator:
    tokens = tuple(tokenize_path(expr))

    def op(value: JsonValue) -> JsonValue:
        return value.replace(value=apply_path(value, tokens))

    return op
