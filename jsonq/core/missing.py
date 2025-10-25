from __future__ import annotations
from enum import Enum
from typing import Any


class MissingMode(str, Enum):
    """How to treat missing values in operations."""

    DROP = "drop"
    KEEP = "keep"
    RAISE = "raise"


class _MissingType:
    """Singleton sentinel distinct from None."""

    __slots__ = ()

    def __bool__(self) -> bool:  # pragma: no cover - trivial
        return False

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return "<MISSING>"


MISSING = _MissingType()


def is_missing(x: Any) -> bool:
    return x is MISSING
