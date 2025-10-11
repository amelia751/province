"""Revenue Procedure items stream for extracting tax tables and thresholds."""

import logging
import re
from typing import Dict, Any, Iterator, Optional, List
from datetime import datetime, date
from urllib.parse import urljoin

from fivetran_connector_sdk import Operations

from .base import BaseStream

logger = logging.getLogger(__name__)


class RevProcItemsStream(BaseStream):
    """Stream for extracting structured data from Revenue Procedures."""
    
    # Removed filtering - now extracting all content
    
    def __init__(self, http_client, jurisdiction_level: str, jurisdiction_code: str):
        # RevProc items don't have a single base URL - they're discovered from newsroom
        super().__init__(http_client, "", jurisdiction_level, jurisdiction_code)
    
    def get_schema(self) -> Dict[str, Any]:
        """Return schema for revproc_items table."""
        return {
            "primary_key": ["tax_year", "section", "key"],
            "columns": {
                "tax_year": {"type": "INTEGER", "primary_key": True},
                "section": {"type": "STRING", "primary_key": True},
                "key": {"type": "STRING", "primary_key": True},
                "value": {"type": "STRING"},
                "units": {"type": "STRING"},
                "source_url": {"type": "STRING"},
                "published_date": {"type": "DATE"},
                "revproc_number": {"type": "STRING"},
                "filing_status": {"type": "STRING"},  # For tax brackets
                "income_range_min": {"type": "INTEGER"},  # For tax brackets
                "income_range_max": {"type": "INTEGER"},  # For tax brackets
                "jurisdiction_level": {"type": "STRING"},
                "jurisdiction_code": {"type": "STRING"},
                "_fivetran_synced": {"type": "TIMESTAMP"}
            }
        }
    
    def test_connection(self) -> bool:
        """Test connection by trying to access IRS IRB."""
        try:
            # Test with a known IRB URL
            test_url = "https://www.irs.gov/irb"
            return self.http_client.test_connection(test_url)
        except Exception as e:
            logger.error(f"RevProc connection test failed: {e}")
            return False
    
    def sync(self, cursor: Optional[str] = None) -> Iterator[Operations]:
        """Sync revenue procedure items."""
        logger.info(f"Starting RevProc items sync with cursor: {cursor}")
        
        # Parse cursor date
        cursor_date = self.parse_cursor_date(cursor) if cursor else None
        
        # Yield schema first
        yield self.create_schema_operation("revproc_items", self.get_schema())
        
        # Find recent inflation adjustment Rev. Procs
        revproc_urls = self._find_inflation_revprocs(cursor_date)
        
        latest_date = cursor_date
        
        for revproc_url, revproc_info in revproc_urls.items():
            try:
                logger.info(f"Processing Rev. Proc: {revproc_url}")
                
                items = self._extract_revproc_items(revproc_url, revproc_info)
                
                for item in items:
                    item_date = item.get('published_date')
                    
                    # Track latest date for cursor
                    if not latest_date or (item_date and item_date > latest_date):
                        latest_date = item_date
                    
                    # Yield the record
                    yield self.create_record_operation("revproc_items", item)
                
            except Exception as e:
                logger.error(f"Error processing Rev. Proc {revproc_url}: {e}")
                continue
        
        # Update cursor
        if latest_date:
            self.set_cursor(self.format_date_for_cursor(latest_date))
        
        logger.info("Completed RevProc items sync")
    
    def _find_inflation_revprocs(self, cursor_date: Optional[date] = None) -> Dict[str, Dict[str, Any]]:
        """Find inflation adjustment Revenue Procedures."""
        revproc_urls = {}
        
        # Search in recent IRB bulletins for inflation Rev. Procs
        current_year = datetime.now().year
        years_to_search = [current_year, current_year - 1]
        
        for year in years_to_search:
            try:
                year_revprocs = self._search_year_for_inflation_revprocs(year, cursor_date)
                revproc_urls.update(year_revprocs)
            except Exception as e:
                logger.error(f"Error searching year {year} for Rev. Procs: {e}")
                continue
        
        return revproc_urls
    
    def _search_year_for_inflation_revprocs(self, year: int, cursor_date: Optional[date] = None) -> Dict[str, Dict[str, Any]]:
        """Search a specific year for inflation adjustment Rev. Procs."""
        revprocs = {}
        
        # IRB year index
        irb_year_url = f"https://www.irs.gov/irb/{year}"
        
        try:
            soup = self.http_client.get_soup(irb_year_url)
            
            # Look for links to bulletins (typically October-December for inflation adjustments)
            bulletin_links = soup.find_all('a', href=re.compile(rf'{year}-(4[0-9]|5[0-2])'))  # Weeks 40-52
            
            for link in bulletin_links:
                try:
                    bulletin_url = link['href']
                    if bulletin_url.startswith('/'):
                        bulletin_url = urljoin("https://www.irs.gov", bulletin_url)
                    
                    bulletin_revprocs = self._search_bulletin_for_inflation_revprocs(bulletin_url, year)
                    revprocs.update(bulletin_revprocs)
                    
                except Exception as e:
                    logger.warning(f"Error searching bulletin: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error searching IRB year {year}: {e}")
        
        return revprocs
    
    def _search_bulletin_for_inflation_revprocs(self, bulletin_url: str, year: int) -> Dict[str, Dict[str, Any]]:
        """Search a specific bulletin for inflation Rev. Procs."""
        revprocs = {}
        
        try:
            soup = self.http_client.get_soup(bulletin_url)
            
            # Look for Revenue Procedure links with inflation keywords
            revproc_links = soup.find_all('a', text=re.compile(r'Revenue Procedure.*\d{4}-\d+', re.I))
            
            for link in revproc_links:
                text = link.get_text()
                href = link.get('href')
                
                # Check if this looks like an inflation adjustment Rev. Proc
                if self._is_inflation_revproc(text):
                    if href and href.startswith('/'):
                        href = urljoin("https://www.irs.gov", href)
                    
                    # Extract Rev. Proc number
                    revproc_match = re.search(r'(\d{4}-\d+)', text)
                    revproc_number = revproc_match.group(1) if revproc_match else f"{year}-unknown"
                    
                    # Extract publication date from bulletin
                    published_date = self._extract_bulletin_date(soup)
                    
                    revprocs[href] = {
                        'revproc_number': revproc_number,
                        'published_date': published_date,
                        'title': text.strip()
                    }
        
        except Exception as e:
            logger.error(f"Error searching bulletin {bulletin_url}: {e}")
        
        return revprocs
    
    def _is_inflation_revproc(self, text: str) -> bool:
        """Accept all Rev. Procs - no filtering."""
        return True
    
    def _extract_bulletin_date(self, soup) -> Optional[date]:
        """Extract publication date from bulletin page."""
        # Look for date in various places
        date_elem = soup.find(['time', 'span'], class_=re.compile(r'date'))
        if date_elem:
            return self.parse_date(date_elem.get_text())
        
        # Look for date in title or header
        title = soup.find('title')
        if title:
            date_match = re.search(r'(\w+ \d{1,2}, \d{4})', title.get_text())
            if date_match:
                return self.parse_date(date_match.group(1))
        
        return None
    
    def _extract_revproc_items(self, revproc_url: str, revproc_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract structured items from a Revenue Procedure."""
        items = []
        
        try:
            soup = self.http_client.get_soup(revproc_url)
            
            # Extract tax year from title or content
            tax_year = self._extract_tax_year(soup, revproc_info)
            
            # Extract all content without section filtering
            try:
                # Get all text content from the document
                content = soup.get_text(strip=True)
                
                # Create a single item with all content
                item = {
                    'tax_year': tax_year,
                    'section': 'full_document',
                    'key': 'content',
                    'value': content[:5000],  # Limit content size
                    'data_type': 'text',
                    'source_url': revproc_url,
                    'revproc_number': revproc_info.get('number', ''),
                    'published_date': revproc_info.get('published_date'),
                    'jurisdiction_level': self.jurisdiction_level,
                    'jurisdiction_code': self.jurisdiction_code
                }
                items.append(item)
                
            except Exception as e:
                logger.warning(f"Error extracting content from {revproc_url}: {e}")
        
        except Exception as e:
            logger.error(f"Error extracting items from {revproc_url}: {e}")
        
        return items
    
    def _extract_tax_year(self, soup, revproc_info: Dict[str, Any]) -> int:
        """Extract tax year from Rev. Proc content."""
        # Try to find tax year in title or content
        text = soup.get_text()
        
        # Look for "tax year YYYY" pattern
        year_match = re.search(r'tax year (\d{4})', text, re.I)
        if year_match:
            return int(year_match.group(1))
        
        # Fall back to current year or year from revproc number
        revproc_number = revproc_info.get('revproc_number', '')
        if revproc_number:
            year_match = re.search(r'(\d{4})', revproc_number)
            if year_match:
                return int(year_match.group(1))
        
        return datetime.now().year
    
    # Removed all section-based extraction methods - now using simple content extraction
