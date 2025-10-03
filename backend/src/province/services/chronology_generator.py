"""
Chronology Generator Service

Automatically generates chronologies from processed evidence documents.
Uses extracted text and entities to identify dates, events, and create
a timeline of relevant activities.
"""

import re
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import json
from collections import defaultdict

import boto3
from dateutil import parser as date_parser

from ..core.config import get_settings
from ..core.exceptions import ProcessingError
from ..models.document import Document
from ..services.evidence_processor import ProcessingResult, ChronologyEntry, Chronology

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class DateExtraction:
    """Extracted date information from text"""
    date: datetime
    text_snippet: str
    confidence: float
    context: str
    source_position: int


@dataclass
class EventExtraction:
    """Extracted event information"""
    event_text: str
    event_type: str
    confidence: float
    entities: List[Dict]
    context: str


class ChronologyGenerator:
    """Service for generating automated chronologies from evidence"""
    
    def __init__(self):
        self.bedrock = boto3.client('bedrock-runtime', region_name=settings.aws_region)
        self.s3 = boto3.client('s3', region_name=settings.aws_region)
        
        # Date patterns for extraction
        self.date_patterns = [
            # MM/DD/YYYY, MM-DD-YYYY
            r'\b(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{4})\b',
            # Month DD, YYYY
            r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})\b',
            # DD Month YYYY
            r'\b(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})\b',
            # YYYY-MM-DD (ISO format)
            r'\b(\d{4})-(\d{1,2})-(\d{1,2})\b',
        ]
        
        # Event type patterns
        self.event_patterns = {
            'medical': [
                r'(appointment|visit|consultation|examination|surgery|procedure|treatment|diagnosis)',
                r'(prescribed|administered|given|took|received)',
                r'(symptoms|pain|injury|condition|illness|disease)'
            ],
            'legal': [
                r'(filed|served|received|signed|executed|notarized)',
                r'(complaint|motion|order|judgment|settlement|agreement)',
                r'(court|hearing|deposition|trial|mediation|arbitration)'
            ],
            'communication': [
                r'(called|emailed|wrote|sent|received|spoke|discussed)',
                r'(letter|email|phone|meeting|conversation|correspondence)'
            ],
            'financial': [
                r'(paid|received|invoiced|billed|charged|cost)',
                r'(payment|bill|invoice|receipt|expense|fee)'
            ]
        }
    
    async def generate_chronology(self, matter_id: str, processing_results: List[ProcessingResult]) -> Chronology:
        """
        Generate a chronology from multiple processed documents
        
        Args:
            matter_id: ID of the matter
            processing_results: List of processing results from evidence documents
            
        Returns:
            Complete chronology for the matter
        """
        try:
            logger.info(f"Generating chronology for matter {matter_id} from {len(processing_results)} documents")
            
            all_entries = []
            
            # Process each document's results
            for result in processing_results:
                if result.status == 'success' and result.extracted_text:
                    entries = await self._extract_chronology_entries(result)
                    all_entries.extend(entries)
            
            # Sort entries by date
            all_entries.sort(key=lambda x: x.date)
            
            # Remove duplicates and merge similar entries
            deduplicated_entries = self._deduplicate_entries(all_entries)
            
            # Enhance entries with AI analysis
            enhanced_entries = await self._enhance_entries_with_ai(deduplicated_entries)
            
            chronology = Chronology(
                matter_id=matter_id,
                entries=enhanced_entries,
                generated_at=datetime.now(timezone.utc),
                last_updated=datetime.now(timezone.utc),
                total_documents_processed=len(processing_results)
            )
            
            # Save chronology to S3
            await self._save_chronology(chronology)
            
            logger.info(f"Generated chronology with {len(enhanced_entries)} entries for matter {matter_id}")
            return chronology
            
        except Exception as e:
            logger.error(f"Error generating chronology for matter {matter_id}: {str(e)}")
            raise ProcessingError(f"Chronology generation failed: {str(e)}")
    
    async def _extract_chronology_entries(self, result: ProcessingResult) -> List[ChronologyEntry]:
        """Extract chronology entries from a single document's processing result"""
        entries = []
        
        if not result.extracted_text:
            return entries
        
        # Extract dates from text
        date_extractions = self._extract_dates(result.extracted_text)
        
        # For each date, try to find associated events
        for date_extraction in date_extractions:
            events = self._extract_events_near_date(
                result.extracted_text, 
                date_extraction
            )
            
            for event in events:
                entry = ChronologyEntry(
                    date=date_extraction.date,
                    event_type=event.event_type,
                    description=event.event_text,
                    source_document=result.document_id,
                    confidence_score=min(date_extraction.confidence, event.confidence),
                    entities=event.entities
                )
                entries.append(entry)
        
        # Also extract events from medical entities if available
        if result.entities:
            medical_entries = self._extract_medical_chronology_entries(result)
            entries.extend(medical_entries)
        
        return entries
    
    def _extract_dates(self, text: str) -> List[DateExtraction]:
        """Extract dates from text using regex patterns"""
        extractions = []
        
        for pattern in self.date_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                try:
                    # Parse the matched date
                    date_str = match.group(0)
                    parsed_date = date_parser.parse(date_str, fuzzy=False)
                    
                    # Get context around the date
                    start = max(0, match.start() - 100)
                    end = min(len(text), match.end() + 100)
                    context = text[start:end].strip()
                    
                    extraction = DateExtraction(
                        date=parsed_date,
                        text_snippet=date_str,
                        confidence=0.8,  # Base confidence for regex matches
                        context=context,
                        source_position=match.start()
                    )
                    extractions.append(extraction)
                    
                except (ValueError, TypeError) as e:
                    logger.debug(f"Failed to parse date '{match.group(0)}': {e}")
                    continue
        
        # Remove duplicates (same date within small text range)
        deduplicated = []
        for extraction in extractions:
            is_duplicate = False
            for existing in deduplicated:
                if (abs((extraction.date - existing.date).days) <= 1 and
                    abs(extraction.source_position - existing.source_position) <= 50):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                deduplicated.append(extraction)
        
        return deduplicated
    
    def _extract_events_near_date(self, text: str, date_extraction: DateExtraction) -> List[EventExtraction]:
        """Extract events that occur near a specific date in the text"""
        events = []
        
        # Define search window around the date
        window_start = max(0, date_extraction.source_position - 200)
        window_end = min(len(text), date_extraction.source_position + 200)
        window_text = text[window_start:window_end]
        
        # Search for event patterns in each category
        for event_type, patterns in self.event_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, window_text, re.IGNORECASE)
                
                for match in matches:
                    # Get sentence containing the event
                    sentence_start = window_text.rfind('.', 0, match.start()) + 1
                    sentence_end = window_text.find('.', match.end())
                    if sentence_end == -1:
                        sentence_end = len(window_text)
                    
                    event_sentence = window_text[sentence_start:sentence_end].strip()
                    
                    if len(event_sentence) > 10:  # Minimum meaningful length
                        event = EventExtraction(
                            event_text=event_sentence,
                            event_type=event_type,
                            confidence=0.7,  # Base confidence for pattern matches
                            entities=[],  # Will be populated later if needed
                            context=window_text
                        )
                        events.append(event)
        
        return events
    
    def _extract_medical_chronology_entries(self, result: ProcessingResult) -> List[ChronologyEntry]:
        """Extract chronology entries from medical entities"""
        entries = []
        
        if not result.entities:
            return entries
        
        # Group medical entities by type
        medical_events = defaultdict(list)
        
        for entity in result.entities:
            if entity.get('category') in ['MEDICAL_CONDITION', 'MEDICATION', 'PROCEDURE']:
                medical_events[entity['category']].append(entity)
        
        # Create chronology entries for medical events
        # Note: Without explicit dates in entities, we'll use document creation date
        # This is a simplified approach - in practice, you'd want more sophisticated date linking
        
        for category, entities in medical_events.items():
            if entities:
                # Create a summary entry for this category
                entity_texts = [e['text'] for e in entities[:5]]  # Limit to top 5
                description = f"{category.replace('_', ' ').title()}: {', '.join(entity_texts)}"
                
                entry = ChronologyEntry(
                    date=datetime.now(timezone.utc),  # Placeholder - would need better date linking
                    event_type='medical',
                    description=description,
                    source_document=result.document_id,
                    confidence_score=0.6,  # Lower confidence without explicit dates
                    entities=entities
                )
                entries.append(entry)
        
        return entries
    
    def _deduplicate_entries(self, entries: List[ChronologyEntry]) -> List[ChronologyEntry]:
        """Remove duplicate chronology entries"""
        deduplicated = []
        
        for entry in entries:
            is_duplicate = False
            
            for existing in deduplicated:
                # Consider entries duplicates if they have the same date and similar descriptions
                if (abs((entry.date - existing.date).days) <= 1 and
                    self._text_similarity(entry.description, existing.description) > 0.8):
                    
                    # Keep the entry with higher confidence
                    if entry.confidence_score > existing.confidence_score:
                        deduplicated.remove(existing)
                        deduplicated.append(entry)
                    
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                deduplicated.append(entry)
        
        return deduplicated
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity based on word overlap"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    async def _enhance_entries_with_ai(self, entries: List[ChronologyEntry]) -> List[ChronologyEntry]:
        """Use AI to enhance and categorize chronology entries"""
        try:
            # Prepare entries for AI analysis
            entries_data = []
            for i, entry in enumerate(entries):
                entries_data.append({
                    'index': i,
                    'date': entry.date.isoformat(),
                    'description': entry.description,
                    'event_type': entry.event_type,
                    'confidence': entry.confidence_score
                })
            
            # Create prompt for AI analysis
            prompt = f"""Analyze the following chronology entries and enhance them by:
1. Improving event descriptions for clarity and legal relevance
2. Categorizing events more precisely
3. Identifying key relationships between events
4. Assigning importance scores (1-10)

Chronology entries:
{json.dumps(entries_data, indent=2)}

Return a JSON response with enhanced entries in the same format, adding:
- enhanced_description: Improved description
- precise_category: More specific category
- importance_score: 1-10 scale
- relationships: List of related entry indices
- legal_significance: Brief note on legal relevance

Focus on medical malpractice, personal injury, and general litigation relevance."""
            
            # Call Bedrock for AI enhancement
            response = self.bedrock.invoke_model(
                modelId='anthropic.claude-3-sonnet-20240229-v1:0',
                body=json.dumps({
                    'anthropic_version': 'bedrock-2023-05-31',
                    'max_tokens': 4000,
                    'messages': [
                        {
                            'role': 'user',
                            'content': prompt
                        }
                    ]
                })
            )
            
            response_body = json.loads(response['body'].read())
            ai_analysis = json.loads(response_body['content'][0]['text'])
            
            # Apply AI enhancements to entries
            enhanced_entries = []
            for entry_data in ai_analysis:
                original_entry = entries[entry_data['index']]
                
                # Create enhanced entry
                enhanced_entry = ChronologyEntry(
                    date=original_entry.date,
                    event_type=entry_data.get('precise_category', original_entry.event_type),
                    description=entry_data.get('enhanced_description', original_entry.description),
                    source_document=original_entry.source_document,
                    page_number=original_entry.page_number,
                    confidence_score=original_entry.confidence_score,
                    entities=original_entry.entities
                )
                
                enhanced_entries.append(enhanced_entry)
            
            return enhanced_entries
            
        except Exception as e:
            logger.warning(f"AI enhancement failed, returning original entries: {e}")
            return entries  # Return original entries if AI enhancement fails
    
    async def _save_chronology(self, chronology: Chronology):
        """Save chronology to S3 as both JSON and Markdown"""
        try:
            # Convert to JSON
            chronology_json = {
                'matter_id': chronology.matter_id,
                'generated_at': chronology.generated_at.isoformat(),
                'last_updated': chronology.last_updated.isoformat(),
                'total_documents_processed': chronology.total_documents_processed,
                'entries': [asdict(entry) for entry in chronology.entries]
            }
            
            # Save JSON version
            json_key = f"matters/{chronology.matter_id}/Evidence/chronology.json"
            self.s3.put_object(
                Bucket=settings.documents_bucket_name,
                Key=json_key,
                Body=json.dumps(chronology_json, indent=2, default=str),
                ContentType='application/json'
            )
            
            # Generate Markdown version
            markdown_content = self._generate_chronology_markdown(chronology)
            
            # Save Markdown version
            md_key = f"matters/{chronology.matter_id}/Evidence/chronology.md"
            self.s3.put_object(
                Bucket=settings.documents_bucket_name,
                Key=md_key,
                Body=markdown_content.encode('utf-8'),
                ContentType='text/markdown'
            )
            
            logger.info(f"Saved chronology for matter {chronology.matter_id} to S3")
            
        except Exception as e:
            logger.error(f"Failed to save chronology: {e}")
            raise ProcessingError(f"Failed to save chronology: {e}")
    
    def _generate_chronology_markdown(self, chronology: Chronology) -> str:
        """Generate a human-readable Markdown chronology"""
        lines = [
            f"# Chronology for Matter {chronology.matter_id}",
            "",
            f"**Generated:** {chronology.generated_at.strftime('%B %d, %Y at %I:%M %p')}",
            f"**Documents Processed:** {chronology.total_documents_processed}",
            f"**Total Events:** {len(chronology.entries)}",
            "",
            "---",
            ""
        ]
        
        # Group entries by date
        entries_by_date = defaultdict(list)
        for entry in chronology.entries:
            date_key = entry.date.strftime('%Y-%m-%d')
            entries_by_date[date_key].append(entry)
        
        # Generate chronology by date
        for date_key in sorted(entries_by_date.keys()):
            date_obj = datetime.strptime(date_key, '%Y-%m-%d')
            lines.append(f"## {date_obj.strftime('%B %d, %Y')}")
            lines.append("")
            
            for entry in entries_by_date[date_key]:
                confidence_indicator = "🟢" if entry.confidence_score > 0.8 else "🟡" if entry.confidence_score > 0.6 else "🔴"
                
                lines.append(f"### {entry.event_type.title()} Event {confidence_indicator}")
                lines.append(f"**Description:** {entry.description}")
                lines.append(f"**Source:** Document {entry.source_document}")
                lines.append(f"**Confidence:** {entry.confidence_score:.2f}")
                
                if entry.entities:
                    lines.append("**Related Entities:**")
                    for entity in entry.entities[:3]:  # Show top 3 entities
                        lines.append(f"- {entity.get('text', 'N/A')} ({entity.get('type', 'Unknown')})")
                
                lines.append("")
        
        lines.extend([
            "---",
            "",
            "*This chronology was automatically generated from evidence documents. Please review for accuracy and completeness.*"
        ])
        
        return "\n".join(lines)
    
    async def update_chronology(self, matter_id: str, new_processing_results: List[ProcessingResult]) -> Chronology:
        """Update existing chronology with new evidence"""
        try:
            # Load existing chronology if it exists
            existing_chronology = await self._load_existing_chronology(matter_id)
            
            # Generate new entries from new documents
            new_entries = []
            for result in new_processing_results:
                if result.status == 'success' and result.extracted_text:
                    entries = await self._extract_chronology_entries(result)
                    new_entries.extend(entries)
            
            # Combine with existing entries
            all_entries = (existing_chronology.entries if existing_chronology else []) + new_entries
            
            # Sort and deduplicate
            all_entries.sort(key=lambda x: x.date)
            deduplicated_entries = self._deduplicate_entries(all_entries)
            
            # Create updated chronology
            updated_chronology = Chronology(
                matter_id=matter_id,
                entries=deduplicated_entries,
                generated_at=existing_chronology.generated_at if existing_chronology else datetime.now(timezone.utc),
                last_updated=datetime.now(timezone.utc),
                total_documents_processed=(existing_chronology.total_documents_processed if existing_chronology else 0) + len(new_processing_results)
            )
            
            # Save updated chronology
            await self._save_chronology(updated_chronology)
            
            return updated_chronology
            
        except Exception as e:
            logger.error(f"Error updating chronology for matter {matter_id}: {str(e)}")
            raise ProcessingError(f"Chronology update failed: {str(e)}")
    
    async def _load_existing_chronology(self, matter_id: str) -> Optional[Chronology]:
        """Load existing chronology from S3"""
        try:
            json_key = f"matters/{matter_id}/Evidence/chronology.json"
            
            response = self.s3.get_object(
                Bucket=settings.documents_bucket_name,
                Key=json_key
            )
            
            chronology_data = json.loads(response['Body'].read().decode('utf-8'))
            
            # Convert back to Chronology object
            entries = []
            for entry_data in chronology_data['entries']:
                entry = ChronologyEntry(
                    date=datetime.fromisoformat(entry_data['date']),
                    event_type=entry_data['event_type'],
                    description=entry_data['description'],
                    source_document=entry_data['source_document'],
                    page_number=entry_data.get('page_number'),
                    confidence_score=entry_data.get('confidence_score', 0.5),
                    entities=entry_data.get('entities', [])
                )
                entries.append(entry)
            
            return Chronology(
                matter_id=chronology_data['matter_id'],
                entries=entries,
                generated_at=datetime.fromisoformat(chronology_data['generated_at']),
                last_updated=datetime.fromisoformat(chronology_data['last_updated']),
                total_documents_processed=chronology_data['total_documents_processed']
            )
            
        except Exception as e:
            logger.debug(f"No existing chronology found for matter {matter_id}: {e}")
            return None