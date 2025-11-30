from __future__ import annotations

from typing import TYPE_CHECKING, cast

from jsonq.core.access import get_item
from jsonq.core.coerce import coerce_json_element
from jsonq.core.missing import MISSING, MissingMode
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


def test_sort_by_allows_boundary_depth_limit() -> None:
    deep_value = _nested_list(_SORT_KEY_MAX_DEPTH)
    seq = _make_seq(coerce_json_element([{"id": "deep", "score": deep_value}]), mode=MissingMode.DROP)
    out = seq.sort_by(lambda item: _get(item, "score", mode=MissingMode.DROP)).unwrap()
    assert out == [{"id": "deep", "score": deep_value}]


def test_sort_by_keep_mode_orders_missing_first_but_stable() -> None:
    data = [
        {"id": "missing1"},
        {"id": "low", "score": 1},
        {"id": "missing2"},
        {"id": "high", "score": 2},
    ]
    seq = _make_seq(data, mode=MissingMode.KEEP)
    out = seq.sort_by(lambda item: _get(item, "score", mode=MissingMode.KEEP)).unwrap()
    assert isinstance(out, list)
    assert [_get_id(item) for item in out] == ["missing1", "missing2", "low", "high"]


def test_seqview_map_and_predicate_errors_are_soft() -> None:
    def risky(value: JsonElement) -> JsonElement:
        x = cast("int", value)
        if x == 0:
            raise RuntimeError("boom")
        return x * 2

    drop_mode = SeqView(JsonValue([1, 0, 2], mode=MissingMode.DROP)).map(risky).to_value()
    assert drop_mode.as_list() == [2, 4]

    keep_mode = SeqView(JsonValue([1, 0], mode=MissingMode.KEEP)).map(risky).to_value().as_list()
    assert keep_mode[0] == 2
    assert JsonValue.is_missing(keep_mode[1])

    def flaky_pred(_: object) -> bool:
        raise RuntimeError("predicate failed")

    seq = SeqView(JsonValue([1, 2], mode=MissingMode.DROP))
    assert seq.filter(flaky_pred).to_value().unwrap() == []
    assert seq.reject(flaky_pred).to_value().unwrap() == [1, 2]


def test_unique_and_flat_with_missing_behaviors() -> None:
    seq_keep = SeqView(JsonValue(coerce_json_element([1, 1, MISSING, MISSING]), mode=MissingMode.KEEP))
    assert seq_keep.unique().unwrap() == [1, MISSING]

    seq_drop = SeqView(JsonValue(coerce_json_element([1, 1, MISSING]), mode=MissingMode.DROP))
    assert seq_drop.unique().unwrap() == [1]

    seq_flat = SeqView(JsonValue(coerce_json_element([1, [2, MISSING], MISSING]), mode=MissingMode.DROP))
    assert seq_flat.flat().unwrap() == [1, 2, MISSING]


def _get_id(item: object) -> str:
    assert isinstance(item, dict)
    return item["id"]
