"""Newsroom releases stream for IRS announcements and inflation adjustments."""

import logging
import re
from typing import Dict, Any, Iterator, Optional, List
from datetime import datetime, date, timedelta
from urllib.parse import urljoin

from fivetran_connector_sdk import Operations

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
                "_fivetran_synced": {"type": "TIMESTAMP"}
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
    
    def sync(self, cursor: Optional[str] = None) -> Iterator[Operations]:
        """Sync newsroom releases."""
        logger.info(f"Starting newsroom releases sync with cursor: {cursor}")
        
        # Parse cursor date
        cursor_date = self.parse_cursor_date(cursor) if cursor else None
        
        # Yield schema first
        yield self.create_schema_operation("newsroom_releases", self.get_schema())
        
        # Get releases from multiple pages
        max_pages = 10  # Limit to prevent infinite loops
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
                    
                    # Yield the record
                    yield self.create_record_operation("newsroom_releases", release)
                
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
        
        logger.info(f"Completed newsroom releases sync, processed {page + 1} pages")
    
    def _get_releases_page(self, page: int = 0) -> List[Dict[str, Any]]:
        """Get releases from a specific page."""
        releases = []
        
        # Get releases from monthly archives (more reliable than main page)
        current_year = datetime.now().year
        current_month = datetime.now().month
        
        # Only try months that exist (don't try future months)
        months = ['october', 'september', 'august', 'july', 'june', 'may', 'april', 'march']
        
        for month in months:
            try:
                # Determine which years to try based on current date
                years_to_try = []
                
                # Map month names to numbers
                month_num = {
                    'january': 1, 'february': 2, 'march': 3, 'april': 4,
                    'may': 5, 'june': 6, 'july': 7, 'august': 8,
                    'september': 9, 'october': 10, 'november': 11, 'december': 12
                }[month]
                
                # Only try current year if the month has already passed
                if month_num <= current_month:
                    years_to_try.append(current_year)
                
                # Always try previous year
                years_to_try.append(current_year - 1)
                
                for year in years_to_try:
                    archive_url = f"https://www.irs.gov/newsroom/news-releases-for-{month}-{year}"
                    
                    try:
                        soup = self.http_client.get_soup(archive_url)
                        month_releases = self._parse_monthly_releases(soup, archive_url)
                        releases.extend(month_releases)
                        
                        # Limit total releases per page
                        if len(releases) >= 20:
                            return releases[:20]
                            
                    except Exception as e:
                        logger.debug(f"Could not fetch {archive_url}: {e}")
                        continue
                        
            except Exception as e:
                logger.warning(f"Error processing month {month}: {e}")
                continue
        
        return releases
    
    def _parse_monthly_releases(self, soup, archive_url: str) -> List[Dict[str, Any]]:
        """Parse releases from a monthly archive page."""
        releases = []
        
        # Find all links that look like news releases
        all_links = soup.find_all('a', href=True)
        
        for link in all_links:
            text = link.get_text(strip=True)
            href = link['href']
            
            # Skip if not substantial content or not a newsroom link
            if not text or len(text) < 20 or not href.startswith('/newsroom/'):
                continue
            
            # Convert to full URL
            full_url = 'https://www.irs.gov' + href
            
            try:
                release = self._create_release_record(text, full_url)
                if release:
                    releases.append(release)
            except Exception as e:
                logger.debug(f"Error creating release record: {e}")
                continue
        
        return releases
    
    def _create_release_record(self, title: str, url: str) -> Optional[Dict[str, Any]]:
        """Create a release record and check relevance with Gemini."""
        try:
            # Get the release content
            soup = self.http_client.get_soup(url)
            
            # Extract actual article content (fixed method)
            content = self._extract_actual_content(soup)
            if not content:
                # Fallback to basic extraction
                content_div = soup.find('article')
                if content_div:
                    content = content_div.get_text(strip=True)
                else:
                    content = soup.get_text(strip=True)[:1000]
            
            # For now, include all content without filtering
            # TODO: Add relevance detection later
            
            # Extract publication date
            published_date = self._extract_date_from_content(soup)
            
            # Generate release ID
            release_id = url.split('/')[-1] or str(hash(url))
            
            return {
                'release_id': release_id,
                'title': title,
                'url': url,
                'published_date': published_date,
                'linked_revproc_url': self._extract_revproc_link_from_content(soup),
                'content_summary': content[:500],  # First 500 chars
                'content_type': 'newsroom_release',
                'jurisdiction_level': self.jurisdiction_level,
                'jurisdiction_code': self.jurisdiction_code
            }
            
        except Exception as e:
            logger.error(f"Error creating release record for {url}: {e}")
            return None
    
    def _extract_date_from_content(self, soup) -> Optional[date]:
        """Extract publication date from release content."""
        # Look for date patterns in the content
        text = soup.get_text()
        
        # Common IRS date patterns
        date_patterns = [
            r'(\w+ \d{1,2}, \d{4})',  # January 1, 2024
            r'(\d{1,2}/\d{1,2}/\d{4})',  # 1/1/2024
            r'(\d{4}-\d{2}-\d{2})'  # 2024-01-01
        ]
        
        current_year = datetime.now().year
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                parsed_date = self.parse_date(match)
                # Only accept reasonable dates (not future dates beyond next year)
                if (parsed_date and 
                    2020 <= parsed_date.year <= current_year + 1 and
                    parsed_date <= date.today() + timedelta(days=365)):
                    return parsed_date
        
        # Default to today if no date found
        return date.today()
    
    def _extract_revproc_link_from_content(self, soup) -> Optional[str]:
        """Extract revenue procedure link from release content."""
        links = soup.find_all('a', href=True)
        
        for link in links:
            href = link['href']
            text = link.get_text().lower()
            
            # Check for revenue procedure indicators
            if any(indicator in text for indicator in ['rev proc', 'revenue procedure']):
                if href.startswith('/'):
                    return 'https://www.irs.gov' + href
                return href
            
            # Check URL patterns
            if '/irb/' in href or 'revenue-procedure' in href:
                if href.startswith('/'):
                    return 'https://www.irs.gov' + href
                return href
        
        return None
    
    def _extract_actual_content(self, soup):
        """Extract actual article content from IRS page."""
        
        # Try selectors in order of preference
        content_selectors = [
            'article',  # Main article content
            'div.field-item',
            'main',
            'div[class*="field-items"]',
            'div.content-area',
            'div.node-content'
        ]
        
        for selector in content_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                # Look for substantial content (not just navigation)
                if (len(text) > 300 and 
                    'official website' not in text.lower()[:100] and
                    'skip to main content' not in text.lower()[:100]):
                    return ' '.join(text.split())  # Clean whitespace
        
        # Fallback: look for paragraphs with substantial content
        paragraphs = soup.find_all('p')
        substantial_content = []
        
        for p in paragraphs:
            text = p.get_text(strip=True)
            if (len(text) > 50 and 
                'official website' not in text.lower() and
                'skip to main' not in text.lower() and
                '.gov website' not in text.lower()):
                substantial_content.append(text)
        
        if substantial_content:
            return ' '.join(substantial_content)
        
        return ""
    
    def _parse_release_item(self, item) -> Optional[Dict[str, Any]]:
        """Parse a single release item from HTML."""
        # Find title and link
        title_elem = item.find(['h1', 'h2', 'h3', 'h4', 'a'])
        if not title_elem:
            return None
        
        title = self.clean_text(title_elem.get_text())
        if not title:
            return None
        
        # Get URL
        link_elem = title_elem if title_elem.name == 'a' else item.find('a')
        if not link_elem or not link_elem.get('href'):
            return None
        
        url = link_elem['href']
        if url.startswith('/'):
            url = urljoin(self.base_url, url)
        
        # Extract date (look for various date patterns)
        date_elem = item.find(['time', 'span'], class_=re.compile(r'date|time'))
        published_date = None
        
        if date_elem:
            date_text = date_elem.get_text(strip=True)
            published_date = self.parse_date(date_text)
        
        # If no date element found, try to extract from text
        if not published_date:
            date_match = re.search(r'(\w+ \d{1,2}, \d{4})', item.get_text())
            if date_match:
                published_date = self.parse_date(date_match.group(1))
        
        # Generate release ID from URL
        release_id = url.split('/')[-1] or str(hash(url))
        
        # Get content summary
        content_elem = item.find(['p', 'div'], class_=re.compile(r'summary|excerpt|content'))
        content_summary = ""
        if content_elem:
            content_summary = self.clean_text(content_elem.get_text())
        
        # Look for linked revenue procedure URLs in the content
        linked_revproc_url = self._extract_revproc_link(item)
        
        return {
            'release_id': release_id,
            'title': title,
            'url': url,
            'published_date': published_date,
            'linked_revproc_url': linked_revproc_url,
            'content_summary': content_summary[:1000],  # Limit length
            'keywords_matched': self._get_matched_keywords(title + " " + content_summary),
            'jurisdiction_level': self.jurisdiction_level,
            'jurisdiction_code': self.jurisdiction_code
        }
    
    def _extract_revproc_link(self, item) -> Optional[str]:
        """Extract revenue procedure link from release content."""
        # Look for links to IRB or revenue procedures
        links = item.find_all('a', href=True)
        
        for link in links:
            href = link['href']
            text = link.get_text().lower()
            
            # Check if this looks like a revenue procedure link
            if ('rev' in text and 'proc' in text) or 'revenue procedure' in text:
                if href.startswith('/'):
                    href = urljoin(self.base_url, href)
                return href
            
            # Check if URL contains IRB patterns
            if '/irb/' in href or 'bulletin' in href:
                if href.startswith('/'):
                    href = urljoin(self.base_url, href)
                return href
        
        return None
    
    def _is_relevant_release(self, release: Dict[str, Any]) -> bool:
        """Check if a release is relevant to tax rules."""
        text = f"{release.get('title', '')} {release.get('content_summary', '')}"
        return self.is_relevant_content(text, self.RELEVANT_KEYWORDS)
    
    def _get_matched_keywords(self, text: str) -> str:
        """Get list of matched keywords as JSON string."""
        if not text:
            return "[]"
        
        text_lower = text.lower()
        matched = [kw for kw in self.RELEVANT_KEYWORDS if kw.lower() in text_lower]
        
        # Return as JSON string for BigQuery compatibility
        import json
        return json.dumps(matched)
