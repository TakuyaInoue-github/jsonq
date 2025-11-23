from .value import JsonValue


class DictView:
    """Dict-focused helpers (placeholder for future extensions)."""

    def __init__(self, v: JsonValue) -> None:
        self._v = v

    def keys(self) -> list[str]:
        data = self._v.unwrap()
        if isinstance(data, dict):
            return list(data.keys())
        return []
