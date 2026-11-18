#!/bin/bash
# Starts the FastAPI backend on http://localhost:8000  (API docs: /docs)
cd "$(dirname "$0")/backend"
exec .venv/bin/uvicorn app.main:app --reload --port 8000
