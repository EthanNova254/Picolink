# Production-ready all-in-one API service
# Optimized for Koyeb free tier (2GB RAM, 2 cores)

FROM python:3.11-slim-bullseye

# Prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    PORT=8000 \
    WORKERS=2 \
    MAX_UPLOAD_SIZE=100 \
    CLEANUP_HOURS=24

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng tesseract-ocr-fra tesseract-ocr-deu tesseract-ocr-spa tesseract-ocr-ara tesseract-ocr-chi-sim \
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

# Create app directory and storage
WORKDIR /app
RUN mkdir -p storage/uploads storage/outputs storage/temp && \
    chmod -R 777 storage

# Copy requirements and upgrade pip first
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --use-feature=fast-deps -r requirements.txt

# Install Playwright browsers (Chromium only)
RUN playwright install chromium && \
    playwright install-deps chromium

# Copy application code
COPY app/ ./app/
COPY startup.sh .
RUN chmod +x startup.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Expose port
EXPOSE ${PORT}

# Run startup script
CMD ["./startup.sh"]
