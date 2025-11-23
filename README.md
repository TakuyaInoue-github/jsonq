# jsonq

`jsonq` is a tiny Python helper that gives you a jq-like JSON exploration experience without leaving the REPL. Chain together safe lookups, vectorized transforms, and diff/patch utilities while staying in pure Python.

## Highlights
- Pythonic facade `Q()` that wraps dicts, lists, or scalars and keeps method chaining ergonomics.
- Safe access everywhere: missing keys/indices propagate as `_Missing` instead of raising.
- Vectorized operations (`q["key"]`, `q[0]`, `pluck`, `map`, `filter`, `sort_by`, `unique`, `flat`) automatically fan out over lists.
- Path navigation via dotted/`[index]` expressions (`q.path("users[0].profile.email")`) plus `exists`, `coalesce`, and missing-value controls.
- JSON diff/patch helpers for quick snapshots of top-level changes.
- Operator modules (`jsonq.operators`) expose reusable building blocks so you can assemble pipelines beyond the built-in `Q` methods.

## Installation
Requires Python 3.10+. The project is managed with [`uv`](https://docs.astral.sh/uv/) so you get reproducible installs and a cached virtual environment.

```bash
uv sync          # resolve & install into .venv/
source .venv/bin/activate
```

Need a new dependency? Use `uv add <package>` (or `uv add --dev <package>` for development-only tooling); the lock file stays up to date automatically.

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

# Compose operators directly without Q methods
from jsonq import operators as ops

op = ops.pipe(
    ops.access.path("users"),
    ops.sequence.filter_items(lambda u: u["active"]),
    ops.sequence.map_items(lambda u: u["name"]),
)

names = Q({"users": users}).apply(op).list()  # ['Alice', 'Cara']
```

`ops.access`, `ops.sequence`, and `ops.missing` work with `JsonValue` directly, so advanced callers can create reusable operator chains and feed them into `Q.apply()` (or into your own wrappers) for composition-heavy workflows. Diff/patchなど生データ向けのユーティリティは `ops.functional` 配下にまとまっています。

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
- Run tests: `uv run python -m unittest discover -s tests`
- Lint/type-check hooks are not wired yet—see `doc/jsonq_仕様書（mvp）.md` for the full MVP spec and roadmap.

## Roadmap Snapshot
1. `0.1.0`: current MVP (safe access, transforms, diff/patch, REPL ergonomics).
2. `0.2.x`: DSL `query()`, richer aggregations.
3. `0.3.x+`: Nested JSON Patch, NDJSON streaming, YAML/rich integrations, strict typing.

## License
License choice is pending (MIT or Apache-2.0 under consideration). See the spec doc for the latest decision.
