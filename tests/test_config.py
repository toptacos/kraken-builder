#!/usr/bin/env python3
"""Configuration: every setting, every scope, and the rules between them.

The requirement this exists for: a setting in the schema must be typed,
resolvable, documented, and testable. So this file walks the schema rather
than hand-picking keys, which means a new setting that is not covered here
fails the suite instead of passing untested.

Each test is offline and uses a throwaway KRAKEN_HOME and working directory,
so nothing depends on the developer's real config.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from kraken.core import config_schema as cs  # noqa: E402
from kraken.core import config_chain as cc  # noqa: E402
from kraken.core import notify as notify_mod  # noqa: E402
from kraken.core.grant import read_allow  # noqa: E402
from kraken.core.paths import data_root, layout_dirs  # noqa: E402


class Env:
    """A fully isolated home + cwd + project dir."""

    def __init__(self, tmp: Path):
        self.home = tmp / "home"
        self.system = tmp / "system"
        self.work = tmp / "work"
        for p in (self.home, self.system, self.work):
            p.mkdir(parents=True, exist_ok=True)
        # Always present, so a test that writes project config does not have
        # to ask for it separately.
        self.project = self.work / ".kraken"

    def apply(self) -> None:
        os.environ["KRAKEN_HOME"] = str(self.home)
        os.environ["KRAKEN_SYSTEM_DIR"] = str(self.system)
        os.chdir(self.work)

    def write(self, scope: str, body: str) -> None:
        if scope == "system":
            base = self.system
        elif scope == "user":
            base = self.home / ".kraken"
        else:
            base = self.project
        base.mkdir(parents=True, exist_ok=True)
        (base / "config.yaml").write_text(body, encoding="utf-8")

    def cfg(self) -> dict:
        return cc.load_yaml(self.project / "config.yaml") if self.project else {}


def sandbox(test):
    """Give a test a clean env and restore it afterwards."""

    def wrapper(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            saved = {
                k: os.environ.get(k)
                for k in (
                    "KRAKEN_HOME",
                    "KRAKEN_SYSTEM_DIR",
                    "KRAKEN_OFFLINE",
                    "KRAKEN_NOTIFY_STDOUT",
                    "KRAKEN_DOCKER_CONFIG_URL",
                    "KRAKEN_LICENSE_REMOTE",
                )
            }
            cwd = Path.cwd()
            env = Env(tmp)
            env.apply()
            try:
                return test(self, env)
            finally:
                os.chdir(cwd)
                for k, v in saved.items():
                    if v is None:
                        os.environ.pop(k, None)
                    else:
                        os.environ[k] = v

    wrapper.__name__ = test.__name__
    return wrapper


class Schema(unittest.TestCase):
    """The table itself has to be internally consistent."""

    def test_every_setting_has_a_summary(self):
        for s in cs.SETTINGS:
            self.assertTrue(s.summary.strip(), f"{s.key} has no summary")

    def test_keys_are_unique(self):
        keys = [s.key for s in cs.SETTINGS]
        self.assertEqual(len(keys), len(set(keys)))

    def test_defaults_match_their_declared_type(self):
        for s in cs.SETTINGS:
            self.assertTrue(
                cs.type_ok(s.kind, s.default),
                f"{s.key} default is not a valid {s.type_name()}",
            )

    def test_defaults_are_complete_and_copyable(self):
        d = cs.defaults()
        self.assertEqual(set(d), {s.key for s in cs.SETTINGS})
        d["docker"]["enabled"] = True
        self.assertIs(
            cs.defaults()["docker"]["enabled"], False, "defaults are shared state"
        )

    def test_nested_keys_exist_in_every_default(self):
        for key, subs in cs.NESTED.items():
            default = cs.BY_KEY[key].default
            for sub in subs:
                self.assertIn(sub, default, f"{key}.{sub} missing from the default")

    def test_nested_defaults_are_typed(self):
        for key, subs in cs.NESTED.items():
            for sub, kind in subs.items():
                self.assertTrue(
                    cs.type_ok(kind, cs.BY_KEY[key].default[sub]),
                    f"{key}.{sub} default is not a {kind}",
                )

    def test_grant_names_match_the_grant_module(self):
        from kraken.core.grant import KNOWN

        self.assertEqual(tuple(KNOWN), cs.KNOWN_GRANTS)

    def test_supported_version_is_the_version_default(self):
        self.assertEqual(cs.SUPPORTED_VERSION, cs.BY_KEY["version"].default)


class Resolution(unittest.TestCase):
    @sandbox
    def test_defaults_when_no_file_exists(self, env):
        merged, origins = cc.resolve()
        self.assertEqual(set(merged), {s.key for s in cs.SETTINGS})
        self.assertTrue(all(o.scope == "default" for o in origins.values()))

    @sandbox
    def test_a_partial_file_still_resolves_completely(self, env):
        env.write("user", "data_dir: elsewhere\n")
        merged, _ = cc.resolve()
        self.assertEqual(merged["data_dir"], "elsewhere")
        self.assertEqual(merged["log_dir"], "logs", "untouched key keeps its default")

    @sandbox
    def test_user_overrides_default(self, env):
        env.write("user", "cache_dir: scratch\n")
        merged, origins = cc.resolve()
        self.assertEqual(merged["cache_dir"], "scratch")
        self.assertEqual(origins["cache_dir"].scope, "user")

    @sandbox
    def test_project_overrides_user(self, env):
        env.write("user", "cache_dir: user-cache\n")
        env.write("project", "cache_dir: project-cache\n")
        merged, origins = cc.resolve()
        self.assertEqual(merged["cache_dir"], "project-cache")
        self.assertEqual(origins["cache_dir"].scope, "project")

    @sandbox
    def test_system_is_the_weakest_scope(self, env):
        env.write("system", "log_dir: sys-logs\n")
        env.write("user", "log_dir: user-logs\n")
        merged, _ = cc.resolve()
        self.assertEqual(merged["log_dir"], "user-logs")

    @sandbox
    def test_maps_merge_per_key(self, env):
        env.write("user", "docker:\n  enabled: true\n")
        env.write("project", "docker:\n  driver: overlay\n")
        merged, _ = cc.resolve()
        self.assertIs(merged["docker"]["enabled"], True, "user value survives")
        self.assertEqual(merged["docker"]["driver"], "overlay", "project value applies")
        self.assertEqual(
            merged["docker"]["name"], "kraken", "untouched key keeps default"
        )

    @sandbox
    def test_a_list_replaces_rather_than_appends(self, env):
        env.write("user", "telemetry:\n  events:\n    - a\n    - b\n")
        env.write("project", "telemetry:\n  events:\n    - c\n")
        merged, _ = cc.resolve()
        self.assertEqual(merged["telemetry"]["events"], ["c"])

    @sandbox
    def test_notify_shorthand_is_normalised(self, env):
        env.write("user", "notify: local\n")
        merged, _ = cc.resolve()
        self.assertEqual(merged["notify"]["channels"], ["stdout"])

    @sandbox
    def test_unknown_keys_do_not_appear_in_resolve(self, env):
        env.write("user", "nonsense: true\n")
        merged, _ = cc.resolve()
        self.assertNotIn("nonsense", merged)

    @sandbox
    def test_unknown_keys_still_load_through(self, env):
        # Forward compatibility: a newer Kraken's key must survive an older
        # one rather than being silently dropped.
        from kraken.core.config import load_config

        env.write("user", "nonsense: true\n")
        self.assertIs(load_config()["nonsense"], True)

    @sandbox
    def test_every_scope_appears_in_the_chain(self, env):
        env.write("system", "version: 1\n")
        env.write("user", "version: 1\n")
        env.write("project", "version: 1\n")
        scopes = [s for s, _, _ in cc.chain_files()]
        self.assertIn("system", scopes)
        self.assertIn("user", scopes)
        self.assertIn("project", scopes)
        self.assertLess(scopes.index("system"), scopes.index("user"))
        self.assertLess(scopes.index("user"), scopes.index("project"))


class EnvironmentOverrides(unittest.TestCase):
    @sandbox
    def test_offline_forces_telemetry_off(self, env):
        os.environ["KRAKEN_OFFLINE"] = "1"
        env.write("user", "telemetry:\n  enabled: true\n")
        merged, origins = cc.resolve()
        self.assertIs(merged["telemetry"]["enabled"], False)
        self.assertEqual(origins["telemetry"].scope, "env")

    @sandbox
    def test_docker_config_url_marks_the_provider(self, env):
        os.environ["KRAKEN_DOCKER_CONFIG_URL"] = "https://example.test/c.json"
        merged, origins = cc.resolve()
        self.assertEqual(merged["docker"]["provider"], "url")
        self.assertEqual(origins["docker"].scope, "env")

    @sandbox
    def test_license_remote_off_is_honoured(self, env):
        os.environ["KRAKEN_LICENSE_REMOTE"] = "0"
        merged, _ = cc.resolve()
        self.assertIs(merged["license"]["remote"], False)

    @sandbox
    def test_env_beats_every_scope(self, env):
        env.write("project", "telemetry:\n  enabled: true\n")
        os.environ["KRAKEN_OFFLINE"] = "1"
        merged, _ = cc.resolve()
        self.assertIs(merged["telemetry"]["enabled"], False)


class Validation(unittest.TestCase):
    @sandbox
    def test_a_clean_config_has_no_problems(self, env):
        env.write("user", "data_dir: data\ndocker:\n  enabled: false\n")
        self.assertEqual(cc.validate_config(), [])

    @sandbox
    def test_unknown_setting_is_reported(self, env):
        env.write("user", "wibble: 1\n")
        problems = cc.validate_config()
        self.assertTrue(any("wibble" in p for p in problems))

    @sandbox
    def test_wrong_type_is_reported(self, env):
        env.write("user", "data_dir: 7\n")
        problems = cc.validate_config()
        self.assertTrue(any("should be string" in p for p in problems))

    @sandbox
    def test_bool_is_not_accepted_as_int(self, env):
        env.write("user", "version: true\n")
        self.assertTrue(any("version" in p for p in cc.validate_config()))

    @sandbox
    def test_unknown_nested_key_is_reported(self, env):
        env.write("user", "docker:\n  wibble: 1\n")
        problems = cc.validate_config()
        self.assertTrue(any("docker.wibble" in p for p in problems))

    @sandbox
    def test_future_version_is_reported(self, env):
        env.write("user", f"version: {cs.SUPPORTED_VERSION + 1}\n")
        self.assertTrue(any("newer than" in p for p in cc.validate_config()))

    @sandbox
    def test_public_docker_network_is_refused(self, env):
        env.write("user", "docker:\n  enabled: true\n  public: true\n")
        problems = cc.validate_config()
        self.assertTrue(any("public" in p for p in problems))

    @sandbox
    def test_unknown_notify_channel_is_reported(self, env):
        env.write("user", "notify:\n  channels:\n    - carrier-pigeon\n")
        self.assertTrue(any("carrier-pigeon" in p for p in cc.validate_config()))

    @sandbox
    def test_bad_policy_default_is_reported(self, env):
        env.write("user", "policy:\n  default: maybe\n")
        self.assertTrue(any("policy.default" in p for p in cc.validate_config()))

    @sandbox
    def test_unknown_hook_event_is_reported(self, env):
        env.write("user", "hooks:\n  after_lunch:\n    - echo\n")
        self.assertTrue(any("after_lunch" in p for p in cc.validate_config()))

    @sandbox
    def test_valid_hook_event_passes(self, env):
        env.write(
            "user", "hooks:\n  after_run:\n    - tentacle: echo\n      action: ping\n"
        )
        self.assertEqual(cc.validate_config(), [])

    @sandbox
    def test_hook_without_a_tentacle_is_reported(self, env):
        env.write("user", "hooks:\n  after_run:\n    - action: ping\n")
        self.assertTrue(any("tentacle" in p for p in cc.validate_config()))

    @sandbox
    def test_non_mapping_file_is_reported(self, env):
        env.write("user", "- just\n- a list\n")
        self.assertTrue(any("mapping" in p for p in cc.validate_config()))

    @sandbox
    def test_bad_notify_shorthand_is_reported(self, env):
        env.write("user", "notify: loud\n")
        self.assertTrue(any("shorthand" in p for p in cc.validate_config()))

    @sandbox
    def test_known_notify_shorthand_is_accepted(self, env):
        for word in cs.NOTIFY_SHORTHAND:
            env.write("user", f"notify: {word}\n")
            self.assertEqual(cc.validate_config(), [], f"{word} should be accepted")

    @sandbox
    def test_problems_name_the_offending_file(self, env):
        env.write("project", "wibble: 1\n")
        problems = cc.validate_config()
        self.assertTrue(any(str(env.project) in p for p in problems))

    def test_every_generated_example_validates(self):
        for scope in ("system", "user", "project"):
            with tempfile.TemporaryDirectory() as raw:
                tmp = Path(raw)
                body = cc.example_yaml(scope)
                target = tmp / scope / "config.yaml"
                target.parent.mkdir(parents=True)
                target.write_text(body, encoding="utf-8")
                import yaml

                data = yaml.safe_load(body)
                for key in data:
                    self.assertIn(
                        key, cs.BY_KEY, f"{scope} example has unknown key {key}"
                    )
                self.assertIsInstance(data["version"], int)


class SettingsThatDoSomething(unittest.TestCase):
    """Not just stored: the ones with behaviour are wired to it."""

    @sandbox
    def test_data_dir_is_honoured(self, env):
        env.write("user", "data_dir: armstore\n")
        self.assertEqual(data_root().name, "armstore")
        self.assertEqual(layout_dirs()["data"], "armstore")

    @sandbox
    def test_data_dir_defaults_when_unset(self, env):
        self.assertEqual(data_root().name, "data")

    @sandbox
    def test_log_and_cache_dirs_are_honoured(self, env):
        env.write("user", "log_dir: l\ncache_dir: c\nkey_dir: k\n")
        dirs = layout_dirs()
        self.assertEqual((dirs["log"], dirs["cache"], dirs["key"]), ("l", "c", "k"))

    @sandbox
    def test_notify_channels_come_from_config(self, env):
        env.write("user", "notify:\n  channels:\n    - stdout\n")
        self.assertEqual(notify_mod.enabled_channels(), ["stdout"])

    @sandbox
    def test_notify_defaults_to_stdout_only(self, env):
        self.assertEqual(notify_mod.enabled_channels(), ["stdout"])

    @sandbox
    def test_notify_ntfy_is_off_unless_asked(self, env):
        env.write("user", "notify:\n  channels:\n    - ntfy\n")
        self.assertEqual(notify_mod.enabled_channels(), ["ntfy"])

    @sandbox
    def test_notify_shorthand_drives_channels(self, env):
        env.write("user", "notify: none\n")
        self.assertEqual(notify_mod.enabled_channels(), [])

    @sandbox
    def test_allow_defaults_to_deny(self, env):
        env.write("user", "data_dir: data\n")
        self.assertFalse(any(read_allow().values()), "nothing granted by default")

    @sandbox
    def test_allow_grants_only_what_is_true(self, env):
        env.write("user", "allow:\n  expose: true\n  tunnel: false\n")
        allowed = read_allow()
        self.assertIs(allowed["expose"], True)
        self.assertIs(allowed["tunnel"], False)

    @sandbox
    def test_a_commented_grant_is_not_a_grant(self, env):
        # The bug: the old resolver grepped for "expose: true" in the file
        # text, so this granted the capability.
        env.write("user", "# expose: true\n# tunnel: true\n")
        allowed = read_allow()
        self.assertFalse(allowed["expose"])
        self.assertFalse(allowed["tunnel"])

    @sandbox
    def test_project_scope_can_deny_a_user_grant(self, env):
        env.write("user", "allow:\n  expose: true\n")
        env.write("project", "allow:\n  expose: false\n")
        self.assertIs(read_allow()["expose"], False)

    @sandbox
    def test_policy_network_feeds_the_docker_resolver(self, env):
        env.write("user", "docker:\n  enabled: true\n")
        env.write("project", "policy:\n  network: kraken\n")
        from kraken.core.network import resolve_docker

        self.assertEqual(resolve_docker()["name"], "kraken")

    @sandbox
    def test_docker_enabled_false_means_no_network(self, env):
        from kraken.core.network import resolve_docker

        env.write("user", "docker:\n  enabled: false\n")
        self.assertIs(resolve_docker()["enabled"], False)

    @sandbox
    def test_tentacles_config_is_what_the_runner_reads(self, env):
        env.write(
            "user",
            "tentacles:\n  - name: demo\n    binary: /bin/echo\n    actions: [ping]\n",
        )
        from kraken.core.config import load_config

        self.assertEqual(load_config()["tentacles"][0]["name"], "demo")


class Cli(unittest.TestCase):
    """The verb is the interface; exercise it as a subprocess."""

    def run_cli(self, *args, env=None):
        environment = dict(os.environ)
        environment.setdefault("KRAKEN_HOME", tempfile.mkdtemp())
        environment["PYTHONPATH"] = str(ROOT)
        if env:
            environment.update(env)
        proc = subprocess.run(
            [sys.executable, "-m", "kraken", "config", *args],
            capture_output=True,
            text=True,
            env=environment,
            cwd=str(ROOT),
            check=False,
        )
        return proc

    def test_list_is_valid_json_when_piped(self):
        proc = self.run_cli("list")
        payload = json.loads(proc.stdout)
        self.assertTrue(payload["ok"])
        self.assertEqual(len(payload["settings"]), len(cs.SETTINGS))
        self.assertEqual(proc.returncode, 0)

    def test_get_one_setting(self):
        payload = json.loads(self.run_cli("get", "data_dir").stdout)
        self.assertEqual(payload["key"], "data_dir")
        self.assertEqual(payload["value"], "data")

    def test_get_unknown_key_exits_two(self):
        proc = self.run_cli("get", "nope")
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(json.loads(proc.stdout)["error"]["code"], "unknown_key")

    def test_explain_names_the_winning_file(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            (tmp / ".kraken").mkdir()
            (tmp / ".kraken" / "config.yaml").write_text("data_dir: from-project\n")
            work = tmp / "work"
            work.mkdir()
            proc = subprocess.run(
                [sys.executable, "-m", "kraken", "config", "explain", "data_dir"],
                capture_output=True,
                text=True,
                env={
                    **os.environ,
                    "PYTHONPATH": str(ROOT),
                    "KRAKEN_HOME": str(tmp / "home"),
                    "KRAKEN_SYSTEM_DIR": str(tmp / "system"),
                },
                cwd=str(work),
                check=False,
            )
            payload = json.loads(proc.stdout)
            self.assertEqual(payload["effective"], "from-project")
            self.assertEqual(payload["won_by"]["scope"], "project")

    def test_path_lists_the_chain(self):
        payload = json.loads(self.run_cli("path").stdout)
        self.assertTrue(any(c["scope"] == "user" for c in payload["chain"]))

    def test_validate_clean_exits_zero(self):
        proc = self.run_cli("validate")
        self.assertEqual(proc.returncode, 0)
        self.assertTrue(json.loads(proc.stdout)["valid"])

    def test_validate_bad_exits_two_and_lists_problems(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            home = tmp / "home"
            (home / ".kraken").mkdir(parents=True)
            (home / ".kraken" / "config.yaml").write_text("wibble: 1\n")
            proc = subprocess.run(
                [sys.executable, "-m", "kraken", "config", "validate"],
                capture_output=True,
                text=True,
                env={
                    **os.environ,
                    "PYTHONPATH": str(ROOT),
                    "KRAKEN_HOME": str(home),
                    "KRAKEN_SYSTEM_DIR": str(tmp / "system"),
                },
                cwd=str(tmp),
                check=False,
            )
            self.assertEqual(proc.returncode, 2)
            self.assertTrue(
                any("wibble" in p for p in json.loads(proc.stdout)["problems"])
            )

    def test_init_writes_a_validating_example(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            work = tmp / "work"
            work.mkdir()
            common = {
                **os.environ,
                "PYTHONPATH": str(ROOT),
                "KRAKEN_HOME": str(tmp / "home"),
                "KRAKEN_SYSTEM_DIR": str(tmp / "system"),
            }
            proc = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "kraken",
                    "config",
                    "init",
                    "--scope",
                    "project",
                ],
                capture_output=True,
                text=True,
                env=common,
                cwd=str(work),
                check=False,
            )
            self.assertEqual(proc.returncode, 0)
            written = work / ".kraken" / "config.yaml"
            self.assertTrue(written.is_file())
            check = subprocess.run(
                [sys.executable, "-m", "kraken", "config", "validate"],
                capture_output=True,
                text=True,
                env=common,
                cwd=str(work),
                check=False,
            )
            self.assertEqual(check.returncode, 0, check.stdout)

    def test_init_refuses_to_clobber(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            work = tmp / "work"
            work.mkdir()
            target = work / ".kraken"
            target.mkdir()
            (target / "config.yaml").write_text("data_dir: mine\n")
            proc = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "kraken",
                    "config",
                    "init",
                    "--scope",
                    "project",
                ],
                capture_output=True,
                text=True,
                env={
                    **os.environ,
                    "PYTHONPATH": str(ROOT),
                    "KRAKEN_HOME": str(tmp / "home"),
                    "KRAKEN_SYSTEM_DIR": str(tmp / "system"),
                },
                cwd=str(work),
                check=False,
            )
            self.assertEqual(proc.returncode, 2)
            self.assertEqual((target / "config.yaml").read_text(), "data_dir: mine\n")

    def test_shipped_examples_match_what_init_writes(self):
        for name, scope in (
            ("system", "system"),
            ("user", "user"),
            ("project", "project"),
        ):
            shipped = ROOT / "examples" / "config" / f"{name}.yaml"
            self.assertTrue(shipped.is_file(), f"examples/config/{name}.yaml missing")
            self.assertEqual(
                shipped.read_text(encoding="utf-8"),
                cc.example_yaml(scope),
                f"{name}.yaml has drifted from config init",
            )


if __name__ == "__main__":
    unittest.main()
