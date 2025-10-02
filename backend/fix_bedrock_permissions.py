#!/usr/bin/env python3
"""Automatically add Bedrock permissions to the IAM user."""

import boto3
import json
import sys

def add_bedrock_permissions():
    """Add Bedrock permissions to the current IAM user."""
    
    print("🔧 Adding Bedrock Permissions")
    print("=" * 50)
    
    try:
        # Get IAM client
        iam = boto3.client('iam')
        sts = boto3.client('sts')
        
        # Get current user
        caller_identity = sts.get_caller_identity()
        user_arn = caller_identity['Arn']
        user_name = user_arn.split('/')[-1]
        
        print(f"Current user: {user_name}")
        print(f"Account: {caller_identity['Account']}")
        print()
        
        # Define the Bedrock policy
        policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "BedrockInvokeModel",
                    "Effect": "Allow",
                    "Action": [
                        "bedrock:InvokeModel",
                        "bedrock:InvokeModelWithResponseStream",
                        "bedrock:ListFoundationModels",
                        "bedrock:GetFoundationModel"
                    ],
                    "Resource": [
                        "arn:aws:bedrock:*::foundation-model/anthropic.claude-*",
                        "arn:aws:bedrock:*::foundation-model/*"
                    ]
                }
            ]
        }
        
        policy_name = "BedrockFullAccess"
        
        print(f"📝 Adding policy '{policy_name}' to user '{user_name}'...")
        
        # Try to add the inline policy
        iam.put_user_policy(
            UserName=user_name,
            PolicyName=policy_name,
            PolicyDocument=json.dumps(policy_document)
        )
        
        print(f"✅ Successfully added Bedrock permissions!")
        print()
        print("Policy added:")
        print(json.dumps(policy_document, indent=2))
        print()
        print("🎉 Bedrock should now be accessible!")
        return True
        
    except Exception as e:
        error_str = str(e)
        print(f"❌ Error: {error_str}")
        print()
        
        if "AccessDenied" in error_str or "not authorized" in error_str:
            print("⚠️  You don't have permission to modify IAM policies programmatically.")
            print()
            print("Please add the policy manually through the AWS Console:")
            print()
            print("=" * 50)
            print("MANUAL STEPS:")
            print("=" * 50)
            print("1. Go to https://console.aws.amazon.com/iam/")
            print("2. Click 'Users' in the left sidebar")
            print("3. Find and click on user: province")
            print("4. Go to 'Permissions' tab")
            print("5. Click 'Add permissions' -> 'Create inline policy'")
            print("6. Click 'JSON' tab")
            print("7. Paste this policy:")
            print()
            print(json.dumps(policy_document, indent=2))
            print()
            print("8. Click 'Review policy'")
            print("9. Name it 'BedrockFullAccess'")
            print("10. Click 'Create policy'")
            print("=" * 50)
        
        return False

if __name__ == "__main__":
    success = add_bedrock_permissions()
    
    if not success:
        sys.exit(1)

