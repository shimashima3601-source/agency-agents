#!/usr/bin/env python3
"""Render the Japanese display catalogue without editing upstream agent names."""
import argparse
import os
from pathlib import Path
from common import ROOT, PROFILE_DIR, catalog, read_json, no_symlinks, fail, ProfileError, report_error


def render():
    agents = catalog()
    translations = read_json(PROFILE_DIR / "i18n/ja.json")["agents"]
    if set(agents) != set(translations):
        fail("辞書とAgentが一致しません。翻訳辞書を確認してから再生成してください")
    target = PROFILE_DIR / "docs/ja/agents.md"
    divisions = {"academic": "学術", "design": "デザイン", "engineering": "エンジニアリング",
                 "finance": "財務・投資", "game-development": "ゲーム開発", "gis": "地理情報",
                 "healthcare": "医療", "marketing": "マーケティング", "paid-media": "有料広告",
                 "product": "プロダクト", "project-management": "プロジェクト管理", "research": "調査",
                 "sales": "営業", "security": "セキュリティ", "spatial-computing": "空間コンピューティング",
                 "specialized": "専門領域", "support": "サポート", "testing": "テスト"}
    lines = ["# 日本語Agent一覧", "", f"元の{len(agents)} Agentを保持しています。英語名とファイルIDは変更しません。",
             "表示用の日本語名であり、個人プロファイルでの全件実行・サービス利用の許可を意味しません。",
             "本文・具体的な成果物はリンク先を参照してください。", ""]
    for division, label in divisions.items():
        lines += ["## " + label, "", "| 日本語表示 | 元の英語名 | 役割の補助説明 |", "|---|---|---|"]
        for agent_id, agent in agents.items():
            if agent["source"].split("/")[0] != division:
                continue
            entry = translations[agent_id]
            link = os.path.relpath(ROOT / agent["source"], target.parent)
            escape = lambda s: s.replace("|", "\\|").replace("\n", " ")
            lines.append(f"| [{escape(entry['name'])}]({link}) | {escape(agent['name'])} | {escape(entry['description'])} |")
        lines.append("")
    return target, "\n".join(lines).rstrip() + "\n"


def main():
    parser = argparse.ArgumentParser(description="日本語表示辞書から一覧を生成")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        path, content = render()
        if args.check:
            if not path.is_file() or path.read_text(encoding="utf-8") != content:
                fail("日本語Agent一覧が更新されていません")
        else:
            no_symlinks(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        print("日本語Agent一覧: OK")
        return 0
    except (ProfileError, OSError, ValueError, KeyError, TypeError) as exc:
        return report_error(exc)


if __name__ == "__main__":
    raise SystemExit(main())
