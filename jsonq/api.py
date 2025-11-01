from __future__ import annotations
from typing import Any, Callable, List, Optional

from .core.value import JsonValue
from .core.missing import MISSING, MissingMode
from .core.path import tokenize_path
from .core.access import apply_path
from .operators import JsonOperator
from .operators import access as access_ops
from .operators import functional as functional_ops
from .operators import missing as missing_ops
from .operators import sequence as sequence_ops


class Q:
    """Thin public facade that delegates to modular internals."""

    def __init__(self, data: Any, *, mode: MissingMode = MissingMode.DROP, strict: bool = False):
        if isinstance(data, JsonValue):
            self._v = data
        else:
            self._v = JsonValue(data, mode=mode, strict=strict)

    def apply(self, operator: JsonOperator) -> "Q":
        """Return a new Q after running the supplied JsonValue operator."""
        return Q(operator(self._v))

    # ----- access -----
    def __getitem__(self, key: Any) -> "Q":
        return self.apply(access_ops.getitem(key))

    def pluck(self, key: str) -> "Q":
        return self[key]

    def path(self, expr: str) -> "Q":
        return self.apply(access_ops.path(expr))

    def exists(self, expr: str) -> bool:
        toks = tokenize_path(expr)
        v = apply_path(self._v, toks)
        return not JsonValue.is_missing(v)

    # ----- transforms -----
    def map(self, fn: Callable[[Any], Any]) -> "Q":
        return self.apply(sequence_ops.map_items(fn))

    def filter(self, pred: Callable[[Any], bool]) -> "Q":
        return self.apply(sequence_ops.filter_items(pred))

    def reject(self, pred: Callable[[Any], bool]) -> "Q":
        return self.apply(sequence_ops.reject_items(pred))

    def sort_by(self, keyfn: Callable[[Any], Any]) -> "Q":
        return self.apply(sequence_ops.sort_by(keyfn))

    def unique(self, keyfn: Optional[Callable[[Any], Any]] = None) -> "Q":
        return self.apply(sequence_ops.unique(keyfn))

    def flat(self) -> "Q":
        return self.apply(sequence_ops.flat())

    # ----- extraction -----
    def get(self, default: Any = None) -> Any:
        return self._v.get(default)

    def list(self) -> List[Any]:
        return self._v.as_list()

    def first(self, default: Any = None) -> Any:
        xs = self.list()
        return xs[0] if xs else default

    # ----- serialization -----
    def to_json(self, indent: Optional[int] = None) -> str:
        return functional_ops.to_json(self._v.unwrap(), indent=indent)

    def pretty(self, indent: int = 2) -> None:
        functional_ops.pretty(self._v.unwrap(), indent=indent)

    # ----- missing policy -----
    def keep_missing(self) -> "Q":
        return self.apply(missing_ops.keep())

    def drop_missing(self) -> "Q":
        return self.apply(missing_ops.drop())

    def assert_present(self) -> "Q":
        self._v.assert_present()
        return self

    def fill_missing(self, value: Any) -> "Q":
        return self.apply(missing_ops.fill(value))

    def coalesce(self, *paths: str, default: Any = None) -> Any:
        for p in paths:
            value = self.path(p).get(MISSING)
            if not JsonValue.is_missing(value):
                return value
        return default

    # ----- diff/patch -----
    @staticmethod
    def diff(a: Any, b: Any):
        return functional_ops.diff(a, b)

    @staticmethod
    def patch(a: Any, ops: Any):
        return functional_ops.patch(a, ops)


class jx:
    """Functional helpers for pipeline composition (minimal for MVP)."""

    @staticmethod
    def list(x: Any) -> List[Any]:
        return Q(x).list()
