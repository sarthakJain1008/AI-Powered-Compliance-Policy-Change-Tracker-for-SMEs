#!/bin/bash
# Starts the Next.js frontend on http://localhost:3000
cd "$(dirname "$0")/frontend"
exec npm run dev
