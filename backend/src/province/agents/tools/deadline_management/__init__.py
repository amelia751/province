"""
Deadline Management System

This module provides comprehensive deadline management capabilities including
DynamoDB operations, EventBridge scheduling, calendar generation, and notifications.
"""

from .models import Deadline, DeadlineStatus, DeadlineType, ReminderSettings
from .repository import DeadlineRepository
from .scheduler import DeadlineScheduler
from .calendar_generator import CalendarGenerator
from .notification_service import NotificationService
from .deadline_service import DeadlineService

__all__ = [
    'Deadline',
    'DeadlineStatus', 
    'DeadlineType',
    'ReminderSettings',
    'DeadlineRepository',
    'DeadlineScheduler',
    'CalendarGenerator',
    'NotificationService',
    'DeadlineService'
]