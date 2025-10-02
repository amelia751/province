# Bedrock Setup Guide

## Problem Identified ✅

Your IAM user `province` (Account: [REDACTED-ACCOUNT-ID]) **does not have Bedrock permissions**.

## Solution - Two Steps Required

### Step 1: Add IAM Permissions

You need to add an inline policy to your IAM user. Follow these steps:

1. **Go to IAM Console**: https://console.aws.amazon.com/iam/
2. **Navigate to Users**: Click "Users" in the left sidebar
3. **Select your user**: Find and click on `province`
4. **Add Policy**:
   - Click the "Permissions" tab
   - Click "Add permissions" dropdown
   - Select "Create inline policy"
5. **Paste Policy**:
   - Click the "JSON" tab
   - Delete the placeholder and paste this:

```json
{
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
```

6. **Create Policy**:
   - Click "Review policy"
   - Name it: `BedrockFullAccess`
   - Click "Create policy"

### Step 2: Enable Claude Models in Bedrock

You also need to enable model access:

1. **Go to Bedrock Console**: https://console.aws.amazon.com/bedrock/
2. **Select Region**: Make sure you're in `us-east-1` (top right corner)
3. **Model Access**: Click "Model access" in the left sidebar
4. **Manage Access**: Click "Manage model access" button
5. **Enable Claude**:
   - Find "Anthropic" section
   - Check the box for "Claude 3.5 Sonnet v2"
   - Alternatively, check "Claude 3.5 Sonnet" or "Claude 3 Sonnet" (older versions)
6. **Save Changes**: Click "Save changes" at the bottom
7. **Wait**: Model access can take a few minutes to be granted

## Testing After Setup

Once you've completed both steps above, run this command to test:

```bash
cd /Users/anhlam/province/backend
source venv/bin/activate
export AWS_ACCESS_KEY_ID=[REDACTED-AWS-KEY-1]
export AWS_SECRET_ACCESS_KEY='[REDACTED-AWS-SECRET-1]'
export AWS_DEFAULT_REGION=us-east-1
python3 test_direct_invoke.py
```

If successful, you should see: **"✅ SUCCESS! Claude responded: Working!"**

## Generate Your First Template

Once Bedrock is working, test template generation:

```bash
python3 test_template_generation_simple.py
```

This will generate a complete legal matter template using Claude!

## Troubleshooting

### If you still get AccessDenied:
- Wait 5-10 minutes for IAM policy changes to propagate
- Try logging out and back into AWS Console
- Verify the policy was created (check IAM > Users > province > Permissions)

### If you get "Model not found":
- Ensure you enabled the correct Claude model in Bedrock console
- Try a different region: `us-west-2` instead of `us-east-1`
- Some accounts need to request access for certain models

### Alternative Models

If Claude 3.5 Sonnet v2 isn't available, try these model IDs (update in test scripts):

- `anthropic.claude-3-5-sonnet-20240620-v1:0` (Claude 3.5 Sonnet v1)
- `anthropic.claude-3-sonnet-20240229-v1:0` (Claude 3 Sonnet)
- `anthropic.claude-3-haiku-20240307-v1:0` (Claude 3 Haiku - cheaper, faster)

## Need Help?

If you're still having issues, check:
1. AWS Console > IAM > Users > province > Permissions tab - is BedrockFullAccess there?
2. AWS Console > Bedrock > Model access - is Claude enabled and status "Access granted"?
3. Run `python3 check_bedrock_access.py` for detailed diagnostics

