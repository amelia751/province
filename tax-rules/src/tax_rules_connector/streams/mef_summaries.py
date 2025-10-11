"""MeF (Modernized e-File) summaries stream for schema version tracking."""

import logging
import re
from typing import Dict, Any, Iterator, Optional, List
from datetime import datetime, date
from urllib.parse import urljoin

from fivetran_connector_sdk import Operations

from .base import BaseStream

logger = logging.getLogger(__name__)


class MeFSummariesStream(BaseStream):
    """Stream for IRS Modernized e-File schema versions and business rules."""
    
    def get_schema(self) -> Dict[str, Any]:
        """Return schema for mef_summaries table."""
        return {
            "primary_key": ["schema_version"],
            "columns": {
                "schema_version": {"type": "STRING", "primary_key": True},
                "published_date": {"type": "DATE"},
                "url": {"type": "STRING"},
                "notes": {"type": "STRING"},
                "tax_year": {"type": "INTEGER"},
                "form_types": {"type": "STRING"},  # JSON array as string
                "schema_type": {"type": "STRING"},  # business_rules, schema, both
                "version_major": {"type": "INTEGER"},
                "version_minor": {"type": "INTEGER"},
                "version_patch": {"type": "INTEGER"},
                "jurisdiction_level": {"type": "STRING"},
                "jurisdiction_code": {"type": "STRING"},
                "_fivetran_synced": {"type": "TIMESTAMP"}
            }
        }
    
    def test_connection(self) -> bool:
        """Test connection to MeF page."""
        try:
            soup = self.http_client.get_soup(self.base_url)
            # Look for MeF-specific content
            return bool(soup.find(text=re.compile(r'modernized.*e-file|mef|schema', re.I)))
        except Exception as e:
            logger.error(f"MeF connection test failed: {e}")
            return False
    
    def sync(self, cursor: Optional[str] = None) -> Iterator[Operations]:
        """Sync MeF summaries."""
        logger.info(f"Starting MeF summaries sync with cursor: {cursor}")
        
        # Parse cursor date
        cursor_date = self.parse_cursor_date(cursor) if cursor else None
        
        # Yield schema first
        yield self.create_schema_operation("mef_summaries", self.get_schema())
        
        # Get MeF versions
        summaries = self._get_mef_summaries(cursor_date)
        
        latest_date = cursor_date
        
        for summary in summaries:
            summary_date = summary.get('published_date')
            
            # Skip if older than cursor
            if cursor_date and summary_date and summary_date <= cursor_date:
                continue
            
            # Track latest date for cursor
            if not latest_date or (summary_date and summary_date > latest_date):
                latest_date = summary_date
            
            # Yield the record
            yield self.create_record_operation("mef_summaries", summary)
        
        # Update cursor
        if latest_date:
            self.set_cursor(self.format_date_for_cursor(latest_date))
        
        logger.info(f"Completed MeF summaries sync, processed {len(summaries)} summaries")
    
    def _get_mef_summaries(self, cursor_date: Optional[date] = None) -> List[Dict[str, Any]]:
        """Get MeF summaries from IRS website."""
        summaries = []
        
        try:
            soup = self.http_client.get_soup(self.base_url)
            
            # Look for schema/version sections
            version_sections = soup.find_all(['div', 'section', 'table'], 
                                           class_=re.compile(r'version|schema|release'))
            
            if not version_sections:
                # Fallback: look for any links to schemas or business rules
                version_sections = [soup]
            
            for section in version_sections:
                section_summaries = self._parse_mef_section(section)
                summaries.extend(section_summaries)
        
        except Exception as e:
            logger.error(f"Error getting MeF summaries: {e}")
        
        return summaries
    
    def _parse_mef_section(self, section) -> List[Dict[str, Any]]:
        """Parse MeF versions from a section."""
        summaries = []
        
        # Look for version-related elements
        version_elements = section.find_all(['tr', 'div', 'li', 'a'], 
                                          text=re.compile(r'version|v\d+|schema|business.*rule', re.I))
        
        if not version_elements:
            # Look for links to schema files
            version_elements = section.find_all('a', href=re.compile(r'\.xsd$|schema|business.*rule', re.I))
        
        for element in version_elements:
            try:
                summary = self._parse_mef_element(element)
                if summary:
                    summaries.append(summary)
            except Exception as e:
                logger.warning(f"Error parsing MeF element: {e}")
                continue
        
        return summaries
    
    def _parse_mef_element(self, element) -> Optional[Dict[str, Any]]:
        """Parse a single MeF element."""
        text = element.get_text()
        
        # Extract version information
        version_info = self._extract_version_info(text)
        if not version_info:
            return None
        
        schema_version = version_info['version']
        
        # Get URL if element is a link
        url = None
        if element.name == 'a' and element.get('href'):
            url = element['href']
            if url.startswith('/'):
                url = urljoin(self.base_url, url)
        else:
            # Look for nearby link
            link = element.find('a') or element.find_next('a')
            if link and link.get('href'):
                url = link['href']
                if url.startswith('/'):
                    url = urljoin(self.base_url, url)
        
        # Extract tax year
        tax_year = self._extract_tax_year_from_text(text)
        
        # Determine schema type
        schema_type = self._determine_schema_type(text, url or '')
        
        # Extract form types
        form_types = self._extract_form_types(text)
        
        # Extract publication date
        published_date = self._extract_publication_date(element)
        
        # Extract notes
        notes = self._extract_notes(element)
        
        return {
            'schema_version': schema_version,
            'published_date': published_date,
            'url': url,
            'notes': notes,
            'tax_year': tax_year,
            'form_types': form_types,
            'schema_type': schema_type,
            'version_major': version_info.get('major'),
            'version_minor': version_info.get('minor'),
            'version_patch': version_info.get('patch'),
            'jurisdiction_level': self.jurisdiction_level,
            'jurisdiction_code': self.jurisdiction_code
        }
    
    def _extract_version_info(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract version information from text."""
        # Look for version patterns
        version_patterns = [
            r'version\s+(\d+)\.(\d+)\.(\d+)',  # version 1.2.3
            r'version\s+(\d+)\.(\d+)',  # version 1.2
            r'v(\d+)\.(\d+)\.(\d+)',  # v1.2.3
            r'v(\d+)\.(\d+)',  # v1.2
            r'(\d{4})\s*v(\d+)',  # 2024 v1
            r'schema\s+(\d+)\.(\d+)',  # schema 1.2
        ]
        
        for pattern in version_patterns:
            match = re.search(pattern, text, re.I)
            if match:
                groups = match.groups()
                
                if len(groups) == 3:
                    major, minor, patch = groups
                    version = f"{major}.{minor}.{patch}"
                elif len(groups) == 2:
                    if pattern.endswith(r'v(\d+)'):  # Year + version pattern
                        year, version_num = groups
                        version = f"{year}.{version_num}"
                        major, minor, patch = year, version_num, 0
                    else:
                        major, minor = groups
                        patch = 0
                        version = f"{major}.{minor}.{patch}"
                else:
                    continue
                
                return {
                    'version': version,
                    'major': int(major),
                    'minor': int(minor),
                    'patch': int(patch)
                }
        
        return None
    
    def _extract_tax_year_from_text(self, text: str) -> Optional[int]:
        """Extract tax year from text."""
        # Look for tax year or 4-digit year
        year_patterns = [
            r'tax year\s+(\d{4})',
            r'ty\s*(\d{4})',
            r'(20\d{2})'
        ]
        
        for pattern in year_patterns:
            match = re.search(pattern, text, re.I)
            if match:
                year = int(match.group(1))
                if 2000 <= year <= datetime.now().year + 2:  # Reasonable year range
                    return year
        
        return None
    
    def _determine_schema_type(self, text: str, url: str) -> str:
        """Determine type of schema/rules."""
        text_lower = text.lower()
        url_lower = url.lower()
        
        has_schema = 'schema' in text_lower or '.xsd' in url_lower
        has_business_rules = 'business' in text_lower and 'rule' in text_lower
        
        if has_schema and has_business_rules:
            return 'both'
        elif has_business_rules:
            return 'business_rules'
        elif has_schema:
            return 'schema'
        else:
            return 'unknown'
    
    def _extract_form_types(self, text: str) -> str:
        """Extract form types as JSON string."""
        form_types = []
        
        # Look for form numbers
        form_matches = re.findall(r'form\s+(\d{4}[a-z-]*)', text, re.I)
        form_types.extend([f"FORM-{match.upper()}" for match in form_matches])
        
        # Look for schedule references
        schedule_matches = re.findall(r'schedule\s+([a-z]+)', text, re.I)
        form_types.extend([f"SCHEDULE-{match.upper()}" for match in schedule_matches])
        
        # Look for common form series
        if '1040' in text:
            form_types.append('1040-SERIES')
        if '1120' in text:
            form_types.append('1120-SERIES')
        if '1065' in text:
            form_types.append('1065-SERIES')
        
        # Remove duplicates and return as JSON
        import json
        return json.dumps(list(set(form_types)))
    
    def _extract_publication_date(self, element) -> Optional[date]:
        """Extract publication date from element."""
        # Look in element and nearby elements
        search_elements = [element]
        if element.parent:
            search_elements.extend(element.parent.find_all(['span', 'div', 'time'], 
                                                         class_=re.compile(r'date|time')))
        
        for elem in search_elements:
            text = elem.get_text()
            
            # Common date patterns
            date_patterns = [
                r'(\w+ \d{1,2}, \d{4})',  # January 1, 2024
                r'(\d{1,2}/\d{1,2}/\d{4})',  # 1/1/2024
                r'(\d{4}-\d{2}-\d{2})',  # 2024-01-01
                r'updated:?\s*(\w+ \d{1,2}, \d{4})',  # Updated: January 1, 2024
                r'released:?\s*(\w+ \d{1,2}, \d{4})'  # Released: January 1, 2024
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, text, re.I)
                if match:
                    parsed_date = self.parse_date(match.group(1))
                    if parsed_date:
                        return parsed_date
        
        # Default to today if no date found
        return date.today()
    
    def _extract_notes(self, element) -> Optional[str]:
        """Extract notes or description."""
        # Look for descriptive text
        text = element.get_text()
        
        # Look for note-like patterns
        note_patterns = [
            r'note:?\s*([^.]+)',
            r'description:?\s*([^.]+)',
            r'summary:?\s*([^.]+)',
            r'changes?:?\s*([^.]+)'
        ]
        
        for pattern in note_patterns:
            match = re.search(pattern, text, re.I)
            if match:
                return self.clean_text(match.group(1))[:500]  # Limit length
        
        # If no specific note pattern, use cleaned text (limited)
        cleaned = self.clean_text(text)
        if len(cleaned) > 50:  # Only if substantial content
            return cleaned[:500]
        
        return None
