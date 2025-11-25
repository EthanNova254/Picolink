"""
Simple web scraping service using requests + BeautifulSoup
No Playwright, no Crawl4AI - just basic HTTP requests
"""
import requests
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from app.config import settings

class CrawlerService:
    """Simple web scraping using requests"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': settings.CRAWL_USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        self.timeout = settings.CRAWL_TIMEOUT
    
    async def scrape_simple(self, url: str) -> Dict:
        """Simple scrape - returns cleaned text"""
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            text = soup.get_text(separator='\n', strip=True)
            
            return {
                "url": url,
                "success": True,
                "text": text,
                "title": self._extract_title(soup),
                "error": None
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
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            
            return {
                "url": url,
                "success": True,
                "html": response.text,
                "error": None
            }
        except Exception as e:
            return {
                "url": url,
                "success": False,
                "error": str(e)
            }
    
    async def scrape_text(self, url: str) -> Dict:
        """Fetch plain text only"""
        return await self.scrape_simple(url)
    
    async def scrape_metadata(self, url: str) -> Dict:
        """Extract page metadata"""
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Extract all links
            base_domain = urlparse(url).netloc
            internal_links = []
            external_links = []
            
            for a in soup.find_all('a', href=True):
                try:
                    full_url = urljoin(url, a.get('href'))
                    if urlparse(full_url).netloc == base_domain:
                        internal_links.append(full_url)
                    else:
                        external_links.append(full_url)
                except:
                    continue
            
            return {
                "url": url,
                "success": True,
                "title": self._extract_title(soup),
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
        """Deep scrape - crawl multiple pages"""
        max_pages = min(max_pages, settings.MAX_CRAWL_PAGES)
        
        visited = set()
        results = []
        to_visit = [url]
        
        base_domain = urlparse(url).netloc if same_domain_only else None
        
        try:
            while to_visit and len(visited) < max_pages:
                current_url = to_visit.pop(0)
                
                if current_url in visited:
                    continue
                
                visited.add(current_url)
                
                try:
                    response = requests.get(current_url, headers=self.headers, timeout=self.timeout)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.content, 'lxml')
                    
                    # Remove script and style
                    for script in soup(["script", "style"]):
                        script.decompose()
                    
                    text = soup.get_text(separator='\n', strip=True)
                    
                    results.append({
                        "url": current_url,
                        "title": self._extract_title(soup),
                        "text": text[:1000],
                    })
                    
                    # Extract links
                    if same_domain_only:
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
    
    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract page title"""
        try:
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
