#!/usr/bin/env bash
set -e

echo "=== Boot: restoring artifacts (if available) ==="

mkdir -p models
mkdir -p data/processed

if [ -f "artifacts/model.joblib" ]; then
  cp -f artifacts/model.joblib models/model.joblib
  echo "OK: models/model.joblib restored"
else
  echo "WARN: artifacts/model.joblib not found"
fi

if [ -f "artifacts/ultima_rodada.csv" ]; then
  cp -f artifacts/ultima_rodada.csv data/processed/ultima_rodada.csv
  echo "OK: data/processed/ultima_rodada.csv restored"
else
  echo "WARN: artifacts/ultima_rodada.csv not found"
fi

echo "=== Starting API on port ${PORT:-8000} ==="
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
