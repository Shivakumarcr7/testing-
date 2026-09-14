import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import base64
import requests
from services.config import SARVAM_API_KEY, SARVAM_BASE_URL

assert SARVAM_API_KEY is not None

TEST_SENTENCES = {
    "kn-IN": "ನಮಸ್ಕಾರ, ಆಸ್ಪತ್ರೆಗೆ ಸ್ವಾಗತ",       # "Hello, welcome to the hospital"
    "hi-IN": "नमस्ते, अस्पताल में आपका स्वागत है",  # same meaning
    "en-IN": "Hello, welcome to the hospital, How can I help you?",
}

def synthesize(text: str, lang_code: str, out_path: str):
    response = requests.post(
        f"{SARVAM_BASE_URL}/text-to-speech",
        headers={
            "api-subscription-key": SARVAM_API_KEY,
            "Content-Type": "application/json",
        },
        json={
            "text": text,
            "target_language_code": lang_code,
            "speaker": "anushka",     # bulbul:v2 default voice
            "model": "bulbul:v2",
        },
    )
    response.raise_for_status()
    audio_b64 = response.json()["audios"][0]
    with open(out_path, "wb") as f:
        f.write(base64.b64decode(audio_b64))
    print(f"Saved {out_path}")

if __name__ == "__main__":
    for lang, text in TEST_SENTENCES.items():
        synthesize(text, lang, f"scripts/output_{lang}.wav")