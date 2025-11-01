from __future__ import annotations

import json
from typing import Any, Optional

from ...core.missing import is_missing


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
        return any(_contains_missing(item) for item in x)
    if isinstance(x, dict):
        return any(_contains_missing(value) for value in x.values())
    return False
