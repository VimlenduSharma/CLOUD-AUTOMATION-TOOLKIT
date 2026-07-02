from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class FleetStore:
    def __init__(self, path: str | os.PathLike[str]) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("[]\n", encoding="utf-8")

    def all(self) -> list[dict[str, Any]]:
        return json.loads(self.path.read_text(encoding="utf-8"))

    def add_report(self, report: dict[str, Any]) -> dict[str, Any]:
        reports = self.all()
        enriched = {
            "received_at": datetime.now(UTC).isoformat(),
            **report,
        }
        reports.append(enriched)
        self.path.write_text(json.dumps(reports, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return enriched

    def summary(self) -> dict[str, Any]:
        reports = self.all()
        newest_by_host: dict[str, dict[str, Any]] = {}
        for report in reports:
            host = str(report.get("hostname", "unknown"))
            newest_by_host[host] = report

        hosts = list(newest_by_host.values())
        critical = [host for host in hosts if _host_status(host) == "critical"]
        warning = [host for host in hosts if _host_status(host) == "warning"]
        healthy = [host for host in hosts if _host_status(host) == "healthy"]
        return {
            "total_hosts": len(hosts),
            "healthy": len(healthy),
            "warning": len(warning),
            "critical": len(critical),
            "reports_received": len(reports),
            "hosts": sorted(hosts, key=lambda item: str(item.get("hostname", ""))),
        }


def _host_status(report: dict[str, Any]) -> str:
    cpu = float(report.get("cpu_percent", 0))
    memory = float(report.get("memory_percent", 0))
    failed_services = int(report.get("failed_services", 0))
    failed_checks = sum(1 for check in report.get("checks", []) if check.get("status") == "fail")
    if cpu >= 90 or memory >= 90 or failed_services > 0 or failed_checks > 0:
        return "critical"
    if cpu >= 75 or memory >= 75:
        return "warning"
    return "healthy"

