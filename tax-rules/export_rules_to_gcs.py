#!/usr/bin/env python3
"""
Export canonical tax rules to GCS for AWS Lambda consumption.
This script exports rules.json files that AWS can pull.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, List
from google.cloud import bigquery
from google.cloud import storage

def export_rules_to_gcs():
    """Export tax rules packages to GCS in the format expected by AWS Lambda."""
    
    # Initialize clients
    bq_client = bigquery.Client(project='province-development')
    storage_client = storage.Client(project='province-development')
    bucket = storage_client.bucket('tax-rules-export-province-dev')
    
    print("🚀 Starting tax rules export to GCS...")
    
    # Query for active rules packages
    query = """
    SELECT 
        tax_year,
        jurisdiction_level,
        jurisdiction_code,
        package_id,
        package_version,
        effective_date,
        last_updated,
        standard_deduction_json,
        tax_brackets_json,
        sources_json,
        checksum_sha256,
        created_at
    FROM `province-development.mart.rules_packages_simple`
    WHERE is_active = true
    ORDER BY tax_year DESC, jurisdiction_level, jurisdiction_code
    """
    
    results = bq_client.query(query).result()
    
    exported_files = []
    
    for row in results:
        try:
            # Parse the JSON fields
            standard_deduction = json.loads(row.standard_deduction_json)
            tax_brackets = json.loads(row.tax_brackets_json) if row.tax_brackets_json != '{}' else {}
            sources = json.loads(row.sources_json)
            
            # Create the rules.json structure
            rules_json = {
                "metadata": {
                    "package_id": row.package_id,
                    "version": row.package_version,
                    "jurisdiction": {
                        "level": row.jurisdiction_level,
                        "code": row.jurisdiction_code
                    },
                    "tax_year": row.tax_year,
                    "effective_date": row.effective_date.isoformat() if row.effective_date else None,
                    "last_updated": row.last_updated.isoformat() if row.last_updated else None,
                    "checksum_sha256": row.checksum_sha256,
                    "exported_at": datetime.utcnow().isoformat() + "Z"
                },
                "rules": {
                    "standard_deduction": standard_deduction,
                    "tax_brackets": tax_brackets,
                    "credits": {},  # Placeholder
                    "deductions": {}  # Placeholder
                },
                "sources": sources,
                "format_version": "1.0"
            }
            
            # Create file paths
            # Structure: jurisdiction/tax_year/version/rules.json
            # Also create: jurisdiction/tax_year/current/rules.json
            
            base_path = f"{row.jurisdiction_level}/{row.jurisdiction_code}/{row.tax_year}"
            version_path = f"{base_path}/{row.package_version}/rules.json"
            current_path = f"{base_path}/current/rules.json"
            
            # Upload versioned file
            blob = bucket.blob(version_path)
            blob.upload_from_string(
                json.dumps(rules_json, indent=2),
                content_type='application/json'
            )
            
            # Upload current file (symlink equivalent)
            current_blob = bucket.blob(current_path)
            current_blob.upload_from_string(
                json.dumps(rules_json, indent=2),
                content_type='application/json'
            )
            
            exported_files.extend([version_path, current_path])
            
            print(f"✅ Exported {row.package_id}")
            print(f"   📁 gs://tax-rules-export-province-dev/{version_path}")
            print(f"   📁 gs://tax-rules-export-province-dev/{current_path}")
            
        except Exception as e:
            print(f"❌ Failed to export {row.package_id}: {e}")
            continue
    
    # Create an index file
    index = {
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "total_packages": len(exported_files) // 2,  # Divide by 2 because we create both versioned and current
        "files": exported_files
    }
    
    index_blob = bucket.blob("index.json")
    index_blob.upload_from_string(
        json.dumps(index, indent=2),
        content_type='application/json'
    )
    
    print(f"\n🎉 Export completed!")
    print(f"   📊 Exported {len(exported_files) // 2} packages")
    print(f"   📁 Index: gs://tax-rules-export-province-dev/index.json")
    
    return {
        "status": "success",
        "packages_exported": len(exported_files) // 2,
        "files": exported_files,
        "bucket": "tax-rules-export-province-dev"
    }

def create_aws_pull_example():
    """Create an example of how AWS Lambda would pull the rules."""
    
    example_code = '''
# AWS Lambda example for pulling tax rules
import json
import boto3
import requests
from datetime import datetime

def lambda_handler(event, context):
    """
    AWS Lambda function to pull tax rules from GCS and store in S3/DynamoDB.
    """
    
    # Configuration
    GCS_BASE_URL = "https://storage.googleapis.com/tax-rules-export-province-dev"
    S3_BUCKET = "your-tax-rules-s3-bucket"
    DYNAMODB_TABLE = "tax-rules"
    
    # Get current rules for US federal 2024
    rules_url = f"{GCS_BASE_URL}/federal/US/2024/current/rules.json"
    
    try:
        # Download rules from GCS
        response = requests.get(rules_url, timeout=30)
        response.raise_for_status()
        
        rules_data = response.json()
        
        # Verify checksum (optional but recommended)
        expected_checksum = rules_data["metadata"]["checksum_sha256"]
        # ... checksum verification logic ...
        
        # Store in S3
        s3_client = boto3.client('s3')
        s3_key = f"tax-rules/{rules_data['metadata']['jurisdiction']['code']}/{rules_data['metadata']['tax_year']}/rules.json"
        
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=json.dumps(rules_data),
            ContentType='application/json'
        )
        
        # Store metadata in DynamoDB
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(DYNAMODB_TABLE)
        
        table.put_item(
            Item={
                'package_id': rules_data['metadata']['package_id'],
                'tax_year': rules_data['metadata']['tax_year'],
                'jurisdiction_code': rules_data['metadata']['jurisdiction']['code'],
                'version': rules_data['metadata']['version'],
                'checksum_sha256': rules_data['metadata']['checksum_sha256'],
                'last_updated': rules_data['metadata']['last_updated'],
                's3_key': s3_key,
                'imported_at': datetime.utcnow().isoformat()
            }
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Tax rules imported successfully',
                'package_id': rules_data['metadata']['package_id'],
                's3_key': s3_key
            })
        }
        
    except Exception as e:
        print(f"Error importing tax rules: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
'''
    
    with open('/Users/anhlam/province/tax-rules/aws_lambda_example.py', 'w') as f:
        f.write(example_code)
    
    print("📝 Created AWS Lambda example at aws_lambda_example.py")

if __name__ == "__main__":
    result = export_rules_to_gcs()
    create_aws_pull_example()
    
    print("\n🔗 Next steps for AWS integration:")
    print("1. Set up AWS Lambda function using the example code")
    print("2. Configure Lambda to run on a schedule (e.g., daily)")
    print("3. Set up S3 bucket and DynamoDB table")
    print("4. Add error handling and notifications")
    print("5. Test the end-to-end pipeline")
