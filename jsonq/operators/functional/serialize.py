import json

from jsonq.core.core_types import JsonElement
from jsonq.core.missing import is_missing


def ensure_serializable(x: JsonElement) -> None:
    if _contains_missing(x):
        raise ValueError("Missing values present; fill or drop before serialization")


def to_json(x: JsonElement, *, indent: int | None = None) -> str:
    ensure_serializable(x)
    return json.dumps(x, ensure_ascii=False, indent=indent)


def pretty(x: JsonElement, *, indent: int = 2) -> None:
    print(to_json(x, indent=indent))


def _contains_missing(x: JsonElement) -> bool:
    if is_missing(x):
        return True
    if isinstance(x, list):
        return any(_contains_missing(item) for item in x)
    if isinstance(x, dict):
        return any(_contains_missing(value) for value in x.values())
    return False
