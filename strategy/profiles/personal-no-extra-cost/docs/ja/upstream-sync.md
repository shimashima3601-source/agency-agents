# Upstream更新の取り込み

元ファイルを保持し、個人設定を `strategy/profiles/` と `scripts/personal/` に集約します。
新しいルート直下ディレクトリは既存部門CIとの衝突を避けるため追加していません。
生成物はCommitせず、更新後に再生成します。

履歴のある通常のFork・cloneでは、originを個人Fork、upstreamを元リポジトリに設定し、
変更を保存したうえでupstream/mainを取り込みます。個人ファイルを自動的に勝たせる
競合解決は行いません。AGENTS.mdがUpstreamに追加された場合も内容を統合します。

取り込み後は以下を確認します。

```bash
bash scripts/check-divisions.sh
bash scripts/check-tools.sh
bash scripts/check-runbooks.sh
bash scripts/lint-agents.sh
python3 scripts/personal/validate.py
python3 scripts/personal/catalog_ja.py --check
python3 -m unittest discover -s scripts/personal/tests -v
```

Agentの追加・改名・削除があれば `i18n/ja.json` と `teams.json` を見直し、一覧を再生成します。
本文に追加されたAPI・有料サービス・コマンドの利用条件も確認してください。
`upstream.json` の検証済みコミットと日付を更新し、生成物を再生成します。
元の変換・導入に変更があれば、Upstreamの回帰テストも実行します。

履歴のない配布用スナップショットを使う場合は、同じ基準コミットの通常cloneに
差分パッチを適用してから追従運用へ移行します。スナップショットのローカルindexを
Upstream履歴と誤認しないでください。GitHub上のFork作成と履歴の取得は別の操作です。
