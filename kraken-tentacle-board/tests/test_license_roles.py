#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = Path(os.environ.get("KRAKEN_SRC") or "/tmp/kraken-builder-src")
if (SRC / "kraken").is_dir():
    sys.path.insert(0, str(SRC))


class BoardLicenseRoles(unittest.TestCase):
    def test_manifest_is_free(self) -> None:
        self.assertIn("license: free", (ROOT / "tentacle.yaml").read_text(encoding="utf-8"))

    @unittest.skipUnless((SRC / "kraken" / "core" / "license.py").exists(), "kraken.core missing")
    def test_free_assert_and_premium_overlay(self) -> None:
        from kraken.core.license import LicenseError, assert_licensed, set_key

        with tempfile.TemporaryDirectory() as tmp:
            os.environ["KRAKEN_HOME"] = tmp
            assert_licensed("board", {"license": "free"}, home=Path(tmp))
            with self.assertRaises(LicenseError):
                assert_licensed("board", {"license": "premium"}, home=Path(tmp))
            os.environ["KRAKEN_LICENSE_OFFLINE"] = "1"
            set_key("board", "k_test_board", home=Path(tmp))
            assert_licensed("board", {"license": "premium"}, home=Path(tmp))


if __name__ == "__main__":
    unittest.main()
