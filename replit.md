# Running on Replit

This is the existing Python 3.12 / FastAPI backend for an iPhone Shortcut, not a browser UI. Keep its structure and stack; see CLAUDE.md for the working spec and trust rules.

## Required configuration

- `ANTHROPIC_API_KEY`: Anthropic API access for task extraction.
- `ELEVENLABS_API_KEY`: ElevenLabs speech-to-text access.
- `ASSISTANT_TOKEN`: a strong shared secret, also entered in the Shortcut's `X-Assistant-Token` header.

Use Replit Secrets or a supported integration to supply credentials. Never put their values in code, logs, or documentation. The server intentionally refuses to start if any required value is missing.

## Run

The `Assistant API` workflow runs:

```sh
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

Dependencies are listed in `requirements.txt`. The existing `scripts/post-merge.sh` restores them after task merges.

Requests without a valid token receive HTTP 401, including `/` and disabled documentation routes. There is deliberately no public homepage or unauthenticated health route. A browser preview is not a functional test of this API.

Send a multipart `POST /voice` with an audio `file`, an optional IANA `timezone` (defaults to `America/New_York`), and the `X-Assistant-Token` header. A successful response contains `transcript` and `task`. End-to-end verification requires working credentials for both external services and an audio sample.

`scripts/try_m0.py` uses macOS speech tools and is not a Linux/Replit test runner. Publishing is a separate step; this workflow runs the development server only.
