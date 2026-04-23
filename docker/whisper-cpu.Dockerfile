FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PYTHONUNBUFFERED=1 \
    WHISPER_MODEL=tiny

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-whisper.txt /app/requirements-whisper.txt
RUN pip install -r /app/requirements-whisper.txt

COPY . /app

CMD ["python3", "scripts/run_whisper_inference.py", "--help"]
