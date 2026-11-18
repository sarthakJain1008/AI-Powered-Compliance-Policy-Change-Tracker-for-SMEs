#!/bin/bash
# Backend (FastAPI) on http://localhost:8000   API docs: http://localhost:8000/docs
cd "$(dirname "$0")/backend"
exec .venv/bin/uvicorn app.main:app --reload --port 8000
