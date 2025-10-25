from __future__ import annotations
from typing import Any, Callable, List, Optional

from .core.value import JsonValue
from .core.missing import MISSING, MissingMode
from .core.path import tokenize_path
from .core.access import apply_path
from .core.seqview import SeqView
from .ops.serialize import to_json as _to_json, pretty as _pretty
from .ops.diff import diff as _diff, patch as _patch


class Q:
    """Thin public facade that delegates to modular internals."""

    def __init__(self, data: Any, *, mode: MissingMode = MissingMode.DROP, strict: bool = False):
        if isinstance(data, JsonValue):
            self._v = data
        else:
            self._v = JsonValue(data, mode=mode, strict=strict)

    # ----- access -----
    def __getitem__(self, key: Any) -> "Q":
        return Q(self._v.getitem(key))

    def pluck(self, key: str) -> "Q":
        return self[key]

    def path(self, expr: str) -> "Q":
        toks = tokenize_path(expr)
        return Q(apply_path(self._v, toks))

    def exists(self, expr: str) -> bool:
        toks = tokenize_path(expr)
        v = apply_path(self._v, toks)
        return not JsonValue.is_missing(v)

    # ----- transforms -----
    def map(self, fn: Callable[[Any], Any]) -> "Q":
        return Q(SeqView(self._v).map(fn).unwrap())

    def filter(self, pred: Callable[[Any], bool]) -> "Q":
        return Q(SeqView(self._v).filter(pred).unwrap())

    def reject(self, pred: Callable[[Any], bool]) -> "Q":
        return Q(SeqView(self._v).reject(pred).unwrap())

    def sort_by(self, keyfn: Callable[[Any], Any]) -> "Q":
        return Q(SeqView(self._v).sort_by(keyfn).unwrap())

    def unique(self, keyfn: Optional[Callable[[Any], Any]] = None) -> "Q":
        return Q(SeqView(self._v).unique(keyfn).unwrap())

    def flat(self) -> "Q":
        return Q(SeqView(self._v).flat().unwrap())

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
        return _to_json(self._v.unwrap(), indent=indent)

    def pretty(self, indent: int = 2) -> None:
        _pretty(self._v.unwrap(), indent=indent)

    # ----- missing policy -----
    def keep_missing(self) -> "Q":
        return Q(self._v.with_mode(MissingMode.KEEP))

    def drop_missing(self) -> "Q":
        return Q(self._v.with_mode(MissingMode.DROP))

    def assert_present(self) -> "Q":
        self._v.assert_present()
        return self

    def fill_missing(self, value: Any) -> "Q":
        return Q(self._v.fill_missing(value))

    def coalesce(self, *paths: str, default: Any = None) -> Any:
        for p in paths:
            value = self.path(p).get(MISSING)
            if not JsonValue.is_missing(value):
                return value
        return default

    # ----- diff/patch -----
    @staticmethod
    def diff(a: Any, b: Any):
        return _diff(a, b)

    @staticmethod
    def patch(a: Any, ops: Any):
        return _patch(a, ops)


class jx:
    """Functional helpers for pipeline composition (minimal for MVP)."""

    @staticmethod
    def list(x: Any) -> List[Any]:
        return Q(x).list()
