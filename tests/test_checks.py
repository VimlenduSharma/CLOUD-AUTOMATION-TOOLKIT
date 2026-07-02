from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from fleet_health.checks import disk_threshold, file_permission, run_checks


class CheckTests(unittest.TestCase):
    def test_file_permission_reports_existing_readable_file(self) -> None:
        with tempfile.NamedTemporaryFile() as handle:
            result = file_permission(handle.name, "read")
        self.assertEqual(result.status, "pass")
        self.assertEqual(result.metadata["mode"], "read")

    def test_file_permission_rejects_unknown_mode(self) -> None:
        result = file_permission("anything", "admin")
        self.assertEqual(result.status, "fail")

    def test_disk_threshold_has_capacity_metadata(self) -> None:
        result = disk_threshold("/")
        self.assertIn(result.status, {"pass", "fail"})
        self.assertIn("free_percent", result.metadata)

    def test_run_checks_accepts_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            results = run_checks(
                {
                    "disk": [{"path": "/", "minimum_free_percent": 1}],
                    "permissions": [{"path": tmp, "mode": "read"}],
                }
            )
        self.assertEqual(len(results), 2)
        self.assertTrue(all("status" in item for item in results))


if __name__ == "__main__":
    unittest.main()
