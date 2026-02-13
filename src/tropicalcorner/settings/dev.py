"""
Development settings for Tropical Corner.
"""

from .base import *  # noqa: F401, F403

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "backend", "10.1.21.49","2ce477f42335.ngrok-free.app"]

# CORS for development (frontend on different port)
CSRF_TRUSTED_ORIGINS = [
    "http://localhost",
    "http://localhost:5173",
    "http://127.0.0.1",
    "http://10.1.21.49",
    "http://2ce477f42335.ngrok-free.app/",
    "https://2ce477f42335.ngrok-free.app",
]
