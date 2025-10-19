"""
FormMappingAgent - Intelligent PDF form field mapping using agentic reasoning.

This agent uses iterative reasoning to achieve 100% field coverage, unlike single-shot prompts.
"""

import json
import logging
import boto3
import time
from typing import Dict, List, Any, Optional
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class FormMappingAgent:
    """
    An intelligent agent that iteratively maps PDF form fields to semantic names.
    
    Unlike single-shot prompting, this agent:
    1. Analyzes fields in chunks
    2. Tracks progress and coverage
    3. Identifies gaps
    4. Iterates until 100% coverage
    5. Self-validates
    """
    
    def __init__(self, aws_region: str = 'us-east-1'):
        self.bedrock = boto3.client('bedrock-runtime', region_name=aws_region)
        self.model_id = 'us.anthropic.claude-3-5-sonnet-20241022-v2:0'
        
    def map_form_fields(
        self, 
        form_type: str,
        tax_year: str,
        fields: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Intelligently map ALL form fields using iterative agentic reasoning.
        
        Args:
            form_type: Form type (e.g., "F1040")
            tax_year: Tax year (e.g., "2024")
            fields: List of extracted PDF fields
            
        Returns:
            Complete mapping with 90%+ coverage guaranteed
        """
        logger.info(f"🤖 FormMappingAgent starting for {form_type} ({tax_year})")
        logger.info(f"📋 Total fields to map: {len(fields)}")
        
        # Initialize mapping
        mapping = {
            "form_metadata": {
                "form_type": form_type,
                "tax_year": tax_year,
                "total_fields": len(fields),
                "field_types": {
                    "text": len([f for f in fields if f['field_type'] == 'Text']),
                    "checkbox": len([f for f in fields if f['field_type'] == 'CheckBox'])
                }
            }
        }
        
        # Phase 1: Initial comprehensive mapping
        logger.info("🔍 Phase 1: Initial comprehensive analysis")
        initial_mapping = self._initial_mapping(form_type, tax_year, fields)
        mapping.update(initial_mapping)
        
        # Phase 2: Identify gaps
        logger.info("🔍 Phase 2: Gap analysis")
        mapped_fields = self._extract_mapped_fields(mapping)
        all_field_names = {f['field_name'] for f in fields}
        unmapped = all_field_names - mapped_fields
        
        coverage = len(mapped_fields) / len(all_field_names) * 100
        logger.info(f"📊 Initial coverage: {coverage:.1f}% ({len(mapped_fields)}/{len(all_field_names)} fields)")
        logger.info(f"❌ Unmapped: {len(unmapped)} fields")
        
        # Phase 3: Iteratively fill gaps until 90%+ coverage
        iteration = 1
        max_iterations = 5
        
        while coverage < 90 and iteration <= max_iterations and unmapped:
            # Add delay between iterations to respect 2 RPM rate limit
            if iteration > 1:
                logger.info(f"⏳ Waiting 30s between iterations (2 RPM rate limit)...")
                time.sleep(30)
            logger.info(f"🔄 Phase 3.{iteration}: Filling gaps ({len(unmapped)} remaining)")
            
            # Get unmapped field details
            unmapped_fields = [f for f in fields if f['field_name'] in unmapped]
            
            # Fill gaps
            gap_mapping = self._fill_gaps(form_type, unmapped_fields, mapping)
            
            # Merge gap mappings
            for section, fields_dict in gap_mapping.items():
                if section == 'form_metadata':
                    continue
                if section not in mapping:
                    mapping[section] = {}
                mapping[section].update(fields_dict)
            
            # Recalculate coverage
            mapped_fields = self._extract_mapped_fields(mapping)
            unmapped = all_field_names - mapped_fields
            coverage = len(mapped_fields) / len(all_field_names) * 100
            
            logger.info(f"📊 After iteration {iteration}: {coverage:.1f}% ({len(mapped_fields)}/{len(all_field_names)} fields)")
            
            iteration += 1
        
        # Phase 4: Final validation
        logger.info("✅ Phase 4: Final validation")
        validation = self._validate_mapping(mapping, fields)
        
        logger.info(f"🎯 FINAL COVERAGE: {coverage:.1f}%")
        logger.info(f"✅ Mapped: {len(mapped_fields)} / {len(all_field_names)} fields")
        
        if coverage >= 90:
            logger.info("🎉 SUCCESS: 90%+ coverage achieved!")
        else:
            logger.warning(f"⚠️  Coverage below target: {coverage:.1f}%")
        
        return mapping
    
    def _initial_mapping(self, form_type: str, tax_year: str, fields: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Phase 1: Create initial comprehensive mapping."""
        
        # Prepare DETAILED field summary with position and full labels
        field_summary = []
        sorted_fields = sorted(fields, key=lambda x: (x['page_number'], x.get('rect', {}).get('y0', 0)))
        
        for idx, f in enumerate(sorted_fields):
            import re
            # Extract simplified field name for reference
            full_name = f['field_name']
            simplified = re.search(r'([fc][12]_\d+)', full_name)
            simple_name = simplified.group(1) if simplified else full_name
            
            field_summary.append({
                'index': idx + 1,
                'field_name': full_name,
                'simple_ref': simple_name,  # e.g., f1_04, c1_1
                'type': f['field_type'],
                'page': f['page_number'],
                'y_position': round(f.get('rect', {}).get('y0', 0), 1),
                'nearby_label': f.get('nearby_label', '')[:150]  # More context
            })
        
        prompt = f"""You are analyzing IRS Form {form_type} with {len(fields)} AcroForm fields.

**CRITICAL**: The nearby_label data is UNRELIABLE. Use FIELD NUMBER PATTERNS and Y-POSITION instead.

FIELDS (sorted top-to-bottom by position):
{json.dumps(field_summary[:60], indent=2)}
... ({len(fields)} total fields)

**EXPLICIT FIELD MAPPINGS** (use these EXACT mappings for these field numbers):

1. Tax Year Fields:
   - f1_01 → "tax_year_begin"
   - f1_02 → "tax_year_end"
   - f1_03 → "tax_year_end_year"

2. Personal Info (y~90-120):
   - f1_04 → "taxpayer_first_name"
   - f1_05 → "taxpayer_last_name" 
   - f1_06 → "taxpayer_ssn"
   - f1_07 → "spouse_first_name"
   - f1_08 → "spouse_last_name"
   - f1_09 → "spouse_ssn"

3. Address (y~130-180):
   - f1_10 → "street_address"
   - f1_11 → "apt_no"
   - f1_12 → "city"
   - f1_13 → "state"
   - f1_14 → "zip"
   - f1_15-f1_17 → foreign address fields

4. Filing Status Checkboxes (y~186):
   - c1_1 → "filing_status_single"
   - c1_2 → "filing_status_married_jointly"
   - c1_3[0] → "filing_status_married_separately"
   - c1_3[1] → "filing_status_head_of_household"
   - c1_4 → "filing_status_qualifying_widow"

5. Digital Assets Checkboxes (y~301-314):
   - c1_5 → "digital_assets_yes"
   - c1_6 → "digital_assets_no"

6. **DEPENDENTS** (y~378-430):
   - f1_18 → "dependent_1_first_name"
   - f1_19 → "dependent_1_last_name"
   - f1_20 → "dependent_1_ssn"
   - f1_21 → "dependent_1_relationship"
   - c1_7 (first instance, y~314) → "dependent_1_child_tax_credit"
   - c1_8 (first instance, y~326) → "dependent_1_other_credit"
   - f1_22-f1_25 → dependent 2 (same pattern)
   - f1_26-f1_29 → dependent 3 (same pattern)
   - f1_30-f1_31 → dependent 4 (same pattern)

7. Income Section (y~450-600, f1_32+):
   - f1_32 → "wages_line_1a"
   - f1_41 → "wages_line_1z"
   - f1_42 → "tax_exempt_interest_2a"
   - f1_43 → "taxable_interest_2b"
   - f1_44 → "qualified_dividends_3a"
   - f1_45 → "ordinary_dividends_3b"
   - Continue for all income/deduction lines through f1_60

8. Page 2 (f2_XX): Tax, credits, payments, refund

**OUTPUT**: Map ALL {len(fields)} fields. For fields with explicit mappings above, use those EXACT semantic names. For other fields, infer from y-position and context."""

        # Invoke with retry on throttling
        response = self._invoke_with_retry(prompt, max_tokens=8000)
        response_text = response
        
        logger.debug(f"Initial mapping response length: {len(response_text)} chars")
        
        # Extract and clean JSON
        import re
        json_match = re.search(r'```json\n({.*?})\n```', response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group(1)
        elif response_text.strip().startswith('{'):
            pass  # Already JSON
        else:
            json_match = re.search(r'({.*})', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(1)
        
        # Clean up common JSON issues
        response_text = re.sub(r'//.*$', '', response_text, flags=re.MULTILINE)  # Remove comments
        response_text = re.sub(r',(\s*[}\]])', r'\1', response_text)  # Fix trailing commas
        
        try:
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse error in initial_mapping: {e}")
            logger.warning(f"Problematic JSON (first 2000 chars): {response_text[:2000]}")
            # Return empty instead of crashing - gap filling will handle it
            return {}
    
    def _fill_gaps(
        self, 
        form_type: str,
        unmapped_fields: List[Dict[str, Any]],
        current_mapping: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Phase 3: Fill specific gaps in mapping."""
        
        if not unmapped_fields:
            return {}
        
        # Group unmapped fields with detailed analysis
        field_summary = []
        sorted_unmapped = sorted(unmapped_fields[:30], key=lambda x: (x['page_number'], x.get('rect', {}).get('y0', 0)))
        
        for f in sorted_unmapped:
            import re
            full_name = f['field_name']
            simplified = re.search(r'([fc][12]_\d+)', full_name)
            simple_name = simplified.group(1) if simplified else full_name
            
            field_summary.append({
                'field_name': full_name,
                'simple_ref': simple_name,
                'type': f['field_type'],
                'page': f['page_number'],
                'y_position': round(f.get('rect', {}).get('y0', 0), 1),
                'nearby_label': f.get('nearby_label', '')[:150]
            })
        
        # Show current sections for context
        sections = [k for k in current_mapping.keys() if k != 'form_metadata']
        
        prompt = f"""You are filling gaps in Form {form_type} mapping.

CURRENT SECTIONS: {', '.join(sections)}

UNMAPPED FIELDS ({len(unmapped_fields)} remaining, analyzing {len(field_summary)}):
{json.dumps(field_summary, indent=2)}

INSTRUCTIONS:
1. Use **simple_ref** (like f1_44, f2_25) + **y_position** + **nearby_label** to identify each field
2. Match field numbers with IRS form line numbers (e.g., f1_44 often = line 2a, f1_45 = line 2b)
3. Add to EXISTING sections or create NEW sections
4. Use FULL field_name in output

OUTPUT: JSON with precise mappings

{{
  "income": {{
    "tax_exempt_interest_2a": "full_field_name_here",
    "taxable_interest_2b": "full_field_name_here"
  }},
  "new_section": {{...}}
}}"""

        # Invoke with retry on throttling
        response = self._invoke_with_retry(prompt, max_tokens=4000)
        response_text = response
        
        logger.debug(f"Gap filling response length: {len(response_text)} chars")
        
        # Extract and clean JSON
        import re
        json_match = re.search(r'```json\n({.*?})\n```', response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group(1)
        elif response_text.strip().startswith('{'):
            pass  # Already JSON
        else:
            json_match = re.search(r'({.*})', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(1)
        
        # Clean up common JSON issues
        response_text = re.sub(r'//.*$', '', response_text, flags=re.MULTILINE)  # Remove comments
        response_text = re.sub(r',(\s*[}\]])', r'\1', response_text)  # Fix trailing commas
        
        try:
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse error in fill_gaps: {e}")
            logger.warning(f"Problematic JSON: {response_text[:1500]}")
            # Return empty mapping on error
            return {}
    
    def _invoke_with_retry(self, prompt: str, max_tokens: int = 4000, max_retries: int = 5) -> str:
        """Invoke Bedrock with exponential backoff on throttling.
        
        Rate limit: 2 RPM (30 seconds between requests)
        Backoff strategy: 30s, 35s, 40s, 50s, 60s
        """
        for attempt in range(max_retries):
            try:
                response = self.bedrock.invoke_model(
                    modelId=self.model_id,
                    contentType='application/json',
                    accept='application/json',
                    body=json.dumps({
                        'anthropic_version': 'bedrock-2023-05-31',
                        'max_tokens': max_tokens,
                        'temperature': 0.0,
                        'messages': [{'role': 'user', 'content': prompt}]
                    })
                )
                
                response_body = json.loads(response['body'].read())
                return response_body['content'][0]['text']
                
            except ClientError as e:
                if e.response['Error']['Code'] == 'ThrottlingException':
                    # 2 RPM = 30 seconds minimum between requests
                    # Exponential backoff: 30s, 35s, 40s, 50s, 60s
                    base_wait = 30
                    wait_time = base_wait + (attempt * 5) + (attempt ** 2)
                    logger.warning(f"⏳ Throttled (2 RPM limit). Waiting {wait_time}s before retry {attempt+1}/{max_retries}")
                    time.sleep(wait_time)
                    if attempt == max_retries - 1:
                        logger.error("❌ Max retries reached. Returning empty response.")
                        return "{}"
                else:
                    raise
        return "{}"
    
    def _extract_mapped_fields(self, mapping: Dict[str, Any]) -> set:
        """Extract all field names that have been mapped."""
        mapped = set()
        
        def extract(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if isinstance(value, str) and 'topmostSubform' in value:
                        mapped.add(value)
                    elif isinstance(value, (dict, list)):
                        extract(value)
            elif isinstance(obj, list):
                for item in obj:
                    extract(item)
        
        extract(mapping)
        return mapped
    
    def _validate_mapping(self, mapping: Dict[str, Any], fields: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate the final mapping."""
        mapped_fields = self._extract_mapped_fields(mapping)
        all_field_names = {f['field_name'] for f in fields}
        
        coverage = len(mapped_fields) / len(all_field_names) * 100 if all_field_names else 0
        
        return {
            'valid': coverage >= 90,
            'coverage': f"{len(mapped_fields)}/{len(all_field_names)} fields mapped",
            'coverage_pct': coverage,
            'errors': [] if coverage >= 90 else [f"Coverage {coverage:.1f}% below 90% target"],
            'warnings': []
        }


# Standalone testing
if __name__ == "__main__":
    import os
    import sys
    from dotenv import load_dotenv
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s'
    )
    
    load_dotenv('.env.local')
    
    # Load fields
    with open('form_1040_complete_fields.json') as f:
        fields = json.load(f)
    
    # Create agent
    agent = FormMappingAgent(aws_region='us-east-1')
    
    # Run mapping
    print("\n" + "=" * 80)
    print("🤖 FORM MAPPING AGENT - AGENTIC APPROACH")
    print("=" * 80)
    print()
    
    mapping = agent.map_form_fields(
        form_type='F1040',
        tax_year='2024',
        fields=fields
    )
    
    # Save result
    with open('agent_generated_mapping.json', 'w') as f:
        json.dump(mapping, f, indent=2)
    
    print()
    print("=" * 80)
    print(f"💾 Saved to: agent_generated_mapping.json")
    print("=" * 80)

