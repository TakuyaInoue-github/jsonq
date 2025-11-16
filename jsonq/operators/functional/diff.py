from __future__ import annotations

import copy
from typing import TYPE_CHECKING, Literal, TypedDict, cast

from jsonq.core.coerce import coerce_json_element

if TYPE_CHECKING:
    from collections.abc import Sequence

    from jsonq.core.core_types import JsonData, JsonElement


class RemoveOp(TypedDict):
    op: Literal["remove"]
    path: str


class AddOp(TypedDict):
    op: Literal["add"]
    path: str
    value: JsonData


class ReplaceOp(TypedDict):
    op: Literal["replace"]
    path: str
    value: JsonData


DiffOp = RemoveOp | AddOp | ReplaceOp


def diff(a: JsonElement, b: JsonElement) -> list[DiffOp]:
    """Shallow dict diff: add/remove/replace on top-level keys."""
    ops: list[DiffOp] = []
    if isinstance(a, dict) and isinstance(b, dict):
        ak, bk = set(a.keys()), set(b.keys())
        ops.extend({"op": "remove", "path": f"/{key}"} for key in sorted(ak - bk))
        ops.extend({"op": "add", "path": f"/{key}", "value": b[key]} for key in sorted(bk - ak))
        ops.extend({"op": "replace", "path": f"/{key}", "value": b[key]} for key in sorted(ak & bk) if a[key] != b[key])
        return ops
    if a != b:
        ops.append({"op": "replace", "path": "/", "value": cast("JsonData", b)})
    return ops


def patch(a: JsonElement, ops: Sequence[DiffOp]) -> JsonElement:
    """Apply shallow ops to a copy; if non-dict and op targets root, replace."""
    current = cast("JsonElement", copy.deepcopy(a))
    for op in ops:
        path = op["path"].lstrip("/")
        if path == "":
            if op["op"] in ("add", "replace"):
                op_with_value = cast(AddOp | ReplaceOp, op)
                current = cast("JsonElement", op_with_value["value"])
            elif op["op"] == "remove":
                current = None
            continue
        if not isinstance(current, dict):
            continue
        if op["op"] == "remove":
            current.pop(path, None)
        elif op["op"] in ("add", "replace"):
            op_with_value = cast(AddOp | ReplaceOp, op)
            current[path] = cast("JsonData", coerce_json_element(op_with_value["value"]))
    return current
