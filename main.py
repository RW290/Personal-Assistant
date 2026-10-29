"""The assistant's web server. Milestone 0: a voice recording in, a task out as JSON.
It also serves the web app (see webapp.py).

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
from fastapi.exceptions import RequestValidationError  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402
from starlette.exceptions import HTTPException as StarletteHTTPException  # noqa: E402

from speech import TranscriptionError, transcribe  # noqa: E402
from task_parser import (  # noqa: E402
    DEFAULT_TIMEZONE,
    TaskParseError,
    describe_task,
    finish_task,
    get_timezone,
    parse_task,
)
from webapp import SESSION_COOKIE, mount_app, valid_session  # noqa: E402
from webapp import router as web_router  # noqa: E402

ASSISTANT_TOKEN = os.environ["ASSISTANT_TOKEN"]
MAX_AUDIO_BYTES = 25 * 1024 * 1024  # a minute of iPhone audio is about 1 MB

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("assistant")

# No auto-generated docs pages: they would describe the API to anyone who finds the URL.
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)


def error_body(code: int, message: str) -> dict:
    """Every error has the same shape, so the Shortcut can show it as is: a title with an
    X and the error code, and a one-line message. `detail` is what the web app reads."""
    return {"ok": False, "code": code, "title": f"\u2717 Error {code}", "message": message, "detail": message}


@app.exception_handler(StarletteHTTPException)
async def http_error(request: Request, error: StarletteHTTPException):
    return JSONResponse(error_body(error.status_code, str(error.detail)), status_code=error.status_code)


@app.exception_handler(RequestValidationError)
async def bad_request(request: Request, error: RequestValidationError):
    fields = ", ".join(str(problem["loc"][-1]) for problem in error.errors())
    return JSONResponse(error_body(422, f"Missing or invalid: {fields}"), status_code=422)


@app.exception_handler(Exception)
async def unexpected_error(request: Request, error: Exception):
    log.error("unexpected error: %s", type(error).__name__)  # the type only: messages can hold content
    return JSONResponse(error_body(500, "Something broke on the server."), status_code=500)


def is_public(request: Request) -> bool:
    """The only routes anyone may reach. None of them hold data."""
    method, path = request.method, request.url.path
    return (
        (method == "GET" and path == "/")  # Replit's health check
        or (method == "GET" and (path == "/app" or path.startswith("/app/")))  # the web app's own files
        or (method == "POST" and path == "/api/login")  # the sign-in form
    )


@app.middleware("http")
async def require_sign_in(request: Request, call_next):
    """Reject every request that isn't public and carries neither the token (the Shortcut)
    nor a signed-in session (the web app), before it reaches any route."""
    if is_public(request):
        return await call_next(request)

    token = request.headers.get("x-assistant-token", "")
    # compare_digest takes the same time no matter where the strings differ, so nobody
    # can guess the token one character at a time by timing how fast we say no.
    has_token = hmac.compare_digest(token.encode(), ASSISTANT_TOKEN.encode())
    if not (has_token or valid_session(request.cookies.get(SESSION_COOKIE, ""))):
        return JSONResponse(error_body(401, "Not signed in. Check the token in the Shortcut."), status_code=401)
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
        log.error("task parsing failed: %s", e)
        raise HTTPException(502, str(e))

    # Logs never hold what I said: they sit on Replit's servers, outside the one place
    # (the database) where I can see and delete my data. Sizes and kinds only.
    log.info("voice: %d bytes of audio, %d characters, kind=%s", len(audio), len(transcript), task["kind"])
    return {
        # Ready to show on the phone as is: the Shortcut puts these in a notification.
        "ok": True,
        "title": "\u2713 Received",
        "message": describe_task(task, local_tz),
        "app_url": None,  # Milestone 1: a link to the approval this request created
        "transcript": transcript,
        "task": task,
    }


app.include_router(web_router)
mount_app(app)
