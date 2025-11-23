from jsonq.core.access import apply_path, get_item
from jsonq.core.path import tokenize_path
from jsonq.core.value import JsonValue
from jsonq.operators.base import JsonOperator


def getitem(key: str | int | slice) -> JsonOperator:
    def op(value: JsonValue) -> JsonValue:
        return value.replace(value=get_item(value, key))

    return op


def path(expr: str) -> JsonOperator:
    tokens = tuple(tokenize_path(expr))

    def op(value: JsonValue) -> JsonValue:
        return value.replace(value=apply_path(value, tokens))

    return op
