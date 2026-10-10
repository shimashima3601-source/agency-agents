# Agency Agents 個人利用ガイド

元のAgency Agentsを保持し、契約済みサービスの範囲で使うための追加レイヤーです。
英語Agent、NEXUS、Runbook、既存ツール対応は削除・翻訳置換していません。
元のREADMEは[こちら](README.md)、ライセンスは[MIT](LICENSE)です。

## personal-no-extra-cost

別名は `personal-free`。主力はChatGPT認証のCodex / Codex Cloudです。
ChatGPT Plusの契約内機能を優先し、Claude Freeと現在のGemini AI契約は
アプリ・Webで手動補助に使います。APIキー、追加契約、クレジット購入、
自動補充、有料APIへの切替は使いません。料金が不明な操作も実行前に停止します。

**これは課金を強制阻止する実行基盤ではありません。** 指示とローカル検証に加え、
サービス側の認証・請求・ネットワーク設定が必要です。成功した生成・配置は、
契約内の残量、Cloud対応、追加請求がないことの証明にはなりません。

## Androidを中心に始める

1. [Android導入ガイド](strategy/profiles/personal-no-extra-cost/docs/ja/setup-android.md)で
   ChatGPT認証と追加課金設定を確認します。PCは必須にしません。
2. [開始プロンプト](strategy/profiles/personal-no-extra-cost/templates/start-prompt.ja.md)を
   Codexに渡して明示的にプロファイルを選択します。
3. [利用方法](strategy/profiles/personal-no-extra-cost/docs/ja/usage.md)に従い、
   必要な役割を順次使います。対応するCloud環境では生成Agentも利用できます。
4. 上限や課金経路の不明点があれば保存して停止します。

Claude・Geminiの補助利用は[手動引継ぎ](strategy/profiles/personal-no-extra-cost/templates/manual-handoff.ja.md)
を使用します。アプリの契約をAPIの利用権として扱いません。

## ローカルファイルの準備

下記はCloud等の作業環境で実行するコマンドです。Android端末にターミナルやCodex CLIを
インストールする必要はありません。Python 3.11以上とBashが必要で、追加Pythonパッケージは不要です。

```bash
python3 scripts/personal/validate.py
python3 scripts/personal/build.py --team core --dry-run
python3 scripts/personal/build.py --team core
python3 scripts/personal/install.py --project /path/to/target-project --dry-run
python3 scripts/personal/install.py --project /path/to/target-project
```

生成物は `dist/personal-no-extra-cost/`、配置先は対象プロジェクトの `.codex/agents/`。
この処理はAIを起動せず、認証・課金設定の変更・ネットワーク接続も行いません。
`Personal / Software Architect` のように生成名を区別します。元の英語名は元ファイルに保持します。
元の生成先 `integrations/codex/agents/` は変更しません。

## 案内

- [日本語Agent一覧](strategy/profiles/personal-no-extra-cost/docs/ja/agents.md)
- [共通方針](strategy/profiles/personal-no-extra-cost/POLICY.md)
- [問題発生時](strategy/profiles/personal-no-extra-cost/docs/ja/troubleshooting.md)
- [Upstream更新](strategy/profiles/personal-no-extra-cost/docs/ja/upstream-sync.md)
- [専門チームの拡張設計](strategy/profiles/personal-no-extra-cost/docs/ja/extensions.md)
- [個人Runbook](strategy/profiles/personal-no-extra-cost/runbooks/codex-personal.md)

チーム名簿は `core`、`app-development`、`japan-equities-research`。後者2つは既存Agentの
選択であり、独自のAndroid・日本株専門Agentを実装したものではありません。
このprofileを明示的に選ばない場合、既存Integrationの通常の使い方を維持します。
