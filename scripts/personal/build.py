#!/usr/bin/env python3
"""Reuse the upstream renderer, then append the personal policy to selected agents."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import tomllib
from common import ROOT, PROFILE_DIR, PROFILE_ID, load_profile, selected, no_symlinks, digest
from common import read_json, atomic_json, ProfileError, report_error, fail


def verify_owned_output(path):
    manifest = read_json(path / "manifest.json")
    if not isinstance(manifest, dict) or set(manifest) != {
            "generator", "profile", "team", "agents", "policy_sha256", "files"}:
        fail("出力先の管理情報の形式が不正です")
    if manifest.get("generator") != "agency-personal-v1" or manifest.get("profile") != PROFILE_ID:
        fail("出力先はこのビルダーの管理対象ではありません")
    files = manifest.get("files")
    import re
    if not isinstance(files, dict) or not files or any(
            not isinstance(value, str) or re.fullmatch(r"[a-f0-9]{64}", value) is None
            for value in files.values()):
        fail("生成物の管理情報が不正です")
    actual = set()
    for item in path.rglob("*"):
        no_symlinks(item)
        if item.is_file() and item != path / "manifest.json":
            relative = str(item.relative_to(path))
            actual.add(relative)
            if files.get(relative) != digest(item):
                fail(f"生成物が変更されています。上書きしません: {relative}")
    if actual != set(files):
        fail("生成物の追加・削除を検出しました。上書きしません")


def build(profile, team, out, dry_run=False):
    data, policy, _, teams, agents = load_profile(profile)
    team = team or data["default_team"]
    chosen = selected(team, teams, agents)
    out = no_symlinks(out)
    if out == ROOT or out in ROOT.parents or out == ROOT / "dist":
        fail("出力先には専用の生成ディレクトリを指定してください")
    if out.is_relative_to(ROOT) and not out.is_relative_to(ROOT / "dist"):
        fail("リポジトリ内の出力先はdist配下に限定します")
    if out.exists():
        if not out.is_dir():
            fail("出力先がディレクトリではありません")
        verify_owned_output(out)
    if dry_run:
        return {"profile": PROFILE_ID, "team": team, "agents": list(chosen),
                "destination": str(out), "dry_run": True}
    out.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".personal-build-", dir=out.parent))
    backup = None
    try:
        process = subprocess.run(["bash", str(ROOT / "scripts/convert.sh"), "--tool", "codex",
                                  "--out", str(stage / "rendered")], capture_output=True, text=True)
        if process.returncode:
            # Do not surface arbitrary converter output/credentials in an error log.
            fail("Upstream Codex変換が失敗しました。元の変換処理をローカルで確認してください")
        destination = stage / "codex/agents"
        destination.mkdir(parents=True)
        mapping = {}
        for agent_id, entry in chosen.items():
            source = stage / "rendered/codex/agents" / (entry["slug"] + ".toml")
            rendered = tomllib.loads(source.read_text(encoding="utf-8"))
            if set(rendered) != {"name", "description", "developer_instructions"}:
                fail("UpstreamのCodex形式が変わりました。アダプターを再確認してください")
            if rendered["name"] != entry["name"]:
                fail(f"Agent名の変換規約が変わりました: {agent_id}")
            name = "Personal / " + rendered["name"]
            filename = "personal-" + entry["slug"] + ".toml"
            instructions = rendered["developer_instructions"] + "\n\n---\n\n" + policy
            payload = {"name": name, "description": rendered["description"],
                       "developer_instructions": instructions}
            content = "\n".join(key + " = " + json.dumps(value, ensure_ascii=False)
                                for key, value in payload.items()) + "\n"
            if tomllib.loads(content) != payload:
                fail(f"TOMLの往復検証に失敗しました: {agent_id}")
            (destination / filename).write_text(content, encoding="utf-8")
            mapping[filename] = {"agent_id": agent_id, "original_name": rendered["name"],
                                 "name": name, "source": entry["source"], "source_sha256": entry["sha256"]}
        manifest = {"generator": "agency-personal-v1", "profile": PROFILE_ID,
                    "team": team, "agents": mapping, "policy_sha256": digest(PROFILE_DIR / "POLICY.md"),
                    "files": {str(p.relative_to(stage)): digest(p)
                              for p in sorted(stage.rglob("*")) if p.is_file()}}
        atomic_json(stage / "manifest.json", manifest)
        if out.exists():
            verify_owned_output(out)
            backup = Path(tempfile.mkdtemp(prefix=".personal-old-", dir=out.parent))
            backup.rmdir()
            os.replace(out, backup)
        try:
            os.replace(stage, out)
        except OSError:
            if backup is not None:
                os.replace(backup, out)
                backup = None
            raise
        if backup is not None:
            shutil.rmtree(backup)
        return {"profile": PROFILE_ID, "team": team, "count": len(chosen), "destination": str(out)}
    finally:
        if stage.exists():
            shutil.rmtree(stage)


def main():
    parser = argparse.ArgumentParser(description="元の変換を再利用し、個人用Codex Agentを生成")
    parser.add_argument("--profile", default=PROFILE_ID)
    parser.add_argument("--team")
    parser.add_argument("--out", type=Path, default=ROOT / "dist" / PROFILE_ID)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        print(json.dumps(build(args.profile, args.team, args.out, args.dry_run), ensure_ascii=False, indent=2))
        return 0
    except (ProfileError, OSError, ValueError, KeyError, TypeError) as exc:
        return report_error(exc)


if __name__ == "__main__":
    raise SystemExit(main())
