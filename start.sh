#!/bin/sh

echo "Starting Zenvy STT on port 8001..."
python -m uvicorn services.stt.main:app --host 0.0.0.0 --port 8001 &

echo "Starting Zenvy TTS on port 8005..."
python -m uvicorn services.tts.main:app --host 0.0.0.0 --port 8005 &

echo "Starting Zenvy Gateway..."
exec python -m uvicorn services.gateway.main:app --host 0.0.0.0 --port ${PORT:-8000}
