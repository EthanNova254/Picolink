"""
Crawl4AI service - Raw web scraping without AI enhancement
"""
import asyncio
from typing import Dict, List, Optional
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from bs4 import BeautifulSoup
from app.config import settings

class CrawlerService:
    """Raw web scraping service using Crawl4AI"""
    
    def __init__(self):
        self.browser_config = BrowserConfig(
            headless=True,
            verbose=False,
            user_agent=settings.CRAWL_USER_AGENT
        )
    
    async def scrape_simple(self, url: str) -> Dict:
        """Simple scrape - returns cleaned text"""
        crawler_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            page_timeout=settings.CRAWL_TIMEOUT * 1000,
            wait_for_images=False,
            screenshot=False,
            process_iframes=False
        )
        
        async with AsyncWebCrawler(config=self.browser_config) as crawler:
            result = await crawler.arun(
                url=url,
                config=crawler_config
            )
            
            return {
                "url": url,
                "success": result.success,
                "text": result.markdown if result.success else None,
                "title": self._extract_title(result.html) if result.success else None,
                "error": result.error_message if not result.success else None
            }
    
    async def scrape_html(self, url: str) -> Dict:
        """Fetch raw HTML"""
        crawler_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            page_timeout=settings.CRAWL_TIMEOUT * 1000,
            wait_for_images=False,
            screenshot=False
        )
        
        async with AsyncWebCrawler(config=self.browser_config) as crawler:
            result = await crawler.arun(url=url, config=crawler_config)
            
            return {
                "url": url,
                "success": result.success,
                "html": result.html if result.success else None,
                "error": result.error_message if not result.success else None
            }
    
    async def scrape_text(self, url: str) -> Dict:
        """Fetch plain text only"""
        crawler_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            page_timeout=settings.CRAWL_TIMEOUT * 1000,
        )
        
        async with AsyncWebCrawler(config=self.browser_config) as crawler:
            result = await crawler.arun(url=url, config=crawler_config)
            
            return {
                "url": url,
                "success": result.success,
                "text": result.markdown if result.success else None,
                "error": result.error_message if not result.success else None
            }
    
    async def scrape_metadata(self, url: str) -> Dict:
        """Extract page metadata"""
        crawler_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            page_timeout=settings.CRAWL_TIMEOUT * 1000,
        )
        
        async with AsyncWebCrawler(config=self.browser_config) as crawler:
            result = await crawler.arun(url=url, config=crawler_config)
            
            if not result.success:
                return {
                    "url": url,
                    "success": False,
                    "error": result.error_message
                }
            
            soup = BeautifulSoup(result.html, 'lxml')
            
            return {
                "url": url,
                "success": True,
                "title": self._extract_title(result.html),
                "meta": {
                    "description": self._get_meta_content(soup, "description"),
                    "keywords": self._get_meta_content(soup, "keywords"),
                    "author": self._get_meta_content(soup, "author"),
                    "og_title": self._get_meta_property(soup, "og:title"),
                    "og_description": self._get_meta_property(soup, "og:description"),
                    "og_image": self._get_meta_property(soup, "og:image"),
                },
                "links_count": len(result.links.get("internal", [])) + len(result.links.get("external", [])),
                "internal_links": result.links.get("internal", [])[:10],
                "external_links": result.links.get("external", [])[:10]
            }
    
    async def scrape_deep(
        self,
        url: str,
        max_pages: int = 10,
        same_domain_only: bool = True
    ) -> Dict:
        """
        Deep scrape - crawl multiple pages
        LIMITED to prevent abuse
        """
        max_pages = min(max_pages, settings.MAX_CRAWL_PAGES)
        
        crawler_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            page_timeout=settings.CRAWL_TIMEOUT * 1000,
        )
        
        visited = set()
        results = []
        to_visit = [url]
        
        async with AsyncWebCrawler(config=self.browser_config) as crawler:
            while to_visit and len(visited) < max_pages:
                current_url = to_visit.pop(0)
                
                if current_url in visited:
                    continue
                
                visited.add(current_url)
                
                result = await crawler.arun(url=current_url, config=crawler_config)
                
                if result.success:
                    results.append({
                        "url": current_url,
                        "title": self._extract_title(result.html),
                        "text": result.markdown[:1000],  # First 1000 chars
                    })
                    
                    # Add internal links to queue
                    if same_domain_only:
                        internal = result.links.get("internal", [])
                        to_visit.extend([link for link in internal if link not in visited])
        
        return {
            "start_url": url,
            "pages_crawled": len(results),
            "pages": results
        }
    
    def _extract_title(self, html: str) -> Optional[str]:
        """Extract page title"""
        soup = BeautifulSoup(html, 'lxml')
        title_tag = soup.find('title')
        return title_tag.string.strip() if title_tag else None
    
    def _get_meta_content(self, soup: BeautifulSoup, name: str) -> Optional[str]:
        """Get meta tag content by name"""
        tag = soup.find('meta', attrs={'name': name})
        return tag.get('content') if tag else None
    
    def _get_meta_property(self, soup: BeautifulSoup, property_name: str) -> Optional[str]:
        """Get meta tag content by property"""
        tag = soup.find('meta', attrs={'property': property_name})
        return tag.get('content') if tag else None

# Singleton instance
crawler_service = CrawlerService()
