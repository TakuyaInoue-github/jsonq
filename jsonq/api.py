from __future__ import annotations

from typing import TYPE_CHECKING

from .core.missing import MISSING, MissingMode, MissingType
from .core.value import JsonValue
from .deps import DEFAULT_OPERATOR_FUNCTIONS, JsonOperatorFunctions

if TYPE_CHECKING:
    from collections.abc import Callable

    from .core.core_types import JsonElement
    from .operators import JsonOperator
    from .operators.functional import DiffOp


class Q:
    """Thin public facade that delegates to modular internals."""

    def __init__(
        self,
        data: JsonElement | JsonValue,
        *,
        mode: MissingMode = MissingMode.DROP,
        strict: bool = False,
        deps: JsonOperatorFunctions = DEFAULT_OPERATOR_FUNCTIONS,
    ) -> None:
        if isinstance(data, JsonValue):
            self._v = data
        else:
            self._v = JsonValue(data, mode=mode, strict=strict)
        self._deps = deps

    def apply(self, operator: JsonOperator) -> Q:
        """Return a new Q after running the supplied JsonValue operator."""
        return Q(operator(self._v), deps=self._deps)

    # ----- access -----
    def __getitem__(self, key: str | int | slice) -> Q:
        return self.apply(self._deps.access.getitem(key))

    def pluck(self, key: str) -> Q:
        return self[key]

    def path(self, expr: str) -> Q:
        return self.apply(self._deps.access.path(expr))

    def exists(self, expr: str) -> bool:
        toks = self._deps.path_resolver.tokenize(expr)
        v = self._deps.path_resolver.apply(self._v, toks)
        return not JsonValue.is_missing(v)

    # ----- transforms -----
    def map(self, fn: Callable[[JsonElement], JsonElement]) -> Q:
        return self.apply(self._deps.sequence.map_items(fn))

    def filter(self, pred: Callable[[JsonElement], bool]) -> Q:
        return self.apply(self._deps.sequence.filter_items(pred))

    def reject(self, pred: Callable[[JsonElement], bool]) -> Q:
        return self.apply(self._deps.sequence.reject_items(pred))

    def sort_by(self, keyfn: Callable[[JsonElement], object]) -> Q:
        return self.apply(self._deps.sequence.sort_by(keyfn))

    def unique(self, keyfn: Callable[[JsonElement], object] | None = None) -> Q:
        return self.apply(self._deps.sequence.unique(keyfn))

    def flat(self) -> Q:
        return self.apply(self._deps.sequence.flat())

    # ----- extraction -----
    def get(self, default: JsonElement | MissingType | None = None) -> JsonElement | MissingType | None:
        return self._v.get(default)

    def list(self) -> list[JsonElement]:
        return self._v.as_list()

    def first(self, default: JsonElement | MissingType | None = None) -> JsonElement | MissingType | None:
        xs = self.list()
        return xs[0] if xs else default

    # ----- serialization -----
    def to_json(self, indent: int | None = None) -> str:
        return self._deps.functional.to_json(self._v.unwrap(), indent=indent)

    def pretty(self, indent: int = 2) -> None:
        self._deps.functional.pretty(self._v.unwrap(), indent=indent)

    # ----- missing policy -----
    def keep_missing(self) -> Q:
        return self.apply(self._deps.missing.keep())

    def drop_missing(self) -> Q:
        return self.apply(self._deps.missing.drop())

    def assert_present(self) -> Q:
        self._v.assert_present()
        return self

    def fill_missing(self, value: JsonElement | MissingType) -> Q:
        return self.apply(self._deps.missing.fill(value))

    def coalesce(self, *paths: str, default: JsonElement | MissingType | None = None) -> JsonElement | MissingType | None:
        for p in paths:
            value = self.path(p).get(MISSING)
            if not JsonValue.is_missing(value):
                return value
        return default

    # ----- diff/patch -----
    @staticmethod
    def diff(a: JsonElement, b: JsonElement) -> list[DiffOp]:
        return DEFAULT_OPERATOR_FUNCTIONS.functional.diff(a, b)

    @staticmethod
    def patch(a: JsonElement, ops: list[DiffOp]) -> JsonElement:
        return DEFAULT_OPERATOR_FUNCTIONS.functional.patch(a, ops)


class Jx:
    """Functional helpers for pipeline composition (minimal for MVP)."""

    @staticmethod
    def list(x: JsonElement | JsonValue) -> list[JsonElement]:
        return Q(x).list()
