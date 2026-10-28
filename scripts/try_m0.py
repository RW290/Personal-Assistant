"""Milestone 0 check: speak five requests with the Mac's `say` voice and send each to the server.

Usage (with the server running):
    python scripts/try_m0.py                              # local server
    python scripts/try_m0.py https://<your-app>.replit.app
"""
import datetime as dt
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx
from dotenv import load_dotenv

# (what to say, expected kind, expected day: a weekday name, "tomorrow", or None)
REQUESTS = [
    ("Add buy groceries to my to do list for Friday", "todo", "Friday"),
    ("Remind me to call mom tomorrow at five pm", "todo", "tomorrow"),
    ("Put dinner with Alex on my calendar Saturday at seven", "event", "Saturday"),
    ("I need to finish the stats problem set by Thursday night", "todo", "Thursday"),
    ("What's on my calendar on Friday?", "question", "Friday"),
]


def expected_date(day: str | None) -> str | None:
    if day is None:
        return None
    today = dt.datetime.now(ZoneInfo("America/New_York")).date()
    if day == "tomorrow":
        return (today + dt.timedelta(days=1)).isoformat()
    weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    days_ahead = (weekdays.index(day) - today.weekday()) % 7 or 7  # the next one, not today
    return (today + dt.timedelta(days=days_ahead)).isoformat()


def speak_to_file(text: str, folder: Path) -> Path:
    """Make an .m4a recording of `text`, the same format the iPhone records."""
    aiff, m4a = folder / "clip.aiff", folder / "clip.m4a"
    subprocess.run(["say", "-o", aiff, text], check=True)
    subprocess.run(["afconvert", "-f", "m4af", "-d", "aac", aiff, m4a], check=True)
    return m4a


def main() -> None:
    load_dotenv()
    url = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000").rstrip("/") + "/voice"
    headers = {"X-Assistant-Token": os.environ["ASSISTANT_TOKEN"]}

    passed = 0
    with tempfile.TemporaryDirectory() as folder:
        for text, kind, day in REQUESTS:
            clip = speak_to_file(text, Path(folder))
            started = dt.datetime.now()
            response = httpx.post(url, headers=headers, files={"file": clip.open("rb")}, timeout=90)
            seconds = (dt.datetime.now() - started).total_seconds()
            if response.status_code != 200:
                print(f"FAIL  {text!r}: HTTP {response.status_code} {response.text}")
                continue
            task = response.json()["task"]
            ok = task["kind"] == kind and task["date"] == expected_date(day)
            passed += ok
            print(f"{'ok  ' if ok else 'FAIL'}  {seconds:4.1f}s  {response.json()['transcript']!r}")
            print(f"      {task}")
    print(f"\n{passed}/{len(REQUESTS)} came out right")


if __name__ == "__main__":
    main()
