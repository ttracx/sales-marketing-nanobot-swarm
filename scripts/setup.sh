#!/bin/bash
set -e
echo "🚀 Setting up Sales & Marketing Nanobot Swarm..."
pip install -e ".[dev]"
cp -n .env.example .env 2>/dev/null || true
echo "✅ Setup complete! Edit .env then run: uvicorn nanobot.api.gateway:app --port 8200"
