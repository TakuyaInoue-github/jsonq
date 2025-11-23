import re

Token = str | int
_IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def tokenize_path(expr: str) -> list[Token]:
    r"""Turn ``a.b[0].c`` into tokens like ``["a", "b", 0, "c"]``."""
    if not expr:
        return []
    tokens: list[Token] = []
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
                message = f"Unclosed '[' in path: {expr}"
                raise ValueError(message)
            raw = expr[i + 1 : end].strip()
            if not raw:
                message = f"Empty index in path: {expr}"
                raise ValueError(message)
            try:
                tokens.append(int(raw))
            except ValueError as exc:
                message = f"Invalid index '{raw}' in path: {expr}"
                raise ValueError(message) from exc
            i = end + 1
            continue
        match = _IDENT_RE.match(expr, i)
        if not match:
            message = f"Invalid identifier at: {expr[i:]} in {expr}"
            raise ValueError(message)
        tokens.append(match.group())
        i = match.end()
    return tokens
