from collections.abc import Callable

from jsonq.core.core_types import JsonElement
from jsonq.core.seqview import SeqView
from jsonq.core.value import JsonValue
from jsonq.operators.base import JsonOperator


def map_items(fn: Callable[[JsonElement], JsonElement]) -> JsonOperator:
    def op(value: JsonValue) -> JsonValue:
        return SeqView(value).map(fn).to_value()

    return op


def filter_items(pred: Callable[[JsonElement], bool]) -> JsonOperator:
    def op(value: JsonValue) -> JsonValue:
        return SeqView(value).filter(pred).to_value()

    return op


def reject_items(pred: Callable[[JsonElement], bool]) -> JsonOperator:
    def op(value: JsonValue) -> JsonValue:
        return SeqView(value).reject(pred).to_value()

    return op


def sort_by(keyfn: Callable[[JsonElement], object]) -> JsonOperator:
    def op(value: JsonValue) -> JsonValue:
        return SeqView(value).sort_by(keyfn).to_value()

    return op


def unique(keyfn: Callable[[JsonElement], object] | None = None) -> JsonOperator:
    def op(value: JsonValue) -> JsonValue:
        return SeqView(value).unique(keyfn).to_value()

    return op


def flat() -> JsonOperator:
    def op(value: JsonValue) -> JsonValue:
        return SeqView(value).flat().to_value()

    return op
