from __future__ import annotations
from typing import Any, Callable, List, Optional

from .core.value import JsonValue
from .core.missing import MISSING, MissingMode
from .core.path import tokenize_path
from .core.access import apply_path
from .core.seqview import SeqView
from .ops.serialize import to_json as _to_json, pretty as _pretty
from .ops.diff import diff as _diff, patch as _patch

JsonOperator = Callable[[JsonValue], JsonValue]


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
        return self.apply(lambda v, k=key: v.getitem(k))

    def pluck(self, key: str) -> "Q":
        return self[key]

    def path(self, expr: str) -> "Q":
        toks = tokenize_path(expr)
        return self.apply(lambda v, tokens=toks: v.replace(value=apply_path(v, tokens)))

    def exists(self, expr: str) -> bool:
        toks = tokenize_path(expr)
        v = apply_path(self._v, toks)
        return not JsonValue.is_missing(v)

    # ----- transforms -----
    def map(self, fn: Callable[[Any], Any]) -> "Q":
        return self.apply(lambda v, fn=fn: SeqView(v).map(fn).to_value())

    def filter(self, pred: Callable[[Any], bool]) -> "Q":
        return self.apply(lambda v, pred=pred: SeqView(v).filter(pred).to_value())

    def reject(self, pred: Callable[[Any], bool]) -> "Q":
        return self.apply(lambda v, pred=pred: SeqView(v).reject(pred).to_value())

    def sort_by(self, keyfn: Callable[[Any], Any]) -> "Q":
        return self.apply(lambda v, keyfn=keyfn: SeqView(v).sort_by(keyfn).to_value())

    def unique(self, keyfn: Optional[Callable[[Any], Any]] = None) -> "Q":
        return self.apply(lambda v, keyfn=keyfn: SeqView(v).unique(keyfn).to_value())

    def flat(self) -> "Q":
        return self.apply(lambda v: SeqView(v).flat().to_value())

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
        return self.apply(lambda v: v.with_mode(MissingMode.KEEP))

    def drop_missing(self) -> "Q":
        return self.apply(lambda v: v.with_mode(MissingMode.DROP))

    def assert_present(self) -> "Q":
        self._v.assert_present()
        return self

    def fill_missing(self, value: Any) -> "Q":
        return self.apply(lambda v, fill=value: v.fill_missing(fill))

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
