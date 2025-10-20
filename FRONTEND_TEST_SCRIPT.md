# 🧪 Frontend Conversation Test Script

## Pre-Test Setup
1. ✅ Backend running on `http://localhost:8000`
2. ✅ Frontend running on `http://localhost:3000`
3. ✅ Logged in with Clerk user ID: `user_33w9KAn1gw3xXSa6MnBsySAQIIm`
4. ✅ W-2 file ready: `~/Downloads/W2_XL_input_clean_1000.pdf`

---

## 📝 Test Conversation Flow

### Step 1: Initial Greeting
**You type:** `Hi, I need help filing my taxes`

**Expected Response:**
- Agent introduces itself
- Asks for filing status or W-2 upload

---

### Step 2: Upload W-2
**Action:** Drag and drop `W2_XL_input_clean_1000.pdf` into chat

**Expected Response:**
- Processing message
- Confirmation: "I've successfully processed your W-2"
- Shows wages: **$55,151.93**
- Shows withholding: **$16,606.17**
- Asks follow-up questions (filing status)

---

### Step 3: Filing Status
**You type:** `I'm filing as Single`

**Expected Response:**
- Confirms filing status saved
- Asks next question (dependents)

---

### Step 4: Dependents
**You type:** `I have no dependents`

**Expected Response:**
- Confirms dependents saved
- May ask for ZIP code or proceed to calculation

---

### Step 5: ZIP Code (if asked)
**You type:** `My ZIP code is 45881`

**Expected Response:**
- Confirms location
- Ready to calculate

---

### Step 6: Calculate Taxes
**You type:** `Please calculate my taxes`

**Expected Response:**
- Shows calculation summary:
  - AGI: **$55,151.93**
  - Standard Deduction: **$14,600.00**
  - Tax Liability: **$4,634.23**
  - **REFUND: $11,971.94** 💰
- Asks if you want to fill Form 1040

---

### Step 7: Fill Form
**You type:** `Yes, please fill out my Form 1040`

**Expected Response:**
- "I've successfully filled out your Form 1040"
- Version number (e.g., v001)
- **Main Editor should update with the filled form PDF**

---

### Step 8: Verify in Main Editor
**Action:** Switch to Main Editor tab → "📋 Form 1040 (Your Taxes)"

**Expected:**
- ✅ Form 1040 visible
- ✅ Shows version (v001)
- ✅ Fields filled:
  - Name: John Smith
  - SSN: 123-45-6789
  - Address: 123 Main St, Anytown, CA 90210
  - Filing Status: Single ✓
  - Wages: $55,151.93
  - Withholding: $16,606.17
  - Refund: $11,971.94

---

## 🐛 Debug Info - Quick Access

### If Anything Fails:

1. **Switch to Debug Info Tab** in Main Editor
2. **Click "📋 Copy Debug Info"** button
3. **Paste it to me** - I'll diagnose the issue

### What the Debug Info Contains:
- ✅ Your User ID (Clerk)
- ✅ Engagement ID (project ID)
- ✅ Session ID (agent session)
- ✅ Recent API calls & responses
- ✅ Chat state (messages, agent name)
- ✅ Any errors
- ✅ Backend connection status
- ✅ Form filling status
- ✅ S3 path for your forms

**This makes troubleshooting instant!** 🚀

---

## ✅ Success Criteria

- [ ] W-2 uploads successfully
- [ ] Agent extracts wages ($55,151.93) and withholding ($16,606.17)
- [ ] Conversation flows naturally (no errors)
- [ ] Tax calculation returns correct refund ($11,971.94)
- [ ] Form 1040 is filled and saved
- [ ] Form appears in Main Editor automatically
- [ ] All critical fields are filled (17+ fields)
- [ ] No console errors in browser

---

## 🔄 Quick Reset (if needed)

If you need to restart the test:
```bash
# Delete test data (run in terminal)
aws s3 rm s3://province-documents-[REDACTED-ACCOUNT-ID]-us-east-1/filled_forms/user_33w9KAn1gw3xXSa6MnBsySAQIIm/ --recursive
aws s3 rm s3://province-documents-[REDACTED-ACCOUNT-ID]-us-east-1/documents/user_33w9KAn1gw3xXSa6MnBsySAQIIm/ --recursive
```

Then refresh the page and start over.

---

## 📋 Copy/Paste Quick Test

**For fastest test, copy/paste these in order:**

1. `Hi, I need help filing my taxes`
2. [Upload W2_XL_input_clean_1000.pdf]
3. `I'm filing as Single`
4. `I have no dependents`
5. `My ZIP code is 45881`
6. `Please calculate my taxes`
7. `Yes, please fill out my Form 1040`

**Expected result:** 
- Form 1040 appears in Main Editor 
- Refund: **$11,971.94** 💰
- All critical fields filled

---

## 🎨 Visual Checks

### In Chat:
- Messages should appear instantly
- No "Processing..." stuck forever
- Agent responses are conversational and helpful
- File uploads show progress

### In Main Editor:
- PDF renders clearly
- Can zoom in/out
- Fields are filled with correct values
- Version number shows (v001, v002, etc.)
- No blank pages

### In Debug Info:
- User ID shows correctly
- Engagement ID matches URL
- No errors in the ERRORS section
- Recent API calls show status 200

---

## 🚨 Common Issues & Solutions

### Issue: W-2 upload fails
**Solution:** Check Debug Info → BACKEND → Test Backend button. Backend might be down.

### Issue: Form doesn't appear in Main Editor
**Solution:** Check Debug Info → FORM_STATUS → s3Path. Verify form was saved.

### Issue: Agent doesn't respond
**Solution:** Check Debug Info → CHAT_STATE → isConnected should be true.

### Issue: Form fields are empty
**Solution:** Copy Debug Info and send to me - likely a mapping issue.

---

## 📞 Need Help?

If anything fails:
1. Click "📋 Copy Debug Info" in Main Editor
2. Paste it to me
3. I'll fix it immediately

**The enhanced debug info includes everything I need to diagnose and fix issues instantly!** 🎯
