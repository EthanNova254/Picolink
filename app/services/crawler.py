"""
Crawl4AI service - Raw web scraping without AI enhancement
Compatible with crawl4ai 0.3.74+ without BrowserConfig
"""
import asyncio
from typing import Dict, List, Optional
from crawl4ai import AsyncWebCrawler
from bs4 import BeautifulSoup
from app.config import settings

class CrawlerService:
    """Raw web scraping service using Crawl4AI - simplified API"""
    
    async def scrape_simple(self, url: str) -> Dict:
        """Simple scrape - returns cleaned text"""
        try:
            async with AsyncWebCrawler(verbose=False) as crawler:
                result = await crawler.arun(url=url)
                
                return {
                    "url": url,
                    "success": result.success,
                    "text": result.markdown if result.success else None,
                    "title": self._extract_title(result.html) if result.success and result.html else None,
                    "error": str(result.error_message) if not result.success else None
                }
        except Exception as e:
            return {
                "url": url,
                "success": False,
                "error": str(e)
            }
    
    async def scrape_html(self, url: str) -> Dict:
        """Fetch raw HTML"""
        try:
            async with AsyncWebCrawler(verbose=False) as crawler:
                result = await crawler.arun(url=url)
                
                return {
                    "url": url,
                    "success": result.success,
                    "html": result.html if result.success else None,
                    "error": str(result.error_message) if not result.success else None
                }
        except Exception as e:
            return {
                "url": url,
                "success": False,
                "error": str(e)
            }
    
    async def scrape_text(self, url: str) -> Dict:
        """Fetch plain text only"""
        try:
            async with AsyncWebCrawler(verbose=False) as crawler:
                result = await crawler.arun(url=url)
                
                return {
                    "url": url,
                    "success": result.success,
                    "text": result.markdown if result.success else None,
                    "error": str(result.error_message) if not result.success else None
                }
        except Exception as e:
            return {
                "url": url,
                "success": False,
                "error": str(e)
            }
    
    async def scrape_metadata(self, url: str) -> Dict:
        """Extract page metadata"""
        try:
            async with AsyncWebCrawler(verbose=False) as crawler:
                result = await crawler.arun(url=url)
                
                if not result.success:
                    return {
                        "url": url,
                        "success": False,
                        "error": str(result.error_message)
                    }
                
                soup = BeautifulSoup(result.html, 'lxml')
                
                # Extract links from HTML directly
                all_links = [a.get('href') for a in soup.find_all('a', href=True)]
                from urllib.parse import urljoin, urlparse
                
                base_domain = urlparse(url).netloc
                internal_links = []
                external_links = []
                
                for link in all_links[:50]:  # Limit to first 50
                    try:
                        full_url = urljoin(url, link)
                        if urlparse(full_url).netloc == base_domain:
                            internal_links.append(full_url)
                        else:
                            external_links.append(full_url)
                    except:
                        continue
                
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
                    "links_count": len(internal_links) + len(external_links),
                    "internal_links": internal_links[:10],
                    "external_links": external_links[:10]
                }
        except Exception as e:
            return {
                "url": url,
                "success": False,
                "error": str(e)
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
        
        visited = set()
        results = []
        to_visit = [url]
        
        from urllib.parse import urljoin, urlparse
        base_domain = urlparse(url).netloc if same_domain_only else None
        
        try:
            async with AsyncWebCrawler(verbose=False) as crawler:
                while to_visit and len(visited) < max_pages:
                    current_url = to_visit.pop(0)
                    
                    if current_url in visited:
                        continue
                    
                    visited.add(current_url)
                    
                    try:
                        result = await crawler.arun(url=current_url)
                        
                        if result.success:
                            results.append({
                                "url": current_url,
                                "title": self._extract_title(result.html),
                                "text": result.markdown[:1000] if result.markdown else "",
                            })
                            
                            # Extract links from HTML
                            if same_domain_only:
                                soup = BeautifulSoup(result.html, 'lxml')
                                for a in soup.find_all('a', href=True):
                                    try:
                                        link = urljoin(current_url, a.get('href'))
                                        if urlparse(link).netloc == base_domain and link not in visited:
                                            to_visit.append(link)
                                    except:
                                        continue
                    except Exception:
                        continue
            
            return {
                "start_url": url,
                "pages_crawled": len(results),
                "pages": results
            }
        except Exception as e:
            return {
                "start_url": url,
                "pages_crawled": 0,
                "error": str(e),
                "pages": []
            }
    
    def _extract_title(self, html: str) -> Optional[str]:
        """Extract page title"""
        try:
            soup = BeautifulSoup(html, 'lxml')
            title_tag = soup.find('title')
            return title_tag.string.strip() if title_tag and title_tag.string else None
        except:
            return None
    
    def _get_meta_content(self, soup: BeautifulSoup, name: str) -> Optional[str]:
        """Get meta tag content by name"""
        try:
            tag = soup.find('meta', attrs={'name': name})
            return tag.get('content') if tag else None
        except:
            return None
    
    def _get_meta_property(self, soup: BeautifulSoup, property_name: str) -> Optional[str]:
        """Get meta tag content by property"""
        try:
            tag = soup.find('meta', attrs={'property': property_name})
            return tag.get('content') if tag else None
        except:
            return None

# Singleton instance
crawler_service = CrawlerService()
