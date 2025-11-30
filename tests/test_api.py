from __future__ import annotations

from jsonq import Q
from jsonq.core.coerce import coerce_json_element
from jsonq.core.missing import MISSING, MissingMode
from jsonq.core.value import JsonValue


def test_q_facade_preserves_mode_and_exists_coalesce_behaviors() -> None:
    q = Q(JsonValue(coerce_json_element(["a", MISSING]), mode=MissingMode.KEEP))
    assert JsonValue.is_missing(q.list()[1])

    dropped = q.drop_missing().list()
    assert dropped == ["a"]

    data = coerce_json_element({"users": [{"name": "alice"}]})
    assert Q(data).exists("users[0].name") is True
    assert Q(data).exists("users[1].name") is False

    assert Q(data).coalesce("users[1].name", "users[0].name", default="n/a") == "alice"
    assert Q(data).coalesce("users[10].name", default="n/a") == "n/a"


def test_q_first_and_get_defaults() -> None:
    assert Q([]).first("fallback") == "fallback"
    assert Q(JsonValue(MISSING, mode=MissingMode.DROP)).first("x") == "x"

    kept = Q(JsonValue(MISSING, mode=MissingMode.KEEP))
    assert kept.get("default") == "default"
