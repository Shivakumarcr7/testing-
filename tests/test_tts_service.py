"""Basic tests for the TTS service's /synthesize endpoint.

External calls to Sarvam are mocked (via monkeypatch) so this suite runs
without a real SARVAM_API_KEY or network access -- see tests/conftest.py
for the placeholder key that lets services.config import cleanly.
"""
import base64
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient

import services.tts.main as tts_main

client = TestClient(tts_main.app)


def test_rejects_invalid_language():
    """An unsupported language code should return 400, not crash."""
    response = client.post("/synthesize", json={"text": "hello", "language": "xx"})
    assert response.status_code == 400


def test_rejects_empty_text():
    """Empty text should be rejected with a clean 400."""
    response = client.post("/synthesize", json={"text": "   ", "language": "en"})
    assert response.status_code == 400


def test_accepts_valid_request(monkeypatch):
    """A valid text + language should return 200 with WAV audio, when Sarvam
    responds successfully. Sarvam itself is mocked -- no real API key/network
    needed."""

    fake_audio_bytes = b"FAKE-WAV-AUDIO-BYTES"
    fake_audio_b64 = base64.b64encode(fake_audio_bytes).decode()

    class FakeSarvamResponse:
        status_code = 200

        def json(self):
            return {"audios": [fake_audio_b64]}

    def fake_post(*args, **kwargs):
        return FakeSarvamResponse()

    monkeypatch.setattr(tts_main.requests, "post", fake_post)

    response = client.post(
        "/synthesize", json={"text": "Hello, welcome to the hospital", "language": "en"}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/wav"
    assert response.content == fake_audio_bytes


def test_upstream_error_returns_502(monkeypatch):
    """If Sarvam itself errors out, the service should return a clean 502,
    not crash or leak a stack trace."""

    class FakeSarvamErrorResponse:
        status_code = 500
        text = "internal error"

    def fake_post(*args, **kwargs):
        return FakeSarvamErrorResponse()

    monkeypatch.setattr(tts_main.requests, "post", fake_post)

    response = client.post(
        "/synthesize", json={"text": "Hello", "language": "en"}
    )
    assert response.status_code == 502
