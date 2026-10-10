"""Offline behavioral tests: no model clients, credentials, or external services."""
import contextlib
from datetime import date
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import common
import build as builder
import install as installer
import validate


class ProfileTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.directory = self.base / "profile"
        shutil.copytree(common.PROFILE_DIR, self.directory)

    def tearDown(self):
        self.temp.cleanup()

    def mutate(self, filename, callback):
        path = self.directory / filename
        data = json.loads(path.read_text())
        callback(data)
        path.write_text(json.dumps(data))

    def test_alias_and_default(self):
        self.assertEqual(common.load_profile("personal-free")[0]["id"], common.PROFILE_ID)

    def test_unknown_profile_stops(self):
        with self.assertRaises(common.ProfileError):
            common.load_profile("unrestricted")

    def test_api_policy_cannot_be_disabled(self):
        self.mutate("profile.json", lambda x: x.update(deny_llm_api=False))
        with self.assertRaises(common.ProfileError):
            common.load_profile(directory=self.directory)

    def test_boolean_is_not_integer(self):
        self.mutate("profile.json", lambda x: x.update(deny_extra_charges=1))
        with self.assertRaises(common.ProfileError):
            common.load_profile(directory=self.directory)

    def test_unknown_setting_stops(self):
        self.mutate("profile.json", lambda x: x.update(automatic_purchase=True))
        with self.assertRaises(common.ProfileError):
            common.load_profile(directory=self.directory)

    def test_paid_route_cannot_be_allowed(self):
        self.mutate("services.json", lambda x: x["actions"]["llm.api"].update(decision="allow"))
        with self.assertRaises(common.ProfileError):
            common.load_profile(directory=self.directory)

    def test_unknown_service_default_cannot_allow(self):
        self.mutate("services.json", lambda x: x.update(default="allow"))
        with self.assertRaises(common.ProfileError):
            common.load_profile(directory=self.directory)

    def test_missing_reference_stops(self):
        self.mutate("teams.json", lambda x: x["teams"]["core"]["agents"].append("missing-specialist"))
        with self.assertRaises(common.ProfileError):
            common.load_profile(directory=self.directory)

    def test_translation_drift_stops(self):
        self.mutate("i18n/ja.json", lambda x: x["agents"].pop("agents-orchestrator"))
        with self.assertRaises(common.ProfileError):
            common.load_profile(directory=self.directory)

    def test_duplicate_json_keys_stop(self):
        path = self.base / "duplicate.json"
        path.write_text('{"id": 1, "id": 2}')
        with self.assertRaises(common.ProfileError):
            common.read_json(path)

    def test_unknown_and_paid_actions_exit_nonzero(self):
        for action in ("llm.api", "credits.purchase", "cloud.billing", "anything-new"):
            with self.subTest(action=action), patch.object(sys, "argv", ["validate", "--action", action]), contextlib.redirect_stderr(io.StringIO()):
                self.assertNotEqual(validate.main(), 0)

    def test_manual_route_is_not_automatic_authorization(self):
        stream = io.StringIO()
        with patch.object(sys, "argv", ["validate", "--action", "claude.free.manual"]), contextlib.redirect_stdout(stream):
            self.assertEqual(validate.main(), 0)
        self.assertIn("手動利用は自動実行の許可ではありません", stream.getvalue())

    def test_runtime_requires_attestation(self):
        with patch.dict(os.environ, {}, clear=True), self.assertRaises(common.ProfileError):
            common.check_runtime(None)

    def attestation(self, **changes):
        data = {"schema_version": 1, "confirmed_on": date.today().isoformat(),
                **{key: True for key in common.ATTESTATIONS}, **changes}
        path = self.base / "account.personal.local.json"
        path.write_text(json.dumps(data))
        return path

    def test_runtime_accepts_current_manual_confirmation(self):
        with patch.dict(os.environ, {}, clear=True):
            common.check_runtime(self.attestation())

    def test_false_or_stale_confirmation_stops(self):
        for changes in ({"no_paid_credit_use": False}, {"confirmed_on": "2000-01-01"}, {"chatgpt_auth": 1}):
            with self.subTest(changes=changes), patch.dict(os.environ, {}, clear=True), self.assertRaises(common.ProfileError):
                common.check_runtime(self.attestation(**changes))

    def test_api_secret_stops_without_exposing_value(self):
        value = "secret-do-not-print"
        with patch.dict(os.environ, {"OPENAI_API_KEY": value}, clear=True):
            with self.assertRaises(common.ProfileError) as error:
                common.check_runtime(self.attestation())
        self.assertIn("OPENAI_API_KEY", str(error.exception))
        self.assertNotIn(value, str(error.exception))


class DeploymentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.base = Path(cls.temp.name)
        cls.output = cls.base / "generated"
        builder.build(common.PROFILE_ID, "core", cls.output)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setUp(self):
        self.temp_case = tempfile.TemporaryDirectory(dir=self.base)
        self.case = Path(self.temp_case.name)
        self.project = self.case / "project"
        self.project.mkdir()

    def tearDown(self):
        self.temp_case.cleanup()

    def test_generated_body_preserves_upstream_and_adds_policy(self):
        manifest = common.read_json(self.output / "manifest.json")
        policy = (common.PROFILE_DIR / "POLICY.md").read_text()
        for filename, metadata in manifest["agents"].items():
            personal = tomllib.loads((self.output / "codex/agents" / filename).read_text())
            entry = common.catalog()[metadata["agent_id"]]
            original = tomllib.loads((self.output / "rendered/codex/agents" / (entry["slug"] + ".toml")).read_text())
            self.assertEqual(personal["name"], "Personal / " + original["name"])
            self.assertEqual(personal["description"], original["description"])
            self.assertEqual(personal["developer_instructions"], original["developer_instructions"] + "\n\n---\n\n" + policy)

    def test_build_dry_run_writes_nothing(self):
        out = self.case / "dry"
        builder.build("personal-free", "core", out, True)
        self.assertFalse(out.exists())

    def test_rebuild_is_owned_and_deterministic(self):
        out = self.case / "rebuild"
        shutil.copytree(self.output, out)
        before = common.read_json(out / "manifest.json")
        builder.build(common.PROFILE_ID, "core", out)
        self.assertEqual(before, common.read_json(out / "manifest.json"))
        self.assertFalse(list(self.case.glob(".personal-old-*")))

    def test_build_refuses_unmanaged_directory(self):
        out = self.case / "existing"
        out.mkdir()
        (out / "user.txt").write_text("keep")
        with self.assertRaises(common.ProfileError):
            builder.build(common.PROFILE_ID, "core", out)
        self.assertEqual((out / "user.txt").read_text(), "keep")

    def test_build_refuses_source_directory(self):
        with self.assertRaises(common.ProfileError):
            builder.build(common.PROFILE_ID, "core", common.ROOT / "engineering", True)

    def test_build_failure_cleans_stage_without_output(self):
        out = self.case / "failed"
        with patch.object(builder.subprocess, "run", return_value=subprocess.CompletedProcess([], 1)):
            with self.assertRaises(common.ProfileError):
                builder.build(common.PROFILE_ID, "core", out)
        self.assertFalse(out.exists())
        self.assertFalse(list(self.case.glob(".personal-build-*")))

    def test_install_dry_run_creates_no_codex_directory(self):
        installer.install(self.output, self.project, True)
        self.assertFalse((self.project / ".codex").exists())

    def test_install_is_idempotent_and_preserves_unrelated_agent(self):
        dest = self.project / ".codex/agents"
        dest.mkdir(parents=True)
        (dest / "other.toml").write_text("unrelated")
        installer.install(self.output, self.project)
        before = {p.name: p.read_bytes() for p in dest.iterdir()}
        installer.install(self.output, self.project)
        self.assertEqual(before, {p.name: p.read_bytes() for p in dest.iterdir()})

    def test_team_switch_removes_only_owned_files(self):
        installer.install(self.output, self.project)
        dest = self.project / ".codex/agents"
        (dest / "unrelated.toml").write_text("keep")
        next_output = self.case / "equities"
        builder.build(common.PROFILE_ID, "japan-equities-research", next_output)
        installer.install(next_output, self.project)
        manifest = common.read_json(next_output / "manifest.json")
        self.assertEqual({p.name for p in dest.glob("personal-*.toml")}, set(manifest["agents"]))
        self.assertEqual((dest / "unrelated.toml").read_text(), "keep")

    def test_collision_refuses_all_writes(self):
        dest = self.project / ".codex/agents"
        dest.mkdir(parents=True)
        name = next(iter(common.read_json(self.output / "manifest.json")["agents"]))
        (dest / name).write_text("user-owned")
        with self.assertRaises(common.ProfileError):
            installer.install(self.output, self.project)
        self.assertEqual(list(dest.iterdir()), [dest / name])
        self.assertEqual((dest / name).read_text(), "user-owned")

    def test_edited_installed_file_is_not_overwritten(self):
        installer.install(self.output, self.project)
        dest = self.project / ".codex/agents"
        name = next(dest.glob("personal-*.toml"))
        name.write_text("edited")
        with self.assertRaises(common.ProfileError):
            installer.install(self.output, self.project)
        self.assertEqual(name.read_text(), "edited")

    def test_dangling_symlink_is_refused(self):
        dest = self.project / ".codex/agents"
        dest.mkdir(parents=True)
        name = next(iter(common.read_json(self.output / "manifest.json")["agents"]))
        (dest / name).symlink_to(self.case / "missing")
        with self.assertRaises(common.ProfileError):
            installer.install(self.output, self.project)
        self.assertFalse((self.case / "missing").exists())

    def test_symlinked_project_is_refused(self):
        link = self.case / "linked"
        link.symlink_to(self.project, target_is_directory=True)
        with self.assertRaises(common.ProfileError):
            installer.install(self.output, link)
        self.assertFalse((self.project / ".codex").exists())

    def test_tampered_build_is_refused(self):
        source = self.case / "tampered"
        shutil.copytree(self.output, source)
        next((source / "codex/agents").glob("*.toml")).write_text("changed")
        with self.assertRaises(common.ProfileError):
            installer.install(source, self.project)
        self.assertFalse((self.project / ".codex").exists())

    def test_stale_policy_is_refused(self):
        source = self.case / "stale"
        shutil.copytree(self.output, source)
        path = source / "manifest.json"
        manifest = common.read_json(path)
        manifest["policy_sha256"] = "old-policy"
        path.write_text(json.dumps(manifest))
        with self.assertRaises(common.ProfileError):
            installer.install(source, self.project)

    def test_malformed_manifest_reports_profile_error(self):
        source = self.case / "invalid"
        source.mkdir()
        (source / "manifest.json").write_text("[]")
        with self.assertRaises(common.ProfileError):
            installer.install(source, self.project)

    def test_partial_failure_rolls_back_existing_install(self):
        installer.install(self.output, self.project)
        dest = self.project / ".codex/agents"
        before = {p.name: p.read_bytes() for p in dest.iterdir()}
        original = installer.write_file
        calls = 0
        def fail_second(path, content):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("simulated disk error")
            return original(path, content)
        with patch.object(installer, "write_file", side_effect=fail_second), self.assertRaises(OSError):
            installer.install(self.output, self.project)
        self.assertEqual(before, {p.name: p.read_bytes() for p in dest.iterdir()})


if __name__ == "__main__":
    unittest.main()
