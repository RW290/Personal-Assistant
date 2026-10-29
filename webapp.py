"""The web app's server side: sign-in, the approval routes, and serving the built React app.

The React app lives in web/ and is built into web/dist, which is served at /app.
It talks to the /api routes below. main.py's middleware decides who gets in.
"""
import hashlib
import hmac
import os
import time
from pathlib import Path

from fastapi import APIRouter, FastAPI, HTTPException, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from approvals import AlreadyDecided, Approval, DemoApprovals, NotFound, Status

SESSION_COOKIE = "assistant_session"
SESSION_SECONDS = 14 * 24 * 3600  # two weeks; Face ID passkeys in Milestone 4 make this shorter
APP_DIR = Path(__file__).parent / "web" / "dist"

router = APIRouter(prefix="/api")
approvals = DemoApprovals()  # replaced by my approval queue in Milestone 1


def _sign(text: str) -> str:
    # The signing key comes from the token, so changing ASSISTANT_TOKEN signs every session out.
    key = hmac.new(os.environ["ASSISTANT_TOKEN"].encode(), b"web-session", hashlib.sha256).digest()
    return hmac.new(key, text.encode(), hashlib.sha256).hexdigest()


def new_session() -> str:
    """A session is just its expiry time plus a signature that only this server can make,
    so there's nothing to store and it works on every Replit instance."""
    expires = str(int(time.time()) + SESSION_SECONDS)
    return f"{expires}.{_sign(expires)}"


def valid_session(value: str) -> bool:
    expires, _, signature = value.partition(".")
    if not expires.isdigit():
        return False
    return hmac.compare_digest(signature, _sign(expires)) and int(expires) > time.time()


class SignIn(BaseModel):
    token: str


@router.post("/login")
def login(body: SignIn, response: Response):
    """Trade the token for a session cookie. The browser never stores the token itself."""
    if not hmac.compare_digest(body.token.strip().encode(), os.environ["ASSISTANT_TOKEN"].encode()):
        raise HTTPException(401, "That token isn't right.")
    # httponly: page scripts can't read it. secure: only sent over HTTPS.
    # samesite=strict: the browser won't send it with requests that other websites start.
    response.set_cookie(
        SESSION_COOKIE, new_session(), max_age=SESSION_SECONDS, httponly=True, secure=True, samesite="strict"
    )
    return {"signed_in": True}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(SESSION_COOKIE, httponly=True, secure=True, samesite="strict")
    return {"signed_in": False}


@router.get("/me")
def me():
    # Reaching this route at all means the middleware let us in.
    return {"signed_in": True}


@router.get("/approvals")
def list_approvals(status: Status | None = None) -> list[Approval]:
    return approvals.list(status)


@router.post("/approvals/{approval_id}/approve")
def approve(approval_id: str) -> Approval:
    return _decide(approval_id, approve=True)


@router.post("/approvals/{approval_id}/reject")
def reject(approval_id: str) -> Approval:
    return _decide(approval_id, approve=False)


def _decide(approval_id: str, approve: bool) -> Approval:
    try:
        return approvals.decide(approval_id, approve)
    except NotFound:
        raise HTTPException(404, "No such approval.")
    except AlreadyDecided:
        raise HTTPException(409, "That one was already decided.")


def mount_app(app: FastAPI) -> None:
    """Serve the built React app at /app, if it has been built."""
    if APP_DIR.is_dir():
        app.mount("/app", StaticFiles(directory=APP_DIR, html=True), name="app")
