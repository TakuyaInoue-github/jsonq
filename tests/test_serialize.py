from __future__ import annotations

import json

import pytest

from jsonq.core.missing import MISSING
from jsonq.operators.functional import serialize


def test_serialize_rejects_missing_values() -> None:
    data = {"a": [1, MISSING]}
    with pytest.raises(ValueError, match="Missing values"):
        serialize.ensure_serializable(data)

    assert serialize.to_json({"a": 1}, indent=None) == json.dumps({"a": 1}, ensure_ascii=False)


def test_pretty_prints_json(capsys: pytest.CaptureFixture[str]) -> None:
    serialize.pretty({"a": 1}, indent=0)
    captured = capsys.readouterr().out
    assert captured.strip() == '{\n"a": 1\n}'
