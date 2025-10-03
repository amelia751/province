"""
AWS Lambda Function: Validate Citations

This Lambda function validates legal citations using external legal databases.
Deployed as: province-validate-citations
"""

import json
import boto3
import logging
import os
import re
import requests
from typing import Dict, Any, List, Tuple
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

secrets_client = boto3.client('secretsmanager')


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Validate legal citations using external legal databases
    
    Args:
        event: Lambda event containing citations to validate
        context: Lambda context
        
    Returns:
        Dict containing validation results
    """
    try:
        # Parse request body
        if 'body' in event:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        else:
            body = event
            
        citations = body.get('citations', [])
        document_context = body.get('document_context', '')
        jurisdiction = body.get('jurisdiction', 'federal')
        
        if not citations:
            raise ValueError("No citations provided for validation")
            
        logger.info(f"Validating {len(citations)} citations for jurisdiction: {jurisdiction}")
        
        # Validate each citation
        validation_results = []
        
        for citation in citations:
            result = validate_single_citation(citation, jurisdiction, document_context)
            validation_results.append(result)
            
        # Calculate overall validation summary
        valid_count = sum(1 for r in validation_results if r['is_valid'])
        invalid_count = len(validation_results) - valid_count
        
        # Prepare response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'result': f"Validated {len(citations)} citations: {valid_count} valid, {invalid_count} invalid",
                'success': True,
                'data': {
                    'total_citations': len(citations),
                    'valid_citations': valid_count,
                    'invalid_citations': invalid_count,
                    'validation_results': validation_results,
                    'jurisdiction': jurisdiction,
                    'validated_at': datetime.utcnow().isoformat()
                }
            })
        }
        
    except Exception as e:
        logger.error(f"Citation validation error: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'result': f"Failed to validate citations: {str(e)}",
                'success': False,
                'error': str(e)
            })
        }


def validate_single_citation(citation: str, jurisdiction: str, context: str) -> Dict[str, Any]:
    """
    Validate a single legal citation
    
    Args:
        citation: The citation string to validate
        jurisdiction: Legal jurisdiction
        context: Document context where citation is used
        
    Returns:
        Dict containing validation result for the citation
    """
    try:
        logger.info(f"Validating citation: {citation}")
        
        # Parse citation format
        citation_info = parse_citation_format(citation)
        
        # Validate against external databases
        external_validation = validate_with_external_db(citation, jurisdiction)
        
        # Check citation format compliance
        format_validation = validate_citation_format(citation, jurisdiction)
        
        # Combine validation results
        is_valid = (
            citation_info['is_parseable'] and
            format_validation['is_valid_format'] and
            external_validation['exists_in_db']
        )
        
        return {
            'citation': citation,
            'is_valid': is_valid,
            'confidence_score': calculate_confidence_score(citation_info, format_validation, external_validation),
            'citation_info': citation_info,
            'format_validation': format_validation,
            'external_validation': external_validation,
            'suggestions': generate_suggestions(citation, citation_info, format_validation),
            'context_relevance': assess_context_relevance(citation, context)
        }
        
    except Exception as e:
        logger.error(f"Error validating citation '{citation}': {str(e)}")
        return {
            'citation': citation,
            'is_valid': False,
            'confidence_score': 0.0,
            'error': str(e),
            'suggestions': [f"Unable to validate citation: {str(e)}"]
        }


def parse_citation_format(citation: str) -> Dict[str, Any]:
    """Parse citation to extract components"""
    
    # Common citation patterns
    patterns = {
        'case_citation': r'(\d+)\s+([A-Za-z\.]+)\s+(\d+)(?:\s*\(([^)]+)\))?',  # e.g., "123 F.3d 456 (9th Cir. 2020)"
        'statute_citation': r'(\d+)\s+U\.?S\.?C\.?\s*§?\s*(\d+)',  # e.g., "42 U.S.C. § 1983"
        'federal_register': r'(\d+)\s+Fed\.?\s*Reg\.?\s+(\d+)',  # e.g., "85 Fed. Reg. 12345"
        'cfr_citation': r'(\d+)\s+C\.?F\.?R\.?\s*§?\s*(\d+)',  # e.g., "29 C.F.R. § 1630.2"
    }
    
    citation_type = 'unknown'
    components = {}
    is_parseable = False
    
    for pattern_name, pattern in patterns.items():
        match = re.search(pattern, citation, re.IGNORECASE)
        if match:
            citation_type = pattern_name
            is_parseable = True
            
            if pattern_name == 'case_citation':
                components = {
                    'volume': match.group(1),
                    'reporter': match.group(2),
                    'page': match.group(3),
                    'court_year': match.group(4) if match.group(4) else None
                }
            elif pattern_name == 'statute_citation':
                components = {
                    'title': match.group(1),
                    'section': match.group(2)
                }
            # Add more parsing logic for other citation types
            
            break
    
    return {
        'citation_type': citation_type,
        'components': components,
        'is_parseable': is_parseable,
        'original_citation': citation
    }


def validate_citation_format(citation: str, jurisdiction: str) -> Dict[str, Any]:
    """Validate citation format according to legal standards"""
    
    # Basic format validation rules
    format_issues = []
    is_valid_format = True
    
    # Check for common format issues
    if not re.search(r'\d', citation):
        format_issues.append("Citation should contain numbers (volume, page, section, etc.)")
        is_valid_format = False
        
    if len(citation.strip()) < 5:
        format_issues.append("Citation appears too short to be valid")
        is_valid_format = False
        
    # Check for proper abbreviations
    common_abbreviations = ['F.', 'F.2d', 'F.3d', 'U.S.', 'S.Ct.', 'L.Ed.', 'C.F.R.']
    has_proper_abbreviation = any(abbr in citation for abbr in common_abbreviations)
    
    if not has_proper_abbreviation and 'U.S.C.' not in citation:
        format_issues.append("Citation may be missing proper legal abbreviations")
        
    # Jurisdiction-specific validation
    if jurisdiction == 'federal':
        federal_indicators = ['F.', 'U.S.', 'S.Ct.', 'Fed.', 'C.F.R.', 'U.S.C.']
        if not any(indicator in citation for indicator in federal_indicators):
            format_issues.append("Federal jurisdiction citation should contain federal court indicators")
    
    return {
        'is_valid_format': is_valid_format,
        'format_issues': format_issues,
        'jurisdiction': jurisdiction
    }


def validate_with_external_db(citation: str, jurisdiction: str) -> Dict[str, Any]:
    """Validate citation against external legal databases"""
    
    try:
        # Try CourtListener API (free legal database)
        courtlistener_result = check_courtlistener(citation)
        
        # Try other APIs if available
        # westlaw_result = check_westlaw(citation)  # Requires API key
        # lexis_result = check_lexis(citation)      # Requires API key
        
        exists_in_db = courtlistener_result.get('found', False)
        
        return {
            'exists_in_db': exists_in_db,
            'sources_checked': ['courtlistener'],
            'courtlistener_result': courtlistener_result,
            'last_checked': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.warning(f"External database validation failed: {str(e)}")
        return {
            'exists_in_db': None,  # Unknown due to error
            'error': str(e),
            'sources_checked': [],
            'last_checked': datetime.utcnow().isoformat()
        }


def check_courtlistener(citation: str) -> Dict[str, Any]:
    """Check citation against CourtListener database"""
    
    try:
        # CourtListener API endpoint
        api_endpoint = os.environ.get('LEGAL_API_ENDPOINT', 'https://www.courtlistener.com/api/rest/v3/')
        
        # Search for the citation
        search_url = f"{api_endpoint}search/"
        params = {
            'q': citation,
            'type': 'o',  # Opinions
            'format': 'json'
        }
        
        response = requests.get(search_url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            
            return {
                'found': len(results) > 0,
                'result_count': len(results),
                'api_response': data if len(results) > 0 else None
            }
        else:
            return {
                'found': False,
                'error': f"API returned status {response.status_code}"
            }
            
    except Exception as e:
        logger.error(f"CourtListener API error: {str(e)}")
        return {
            'found': False,
            'error': str(e)
        }


def calculate_confidence_score(citation_info: Dict, format_validation: Dict, external_validation: Dict) -> float:
    """Calculate confidence score for citation validation"""
    
    score = 0.0
    
    # Parsing score (30%)
    if citation_info.get('is_parseable', False):
        score += 0.3
    
    # Format score (40%)
    if format_validation.get('is_valid_format', False):
        score += 0.4
    
    # External validation score (30%)
    if external_validation.get('exists_in_db') is True:
        score += 0.3
    elif external_validation.get('exists_in_db') is None:
        # If we couldn't check external DB, don't penalize
        score += 0.15
    
    return round(score, 2)


def generate_suggestions(citation: str, citation_info: Dict, format_validation: Dict) -> List[str]:
    """Generate suggestions for improving the citation"""
    
    suggestions = []
    
    if not citation_info.get('is_parseable', False):
        suggestions.append("Citation format is not recognized. Please check standard legal citation format.")
    
    if format_validation.get('format_issues'):
        suggestions.extend(format_validation['format_issues'])
    
    # Add specific suggestions based on citation type
    if citation_info.get('citation_type') == 'unknown':
        suggestions.append("Consider using standard Bluebook citation format.")
    
    return suggestions


def assess_context_relevance(citation: str, context: str) -> Dict[str, Any]:
    """Assess how relevant the citation is to the document context"""
    
    if not context:
        return {'relevance_score': None, 'note': 'No context provided'}
    
    # Simple keyword matching (in production, use more sophisticated NLP)
    citation_keywords = set(re.findall(r'\b\w+\b', citation.lower()))
    context_keywords = set(re.findall(r'\b\w+\b', context.lower()))
    
    common_keywords = citation_keywords.intersection(context_keywords)
    relevance_score = len(common_keywords) / max(len(citation_keywords), 1)
    
    return {
        'relevance_score': round(relevance_score, 2),
        'common_keywords': list(common_keywords),
        'note': 'Basic keyword matching analysis'
    }


# For local testing
if __name__ == "__main__":
    test_event = {
        "citations": [
            "123 F.3d 456 (9th Cir. 2020)",
            "42 U.S.C. § 1983",
            "Invalid Citation Format"
        ],
        "document_context": "This contract involves federal employment law and civil rights violations.",
        "jurisdiction": "federal"
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))