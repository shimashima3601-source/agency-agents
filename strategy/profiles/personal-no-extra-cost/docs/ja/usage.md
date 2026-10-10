# 利用方法

## 選択と生成

開始プロンプトで `personal-no-extra-cost` または `personal-free` を明示します。
全Agentを一度に実行せず、現在の段階に必要な役割だけを使います。

```bash
python3 scripts/personal/validate.py --profile personal-free --team app-development
python3 scripts/personal/build.py --profile personal-free --team app-development --dry-run
python3 scripts/personal/build.py --profile personal-free --team app-development
```

`core` は調査・設計・レビュー、`app-development` は既存の開発・QA、
`japan-equities-research` は既存の財務・投資リサーチ・統合役です。
名簿は元ファイルIDで参照し、ツールの表示名や生成slugに依存しません。

ビルダーはUpstreamの `convert.sh --tool codex --out ...` を一時出力先で実行し、
元のTOMLに共通方針を付けます。選択した個人Agentだけが配置対象です。
元コンバーターは全件変換するため、生成と全件実行は同じではありません。
名前を `Personal / 元英語名`、ファイルを `personal-<slug>.toml` に区別します。

既定の出力先は `dist/personal-no-extra-cost/`。`--out` は専用の生成ディレクトリです。
既存の管理外ディレクトリや、編集された生成物への上書きを拒否します。
再生成時は元Agentと共通方針のハッシュを記録します。

## 配置

```bash
python3 scripts/personal/install.py --project /path/to/target-project --dry-run
python3 scripts/personal/install.py --project /path/to/target-project
```

別の生成先を使った場合は `--source /path/to/output` を指定します。
対象プロジェクトは既存ディレクトリである必要があります。
配置先 `.codex/agents/` の `.agency-personal.json` に所有ファイルを記録します。
管理外の同名ファイル、編集・削除された所有ファイル、シンボリックリンクは拒否します。
チーム変更時は以前の未編集の所有ファイルだけを削除します。無関係なAgentは残します。
同時に同じ配置先を更新しないでください。

対象プロジェクト側でも `.codex/agents/` をGit除外してください。鍵・残高・個人資料を
生成物や公開Forkに混ぜません。配置はCodexの起動・ログイン・課金設定の変更を行いません。

## 操作条件の確認

```bash
python3 scripts/personal/validate.py --action codex.subscription
python3 scripts/personal/validate.py --action llm.api
```

前者は契約内利用などの前提を表示するだけです。後者と未知の操作は非ゼロ終了で停止します。
このチェッカーが任意コマンドやAPI呼び出しを自動的に捕捉するわけではありません。
実行するホスト側にも共通方針・権限制約を渡します。

## 起動と引継ぎ

読み込みを確認できた環境では「Personal / Code Reviewerを使ってレビューしてください」等と
指定します。元の制約なしAgentへ自動的に切り替えません。
モデル名を固定せず、現在の契約で利用できるモデルを継承します。
同時実行は契約内残量と明示的な指示を確認できる場合だけ行います。

Claude Free・Gemini補助は手動引継ぎテンプレートを使います。回答はCodexに戻して統合します。
無料枠が尽きたら停止または別の契約内手段に縮退します。有料経路で代替しません。
最大3回の試行、品質ゲート、未検証範囲の明示、進捗保存を維持します。
