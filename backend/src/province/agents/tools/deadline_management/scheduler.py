"""
Deadline Scheduler

This module provides EventBridge integration for scheduling deadline reminders
and managing automated deadline processing.
"""

import boto3
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from botocore.exceptions import ClientError

from .models import Deadline, DeadlineStatus

logger = logging.getLogger(__name__)


class DeadlineScheduler:
    """EventBridge scheduler for deadline reminders and processing"""
    
    def __init__(self, region_name: str = "us-east-1"):
        self.region_name = region_name
        self.events_client = boto3.client('events', region_name=region_name)
        self.lambda_client = boto3.client('lambda', region_name=region_name)
        
        # Configuration
        self.rule_prefix = "deadline-reminder"
        self.target_lambda_arn = None  # Will be set based on environment
        
    def set_target_lambda_arn(self, lambda_arn: str):
        """Set the target Lambda function ARN for deadline processing"""
        self.target_lambda_arn = lambda_arn
    
    def schedule_deadline_reminders(self, deadline: Deadline) -> List[str]:
        """
        Schedule EventBridge rules for deadline reminders
        
        Args:
            deadline: Deadline object to schedule reminders for
            
        Returns:
            List of created rule ARNs
        """
        created_rules = []
        
        try:
            # Clear existing rules if any
            if deadline.eventbridge_rules:
                self.clear_deadline_reminders(deadline.deadline_id)
            
            # Create reminder rules for each reminder interval
            for days_before in deadline.reminder_settings.days_before:
                reminder_date = deadline.due_date - timedelta(days=days_before)
                
                # Only create rules for future dates
                if reminder_date > datetime.utcnow():
                    rule_arn = self._create_reminder_rule(deadline, days_before, reminder_date)
                    if rule_arn:
                        created_rules.append(rule_arn)
            
            # Create final deadline rule (on due date)
            if deadline.due_date > datetime.utcnow():
                final_rule_arn = self._create_final_deadline_rule(deadline)
                if final_rule_arn:
                    created_rules.append(final_rule_arn)
            
            # Update deadline with rule ARNs
            deadline.eventbridge_rules = created_rules
            
            logger.info(f"Scheduled {len(created_rules)} reminder rules for deadline {deadline.deadline_id}")
            return created_rules
            
        except Exception as e:
            logger.error(f"Error scheduling deadline reminders: {str(e)}")
            return []
    
    def _create_reminder_rule(self, deadline: Deadline, days_before: int, reminder_date: datetime) -> Optional[str]:
        """Create a single reminder rule"""
        
        try:
            rule_name = f"{self.rule_prefix}-{deadline.deadline_id}-{days_before}d"
            
            # Create cron expression for the reminder date
            cron_expression = self._datetime_to_cron(reminder_date)
            
            # Create EventBridge rule
            response = self.events_client.put_rule(
                Name=rule_name,
                ScheduleExpression=cron_expression,
                Description=f"Reminder for deadline '{deadline.title}' ({days_before} days before)",
                State='ENABLED',
                Tags=[
                    {'Key': 'DeadlineId', 'Value': deadline.deadline_id},
                    {'Key': 'MatterId', 'Value': deadline.matter_id},
                    {'Key': 'ReminderType', 'Value': 'reminder'},
                    {'Key': 'DaysBefore', 'Value': str(days_before)}
                ]
            )
            
            rule_arn = response['RuleArn']
            
            # Add target to the rule
            if self.target_lambda_arn:
                self._add_lambda_target(rule_name, deadline, days_before, 'reminder')
            
            logger.info(f"Created reminder rule: {rule_name}")
            return rule_arn
            
        except Exception as e:
            logger.error(f"Error creating reminder rule: {str(e)}")
            return None
    
    def _create_final_deadline_rule(self, deadline: Deadline) -> Optional[str]:
        """Create rule for final deadline notification"""
        
        try:
            rule_name = f"{self.rule_prefix}-{deadline.deadline_id}-final"
            
            # Create cron expression for the due date
            cron_expression = self._datetime_to_cron(deadline.due_date)
            
            # Create EventBridge rule
            response = self.events_client.put_rule(
                Name=rule_name,
                ScheduleExpression=cron_expression,
                Description=f"Final deadline notification for '{deadline.title}'",
                State='ENABLED',
                Tags=[
                    {'Key': 'DeadlineId', 'Value': deadline.deadline_id},
                    {'Key': 'MatterId', 'Value': deadline.matter_id},
                    {'Key': 'ReminderType', 'Value': 'final'},
                    {'Key': 'DaysBefore', 'Value': '0'}
                ]
            )
            
            rule_arn = response['RuleArn']
            
            # Add target to the rule
            if self.target_lambda_arn:
                self._add_lambda_target(rule_name, deadline, 0, 'final')
            
            logger.info(f"Created final deadline rule: {rule_name}")
            return rule_arn
            
        except Exception as e:
            logger.error(f"Error creating final deadline rule: {str(e)}")
            return None
    
    def _add_lambda_target(self, rule_name: str, deadline: Deadline, days_before: int, reminder_type: str):
        """Add Lambda target to EventBridge rule"""
        
        try:
            # Prepare input for Lambda function
            lambda_input = {
                'deadline_id': deadline.deadline_id,
                'matter_id': deadline.matter_id,
                'title': deadline.title,
                'due_date': deadline.due_date.isoformat(),
                'days_before': days_before,
                'reminder_type': reminder_type,
                'reminder_settings': deadline.reminder_settings.to_dict()
            }
            
            # Add target
            self.events_client.put_targets(
                Rule=rule_name,
                Targets=[
                    {
                        'Id': '1',
                        'Arn': self.target_lambda_arn,
                        'Input': json.dumps(lambda_input)
                    }
                ]
            )
            
            # Add permission for EventBridge to invoke Lambda
            try:
                self.lambda_client.add_permission(
                    FunctionName=self.target_lambda_arn,
                    StatementId=f"allow-eventbridge-{rule_name}",
                    Action='lambda:InvokeFunction',
                    Principal='events.amazonaws.com',
                    SourceArn=f"arn:aws:events:{self.region_name}:*:rule/{rule_name}"
                )
            except ClientError as e:
                if e.response['Error']['Code'] != 'ResourceConflictException':
                    raise  # Permission already exists, ignore
            
            logger.info(f"Added Lambda target to rule: {rule_name}")
            
        except Exception as e:
            logger.error(f"Error adding Lambda target: {str(e)}")
    
    def clear_deadline_reminders(self, deadline_id: str) -> bool:
        """
        Clear all EventBridge rules for a deadline
        
        Args:
            deadline_id: ID of the deadline
            
        Returns:
            bool: True if successful
        """
        try:
            # List rules with the deadline ID tag
            response = self.events_client.list_rules(
                NamePrefix=f"{self.rule_prefix}-{deadline_id}"
            )
            
            deleted_count = 0
            for rule in response['Rules']:
                rule_name = rule['Name']
                
                try:
                    # Remove targets first
                    targets_response = self.events_client.list_targets_by_rule(Rule=rule_name)
                    if targets_response['Targets']:
                        target_ids = [target['Id'] for target in targets_response['Targets']]
                        self.events_client.remove_targets(
                            Rule=rule_name,
                            Ids=target_ids
                        )
                    
                    # Delete the rule
                    self.events_client.delete_rule(Name=rule_name)
                    deleted_count += 1
                    
                except Exception as e:
                    logger.error(f"Error deleting rule {rule_name}: {str(e)}")
            
            logger.info(f"Deleted {deleted_count} reminder rules for deadline {deadline_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing deadline reminders: {str(e)}")
            return False
    
    def reschedule_deadline_reminders(self, deadline: Deadline) -> List[str]:
        """
        Reschedule reminders for a deadline (clear old ones and create new ones)
        
        Args:
            deadline: Updated deadline object
            
        Returns:
            List of new rule ARNs
        """
        # Clear existing reminders
        self.clear_deadline_reminders(deadline.deadline_id)
        
        # Schedule new reminders
        return self.schedule_deadline_reminders(deadline)
    
    def _datetime_to_cron(self, dt: datetime) -> str:
        """
        Convert datetime to EventBridge cron expression
        
        Args:
            dt: Datetime to convert
            
        Returns:
            Cron expression string
        """
        # EventBridge cron format: cron(minute hour day month day-of-week year)
        return f"cron({dt.minute} {dt.hour} {dt.day} {dt.month} ? {dt.year})"
    
    def get_scheduled_rules(self, deadline_id: str) -> List[Dict[str, Any]]:
        """
        Get all scheduled rules for a deadline
        
        Args:
            deadline_id: ID of the deadline
            
        Returns:
            List of rule information
        """
        try:
            response = self.events_client.list_rules(
                NamePrefix=f"{self.rule_prefix}-{deadline_id}"
            )
            
            rules_info = []
            for rule in response['Rules']:
                # Get rule tags
                tags_response = self.events_client.list_tags_for_resource(
                    ResourceARN=rule['Arn']
                )
                
                tags = {tag['Key']: tag['Value'] for tag in tags_response['Tags']}
                
                rules_info.append({
                    'name': rule['Name'],
                    'arn': rule['Arn'],
                    'schedule': rule.get('ScheduleExpression', ''),
                    'state': rule['State'],
                    'description': rule.get('Description', ''),
                    'tags': tags
                })
            
            return rules_info
            
        except Exception as e:
            logger.error(f"Error getting scheduled rules: {str(e)}")
            return []
    
    def create_recurring_deadline_check(self) -> str:
        """
        Create a recurring rule to check for overdue deadlines and update statuses
        
        Returns:
            Rule ARN if successful
        """
        try:
            rule_name = "deadline-status-checker"
            
            # Run every hour
            cron_expression = "cron(0 * * * ? *)"
            
            response = self.events_client.put_rule(
                Name=rule_name,
                ScheduleExpression=cron_expression,
                Description="Hourly check for overdue deadlines and status updates",
                State='ENABLED',
                Tags=[
                    {'Key': 'Purpose', 'Value': 'DeadlineStatusCheck'},
                    {'Key': 'System', 'Value': 'ProvinceDeadlineManagement'}
                ]
            )
            
            # Add Lambda target for status checking
            if self.target_lambda_arn:
                lambda_input = {
                    'action': 'status_check',
                    'check_type': 'overdue_and_approaching'
                }
                
                self.events_client.put_targets(
                    Rule=rule_name,
                    Targets=[
                        {
                            'Id': '1',
                            'Arn': self.target_lambda_arn,
                            'Input': json.dumps(lambda_input)
                        }
                    ]
                )
            
            logger.info(f"Created recurring deadline check rule: {rule_name}")
            return response['RuleArn']
            
        except Exception as e:
            logger.error(f"Error creating recurring deadline check: {str(e)}")
            return ""
    
    def pause_deadline_reminders(self, deadline_id: str) -> bool:
        """
        Pause (disable) all reminders for a deadline
        
        Args:
            deadline_id: ID of the deadline
            
        Returns:
            bool: True if successful
        """
        try:
            response = self.events_client.list_rules(
                NamePrefix=f"{self.rule_prefix}-{deadline_id}"
            )
            
            paused_count = 0
            for rule in response['Rules']:
                self.events_client.disable_rule(Name=rule['Name'])
                paused_count += 1
            
            logger.info(f"Paused {paused_count} reminder rules for deadline {deadline_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error pausing deadline reminders: {str(e)}")
            return False
    
    def resume_deadline_reminders(self, deadline_id: str) -> bool:
        """
        Resume (enable) all reminders for a deadline
        
        Args:
            deadline_id: ID of the deadline
            
        Returns:
            bool: True if successful
        """
        try:
            response = self.events_client.list_rules(
                NamePrefix=f"{self.rule_prefix}-{deadline_id}"
            )
            
            resumed_count = 0
            for rule in response['Rules']:
                self.events_client.enable_rule(Name=rule['Name'])
                resumed_count += 1
            
            logger.info(f"Resumed {resumed_count} reminder rules for deadline {deadline_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error resuming deadline reminders: {str(e)}")
            return False