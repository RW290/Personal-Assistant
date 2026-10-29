"""Turn a transcript into a task: Claude fills in a fixed JSON shape, then code works out the exact time."""
import datetime as dt
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import anthropic
from pydantic import BaseModel, Field

MODEL = "claude-haiku-5-5"
# Used when the phone doesn't say where I am. Moves into facts memory in Milestone 1.
DEFAULT_TIMEZONE = "America/New_York"

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment


class Task(BaseModel):
    """The shape Claude must answer in. The API enforces it, so the reply always parses."""

    kind: Literal["todo", "event", "question", "other"] = Field(
        description="todo: something to do or be reminded of. event: something at a set time "
        "that belongs on the calendar. question: asking for information. other: anything else."
    )
    title: str = Field(description="Short title in the speaker's words, with no date or time in it.")
    date: dt.date | None = Field(description="The day, only if one was said.")
    time: dt.time | None = Field(description="The clock time as said, only if one was said.")
    timezone: str | None = Field(
        description="IANA time zone name (like America/Los_Angeles) the time is meant in, only if "
        "the speaker said one: a zone ('3pm Pacific', '5 East Coast time'), a place for the time "
        "('noon London time'), or where they will be then ('I'll be back in Durham by then'). "
        "Otherwise null."
    )
    notes: str | None = Field(description="Any other detail that was said, or null.")


class TaskParseError(Exception):
    pass


def get_timezone(name: str | None) -> ZoneInfo | None:
    """Look up a time zone by IANA name. Returns None for a missing or unknown name."""
    if not name:
        return None
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError):  # ValueError: malformed names like "../x"
        return None


def build_system_prompt(now: dt.datetime) -> str:
    # List the next week's dates so Claude looks up "Friday" instead of doing date arithmetic.
    upcoming = "\n".join(
        f"- {day:%A}: {day:%Y-%m-%d}" for day in (now + dt.timedelta(days=i) for i in range(1, 8))
    )
    return f"""You turn one spoken request into a task. The request was transcribed from speech, \
so it may contain small transcription mistakes: go by what the speaker meant.

The speaker is in the {now.tzinfo} time zone, where it is now {now:%A %Y-%m-%d, %H:%M}. \
The next seven days:
{upcoming}

Resolve relative days like "tomorrow" or "Friday" with the list above. Give the time as the \
clock time the speaker said; don't convert it between time zones. If they say where they will be \
at that time, the time zone is that place's, not where they are now. Fill in a date, time or time \
zone only if the speaker said one; never invent one."""


def parse_task(transcript: str, local_tz: ZoneInfo) -> Task:
    try:
        response = client.messages.parse(
            model=MODEL,
            max_tokens=4000,
            # Low effort: this is a short extraction, and the phone is waiting.
            output_config={"effort": "low"},
            system=build_system_prompt(dt.datetime.now(local_tz)),
            messages=[{"role": "user", "content": transcript}],
            output_format=Task,
        )
    except anthropic.APIConnectionError as e:
        raise TaskParseError("Couldn't reach Claude.") from e
    except anthropic.APIStatusError as e:
        raise TaskParseError(f"Claude returned an error ({e.status_code}): {e.message}") from e

    if response.stop_reason == "refusal":
        raise TaskParseError("Claude declined this request.")
    if response.stop_reason == "max_tokens":
        raise TaskParseError("Claude ran out of room before finishing.")
    return response.parsed_output


KIND_WORDS = {"todo": "To-do", "event": "Event", "question": "Question", "other": "Noted"}


def describe_task(task: dict, local_tz: ZoneInfo) -> str:
    """A short message for the phone's notification. Code writes it from the task itself,
    so it always matches what was actually understood."""
    lines = [f"{KIND_WORDS[task['kind']]}: {task['title']}"]
    if task["datetime"]:
        # The saved datetime only has an offset (-08:00); its zone gives the name ("PST").
        moment = dt.datetime.fromisoformat(task["datetime"]).astimezone(ZoneInfo(task["timezone"]))
        when = f"{moment:%a, %b} {moment.day} at {moment.hour % 12 or 12}:{moment:%M %p}"
        if task["timezone"] != local_tz.key:
            when += f" {moment.tzname()}"  # e.g. "PST", only when it isn't where the phone is
        lines.append(when)
    elif task["date"]:
        day = dt.date.fromisoformat(task["date"])
        lines.append(f"{day:%a, %b} {day.day}")
    if task["notes"]:
        lines.append(task["notes"])
    return "\n".join(lines)


def finish_task(task: Task, local_tz: ZoneInfo) -> dict:
    """Pin the task to an exact moment. Code does this, not the model, so the time zone
    offset is always right, including across daylight saving changes."""
    # A zone the speaker named wins; otherwise the zone the phone is in.
    tz = get_timezone(task.timezone) or local_tz
    moment = None
    if task.date and task.time:
        # The zone comes from tz, so drop any offset Claude may have attached to the time.
        moment = dt.datetime.combine(task.date, task.time.replace(tzinfo=None), tzinfo=tz)
    return {
        **task.model_dump(mode="json"),
        "timezone": tz.key,
        "datetime": moment.isoformat() if moment else None,
    }
