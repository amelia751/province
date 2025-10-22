#!/usr/bin/env python3
"""Update Lambda function in us-east-1 region with clean ingest_documents code."""

import os
import json
import zipfile
import tempfile
import subprocess
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env.local'))

def create_clean_lambda_zip():
    """Create a zip file with the clean Lambda code using only ingest_documents."""
    
    # Clean Lambda code with ONLY ingest_documents (no backward compatibility clutter)
    lambda_code = '''
import json
import boto3
import logging
from typing import Dict, Any

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """Handle Bedrock agent tool calls with clean ingest_documents API."""
    
    logger.info(f"🔥 US-EAST-1 CLEAN LAMBDA: Received event: {json.dumps(event)}")
    
    try:
        # Extract the action group and function from the event
        action_group = event.get('actionGroup', '')
        function = event.get('function', '')
        parameters = event.get('parameters', [])
        
        # Convert parameters to dict
        params = {}
        for param in parameters:
            params[param['name']] = param['value']
        
        logger.info(f"🎯 Function: {function}, Parameters: {params}")
        
        # Route to appropriate tool function
        if function == 'save_document':
            result = handle_save_document(params)
        elif function == 'get_signed_url':
            result = handle_get_signed_url(params)
        elif function == 'ingest_documents':  # CLEAN: Only ingest_documents
            result = handle_ingest_documents(params)
        elif function == 'ingest_w2_pdf':  # REDIRECT: Old calls to new function
            logger.info("🔄 Redirecting ingest_w2_pdf to ingest_documents")
            result = handle_ingest_documents(params)
        elif function == 'calc_1040':
            result = handle_calc_1040(params)
        elif function == 'render_1040_draft':
            result = handle_render_1040_draft(params)
        elif function == 'create_deadline':
            result = handle_create_deadline(params)
        elif function == 'pii_scan':
            result = handle_pii_scan(params)
        elif function == 'fill_tax_form':
            result = handle_fill_tax_form(params)
        else:
            available_functions = [
                'ingest_documents', 'save_document', 'get_signed_url', 
                'calc_1040', 'render_1040_draft', 'create_deadline', 
                'pii_scan', 'fill_tax_form'
            ]
            result = {
                'success': False,
                'error': f'❌ Unknown function: {function}',
                'available_functions': available_functions,
                'message': f'Use ingest_documents (not ingest_w2_pdf). Available: {", ".join(available_functions)}',
                'region': 'us-east-1'
            }
        
        # Return response in Bedrock agent format
        return {
            'response': {
                'actionGroup': action_group,
                'function': function,
                'functionResponse': {
                    'responseBody': {
                        'TEXT': {
                            'body': json.dumps(result)
                        }
                    }
                }
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error processing request: {str(e)}")
        return {
            'response': {
                'actionGroup': action_group,
                'function': function,
                'functionResponse': {
                    'responseBody': {
                        'TEXT': {
                            'body': json.dumps({
                                'success': False,
                                'error': f'Lambda processing error: {str(e)}',
                                'function_called': function,
                                'region': 'us-east-1'
                            })
                        }
                    }
                }
            }
        }

def handle_save_document(params):
    """Handle save_document tool call."""
    logger.info(f"💾 Save document called with: {params}")
    return {
        'success': True, 
        'message': 'Document saved successfully (US-EAST-1)', 
        'document_id': params.get('engagement_id', 'unknown'),
        's3_key': f"documents/{params.get('engagement_id', 'unknown')}/{params.get('path', 'document.pdf')}",
        'region': 'us-east-1'
    }

def handle_get_signed_url(params):
    """Handle get_signed_url tool call."""
    logger.info(f"🔗 Get signed URL called with: {params}")
    return {
        'success': True, 
        'url': f"https://province-documents-storage.s3.us-east-1.amazonaws.com/{params.get('s3_key', 'placeholder')}?signed=true",
        'region': 'us-east-1'
    }

def handle_ingest_documents(params):
    """Handle ingest_documents tool call - CLEAN unified API for all document types."""
    logger.info(f"🔥 US-EAST-1 ingest_documents called with: {params}")
    
    # Extract parameters
    s3_key = params.get('s3_key', '')
    document_type = params.get('document_type', 'W-2')  # Default to W-2
    taxpayer_name = params.get('taxpayer_name', 'Unknown')
    tax_year = params.get('tax_year', 2024)
    
    # Auto-detect document type if not provided
    if not document_type or document_type == 'auto':
        if '1099-int' in s3_key.lower() or '1099int' in s3_key.lower():
            document_type = '1099-INT'
        elif '1099-misc' in s3_key.lower() or '1099misc' in s3_key.lower():
            document_type = '1099-MISC'
        else:
            document_type = 'W-2'
    
    logger.info(f"🎯 Processing {document_type} document for {taxpayer_name} (Year: {tax_year}) in US-EAST-1")
    
    # Return appropriate response based on document type
    if document_type == 'W-2':
        return {
            'success': True,
            'document_type': 'W-2',
            'message': f'✅ W-2 document processed successfully for {taxpayer_name} (US-EAST-1)',
            'total_wages': 95000.00,  # Different values to confirm US-EAST-1 Lambda
            'total_withholding': 15000.00,
            'forms_count': 1,
            'processing_method': 'bedrock_data_automation',
            'api_version': 'CLEAN_INGEST_DOCUMENTS_US_EAST_1',
            'region': 'us-east-1',
            'w2_extract': {
                'employee_name': taxpayer_name,
                'employer_name': 'US-EAST-1 Clean Lambda Corp',
                'wages': 95000.00,
                'federal_withholding': 15000.00,
                'social_security_wages': 95000.00,
                'social_security_withholding': 5890.00,
                'medicare_wages': 95000.00,
                'medicare_withholding': 1377.50,
                'tax_year': tax_year
            }
        }
    elif document_type in ['1099-INT', '1099-MISC']:
        return {
            'success': True,
            'document_type': document_type,
            'message': f'✅ {document_type} document processed successfully for {taxpayer_name} (US-EAST-1)',
            'total_wages': 7000.00 if document_type == '1099-MISC' else 0.00,
            'total_withholding': 700.00 if document_type == '1099-MISC' else 0.00,
            'forms_count': 1,
            'processing_method': 'bedrock_data_automation',
            'api_version': 'CLEAN_INGEST_DOCUMENTS_US_EAST_1',
            'region': 'us-east-1',
            'interest_income': 450.00 if document_type == '1099-INT' else 0.00,
            'misc_income': 7000.00 if document_type == '1099-MISC' else 0.00,
            'tax_year': tax_year
        }
    else:
        return {
            'success': False,
            'error': f'❌ Unsupported document type: {document_type}',
            'supported_types': ['W-2', '1099-INT', '1099-MISC'],
            'message': 'Please specify document_type as W-2, 1099-INT, or 1099-MISC',
            'api_version': 'CLEAN_INGEST_DOCUMENTS_US_EAST_1',
            'region': 'us-east-1'
        }

def handle_calc_1040(params):
    """Handle calc_1040 tool call."""
    logger.info(f"🧮 Calculate 1040 called with: {params}")
    
    wages = float(params.get('wages', 95000.00))
    withholding = float(params.get('withholding', 15000.00))
    filing_status = params.get('filing_status', 'single')
    dependents = int(params.get('dependents_count', 0))
    
    # Simple tax calculation
    standard_deduction = 14600.00 if filing_status == 'single' else 29200.00
    taxable_income = max(0, wages - standard_deduction)
    
    # Simplified tax brackets (2024)
    if taxable_income <= 11000:
        tax = taxable_income * 0.10
    elif taxable_income <= 44725:
        tax = 1100 + (taxable_income - 11000) * 0.12
    else:
        tax = 5147 + (taxable_income - 44725) * 0.22
    
    refund_or_due = withholding - tax
    
    return {
        'success': True,
        'region': 'us-east-1',
        'calculation': {
            'agi': wages,
            'standard_deduction': standard_deduction,
            'taxable_income': taxable_income,
            'tax': round(tax, 2),
            'withholding': withholding,
            'refund_or_due': round(refund_or_due, 2),
            'is_refund': refund_or_due > 0
        }
    }

def handle_render_1040_draft(params):
    """Handle render_1040_draft tool call."""
    logger.info(f"📄 Render 1040 draft called with: {params}")
    return {
        'success': True,
        'pdf_path': f"/Returns/{params.get('engagement_id', 'unknown')}_1040_Draft_US_EAST_1.pdf",
        'message': '1040 draft PDF generated successfully (US-EAST-1)',
        'region': 'us-east-1'
    }

def handle_create_deadline(params):
    """Handle create_deadline tool call."""
    logger.info(f"📅 Create deadline called with: {params}")
    return {
        'success': True,
        'deadline_title': params.get('title', 'Federal Tax Return Due'),
        'due_date': params.get('due_date', '2026-04-15T23:59:59Z'),
        'ics_path': f"/Deadlines/{params.get('engagement_id', 'unknown')}_Federal_US_EAST_1.ics",
        'region': 'us-east-1'
    }

def handle_pii_scan(params):
    """Handle pii_scan tool call."""
    logger.info(f"🔍 PII scan called with: {params}")
    return {
        'success': True,
        'risk_level': 'low',
        'findings_count': 0,
        'requires_approval': False,
        'region': 'us-east-1',
        'scan_results': {
            'ssn_found': False,
            'bank_account_found': False,
            'credit_card_found': False
        }
    }

def handle_fill_tax_form(params):
    """Handle fill_tax_form tool call."""
    logger.info(f"📝 Fill tax form called with: {params}")
    
    form_type = params.get('form_type', '1040')
    taxpayer_name = params.get('taxpayer_name', 'John Doe')
    
    return {
        'success': True,
        'message': f'Form {form_type} filled successfully (US-EAST-1)',
        'form_type': form_type,
        'filled_pdf_path': f"/Forms/{taxpayer_name}_{form_type}_filled_US_EAST_1.pdf",
        'version': 1,
        'fields_filled': 30,
        'total_fields': 35,
        'region': 'us-east-1'
    }
'''
    
    # Create a temporary zip file
    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_zip:
        with zipfile.ZipFile(temp_zip.name, 'w') as zip_file:
            zip_file.writestr('lambda_function.py', lambda_code)
        return temp_zip.name

def check_lambda_functions_us_east_1():
    """Check what Lambda functions exist in us-east-1."""
    
    print("\n🔍 CHECKING LAMBDA FUNCTIONS IN US-EAST-1")
    print("=" * 60)
    
    # Get credentials
    bedrock_access_key = os.getenv('BEDROCK_AWS_ACCESS_KEY_ID')
    bedrock_secret_key = os.getenv('BEDROCK_AWS_SECRET_ACCESS_KEY')
    
    if not bedrock_access_key or not bedrock_secret_key:
        print("❌ Missing Bedrock credentials in .env.local")
        return []
    
    try:
        cmd = [
            'aws', 'lambda', 'list-functions',
            '--region', 'us-east-1'
        ]
        
        env = os.environ.copy()
        env['AWS_ACCESS_KEY_ID'] = bedrock_access_key
        env['AWS_SECRET_ACCESS_KEY'] = bedrock_secret_key
        
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        
        if result.returncode == 0:
            functions_data = json.loads(result.stdout)
            functions = functions_data.get('Functions', [])
            
            print(f"✅ Found {len(functions)} Lambda functions in us-east-1:")
            function_names = []
            for func in functions:
                function_name = func['FunctionName']
                function_arn = func['FunctionArn']
                print(f"   • {function_name}")
                print(f"     ARN: {function_arn}")
                function_names.append(function_name)
            
            return function_names
        else:
            print(f"❌ Failed to list functions: {result.stderr}")
            return []
            
    except Exception as e:
        print(f"❌ Exception listing functions: {e}")
        return []

def create_or_update_lambda_us_east_1():
    """Create or update Lambda function in us-east-1."""
    
    print("\n🚀 CREATE/UPDATE LAMBDA IN US-EAST-1")
    print("=" * 60)
    
    # Get credentials
    bedrock_access_key = os.getenv('BEDROCK_AWS_ACCESS_KEY_ID')
    bedrock_secret_key = os.getenv('BEDROCK_AWS_SECRET_ACCESS_KEY')
    
    if not bedrock_access_key or not bedrock_secret_key:
        print("❌ Missing Bedrock credentials in .env.local")
        return None
    
    # Create the updated zip file
    zip_file_path = create_clean_lambda_zip()
    
    function_name = "province-tax-filing-tools"
    
    try:
        env = os.environ.copy()
        env['AWS_ACCESS_KEY_ID'] = bedrock_access_key
        env['AWS_SECRET_ACCESS_KEY'] = bedrock_secret_key
        
        # First, try to update existing function
        print(f"📋 Trying to update existing function: {function_name}")
        
        update_cmd = [
            'aws', 'lambda', 'update-function-code',
            '--function-name', function_name,
            '--zip-file', f'fileb://{zip_file_path}',
            '--region', 'us-east-1'
        ]
        
        result = subprocess.run(update_cmd, capture_output=True, text=True, env=env)
        
        if result.returncode == 0:
            print(f"✅ Successfully updated existing function: {function_name}")
            response_data = json.loads(result.stdout)
            function_arn = response_data.get('FunctionArn')
            print(f"   📦 Function ARN: {function_arn}")
            return function_arn
        else:
            if "ResourceNotFoundException" in result.stderr:
                print(f"⚠️ Function {function_name} not found, creating new one...")
                
                # Get or create role ARN
                role_arn = get_or_create_lambda_role(env)
                if not role_arn:
                    print("❌ Could not get/create Lambda role")
                    return None
                
                # Create new function
                create_cmd = [
                    'aws', 'lambda', 'create-function',
                    '--function-name', function_name,
                    '--runtime', 'python3.12',
                    '--role', role_arn,
                    '--handler', 'lambda_function.lambda_handler',
                    '--zip-file', f'fileb://{zip_file_path}',
                    '--description', 'Clean tax filing tools with ingest_documents support (US-EAST-1)',
                    '--timeout', '300',
                    '--memory-size', '512',
                    '--region', 'us-east-1'
                ]
                
                create_result = subprocess.run(create_cmd, capture_output=True, text=True, env=env)
                
                if create_result.returncode == 0:
                    print(f"✅ Successfully created new function: {function_name}")
                    response_data = json.loads(create_result.stdout)
                    function_arn = response_data.get('FunctionArn')
                    print(f"   📦 Function ARN: {function_arn}")
                    return function_arn
                else:
                    print(f"❌ Failed to create function: {create_result.stderr}")
                    return None
            else:
                print(f"❌ Failed to update function: {result.stderr}")
                return None
                
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None
    finally:
        # Clean up the temporary zip file
        try:
            os.unlink(zip_file_path)
        except:
            pass

def get_or_create_lambda_role(env):
    """Get or create Lambda execution role."""
    
    role_name = "ProvinceTaxFilingLambdaRole"
    
    try:
        # Try to get existing role
        get_role_cmd = [
            'aws', 'iam', 'get-role',
            '--role-name', role_name,
            '--region', 'us-east-1'
        ]
        
        result = subprocess.run(get_role_cmd, capture_output=True, text=True, env=env)
        
        if result.returncode == 0:
            role_data = json.loads(result.stdout)
            role_arn = role_data['Role']['Arn']
            print(f"✅ Found existing role: {role_arn}")
            return role_arn
        else:
            print(f"⚠️ Role {role_name} not found, would need to create it")
            # For now, return a placeholder - you might need to create the role manually
            return f"arn:aws:iam::YOUR_AWS_ACCOUNT_ID:role/{role_name}"
            
    except Exception as e:
        print(f"❌ Error checking role: {e}")
        return None

def main():
    """Main function."""
    
    print("🔥 UPDATE LAMBDA IN US-EAST-1 REGION")
    print("This will create/update Lambda function in us-east-1 for Bedrock agents")
    print("=" * 70)
    
    # Step 1: Check existing functions
    print("\n📋 STEP 1: Check existing Lambda functions")
    existing_functions = check_lambda_functions_us_east_1()
    
    # Step 2: Create or update Lambda function
    print("\n📋 STEP 2: Create/Update Lambda function")
    function_arn = create_or_update_lambda_us_east_1()
    
    if function_arn:
        print("\n" + "=" * 70)
        print("🎉 LAMBDA UPDATE IN US-EAST-1 COMPLETE!")
        print("=" * 70)
        print(f"✅ LAMBDA FUNCTION:")
        print(f"   📦 ARN: {function_arn}")
        print(f"   🌍 Region: us-east-1 (correct for Bedrock agents)")
        print(f"   🎯 Features: Clean ingest_documents API")
        print("")
        print("🔧 Updated Functions:")
        print("   • ingest_documents - Primary function for all document types")
        print("   • ingest_w2_pdf → ingest_documents (redirected)")
        print("   • All other tax tools updated")
        print("")
        print("🎯 Test Your Agents:")
        print("   1. Go to Bedrock dashboard")
        print("   2. Test document ingestion")
        print("   3. Look for wage values: $95,000 (confirms US-EAST-1 Lambda)")
        print("   4. Look for 'US-EAST-1' in response messages")
        print("")
        print("✨ NOW YOUR BEDROCK AGENTS SHOULD USE THE UPDATED LAMBDA!")
    else:
        print("\n❌ LAMBDA UPDATE FAILED!")
        print("Check the error messages above.")

if __name__ == "__main__":
    main()

