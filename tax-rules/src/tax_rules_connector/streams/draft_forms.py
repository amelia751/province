"""Draft forms stream for tracking Form 1040 and instruction changes."""

import logging
import re
from typing import Dict, Any, Iterator, Optional, List
from datetime import datetime, date
from urllib.parse import urljoin

from fivetran_connector_sdk import Operations

from .base import BaseStream

logger = logging.getLogger(__name__)


class DraftFormsStream(BaseStream):
    """Stream for IRS draft and final forms, focusing on Form 1040 series."""
    
    # Removed filtering - now extracting all forms
    
    def get_schema(self) -> Dict[str, Any]:
        """Return schema for draft_forms table."""
        return {
            "primary_key": ["form_number", "revision"],
            "columns": {
                "form_number": {"type": "STRING", "primary_key": True},
                "revision": {"type": "STRING", "primary_key": True},
                "status": {"type": "STRING"},  # draft, final, revised
                "published_date": {"type": "DATE"},
                "url_pdf": {"type": "STRING"},
                "url_instructions": {"type": "STRING"},
                "changes_summary": {"type": "STRING"},
                "tax_year": {"type": "INTEGER"},
                "form_title": {"type": "STRING"},
                "pdf_sha256": {"type": "STRING"},
                "instructions_sha256": {"type": "STRING"},
                "jurisdiction_level": {"type": "STRING"},
                "jurisdiction_code": {"type": "STRING"},
                "_fivetran_synced": {"type": "TIMESTAMP"}
            }
        }
    
    def test_connection(self) -> bool:
        """Test connection to IRS draft forms page."""
        try:
            soup = self.http_client.get_soup(self.base_url)
            # Look for forms-related content
            return bool(soup.find(text=re.compile(r'draft|form|1040', re.I)))
        except Exception as e:
            logger.error(f"Draft forms connection test failed: {e}")
            return False
    
    def sync(self, cursor: Optional[str] = None) -> Iterator[Operations]:
        """Sync draft forms."""
        logger.info(f"Starting draft forms sync with cursor: {cursor}")
        
        # Parse cursor date
        cursor_date = self.parse_cursor_date(cursor) if cursor else None
        
        # Yield schema first
        yield self.create_schema_operation("draft_forms", self.get_schema())
        
        # Get forms from the draft forms page
        forms = self._get_draft_forms(cursor_date)
        
        latest_date = cursor_date
        
        for form in forms:
            form_date = form.get('published_date')
            
            # Skip if older than cursor
            if cursor_date and form_date and form_date <= cursor_date:
                continue
            
            # Track latest date for cursor
            if not latest_date or (form_date and form_date > latest_date):
                latest_date = form_date
            
            # Yield the record
            yield self.create_record_operation("draft_forms", form)
        
        # Update cursor
        if latest_date:
            self.set_cursor(self.format_date_for_cursor(latest_date))
        
        logger.info(f"Completed draft forms sync, processed {len(forms)} forms")
    
    def _get_draft_forms(self, cursor_date: Optional[date] = None) -> List[Dict[str, Any]]:
        """Get draft forms from IRS website."""
        forms = []
        
        try:
            soup = self.http_client.get_soup(self.base_url)
            
            # Look for form sections or tables
            form_sections = soup.find_all(['table', 'div', 'section'], 
                                        class_=re.compile(r'form|draft|table'))
            
            if not form_sections:
                # Fallback: look for any links to forms
                form_sections = [soup]
            
            for section in form_sections:
                section_forms = self._parse_forms_section(section)
                forms.extend(section_forms)
        
        except Exception as e:
            logger.error(f"Error getting draft forms: {e}")
        
        return forms
    
    def _parse_forms_section(self, section) -> List[Dict[str, Any]]:
        """Parse forms from a section of the page."""
        forms = []
        
        # Look for form links or table rows
        form_elements = section.find_all(['tr', 'div', 'li'], 
                                       class_=re.compile(r'form|row|item'))
        
        if not form_elements:
            # Fallback: look for any links that might be forms
            form_elements = section.find_all('a', href=re.compile(r'\.pdf$', re.I))
        
        for element in form_elements:
            try:
                form_data = self._parse_form_element(element)
                if form_data:  # Accept all forms
                    forms.append(form_data)
            except Exception as e:
                logger.warning(f"Error parsing form element: {e}")
                continue
        
        return forms
    
    def _parse_form_element(self, element) -> Optional[Dict[str, Any]]:
        """Parse a single form element."""
        # Look for form number
        text = element.get_text()
        form_number = self._extract_form_number(text)
        
        if not form_number:
            return None
        
        # Look for PDF link
        pdf_link = element.find('a', href=re.compile(r'\.pdf$', re.I))
        if not pdf_link:
            # Maybe the element itself is a link
            if element.name == 'a' and element.get('href', '').endswith('.pdf'):
                pdf_link = element
        
        if not pdf_link:
            return None
        
        pdf_url = pdf_link['href']
        if pdf_url.startswith('/'):
            pdf_url = urljoin(self.base_url, pdf_url)
        
        # Extract form title
        form_title = self._extract_form_title(text, pdf_link.get_text())
        
        # Determine status (draft vs final)
        status = self._determine_form_status(text, pdf_url)
        
        # Extract tax year
        tax_year = self._extract_tax_year(text, pdf_url)
        
        # Create revision identifier
        revision = self._create_revision_id(form_number, tax_year, status)
        
        # Extract publication date
        published_date = self._extract_publication_date(element)
        
        # Look for instructions link
        instructions_url = self._find_instructions_link(element, form_number)
        
        # Get PDF hash
        pdf_sha256 = self._get_pdf_hash(pdf_url)
        instructions_sha256 = self._get_pdf_hash(instructions_url) if instructions_url else None
        
        # Extract changes summary if available
        changes_summary = self._extract_changes_summary(element)
        
        return {
            'form_number': form_number,
            'revision': revision,
            'status': status,
            'published_date': published_date,
            'url_pdf': pdf_url,
            'url_instructions': instructions_url,
            'changes_summary': changes_summary,
            'tax_year': tax_year,
            'form_title': form_title,
            'pdf_sha256': pdf_sha256,
            'instructions_sha256': instructions_sha256,
            'jurisdiction_level': self.jurisdiction_level,
            'jurisdiction_code': self.jurisdiction_code
        }
    
    def _extract_form_number(self, text: str) -> Optional[str]:
        """Extract form number from text."""
        # Look for Form XXXX pattern
        form_match = re.search(r'form\s+(\d{4}(?:-[a-z]+)?)', text, re.I)
        if form_match:
            return form_match.group(1).upper()
        
        # Look for Schedule X pattern
        schedule_match = re.search(r'schedule\s+([a-z]+)', text, re.I)
        if schedule_match:
            return f"SCHEDULE-{schedule_match.group(1).upper()}"
        
        return None
    
    def _extract_form_title(self, text: str, link_text: str) -> str:
        """Extract form title."""
        # Clean up the text
        title = self.clean_text(text or link_text)
        
        # Remove common prefixes/suffixes
        title = re.sub(r'^(form|schedule)\s+\d+[a-z-]*\s*[-:]?\s*', '', title, flags=re.I)
        title = re.sub(r'\s*\(.*?\)\s*$', '', title)  # Remove parenthetical info
        
        return title[:200]  # Limit length
    
    def _determine_form_status(self, text: str, url: str) -> str:
        """Determine if form is draft, final, or revised."""
        text_lower = text.lower()
        url_lower = url.lower()
        
        if 'draft' in text_lower or 'draft' in url_lower:
            return 'draft'
        elif 'revised' in text_lower or 'rev' in url_lower:
            return 'revised'
        else:
            return 'final'
    
    def _extract_tax_year(self, text: str, url: str) -> Optional[int]:
        """Extract tax year from text or URL."""
        # Look for 4-digit year
        year_match = re.search(r'(20\d{2})', text + ' ' + url)
        if year_match:
            return int(year_match.group(1))
        
        # Default to current year
        return datetime.now().year
    
    def _create_revision_id(self, form_number: str, tax_year: Optional[int], status: str) -> str:
        """Create a revision identifier."""
        year_str = str(tax_year) if tax_year else str(datetime.now().year)
        return f"{year_str}_{status}_{datetime.now().strftime('%Y%m%d')}"
    
    def _extract_publication_date(self, element) -> Optional[date]:
        """Extract publication date from element."""
        # Look for date in various formats
        text = element.get_text()
        
        # Common date patterns
        date_patterns = [
            r'(\w+ \d{1,2}, \d{4})',  # January 1, 2024
            r'(\d{1,2}/\d{1,2}/\d{4})',  # 1/1/2024
            r'(\d{4}-\d{2}-\d{2})'  # 2024-01-01
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                parsed_date = self.parse_date(match.group(1))
                if parsed_date:
                    return parsed_date
        
        # Default to today if no date found
        return date.today()
    
    def _find_instructions_link(self, element, form_number: str) -> Optional[str]:
        """Find instructions link for the form."""
        # Look for instructions link near the form
        parent = element.parent
        if parent:
            # Look for "instructions" link
            instr_links = parent.find_all('a', text=re.compile(r'instruction', re.I))
            if instr_links:
                href = instr_links[0]['href']
                if href.startswith('/'):
                    return urljoin(self.base_url, href)
                return href
            
            # Look for PDF with "i" suffix (common pattern)
            instr_pattern = rf'{form_number.lower()}i.*\.pdf'
            instr_links = parent.find_all('a', href=re.compile(instr_pattern, re.I))
            if instr_links:
                href = instr_links[0]['href']
                if href.startswith('/'):
                    return urljoin(self.base_url, href)
                return href
        
        return None
    
    def _get_pdf_hash(self, pdf_url: str) -> Optional[str]:
        """Get SHA256 hash of PDF file."""
        if not pdf_url:
            return None
        
        try:
            metadata = self.http_client.get_pdf_metadata(pdf_url)
            return metadata.get('partial_sha256')
        except Exception as e:
            logger.warning(f"Could not get PDF hash for {pdf_url}: {e}")
            return None
    
    def _extract_changes_summary(self, element) -> Optional[str]:
        """Extract changes summary if available."""
        # Look for change-related text
        text = element.get_text()
        
        # Look for common change indicators
        change_patterns = [
            r'changes?:?\s*([^.]+)',
            r'revised?:?\s*([^.]+)',
            r'updated?:?\s*([^.]+)',
            r'new:?\s*([^.]+)'
        ]
        
        for pattern in change_patterns:
            match = re.search(pattern, text, re.I)
            if match:
                return self.clean_text(match.group(1))[:500]  # Limit length
        
        return None
    
    # Removed form filtering - accepting all forms
