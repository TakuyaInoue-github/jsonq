from __future__ import annotations

from typing import Any, Dict, List

Op = Dict[str, Any]


def diff(a: Any, b: Any) -> List[Op]:
    """Shallow dict diff: add/remove/replace on top-level keys."""

    ops: List[Op] = []
    if isinstance(a, dict) and isinstance(b, dict):
        ak, bk = set(a.keys()), set(b.keys())
        for key in sorted(ak - bk):
            ops.append({"op": "remove", "path": f"/{key}"})
        for key in sorted(bk - ak):
            ops.append({"op": "add", "path": f"/{key}", "value": b[key]})
        for key in sorted(ak & bk):
            if a[key] != b[key]:
                ops.append({"op": "replace", "path": f"/{key}", "value": b[key]})
        return ops
    if a != b:
        ops.append({"op": "replace", "path": "/", "value": b})
    return ops


def patch(a: Any, ops: List[Op]) -> Any:
    """Apply shallow ops to a copy; if non-dict and op targets root, replace."""

    import copy

    current = copy.deepcopy(a)
    for op in ops:
        path = op["path"].lstrip("/")
        if path == "":
            if op["op"] in ("add", "replace"):
                current = op.get("value")
            elif op["op"] == "remove":
                current = None
            continue
        if not isinstance(current, dict):
            continue
        if op["op"] == "remove":
            current.pop(path, None)
        elif op["op"] in ("add", "replace"):
            current[path] = op.get("value")
    return current
