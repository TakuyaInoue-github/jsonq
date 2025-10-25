# jsonq

`jsonq` is a tiny Python helper that gives you a jq-like JSON exploration experience without leaving the REPL. Chain together safe lookups, vectorized transforms, and diff/patch utilities while staying in pure Python.

## Highlights
- Pythonic facade `Q()` that wraps dicts, lists, or scalars and keeps method chaining ergonomics.
- Safe access everywhere: missing keys/indices propagate as `_Missing` instead of raising.
- Vectorized operations (`q["key"]`, `q[0]`, `pluck`, `map`, `filter`, `sort_by`, `unique`, `flat`) automatically fan out over lists.
- Path navigation via dotted/`[index]` expressions (`q.path("users[0].profile.email")`) plus `exists`, `coalesce`, and missing-value controls.
- JSON diff/patch helpers for quick snapshots of top-level changes.

## Installation
Requires Python 3.10+ and only uses the standard library.

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
```

## Quick Start
```python
from jsonq import Q

users = [
    {"name": "Alice", "age": 30, "active": True},
    {"name": "Bob",   "age": 22, "active": False},
    {"name": "Cara",  "age": 27, "active": True},
]

q = Q(users)

active_names = (
    q.filter(lambda u: u["active"])
     .sort_by(lambda u: u["age"])
     .pluck("name")
     .list()
)  # ['Cara', 'Alice']

profile_email = Q({"users": users}).path("users[10].profile.email").get("N/A")
```

## Working with Missing Values
- `_Missing` is carried through the chain, letting you defer error handling.
- Switch policies with `.keep_missing()`, `.drop_missing()`, `.fill_missing(value)`, or `.assert_present()`.
- `coalesce("path.one", "fallback.path", default=None)` returns the first present value.

## Diff / Patch
```python
from jsonq import Q

ops = Q.diff({"a": 1}, {"a": 2, "b": 3})
# [
#   {"op": "replace", "path": "/a", "value": 2},
#   {"op": "add", "path": "/b", "value": 3},
# ]

patched = Q.patch({"a": 1}, ops)  # {"a": 2, "b": 3}
```

## Development
- Run tests: `pytest`
- Lint/type-check hooks are not wired yet—see `doc/jsonq_仕様書（mvp）.md` for the full MVP spec and roadmap.

## Roadmap Snapshot
1. `0.1.0`: current MVP (safe access, transforms, diff/patch, REPL ergonomics).
2. `0.2.x`: DSL `query()`, richer aggregations.
3. `0.3.x+`: Nested JSON Patch, NDJSON streaming, YAML/rich integrations, strict typing.

## License
License choice is pending (MIT or Apache-2.0 under consideration). See the spec doc for the latest decision.
