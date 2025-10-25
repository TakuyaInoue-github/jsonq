from __future__ import annotations
import re
from typing import List, Union

Token = Union[str, int]
_IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def tokenize_path(expr: str) -> List[Token]:
    """Turn ``a.b[0].c`` into tokens like ``[\"a\", \"b\", 0, \"c\"]``."""

    if not expr:
        return []
    tokens: List[Token] = []
    i = 0
    n = len(expr)
    while i < n:
        ch = expr[i]
        if ch == ".":
            i += 1
            continue
        if ch == "[":
            end = expr.find("]", i + 1)
            if end == -1:
                raise ValueError(f"Unclosed '[' in path: {expr}")
            raw = expr[i + 1 : end].strip()
            if not raw:
                raise ValueError(f"Empty index in path: {expr}")
            try:
                tokens.append(int(raw))
            except ValueError as exc:
                raise ValueError(f"Invalid index '{raw}' in path: {expr}") from exc
            i = end + 1
            continue
        match = _IDENT_RE.match(expr, i)
        if not match:
            raise ValueError(f"Invalid identifier at: {expr[i:]} in {expr}")
        tokens.append(match.group())
        i = match.end()
    return tokens
