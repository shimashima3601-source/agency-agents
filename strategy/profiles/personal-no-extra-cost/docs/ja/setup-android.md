# Android中心の導入

## アカウント側の確認

- ChatGPTアカウントでCodexにログインします。OpenAI API認証は選びません。
- 現在のPlus契約でCodex Cloudが利用可能か確認します。提供状況やアカウントにより異なります。
- クレジットの追加購入・自動補充を有効にしません。既に有効なら設定画面で無効化します。
- 購入済みクレジットを消費しない契約内利用を確認します。その区別を確認できない場合は
  profileの利用を開始せず停止します。存在しない「クレジット禁止設定」を想定しません。
- 新しいSaaS、Cloud Billing、有料試用、LLM APIキーを登録しません。
- GitHubは対象リポジトリへの必要な権限だけ接続します。

## Cloudを準備する

Androidアプリで利用できる既存環境を選択します。新規環境作成はWeb側の設定画面が
必要な場合があります。Androidブラウザから利用できるか実機で確認してください。
利用できない機能をPC購入・新規有料サービス導入で補完することはしません。

Forkと開発対象リポジトリを接続し、Python 3.11以上とBashを確認します。
このprofileの生成にモデルAPI・外部SaaS・追加Pythonパッケージは不要です。
環境の自動セットアップにも課金禁止方針を渡してください。Agent読込より前に実行される
セットアップは、Agentの指示だけでは保護できません。

ホストが対応している場合は、必要な公開資料・パッケージ配布先だけをネットワーク許可します。
請求可能な資格情報、LLM APIキー、有料サービスの接続を環境へ追加しません。
GitHub認証はLLM APIキーとは区別します。未知のネットワーク先はまず用途・料金を確認します。

## 読込確認

生成・配置後に、選んだ `Personal / ...` Agentが認識され、共通方針を参照できるか確認します。
本実装ではCodex CloudのカスタムAgent読込は実機検証していません。
対応しない場合は、開始プロンプトと元Markdownを読み込み、役割を順次適用します。
独立したAgentが起動した・テストが完了したと偽って報告しません。

実行前確認をローカルJSONに残す場合は `account.personal.local.json` 等を使います。
これは当日のユーザー確認記録であり、ホストの請求状態を自動取得する機能ではありません。
確認不能な項目をtrueにしないでください。

```json
{
  "schema_version": 1,
  "confirmed_on": "YYYY-MM-DD",
  "chatgpt_auth": true,
  "included_only_usage": true,
  "auto_reload_disabled": true,
  "no_paid_credit_use": true,
  "cloud_access_verified": true
}
```

```bash
python3 scripts/personal/validate.py --check-runtime --attestation /private/path/account.personal.local.json
```

API環境変数があれば名前だけを表示して停止します。値は読み出して表示しません。
この検査は保存済み認証ファイル、全プロバイダー設定、UI状態、請求残高を網羅しません。
別プロジェクトへ確認記録を置く場合もGitに追加しないでください。

公式参照：[Codex契約](https://help.openai.com/en/articles/11369540-using-codex-with-your-chatgpt-plan)、
[クレジット](https://help.openai.com/en/articles/12642688-using-credits-for-flexible-usage-in-chatgpt-personal-plans)、
[Cloud](https://developers.openai.com/codex/cloud/)。仕様が変わったら再確認します。
