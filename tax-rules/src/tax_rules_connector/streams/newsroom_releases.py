"""Newsroom releases stream for IRS announcements and inflation adjustments."""

import logging
import re
import json
from typing import Dict, Any, Iterator, Optional, List
from datetime import datetime, date, timedelta
from urllib.parse import urljoin

from .base import BaseStream

logger = logging.getLogger(__name__)


class NewsroomReleasesStream(BaseStream):
    """Stream for IRS Newsroom releases, focusing on tax rule changes."""
    
    # Keywords that indicate tax rule changes
    RELEVANT_KEYWORDS = [
        'inflation', 'adjustment', 'standard deduction', 'tax bracket',
        'revenue procedure', 'rev proc', 'tax year', 'eitc', 'earned income tax credit',
        'child tax credit', 'ctc', 'additional child tax credit', 'actc',
        'alternative minimum tax', 'amt', 'estate tax', 'gift tax'
    ]
    
    def get_schema(self) -> Dict[str, Any]:
        """Return schema for newsroom_releases table."""
        return {
            "primary_key": ["release_id"],
            "columns": {
                "release_id": {"type": "STRING", "primary_key": True},
                "title": {"type": "STRING"},
                "url": {"type": "STRING"},
                "published_date": {"type": "DATE"},
                "linked_revproc_url": {"type": "STRING"},
                "content_summary": {"type": "STRING"},
                "keywords_matched": {"type": "STRING"},  # JSON array as string
                "jurisdiction_level": {"type": "STRING"},
                "jurisdiction_code": {"type": "STRING"},
                "_extracted_at": {"type": "TIMESTAMP"}
            }
        }
    
    def test_connection(self) -> bool:
        """Test connection to IRS newsroom."""
        try:
            soup = self.http_client.get_soup(self.base_url)
            return soup.title is not None
        except Exception as e:
            logger.error(f"Newsroom connection test failed: {e}")
            return False
    
    def read_records(self, cursor: Optional[str] = None) -> Iterator[Dict[str, Any]]:
        """Read newsroom releases records."""
        logger.info(f"Reading newsroom releases with cursor: {cursor}")
        
        # Parse cursor date
        cursor_date = self.parse_cursor_date(cursor) if cursor else None
        
        # Get releases from multiple pages
        max_pages = 3  # Limit for testing
        page = 0
        latest_date = cursor_date
        
        while page < max_pages:
            try:
                releases = self._get_releases_page(page)
                if not releases:
                    break
                
                found_new_records = False
                
                for release in releases:
                    release_date = release.get('published_date')
                    
                    # Skip if older than cursor
                    if cursor_date and release_date and release_date <= cursor_date:
                        continue
                    
                    found_new_records = True
                    
                    # Track latest date for cursor
                    if not latest_date or (release_date and release_date > latest_date):
                        latest_date = release_date
                    
                    # Add common fields and yield
                    yield self.add_common_fields(release)
                
                # If no new records found, we can stop
                if not found_new_records:
                    break
                
                page += 1
                
            except Exception as e:
                logger.error(f"Error processing newsroom page {page}: {e}")
                break
        
        # Update cursor
        if latest_date:
            self.set_cursor(self.format_date_for_cursor(latest_date))
        
        logger.info(f"Completed newsroom releases read, processed {page} pages")
    
    def parse_cursor_date(self, cursor: Optional[str]) -> Optional[date]:
        """Parse cursor string to date."""
        if not cursor:
            return None
        try:
            return datetime.fromisoformat(cursor.replace('Z', '')).date()
        except:
            return None
    
    def _get_releases_page(self, page: int = 0) -> List[Dict[str, Any]]:
        """Get releases from a specific page."""
        releases = []
        
        # Try recent months that should have data
        months_to_try = [
            ('october', 2024),
            ('september', 2024), 
            ('august', 2024),
            ('july', 2024),
            ('june', 2024),
            ('may', 2024),
            ('december', 2023),
            ('november', 2023),
            ('october', 2023)
        ]
        
        for month, year in months_to_try:
            try:
                archive_url = f"https://www.irs.gov/newsroom/news-releases-for-{month}-{year}"
                
                soup = self.http_client.get_soup(archive_url)
                month_releases = self._parse_monthly_releases(soup, archive_url)
                releases.extend(month_releases)
                
                # Limit total releases per page
                if len(releases) >= 20:
                    return releases[:20]
                        
            except Exception as e:
                logger.debug(f"Could not fetch {archive_url}: {e}")
                continue
        
        return releases
    
    def _parse_monthly_releases(self, soup, archive_url: str) -> List[Dict[str, Any]]:
        """Parse releases from a monthly archive page."""
        releases = []
        
        # Look for IRS announcement links
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            # Skip if not an announcement
            if not text or len(text) < 20:  # Skip very short texts
                continue
            
            # Look for IRS announcements or relevant content
            if not (href.startswith('/newsroom/') and 
                   ('announces' in text.lower() or 
                    'irs' in text.lower() or 
                    any(keyword in text.lower() for keyword in self.RELEVANT_KEYWORDS))):
                continue
            
            # Convert relative URL to absolute
            if href.startswith('/'):
                href = urljoin('https://www.irs.gov', href)
            
            # Extract date from the archive URL
            date_match = re.search(r'(\w+)-(\d{4})', archive_url)
            if date_match:
                month_name, year = date_match.groups()
                # Approximate date - use middle of month
                try:
                    month_num = {
                        'january': 1, 'february': 2, 'march': 3, 'april': 4,
                        'may': 5, 'june': 6, 'july': 7, 'august': 8,
                        'september': 9, 'october': 10, 'november': 11, 'december': 12
                    }[month_name]
                    published_date = date(int(year), month_num, 15)
                except:
                    published_date = date.today()
            else:
                published_date = date.today()
            
            # Create release record
            release = {
                'release_id': self.generate_id(href, text),
                'title': self.clean_text(text),
                'url': href,
                'published_date': published_date,
                'content_summary': self._extract_summary(text),
                'linked_revproc_url': self._find_linked_revproc(text),
                'keywords_matched': json.dumps(self._find_keywords(text)),
                'is_inflation_related': self._is_inflation_related(text),
                'is_tax_year_update': self._is_tax_year_update(text)
            }
            
            releases.append(release)
        
        return releases
    
    def _is_relevant_release(self, text: str) -> bool:
        """Check if a release is relevant to tax rules."""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.RELEVANT_KEYWORDS)
    
    def _extract_summary(self, text: str) -> str:
        """Extract a summary from the release text."""
        # For now, just return the cleaned text
        return self.clean_text(text)[:500]
    
    def _find_linked_revproc(self, text: str) -> Optional[str]:
        """Find linked revenue procedure URL."""
        # Look for Rev. Proc. references
        if 'rev' in text.lower() and 'proc' in text.lower():
            # This would need more sophisticated parsing
            return "https://www.irs.gov/irb"  # Placeholder
        return None
    
    def _find_keywords(self, text: str) -> List[str]:
        """Find matching keywords in the text."""
        text_lower = text.lower()
        return [kw for kw in self.RELEVANT_KEYWORDS if kw in text_lower]
    
    def _is_inflation_related(self, text: str) -> bool:
        """Check if release is related to inflation adjustments."""
        inflation_keywords = ['inflation', 'adjustment', 'standard deduction', 'tax bracket']
        text_lower = text.lower()
        return any(kw in text_lower for kw in inflation_keywords)
    
    def _is_tax_year_update(self, text: str) -> bool:
        """Check if release is a tax year update."""
        return 'tax year' in text.lower() or re.search(r'20\d{2}', text) is not None