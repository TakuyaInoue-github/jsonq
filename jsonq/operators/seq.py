from __future__ import annotations

from typing import Any, Callable, Optional

from ..core.seqview import SeqView
from ..core.value import JsonValue
from .base import JsonOperator


def map_items(fn: Callable[[Any], Any]) -> JsonOperator:
    def op(value: JsonValue) -> JsonValue:
        return SeqView(value).map(fn).to_value()

    return op


def filter_items(pred: Callable[[Any], bool]) -> JsonOperator:
    def op(value: JsonValue) -> JsonValue:
        return SeqView(value).filter(pred).to_value()

    return op


def reject_items(pred: Callable[[Any], bool]) -> JsonOperator:
    def op(value: JsonValue) -> JsonValue:
        return SeqView(value).reject(pred).to_value()

    return op


def sort_by(keyfn: Callable[[Any], Any]) -> JsonOperator:
    def op(value: JsonValue) -> JsonValue:
        return SeqView(value).sort_by(keyfn).to_value()

    return op


def unique(keyfn: Optional[Callable[[Any], Any]] = None) -> JsonOperator:
    def op(value: JsonValue) -> JsonValue:
        return SeqView(value).unique(keyfn).to_value()

    return op


def flat() -> JsonOperator:
    def op(value: JsonValue) -> JsonValue:
        return SeqView(value).flat().to_value()

    return op
