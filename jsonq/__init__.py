"""jsonq public API.

Expose Q facade and key utilities. Internals live under jsonq.core / jsonq.operators.
"""

from .api import Q
from .core.missing import MISSING, MissingMode

__all__ = ["MISSING", "MissingMode", "Q"]
