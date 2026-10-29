"""The assistant's web server. Milestone 0: a voice recording in, a task out as JSON.

Run locally:  uvicorn main:app --reload
"""
import hmac
import logging
import os

from dotenv import load_dotenv

# Load .env before anything reads the environment. On Replit there is no .env file;
# the same names come from Replit Secrets, and this line does nothing.
load_dotenv()

for name in ("ASSISTANT_TOKEN", "ANTHROPIC_API_KEY", "ELEVENLABS_API_KEY"):
    if not os.environ.get(name):
        # Refuse to start rather than run half-configured (and, without a token, wide open).
        raise RuntimeError(f"{name} is not set (.env locally, Replit Secrets when deployed)")

from fastapi import FastAPI, Form, HTTPException, Request, UploadFile  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402

from speech import TranscriptionError, transcribe  # noqa: E402
from task_parser import (  # noqa: E402
    DEFAULT_TIMEZONE,
    TaskParseError,
    finish_task,
    get_timezone,
    parse_task,
)

ASSISTANT_TOKEN = os.environ["ASSISTANT_TOKEN"]
MAX_AUDIO_BYTES = 25 * 1024 * 1024  # a minute of iPhone audio is about 1 MB

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("assistant")

# No auto-generated docs pages: they would describe the API to anyone who finds the URL.
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)


@app.middleware("http")
async def require_token(request: Request, call_next):
    """Allow only the generic liveness check through without the shared secret."""
    if request.method == "GET" and request.url.path == "/":
        return await call_next(request)

    token = request.headers.get("x-assistant-token", "")
    # compare_digest takes the same time no matter where the strings differ, so nobody
    # can guess the token one character at a time by timing how fast we say no.
    if not hmac.compare_digest(token.encode(), ASSISTANT_TOKEN.encode()):
        return JSONResponse({"detail": "unauthorized"}, status_code=401)
    return await call_next(request)


@app.get("/")
def health():
    """Minimal public response for Replit's Autoscale health check."""
    return {"status": "ok"}


@app.post("/voice")
def voice(file: UploadFile, timezone: str = Form(DEFAULT_TIMEZONE)):
    """Transcribe a recording from the iPhone Shortcut and turn it into a task.

    `timezone` is where the phone is right now (an IANA name like America/New_York),
    so "tomorrow at 5" means 5 where I am, even when I travel.
    """
    local_tz = get_timezone(timezone)
    if local_tz is None:
        raise HTTPException(400, f"Unknown time zone {timezone!r}.")

    audio = file.file.read(MAX_AUDIO_BYTES + 1)
    if len(audio) > MAX_AUDIO_BYTES:
        raise HTTPException(413, "That recording is too long.")

    try:
        transcript = transcribe(audio, file.filename or "recording.m4a")
    except TranscriptionError as e:
        log.error("transcription failed: %s", e)
        raise HTTPException(502, "Couldn't transcribe the recording.")
    if not transcript:
        raise HTTPException(400, "I didn't hear anything.")

    try:
        task = finish_task(parse_task(transcript, local_tz), local_tz)
    except TaskParseError as e:
        log.error("task parsing failed for %r: %s", transcript, e)
        raise HTTPException(502, str(e))

    log.info("transcript=%r task=%s", transcript, task)
    return {"transcript": transcript, "task": task}
