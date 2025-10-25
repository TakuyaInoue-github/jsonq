from __future__ import annotations
from typing import Any, List

from .value import JsonValue


class DictView:
    """Dict-focused helpers (placeholder for future extensions)."""

    def __init__(self, v: JsonValue):
        self._v = v

    def keys(self) -> List[Any]:
        data = self._v.unwrap()
        if isinstance(data, dict):
            return list(data.keys())
        return []
