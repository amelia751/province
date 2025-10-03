"""
Deadline Service

Main service that orchestrates all deadline management components including
repository operations, scheduling, calendar generation, and notifications.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from .models import Deadline, DeadlineStatus, DeadlineType, Priority, ReminderSettings
from .repository import DeadlineRepository
from .scheduler import DeadlineScheduler
from .calendar_generator import CalendarGenerator
from .notification_service import NotificationService

logger = logging.getLogger(__name__)


class DeadlineService:
    """
    Main service for comprehensive deadline management
    
    Orchestrates all deadline management components including storage,
    scheduling, calendar generation, and notifications.
    """
    
    def __init__(self, 
                 table_name: str = "province-deadlines",
                 s3_bucket: str = "province-legal-calendars",
                 region_name: str = "us-east-1"):
        
        self.repository = DeadlineRepository(table_name, region_name)
        self.scheduler = DeadlineScheduler(region_name)
        self.calendar_generator = CalendarGenerator(s3_bucket, region_name)
        self.notification_service = NotificationService(region_name)
        
        # Configuration
        self.default_recipients = []
        self.lambda_arn = None
        self.topic_arn = None
    
    def configure(self, 
                 lambda_arn: Optional[str] = None,
                 topic_arn: Optional[str] = None,
                 default_recipients: List[str] = None):
        """Configure service with AWS resource ARNs"""
        
        if lambda_arn:
            self.lambda_arn = lambda_arn
            self.scheduler.set_target_lambda_arn(lambda_arn)
        
        if topic_arn:
            self.topic_arn = topic_arn
            self.notification_service.set_default_topic_arn(topic_arn)
        
        if default_recipients:
            self.default_recipients = default_recipients
    
    def create_deadline(self, 
                       title: str,
                       due_date: datetime,
                       matter_id: str,
                       description: str = "",
                       deadline_type: DeadlineType = DeadlineType.OTHER,
                       priority: Priority = Priority.MEDIUM,
                       reminder_settings: Optional[ReminderSettings] = None,
                       court_name: Optional[str] = None,
                       case_number: Optional[str] = None,
                       jurisdiction: str = "federal",
                       created_by: str = "",
                       recipients: List[str] = None) -> Optional[Deadline]:
        """
        Create a new deadline with full integration
        
        Args:
            title: Deadline title
            due_date: When the deadline is due
            matter_id: Associated matter ID
            description: Optional description
            deadline_type: Type of deadline
            priority: Priority level
            reminder_settings: Custom reminder settings
            court_name: Court name if applicable
            case_number: Case number if applicable
            jurisdiction: Legal jurisdiction
            created_by: Who created the deadline
            recipients: List of notification recipients
            
        Returns:
            Created Deadline object if successful, None otherwise
        """
        try:
            # Create deadline object
            deadline = Deadline(
                title=title,
                due_date=due_date,
                matter_id=matter_id,
                description=description,
                deadline_type=deadline_type,
                priority=priority,
                reminder_settings=reminder_settings or ReminderSettings(),
                court_name=court_name,
                case_number=case_number,
                jurisdiction=jurisdiction,
                created_by=created_by
            )
            
            # Save to database
            if not self.repository.create_deadline(deadline):
                logger.error(f"Failed to create deadline in database")
                return None
            
            # Schedule reminders
            rule_arns = self.scheduler.schedule_deadline_reminders(deadline)
            deadline.eventbridge_rules = rule_arns
            
            # Generate calendar file
            calendar_url = self.calendar_generator.generate_and_save_deadline_calendar(deadline)
            if calendar_url:
                deadline.ics_file_path = calendar_url
            
            # Update deadline with scheduling info
            self.repository.update_deadline(deadline)
            
            # Send creation notification if recipients provided
            if recipients or self.default_recipients:
                notification_recipients = recipients or self.default_recipients
                self._send_creation_notification(deadline, notification_recipients)
            
            logger.info(f"Successfully created deadline: {deadline.deadline_id}")
            return deadline
            
        except Exception as e:
            logger.error(f"Error creating deadline: {str(e)}")
            return None
    
    def update_deadline(self, 
                       deadline_id: str,
                       updates: Dict[str, Any],
                       updated_by: str = "") -> Optional[Deadline]:
        """
        Update an existing deadline
        
        Args:
            deadline_id: ID of deadline to update
            updates: Dictionary of fields to update
            updated_by: Who updated the deadline
            
        Returns:
            Updated Deadline object if successful, None otherwise
        """
        try:
            # Get existing deadline
            deadline = self.repository.get_deadline(deadline_id)
            if not deadline:
                logger.error(f"Deadline not found: {deadline_id}")
                return None
            
            # Track if due date changed (affects scheduling)
            due_date_changed = 'due_date' in updates and updates['due_date'] != deadline.due_date
            
            # Apply updates
            for field, value in updates.items():
                if hasattr(deadline, field):
                    setattr(deadline, field, value)
            
            deadline.updated_by = updated_by
            deadline.updated_at = datetime.utcnow()
            
            # Update in database
            if not self.repository.update_deadline(deadline):
                logger.error(f"Failed to update deadline in database")
                return None
            
            # Reschedule reminders if due date changed
            if due_date_changed:
                rule_arns = self.scheduler.reschedule_deadline_reminders(deadline)
                deadline.eventbridge_rules = rule_arns
                
                # Regenerate calendar
                calendar_url = self.calendar_generator.generate_and_save_deadline_calendar(deadline)
                if calendar_url:
                    deadline.ics_file_path = calendar_url
                
                # Update again with new scheduling info
                self.repository.update_deadline(deadline)
            
            logger.info(f"Successfully updated deadline: {deadline_id}")
            return deadline
            
        except Exception as e:
            logger.error(f"Error updating deadline: {str(e)}")
            return None
    
    def complete_deadline(self, 
                         deadline_id: str,
                         completion_notes: str = "",
                         completed_by: str = "",
                         recipients: List[str] = None) -> bool:
        """
        Mark a deadline as completed
        
        Args:
            deadline_id: ID of deadline to complete
            completion_notes: Optional completion notes
            completed_by: Who completed the deadline
            recipients: List of notification recipients
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get deadline
            deadline = self.repository.get_deadline(deadline_id)
            if not deadline:
                logger.error(f"Deadline not found: {deadline_id}")
                return False
            
            # Mark as completed
            deadline.mark_completed(completion_notes, completed_by)
            
            # Update in database
            if not self.repository.update_deadline(deadline):
                logger.error(f"Failed to update completed deadline")
                return False
            
            # Clear scheduled reminders
            self.scheduler.clear_deadline_reminders(deadline_id)
            
            # Send completion notification
            if recipients or self.default_recipients:
                notification_recipients = recipients or self.default_recipients
                self.notification_service.send_completion_notification(
                    deadline, notification_recipients, completed_by
                )
            
            logger.info(f"Successfully completed deadline: {deadline_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error completing deadline: {str(e)}")
            return False
    
    def cancel_deadline(self, 
                       deadline_id: str,
                       cancellation_reason: str = "",
                       cancelled_by: str = "") -> bool:
        """
        Cancel a deadline
        
        Args:
            deadline_id: ID of deadline to cancel
            cancellation_reason: Reason for cancellation
            cancelled_by: Who cancelled the deadline
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get deadline
            deadline = self.repository.get_deadline(deadline_id)
            if not deadline:
                logger.error(f"Deadline not found: {deadline_id}")
                return False
            
            # Mark as cancelled
            deadline.mark_cancelled(cancellation_reason, cancelled_by)
            
            # Update in database
            if not self.repository.update_deadline(deadline):
                logger.error(f"Failed to update cancelled deadline")
                return False
            
            # Clear scheduled reminders
            self.scheduler.clear_deadline_reminders(deadline_id)
            
            logger.info(f"Successfully cancelled deadline: {deadline_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling deadline: {str(e)}")
            return False
    
    def get_deadline(self, deadline_id: str) -> Optional[Deadline]:
        """Get a deadline by ID"""
        return self.repository.get_deadline(deadline_id)
    
    def get_matter_deadlines(self, matter_id: str, status: Optional[DeadlineStatus] = None) -> List[Deadline]:
        """Get all deadlines for a matter"""
        return self.repository.get_deadlines_by_matter(matter_id, status)
    
    def get_upcoming_deadlines(self, days_ahead: int = 30) -> List[Deadline]:
        """Get upcoming deadlines"""
        return self.repository.get_upcoming_deadlines(days_ahead)
    
    def get_overdue_deadlines(self) -> List[Deadline]:
        """Get overdue deadlines"""
        return self.repository.get_overdue_deadlines()
    
    def process_deadline_reminders(self) -> Dict[str, Any]:
        """
        Process all deadlines that need reminders sent
        
        Returns:
            Dictionary with processing results
        """
        try:
            deadlines_needing_reminders = self.repository.get_deadlines_needing_reminders()
            
            results = {
                'processed': 0,
                'sent': 0,
                'errors': 0,
                'details': []
            }
            
            for deadline in deadlines_needing_reminders:
                results['processed'] += 1
                
                try:
                    # Determine which reminders to send
                    current_time = datetime.utcnow()
                    
                    for days_before in deadline.reminder_settings.days_before:
                        reminder_date = deadline.due_date - timedelta(days=days_before)
                        
                        # Check if this reminder should be sent now
                        if reminder_date <= current_time:
                            # Check if already sent
                            already_sent = any(
                                r.get('days_before') == days_before 
                                for r in deadline.reminders_sent
                            )
                            
                            if not already_sent:
                                # Send reminder
                                recipients = self.default_recipients
                                notification_result = self.notification_service.send_deadline_reminder(
                                    deadline, days_before, recipients
                                )
                                
                                if notification_result['errors']:
                                    results['errors'] += 1
                                else:
                                    results['sent'] += 1
                                
                                results['details'].append({
                                    'deadline_id': deadline.deadline_id,
                                    'days_before': days_before,
                                    'result': notification_result
                                })
                                
                                # Update deadline with reminder record
                                self.repository.update_deadline(deadline)
                                
                                break  # Only send one reminder per deadline per run
                
                except Exception as e:
                    logger.error(f"Error processing reminder for deadline {deadline.deadline_id}: {str(e)}")
                    results['errors'] += 1
            
            logger.info(f"Processed {results['processed']} deadlines, sent {results['sent']} reminders")
            return results
            
        except Exception as e:
            logger.error(f"Error processing deadline reminders: {str(e)}")
            return {'processed': 0, 'sent': 0, 'errors': 1, 'details': []}
    
    def update_overdue_statuses(self) -> int:
        """
        Update status for overdue deadlines
        
        Returns:
            Number of deadlines updated
        """
        try:
            overdue_deadlines = self.repository.get_overdue_deadlines()
            updated_count = 0
            
            for deadline in overdue_deadlines:
                if deadline.status != DeadlineStatus.OVERDUE:
                    deadline.status = DeadlineStatus.OVERDUE
                    if self.repository.update_deadline(deadline):
                        updated_count += 1
                        
                        # Send overdue notification
                        if self.default_recipients:
                            self.notification_service.send_overdue_notification(
                                deadline, self.default_recipients
                            )
            
            logger.info(f"Updated {updated_count} deadlines to overdue status")
            return updated_count
            
        except Exception as e:
            logger.error(f"Error updating overdue statuses: {str(e)}")
            return 0
    
    def generate_matter_calendar(self, matter_id: str) -> Optional[str]:
        """
        Generate calendar file for all deadlines in a matter
        
        Args:
            matter_id: ID of the matter
            
        Returns:
            S3 URL of generated calendar file
        """
        try:
            deadlines = self.repository.get_deadlines_by_matter(matter_id)
            if not deadlines:
                logger.warning(f"No deadlines found for matter {matter_id}")
                return None
            
            return self.calendar_generator.generate_and_save_matter_calendar(matter_id, deadlines)
            
        except Exception as e:
            logger.error(f"Error generating matter calendar: {str(e)}")
            return None
    
    def search_deadlines(self, **search_criteria) -> List[Deadline]:
        """Search deadlines with various criteria"""
        return self.repository.search_deadlines(**search_criteria)
    
    def get_deadline_statistics(self, matter_id: Optional[str] = None) -> Dict[str, Any]:
        """Get deadline statistics"""
        return self.repository.get_deadline_statistics(matter_id)
    
    def _send_creation_notification(self, deadline: Deadline, recipients: List[str]):
        """Send notification when deadline is created"""
        
        try:
            subject = f"New Deadline Created: {deadline.title}"
            
            message = f"""New Deadline Notification

A new deadline has been created:

Title: {deadline.title}
Due Date: {deadline.due_date.strftime('%A, %B %d, %Y at %I:%M %p')}
Priority: {deadline.priority.value.title()}
Type: {deadline.deadline_type.value.replace('_', ' ').title()}

{f'Description: {deadline.description}' if deadline.description else ''}
Matter ID: {deadline.matter_id}
{f'Court: {deadline.court_name}' if deadline.court_name else ''}
{f'Case Number: {deadline.case_number}' if deadline.case_number else ''}

Reminders will be sent {', '.join(map(str, deadline.reminder_settings.days_before))} days before the due date.

---
Province Legal OS Deadline Management System"""
            
            # Send email notification
            self.notification_service._send_email_notifications(
                deadline, subject, message, recipients
            )
            
        except Exception as e:
            logger.error(f"Error sending creation notification: {str(e)}")
    
    def bulk_update_deadlines(self, 
                            deadline_ids: List[str], 
                            updates: Dict[str, Any],
                            updated_by: str = "") -> Dict[str, Any]:
        """
        Bulk update multiple deadlines
        
        Args:
            deadline_ids: List of deadline IDs to update
            updates: Dictionary of fields to update
            updated_by: Who updated the deadlines
            
        Returns:
            Dictionary with update results
        """
        results = {
            'total': len(deadline_ids),
            'updated': 0,
            'failed': 0,
            'errors': []
        }
        
        for deadline_id in deadline_ids:
            try:
                updated_deadline = self.update_deadline(deadline_id, updates, updated_by)
                if updated_deadline:
                    results['updated'] += 1
                else:
                    results['failed'] += 1
                    results['errors'].append(f"Failed to update deadline {deadline_id}")
            except Exception as e:
                results['failed'] += 1
                results['errors'].append(f"Error updating deadline {deadline_id}: {str(e)}")
        
        return results
    
    def cleanup_completed_deadlines(self, days_old: int = 90) -> int:
        """
        Clean up old completed deadlines
        
        Args:
            days_old: Remove completed deadlines older than this many days
            
        Returns:
            Number of deadlines cleaned up
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            # Get completed deadlines older than cutoff
            completed_deadlines = self.repository.search_deadlines(
                status=DeadlineStatus.COMPLETED,
                limit=1000
            )
            
            cleanup_count = 0
            for deadline in completed_deadlines:
                if deadline.completion_date and deadline.completion_date < cutoff_date:
                    # Delete calendar file if exists
                    if deadline.ics_file_path:
                        s3_key = deadline.ics_file_path.replace(f"s3://{self.calendar_generator.s3_bucket}/", "")
                        self.calendar_generator.delete_calendar_file(s3_key)
                    
                    # Delete deadline
                    if self.repository.delete_deadline(deadline.deadline_id):
                        cleanup_count += 1
            
            logger.info(f"Cleaned up {cleanup_count} old completed deadlines")
            return cleanup_count
            
        except Exception as e:
            logger.error(f"Error cleaning up completed deadlines: {str(e)}")
            return 0