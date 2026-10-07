#!/bin/sh
# run migrations then start the api
set -e
alembic upgrade head
exec uvicorn src.app.api.main:app --host 0.0.0.0 --port 8000
