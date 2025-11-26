# Minimal production build - No Playwright, No Crawl4AI
# OCR + PDF + FFmpeg only - 100% stable

FROM python:3.11-slim-bullseye

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PORT=8000 \
    WORKERS=1 \
    MAX_UPLOAD_SIZE=100 \
    CLEANUP_HOURS=24

# Install system dependencies (no Playwright deps)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-fra \
    tesseract-ocr-deu \
    tesseract-ocr-spa \
    libtesseract-dev \
    libleptonica-dev \
    poppler-utils \
    libpoppler-cpp-dev \
    ffmpeg \
    wget \
    curl \
    ca-certificates \
    gcc \
    g++ \
    make \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
RUN mkdir -p storage/uploads storage/outputs storage/temp && \
    chmod -R 777 storage

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY startup.sh .
RUN chmod +x startup.sh

RUN touch app/routers/__init__.py && \
    touch app/services/__init__.py

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

EXPOSE ${PORT}

CMD ["./startup.sh"]
