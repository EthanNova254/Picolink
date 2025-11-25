"""
Crawl4AI router - Web scraping endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, HttpUrl
from typing import Optional
from app.services.crawler import crawler_service
from app.utils import validate_url

router = APIRouter(prefix="/crawl", tags=["Web Scraping"])

class ScrapeRequest(BaseModel):
    url: HttpUrl
    
class DeepScrapeRequest(BaseModel):
    url: HttpUrl
    max_pages: int = 10
    same_domain_only: bool = True

@router.post("/scrape")
async def scrape_simple(request: ScrapeRequest):
    """
    Simple web scrape - returns cleaned text
    
    **Use cases:**
    - Extract article content
    - Get blog post text
    - Quick page summary
    
    **n8n example:**
    ```json
    {
      "method": "POST",
      "url": "https://your-service.koyeb.app/crawl/scrape",
      "body": {
        "url": "https://example.com/article"
      }
    }
    ```
    """
    if not validate_url(str(request.url)):
        raise HTTPException(status_code=400, detail="Invalid URL")
    
    result = await crawler_service.scrape_simple(str(request.url))
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result

@router.post("/scrape/html")
async def scrape_html(request: ScrapeRequest):
    """
    Fetch raw HTML from URL
    
    **Use cases:**
    - Get complete page HTML
    - Parse custom elements
    - Archive web pages
    
    **n8n example:**
    ```json
    {
      "method": "POST",
      "url": "https://your-service.koyeb.app/crawl/scrape/html",
      "body": {
        "url": "https://example.com"
      }
    }
    ```
    """
    if not validate_url(str(request.url)):
        raise HTTPException(status_code=400, detail="Invalid URL")
    
    result = await crawler_service.scrape_html(str(request.url))
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result

@router.post("/scrape/text")
async def scrape_text(request: ScrapeRequest):
    """
    Fetch plain text only (no HTML)
    
    **Use cases:**
    - Text-only extraction
    - Feed into text analysis
    - Simple content retrieval
    """
    if not validate_url(str(request.url)):
        raise HTTPException(status_code=400, detail="Invalid URL")
    
    result = await crawler_service.scrape_text(str(request.url))
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result

@router.post("/scrape/meta")
async def scrape_metadata(request: ScrapeRequest):
    """
    Extract page metadata and links
    
    **Returns:**
    - Title
    - Meta description
    - Open Graph data
    - Internal/external links
    
    **Use cases:**
    - SEO analysis
    - Link discovery
    - Social media preview data
    """
    if not validate_url(str(request.url)):
        raise HTTPException(status_code=400, detail="Invalid URL")
    
    result = await crawler_service.scrape_metadata(str(request.url))
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result

@router.post("/scrape/deep")
async def scrape_deep(request: DeepScrapeRequest):
    """
    Deep crawl - multiple pages
    
    **Parameters:**
    - max_pages: Maximum pages to crawl (1-50)
    - same_domain_only: Stay on same domain
    
    **Use cases:**
    - Crawl entire blog
    - Site mapping
    - Multi-page content extraction
    
    **Warning:** Resource intensive, use sparingly
    
    **n8n example:**
    ```json
    {
      "method": "POST",
      "url": "https://your-service.koyeb.app/crawl/scrape/deep",
      "body": {
        "url": "https://blog.example.com",
        "max_pages": 20,
        "same_domain_only": true
      }
    }
    ```
    """
    if not validate_url(str(request.url)):
        raise HTTPException(status_code=400, detail="Invalid URL")
    
    result = await crawler_service.scrape_deep(
        str(request.url),
        request.max_pages,
        request.same_domain_only
    )
    
    return result
