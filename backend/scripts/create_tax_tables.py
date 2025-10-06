#!/usr/bin/env python3
"""Script to create DynamoDB tables for tax system."""

import boto3
import os
from botocore.exceptions import ClientError


def create_tax_tables():
    """Create DynamoDB tables for the tax system."""
    
    # Get AWS credentials from environment
    dynamodb = boto3.resource(
        'dynamodb',
        region_name=os.getenv('AWS_REGION', 'us-east-2'),
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )
    
    tables_to_create = [
        {
            'TableName': 'province-tax-engagements',
            'KeySchema': [
                {
                    'AttributeName': 'tenant_id#engagement_id',
                    'KeyType': 'HASH'
                }
            ],
            'AttributeDefinitions': [
                {
                    'AttributeName': 'tenant_id#engagement_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'created_by',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'created_at',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'status',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'updated_at',
                    'AttributeType': 'S'
                }
            ],
            'BillingMode': 'PAY_PER_REQUEST',
            'GlobalSecondaryIndexes': [
                {
                    'IndexName': 'UserIndex',
                    'KeySchema': [
                        {
                            'AttributeName': 'created_by',
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
                },
                {
                    'IndexName': 'StatusIndex',
                    'KeySchema': [
                        {
                            'AttributeName': 'status',
                            'KeyType': 'HASH'
                        },
                        {
                            'AttributeName': 'updated_at',
                            'KeyType': 'RANGE'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    }
                }
            ]
        },
        {
            'TableName': 'province-tax-documents',
            'KeySchema': [
                {
                    'AttributeName': 'tenant_id#engagement_id',
                    'KeyType': 'HASH'
                },
                {
                    'AttributeName': 'doc#path',
                    'KeyType': 'RANGE'
                }
            ],
            'AttributeDefinitions': [
                {
                    'AttributeName': 'tenant_id#engagement_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'doc#path',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'document_type',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'created_at',
                    'AttributeType': 'S'
                }
            ],
            'BillingMode': 'PAY_PER_REQUEST',
            'GlobalSecondaryIndexes': [
                {
                    'IndexName': 'DocumentTypeIndex',
                    'KeySchema': [
                        {
                            'AttributeName': 'document_type',
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
        },
        {
            'TableName': 'province-tax-permissions',
            'KeySchema': [
                {
                    'AttributeName': 'tenant_id#engagement_id',
                    'KeyType': 'HASH'
                },
                {
                    'AttributeName': 'perm#user#user_id',
                    'KeyType': 'RANGE'
                }
            ],
            'AttributeDefinitions': [
                {
                    'AttributeName': 'tenant_id#engagement_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'perm#user#user_id',
                    'AttributeType': 'S'
                }
            ],
            'BillingMode': 'PAY_PER_REQUEST'
        },
        {
            'TableName': 'province-tax-deadlines',
            'KeySchema': [
                {
                    'AttributeName': 'tenant_id#engagement_id',
                    'KeyType': 'HASH'
                },
                {
                    'AttributeName': 'deadline#deadline_id',
                    'KeyType': 'RANGE'
                }
            ],
            'AttributeDefinitions': [
                {
                    'AttributeName': 'tenant_id#engagement_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'deadline#deadline_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'owner_user_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'due_date',
                    'AttributeType': 'S'
                }
            ],
            'BillingMode': 'PAY_PER_REQUEST',
            'GlobalSecondaryIndexes': [
                {
                    'IndexName': 'DueDateIndex',
                    'KeySchema': [
                        {
                            'AttributeName': 'owner_user_id',
                            'KeyType': 'HASH'
                        },
                        {
                            'AttributeName': 'due_date',
                            'KeyType': 'RANGE'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    }
                }
            ]
        },
        {
            'TableName': 'province-tax-connections',
            'KeySchema': [
                {
                    'AttributeName': 'connection_id',
                    'KeyType': 'HASH'
                }
            ],
            'AttributeDefinitions': [
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
            'BillingMode': 'PAY_PER_REQUEST',
            'TimeToLiveSpecification': {
                'AttributeName': 'ttl',
                'Enabled': True
            },
            'GlobalSecondaryIndexes': [
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
        }
    ]
    
    for table_config in tables_to_create:
        table_name = table_config['TableName']
        
        try:
            # Check if table already exists
            table = dynamodb.Table(table_name)
            table.load()
            print(f"Table {table_name} already exists")
            continue
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                # Table doesn't exist, create it
                print(f"Creating table {table_name}...")
                
                try:
                    table = dynamodb.create_table(**table_config)
                    
                    # Wait for table to be created
                    print(f"Waiting for table {table_name} to be created...")
                    table.wait_until_exists()
                    
                    print(f"✅ Table {table_name} created successfully")
                    
                except ClientError as create_error:
                    print(f"❌ Error creating table {table_name}: {create_error}")
                    
            else:
                print(f"❌ Error checking table {table_name}: {e}")


if __name__ == "__main__":
    print("Creating DynamoDB tables for tax system...")
    create_tax_tables()
    print("Done!")
