# nlk (Python)

[nlink-jp](https://github.com/nlink-jp) プロジェクト向けの軽量LLMユーティリティツールキット。Python版。

LLM API呼び出しの「周辺」に特化した小さな独立モジュール群。外部依存ゼロ。

Go版: [nlk](https://github.com/nlink-jp/nlk)

## モジュール

| モジュール | 説明 |
|-----------|------|
| [`guard`](src/nlk/guard.py) | ノンスタグXMLラッピングによるプロンプトインジェクション防御（128ビットノンス） |
| [`jsonfix`](src/nlk/jsonfix.py) | 再帰下降パーサーによるJSON修復 |
| [`strip`](src/nlk/strip.py) | LLM思考/推論タグの除去（DeepSeek R1, Qwen, Gemma 4等） |
| [`backoff`](src/nlk/backoff.py) | ジッター付き指数バックオフ待ち時間計算 |
| [`validate`](src/nlk/validate.py) | ルールベースのLLM出力バリデーション |

[リファレンスマニュアル](docs/ja/reference.ja.md)に完全なAPIドキュメントがあります。

## インストール

```bash
pip install nlk
```

## 設計方針

- **ツールボックスであってフレームワークではない** — 各モジュールは独立
- **LLM API抽象化なし** — LLM呼び出しはアプリの責務
- **外部依存ゼロ** — 標準ライブラリのみ
- **純粋関数** — 副作用なし

## ライセンス

MIT
