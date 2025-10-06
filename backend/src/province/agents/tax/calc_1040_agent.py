"""1040 Calculation Agent - Deterministic tax calculation for simple returns."""

import json
import logging
from typing import Dict, List, Optional, Any
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime

from province.core.config import get_settings
from province.agents.bedrock_agent_client import BedrockAgentClient
from .models import FilingStatus, TaxCalculation, TAX_YEAR_2025_CONSTANTS

logger = logging.getLogger(__name__)


class Calc1040Agent:
    """
    1040 Calculation Agent - Performs deterministic tax calculations.
    
    This agent:
    1. Loads W2_Extracts.json for income data
    2. Applies standard deduction based on filing status
    3. Calculates tax using 2025 IRS tax tables/brackets
    4. Computes Child Tax Credit if applicable
    5. Determines refund or amount due
    6. Emits machine-readable Calc_1040_Simple.json
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.bedrock_client = BedrockAgentClient()
        self.agent_id = None
        self.agent_alias_id = None
        
    async def create_agent(self) -> str:
        """Create the 1040 Calculation Agent in AWS Bedrock."""
        
        instruction = """You are the 1040 Calculation Agent for Province Tax Filing System. Your job is to perform accurate, deterministic tax calculations for simple W-2 employee returns.

CALCULATION WORKFLOW:
1. Load W2_Extracts.json to get total wages and withholding
2. Apply standard deduction based on filing status
3. Calculate taxable income (AGI - standard deduction)
4. Apply 2025 tax brackets to determine tax liability
5. Calculate Child Tax Credit if dependents qualify
6. Determine refund (withholding > tax) or amount due (tax > withholding)
7. Save detailed calculation to Calc_1040_Simple.json

2025 TAX YEAR CONSTANTS:
Standard Deductions:
- Single: $14,600
- Married Filing Jointly: $29,200
- Married Filing Separately: $14,600
- Head of Household: $21,900
- Qualifying Widow: $29,200

Tax Brackets (Single):
- 10%: $0 - $11,000
- 12%: $11,001 - $44,725
- 22%: $44,726 - $95,375
- 24%: $95,376 - $182,050
- 32%: $182,051 - $231,250
- 35%: $231,251 - $578,125
- 37%: $578,126+

Child Tax Credit:
- $2,000 per qualifying child under 17
- Phase-out starts at $200,000 (Single) / $400,000 (MFJ)

CALCULATION RULES:
- Round all dollar amounts to nearest cent
- AGI = Total W-2 wages (Box 1)
- Taxable Income = AGI - Standard Deduction (minimum $0)
- Tax = Apply progressive tax brackets
- Credits reduce tax dollar-for-dollar
- Refund = Withholding - (Tax - Credits)"""

        tools = [
            {
                "toolSpec": {
                    "name": "load_w2_extracts",
                    "description": "Load W-2 extract data for calculation",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "engagement_id": {"type": "string"}
                            },
                            "required": ["engagement_id"]
                        }
                    }
                }
            },
            {
                "toolSpec": {
                    "name": "calculate_standard_deduction",
                    "description": "Calculate standard deduction based on filing status",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "filing_status": {"type": "string"},
                                "tax_year": {"type": "integer"}
                            },
                            "required": ["filing_status", "tax_year"]
                        }
                    }
                }
            },
            {
                "toolSpec": {
                    "name": "calculate_tax_liability",
                    "description": "Calculate tax liability using progressive brackets",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "taxable_income": {"type": "number"},
                                "filing_status": {"type": "string"},
                                "tax_year": {"type": "integer"}
                            },
                            "required": ["taxable_income", "filing_status", "tax_year"]
                        }
                    }
                }
            },
            {
                "toolSpec": {
                    "name": "calculate_child_tax_credit",
                    "description": "Calculate Child Tax Credit",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "agi": {"type": "number"},
                                "filing_status": {"type": "string"},
                                "qualifying_children": {"type": "integer"},
                                "tax_year": {"type": "integer"}
                            },
                            "required": ["agi", "filing_status", "qualifying_children", "tax_year"]
                        }
                    }
                }
            },
            {
                "toolSpec": {
                    "name": "save_calculation_results",
                    "description": "Save calculation results to workpapers",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "engagement_id": {"type": "string"},
                                "calculation": {"type": "object"}
                            },
                            "required": ["engagement_id", "calculation"]
                        }
                    }
                }
            }
        ]
        
        # Create the agent
        response = await self.bedrock_client.create_agent(
            agent_name="Calc1040Agent",
            instruction=instruction,
            foundation_model="anthropic.claude-3-5-sonnet-20241022-v2:0",
            tools=tools
        )
        
        self.agent_id = response["agent"]["agentId"]
        logger.info(f"Created 1040 Calculation agent with ID: {self.agent_id}")
        
        # Create alias
        alias_response = await self.bedrock_client.create_agent_alias(
            agent_id=self.agent_id,
            agent_alias_name="DRAFT"
        )
        
        self.agent_alias_id = alias_response["agentAlias"]["agentAliasId"]
        logger.info(f"Created agent alias with ID: {self.agent_alias_id}")
        
        return self.agent_id
    
    async def invoke(self, session_id: str, input_text: str, engagement_id: str) -> Dict[str, Any]:
        """Invoke the 1040 Calculation agent."""
        
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
    
    def calculate_standard_deduction(self, filing_status: FilingStatus, tax_year: int = 2025) -> Decimal:
        """Calculate standard deduction for given filing status."""
        
        if tax_year != 2025:
            raise ValueError(f"Tax year {tax_year} not supported. Only 2025 is currently supported.")
        
        return TAX_YEAR_2025_CONSTANTS["standard_deductions"][filing_status]
    
    def calculate_tax_liability(self, taxable_income: Decimal, filing_status: FilingStatus, tax_year: int = 2025) -> Decimal:
        """Calculate tax liability using progressive tax brackets."""
        
        if tax_year != 2025:
            raise ValueError(f"Tax year {tax_year} not supported. Only 2025 is currently supported.")
        
        if taxable_income <= 0:
            return Decimal("0")
        
        brackets = TAX_YEAR_2025_CONSTANTS["tax_brackets"].get(filing_status)
        if not brackets:
            # Default to single filer brackets if filing status not found
            brackets = TAX_YEAR_2025_CONSTANTS["tax_brackets"][FilingStatus.SINGLE]
        
        tax = Decimal("0")
        previous_bracket = Decimal("0")
        
        for bracket_limit, rate in brackets:
            if bracket_limit == float("inf"):
                # Top bracket - apply rate to remaining income
                tax += (taxable_income - previous_bracket) * rate
                break
            elif taxable_income <= bracket_limit:
                # Income falls within this bracket
                tax += (taxable_income - previous_bracket) * rate
                break
            else:
                # Income exceeds this bracket - apply rate to bracket width
                tax += (bracket_limit - previous_bracket) * rate
                previous_bracket = bracket_limit
        
        # Round to nearest cent
        return tax.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    
    def calculate_child_tax_credit(self, agi: Decimal, filing_status: FilingStatus, qualifying_children: int, tax_year: int = 2025) -> Decimal:
        """Calculate Child Tax Credit."""
        
        if tax_year != 2025 or qualifying_children <= 0:
            return Decimal("0")
        
        ctc_constants = TAX_YEAR_2025_CONSTANTS["child_tax_credit"]
        base_credit = ctc_constants["amount_per_child"] * qualifying_children
        
        # Phase-out calculation
        phase_out_threshold = ctc_constants["phase_out_threshold"].get(filing_status, Decimal("200000"))
        
        if agi <= phase_out_threshold:
            return base_credit
        
        # Calculate phase-out reduction
        excess_income = agi - phase_out_threshold
        # Phase-out is $50 for every $1,000 over threshold
        phase_out_amount = (excess_income / Decimal("1000")).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * Decimal("50")
        
        # Credit cannot be negative
        return max(Decimal("0"), base_credit - phase_out_amount)
    
    def perform_full_calculation(self, 
                                agi: Decimal, 
                                withholding: Decimal,
                                filing_status: FilingStatus,
                                qualifying_children: int = 0,
                                tax_year: int = 2025) -> TaxCalculation:
        """Perform complete 1040 calculation."""
        
        # Calculate standard deduction
        standard_deduction = self.calculate_standard_deduction(filing_status, tax_year)
        
        # Calculate taxable income
        taxable_income = max(Decimal("0"), agi - standard_deduction)
        
        # Calculate tax liability
        tax = self.calculate_tax_liability(taxable_income, filing_status, tax_year)
        
        # Calculate Child Tax Credit
        ctc = self.calculate_child_tax_credit(agi, filing_status, qualifying_children, tax_year)
        
        # Apply credits to reduce tax
        tax_after_credits = max(Decimal("0"), tax - ctc)
        
        # Calculate refund or amount due
        refund_or_due = withholding - tax_after_credits
        
        # Build provenance information
        provenance = {
            "calculation_date": datetime.now().isoformat(),
            "tax_year": tax_year,
            "filing_status": filing_status.value,
            "standard_deduction_amount": float(standard_deduction),
            "tax_brackets_version": "2025.1",
            "ctc_qualifying_children": qualifying_children,
            "ctc_amount": float(ctc)
        }
        
        return TaxCalculation(
            agi=agi,
            standard_deduction=standard_deduction,
            taxable_income=taxable_income,
            tax=tax,
            credits={"CTC": ctc},
            withholding=withholding,
            refund_or_due=refund_or_due,
            provenance=provenance
        )
    
    def generate_calculation_summary(self, calculation: TaxCalculation) -> str:
        """Generate a human-readable calculation summary."""
        
        summary = f"""# Tax Calculation Summary

## Income
- Adjusted Gross Income (AGI): ${calculation.agi:,.2f}
- Standard Deduction: ${calculation.standard_deduction:,.2f}
- Taxable Income: ${calculation.taxable_income:,.2f}

## Tax Calculation
- Tax Liability: ${calculation.tax:,.2f}
- Child Tax Credit: ${calculation.credits.get('CTC', Decimal('0')):,.2f}
- Tax After Credits: ${max(Decimal('0'), calculation.tax - calculation.credits.get('CTC', Decimal('0'))):,.2f}

## Withholding & Refund
- Federal Withholding: ${calculation.withholding:,.2f}
- **{'Refund' if calculation.refund_or_due >= 0 else 'Amount Due'}: ${abs(calculation.refund_or_due):,.2f}**

## Calculation Details
- Filing Status: {calculation.provenance.get('filing_status', 'Unknown')}
- Tax Year: {calculation.provenance.get('tax_year', 'Unknown')}
- Calculation Date: {calculation.provenance.get('calculation_date', 'Unknown')}
"""
        
        return summary
