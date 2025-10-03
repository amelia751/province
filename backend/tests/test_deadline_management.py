"""
Unit tests for Deadline Management System

Tests all components of the deadline management system including
models, repository, scheduler, calendar generator, and notifications.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import json

from src.province.agents.tools.deadline_management.models import (
    Deadline, DeadlineStatus, DeadlineType, Priority, ReminderSettings
)
from src.province.agents.tools.deadline_management.repository import DeadlineRepository
from src.province.agents.tools.deadline_management.scheduler import DeadlineScheduler
from src.province.agents.tools.deadline_management.calendar_generator import CalendarGenerator
from src.province.agents.tools.deadline_management.notification_service import NotificationService
from src.province.agents.tools.deadline_management.deadline_service import DeadlineService


class TestDeadlineModels:
    """Test deadline data models"""
    
    def test_deadline_creation(self):
        """Test basic deadline creation"""
        
        due_date = datetime.utcnow() + timedelta(days=7)
        
        deadline = Deadline(
            title="File Motion",
            matter_id="matter-123",
            due_date=due_date,
            deadline_type=DeadlineType.MOTION,
            priority=Priority.HIGH
        )
        
        assert deadline.title == "File Motion"
        assert deadline.matter_id == "matter-123"
        assert deadline.due_date == due_date
        assert deadline.deadline_type == DeadlineType.MOTION
        assert deadline.priority == Priority.HIGH
        assert deadline.status == DeadlineStatus.ACTIVE
    
    def test_deadline_status_updates(self):
        """Test deadline status update logic"""
        
        # Test overdue deadline
        overdue_date = datetime.utcnow() - timedelta(days=1)
        deadline = Deadline(
            title="Overdue Test",
            matter_id="matter-123",
            due_date=overdue_date
        )
        
        deadline.update_status()
        assert deadline.status == DeadlineStatus.OVERDUE
        assert deadline.is_overdue is True
        
        # Test approaching deadline
        approaching_date = datetime.utcnow() + timedelta(days=3)
        deadline2 = Deadline(
            title="Approaching Test",
            matter_id="matter-123",
            due_date=approaching_date
        )
        
        deadline2.update_status()
        assert deadline2.status == DeadlineStatus.APPROACHING
        assert deadline2.is_approaching is True
    
    def test_deadline_completion(self):
        """Test deadline completion"""
        
        deadline = Deadline(
            title="Test Deadline",
            matter_id="matter-123",
            due_date=datetime.utcnow() + timedelta(days=7)
        )
        
        deadline.mark_completed("Task completed successfully", "user-123")
        
        assert deadline.status == DeadlineStatus.COMPLETED
        assert deadline.completion_date is not None
        assert deadline.completion_notes == "Task completed successfully"
        assert deadline.updated_by == "user-123"
    
    def test_reminder_settings(self):
        """Test reminder settings functionality"""
        
        settings = ReminderSettings(
            days_before=[14, 7, 3, 1],
            email_enabled=True,
            sms_enabled=False,
            custom_message="Custom reminder message"
        )
        
        # Test serialization
        settings_dict = settings.to_dict()
        assert settings_dict['days_before'] == [14, 7, 3, 1]
        assert settings_dict['email_enabled'] is True
        assert settings_dict['sms_enabled'] is False
        
        # Test deserialization
        restored_settings = ReminderSettings.from_dict(settings_dict)
        assert restored_settings.days_before == [14, 7, 3, 1]
        assert restored_settings.custom_message == "Custom reminder message"
    
    def test_deadline_serialization(self):
        """Test deadline to/from dict conversion"""
        
        due_date = datetime.utcnow() + timedelta(days=7)
        
        deadline = Deadline(
            title="Test Deadline",
            matter_id="matter-123",
            due_date=due_date,
            deadline_type=DeadlineType.COURT_FILING,
            priority=Priority.CRITICAL,
            court_name="Superior Court",
            case_number="CV-2024-001"
        )
        
        # Test serialization
        deadline_dict = deadline.to_dict()
        assert deadline_dict['title'] == "Test Deadline"
        assert deadline_dict['deadline_type'] == "court_filing"
        assert deadline_dict['priority'] == "critical"
        
        # Test deserialization
        restored_deadline = Deadline.from_dict(deadline_dict)
        assert restored_deadline.title == "Test Deadline"
        assert restored_deadline.deadline_type == DeadlineType.COURT_FILING
        assert restored_deadline.priority == Priority.CRITICAL
        assert restored_deadline.court_name == "Superior Court"


class TestDeadlineRepository:
    """Test deadline repository operations"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.repository = DeadlineRepository("test-table")
    
    @patch('boto3.resource')
    def test_create_deadline(self, mock_boto_resource):
        """Test deadline creation in DynamoDB"""
        
        # Mock DynamoDB table
        mock_table = Mock()
        mock_boto_resource.return_value.Table.return_value = mock_table
        
        deadline = Deadline(
            title="Test Deadline",
            matter_id="matter-123",
            due_date=datetime.utcnow() + timedelta(days=7)
        )
        
        # Mock successful put_item
        mock_table.put_item.return_value = {}
        
        result = self.repository.create_deadline(deadline)
        
        assert result is True
        mock_table.put_item.assert_called_once()
        
        # Check that the call included the deadline data
        call_args = mock_table.put_item.call_args
        assert 'Item' in call_args[1]
        assert call_args[1]['Item']['title'] == "Test Deadline"
    
    @patch('boto3.resource')
    def test_get_deadline(self, mock_boto_resource):
        """Test deadline retrieval"""
        
        mock_table = Mock()
        mock_boto_resource.return_value.Table.return_value = mock_table
        
        # Mock successful get_item
        mock_deadline_data = {
            'deadline_id': 'test-id',
            'title': 'Test Deadline',
            'matter_id': 'matter-123',
            'due_date': (datetime.utcnow() + timedelta(days=7)).isoformat(),
            'deadline_type': 'other',
            'priority': 'medium',
            'status': 'active',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
            'reminder_settings': {
                'days_before': [7, 3, 1],
                'email_enabled': True,
                'sms_enabled': False,
                'push_enabled': True
            },
            'reminders_sent': [],
            'completion_notes': '',
            'jurisdiction': 'federal',
            'eventbridge_rules': []
        }
        
        mock_table.get_item.return_value = {'Item': mock_deadline_data}
        
        deadline = self.repository.get_deadline('test-id')
        
        assert deadline is not None
        assert deadline.title == "Test Deadline"
        assert deadline.matter_id == "matter-123"
        mock_table.get_item.assert_called_once_with(Key={'deadline_id': 'test-id'})
    
    @patch('boto3.resource')
    def test_get_deadlines_by_matter(self, mock_boto_resource):
        """Test getting deadlines by matter ID"""
        
        mock_table = Mock()
        mock_boto_resource.return_value.Table.return_value = mock_table
        
        # Mock query response
        mock_table.query.return_value = {
            'Items': [
                {
                    'deadline_id': 'deadline-1',
                    'title': 'Deadline 1',
                    'matter_id': 'matter-123',
                    'due_date': (datetime.utcnow() + timedelta(days=7)).isoformat(),
                    'deadline_type': 'other',
                    'priority': 'medium',
                    'status': 'active',
                    'created_at': datetime.utcnow().isoformat(),
                    'updated_at': datetime.utcnow().isoformat(),
                    'reminder_settings': {'days_before': [7, 3, 1], 'email_enabled': True, 'sms_enabled': False, 'push_enabled': True},
                    'reminders_sent': [],
                    'completion_notes': '',
                    'jurisdiction': 'federal',
                    'eventbridge_rules': []
                }
            ]
        }
        
        deadlines = self.repository.get_deadlines_by_matter('matter-123')
        
        assert len(deadlines) == 1
        assert deadlines[0].title == "Deadline 1"
        assert deadlines[0].matter_id == "matter-123"


class TestDeadlineScheduler:
    """Test EventBridge scheduling functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.scheduler = DeadlineScheduler()
    
    @patch('boto3.client')
    def test_schedule_deadline_reminders(self, mock_boto_client):
        """Test scheduling EventBridge rules for reminders"""
        
        mock_events = Mock()
        mock_lambda = Mock()
        mock_boto_client.side_effect = lambda service, **kwargs: {
            'events': mock_events,
            'lambda': mock_lambda
        }[service]
        
        # Mock successful rule creation
        mock_events.put_rule.return_value = {'RuleArn': 'arn:aws:events:us-east-1:123456789012:rule/test-rule'}
        mock_events.put_targets.return_value = {}
        mock_lambda.add_permission.return_value = {}
        
        deadline = Deadline(
            title="Test Deadline",
            matter_id="matter-123",
            due_date=datetime.utcnow() + timedelta(days=7)
        )
        
        # Set target Lambda ARN
        self.scheduler.set_target_lambda_arn('arn:aws:lambda:us-east-1:123456789012:function:test')
        
        rule_arns = self.scheduler.schedule_deadline_reminders(deadline)
        
        assert len(rule_arns) > 0
        assert all('arn:aws:events' in arn for arn in rule_arns)
        
        # Verify EventBridge rules were created
        assert mock_events.put_rule.call_count > 0
    
    def test_datetime_to_cron(self):
        """Test datetime to cron expression conversion"""
        
        test_date = datetime(2024, 12, 25, 14, 30, 0)
        cron_expr = self.scheduler._datetime_to_cron(test_date)
        
        expected = "cron(30 14 25 12 ? 2024)"
        assert cron_expr == expected
    
    @patch('boto3.client')
    def test_clear_deadline_reminders(self, mock_boto_client):
        """Test clearing EventBridge rules"""
        
        mock_events = Mock()
        mock_boto_client.return_value = mock_events
        
        # Mock list_rules response
        mock_events.list_rules.return_value = {
            'Rules': [
                {'Name': 'deadline-reminder-test-id-7d'},
                {'Name': 'deadline-reminder-test-id-3d'}
            ]
        }
        
        # Mock other operations
        mock_events.list_targets_by_rule.return_value = {'Targets': []}
        mock_events.remove_targets.return_value = {}
        mock_events.delete_rule.return_value = {}
        
        result = self.scheduler.clear_deadline_reminders('test-id')
        
        assert result is True
        assert mock_events.delete_rule.call_count == 2


class TestCalendarGenerator:
    """Test ICS calendar generation"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.generator = CalendarGenerator("test-bucket")
    
    def test_generate_deadline_ics(self):
        """Test ICS calendar generation for a deadline"""
        
        due_date = datetime(2024, 12, 25, 14, 30, 0)
        
        deadline = Deadline(
            title="Christmas Deadline",
            matter_id="matter-123",
            due_date=due_date,
            description="Important holiday deadline",
            deadline_type=DeadlineType.COURT_FILING,
            priority=Priority.HIGH,
            court_name="Superior Court"
        )
        
        ics_content = self.generator.generate_deadline_ics(deadline)
        
        assert "BEGIN:VCALENDAR" in ics_content
        assert "END:VCALENDAR" in ics_content
        assert "Christmas Deadline" in ics_content
        assert "20241225T143000Z" in ics_content  # Due date in UTC format
        assert "Superior Court" in ics_content
        assert "BEGIN:VALARM" in ics_content  # Should have reminders
    
    def test_generate_matter_calendar(self):
        """Test generating calendar for multiple deadlines"""
        
        deadlines = [
            Deadline(
                title="Deadline 1",
                matter_id="matter-123",
                due_date=datetime.utcnow() + timedelta(days=7)
            ),
            Deadline(
                title="Deadline 2", 
                matter_id="matter-123",
                due_date=datetime.utcnow() + timedelta(days=14)
            )
        ]
        
        ics_content = self.generator.generate_matter_calendar("matter-123", deadlines)
        
        assert "BEGIN:VCALENDAR" in ics_content
        assert "END:VCALENDAR" in ics_content
        assert "Deadline 1" in ics_content
        assert "Deadline 2" in ics_content
        assert ics_content.count("BEGIN:VEVENT") == 2
    
    @patch('boto3.client')
    def test_save_calendar_to_s3(self, mock_boto_client):
        """Test saving calendar to S3"""
        
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3
        
        ics_content = "BEGIN:VCALENDAR\nVERSION:2.0\nEND:VCALENDAR"
        
        mock_s3.put_object.return_value = {}
        
        s3_url = self.generator.save_calendar_to_s3(ics_content, "test/calendar.ics")
        
        assert s3_url == "s3://test-bucket/test/calendar.ics"
        mock_s3.put_object.assert_called_once()
        
        # Check put_object call arguments
        call_args = mock_s3.put_object.call_args
        assert call_args[1]['Bucket'] == 'test-bucket'
        assert call_args[1]['Key'] == 'test/calendar.ics'
        assert call_args[1]['ContentType'] == 'text/calendar'
    
    def test_validate_ics_content(self):
        """Test ICS content validation"""
        
        # Valid ICS content
        valid_ics = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test//Test//EN
BEGIN:VEVENT
SUMMARY:Test Event
END:VEVENT
END:VCALENDAR"""
        
        assert self.generator.validate_ics_content(valid_ics) is True
        
        # Invalid ICS content (missing END:VCALENDAR)
        invalid_ics = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test//Test//EN"""
        
        assert self.generator.validate_ics_content(invalid_ics) is False


class TestNotificationService:
    """Test notification service functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.service = NotificationService()
    
    def test_prepare_reminder_content(self):
        """Test reminder content preparation"""
        
        deadline = Deadline(
            title="Important Deadline",
            matter_id="matter-123",
            due_date=datetime.utcnow() + timedelta(days=3),
            priority=Priority.HIGH,
            description="Critical court filing"
        )
        
        subject, message = self.service._prepare_reminder_content(deadline, 3)
        
        assert "Important Deadline" in subject
        assert "DUE IN 3 DAYS" in subject
        assert "HIGH PRIORITY" in subject
        assert "Important Deadline" in message
        assert "matter-123" in message
        assert "Critical court filing" in message
    
    @patch('boto3.client')
    def test_send_email_notifications(self, mock_boto_client):
        """Test email notification sending"""
        
        mock_ses = Mock()
        mock_boto_client.return_value = mock_ses
        
        deadline = Deadline(
            title="Test Deadline",
            matter_id="matter-123",
            due_date=datetime.utcnow() + timedelta(days=1)
        )
        
        mock_ses.send_email.return_value = {'MessageId': 'test-message-id'}
        
        result = self.service._send_email_notifications(
            deadline, 
            "Test Subject", 
            "Test Message",
            ["test@example.com"]
        )
        
        assert len(result['sent']) == 1
        assert result['sent'][0]['type'] == 'email'
        assert result['sent'][0]['recipient'] == 'test@example.com'
        assert len(result['errors']) == 0
        
        mock_ses.send_email.assert_called_once()
    
    def test_format_html_email(self):
        """Test HTML email formatting"""
        
        deadline = Deadline(
            title="Test Deadline",
            matter_id="matter-123",
            due_date=datetime.utcnow() + timedelta(days=1),
            priority=Priority.CRITICAL,
            court_name="Test Court"
        )
        
        html_content = self.service._format_html_email(deadline, "Test message")
        
        assert "<html>" in html_content
        assert "Test Deadline" in html_content
        assert "Test Court" in html_content
        assert "#dc3545" in html_content  # Critical priority color


class TestDeadlineService:
    """Test main deadline service"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.service = DeadlineService("test-table", "test-bucket")
    
    @patch('src.province.agents.tools.deadline_management.repository.DeadlineRepository')
    @patch('src.province.agents.tools.deadline_management.scheduler.DeadlineScheduler')
    @patch('src.province.agents.tools.deadline_management.calendar_generator.CalendarGenerator')
    def test_create_deadline(self, mock_calendar, mock_scheduler, mock_repository):
        """Test complete deadline creation workflow"""
        
        # Mock successful operations
        mock_repository.return_value.create_deadline.return_value = True
        mock_repository.return_value.update_deadline.return_value = True
        mock_scheduler.return_value.schedule_deadline_reminders.return_value = ['rule-arn-1']
        mock_calendar.return_value.generate_and_save_deadline_calendar.return_value = 's3://test/calendar.ics'
        
        deadline = self.service.create_deadline(
            title="Test Deadline",
            due_date=datetime.utcnow() + timedelta(days=7),
            matter_id="matter-123",
            description="Test description",
            created_by="user-123"
        )
        
        assert deadline is not None
        assert deadline.title == "Test Deadline"
        assert deadline.matter_id == "matter-123"
        assert deadline.created_by == "user-123"
    
    @patch('src.province.agents.tools.deadline_management.repository.DeadlineRepository')
    def test_complete_deadline(self, mock_repository):
        """Test deadline completion"""
        
        # Mock existing deadline
        existing_deadline = Deadline(
            title="Test Deadline",
            matter_id="matter-123",
            due_date=datetime.utcnow() + timedelta(days=7)
        )
        
        mock_repository.return_value.get_deadline.return_value = existing_deadline
        mock_repository.return_value.update_deadline.return_value = True
        
        result = self.service.complete_deadline(
            "test-id",
            "Completed successfully",
            "user-123"
        )
        
        assert result is True
        assert existing_deadline.status == DeadlineStatus.COMPLETED
        assert existing_deadline.completion_notes == "Completed successfully"
        assert existing_deadline.updated_by == "user-123"


if __name__ == "__main__":
    pytest.main([__file__])