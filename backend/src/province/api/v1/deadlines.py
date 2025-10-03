"""
API endpoints for Deadline Management

This module provides REST API endpoints for comprehensive deadline management
including creation, updates, scheduling, and notifications.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import logging

from ...agents.tools.deadline_management.deadline_service import DeadlineService
from ...agents.tools.deadline_management.models import (
    Deadline, DeadlineStatus, DeadlineType, Priority, ReminderSettings
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/deadlines", tags=["deadlines"])

# Global deadline service instance
deadline_service = DeadlineService()


class CreateDeadlineRequest(BaseModel):
    """Request model for creating a deadline"""
    title: str = Field(..., description="Deadline title")
    due_date: datetime = Field(..., description="When the deadline is due")
    matter_id: str = Field(..., description="Associated matter ID")
    description: str = Field("", description="Optional description")
    deadline_type: str = Field("other", description="Type of deadline")
    priority: str = Field("medium", description="Priority level")
    court_name: Optional[str] = Field(None, description="Court name if applicable")
    case_number: Optional[str] = Field(None, description="Case number if applicable")
    jurisdiction: str = Field("federal", description="Legal jurisdiction")
    reminder_days: List[int] = Field([7, 3, 1], description="Days before due date to send reminders")
    email_enabled: bool = Field(True, description="Enable email reminders")
    sms_enabled: bool = Field(False, description="Enable SMS reminders")
    push_enabled: bool = Field(True, description="Enable push notifications")
    custom_message: Optional[str] = Field(None, description="Custom reminder message")
    recipients: List[str] = Field([], description="Notification recipients")
    created_by: str = Field("", description="Who created the deadline")


class UpdateDeadlineRequest(BaseModel):
    """Request model for updating a deadline"""
    title: Optional[str] = None
    due_date: Optional[datetime] = None
    description: Optional[str] = None
    deadline_type: Optional[str] = None
    priority: Optional[str] = None
    court_name: Optional[str] = None
    case_number: Optional[str] = None
    jurisdiction: Optional[str] = None
    reminder_days: Optional[List[int]] = None
    email_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None
    custom_message: Optional[str] = None
    updated_by: str = Field("", description="Who updated the deadline")


class DeadlineResponse(BaseModel):
    """Response model for deadline data"""
    deadline_id: str
    title: str
    due_date: datetime
    matter_id: str
    description: str
    deadline_type: str
    priority: str
    status: str
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str
    court_name: Optional[str] = None
    case_number: Optional[str] = None
    jurisdiction: str
    days_until_due: int
    is_overdue: bool
    is_approaching: bool
    reminder_settings: Dict[str, Any]
    reminders_sent: List[Dict[str, Any]]
    completion_date: Optional[datetime] = None
    completion_notes: str
    ics_file_path: Optional[str] = None
    eventbridge_rules: List[str]


class CompleteDeadlineRequest(BaseModel):
    """Request model for completing a deadline"""
    completion_notes: str = Field("", description="Optional completion notes")
    completed_by: str = Field(..., description="Who completed the deadline")
    recipients: List[str] = Field([], description="Notification recipients")


class CancelDeadlineRequest(BaseModel):
    """Request model for cancelling a deadline"""
    cancellation_reason: str = Field(..., description="Reason for cancellation")
    cancelled_by: str = Field(..., description="Who cancelled the deadline")


@router.post("/", response_model=DeadlineResponse)
async def create_deadline(request: CreateDeadlineRequest):
    """
    Create a new deadline with full integration
    
    Creates a deadline with EventBridge scheduling, calendar generation,
    and notification setup.
    """
    try:
        # Convert string enums to proper types
        try:
            deadline_type = DeadlineType(request.deadline_type.lower())
        except ValueError:
            deadline_type = DeadlineType.OTHER
        
        try:
            priority = Priority(request.priority.lower())
        except ValueError:
            priority = Priority.MEDIUM
        
        # Create reminder settings
        reminder_settings = ReminderSettings(
            days_before=request.reminder_days,
            email_enabled=request.email_enabled,
            sms_enabled=request.sms_enabled,
            push_enabled=request.push_enabled,
            custom_message=request.custom_message
        )
        
        # Create deadline
        deadline = deadline_service.create_deadline(
            title=request.title,
            due_date=request.due_date,
            matter_id=request.matter_id,
            description=request.description,
            deadline_type=deadline_type,
            priority=priority,
            reminder_settings=reminder_settings,
            court_name=request.court_name,
            case_number=request.case_number,
            jurisdiction=request.jurisdiction,
            created_by=request.created_by,
            recipients=request.recipients
        )
        
        if not deadline:
            raise HTTPException(status_code=500, detail="Failed to create deadline")
        
        return _deadline_to_response(deadline)
        
    except ValueError as e:
        logger.error(f"Validation error creating deadline: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating deadline: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create deadline: {str(e)}")


@router.get("/{deadline_id}", response_model=DeadlineResponse)
async def get_deadline(deadline_id: str):
    """Get a deadline by ID"""
    
    try:
        deadline = deadline_service.get_deadline(deadline_id)
        
        if not deadline:
            raise HTTPException(status_code=404, detail="Deadline not found")
        
        return _deadline_to_response(deadline)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting deadline: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{deadline_id}", response_model=DeadlineResponse)
async def update_deadline(deadline_id: str, request: UpdateDeadlineRequest):
    """Update an existing deadline"""
    
    try:
        # Build updates dictionary
        updates = {}
        
        if request.title is not None:
            updates['title'] = request.title
        if request.due_date is not None:
            updates['due_date'] = request.due_date
        if request.description is not None:
            updates['description'] = request.description
        if request.deadline_type is not None:
            try:
                updates['deadline_type'] = DeadlineType(request.deadline_type.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid deadline type: {request.deadline_type}")
        if request.priority is not None:
            try:
                updates['priority'] = Priority(request.priority.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid priority: {request.priority}")
        if request.court_name is not None:
            updates['court_name'] = request.court_name
        if request.case_number is not None:
            updates['case_number'] = request.case_number
        if request.jurisdiction is not None:
            updates['jurisdiction'] = request.jurisdiction
        
        # Update reminder settings if any reminder fields provided
        if any([
            request.reminder_days is not None,
            request.email_enabled is not None,
            request.sms_enabled is not None,
            request.push_enabled is not None,
            request.custom_message is not None
        ]):
            # Get current deadline to preserve existing settings
            current_deadline = deadline_service.get_deadline(deadline_id)
            if not current_deadline:
                raise HTTPException(status_code=404, detail="Deadline not found")
            
            current_settings = current_deadline.reminder_settings
            
            new_settings = ReminderSettings(
                days_before=request.reminder_days if request.reminder_days is not None else current_settings.days_before,
                email_enabled=request.email_enabled if request.email_enabled is not None else current_settings.email_enabled,
                sms_enabled=request.sms_enabled if request.sms_enabled is not None else current_settings.sms_enabled,
                push_enabled=request.push_enabled if request.push_enabled is not None else current_settings.push_enabled,
                custom_message=request.custom_message if request.custom_message is not None else current_settings.custom_message
            )
            
            updates['reminder_settings'] = new_settings
        
        if not updates:
            raise HTTPException(status_code=400, detail="No updates provided")
        
        # Update deadline
        updated_deadline = deadline_service.update_deadline(
            deadline_id, updates, request.updated_by
        )
        
        if not updated_deadline:
            raise HTTPException(status_code=404, detail="Deadline not found or update failed")
        
        return _deadline_to_response(updated_deadline)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating deadline: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{deadline_id}/complete")
async def complete_deadline(deadline_id: str, request: CompleteDeadlineRequest):
    """Mark a deadline as completed"""
    
    try:
        success = deadline_service.complete_deadline(
            deadline_id,
            request.completion_notes,
            request.completed_by,
            request.recipients
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Deadline not found or completion failed")
        
        return {"message": "Deadline completed successfully", "deadline_id": deadline_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing deadline: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{deadline_id}/cancel")
async def cancel_deadline(deadline_id: str, request: CancelDeadlineRequest):
    """Cancel a deadline"""
    
    try:
        success = deadline_service.cancel_deadline(
            deadline_id,
            request.cancellation_reason,
            request.cancelled_by
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Deadline not found or cancellation failed")
        
        return {"message": "Deadline cancelled successfully", "deadline_id": deadline_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling deadline: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{deadline_id}")
async def delete_deadline(deadline_id: str):
    """Delete a deadline"""
    
    try:
        # First cancel the deadline to clean up scheduled reminders
        success = deadline_service.cancel_deadline(deadline_id, "Deleted", "system")
        
        if not success:
            raise HTTPException(status_code=404, detail="Deadline not found")
        
        return {"message": "Deadline deleted successfully", "deadline_id": deadline_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting deadline: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/matter/{matter_id}", response_model=List[DeadlineResponse])
async def get_matter_deadlines(
    matter_id: str,
    status: Optional[str] = Query(None, description="Filter by status")
):
    """Get all deadlines for a matter"""
    
    try:
        # Convert status string to enum if provided
        status_filter = None
        if status:
            try:
                status_filter = DeadlineStatus(status.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        deadlines = deadline_service.get_matter_deadlines(matter_id, status_filter)
        
        return [_deadline_to_response(deadline) for deadline in deadlines]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting matter deadlines: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/upcoming/", response_model=List[DeadlineResponse])
async def get_upcoming_deadlines(
    days_ahead: int = Query(30, description="Number of days to look ahead")
):
    """Get upcoming deadlines"""
    
    try:
        if days_ahead < 1 or days_ahead > 365:
            raise HTTPException(status_code=400, detail="days_ahead must be between 1 and 365")
        
        deadlines = deadline_service.get_upcoming_deadlines(days_ahead)
        
        return [_deadline_to_response(deadline) for deadline in deadlines]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting upcoming deadlines: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/overdue/", response_model=List[DeadlineResponse])
async def get_overdue_deadlines():
    """Get overdue deadlines"""
    
    try:
        deadlines = deadline_service.get_overdue_deadlines()
        
        return [_deadline_to_response(deadline) for deadline in deadlines]
        
    except Exception as e:
        logger.error(f"Error getting overdue deadlines: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/", response_model=List[DeadlineResponse])
async def search_deadlines(
    title_contains: Optional[str] = Query(None, description="Search in title"),
    deadline_type: Optional[str] = Query(None, description="Filter by deadline type"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    status: Optional[str] = Query(None, description="Filter by status"),
    court_name: Optional[str] = Query(None, description="Filter by court name"),
    limit: int = Query(50, description="Maximum number of results")
):
    """Search deadlines with various filters"""
    
    try:
        # Convert string enums to proper types
        search_criteria = {}
        
        if title_contains:
            search_criteria['title_contains'] = title_contains
        
        if deadline_type:
            try:
                search_criteria['deadline_type'] = DeadlineType(deadline_type.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid deadline type: {deadline_type}")
        
        if priority:
            try:
                search_criteria['priority'] = Priority(priority.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid priority: {priority}")
        
        if status:
            try:
                search_criteria['status'] = DeadlineStatus(status.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        if court_name:
            search_criteria['court_name'] = court_name
        
        search_criteria['limit'] = min(limit, 100)  # Cap at 100 results
        
        deadlines = deadline_service.search_deadlines(**search_criteria)
        
        return [_deadline_to_response(deadline) for deadline in deadlines]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching deadlines: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics/")
async def get_deadline_statistics(
    matter_id: Optional[str] = Query(None, description="Filter by matter ID")
):
    """Get deadline statistics"""
    
    try:
        stats = deadline_service.get_deadline_statistics(matter_id)
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting deadline statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/matter/{matter_id}/calendar")
async def generate_matter_calendar(matter_id: str):
    """Generate calendar file for all deadlines in a matter"""
    
    try:
        calendar_url = deadline_service.generate_matter_calendar(matter_id)
        
        if not calendar_url:
            raise HTTPException(status_code=404, detail="No deadlines found for matter or calendar generation failed")
        
        return {
            "calendar_url": calendar_url,
            "matter_id": matter_id,
            "message": "Calendar generated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating matter calendar: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process-reminders")
async def process_deadline_reminders():
    """
    Process all deadlines that need reminders sent
    
    This endpoint is typically called by scheduled jobs or EventBridge rules.
    """
    try:
        results = deadline_service.process_deadline_reminders()
        
        return {
            "message": "Reminder processing completed",
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error processing deadline reminders: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update-overdue-statuses")
async def update_overdue_statuses():
    """
    Update status for overdue deadlines
    
    This endpoint is typically called by scheduled jobs.
    """
    try:
        updated_count = deadline_service.update_overdue_statuses()
        
        return {
            "message": f"Updated {updated_count} deadlines to overdue status",
            "updated_count": updated_count
        }
        
    except Exception as e:
        logger.error(f"Error updating overdue statuses: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/types/")
async def get_deadline_types():
    """Get available deadline types"""
    
    return {
        "deadline_types": [
            {"value": dt.value, "display_name": dt.value.replace('_', ' ').title()}
            for dt in DeadlineType
        ]
    }


@router.get("/priorities/")
async def get_priorities():
    """Get available priority levels"""
    
    return {
        "priorities": [
            {"value": p.value, "display_name": p.value.title()}
            for p in Priority
        ]
    }


@router.get("/statuses/")
async def get_statuses():
    """Get available deadline statuses"""
    
    return {
        "statuses": [
            {"value": s.value, "display_name": s.value.replace('_', ' ').title()}
            for s in DeadlineStatus
        ]
    }


@router.get("/health")
async def deadline_health_check():
    """Check the health of the deadline management system"""
    
    try:
        # Test basic functionality
        stats = deadline_service.get_deadline_statistics()
        
        health_status = {
            "status": "healthy",
            "service": "Deadline Management System",
            "components": {
                "repository": "operational",
                "scheduler": "operational", 
                "calendar_generator": "operational",
                "notification_service": "operational"
            },
            "total_deadlines": stats.get('total_deadlines', 0)
        }
        
        return health_status
        
    except Exception as e:
        logger.error(f"Deadline health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


def _deadline_to_response(deadline: Deadline) -> DeadlineResponse:
    """Convert Deadline model to API response"""
    
    return DeadlineResponse(
        deadline_id=deadline.deadline_id,
        title=deadline.title,
        due_date=deadline.due_date,
        matter_id=deadline.matter_id,
        description=deadline.description,
        deadline_type=deadline.deadline_type.value,
        priority=deadline.priority.value,
        status=deadline.status.value,
        created_at=deadline.created_at,
        updated_at=deadline.updated_at,
        created_by=deadline.created_by,
        updated_by=deadline.updated_by,
        court_name=deadline.court_name,
        case_number=deadline.case_number,
        jurisdiction=deadline.jurisdiction,
        days_until_due=deadline.days_until_due,
        is_overdue=deadline.is_overdue,
        is_approaching=deadline.is_approaching,
        reminder_settings=deadline.reminder_settings.to_dict(),
        reminders_sent=deadline.reminders_sent,
        completion_date=deadline.completion_date,
        completion_notes=deadline.completion_notes,
        ics_file_path=deadline.ics_file_path,
        eventbridge_rules=deadline.eventbridge_rules
    )