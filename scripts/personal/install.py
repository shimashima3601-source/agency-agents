#!/usr/bin/env python3
"""Copy only verified, managed personal agents into a project's .codex/agents."""
import argparse
import json
import os
from pathlib import Path
import tempfile
import tomllib
from build import verify_owned_output
from common import ROOT, PROFILE_ID, PROFILE_DIR, load_profile, selected, no_symlinks
from common import read_json, digest, atomic_json, fail, ProfileError, report_error

STATE = ".agency-personal.json"


def safe_filename(name):
    import re
    return isinstance(name, str) and re.fullmatch(r"personal-[a-z0-9-]+\.toml", name) is not None


def write_file(path, content):
    fd, name = tempfile.mkstemp(prefix=".personal-copy-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(content)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def install(source, project, dry_run=False):
    _, policy, _, teams, agents = load_profile()
    source = no_symlinks(source)
    project = no_symlinks(project)
    if not project.is_dir():
        fail("配置先プロジェクトのディレクトリがありません")
    verify_owned_output(source)
    manifest = read_json(source / "manifest.json")
    if manifest.get("policy_sha256") != digest(PROFILE_DIR / "POLICY.md"):
        fail("共通方針が更新されています。再生成してください")
    chosen = selected(manifest.get("team"), teams, agents)
    expected = {"personal-" + entry["slug"] + ".toml": (agent_id, entry)
                for agent_id, entry in chosen.items()}
    if not isinstance(manifest.get("agents"), dict) or set(manifest["agents"]) != set(expected):
        fail("生成物の名簿が現在のチーム定義と一致しません")
    payloads = {}
    for filename, (agent_id, entry) in expected.items():
        metadata = manifest["agents"][filename]
        if not isinstance(metadata, dict) or set(metadata) != {
                "agent_id", "original_name", "name", "source", "source_sha256"}:
            fail("生成物のAgent管理情報が不正です")
        if metadata.get("source_sha256") != entry["sha256"] or metadata.get("agent_id") != agent_id:
            fail(f"元Agentが更新されています。再生成してください: {agent_id}")
        original = tomllib.loads((source / "rendered/codex/agents" / (entry["slug"] + ".toml"))
                                .read_text(encoding="utf-8"))
        target = source / "codex/agents" / filename
        generated = tomllib.loads(target.read_text(encoding="utf-8"))
        expected_payload = {"name": "Personal / " + entry["name"],
                            "description": original["description"],
                            "developer_instructions": original["developer_instructions"] + "\n\n---\n\n" + policy}
        if generated != expected_payload:
            fail(f"個人用指示の構成が不正です: {agent_id}")
        payloads[filename] = target.read_bytes()
    destination = no_symlinks(project / ".codex/agents")
    state_path = no_symlinks(destination / STATE)
    previous = {}
    if state_path.exists():
        state = read_json(state_path)
        if not isinstance(state, dict) or set(state) != {"generator", "profile", "files"} or state.get("generator") != "agency-personal-v1" or state.get("profile") != PROFILE_ID:
            fail("配置先の所有情報が不正です")
        previous = state["files"]
        if not isinstance(previous, dict) or any(not safe_filename(x) for x in previous):
            fail("配置先の所有ファイル名が不正です")
        for filename, expected_hash in previous.items():
            path = no_symlinks(destination / filename)
            if not path.is_file() or digest(path) != expected_hash:
                fail(f"配置済みAgentが編集・削除されています。上書きしません: {filename}")
    for filename in payloads:
        path = no_symlinks(destination / filename)
        if path.exists() and filename not in previous:
            fail(f"無関係な既存ファイルと衝突します: {filename}")
    result = {"destination": str(destination), "install": list(payloads),
              "remove_owned": sorted(set(previous) - set(payloads)), "dry_run": dry_run}
    if dry_run:
        return result
    destination.mkdir(parents=True, exist_ok=True)
    old = {filename: (destination / filename).read_bytes() for filename in previous}
    old_state = state_path.read_bytes() if state_path.exists() else None
    touched = set()
    try:
        for filename, content in payloads.items():
            # Recheck immediately before replacement, including dangling symlinks.
            no_symlinks(destination / filename)
            touched.add(filename)
            write_file(destination / filename, content)
        for filename in set(previous) - set(payloads):
            touched.add(filename)
            (destination / filename).unlink()
        import hashlib
        atomic_json(state_path, {"generator": "agency-personal-v1", "profile": PROFILE_ID,
                                 "files": {name: hashlib.sha256(content).hexdigest()
                                           for name, content in payloads.items()}})
    except (OSError, ProfileError):
        for filename in touched:
            if filename in old:
                write_file(destination / filename, old[filename])
            else:
                (destination / filename).unlink(missing_ok=True)
        if old_state is not None:
            write_file(state_path, old_state)
        else:
            state_path.unlink(missing_ok=True)
        raise
    return result


def main():
    parser = argparse.ArgumentParser(description="個人用Agentをプロジェクトに配置（AIは起動しません）")
    parser.add_argument("--source", type=Path, default=ROOT / "dist" / PROFILE_ID)
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        print(json.dumps(install(args.source, args.project, args.dry_run), ensure_ascii=False, indent=2))
        print("配置計画のみ表示。ファイルは配置していません。" if args.dry_run else
              "配置のみ完了。利用前に認証・請求設定・Cloudでの読み込みを確認してください。")
        return 0
    except (ProfileError, OSError, ValueError, KeyError, TypeError) as exc:
        return report_error(exc)


if __name__ == "__main__":
    raise SystemExit(main())
