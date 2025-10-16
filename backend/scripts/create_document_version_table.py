#!/usr/bin/env python3
"""
Create DynamoDB table for document version metadata.

This script creates the 'province-document-versions' table to store
version metadata for tax forms and documents.
"""

import boto3
import os
import sys
from botocore.exceptions import ClientError

def create_document_version_table():
    """Create the document version metadata table."""
    
    # Get AWS credentials
    aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    aws_region = os.getenv('AWS_REGION', 'us-east-1')
    
    if not aws_access_key_id or not aws_secret_access_key:
        print("❌ Error: AWS credentials not found in environment variables")
        print("Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
        return False
    
    # Initialize DynamoDB client
    dynamodb = boto3.client(
        'dynamodb',
        region_name=aws_region,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key
    )
    
    table_name = 'province-document-versions'
    
    try:
        # Check if table already exists
        try:
            response = dynamodb.describe_table(TableName=table_name)
            print(f"✅ Table '{table_name}' already exists")
            print(f"   Status: {response['Table']['TableStatus']}")
            print(f"   ARN: {response['Table']['TableArn']}")
            return True
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceNotFoundException':
                raise
            # Table doesn't exist, continue to create it
        
        print(f"📋 Creating DynamoDB table: {table_name}")
        
        # Create table
        response = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'document_id',
                    'KeyType': 'HASH'  # Partition key
                },
                {
                    'AttributeName': 'version',
                    'KeyType': 'RANGE'  # Sort key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'document_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'version',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'taxpayer_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'form_type',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'created_at',
                    'AttributeType': 'S'
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'taxpayer-form-index',
                    'KeySchema': [
                        {
                            'AttributeName': 'taxpayer_id',
                            'KeyType': 'HASH'
                        },
                        {
                            'AttributeName': 'form_type',
                            'KeyType': 'RANGE'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    }
                },
                {
                    'IndexName': 'created-at-index',
                    'KeySchema': [
                        {
                            'AttributeName': 'form_type',
                            'KeyType': 'HASH'
                        },
                        {
                            'AttributeName': 'created_at',
                            'KeyType': 'RANGE'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    }
                }
            ],
            BillingMode='PAY_PER_REQUEST',
            Tags=[
                {
                    'Key': 'Environment',
                    'Value': 'production'
                },
                {
                    'Key': 'Service',
                    'Value': 'province-tax-system'
                },
                {
                    'Key': 'Purpose',
                    'Value': 'document-version-tracking'
                }
            ]
        )
        
        print(f"✅ Table creation initiated successfully")
        print(f"   Table ARN: {response['TableDescription']['TableArn']}")
        print(f"   Status: {response['TableDescription']['TableStatus']}")
        
        # Wait for table to be active
        print("⏳ Waiting for table to become active...")
        waiter = dynamodb.get_waiter('table_exists')
        waiter.wait(
            TableName=table_name,
            WaiterConfig={
                'Delay': 5,
                'MaxAttempts': 60
            }
        )
        
        # Verify table is active
        response = dynamodb.describe_table(TableName=table_name)
        if response['Table']['TableStatus'] == 'ACTIVE':
            print(f"🎉 Table '{table_name}' is now ACTIVE and ready to use!")
            
            # Print table details
            table = response['Table']
            print(f"\n📊 Table Details:")
            print(f"   Name: {table['TableName']}")
            print(f"   Status: {table['TableStatus']}")
            print(f"   Creation Date: {table['CreationDateTime']}")
            print(f"   Item Count: {table.get('ItemCount', 0)}")
            print(f"   Size: {table.get('TableSizeBytes', 0)} bytes")
            
            print(f"\n🔑 Key Schema:")
            for key in table['KeySchema']:
                print(f"   {key['AttributeName']} ({key['KeyType']})")
            
            print(f"\n📇 Global Secondary Indexes:")
            for gsi in table.get('GlobalSecondaryIndexes', []):
                print(f"   {gsi['IndexName']}")
                for key in gsi['KeySchema']:
                    print(f"     {key['AttributeName']} ({key['KeyType']})")
            
            return True
        else:
            print(f"❌ Table creation failed. Status: {response['Table']['TableStatus']}")
            return False
            
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        
        if error_code == 'ResourceInUseException':
            print(f"✅ Table '{table_name}' already exists")
            return True
        else:
            print(f"❌ Error creating table: {error_code} - {error_message}")
            return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

def main():
    """Main function."""
    print("🏗️  Province Document Version Table Setup")
    print("=" * 50)
    
    success = create_document_version_table()
    
    if success:
        print("\n✅ Setup completed successfully!")
        print("\n📋 Next Steps:")
        print("1. Update your .env.local file with:")
        print("   DOCUMENT_VERSIONS_TABLE_NAME=province-document-versions")
        print("2. The table is ready for document version tracking")
        print("3. Test the versioning system with the tax form filler")
        
        return 0
    else:
        print("\n❌ Setup failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
