import os
from dotenv import load_dotenv

load_dotenv()

SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")
SARVAM_BASE_URL = "https://api.sarvam.ai"

if not SARVAM_API_KEY:
    raise RuntimeError(
        "SARVAM_API_KEY is not set. Copy .env.example to .env and add your key."
    )