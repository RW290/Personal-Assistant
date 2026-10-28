"""Speech to text with ElevenLabs Scribe."""
import os

import httpx

SCRIBE_URL = "https://api.elevenlabs.io/v1/speech-to-text"
SCRIBE_MODEL = "scribe_v2"


class TranscriptionError(Exception):
    pass


def transcribe(audio: bytes, filename: str) -> str:
    """Send a voice recording to Scribe and return what was said, as plain text."""
    response = httpx.post(
        SCRIBE_URL,
        headers={"xi-api-key": os.environ["ELEVENLABS_API_KEY"]},
        data={
            "model_id": SCRIBE_MODEL,
            "language_code": "en",
            # Leave out sound tags like "(laughs)": we only want the words.
            "tag_audio_events": "false",
        },
        files={"file": (filename, audio)},
        timeout=60,
    )
    if response.status_code != 200:
        raise TranscriptionError(f"Scribe returned {response.status_code}: {response.text[:200]}")
    return response.json()["text"].strip()
