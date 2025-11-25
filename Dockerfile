# Production-ready all-in-one API service
# Compatible with Render, Koyeb, and other platforms

FROM python:3.11-slim-bullseye

# Prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    PORT=8000 \
    WORKERS=1 \
    MAX_UPLOAD_SIZE=100 \
    CLEANUP_HOURS=24

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Tesseract OCR + languages
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-fra \
    tesseract-ocr-deu \
    tesseract-ocr-spa \
    tesseract-ocr-ara \
    tesseract-ocr-chi-sim \
    # Image processing
    libtesseract-dev \
    libleptonica-dev \
    poppler-utils \
    libpoppler-cpp-dev \
    # FFmpeg (full build)
    ffmpeg \
    # Web scraping dependencies
    wget \
    curl \
    ca-certificates \
    # Build tools
    gcc \
    g++ \
    make \
    # Cleanup
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create app directory and storage
WORKDIR /app
RUN mkdir -p storage/uploads storage/outputs storage/temp && \
    chmod -R 777 storage

# Copy requirements first (better caching)
COPY requirements.txt .

# Upgrade pip and install Python packages
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (Chromium only for efficiency)
RUN playwright install chromium && \
    playwright install-deps chromium || true

# Copy application code
COPY app/ ./app/
COPY startup.sh .
RUN chmod +x startup.sh

# Create empty __init__.py files if they don't exist
RUN touch app/routers/__init__.py && \
    touch app/services/__init__.py

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Expose port
EXPOSE ${PORT}

# Run startup script
CMD ["./startup.sh"]
