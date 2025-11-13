from typing import Protocol

from jsonq.core.value import JsonValue


class JsonOperator(Protocol):
    def __call__(self, value: JsonValue) -> JsonValue: ...


def pipe(*ops: JsonOperator) -> JsonOperator:
    """Compose multiple JsonOperators into one pipeline."""

    def composed(value: JsonValue) -> JsonValue:
        out = value
        for op in ops:
            out = op(out)
        return out

    return composed


def identity() -> JsonOperator:
    """Return an operator that yields its input unchanged."""

    def _identity(value: JsonValue) -> JsonValue:
        return value

    return _identity
