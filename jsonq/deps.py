from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from jsonq.core.access import apply_path
from jsonq.core.path import Token, tokenize_path
from jsonq.operators import access as access_ops
from jsonq.operators import functional as functional_ops
from jsonq.operators import missing as missing_ops
from jsonq.operators import sequence as sequence_ops

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from jsonq.core.value import JsonValue
    from jsonq.operators.base import JsonOperator
    from jsonq.operators.functional import DiffOp

    from .core.core_types import JsonElement


class AccessService(Protocol):
    def getitem(self, key: str | int | slice) -> JsonOperator: ...

    def path(self, expr: str) -> JsonOperator: ...


class SequenceService(Protocol):
    def map_items(self, fn: Callable[[JsonElement], JsonElement]) -> JsonOperator: ...

    def filter_items(self, pred: Callable[[JsonElement], bool]) -> JsonOperator: ...

    def reject_items(self, pred: Callable[[JsonElement], bool]) -> JsonOperator: ...

    def sort_by(self, keyfn: Callable[[JsonElement], object]) -> JsonOperator: ...

    def unique(self, keyfn: Callable[[JsonElement], object] | None = None) -> JsonOperator: ...

    def flat(self) -> JsonOperator: ...


class MissingService(Protocol):
    def keep(self) -> JsonOperator: ...

    def drop(self) -> JsonOperator: ...

    def fill(self, value_to_use: JsonElement) -> JsonOperator: ...


class FunctionalService(Protocol):
    def diff(self, a: JsonElement, b: JsonElement) -> list[DiffOp]: ...

    def patch(self, a: JsonElement, ops: Sequence[DiffOp]) -> JsonElement: ...

    def to_json(self, x: JsonElement, *, indent: int | None = None) -> str: ...

    def pretty(self, x: JsonElement, *, indent: int = 2) -> None: ...


class PathResolver(Protocol):
    def tokenize(self, expr: str) -> tuple[Token, ...]: ...

    def apply(self, value: JsonValue, tokens: Sequence[Token]) -> JsonElement: ...


class _DefaultAccessService:
    def getitem(self, key: str | int | slice) -> JsonOperator:
        return access_ops.getitem(key)

    def path(self, expr: str) -> JsonOperator:
        return access_ops.path(expr)


class _DefaultSequenceService:
    def map_items(self, fn: Callable[[JsonElement], JsonElement]) -> JsonOperator:
        return sequence_ops.map_items(fn)

    def filter_items(self, pred: Callable[[JsonElement], bool]) -> JsonOperator:
        return sequence_ops.filter_items(pred)

    def reject_items(self, pred: Callable[[JsonElement], bool]) -> JsonOperator:
        return sequence_ops.reject_items(pred)

    def sort_by(self, keyfn: Callable[[JsonElement], object]) -> JsonOperator:
        return sequence_ops.sort_by(keyfn)

    def unique(self, keyfn: Callable[[JsonElement], object] | None = None) -> JsonOperator:
        return sequence_ops.unique(keyfn)

    def flat(self) -> JsonOperator:
        return sequence_ops.flat()


class _DefaultMissingService:
    def keep(self) -> JsonOperator:
        return missing_ops.keep()

    def drop(self) -> JsonOperator:
        return missing_ops.drop()

    def fill(self, value_to_use: JsonElement) -> JsonOperator:
        return missing_ops.fill(value_to_use)


class _DefaultFunctionalService:
    def diff(self, a: JsonElement, b: JsonElement) -> list[DiffOp]:
        return functional_ops.diff(a, b)

    def patch(self, a: JsonElement, ops: Sequence[DiffOp]) -> JsonElement:
        return functional_ops.patch(a, ops)

    def to_json(self, x: JsonElement, *, indent: int | None = None) -> str:
        return functional_ops.to_json(x, indent=indent)

    def pretty(self, x: JsonElement, *, indent: int = 2) -> None:
        functional_ops.pretty(x, indent=indent)


class _DefaultPathResolver:
    def tokenize(self, expr: str) -> tuple[Token, ...]:
        return tuple(tokenize_path(expr))

    def apply(self, value: JsonValue, tokens: Sequence[Token]) -> JsonElement:
        return apply_path(value, tuple(tokens))


@dataclass(slots=True)
class JsonOperatorFunctions:
    access: AccessService
    sequence: SequenceService
    missing: MissingService
    functional: FunctionalService
    path_resolver: PathResolver


DEFAULT_OPERATOR_FUNCTIONS = JsonOperatorFunctions(
    access=_DefaultAccessService(),
    sequence=_DefaultSequenceService(),
    missing=_DefaultMissingService(),
    functional=_DefaultFunctionalService(),
    path_resolver=_DefaultPathResolver(),
)
