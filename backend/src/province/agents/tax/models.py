"""Tax data models for Province Tax Filing System."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class FilingStatus(str, Enum):
    """Tax filing status options."""
    SINGLE = "S"
    MARRIED_FILING_JOINTLY = "MFJ"
    MARRIED_FILING_SEPARATELY = "MFS"
    HEAD_OF_HOUSEHOLD = "HOH"
    QUALIFYING_WIDOW = "QW"


class EngagementStatus(str, Enum):
    """Tax engagement status."""
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    APPROVED = "approved"
    FILED = "filed"
    CANCELLED = "cancelled"


class DocumentType(str, Enum):
    """Tax document types."""
    W2 = "w2"
    PRIOR_YEAR_1040 = "prior_year_1040"
    ORGANIZER = "organizer"
    W2_EXTRACTS = "w2_extracts"
    CALC_1040_SIMPLE = "calc_1040_simple"
    DRAFT_1040 = "draft_1040"
    FEDERAL_ICS = "federal_ics"


class W2Box(BaseModel):
    """W-2 box data with pin-cite information."""
    value: Decimal = Field(description="Box value")
    pin_cite: Dict[str, Any] = Field(description="Pin-cite information (file, page, bbox)")


class W2Form(BaseModel):
    """W-2 form data structure."""
    employer: Dict[str, str] = Field(description="Employer information (name, EIN)")
    employee: Dict[str, str] = Field(description="Employee information (name, SSN)")
    boxes: Dict[str, Any] = Field(description="W-2 boxes with values")
    pin_cites: Dict[str, Dict[str, Any]] = Field(description="Pin-cite information for each box")


class W2Extract(BaseModel):
    """W-2 extraction result."""
    year: int = Field(description="Tax year")
    forms: List[W2Form] = Field(description="List of W-2 forms")
    total_wages: Decimal = Field(description="Total wages (sum of Box 1)")
    total_withholding: Decimal = Field(description="Total federal withholding (sum of Box 2)")


class Dependent(BaseModel):
    """Dependent information."""
    name: str = Field(description="Dependent's name")
    ssn: Optional[str] = Field(description="Dependent's SSN")
    relationship: str = Field(description="Relationship to taxpayer")
    birth_date: Optional[datetime] = Field(description="Birth date")
    qualifying_child: bool = Field(default=False, description="Qualifies as child for CTC")


class TaxCalculation(BaseModel):
    """Tax calculation results."""
    agi: Decimal = Field(description="Adjusted Gross Income")
    standard_deduction: Decimal = Field(description="Standard deduction amount")
    taxable_income: Decimal = Field(description="Taxable income")
    tax: Decimal = Field(description="Tax liability")
    credits: Dict[str, Decimal] = Field(description="Tax credits")
    withholding: Decimal = Field(description="Total withholding")
    refund_or_due: Decimal = Field(description="Refund (positive) or amount due (negative)")
    provenance: Dict[str, Any] = Field(description="Calculation provenance and references")


class TaxEngagement(BaseModel):
    """Tax engagement data structure."""
    engagement_id: str = Field(description="Unique engagement ID")
    tenant_id: str = Field(description="Tenant ID")
    tax_year: int = Field(description="Tax year")
    status: EngagementStatus = Field(description="Engagement status")
    filing_status: Optional[FilingStatus] = Field(description="Filing status")
    dependents_count: int = Field(default=0, description="Number of dependents")
    dependents: List[Dependent] = Field(default_factory=list, description="Dependent details")
    taxpayer_info: Dict[str, Any] = Field(default_factory=dict, description="Taxpayer information")
    created_by: str = Field(description="User who created the engagement")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


class TaxDocument(BaseModel):
    """Tax document metadata."""
    engagement_id: str = Field(description="Associated engagement ID")
    tenant_id: str = Field(description="Tenant ID")
    document_type: DocumentType = Field(description="Document type")
    path: str = Field(description="Document path within engagement folder")
    s3_key: str = Field(description="S3 object key")
    mime_type: str = Field(description="MIME type")
    version: int = Field(default=1, description="Document version")
    hash: str = Field(description="Document hash")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


class TaxDeadline(BaseModel):
    """Tax deadline information."""
    engagement_id: str = Field(description="Associated engagement ID")
    tenant_id: str = Field(description="Tenant ID")
    deadline_id: str = Field(description="Unique deadline ID")
    title: str = Field(description="Deadline title")
    due_date: datetime = Field(description="Due date")
    reminders: List[int] = Field(description="Reminder days before due date")
    acknowledged: bool = Field(default=False, description="User acknowledged deadline")
    created_at: datetime = Field(description="Creation timestamp")


class TaxConnection(BaseModel):
    """Tax agent connection/session."""
    connection_id: str = Field(description="Unique connection ID")
    engagement_id: str = Field(description="Associated engagement ID")
    user_id: str = Field(description="User ID")
    agent_session_id: Optional[str] = Field(description="Bedrock agent session ID")
    status: str = Field(description="Connection status")
    created_at: datetime = Field(description="Creation timestamp")
    ttl: int = Field(description="TTL for automatic cleanup")


# Tax calculation constants for 2025
TAX_YEAR_2025_CONSTANTS = {
    "standard_deductions": {
        FilingStatus.SINGLE: Decimal("14600"),
        FilingStatus.MARRIED_FILING_JOINTLY: Decimal("29200"),
        FilingStatus.MARRIED_FILING_SEPARATELY: Decimal("14600"),
        FilingStatus.HEAD_OF_HOUSEHOLD: Decimal("21900"),
        FilingStatus.QUALIFYING_WIDOW: Decimal("29200"),
    },
    "tax_brackets": {
        FilingStatus.SINGLE: [
            (Decimal("11000"), Decimal("0.10")),
            (Decimal("44725"), Decimal("0.12")),
            (Decimal("95375"), Decimal("0.22")),
            (Decimal("182050"), Decimal("0.24")),
            (Decimal("231250"), Decimal("0.32")),
            (Decimal("578125"), Decimal("0.35")),
            (float("inf"), Decimal("0.37")),
        ],
        FilingStatus.MARRIED_FILING_JOINTLY: [
            (Decimal("22000"), Decimal("0.10")),
            (Decimal("89450"), Decimal("0.12")),
            (Decimal("190750"), Decimal("0.22")),
            (Decimal("364200"), Decimal("0.24")),
            (Decimal("462500"), Decimal("0.32")),
            (Decimal("693750"), Decimal("0.35")),
            (float("inf"), Decimal("0.37")),
        ],
        # Add other filing statuses as needed
    },
    "child_tax_credit": {
        "amount_per_child": Decimal("2000"),
        "phase_out_threshold": {
            FilingStatus.SINGLE: Decimal("200000"),
            FilingStatus.MARRIED_FILING_JOINTLY: Decimal("400000"),
        },
        "phase_out_rate": Decimal("0.05"),  # $50 per $1000 over threshold
    },
}
