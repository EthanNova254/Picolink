#!/bin/bash
set -e

echo "=================================================="
echo "🚀 All-in-One API Service Starting"
echo "=================================================="

# Verify critical dependencies
echo "✓ Checking Tesseract..."
tesseract --version | head -n 1 || echo "⚠️  Tesseract check failed"

echo "✓ Checking FFmpeg..."
ffmpeg -version | head -n 1 || echo "⚠️  FFmpeg check failed"

echo "✓ Checking storage directories..."
ls -la storage/ || echo "⚠️  Storage check failed"

# Start background cleanup job (runs every hour)
(
  python3 -c "
import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

async def cleanup_old_files():
    cleanup_hours = int(os.getenv('CLEANUP_HOURS', '24'))
    while True:
        try:
            cutoff = datetime.now() - timedelta(hours=cleanup_hours)
            for folder in ['storage/uploads', 'storage/outputs', 'storage/temp']:
                try:
                    for file_path in Path(folder).glob('*'):
                        if file_path.is_file():
                            mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                            if mtime < cutoff:
                                file_path.unlink()
                                print(f'🗑️  Cleaned up: {file_path}')
                except Exception as e:
                    print(f'⚠️  Cleanup error in {folder}: {e}')
        except Exception as e:
            print(f'⚠️  Cleanup loop error: {e}')
        await asyncio.sleep(3600)

try:
    asyncio.run(cleanup_old_files())
except KeyboardInterrupt:
    sys.exit(0)
" 2>&1 | while IFS= read -r line; do echo "[CLEANUP] $line"; done
) &

CLEANUP_PID=$!
echo "✓ Background cleanup job started (PID: $CLEANUP_PID)"

# Ensure PORT is set
if [ -z "$PORT" ]; then
    export PORT=8000
    echo "⚠️  PORT not set, defaulting to 8000"
fi

# Ensure WORKERS is set
if [ -z "$WORKERS" ]; then
    export WORKERS=1
    echo "⚠️  WORKERS not set, defaulting to 1"
fi

# Start FastAPI server
echo "=================================================="
echo "🌐 Starting API server on port ${PORT}"
echo "📝 Workers: ${WORKERS}"
echo "=================================================="

exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port ${PORT} \
    --workers ${WORKERS} \
    --timeout-keep-alive 300 \
    --limit-concurrency 50 \
    --log-level info \
    --access-log
