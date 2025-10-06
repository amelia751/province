"""W-2 Ingest Agent - OCR parsing and validation of W-2 documents."""

import json
import logging
from typing import Dict, List, Optional, Any
from decimal import Decimal
from datetime import datetime

from province.core.config import get_settings
from province.agents.bedrock_agent_client import BedrockAgentClient
from .models import W2Form, W2Extract

logger = logging.getLogger(__name__)


class W2IngestAgent:
    """
    W-2 Ingest Agent - Processes W-2 PDFs using OCR and validates data.
    
    This agent:
    1. Uses AWS Textract to OCR parse W-2 PDFs
    2. Normalizes data into structured JSON with pin-cites
    3. Aggregates multiple W-2s automatically
    4. Validates totals and flags anomalies
    5. Stores consolidated W2_Extracts.json
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.bedrock_client = BedrockAgentClient()
        self.agent_id = None
        self.agent_alias_id = None
        
    async def create_agent(self) -> str:
        """Create the W-2 Ingest Agent in AWS Bedrock."""
        
        instruction = """You are the W-2 Ingest Agent for Province Tax Filing System. Your job is to process W-2 documents using OCR and extract structured tax data.

PROCESSING WORKFLOW:
1. Receive W-2 PDF document from S3
2. Use AWS Textract to extract text and form data
3. Parse and validate W-2 boxes (1-20)
4. Create pin-cite references (filename, page, bounding box)
5. Validate data consistency and flag anomalies
6. Aggregate multiple W-2s if present
7. Save structured W2_Extracts.json to /Workpapers/

KEY W-2 BOXES TO EXTRACT:
- Box 1: Wages, tips, other compensation
- Box 2: Federal income tax withheld
- Box 3: Social security wages
- Box 4: Social security tax withheld
- Box 5: Medicare wages and tips
- Box 6: Medicare tax withheld
- Box 12: Various codes (401k, health insurance, etc.)
- Employer info: Name, EIN, Address
- Employee info: Name, SSN, Address

VALIDATION CHECKS:
- Box 1 should generally equal Box 3 and Box 5 (unless over SS wage base)
- Box 3 should not exceed Social Security wage base ($168,600 for 2025)
- EIN format should be XX-XXXXXXX
- SSN format should be XXX-XX-XXXX
- All monetary amounts should be positive numbers

ANOMALY DETECTION:
- Flag if Box 1 significantly differs from Box 3/5
- Flag if withholding rates seem unusually high/low
- Flag if employer information is incomplete
- Flag if multiple W-2s have inconsistent employee info"""

        tools = [
            {
                "toolSpec": {
                    "name": "extract_w2_with_textract",
                    "description": "Extract W-2 data using AWS Textract",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "s3_bucket": {"type": "string"},
                                "s3_key": {"type": "string"},
                                "taxpayer_name": {"type": "string"},
                                "tax_year": {"type": "integer"}
                            },
                            "required": ["s3_bucket", "s3_key", "taxpayer_name", "tax_year"]
                        }
                    }
                }
            },
            {
                "toolSpec": {
                    "name": "validate_w2_data",
                    "description": "Validate extracted W-2 data for consistency",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "w2_data": {"type": "object"},
                                "tax_year": {"type": "integer"}
                            },
                            "required": ["w2_data", "tax_year"]
                        }
                    }
                }
            },
            {
                "toolSpec": {
                    "name": "aggregate_multiple_w2s",
                    "description": "Aggregate data from multiple W-2 forms",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "w2_forms": {"type": "array"},
                                "taxpayer_name": {"type": "string"}
                            },
                            "required": ["w2_forms", "taxpayer_name"]
                        }
                    }
                }
            },
            {
                "toolSpec": {
                    "name": "save_w2_extracts",
                    "description": "Save consolidated W-2 extracts to workpapers",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "engagement_id": {"type": "string"},
                                "w2_extract": {"type": "object"}
                            },
                            "required": ["engagement_id", "w2_extract"]
                        }
                    }
                }
            },
            {
                "toolSpec": {
                    "name": "flag_anomaly",
                    "description": "Flag data anomalies for review",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "engagement_id": {"type": "string"},
                                "anomaly_type": {"type": "string"},
                                "description": {"type": "string"},
                                "severity": {"type": "string"}
                            },
                            "required": ["engagement_id", "anomaly_type", "description"]
                        }
                    }
                }
            }
        ]
        
        # Create the agent
        response = await self.bedrock_client.create_agent(
            agent_name="W2IngestAgent",
            instruction=instruction,
            foundation_model="anthropic.claude-3-5-sonnet-20241022-v2:0",
            tools=tools
        )
        
        self.agent_id = response["agent"]["agentId"]
        logger.info(f"Created W-2 Ingest agent with ID: {self.agent_id}")
        
        # Create alias
        alias_response = await self.bedrock_client.create_agent_alias(
            agent_id=self.agent_id,
            agent_alias_name="DRAFT"
        )
        
        self.agent_alias_id = alias_response["agentAlias"]["agentAliasId"]
        logger.info(f"Created agent alias with ID: {self.agent_alias_id}")
        
        return self.agent_id
    
    async def invoke(self, session_id: str, input_text: str, engagement_id: str) -> Dict[str, Any]:
        """Invoke the W-2 Ingest agent."""
        
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
    
    def validate_w2_boxes(self, boxes: Dict[str, Any], tax_year: int) -> List[Dict[str, str]]:
        """Validate W-2 box data and return any anomalies."""
        
        anomalies = []
        
        try:
            # Convert string values to Decimal for validation
            box1 = Decimal(str(boxes.get("1", 0))) if boxes.get("1") else Decimal("0")
            box2 = Decimal(str(boxes.get("2", 0))) if boxes.get("2") else Decimal("0")
            box3 = Decimal(str(boxes.get("3", 0))) if boxes.get("3") else Decimal("0")
            box4 = Decimal(str(boxes.get("4", 0))) if boxes.get("4") else Decimal("0")
            box5 = Decimal(str(boxes.get("5", 0))) if boxes.get("5") else Decimal("0")
            box6 = Decimal(str(boxes.get("6", 0))) if boxes.get("6") else Decimal("0")
            
            # Social Security wage base for 2025
            ss_wage_base = Decimal("168600")
            
            # Validation checks
            if box3 > ss_wage_base:
                anomalies.append({
                    "type": "ss_wage_base_exceeded",
                    "description": f"Box 3 (${box3}) exceeds Social Security wage base (${ss_wage_base})",
                    "severity": "warning"
                })
            
            # Box 1 vs Box 3/5 consistency (allowing for some variation due to pre-tax deductions)
            if box1 > 0 and box3 > 0:
                diff_percentage = abs(box1 - box3) / box1 * 100
                if diff_percentage > 20:  # More than 20% difference
                    anomalies.append({
                        "type": "wage_inconsistency",
                        "description": f"Significant difference between Box 1 (${box1}) and Box 3 (${box3})",
                        "severity": "warning"
                    })
            
            # Withholding rate checks
            if box1 > 0 and box2 > 0:
                withholding_rate = (box2 / box1) * 100
                if withholding_rate > 50:
                    anomalies.append({
                        "type": "high_withholding",
                        "description": f"Federal withholding rate is {withholding_rate:.1f}% - unusually high",
                        "severity": "warning"
                    })
                elif withholding_rate < 5:
                    anomalies.append({
                        "type": "low_withholding",
                        "description": f"Federal withholding rate is {withholding_rate:.1f}% - unusually low",
                        "severity": "info"
                    })
            
        except (ValueError, TypeError, ZeroDivisionError) as e:
            anomalies.append({
                "type": "validation_error",
                "description": f"Error validating W-2 data: {str(e)}",
                "severity": "error"
            })
        
        return anomalies
    
    def validate_employer_info(self, employer: Dict[str, str]) -> List[Dict[str, str]]:
        """Validate employer information."""
        
        anomalies = []
        
        # Check EIN format
        ein = employer.get("EIN", "")
        if ein and not self._is_valid_ein(ein):
            anomalies.append({
                "type": "invalid_ein",
                "description": f"EIN format appears invalid: {ein}",
                "severity": "warning"
            })
        
        # Check required fields
        if not employer.get("name"):
            anomalies.append({
                "type": "missing_employer_name",
                "description": "Employer name is missing",
                "severity": "error"
            })
        
        return anomalies
    
    def validate_employee_info(self, employee: Dict[str, str]) -> List[Dict[str, str]]:
        """Validate employee information."""
        
        anomalies = []
        
        # Check SSN format
        ssn = employee.get("SSN", "")
        if ssn and not self._is_valid_ssn(ssn):
            anomalies.append({
                "type": "invalid_ssn",
                "description": f"SSN format appears invalid: {ssn}",
                "severity": "warning"
            })
        
        # Check required fields
        if not employee.get("name"):
            anomalies.append({
                "type": "missing_employee_name",
                "description": "Employee name is missing",
                "severity": "error"
            })
        
        return anomalies
    
    def _is_valid_ein(self, ein: str) -> bool:
        """Validate EIN format (XX-XXXXXXX)."""
        
        # Remove any spaces or dashes
        clean_ein = ein.replace("-", "").replace(" ", "")
        
        # Should be 9 digits
        if len(clean_ein) != 9 or not clean_ein.isdigit():
            return False
        
        # First two digits should be valid prefixes (simplified check)
        prefix = int(clean_ein[:2])
        return 10 <= prefix <= 99
    
    def _is_valid_ssn(self, ssn: str) -> bool:
        """Validate SSN format (XXX-XX-XXXX)."""
        
        # Remove any spaces or dashes
        clean_ssn = ssn.replace("-", "").replace(" ", "")
        
        # Should be 9 digits
        if len(clean_ssn) != 9 or not clean_ssn.isdigit():
            return False
        
        # Basic validation - no all zeros, 666, or 900-999 area numbers
        area = int(clean_ssn[:3])
        return area != 0 and area != 666 and area < 900
    
    def aggregate_w2_data(self, w2_forms: List[W2Form]) -> W2Extract:
        """Aggregate multiple W-2 forms into a single extract."""
        
        if not w2_forms:
            raise ValueError("No W-2 forms provided")
        
        # Calculate totals
        total_wages = sum(Decimal(str(form.boxes.get("1", 0))) for form in w2_forms)
        total_withholding = sum(Decimal(str(form.boxes.get("2", 0))) for form in w2_forms)
        
        # Use tax year from first form (assuming all same year)
        tax_year = datetime.now().year  # Default to current year
        
        return W2Extract(
            year=tax_year,
            forms=w2_forms,
            total_wages=total_wages,
            total_withholding=total_withholding
        )
