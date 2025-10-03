"""
Unit tests for evidence processing functionality
"""

import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import json

from src.province.services.evidence_processor import (
    EvidenceProcessor, 
    ProcessingResult
)
from src.province.services.chronology_generator import (
    ChronologyGenerator, 
    ChronologyEntry, 
    Chronology,
    DateExtraction,
    EventExtraction
)
from src.province.models.document import Document


@pytest.fixture
def sample_document():
    """Create a sample document for testing"""
    return Document(
        document_id="doc_123",
        matter_id="matter_456",
        path="/Evidence/medical_record.pdf",
        filename="medical_record.pdf",
        mime_type="application/pdf",
        size=1024000,
        version="v1",
        created_by="user_789",
        created_at=datetime.now(timezone.utc),
        s3_key="matters/matter_456/Evidence/medical_record.pdf",
        metadata={}
    )


@pytest.fixture
def sample_processing_result():
    """Create a sample processing result"""
    return ProcessingResult(
        document_id="doc_123",
        processing_type="textract_sync",
        status="success",
        extracted_text="Patient visited on January 15, 2024 for routine checkup. Prescribed medication for hypertension.",
        entities=[
            {
                "text": "hypertension",
                "category": "MEDICAL_CONDITION",
                "type": "DX_NAME",
                "score": 0.95
            }
        ],
        metadata={"pages_processed": 1}
    )


class TestEvidenceProcessor:
    """Test cases for EvidenceProcessor"""
    
    @pytest.fixture
    def processor(self):
        """Create EvidenceProcessor instance with mocked AWS clients"""
        with patch('src.province.services.evidence_processor.boto3.client') as mock_boto3, \
             patch('src.province.services.evidence_processor.DocumentService') as mock_doc_service:
            
            # Mock the DocumentService to return a mock instance
            mock_doc_service.return_value = Mock()
            
            processor = EvidenceProcessor()
            processor.textract = Mock()
            processor.transcribe = Mock()
            processor.comprehend_medical = Mock()
            processor.s3 = Mock()
            processor.document_service = Mock()
            return processor
    
    @pytest.mark.asyncio
    async def test_process_pdf_document_sync(self, processor, sample_document):
        """Test processing PDF document with Textract (sync)"""
        # Mock Textract response
        textract_response = {
            'Blocks': [
                {
                    'BlockType': 'LINE',
                    'Text': 'Patient visited on January 15, 2024',
                    'Confidence': 95.5
                },
                {
                    'BlockType': 'LINE', 
                    'Text': 'Prescribed medication for hypertension',
                    'Confidence': 92.3
                }
            ]
        }
        
        processor.textract.detect_document_text.return_value = textract_response
        processor.document_service.update_document_metadata = AsyncMock()
        
        # Test processing
        result = await processor.process_document(sample_document)
        
        # Assertions
        assert result.status == "success"
        assert result.processing_type == "textract_sync"
        assert "Patient visited on January 15, 2024" in result.extracted_text
        assert result.processing_time is not None
        
        # Verify Textract was called correctly
        processor.textract.detect_document_text.assert_called_once()
        call_args = processor.textract.detect_document_text.call_args[1]
        assert call_args['Document']['S3Object']['Name'] == sample_document.s3_key
    
    @pytest.mark.asyncio
    async def test_process_large_pdf_document_async(self, processor, sample_document):
        """Test processing large PDF document with Textract (async)"""
        # Make document large enough to trigger async processing
        sample_document.size = 10 * 1024 * 1024  # 10MB
        
        # Mock async Textract responses
        processor.textract.start_document_text_detection.return_value = {
            'JobId': 'job_123'
        }
        
        processor.textract.get_document_text_detection.return_value = {
            'JobStatus': 'SUCCEEDED',
            'Blocks': [
                {
                    'BlockType': 'LINE',
                    'Text': 'Large document content',
                    'Confidence': 90.0
                }
            ]
        }
        
        processor.document_service.update_document_metadata = AsyncMock()
        
        # Test processing
        result = await processor.process_document(sample_document)
        
        # Assertions
        assert result.status == "success"
        assert result.processing_type == "textract_async"
        assert "Large document content" in result.extracted_text
        assert result.metadata['textract_job_id'] == 'job_123'
    
    @pytest.mark.asyncio
    async def test_process_audio_document(self, processor, sample_document):
        """Test processing audio document with Transcribe"""
        # Change document to audio
        sample_document.mime_type = "audio/mp3"
        sample_document.filename = "interview.mp3"
        
        # Mock Transcribe responses
        processor.transcribe.start_transcription_job.return_value = {
            'TranscriptionJob': {'TranscriptionJobName': 'job_audio_123'}
        }
        
        processor.transcribe.get_transcription_job.return_value = {
            'TranscriptionJob': {
                'TranscriptionJobStatus': 'COMPLETED',
                'Transcript': {
                    'TranscriptFileUri': 'https://s3.amazonaws.com/bucket/transcript.json'
                }
            }
        }
        
        # Mock transcript download
        processor._download_transcript = AsyncMock(return_value="This is the transcribed audio content.")
        processor.document_service.update_document_metadata = AsyncMock()
        
        # Test processing
        result = await processor.process_document(sample_document)
        
        # Assertions
        assert result.status == "success"
        assert result.processing_type == "transcribe"
        assert result.extracted_text == "This is the transcribed audio content."
    
    @pytest.mark.asyncio
    async def test_medical_entity_extraction(self, processor):
        """Test medical entity extraction with Comprehend Medical"""
        text = "Patient has diabetes and hypertension. Prescribed metformin 500mg twice daily."
        
        # Mock Comprehend Medical response
        processor.comprehend_medical.detect_entities_v2.return_value = {
            'Entities': [
                {
                    'Text': 'diabetes',
                    'Category': 'MEDICAL_CONDITION',
                    'Type': 'DX_NAME',
                    'Score': 0.95,
                    'BeginOffset': 12,
                    'EndOffset': 20,
                    'Attributes': [],
                    'Traits': []
                },
                {
                    'Text': 'metformin',
                    'Category': 'MEDICATION',
                    'Type': 'GENERIC_NAME',
                    'Score': 0.98,
                    'BeginOffset': 55,
                    'EndOffset': 64,
                    'Attributes': [],
                    'Traits': []
                }
            ]
        }
        
        # Test entity extraction
        entities = await processor._extract_medical_entities(text)
        
        # Assertions
        assert len(entities) == 2
        assert entities[0]['text'] == 'diabetes'
        assert entities[0]['category'] == 'MEDICAL_CONDITION'
        assert entities[1]['text'] == 'metformin'
        assert entities[1]['category'] == 'MEDICATION'
    
    def test_is_medical_content(self, processor):
        """Test medical content detection heuristic"""
        medical_text = "Patient visited doctor for blood pressure medication prescription"
        non_medical_text = "The contract was signed on January 15th by both parties"
        
        assert processor._is_medical_content(medical_text) == True
        assert processor._is_medical_content(non_medical_text) == False
    
    def test_extract_text_from_textract_response(self, processor):
        """Test text extraction from Textract response"""
        response = {
            'Blocks': [
                {'BlockType': 'LINE', 'Text': 'First line'},
                {'BlockType': 'WORD', 'Text': 'Word'},  # Should be ignored
                {'BlockType': 'LINE', 'Text': 'Second line'},
            ]
        }
        
        text = processor._extract_text_from_textract_response(response)
        assert text == "First line\nSecond line"


class TestChronologyGenerator:
    """Test cases for ChronologyGenerator"""
    
    @pytest.fixture
    def generator(self):
        """Create ChronologyGenerator instance with mocked AWS clients"""
        with patch('boto3.client') as mock_boto3:
            generator = ChronologyGenerator()
            generator.bedrock = Mock()
            generator.s3 = Mock()
            return generator
    
    def test_extract_dates(self, generator):
        """Test date extraction from text"""
        text = "Patient visited on 01/15/2024 and returned on January 20, 2024 for follow-up."
        
        extractions = generator._extract_dates(text)
        
        assert len(extractions) >= 2
        # Check that dates were parsed correctly
        dates = [e.date for e in extractions]
        assert any(d.month == 1 and d.day == 15 and d.year == 2024 for d in dates)
        assert any(d.month == 1 and d.day == 20 and d.year == 2024 for d in dates)
    
    def test_extract_events_near_date(self, generator):
        """Test event extraction near specific dates"""
        text = "On January 15, 2024, patient underwent surgery for appendectomy. Recovery was successful."
        
        date_extraction = DateExtraction(
            date=datetime(2024, 1, 15),
            text_snippet="January 15, 2024",
            confidence=0.9,
            context=text,
            source_position=3
        )
        
        events = generator._extract_events_near_date(text, date_extraction)
        
        assert len(events) > 0
        # Should find medical event
        medical_events = [e for e in events if e.event_type == 'medical']
        assert len(medical_events) > 0
        assert 'surgery' in medical_events[0].event_text.lower()
    
    @pytest.mark.asyncio
    async def test_extract_chronology_entries(self, generator, sample_processing_result):
        """Test chronology entry extraction from processing result"""
        entries = await generator._extract_chronology_entries(sample_processing_result)
        
        assert len(entries) > 0
        # Should extract entry for January 15, 2024
        jan_entries = [e for e in entries if e.date.month == 1 and e.date.day == 15]
        assert len(jan_entries) > 0
        assert jan_entries[0].source_document == "doc_123"
    
    def test_deduplicate_entries(self, generator):
        """Test chronology entry deduplication"""
        entries = [
            ChronologyEntry(
                date=datetime(2024, 1, 15),
                event_type="medical",
                description="Patient visit for checkup",
                source_document="doc_1",
                confidence_score=0.8
            ),
            ChronologyEntry(
                date=datetime(2024, 1, 15),
                event_type="medical", 
                description="Patient visit for routine checkup",  # Similar description
                source_document="doc_2",
                confidence_score=0.9
            ),
            ChronologyEntry(
                date=datetime(2024, 1, 16),
                event_type="medical",
                description="Follow-up appointment",
                source_document="doc_3",
                confidence_score=0.7
            )
        ]
        
        deduplicated = generator._deduplicate_entries(entries)
        
        # Should keep the higher confidence entry and the different date entry
        assert len(deduplicated) == 2
        assert deduplicated[0].confidence_score == 0.9  # Higher confidence kept
        assert deduplicated[1].date.day == 16  # Different date kept
    
    def test_text_similarity(self, generator):
        """Test text similarity calculation"""
        text1 = "Patient visit for checkup"
        text2 = "Patient visit for routine checkup"
        text3 = "Surgery performed successfully"
        
        # Similar texts should have high similarity
        similarity1 = generator._text_similarity(text1, text2)
        assert similarity1 > 0.7
        
        # Different texts should have low similarity
        similarity2 = generator._text_similarity(text1, text3)
        assert similarity2 < 0.3
    
    @pytest.mark.asyncio
    async def test_generate_chronology(self, generator):
        """Test complete chronology generation"""
        processing_results = [
            ProcessingResult(
                document_id="doc_1",
                processing_type="textract_sync",
                status="success",
                extracted_text="Patient visited on January 15, 2024 for surgery.",
                entities=[]
            ),
            ProcessingResult(
                document_id="doc_2", 
                processing_type="textract_sync",
                status="success",
                extracted_text="Follow-up appointment on January 20, 2024 showed good recovery.",
                entities=[]
            )
        ]
        
        # Mock AI enhancement
        generator._enhance_entries_with_ai = AsyncMock(side_effect=lambda x: x)
        generator._save_chronology = AsyncMock()
        
        chronology = await generator.generate_chronology("matter_123", processing_results)
        
        assert chronology.matter_id == "matter_123"
        assert len(chronology.entries) >= 2
        assert chronology.total_documents_processed == 2
        
        # Verify save was called
        generator._save_chronology.assert_called_once()
    
    def test_generate_chronology_markdown(self, generator):
        """Test Markdown chronology generation"""
        chronology = Chronology(
            matter_id="matter_123",
            entries=[
                ChronologyEntry(
                    date=datetime(2024, 1, 15),
                    event_type="medical",
                    description="Patient surgery",
                    source_document="doc_1",
                    confidence_score=0.9
                ),
                ChronologyEntry(
                    date=datetime(2024, 1, 20),
                    event_type="medical",
                    description="Follow-up visit",
                    source_document="doc_2", 
                    confidence_score=0.8
                )
            ],
            generated_at=datetime.now(timezone.utc),
            last_updated=datetime.now(timezone.utc),
            total_documents_processed=2
        )
        
        markdown = generator._generate_chronology_markdown(chronology)
        
        assert "# Chronology for Matter matter_123" in markdown
        assert "January 15, 2024" in markdown
        assert "January 20, 2024" in markdown
        assert "Patient surgery" in markdown
        assert "Follow-up visit" in markdown
        assert "🟢" in markdown  # High confidence indicator


@pytest.mark.asyncio
async def test_integration_evidence_processing_to_chronology():
    """Integration test: process evidence and generate chronology"""
    with patch('boto3.client'):
        processor = EvidenceProcessor()
        generator = ChronologyGenerator()
        
        # Mock all external dependencies
        processor.textract = Mock()
        processor.document_service = Mock()
        processor.document_service.update_document_metadata = AsyncMock()
        
        generator._enhance_entries_with_ai = AsyncMock(side_effect=lambda x: x)
        generator._save_chronology = AsyncMock()
        
        # Mock Textract response
        processor.textract.detect_document_text.return_value = {
            'Blocks': [
                {
                    'BlockType': 'LINE',
                    'Text': 'Medical record from January 15, 2024',
                    'Confidence': 95.0
                },
                {
                    'BlockType': 'LINE',
                    'Text': 'Patient underwent appendectomy surgery',
                    'Confidence': 92.0
                }
            ]
        }
        
        # Create test document
        document = Document(
            document_id="doc_integration",
            matter_id="matter_integration",
            path="/Evidence/medical.pdf",
            filename="medical.pdf",
            mime_type="application/pdf",
            size=500000,
            version="v1",
            created_by="user_test",
            created_at=datetime.now(timezone.utc),
            s3_key="matters/matter_integration/Evidence/medical.pdf",
            metadata={}
        )
        
        # Process document
        result = await processor.process_document(document)
        assert result.status == "success"
        
        # Generate chronology
        chronology = await generator.generate_chronology("matter_integration", [result])
        
        # Verify integration
        assert chronology.matter_id == "matter_integration"
        assert len(chronology.entries) > 0
        
        # Should have extracted medical event from January 15, 2024
        jan_entries = [e for e in chronology.entries if e.date.month == 1 and e.date.day == 15]
        assert len(jan_entries) > 0
        assert any('surgery' in e.description.lower() for e in jan_entries)