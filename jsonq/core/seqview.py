from __future__ import annotations

from typing import TYPE_CHECKING

from .missing import MISSING, MissingMode, is_missing

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from .core_types import JsonElement
    from .value import JsonValue


class SeqView:
    """List-like transformations over JsonValue."""

    def __init__(self, v: JsonValue) -> None:
        self._v = v

    def _iter(self) -> Iterable[JsonElement]:
        xs = self._v.as_list()
        for item in xs:
            if self._v.mode is MissingMode.DROP and is_missing(item):
                continue
            yield item

    def map(self, fn: Callable[[JsonElement], JsonElement]) -> SeqView:
        out = [_safe_apply(fn, item) for item in self._iter()]
        return _wrap_seq(self._v, out)

    def filter(self, pred: Callable[[JsonElement], bool]) -> SeqView:
        out = [item for item in self._iter() if _safe_pred(pred, item)]
        return _wrap_seq(self._v, out)

    def reject(self, pred: Callable[[JsonElement], bool]) -> SeqView:
        out = [item for item in self._iter() if not _safe_pred(pred, item)]
        return _wrap_seq(self._v, out)

    def sort_by(self, keyfn: Callable[[JsonElement], object]) -> SeqView:
        # TODO: implement coercion rules
        raise NotImplementedError

    def unique(self, keyfn: Callable[[JsonElement], object] | None = None) -> SeqView:
        seen = set()
        out = []
        for item in self._iter():
            marker = keyfn(item) if keyfn else item
            if marker not in seen:
                seen.add(marker)
                out.append(item)
        return _wrap_seq(self._v, out)

    def flat(self) -> SeqView:
        out: list[JsonElement] = []
        for item in self._iter():
            if isinstance(item, list):
                out.extend(item)
            else:
                out.append(item)
        return _wrap_seq(self._v, out)

    def unwrap(self) -> JsonElement:
        return self._v.unwrap()

    def to_value(self) -> JsonValue:
        """Expose the transformed JsonValue for operator chaining."""
        return self._v


def _safe_pred(pred: Callable[[JsonElement], bool], value: JsonElement) -> bool:
    try:
        return bool(pred(value))
    except Exception:  # noqa: BLE001 - user-supplied predicates may raise arbitrary exceptions
        return False


def _safe_apply(fn: Callable[[JsonElement], JsonElement], value: JsonElement) -> JsonElement:
    try:
        return fn(value)
    except Exception:  # noqa: BLE001 - user-supplied transformers may raise arbitrary exceptions
        return MISSING


def _wrap_seq(v: JsonValue, out: list[JsonElement]) -> SeqView:
    return SeqView(v.replace(value=out))
