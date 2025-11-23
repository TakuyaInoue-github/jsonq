from __future__ import annotations

from typing import TYPE_CHECKING

from jsonq.core.access import get_item
from jsonq.core.coerce import coerce_json_element
from jsonq.core.missing import MissingMode
from jsonq.core.seqview import _SORT_KEY_MAX_DEPTH, SeqView
from jsonq.core.value import JsonValue

if TYPE_CHECKING:
    from jsonq.core.core_types import JsonElement


def _make_seq(data: JsonElement, *, mode: MissingMode = MissingMode.DROP) -> SeqView:
    return SeqView(JsonValue(coerce_json_element(data), mode=mode))


def _get(item: JsonElement, key: str, *, mode: MissingMode) -> JsonElement:
    return get_item(JsonValue(item, mode=mode), key)


def test_sort_by_orders_values_stably() -> None:
    seq = _make_seq(
        [
            {"id": "first", "score": 3},
            {"id": "second", "score": 1},
            {"id": "third", "score": 2},
            {"id": "fourth", "score": 1},
        ]
    )

    out = seq.sort_by(lambda item: _get(item, "score", mode=MissingMode.DROP)).unwrap()

    assert isinstance(out, list)
    assert [_get(item, "id", mode=MissingMode.DROP) for item in out] == [
        "second",
        "fourth",
        "third",
        "first",
    ]


def test_sort_by_drops_missing_keys_when_in_drop_mode() -> None:
    seq = _make_seq(
        [
            {"id": "has-key", "score": 3},
            {"id": "missing-key"},
            {"id": "low", "score": 1},
        ]
    )

    out = seq.sort_by(lambda item: _get(item, "score", mode=MissingMode.DROP)).unwrap()

    assert isinstance(out, list)
    assert [_get(item, "id", mode=MissingMode.DROP) for item in out] == ["low", "has-key"]


def test_sort_by_keeps_missing_keys_in_keep_mode() -> None:
    seq = _make_seq(
        [
            {"id": "missing-key"},
            {"id": "low", "score": 1},
            {"id": "high", "score": 3},
        ],
        mode=MissingMode.KEEP,
    )

    out = seq.sort_by(lambda item: _get(item, "score", mode=MissingMode.KEEP)).unwrap()

    assert isinstance(out, list)
    assert [_get(item, "id", mode=MissingMode.KEEP) for item in out] == [
        "missing-key",
        "low",
        "high",
    ]


def _nested_list(depth: int) -> JsonElement:
    payload: JsonElement = 0
    for _ in range(depth):
        payload = [payload]
    return payload


def test_sort_by_skips_elements_when_sort_key_depth_limit_exceeded() -> None:
    deep_value = _nested_list(_SORT_KEY_MAX_DEPTH + 1)
    seq = _make_seq(
        coerce_json_element(
            [
                {"id": "too-deep", "score": deep_value},
                {"id": "shallow", "score": 0},
            ]
        )
    )

    out = seq.sort_by(lambda item: _get(item, "score", mode=MissingMode.DROP)).unwrap()
    assert isinstance(out, list)

    assert [_get(item, "id", mode=MissingMode.DROP) for item in out] == ["shallow"]
