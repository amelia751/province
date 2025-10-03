"""
AWS Lambda Function: Create Deadline

This Lambda function creates deadlines with EventBridge scheduling and SNS notifications.
Deployed as: province-create-deadline
"""

import json
import boto3
import logging
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
events_client = boto3.client('events')
sns_client = boto3.client('sns')


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Create a deadline with EventBridge scheduling and notifications
    
    Args:
        event: Lambda event containing deadline data
        context: Lambda context
        
    Returns:
        Dict containing deadline creation results
    """
    try:
        # Parse request body
        if 'body' in event:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        else:
            body = event
            
        matter_id = body.get('matter_id')
        title = body.get('title')
        due_date_str = body.get('due_date')
        description = body.get('description', '')
        reminder_days = body.get('reminder_days', [7, 3, 1])  # Default reminders
        
        if not all([matter_id, title, due_date_str]):
            raise ValueError("Missing required fields: matter_id, title, due_date")
            
        # Parse due date
        try:
            due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
        except ValueError:
            raise ValueError(f"Invalid due_date format: {due_date_str}. Use ISO format.")
            
        logger.info(f"Creating deadline: {title} for matter: {matter_id}, due: {due_date}")
        
        # Generate deadline ID
        deadline_id = str(uuid.uuid4())
        created_at = datetime.utcnow()
        
        # Save deadline to DynamoDB
        table_name = os.environ.get('DYNAMODB_TABLE')
        if not table_name:
            raise ValueError("DYNAMODB_TABLE environment variable not set")
            
        table = dynamodb.Table(table_name)
        
        deadline_item = {
            'deadline_id': deadline_id,
            'matter_id': matter_id,
            'title': title,
            'description': description,
            'due_date': due_date.isoformat(),
            'created_at': created_at.isoformat(),
            'status': 'active',
            'reminder_days': reminder_days,
            'notifications_sent': []
        }
        
        table.put_item(Item=deadline_item)
        logger.info(f"Deadline saved to DynamoDB: {deadline_id}")
        
        # Create EventBridge rules for reminders
        rule_arns = []
        
        for days_before in reminder_days:
            reminder_date = due_date - timedelta(days=days_before)
            
            # Only create reminders for future dates
            if reminder_date > datetime.utcnow():
                rule_name = f"deadline-reminder-{deadline_id}-{days_before}d"
                
                # Create EventBridge rule
                cron_expression = f"cron({reminder_date.minute} {reminder_date.hour} {reminder_date.day} {reminder_date.month} ? {reminder_date.year})"
                
                events_client.put_rule(
                    Name=rule_name,
                    ScheduleExpression=cron_expression,
                    Description=f"Reminder for deadline: {title} ({days_before} days before)",
                    State='ENABLED'
                )
                
                # Add SNS target to the rule
                sns_topic_arn = os.environ.get('SNS_TOPIC_ARN')
                if sns_topic_arn:
                    target_input = {
                        'deadline_id': deadline_id,
                        'matter_id': matter_id,
                        'title': title,
                        'due_date': due_date.isoformat(),
                        'days_before': days_before,
                        'reminder_type': 'deadline_reminder'
                    }
                    
                    events_client.put_targets(
                        Rule=rule_name,
                        Targets=[
                            {
                                'Id': '1',
                                'Arn': sns_topic_arn,
                                'Input': json.dumps(target_input)
                            }
                        ]
                    )
                
                rule_arn = f"arn:aws:events:{os.environ.get('AWS_REGION', 'us-east-1')}:{context.invoked_function_arn.split(':')[4]}:rule/{rule_name}"
                rule_arns.append(rule_arn)
                
                logger.info(f"Created reminder rule: {rule_name} for {reminder_date}")
        
        # Create final deadline notification
        final_rule_name = f"deadline-final-{deadline_id}"
        final_cron = f"cron({due_date.minute} {due_date.hour} {due_date.day} {due_date.month} ? {due_date.year})"
        
        events_client.put_rule(
            Name=final_rule_name,
            ScheduleExpression=final_cron,
            Description=f"Final deadline notification: {title}",
            State='ENABLED'
        )
        
        # Add SNS target for final notification
        sns_topic_arn = os.environ.get('SNS_TOPIC_ARN')
        if sns_topic_arn:
            final_target_input = {
                'deadline_id': deadline_id,
                'matter_id': matter_id,
                'title': title,
                'due_date': due_date.isoformat(),
                'days_before': 0,
                'reminder_type': 'deadline_due'
            }
            
            events_client.put_targets(
                Rule=final_rule_name,
                Targets=[
                    {
                        'Id': '1',
                        'Arn': sns_topic_arn,
                        'Input': json.dumps(final_target_input)
                    }
                ]
            )
        
        final_rule_arn = f"arn:aws:events:{os.environ.get('AWS_REGION', 'us-east-1')}:{context.invoked_function_arn.split(':')[4]}:rule/{final_rule_name}"
        rule_arns.append(final_rule_arn)
        
        # Generate calendar file (ICS format)
        ics_content = generate_ics_calendar(deadline_id, title, description, due_date, matter_id)
        
        # Save calendar file to S3 (optional)
        try:
            s3_client = boto3.client('s3')
            calendar_bucket = os.environ.get('CALENDAR_BUCKET', 'province-legal-calendars')
            calendar_key = f"deadlines/{matter_id}/{deadline_id}.ics"
            
            s3_client.put_object(
                Bucket=calendar_bucket,
                Key=calendar_key,
                Body=ics_content,
                ContentType='text/calendar'
            )
            
            calendar_url = f"s3://{calendar_bucket}/{calendar_key}"
            logger.info(f"Calendar file saved: {calendar_url}")
            
        except Exception as e:
            logger.warning(f"Failed to save calendar file: {str(e)}")
            calendar_url = None
        
        # Prepare response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'result': f"Deadline '{title}' created successfully for matter {matter_id}",
                'success': True,
                'data': {
                    'deadline_id': deadline_id,
                    'matter_id': matter_id,
                    'title': title,
                    'description': description,
                    'due_date': due_date.isoformat(),
                    'created_at': created_at.isoformat(),
                    'reminder_days': reminder_days,
                    'eventbridge_rules': rule_arns,
                    'calendar_url': calendar_url,
                    'ics_content': ics_content
                }
            })
        }
        
    except Exception as e:
        logger.error(f"Deadline creation error: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'result': f"Failed to create deadline: {str(e)}",
                'success': False,
                'error': str(e)
            })
        }


def generate_ics_calendar(deadline_id: str, title: str, description: str, due_date: datetime, matter_id: str) -> str:
    """Generate ICS calendar content for the deadline"""
    
    ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Province Legal OS//Deadline Calendar//EN
CALSCALE:GREGORIAN
METHOD:PUBLISH
BEGIN:VEVENT
UID:{deadline_id}@province-legal-os.com
DTSTART:{due_date.strftime('%Y%m%dT%H%M%SZ')}
DTEND:{(due_date + timedelta(hours=1)).strftime('%Y%m%dT%H%M%SZ')}
SUMMARY:{title}
DESCRIPTION:Legal deadline for matter {matter_id}\\n\\n{description}
LOCATION:Legal Department
STATUS:CONFIRMED
PRIORITY:5
CATEGORIES:Legal,Deadline
BEGIN:VALARM
TRIGGER:-P1D
ACTION:DISPLAY
DESCRIPTION:Reminder: {title} due tomorrow
END:VALARM
BEGIN:VALARM
TRIGGER:-P3D
ACTION:DISPLAY
DESCRIPTION:Reminder: {title} due in 3 days
END:VALARM
END:VEVENT
END:VCALENDAR"""
    
    return ics_content


# For local testing
if __name__ == "__main__":
    test_event = {
        "matter_id": "matter-123",
        "title": "File Motion for Summary Judgment",
        "due_date": "2024-12-31T17:00:00Z",
        "description": "Motion must be filed before court closes",
        "reminder_days": [7, 3, 1]
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))