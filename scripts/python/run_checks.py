#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from fleet_health.checks import run_checks  # noqa: E402


DEFAULT_CONFIG = {
    "dns": ["github.com", "microsoft.com"],
    "tcp": [{"host": "github.com", "port": 443}],
    "http": ["https://github.com"],
    "disk": [{"path": "/", "minimum_free_percent": 10}],
    "permissions": [{"path": str(ROOT), "mode": "read"}],
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run fleet health diagnostics.")
    parser.add_argument("--api", help="Optional API base URL, for example http://localhost:8080")
    parser.add_argument("--config", help="JSON file containing diagnostic targets.")
    args = parser.parse_args()

    config = DEFAULT_CONFIG
    if args.config:
        config = json.loads(Path(args.config).read_text(encoding="utf-8"))

    results = run_checks(config)
    print(json.dumps({"checks": results}, indent=2))

    if args.api:
        body = json.dumps(config).encode("utf-8")
        request = urllib.request.Request(
            f"{args.api.rstrip('/')}/api/checks",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=10) as response:
            print(response.read().decode("utf-8"))

    return 1 if any(check["status"] == "fail" for check in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())

