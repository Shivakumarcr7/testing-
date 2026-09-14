"""
Manual voice-echo demo for Week 1.
Chains Sarvam STT (Saarika v2.5) and Sarvam TTS (Bulbul v2):
takes an input audio clip, transcribes it, then speaks the
transcript back out as a new audio file.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import base64
import requests
from services.config import SARVAM_API_KEY, SARVAM_BASE_URL

assert SARVAM_API_KEY is not None


def transcribe(file_path: str) -> dict:
    """Send an audio file to Sarvam Saarika v2.5 and return {transcript, language_code}."""
    filename = Path(file_path).name
    with open(file_path, "rb") as f:
        response = requests.post(
            f"{SARVAM_BASE_URL}/speech-to-text",
            headers={"api-subscription-key": SARVAM_API_KEY},
            files={"file": (filename, f, "audio/wav")},
            data={"model": "saarika:v2.5"},
        )
    if response.status_code != 200:
        print("SARVAM ERROR RESPONSE:", response.text)
    response.raise_for_status()
    return response.json()


def synthesize(text: str, lang_code: str, out_path: str) -> str:
    """Send text to Sarvam Bulbul v2 and save the returned audio as a WAV file."""
    response = requests.post(
        f"{SARVAM_BASE_URL}/text-to-speech",
        headers={
            "api-subscription-key": SARVAM_API_KEY,
            "Content-Type": "application/json",
        },
        json={
            "text": text,
            "target_language_code": lang_code,
            "speaker": "anushka",
            "model": "bulbul:v2",
        },
    )
    response.raise_for_status()
    audio_b64 = response.json()["audios"][0]
    with open(out_path, "wb") as f:
        f.write(base64.b64decode(audio_b64))
    return out_path

def voice_echo(input_audio_path: str, echo_output_path: str) -> None:
    """Full round trip: speak in, transcribe, synthesize the transcript back."""
    stt_result = transcribe(input_audio_path)
    transcript = stt_result["transcript"]
    lang_code = stt_result["language_code"]
    print(f"Heard ({lang_code}): {transcript}")

    synthesize(transcript, lang_code, echo_output_path)
    print(f"Echoed audio saved to: {echo_output_path}")


if __name__ == "__main__":
    voice_echo("scripts/output_en-IN.wav", "scripts/echo_en-IN.wav")