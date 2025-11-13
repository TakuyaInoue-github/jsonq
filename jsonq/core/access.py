from .core_types import JsonElement
from .missing import MISSING, MissingMode, is_missing
from .value import JsonValue


def _flatten_once(seq: list[JsonElement], *, drop_missing: bool) -> list[JsonElement]:
    out: list[JsonElement] = []
    for item in seq:
        if isinstance(item, list):
            out.extend(item)
        elif drop_missing and is_missing(item):
            continue
        else:
            out.append(item)
    return out


def _handle_missing(mode: MissingMode, *, exc: Exception | None = None) -> JsonElement:
    if mode is MissingMode.RAISE:
        if exc is not None:
            raise exc
        raise KeyError("missing")
    return MISSING


def _getitem_list(val: list[JsonElement], key: str | int | slice, mode: MissingMode) -> JsonElement | list[JsonElement]:
    if isinstance(key, int | slice):
        try:
            return val[key]
        except (IndexError, TypeError) as exc:
            return _handle_missing(mode, exc=exc)
    if isinstance(key, str):
        results: list[JsonElement] = []
        missing_seen = False
        for el in val:
            result = el.get(key, MISSING) if isinstance(el, dict) else MISSING
            if is_missing(result):
                missing_seen = True
            results.append(result)
        if missing_seen and mode is MissingMode.RAISE:
            raise KeyError(key)
        drop = mode is MissingMode.DROP
        return _flatten_once(results, drop_missing=drop)
    return _handle_missing(mode)


def _getitem_dict(val: dict[str, JsonElement], key: str | int | slice, mode: MissingMode) -> JsonElement | list[JsonElement]:
    if isinstance(key, str):
        if key in val:
            return val[key]
        return _handle_missing(mode)
    return _handle_missing(mode)


def get_item(v: JsonValue, key: str | int | slice) -> JsonElement | list[JsonElement]:
    """Vectorized safe item access based on current MissingMode."""
    # TODO: implement coercion rules
    raise NotImplementedError


def apply_path(v: JsonValue, tokens: tuple[str | int, ...]) -> JsonElement:
    """Apply a tokenized path expression to a JsonValue."""
    # TODO: implement coercion rules
    raise NotImplementedError
