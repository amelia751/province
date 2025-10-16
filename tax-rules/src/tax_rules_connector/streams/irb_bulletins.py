"""IRB bulletins stream for Internal Revenue Bulletin documents."""

import logging
import re
from typing import Dict, Any, Iterator, Optional, List
from datetime import datetime, date
from urllib.parse import urljoin

from .base import BaseStream

logger = logging.getLogger(__name__)


class IRBBulletinsStream(BaseStream):
    """Stream for Internal Revenue Bulletin documents."""
    
    def get_schema(self) -> Dict[str, Any]:
        """Return schema for irb_bulletins table."""
        return {
            "primary_key": ["bulletin_no", "doc_number"],
            "columns": {
                "bulletin_no": {"type": "STRING", "primary_key": True},
                "doc_number": {"type": "STRING", "primary_key": True},
                "published_date": {"type": "DATE"},
                "doc_type": {"type": "STRING"},
                "title": {"type": "STRING"},
                "url_html": {"type": "STRING"},
                "url_pdf": {"type": "STRING"},
                "jurisdiction_level": {"type": "STRING"},
                "jurisdiction_code": {"type": "STRING"},
                "_extracted_at": {"type": "TIMESTAMP"}
            }
        }
    
    def test_connection(self) -> bool:
        """Test connection to IRB."""
        try:
            soup = self.http_client.get_soup(self.base_url)
            return soup.title is not None
        except Exception as e:
            logger.error(f"IRB connection test failed: {e}")
            return False
    
    def read_records(self, cursor: Optional[str] = None) -> Iterator[Dict[str, Any]]:
        """Read IRB bulletin records."""
        logger.info(f"Reading IRB bulletins with cursor: {cursor}")
        
        # Get bulletins for current and previous year
        current_year = datetime.now().year
        years_to_process = [current_year, current_year - 1]
        
        for year in years_to_process:
            try:
                bulletins = self._get_bulletins_for_year(year)
                for bulletin in bulletins:
                    yield self.add_common_fields(bulletin)
                    
            except Exception as e:
                logger.error(f"Error processing IRB year {year}: {e}")
                continue
        
        logger.info("Completed IRB bulletins read")
    
    def _get_bulletins_for_year(self, year: int) -> List[Dict[str, Any]]:
        """Get all bulletins for a specific year."""
        bulletins = []
        
        try:
            # Use main IRB page to find bulletins
            soup = self.http_client.get_soup(self.base_url)
            
            # Look for bulletin links with the pattern YYYY-NN_IRB
            bulletin_links = soup.find_all('a', href=re.compile(rf'{year}-\d+_IRB'))
            
            for link in bulletin_links:
                try:
                    bulletin_data = self._parse_bulletin_link(link, year)
                    if bulletin_data:
                        bulletins.append(bulletin_data)
                        
                except Exception as e:
                    logger.warning(f"Error parsing bulletin link: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error fetching IRB year index for {year}: {e}")
        
        return bulletins
    
    def _parse_bulletin_link(self, link, year: int) -> Optional[Dict[str, Any]]:
        """Parse a bulletin link into structured data."""
        href = link.get('href', '')
        text = link.get_text(strip=True)
        
        if not href:
            return None
        
        # Extract bulletin number (e.g., "2024-44_IRB" -> "2024-44")
        bulletin_match = re.search(rf'({year}-\d+)_IRB', href)
        if not bulletin_match:
            return None
        
        bulletin_no = bulletin_match.group(1)
        
        # Convert relative URL to absolute
        if href.startswith('/'):
            href = urljoin(self.base_url, href)
        
        # Extract date from bulletin number (approximate)
        try:
            week_num = int(bulletin_no.split('-')[1])
            # Approximate date based on week number
            published_date = date(year, min(12, max(1, week_num // 4)), 15)
        except:
            published_date = date(year, 6, 15)  # Default to mid-year
        
        # Create bulletin record
        bulletin = {
            'bulletin_no': bulletin_no,
            'doc_number': f"{bulletin_no}_1",  # Default doc number
            'published_date': published_date,
            'doc_type': 'irb_document',
            'title': self.clean_text(text) or f"Internal Revenue Bulletin {bulletin_no}",
            'url_html': href,
            'url_pdf': href.replace('_IRB', '.pdf') if '_IRB' in href else None
        }
        
        return bulletin