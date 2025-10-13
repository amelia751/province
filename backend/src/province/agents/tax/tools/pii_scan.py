"""PII scanning tool for tax documents."""

import json
import logging
from typing import Dict, Any
import boto3

from province.core.config import get_settings
# ComplianceAgent implementation moved inline

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
        
        # Simple PII scanning implementation
        pii_findings = _scan_for_pii_simple(content)
        
        # Assess risk level
        risk_level = _assess_risk_level(pii_findings)
        
        # Generate simple compliance report
        engagement_id = _extract_engagement_id_from_s3_key(s3_key)
        compliance_report = _generate_compliance_report(engagement_id, pii_findings)
        
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


def _scan_for_pii_simple(content: str) -> list:
    """Simple PII scanning implementation."""
    import re
    
    findings = []
    
    # SSN pattern (XXX-XX-XXXX)
    ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'
    ssn_matches = re.findall(ssn_pattern, content)
    for match in ssn_matches:
        findings.append({
            'type': 'SSN',
            'value': match,
            'confidence': 0.9,
            'risk_level': 'HIGH'
        })
    
    # Bank account pattern (simple)
    bank_pattern = r'\b\d{8,17}\b'
    bank_matches = re.findall(bank_pattern, content)
    for match in bank_matches:
        if len(match) >= 10:  # Likely bank account
            findings.append({
                'type': 'BANK_ACCOUNT',
                'value': match,
                'confidence': 0.7,
                'risk_level': 'MEDIUM'
            })
    
    return findings


def _assess_risk_level(pii_findings: list) -> str:
    """Assess overall risk level."""
    if not pii_findings:
        return 'LOW'
    
    high_risk_count = sum(1 for f in pii_findings if f.get('risk_level') == 'HIGH')
    if high_risk_count > 0:
        return 'HIGH'
    
    medium_risk_count = sum(1 for f in pii_findings if f.get('risk_level') == 'MEDIUM')
    if medium_risk_count > 2:
        return 'MEDIUM'
    
    return 'LOW'


def _generate_compliance_report(engagement_id: str, pii_findings: list) -> dict:
    """Generate simple compliance report."""
    return {
        'engagement_id': engagement_id,
        'scan_timestamp': '2025-01-01T00:00:00Z',
        'findings_count': len(pii_findings),
        'findings': pii_findings,
        'recommendations': [
            'Review document for PII before sharing',
            'Consider redacting sensitive information'
        ] if pii_findings else ['No PII detected - document appears safe']
    }
