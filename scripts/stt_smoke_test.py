import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import requests
from services.config import SARVAM_API_KEY, SARVAM_BASE_URL

assert SARVAM_API_KEY is not None

TEST_FILES = {
    "kn-IN": "scripts/output_kn-IN.wav",
    "hi-IN": "scripts/output_hi-IN.wav",
    "en-IN": "scripts/output_en-IN.wav",
}

def transcribe(file_path: str):
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

if __name__ == "__main__":
    for expected_lang, path in TEST_FILES.items():
        result = transcribe(path)
        print(f"Expected: {expected_lang} | Got language_code: {result.get('language_code')}")
        print(f"Transcript: {result.get('transcript')}\n")