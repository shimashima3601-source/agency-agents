#!/usr/bin/env python3
"""Validate local data; action checks are advisory, not runtime interception."""
import argparse
from pathlib import Path
from common import load_profile, selected, check_runtime, report_error, ProfileError, fail


def main():
    parser = argparse.ArgumentParser(description="個人プロファイルを検証（課金APIは呼び出しません）")
    parser.add_argument("--profile", default="personal-no-extra-cost")
    parser.add_argument("--team")
    parser.add_argument("--action", help="判定する明示的な操作ID。未知の操作は停止")
    parser.add_argument("--check-runtime", action="store_true", help="API環境変数と当日の手動確認を検査")
    parser.add_argument("--attestation", type=Path, help="個人確認JSON。Gitに追加しないこと")
    args = parser.parse_args()
    try:
        data, _, services, teams, agents = load_profile(args.profile)
        if args.team:
            selected(args.team, teams, agents)
        if args.attestation and not args.check_runtime:
            fail("--attestationは--check-runtimeと併用してください")
        if args.check_runtime:
            check_runtime(args.attestation)
        if args.action:
            entry = services["actions"].get(args.action)
            if entry is None or entry["decision"] == "stop":
                fail(f"課金禁止または未確認の操作: {args.action}")
            print(f"操作判定: {entry['decision']} / 前提: {', '.join(entry['requirements'])}")
            print("前提は自動確認されません。手動利用は自動実行の許可ではありません。")
        print(f"検証OK: {data['id']} / {len(agents)} Agent / {len(teams)}チーム")
        print("ローカル定義の検証です。Cloud対応・認証・残量・請求の確認にはなりません。")
        return 0
    except (ProfileError, OSError, KeyError, TypeError, ValueError) as exc:
        return report_error(exc)


if __name__ == "__main__":
    raise SystemExit(main())
