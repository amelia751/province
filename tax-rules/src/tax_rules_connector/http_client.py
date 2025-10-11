"""HTTP client for IRS websites with retry logic and error handling."""

import logging
import time
import hashlib
from typing import Optional, Dict, Any
from urllib.parse import urljoin, urlparse

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class IRSHttpClient:
    """HTTP client specifically designed for IRS website scraping."""
    
    def __init__(self, timeout: int = 30, max_retries: int = 3):
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """Create a requests session with retry strategy."""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=self.max_retries,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],
            backoff_factor=1
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set user agent to identify as a legitimate scraper
        session.headers.update({
            'User-Agent': 'TaxRulesConnector/1.0 (Fivetran Integration; contact@yourorg.com)'
        })
        
        return session
    
    def get(self, url: str, **kwargs) -> requests.Response:
        """Make a GET request with error handling."""
        try:
            logger.debug(f"Making GET request to: {url}")
            response = self.session.get(url, timeout=self.timeout, **kwargs)
            response.raise_for_status()
            
            # Add small delay to be respectful to IRS servers
            time.sleep(0.5)
            
            return response
            
        except requests.RequestException as e:
            logger.error(f"HTTP request failed for {url}: {e}")
            raise
    
    def get_soup(self, url: str, parser: str = 'html.parser') -> BeautifulSoup:
        """Get a BeautifulSoup object from a URL."""
        response = self.get(url)
        return BeautifulSoup(response.content, parser)
    
    def get_pdf_metadata(self, url: str) -> Dict[str, Any]:
        """Get metadata about a PDF file without downloading the full content."""
        try:
            # Make a HEAD request first to get content info
            head_response = self.session.head(url, timeout=self.timeout)
            head_response.raise_for_status()
            
            metadata = {
                'url': url,
                'content_type': head_response.headers.get('content-type', ''),
                'content_length': head_response.headers.get('content-length'),
                'last_modified': head_response.headers.get('last-modified'),
                'etag': head_response.headers.get('etag')
            }
            
            # For PDFs, we might want to get a hash of the first few KB
            if 'pdf' in metadata['content_type'].lower():
                try:
                    # Get first 8KB for hash calculation
                    partial_response = self.session.get(
                        url, 
                        headers={'Range': 'bytes=0-8191'},
                        timeout=self.timeout
                    )
                    if partial_response.status_code in [200, 206]:
                        metadata['partial_sha256'] = hashlib.sha256(
                            partial_response.content
                        ).hexdigest()
                except Exception as e:
                    logger.warning(f"Could not get partial hash for {url}: {e}")
            
            return metadata
            
        except requests.RequestException as e:
            logger.error(f"Failed to get PDF metadata for {url}: {e}")
            raise
    
    def download_pdf_content(self, url: str, max_size_mb: int = 50) -> bytes:
        """Download PDF content with size limit."""
        max_size_bytes = max_size_mb * 1024 * 1024
        
        try:
            response = self.session.get(url, stream=True, timeout=self.timeout)
            response.raise_for_status()
            
            content = b''
            for chunk in response.iter_content(chunk_size=8192):
                content += chunk
                if len(content) > max_size_bytes:
                    logger.warning(f"PDF {url} exceeds {max_size_mb}MB limit, truncating")
                    break
            
            return content
            
        except requests.RequestException as e:
            logger.error(f"Failed to download PDF {url}: {e}")
            raise
    
    def calculate_content_hash(self, content: bytes) -> str:
        """Calculate SHA256 hash of content."""
        return hashlib.sha256(content).hexdigest()
    
    def is_valid_irs_url(self, url: str) -> bool:
        """Check if URL is from IRS domain."""
        parsed = urlparse(url)
        netloc = parsed.netloc.lower()
        return netloc == 'irs.gov' or netloc == 'www.irs.gov'
    
    def resolve_relative_url(self, base_url: str, relative_url: str) -> str:
        """Resolve a relative URL against a base URL."""
        return urljoin(base_url, relative_url)
    
    def test_connection(self, test_url: str = "https://www.irs.gov") -> bool:
        """Test if we can connect to IRS website."""
        try:
            response = self.get(test_url)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def close(self):
        """Close the session."""
        if self.session:
            self.session.close()
