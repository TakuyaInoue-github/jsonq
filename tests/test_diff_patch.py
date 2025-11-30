from __future__ import annotations

from typing import TYPE_CHECKING, cast

from jsonq.core.coerce import coerce_json_element
from jsonq.operators.functional.diff import diff, patch

if TYPE_CHECKING:
    from collections.abc import Sequence

    from jsonq.operators.functional.diff import DiffOp


def test_diff_and_patch_roundtrip_and_coercion() -> None:
    before = coerce_json_element({"a": 1, "b": 2})
    after = coerce_json_element({"a": 3, "c": 4})

    ops: Sequence[DiffOp] = diff(before, after)
    assert ops == [
        {"op": "remove", "path": "/b"},
        {"op": "add", "path": "/c", "value": 4},
        {"op": "replace", "path": "/a", "value": 3},
    ]
    assert patch(before, ops) == after

    coerced = patch({}, cast("Sequence[DiffOp]", [{"op": "add", "path": "/arr", "value": (1, 2)}]))
    assert coerced == {"arr": [1, 2]}


def test_diff_and_patch_on_non_dict_root() -> None:
    ops: Sequence[DiffOp] = diff(1, 2)
    assert ops == [{"op": "replace", "path": "/", "value": 2}]
    assert patch(1, ops) == 2

    assert patch(1, cast("Sequence[DiffOp]", [{"op": "add", "path": "/key", "value": 3}])) == 1
    assert patch(1, cast("Sequence[DiffOp]", [{"op": "remove", "path": "/key"}])) == 1

    assert patch({"a": 1}, [{"op": "remove", "path": "/"}]) is None
