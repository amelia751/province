"""Create tax deadline tool."""

import json
import logging
from typing import Dict, Any, List
from datetime import datetime
import boto3

from province.core.config import get_settings
# DeadlinesAgent implementation moved inline

logger = logging.getLogger(__name__)


async def create_deadline(engagement_id: str, title: str, due_at_iso: str, reminders: List[int]) -> Dict[str, Any]:
    """
    Create a tax deadline with calendar events.
    
    Args:
        engagement_id: The tax engagement ID
        title: Deadline title
        due_at_iso: Due date in ISO format
        reminders: List of reminder days before due date
    
    Returns:
        Dict with deadline creation results
    """
    
    try:
        # Parse due date
        due_date = datetime.fromisoformat(due_at_iso.replace('Z', '+00:00'))
        
        # Generate simple ICS content for tax deadline
        tax_year = 2025
        ics_content = _generate_simple_ics_content(title, due_date, reminders)
        
        # Save ICS file
        from .save_document import save_document
        import base64
        
        result = await save_document(
            engagement_id=engagement_id,
            path="/Deadlines/Federal.ics",
            content_b64=base64.b64encode(ics_content.encode('utf-8')).decode('utf-8'),
            mime_type="text/calendar"
        )
        
        if not result['success']:
            return result
        
        # Save deadline information to DynamoDB
        await _save_deadline_info(engagement_id, title, due_date, reminders)
        
        logger.info(f"Created tax deadline for engagement {engagement_id}")
        
        return {
            'success': True,
            'deadline_title': title,
            'due_date': due_at_iso,
            'ics_path': '/Deadlines/Federal.ics',
            's3_key': result['s3_key'],
            'events_count': 1
        }
        
    except Exception as e:
        logger.error(f"Error creating deadline: {e}")
        return {
            'success': False,
            'error': str(e)
        }


async def _save_deadline_info(engagement_id: str, title: str, due_date: datetime, reminders: List[int]) -> None:
    """Save deadline information to DynamoDB."""
    
    settings = get_settings()
    
    try:
        dynamodb = boto3.resource('dynamodb', region_name=settings.aws_region)
        table = dynamodb.Table(settings.tax_deadlines_table_name)
        
        # Extract tenant_id from engagement_id
        if '#' in engagement_id:
            tenant_id = engagement_id.split('#')[0]
        else:
            tenant_id = "default"
        
        deadline_id = f"federal_{due_date.strftime('%Y%m%d')}"
        
        table.put_item(
            Item={
                'tenant_id#engagement_id': f"{tenant_id}#{engagement_id}",
                'deadline#deadline_id': f"deadline#{deadline_id}",
                'title': title,
                'due_date': due_date.isoformat(),
                'reminders': reminders,
                'acknowledged': False,
                'owner_user_id': tenant_id,  # Simplified
                'created_at': datetime.now().isoformat()
            }
        )
        
        logger.info(f"Saved deadline info for engagement {engagement_id}")
        
    except Exception as e:
        logger.error(f"Error saving deadline info: {e}")
        raise


def _generate_simple_ics_content(title: str, due_date: datetime, reminders: List[int]) -> str:
    """Generate simple ICS calendar content."""
    
    ics_content = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Province Tax//Tax Deadlines//EN
CALSCALE:GREGORIAN
METHOD:PUBLISH
BEGIN:VEVENT
UID:{uid}@province-tax.com
DTSTART:{start_date}
DTEND:{end_date}
SUMMARY:{title}
DESCRIPTION:Tax filing deadline for 2025 tax year
LOCATION:Online
STATUS:CONFIRMED
TRANSP:OPAQUE
END:VEVENT
END:VCALENDAR""".format(
        uid=f"tax-deadline-{due_date.strftime('%Y%m%d')}",
        start_date=due_date.strftime('%Y%m%dT%H%M%SZ'),
        end_date=due_date.strftime('%Y%m%dT%H%M%SZ'),
        title=title
    )
    
    return ics_content
