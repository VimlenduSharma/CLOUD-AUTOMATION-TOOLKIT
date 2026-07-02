# API Examples

## Health

```bash
curl http://localhost:8080/api/health
```

## Fleet Summary

```bash
curl http://localhost:8080/api/fleet
```

## Ingest Report

```bash
curl -X POST http://localhost:8080/api/reports \
  -H "Content-Type: application/json" \
  --data @sample-data/report.json
```

## Run Custom Checks

```bash
curl -X POST http://localhost:8080/api/checks \
  -H "Content-Type: application/json" \
  -d '{
    "dns": ["github.com"],
    "tcp": [{ "host": "github.com", "port": 443 }],
    "http": ["https://github.com"],
    "disk": [{ "path": "/", "minimum_free_percent": 10 }],
    "permissions": [{ "path": ".", "mode": "read" }]
  }'
```
