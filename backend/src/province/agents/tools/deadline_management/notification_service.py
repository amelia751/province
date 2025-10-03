"""
Notification Service

This module provides SNS integration for deadline notifications
including email, SMS, and push notifications.
"""

import boto3
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from botocore.exceptions import ClientError

from .models import Deadline, DeadlineStatus, Priority

logger = logging.getLogger(__name__)


class NotificationService:
    """SNS-based notification service for deadline reminders"""
    
    def __init__(self, region_name: str = "us-east-1"):
        self.region_name = region_name
        self.sns_client = boto3.client('sns', region_name=region_name)
        self.ses_client = boto3.client('ses', region_name=region_name)
        
        # Configuration
        self.default_topic_arn = None
        self.email_source = "noreply@province-legal-os.com"
        
    def set_default_topic_arn(self, topic_arn: str):
        """Set the default SNS topic ARN for notifications"""
        self.default_topic_arn = topic_arn
    
    def send_deadline_reminder(self, 
                             deadline: Deadline, 
                             days_before: int,
                             recipients: List[str],
                             notification_types: List[str] = None) -> Dict[str, Any]:
        """
        Send deadline reminder notification
        
        Args:
            deadline: Deadline object
            days_before: Number of days before due date
            recipients: List of recipient identifiers (email/phone)
            notification_types: Types of notifications to send ['email', 'sms', 'push']
            
        Returns:
            Dictionary with send results
        """
        if notification_types is None:
            notification_types = ['email']
        
        results = {
            'deadline_id': deadline.deadline_id,
            'days_before': days_before,
            'notifications_sent': [],
            'errors': []
        }
        
        try:
            # Prepare notification content
            subject, message = self._prepare_reminder_content(deadline, days_before)
            
            # Send notifications based on enabled types
            for notification_type in notification_types:
                if notification_type == 'email' and deadline.reminder_settings.email_enabled:
                    email_results = self._send_email_notifications(
                        deadline, subject, message, recipients
                    )
                    results['notifications_sent'].extend(email_results['sent'])
                    results['errors'].extend(email_results['errors'])
                
                elif notification_type == 'sms' and deadline.reminder_settings.sms_enabled:
                    sms_results = self._send_sms_notifications(
                        deadline, message, recipients
                    )
                    results['notifications_sent'].extend(sms_results['sent'])
                    results['errors'].extend(sms_results['errors'])
                
                elif notification_type == 'push' and deadline.reminder_settings.push_enabled:
                    push_results = self._send_push_notifications(
                        deadline, subject, message, recipients
                    )
                    results['notifications_sent'].extend(push_results['sent'])
                    results['errors'].extend(push_results['errors'])
            
            # Record reminder sent
            deadline.add_reminder_sent(
                reminder_type='scheduled',
                recipient=', '.join(recipients),
                success=len(results['errors']) == 0
            )
            
            logger.info(f"Sent {len(results['notifications_sent'])} notifications for deadline {deadline.deadline_id}")
            return results
            
        except Exception as e:
            logger.error(f"Error sending deadline reminder: {str(e)}")
            results['errors'].append(str(e))
            return results
    
    def _prepare_reminder_content(self, deadline: Deadline, days_before: int) -> tuple:
        """Prepare notification subject and message content"""
        
        # Use custom message if provided
        if deadline.reminder_settings.custom_message:
            message = deadline.reminder_settings.custom_message
            subject = f"Deadline Reminder: {deadline.title}"
        else:
            # Generate standard message
            if days_before == 0:
                urgency = "DUE TODAY"
                time_phrase = "today"
            elif days_before == 1:
                urgency = "DUE TOMORROW"
                time_phrase = "tomorrow"
            else:
                urgency = f"DUE IN {days_before} DAYS"
                time_phrase = f"in {days_before} days"
            
            # Priority indicator
            priority_indicator = ""
            if deadline.priority == Priority.CRITICAL:
                priority_indicator = "🚨 CRITICAL: "
            elif deadline.priority == Priority.HIGH:
                priority_indicator = "⚠️ HIGH PRIORITY: "
            
            subject = f"{priority_indicator}Deadline {urgency}: {deadline.title}"
            
            # Build detailed message
            message_parts = [
                f"Deadline Reminder",
                f"",
                f"Title: {deadline.title}",
                f"Due Date: {deadline.due_date.strftime('%A, %B %d, %Y at %I:%M %p')}",
                f"Time Remaining: {time_phrase}",
                f"Priority: {deadline.priority.value.title()}",
                f"Type: {deadline.deadline_type.value.replace('_', ' ').title()}"
            ]
            
            if deadline.description:
                message_parts.extend(["", f"Description: {deadline.description}"])
            
            if deadline.matter_id:
                message_parts.append(f"Matter ID: {deadline.matter_id}")
            
            if deadline.court_name:
                message_parts.append(f"Court: {deadline.court_name}")
            
            if deadline.case_number:
                message_parts.append(f"Case Number: {deadline.case_number}")
            
            message_parts.extend([
                "",
                "Please take appropriate action to meet this deadline.",
                "",
                "---",
                "Province Legal OS Deadline Management System"
            ])
            
            message = "\n".join(message_parts)
        
        return subject, message
    
    def _send_email_notifications(self, 
                                deadline: Deadline, 
                                subject: str, 
                                message: str, 
                                recipients: List[str]) -> Dict[str, List]:
        """Send email notifications using SES"""
        
        results = {'sent': [], 'errors': []}
        
        try:
            # Filter email recipients
            email_recipients = [r for r in recipients if '@' in r]
            
            if not email_recipients:
                return results
            
            # Prepare HTML version of the message
            html_message = self._format_html_email(deadline, message)
            
            for recipient in email_recipients:
                try:
                    response = self.ses_client.send_email(
                        Source=self.email_source,
                        Destination={'ToAddresses': [recipient]},
                        Message={
                            'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                            'Body': {
                                'Text': {'Data': message, 'Charset': 'UTF-8'},
                                'Html': {'Data': html_message, 'Charset': 'UTF-8'}
                            }
                        },
                        Tags=[
                            {'Name': 'DeadlineId', 'Value': deadline.deadline_id},
                            {'Name': 'NotificationType', 'Value': 'deadline_reminder'},
                            {'Name': 'Priority', 'Value': deadline.priority.value}
                        ]
                    )
                    
                    results['sent'].append({
                        'type': 'email',
                        'recipient': recipient,
                        'message_id': response['MessageId'],
                        'sent_at': datetime.utcnow().isoformat()
                    })
                    
                except Exception as e:
                    logger.error(f"Error sending email to {recipient}: {str(e)}")
                    results['errors'].append(f"Email to {recipient}: {str(e)}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in email notification process: {str(e)}")
            results['errors'].append(f"Email process error: {str(e)}")
            return results
    
    def _send_sms_notifications(self, 
                              deadline: Deadline, 
                              message: str, 
                              recipients: List[str]) -> Dict[str, List]:
        """Send SMS notifications using SNS"""
        
        results = {'sent': [], 'errors': []}
        
        try:
            # Filter phone number recipients (simple check for digits)
            phone_recipients = [r for r in recipients if r.replace('+', '').replace('-', '').replace(' ', '').isdigit()]
            
            if not phone_recipients:
                return results
            
            # Prepare SMS message (truncate if too long)
            sms_message = message
            if len(sms_message) > 160:
                sms_message = message[:157] + "..."
            
            for recipient in phone_recipients:
                try:
                    response = self.sns_client.publish(
                        PhoneNumber=recipient,
                        Message=sms_message,
                        MessageAttributes={
                            'AWS.SNS.SMS.SMSType': {
                                'DataType': 'String',
                                'StringValue': 'Transactional'
                            }
                        }
                    )
                    
                    results['sent'].append({
                        'type': 'sms',
                        'recipient': recipient,
                        'message_id': response['MessageId'],
                        'sent_at': datetime.utcnow().isoformat()
                    })
                    
                except Exception as e:
                    logger.error(f"Error sending SMS to {recipient}: {str(e)}")
                    results['errors'].append(f"SMS to {recipient}: {str(e)}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in SMS notification process: {str(e)}")
            results['errors'].append(f"SMS process error: {str(e)}")
            return results
    
    def _send_push_notifications(self, 
                               deadline: Deadline, 
                               subject: str, 
                               message: str, 
                               recipients: List[str]) -> Dict[str, List]:
        """Send push notifications using SNS topics"""
        
        results = {'sent': [], 'errors': []}
        
        try:
            if not self.default_topic_arn:
                results['errors'].append("No default topic ARN configured for push notifications")
                return results
            
            # Prepare push notification payload
            push_payload = {
                'default': message,
                'GCM': json.dumps({
                    'data': {
                        'title': subject,
                        'body': message[:100] + "..." if len(message) > 100 else message,
                        'deadline_id': deadline.deadline_id,
                        'matter_id': deadline.matter_id,
                        'due_date': deadline.due_date.isoformat(),
                        'priority': deadline.priority.value
                    }
                }),
                'APNS': json.dumps({
                    'aps': {
                        'alert': {
                            'title': subject,
                            'body': message[:100] + "..." if len(message) > 100 else message
                        },
                        'badge': 1,
                        'sound': 'default'
                    },
                    'deadline_id': deadline.deadline_id,
                    'matter_id': deadline.matter_id
                })
            }
            
            try:
                response = self.sns_client.publish(
                    TopicArn=self.default_topic_arn,
                    Message=json.dumps(push_payload),
                    MessageStructure='json',
                    MessageAttributes={
                        'DeadlineId': {
                            'DataType': 'String',
                            'StringValue': deadline.deadline_id
                        },
                        'Priority': {
                            'DataType': 'String',
                            'StringValue': deadline.priority.value
                        }
                    }
                )
                
                results['sent'].append({
                    'type': 'push',
                    'recipient': 'topic_subscribers',
                    'message_id': response['MessageId'],
                    'sent_at': datetime.utcnow().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error sending push notification: {str(e)}")
                results['errors'].append(f"Push notification error: {str(e)}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in push notification process: {str(e)}")
            results['errors'].append(f"Push process error: {str(e)}")
            return results
    
    def _format_html_email(self, deadline: Deadline, message: str) -> str:
        """Format HTML version of email message"""
        
        # Priority color coding
        priority_colors = {
            Priority.CRITICAL: '#dc3545',  # Red
            Priority.HIGH: '#fd7e14',      # Orange
            Priority.MEDIUM: '#ffc107',    # Yellow
            Priority.LOW: '#28a745'        # Green
        }
        
        priority_color = priority_colors.get(deadline.priority, '#6c757d')
        
        # Convert plain text message to HTML
        html_lines = message.split('\n')
        html_content = '<br>'.join(html_lines)
        
        html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Deadline Reminder</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f8f9fa; }}
        .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .priority-badge {{ display: inline-block; padding: 4px 12px; border-radius: 4px; color: white; font-weight: bold; background-color: {priority_color}; }}
        .deadline-info {{ background-color: #f8f9fa; padding: 20px; border-radius: 6px; margin: 20px 0; }}
        .footer {{ text-align: center; margin-top: 30px; font-size: 12px; color: #6c757d; }}
        .due-date {{ font-size: 18px; font-weight: bold; color: {priority_color}; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚖️ Deadline Reminder</h1>
            <span class="priority-badge">{deadline.priority.value.upper()}</span>
        </div>
        
        <div class="deadline-info">
            <h2>{deadline.title}</h2>
            <p class="due-date">Due: {deadline.due_date.strftime('%A, %B %d, %Y at %I:%M %p')}</p>
            
            {f'<p><strong>Description:</strong> {deadline.description}</p>' if deadline.description else ''}
            {f'<p><strong>Matter ID:</strong> {deadline.matter_id}</p>' if deadline.matter_id else ''}
            {f'<p><strong>Court:</strong> {deadline.court_name}</p>' if deadline.court_name else ''}
            {f'<p><strong>Case Number:</strong> {deadline.case_number}</p>' if deadline.case_number else ''}
            
            <p><strong>Type:</strong> {deadline.deadline_type.value.replace('_', ' ').title()}</p>
        </div>
        
        <p>Please take appropriate action to meet this deadline.</p>
        
        <div class="footer">
            <p>Province Legal OS Deadline Management System</p>
            <p>This is an automated reminder. Please do not reply to this email.</p>
        </div>
    </div>
</body>
</html>"""
        
        return html_template
    
    def send_overdue_notification(self, deadline: Deadline, recipients: List[str]) -> Dict[str, Any]:
        """Send notification for overdue deadline"""
        
        subject = f"🚨 OVERDUE DEADLINE: {deadline.title}"
        
        overdue_hours = deadline.hours_until_due * -1  # Negative value for overdue
        
        if overdue_hours < 24:
            overdue_text = f"{int(overdue_hours)} hours overdue"
        else:
            overdue_days = int(overdue_hours / 24)
            overdue_text = f"{overdue_days} day{'s' if overdue_days != 1 else ''} overdue"
        
        message = f"""URGENT: Overdue Deadline Alert

Title: {deadline.title}
Due Date: {deadline.due_date.strftime('%A, %B %d, %Y at %I:%M %p')}
Status: {overdue_text}

This deadline has passed and requires immediate attention.

Matter ID: {deadline.matter_id}
Priority: {deadline.priority.value.title()}
Type: {deadline.deadline_type.value.replace('_', ' ').title()}

Please address this overdue deadline immediately.

---
Province Legal OS Deadline Management System"""
        
        return self.send_deadline_reminder(deadline, -1, recipients, ['email', 'push'])
    
    def send_completion_notification(self, deadline: Deadline, recipients: List[str], completed_by: str) -> Dict[str, Any]:
        """Send notification when deadline is completed"""
        
        subject = f"✅ Deadline Completed: {deadline.title}"
        
        message = f"""Deadline Completion Notification

Title: {deadline.title}
Due Date: {deadline.due_date.strftime('%A, %B %d, %Y at %I:%M %p')}
Completed: {deadline.completion_date.strftime('%A, %B %d, %Y at %I:%M %p')}
Completed By: {completed_by}

{f'Notes: {deadline.completion_notes}' if deadline.completion_notes else ''}

Matter ID: {deadline.matter_id}
Type: {deadline.deadline_type.value.replace('_', ' ').title()}

---
Province Legal OS Deadline Management System"""
        
        return self.send_deadline_reminder(deadline, 0, recipients, ['email'])
    
    def create_notification_topic(self, topic_name: str) -> Optional[str]:
        """Create SNS topic for notifications"""
        
        try:
            response = self.sns_client.create_topic(Name=topic_name)
            topic_arn = response['TopicArn']
            
            # Set topic attributes
            self.sns_client.set_topic_attributes(
                TopicArn=topic_arn,
                AttributeName='DisplayName',
                AttributeValue=f'Province Legal OS - {topic_name}'
            )
            
            logger.info(f"Created notification topic: {topic_arn}")
            return topic_arn
            
        except Exception as e:
            logger.error(f"Error creating notification topic: {str(e)}")
            return None
    
    def subscribe_to_notifications(self, topic_arn: str, protocol: str, endpoint: str) -> Optional[str]:
        """Subscribe to notification topic"""
        
        try:
            response = self.sns_client.subscribe(
                TopicArn=topic_arn,
                Protocol=protocol,  # 'email', 'sms', 'application'
                Endpoint=endpoint
            )
            
            subscription_arn = response['SubscriptionArn']
            logger.info(f"Created subscription: {subscription_arn}")
            return subscription_arn
            
        except Exception as e:
            logger.error(f"Error creating subscription: {str(e)}")
            return None