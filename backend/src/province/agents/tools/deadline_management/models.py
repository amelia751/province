"""
Deadline Data Models

This module defines the data models for deadline management including
deadline entities, reminder settings, and status tracking.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from enum import Enum
import uuid


class DeadlineStatus(Enum):
    """Status of a deadline"""
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    OVERDUE = "overdue"
    APPROACHING = "approaching"


class DeadlineType(Enum):
    """Type of legal deadline"""
    COURT_FILING = "court_filing"
    DISCOVERY = "discovery"
    MOTION = "motion"
    HEARING = "hearing"
    TRIAL = "trial"
    APPEAL = "appeal"
    CONTRACT = "contract"
    COMPLIANCE = "compliance"
    INTERNAL = "internal"
    CLIENT_MEETING = "client_meeting"
    OTHER = "other"


class Priority(Enum):
    """Priority level of a deadline"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ReminderSettings:
    """Settings for deadline reminders"""
    days_before: List[int] = field(default_factory=lambda: [7, 3, 1])
    email_enabled: bool = True
    sms_enabled: bool = False
    push_enabled: bool = True
    custom_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for DynamoDB storage"""
        return {
            'days_before': self.days_before,
            'email_enabled': self.email_enabled,
            'sms_enabled': self.sms_enabled,
            'push_enabled': self.push_enabled,
            'custom_message': self.custom_message
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReminderSettings':
        """Create from dictionary"""
        return cls(
            days_before=data.get('days_before', [7, 3, 1]),
            email_enabled=data.get('email_enabled', True),
            sms_enabled=data.get('sms_enabled', False),
            push_enabled=data.get('push_enabled', True),
            custom_message=data.get('custom_message')
        )


@dataclass
class Deadline:
    """Main deadline entity"""
    deadline_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    matter_id: str = ""
    title: str = ""
    description: str = ""
    due_date: datetime = field(default_factory=datetime.utcnow)
    deadline_type: DeadlineType = DeadlineType.OTHER
    priority: Priority = Priority.MEDIUM
    status: DeadlineStatus = DeadlineStatus.ACTIVE
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = ""
    updated_at: datetime = field(default_factory=datetime.utcnow)
    updated_by: str = ""
    
    # Reminder settings
    reminder_settings: ReminderSettings = field(default_factory=ReminderSettings)
    
    # Tracking
    reminders_sent: List[Dict[str, Any]] = field(default_factory=list)
    completion_date: Optional[datetime] = None
    completion_notes: str = ""
    
    # Legal context
    court_name: Optional[str] = None
    case_number: Optional[str] = None
    jurisdiction: str = "federal"
    
    # Calendar integration
    calendar_event_id: Optional[str] = None
    ics_file_path: Optional[str] = None
    
    # EventBridge rules for reminders
    eventbridge_rules: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Post-initialization processing"""
        if isinstance(self.due_date, str):
            self.due_date = datetime.fromisoformat(self.due_date.replace('Z', '+00:00'))
        if isinstance(self.created_at, str):
            self.created_at = datetime.fromisoformat(self.created_at.replace('Z', '+00:00'))
        if isinstance(self.updated_at, str):
            self.updated_at = datetime.fromisoformat(self.updated_at.replace('Z', '+00:00'))
        if isinstance(self.completion_date, str):
            self.completion_date = datetime.fromisoformat(self.completion_date.replace('Z', '+00:00'))
    
    @property
    def is_overdue(self) -> bool:
        """Check if deadline is overdue"""
        return self.due_date < datetime.utcnow() and self.status == DeadlineStatus.ACTIVE
    
    @property
    def is_approaching(self) -> bool:
        """Check if deadline is approaching (within 7 days)"""
        if self.status != DeadlineStatus.ACTIVE:
            return False
        days_until = (self.due_date - datetime.utcnow()).days
        return 0 <= days_until <= 7
    
    @property
    def days_until_due(self) -> int:
        """Get number of days until due date"""
        return (self.due_date - datetime.utcnow()).days
    
    @property
    def hours_until_due(self) -> float:
        """Get number of hours until due date"""
        return (self.due_date - datetime.utcnow()).total_seconds() / 3600
    
    def update_status(self):
        """Update status based on current conditions"""
        if self.completion_date:
            self.status = DeadlineStatus.COMPLETED
        elif self.is_overdue:
            self.status = DeadlineStatus.OVERDUE
        elif self.is_approaching:
            self.status = DeadlineStatus.APPROACHING
        else:
            self.status = DeadlineStatus.ACTIVE
    
    def mark_completed(self, completion_notes: str = "", completed_by: str = ""):
        """Mark deadline as completed"""
        self.status = DeadlineStatus.COMPLETED
        self.completion_date = datetime.utcnow()
        self.completion_notes = completion_notes
        self.updated_at = datetime.utcnow()
        self.updated_by = completed_by
    
    def mark_cancelled(self, cancellation_reason: str = "", cancelled_by: str = ""):
        """Mark deadline as cancelled"""
        self.status = DeadlineStatus.CANCELLED
        self.completion_notes = f"Cancelled: {cancellation_reason}"
        self.updated_at = datetime.utcnow()
        self.updated_by = cancelled_by
    
    def add_reminder_sent(self, reminder_type: str, sent_at: datetime = None, 
                         recipient: str = "", success: bool = True, error: str = ""):
        """Add a record of a sent reminder"""
        if sent_at is None:
            sent_at = datetime.utcnow()
        
        reminder_record = {
            'type': reminder_type,
            'sent_at': sent_at.isoformat(),
            'recipient': recipient,
            'success': success,
            'error': error,
            'days_before': self.days_until_due
        }
        
        self.reminders_sent.append(reminder_record)
    
    def get_next_reminder_dates(self) -> List[datetime]:
        """Get list of upcoming reminder dates"""
        reminder_dates = []
        
        for days_before in self.reminder_settings.days_before:
            reminder_date = self.due_date - timedelta(days=days_before)
            if reminder_date > datetime.utcnow():
                reminder_dates.append(reminder_date)
        
        return sorted(reminder_dates)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for DynamoDB storage"""
        return {
            'deadline_id': self.deadline_id,
            'matter_id': self.matter_id,
            'title': self.title,
            'description': self.description,
            'due_date': self.due_date.isoformat(),
            'deadline_type': self.deadline_type.value,
            'priority': self.priority.value,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'created_by': self.created_by,
            'updated_at': self.updated_at.isoformat(),
            'updated_by': self.updated_by,
            'reminder_settings': self.reminder_settings.to_dict(),
            'reminders_sent': self.reminders_sent,
            'completion_date': self.completion_date.isoformat() if self.completion_date else None,
            'completion_notes': self.completion_notes,
            'court_name': self.court_name,
            'case_number': self.case_number,
            'jurisdiction': self.jurisdiction,
            'calendar_event_id': self.calendar_event_id,
            'ics_file_path': self.ics_file_path,
            'eventbridge_rules': self.eventbridge_rules
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Deadline':
        """Create from dictionary"""
        # Handle enum conversions
        deadline_type = DeadlineType(data.get('deadline_type', 'other'))
        priority = Priority(data.get('priority', 'medium'))
        status = DeadlineStatus(data.get('status', 'active'))
        
        # Handle datetime conversions
        due_date = data.get('due_date')
        if isinstance(due_date, str):
            due_date = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
        
        created_at = data.get('created_at')
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        
        updated_at = data.get('updated_at')
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
        
        completion_date = data.get('completion_date')
        if completion_date and isinstance(completion_date, str):
            completion_date = datetime.fromisoformat(completion_date.replace('Z', '+00:00'))
        
        # Handle reminder settings
        reminder_settings_data = data.get('reminder_settings', {})
        reminder_settings = ReminderSettings.from_dict(reminder_settings_data)
        
        return cls(
            deadline_id=data.get('deadline_id', str(uuid.uuid4())),
            matter_id=data.get('matter_id', ''),
            title=data.get('title', ''),
            description=data.get('description', ''),
            due_date=due_date or datetime.utcnow(),
            deadline_type=deadline_type,
            priority=priority,
            status=status,
            created_at=created_at or datetime.utcnow(),
            created_by=data.get('created_by', ''),
            updated_at=updated_at or datetime.utcnow(),
            updated_by=data.get('updated_by', ''),
            reminder_settings=reminder_settings,
            reminders_sent=data.get('reminders_sent', []),
            completion_date=completion_date,
            completion_notes=data.get('completion_notes', ''),
            court_name=data.get('court_name'),
            case_number=data.get('case_number'),
            jurisdiction=data.get('jurisdiction', 'federal'),
            calendar_event_id=data.get('calendar_event_id'),
            ics_file_path=data.get('ics_file_path'),
            eventbridge_rules=data.get('eventbridge_rules', [])
        )
    
    def __str__(self) -> str:
        """String representation"""
        return f"Deadline('{self.title}', due={self.due_date.strftime('%Y-%m-%d')}, status={self.status.value})"
    
    def __repr__(self) -> str:
        """Detailed representation"""
        return (f"Deadline(id='{self.deadline_id}', title='{self.title}', "
                f"due_date='{self.due_date}', status='{self.status.value}')")