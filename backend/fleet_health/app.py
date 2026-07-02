from __future__ import annotations

import json
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from fleet_health.checks import run_checks
from fleet_health.store import FleetStore


ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = ROOT / "frontend"
DATA_PATH = Path(os.environ.get("FLEET_DATA_PATH", ROOT / "data" / "reports.json"))
DEFAULT_CHECK_CONFIG = {
    "dns": ["github.com", "microsoft.com"],
    "tcp": [{"host": "github.com", "port": 443}],
    "http": ["https://github.com"],
    "disk": [{"path": "/", "minimum_free_percent": 10}],
    "permissions": [{"path": str(ROOT), "mode": "read"}],
}


class FleetRequestHandler(SimpleHTTPRequestHandler):
    store = FleetStore(DATA_PATH)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(FRONTEND_DIR), **kwargs)

    def do_GET(self) -> None:
        route = urlparse(self.path).path
        if route == "/api/health":
            self._json({"status": "ok", "service": "windows-fleet-health-api"})
            return
        if route == "/api/fleet":
            self._json(self.store.summary())
            return
        if route == "/api/checks":
            self._json({"checks": run_checks(DEFAULT_CHECK_CONFIG)})
            return
        if route == "/":
            self.path = "/index.html"
        super().do_GET()

    def do_POST(self) -> None:
        route = urlparse(self.path).path
        if route == "/api/reports":
            payload = self._read_json()
            errors = _validate_report(payload)
            if errors:
                self._json({"errors": errors}, status=400)
                return
            self._json(self.store.add_report(payload), status=201)
            return
        if route == "/api/checks":
            payload = self._read_json()
            self._json({"checks": run_checks(payload)})
            return
        self._json({"error": "not_found"}, status=404)

    def log_message(self, format: str, *args: Any) -> None:
        print(json.dumps({"level": "info", "client": self.address_string(), "message": format % args}))

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8")
        return json.loads(raw or "{}")

    def _json(self, payload: dict[str, Any], status: int = 200) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def _validate_report(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in ["hostname", "cpu_percent", "memory_percent"]:
        if key not in payload:
            errors.append(f"{key} is required")
    for numeric_key in ["cpu_percent", "memory_percent", "failed_services"]:
        if numeric_key in payload:
            try:
                float(payload[numeric_key])
            except (TypeError, ValueError):
                errors.append(f"{numeric_key} must be numeric")
    return errors


def main() -> None:
    port = int(os.environ.get("PORT", "8080"))
    server = ThreadingHTTPServer(("0.0.0.0", port), FleetRequestHandler)
    print(json.dumps({"level": "info", "message": f"Fleet Health API listening on {port}"}))
    server.serve_forever()


if __name__ == "__main__":
    main()

