from __future__ import annotations

import os
import socket
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


@dataclass
class CheckResult:
    name: str
    status: str
    message: str
    latency_ms: int | None = None
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "name": self.name,
            "status": self.status,
            "message": self.message,
        }
        if self.latency_ms is not None:
            payload["latency_ms"] = self.latency_ms
        if self.metadata:
            payload["metadata"] = self.metadata
        return payload


def _elapsed_ms(start: float) -> int:
    return round((time.perf_counter() - start) * 1000)


def dns_resolution(hostname: str, timeout_seconds: float = 3.0) -> CheckResult:
    start = time.perf_counter()
    previous_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(timeout_seconds)
    try:
        addresses = socket.getaddrinfo(hostname, None)
        unique_ips = sorted({item[4][0] for item in addresses})
        return CheckResult(
            name="dns_resolution",
            status="pass",
            message=f"{hostname} resolved to {len(unique_ips)} address(es).",
            latency_ms=_elapsed_ms(start),
            metadata={"hostname": hostname, "addresses": unique_ips[:8]},
        )
    except socket.gaierror as exc:
        return CheckResult(
            name="dns_resolution",
            status="fail",
            message=f"{hostname} could not be resolved: {exc}.",
            latency_ms=_elapsed_ms(start),
            metadata={"hostname": hostname},
        )
    finally:
        socket.setdefaulttimeout(previous_timeout)


def tcp_connectivity(hostname: str, port: int, timeout_seconds: float = 3.0) -> CheckResult:
    start = time.perf_counter()
    try:
        with socket.create_connection((hostname, port), timeout=timeout_seconds):
            return CheckResult(
                name="tcp_connectivity",
                status="pass",
                message=f"Connected to {hostname}:{port}.",
                latency_ms=_elapsed_ms(start),
                metadata={"hostname": hostname, "port": port},
            )
    except OSError as exc:
        return CheckResult(
            name="tcp_connectivity",
            status="fail",
            message=f"Could not connect to {hostname}:{port}: {exc}.",
            latency_ms=_elapsed_ms(start),
            metadata={"hostname": hostname, "port": port},
        )


def http_endpoint(url: str, timeout_seconds: float = 5.0) -> CheckResult:
    start = time.perf_counter()
    request = urllib.request.Request(url, headers={"User-Agent": "fleet-health-check/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            status_code = response.status
            result = "pass" if 200 <= status_code < 400 else "warn"
            return CheckResult(
                name="http_endpoint",
                status=result,
                message=f"{url} returned HTTP {status_code}.",
                latency_ms=_elapsed_ms(start),
                metadata={"url": url, "status_code": status_code},
            )
    except urllib.error.HTTPError as exc:
        return CheckResult(
            name="http_endpoint",
            status="fail",
            message=f"{url} returned HTTP {exc.code}.",
            latency_ms=_elapsed_ms(start),
            metadata={"url": url, "status_code": exc.code},
        )
    except urllib.error.URLError as exc:
        return CheckResult(
            name="http_endpoint",
            status="fail",
            message=f"{url} is unreachable: {exc.reason}.",
            latency_ms=_elapsed_ms(start),
            metadata={"url": url},
        )


def disk_threshold(path: str, minimum_free_percent: float = 15.0) -> CheckResult:
    usage = os.statvfs(path)
    total = usage.f_blocks * usage.f_frsize
    free = usage.f_bavail * usage.f_frsize
    free_percent = (free / total) * 100 if total else 0
    status = "pass" if free_percent >= minimum_free_percent else "fail"
    return CheckResult(
        name="disk_threshold",
        status=status,
        message=f"{path} has {free_percent:.1f}% free space.",
        metadata={
            "path": path,
            "free_percent": round(free_percent, 2),
            "minimum_free_percent": minimum_free_percent,
            "free_gb": round(free / 1024**3, 2),
            "total_gb": round(total / 1024**3, 2),
        },
    )


def file_permission(path: str, mode: str = "read") -> CheckResult:
    checks = {
        "read": os.R_OK,
        "write": os.W_OK,
        "execute": os.X_OK,
    }
    if mode not in checks:
        return CheckResult(
            name="file_permission",
            status="fail",
            message=f"Unsupported permission mode: {mode}.",
            metadata={"path": path, "mode": mode},
        )
    exists = os.path.exists(path)
    allowed = exists and os.access(path, checks[mode])
    return CheckResult(
        name="file_permission",
        status="pass" if allowed else "fail",
        message=f"{path} {'allows' if allowed else 'does not allow'} {mode} access.",
        metadata={"path": path, "mode": mode, "exists": exists},
    )


def run_checks(config: dict[str, Any]) -> list[dict[str, Any]]:
    results: list[CheckResult] = []
    for hostname in config.get("dns", []):
        results.append(dns_resolution(str(hostname)))
    for target in config.get("tcp", []):
        results.append(tcp_connectivity(str(target["host"]), int(target["port"])))
    for url in config.get("http", []):
        results.append(http_endpoint(str(url)))
    for disk in config.get("disk", []):
        results.append(disk_threshold(str(disk.get("path", "/")), float(disk.get("minimum_free_percent", 15))))
    for permission in config.get("permissions", []):
        results.append(file_permission(str(permission["path"]), str(permission.get("mode", "read"))))
    return [result.to_dict() for result in results]

