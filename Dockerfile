FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app
COPY backend ./backend
COPY frontend ./frontend
COPY sample-data ./sample-data

ENV PYTHONPATH=/app/backend
EXPOSE 8080

CMD ["python", "-m", "fleet_health.app"]

