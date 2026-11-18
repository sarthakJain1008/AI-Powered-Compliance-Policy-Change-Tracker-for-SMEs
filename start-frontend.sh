#!/bin/bash
# Frontend (Next.js) on http://localhost:3000, proxying /api to the backend on 8000
cd "$(dirname "$0")/frontend"
exec npm run dev
