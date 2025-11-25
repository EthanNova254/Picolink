#!/bin/bash
set -e

echo "=================================================="
echo "🚀 All-in-One API Service Starting"
echo "=================================================="

# Verify critical dependencies
echo "✓ Checking Tesseract..."
tesseract --version | head -n 1

echo "✓ Checking FFmpeg..."
ffmpeg -version | head -n 1

echo "✓ Checking Playwright..."
playwright --version

echo "✓ Checking storage directories..."
ls -la storage/

# Start background cleanup job (runs every hour)
python3 -c "
import asyncio
import os
import time
from pathlib import Path
from datetime import datetime, timedelta

async def cleanup_old_files():
    cleanup_hours = int(os.getenv('CLEANUP_HOURS', '24'))
    while True:
        try:
            cutoff = datetime.now() - timedelta(hours=cleanup_hours)
            for folder in ['storage/uploads', 'storage/outputs', 'storage/temp']:
                for file_path in Path(folder).glob('*'):
                    if file_path.is_file():
                        mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                        if mtime < cutoff:
                            file_path.unlink()
                            print(f'🗑️  Cleaned up: {file_path}')
        except Exception as e:
            print(f'⚠️  Cleanup error: {e}')
        await asyncio.sleep(3600)  # Every hour

asyncio.run(cleanup_old_files())
" &

CLEANUP_PID=$!
echo "✓ Background cleanup job started (PID: $CLEANUP_PID)"

# Start FastAPI server
echo "=================================================="
echo "🌐 Starting API server on port ${PORT}"
echo "=================================================="

exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port ${PORT} \
    --workers ${WORKERS} \
    --timeout-keep-alive 300 \
    --limit-concurrency 50 \
    --log-level info
