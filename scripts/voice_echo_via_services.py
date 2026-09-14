"""
Voice-echo demo via running services (Week 2).
Unlike Week 1's voice_echo.py (which called Sarvam directly), this
version calls our own STT service (port 8001) and TTS service
(port 8005) over HTTP — proving the two services work together
correctly, the way the future Channel Gateway will call them.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import requests

STT_URL = "http://127.0.0.1:8001/transcribe"
TTS_URL = "http://127.0.0.1:8005/synthesize"

LANGUAGE_CODE_TO_SHORT = {
    "kn-IN": "kn",
    "hi-IN": "hi",
    "en-IN": "en",
}


def transcribe_via_service(file_path: str) -> dict:
    """Call the running STT service and return {text, language_code}."""
    filename = Path(file_path).name
    with open(file_path, "rb") as f:
        response = requests.post(
            STT_URL,
            files={"file": (filename, f, "audio/wav")},
        )
    response.raise_for_status()
    return response.json()


def synthesize_via_service(text: str, short_lang: str, out_path: str) -> str:
    """Call the running TTS service and save the returned WAV audio."""
    response = requests.post(
        TTS_URL,
        json={"text": text, "language": short_lang},
    )
    response.raise_for_status()
    with open(out_path, "wb") as f:
        f.write(response.content)
    return out_path


def voice_echo_via_services(input_audio_path: str, echo_output_path: str) -> None:
    """Full round trip through the two live services: audio -> STT -> text -> TTS -> audio."""
    stt_result = transcribe_via_service(input_audio_path)
    transcript = stt_result["text"]
    lang_code = stt_result["language_code"]
    print(f"Heard ({lang_code}): {transcript}")

    short_lang = LANGUAGE_CODE_TO_SHORT[lang_code]
    synthesize_via_service(transcript, short_lang, echo_output_path)
    print(f"Echoed audio saved to: {echo_output_path}")


if __name__ == "__main__":
    voice_echo_via_services("scripts/output_kn-IN.wav", "scripts/service_echo_kn-IN.wav")