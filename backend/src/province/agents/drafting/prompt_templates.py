"""
Prompt Templates for Legal Document Drafting

This module provides specialized prompt templates for different types of
legal documents, optimized for Bedrock models.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class DocumentType(Enum):
    """Supported legal document types"""
    CONTRACT = "contract"
    NDA = "nda"
    EMPLOYMENT_AGREEMENT = "employment_agreement"
    SERVICE_AGREEMENT = "service_agreement"
    LEASE_AGREEMENT = "lease_agreement"
    LITIGATION_BRIEF = "litigation_brief"
    MOTION = "motion"
    LEGAL_MEMO = "legal_memo"
    DEMAND_LETTER = "demand_letter"
    CORPORATE_RESOLUTION = "corporate_resolution"
    PRIVACY_POLICY = "privacy_policy"
    TERMS_OF_SERVICE = "terms_of_service"


@dataclass
class PromptTemplate:
    """Template for legal document prompts"""
    document_type: DocumentType
    system_prompt: str
    user_prompt_template: str
    required_fields: List[str]
    optional_fields: List[str]
    example_context: Dict[str, Any]
    jurisdiction_specific: bool = True


class PromptTemplateManager:
    """Manager for legal document prompt templates"""
    
    def __init__(self):
        self.templates: Dict[DocumentType, PromptTemplate] = {}
        self._initialize_templates()
    
    def _initialize_templates(self):
        """Initialize all prompt templates"""
        
        # NDA Template
        nda_template = PromptTemplate(
            document_type=DocumentType.NDA,
            system_prompt="""You are an expert legal document drafter specializing in Non-Disclosure Agreements (NDAs). 
            
Your expertise includes:
- Confidentiality and trade secret law
- Bilateral and unilateral NDA structures
- Industry-specific confidentiality requirements
- Enforcement mechanisms and remedies
- Compliance with state and federal privacy laws

Always ensure NDAs are:
- Clearly scoped and not overly broad
- Enforceable in the specified jurisdiction
- Balanced between protection and practicality
- Compliant with employment and trade secret laws""",
            
            user_prompt_template="""Draft a comprehensive Non-Disclosure Agreement with the following specifications:

**Parties:**
{parties}

**Agreement Type:** {agreement_type} (unilateral/bilateral)
**Purpose:** {purpose}
**Jurisdiction:** {jurisdiction}

**Key Terms:**
- Confidentiality Period: {confidentiality_period}
- Definition of Confidential Information: {confidential_info_definition}
- Permitted Disclosures: {permitted_disclosures}
- Return of Materials: {return_materials}
- Remedies: {remedies}

**Additional Requirements:**
{additional_requirements}

Please draft a complete NDA that includes:
1. Comprehensive definitions section
2. Confidentiality obligations
3. Exceptions to confidentiality
4. Term and termination provisions
5. Remedies and enforcement
6. General provisions (governing law, severability, etc.)
7. Signature blocks

Ensure the agreement is enforceable under {jurisdiction} law and includes appropriate legal protections for both parties.""",
            
            required_fields=['parties', 'agreement_type', 'purpose', 'jurisdiction'],
            optional_fields=['confidentiality_period', 'confidential_info_definition', 'permitted_disclosures', 'return_materials', 'remedies', 'additional_requirements'],
            example_context={
                'parties': [
                    {'name': 'TechCorp Inc.', 'type': 'company', 'state': 'Delaware'},
                    {'name': 'John Smith', 'type': 'individual', 'state': 'California'}
                ],
                'agreement_type': 'bilateral',
                'purpose': 'Evaluation of potential business partnership',
                'jurisdiction': 'California',
                'confidentiality_period': '5 years',
                'return_materials': True
            }
        )
        self.templates[DocumentType.NDA] = nda_template
        
        # Employment Agreement Template
        employment_template = PromptTemplate(
            document_type=DocumentType.EMPLOYMENT_AGREEMENT,
            system_prompt="""You are an expert employment law attorney specializing in employment agreements.

Your expertise includes:
- Employment law compliance (federal and state)
- At-will employment vs. contract employment
- Compensation and benefits structures
- Non-compete and non-solicitation provisions
- Intellectual property assignment
- Termination and severance provisions

Always ensure employment agreements:
- Comply with applicable labor laws
- Include proper at-will disclaimers where appropriate
- Address intellectual property ownership
- Include appropriate confidentiality provisions
- Are enforceable and fair to both parties""",
            
            user_prompt_template="""Draft a comprehensive Employment Agreement with the following specifications:

**Employer:** {employer_name}
**Employee:** {employee_name}
**Position:** {position_title}
**Department:** {department}
**Start Date:** {start_date}
**Employment Type:** {employment_type} (at-will/contract)
**Jurisdiction:** {jurisdiction}

**Compensation:**
- Base Salary: {base_salary}
- Bonus Structure: {bonus_structure}
- Benefits: {benefits}
- Equity/Stock Options: {equity}

**Work Arrangements:**
- Work Location: {work_location}
- Work Schedule: {work_schedule}
- Remote Work Policy: {remote_work}

**Key Provisions:**
- Confidentiality: {confidentiality_required}
- Non-Compete: {non_compete}
- Non-Solicitation: {non_solicitation}
- IP Assignment: {ip_assignment}
- Termination Notice: {termination_notice}

**Additional Terms:**
{additional_terms}

Please draft a complete employment agreement that includes:
1. Position and duties description
2. Compensation and benefits
3. Term of employment
4. Confidentiality and proprietary information
5. Non-compete and non-solicitation (if applicable)
6. Intellectual property assignment
7. Termination provisions
8. General provisions
9. Signature blocks

Ensure compliance with {jurisdiction} employment laws and include all necessary legal protections.""",
            
            required_fields=['employer_name', 'employee_name', 'position_title', 'employment_type', 'jurisdiction'],
            optional_fields=['department', 'start_date', 'base_salary', 'bonus_structure', 'benefits', 'equity', 'work_location', 'work_schedule', 'remote_work', 'confidentiality_required', 'non_compete', 'non_solicitation', 'ip_assignment', 'termination_notice', 'additional_terms'],
            example_context={
                'employer_name': 'TechCorp Inc.',
                'employee_name': 'Jane Doe',
                'position_title': 'Senior Software Engineer',
                'employment_type': 'at-will',
                'jurisdiction': 'California',
                'base_salary': '$150,000',
                'confidentiality_required': True
            }
        )
        self.templates[DocumentType.EMPLOYMENT_AGREEMENT] = employment_template
        
        # Service Agreement Template
        service_template = PromptTemplate(
            document_type=DocumentType.SERVICE_AGREEMENT,
            system_prompt="""You are an expert contract attorney specializing in service agreements and professional services contracts.

Your expertise includes:
- Service contract structures and terms
- Statement of work (SOW) integration
- Payment terms and milestone structures
- Intellectual property ownership and licensing
- Limitation of liability and indemnification
- Professional services regulations

Always ensure service agreements:
- Clearly define scope of services
- Include appropriate payment terms
- Address intellectual property ownership
- Include proper limitation of liability
- Are enforceable and protect both parties""",
            
            user_prompt_template="""Draft a comprehensive Service Agreement with the following specifications:

**Service Provider:** {provider_name}
**Client:** {client_name}
**Service Type:** {service_type}
**Project Description:** {project_description}
**Jurisdiction:** {jurisdiction}

**Service Details:**
- Scope of Services: {scope_of_services}
- Deliverables: {deliverables}
- Timeline: {timeline}
- Performance Standards: {performance_standards}

**Financial Terms:**
- Total Contract Value: {contract_value}
- Payment Structure: {payment_structure}
- Payment Terms: {payment_terms}
- Expenses: {expense_handling}

**Key Provisions:**
- Intellectual Property: {ip_ownership}
- Confidentiality: {confidentiality}
- Limitation of Liability: {liability_limit}
- Indemnification: {indemnification}
- Termination: {termination_terms}

**Additional Requirements:**
{additional_requirements}

Please draft a complete service agreement that includes:
1. Service description and scope
2. Statement of work or deliverables
3. Compensation and payment terms
4. Intellectual property provisions
5. Confidentiality obligations
6. Limitation of liability and indemnification
7. Term and termination
8. General provisions
9. Signature blocks

Ensure the agreement is enforceable under {jurisdiction} law and provides appropriate protections for both parties.""",
            
            required_fields=['provider_name', 'client_name', 'service_type', 'jurisdiction'],
            optional_fields=['project_description', 'scope_of_services', 'deliverables', 'timeline', 'performance_standards', 'contract_value', 'payment_structure', 'payment_terms', 'expense_handling', 'ip_ownership', 'confidentiality', 'liability_limit', 'indemnification', 'termination_terms', 'additional_requirements'],
            example_context={
                'provider_name': 'Consulting Corp LLC',
                'client_name': 'Business Inc.',
                'service_type': 'Software Development',
                'jurisdiction': 'New York',
                'contract_value': '$100,000',
                'payment_structure': 'Monthly milestones'
            }
        )
        self.templates[DocumentType.SERVICE_AGREEMENT] = service_template
        
        # Legal Memo Template
        memo_template = PromptTemplate(
            document_type=DocumentType.LEGAL_MEMO,
            system_prompt="""You are an expert legal researcher and memo writer with extensive experience in legal analysis and writing.

Your expertise includes:
- Legal research and case law analysis
- Statutory interpretation and regulatory compliance
- Legal memo structure and formatting
- Citation formats and legal writing standards
- Risk assessment and legal recommendations

Always ensure legal memos:
- Follow proper legal memo format
- Include comprehensive legal analysis
- Cite relevant authorities properly
- Provide clear recommendations
- Address potential counterarguments""",
            
            user_prompt_template="""Draft a comprehensive Legal Memorandum with the following specifications:

**To:** {recipient}
**From:** {author}
**Date:** {date}
**Re:** {subject}

**Legal Issue:** {legal_issue}
**Jurisdiction:** {jurisdiction}
**Client/Matter:** {client_matter}

**Facts:**
{facts}

**Specific Questions:**
{legal_questions}

**Research Areas:**
{research_areas}

**Key Considerations:**
- Applicable Laws/Regulations: {applicable_laws}
- Relevant Cases: {relevant_cases}
- Risk Factors: {risk_factors}
- Business Objectives: {business_objectives}

**Additional Context:**
{additional_context}

Please draft a complete legal memorandum that includes:
1. Header with To/From/Date/Re
2. Executive Summary
3. Statement of Facts
4. Legal Analysis (with proper citations)
5. Discussion of relevant case law and statutes
6. Risk assessment
7. Recommendations and next steps
8. Conclusion

Ensure all legal citations follow Bluebook format and provide thorough analysis under {jurisdiction} law.""",
            
            required_fields=['recipient', 'author', 'subject', 'legal_issue', 'jurisdiction'],
            optional_fields=['date', 'client_matter', 'facts', 'legal_questions', 'research_areas', 'applicable_laws', 'relevant_cases', 'risk_factors', 'business_objectives', 'additional_context'],
            example_context={
                'recipient': 'Senior Partner',
                'author': 'Associate Attorney',
                'subject': 'Contract Enforceability Analysis',
                'legal_issue': 'Whether non-compete clause is enforceable',
                'jurisdiction': 'California'
            }
        )
        self.templates[DocumentType.LEGAL_MEMO] = memo_template
        
        # Add more templates as needed...
    
    def get_template(self, document_type: DocumentType) -> Optional[PromptTemplate]:
        """Get template for a specific document type"""
        return self.templates.get(document_type)
    
    def list_available_templates(self) -> List[DocumentType]:
        """List all available document types"""
        return list(self.templates.keys())
    
    def generate_prompt(self, document_type: DocumentType, context: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate system and user prompts for a document type
        
        Args:
            document_type: Type of document to generate
            context: Context variables for the template
            
        Returns:
            Dict with 'system_prompt' and 'user_prompt' keys
        """
        template = self.get_template(document_type)
        if not template:
            raise ValueError(f"No template found for document type: {document_type}")
        
        # Validate required fields
        missing_fields = []
        for field in template.required_fields:
            if field not in context:
                missing_fields.append(field)
        
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")
        
        # Fill in optional fields with defaults
        filled_context = context.copy()
        for field in template.optional_fields:
            if field not in filled_context:
                filled_context[field] = "[Not specified]"
        
        # Generate the user prompt
        try:
            user_prompt = template.user_prompt_template.format(**filled_context)
        except KeyError as e:
            raise ValueError(f"Template formatting error: {str(e)}")
        
        return {
            'system_prompt': template.system_prompt,
            'user_prompt': user_prompt
        }
    
    def validate_context(self, document_type: DocumentType, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and return context validation results
        
        Args:
            document_type: Type of document
            context: Context to validate
            
        Returns:
            Dict with validation results
        """
        template = self.get_template(document_type)
        if not template:
            return {'valid': False, 'error': f'No template found for {document_type}'}
        
        missing_required = [field for field in template.required_fields if field not in context]
        available_optional = [field for field in template.optional_fields if field in context]
        
        return {
            'valid': len(missing_required) == 0,
            'missing_required': missing_required,
            'available_optional': available_optional,
            'template_info': {
                'required_fields': template.required_fields,
                'optional_fields': template.optional_fields,
                'jurisdiction_specific': template.jurisdiction_specific
            }
        }
    
    def get_example_context(self, document_type: DocumentType) -> Dict[str, Any]:
        """Get example context for a document type"""
        template = self.get_template(document_type)
        if not template:
            return {}
        
        return template.example_context.copy()
    
    def add_custom_template(self, template: PromptTemplate):
        """Add a custom template"""
        self.templates[template.document_type] = template
        logger.info(f"Added custom template for {template.document_type}")
    
    def get_template_info(self, document_type: DocumentType) -> Dict[str, Any]:
        """Get detailed information about a template"""
        template = self.get_template(document_type)
        if not template:
            return {}
        
        return {
            'document_type': template.document_type.value,
            'required_fields': template.required_fields,
            'optional_fields': template.optional_fields,
            'jurisdiction_specific': template.jurisdiction_specific,
            'example_context': template.example_context,
            'system_prompt_preview': template.system_prompt[:200] + "..." if len(template.system_prompt) > 200 else template.system_prompt
        }