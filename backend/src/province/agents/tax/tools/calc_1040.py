"""Simple 1040 calculation tool."""

import json
import logging
from typing import Dict, Any
from decimal import Decimal
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

from province.core.config import get_settings
from ..models import FilingStatus, TaxCalculation, TAX_YEAR_2025_CONSTANTS
# Calc1040Agent implementation moved inline

logger = logging.getLogger(__name__)


async def calc_1040(engagement_id: str, filing_status: str, dependents_count: int) -> Dict[str, Any]:
    """
    Calculate simple 1040 tax return.
    
    Args:
        engagement_id: The tax engagement ID
        filing_status: Filing status (S, MFJ, MFS, HOH, QW)
        dependents_count: Number of dependents
    
    Returns:
        Dict with calculation results
    """
    
    settings = get_settings()
    
    try:
        # Load W-2 extract data
        w2_data = await _load_w2_extracts(engagement_id)
        if not w2_data:
            return {
                'success': False,
                'error': 'W-2 data not found. Please upload and process W-2 forms first.'
            }
        
        # Extract income and withholding from W-2 data
        total_wages = Decimal(str(w2_data.get('total_wages', 0)))
        total_withholding = Decimal(str(w2_data.get('total_withholding', 0)))
        
        # Convert filing status string to enum
        try:
            filing_status_enum = FilingStatus(filing_status)
        except ValueError:
            return {
                'success': False,
                'error': f'Invalid filing status: {filing_status}'
            }
        
        # Perform tax calculation inline
        calculation = _perform_tax_calculation(
            agi=total_wages,
            withholding=total_withholding,
            filing_status=filing_status_enum,
            qualifying_children=dependents_count,
            tax_year=2025
        )
        
        # Save calculation results
        await _save_calculation_results(engagement_id, calculation)
        
        logger.info(f"Completed 1040 calculation for engagement {engagement_id}")
        
        return {
            'success': True,
            'calculation': calculation.dict(),
            'summary': {
                'agi': float(calculation.agi),
                'standard_deduction': float(calculation.standard_deduction),
                'taxable_income': float(calculation.taxable_income),
                'tax': float(calculation.tax),
                'credits': {k: float(v) for k, v in calculation.credits.items()},
                'withholding': float(calculation.withholding),
                'refund_or_due': float(calculation.refund_or_due),
                'is_refund': calculation.refund_or_due >= 0
            }
        }
        
    except Exception as e:
        logger.error(f"Error calculating 1040: {e}")
        return {
            'success': False,
            'error': str(e)
        }


async def _load_w2_extracts(engagement_id: str) -> Dict[str, Any]:
    """Load W-2 extract data from DynamoDB."""
    
    settings = get_settings()
    
    try:
        dynamodb = boto3.resource('dynamodb', region_name=settings.aws_region)
        table = dynamodb.Table(settings.tax_documents_table_name)
        
        # Extract tenant_id from engagement_id
        if '#' in engagement_id:
            tenant_id = engagement_id.split('#')[0]
        else:
            tenant_id = "default"
        
        # Query for W-2 extracts document
        response = table.get_item(
            Key={
                'tenant_id#engagement_id': f"{tenant_id}#{engagement_id}",
                'doc#path': 'doc#/Workpapers/W2_Extracts.json'
            }
        )
        
        if 'Item' not in response:
            return None
        
        # Load the actual document from S3
        s3_client = boto3.client('s3', region_name=settings.aws_region)
        s3_key = response['Item']['s3_key']
        
        s3_response = s3_client.get_object(
            Bucket="province-documents-storage",
            Key=s3_key
        )
        
        content = s3_response['Body'].read().decode('utf-8')
        return json.loads(content)
        
    except ClientError as e:
        logger.error(f"Error loading W-2 extracts: {e}")
        return None
    except Exception as e:
        logger.error(f"Error loading W-2 extracts: {e}")
        return None


async def _save_calculation_results(engagement_id: str, calculation: TaxCalculation) -> None:
    """Save calculation results to S3 and DynamoDB."""
    
    settings = get_settings()
    
    try:
        # Convert calculation to JSON
        calc_json = calculation.dict()
        calc_content = json.dumps(calc_json, indent=2, default=str)
        
        # Save to S3
        s3_client = boto3.client('s3', region_name=settings.aws_region)
        s3_key = f"tax-engagements/{engagement_id}/Workpapers/Calc_1040_Simple.json"
        
        s3_client.put_object(
            Bucket="province-documents-storage",
            Key=s3_key,
            Body=calc_content.encode('utf-8'),
            ContentType='application/json',
            Metadata={
                'engagement_id': engagement_id,
                'document_type': 'calc_1040_simple',
                'calculation_timestamp': datetime.now().isoformat()
            }
        )
        
        # Update DynamoDB
        dynamodb = boto3.resource('dynamodb', region_name=settings.aws_region)
        table = dynamodb.Table(settings.tax_documents_table_name)
        
        # Extract tenant_id from engagement_id
        if '#' in engagement_id:
            tenant_id = engagement_id.split('#')[0]
        else:
            tenant_id = "default"
        
        import hashlib
        content_hash = hashlib.sha256(calc_content.encode('utf-8')).hexdigest()
        
        table.put_item(
            Item={
                'tenant_id#engagement_id': f"{tenant_id}#{engagement_id}",
                'doc#path': 'doc#/Workpapers/Calc_1040_Simple.json',
                'document_type': 'calc_1040_simple',
                's3_key': s3_key,
                'mime_type': 'application/json',
                'version': 1,
                'hash': content_hash,
                'size_bytes': len(calc_content.encode('utf-8')),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
        )
        
        logger.info(f"Saved calculation results for engagement {engagement_id}")
        
    except Exception as e:
        logger.error(f"Error saving calculation results: {e}")
        raise


def _perform_tax_calculation(
    agi: Decimal,
    withholding: Decimal,
    filing_status: FilingStatus,
    qualifying_children: int,
    tax_year: int
) -> TaxCalculation:
    """Perform inline tax calculation."""
    
    # Get standard deduction for filing status
    standard_deductions = TAX_YEAR_2025_CONSTANTS["standard_deductions"]
    standard_deduction = Decimal(str(standard_deductions[filing_status.value]))
    
    # Calculate taxable income
    taxable_income = max(Decimal('0'), agi - standard_deduction)
    
    # Calculate tax using tax brackets
    tax_brackets = TAX_YEAR_2025_CONSTANTS["tax_brackets"][filing_status.value]
    tax = Decimal('0')
    
    for bracket in tax_brackets:
        bracket_min = Decimal(str(bracket["min"]))
        bracket_max = Decimal(str(bracket["max"])) if bracket["max"] is not None else None
        bracket_rate = Decimal(str(bracket["rate"]))
        
        if taxable_income <= bracket_min:
            break
            
        if bracket_max is None:
            # Top bracket
            tax += (taxable_income - bracket_min) * bracket_rate
            break
        elif taxable_income <= bracket_max:
            # Within this bracket
            tax += (taxable_income - bracket_min) * bracket_rate
            break
        else:
            # Full bracket
            tax += (bracket_max - bracket_min) * bracket_rate
    
    # Calculate Child Tax Credit
    child_tax_credit = Decimal(str(qualifying_children * 2000))  # $2000 per qualifying child
    
    # Apply credits
    credits = {"child_tax_credit": child_tax_credit}
    total_credits = child_tax_credit
    
    # Calculate final amounts
    tax_after_credits = max(Decimal('0'), tax - total_credits)
    refund_or_due = withholding - tax_after_credits
    
    return TaxCalculation(
        tax_year=tax_year,
        filing_status=filing_status,
        agi=agi,
        standard_deduction=standard_deduction,
        taxable_income=taxable_income,
        tax=tax,
        credits=credits,
        withholding=withholding,
        refund_or_due=refund_or_due
    )
