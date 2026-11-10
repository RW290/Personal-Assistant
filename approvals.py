"""Approval queue items: the shape the web app shows, and a stand-in queue.

`Approval` is the agreed shape between the approval queue (which I write in Milestone 1)
and the web app. Until my queue exists, `DemoApprovals` serves a few made-up items so the
app can be built and tried on the phone.
"""
import datetime as dt
from typing import Literal

from pydantic import BaseModel

Status = Literal["pending", "approved", "rejected", "done", "failed"]


class Approval(BaseModel):
    id: str
    summary: str  # what will change, written by code from the exact arguments, not by the model
    reason: str  # why, in the model's words (every tool's input has a required `reason` field)
    tool: str  # the write tool it wants to run
    arguments: dict  # exactly what that tool will run with
    tools_used: list[str]  # the read tools it used to get here
    request: str  # what I asked
    status: Status
    created_at: dt.datetime
    decided_at: dt.datetime | None = None


class NotFound(Exception):
    pass


class AlreadyDecided(Exception):
    pass


def _next(weekday: int, today: dt.date) -> dt.date:
    """The next given weekday (Monday is 0), not counting today."""
    return today + dt.timedelta(days=(weekday - today.weekday()) % 7 or 7)


class DemoApprovals:
    """Stand-in for my approval queue: made-up items kept in memory, reset on every restart.
    Approving one only changes its status; nothing runs."""

    def __init__(self) -> None:
        now = dt.datetime.now(dt.timezone.utc)
        friday, saturday = _next(4, now.date()), _next(5, now.date())
        items = [
            Approval(
                id="demo-1",
                summary=f"Add “Buy groceries” to your to-do list, due {friday:%a, %b} {friday.day}",
                reason="You asked to add groceries to your list for Friday.",
                tool="google_tasks.add_task",
                arguments={"list": "My Tasks", "title": "Buy groceries", "due": friday.isoformat()},
                tools_used=["google_tasks.list_tasklists"],
                request="Add buy groceries to my to-do list for Friday",
                status="pending",
                created_at=now - dt.timedelta(minutes=3),
            ),
            Approval(
                id="demo-2",
                summary=f"Add “Dinner with Alex” to your calendar, {saturday:%a, %b} {saturday.day}, 7:00 to 9:00 PM",
                reason="You asked for dinner with Alex on Saturday at seven, and your calendar is free then.",
                tool="calendar.create_event",
                arguments={
                    "title": "Dinner with Alex",
                    "start": f"{saturday.isoformat()}T19:00:00-04:00",
                    "end": f"{saturday.isoformat()}T21:00:00-04:00",
                },
                tools_used=["calendar.list_events"],
                request="Put dinner with Alex on my calendar Saturday at seven",
                status="pending",
                created_at=now - dt.timedelta(minutes=40),
            ),
            Approval(
                id="demo-3",
                summary="Save a reply to Jordan about Thursday's club meeting as a Gmail draft (not sent)",
                reason="You asked me to tell Jordan you can make Thursday's meeting but will be 10 minutes late.",
                tool="gmail.create_draft",
                arguments={
                    "to": "jordan@example.com",
                    "subject": "Re: Club meeting Thursday",
                    "body": "Hey Jordan, I can make it Thursday but I'll be about 10 minutes late. See you there!",
                },
                tools_used=["gmail.search"],
                request="Tell Jordan I can make Thursday's meeting but I'll be ten minutes late",
                status="pending",
                created_at=now - dt.timedelta(hours=2),
            ),
            Approval(
                id="demo-4",
                summary="Add “Call mom” to your to-do list, due tomorrow",
                reason="You asked to be reminded to call your mom tomorrow.",
                tool="google_tasks.add_task",
                arguments={"list": "My Tasks", "title": "Call mom", "due": (now.date() + dt.timedelta(days=1)).isoformat()},
                tools_used=[],
                request="Remind me to call mom tomorrow",
                status="done",
                created_at=now - dt.timedelta(days=1),
                decided_at=now - dt.timedelta(days=1, minutes=-2),
            ),
        ]
        self._items = {item.id: item for item in items}

    def list(self, status: Status | None = None) -> list[Approval]:
        items = [item for item in self._items.values() if status is None or item.status == status]
        return sorted(items, key=lambda item: item.created_at, reverse=True)

    def decide(self, approval_id: str, approve: bool) -> Approval:
        item = self._items.get(approval_id)
        if item is None:
            raise NotFound(approval_id)
        if item.status != "pending":
            raise AlreadyDecided(approval_id)
        item.status = "approved" if approve else "rejected"
        item.decided_at = dt.datetime.now(dt.timezone.utc)
        return item
