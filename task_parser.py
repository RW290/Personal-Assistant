"""Turn a transcript into a task: Claude fills in a fixed JSON shape."""
import datetime as dt
from typing import Literal
from zoneinfo import ZoneInfo

import anthropic
from pydantic import BaseModel, Field

MODEL = "claude-opus-5-5"
TIMEZONE = ZoneInfo("America/New_York")  # Durham. Moves into facts memory in Milestone 1.

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment


class Task(BaseModel):
    """The shape Claude must answer in. The API enforces it, so the reply always parses."""

    kind: Literal["todo", "event", "question", "other"] = Field(
        description="todo: something to do or be reminded of. event: something at a set time "
        "that belongs on the calendar. question: asking for information. other: anything else."
    )
    title: str = Field(description="Short title in the speaker's words, with no date or time in it.")
    date: dt.date | None = Field(description="The day, only if one was said.")
    time: dt.time | None = Field(description="The time of day, only if one was said.")
    notes: str | None = Field(description="Any other detail that was said, or null.")


class TaskParseError(Exception):
    pass


def build_system_prompt(now: dt.datetime) -> str:
    # List the next week's dates so Claude looks up "Friday" instead of doing date arithmetic.
    upcoming = "\n".join(
        f"- {day:%A}: {day:%Y-%m-%d}" for day in (now + dt.timedelta(days=i) for i in range(1, 8))
    )
    return f"""You turn one spoken request into a task. The request was transcribed from speech, \
so it may contain small transcription mistakes: go by what the speaker meant.

Right now it is {now:%A %Y-%m-%d, %H:%M} ({TIMEZONE.key}). The next seven days:
{upcoming}

Resolve relative days like "tomorrow" or "Friday" with the list above. Fill in a date or time \
only if the speaker said one; never invent one."""


def parse_task(transcript: str) -> Task:
    try:
        response = client.beta.messages.parse(
            model=MODEL,
            max_tokens=4000,
            # Low effort: this is a short extraction, and the phone is waiting.
            output_config={"effort": "low"},
            # If Claude declines a request, the API retries it on a backup model it picks.
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            system=build_system_prompt(dt.datetime.now(TIMEZONE)),
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
