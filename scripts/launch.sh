#!/bin/bash
set -e
source .env 2>/dev/null || true
uvicorn nanobot.api.gateway:app --host 0.0.0.0 --port ${PORT:-8200} --reload
