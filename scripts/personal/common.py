"""Local-only profile helpers. No authentication, model calls, or billing APIs."""
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile

ROOT = Path(__file__).resolve().parents[2]
PROFILE_DIR = ROOT / "strategy/profiles/personal-no-extra-cost"
PROFILE_ID = "personal-no-extra-cost"
API_ENV = ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY",
           "AZURE_OPENAI_API_KEY", "OPENAI_BASE_URL", "ANTHROPIC_BASE_URL",
           "GOOGLE_APPLICATION_CREDENTIALS", "GOOGLE_GENAI_USE_VERTEXAI")
ATTESTATIONS = ("chatgpt_auth", "included_only_usage", "auto_reload_disabled",
                "no_paid_credit_use", "cloud_access_verified")


class ProfileError(Exception):
    pass


def fail(message):
    raise ProfileError(message)


def no_symlinks(path):
    path = Path(os.path.abspath(path))
    for item in (path, *path.parents):
        if item.is_symlink():
            fail(f"シンボリックリンクは使用できません: {item}")
    return path


def read_json(path):
    no_symlinks(path)
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                fail(f"JSONキーが重複しています: {key}")
            result[key] = value
        return result
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=unique)
    except (OSError, ValueError) as exc:
        fail(f"JSONを読み込めません: {path}: {exc}")


def exact_keys(data, keys, label):
    if not isinstance(data, dict) or set(data) != set(keys):
        fail(f"{label}: 必須項目の不足または未知の項目があります")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def slug(name):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]", "-", name.lower())).strip("-")


def catalog(root=ROOT):
    divisions = read_json(root / "divisions.json")["divisions"]
    result = {}
    names = set()
    for division in divisions:
        for path in sorted((root / division).rglob("*.md")):
            no_symlinks(path)
            content = path.read_text(encoding="utf-8")
            if not content.startswith("---\n"):
                continue
            frontmatter = content.split("---", 2)[1]
            match = re.search(r"^name: (.+)$", frontmatter, re.M)
            if not match:
                fail(f"Agent名がありません: {path}")
            name = match[1].strip().strip("\"'")
            agent_slug = slug(name)
            if not agent_slug or agent_slug in names or path.stem in result:
                fail(f"Agent IDまたはslugが衝突しています: {path}")
            names.add(agent_slug)
            result[path.stem] = {"source": str(path.relative_to(root)), "name": name,
                                 "slug": agent_slug, "sha256": digest(path)}
    return result


def load_profile(profile="personal-no-extra-cost", directory=PROFILE_DIR, root=ROOT):
    if profile not in (PROFILE_ID, "personal-free"):
        fail(f"未知のプロファイル: {profile}")
    data = read_json(directory / "profile.json")
    expected = {
        "schema_version": 1, "id": PROFILE_ID, "aliases": ["personal-free"],
        "language": "ja", "primary": "codex-chatgpt-subscription",
        "secondary": ["claude-free-manual", "gemini-existing-plan-manual"],
        "default_team": "core", "policy": "POLICY.md", "services": "services.json",
        "teams": "teams.json", "i18n": "i18n/ja.json", "deny_llm_api": True,
        "deny_extra_charges": True, "deny_credit_purchases": True,
        "deny_paid_credit_use": True, "unknown_service": "stop",
        "quota_exhausted": "checkpoint-and-stop", "max_attempts_per_task": 3,
        "execution": "sequential-by-default",
    }
    # This profile is deliberately strict. Changes to its contract need code review.
    if json.dumps(data, sort_keys=True) != json.dumps(expected, sort_keys=True):
        fail("profile.jsonが対応する追加課金禁止契約と一致しません")
    policy_path = directory / data["policy"]
    no_symlinks(policy_path)
    policy = policy_path.read_text(encoding="utf-8")
    if not policy.startswith("# ") or len(policy) < 100:
        fail("共通方針が空、またはAgentとして誤認される形式です")
    services = read_json(directory / data["services"])
    exact_keys(services, ("schema_version", "default", "actions"), "services")
    if type(services["schema_version"]) is not int or services["schema_version"] != 1 or services["default"] != "stop":
        fail("未知サービスは必ず停止する必要があります")
    expected_actions = {
        "codex.subscription": ("allow", "included"),
        "chatgpt.included": ("allow", "included"),
        "claude.free.manual": ("manual", "included"),
        "gemini.existing.manual": ("manual", "included"),
        "github.repository": ("allow", "included"),
        "public.documents": ("allow", "public-zero"),
        "local.open-source": ("allow", "public-zero"),
        "llm.api": ("stop", "unknown"),
        "credits.purchase": ("stop", "additional"),
        "credits.consume": ("stop", "additional"),
        "saas.paid": ("stop", "additional"),
        "cloud.billing": ("stop", "additional"),
        "github.paid-addon": ("stop", "additional"),
    }
    if not isinstance(services["actions"], dict) or set(services["actions"]) != set(expected_actions):
        fail("サービス定義に不足または未対応の操作があります")
    for action, entry in services["actions"].items():
        exact_keys(entry, ("decision", "cost", "requirements"), action)
        if (entry["decision"], entry["cost"]) != expected_actions[action]:
            fail(f"課金経路を許可する変更はできません: {action}")
        if not isinstance(entry["requirements"], list) or not entry["requirements"] or any(
                not isinstance(x, str) or not x for x in entry["requirements"]):
            fail(f"利用前提がありません: {action}")
    teams = read_json(directory / data["teams"])
    exact_keys(teams, ("schema_version", "teams"), "teams")
    if type(teams["schema_version"]) is not int or teams["schema_version"] != 1 or not isinstance(teams["teams"], dict) or not teams["teams"]:
        fail("チーム定義がありません")
    agents = catalog(root)
    for team, entry in teams["teams"].items():
        exact_keys(entry, ("description", "agents"), team)
        ids = entry["agents"]
        if not isinstance(ids, list) or not ids or any(not isinstance(x, str) for x in ids):
            fail(f"チーム名簿が不正です: {team}")
        if len(ids) != len(set(ids)) or any(x not in agents for x in ids):
            fail(f"Agent参照の重複または参照切れがあります: {team}")
        if not isinstance(entry["description"], str) or not entry["description"]:
            fail(f"チーム説明がありません: {team}")
    if data["default_team"] not in teams["teams"]:
        fail("既定チームがありません")
    translations = read_json(directory / data["i18n"])
    exact_keys(translations, ("schema_version", "agents", "errors"), "i18n")
    if type(translations["schema_version"]) is not int or translations["schema_version"] != 1 or not isinstance(translations["agents"], dict) or set(translations["agents"]) != set(agents):
        fail("日本語Agent一覧がUpstreamと一致しません。追加・削除・改名を確認してください")
    for agent_id, entry in translations["agents"].items():
        exact_keys(entry, ("name", "description"), agent_id)
        if any(not isinstance(v, str) or not v for v in entry.values()):
            fail(f"日本語表示が不正です: {agent_id}")
    exact_keys(translations["errors"], ("unknown_action", "extra_cost", "quota", "credentials", "cloud_unverified"), "日本語エラー")
    if any(not isinstance(v, str) or not v for v in translations["errors"].values()):
        fail("日本語エラーの説明がありません")
    return data, policy, services, teams["teams"], agents


def selected(team, teams, agents):
    if team not in teams:
        fail(f"未知のチーム: {team}")
    return {agent_id: agents[agent_id] for agent_id in teams[team]["agents"]}


def check_runtime(attestation):
    present = [name for name in API_ENV if os.environ.get(name)]
    if present:
        fail("API認証・接続先設定を検出しました（値は表示しません）: " + ", ".join(present))
    if attestation is None:
        fail("実行前確認がありません。契約内利用・自動補充・課金経路を画面で確認してください")
    data = read_json(attestation)
    exact_keys(data, ("schema_version", "confirmed_on", *ATTESTATIONS), "実行前確認")
    from datetime import date
    if type(data["schema_version"]) is not int or data["schema_version"] != 1 or data["confirmed_on"] != date.today().isoformat():
        fail("実行前確認は当日の確認日を指定してください")
    if any(data[name] is not True for name in ATTESTATIONS):
        fail("契約内利用を確認できないため停止します")


def atomic_json(path, data):
    path = no_symlinks(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent, prefix=".personal-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def report_error(exc):
    import sys
    print(f"停止: {exc}\n追加購入や有料APIへの切替は行いません。条件を確認して再開してください。", file=sys.stderr)
    return 2
