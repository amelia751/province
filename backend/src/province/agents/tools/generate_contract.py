"""
AWS Lambda Function: Generate Contract

This Lambda function generates legal contracts using Bedrock models and templates.
Deployed as: province-generate-contract
"""

import json
import boto3
import logging
import os
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

bedrock_runtime = boto3.client('bedrock-runtime')
s3_client = boto3.client('s3')


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Generate legal contract using Bedrock models and templates
    
    Args:
        event: Lambda event containing contract parameters
        context: Lambda context
        
    Returns:
        Dict containing generated contract
    """
    try:
        # Parse request body
        if 'body' in event:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        else:
            body = event
            
        contract_type = body.get('contract_type')
        parties = body.get('parties', [])
        terms = body.get('terms', {})
        jurisdiction = body.get('jurisdiction', 'New York')
        
        if not all([contract_type, parties]):
            raise ValueError("Missing required fields: contract_type, parties")
            
        logger.info(f"Generating {contract_type} contract for {len(parties)} parties in {jurisdiction}")
        
        # Load contract template
        template_content = load_contract_template(contract_type)
        
        # Generate contract using Bedrock
        contract_content = generate_contract_with_bedrock(
            contract_type, parties, terms, jurisdiction, template_content
        )
        
        # Post-process and validate contract
        processed_contract = post_process_contract(contract_content, contract_type, parties)
        
        # Generate contract metadata
        contract_metadata = {
            'contract_type': contract_type,
            'parties': parties,
            'jurisdiction': jurisdiction,
            'generated_at': datetime.utcnow().isoformat(),
            'model_used': os.environ.get('BEDROCK_MODEL_ID', 'claude-3-5-sonnet'),
            'template_version': '1.0'
        }
        
        # Prepare response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'result': f"Successfully generated {contract_type} contract",
                'success': True,
                'data': {
                    'contract_content': processed_contract,
                    'contract_type': contract_type,
                    'parties': parties,
                    'jurisdiction': jurisdiction,
                    'metadata': contract_metadata,
                    'word_count': len(processed_contract.split()),
                    'sections': extract_contract_sections(processed_contract)
                }
            })
        }
        
    except Exception as e:
        logger.error(f"Contract generation error: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'result': f"Failed to generate contract: {str(e)}",
                'success': False,
                'error': str(e)
            })
        }


def load_contract_template(contract_type: str) -> str:
    """Load contract template from S3"""
    
    try:
        template_bucket = os.environ.get('TEMPLATE_BUCKET', 'province-legal-templates')
        template_key = f"contracts/{contract_type.lower().replace(' ', '_')}_template.txt"
        
        response = s3_client.get_object(Bucket=template_bucket, Key=template_key)
        template_content = response['Body'].read().decode('utf-8')
        
        logger.info(f"Loaded template for {contract_type} from S3")
        return template_content
        
    except Exception as e:
        logger.warning(f"Could not load template for {contract_type}: {str(e)}")
        # Return default template structure
        return get_default_template(contract_type)


def get_default_template(contract_type: str) -> str:
    """Get default template structure for contract type"""
    
    templates = {
        'nda': """
NON-DISCLOSURE AGREEMENT

This Non-Disclosure Agreement ("Agreement") is entered into on [DATE] by and between [PARTY1] and [PARTY2].

1. CONFIDENTIAL INFORMATION
[Define what constitutes confidential information]

2. OBLIGATIONS
[Outline obligations of receiving party]

3. TERM
[Specify duration of agreement]

4. REMEDIES
[Describe remedies for breach]

5. GOVERNING LAW
This Agreement shall be governed by the laws of [JURISDICTION].

[SIGNATURE BLOCKS]
""",
        'employment': """
EMPLOYMENT AGREEMENT

This Employment Agreement ("Agreement") is entered into on [DATE] between [EMPLOYER] and [EMPLOYEE].

1. POSITION AND DUTIES
[Job title and responsibilities]

2. COMPENSATION
[Salary and benefits]

3. TERM OF EMPLOYMENT
[Employment duration]

4. CONFIDENTIALITY
[Confidentiality obligations]

5. TERMINATION
[Termination conditions]

6. GOVERNING LAW
This Agreement shall be governed by the laws of [JURISDICTION].

[SIGNATURE BLOCKS]
""",
        'service_agreement': """
SERVICE AGREEMENT

This Service Agreement ("Agreement") is entered into on [DATE] between [CLIENT] and [SERVICE_PROVIDER].

1. SERVICES
[Description of services to be provided]

2. COMPENSATION
[Payment terms and amounts]

3. TERM
[Duration of services]

4. INTELLECTUAL PROPERTY
[IP ownership and licensing]

5. LIMITATION OF LIABILITY
[Liability limitations]

6. GOVERNING LAW
This Agreement shall be governed by the laws of [JURISDICTION].

[SIGNATURE BLOCKS]
"""
    }
    
    return templates.get(contract_type.lower(), templates['service_agreement'])


def generate_contract_with_bedrock(
    contract_type: str, 
    parties: List[Dict], 
    terms: Dict, 
    jurisdiction: str, 
    template: str
) -> str:
    """Generate contract content using Bedrock model"""
    
    # Prepare prompt for Bedrock
    prompt = f"""You are a legal contract drafting assistant. Generate a comprehensive {contract_type} contract based on the following information:

Contract Type: {contract_type}
Jurisdiction: {jurisdiction}

Parties:
{json.dumps(parties, indent=2)}

Terms and Conditions:
{json.dumps(terms, indent=2)}

Template Structure:
{template}

Instructions:
1. Create a complete, legally sound contract
2. Use proper legal language and formatting
3. Include all necessary clauses for this contract type
4. Ensure compliance with {jurisdiction} law
5. Replace all placeholders with actual information
6. Include appropriate signature blocks
7. Add standard legal provisions (governing law, severability, etc.)

Generate the complete contract:"""

    try:
        model_id = os.environ.get('BEDROCK_MODEL_ID', 'anthropic.claude-3-5-sonnet-20241022-v2:0')
        
        # Prepare request body based on model
        if 'claude' in model_id:
            request_body = {
                "prompt": f"\n\nHuman: {prompt}\n\nAssistant:",
                "max_tokens_to_sample": 4000,
                "temperature": 0.1,
                "top_p": 0.9
            }
        elif 'nova' in model_id:
            request_body = {
                "inputText": prompt,
                "textGenerationConfig": {
                    "maxTokenCount": 4000,
                    "temperature": 0.1,
                    "topP": 0.9
                }
            }
        else:
            raise ValueError(f"Unsupported model: {model_id}")
        
        # Invoke Bedrock model
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            body=json.dumps(request_body),
            contentType="application/json",
            accept="application/json"
        )
        
        response_body = json.loads(response['body'].read())
        
        # Extract generated text based on model
        if 'claude' in model_id:
            generated_text = response_body['completion']
        elif 'nova' in model_id:
            generated_text = response_body['results'][0]['outputText']
        else:
            generated_text = str(response_body)
        
        logger.info(f"Generated contract using {model_id}")
        return generated_text.strip()
        
    except Exception as e:
        logger.error(f"Bedrock model invocation failed: {str(e)}")
        raise


def post_process_contract(contract_content: str, contract_type: str, parties: List[Dict]) -> str:
    """Post-process and validate the generated contract"""
    
    # Clean up the contract text
    processed_content = contract_content.strip()
    
    # Ensure proper formatting
    if not processed_content.startswith(contract_type.upper()):
        processed_content = f"{contract_type.upper()} AGREEMENT\n\n{processed_content}"
    
    # Add date if missing
    if '[DATE]' in processed_content:
        current_date = datetime.utcnow().strftime('%B %d, %Y')
        processed_content = processed_content.replace('[DATE]', current_date)
    
    # Validate that all parties are mentioned
    for party in parties:
        party_name = party.get('name', party.get('company_name', 'Unknown Party'))
        if party_name.lower() not in processed_content.lower():
            logger.warning(f"Party '{party_name}' may not be properly referenced in contract")
    
    # Add footer with generation info
    footer = f"\n\n---\nGenerated by Province Legal OS on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\nThis document should be reviewed by qualified legal counsel before execution."
    
    return processed_content + footer


def extract_contract_sections(contract_content: str) -> List[Dict[str, str]]:
    """Extract sections from the contract for easier navigation"""
    
    sections = []
    lines = contract_content.split('\n')
    current_section = None
    current_content = []
    
    for line in lines:
        # Look for section headers (numbered or all caps)
        if (line.strip() and 
            (line.strip()[0].isdigit() or line.strip().isupper()) and 
            len(line.strip()) < 100):
            
            # Save previous section
            if current_section:
                sections.append({
                    'title': current_section,
                    'content': '\n'.join(current_content).strip()
                })
            
            # Start new section
            current_section = line.strip()
            current_content = []
        else:
            if current_section:
                current_content.append(line)
    
    # Add final section
    if current_section:
        sections.append({
            'title': current_section,
            'content': '\n'.join(current_content).strip()
        })
    
    return sections


# For local testing
if __name__ == "__main__":
    test_event = {
        "contract_type": "NDA",
        "parties": [
            {
                "name": "TechCorp Inc.",
                "type": "company",
                "address": "123 Tech Street, San Francisco, CA 94105"
            },
            {
                "name": "John Smith",
                "type": "individual",
                "address": "456 Main Street, New York, NY 10001"
            }
        ],
        "terms": {
            "confidentiality_period": "5 years",
            "purpose": "Evaluation of potential business partnership",
            "return_materials": True
        },
        "jurisdiction": "California"
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))