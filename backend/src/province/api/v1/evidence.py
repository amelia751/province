"""
Evidence Processing API Endpoints

Provides REST API endpoints for evidence document processing,
including OCR, transcription, entity extraction, and chronology generation.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncio

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ...core.config import get_settings
from ...core.exceptions import ProcessingError, ValidationError
from ...services.evidence_processor import EvidenceProcessor, ProcessingResult
from ...services.chronology_generator import ChronologyGenerator, Chronology
from ...services.document import DocumentService
from ...models.document import Document

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/evidence", tags=["evidence"])

# Initialize services lazily to avoid configuration issues during import
evidence_processor = None
chronology_generator = None
document_service = None


def get_evidence_processor():
    """Get or create evidence processor instance"""
    global evidence_processor
    if evidence_processor is None:
        evidence_processor = EvidenceProcessor()
    return evidence_processor


def get_chronology_generator():
    """Get or create chronology generator instance"""
    global chronology_generator
    if chronology_generator is None:
        chronology_generator = ChronologyGenerator()
    return chronology_generator


def get_document_service():
    """Get or create document service instance"""
    global document_service
    if document_service is None:
        document_service = DocumentService()
    return document_service


# Request/Response Models
class ProcessDocumentRequest(BaseModel):
    document_id: str = Field(..., description="ID of the document to process")
    processing_options: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="Optional processing configuration"
    )


class ProcessDocumentResponse(BaseModel):
    document_id: str
    processing_type: str
    status: str
    extracted_text_length: Optional[int] = None
    entity_count: Optional[int] = None
    processing_time: Optional[float] = None
    error_message: Optional[str] = None


class BatchProcessRequest(BaseModel):
    matter_id: str = Field(..., description="ID of the matter")
    document_ids: List[str] = Field(..., description="List of document IDs to process")
    generate_chronology: bool = Field(default=True, description="Whether to generate chronology")
    processing_options: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional processing configuration"
    )


class BatchProcessResponse(BaseModel):
    matter_id: str
    total_documents: int
    successful_processing: int
    failed_processing: int
    processing_results: List[ProcessDocumentResponse]
    chronology_generated: bool
    total_processing_time: float


class ChronologyResponse(BaseModel):
    matter_id: str
    total_entries: int
    generated_at: datetime
    last_updated: datetime
    total_documents_processed: int
    entries: List[Dict[str, Any]]


class ProcessingStatusResponse(BaseModel):
    document_id: str
    status: str  # "not_processed", "processing", "completed", "failed"
    processing_type: Optional[str] = None
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None


@router.post("/process-document", response_model=ProcessDocumentResponse)
async def process_document(
    request: ProcessDocumentRequest,
    background_tasks: BackgroundTasks
) -> ProcessDocumentResponse:
    """
    Process a single evidence document for OCR, transcription, and entity extraction
    """
    try:
        logger.info(f"Processing document {request.document_id}")
        
        # Get document from repository
        document = await get_document_service().get_document(request.document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Process document
        result = await get_evidence_processor().process_document(
            document, 
            request.processing_options
        )
        
        # Convert result to response
        response = ProcessDocumentResponse(
            document_id=result.document_id,
            processing_type=result.processing_type,
            status=result.status,
            extracted_text_length=len(result.extracted_text) if result.extracted_text else None,
            entity_count=len(result.entities) if result.entities else None,
            processing_time=result.processing_time,
            error_message=result.error_message
        )
        
        logger.info(f"Document {request.document_id} processed successfully: {result.status}")
        return response
        
    except Exception as e:
        logger.error(f"Error processing document {request.document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.post("/batch-process", response_model=BatchProcessResponse)
async def batch_process_documents(
    request: BatchProcessRequest,
    background_tasks: BackgroundTasks
) -> BatchProcessResponse:
    """
    Process multiple evidence documents and optionally generate chronology
    """
    try:
        logger.info(f"Batch processing {len(request.document_ids)} documents for matter {request.matter_id}")
        
        start_time = datetime.now()
        processing_results = []
        successful_count = 0
        failed_count = 0
        
        # Process documents concurrently (with limit to avoid overwhelming services)
        semaphore = asyncio.Semaphore(5)  # Limit to 5 concurrent processes
        
        async def process_single_document(doc_id: str) -> ProcessingResult:
            async with semaphore:
                document = await get_document_service().get_document(doc_id)
                if not document:
                    logger.warning(f"Document {doc_id} not found, skipping")
                    return ProcessingResult(
                        document_id=doc_id,
                        processing_type="error",
                        status="failed",
                        error_message="Document not found"
                    )
                
                return await get_evidence_processor().process_document(
                    document,
                    request.processing_options
                )
        
        # Execute processing tasks
        tasks = [process_single_document(doc_id) for doc_id in request.document_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        valid_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Processing task failed: {result}")
                failed_count += 1
                processing_results.append(ProcessDocumentResponse(
                    document_id="unknown",
                    processing_type="error",
                    status="failed",
                    error_message=str(result)
                ))
            else:
                if result.status == "success":
                    successful_count += 1
                    valid_results.append(result)
                else:
                    failed_count += 1
                
                processing_results.append(ProcessDocumentResponse(
                    document_id=result.document_id,
                    processing_type=result.processing_type,
                    status=result.status,
                    extracted_text_length=len(result.extracted_text) if result.extracted_text else None,
                    entity_count=len(result.entities) if result.entities else None,
                    processing_time=result.processing_time,
                    error_message=result.error_message
                ))
        
        # Generate chronology if requested and we have successful results
        chronology_generated = False
        if request.generate_chronology and valid_results:
            try:
                await get_chronology_generator().generate_chronology(request.matter_id, valid_results)
                chronology_generated = True
                logger.info(f"Chronology generated for matter {request.matter_id}")
            except Exception as e:
                logger.error(f"Chronology generation failed: {e}")
                # Don't fail the entire request if chronology generation fails
        
        total_time = (datetime.now() - start_time).total_seconds()
        
        response = BatchProcessResponse(
            matter_id=request.matter_id,
            total_documents=len(request.document_ids),
            successful_processing=successful_count,
            failed_processing=failed_count,
            processing_results=processing_results,
            chronology_generated=chronology_generated,
            total_processing_time=total_time
        )
        
        logger.info(f"Batch processing completed for matter {request.matter_id}: {successful_count} successful, {failed_count} failed")
        return response
        
    except Exception as e:
        logger.error(f"Error in batch processing for matter {request.matter_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Batch processing failed: {str(e)}")


@router.get("/chronology/{matter_id}", response_model=ChronologyResponse)
async def get_chronology(matter_id: str) -> ChronologyResponse:
    """
    Get the chronology for a specific matter
    """
    try:
        logger.info(f"Retrieving chronology for matter {matter_id}")
        
        # Load chronology from S3
        chronology = await get_chronology_generator()._load_existing_chronology(matter_id)
        
        if not chronology:
            raise HTTPException(status_code=404, detail="Chronology not found")
        
        # Convert entries to dict format for response
        entries_dict = []
        for entry in chronology.entries:
            entry_dict = {
                "date": entry.date.isoformat(),
                "event_type": entry.event_type,
                "description": entry.description,
                "source_document": entry.source_document,
                "page_number": entry.page_number,
                "confidence_score": entry.confidence_score,
                "entities": entry.entities or []
            }
            entries_dict.append(entry_dict)
        
        response = ChronologyResponse(
            matter_id=chronology.matter_id,
            total_entries=len(chronology.entries),
            generated_at=chronology.generated_at,
            last_updated=chronology.last_updated,
            total_documents_processed=chronology.total_documents_processed,
            entries=entries_dict
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving chronology for matter {matter_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve chronology: {str(e)}")


@router.post("/chronology/{matter_id}/regenerate")
async def regenerate_chronology(
    matter_id: str,
    background_tasks: BackgroundTasks
) -> JSONResponse:
    """
    Regenerate chronology for a matter using all processed documents
    """
    try:
        logger.info(f"Regenerating chronology for matter {matter_id}")
        
        # Get all documents for the matter
        documents = await get_document_service().list_documents_by_matter(matter_id)
        
        # Filter for documents that have been processed
        processed_results = []
        for document in documents:
            if (document.metadata and 
                document.metadata.get('evidence_processing') and
                document.metadata['evidence_processing'].get('status') == 'success'):
                
                # Reconstruct processing result from metadata
                processing_data = document.metadata['evidence_processing']
                result = ProcessingResult(
                    document_id=document.document_id,
                    processing_type=processing_data.get('processing_type', 'unknown'),
                    status='success',
                    extracted_text="",  # We'll need to retrieve this separately if needed
                    entities=[],  # Same here
                    metadata=processing_data.get('metadata', {})
                )
                processed_results.append(result)
        
        if not processed_results:
            raise HTTPException(
                status_code=400, 
                detail="No processed documents found for chronology generation"
            )
        
        # Schedule chronology regeneration in background
        background_tasks.add_task(
            get_chronology_generator().generate_chronology,
            matter_id,
            processed_results
        )
        
        return JSONResponse(
            content={
                "message": f"Chronology regeneration started for matter {matter_id}",
                "documents_found": len(processed_results)
            },
            status_code=202
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error regenerating chronology for matter {matter_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to regenerate chronology: {str(e)}")


@router.get("/status/{document_id}", response_model=ProcessingStatusResponse)
async def get_processing_status(document_id: str) -> ProcessingStatusResponse:
    """
    Get the processing status of a specific document
    """
    try:
        logger.info(f"Checking processing status for document {document_id}")
        
        # Get document from repository
        document = await get_document_service().get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check processing metadata
        if (document.metadata and 
            document.metadata.get('evidence_processing')):
            
            processing_data = document.metadata['evidence_processing']
            
            response = ProcessingStatusResponse(
                document_id=document_id,
                status=processing_data.get('status', 'unknown'),
                processing_type=processing_data.get('processing_type'),
                processed_at=datetime.fromisoformat(processing_data['processed_at']) if processing_data.get('processed_at') else None,
                error_message=processing_data.get('error_message')
            )
        else:
            response = ProcessingStatusResponse(
                document_id=document_id,
                status="not_processed"
            )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking processing status for document {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to check processing status: {str(e)}")


@router.post("/upload-and-process")
async def upload_and_process_evidence(
    matter_id: str = Form(...),
    file: UploadFile = File(...),
    processing_options: Optional[str] = Form(None),
    background_tasks: BackgroundTasks = None
) -> ProcessDocumentResponse:
    """
    Upload an evidence document and immediately process it
    """
    try:
        logger.info(f"Uploading and processing evidence file {file.filename} for matter {matter_id}")
        
        # Parse processing options if provided
        options = None
        if processing_options:
            import json
            options = json.loads(processing_options)
        
        # Upload document first
        document = await get_document_service().upload_document(
            matter_id=matter_id,
            file_path=f"Evidence/{file.filename}",
            content=await file.read(),
            metadata={
                "uploaded_for_processing": True,
                "original_filename": file.filename,
                "content_type": file.content_type
            }
        )
        
        # Process the uploaded document
        result = await get_evidence_processor().process_document(document, options)
        
        # Convert result to response
        response = ProcessDocumentResponse(
            document_id=result.document_id,
            processing_type=result.processing_type,
            status=result.status,
            extracted_text_length=len(result.extracted_text) if result.extracted_text else None,
            entity_count=len(result.entities) if result.entities else None,
            processing_time=result.processing_time,
            error_message=result.error_message
        )
        
        logger.info(f"Evidence file {file.filename} uploaded and processed successfully")
        return response
        
    except Exception as e:
        logger.error(f"Error uploading and processing evidence file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload and processing failed: {str(e)}")


@router.get("/matter/{matter_id}/processing-summary")
async def get_matter_processing_summary(matter_id: str) -> Dict[str, Any]:
    """
    Get a summary of evidence processing for a matter
    """
    try:
        logger.info(f"Getting processing summary for matter {matter_id}")
        
        # Get all documents for the matter
        documents = await get_document_service().list_documents_by_matter(matter_id)
        
        # Analyze processing status
        total_documents = len(documents)
        processed_documents = 0
        failed_documents = 0
        processing_types = {}
        
        for document in documents:
            if (document.metadata and 
                document.metadata.get('evidence_processing')):
                
                processing_data = document.metadata['evidence_processing']
                status = processing_data.get('status')
                
                if status == 'success':
                    processed_documents += 1
                elif status == 'failed':
                    failed_documents += 1
                
                # Count processing types
                proc_type = processing_data.get('processing_type', 'unknown')
                processing_types[proc_type] = processing_types.get(proc_type, 0) + 1
        
        # Check if chronology exists
        chronology = await get_chronology_generator()._load_existing_chronology(matter_id)
        
        summary = {
            "matter_id": matter_id,
            "total_documents": total_documents,
            "processed_documents": processed_documents,
            "failed_documents": failed_documents,
            "unprocessed_documents": total_documents - processed_documents - failed_documents,
            "processing_types": processing_types,
            "chronology_exists": chronology is not None,
            "chronology_entries": len(chronology.entries) if chronology else 0,
            "chronology_last_updated": chronology.last_updated.isoformat() if chronology else None
        }
        
        return summary
        
    except Exception as e:
        logger.error(f"Error getting processing summary for matter {matter_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get processing summary: {str(e)}")