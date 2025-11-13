from typing import TypeAlias

from jsonq.core.missing import MissingType

# Core JSON-compatible primitives
JsonPrimitive: TypeAlias = None | bool | int | float | str

# Recursive JSON structures
JsonArray: TypeAlias = list["JsonValue"]
JsonObject: TypeAlias = dict[str, "JsonValue"]
JsonValue: TypeAlias = JsonPrimitive | JsonArray | JsonObject

# Publicly exported element type (JSON or the missing sentinel)
JsonElement: TypeAlias = JsonValue | MissingType
