# Running on Replit

This is the existing Python 3.12 / FastAPI backend for an iPhone Shortcut, not a browser UI. Keep its structure and stack; see CLAUDE.md for the working spec and trust rules.

## Rules for Replit Agent (from the owner; these override anything else)

Code changes are written elsewhere and reach this project through reviewed pull requests on GitHub. Replit is used to run and publish the app.

- **Ask before changing any file.** Describe the change and wait for a yes in this conversation. This includes code, `requirements.txt`, `.replit`, CLAUDE.md, README and this file.
- **Never commit or push to `main` on your own.** The owner merges every change through a pull request.
- **Never change the trust rules** in CLAUDE.md or the code that enforces them (the token check, logging, approvals). Point out a problem instead.
- **Stay out of the live database.** Don't query, export, change or delete its data, and never run destructive SQL anywhere. It holds the owner's private notes.
- **Never write data files** (exports, dumps, recordings, logs) into the workspace. The GitHub repo is public.
- **Never print or write secret values**, including in logs or messages.

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

`GET /` is intentionally public and returns only `{"status":"ok"}` for Replit Autoscale's health check. It does not read data or call tools. All other routes and methods require a valid assistant token and receive HTTP 401 without it; framework documentation routes are disabled. A browser preview is not a functional test of this API.

Send a multipart `POST /voice` with an audio `file`, an optional IANA `timezone` (defaults to `America/New_York`), and the `X-Assistant-Token` header. A successful response contains `transcript` and `task`. End-to-end verification requires working credentials for both external services and an audio sample.

`scripts/try_m0.py` uses macOS speech tools and is not a Linux/Replit test runner. Publishing is a separate step; this workflow runs the development server only.
