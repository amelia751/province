# 🚀 Quick Fix - Bedrock Access Issue

## The Problem
Your IAM user lacks Bedrock permissions. The error is:
```
User: arn:aws:iam::[REDACTED-ACCOUNT-ID]:user/province is not authorized to perform: bedrock:InvokeModel
```

## The Fix (5 minutes)

### 1️⃣ Add IAM Policy (2 minutes)

**Go to:** https://console.aws.amazon.com/iam/home?#/users/province

**Then:**
1. Click **"Permissions"** tab
2. Click **"Add permissions"** → **"Create inline policy"**
3. Click **"JSON"** tab
4. Paste this:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": [
      "bedrock:InvokeModel",
      "bedrock:InvokeModelWithResponseStream",
      "bedrock:ListFoundationModels"
    ],
    "Resource": "arn:aws:bedrock:*::foundation-model/*"
  }]
}
```

5. Name it: **BedrockFullAccess**
6. Click **"Create policy"**

### 2️⃣ Enable Claude Model (2 minutes)

**Go to:** https://console.aws.amazon.com/bedrock/home?region=us-east-1#/modelaccess

**Then:**
1. Click **"Manage model access"**
2. Find **"Anthropic"** section
3. Check ✅ **"Claude 3.5 Sonnet"** (or any Claude model)
4. Click **"Save changes"**
5. **Wait 2-3 minutes** for access to be granted

### 3️⃣ Test It (1 minute)

Run this in your terminal:

```bash
cd /Users/anhlam/province/backend
./test_after_permissions_fix.sh
```

You should see:
```
🎉 SUCCESS! Bedrock is fully working!
```

## That's It!

Once you see the success message, your backend can generate legal templates using Claude AI.

---

## Still Having Issues?

### Check IAM Policy
```bash
aws iam list-user-policies --user-name province
# Should show: BedrockFullAccess
```

### Check Model Access
Go to Bedrock console and verify status is **"Access granted"**

### Try Different Region
If us-east-1 doesn't work, try:
- `export BEDROCK_REGION=us-west-2`
- Then run the test again

### Try Different Model
Edit `test_after_permissions_fix.sh` and change model ID to:
- `anthropic.claude-3-sonnet-20240229-v1:0` (older, more available)
- `anthropic.claude-3-haiku-20240307-v1:0` (faster, cheaper)

---

## Need More Help?

See detailed guide: [BEDROCK_SETUP_GUIDE.md](./BEDROCK_SETUP_GUIDE.md)

