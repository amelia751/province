"""Compliance Agent - PII scanning and approval gates for tax documents."""

import json
import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from province.core.config import get_settings
from province.agents.bedrock_agent_client import BedrockAgentClient

logger = logging.getLogger(__name__)


class ComplianceAgent:
    """
    Compliance Agent - Handles PII scanning and approval gates.
    
    This agent:
    1. Scans outbound drafts for PII (SSNs, bank numbers, etc.)
    2. Suggests redaction for summaries (SSN to last-4)
    3. Blocks sharing if high-risk PII is detected
    4. Requires user approval before document release
    5. Maintains audit trail of all compliance checks
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.bedrock_client = BedrockAgentClient()
        self.agent_id = None
        self.agent_alias_id = None
        
    async def create_agent(self) -> str:
        """Create the Compliance Agent in AWS Bedrock."""
        
        instruction = """You are the Compliance Agent for Province Tax Filing System. Your job is to protect sensitive taxpayer information and ensure compliance with privacy regulations.

PII DETECTION:
1. Social Security Numbers (XXX-XX-XXXX or XXXXXXXXX)
2. Bank account numbers (typically 8-17 digits)
3. Bank routing numbers (9 digits)
4. Credit card numbers (13-19 digits with patterns)
5. Driver's license numbers
6. Full dates of birth
7. Full addresses in certain contexts

RISK LEVELS:
- HIGH: Full SSNs, bank account numbers, routing numbers
- MEDIUM: Partial SSNs, addresses, phone numbers  
- LOW: Names, ZIP codes, employer names

REDACTION RULES:
- SSNs: Show only last 4 digits (***-**-1234)
- Bank accounts: Show only last 4 digits (****1234)
- Routing numbers: Completely redact (*********)
- Addresses: Show only city, state, ZIP

APPROVAL GATES:
1. All documents must pass PII scan before release
2. High-risk documents require explicit user approval
3. Medium-risk documents show warnings but allow download
4. Low-risk documents can be released automatically

AUDIT REQUIREMENTS:
- Log all PII detections with timestamps
- Record user approval decisions
- Track document access and sharing
- Maintain compliance reports"""

        tools = [
            {
                "toolSpec": {
                    "name": "scan_document_for_pii",
                    "description": "Scan document content for PII",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "document_content": {"type": "string"},
                                "document_type": {"type": "string"},
                                "engagement_id": {"type": "string"}
                            },
                            "required": ["document_content", "document_type"]
                        }
                    }
                }
            },
            {
                "toolSpec": {
                    "name": "redact_sensitive_info",
                    "description": "Redact sensitive information from content",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "content": {"type": "string"},
                                "redaction_rules": {"type": "object"}
                            },
                            "required": ["content", "redaction_rules"]
                        }
                    }
                }
            },
            {
                "toolSpec": {
                    "name": "assess_risk_level",
                    "description": "Assess risk level of detected PII",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "pii_findings": {"type": "array"},
                                "document_type": {"type": "string"}
                            },
                            "required": ["pii_findings", "document_type"]
                        }
                    }
                }
            },
            {
                "toolSpec": {
                    "name": "require_user_approval",
                    "description": "Flag document for user approval",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "engagement_id": {"type": "string"},
                                "document_path": {"type": "string"},
                                "risk_level": {"type": "string"},
                                "findings": {"type": "array"}
                            },
                            "required": ["engagement_id", "document_path", "risk_level"]
                        }
                    }
                }
            },
            {
                "toolSpec": {
                    "name": "log_compliance_event",
                    "description": "Log compliance-related events",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "engagement_id": {"type": "string"},
                                "event_type": {"type": "string"},
                                "details": {"type": "object"},
                                "user_id": {"type": "string"}
                            },
                            "required": ["engagement_id", "event_type", "details"]
                        }
                    }
                }
            }
        ]
        
        # Create the agent
        response = await self.bedrock_client.create_agent(
            agent_name="ComplianceAgent",
            instruction=instruction,
            foundation_model="anthropic.claude-3-5-sonnet-20241022-v2:0",
            tools=tools
        )
        
        self.agent_id = response["agent"]["agentId"]
        logger.info(f"Created Compliance agent with ID: {self.agent_id}")
        
        # Create alias
        alias_response = await self.bedrock_client.create_agent_alias(
            agent_id=self.agent_id,
            agent_alias_name="DRAFT"
        )
        
        self.agent_alias_id = alias_response["agentAlias"]["agentAliasId"]
        logger.info(f"Created agent alias with ID: {self.agent_alias_id}")
        
        return self.agent_id
    
    async def invoke(self, session_id: str, input_text: str, engagement_id: str) -> Dict[str, Any]:
        """Invoke the Compliance agent."""
        
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
    
    def scan_for_pii(self, content: str) -> List[Dict[str, Any]]:
        """Scan content for personally identifiable information."""
        
        findings = []
        
        # SSN patterns
        ssn_patterns = [
            r'\b\d{3}-\d{2}-\d{4}\b',  # XXX-XX-XXXX
            r'\b\d{9}\b',              # XXXXXXXXX (9 consecutive digits)
        ]
        
        for pattern in ssn_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                # Additional validation for 9-digit pattern
                if pattern == r'\b\d{9}\b':
                    digits = match.group()
                    # Skip if it looks like a phone number or other non-SSN
                    if digits.startswith(('0', '666', '9')):
                        continue
                
                findings.append({
                    'type': 'ssn',
                    'value': match.group(),
                    'start': match.start(),
                    'end': match.end(),
                    'risk_level': 'high'
                })
        
        # Bank account numbers (8-17 digits, often in specific contexts)
        bank_account_pattern = r'\b(?:account|acct|a/c)[\s#:]*(\d{8,17})\b'
        matches = re.finditer(bank_account_pattern, content, re.IGNORECASE)
        for match in matches:
            findings.append({
                'type': 'bank_account',
                'value': match.group(1),
                'start': match.start(1),
                'end': match.end(1),
                'risk_level': 'high'
            })
        
        # Bank routing numbers (9 digits)
        routing_pattern = r'\b(?:routing|aba|rtn)[\s#:]*(\d{9})\b'
        matches = re.finditer(routing_pattern, content, re.IGNORECASE)
        for match in matches:
            findings.append({
                'type': 'routing_number',
                'value': match.group(1),
                'start': match.start(1),
                'end': match.end(1),
                'risk_level': 'high'
            })
        
        # Credit card numbers (basic pattern)
        cc_pattern = r'\b(?:\d{4}[-\s]?){3}\d{4}\b'
        matches = re.finditer(cc_pattern, content)
        for match in matches:
            # Basic Luhn algorithm check could be added here
            findings.append({
                'type': 'credit_card',
                'value': match.group(),
                'start': match.start(),
                'end': match.end(),
                'risk_level': 'high'
            })
        
        # Phone numbers
        phone_pattern = r'\b(?:\+1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b'
        matches = re.finditer(phone_pattern, content)
        for match in matches:
            findings.append({
                'type': 'phone_number',
                'value': match.group(),
                'start': match.start(),
                'end': match.end(),
                'risk_level': 'medium'
            })
        
        # Email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        matches = re.finditer(email_pattern, content)
        for match in matches:
            findings.append({
                'type': 'email',
                'value': match.group(),
                'start': match.start(),
                'end': match.end(),
                'risk_level': 'low'
            })
        
        return findings
    
    def assess_overall_risk(self, findings: List[Dict[str, Any]], document_type: str) -> str:
        """Assess overall risk level based on PII findings."""
        
        if not findings:
            return 'low'
        
        high_risk_types = ['ssn', 'bank_account', 'routing_number', 'credit_card']
        medium_risk_types = ['phone_number', 'partial_ssn']
        
        # Check for high-risk PII
        for finding in findings:
            if finding['type'] in high_risk_types:
                return 'high'
        
        # Check for medium-risk PII
        for finding in findings:
            if finding['type'] in medium_risk_types:
                return 'medium'
        
        return 'low'
    
    def redact_content(self, content: str, findings: List[Dict[str, Any]], redaction_level: str = 'summary') -> str:
        """Redact sensitive information from content."""
        
        redacted_content = content
        
        # Sort findings by position (reverse order to maintain positions)
        findings_sorted = sorted(findings, key=lambda x: x['start'], reverse=True)
        
        for finding in findings_sorted:
            start = finding['start']
            end = finding['end']
            pii_type = finding['type']
            value = finding['value']
            
            if redaction_level == 'summary':
                # For summaries, show partial information
                if pii_type == 'ssn':
                    if '-' in value:
                        redacted = f"***-**-{value[-4:]}"
                    else:
                        redacted = f"*****{value[-4:]}"
                elif pii_type == 'bank_account':
                    redacted = f"****{value[-4:]}"
                elif pii_type == 'routing_number':
                    redacted = "*********"
                elif pii_type == 'credit_card':
                    redacted = f"****-****-****-{value[-4:]}"
                elif pii_type == 'phone_number':
                    redacted = f"***-***-{value[-4:]}"
                else:
                    redacted = "[REDACTED]"
            else:
                # For full redaction
                redacted = "[REDACTED]"
            
            redacted_content = redacted_content[:start] + redacted + redacted_content[end:]
        
        return redacted_content
    
    def generate_compliance_report(self, engagement_id: str, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a compliance report for the engagement."""
        
        report = {
            'engagement_id': engagement_id,
            'scan_timestamp': datetime.now().isoformat(),
            'total_findings': len(findings),
            'risk_assessment': self.assess_overall_risk(findings, 'mixed'),
            'findings_by_type': {},
            'recommendations': []
        }
        
        # Group findings by type
        for finding in findings:
            pii_type = finding['type']
            if pii_type not in report['findings_by_type']:
                report['findings_by_type'][pii_type] = 0
            report['findings_by_type'][pii_type] += 1
        
        # Generate recommendations
        if report['risk_assessment'] == 'high':
            report['recommendations'].append("User approval required before document release")
            report['recommendations'].append("Consider additional redaction for shared summaries")
        elif report['risk_assessment'] == 'medium':
            report['recommendations'].append("Review document before sharing")
            report['recommendations'].append("Apply standard redaction rules")
        else:
            report['recommendations'].append("Document cleared for standard release")
        
        return report
