"""Base stream class for IRS tax rules data extraction."""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Iterator, Optional, List
from datetime import datetime, date
from dateutil.parser import parse as parse_date

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
    def read_records(self, cursor: Optional[str] = None) -> Iterator[Dict[str, Any]]:
        """Read records from the source."""
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
    
    def add_common_fields(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Add common fields to all records."""
        record.update({
            'jurisdiction_level': self.jurisdiction_level,
            'jurisdiction_code': self.jurisdiction_code,
            '_extracted_at': datetime.utcnow().isoformat() + 'Z',
            '_source_url': self.base_url
        })
        return record
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        if not text:
            return ""
        
        # Remove extra whitespace and normalize
        text = ' '.join(text.split())
        
        # Remove common HTML entities
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')
        
        return text.strip()
    
    def generate_id(self, *components) -> str:
        """Generate a deterministic ID from components."""
        import hashlib
        
        # Join components and create hash
        content = '|'.join(str(c) for c in components if c)
        return hashlib.sha1(content.encode('utf-8')).hexdigest()[:16]