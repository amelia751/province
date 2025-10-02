# 🚀 Enable Bedrock Model Access

## Current Status: ✅ Credentials Working! 

Your Bedrock credentials are correctly configured and working. However, **no Claude models are enabled** for your account.

## What You Need To Do (2 minutes)

### Enable Claude Models in Bedrock Console

1. **Open Bedrock Console**  
   Go to: https://console.aws.amazon.com/bedrock/home?region=us-east-1#/modelaccess

2. **Click "Manage model access"**  
   This is the orange button at the top of the page

3. **Enable Anthropic Claude Models**  
   Find the "Anthropic" section and check these boxes:
   - ✅ **Claude 3 Haiku** (fastest, cheapest - recommended to start)
   - ✅ **Claude 3 Sonnet** (balanced)
   - ✅ **Claude 3.5 Sonnet** (most capable)
   
   *Tip: Enable all three to have flexibility*

4. **Review and Save**  
   - Scroll to bottom
   - Review the terms
   - Click **"Request model access"** or **"Save changes"**

5. **Wait for Access**  
   - Status will show "In progress" → "Access granted"
   - Usually takes 1-2 minutes (can take up to 10 minutes)
   - You can refresh the page to check status

## Test After Enabling

Once you see **"Access granted"** status, run:

```bash
cd /Users/anhlam/province/backend
source venv/bin/activate
export $(cat .env.local | grep -v '^#' | xargs)
python3 test_multiple_models.py
```

You should see:
```
🎉 Found X working model(s):
  ✅ anthropic.claude-3-haiku-20240307-v1:0
  ...
```

## Then Test Template Generation

Once models are enabled:

```bash
python3 test_template_generation_simple.py
```

This will generate a complete legal matter template using Claude!

## Troubleshooting

### "Still showing Access Denied"
- Wait 5-10 minutes for AWS to propagate the changes
- Try logging out and back into AWS Console
- Refresh the Bedrock model access page to check status

### "Model not found"
- Ensure you're in the correct region (us-east-1)
- Try a different region: `export BEDROCK_REGION=us-west-2`

### "Quota exceeded"
- Some accounts have usage limits
- Check the Bedrock quotas page
- Request a quota increase if needed

## Cost Information

Claude model pricing (approximate):
- **Claude 3 Haiku**: $0.25 per 1M input tokens, $1.25 per 1M output tokens
- **Claude 3 Sonnet**: $3 per 1M input tokens, $15 per 1M output tokens  
- **Claude 3.5 Sonnet**: $3 per 1M input tokens, $15 per 1M output tokens

Template generation uses ~2,000-4,000 tokens per request (~$0.01-0.06 per template).

---

**Current Status**: ⏸️ Waiting for model access to be enabled  
**Next Step**: Enable Claude models in Bedrock console (link above)  
**Estimated Time**: 2 minutes + waiting for access grant

