# 🧪 Frontend Testing Instructions - With Proper Fix

## ✅ Proper Fix Summary

The system now **properly waits for Bedrock Data Automation processing** before extracting W-2 data. This means:
- ✅ Frontend and backend will use the same real data
- ✅ No more hardcoded fallback values (John Smith, etc.)
- ✅ System automatically waits up to 3 minutes for Bedrock to complete

---

## 🚀 Test Setup

### Prerequisites:
1. ✅ Backend running on port 8000 (currently running)
2. ✅ Frontend running on port 3000
3. ✅ Logged in with Clerk user ID: `user_33w9KAn1gw3xXSa6MnBsySAQIIm`

### S3 Status:
```bash
# All previous data cleaned:
✅ S3 filled_forms deleted
✅ S3 documents deleted
✅ Ready for fresh test
```

---

## 📝 Test Sequence

### Step 1: Upload W-2
**Action**: Upload W-2 PDF file via frontend

**What happens**:
- File uploads to S3: `documents/user_33w9KAn1gw3xXSa6MnBsySAQIIm/your_file.pdf`
- Frontend should show loading indicator

**Backend logs to watch for**:
```
🚀 Starting Bedrock Data Automation processing...
   Input: s3://province-documents.../your_file.pdf
   Job UUID: xxx
⏳ Waiting for Bedrock processing (max 180s)...
   [5s] Check #1: Status = IN_PROGRESS
   [10s] Check #2: Status = IN_PROGRESS
   [15s] Check #3: Status = COMPLETED
✅ Bedrock processing completed in 15s
```

**Expected time**: 10-30 seconds for first upload, instant for re-upload

---

### Step 2: Start Conversation
**Say**: `"Hi, I need help filing my taxes"`

**Agent response**: Welcome message

---

### Step 3: Tell Agent About W-2
**Say**: `"I uploaded my W-2 at documents/user_33w9KAn1gw3xXSa6MnBsySAQIIm/YOUR_FILE_NAME.pdf"`

**Backend logs to watch for**:
```
✅ Stored W-2 data in session 'tax_session_xxx'
   Employee: [REAL NAME FROM W-2]
   SSN: [REAL SSN FROM W-2]
   Address: [REAL ADDRESS FROM W-2]
```

**Agent response**: Should confirm W-2 processed with wages and withholding amounts

---

### Step 4: Filing Status
**Say**: `"Single"`

**Agent response**: Confirms filing status

---

### Step 5: Dependents
**Say**: `"No dependents"`

**Agent response**: Confirms no dependents

---

### Step 6: Fill Form
**Say**: `"Please fill my Form 1040"`

**Backend logs to watch for**:
```
🔍 DEBUG fill_form_tool:
   Current session_id: tax_session_xxx
   Session data keys: ['started_at', 'status', 'user_id', 'w2_data']
   Has w2_data: True
   W2 data keys: ['forms', 'total_wages', 'total_withholding', ...]
✅ Found W-2 employee data: {'name': '[REAL NAME]', 'SSN': '[REAL SSN]', 'address': '[REAL ADDRESS]', ...}
```

**⚠️ If you see this**: `⚠️ NO W-2 DATA FOUND in session 'xxx' - will use fallback values!`
→ **Problem**: Session state lost or W-2 not stored properly
→ **Copy and paste the debug info from frontend**

---

## 🔍 What to Check in Frontend Debug Info

After filling the form, check the debug info tab for:

```json
{
  "USER_ID": "user_33w9KAn1gw3xXSa6MnBsySAQIIm",
  "ENGAGEMENT_ID": "ea3b3a4f-c877-4d29-bd66-2cff2aa77476",
  "CHAT_STATE": {
    "currentSession": {
      "sessionId": "tax_session_20251020_105926",
      "status": "active"
    }
  },
  "RECENT_API_CALLS": [
    {
      "url": "/api/v1/tax-service/continue",
      "status": 200,
      "timestamp": "..."
    }
  ]
}
```

---

## ✅ Expected Results

### Form Should Show:
- ✅ **Real employee name** (from your W-2)
- ✅ **Real SSN** (from your W-2)
- ✅ **Real address** (from your W-2)
- ✅ **Real wages** (Box 1 from W-2)
- ✅ **Real withholding** (Box 2 from W-2)
- ✅ **Calculated refund/tax due**

### Form Should NOT Show:
- ❌ John Smith
- ❌ 123 Main St, Anytown, CA 90210
- ❌ 123-45-6789

---

## 🐛 Troubleshooting

### Issue 1: Still Seeing Hardcoded Data

**Check Backend Logs For**:
```bash
# In terminal or backend.log:
tail -100 /Users/anhlam/province/backend/backend.log | grep -E "(NO W-2 DATA|Stored W-2|Found W-2)"
```

**If you see**: `⚠️ NO W-2 DATA FOUND`
→ W-2 was not stored in session

**Possible causes**:
1. Session ID mismatch between API calls
2. Bedrock processing failed/timed out
3. File path incorrect

**Solution**: Copy full debug info from frontend and backend logs

---

### Issue 2: Long Wait Time

**If Bedrock takes > 30 seconds**:
- ✅ This is normal for first-time uploads
- ✅ System will wait up to 3 minutes
- ✅ Subsequent uploads of same file are instant (cached)

**If timeout after 3 minutes**:
- Check AWS Bedrock service status
- Check IAM permissions
- Check backend logs for specific error

---

### Issue 3: Form Not Visible

**Check**:
1. Backend returned S3 URL in response
2. Frontend is calling `/api/v1/forms/1040/{engagement_id}/versions`
3. S3 file exists at path: `filled_forms/user_33w9KAn1gw3xXSa6MnBsySAQIIm/1040/2024/vXXX_1040_*.pdf`

**Verify**:
```bash
aws s3 ls s3://province-documents-[REDACTED-ACCOUNT-ID]-us-east-1/filled_forms/user_33w9KAn1gw3xXSa6MnBsySAQIIm/1040/2024/
```

---

## 📊 Performance Expectations

| Action | Expected Time |
|--------|--------------|
| Upload W-2 (first time) | 10-30 seconds |
| Upload W-2 (re-upload) | < 1 second |
| Fill Form | 3-5 seconds |
| Save Form | 1-2 seconds |
| Render Form | < 1 second |

**Total End-to-End**: 30-60 seconds for first-time W-2

---

## 🎯 Success Criteria

✅ No hardcoded data in form  
✅ Real employee information from W-2  
✅ Correct tax calculations  
✅ Form saved to S3 with user_id path  
✅ Form visible in frontend  
✅ All fields populated correctly  

---

## 📞 If Issues Occur

**Copy and paste**:
1. Frontend debug info (from debug info tab)
2. Backend logs (last 50 lines):
   ```bash
   tail -50 /Users/anhlam/province/backend/backend.log
   ```
3. Session ID from chat state
4. User ID from Clerk

**This will help diagnose**:
- Session state issues
- Bedrock processing failures
- Data extraction problems
- API communication issues

---

## 🚀 Ready to Test!

**Everything is set up and ready**:
- ✅ Backend updated with proper Bedrock wait logic
- ✅ Enhanced debug logging
- ✅ S3 cleaned for fresh test
- ✅ Backend running on port 8000

**Start testing by**:
1. Opening frontend at `http://localhost:3000`
2. Going to your project
3. Following the test sequence above
4. Watching backend logs in real-time

**Good luck! 🎉**

