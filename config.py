"""Settings, read once from the environment. Every other module gets its keys from here.

Locally the values come from .env. On Replit there is no .env file; the same names come
from Replit Secrets, and load_dotenv does nothing.
"""
import os

from dotenv import load_dotenv

load_dotenv()


def _required(name: str) -> str:
    value = os.environ.get(name, "")
    if not value:
        # Refuse to start rather than run half-configured (and, without a token, wide open).
        raise RuntimeError(f"{name} is not set (.env locally, Replit Secrets when deployed)")
    return value


ASSISTANT_TOKEN = _required("ASSISTANT_TOKEN")
ANTHROPIC_API_KEY = _required("ANTHROPIC_API_KEY")
ELEVENLABS_API_KEY = _required("ELEVENLABS_API_KEY")
