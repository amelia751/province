#!/usr/bin/env python3
"""Script to create the tax connections table with TTL."""

import boto3
import os
from botocore.exceptions import ClientError


def create_connections_table():
    """Create the tax connections table with TTL."""
    
    # Get AWS credentials from environment
    dynamodb = boto3.resource(
        'dynamodb',
        region_name=os.getenv('AWS_REGION', 'us-east-2'),
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )
    
    table_name = 'province-tax-connections'
    
    try:
        # Check if table already exists
        table = dynamodb.Table(table_name)
        table.load()
        print(f"Table {table_name} already exists")
        return
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            # Table doesn't exist, create it
            print(f"Creating table {table_name}...")
            
            try:
                # Create table without TTL first
                table = dynamodb.create_table(
                    TableName=table_name,
                    KeySchema=[
                        {
                            'AttributeName': 'connection_id',
                            'KeyType': 'HASH'
                        }
                    ],
                    AttributeDefinitions=[
                        {
                            'AttributeName': 'connection_id',
                            'AttributeType': 'S'
                        },
                        {
                            'AttributeName': 'engagement_id',
                            'AttributeType': 'S'
                        },
                        {
                            'AttributeName': 'created_at',
                            'AttributeType': 'S'
                        }
                    ],
                    BillingMode='PAY_PER_REQUEST',
                    GlobalSecondaryIndexes=[
                        {
                            'IndexName': 'EngagementIndex',
                            'KeySchema': [
                                {
                                    'AttributeName': 'engagement_id',
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
                    ]
                )
                
                # Wait for table to be created
                print(f"Waiting for table {table_name} to be created...")
                table.wait_until_exists()
                
                # Now enable TTL
                print(f"Enabling TTL for table {table_name}...")
                dynamodb_client = boto3.client(
                    'dynamodb',
                    region_name=os.getenv('AWS_REGION', 'us-east-2'),
                    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
                )
                
                dynamodb_client.update_time_to_live(
                    TableName=table_name,
                    TimeToLiveSpecification={
                        'AttributeName': 'ttl',
                        'Enabled': True
                    }
                )
                
                print(f"✅ Table {table_name} created successfully with TTL")
                
            except ClientError as create_error:
                print(f"❌ Error creating table {table_name}: {create_error}")
                
        else:
            print(f"❌ Error checking table {table_name}: {e}")


if __name__ == "__main__":
    print("Creating tax connections table...")
    create_connections_table()
    print("Done!")
