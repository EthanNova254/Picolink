"""
Main FastAPI application
All-in-One API Service - Production Ready
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time

from app.config import settings
from app.routers import crawl, ocr, pdf, ffmpeg, health

# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("=" * 60)
    print("🚀 All-in-One API Service Starting")
    print("=" * 60)
    print(f"📍 Storage: {settings.STORAGE_DIR}")
    print(f"⚙️  Max upload: {settings.MAX_UPLOAD_SIZE}MB")
    print(f"🧹 Cleanup: Every {settings.CLEANUP_HOURS} hours")
    print("=" * 60)
    
    yield
    
    # Shutdown
    print("=" * 60)
    print("👋 All-in-One API Service Shutting Down")
    print("=" * 60)

# Create FastAPI app
app = FastAPI(
    title="All-in-One API Service",
    description="""
    **Production-ready API service with zero external dependencies**
    
    ## Features
    
    ✅ **Web Scraping** (Crawl4AI)
    - Raw HTML extraction
    - Text extraction
    - Metadata extraction
    - Deep crawling
    
    ✅ **OCR** (Tesseract)
    - Image text extraction
    - PDF text extraction
    - Multiple languages
    - Multiple output formats
    
    ✅ **PDF Generation**
    - From text
    - From HTML
    - From markdown
    - From images
    - PDF merging
    
    ✅ **Video/Audio Processing** (FFmpeg)
    - Trimming
    - Merging
    - Resizing
    - Compression
    - Audio extraction
    - Thumbnail generation
    - Format conversion
    
    ## No API Keys Required
    Everything runs locally inside this container.
    
    ## Resource Limits
    Optimized for Koyeb free tier (2GB RAM, 2 cores)
    
    ## Rate Limiting
    Max {0} concurrent requests to prevent resource exhaustion
    """.format(settings.MAX_CONCURRENT_REQUESTS),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "path": str(request.url)
        }
    )

# Include routers
app.include_router(health.router)
app.include_router(crawl.router)
app.include_router(ocr.router)
app.include_router(pdf.router)
app.include_router(ffmpeg.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.PORT,
        workers=settings.WORKERS
    )
