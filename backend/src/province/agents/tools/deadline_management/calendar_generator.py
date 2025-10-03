"""
Calendar Generator

This module provides ICS calendar file generation and S3 storage
for deadline management and calendar integration.
"""

import boto3
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from io import StringIO
import uuid

from .models import Deadline, DeadlineType, Priority

logger = logging.getLogger(__name__)


class CalendarGenerator:
    """Generator for ICS calendar files and S3 storage"""
    
    def __init__(self, s3_bucket: str = "province-legal-calendars", region_name: str = "us-east-1"):
        self.s3_bucket = s3_bucket
        self.region_name = region_name
        self.s3_client = boto3.client('s3', region_name=region_name)
    
    def generate_deadline_ics(self, deadline: Deadline) -> str:
        """
        Generate ICS calendar content for a single deadline
        
        Args:
            deadline: Deadline object to generate calendar for
            
        Returns:
            ICS calendar content as string
        """
        try:
            # Generate unique UID for the event
            event_uid = f"{deadline.deadline_id}@province-legal-os.com"
            
            # Calculate event duration (default 1 hour)
            start_time = deadline.due_date
            end_time = start_time + timedelta(hours=1)
            
            # Format dates for ICS (UTC format)
            start_str = start_time.strftime('%Y%m%dT%H%M%SZ')
            end_str = end_time.strftime('%Y%m%dT%H%M%SZ')
            created_str = deadline.created_at.strftime('%Y%m%dT%H%M%SZ')
            modified_str = deadline.updated_at.strftime('%Y%m%dT%H%M%SZ')
            
            # Build description
            description_parts = [deadline.description] if deadline.description else []
            
            if deadline.matter_id:
                description_parts.append(f"Matter ID: {deadline.matter_id}")
            
            if deadline.court_name:
                description_parts.append(f"Court: {deadline.court_name}")
            
            if deadline.case_number:
                description_parts.append(f"Case Number: {deadline.case_number}")
            
            description_parts.append(f"Priority: {deadline.priority.value.title()}")
            description_parts.append(f"Type: {deadline.deadline_type.value.replace('_', ' ').title()}")
            
            description = "\\n\\n".join(description_parts)
            
            # Determine priority number (1=high, 9=low)
            priority_map = {
                Priority.CRITICAL: 1,
                Priority.HIGH: 3,
                Priority.MEDIUM: 5,
                Priority.LOW: 7
            }
            priority_num = priority_map.get(deadline.priority, 5)
            
            # Build categories
            categories = ["Legal", "Deadline"]
            if deadline.deadline_type != DeadlineType.OTHER:
                categories.append(deadline.deadline_type.value.replace('_', ' ').title())
            
            # Generate ICS content
            ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Province Legal OS//Deadline Calendar//EN
CALSCALE:GREGORIAN
METHOD:PUBLISH
BEGIN:VEVENT
UID:{event_uid}
DTSTART:{start_str}
DTEND:{end_str}
DTSTAMP:{created_str}
CREATED:{created_str}
LAST-MODIFIED:{modified_str}
SUMMARY:{deadline.title}
DESCRIPTION:{description}
LOCATION:{deadline.court_name or 'Legal Department'}
STATUS:CONFIRMED
PRIORITY:{priority_num}
CATEGORIES:{','.join(categories)}
CLASS:PRIVATE"""

            # Add reminders based on reminder settings
            for days_before in deadline.reminder_settings.days_before:
                if days_before > 0:
                    ics_content += f"""
BEGIN:VALARM
TRIGGER:-P{days_before}D
ACTION:DISPLAY
DESCRIPTION:Reminder: {deadline.title} due in {days_before} day{'s' if days_before != 1 else ''}
END:VALARM"""
            
            # Add final reminder (1 hour before)
            ics_content += f"""
BEGIN:VALARM
TRIGGER:-PT1H
ACTION:DISPLAY
DESCRIPTION:Final reminder: {deadline.title} due in 1 hour
END:VALARM
END:VEVENT
END:VCALENDAR"""
            
            return ics_content
            
        except Exception as e:
            logger.error(f"Error generating ICS for deadline {deadline.deadline_id}: {str(e)}")
            return ""
    
    def generate_matter_calendar(self, matter_id: str, deadlines: List[Deadline]) -> str:
        """
        Generate ICS calendar for all deadlines in a matter
        
        Args:
            matter_id: ID of the matter
            deadlines: List of deadlines for the matter
            
        Returns:
            ICS calendar content as string
        """
        try:
            if not deadlines:
                return ""
            
            # Calendar header
            ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Province Legal OS//Matter Calendar//EN
CALSCALE:GREGORIAN
METHOD:PUBLISH
X-WR-CALNAME:Matter {matter_id} Deadlines
X-WR-CALDESC:Legal deadlines for matter {matter_id}
X-WR-TIMEZONE:UTC"""
            
            # Add each deadline as an event
            for deadline in deadlines:
                event_content = self._generate_event_content(deadline)
                ics_content += "\n" + event_content
            
            ics_content += "\nEND:VCALENDAR"
            
            return ics_content
            
        except Exception as e:
            logger.error(f"Error generating matter calendar for {matter_id}: {str(e)}")
            return ""
    
    def _generate_event_content(self, deadline: Deadline) -> str:
        """Generate VEVENT content for a deadline"""
        
        event_uid = f"{deadline.deadline_id}@province-legal-os.com"
        start_time = deadline.due_date
        end_time = start_time + timedelta(hours=1)
        
        start_str = start_time.strftime('%Y%m%dT%H%M%SZ')
        end_str = end_time.strftime('%Y%m%dT%H%M%SZ')
        created_str = deadline.created_at.strftime('%Y%m%dT%H%M%SZ')
        
        # Build description
        description_parts = []
        if deadline.description:
            description_parts.append(deadline.description)
        
        description_parts.extend([
            f"Matter ID: {deadline.matter_id}",
            f"Priority: {deadline.priority.value.title()}",
            f"Type: {deadline.deadline_type.value.replace('_', ' ').title()}"
        ])
        
        if deadline.court_name:
            description_parts.append(f"Court: {deadline.court_name}")
        
        description = "\\n".join(description_parts)
        
        event_content = f"""BEGIN:VEVENT
UID:{event_uid}
DTSTART:{start_str}
DTEND:{end_str}
DTSTAMP:{created_str}
SUMMARY:{deadline.title}
DESCRIPTION:{description}
LOCATION:{deadline.court_name or 'Legal Department'}
STATUS:CONFIRMED
CATEGORIES:Legal,Deadline
END:VEVENT"""
        
        return event_content
    
    def save_calendar_to_s3(self, ics_content: str, file_key: str) -> Optional[str]:
        """
        Save ICS calendar content to S3
        
        Args:
            ics_content: ICS calendar content
            file_key: S3 key for the file
            
        Returns:
            S3 URL if successful, None otherwise
        """
        try:
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=file_key,
                Body=ics_content.encode('utf-8'),
                ContentType='text/calendar',
                ContentDisposition=f'attachment; filename="{file_key.split("/")[-1]}"',
                Metadata={
                    'generated_at': datetime.utcnow().isoformat(),
                    'generator': 'province-legal-os'
                }
            )
            
            # Generate S3 URL
            s3_url = f"s3://{self.s3_bucket}/{file_key}"
            
            logger.info(f"Saved calendar to S3: {s3_url}")
            return s3_url
            
        except Exception as e:
            logger.error(f"Error saving calendar to S3: {str(e)}")
            return None
    
    def generate_and_save_deadline_calendar(self, deadline: Deadline) -> Optional[str]:
        """
        Generate and save calendar for a single deadline
        
        Args:
            deadline: Deadline to generate calendar for
            
        Returns:
            S3 URL if successful, None otherwise
        """
        try:
            # Generate ICS content
            ics_content = self.generate_deadline_ics(deadline)
            if not ics_content:
                return None
            
            # Generate S3 key
            file_key = f"deadlines/{deadline.matter_id}/{deadline.deadline_id}.ics"
            
            # Save to S3
            s3_url = self.save_calendar_to_s3(ics_content, file_key)
            
            # Update deadline with calendar info
            if s3_url:
                deadline.ics_file_path = s3_url
                deadline.calendar_event_id = f"{deadline.deadline_id}@province-legal-os.com"
            
            return s3_url
            
        except Exception as e:
            logger.error(f"Error generating and saving deadline calendar: {str(e)}")
            return None
    
    def generate_and_save_matter_calendar(self, matter_id: str, deadlines: List[Deadline]) -> Optional[str]:
        """
        Generate and save calendar for all deadlines in a matter
        
        Args:
            matter_id: ID of the matter
            deadlines: List of deadlines for the matter
            
        Returns:
            S3 URL if successful, None otherwise
        """
        try:
            # Generate ICS content
            ics_content = self.generate_matter_calendar(matter_id, deadlines)
            if not ics_content:
                return None
            
            # Generate S3 key with timestamp
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            file_key = f"matters/{matter_id}/calendar_{timestamp}.ics"
            
            # Save to S3
            return self.save_calendar_to_s3(ics_content, file_key)
            
        except Exception as e:
            logger.error(f"Error generating and saving matter calendar: {str(e)}")
            return None
    
    def get_calendar_download_url(self, s3_key: str, expiration: int = 3600) -> Optional[str]:
        """
        Generate a presigned URL for calendar download
        
        Args:
            s3_key: S3 key of the calendar file
            expiration: URL expiration time in seconds
            
        Returns:
            Presigned URL if successful, None otherwise
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.s3_bucket, 'Key': s3_key},
                ExpiresIn=expiration
            )
            
            return url
            
        except Exception as e:
            logger.error(f"Error generating presigned URL: {str(e)}")
            return None
    
    def delete_calendar_file(self, s3_key: str) -> bool:
        """
        Delete a calendar file from S3
        
        Args:
            s3_key: S3 key of the file to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.s3_bucket,
                Key=s3_key
            )
            
            logger.info(f"Deleted calendar file: {s3_key}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting calendar file: {str(e)}")
            return False
    
    def generate_recurring_deadline_calendar(self, 
                                           title: str,
                                           start_date: datetime,
                                           end_date: datetime,
                                           recurrence_rule: str,
                                           matter_id: str) -> str:
        """
        Generate ICS content for recurring deadlines
        
        Args:
            title: Title of the recurring deadline
            start_date: Start date for recurrence
            end_date: End date for recurrence
            recurrence_rule: RRULE string for recurrence pattern
            matter_id: Associated matter ID
            
        Returns:
            ICS calendar content
        """
        try:
            event_uid = f"recurring-{uuid.uuid4()}@province-legal-os.com"
            
            start_str = start_date.strftime('%Y%m%dT%H%M%SZ')
            end_str = (start_date + timedelta(hours=1)).strftime('%Y%m%dT%H%M%SZ')
            until_str = end_date.strftime('%Y%m%dT%H%M%SZ')
            
            ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Province Legal OS//Recurring Deadline Calendar//EN
CALSCALE:GREGORIAN
METHOD:PUBLISH
BEGIN:VEVENT
UID:{event_uid}
DTSTART:{start_str}
DTEND:{end_str}
DTSTAMP:{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}
SUMMARY:{title}
DESCRIPTION:Recurring deadline for matter {matter_id}
LOCATION:Legal Department
STATUS:CONFIRMED
CATEGORIES:Legal,Deadline,Recurring
RRULE:{recurrence_rule};UNTIL={until_str}
BEGIN:VALARM
TRIGGER:-P1D
ACTION:DISPLAY
DESCRIPTION:Reminder: {title} due tomorrow
END:VALARM
END:VEVENT
END:VCALENDAR"""
            
            return ics_content
            
        except Exception as e:
            logger.error(f"Error generating recurring deadline calendar: {str(e)}")
            return ""
    
    def validate_ics_content(self, ics_content: str) -> bool:
        """
        Validate ICS calendar content
        
        Args:
            ics_content: ICS content to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Basic validation checks
            required_elements = [
                'BEGIN:VCALENDAR',
                'END:VCALENDAR',
                'VERSION:2.0',
                'PRODID:'
            ]
            
            for element in required_elements:
                if element not in ics_content:
                    logger.error(f"Missing required element: {element}")
                    return False
            
            # Check for balanced BEGIN/END pairs
            begin_count = ics_content.count('BEGIN:')
            end_count = ics_content.count('END:')
            
            if begin_count != end_count:
                logger.error(f"Unbalanced BEGIN/END pairs: {begin_count} vs {end_count}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating ICS content: {str(e)}")
            return False