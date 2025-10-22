#!/usr/bin/env python3
"""
Fix Bedrock Data Automation Execution Role permissions.

The issue: Bedrock Data Automation uses a service role (BedrockDataAutomationExecutionRole)
that needs permission to read from the input S3 bucket and write to the output S3 bucket.

This script adds the necessary S3 permissions to that role.
"""

import boto3
import json

def fix_bedrock_execution_role():
    """Add S3 permissions to the Bedrock Data Automation Execution Role."""
    
    iam = boto3.client('iam')
    
    role_name = "BedrockDataAutomationExecutionRole"
    account_id = "[REDACTED-ACCOUNT-ID]"
    
    # S3 policy for Bedrock to access input/output buckets
    s3_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "ReadFromInputBucket",
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:GetObjectVersion",
                    "s3:ListBucket",
                    "s3:GetBucketLocation"
                ],
                "Resource": [
                    f"arn:aws:s3:::province-documents-{account_id}-us-east-1",
                    f"arn:aws:s3:::province-documents-{account_id}-us-east-1/*"
                ]
            },
            {
                "Sid": "WriteToOutputBucket",
                "Effect": "Allow",
                "Action": [
                    "s3:PutObject",
                    "s3:PutObjectAcl",
                    "s3:ListBucket",
                    "s3:GetBucketLocation"
                ],
                "Resource": [
                    "arn:aws:s3:::[REDACTED-BEDROCK-BUCKET]",
                    "arn:aws:s3:::[REDACTED-BEDROCK-BUCKET]/*"
                ]
            }
        ]
    }
    
    policy_name = "BedrockDataAutomationS3Access"
    
    try:
        print(f"📋 Checking if role '{role_name}' exists...")
        
        # Check if role exists
        try:
            iam.get_role(RoleName=role_name)
            print(f"✅ Role '{role_name}' exists")
        except iam.exceptions.NoSuchEntityException:
            print(f"❌ Role '{role_name}' not found!")
            print(f"\n💡 You need to create this role first. Here's how:")
            print(f"\n1. Go to AWS IAM Console: https://console.aws.amazon.com/iam/")
            print(f"2. Navigate to Roles → Create role")
            print(f"3. Select 'AWS service' → 'Bedrock'")
            print(f"4. Name it: {role_name}")
            print(f"5. Then run this script again")
            return
        
        print(f"\n📝 Attaching S3 access policy...")
        
        # Try to attach the policy (will update if it exists)
        iam.put_role_policy(
            RoleName=role_name,
            PolicyName=policy_name,
            PolicyDocument=json.dumps(s3_policy)
        )
        
        print(f"✅ Successfully attached policy '{policy_name}' to role '{role_name}'")
        
        # Verify the policy was attached
        print(f"\n🔍 Verifying policy attachment...")
        policies = iam.list_role_policies(RoleName=role_name)
        
        if policy_name in policies['PolicyNames']:
            print(f"✅ Policy '{policy_name}' is attached to role '{role_name}'")
            print(f"\n📊 Current inline policies on role:")
            for policy in policies['PolicyNames']:
                print(f"   - {policy}")
        else:
            print(f"⚠️  Policy attachment verification failed")
        
        print(f"\n" + "="*80)
        print(f"✅ Bedrock Data Automation Execution Role permissions fixed!")
        print(f"="*80)
        print(f"\n💡 Next steps:")
        print(f"1. Try uploading a W-2 through the frontend again")
        print(f"2. The Bedrock processing should now work without AccessDeniedException")
        print(f"3. If you still get errors, check the CloudWatch logs for Bedrock")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"\n💡 Possible solutions:")
        print(f"1. Make sure you have IAM permissions to modify roles")
        print(f"2. Try running with admin credentials")
        print(f"3. Manually add the policy via AWS Console:")
        print(f"   - Go to IAM → Roles → {role_name}")
        print(f"   - Add inline policy with the JSON above")


if __name__ == "__main__":
    fix_bedrock_execution_role()

