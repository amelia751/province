"""
API endpoints for PDF form filling functionality.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import logging

from province.agents.tax.tools.form_filler import fill_tax_form, get_available_tax_forms, get_tax_form_fields
from province.core.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/form-filler", tags=["form-filler"])


class TaxpayerInfo(BaseModel):
    """Taxpayer personal information for form filling."""
    first_name: str = Field(..., description="Taxpayer's first name")
    last_name: str = Field(..., description="Taxpayer's last name")
    ssn: str = Field(..., description="Social Security Number")
    address: str = Field(..., description="Street address")
    city: str = Field(..., description="City")
    state: str = Field(..., description="State abbreviation")
    zip_code: str = Field(..., description="ZIP code")
    filing_status: str = Field(
        default="single", 
        description="Filing status: single, married_filing_jointly, married_filing_separately, head_of_household"
    )
    phone: Optional[str] = Field(None, description="Phone number")
    email: Optional[str] = Field(None, description="Email address")


class FormFillRequest(BaseModel):
    """Request to fill a tax form with W2 data."""
    w2_extract_data: Dict[str, Any] = Field(..., description="W2 extraction result from ingest_w2 tool")
    taxpayer_info: TaxpayerInfo = Field(..., description="Taxpayer personal information")
    form_type: str = Field(default="1040", description="Type of tax form to fill")
    form_year: int = Field(default=2024, description="Tax year")


class FormFillResponse(BaseModel):
    """Response from form filling operation."""
    success: bool
    filled_form_url: Optional[str] = None
    form_summary: Optional[Dict[str, Any]] = None
    field_mappings: Optional[Dict[str, Any]] = None
    form_year: Optional[int] = None
    total_wages: Optional[float] = None
    total_withholding: Optional[float] = None
    error: Optional[str] = None


@router.post("/fill-form", response_model=FormFillResponse)
async def fill_tax_form_endpoint(request: FormFillRequest):
    """
    Fill a tax form with extracted W2 data.
    
    This endpoint takes W2 extraction results and taxpayer information,
    then generates a filled PDF tax form.
    
    Args:
        request: Form fill request with W2 data and taxpayer info
        
    Returns:
        FormFillResponse with filled form URL and summary
        
    Raises:
        HTTPException: If form filling fails
    """
    
    try:
        logger.info(f"Processing form fill request for {request.taxpayer_info.first_name} {request.taxpayer_info.last_name}")
        
        # Validate W2 data
        if not request.w2_extract_data.get('success'):
            raise HTTPException(
                status_code=400,
                detail="Invalid W2 extraction data provided"
            )
        
        # Convert taxpayer info to dict
        taxpayer_dict = request.taxpayer_info.dict()
        
        # Convert data to the format expected by the new tool
        form_data = {
            # Personal info from taxpayer_info
            'f1_01': taxpayer_dict.get('first_name', ''),
            'f1_02': taxpayer_dict.get('last_name', ''),
            'f1_03': taxpayer_dict.get('ssn', ''),
            'f1_07': taxpayer_dict.get('address', ''),
            'f1_10': taxpayer_dict.get('city', ''),
            'f1_11': taxpayer_dict.get('state', ''),
            'f1_12': taxpayer_dict.get('zip_code', ''),
            
            # W2 data
            'f1_13': request.w2_extract_data.get('w2_extract', {}).get('total_wages', 0),
            'f1_44': request.w2_extract_data.get('w2_extract', {}).get('total_withholding', 0),
            
            # Filing status checkbox
            'c1_1': taxpayer_dict.get('filing_status') == 'single',
            'c1_3': taxpayer_dict.get('filing_status') == 'married_filing_jointly',
        }
        
        # Fill the form using the new tool
        result = await fill_tax_form(request.form_type, form_data)
        
        if not result.get('success'):
            raise HTTPException(
                status_code=500,
                detail=f"Form filling failed: {result.get('error', 'Unknown error')}"
            )
        
        logger.info(f"Successfully filled {request.form_type} form for {request.taxpayer_info.first_name} {request.taxpayer_info.last_name}")
        
        return FormFillResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in form filling: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/available-forms")
async def get_available_forms():
    """
    Get list of available tax forms for filling.
    
    Returns:
        List of available forms with metadata
    """
    
    # Use the new tool function
    available_forms = get_available_tax_forms()
    
    return {
        "available_forms": available_forms,
        "total_forms": len(available_forms)
    }


@router.get("/form-fields/{form_type}")
async def get_form_fields(form_type: str, year: int = 2024):
    """
    Get available fields for a specific form type.
    
    Args:
        form_type: Type of form (e.g., '1040')
        year: Tax year
        
    Returns:
        List of form fields with metadata
    """
    
    # Use the new tool function
    fields = get_tax_form_fields(form_type)
    
    if not fields:
        raise HTTPException(
            status_code=404,
            detail=f"Form type {form_type} not supported"
        )
    
    return {
        "form_type": form_type,
        "year": year,
        "fields": fields,
        "total_fields": len(fields)
    }


@router.post("/fill-form-joyfill")
async def fill_form_joyfill(request: dict):
    """
    Fill a form using JoyFill component data.
    
    This endpoint takes form data from JoyFill components and generates a filled PDF.
    
    Args:
        request: Dict containing form_data, form_type, and tax_year
        
    Returns:
        FormFillResponse with filled form URL
    """
    
    try:
        form_data = request.get('form_data', {})
        form_type = request.get('form_type', '1040')
        tax_year = request.get('tax_year', 2024)
        
        logger.info(f"Processing JoyFill form data for {form_type} {tax_year}")
        logger.info(f"Received {len(form_data)} form fields")
        
        # Use the new form filling tool
        result = await fill_tax_form(form_type, form_data)
        
        if not result.get('success'):
            raise HTTPException(
                status_code=500,
                detail=f"Form filling failed: {result.get('error', 'Unknown error')}"
            )
        
        logger.info(f"Successfully filled {form_type} form using JoyFill data")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in JoyFill form filling: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/preview-calculations")
async def preview_calculations(request: FormFillRequest):
    """
    Preview tax calculations without generating the actual PDF.
    
    Args:
        request: Form fill request with W2 data and taxpayer info
        
    Returns:
        Calculated values for preview
    """
    
    try:
        # This would use the same calculation logic as the form filler
        # but return just the calculated values for preview
        
        w2_extract = request.w2_extract_data.get('w2_extract', {})
        total_wages = float(w2_extract.get('total_wages', 0))
        total_withholding = float(w2_extract.get('total_withholding', 0))
        
        # Get standard deduction
        filing_status = request.taxpayer_info.filing_status
        standard_deduction_amounts = {
            'single': 14600.0,
            'married_filing_jointly': 29200.0,
            'married_filing_separately': 14600.0,
            'head_of_household': 21900.0
        }
        standard_deduction = standard_deduction_amounts.get(filing_status, 14600.0)
        
        # Calculate taxable income
        adjusted_gross_income = total_wages
        taxable_income = max(0, adjusted_gross_income - standard_deduction)
        
        # Simple tax calculation (this would use the same logic as the form filler)
        if taxable_income <= 11000:
            tax_owed = taxable_income * 0.10
        elif taxable_income <= 44725:
            tax_owed = 1100 + (taxable_income - 11000) * 0.12
        else:
            tax_owed = 5147 + (taxable_income - 44725) * 0.22  # Simplified
        
        # Refund or amount owed
        refund_or_owed = total_withholding - tax_owed
        
        return {
            "calculations": {
                "total_wages": total_wages,
                "adjusted_gross_income": adjusted_gross_income,
                "standard_deduction": standard_deduction,
                "taxable_income": taxable_income,
                "tax_owed": tax_owed,
                "total_withholding": total_withholding,
                "refund_amount": max(0, refund_or_owed),
                "amount_owed": max(0, -refund_or_owed),
                "filing_status": filing_status
            },
            "w2_summary": {
                "forms_count": len(w2_extract.get('forms', [])),
                "total_wages": total_wages,
                "total_withholding": total_withholding
            }
        }
        
    except Exception as e:
        logger.error(f"Error in preview calculations: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Calculation error: {str(e)}"
        )
