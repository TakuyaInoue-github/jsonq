from jsonq.core.core_types import JsonElement
from jsonq.core.missing import MissingMode
from jsonq.core.value import JsonValue
from jsonq.operators.base import JsonOperator


def keep() -> JsonOperator:
    def op(value: JsonValue) -> JsonValue:
        return value.with_mode(MissingMode.KEEP)

    return op


def drop() -> JsonOperator:
    def op(value: JsonValue) -> JsonValue:
        return value.with_mode(MissingMode.DROP)

    return op


def fill(value_to_use: JsonElement) -> JsonOperator:
    def op(value: JsonValue) -> JsonValue:
        return value.fill_missing(value_to_use)

    return op
