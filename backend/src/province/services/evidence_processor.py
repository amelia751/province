"""
Evidence Processing Service

Handles automated processing of evidence documents including:
- OCR processing with Textract
- Audio transcription with Transcribe
- Medical entity extraction with Comprehend Medical
- Automated chronology generation
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import boto3
from botocore.exceptions import ClientError

from ..core.config import get_settings
from ..core.exceptions import ProcessingError, ValidationError
from ..models.document import Document
from ..services.document import DocumentService

logger = logging.getLogger(__name__)
# settings = get_settings()  # Moved to function calls to avoid import-time errors


@dataclass
class ProcessingResult:
    """Result of evidence processing operation"""
    document_id: str
    processing_type: str
    status: str  # "success", "failed", "partial"
    extracted_text: Optional[str] = None
    entities: Optional[List[Dict]] = None
    metadata: Optional[Dict] = None
    error_message: Optional[str] = None
    processing_time: Optional[float] = None


@dataclass
class ChronologyEntry:
    """Single entry in an automated chronology"""
    date: datetime
    event_type: str
    description: str
    source_document: str
    page_number: Optional[int] = None
    confidence_score: Optional[float] = None
    entities: Optional[List[Dict]] = None


@dataclass
class Chronology:
    """Complete chronology for a matter"""
    matter_id: str
    entries: List[ChronologyEntry]
    generated_at: datetime
    last_updated: datetime
    total_documents_processed: int


class EvidenceProcessor:
    """Service for processing evidence documents and generating insights"""
    
    def __init__(self):
        settings = get_settings()
        aws_region = getattr(settings, 'aws_region', 'us-east-1')  # Default fallback
        self.textract = boto3.client('textract', region_name=aws_region)
        self.transcribe = boto3.client('transcribe', region_name=aws_region)
        self.comprehend_medical = boto3.client('comprehendmedical', region_name=aws_region)
        self.s3 = boto3.client('s3', region_name=aws_region)
        self.document_service = DocumentService()
        
    async def process_document(self, document: Document, processing_options: Dict[str, Any] = None) -> ProcessingResult:
        """
        Process a single evidence document based on its type
        
        Args:
            document: Document to process
            processing_options: Optional processing configuration
            
        Returns:
            ProcessingResult with extracted information
        """
        start_time = datetime.now()
        
        try:
            # Determine processing type based on document MIME type
            if document.mime_type.startswith('image/') or document.mime_type == 'application/pdf':
                result = await self._process_with_textract(document, processing_options)
            elif document.mime_type.startswith('audio/'):
                result = await self._process_with_transcribe(document, processing_options)
            elif document.mime_type.startswith('video/'):
                result = await self._process_video_with_transcribe(document, processing_options)
            else:
                # For text documents, extract text directly
                result = await self._process_text_document(document, processing_options)
                
            # If this appears to be medical content, run Comprehend Medical
            if result.extracted_text and self._is_medical_content(result.extracted_text):
                medical_entities = await self._extract_medical_entities(result.extracted_text)
                if result.entities:
                    result.entities.extend(medical_entities)
                else:
                    result.entities = medical_entities
                    
            result.processing_time = (datetime.now() - start_time).total_seconds()
            
            # Store processing results as metadata
            await self._store_processing_results(document, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing document {document.document_id}: {str(e)}")
            return ProcessingResult(
                document_id=document.document_id,
                processing_type="error",
                status="failed",
                error_message=str(e),
                processing_time=(datetime.now() - start_time).total_seconds()
            )
    
    async def _process_with_textract(self, document: Document, options: Dict = None) -> ProcessingResult:
        """Process document using AWS Textract for OCR"""
        try:
            # For large documents, use async job processing
            if document.size > 5 * 1024 * 1024:  # 5MB threshold
                return await self._process_textract_async(document, options)
            else:
                return await self._process_textract_sync(document, options)
                
        except ClientError as e:
            raise ProcessingError(f"Textract processing failed: {e}")
    
    async def _process_textract_sync(self, document: Document, options: Dict = None) -> ProcessingResult:
        """Process document synchronously with Textract"""
        try:
            # Get document from S3
            s3_object = {
                'Bucket': getattr(get_settings(), 'documents_bucket_name', 'default-bucket'),
                'Name': document.s3_key
            }
            
            # Detect document text
            response = self.textract.detect_document_text(
                Document={'S3Object': s3_object}
            )
            
            # Extract text and metadata
            extracted_text = self._extract_text_from_textract_response(response)
            
            # Extract additional entities if requested
            entities = []
            if options and options.get('extract_entities', True):
                entities = self._extract_entities_from_textract_response(response)
            
            return ProcessingResult(
                document_id=document.document_id,
                processing_type="textract_sync",
                status="success",
                extracted_text=extracted_text,
                entities=entities,
                metadata={
                    'textract_job_id': None,
                    'pages_processed': len(response.get('Blocks', [])),
                    'confidence_scores': self._calculate_confidence_scores(response)
                }
            )
            
        except ClientError as e:
            logger.error(f"Textract sync processing failed: {e}")
            raise ProcessingError(f"Textract processing failed: {e}")
    
    async def _process_textract_async(self, document: Document, options: Dict = None) -> ProcessingResult:
        """Process large document asynchronously with Textract"""
        try:
            # Start async job
            response = self.textract.start_document_text_detection(
                DocumentLocation={
                    'S3Object': {
                        'Bucket': getattr(get_settings(), 'documents_bucket_name', 'default-bucket'),
                        'Name': document.s3_key
                    }
                },
                JobTag=f"evidence_processing_{document.document_id}"
            )
            
            job_id = response['JobId']
            
            # Poll for completion
            max_attempts = 60  # 5 minutes max wait
            attempt = 0
            
            while attempt < max_attempts:
                result = self.textract.get_document_text_detection(JobId=job_id)
                status = result['JobStatus']
                
                if status == 'SUCCEEDED':
                    extracted_text = self._extract_text_from_textract_response(result)
                    entities = []
                    
                    if options and options.get('extract_entities', True):
                        entities = self._extract_entities_from_textract_response(result)
                    
                    return ProcessingResult(
                        document_id=document.document_id,
                        processing_type="textract_async",
                        status="success",
                        extracted_text=extracted_text,
                        entities=entities,
                        metadata={
                            'textract_job_id': job_id,
                            'pages_processed': len(result.get('Blocks', [])),
                            'confidence_scores': self._calculate_confidence_scores(result)
                        }
                    )
                elif status == 'FAILED':
                    raise ProcessingError(f"Textract job failed: {result.get('StatusMessage', 'Unknown error')}")
                
                await asyncio.sleep(5)  # Wait 5 seconds before next check
                attempt += 1
            
            raise ProcessingError("Textract job timed out")
            
        except ClientError as e:
            logger.error(f"Textract async processing failed: {e}")
            raise ProcessingError(f"Textract processing failed: {e}")
    
    async def _process_with_transcribe(self, document: Document, options: Dict = None) -> ProcessingResult:
        """Process audio document using AWS Transcribe"""
        try:
            job_name = f"evidence_transcribe_{document.document_id}_{int(datetime.now().timestamp())}"
            
            # Start transcription job
            response = self.transcribe.start_transcription_job(
                TranscriptionJobName=job_name,
                Media={
                    'MediaFileUri': f"s3://{getattr(get_settings(), 'documents_bucket_name', 'default-bucket')}/{document.s3_key}"
                },
                MediaFormat=self._get_audio_format(document.mime_type),
                LanguageCode='en-US',  # Could be configurable
                Settings={
                    'ShowSpeakerLabels': True,
                    'MaxSpeakerLabels': 10,
                    'ShowAlternatives': True,
                    'MaxAlternatives': 3
                }
            )
            
            # Poll for completion
            max_attempts = 120  # 10 minutes max wait for audio
            attempt = 0
            
            while attempt < max_attempts:
                result = self.transcribe.get_transcription_job(
                    TranscriptionJobName=job_name
                )
                
                status = result['TranscriptionJob']['TranscriptionJobStatus']
                
                if status == 'COMPLETED':
                    # Get transcript from S3
                    transcript_uri = result['TranscriptionJob']['Transcript']['TranscriptFileUri']
                    transcript_text = await self._download_transcript(transcript_uri)
                    
                    return ProcessingResult(
                        document_id=document.document_id,
                        processing_type="transcribe",
                        status="success",
                        extracted_text=transcript_text,
                        metadata={
                            'transcribe_job_name': job_name,
                            'transcript_uri': transcript_uri,
                            'media_format': self._get_audio_format(document.mime_type),
                            'language_code': 'en-US'
                        }
                    )
                elif status == 'FAILED':
                    failure_reason = result['TranscriptionJob'].get('FailureReason', 'Unknown error')
                    raise ProcessingError(f"Transcribe job failed: {failure_reason}")
                
                await asyncio.sleep(5)
                attempt += 1
            
            raise ProcessingError("Transcribe job timed out")
            
        except ClientError as e:
            logger.error(f"Transcribe processing failed: {e}")
            raise ProcessingError(f"Transcribe processing failed: {e}")
    
    async def _process_video_with_transcribe(self, document: Document, options: Dict = None) -> ProcessingResult:
        """Process video document using AWS Transcribe (audio extraction)"""
        # Similar to audio processing but with video-specific settings
        return await self._process_with_transcribe(document, options)
    
    async def _process_text_document(self, document: Document, options: Dict = None) -> ProcessingResult:
        """Process plain text documents"""
        try:
            # Download document content from S3
            response = self.s3.get_object(
                Bucket=getattr(get_settings(), 'documents_bucket_name', 'default-bucket'),
                Key=document.s3_key
            )
            
            content = response['Body'].read()
            
            # Decode based on document type
            if document.mime_type == 'application/json':
                text_content = json.loads(content.decode('utf-8'))
                extracted_text = json.dumps(text_content, indent=2)
            else:
                extracted_text = content.decode('utf-8')
            
            return ProcessingResult(
                document_id=document.document_id,
                processing_type="text_extraction",
                status="success",
                extracted_text=extracted_text,
                metadata={
                    'original_size': len(content),
                    'encoding': 'utf-8'
                }
            )
            
        except Exception as e:
            logger.error(f"Text document processing failed: {e}")
            raise ProcessingError(f"Text processing failed: {e}")
    
    async def _extract_medical_entities(self, text: str) -> List[Dict]:
        """Extract medical entities using Comprehend Medical"""
        try:
            entities = []
            
            # Process text in chunks (Comprehend Medical has size limits)
            chunk_size = 20000  # 20KB chunks
            text_chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
            
            for chunk in text_chunks:
                # Detect entities
                response = self.comprehend_medical.detect_entities_v2(Text=chunk)
                
                for entity in response.get('Entities', []):
                    entities.append({
                        'text': entity['Text'],
                        'category': entity['Category'],
                        'type': entity['Type'],
                        'score': entity['Score'],
                        'begin_offset': entity['BeginOffset'],
                        'end_offset': entity['EndOffset'],
                        'attributes': entity.get('Attributes', []),
                        'traits': entity.get('Traits', [])
                    })
            
            return entities
            
        except ClientError as e:
            logger.error(f"Comprehend Medical processing failed: {e}")
            return []  # Return empty list on failure, don't break the pipeline
    
    def _is_medical_content(self, text: str) -> bool:
        """Heuristic to determine if content is medical-related"""
        medical_keywords = [
            'patient', 'diagnosis', 'treatment', 'medication', 'doctor', 'physician',
            'hospital', 'medical', 'clinical', 'symptoms', 'condition', 'therapy',
            'prescription', 'dosage', 'mg', 'ml', 'blood pressure', 'heart rate'
        ]
        
        text_lower = text.lower()
        medical_count = sum(1 for keyword in medical_keywords if keyword in text_lower)
        
        # If more than 3 medical keywords found, consider it medical content
        return medical_count >= 3
    
    def _extract_text_from_textract_response(self, response: Dict) -> str:
        """Extract plain text from Textract response"""
        text_lines = []
        
        for block in response.get('Blocks', []):
            if block['BlockType'] == 'LINE':
                text_lines.append(block['Text'])
        
        return '\n'.join(text_lines)
    
    def _extract_entities_from_textract_response(self, response: Dict) -> List[Dict]:
        """Extract structured entities from Textract response"""
        entities = []
        
        for block in response.get('Blocks', []):
            if block['BlockType'] == 'KEY_VALUE_SET':
                if block.get('EntityTypes') and 'KEY' in block['EntityTypes']:
                    # This is a key-value pair
                    entities.append({
                        'type': 'key_value_pair',
                        'text': block.get('Text', ''),
                        'confidence': block.get('Confidence', 0),
                        'geometry': block.get('Geometry', {})
                    })
        
        return entities
    
    def _calculate_confidence_scores(self, response: Dict) -> Dict:
        """Calculate average confidence scores from Textract response"""
        confidences = []
        
        for block in response.get('Blocks', []):
            if 'Confidence' in block:
                confidences.append(block['Confidence'])
        
        if confidences:
            return {
                'average': sum(confidences) / len(confidences),
                'min': min(confidences),
                'max': max(confidences),
                'count': len(confidences)
            }
        
        return {'average': 0, 'min': 0, 'max': 0, 'count': 0}
    
    def _get_audio_format(self, mime_type: str) -> str:
        """Convert MIME type to Transcribe format"""
        format_mapping = {
            'audio/mpeg': 'mp3',
            'audio/mp3': 'mp3',
            'audio/wav': 'wav',
            'audio/flac': 'flac',
            'audio/ogg': 'ogg',
            'audio/amr': 'amr',
            'audio/webm': 'webm',
            'video/mp4': 'mp4',
            'video/webm': 'webm'
        }
        
        return format_mapping.get(mime_type, 'mp3')  # Default to mp3
    
    async def _download_transcript(self, transcript_uri: str) -> str:
        """Download transcript from S3 URI"""
        try:
            # Parse S3 URI
            if transcript_uri.startswith('https://'):
                # Extract bucket and key from HTTPS URL
                import urllib.parse
                parsed = urllib.parse.urlparse(transcript_uri)
                bucket = parsed.netloc.split('.')[0]
                key = parsed.path.lstrip('/')
            else:
                raise ValueError(f"Unsupported transcript URI format: {transcript_uri}")
            
            response = self.s3.get_object(Bucket=bucket, Key=key)
            transcript_data = json.loads(response['Body'].read().decode('utf-8'))
            
            # Extract transcript text
            return transcript_data['results']['transcripts'][0]['transcript']
            
        except Exception as e:
            logger.error(f"Failed to download transcript: {e}")
            return ""
    
    async def _store_processing_results(self, document: Document, result: ProcessingResult):
        """Store processing results as document metadata"""
        try:
            # Update document metadata with processing results
            metadata_update = {
                'evidence_processing': {
                    'processed_at': datetime.now(timezone.utc).isoformat(),
                    'processing_type': result.processing_type,
                    'status': result.status,
                    'processing_time': result.processing_time,
                    'has_extracted_text': bool(result.extracted_text),
                    'entity_count': len(result.entities) if result.entities else 0,
                    'metadata': result.metadata
                }
            }
            
            # Merge with existing metadata
            if document.metadata:
                document.metadata.update(metadata_update)
            else:
                document.metadata = metadata_update
            
            # Update document in repository
            await self.document_service.update_document_metadata(
                document.document_id, 
                document.metadata
            )
            
        except Exception as e:
            logger.error(f"Failed to store processing results: {e}")
            # Don't raise - this is not critical for the processing pipeline