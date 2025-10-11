"""Base stream class for IRS tax rules data extraction."""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Iterator, Optional, List
from datetime import datetime, date
from dateutil.parser import parse as parse_date

from fivetran_connector_sdk import Operations

logger = logging.getLogger(__name__)


class BaseStream(ABC):
    """Base class for all IRS data streams."""
    
    def __init__(self, http_client, base_url: str, jurisdiction_level: str, jurisdiction_code: str):
        self.http_client = http_client
        self.base_url = base_url
        self.jurisdiction_level = jurisdiction_level
        self.jurisdiction_code = jurisdiction_code
        self.cursor = None
    
    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """Return the schema definition for this stream."""
        pass
    
    @abstractmethod
    def sync(self, cursor: Optional[str] = None) -> Iterator[Operations]:
        """Sync data from the source."""
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """Test if we can connect to the data source."""
        pass
    
    def get_cursor(self) -> Optional[str]:
        """Get the current cursor value."""
        return self.cursor
    
    def set_cursor(self, cursor: str):
        """Set the cursor value."""
        self.cursor = cursor
    
    def parse_date(self, date_str: str) -> Optional[date]:
        """Parse a date string into a date object."""
        if not date_str:
            return None
        
        try:
            parsed = parse_date(date_str)
            return parsed.date() if parsed else None
        except Exception as e:
            logger.warning(f"Could not parse date '{date_str}': {e}")
            return None
    
    def format_date_for_cursor(self, date_obj: date) -> str:
        """Format a date object for use as a cursor."""
        return date_obj.isoformat() if date_obj else ""
    
    def parse_cursor_date(self, cursor: str) -> Optional[date]:
        """Parse a cursor string back to a date object."""
        if not cursor:
            return None
        
        try:
            return date.fromisoformat(cursor)
        except Exception as e:
            logger.warning(f"Could not parse cursor date '{cursor}': {e}")
            return None
    
    def create_record_operation(self, table_name: str, record: Dict[str, Any]) -> Operations:
        """Create a record operation for Fivetran."""
        # Add Fivetran metadata
        record['_fivetran_synced'] = datetime.utcnow().isoformat()
        
        return Operations.upsert(
            table=table_name,
            data=record
        )
    
    def create_schema_operation(self, table_name: str, schema: Dict[str, Any]) -> Operations:
        """Create a schema operation for Fivetran."""
        # For now, we'll just return an upsert operation with schema info
        # The actual schema is handled by the connector's schema() method
        return Operations.upsert(
            table=table_name,
            data={'_schema_info': 'defined'}
        )
    
    def extract_links_from_text(self, soup, base_url: str) -> List[Dict[str, str]]:
        """Extract links from BeautifulSoup object."""
        links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text(strip=True)
            
            # Convert relative URLs to absolute
            if href.startswith('/'):
                href = self.http_client.resolve_relative_url(base_url, href)
            elif not href.startswith('http'):
                continue
            
            # Only include IRS links
            if self.http_client.is_valid_irs_url(href):
                links.append({
                    'url': href,
                    'text': text,
                    'title': link.get('title', '')
                })
        
        return links
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        if not text:
            return ""
        
        # Remove extra whitespace and normalize
        return ' '.join(text.split())
    
    def is_relevant_content(self, text: str, keywords: List[str]) -> bool:
        """Check if text contains relevant keywords."""
        if not text or not keywords:
            return False
        
        text_lower = text.lower()
        return any(keyword.lower() in text_lower for keyword in keywords)
