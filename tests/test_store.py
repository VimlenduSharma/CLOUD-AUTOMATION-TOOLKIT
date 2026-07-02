from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from fleet_health.store import FleetStore


class FleetStoreTests(unittest.TestCase):
    def test_summary_uses_latest_report_per_host(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = FleetStore(Path(tmp) / "reports.json")
            store.add_report({"hostname": "WIN-1", "cpu_percent": 20, "memory_percent": 30, "failed_services": 0})
            store.add_report({"hostname": "WIN-1", "cpu_percent": 95, "memory_percent": 30, "failed_services": 0})

            summary = store.summary()

        self.assertEqual(summary["total_hosts"], 1)
        self.assertEqual(summary["critical"], 1)
        self.assertEqual(summary["reports_received"], 2)


if __name__ == "__main__":
    unittest.main()
