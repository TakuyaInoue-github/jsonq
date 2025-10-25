# ==== Package layout proposal ====
# jsonq/
#   __init__.py
#   api.py                 # Public facade (Q, jx helpers)
#   core/
#     value.py             # JsonValue (immutable holder) + policies
#     missing.py           # MISSING, MissingMode, helpers
#     path.py              # Path tokens & parser
#     access.py            # get_item / apply_path (stateless)
#     seqview.py           # SeqView (list-like ops)
#     dictview.py          # DictView (dict-like ops)
#   ops/
#     serialize.py         # to_json / pretty / ensure_serializable
#     diff.py              # diff/patch (shallow MVP)

# ---------------------------------------------------------------------
# file: jsonq/__init__.py
"""jsonq public API.

Expose Q facade and key utilities. Internals live under jsonq.core / jsonq.ops.
"""
from .api import Q, jx  # noqa: F401
from .core.missing import MISSING, MissingMode  # noqa: F401

__all__ = ["Q", "jx", "MISSING", "MissingMode"]


# ---------------------------------------------------------------------
# file: jsonq/api.py
from __future__ import annotations
from typing import Any, Callable, Optional, List
from .core.value import JsonValue
from .core.missing import MissingMode
from .core.path import tokenize_path
from .core.access import apply_path
from .core.seqview import SeqView
from .core.dictview import DictView
from .ops.serialize import to_json as _to_json, pretty as _pretty
from .ops.diff import diff as _diff, patch as _patch


class Q:
    """Thin public facade that delegates to modular internals.

    This preserves the REPL-friendly API while keeping responsibilities split.
    """

    def __init__(self, data: Any, *, mode: MissingMode = MissingMode.DROP, strict: bool = False):
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
            v = Q(self._v.unwrap()).path(p).get(MissingMode)
            if not JsonValue.is_missing(v):
                return v
        return default

    # ----- diff/patch -----
    @staticmethod
    def diff(a: Any, b: Any):
        return _diff(a, b)

    @staticmethod
    def patch(a: Any, ops: Any):
        return _patch(a, ops)


# Optional functional facade (pipeline-friendly)
class jx:
    """Functional helpers for pipeline composition.

    This is intentionally minimal for MVP.
    """
    @staticmethod
    def list(x: Any) -> List[Any]:
        return Q(x).list()


# ---------------------------------------------------------------------
# file: jsonq/core/missing.py
from __future__ import annotations
from enum import Enum
from typing import Any


class MissingMode(str, Enum):
    """How to treat missing values in operations.
    - DROP: exclude missing values from vectorized results (default)
    - KEEP: keep missing marker in results
    - RAISE: raise on missing access
    """
    DROP = "drop"
    KEEP = "keep"
    RAISE = "raise"


class _MissingType:
    """Singleton sentinel distinct from None.
    bool(MISSING) is False; comparisons except identity are discouraged.
    """
    __slots__ = ()
    def __bool__(self) -> bool:
        return False
    def __repr__(self) -> str:
        return "<MISSING>"


MISSING = _MissingType()


def is_missing(x: Any) -> bool:
    return x is MISSING


# ---------------------------------------------------------------------
# file: jsonq/core/value.py
from __future__ import annotations
from typing import Any, List
from .missing import MISSING, MissingMode, is_missing


class JsonValue:
    """Immutable holder for a JSON-ish value + missing policy.

    The holder exposes small helpers used by views and API.
    """
    __slots__ = ("_v", "_mode", "_strict")

    def __init__(self, v: Any, *, mode: MissingMode, strict: bool):
        self._v = v
        self._mode = mode
        self._strict = strict

    def unwrap(self) -> Any:
        return self._v

    def with_mode(self, mode: MissingMode) -> "JsonValue":
        return JsonValue(self._v, mode=mode, strict=self._strict)

    @staticmethod
    def is_missing(x: Any) -> bool:
        return is_missing(x)

    def get(self, default: Any = None) -> Any:
        return self._v if not is_missing(self._v) else default

    def as_list(self) -> List[Any]:
        if is_missing(self._v):
            return []
        if isinstance(self._v, list):
            return self._v
        return [self._v]

    # Access used by Q.__getitem__ (MVP: delegate later to Accessor)
    def getitem(self, key: Any) -> "JsonValue":
        from .access import get_item
        return JsonValue(get_item(self, key), mode=self._mode, strict=self._strict)

    # Missing utilities
    def assert_present(self) -> None:
        if is_missing(self._v):
            raise ValueError("Missing value present")

    def fill_missing(self, value: Any) -> "JsonValue":
        return JsonValue(value if is_missing(self._v) else self._v, mode=self._mode, strict=self._strict)


# ---------------------------------------------------------------------
# file: jsonq/core/path.py
from __future__ import annotations
import re
from typing import List, Union

Token = Union[str, int]
_IDENT = r"[A-Za-z_][A-Za-z0-9_]*"
_IDX = r"\[(-?\d+)\]"

_pat = re.compile(rf"({_IDENT})|{_IDX}")


def tokenize_path(expr: str) -> List[Token]:
    """Turn "a.b[0].c" into tokens ["a", "b", 0, "c"].
    Raises ValueError if expression is malformed.
    """
    if not expr:
        return []
    # Replace dots with "][" to reuse one regex walker
    parts = expr.split('.')
    s = "][".join(parts)
    tokens: List[Token] = []
    pos = 0
    for m in _pat.finditer(s):
        if m.start() != pos:
            raise ValueError(f"Invalid path near: {s[pos:]} in {expr}")
        name, idx = m.group(1), m.group(2)
        if name is not None:
            tokens.append(name)
        elif idx is not None:
            tokens.append(int(idx))
        pos = m.end()
    if pos != len(s):
        raise ValueError(f"Invalid path tail: {s[pos:]} in {expr}")
    return tokens


# ---------------------------------------------------------------------
# file: jsonq/core/access.py
from __future__ import annotations
from typing import Any, List, Iterable, Union
from .missing import MISSING, MissingMode, is_missing
from .value import JsonValue


def _as_list(x: Any) -> List[Any]:
    if is_missing(x):
        return []
    return x if isinstance(x, list) else [x]


def _flatten_once(seq: Iterable[Any], *, drop_missing: bool) -> List[Any]:
    out: List[Any] = []
    for x in seq:
        if isinstance(x, list):
            out.extend(x)
        elif not (drop_missing and is_missing(x)):
            out.append(x)
    return out


def get_item(v: JsonValue, key: Union[str, int, slice]) -> Any:
    """Vectorized safe item access based on current MissingMode.
    - dict/str-key: dict.get; returns MISSING if absent
    - list/int or slice: Python indexing; IndexError -> MISSING
    - list/str-key: vectorized pluck over elements
    """
    val = v.unwrap()
    mode = v._mode  # internal use by design

    def on_missing(exc: Exception | None = None):
        if mode is MissingMode.RAISE:
            if isinstance(exc, Exception):
                raise exc
            raise KeyError("missing")
        return MISSING

    if isinstance(val, list):
        if isinstance(key, int) or isinstance(key, slice):
            try:
                return val[key]
            except Exception as e:
                return on_missing(e)
        # vectorized pluck across elements
        out = []
        for el in val:
            if isinstance(el, dict) and isinstance(key, str):
                out.append(el.get(key, MISSING))
            else:
                out.append(MISSING)
        drop = (mode is MissingMode.DROP)
        return _flatten_once(out, drop_missing=drop)

    if isinstance(val, dict):
        if isinstance(key, str):
            return val.get(key, on_missing())
        else:
            return on_missing()

    return on_missing()


def apply_path(v: JsonValue, tokens: List[Union[str, int]]) -> Any:
    cur: Any = v
    for t in tokens:
        if isinstance(cur, JsonValue):
            cur = get_item(cur, t)
        else:
            cur = get_item(JsonValue(cur, mode=v._mode, strict=v._strict), t)
        if is_missing(cur):
            break
    return cur


# ---------------------------------------------------------------------
# file: jsonq/core/seqview.py
from __future__ import annotations
from typing import Any, Callable, List, Optional
from .value import JsonValue
from .missing import is_missing, MISSING, MissingMode


class SeqView:
    """List-like transformations over JsonValue.
    If underlying value is scalar, it is treated as single-element list.
    """
    def __init__(self, v: JsonValue):
        self._v = v

    def _iter(self):
        xs = self._v.as_list()
        for x in xs:
            if not (self._v._mode is MissingMode.DROP and is_missing(x)):
                yield x

    def map(self, fn: Callable[[Any], Any]) -> "SeqView":
        out = [ _safe_apply(fn, x) for x in self._iter() ]
        return _wrap_seq(self._v, out)

    def filter(self, pred: Callable[[Any], bool]) -> "SeqView":
        out = [ x for x in self._iter() if _safe_pred(pred, x) ]
        return _wrap_seq(self._v, out)

    def reject(self, pred: Callable[[Any], bool]) -> "SeqView":
        out = [ x for x in self._iter() if not _safe_pred(pred, x) ]
        return _wrap_seq(self._v, out)

    def sort_by(self, keyfn: Callable[[Any], Any]) -> "SeqView":
        out = sorted(list(self._iter()), key=keyfn)
        return _wrap_seq(self._v, out)

    def unique(self, keyfn: Optional[Callable[[Any], Any]] = None) -> "SeqView":
        seen = set()
        out = []
        for x in self._iter():
            k = keyfn(x) if keyfn else x
            if k not in seen:
                seen.add(k)
                out.append(x)
        return _wrap_seq(self._v, out)

    def flat(self) -> "SeqView":
        out: List[Any] = []
        for x in self._iter():
            if isinstance(x, list):
                out.extend(x)
            else:
                out.append(x)
        return _wrap_seq(self._v, out)

    def unwrap(self) -> Any:
        return self._v.unwrap()


def _safe_pred(pred: Callable[[Any], bool], x: Any) -> bool:
    try:
        return bool(pred(x))
    except Exception:
        return False


def _safe_apply(fn: Callable[[Any], Any], x: Any) -> Any:
    try:
        return fn(x)
    except Exception:
        return MISSING


def _wrap_seq(v: JsonValue, out: List[Any]) -> SeqView:
    return SeqView(JsonValue(out, mode=v._mode, strict=v._strict))


# ---------------------------------------------------------------------
# file: jsonq/core/dictview.py
from __future__ import annotations
from typing import Any, List
from .value import JsonValue
from .missing import MISSING, is_missing, MissingMode


class DictView:
    """Dict-focused helpers (placeholder for future extensions)."""
    def __init__(self, v: JsonValue):
        self._v = v

    def keys(self) -> List[Any]:
        d = self._v.unwrap()
        if isinstance(d, dict):
            return list(d.keys())
        return []


# ---------------------------------------------------------------------
# file: jsonq/ops/serialize.py
from __future__ import annotations
from typing import Any, Optional
import json
from ..core.missing import is_missing


def ensure_serializable(x: Any) -> None:
    if _contains_missing(x):
        raise ValueError("Missing values present; fill or drop before serialization")


def to_json(x: Any, *, indent: Optional[int] = None) -> str:
    ensure_serializable(x)
    return json.dumps(x, ensure_ascii=False, indent=indent)


def pretty(x: Any, *, indent: int = 2) -> None:
    print(to_json(x, indent=indent))


def _contains_missing(x: Any) -> bool:
    if is_missing(x):
        return True
    if isinstance(x, list):
        return any(_contains_missing(el) for el in x)
    if isinstance(x, dict):
        return any(_contains_missing(v) for v in x.values())
    return False


# ---------------------------------------------------------------------
# file: jsonq/ops/diff.py
from __future__ import annotations
from typing import Any, List, Dict

Op = Dict[str, Any]


def diff(a: Any, b: Any) -> List[Op]:
    """Shallow dict diff (MVP): add/remove/replace on top-level keys.
    If inputs are not both dicts, emit single replace op when unequal.
    """
    ops: List[Op] = []
    if isinstance(a, dict) and isinstance(b, dict):
        ak, bk = set(a.keys()), set(b.keys())
        for k in sorted(ak - bk):
            ops.append({"op": "remove", "path": f"/{k}"})
        for k in sorted(bk - ak):
            ops.append({"op": "add", "path": f"/{k}", "value": b[k]})
        for k in sorted(ak & bk):
            if a[k] != b[k]:
                ops.append({"op": "replace", "path": f"/{k}", "value": b[k]})
        return ops
    if a != b:
        ops.append({"op": "replace", "path": "/", "value": b})
    return ops


def patch(a: Any, ops: List[Op]) -> Any:
    """Apply shallow ops to a copy; if non-dict and op targets root, replace."""
    import copy
    x = copy.deepcopy(a)
    for op in ops:
        path = op["path"].lstrip("/")
        if path == "":
            if op["op"] in ("add", "replace"):
                x = op.get("value")
            elif op["op"] == "remove":
                x = None
            continue
        if not isinstance(x, dict):
            continue
        if op["op"] == "remove":
            x.pop(path, None)
        elif op["op"] in ("add", "replace"):
            x[path] = op.get("value")
    return x
