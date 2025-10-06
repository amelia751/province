# Bedrock Permissions Fix

## Issue
The IAM user `BedrockAPIKey-5rpi` ([REDACTED-AWS-KEY-2]) can invoke Bedrock agents but gets "Access denied when calling Bedrock" when the agent tries to invoke the underlying foundation models.

## Root Cause
The IAM user has `bedrock-agent:InvokeAgent` permission but lacks `bedrock:InvokeModel` permission for the foundation models used by the agents.

## Required IAM Permissions

Add these permissions to the IAM user `BedrockAPIKey-5rpi`:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream"
            ],
            "Resource": [
                "arn:aws:bedrock:us-east-2::foundation-model/anthropic.claude-3-5-sonnet-20240620-v1:0",
                "arn:aws:bedrock:us-east-2::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0",
                "arn:aws:bedrock:us-east-2::foundation-model/amazon.nova-pro-v1:0",
                "arn:aws:bedrock:us-east-2::foundation-model/amazon.nova-lite-v1:0",
                "arn:aws:bedrock:us-east-2::foundation-model/us.anthropic.claude-3-5-sonnet-20240620-v1:0"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "bedrock-agent:InvokeAgent"
            ],
            "Resource": [
                "arn:aws:bedrock:us-east-2:[REDACTED-ACCOUNT-ID]:agent/*"
            ]
        }
    ]
}
```

## How to Fix

### Option 1: AWS Console
1. Go to AWS IAM Console
2. Find user `BedrockAPIKey-5rpi`
3. Add the above policy as an inline policy or attach a managed policy

### Option 2: AWS CLI
```bash
# Create policy document
cat > bedrock-permissions.json << 'EOF'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream"
            ],
            "Resource": [
                "arn:aws:bedrock:us-east-2::foundation-model/anthropic.claude-3-5-sonnet-20240620-v1:0",
                "arn:aws:bedrock:us-east-2::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0",
                "arn:aws:bedrock:us-east-2::foundation-model/amazon.nova-pro-v1:0",
                "arn:aws:bedrock:us-east-2::foundation-model/amazon.nova-lite-v1:0",
                "arn:aws:bedrock:us-east-2::foundation-model/us.anthropic.claude-3-5-sonnet-20240620-v1:0"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "bedrock-agent:InvokeAgent"
            ],
            "Resource": [
                "arn:aws:bedrock:us-east-2:[REDACTED-ACCOUNT-ID]:agent/*"
            ]
        }
    ]
}
EOF

# Apply the policy
aws iam put-user-policy \
    --user-name BedrockAPIKey-5rpi \
    --policy-name BedrockModelAccess \
    --policy-document file://bedrock-permissions.json
```

## Verification

After applying the permissions, test with:

```bash
cd /Users/anhlam/province/backend
source venv/bin/activate
python test_bedrock.py
```

You should see a successful response from the Bedrock agent instead of the access denied error.

## Current Status

✅ Mock responses removed from code
✅ Real Bedrock agent invocation working
✅ API endpoints working
❌ IAM permissions need to be updated (this document provides the fix)

Once permissions are fixed, the system will work with real Bedrock responses instead of mocks.
