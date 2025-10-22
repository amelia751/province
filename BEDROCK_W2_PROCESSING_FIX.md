# Bedrock W-2 Processing Fix

## Summary of Issues

### 1. ✅ FIXED: Next.js Route Error
**Error**: `Route "/api/forms/[form_type]/[engagement_id]/versions" used params.engagement_id. params should be awaited`

**Fix Applied**: Updated the route to await the `params` object (Next.js 15 requirement).

**File**: `frontend/src/app/api/forms/[form_type]/[engagement_id]/versions/route.ts`

### 2. ⚠️  TO FIX: Bedrock Data Automation AccessDeniedException

**Error**: 
```
❌ Bedrock invocation failed:
   Error Code: AccessDeniedException
   Message: Access Denied. Check S3 URIs and read/write permissions.
```

**Root Cause**: The **Bedrock Data Automation Execution Role** (service role) doesn't have permission to:
- Read from the input S3 bucket (`province-documents-[REDACTED-ACCOUNT-ID]-us-east-1`)
- Write to the output S3 bucket (`[REDACTED-BEDROCK-BUCKET]`)

**Note**: Your IAM user policy is correct! The issue is with Bedrock's internal service role.

---

## How to Fix (AWS Console)

### Step 1: Navigate to IAM Roles
1. Go to **AWS Console**: https://console.aws.amazon.com/iam/
2. Click **Roles** in the left sidebar
3. Search for `BedrockDataAutomationExecutionRole`
4. Click on the role to open it

### Step 2: Add S3 Permissions
1. Click the **Permissions** tab
2. Click **Add permissions** → **Create inline policy**
3. Click the **JSON** tab
4. Replace the content with the following policy:

```json
{
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
                "arn:aws:s3:::province-documents-[REDACTED-ACCOUNT-ID]-us-east-1",
                "arn:aws:s3:::province-documents-[REDACTED-ACCOUNT-ID]-us-east-1/*"
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
```

5. Click **Review policy**
6. Name it: `BedrockDataAutomationS3Access`
7. Click **Create policy**

### Step 3: Verify Trust Relationship
While you're in the role, click the **Trust relationships** tab and verify it includes:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "bedrock.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
```

If not, click **Edit trust policy** and add it.

---

## Testing the Fix

### Option 1: Test via Frontend
1. Go to your frontend: http://localhost:3000
2. Upload a W-2 document through the chat
3. The agent should now successfully process it without AccessDeniedException

### Option 2: Test via Backend Script
```bash
cd /Users/anhlam/province/backend
python test_full_user_conversation.py
```

Expected output:
```
✅ Session started: tax_session_...
🤖 Agent: Hi! I'm your AI tax filing assistant...

📤 Uploading W-2 to S3...
✅ W-2 uploaded to S3

💬 User: I've uploaded my W-2 form. Can you process it?
Tool #1: ingest_documents_tool
Great news! I've successfully processed your W-2 form...
```

---

## What Was Tested

✅ **Backend conversation flow works**:
- Start conversation
- Upload W-2 to S3
- Process W-2 (pending Bedrock fix)
- Answer questions (filing status, dependents)
- Calculate taxes
- Fill Form 1040
- Save to S3

✅ **Form generation works**:
- 4 versions of Form 1040 created in S3
- Latest version: `filled_forms/user_33w9KAn1gw3xXSa6MnBsySAQIIm/1040/2024/v004_1040_1761069761.pdf`

⚠️ **W-2 processing blocked by Bedrock permissions**:
- Bedrock Data Automation can't read the input W-2
- Needs the execution role fix above

---

## Alternative: If Role Doesn't Exist

If `BedrockDataAutomationExecutionRole` doesn't exist, you need to create it:

### Create the Role
1. Go to **IAM** → **Roles** → **Create role**
2. Select **AWS service** → **Bedrock**
3. Select **Bedrock - Customizable** (allows for Data Automation)
4. Click **Next**
5. Don't attach any managed policies yet (we'll add inline policies)
6. Click **Next**
7. Name: `BedrockDataAutomationExecutionRole`
8. Click **Create role**

### Then follow Step 2 above to add the S3 permissions.

---

## Expected Result After Fix

When you upload a W-2 through the frontend:

**Before (current):**
```
❌ Bedrock invocation failed:
   Error Code: AccessDeniedException
   Message: Access Denied. Check S3 URIs and read/write permissions.
```

**After (with fix):**
```
🚀 Starting Bedrock Data Automation processing...
   Input: s3://province-documents-[REDACTED-ACCOUNT-ID]-us-east-1/W2_XL_input_clean_1000.pdf
   Profile: arn:aws:bedrock:us-east-1:[REDACTED-ACCOUNT-ID]:data-automation-profile/us.data-automation-v1
✅ Bedrock job submitted successfully
   Job UUID: <uuid>
⏳ Waiting for Bedrock processing (up to 180 seconds)...
✅ Bedrock processing complete!
✅ Successfully extracted W-2 data
```

---

## Questions?

If the fix doesn't work:
1. Check CloudWatch Logs for Bedrock Data Automation
2. Verify the S3 bucket names are correct
3. Ensure the role has the correct trust relationship
4. Try restarting the backend server: `cd backend && ./restart.sh`

