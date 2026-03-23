#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-dev}"

case "$MODE" in
  dev)
    echo "Starting in development mode..."
    # Start ARQ worker in the background
    uv run arq app.worker.WorkerSettings &

    uv run uvicorn app.main:app \
      --host 0.0.0.0 \
      --port 8000 \
      --reload \
      --log-level debug
    ;;

  prod)
    echo "Starting in production mode..."
    uv run arq app.worker.WorkerSettings &

    uv run gunicorn app.main:app \
      --config app/gunicorn_config.py
    ;;

  *)
    echo "Usage: ./app/run.sh [dev|prod]"
    exit 1
    ;;
esac
