"""
Web crawler module for discovering and fetching documents
"""

import logging
import hashlib
import time
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from config import CRAWLER_TIMEOUT, CRAWLER_USER_AGENT, CRAWLER_MAX_RETRIES

logger = logging.getLogger(__name__)


class Crawler:
    """Web crawler for discovering and fetching documents"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": CRAWLER_USER_AGENT})
        self.visited_urls = set()
        
    def fetch_url(self, url: str, timeout: int = CRAWLER_TIMEOUT) -> Optional[Dict]:
        """Fetch a URL and extract content"""
        if url in self.visited_urls:
            logger.debug(f"URL already visited: {url}")
            return None
            
        self.visited_urls.add(url)
        
        for attempt in range(CRAWLER_MAX_RETRIES):
            try:
                logger.info(f"Fetching: {url} (attempt {attempt + 1})")
                response = self.session.get(url, timeout=timeout, allow_redirects=True)
                
                # Compute hash
                content_hash = hashlib.sha256(response.content).hexdigest()
                
                # Extract text based on content type
                if "text/html" in response.headers.get("content-type", ""):
                    text_content = self._extract_html_text(response.text)
                    content_type = "text/html"
                elif "application/pdf" in response.headers.get("content-type", ""):
                    text_content = self._extract_pdf_text(response.content)
                    content_type = "application/pdf"
                else:
                    text_content = response.text
                    content_type = response.headers.get("content-type", "unknown")
                
                # Extract title
                title = self._extract_title(response.text) if "text/html" in response.headers.get("content-type", "") else None
                
                return {
                    "url": response.url,
                    "canonical_url": self._get_canonical_url(response.text, response.url),
                    "http_status": response.status_code,
                    "content_type": content_type,
                    "title": title,
                    "hash_sha256": content_hash,
                    "text_content": text_content,
                    "lang": self._detect_language(text_content),
                    "fetched_at": time.time()
                }
                
            except requests.Timeout:
                logger.warning(f"Timeout fetching {url}")
                if attempt == CRAWLER_MAX_RETRIES - 1:
                    return {"url": url, "error": "Timeout"}
                time.sleep(2 ** attempt)
                
            except requests.RequestException as e:
                logger.warning(f"Error fetching {url}: {e}")
                if attempt == CRAWLER_MAX_RETRIES - 1:
                    return {"url": url, "error": str(e)}
                time.sleep(2 ** attempt)
                
        return None
        
    def discover_urls(self, base_url: str, max_depth: int = 2) -> List[str]:
        """Discover URLs from a base URL (simple crawler)"""
        discovered = []
        to_crawl = [(base_url, 0)]
        
        while to_crawl:
            url, depth = to_crawl.pop(0)
            
            if depth > max_depth or url in self.visited_urls:
                continue
                
            try:
                response = self.session.get(url, timeout=CRAWLER_TIMEOUT)
                if "text/html" not in response.headers.get("content-type", ""):
                    continue
                    
                soup = BeautifulSoup(response.text, "html.parser")
                
                for link in soup.find_all("a", href=True):
                    href = link["href"]
                    absolute_url = urljoin(url, href)
                    
                    # Only follow same domain
                    if urlparse(absolute_url).netloc == urlparse(base_url).netloc:
                        if absolute_url not in self.visited_urls:
                            discovered.append(absolute_url)
                            if depth < max_depth:
                                to_crawl.append((absolute_url, depth + 1))
                                
            except Exception as e:
                logger.warning(f"Error discovering URLs from {url}: {e}")
                
        return discovered
        
    def _extract_html_text(self, html: str) -> str:
        """Extract clean text from HTML"""
        try:
            soup = BeautifulSoup(html, "html.parser")
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
                
            # Get text
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = " ".join(chunk for chunk in chunks if chunk)
            
            return text[:50000]  # Limit to 50k chars
        except Exception as e:
            logger.error(f"Error extracting HTML text: {e}")
            return ""
            
    def _extract_pdf_text(self, pdf_content: bytes) -> str:
        """Extract text from PDF (basic implementation)"""
        try:
            # For MVP, use pdfplumber if available
            import pdfplumber
            import io
            
            with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() or ""
                return text[:50000]
        except ImportError:
            logger.warning("pdfplumber not installed, returning empty text for PDF")
            return ""
        except Exception as e:
            logger.error(f"Error extracting PDF text: {e}")
            return ""
            
    def _extract_title(self, html: str) -> Optional[str]:
        """Extract title from HTML"""
        try:
            soup = BeautifulSoup(html, "html.parser")
            title_tag = soup.find("title")
            if title_tag:
                return title_tag.get_text().strip()
            
            h1 = soup.find("h1")
            if h1:
                return h1.get_text().strip()
                
        except Exception as e:
            logger.debug(f"Error extracting title: {e}")
            
        return None
        
    def _get_canonical_url(self, html: str, url: str) -> str:
        """Extract canonical URL from HTML or return original"""
        try:
            soup = BeautifulSoup(html, "html.parser")
            canonical = soup.find("link", rel="canonical")
            if canonical and canonical.get("href"):
                return canonical["href"]
        except Exception as e:
            logger.debug(f"Error extracting canonical URL: {e}")
            
        return url
        
    def _detect_language(self, text: str) -> str:
        """Detect language (simple heuristic)"""
        try:
            from textblob import TextBlob
            blob = TextBlob(text[:500])
            return str(blob.detect_language())
        except ImportError:
            # Fallback: check for common words
            if any(word in text.lower() for word in ["de", "het", "een", "van", "en"]):
                return "nl"
            return "en"
        except Exception as e:
            logger.debug(f"Error detecting language: {e}")
            return "unknown"
