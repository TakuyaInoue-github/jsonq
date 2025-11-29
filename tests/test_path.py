from __future__ import annotations

import pytest

from jsonq import Q
from jsonq.core.path import tokenize_path


def test_tokenize_path_happy_and_error_cases() -> None:
    assert tokenize_path("user[0].profile.email") == ["user", 0, "profile", "email"]
    assert tokenize_path("a[-1]") == ["a", -1]
    assert tokenize_path("") == []

    with pytest.raises(ValueError, match="Unclosed"):
        tokenize_path("a[1")
    with pytest.raises(ValueError, match="Empty index"):
        tokenize_path("a[]")
    with pytest.raises(ValueError, match="Invalid index"):
        tokenize_path("a[foo]")
    with pytest.raises(ValueError, match="Invalid identifier"):
        tokenize_path("1bad")


def test_q_path_invalid_strings_raise() -> None:
    with pytest.raises(ValueError, match="Invalid identifier"):
        Q({"a": 1}).path("1bad")
