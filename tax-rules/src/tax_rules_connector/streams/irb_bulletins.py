"""IRB (Internal Revenue Bulletin) stream for official tax publications."""

import logging
import re
from typing import Dict, Any, Iterator, Optional, List
from datetime import datetime, date
from urllib.parse import urljoin

from fivetran_connector_sdk import Operations

from .base import BaseStream

logger = logging.getLogger(__name__)


class IRBBulletinsStream(BaseStream):
    """Stream for Internal Revenue Bulletin index and documents."""
    
    def get_schema(self) -> Dict[str, Any]:
        """Return schema for irb_bulletins table."""
        return {
            "primary_key": ["bulletin_no", "doc_number"],
            "columns": {
                "bulletin_no": {"type": "STRING", "primary_key": True},
                "published_date": {"type": "DATE"},
                "doc_type": {"type": "STRING"},
                "doc_number": {"type": "STRING", "primary_key": True},
                "title": {"type": "STRING"},
                "url_html": {"type": "STRING"},
                "url_pdf": {"type": "STRING"},
                "sha256": {"type": "STRING"},
                "content_length": {"type": "INTEGER"},
                "jurisdiction_level": {"type": "STRING"},
                "jurisdiction_code": {"type": "STRING"},
                "_fivetran_synced": {"type": "TIMESTAMP"}
            }
        }
    
    def test_connection(self) -> bool:
        """Test connection to IRB index."""
        try:
            soup = self.http_client.get_soup(self.base_url)
            # Look for IRB-specific content
            return bool(soup.find(text=re.compile(r'Internal Revenue Bulletin|IRB')))
        except Exception as e:
            logger.error(f"IRB connection test failed: {e}")
            return False
    
    def sync(self, cursor: Optional[str] = None) -> Iterator[Operations]:
        """Sync IRB bulletins."""
        logger.info(f"Starting IRB bulletins sync with cursor: {cursor}")
        
        # Parse cursor (format: "YYYY-MM-DD" for published_date)
        cursor_date = self.parse_cursor_date(cursor) if cursor else None
        
        # Yield schema first
        yield self.create_schema_operation("irb_bulletins", self.get_schema())
        
        # Get current year and previous year bulletins
        current_year = datetime.now().year
        years_to_process = [current_year, current_year - 1]
        
        latest_date = cursor_date
        
        for year in years_to_process:
            try:
                bulletins = self._get_bulletins_for_year(year, cursor_date)
                
                for bulletin in bulletins:
                    bulletin_date = bulletin.get('published_date')
                    
                    # Track latest date for cursor
                    if not latest_date or (bulletin_date and bulletin_date > latest_date):
                        latest_date = bulletin_date
                    
                    # Yield the record
                    yield self.create_record_operation("irb_bulletins", bulletin)
                
            except Exception as e:
                logger.error(f"Error processing IRB bulletins for year {year}: {e}")
                continue
        
        # Update cursor
        if latest_date:
            self.set_cursor(self.format_date_for_cursor(latest_date))
        
        logger.info("Completed IRB bulletins sync")
    
    def _get_bulletins_for_year(self, year: int, cursor_date: Optional[date] = None) -> List[Dict[str, Any]]:
        """Get all bulletins for a specific year."""
        bulletins = []
        
        # IRB year index URL (adjust based on actual IRS URL structure)
        year_url = f"{self.base_url}/{year}"
        
        try:
            soup = self.http_client.get_soup(year_url)
            
            # Look for bulletin links (adjust selectors based on actual HTML)
            bulletin_links = soup.find_all('a', href=re.compile(rf'{year}-\d+'))
            
            for link in bulletin_links:
                try:
                    bulletin_data = self._parse_bulletin_link(link, year)
                    if bulletin_data:
                        # Skip if older than cursor
                        if cursor_date and bulletin_data.get('published_date'):
                            if bulletin_data['published_date'] <= cursor_date:
                                continue
                        
                        # Get detailed bulletin content
                        detailed_bulletins = self._get_bulletin_details(bulletin_data)
                        bulletins.extend(detailed_bulletins)
                        
                except Exception as e:
                    logger.warning(f"Error processing bulletin link: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error fetching IRB year index for {year}: {e}")
        
        return bulletins
    
    def _parse_bulletin_link(self, link, year: int) -> Optional[Dict[str, Any]]:
        """Parse a bulletin link from the year index."""
        href = link.get('href')
        text = link.get_text(strip=True)
        
        if not href:
            return None
        
        # Extract bulletin number (e.g., "2024-44")
        bulletin_match = re.search(rf'({year}-\d+)', href)
        if not bulletin_match:
            return None
        
        bulletin_no = bulletin_match.group(1)
        
        # Convert relative URL to absolute
        if href.startswith('/'):
            href = urljoin(self.base_url, href)
        
        # Try to extract date from text or bulletin number
        published_date = self._extract_bulletin_date(text, bulletin_no)
        
        return {
            'bulletin_no': bulletin_no,
            'url': href,
            'title': text,
            'published_date': published_date
        }
    
    def _extract_bulletin_date(self, text: str, bulletin_no: str) -> Optional[date]:
        """Extract publication date from bulletin text or number."""
        # Try to parse date from text first
        date_match = re.search(r'(\w+ \d{1,2}, \d{4})', text)
        if date_match:
            return self.parse_date(date_match.group(1))
        
        # Estimate date from bulletin number (IRB is published weekly)
        # This is approximate - you might want to maintain a mapping
        try:
            year, week = bulletin_no.split('-')
            year = int(year)
            week = int(week)
            
            # Approximate: first bulletin of year is first Monday of January
            from datetime import timedelta
            jan_1 = date(year, 1, 1)
            days_to_monday = (7 - jan_1.weekday()) % 7
            first_monday = jan_1 + timedelta(days=days_to_monday)
            
            # Add weeks
            estimated_date = first_monday + timedelta(weeks=week - 1)
            return estimated_date
            
        except Exception:
            return None
    
    def _get_bulletin_details(self, bulletin_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get detailed content from a specific bulletin."""
        bulletin_url = bulletin_data['url']
        bulletin_no = bulletin_data['bulletin_no']
        published_date = bulletin_data['published_date']
        
        documents = []
        
        try:
            soup = self.http_client.get_soup(bulletin_url)
            
            # Look for document sections in the bulletin
            # IRB typically has sections like "Revenue Rulings", "Revenue Procedures", etc.
            doc_sections = soup.find_all(['div', 'section'], class_=re.compile(r'document|ruling|procedure'))
            
            if not doc_sections:
                # Fallback: look for any links to documents
                doc_sections = [soup]
            
            for section in doc_sections:
                section_docs = self._parse_bulletin_section(section, bulletin_no, published_date)
                documents.extend(section_docs)
        
        except Exception as e:
            logger.error(f"Error getting bulletin details for {bulletin_no}: {e}")
        
        return documents
    
    def _parse_bulletin_section(self, section, bulletin_no: str, published_date: Optional[date]) -> List[Dict[str, Any]]:
        """Parse documents from a bulletin section."""
        documents = []
        
        # Look for document links
        doc_links = section.find_all('a', href=True)
        
        for link in doc_links:
            href = link['href']
            text = link.get_text(strip=True)
            
            # Skip if not a document link
            if not self._is_document_link(href, text):
                continue
            
            # Convert relative URL
            if href.startswith('/'):
                href = urljoin(self.base_url, href)
            
            # Generate simple document ID
            doc_number = f"{bulletin_no}_{len(documents) + 1}"
            
            # Get PDF URL if available
            pdf_url = self._find_pdf_url(link, href)
            
            # Calculate hash for PDF if available
            sha256 = None
            content_length = None
            
            if pdf_url:
                try:
                    pdf_metadata = self.http_client.get_pdf_metadata(pdf_url)
                    sha256 = pdf_metadata.get('partial_sha256')
                    content_length = pdf_metadata.get('content_length')
                    if content_length:
                        content_length = int(content_length)
                except Exception as e:
                    logger.warning(f"Could not get PDF metadata for {pdf_url}: {e}")
            
            document = {
                'bulletin_no': bulletin_no,
                'published_date': published_date,
                'doc_type': 'irb_document',
                'doc_number': doc_number,
                'title': text,
                'url_html': href,
                'url_pdf': pdf_url,
                'sha256': sha256,
                'content_length': content_length,
                'jurisdiction_level': self.jurisdiction_level,
                'jurisdiction_code': self.jurisdiction_code
            }
            
            documents.append(document)
        
        return documents
    
    def _is_document_link(self, href: str, text: str) -> bool:
        """Check if a link is to a tax document."""
        text_lower = text.lower()
        href_lower = href.lower()
        
        # Look for document type indicators
        doc_indicators = [
            'revenue ruling', 'rev rul', 'revenue procedure', 'rev proc',
            'notice', 'announcement', 'temporary regulation', 'proposed regulation',
            'treasury decision', 'td', 'private letter ruling', 'plr'
        ]
        
        return any(indicator in text_lower or indicator in href_lower for indicator in doc_indicators)
    
    def _find_pdf_url(self, link_elem, html_url: str) -> Optional[str]:
        """Find PDF URL for a document."""
        # Look for PDF link near the HTML link
        parent = link_elem.parent
        if parent:
            pdf_links = parent.find_all('a', href=re.compile(r'\.pdf$', re.I))
            if pdf_links:
                pdf_href = pdf_links[0]['href']
                if pdf_href.startswith('/'):
                    return urljoin(self.base_url, pdf_href)
                return pdf_href
        
        # Try to construct PDF URL from HTML URL
        if html_url.endswith('.html'):
            return html_url.replace('.html', '.pdf')
        
        return None
