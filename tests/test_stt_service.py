"""Basic tests for the STT service's /transcribe endpoint.

External calls to Sarvam are mocked (via monkeypatch) so this suite runs
without a real SARVAM_API_KEY or network access -- see tests/conftest.py
for the placeholder key that lets services.config import cleanly.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient

import services.stt.main as stt_main

client = TestClient(stt_main.app)


def test_rejects_wrong_file_type():
    """Uploading a non-audio file should return 400, not crash."""
    response = client.post(
        "/transcribe",
        files={"file": ("test.txt", b"not audio", "text/plain")},
    )
    assert response.status_code == 400


def test_rejects_empty_file():
    """An empty audio file should be rejected with a clean 400."""
    response = client.post(
        "/transcribe",
        files={"file": ("empty.wav", b"", "audio/wav")},
    )
    assert response.status_code == 400


def test_accepts_valid_audio(monkeypatch):
    """A WAV file should return 200 with a transcript when Sarvam responds
    successfully. Sarvam itself is mocked -- no real API key/network needed."""

    class FakeSarvamResponse:
        status_code = 200
        ok = True
        text = ""

        def json(self):
            return {"transcript": "hello doctor", "language_code": "en-IN"}

    def fake_post(*args, **kwargs):
        return FakeSarvamResponse()

    monkeypatch.setattr(stt_main.requests, "post", fake_post)

    with open("scripts/output_en-IN.wav", "rb") as f:
        response = client.post(
            "/transcribe",
            files={"file": ("output_en-IN.wav", f, "audio/wav")},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["text"] == "hello doctor"
    assert body["language_code"] == "en-IN"


def test_upstream_error_returns_502(monkeypatch):
    """If Sarvam itself errors out, the service should return a clean 502,
    not crash or leak a stack trace."""

    class FakeSarvamErrorResponse:
        status_code = 500
        ok = False
        text = "internal error"

    def fake_post(*args, **kwargs):
        return FakeSarvamErrorResponse()

    monkeypatch.setattr(stt_main.requests, "post", fake_post)

    with open("scripts/output_en-IN.wav", "rb") as f:
        response = client.post(
            "/transcribe",
            files={"file": ("output_en-IN.wav", f, "audio/wav")},
        )

    assert response.status_code == 502
