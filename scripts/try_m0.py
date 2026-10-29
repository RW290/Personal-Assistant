"""Milestone 0 check: speak test requests with the Mac's `say` voice and send each to the server.

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

HOME_TIMEZONE = "America/New_York"

# say: what to speak. kind: expected kind. day: a weekday name or "tomorrow".
# time: the clock time, if one is said. zone: the time zone the time is meant in, if one is said.
# phone: where the phone is (the Shortcut's `timezone`), to test being away from home.
REQUESTS = [
    {"say": "Add buy groceries to my to do list for Friday", "kind": "todo", "day": "Friday"},
    {"say": "Remind me to call mom tomorrow at five pm", "kind": "todo", "day": "tomorrow",
     "time": "17:00"},
    {"say": "Put dinner with Alex on my calendar Saturday at seven", "kind": "event",
     "day": "Saturday", "time": "19:00"},
    {"say": "I need to finish the stats problem set by Thursday night", "kind": "todo",
     "day": "Thursday"},
    {"say": "What's on my calendar on Friday?", "kind": "question", "day": "Friday"},
    {"say": "Remind me to submit the housing form Monday at nine am", "kind": "todo",
     "day": "Monday", "time": "09:00"},
    {"say": "Remind me to call grandma Sunday at three pm Pacific time", "kind": "todo",
     "day": "Sunday", "time": "15:00", "zone": "America/Los_Angeles"},
    # Away from home: the phone is in California.
    {"say": "Remind me to check out of the hotel tomorrow at eleven am", "kind": "todo",
     "day": "tomorrow", "time": "11:00", "phone": "America/Los_Angeles"},
    {"say": "Set a reminder for tomorrow at five pm East Coast time to join the club call",
     "kind": "todo", "day": "tomorrow", "time": "17:00", "zone": "America/New_York",
     "phone": "America/Los_Angeles"},
    {"say": "Remind me to call the bank Monday at nine am, I'll be back in Durham by then",
     "kind": "todo", "day": "Monday", "time": "09:00", "zone": "America/New_York",
     "phone": "America/Los_Angeles"},
    {"say": "Remind me Thursday at eight am Chicago time to email my TA", "kind": "todo",
     "day": "Thursday", "time": "08:00", "zone": "America/Chicago"},
]


def expected_date(day: str, phone: str) -> dt.date:
    today = dt.datetime.now(ZoneInfo(phone)).date()  # "tomorrow" is from where the phone is
    if day == "tomorrow":
        return today + dt.timedelta(days=1)
    weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    days_ahead = (weekdays.index(day) - today.weekday()) % 7 or 7  # the next one, not today
    return today + dt.timedelta(days=days_ahead)


def expected_datetime(day: dt.date, clock: str, zone: str) -> str:
    return dt.datetime.combine(day, dt.time.fromisoformat(clock), ZoneInfo(zone)).isoformat()


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
        for case in REQUESTS:
            phone = case.get("phone", HOME_TIMEZONE)
            clip = speak_to_file(case["say"], Path(folder))
            started = dt.datetime.now()
            response = httpx.post(
                url,
                headers=headers,
                data={"timezone": phone},
                files={"file": clip.open("rb")},
                timeout=90,
            )
            seconds = (dt.datetime.now() - started).total_seconds()
            if response.status_code != 200:
                print(f"FAIL  {case['say']!r}: HTTP {response.status_code} {response.text}")
                continue
            task = response.json()["task"]
            date = expected_date(case["day"], phone)
            ok = task["kind"] == case["kind"] and task["date"] == date.isoformat()
            if "time" in case:  # a time was said, so the exact moment must match too
                zone = case.get("zone", phone)
                ok = ok and task["datetime"] == expected_datetime(date, case["time"], zone)
            passed += ok
            where = f"  [phone in {phone}]" if phone != HOME_TIMEZONE else ""
            print(f"{'ok  ' if ok else 'FAIL'}  {seconds:4.1f}s  {response.json()['transcript']!r}{where}")
            print(f"      {task['kind']}, {task['title']!r}, {task['datetime'] or task['date']}, "
                  f"{task['timezone']}")
    print(f"\n{passed}/{len(REQUESTS)} came out right")


if __name__ == "__main__":
    main()
