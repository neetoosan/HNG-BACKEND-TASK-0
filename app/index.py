"""Vercel FastAPI entrypoint.

Vercel auto-detects FastAPI apps from app/index.py, while local development
continues to use app.main:app.
"""

from app.main import app
