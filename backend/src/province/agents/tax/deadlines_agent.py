"""Deadlines Agent - Creates tax filing deadlines and calendar events."""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from calendar import monthrange

from province.core.config import get_settings
from province.agents.bedrock_agent_client import BedrockAgentClient

logger = logging.getLogger(__name__)


class DeadlinesAgent:
    """
    Deadlines Agent - Creates tax filing deadlines and calendar reminders.
    
    This agent:
    1. Calculates federal filing deadline (April 15, adjusted for weekends/holidays)
    2. Creates .ics calendar file with filing deadline
    3. Adds reminder events (30, 7, 1 days prior)
    4. Includes extension fallback information (Form 4868)
    5. Saves to /Deadlines/Federal.ics
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.bedrock_client = BedrockAgentClient()
        self.agent_id = None
        self.agent_alias_id = None
        
    async def create_agent(self) -> str:
        """Create the Deadlines Agent in AWS Bedrock."""
        
        instruction = """You are the Deadlines Agent for Province Tax Filing System. Your job is to create accurate tax filing deadlines and helpful calendar reminders.

DEADLINE CALCULATION:
1. Standard federal filing deadline is April 15 of the year following the tax year
2. If April 15 falls on a weekend or federal holiday, move to next business day
3. Consider major federal holidays: New Year's Day, MLK Day, Presidents Day, Memorial Day, Independence Day, Labor Day, Columbus Day, Veterans Day, Thanksgiving, Christmas
4. Washington D.C. Emancipation Day (April 16) can also affect the deadline

CALENDAR EVENT CREATION:
1. Main filing deadline event
2. Reminder 30 days before deadline
3. Reminder 7 days before deadline  
4. Reminder 1 day before deadline
5. Extension deadline (October 15) if close to original deadline

ICS FILE FORMAT:
- Use standard iCalendar format
- Include VTIMEZONE for proper time handling
- Set appropriate DTSTART and DTEND times
- Add SUMMARY, DESCRIPTION, and LOCATION fields
- Include VALARM for reminders
- Set PRIORITY and CATEGORIES appropriately

EXTENSION INFORMATION:
- Form 4868 extends filing deadline to October 15
- Extension is automatic if filed by original deadline
- Must still pay estimated taxes by original deadline
- No penalty for extension if no tax is owed"""

        tools = [
            {
                "toolSpec": {
                    "name": "calculate_filing_deadline",
                    "description": "Calculate the federal tax filing deadline",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "tax_year": {"type": "integer"}
                            },
                            "required": ["tax_year"]
                        }
                    }
                }
            },
            {
                "toolSpec": {
                    "name": "check_federal_holidays",
                    "description": "Check if a date falls on a federal holiday",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "date": {"type": "string"},
                                "year": {"type": "integer"}
                            },
                            "required": ["date", "year"]
                        }
                    }
                }
            },
            {
                "toolSpec": {
                    "name": "generate_ics_calendar",
                    "description": "Generate ICS calendar file with deadlines",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "events": {"type": "array"},
                                "tax_year": {"type": "integer"}
                            },
                            "required": ["events", "tax_year"]
                        }
                    }
                }
            },
            {
                "toolSpec": {
                    "name": "save_deadline_calendar",
                    "description": "Save the deadline calendar file",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "engagement_id": {"type": "string"},
                                "ics_content": {"type": "string"},
                                "deadline_info": {"type": "object"}
                            },
                            "required": ["engagement_id", "ics_content"]
                        }
                    }
                }
            }
        ]
        
        # Create the agent
        response = await self.bedrock_client.create_agent(
            agent_name="DeadlinesAgent",
            instruction=instruction,
            foundation_model="anthropic.claude-3-5-sonnet-20241022-v2:0",
            tools=tools
        )
        
        self.agent_id = response["agent"]["agentId"]
        logger.info(f"Created Deadlines agent with ID: {self.agent_id}")
        
        # Create alias
        alias_response = await self.bedrock_client.create_agent_alias(
            agent_id=self.agent_id,
            agent_alias_name="DRAFT"
        )
        
        self.agent_alias_id = alias_response["agentAlias"]["agentAliasId"]
        logger.info(f"Created agent alias with ID: {self.agent_alias_id}")
        
        return self.agent_id
    
    async def invoke(self, session_id: str, input_text: str, engagement_id: str) -> Dict[str, Any]:
        """Invoke the Deadlines agent."""
        
        if not self.agent_id or not self.agent_alias_id:
            raise ValueError("Agent not deployed. Call create_agent() first.")
        
        # Add engagement context
        input_text = f"[ENGAGEMENT_ID: {engagement_id}] {input_text}"
        
        response = await self.bedrock_client.invoke_agent(
            agent_id=self.agent_id,
            agent_alias_id=self.agent_alias_id,
            session_id=session_id,
            input_text=input_text
        )
        
        return response
    
    def calculate_filing_deadline(self, tax_year: int) -> datetime:
        """Calculate the federal tax filing deadline for a given tax year."""
        
        # Standard deadline is April 15 of the following year
        deadline_year = tax_year + 1
        deadline = datetime(deadline_year, 4, 15)
        
        # Check if it falls on a weekend
        while deadline.weekday() >= 5:  # Saturday = 5, Sunday = 6
            deadline += timedelta(days=1)
        
        # Check for federal holidays that might affect the deadline
        if self._is_federal_holiday(deadline):
            deadline += timedelta(days=1)
            # Check again in case the next day is also a holiday or weekend
            while deadline.weekday() >= 5 or self._is_federal_holiday(deadline):
                deadline += timedelta(days=1)
        
        return deadline
    
    def _is_federal_holiday(self, date: datetime) -> bool:
        """Check if a date is a federal holiday that affects tax deadlines."""
        
        year = date.year
        month = date.month
        day = date.day
        
        # Fixed date holidays
        fixed_holidays = [
            (1, 1),   # New Year's Day
            (7, 4),   # Independence Day
            (11, 11), # Veterans Day
            (12, 25), # Christmas Day
        ]
        
        if (month, day) in fixed_holidays:
            return True
        
        # Washington D.C. Emancipation Day (April 16)
        if month == 4 and day == 16:
            return True
        
        # Variable holidays (simplified - would need more complex logic for exact dates)
        # MLK Day (3rd Monday in January)
        # Presidents Day (3rd Monday in February)
        # Memorial Day (last Monday in May)
        # Labor Day (1st Monday in September)
        # Columbus Day (2nd Monday in October)
        # Thanksgiving (4th Thursday in November)
        
        return False
    
    def generate_ics_content(self, events: List[Dict[str, Any]], tax_year: int) -> str:
        """Generate ICS calendar content for tax deadlines."""
        
        ics_content = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Province Tax Filing System//Tax Deadlines//EN
CALSCALE:GREGORIAN
METHOD:PUBLISH
X-WR-CALNAME:Tax Filing Deadlines {tax_year}
X-WR-TIMEZONE:America/New_York
BEGIN:VTIMEZONE
TZID:America/New_York
BEGIN:DAYLIGHT
TZOFFSETFROM:-0500
TZOFFSETTO:-0400
TZNAME:EDT
DTSTART:20070311T020000
RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=2SU
END:DAYLIGHT
BEGIN:STANDARD
TZOFFSETFROM:-0400
TZOFFSETTO:-0500
TZNAME:EST
DTSTART:20071104T020000
RRULE:FREQ=YEARLY;BYMONTH=11;BYDAY=1SU
END:STANDARD
END:VTIMEZONE
""".format(tax_year=tax_year)
        
        for event in events:
            event_start = event['start_date'].strftime('%Y%m%dT%H%M%S')
            event_end = event['end_date'].strftime('%Y%m%dT%H%M%S')
            uid = f"{event['type']}-{tax_year}-{event_start}@province-tax.com"
            
            ics_content += f"""BEGIN:VEVENT
UID:{uid}
DTSTART;TZID=America/New_York:{event_start}
DTEND;TZID=America/New_York:{event_end}
SUMMARY:{event['summary']}
DESCRIPTION:{event['description']}
LOCATION:Online - Province Tax Filing System
CATEGORIES:TAX,DEADLINE
PRIORITY:{event.get('priority', 5)}
STATUS:CONFIRMED
TRANSP:OPAQUE
"""
            
            # Add alarm for reminders
            if event.get('reminder_minutes'):
                ics_content += f"""BEGIN:VALARM
ACTION:DISPLAY
DESCRIPTION:Reminder: {event['summary']}
TRIGGER:-PT{event['reminder_minutes']}M
END:VALARM
"""
            
            ics_content += "END:VEVENT\n"
        
        ics_content += "END:VCALENDAR\n"
        
        return ics_content
    
    def create_deadline_events(self, tax_year: int) -> List[Dict[str, Any]]:
        """Create all deadline-related calendar events."""
        
        filing_deadline = self.calculate_filing_deadline(tax_year)
        extension_deadline = datetime(tax_year + 1, 10, 15)
        
        events = []
        
        # Main filing deadline
        events.append({
            'type': 'filing_deadline',
            'start_date': filing_deadline.replace(hour=9, minute=0),
            'end_date': filing_deadline.replace(hour=23, minute=59),
            'summary': f'{tax_year} Federal Tax Return Due',
            'description': f'Federal tax return for {tax_year} is due today. File your return or request an extension (Form 4868) to avoid penalties.',
            'priority': 1,
            'reminder_minutes': 60  # 1 hour before
        })
        
        # 30-day reminder
        reminder_30 = filing_deadline - timedelta(days=30)
        events.append({
            'type': 'reminder_30',
            'start_date': reminder_30.replace(hour=9, minute=0),
            'end_date': reminder_30.replace(hour=9, minute=30),
            'summary': f'Tax Deadline Reminder - 30 Days',
            'description': f'Your {tax_year} federal tax return is due in 30 days ({filing_deadline.strftime("%B %d, %Y")}). Start gathering your documents if you haven\'t already.',
            'priority': 3,
            'reminder_minutes': 0
        })
        
        # 7-day reminder
        reminder_7 = filing_deadline - timedelta(days=7)
        events.append({
            'type': 'reminder_7',
            'start_date': reminder_7.replace(hour=9, minute=0),
            'end_date': reminder_7.replace(hour=9, minute=30),
            'summary': f'Tax Deadline Reminder - 1 Week',
            'description': f'Your {tax_year} federal tax return is due in 1 week ({filing_deadline.strftime("%B %d, %Y")}). Complete and review your return soon.',
            'priority': 2,
            'reminder_minutes': 0
        })
        
        # 1-day reminder
        reminder_1 = filing_deadline - timedelta(days=1)
        events.append({
            'type': 'reminder_1',
            'start_date': reminder_1.replace(hour=18, minute=0),
            'end_date': reminder_1.replace(hour=18, minute=30),
            'summary': f'Tax Deadline Tomorrow!',
            'description': f'Your {tax_year} federal tax return is due tomorrow ({filing_deadline.strftime("%B %d, %Y")}). File your return or request an extension today.',
            'priority': 1,
            'reminder_minutes': 0
        })
        
        # Extension deadline (if needed)
        events.append({
            'type': 'extension_deadline',
            'start_date': extension_deadline.replace(hour=9, minute=0),
            'end_date': extension_deadline.replace(hour=23, minute=59),
            'summary': f'{tax_year} Extended Tax Return Due',
            'description': f'If you filed Form 4868 for an extension, your {tax_year} federal tax return is due today.',
            'priority': 1,
            'reminder_minutes': 60
        })
        
        return events
