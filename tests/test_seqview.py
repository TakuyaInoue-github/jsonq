from __future__ import annotations

from typing import Any

from jsonq.core.missing import MISSING, MissingMode
from jsonq.core.seqview import _SORT_KEY_MAX_DEPTH, SeqView
from jsonq.core.value import JsonValue


def _make_seq(data: list[dict[str, Any]], *, mode: MissingMode = MissingMode.DROP) -> SeqView:
    return SeqView(JsonValue(cast("JSONElement" , data), mode=mode))


def test_sort_by_orders_values_stably() -> None:
    seq = _make_seq(
        [
            {"id": "first", "score": 3},
            {"id": "second", "score": 1},
            {"id": "third", "score": 2},
            {"id": "fourth", "score": 1},
        ]
    )

    out = seq.sort_by(lambda item: item["score"]).unwrap()

    assert [item["id"] for item in out] == ["second", "fourth", "third", "first"]


def test_sort_by_drops_missing_keys_when_in_drop_mode() -> None:
    seq = _make_seq(
        [
            {"id": "has-key", "score": 3},
            {"id": "missing-key"},
            {"id": "low", "score": 1},
        ]
    )

    out = seq.sort_by(lambda item: item.get("score", MISSING)).unwrap()

    assert [item["id"] for item in out] == ["low", "has-key"]


def test_sort_by_keeps_missing_keys_in_keep_mode() -> None:
    seq = _make_seq(
        [
            {"id": "missing-key"},
            {"id": "low", "score": 1},
            {"id": "high", "score": 3},
        ],
        mode=MissingMode.KEEP,
    )

    out = seq.sort_by(lambda item: item.get("score", MISSING)).unwrap()

    assert [item["id"] for item in out] == ["missing-key", "low", "high"]


def _nested_list(depth: int) -> list[Any]:
    payload: Any = 0
    for _ in range(depth):
        payload = [payload]
    return payload


def test_sort_by_skips_elements_when_sort_key_depth_limit_exceeded() -> None:
    deep_value = _nested_list(_SORT_KEY_MAX_DEPTH + 1)
    seq = _make_seq(
        [
            {"id": "too-deep", "score": deep_value},
            {"id": "shallow", "score": 0},
        ]
    )

    out = seq.sort_by(lambda item: item["score"]).unwrap()

    assert [item["id"] for item in out] == ["shallow"]
