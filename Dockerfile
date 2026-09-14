FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services ./services

# Default command runs the Gateway. STT/TTS override this (see docker-compose.yml
# locally, or the Render "Start Command" per service in the deployment guide).
# Shell form so $PORT expands -- Render injects PORT at runtime; 8000 is the
# local-dev fallback when PORT isn't set.
CMD python -m uvicorn services.gateway.main:app --host 0.0.0.0 --port ${PORT:-8000}