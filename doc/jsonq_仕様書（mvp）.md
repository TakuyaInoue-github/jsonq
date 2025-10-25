# jsonq 仕様書（MVP）

最終更新: 2025-10-04 (Asia/Tokyo)

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
* **安全アクセス**: 存在しないキー/インデックスで例外を出さず「欠損（_Missing）」扱いとする振る舞い。

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
q = Q(data)  # data: dict/list/scalar
```

### 5.2 値の取り出し

* `Q.get(default=None) -> Any`  : 欠損は `default` を返す。
* `Q.list() / Q.to_list() -> list` : スカラーは単一要素リスト化。
* `Q.first(default=None) -> Any` : 先頭要素取得。

### 5.3 添字 / ベクトル化

* `q["key"]` :

  * `dict` → `dict.get("key", _Missing)`
  * `list` → 各要素に対して上記を適用し、一次元にフラット化（`_Missing` は除外）。
* `q[index]` : `list` のインデックス取得（`dict` は `_Missing`）。
* `q.pluck(key)` は `q[key]` の糖衣。

### 5.4 パスアクセス

* `q.path("users[0].profile.email") -> Q`
* 存在しない経路は `_Missing`。
* `q.exists(path: str) -> bool`

**パス構文（MVP）**

* 識別子: `[A-Za-z_][A-Za-z0-9_]*`
* インデックス: `[<int>]`（負数可）
* ドット区切り: `a.b.c` をトークン列へ変換して逐次適用。

### 5.5 変形 / 絞り込み / 集計

* `q.map(fn)` : 各要素に関数適用。
* `q.filter(pred)` / `q.reject(pred)` : 述語でフィルタ。
* `q.sort_by(keyfn)` : 安定ソート。
* `q.unique(keyfn=None)` : 重複排除。
* `q.flat()` : 一段フラット化。

### 5.6 整形 / シリアライズ

* `q.to_json(indent: Optional[int]=None) -> str`
* `q.pretty(indent: int=2) -> None`

### 5.7 差分 / パッチ（MVP）

* `Q.diff(a, b) -> List[Op]` : `dict` 直下キーの `add/replace/remove` を生成（ネスト/配列は将来対応）。
* `Q.patch(a, ops) -> JSON` : `diff` 結果を非破壊適用。

**Op 形式（MVP）**

```json
{"op": "add|remove|replace", "path": "/<key>|/", "value"?: any}
```

---

## 6. エラー方針

* **基本**: ランタイム例外は極力吞み込み、`_Missing` として扱う。
* **明示的例外**: `map/filter/sort_by` 中のユーザ関数で発生した例外は抑制して要素を落とす（MVP）。将来、`strict=True` で伝播オプションを追加。

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

* **ファイル構成**: 単一モジュール `jsonq.py`。
* **主要コンポーネント**:

  * `Q` クラス（薄いラッパ）
  * `_Missing` センチネル
  * `_tokenize_path`（軽量トークナイザ）
  * ベクトル化ユーティリティ（`_get_item`, `_flatten_once`, `_as_list`）
* **拡張ポイント**:

  * DSL クエリ `q.query("...")` を追加し、内部で自前/`jmespath` を切替可能に。

---

## 9. 互換性 / 型

* **Python**: 3.9+（`from __future__ import annotations` 前提）。
* **型**: `typing` をフル活用。公開 API は `py.typed` 化（将来）。

---

## 10. パフォーマンス / 制約

* **前提**: 数十 MB 程度までのインメモリ処理。
* **ストリーム**: NDJSON ストリーム処理は将来追加（`iter_loads`）。

---

## 11. セキュリティ

* 任意関数を受け取る API（`map/filter/sort_by`）は REPL 前提。信頼できる環境で使用。

---

## 12. テスト戦略

* **単体テスト**: パス解決、ベクトル化規則、欠損伝播、差分/パッチ。
* **プロパティテスト**: `patch(diff(a,b)) == b`、欠損耐性。
* **サンプル JSON**: 小規模フィクスチャを `tests/fixtures/` に配置。

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
5. **0.5.x**: Pydantic 連携、`strict` モード、型安全 API。

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
* **アクセス**: `q["key"]`, `q[0]`, `.path("a.b[0].c")`, `.exists("a.b")`
* **変形**: `.map(fn)`, `.pluck(key)`, `.flat()`
* **絞込/ソート**: `.filter(pred)`, `.reject(pred)`, `.sort_by(fn)`, `.unique([fn])`
* **整形**: `.to_json([indent])`, `.pretty([indent])`
* **差分/パッチ**: `Q.diff(a,b)`, `Q.patch(a,ops)`

---

## 18. 付録 B: サンプル JSON と API 利用例

(※ ここは前回追記した EC/ログ/設定の例を保持)

---

## 19. `_Missing` の扱い方針

### デフォルト規則

* **探索時は隠蔽 (drop)** : ベクトル化や `pluck`・`path` の結果で `_Missing` は除外。
* **to_json()** : 内部に `_Missing` が残っていた場合は `ValueError` を送出。
* **sort_by / unique** : `_Missing` は除外。`keep_missing=True` 指定で保持可能。

### 公開 API

* `from jsonq import Q, MISSING`
* `keep_missing()` : 以降の演算で `_Missing` を保持するモード。
* `drop_missing()` : 既定の除外モードに戻す。
* `fill_missing(value)` : `_Missing` を指定値に置換。
* `assert_present()` : 欠損があれば例外。
* `coalesce(*paths, default=None)` : 最初に存在するパスの値を返す。

### モード切替

* 局所チェーン: `.keep_missing()` / `.drop_missing()` を差し込む。
* グローバル: `with q.missing_policy("keep"):` で文脈切替可能に。
* `Q(data, strict=True)` : strict モードでは欠損アクセスで即例外。

### 等値・真偽・比較

* `MISSING is MISSING` (シングルトン)
* `bool(MISSING) == False`
* `MISSING != None` (区別)
* 大小比較演算はエラー。

### 相互運用

* pandas 連携時は `_Missing`→`pd.NA`
* `to_dict(drop_missing=True|False, fill=None)` で制御可能。

---

## 20. 未決事項 (Open Questions)

* `.query()` DSL の文法レベル（JSONPath vs JMESPath vs 独自）
* `sort_by` の None/欠損キーの比較規則
