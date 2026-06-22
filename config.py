"""
config.py
---------
Loads configuration (Gemini API key + model name) from environment
variables, optionally via a .env file (see .env.example).
"""

import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv is optional; if it's not installed we just rely on
    # whatever is already in the real environment variables.
    pass

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash").strip()


def require_api_key():
    """Raise a clear, actionable error if no API key is configured."""
    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is not set.\n"
            "  1. Copy .env.example to .env\n"
            "  2. Put your Gemini API key in it: GEMINI_API_KEY=your_key_here\n"
            "  3. Re-run the program.\n"
            "(Get a key at https://aistudio.google.com/app/apikey)"
        )
