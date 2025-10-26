from __future__ import annotations
from typing import Any, Callable, Iterable, List, Optional

from .value import JsonValue
from .missing import MISSING, MissingMode, is_missing


class SeqView:
    """List-like transformations over JsonValue."""

    def __init__(self, v: JsonValue):
        self._v = v

    def _iter(self) -> Iterable[Any]:
        xs = self._v.as_list()
        for item in xs:
            if self._v.mode is MissingMode.DROP and is_missing(item):
                continue
            yield item

    def map(self, fn: Callable[[Any], Any]) -> SeqView:
        out = [_safe_apply(fn, item) for item in self._iter()]
        return _wrap_seq(self._v, out)

    def filter(self, pred: Callable[[Any], bool]) -> SeqView:
        out = [item for item in self._iter() if _safe_pred(pred, item)]
        return _wrap_seq(self._v, out)

    def reject(self, pred: Callable[[Any], bool]) -> SeqView:
        out = [item for item in self._iter() if not _safe_pred(pred, item)]
        return _wrap_seq(self._v, out)

    def sort_by(self, keyfn: Callable[[Any], Any]) -> SeqView:
        out = sorted(list(self._iter()), key=keyfn)
        return _wrap_seq(self._v, out)

    def unique(self, keyfn: Optional[Callable[[Any], Any]] = None) -> SeqView:
        seen = set()
        out = []
        for item in self._iter():
            marker = keyfn(item) if keyfn else item
            if marker not in seen:
                seen.add(marker)
                out.append(item)
        return _wrap_seq(self._v, out)

    def flat(self) -> SeqView:
        out: List[Any] = []
        for item in self._iter():
            if isinstance(item, list):
                out.extend(item)
            else:
                out.append(item)
        return _wrap_seq(self._v, out)

    def unwrap(self) -> Any:
        return self._v.unwrap()

    def to_value(self) -> JsonValue:
        """Expose the transformed JsonValue for operator chaining."""
        return self._v


def _safe_pred(pred: Callable[[Any], bool], value: Any) -> bool:
    try:
        return bool(pred(value))
    except Exception:
        return False


def _safe_apply(fn: Callable[[Any], Any], value: Any) -> Any:
    try:
        return fn(value)
    except Exception:
        return MISSING


def _wrap_seq(v: JsonValue, out: List[Any]) -> SeqView:
    return SeqView(v.replace(value=out))
