# Requirements Trace

| Requirement | Implementation |
| --- | --- |
| PowerShell scripts collect Windows system health | `scripts/powershell/Collect-FleetHealth.ps1` |
| Python scripts collect/check health signals | `scripts/python/run_checks.py`, `backend/fleet_health/checks.py` |
| CPU and memory collection | PowerShell CIM queries in collector |
| HTTP endpoint checks | PowerShell `Invoke-WebRequest`, Python `urllib.request` |
| DNS resolution checks | PowerShell `Resolve-DnsName`, Python `socket.getaddrinfo` |
| TCP connectivity checks | PowerShell `TcpClient`, Python `socket.create_connection` |
| Disk thresholds | Python `disk_threshold` diagnostic |
| File permissions | Python `file_permission` diagnostic |
| GitHub Actions script checks | `.github/workflows/ci.yml` |
| Clear setup, execution, debugging docs | `README.md`, `docs/OPERATIONS.md` |
| Docker/Linux support | `Dockerfile`, `docker-compose.yml` |
| Logs | Backend emits structured JSON request logs |
| Beautiful frontend | `frontend/index.html`, `frontend/styles.css`, `frontend/app.js` |

