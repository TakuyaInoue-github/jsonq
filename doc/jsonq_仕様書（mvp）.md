# jsonq 仕様書（MVP）

最終更新: 2025-11-30 (Asia/Tokyo)

---

## 1. 目的 / スコープ

**jsonq** は、REPL から直感的に JSON を探索・変形・抽出できる Python ミニライブラリです。

* **目的**: Python 内で jq 的な表現力を“Pythonic”なメソッド連鎖で提供する。
* **ユースケース**: データ探索、テストデータ整形、ログ/設定の抽出、簡易集計、差分の可視化。
* **非目標**: フル DSL の再発明、巨大分散処理、jq の完全互換。

---

## 2. 用語

* **JSON**: `dict | list | int | float | str | bool | None`。
* **ベクトル化**: 対象が配列の場合、キー/インデックス操作を各要素に適用して配列を返す規則。
* **安全アクセス**: 存在しないキー/インデックスで例外を出さず「欠損（`<MISSING>`）」扱いとする振る舞い。

---

## 3. ターゲットユーザー

* Python を日常的に使い、REPL や notebook で JSON をいじる開発者/データエンジニア/テストエンジニア。

---

## 4. インストール / 依存

* **依存**: 標準ライブラリのみ（MVP）。
* **将来**: `jmespath` / `rich` / `pyyaml` はオプション依存として連携可。

---

## 5. コア API デザイン

### 5.1 エントリポイント

```python
from jsonq import Q
from jsonq.core.missing import MissingMode

q = Q(data, mode=MissingMode.DROP, strict=False)  # data: dict/list/scalar
```

`mode` で欠損扱いを制御（`DROP`=欠損を捨てる、`KEEP`=欠損を `<MISSING>` として保持、`RAISE`=例外を送出）。`strict=True` も欠損を例外化するショートカット。

### 5.2 値の取り出し

* `Q.get(default=None) -> Any`  : 現在値が欠損なら `default`。
* `Q.list() -> list` : スカラーは単一要素リスト化。欠損は `DROP` なら空リスト、`KEEP` なら `[<MISSING>]`。
* `Q.first(default=None) -> Any` : 先頭要素取得（空なら `default`）。

### 5.3 添字 / ベクトル化

* `q["key"]` :

  * `dict` → `dict[key]` を安全に取得し、欠損はモードに従う。
  * `list` → 各要素へ同じ取得を適用し、一次元にフラット化（`DROP` 時は欠損を除外）。
* `q[index]` / `q[slice]` : リストのインデックス/スライス取得（非リストは欠損扱い）。
* `q.pluck(key)` は `q[key]` の糖衣。

### 5.4 パスアクセス

* `q.path("users[0].profile.email") -> Q`
* 存在しない経路はモードに従って欠損扱い。`strict=True` なら例外。
* パス文字列が不正なら `ValueError`。
* `q.exists(path: str) -> bool`

**パス構文（MVP）**

* 識別子: `[A-Za-z_][A-Za-z0-9_]*`
* インデックス: `[<int>]`（負数可）
* ドット区切り: `a.b.c` をトークン列へ変換して逐次適用。

### 5.5 変形 / 絞り込み / 集計

* `q.map(fn)` : 各要素に関数適用。例外は欠損として扱う。
* `q.filter(pred)` / `q.reject(pred)` : 述語例外は偽判定として扱う。
* `q.sort_by(keyfn)` : 安定ソート。欠損キーは `DROP` で除外、`KEEP` で先頭に残す。極端なネストは安全のためスキップ。
* `q.unique(keyfn=None)` : 重複排除（欠損保持/除外はモード依存）。
* `q.flat()` : 一段フラット化。

### 5.6 整形 / シリアライズ

* `q.to_json(indent: Optional[int]=None) -> str` : `<MISSING>` が含まれる場合は `ValueError`。
* `q.pretty(indent: int=2) -> None`

### 5.7 差分 / パッチ（MVP）

* `Q.diff(a, b) -> List[Op]` : `dict` 直下キーの `add/replace/remove` を生成。`dict` 以外はルート `/` に対する `replace`。
* `Q.patch(a, ops) -> JSON` : `diff` 結果を非破壊適用。`/` への `remove` で `None` を返す。

**Op 形式（MVP）**

```json
{"op": "add|remove|replace", "path": "/<key>|/", "value"?: any}
```

### 5.8 オペレーター（関数型 API）

* `jsonq.operators.JsonOperator` は `JsonValue -> JsonValue` の Protocol。
* `operators.pipe(*ops)` で合成し、`Q.apply(op)` で適用。
* `operators.access/sequence/missing/functional` に低レベル部品を配置。

---

## 6. エラー方針

* **基本**: ランタイム例外は極力吞み込み、`<MISSING>` として扱う（`MissingMode.DROP` なら除外）。
* **明示的例外**: `map/filter/sort_by` 中のユーザ関数で発生した例外は抑制して要素を落とす/欠損化。欠損アクセスを例外にしたい場合は `mode=MissingMode.RAISE` または `strict=True` を利用。

---

## 7. REPL 使用例

```python
from jsonq import Q

users = [
  {"name": "Alice", "age": 30, "active": True},
  {"name": "Bob",   "age": 22, "active": False},
  {"name": "Cara",  "age": 27, "active": True},
]

# 有効ユーザーの名前（年齢昇順）
Q(users).filter(lambda u: u["active"]) \
        .sort_by(lambda u: u["age"])   \
        .pluck("name").list()  # => ['Cara', 'Alice']

# 安全パスアクセス
profile_email = Q({"users": users}).path("users[10].profile.email").get("N/A")

# 集計例
avg_age = sum(Q(users).pluck("age").list()) / len(users)

# 差分
ops = Q.diff({"a":1, "b":2}, {"a":1, "c":3})
patched = Q.patch({"a":1, "b":2}, ops)
```

---

## 8. アーキテクチャ / 実装方針（MVP）

* **パッケージ構成**:
  * `jsonq/api.py` : 公開ファサード `Q` と簡易関数 `Jx`。
  * `jsonq/core/` : `JsonValue`（値+MissingMode+strict）、`missing` センチネルと判定、`access`（安全アクセス）、`path`（トークナイザ）、`seqview`（シーケンス変換）、`coerce`（型正規化）、`dictview`、型エイリアス。
  * `jsonq/operators/` : `base`（JsonOperator/pipe）、`access`/`sequence`/`missing`（Q メソッドの実体）、`functional`（diff/serialize）。
* **主要コンポーネント**:
  * `JsonValue` : dataclass で値と欠損ポリシーを束ねる。
  * `_tokenize_path` : シンプルな文字列 → トークン変換。
  * `SeqView` : map/filter/sort_by/unique/flat のモード尊重実装。
* **拡張ポイント**:
  * DSL クエリ `q.query("...")` を追加し、内部で自前/`jmespath` を切替可能に（将来）。

---

## 9. 互換性 / 型

* **Python**: 3.10+。
* **型**: `typing` ベースで公開 API も型付き。`py.typed` 配布は未設定（将来）。

---

## 10. パフォーマンス / 制約

* **前提**: 数十 MB 程度までのインメモリ処理。
* **ストリーム**: NDJSON ストリーム処理は将来追加（`iter_loads`）。

---

## 11. セキュリティ

* 任意関数を受け取る API（`map/filter/sort_by`）は REPL 前提。信頼できる環境で使用。

---

## 12. テスト戦略

* **単体テスト**: パス解決、ベクトル化規則、欠損伝播、差分/パッチ、シリアライズ。
* **プロパティテスト**: `patch(diff(a,b)) == b`、欠損耐性。
* **サンプル JSON**: 必要に応じて `tests/fixtures/` に配置（現状は最小限）。
* **実行**: `uv run pytest`

---

## 13. バージョニング / リリース

* **バージョン**: SemVer（MVP = `0.1.0`）。
* **互換性ポリシー**: 0.x 期間は破壊的変更の可能性あり。1.0 で安定。

---

## 14. ロードマップ（概略）

1. **0.1.0 (MVP)**: 本仕様どおり。
2. **0.2.x**: DSL `query()`、`exists_all/any`、`group_by`、`count_by`。
3. **0.3.x**: JSON Patch RFC 6902 準拠のネスト差分、NDJSON ストリーム。
4. **0.4.x**: `to_yaml()/from_yaml()`、`rich` 連携 `q.tree()/q.table()`。
5. **0.5.x**: Pydantic 連携、`py.typed` 配布、型安全 API の拡充。

---

## 15. ライセンス / 著作権

* **案**: MIT または Apache-2.0。

---

## 16. 付録 A: パス構文（MVP） EBNF（擬似）

```
path    := segment {'.' segment} ;
segment := ident | index ;
ident   := /[A-Za-z_][A-Za-z0-9_]*/ ;
index   := '[' int ']' ;   # int は負数可
```

---

## 17. クイックリファレンス

* **作成**: `Q(data)`
* **取り出し**: `.get()`, `.first()`, `.list()`
* **アクセス**: `q["key"]`, `q[0]`, `q[1:3]`, `.path("a.b[0].c")`, `.exists("a.b")`
* **変形**: `.map(fn)`, `.pluck(key)`, `.flat()`
* **絞込/ソート**: `.filter(pred)`, `.reject(pred)`, `.sort_by(fn)`, `.unique([fn])`
* **欠損制御**: `.keep_missing()`, `.drop_missing()`, `.fill_missing(x)`, `.assert_present()`, `.coalesce(*paths)`
* **整形**: `.to_json([indent])`, `.pretty([indent])`（欠損が残っていると `ValueError`）
* **差分/パッチ**: `Q.diff(a,b)`, `Q.patch(a,ops)`

---

## 18. 付録 B: サンプル JSON と API 利用例

(※ ここは前回追記した EC/ログ/設定の例を保持)

---

## 19. `MISSING` の扱い方針

* **シングルトン**: `from jsonq.core.missing import MISSING`。`bool(MISSING) == False`。
* **モード**: `DROP` で除外、`KEEP` で保持、`RAISE/strict` で例外。
* **API**: `.keep_missing() / .drop_missing() / .fill_missing(v) / .assert_present() / .coalesce(*paths, default=None)`。
* **シリアライズ**: `<MISSING>` が残ったまま `to_json/pretty` を呼ぶと `ValueError`。

---

## 20. 未決事項 (Open Questions)

* `.query()` DSL の文法レベル（JSONPath vs JMESPath vs 独自）
* JSON Patch のネスト対応方針（RFC 6902 への寄せ方）
