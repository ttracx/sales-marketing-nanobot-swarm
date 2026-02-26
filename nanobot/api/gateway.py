"""
Gateway entry point for Docker / Railway / Render deployments.
Imports and re-exports the Vercel API app.
"""
from api.index import app

__all__ = ["app"]
