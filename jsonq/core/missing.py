from enum import Enum
from typing import TypeGuard


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

MissingType = _MissingType

__all__ = ["MISSING", "MissingMode", "MissingType", "is_missing"]


def is_missing(x: object) -> TypeGuard[_MissingType]:
    return isinstance(x, _MissingType)
