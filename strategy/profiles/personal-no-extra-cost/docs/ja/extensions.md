# 専門チームの拡張設計

独自Agentはまだ実装していません。teams.jsonは既存定義の参照だけです。
最初は役割・入力・成果物・根拠・品質ゲートをRunbookで設定し、不足する専門性だけ追加します。

## 日本株

| 役割 | 再利用・追加方針 |
|---|---|
| 投資リサーチ | Investment Researcherを再利用 |
| 財務分析 | Financial Analystを再利用 |
| 決算分析 | 上記2つに期間、会計基準、会社予想との比較を補足 |
| IR分析 | 日本企業の開示・経営説明の専門定義を将来追加 |
| 日本株市場分析 | 東証区分・業種・為替・政策等の専門定義を将来追加 |
| テクニカル分析 | 株価補正・指標・検証条件の専門定義を将来追加 |
| 需給分析 | 信用残・空売り・自己株買い等の専門定義を将来追加 |
| リスク分析 | 投資・財務Agentに日本市場の補足 |
| Bull Case / Bear Case | 投資Agentの別実行・別成果物。自動的な独立性を主張しない |
| 反証 | Research Synthesistを利用し、証拠不足と仮説破綻条件を確認 |
| 最終統合 | Research Synthesist / Executive Summary Generator |

企業IR、適時開示、有価証券報告書、公開統計、ユーザー提供資料を優先します。
APIキーや有料データ取得は使いません。欠測データを推測で埋めず、取得日・資料日・
対象期間・単位・会計基準・実績/予想を記録します。株価・需給データの権利・取得経路も確認します。
証券口座への接続や売買注文は行いません。Strategy Duel Agentは金融反証の代用にしません。

## アプリ開発

| 役割 | 既存定義 |
|---|---|
| Orchestrator | Agents Orchestrator |
| Project Manager | Senior Project Manager |
| Software Architect | Software Architect |
| Android Developer | Mobile App Builder。Kotlin / Composeを中心に補足 |
| Web Developer | Frontend Developer。必要ならBackend Architect |
| Code Reviewer | Code Reviewer |
| QA | Evidence Collector、必要ならTest Automation Engineer / Test Results Analyzer |
| Reality Checker | Reality Checker |

CloudでSDK・JDK・ビルド・成果物取得を確認し、Android実機で検証します。
既存QAの例にある `qa-playwright-capture.sh` はこのリポジトリに同梱されていません。
署名鍵・個人設定・APIキーを公開Forkへ保存しません。有料デバイスクラウド、アプリストア登録、
課金バックエンドは自動導入しません。

## 将来追加する場所

日本株専門Agentは `finance/personal/`、Android専門Agentは必要になったときに
`engineering/personal/`。既存部門の再帰走査を利用し、部門を増やしません。
元Agentのコピー・国名置換だけの新規定義を避け、固有の責務と評価基準を持たせます。
新規英語名・slug・ファイルIDの重複を検査します。

追加後は既存Lint、独自性検査、全ツール変換と生成ハッシュを確認します。
既存の全件変換にも新Agentが含まれる点に注意してください。
