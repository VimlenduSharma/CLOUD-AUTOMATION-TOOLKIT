# Operations Guide

## Deployment Model

Run the API on a Linux VM, container host, or internal platform. Windows servers and workstations execute the PowerShell collector on a schedule and POST JSON health reports to the API.

## Suggested Scheduled Task

```powershell
$Action = New-ScheduledTaskAction `
  -Execute "pwsh" `
  -Argument "-File C:\FleetHealth\Collect-FleetHealth.ps1 -ApiUrl http://fleet-api:8080/api/reports"

$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 15)
Register-ScheduledTask -TaskName "Fleet Health Collector" -Action $Action -Trigger $Trigger -Description "Collect Windows fleet health every 15 minutes"
```

## Threshold Defaults

| Signal | Warning | Critical |
| --- | ---: | ---: |
| CPU | 75% | 90% |
| Memory | 75% | 90% |
| Failed services | n/a | greater than 0 |
| Failed checks | n/a | greater than 0 |

## Production Hardening Ideas

- Place the API behind TLS and authentication.
- Replace JSON file storage with SQLite or PostgreSQL when report volume grows.
- Add host groups and ownership metadata.
- Export summary metrics to Prometheus or another monitoring stack.
- Store collector logs in Windows Event Log or a central log platform.

