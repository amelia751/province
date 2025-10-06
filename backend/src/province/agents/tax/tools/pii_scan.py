"""PII scanning tool for tax documents."""

import json
import logging
from typing import Dict, Any
import boto3

from province.core.config import get_settings
from ..compliance_agent import ComplianceAgent

logger = logging.getLogger(__name__)


async def pii_scan(s3_key: str) -> Dict[str, Any]:
    """
    Scan document for PII and assess risk level.
    
    Args:
        s3_key: S3 key of the document to scan
    
    Returns:
        Dict with PII scan results and risk assessment
    """
    
    settings = get_settings()
    
    try:
        # Load document content from S3
        s3_client = boto3.client('s3', region_name=settings.aws_region)
        
        response = s3_client.get_object(
            Bucket="province-documents-storage",
            Key=s3_key
        )
        
        content = response['Body'].read().decode('utf-8', errors='ignore')
        
        # Create compliance agent and scan for PII
        compliance_agent = ComplianceAgent()
        
        # Scan for PII
        pii_findings = compliance_agent.scan_for_pii(content)
        
        # Assess risk level
        risk_level = compliance_agent.assess_overall_risk(pii_findings, 'document')
        
        # Generate compliance report
        engagement_id = _extract_engagement_id_from_s3_key(s3_key)
        compliance_report = compliance_agent.generate_compliance_report(engagement_id, pii_findings)
        
        logger.info(f"PII scan completed for {s3_key}: {len(pii_findings)} findings, risk level: {risk_level}")
        
        return {
            'success': True,
            'risk_level': risk_level,
            'findings_count': len(pii_findings),
            'findings': pii_findings,
            'compliance_report': compliance_report,
            'requires_approval': risk_level == 'high',
            'redaction_recommended': len(pii_findings) > 0
        }
        
    except Exception as e:
        logger.error(f"Error scanning document for PII: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def _extract_engagement_id_from_s3_key(s3_key: str) -> str:
    """Extract engagement ID from S3 key."""
    
    # Expected format: tax-engagements/{engagement_id}/path/to/file
    parts = s3_key.split('/')
    if len(parts) >= 2 and parts[0] == 'tax-engagements':
        return parts[1]
    
    return 'unknown'
