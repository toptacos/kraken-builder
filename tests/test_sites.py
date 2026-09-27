#!/usr/bin/env python3
"""The site-tentacle contract: a new face is a new yaml, not a new droplet.

Also proves the validator actually rejects bad input — a validator that only
passes is worse than none.
"""

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_sites import REQUIRED, validate_dir, validate_file  # noqa: E402

SITES = ROOT / "sites"


def write(name: str, body: str) -> Path:
    d = Path(tempfile.mkdtemp())
    p = d / f"{name}.yaml"
    p.write_text(body, encoding="utf-8")
    return p


class ShippedSites(unittest.TestCase):
    def test_all_shipped_sites_are_valid(self):
        self.assertEqual(validate_dir(SITES), [])

    def test_every_required_vhost_exists(self):
        have = {p.stem for p in SITES.glob("*.yaml")}
        self.assertEqual(REQUIRED - have, set())

    def test_seven_faces(self):
        self.assertEqual(len(list(SITES.glob("*.yaml"))), 7)


class Rejections(unittest.TestCase):
    def test_rejects_name_filename_mismatch(self):
        p = write(
            "thing",
            "name: other\nhost: thing.topta.co\nmount: site\nlicense: free\napi:\n  collection: x\n",
        )
        self.assertTrue(any("does not match filename" in x for x in validate_file(p)))

    def test_rejects_wrong_host(self):
        p = write(
            "thing",
            "name: thing\nhost: wrong.example.com\nmount: site\nlicense: free\napi:\n  collection: x\n",
        )
        self.assertTrue(any("host" in x for x in validate_file(p)))

    def test_rejects_bad_mount(self):
        p = write(
            "thing",
            "name: thing\nhost: thing.topta.co\nmount: daemon\nlicense: free\napi:\n  collection: x\n",
        )
        self.assertTrue(any("mount must be" in x for x in validate_file(p)))

    def test_rejects_bad_license(self):
        p = write(
            "thing",
            "name: thing\nhost: thing.topta.co\nmount: site\nlicense: crack\napi:\n  collection: x\n",
        )
        self.assertTrue(any("license must be" in x for x in validate_file(p)))

    def test_requires_api_collection(self):
        p = write(
            "thing", "name: thing\nhost: thing.topta.co\nmount: site\nlicense: free\n"
        )
        self.assertTrue(any("api.collection" in x for x in validate_file(p)))

    def test_cli_mount_requires_cli_block(self):
        p = write(
            "thing",
            "name: thing\nhost: thing.topta.co\nmount: cli\nlicense: free\napi:\n  collection: x\n",
        )
        self.assertTrue(any("requires a cli block" in x for x in validate_file(p)))

    def test_rejects_secret_key(self):
        p = write(
            "thing",
            "name: thing\nhost: thing.topta.co\nmount: site\nlicense: free\n"
            "api:\n  collection: x\n  token: abc\n",
        )
        self.assertTrue(any("must not appear" in x for x in validate_file(p)))

    def test_rejects_secret_looking_value(self):
        p = write(
            "thing",
            "name: thing\nhost: thing.topta.co\nmount: site\nlicense: free\n"
            "api:\n  collection: x\n  note: sk-abcdef123456\n",
        )
        self.assertTrue(any("looks like a secret" in x for x in validate_file(p)))

    def test_rejects_private_key_block(self):
        p = write(
            "thing",
            "name: thing\nhost: thing.topta.co\nmount: site\nlicense: free\n"
            "api:\n  collection: x\n  cert: '-----BEGIN RSA PRIVATE KEY-----'\n",
        )
        self.assertTrue(any("looks like a secret" in x for x in validate_file(p)))

    def test_rejects_malformed_yaml(self):
        p = write("thing", "name: [unclosed\n")
        self.assertTrue(any("not valid YAML" in x for x in validate_file(p)))

    def test_rejects_non_mapping(self):
        p = write("thing", "- just\n- a list\n")
        self.assertTrue(any("must be a mapping" in x for x in validate_file(p)))

    def test_duplicate_host_is_caught(self):
        d = Path(tempfile.mkdtemp())
        body = "name: {n}\nhost: dup.topta.co\nmount: site\nlicense: free\napi:\n  collection: x\n"
        (d / "one.yaml").write_text(body.format(n="one"), encoding="utf-8")
        (d / "two.yaml").write_text(body.format(n="two"), encoding="utf-8")
        problems = validate_dir(d)
        self.assertTrue(any("already claimed" in x for x in problems))

    def test_missing_required_site_is_caught(self):
        d = Path(tempfile.mkdtemp())
        (d / "tacos.yaml").write_text(
            "name: tacos\nhost: tacos.topta.co\nmount: site\nlicense: free\napi:\n  collection: x\n",
            encoding="utf-8",
        )
        problems = validate_dir(d)
        self.assertTrue(any("missing required site yaml" in x for x in problems))

    def test_empty_dir_is_an_error(self):
        problems = validate_dir(Path(tempfile.mkdtemp()))
        self.assertTrue(any("no site yaml" in x for x in problems))


class KrakenSite(unittest.TestCase):
    def test_kraken_declares_the_shared_network(self):
        import yaml

        doc = yaml.safe_load((SITES / "kraken.yaml").read_text(encoding="utf-8"))
        self.assertEqual(doc["cli"]["network"], "kraken")
        self.assertEqual(doc["cli"]["command"], "up")
        self.assertEqual(doc["mount"], "both")

    def test_profile_gates_the_other_hosts(self):
        import yaml

        doc = yaml.safe_load((SITES / "profile.yaml").read_text(encoding="utf-8"))
        self.assertTrue(doc["auth"]["required"])
        for host in ("blog", "tacos", "music", "discgolf", "kraken", "portfolio"):
            self.assertIn(host, doc["auth"]["gate_hosts"])


if __name__ == "__main__":
    unittest.main()
