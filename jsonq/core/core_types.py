from typing import TypeAlias

from jsonq.core.missing import MissingType

# Core JSON-compatible primitives
JsonPrimitive: TypeAlias = None | bool | int | float | str

# Recursive JSON structures
JsonArray: TypeAlias = list["JsonData"]
JsonObject: TypeAlias = dict[str, "JsonData"]
JsonData: TypeAlias = JsonPrimitive | JsonArray | JsonObject

# Publicly exported element type (JSON or the missing sentinel)
JsonElement: TypeAlias = JsonData | MissingType
