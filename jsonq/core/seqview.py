from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import TYPE_CHECKING

from .coerce import coerce_json_element
from .missing import MISSING, MissingMode, is_missing

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from .core_types import JsonElement
    from .value import JsonValue


_SORT_KEY_MAX_DEPTH = 32


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
        drop_missing = self._v.mode is MissingMode.DROP
        candidates: list[SortCandidate] = []
        for idx, item in enumerate(self._iter()):
            try:
                candidate = _build_sort_candidate(item, idx, keyfn, drop_missing=drop_missing)
            except InvalidSortException:
                continue
            candidates.append(candidate)

        candidates.sort(key=lambda cand: (cand.key, cand.index))
        out = [cand.value for cand in candidates]
        return _wrap_seq(self._v, out)

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


class InvalidSortException(Exception):
    """Raised when a sort key cannot be derived."""


@dataclass(slots=True)
class SortCandidate:
    key: tuple[SortType, object]
    index: int
    value: JsonElement


class SortType(IntEnum):
    MISSING = 0
    NONE = 1
    BOOL = 2
    NUMBER = 3
    STRING = 4
    ARRAY = 5
    OBJECT = 6


class SortType(IntEnum):
    MISSING = 0
    NONE = 1
    BOOL = 2
    NUMBER = 3
    STRING = 4
    ARRAY = 5
    OBJECT = 6


def _build_sort_key(
    value: JsonElement,
    *,
    depth: int = 0,
    max_depth: int | None = None,
) -> tuple[SortType, object]:
    limit = _SORT_KEY_MAX_DEPTH if max_depth is None else max_depth
    if limit is not None and depth > limit:
        msg = "sort key depth exceeded"
        raise TypeError(msg)
    if is_missing(value):
        return (SortType.MISSING, 0)
    if value is None:
        return (SortType.NONE, 0)
    if isinstance(value, bool):
        return (SortType.BOOL, int(value))
    if isinstance(value, (int, float)):
        return (SortType.NUMBER, value)
    if isinstance(value, str):
        return (SortType.STRING, value)
    if isinstance(value, list):
        nested = tuple(_build_sort_key(item, depth=depth + 1, max_depth=limit) for item in value)
        return (SortType.ARRAY, nested)
    if isinstance(value, dict):
        nested = tuple((key, _build_sort_key(value[key], depth=depth + 1, max_depth=limit)) for key in sorted(value))
        return (SortType.OBJECT, nested)
    msg = f"Unsupported sort key type: {type(value).__name__}"
    raise TypeError(msg)


def _build_sort_candidate(
    item: JsonElement,
    idx: int,
    keyfn: Callable[[JsonElement], object],
    *,
    drop_missing: bool,
) -> SortCandidate:
    """Derive a SortCandidate, dropping `_Missing` keys when in drop mode."""
    try:
        raw_key = keyfn(item)
    except Exception as exc:
        raise InvalidSortException from exc

    if is_missing(raw_key):
        if drop_missing:
            raise InvalidSortException
        key_value = raw_key
    else:
        try:
            key_value = coerce_json_element(raw_key)
        except TypeError as exc:
            raise InvalidSortException from exc

    if is_missing(key_value) and drop_missing:
        raise InvalidSortException

    try:
        sort_key = _build_sort_key(key_value)
    except TypeError as exc:
        raise InvalidSortException from exc

    return SortCandidate(sort_key, idx, item)
