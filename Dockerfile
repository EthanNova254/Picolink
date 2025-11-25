FROM python:3.11-slim-bullseye

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    PORT=8000 \
    WORKERS=2

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr tesseract-ocr-eng tesseract-ocr-fra tesseract-ocr-deu \
    tesseract-ocr-spa tesseract-ocr-ara tesseract-ocr-chi-sim \
    libtesseract-dev libleptonica-dev poppler-utils libpoppler-cpp-dev \
    ffmpeg wget curl ca-certificates gcc g++ make \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app
RUN mkdir -p storage/uploads storage/outputs storage/temp && chmod -R 777 storage

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

RUN playwright install chromium && playwright install-deps chromium

COPY app/ ./app/
COPY startup.sh .
RUN chmod +x startup.sh

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

EXPOSE ${PORT}
CMD ["./startup.sh"]
